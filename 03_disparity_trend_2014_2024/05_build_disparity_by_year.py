#!/usr/bin/env python
"""
STEP 5 — Build the decade series data/conus_disparity_by_year.csv (2015-2024).

This is the script that GENERATES the table STEP 6 plots. It reproduces, for every year,
exactly what STEPS 1-3 do for 2023 — but reads two pre-computed per-county panels so it
runs in seconds instead of re-harvesting all of CONUS ten times. (To rebuild those two
panels from scratch in the cloud, see generators/ — that is the slow, full-provenance path.)

Inputs (in data/):
  county_landcover_wide.csv   per-county ag_<year>/land_<year>/ALAND from USGS Annual NLCD
                              (classes 81+82), one row per CONUS county.
                              -> produced by generators/export_county_landcover_panel.py
  county_obs_panel_long.csv   per-county per-year total_obs + obs_on_ag from the GBIF
                              Maps-API x NLCD-ag overlay (same overlay as STEP 2, zoom 9).
                              -> produced by generators/build_county_obs_panel.py

Metric definitions (identical to STEPS 1-3, applied per year):
  pct_ag_area    = 100 * sum(ag_<year>) / sum(ALAND)           [CONUS aggregate]
  pct_obs_on_ag  = 100 * sum(obs_on_ag) / sum(total_obs)        [CONUS aggregate]
  conus_disparity= pct_ag_area / pct_obs_on_ag                  (>1 => farmland under-observed)
  pct_counties_underobserved = share of counties with per-county disparity > 1
  total_obs_millions = sum(total_obs) / 1e6

Output: data/conus_disparity_by_year.csv   (year, pct_ag_area, pct_obs_on_ag,
        conus_disparity, pct_counties_underobserved, total_obs_millions)

Run:  python 05_build_disparity_by_year.py
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

YEARS = list(range(2015, 2025))

# --- per-county land cover (wide -> long): ag & land area per year ---
lc = pd.read_csv('data/county_landcover_wide.csv')
lc['FIPS'] = lc['GEOID'].astype(str).str.zfill(5)
lc_long = pd.concat([
    pd.DataFrame({'FIPS': lc['FIPS'], 'year': y,
                  'ag_km2': lc[f'ag_{y}'] / 1e6,
                  'aland_km2': lc['ALAND'] / 1e6})
    for y in YEARS], ignore_index=True)

# --- per-county observations (already long): total_obs & obs_on_ag per year ---
obs = pd.read_csv('data/county_obs_panel_long.csv', dtype={'FIPS': str})
obs['FIPS'] = obs['FIPS'].str.zfill(5)

# --- merge to one county x year panel; counties with no obs that year -> 0 ---
m = lc_long.merge(obs[['FIPS', 'year', 'total_obs', 'obs_on_ag']],
                  on=['FIPS', 'year'], how='left')
m['total_obs'] = m['total_obs'].fillna(0)
m['obs_on_ag'] = m['obs_on_ag'].fillna(0)

# per-county metrics (used for the "share of counties under-observed" statistic)
m['pct_ag_area']   = 100 * m['ag_km2'] / m['aland_km2']
m['pct_obs_on_ag'] = np.where(m['total_obs'] > 0, 100 * m['obs_on_ag'] / m['total_obs'], np.nan)
m['disparity']     = np.where((m['pct_obs_on_ag'] > 0) & (m['pct_ag_area'] > 0),
                              m['pct_ag_area'] / m['pct_obs_on_ag'], np.nan)

# --- CONUS-level summary, one row per year ---
rows = []
for y in YEARS:
    d = m[m['year'] == y]
    du = d[d['disparity'].notna()]                       # counties with observations
    pa = 100 * d['ag_km2'].sum() / d['aland_km2'].sum()
    po = 100 * d['obs_on_ag'].sum() / d['total_obs'].sum()
    rows.append({
        'year': y,
        'pct_ag_area': round(pa, 2),
        'pct_obs_on_ag': round(po, 2),
        'conus_disparity': round(pa / po, 3),
        'pct_counties_underobserved': round(100 * (du['disparity'] > 1).mean(), 1),
        'total_obs_millions': round(d['total_obs'].sum() / 1e6, 1),
    })
out = pd.DataFrame(rows)
out.to_csv('data/conus_disparity_by_year.csv', index=False)

pd.set_option('display.width', 120)
print(out.to_string(index=False))
print("\nSaved -> data/conus_disparity_by_year.csv")
print(f"Disparity {out.conus_disparity.iloc[0]:.2f} ({YEARS[0]}) -> "
      f"{out.loc[out.year==2023,'conus_disparity'].iloc[0]:.2f} (2023); "
      f"observations {out.total_obs_millions.iloc[0]:.0f}M -> {out.total_obs_millions.iloc[-1]:.0f}M "
      f"({out.total_obs_millions.iloc[-1]/out.total_obs_millions.iloc[0]:.1f}x).")
