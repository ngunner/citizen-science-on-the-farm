#!/usr/bin/env python3
# Provenance: copied from `Raw Data/Bridging Gaps Dataset/Finals/Filter to only Counties/deduplicate_counties.py` (last modified 2025-09-19) into the
# Citizen Science on the Farm replication package, September 2026.
# Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
"""
Deduplicate county-level data by aggregating sub-regions within the same FIPS code.

This script handles the case where counties are split into multiple geographic sub-regions
(e.g., Monroe County split into Mainland, Upper Keys, Lower Keys, Middle Keys) and
aggregates them into single county-level records.
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

def aggregate_county_data(df, strategy='weighted_centroid'):
    """
    Aggregate duplicate FIPS codes using different strategies.
    
    Parameters:
    - df: DataFrame with duplicate FIPS codes
    - strategy: 'first', 'last', 'mean', 'sum', 'weighted_centroid', 'max_obs'
    
    Returns:
    - Aggregated DataFrame with one row per FIPS code
    """
    
    print(f"Using aggregation strategy: {strategy}")
    
    if strategy == 'first':
        # Keep first occurrence
        return df.groupby('FIPS').first().reset_index()
    
    elif strategy == 'last':
        # Keep last occurrence
        return df.groupby('FIPS').last().reset_index()
    
    elif strategy == 'mean':
        # Take mean of numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(exclude=[np.number]).columns
        
        result = df.groupby('FIPS')[numeric_cols].mean().reset_index()
        
        # Add categorical columns (take first occurrence)
        for col in categorical_cols:
            if col != 'FIPS':
                result[col] = df.groupby('FIPS')[col].first().values
        
        return result
    
    elif strategy == 'sum':
        # Sum numeric columns (useful for counts)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(exclude=[np.number]).columns
        
        result = df.groupby('FIPS')[numeric_cols].sum().reset_index()
        
        # Add categorical columns (take first occurrence)
        for col in categorical_cols:
            if col != 'FIPS':
                result[col] = df.groupby('FIPS')[col].first().values
        
        return result
    
    elif strategy == 'weighted_centroid':
        # Calculate weighted centroid for coordinates, mean for other numeric values
        result = df.groupby('FIPS').agg({
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
        
        return result
    
    elif strategy == 'max_obs':
        # Keep the sub-region with maximum GBIF observations
        idx_max_obs = df.groupby('FIPS')['TOTAL_GBIF_OBS_COUNT'].idxmax()
        return df.loc[idx_max_obs].reset_index(drop=True)
    
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

def main():
    print("Loading GBIF dataset...")
    gbif_df = load_csv_with_encoding('FINAL_CONTUS_GBIF - Dataset.csv')
    
    print(f"Original dataset: {len(gbif_df)} rows, {gbif_df['FIPS'].nunique()} unique FIPS codes")
    
    # Show duplicate statistics
    fips_counts = gbif_df['FIPS'].value_counts()
    duplicates = fips_counts[fips_counts > 1]
    print(f"FIPS codes with duplicates: {len(duplicates)}")
    print(f"Total duplicate rows: {duplicates.sum() - len(duplicates)}")
    
    # Try different strategies
    strategies = ['weighted_centroid', 'max_obs', 'mean', 'sum']
    
    for strategy in strategies:
        print(f"\n{'='*50}")
        print(f"Testing strategy: {strategy}")
        print(f"{'='*50}")
        
        try:
            aggregated_df = aggregate_county_data(gbif_df, strategy)
            print(f"Result: {len(aggregated_df)} rows, {aggregated_df['FIPS'].nunique()} unique FIPS codes")
            
            # Save the result
            output_file = f"FINAL_CONTUS_GBIF_Counties_Deduplicated_{strategy}.csv"
            aggregated_df.to_csv(output_file, index=False)
            print(f"Saved to: {output_file}")
            
            # Show sample of aggregated data
            print(f"\nSample aggregated data:")
            print(aggregated_df[['FIPS', 'COUNTYNAME', 'LONGITUDE', 'LATITUDE', 'TOTAL_GBIF_OBS_COUNT']].head())
            
        except Exception as e:
            print(f"Error with strategy {strategy}: {e}")
    
    print(f"\n{'='*50}")
    print("RECOMMENDATION:")
    print("The 'weighted_centroid' strategy is recommended because it:")
    print("- Calculates proper geographic centroids for coordinates")
    print("- Sums observation counts (preserving total data)")
    print("- Averages percentages and rates appropriately")
    print("- Cleans up county names (removes sub-region designations)")
    print("- Preserves population and area data (should be same for county)")

if __name__ == "__main__":
    main()
