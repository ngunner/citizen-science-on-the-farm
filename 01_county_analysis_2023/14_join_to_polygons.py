#!/usr/bin/env python3
# Provenance: copied from `Raw Data/Bridging Gaps Dataset/Finals/Joined to Polygons/create_geojson.py` (last modified 2025-11-18) into the
# Citizen Science on the Farm replication package, September 2026.
# Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
"""
Script to create a GeoJSON file by combining CSV data with shapefile polygons.
Handles duplicate FIPS codes by selecting the polygon with the largest area.
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import shape
import json
import os

def main():
    # File paths
    csv_path = "FINAL_CONTUS_GBIF.csv"
    shapefile_path = "inputs/c_05mr24/c_05mr24.shp"
    output_path = "contus_counties.geojson"
    
    print("Loading CSV data...")
    # Load CSV data
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} records from CSV")
    print(f"CSV columns: {list(df.columns)}")
    
    print("\nLoading shapefile...")
    # Load shapefile
    gdf = gpd.read_file(shapefile_path)
    print(f"Loaded {len(gdf)} polygons from shapefile")
    print(f"Shapefile columns: {list(gdf.columns)}")
    
    # Check for FIPS column in shapefile
    fips_col = None
    for col in gdf.columns:
        if 'FIPS' in col.upper() or 'FIPS' in col:
            fips_col = col
            break
    
    if fips_col is None:
        print("Available columns in shapefile:")
        for i, col in enumerate(gdf.columns):
            print(f"  {i}: {col}")
        fips_col = input("Enter the column name that contains FIPS codes: ")
    
    print(f"Using FIPS column: {fips_col}")
    
    # Convert FIPS to string and ensure consistent 5-digit format
    gdf[fips_col] = gdf[fips_col].astype(str).str.zfill(5)  # Pad with leading zeros to 5 digits
    df['FIPS'] = df['FIPS'].astype(str).str.zfill(5)  # Pad with leading zeros to 5 digits
    
    # Calculate area for each polygon (convert to projected CRS for accurate area calculation)
    print("\nCalculating polygon areas...")
    # Convert to a projected CRS for accurate area calculation
    gdf_projected = gdf.to_crs('EPSG:3857')  # Web Mercator projection
    gdf['area'] = gdf_projected.geometry.area
    
    # Find and handle duplicate FIPS codes
    print("\nChecking for duplicate FIPS codes...")
    duplicates = gdf[gdf.duplicated(subset=[fips_col], keep=False)]
    
    if len(duplicates) > 0:
        print(f"Found {len(duplicates)} polygons with duplicate FIPS codes")
        
        # Group by FIPS and keep the one with largest area
        gdf_filtered = gdf.loc[gdf.groupby(fips_col)['area'].idxmax()]
        print(f"After filtering duplicates: {len(gdf_filtered)} polygons")
    else:
        print("No duplicate FIPS codes found")
        gdf_filtered = gdf
    
    # Merge CSV data with shapefile data
    print("\nMerging CSV data with shapefile...")
    merged = gdf_filtered.merge(df, left_on=fips_col, right_on='FIPS', how='inner')
    print(f"Merged data contains {len(merged)} records")
    
    # Check for any missing matches
    missing_from_csv = set(gdf_filtered[fips_col]) - set(df['FIPS'])
    missing_from_shapefile = set(df['FIPS']) - set(gdf_filtered[fips_col])
    
    if missing_from_csv:
        print(f"\nWarning: {len(missing_from_csv)} FIPS codes in shapefile not found in CSV")
        print(f"First 10 missing: {list(missing_from_csv)[:10]}")
    
    if missing_from_shapefile:
        print(f"\nWarning: {len(missing_from_shapefile)} FIPS codes in CSV not found in shapefile")
        print(f"First 10 missing: {list(missing_from_shapefile)[:10]}")
    
    # Simplify polygons to reduce file size
    print("\nSimplifying polygons to reduce file size...")
    # Convert to projected CRS for simplification
    merged_projected = merged.to_crs('EPSG:3857')
    # Simplify with tolerance of 100 meters
    merged_projected['geometry'] = merged_projected.geometry.simplify(tolerance=100, preserve_topology=True)
    # Convert back to original CRS
    merged_simplified = merged_projected.to_crs(merged.crs)
    
    # Save as GeoJSON
    print(f"\nSaving GeoJSON to {output_path}...")
    merged_simplified.to_file(output_path, driver='GeoJSON')
    print("GeoJSON file created successfully!")
    
    # Print summary statistics
    print(f"\nSummary:")
    print(f"  Total counties in final GeoJSON: {len(merged_simplified)}")
    print(f"  Coordinate system: {merged_simplified.crs}")
    print(f"  Bounding box: {merged_simplified.total_bounds}")
    
    # Calculate file size reduction
    original_size = len(merged.geometry.iloc[0].wkt) if len(merged) > 0 else 0
    simplified_size = len(merged_simplified.geometry.iloc[0].wkt) if len(merged_simplified) > 0 else 0
    if original_size > 0:
        reduction = (1 - simplified_size / original_size) * 100
        print(f"  Polygon simplification: ~{reduction:.1f}% size reduction")
    
    return merged_simplified

if __name__ == "__main__":
    result = main()
