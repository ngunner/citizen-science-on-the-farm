#!/usr/bin/env python3
# Provenance: copied from `Raw Data/Bridging Gaps Dataset/Finals/Filter to only Counties/filter_county_data.py` (last modified 2025-09-19) into the
# Citizen Science on the Farm replication package, September 2026.
# Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
"""
Filter GBIF dataset to only include county-level FIPS codes.

This script reads the FINAL_CONTUS_GBIF - Dataset.csv file and filters it
to only include rows where the FIPS code matches those in county_fips_master.csv,
effectively removing city-level entries and keeping only county-level data.
"""

import pandas as pd
import sys
from pathlib import Path

def main():
    # Define file paths
    gbif_file = "FINAL_CONTUS_GBIF - Dataset.csv"
    county_fips_file = "county_fips_master.csv"
    output_file = "FINAL_CONTUS_GBIF_Counties_Only.csv"
    
    print("Loading county FIPS codes...")
    # Load county FIPS codes with encoding detection
    try:
        county_df = pd.read_csv(county_fips_file, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            county_df = pd.read_csv(county_fips_file, encoding='latin-1')
        except UnicodeDecodeError:
            county_df = pd.read_csv(county_fips_file, encoding='cp1252')
    
    county_fips_codes = set(county_df['fips'].astype(str))
    print(f"Loaded {len(county_fips_codes)} county FIPS codes")
    
    print("Loading GBIF dataset...")
    # Load GBIF dataset with encoding detection
    try:
        gbif_df = pd.read_csv(gbif_file, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            gbif_df = pd.read_csv(gbif_file, encoding='latin-1')
        except UnicodeDecodeError:
            gbif_df = pd.read_csv(gbif_file, encoding='cp1252')
    print(f"Loaded {len(gbif_df)} rows from GBIF dataset")
    
    # Convert FIPS column to string for comparison
    gbif_df['FIPS'] = gbif_df['FIPS'].astype(str)
    
    print("Filtering to county-level data only...")
    # Filter to only include rows where FIPS is in county codes
    filtered_df = gbif_df[gbif_df['FIPS'].isin(county_fips_codes)]
    
    print(f"Filtered dataset contains {len(filtered_df)} rows (removed {len(gbif_df) - len(filtered_df)} city-level entries)")
    
    # Save filtered dataset
    print(f"Saving filtered dataset to {output_file}...")
    filtered_df.to_csv(output_file, index=False)
    
    print("Filtering complete!")
    
    # Show some statistics
    print("\nSummary:")
    print(f"Original dataset: {len(gbif_df)} rows")
    print(f"County-only dataset: {len(filtered_df)} rows")
    print(f"Removed: {len(gbif_df) - len(filtered_df)} rows (city-level data)")
    print(f"Retention rate: {len(filtered_df)/len(gbif_df)*100:.1f}%")
    
    # Show unique FIPS codes in filtered data
    unique_fips = filtered_df['FIPS'].nunique()
    print(f"Unique county FIPS codes in filtered data: {unique_fips}")

if __name__ == "__main__":
    main()
