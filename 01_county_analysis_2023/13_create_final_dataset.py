#!/usr/bin/env python3
# Provenance: copied from `Raw Data/Bridging Gaps Dataset/Finals/Filter to only Counties/create_final_dataset.py` (last modified 2025-09-19) into the
# Citizen Science on the Farm replication package, September 2026.
# Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
"""
Create the final deduplicated county-level dataset.
"""

import pandas as pd
import numpy as np

def load_csv_with_encoding(filepath):
    """Load CSV file with automatic encoding detection."""
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(filepath, encoding=encoding)
            return df
        except UnicodeDecodeError:
            continue
    
    raise ValueError(f"Could not load {filepath} with any of the attempted encodings")

def create_final_dataset():
    """Create the final deduplicated county-level dataset."""
    
    print("Loading original GBIF dataset...")
    gbif_df = load_csv_with_encoding('FINAL_CONTUS_GBIF - Dataset.csv')
    
    print(f"Original dataset: {len(gbif_df)} rows, {gbif_df['FIPS'].nunique()} unique FIPS codes")
    
    # Use the weighted_centroid strategy for aggregation
    print("Aggregating duplicate FIPS codes using weighted centroid method...")
    
    aggregated_df = gbif_df.groupby('FIPS').agg({
        'STATE': 'first',
        'CWA': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0],
        'COUNTYNAME': lambda x: x.iloc[0].split(' in ')[0] if ' in ' in x.iloc[0] else x.iloc[0],
        'TIME_ZONE': 'first',
        'FE_AREA': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0],
        'LONGITUDE': 'mean',
        'LATITUDE': 'mean',
        'PERCENT_ADULTS_BACHELORS_DEGREE_2023': 'mean',
        'POPULATION_ESTIMATE_2023': 'first',  # Population should be same for county
        'PERCENT_POVERTY_2023': 'mean',
        'UNEMPLOYMENT_RATE_2023': 'mean',
        'MEDIAN_HOUSEHOLD_INCOME_2022': 'mean',
        'MEDIAN_HOUSEHOLD_INCOME_PERCENT_OF_STATE_TOTAL_2022': 'mean',
        'AREA_KM2': 'first',  # Area should be same for county
        'TOTAL_GBIF_OBS_COUNT': 'sum',  # Sum observations
        'GBIF_OBS_DENSITY_KM2': 'mean',
        'POPULATION_DENSITY_KM2': 'mean',
        'PERCENT_AGRICULTURE': 'mean',
        'PERCENT_DEVELOPED': 'mean',
        'PERCENT_FOREST': 'mean',
        'PERCENTAGE_GBIF_OBS_ON_AG_LAND': 'mean',
        'PERCENTAGE_OF_AG_LAND_WITHIN_1KM_GBIF_OBS': 'mean'
    }).reset_index()
    
    print(f"Final dataset: {len(aggregated_df)} rows, {aggregated_df['FIPS'].nunique()} unique FIPS codes")
    
    # Save the final dataset
    output_file = "FINAL_CONTUS_GBIF_Counties_Only.csv"
    aggregated_df.to_csv(output_file, index=False)
    print(f"Saved final dataset to: {output_file}")
    
    # Show summary statistics
    print(f"\nSummary:")
    print(f"Original rows: {len(gbif_df)}")
    print(f"Final rows: {len(aggregated_df)}")
    print(f"Rows removed: {len(gbif_df) - len(aggregated_df)}")
    print(f"Reduction: {((len(gbif_df) - len(aggregated_df)) / len(gbif_df) * 100):.1f}%")
    
    # Show examples of cleaned county names
    print(f"\nExamples of cleaned county names:")
    cleaned_names = aggregated_df[aggregated_df['COUNTYNAME'].str.contains('Monroe', na=False)]
    if len(cleaned_names) > 0:
        print(cleaned_names[['FIPS', 'COUNTYNAME']].head())
    
    # Show sample of final data
    print(f"\nSample of final dataset:")
    print(aggregated_df[['FIPS', 'STATE', 'COUNTYNAME', 'LONGITUDE', 'LATITUDE', 'TOTAL_GBIF_OBS_COUNT']].head(10))
    
    return aggregated_df

if __name__ == "__main__":
    create_final_dataset()
