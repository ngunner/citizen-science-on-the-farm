# Provenance: copied from `Figures/GEOM Comparison/create_comprehensive_comparison.py` (last modified 2025-12-07) into the
# Citizen Science on the Farm replication package, September 2026.
# Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
# Manuscript Figure S1.
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

# Set style
plt.rcParams['font.size'] = 9
plt.rcParams['font.family'] = 'sans-serif'
plt.style.use('seaborn-v0_8-whitegrid')

# Read the data
bottom_df = pd.read_csv('../data/top_bottom_30/contus_counties_updated_optimized - BOTTOM30.csv')
top_df = pd.read_csv('../data/top_bottom_30/contus_counties_updated_optimized - TOP30.csv')

# Combine dataframes
bottom_df['Group'] = 'Low-Performing'
top_df['Group'] = 'High-Performing'
combined_df = pd.concat([bottom_df, top_df], ignore_index=True)

# Colors for the groups
colors = ['#efc130', '#6aa74f']  # Low, High

# Function to calculate rank-biserial correlation (effect size for Mann-Whitney U)
def rank_biserial_correlation(u_stat, n1, n2):
    """Calculate rank-biserial correlation from Mann-Whitney U statistic"""
    return 1 - (2 * u_stat) / (n1 * n2)

# Function to get significance asterisks
def get_significance_asterisks(p_value):
    """Return asterisks based on p-value"""
    if p_value < 0.001:
        return '***'
    elif p_value < 0.01:
        return '**'
    elif p_value < 0.05:
        return '*'
    else:
        return 'ns'

# Create figure with multiple subplots arranged vertically for horizontal boxplots
fig, axes = plt.subplots(11, 1, figsize=(10, 14))

# Define variables to plot with their properties
variables = [
    {
        'column': 'GEOMEAN_SCORE',
        'title': 'GEOMEAN Score',
        'xlabel': 'Score',
        'log_scale': False,
        'multiply': 1
    },
    {
        'column': 'PERCENTAGE_OF_AG_LAND_WITHIN_1KM_GBIF_OBS',
        'title': 'Agricultural Land Coverage',
        'xlabel': 'Coverage (%)',
        'log_scale': False,
        'multiply': 100
    },
    {
        'column': 'PERCENTAGE_GBIF_OBS_ON_AG_LAND',
        'title': 'Observations on Ag Land',
        'xlabel': 'Percentage (%)',
        'log_scale': False,
        'multiply': 100
    },
    {
        'column': 'GBIF_OBS_DENSITY_KM2',
        'title': 'Observation Density',
        'xlabel': 'Observations per km² (log scale)',
        'log_scale': True,
        'multiply': 1
    },
    {
        'column': 'POPULATION_DENSITY_2023_KM2',
        'title': 'Population Density',
        'xlabel': 'People per km² (log scale)',
        'log_scale': True,
        'multiply': 1
    },
    {
        'column': 'AREA_KM2',
        'title': 'County Area',
        'xlabel': 'Area (km²)',
        'log_scale': False,
        'multiply': 1
    },
    {
        'column': 'PERCENT_FOREST',
        'title': 'Forest Cover',
        'xlabel': 'Coverage (%)',
        'log_scale': False,
        'multiply': 100
    },
    {
        'column': 'PERCENT_DEVELOPED',
        'title': 'Developed Land',
        'xlabel': 'Coverage (%)',
        'log_scale': False,
        'multiply': 100
    },
    {
        'column': 'MEDIAN_HOUSEHOLD_INCOME_PERCENT_OF_STATE_TOTAL_2022',
        'title': 'Household Income',
        'xlabel': '% of State Median',
        'log_scale': False,
        'multiply': 100
    },
    {
        'column': 'TOTAL_GBIF_OBS_COUNT_2023',
        'title': 'Total GBIF Observations',
        'xlabel': 'Count (log scale)',
        'log_scale': True,
        'multiply': 1
    },
    {
        'column': 'PERCENT_AGRICULTURE',
        'title': 'Agricultural Land',
        'xlabel': 'Coverage (%)',
        'log_scale': False,
        'multiply': 100
    }
]

# Create horizontal boxplots for each variable
for idx, var_info in enumerate(variables):
    ax = axes[idx]
    column = var_info['column']
    
    # Prepare data - note the order: [Low, High]
    box_data = [bottom_df[column] * var_info['multiply'], 
                top_df[column] * var_info['multiply']]
    
    # Create horizontal boxplot
    bp = ax.boxplot(box_data, 
                    labels=['Low', 'High'],
                    patch_artist=True, 
                    widths=0.5,
                    vert=False,  # Make it horizontal
                    medianprops=dict(color='black', linewidth=1.5))
    
    # Color the boxes
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)
    
    # Set log scale if needed
    if var_info['log_scale']:
        ax.set_xscale('log')
    
    # Labels and title
    ax.set_xlabel(var_info['xlabel'], fontsize=9)
    ax.set_ylabel('')
    ax.set_title(var_info['title'], fontsize=10, fontweight='bold', 
                 loc='left', pad=5)
    ax.grid(True, alpha=0.3, axis='x', which='both' if var_info['log_scale'] else 'major')
    
    # Calculate and display statistics
    low_median = np.median(box_data[0])
    high_median = np.median(box_data[1])
    
    # Perform Mann-Whitney U test
    low_data_clean = box_data[0].dropna()
    high_data_clean = box_data[1].dropna()
    
    if len(low_data_clean) > 0 and len(high_data_clean) > 0:
        u_stat, p_value = stats.mannwhitneyu(high_data_clean, low_data_clean, 
                                             alternative='two-sided')
        n1, n2 = len(low_data_clean), len(high_data_clean)
        effect_size = rank_biserial_correlation(u_stat, n1, n2)
        asterisks = get_significance_asterisks(p_value)
    else:
        p_value = np.nan
        effect_size = np.nan
        asterisks = 'ns'
    
    # Store statistical results for summary
    var_info['p_value'] = p_value
    var_info['effect_size'] = effect_size
    var_info['asterisks'] = asterisks
    
    # Format p-value for display
    if p_value < 0.001:
        p_display = 'p<0.001'
    elif p_value < 0.01:
        p_display = f'p={p_value:.3f}'
    else:
        p_display = f'p={p_value:.3f}'
    
    # Add text annotation showing the difference, p-value, and asterisks (inline format)
    if var_info['log_scale']:
        ratio = high_median / low_median if low_median > 0 else float('inf')
        annotation_text = f'{ratio:.1f}× {p_display} {asterisks}'
    else:
        diff = high_median - low_median
        annotation_text = f'Δ{diff:+.1f} {p_display} {asterisks}'
    
    # Position annotation at bottom right of subplot, below the boxplots
    ax.text(0.98, 0.05, annotation_text, 
            transform=ax.transAxes, 
            ha='right', va='bottom',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                     edgecolor='gray', alpha=0.9),
            fontsize=8, fontweight='bold')
    
    # Adjust y-axis labels
    ax.tick_params(axis='y', labelsize=8)
    ax.tick_params(axis='x', labelsize=8)

# Adjust layout with extra padding between subplots to make room for statistics boxes
plt.tight_layout(h_pad=2.5)

# Save figure
plt.savefig('../figures/comprehensive_geomean_comparison.png', dpi=300, bbox_inches='tight')
plt.savefig('../figures/comprehensive_geomean_comparison.pdf', bbox_inches='tight')
print("Comprehensive figure saved as 'comprehensive_geomean_comparison.png' and '.pdf'")

# Print detailed summary statistics
print("\n" + "="*80)
print("COMPREHENSIVE SUMMARY STATISTICS")
print("="*80 + "\n")

for var_info in variables:
    column = var_info['column']
    multiplier = var_info['multiply']
    
    low_data = bottom_df[column] * multiplier
    high_data = top_df[column] * multiplier
    
    print(f"{var_info['title']}:")
    print(f"  Low-Performing:  Median = {low_data.median():>10.2f}, Mean = {low_data.mean():>10.2f}")
    print(f"  High-Performing: Median = {high_data.median():>10.2f}, Mean = {high_data.mean():>10.2f}")
    
    if var_info['log_scale'] and low_data.median() > 0:
        ratio = high_data.median() / low_data.median()
        print(f"  Median Ratio (High/Low): {ratio:.2f}x")
    else:
        diff = high_data.median() - low_data.median()
        print(f"  Median Difference: {diff:+.2f}")
    
    # Print statistical test results
    if 'p_value' in var_info and not np.isnan(var_info['p_value']):
        print(f"  Mann-Whitney U test: p = {var_info['p_value']:.4f} {var_info['asterisks']}")
        print(f"  Effect size (rank-biserial r): {var_info['effect_size']:.3f}")
    print()

print("="*80)
print("STATISTICAL TEST SUMMARY")
print("="*80)
print("Mann-Whitney U test (non-parametric) used to compare distributions.")
print("Significance levels: * p<0.05, ** p<0.01, *** p<0.001, ns = not significant")
print("Effect size interpretation: |r|>0.3 = moderate, |r|>0.5 = large effect")
print("="*80)
print("\nFigure generation complete!")
