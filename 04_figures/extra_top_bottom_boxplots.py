# Provenance: copied from `Figures/GEOM Comparison/create_comparison_figure.py` (last modified 2025-10-19) into the
# Citizen Science on the Farm replication package, September 2026.
# Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
# Earlier three-panel version of the S1 comparison (not in the manuscript).
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Set style
plt.rcParams['font.size'] = 11
plt.rcParams['font.family'] = 'sans-serif'
plt.style.use('seaborn-v0_8-whitegrid')

# Read the data
bottom_df = pd.read_csv('../data/top_bottom_30/contus_counties_updated_optimized - BOTTOM30.csv')
top_df = pd.read_csv('../data/top_bottom_30/contus_counties_updated_optimized - TOP30.csv')

# Combine dataframes
bottom_df['Group'] = 'Low-Performing'
top_df['Group'] = 'High-Performing'
combined_df = pd.concat([bottom_df, top_df], ignore_index=True)

# Create figure with three subplots
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Colors for the groups
colors = {'Low-Performing': '#efc130', 'High-Performing': '#6aa74f'}

# 1. Population Density (log scale)
ax1 = axes[0]
box_data_pop = [bottom_df['POPULATION_DENSITY_2023_KM2'], 
                 top_df['POPULATION_DENSITY_2023_KM2']]
bp1 = ax1.boxplot(box_data_pop, labels=['Low-Performing', 'High-Performing'],
                   patch_artist=True, widths=0.6)
for patch, color in zip(bp1['boxes'], [colors['Low-Performing'], colors['High-Performing']]):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
ax1.set_yscale('log')
ax1.set_ylabel('Population Density (km⁻²)', fontsize=12, fontweight='bold')
ax1.set_title('Population Density', fontsize=13, fontweight='bold', pad=10)
ax1.tick_params(axis='x', rotation=15)
ax1.grid(True, alpha=0.3, which='both')

# 2. Observation Density (log scale)
ax2 = axes[1]
box_data_obs = [bottom_df['GBIF_OBS_DENSITY_KM2'], 
                top_df['GBIF_OBS_DENSITY_KM2']]
bp2 = ax2.boxplot(box_data_obs, labels=['Low-Performing', 'High-Performing'],
                   patch_artist=True, widths=0.6)
for patch, color in zip(bp2['boxes'], [colors['Low-Performing'], colors['High-Performing']]):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
ax2.set_yscale('log')
ax2.set_ylabel('Observation Density (km⁻²)', fontsize=12, fontweight='bold')
ax2.set_title('GBIF Observation Density', fontsize=13, fontweight='bold', pad=10)
ax2.tick_params(axis='x', rotation=15)
ax2.grid(True, alpha=0.3, which='both')

# 3. Forest Cover Percentage (linear scale)
ax3 = axes[2]
# Convert to percentage (multiply by 100)
box_data_forest = [bottom_df['PERCENT_FOREST'] * 100, 
                   top_df['PERCENT_FOREST'] * 100]
bp3 = ax3.boxplot(box_data_forest, labels=['Low-Performing', 'High-Performing'],
                   patch_artist=True, widths=0.6)
for patch, color in zip(bp3['boxes'], [colors['Low-Performing'], colors['High-Performing']]):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
ax3.set_ylabel('Forest Cover (%)', fontsize=12, fontweight='bold')
ax3.set_title('Forest Cover', fontsize=13, fontweight='bold', pad=10)
ax3.tick_params(axis='x', rotation=15)
ax3.grid(True, alpha=0.3, axis='y')

# Adjust layout
plt.tight_layout()

# Save figure
plt.savefig('../figures/geomean_comparison_boxplots.png', dpi=300, bbox_inches='tight')
plt.savefig('../figures/geomean_comparison_boxplots.pdf', bbox_inches='tight')
print("Figure saved as 'geomean_comparison_boxplots.png' and 'geomean_comparison_boxplots.pdf'")

# Print summary statistics
print("\n=== Summary Statistics ===\n")
print("Population Density (km⁻²):")
print(f"  Low-Performing: Median = {bottom_df['POPULATION_DENSITY_2023_KM2'].median():.2f}, "
      f"Mean = {bottom_df['POPULATION_DENSITY_2023_KM2'].mean():.2f}")
print(f"  High-Performing: Median = {top_df['POPULATION_DENSITY_2023_KM2'].median():.2f}, "
      f"Mean = {top_df['POPULATION_DENSITY_2023_KM2'].mean():.2f}")

print("\nObservation Density (km⁻²):")
print(f"  Low-Performing: Median = {bottom_df['GBIF_OBS_DENSITY_KM2'].median():.2f}, "
      f"Mean = {bottom_df['GBIF_OBS_DENSITY_KM2'].mean():.2f}")
print(f"  High-Performing: Median = {top_df['GBIF_OBS_DENSITY_KM2'].median():.2f}, "
      f"Mean = {top_df['GBIF_OBS_DENSITY_KM2'].mean():.2f}")

print("\nForest Cover (%):")
print(f"  Low-Performing: Median = {bottom_df['PERCENT_FOREST'].median()*100:.2f}%, "
      f"Mean = {bottom_df['PERCENT_FOREST'].mean()*100:.2f}%")
print(f"  High-Performing: Median = {top_df['PERCENT_FOREST'].median()*100:.2f}%, "
      f"Mean = {top_df['PERCENT_FOREST'].mean()*100:.2f}%")

plt.show()

