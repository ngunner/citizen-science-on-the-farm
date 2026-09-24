#!/usr/bin/env python3
# Provenance: copied from `Raw Data/Bridging Gaps Dataset/add_population_density.py` (last modified 2025-09-17) into the
# Citizen Science on the Farm replication package, September 2026.
# Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
"""
Script to add population density column to the merged dataset
Author: AI Assistant
Date: Generated for adding population density
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

def calculate_population_density(population, area_km2):
    """Calculate population density (people per km²)"""
    try:
        pop = float(population) if population else 0
        area = float(area_km2) if area_km2 else 0
        
        if area > 0:
            return pop / area
        else:
            return 0
    except (ValueError, TypeError):
        return 0

def main():
    # Set working directory to the Bridging Gaps Dataset folder
    # Read the fixed merged dataset
    print("Reading fixed merged dataset...")
    data = read_csv_to_dict("Finals/CONTUS_counties_with_final_metrics_and_obs_data_FIXED.csv")
    
    print(f"Dataset dimensions: {len(data)} rows, {len(data[0])} columns")
    
    # Add population density column
    print("Calculating population density...")
    for row in data:
        population = row['POPULATION_ESTIMATE_2023']
        area_km2 = row['area_km2']
        
        pop_density = calculate_population_density(population, area_km2)
        row['population_density_km2'] = pop_density
    
    # Display some statistics
    pop_densities = [float(row['population_density_km2']) for row in data if row['population_density_km2'] != 0]
    
    if pop_densities:
        print(f"\nPopulation density statistics:")
        print(f"  Count of counties with valid data: {len(pop_densities)}")
        print(f"  Mean population density: {sum(pop_densities)/len(pop_densities):.2f} people/km²")
        print(f"  Median population density: {sorted(pop_densities)[len(pop_densities)//2]:.2f} people/km²")
        print(f"  Min population density: {min(pop_densities):.2f} people/km²")
        print(f"  Max population density: {max(pop_densities):.2f} people/km²")
    
    # Show some examples
    print(f"\nFirst 10 counties with population density:")
    for i, row in enumerate(data[:10]):
        fips = row['FIPS']
        state = row['STATE']
        county = row['COUNTYNAME']
        pop = row['POPULATION_ESTIMATE_2023']
        area = row['area_km2']
        density = row['population_density_km2']
        print(f"  {fips} - {state} {county}: {int(float(pop)):,} people, {float(area):.1f} km², {float(density):.1f} people/km²")
    
    # Save the updated dataset
    output_file = "Finals/CONTUS_counties_with_final_metrics_and_obs_data_with_pop_density.csv"
    
    # Get fieldnames from the first row
    fieldnames = list(data[0].keys())
    write_dict_to_csv(data, output_file, fieldnames)
    
    print(f"\nUpdated dataset saved to: {output_file}")
    print("Population density column added successfully!")

if __name__ == "__main__":
    main()
