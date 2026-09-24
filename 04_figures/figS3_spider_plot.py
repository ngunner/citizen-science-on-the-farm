#!/usr/bin/env python3
"""
figS3_spider_plot.py — RECONSTRUCTION of manuscript Figure S3 (Top-30 vs Bottom-30 OEI county profiles).

Added at packaging (September 2026). The original spider plot was produced interactively and
no script survived, so this file re-creates it from the shipped data
(`../data/top_bottom_30/counties_enriched_with_usda_data.csv`, produced by fetch_usda_nass_acres.py).
Six axes, each min–max scaled to 0–1 across the 60 counties; heavy line = group mean, faint lines =
individual counties. Axis choices follow the Figure S3 caption (Development, Nature/Forest, Pop
Density (log), Industrial Monoculture = corn acres harvested) plus observation density (log) and
farmland coverage; confirm against the published figure before reuse.
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(HERE, "..", "data", "top_bottom_30", "counties_enriched_with_usda_data.csv"))

axes_spec = [  # (label, column, log?)
    ("Development\n(% developed)", "PERCENT_DEVELOPED", False),
    ("Nature / Forest\n(% forest)", "PERCENT_FOREST", False),
    ("Pop. density\n(log)", "POPULATION_DENSITY_2023_KM2", True),
    ("Obs. density\n(log)", "GBIF_OBS_DENSITY_KM2", True),
    ("Farmland within\n1 km of obs.", "PERCENTAGE_OF_AG_LAND_WITHIN_1KM_GBIF_OBS", False),
    ("Industrial monoculture\n(corn acres, log)", "CORN_ACRES", True),
]
X = np.column_stack([np.log10(df[c] + 1) if lg else df[c].astype(float) for _, c, lg in axes_spec])
X = (X - X.min(0)) / (X.max(0) - X.min(0))
labels = [a[0] for a in axes_spec]
ang = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)
ang_c = np.concatenate([ang, ang[:1]])

fig, ax = plt.subplots(figsize=(7.5, 7.5), subplot_kw=dict(polar=True))
colors = {"Top": "#6aa74f", "Bottom": "#d9534f"}
names = {"Top": "Top 30 OEI (peri-urban / observed)", "Bottom": "Bottom 30 OEI (industrial / neglected)"}
for grp in ["Top", "Bottom"]:
    sel = (df["RANK"] == grp).values
    for row in X[sel]:
        ax.plot(ang_c, np.concatenate([row, row[:1]]), color=colors[grp], alpha=0.12, lw=0.8)
    mean = X[sel].mean(0)
    ax.plot(ang_c, np.concatenate([mean, mean[:1]]), color=colors[grp], lw=3, label=names[grp])
    ax.fill(ang_c, np.concatenate([mean, mean[:1]]), color=colors[grp], alpha=0.10)
ax.set_xticks(ang); ax.set_xticklabels(labels, fontsize=9)
ax.set_yticks([0.25, 0.5, 0.75, 1.0]); ax.set_yticklabels(["", "", "", ""]); ax.set_ylim(0, 1)
ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.12), fontsize=9, frameon=False)
ax.set_title("Top 30 vs Bottom 30 OEI counties — multivariable profiles\n(min–max scaled across the 60 counties)", fontsize=11, pad=24)
out = os.path.join(HERE, "..", "figures", "figS3_spider_plot_reconstructed.png")
fig.savefig(out, dpi=200, bbox_inches="tight")
print("wrote", out)
