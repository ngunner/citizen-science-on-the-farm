#!/usr/bin/env python3
"""
fig2_disparity_distribution.py — Manuscript Figure 2: distribution of county observational disparity.

Revised 2026-09-09 (supersedes fig2_disparity_distribution_2026-07_legacy.py). Two corrections:
  * Counties with farmland but ZERO farmland observations (n = 80) have an undefined (infinite)
    disparity. The county table codes them 0.0, so the legacy figure counted them as "no disparity"
    and — because the log bins start at 0.01 — silently omitted them from the histogram. They are now
    drawn as a separate hatched bar at the right edge, labelled "undefined", and counted as under-observed.
  * The 11 counties with no NLCD farmland at all (disparity 0/0) are excluded; N = 3,097 counties with farmland.
Input : ../data/CONUS_COUNTIES_WITH_METRICS.csv
Output: ../figures/observational_disparity_distribution.png / .pdf
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")
plt.rcParams.update({'font.size': 12, 'axes.labelsize': 14, 'axes.titlesize': 16,
                     'xtick.labelsize': 11, 'ytick.labelsize': 11, 'legend.fontsize': 11, 'figure.dpi': 300})

df = pd.read_csv('../data/CONUS_COUNTIES_WITH_METRICS.csv')
farm = df[df['PERCENT_AGRICULTURE'] > 0].copy()                       # counties that have any farmland
pa, po = farm['PERCENT_AGRICULTURE'], farm['PERCENTAGE_GBIF_OBS_ON_AG_LAND']
finite = (pa / po[po > 0]).dropna()                                    # defined ratios
n_undef = int((po == 0).sum())                                         # farmland, but no observations on it
n_total = len(farm)
n_below = int((finite <= 1).sum()); n_above = int((finite > 1).sum())
pct_below, pct_above, pct_undef = 100 * n_below / n_total, 100 * n_above / n_total, 100 * n_undef / n_total
pct_under = pct_above + pct_undef

print(f"counties with farmland: {n_total}  (excluded, no farmland: {len(df) - n_total})")
print(f"  disparity <= 1 : {n_below} ({pct_below:.1f}%)")
print(f"  disparity  > 1 : {n_above} ({pct_above:.1f}%)")
print(f"  undefined (0 farmland obs.): {n_undef} ({pct_undef:.1f}%)")
print(f"  under-observed total: {n_above + n_undef} ({pct_under:.1f}%)")

fig, ax = plt.subplots(figsize=(10, 6))
bins = np.logspace(np.log10(finite.min()), np.log10(finite.max()) + 0.02, 50)
ax.hist(finite[finite <= 1], bins=bins, color='#81e0a9', edgecolor='black', linewidth=0.3,
        label=f'Disparity ≤ 1 (not under-observed): {n_below} counties ({pct_below:.1f}%)')
ax.hist(finite[finite > 1], bins=bins, color='#ed8276', edgecolor='black', linewidth=0.3,
        label=f'Disparity > 1 (under-observed): {n_above} counties ({pct_above:.1f}%)')

# undefined-ratio counties as a detached bar beyond the finite range
x_undef = finite.max() * 6
ax.bar(x_undef, n_undef, width=x_undef * 0.7, color='#ed8276', edgecolor='black', linewidth=0.6,
       hatch='///', label=f'Undefined — farmland but no farmland observations: {n_undef} counties ({pct_undef:.1f}%)')
ax.text(x_undef, n_undef + 4, f'{n_undef}', ha='center', va='bottom', fontsize=10, fontweight='bold')

ax.axvline(x=1, color='#2c3e50', linestyle='--', linewidth=2.5, zorder=10, alpha=0.8, label='Parity (disparity = 1.0)')
ax.set_xscale('log')
ax.set_xlim(finite.min() * 0.8, x_undef * 2.2)
ticks = [0.01, 0.1, 1, 10, 100, 1000]
ax.set_xticks(ticks + [x_undef]); ax.set_xticklabels([str(t) if t < 1 else f'{t:g}' for t in ticks] + ['undefined\n(∞)'])
ax.set_xlabel('Observational Disparity (log scale)', fontweight='bold')
ax.set_ylabel('Number of Counties', fontweight='bold')
ax.set_title('Distribution of Observational Disparity Across CONUS Counties with Farmland', fontweight='bold', pad=20)
ax.legend(loc='upper right', frameon=True, fancybox=True, shadow=True, fontsize=10)
ax.text(0.02, 0.98, f'{pct_under:.1f}% of counties with farmland\nare under-observed\n(N = {n_total:,})',
        transform=ax.transAxes, fontsize=13, va='top', ha='left', fontweight='bold', color='#333333',
        bbox=dict(boxstyle='round', facecolor='#fff3cd', alpha=0.9, edgecolor='#856404', linewidth=2))
ax.set_ylim(0, 300)                                                    # headroom so the legend clears the tallest bars
ax.grid(True, alpha=0.3, linewidth=0.5); ax.set_axisbelow(True)
plt.tight_layout()
plt.savefig('../figures/observational_disparity_distribution.png', dpi=300, bbox_inches='tight')
plt.savefig('../figures/observational_disparity_distribution.pdf', bbox_inches='tight')
print("saved ../figures/observational_disparity_distribution.png/.pdf")
