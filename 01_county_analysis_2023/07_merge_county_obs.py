#!/usr/bin/env python3
# Provenance: copied from `Raw Data/Bridging Gaps Dataset/merge_county_data_fixed.py` (last modified 2025-09-17) into the
# Citizen Science on the Farm replication package, September 2026.
# Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
"""
Script to merge county area observation data with CONTUS counties dataset
Author: AI Assistant
Date: Generated for merging datasets
Fixed: Handles FIPS code formatting differences (leading zeros)
"""

import csv
import os
from collections import defaultdict

def read_csv_to_dict(filename):
    """Read CSV file and return as list of dictionaries"""
    data = []
    with open(filename, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            data.append(row)
    return data

def write_dict_to_csv(data, filename, fieldnames):
    """Write list of dictionaries to CSV file"""
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def normalize_fips(fips):
    """Normalize FIPS code to 5 digits with leading zeros"""
    return fips.zfill(5)

def main():
    # Set working directory to the Bridging Gaps Dataset folder
    # Read the datasets
    print("Reading CONTUS counties dataset...")
    contus_data = read_csv_to_dict("Finals/CONTUS_counties_with_final_metrics.csv")
    
    print("Reading county area observation data...")
    obs_data = read_csv_to_dict("county_area_obs_data.csv")
    
    # Display basic information about the datasets
    print(f"CONTUS dataset dimensions: {len(contus_data)} rows, {len(contus_data[0])} columns")
    print(f"Observation data dimensions: {len(obs_data)} rows, {len(obs_data[0])} columns")
    
    # Create a lookup dictionary for observation data by normalized FIPS
    obs_lookup = {}
    for row in obs_data:
        fips = normalize_fips(row['FIPS'])
        obs_lookup[fips] = {
            'area_km2': row['area_km2'],
            'area_ha': row['area_ha'],
            'total_obs_count': row['total_obs_count'],
            'obs_density_km2': row['obs_density_km2']
        }
    
    # Check for unique FIPS codes
    contus_fips = set(normalize_fips(row['FIPS']) for row in contus_data)
    obs_fips = set(normalize_fips(row['FIPS']) for row in obs_data)
    print(f"Unique FIPS in CONTUS dataset (normalized): {len(contus_fips)}")
    print(f"Unique FIPS in observation data (normalized): {len(obs_fips)}")
    
    # Merge the datasets
    print("Merging datasets...")
    merged_data = []
    missing_count = 0
    matched_count = 0
    
    for row in contus_data:
        fips = normalize_fips(row['FIPS'])
        if fips in obs_lookup:
            # Add observation data columns
            row.update(obs_lookup[fips])
            matched_count += 1
        else:
            # Add empty values for missing observation data
            row['area_km2'] = ''
            row['area_ha'] = ''
            row['total_obs_count'] = ''
            row['obs_density_km2'] = ''
            missing_count += 1
        
        merged_data.append(row)
    
    # Check the merge results
    print(f"Merged dataset dimensions: {len(merged_data)} rows, {len(merged_data[0])} columns")
    print(f"Counties with observation data: {matched_count}")
    print(f"Counties without observation data: {missing_count}")
    
    # Save the merged dataset
    output_file = "Finals/CONTUS_counties_with_final_metrics_and_obs_data_FIXED.csv"
    
    # Get fieldnames from the first row
    fieldnames = list(merged_data[0].keys())
    write_dict_to_csv(merged_data, output_file, fieldnames)
    
    print(f"Merged dataset saved to: {output_file}")
    print("Merge completed successfully!")
    
    # Display some statistics
    print("\nSummary of merge:")
    print(f"Total counties in CONTUS dataset: {len(contus_data)}")
    print(f"Counties with observation data: {matched_count}")
    print(f"Counties without observation data: {missing_count}")
    print(f"Match rate: {matched_count/len(contus_data)*100:.1f}%")
    print(f"New columns added: area_km2, area_ha, total_obs_count, obs_density_km2")

if __name__ == "__main__":
    main()
