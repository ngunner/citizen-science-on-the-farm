#!/usr/bin/env python3
# Provenance: copied from `Raw Data/Bridging Gaps Dataset/merge_landcover_data.py` (last modified 2025-09-17) into the
# Citizen Science on the Farm replication package, September 2026.
# Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
"""
Script to merge land cover percentages with the existing merged dataset
Author: AI Assistant
Date: Generated for merging land cover data
"""

import csv
import os

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
    # Read the existing merged dataset with population density
    print("Reading existing merged dataset with population density...")
    merged_data = read_csv_to_dict("Finals/CONTUS_counties_with_final_metrics_and_obs_data_with_pop_density.csv")
    
    # Read the land cover percentages
    print("Reading land cover percentages...")
    landcover_data = read_csv_to_dict("counties_landcover_percentages_optimized.csv")
    
    print(f"Existing dataset: {len(merged_data)} counties, {len(merged_data[0])} columns")
    print(f"Land cover data: {len(landcover_data)} counties, {len(landcover_data[0])} columns")
    
    # Create a lookup dictionary for land cover data by normalized FIPS
    landcover_lookup = {}
    for row in landcover_data:
        fips = normalize_fips(row['FIPS'])
        landcover_lookup[fips] = {
            'PERCENT_DEVELOPED': row['PERCENT_DEVELOPED'],
            'PERCENT_FOREST': row['PERCENT_FOREST'],
            'PERCENT_WATER': row['PERCENT_WATER']
        }
    
    # Check for unique FIPS codes
    merged_fips = set(normalize_fips(row['FIPS']) for row in merged_data)
    landcover_fips = set(normalize_fips(row['FIPS']) for row in landcover_data)
    print(f"Unique FIPS in merged dataset (normalized): {len(merged_fips)}")
    print(f"Unique FIPS in land cover data (normalized): {len(landcover_fips)}")
    
    # Merge the datasets
    print("Merging land cover data...")
    matched_count = 0
    missing_count = 0
    
    for row in merged_data:
        fips = normalize_fips(row['FIPS'])
        if fips in landcover_lookup:
            # Add land cover columns
            row.update(landcover_lookup[fips])
            matched_count += 1
        else:
            # Add empty values for missing land cover data
            row['PERCENT_DEVELOPED'] = ''
            row['PERCENT_FOREST'] = ''
            row['PERCENT_WATER'] = ''
            missing_count += 1
    
    # Check the merge results
    print(f"Counties with land cover data: {matched_count}")
    print(f"Counties without land cover data: {missing_count}")
    
    # Save the updated dataset
    output_file = "Finals/CONTUS_counties_with_final_metrics_and_obs_data_with_pop_density_and_landcover.csv"
    
    # Get fieldnames from the first row
    fieldnames = list(merged_data[0].keys())
    write_dict_to_csv(merged_data, output_file, fieldnames)
    
    print(f"Updated dataset saved to: {output_file}")
    print("Land cover data merged successfully!")
    
    # Display some statistics
    print("\nLand Cover Summary:")
    landcover_values = [row for row in merged_data if row['PERCENT_DEVELOPED'] and row['PERCENT_DEVELOPED'] != '']
    
    if landcover_values:
        developed_values = [float(row['PERCENT_DEVELOPED']) for row in landcover_values]
        forest_values = [float(row['PERCENT_FOREST']) for row in landcover_values]
        water_values = [float(row['PERCENT_WATER']) for row in landcover_values]
        
        print(f"Counties with valid land cover data: {len(landcover_values)}")
        print(f"Mean % developed: {sum(developed_values)/len(developed_values)*100:.2f}%")
        print(f"Mean % forest: {sum(forest_values)/len(forest_values)*100:.2f}%")
        print(f"Mean % water: {sum(water_values)/len(water_values)*100:.2f}%")
    
    # Show some examples
    print(f"\nFirst 5 counties with land cover data:")
    for i, row in enumerate(landcover_values[:5]):
        fips = row['FIPS']
        state = row['STATE']
        county = row['COUNTYNAME']
        developed = float(row['PERCENT_DEVELOPED']) * 100
        forest = float(row['PERCENT_FOREST']) * 100
        water = float(row['PERCENT_WATER']) * 100
        print(f"  {fips} - {state} {county}: {developed:.1f}% developed, {forest:.1f}% forest, {water:.1f}% water")

if __name__ == "__main__":
    main()
