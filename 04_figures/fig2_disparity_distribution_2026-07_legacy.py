# Provenance: copied from `Figures/Disparity Plot/create_disparity_plot.py` (last modified 2026-01-15) into the
# Citizen Science on the Farm replication package, September 2026.
# Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
# Manuscript Figure 2.
"""
Create a publication-quality visualization of OBSERVATIONAL_DISPARITY
showing that the majority of counties have a disparity (values > 1).
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Set style for publication-quality figures
sns.set_style("whitegrid")
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['xtick.labelsize'] = 11
plt.rcParams['ytick.labelsize'] = 11
plt.rcParams['legend.fontsize'] = 11
plt.rcParams['figure.dpi'] = 300

# Load data
print("Loading data...")
df = pd.read_csv('../data/CONUS_COUNTIES_WITH_METRICS.csv')

# Handle any missing values (though we know there are none)
disparity = df['OBSERVATIONAL_DISPARITY'].dropna()

# Calculate summary statistics
total_counties = len(disparity)
counties_with_disparity = (disparity > 1).sum()
percentage_with_disparity = (counties_with_disparity / total_counties) * 100

print(f"Total counties: {total_counties}")
print(f"Counties with disparity > 1: {counties_with_disparity} ({percentage_with_disparity:.1f}%)")

# Handle zero values for log scale (add small epsilon or filter)
# We'll use log scale, so need to handle zeros
disparity_log = np.log10(disparity + 1)  # Add 1 to handle zeros, then log10

# Create figure
fig, ax = plt.subplots(figsize=(10, 6))

# Separate data for above and below threshold
disparity_above = disparity[disparity > 1]
disparity_below = disparity[disparity <= 1]

# Create histogram with log scale
# Use log bins for better visualization
bins = np.logspace(np.log10(disparity.min() + 0.01), np.log10(disparity.max() + 1), 50)

# Plot histogram with color coding
n_below, bins_below, patches_below = ax.hist(
    disparity_below, bins=bins, alpha=1, color='#81e0a9', 
    label=f'No Disparity (≤1): {len(disparity_below)} counties ({100-percentage_with_disparity:.1f}%)',
    edgecolor='black', linewidth=0.3
)

n_above, bins_above, patches_above = ax.hist(
    disparity_above, bins=bins, alpha=1, color='#ed8276',
    label=f'Disparity (>1): {len(disparity_above)} counties ({percentage_with_disparity:.1f}%)',
    edgecolor='black', linewidth=0.3
)

# Add vertical line at threshold = 1
ax.axvline(x=1, color='#2c3e50', linestyle='--', linewidth=2.5, 
           label='Disparity Threshold (1.0)', zorder=10, alpha=0.8)

# Set x-axis to log scale
ax.set_xscale('log')

# Add labels and title
ax.set_xlabel('Observational Disparity', fontweight='bold')
ax.set_ylabel('Number of Counties', fontweight='bold')
ax.set_title('Distribution of Observational Disparity Across US Counties', 
             fontweight='bold', pad=20)

# Add legend
ax.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)

# Add text annotation highlighting the majority
ax.text(0.02, 0.98, 
        f'{percentage_with_disparity:.1f}% of counties\nhave observational disparity',
        transform=ax.transAxes,
        fontsize=13,
        verticalalignment='top',
        horizontalalignment='left',
        bbox=dict(boxstyle='round', facecolor='#fff3cd', alpha=0.9, edgecolor='#856404', linewidth=2),
        fontweight='bold',
        color='#333333')

# Add grid for better readability
ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
ax.set_axisbelow(True)

# Tight layout
plt.tight_layout()

# Save figure in multiple formats
print("Saving figures...")
plt.savefig('../figures/observational_disparity_distribution.png', dpi=300, bbox_inches='tight')
plt.savefig('../figures/observational_disparity_distribution.pdf', bbox_inches='tight')
print("Figures saved as:")
print("  - observational_disparity_distribution.png")
print("  - observational_disparity_distribution.pdf")

# Show the plot (comment out if running in headless environment)
# plt.show()

print("\nVisualization complete!")

