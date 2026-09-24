#!/usr/bin/env python3
# Provenance: copied from `Raw Data/Bridging Gaps Dataset/Finals/Check area calculations and population density/verify_areas_fixed.py` (last modified 2025-09-19) into the
# Citizen Science on the Farm replication package, September 2026.
# Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
# Recomputes AREA_KM2 and population density from shapefile geometry (EPSG:5070); handles duplicate FIPS polygons.
"""
Script to verify and correct area and population density calculations
using shapefile geometry data - FIXED VERSION that handles duplicates properly.
"""

import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point
import warnings
warnings.filterwarnings('ignore')

def main():
    print("Loading data...")
    
    # Load CSV data
    csv_path = "FINAL_CONTUS_GBIF.csv"
    df = pd.read_csv(csv_path)
    print(f"Loaded CSV with {len(df)} counties")
    
    # Load shapefile
    shapefile_path = "c_05mr24/c_05mr24.shp"
    gdf = gpd.read_file(shapefile_path)
    print(f"Loaded shapefile with {len(gdf)} counties")
    
    # Check for duplicates
    fips_counts = gdf['FIPS'].value_counts()
    duplicates = fips_counts[fips_counts > 1]
    print(f"Found {len(duplicates)} FIPS codes with duplicates in shapefile")
    
    # Check if shapefile has FIPS column
    print("Shapefile columns:", gdf.columns.tolist())
    
    # Look for FIPS or similar identifier in shapefile
    fips_candidates = [col for col in gdf.columns if 'FIPS' in col.upper() or 'GEOID' in col.upper() or 'COUNTY' in col.upper()]
    print("Potential FIPS columns in shapefile:", fips_candidates)
    
    if 'FIPS' in gdf.columns:
        fips_col = 'FIPS'
    elif 'GEOID' in gdf.columns:
        fips_col = 'GEOID'
    else:
        print("Available columns:", gdf.columns.tolist())
        return
    
    # Convert FIPS to string for matching
    df['FIPS'] = df['FIPS'].astype(str)
    gdf[fips_col] = gdf[fips_col].astype(str)
    
    # Merge data
    merged = df.merge(gdf, left_on='FIPS', right_on=fips_col, how='inner', suffixes=('_csv', '_shp'))
    print(f"Successfully merged {len(merged)} counties")
    
    if len(merged) == 0:
        print("No matching counties found. Checking FIPS formats...")
        print("Sample CSV FIPS:", df['FIPS'].head().tolist())
        print("Sample shapefile FIPS:", gdf[fips_col].head().tolist())
        return
    
    # Calculate areas from shapefile geometry
    print("Calculating areas from shapefile geometry...")
    
    # Ensure we're using a projected CRS for accurate area calculations
    if gdf.crs is None or gdf.crs.is_geographic:
        # Use Albers Equal Area Conic for CONUS (EPSG:5070)
        gdf_projected = gdf.to_crs('EPSG:5070')
    else:
        gdf_projected = gdf
    
    # Create a dictionary mapping FIPS to areas - USE LARGEST AREA for duplicates
    area_dict = {}
    for idx, row in gdf_projected.iterrows():
        fips = str(row[fips_col])
        area_km2 = row.geometry.area / 1_000_000  # Convert from m² to km²
        
        if fips not in area_dict or area_km2 > area_dict[fips]:
            area_dict[fips] = area_km2
    
    print(f"Created area dictionary with {len(area_dict)} unique FIPS codes")
    
    # Add calculated areas to merged data
    merged['AREA_KM2_CALCULATED'] = merged['FIPS'].map(area_dict)
    
    # Remove rows where we couldn't find the area (shouldn't happen after merge, but just in case)
    merged = merged.dropna(subset=['AREA_KM2_CALCULATED'])
    print(f"After area calculation: {len(merged)} counties")
    
    # Calculate population density using calculated areas
    merged['POP_DENSITY_CALCULATED'] = merged['POPULATION_ESTIMATE_2023'] / merged['AREA_KM2_CALCULATED']
    
    # Compare with original values
    print("\nComparing original vs calculated values...")
    
    # Calculate differences
    merged['AREA_DIFF_PERCENT'] = ((merged['AREA_KM2_CALCULATED'] - merged['AREA_KM2']) / merged['AREA_KM2']) * 100
    merged['POP_DENSITY_DIFF_PERCENT'] = ((merged['POP_DENSITY_CALCULATED'] - merged['POPULATION_DENSITY_KM2']) / merged['POPULATION_DENSITY_KM2']) * 100
    
    # Summary statistics
    print(f"Area differences (calculated - original):")
    print(f"  Mean: {merged['AREA_DIFF_PERCENT'].mean():.2f}%")
    print(f"  Median: {merged['AREA_DIFF_PERCENT'].median():.2f}%")
    print(f"  Std: {merged['AREA_DIFF_PERCENT'].std():.2f}%")
    print(f"  Min: {merged['AREA_DIFF_PERCENT'].min():.2f}%")
    print(f"  Max: {merged['AREA_DIFF_PERCENT'].max():.2f}%")
    
    print(f"\nPopulation density differences (calculated - original):")
    print(f"  Mean: {merged['POP_DENSITY_DIFF_PERCENT'].mean():.2f}%")
    print(f"  Median: {merged['POP_DENSITY_DIFF_PERCENT'].median():.2f}%")
    print(f"  Std: {merged['POP_DENSITY_DIFF_PERCENT'].std():.2f}%")
    print(f"  Min: {merged['POP_DENSITY_DIFF_PERCENT'].min():.2f}%")
    print(f"  Max: {merged['POP_DENSITY_DIFF_PERCENT'].max():.2f}%")
    
    # Check Baltimore City specifically
    baltimore = merged[merged['FIPS'] == '24510']
    if len(baltimore) > 0:
        print(f"\nBaltimore City (FIPS 24510):")
        print(f"  Original area: {baltimore['AREA_KM2'].iloc[0]:.2f} km²")
        print(f"  Calculated area: {baltimore['AREA_KM2_CALCULATED'].iloc[0]:.2f} km²")
        print(f"  Area difference: {baltimore['AREA_DIFF_PERCENT'].iloc[0]:.2f}%")
        print(f"  Original density: {baltimore['POPULATION_DENSITY_KM2'].iloc[0]:.2f} people/km²")
        print(f"  Calculated density: {baltimore['POP_DENSITY_CALCULATED'].iloc[0]:.2f} people/km²")
        print(f"  Density difference: {baltimore['POP_DENSITY_DIFF_PERCENT'].iloc[0]:.2f}%")
    
    # Show counties with largest differences
    print("\nCounties with largest area differences:")
    available_cols = ['FIPS', 'AREA_KM2', 'AREA_KM2_CALCULATED', 'AREA_DIFF_PERCENT']
    if 'COUNTYNAME' in merged.columns:
        available_cols.insert(1, 'COUNTYNAME')
    elif 'COUNTYNAME_csv' in merged.columns:
        available_cols.insert(1, 'COUNTYNAME_csv')
    
    large_area_diff = merged.nlargest(10, 'AREA_DIFF_PERCENT')[available_cols]
    print(large_area_diff.to_string(index=False))
    
    print("\nCounties with largest population density differences:")
    density_cols = ['FIPS', 'POPULATION_DENSITY_KM2', 'POP_DENSITY_CALCULATED', 'POP_DENSITY_DIFF_PERCENT']
    if 'COUNTYNAME' in merged.columns:
        density_cols.insert(1, 'COUNTYNAME')
    elif 'COUNTYNAME_csv' in merged.columns:
        density_cols.insert(1, 'COUNTYNAME_csv')
    
    large_density_diff = merged.nlargest(10, 'POP_DENSITY_DIFF_PERCENT')[density_cols]
    print(large_density_diff.to_string(index=False))
    
    # Create corrected dataset
    print("\nCreating corrected dataset...")
    
    # Create a copy of the original dataframe
    corrected_df = df.copy()
    
    # Update with corrected values where differences are significant (>5%)
    significant_area_diff = abs(merged['AREA_DIFF_PERCENT']) > 5
    significant_density_diff = abs(merged['POP_DENSITY_DIFF_PERCENT']) > 5
    
    print(f"Counties with significant area differences (>5%): {significant_area_diff.sum()}")
    print(f"Counties with significant density differences (>5%): {significant_density_diff.sum()}")
    
    # Update corrected values
    for idx, row in merged.iterrows():
        fips = row['FIPS']
        if significant_area_diff.iloc[idx]:
            corrected_df.loc[corrected_df['FIPS'] == fips, 'AREA_KM2'] = row['AREA_KM2_CALCULATED']
        if significant_density_diff.iloc[idx]:
            corrected_df.loc[corrected_df['FIPS'] == fips, 'POPULATION_DENSITY_KM2'] = row['POP_DENSITY_CALCULATED']
    
    # Save corrected dataset
    output_path = "FINAL_CONTUS_GBIF_CORRECTED_FIXED.csv"
    corrected_df.to_csv(output_path, index=False)
    print(f"Saved corrected dataset to {output_path}")
    
    # Save detailed comparison
    comparison_path = "area_density_comparison_fixed.csv"
    comparison_cols = ['FIPS', 'AREA_KM2', 'AREA_KM2_CALCULATED', 'AREA_DIFF_PERCENT', 
                      'POPULATION_DENSITY_KM2', 'POP_DENSITY_CALCULATED', 'POP_DENSITY_DIFF_PERCENT']
    
    # Add county name if available
    if 'COUNTYNAME' in merged.columns:
        comparison_cols.insert(1, 'COUNTYNAME')
    elif 'COUNTYNAME_csv' in merged.columns:
        comparison_cols.insert(1, 'COUNTYNAME_csv')
    
    # Add state if available
    if 'STATE' in merged.columns:
        comparison_cols.insert(2, 'STATE')
    elif 'STATE_csv' in merged.columns:
        comparison_cols.insert(2, 'STATE_csv')
    
    merged[comparison_cols].to_csv(comparison_path, index=False)
    print(f"Saved detailed comparison to {comparison_path}")

if __name__ == "__main__":
    main()
