#!/usr/bin/env python
"""
STEP 3 — County-level observational disparity (2023): how widespread is the bias?

Assigns each observation cell (from STEP 2) to its county, computes each county's
observational disparity (%agricultural land / %observations on farmland), and reports the
share of counties where farmland is under-observed (disparity > 1). Reproduces the paper's
disparity-distribution figure.

Inputs : data/obs_cells_2023.parquet      (from STEP 2)
         data/county_ag_area_2023.csv      (per-county farmland area, NLCD 2023)
         data/us_counties.geojson          (county boundaries, FIPS)
Output : outputs/observational_disparity_distribution.png

Run:  python 03_county_disparity_2023.py
Expected: ~78% of counties under-observe farmland (disparity > 1).
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, geopandas as gpd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

cells = pd.read_parquet('data/obs_cells_2023.parquet')
counties = gpd.read_file('data/us_counties.geojson')[['FIPS', 'geometry']]
agc = pd.read_csv('data/county_ag_area_2023.csv', dtype={'FIPS': str})
agc['FIPS'] = agc['FIPS'].str.zfill(5)

# assign each observation cell to a county
pts = gpd.GeoDataFrame(cells, geometry=gpd.points_from_xy(cells.lon, cells.lat), crs=4326)
j = gpd.sjoin(pts, counties, how='inner', predicate='within')
j['obs_on_ag'] = j['count'] * j['ag_frac']
obs = (j.groupby('FIPS').agg(total_obs=('count', 'sum'), obs_on_ag=('obs_on_ag', 'sum'))
       .reset_index())

# combine with per-county farmland area -> disparity
d = obs.merge(agc, on='FIPS', how='inner')
d['pct_obs_on_ag'] = 100 * d['obs_on_ag'] / d['total_obs']
d = d[(d['total_obs'] > 0) & (d['pct_ag_area'] > 0) & (d['pct_obs_on_ag'] > 0)]
d['disparity'] = d['pct_ag_area'] / d['pct_obs_on_ag']

share = 100 * (d['disparity'] > 1).mean()
print(f"Counties analyzed          : {len(d)}")
print(f"Median county disparity    : {d['disparity'].median():.2f}")
print(f"=> {share:.1f}% of counties under-observe farmland (disparity > 1)")
d.to_csv('outputs/county_disparity_2023.csv', index=False)

# distribution figure (log x-axis, threshold at 1) — mirrors the paper's figure
fig, ax = plt.subplots(figsize=(9, 5.5))
disp = d['disparity'].clip(0.02, 100)
bins = np.logspace(np.log10(disp.min()), np.log10(disp.max()), 45)
ax.hist(disp[disp <= 1], bins=bins, color='#81e0a9', edgecolor='k', lw=.3,
        label=f'No disparity (≤1): {100-share:.1f}%')
ax.hist(disp[disp > 1], bins=bins, color='#ed8276', edgecolor='k', lw=.3,
        label=f'Disparity (>1): {share:.1f}%')
ax.axvline(1, ls='--', color='#2c3e50', lw=2, label='threshold (1.0)')
ax.set_xscale('log'); ax.set_xlabel('Observational disparity (%ag land / %obs on ag)')
ax.set_ylabel('Number of counties')
ax.set_title(f'Most CONUS counties under-observe farmland (2023): {share:.0f}% have disparity > 1')
ax.legend(); fig.tight_layout()
fig.savefig('outputs/observational_disparity_distribution.png', dpi=200, bbox_inches='tight')
print("Saved -> outputs/observational_disparity_distribution.png")
