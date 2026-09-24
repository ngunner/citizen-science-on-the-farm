#!/usr/bin/env python
"""
STEP 2 — What fraction of citizen-science observations fall on farmland? (2023)
         And the resulting observational disparity.

Method: harvest per-cell GBIF occurrence counts (GBIF Maps API, ~150 m grid) across CONUS
and overlay each cell on the NLCD agricultural fraction (in Earth Engine). Each observation
is classified as on- or off-farmland by the land cover beneath it.

Saves the per-cell result to data/obs_cells_2023.parquet (used by STEP 3).

Run:  python 02_obs_disparity_2023.py   (~5-10 min: it harvests all of CONUS)
Expected: ~9.5% of observations on farmland; disparity (24% land / 9.5% obs) ~2.5x.

Note on resolution: the ~150 m grid slightly OVERstates on-farmland observation (observers
cluster on roads/farmsteads within farm cells), so this disparity is a conservative lower
bound; a ~19 m grid gives a slightly larger gap. See README.
"""
import warnings; warnings.filterwarnings("ignore")
import os, ee
ee.Initialize()
from gbif_overlay import harvest_overlay

YEAR = 2023
CONUS = (-125.0, 24.5, -66.9, 49.4)   # west, south, east, north

print("Harvesting CONUS GBIF observations x NLCD farmland overlay (2023)...")
df = harvest_overlay(*CONUS, YEAR, zoom=9, workers=16, verbose=True)

total = df['count'].sum()
on_ag = (df['count'] * df['ag_frac']).sum()
pct_ag_area = 23.8          # from STEP 1
pct_on_ag = 100 * on_ag / total
print(f"\nTotal observations (2023)     : {total:,.0f}")
print(f"Observations on farmland      : {on_ag:,.0f}  ({pct_on_ag:.1f}%)")
print(f"Agricultural land (STEP 1)    : {pct_ag_area:.1f}% of CONUS")
print(f"=> Observational disparity    : {pct_ag_area/pct_on_ag:.2f}  "
      f"(%ag land / %obs on ag; >1 means farmland under-observed)")

os.makedirs('data', exist_ok=True)
df.to_parquet('data/obs_cells_2023.parquet', index=False)
print("\nSaved per-cell overlay -> data/obs_cells_2023.parquet (for STEP 3).")
