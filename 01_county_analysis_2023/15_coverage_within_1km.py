#!/usr/bin/env python3
# Provenance: copied from `Raw Data/Bridging Gaps Dataset/Finals/Test Coverage Process/analyze_coverage_optimized.py` (last modified 2025-09-21) into the
# Citizen Science on the Farm replication package, September 2026.
# Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
# Recomputes PERCENTAGE_OF_AG_LAND_WITHIN_1KM_GBIF_OBS per county by pixel counting (ag_raster x obs_1km_raster_merged).
"""
Optimized Agricultural Land Coverage Analysis within 1km of GBIF Observations

This script analyzes the percentage of agricultural land within 1km of GBIF observations
for each county in the continental US using multithreading and efficient processing.
"""

import rasterio
import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio.mask import mask
from rasterio.warp import transform_geom
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp
import warnings
import gc
import os
from functools import partial
import time

warnings.filterwarnings('ignore')

def examine_datasets():
    """Examine the datasets to understand their structure and CRS."""
    print("=== Dataset Information ===")
    
    # Agricultural raster
    with rasterio.open('ag_raster.tif') as src:
        print(f"Agricultural Raster:")
        print(f"  CRS: {src.crs}")
        print(f"  Shape: {src.shape}")
        print(f"  Bounds: {src.bounds}")
        print(f"  Transform: {src.transform}")
        print(f"  NoData value: {src.nodata}")
        # Sample a larger portion to check values
        sample_data = src.read(1, window=((0, 2000), (0, 2000)))
        valid_data = sample_data[~np.isnan(sample_data)]
        print(f"  Sample unique values: {np.unique(valid_data) if len(valid_data) > 0 else 'No valid data in sample'}")
        print(f"  Sample shape: {sample_data.shape}, Valid pixels: {len(valid_data)}")
        print()
        ag_profile = src.profile
    
    # Observation buffer raster (correct filename)
    with rasterio.open('obs_1km_raster_merged.tif') as src:
        print(f"Observation Buffer Raster (1km):")
        print(f"  CRS: {src.crs}")
        print(f"  Shape: {src.shape}")
        print(f"  Bounds: {src.bounds}")
        print(f"  Transform: {src.transform}")
        print(f"  NoData value: {src.nodata}")
        # Sample a larger portion to check values
        sample_data = src.read(1, window=((0, 2000), (0, 2000)))
        valid_data = sample_data[~np.isnan(sample_data)]
        print(f"  Sample unique values: {np.unique(valid_data) if len(valid_data) > 0 else 'No valid data in sample'}")
        print(f"  Sample shape: {sample_data.shape}, Valid pixels: {len(valid_data)}")
        print()
        obs_profile = src.profile
    
    # Counties GeoJSON
    print("Loading counties data...")
    counties = gpd.read_file('contus_counties.geojson')
    print(f"Counties GeoJSON:")
    print(f"  CRS: {counties.crs}")
    print(f"  Number of counties: {len(counties)}")
    print(f"  Columns: {list(counties.columns)}")
    if 'PERCENTAGE_OF_AG_LAND_WITHIN_1KM_GBIF_OBS' in counties.columns:
        print(f"  Previous calculation column exists: PERCENTAGE_OF_AG_LAND_WITHIN_1KM_GBIF_OBS")
    print(f"  Sample county names: {counties['COUNTYNAME'].head().tolist()}")
    print()
    
    return counties, ag_profile, obs_profile

def process_single_county(county_data, ag_raster_path, obs_raster_path, counties_crs):
    """Process a single county to calculate agricultural coverage within 1km of observations."""
    idx, county = county_data
    
    try:
        # Get county geometry and reproject to raster CRS if needed
        county_geom = county.geometry
        
        # Open rasters for this county
        with rasterio.open(ag_raster_path) as ag_src, rasterio.open(obs_raster_path) as obs_src:
            if counties_crs != ag_src.crs:
                reprojected_geoms = reproject_geometries_to_raster_crs([county_geom], counties_crs, ag_src.crs)
                county_geom = reprojected_geoms[0]
            
            # Mask agricultural raster to county
            ag_masked, ag_transform = mask(ag_src, [county_geom], crop=True)
            ag_masked = ag_masked[0]  # Get first band
            
            # Mask observation raster to county
            obs_masked, obs_transform = mask(obs_src, [county_geom], crop=True)
            obs_masked = obs_masked[0]  # Get first band
            
            # Ensure both rasters have the same shape after masking
            if ag_masked.shape != obs_masked.shape:
                return {
                    'county_index': idx,
                    'county_name': county.get('COUNTYNAME', 'Unknown'),
                    'total_ag_pixels': 0,
                    'ag_within_1km_pixels': 0,
                    'percentage_ag_within_1km': 0.0,
                    'error': 'Shape mismatch'
                }
            
            # Count agricultural pixels (assuming 1 = agricultural, 0 = non-agricultural)
            ag_pixels = np.sum(ag_masked == 1)
            
            # Count pixels that are both agricultural and within 1km of observation
            ag_within_1km = np.sum((ag_masked == 1) & (obs_masked == 1))
            
            # Calculate percentage
            if ag_pixels > 0:
                percentage = (ag_within_1km / ag_pixels) * 100
            else:
                percentage = 0.0
            
            return {
                'county_index': idx,
                'county_name': county.get('COUNTYNAME', 'Unknown'),
                'total_ag_pixels': int(ag_pixels),
                'ag_within_1km_pixels': int(ag_within_1km),
                'percentage_ag_within_1km': float(percentage),
                'error': None
            }
            
    except Exception as e:
        return {
            'county_index': idx,
            'county_name': county.get('COUNTYNAME', 'Unknown'),
            'total_ag_pixels': 0,
            'ag_within_1km_pixels': 0,
            'percentage_ag_within_1km': 0.0,
            'error': str(e)
        }

def reproject_geometries_to_raster_crs(geometries, from_crs, to_crs):
    """Reproject geometries to match raster CRS."""
    if from_crs == to_crs:
        return geometries
    
    reprojected_geometries = []
    for geom in geometries:
        try:
            # Transform geometry to raster CRS
            geom_dict = geom.__geo_interface__
            transformed_geom_dict = transform_geom(from_crs, to_crs, geom_dict)
            
            # Convert back to shapely geometry
            from shapely.geometry import shape
            reprojected_geom = shape(transformed_geom_dict)
            reprojected_geometries.append(reprojected_geom)
        except Exception as e:
            print(f"Warning: Failed to reproject geometry: {e}")
            reprojected_geometries.append(geom)
    
    return reprojected_geometries

def calculate_ag_coverage_multithreaded(counties, ag_raster_path, obs_raster_path, max_workers=None, batch_size=100):
    """Calculate agricultural land coverage using multithreading."""
    print(f"=== Calculating Agricultural Coverage (Multithreaded) ===")
    
    if max_workers is None:
        max_workers = min(mp.cpu_count(), 8)  # Limit to 8 threads to avoid memory issues
    
    print(f"Using {max_workers} worker threads")
    print(f"Processing {len(counties)} counties in batches of {batch_size}")
    
    results = []
    total_counties = len(counties)
    processed_count = 0
    
    # Process counties in batches to manage memory
    for batch_start in range(0, total_counties, batch_size):
        batch_end = min(batch_start + batch_size, total_counties)
        batch_counties = counties.iloc[batch_start:batch_end]
        
        print(f"Processing batch {batch_start//batch_size + 1}: counties {batch_start+1}-{batch_end}")
        
        # Prepare county data for processing
        county_data_list = [(batch_start + idx, county) for idx, (_, county) in enumerate(batch_counties.iterrows())]
        
        # Process batch with multithreading
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create partial function with fixed arguments
            process_func = partial(process_single_county, 
                                 ag_raster_path=ag_raster_path,
                                 obs_raster_path=obs_raster_path,
                                 counties_crs=counties.crs)
            
            # Submit all counties in batch
            future_to_county = {executor.submit(process_func, county_data): county_data[0] 
                               for county_data in county_data_list}
            
            # Collect results as they complete
            batch_results = []
            for future in as_completed(future_to_county):
                try:
                    result = future.result()
                    batch_results.append(result)
                    processed_count += 1
                    
                    if processed_count % 10 == 0:
                        print(f"  Processed {processed_count}/{total_counties} counties")
                        
                except Exception as e:
                    county_idx = future_to_county[future]
                    print(f"Error processing county {county_idx}: {e}")
                    batch_results.append({
                        'county_index': county_idx,
                        'county_name': 'Unknown',
                        'total_ag_pixels': 0,
                        'ag_within_1km_pixels': 0,
                        'percentage_ag_within_1km': 0.0,
                        'error': str(e)
                    })
        
        # Add batch results to overall results
        results.extend(batch_results)
        
        # Force garbage collection after each batch
        gc.collect()
        print(f"Completed batch {batch_start//batch_size + 1}")
    
    print(f"Completed processing all {total_counties} counties")
    return results

def update_counties_geojson(counties, results, output_path):
    """Update the counties GeoJSON with the new calculation results."""
    print("=== Updating Counties GeoJSON ===")
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    # Create a mapping from county index to results
    results_dict = {row['county_index']: row for _, row in results_df.iterrows()}
    
    # Add new columns to counties
    counties['TOTAL_AG_PIXELS'] = counties.index.map(lambda x: results_dict.get(x, {}).get('total_ag_pixels', 0))
    counties['AG_WITHIN_1KM_PIXELS'] = counties.index.map(lambda x: results_dict.get(x, {}).get('ag_within_1km_pixels', 0))
    counties['PERCENTAGE_AG_WITHIN_1KM_NEW'] = counties.index.map(lambda x: results_dict.get(x, {}).get('percentage_ag_within_1km', 0.0))
    
    # Save updated GeoJSON
    counties.to_file(output_path, driver='GeoJSON')
    print(f"Updated counties saved to: {output_path}")
    
    # Print summary statistics
    print("\n=== Summary Statistics ===")
    print(f"Total counties processed: {len(counties)}")
    print(f"Counties with agricultural land: {len(counties[counties['TOTAL_AG_PIXELS'] > 0])}")
    print(f"Average percentage of ag land within 1km: {counties['PERCENTAGE_AG_WITHIN_1KM_NEW'].mean():.2f}%")
    print(f"Median percentage of ag land within 1km: {counties['PERCENTAGE_AG_WITHIN_1KM_NEW'].median():.2f}%")
    print(f"Max percentage of ag land within 1km: {counties['PERCENTAGE_AG_WITHIN_1KM_NEW'].max():.2f}%")
    
    # Show top counties by percentage
    top_counties = counties[counties['TOTAL_AG_PIXELS'] > 0].nlargest(10, 'PERCENTAGE_AG_WITHIN_1KM_NEW')
    if len(top_counties) > 0:
        print("\nTop 10 counties by percentage of agricultural land within 1km of observations:")
        for _, county in top_counties.iterrows():
            print(f"  {county['COUNTYNAME']}, {county['STATE']}: {county['PERCENTAGE_AG_WITHIN_1KM_NEW']:.2f}%")
    
    # Compare with previous calculation if it exists
    if 'PERCENTAGE_OF_AG_LAND_WITHIN_1KM_GBIF_OBS' in counties.columns:
        print("\n=== Comparison with Previous Calculation ===")
        prev_col = 'PERCENTAGE_OF_AG_LAND_WITHIN_1KM_GBIF_OBS'
        new_col = 'PERCENTAGE_AG_WITHIN_1KM_NEW'
        
        # Remove rows where either column is NaN for comparison
        comparison_data = counties[[prev_col, new_col]].dropna()
        
        if len(comparison_data) > 0:
            correlation = comparison_data[prev_col].corr(comparison_data[new_col])
            print(f"Correlation with previous calculation: {correlation:.4f}")
            print(f"Mean difference (new - previous): {(comparison_data[new_col] - comparison_data[prev_col]).mean():.2f}%")
            print(f"RMSE: {np.sqrt(((comparison_data[new_col] - comparison_data[prev_col]) ** 2).mean()):.2f}%")
    
    return counties

def main():
    """Main analysis function."""
    print("Optimized Agricultural Land Coverage Analysis within 1km of GBIF Observations")
    print("=" * 80)
    
    start_time = time.time()
    
    # Examine datasets
    counties, ag_profile, obs_profile = examine_datasets()
    
    # Calculate agricultural coverage using multithreading
    results = calculate_ag_coverage_multithreaded(
        counties, 
        'ag_raster.tif', 
        'obs_1km_raster_merged.tif',
        max_workers=6,  # Adjust based on your system
        batch_size=50
    )
    
    # Update counties GeoJSON
    updated_counties = update_counties_geojson(counties, results, 'contus_counties_updated_optimized.geojson')
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"\nAnalysis complete!")
    print(f"Total processing time: {processing_time:.2f} seconds ({processing_time/60:.2f} minutes)")
    print("New columns added:")
    print("- TOTAL_AG_PIXELS: Total number of agricultural pixels in county")
    print("- AG_WITHIN_1KM_PIXELS: Number of agricultural pixels within 1km of observations")
    print("- PERCENTAGE_AG_WITHIN_1KM_NEW: Percentage of agricultural land within 1km of observations")

if __name__ == "__main__":
    main()