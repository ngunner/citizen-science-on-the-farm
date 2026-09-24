# Provenance: copied from `Figures/GEOM Comparison/create_county_spotlight.py` (last modified 2025-10-19) into the
# Citizen Science on the Farm replication package, September 2026.
# Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
# Manuscript Figure S2 (Jessamine, KY vs Boyd, NE).
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

# Set style
plt.rcParams['font.size'] = 10
plt.rcParams['font.family'] = 'sans-serif'

# Read the data
bottom_df = pd.read_csv('../data/top_bottom_30/contus_counties_updated_optimized - BOTTOM30.csv')
top_df = pd.read_csv('../data/top_bottom_30/contus_counties_updated_optimized - TOP30.csv')

# Get the top and bottom performers
top_county = top_df.nlargest(1, 'GEOMEAN_SCORE').iloc[0]
bottom_county = bottom_df.nsmallest(1, 'GEOMEAN_SCORE').iloc[0]

# Colors
color_top = '#6aa74f'
color_bottom = '#efc130'

# Create figure with better spacing
fig = plt.figure(figsize=(18, 11))
gs = fig.add_gridspec(3, 3, hspace=0.50, wspace=0.35, top=0.88, bottom=0.06, left=0.08, right=0.96)

# Title with more space
fig.suptitle(f'County Spotlight: Best vs. Worst Performers\n{top_county["COUNTYNAME"]} County, {top_county["STATE"]} (GEOMEAN = {top_county["GEOMEAN_SCORE"]:.3f}) vs. {bottom_county["COUNTYNAME"]} County, {bottom_county["STATE"]} (GEOMEAN = {bottom_county["GEOMEAN_SCORE"]:.3f})', 
             fontsize=15, fontweight='bold', y=0.98)

# ============ Row 1: Core Performance Metrics ============
# Panel 1a: GEOMEAN and Coverage metrics (percentages)
ax1 = fig.add_subplot(gs[0, 0])
metrics1 = [
    'GEOMEAN\nScore (%)',
    'Ag Land\nCoverage (%)',
    'Obs on\nAg Land (%)',
]
columns1 = [
    ('GEOMEAN_SCORE', 100),
    ('PERCENTAGE_OF_AG_LAND_WITHIN_1KM_GBIF_OBS', 100),
    ('PERCENTAGE_GBIF_OBS_ON_AG_LAND', 100),
]

x = np.arange(len(metrics1))
width = 0.35

top_vals1 = [top_county[col[0]] * col[1] for col in columns1]
bottom_vals1 = [bottom_county[col[0]] * col[1] for col in columns1]

bars1 = ax1.bar(x - width/2, bottom_vals1, width, label=f'{bottom_county["COUNTYNAME"]}, {bottom_county["STATE"]}',
               color=color_bottom, alpha=0.85, edgecolor='black', linewidth=0.5)
bars2 = ax1.bar(x + width/2, top_vals1, width, label=f'{top_county["COUNTYNAME"]}, {top_county["STATE"]}',
               color=color_top, alpha=0.85, edgecolor='black', linewidth=0.5)

ax1.set_ylabel('Percentage (%)', fontsize=11, fontweight='bold')
ax1.set_title('Performance & Coverage Metrics', fontsize=12, fontweight='bold', pad=12)
ax1.set_xticks(x)
ax1.set_xticklabels(metrics1, fontsize=10)
ax1.legend(loc='upper right', fontsize=8, framealpha=0.9)
ax1.grid(axis='y', alpha=0.3)
ax1.set_ylim(0, max(top_vals1 + bottom_vals1) * 1.15)

# Add value labels
for bar, val in zip(bars1, bottom_vals1):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
            f'{val:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

for bar, val in zip(bars2, top_vals1):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
            f'{val:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

# Panel 1b: Observation Counts
ax2 = fig.add_subplot(gs[0, 1])
metrics2 = ['Total GBIF\nObservations', 'Ag Land\nObservations']
columns2 = ['TOTAL_GBIF_OBS_COUNT_2023', 'GBIF_AG_OBS_COUNT_2023']

x = np.arange(len(metrics2))
top_vals2 = [top_county[col] for col in columns2]
bottom_vals2 = [bottom_county[col] for col in columns2]

bars1 = ax2.bar(x - width/2, bottom_vals2, width, label=f'{bottom_county["COUNTYNAME"]}, {bottom_county["STATE"]}',
               color=color_bottom, alpha=0.85, edgecolor='black', linewidth=0.5)
bars2 = ax2.bar(x + width/2, top_vals2, width, label=f'{top_county["COUNTYNAME"]}, {top_county["STATE"]}',
               color=color_top, alpha=0.85, edgecolor='black', linewidth=0.5)

ax2.set_ylabel('Count', fontsize=11, fontweight='bold')
ax2.set_title('Observation Counts', fontsize=12, fontweight='bold', pad=12)
ax2.set_xticks(x)
ax2.set_xticklabels(metrics2, fontsize=10)
ax2.legend(loc='upper right', fontsize=8, framealpha=0.9)
ax2.grid(axis='y', alpha=0.3)
ax2.set_ylim(0, max(top_vals2 + bottom_vals2) * 1.15)

for bar, val in zip(bars1, bottom_vals2):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(val):,}', ha='center', va='bottom', fontsize=9, fontweight='bold')

for bar, val in zip(bars2, top_vals2):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(val):,}', ha='center', va='bottom', fontsize=9, fontweight='bold')

# Panel 1c: Density Metrics (log scale)
ax3 = fig.add_subplot(gs[0, 2])
metrics3 = ['Population\nDensity', 'Observation\nDensity']
columns3 = [
    ('POPULATION_DENSITY_2023_KM2', 1),
    ('GBIF_OBS_DENSITY_KM2', 1),
]

x = np.arange(len(metrics3))
top_vals3 = [top_county[col[0]] * col[1] for col in columns3]
bottom_vals3 = [bottom_county[col[0]] * col[1] for col in columns3]

bars1 = ax3.bar(x - width/2, bottom_vals3, width, label=f'{bottom_county["COUNTYNAME"]}, {bottom_county["STATE"]}',
               color=color_bottom, alpha=0.85, edgecolor='black', linewidth=0.5)
bars2 = ax3.bar(x + width/2, top_vals3, width, label=f'{top_county["COUNTYNAME"]}, {top_county["STATE"]}',
               color=color_top, alpha=0.85, edgecolor='black', linewidth=0.5)

ax3.set_ylabel('Density (log scale)', fontsize=11, fontweight='bold')
ax3.set_yscale('log')
ax3.set_title('Density Comparisons', fontsize=12, fontweight='bold', pad=12)
ax3.set_xticks(x)
ax3.set_xticklabels(metrics3, fontsize=10)
ax3.legend(loc='upper right', fontsize=8, framealpha=0.9)
ax3.grid(axis='y', alpha=0.3, which='both')
ax3.set_ylim(bottom=min([v for v in bottom_vals3 + top_vals3 if v > 0]) * 0.5, 
             top=max(top_vals3 + bottom_vals3) * 3)

for bar, val in zip(bars1, bottom_vals3):
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height * 1.5,
            f'{val:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

for bar, val in zip(bars2, top_vals3):
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height * 1.3,
            f'{val:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

# ============ Row 2: Land Use Percentages ============
ax4 = fig.add_subplot(gs[1, :])
metrics4 = ['Agricultural\nLand', 'Forest\nCover', 'Developed\nLand']
columns4 = [
    ('PERCENT_AGRICULTURE', 100),
    ('PERCENT_FOREST', 100),
    ('PERCENT_DEVELOPED', 100),
]

x = np.arange(len(metrics4))
top_vals4 = [top_county[col[0]] * col[1] for col in columns4]
bottom_vals4 = [bottom_county[col[0]] * col[1] for col in columns4]

bars1 = ax4.bar(x - width/2, bottom_vals4, width, label=f'{bottom_county["COUNTYNAME"]}, {bottom_county["STATE"]}',
               color=color_bottom, alpha=0.85, edgecolor='black', linewidth=0.5)
bars2 = ax4.bar(x + width/2, top_vals4, width, label=f'{top_county["COUNTYNAME"]}, {top_county["STATE"]}',
               color=color_top, alpha=0.85, edgecolor='black', linewidth=0.5)

ax4.set_ylabel('Percentage (%)', fontsize=11, fontweight='bold')
ax4.set_title('Land Use Composition', fontsize=12, fontweight='bold', pad=12)
ax4.set_xticks(x)
ax4.set_xticklabels(metrics4, fontsize=11)
ax4.legend(loc='upper right', fontsize=9, framealpha=0.9)
ax4.grid(axis='y', alpha=0.3)
ax4.set_ylim(0, max(top_vals4 + bottom_vals4) * 1.15)

for bar, val in zip(bars1, bottom_vals4):
    height = bar.get_height()
    ax4.text(bar.get_x() + bar.get_width()/2., height + 0.5,
            f'{val:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

for bar, val in zip(bars2, top_vals4):
    height = bar.get_height()
    ax4.text(bar.get_x() + bar.get_width()/2., height + 0.5,
            f'{val:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

# ============ Row 3: Area Metrics (km²) ============
ax5 = fig.add_subplot(gs[2, 0])
metrics5 = ['Total County\nArea', 'Agricultural\nArea', 'Covered Ag\nArea']
columns5 = [
    ('AREA_KM2', 1),
    ('AG_AREA_KM2', 1),
    ('COVERED_AG_AREA_KM2', 1),
]

x = np.arange(len(metrics5))
top_vals5 = [top_county[col[0]] * col[1] for col in columns5]
bottom_vals5 = [bottom_county[col[0]] * col[1] for col in columns5]

bars1 = ax5.bar(x - width/2, bottom_vals5, width, label=f'{bottom_county["COUNTYNAME"]}, {bottom_county["STATE"]}',
               color=color_bottom, alpha=0.85, edgecolor='black', linewidth=0.5)
bars2 = ax5.bar(x + width/2, top_vals5, width, label=f'{top_county["COUNTYNAME"]}, {top_county["STATE"]}',
               color=color_top, alpha=0.85, edgecolor='black', linewidth=0.5)

ax5.set_ylabel('Area (km²)', fontsize=11, fontweight='bold')
ax5.set_title('Spatial Extent', fontsize=12, fontweight='bold', pad=12)
ax5.set_xticks(x)
ax5.set_xticklabels(metrics5, fontsize=9)
ax5.legend(loc='upper right', fontsize=8, framealpha=0.9)
ax5.grid(axis='y', alpha=0.3)
ax5.set_ylim(0, max(top_vals5 + bottom_vals5) * 1.15)

for bar, val in zip(bars1, bottom_vals5):
    height = bar.get_height()
    ax5.text(bar.get_x() + bar.get_width()/2., height,
            f'{val:.0f}', ha='center', va='bottom', fontsize=8, fontweight='bold')

for bar, val in zip(bars2, top_vals5):
    height = bar.get_height()
    ax5.text(bar.get_x() + bar.get_width()/2., height,
            f'{val:.0f}', ha='center', va='bottom', fontsize=8, fontweight='bold')

# ============ Row 3: Population Metrics ============
ax6 = fig.add_subplot(gs[2, 1])
metrics6 = ['Total\nPopulation', 'Population\nDensity']
columns6 = [
    ('POPULATION_ESTIMATE_2023', 1),
    ('POPULATION_DENSITY_2023_KM2', 1),
]

x = np.arange(len(metrics6))
top_vals6 = [top_county[col[0]] * col[1] for col in columns6]
bottom_vals6 = [bottom_county[col[0]] * col[1] for col in columns6]

# Need to normalize these since they're on different scales
# Show them as percentage of max
max_vals6 = [max(t, b) for t, b in zip(top_vals6, bottom_vals6)]
top_norm6 = [t/m * 100 for t, m in zip(top_vals6, max_vals6)]
bottom_norm6 = [b/m * 100 for b, m in zip(bottom_vals6, max_vals6)]

bars1 = ax6.bar(x - width/2, bottom_norm6, width, label=f'{bottom_county["COUNTYNAME"]}, {bottom_county["STATE"]}',
               color=color_bottom, alpha=0.85, edgecolor='black', linewidth=0.5)
bars2 = ax6.bar(x + width/2, top_norm6, width, label=f'{top_county["COUNTYNAME"]}, {top_county["STATE"]}',
               color=color_top, alpha=0.85, edgecolor='black', linewidth=0.5)

ax6.set_ylabel('Relative Value (% of max)', fontsize=11, fontweight='bold')
ax6.set_title('Population Comparison (Normalized)', fontsize=12, fontweight='bold', pad=12)
ax6.set_xticks(x)
ax6.set_xticklabels(metrics6, fontsize=10)
ax6.legend(loc='upper right', fontsize=8, framealpha=0.9)
ax6.grid(axis='y', alpha=0.3)
ax6.set_ylim(0, 140)
# Set custom y-axis ticks to only show up to 100
ax6.set_yticks([0, 20, 40, 60, 80, 100])

# Add actual value labels
for i, (bar, val, actual) in enumerate(zip(bars1, bottom_norm6, bottom_vals6)):
    height = bar.get_height()
    if i == 0:
        ax6.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{int(actual):,}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    else:
        ax6.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{actual:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

for i, (bar, val, actual) in enumerate(zip(bars2, top_norm6, top_vals6)):
    height = bar.get_height()
    if i == 0:
        ax6.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{int(actual):,}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    else:
        ax6.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{actual:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

# ============ Row 3: Socioeconomic ============
ax7 = fig.add_subplot(gs[2, 2])
metrics7 = ['Median HH Income\n(% of State)', 'Adults w/\nBachelor\'s (%)', 'Poverty\nRate (%)']
columns7 = [
    ('MEDIAN_HOUSEHOLD_INCOME_PERCENT_OF_STATE_TOTAL_2022', 100),
    ('PERCENT_ADULTS_BACHELORS_DEGREE_2023', 100),
    ('PERCENT_POVERTY_2023', 100),
]

x = np.arange(len(metrics7))
top_vals7 = [top_county[col[0]] * col[1] for col in columns7]
bottom_vals7 = [bottom_county[col[0]] * col[1] for col in columns7]

bars1 = ax7.bar(x - width/2, bottom_vals7, width, label=f'{bottom_county["COUNTYNAME"]}, {bottom_county["STATE"]}',
               color=color_bottom, alpha=0.85, edgecolor='black', linewidth=0.5)
bars2 = ax7.bar(x + width/2, top_vals7, width, label=f'{top_county["COUNTYNAME"]}, {top_county["STATE"]}',
               color=color_top, alpha=0.85, edgecolor='black', linewidth=0.5)

ax7.set_ylabel('Percentage (%)', fontsize=11, fontweight='bold')
ax7.set_title('Socioeconomic Indicators', fontsize=12, fontweight='bold', pad=12)
ax7.set_xticks(x)
ax7.set_xticklabels(metrics7, fontsize=9)
ax7.legend(loc='upper right', fontsize=8, framealpha=0.9)
ax7.grid(axis='y', alpha=0.3)
ax7.set_ylim(0, max(top_vals7 + bottom_vals7) * 1.15)

for bar, val in zip(bars1, bottom_vals7):
    height = bar.get_height()
    ax7.text(bar.get_x() + bar.get_width()/2., height + 1,
            f'{val:.1f}%', ha='center', va='bottom', fontsize=8, fontweight='bold')

for bar, val in zip(bars2, top_vals7):
    height = bar.get_height()
    ax7.text(bar.get_x() + bar.get_width()/2., height + 1,
            f'{val:.1f}%', ha='center', va='bottom', fontsize=8, fontweight='bold')

# Save figure
plt.savefig('../figures/county_spotlight_comparison.png', dpi=300, bbox_inches='tight')
plt.savefig('../figures/county_spotlight_comparison.pdf', bbox_inches='tight')
print(f"\n✓ County Spotlight Figure saved!")
print(f"\nComparing:")
print(f"  TOP:    {top_county['COUNTYNAME']} County, {top_county['STATE']} (GEOMEAN = {top_county['GEOMEAN_SCORE']:.3f})")
print(f"  BOTTOM: {bottom_county['COUNTYNAME']} County, {bottom_county['STATE']} (GEOMEAN = {bottom_county['GEOMEAN_SCORE']:.3f})")
print(f"\nFiles created: county_spotlight_comparison.png and .pdf")
