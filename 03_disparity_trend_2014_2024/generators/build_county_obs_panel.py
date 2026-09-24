#!/usr/bin/env python
"""
GENERATOR (slow, full-provenance) — build data/county_obs_panel_long.csv from scratch.

For each year 2015-2024 this harvests the entire CONUS GBIF occurrence-density grid (GBIF
Maps API, zoom 9 ~ 137 m cells), overlays each cell on the USGS Annual NLCD agricultural
fraction (classes 81+82) in Earth Engine, assigns every cell to its county, and aggregates:
    total_obs = sum(count)
    obs_on_ag = sum(count * ag_frac)
This is exactly STEP 2's overlay, looped over all ten years and rolled up per county.

This is the SLOW path (re-queries the live GBIF API for all of CONUS x 10 years; roughly
30-90 min total and the GBIF counts drift a few percent between runs). You do NOT need to run
it to reproduce the paper: data/county_obs_panel_long.csv is already provided, and STEP 5
(../05_build_disparity_by_year.py) builds the decade series from it in seconds. Run this only
to regenerate the observation panel from the live data source.

Inputs : ../gbif_overlay.py            (the shared harvest+overlay helper, used by STEP 2)
         ../data/us_counties.geojson   (county boundaries, FIPS)
Output : ../data/county_obs_panel_long.csv   (FIPS, total_obs, obs_on_ag, n_cells, year)
         per-year checkpoints in ../data/county_obs_by_year/  (resumable)

Run:  python generators/build_county_obs_panel.py     (from the replication/ folder)
Env:  earthengine-api requests pyarrow geopandas mapbox-vector-tile mercantile
"""
import warnings; warnings.filterwarnings("ignore")
import os, sys, glob, time
import pandas as pd, geopandas as gpd
import ee
ee.Initialize()

HERE = os.path.dirname(os.path.abspath(__file__))
REP  = os.path.abspath(os.path.join(HERE, '..'))       # the replication/ folder
sys.path.insert(0, REP)                                # reuse the SAME gbif_overlay.py as STEP 2
from gbif_overlay import harvest_overlay

DATA  = os.path.join(REP, 'data')
CKPT  = os.path.join(DATA, 'county_obs_by_year')
os.makedirs(CKPT, exist_ok=True)
COUNTIES = os.path.join(DATA, 'us_counties.geojson')

YEARS = list(range(2015, 2025))
CONUS = (-125.0, 24.5, -66.9, 49.4)      # west, south, east, north
ZOOM  = 9

print("Loading county polygons ...")
counties = gpd.read_file(COUNTIES).to_crs(4326)[['FIPS', 'geometry']]
counties['FIPS'] = counties['FIPS'].astype(str).str.zfill(5)

for year in YEARS:
    ck = os.path.join(CKPT, f'county_obs_{year}.csv')
    if os.path.exists(ck):
        print(f"{year}: checkpoint exists, skipping"); continue
    t0 = time.time()
    print(f"{year}: harvesting CONUS overlay (zoom {ZOOM}) ...")
    df = harvest_overlay(*CONUS, year, zoom=ZOOM, workers=12, verbose=True)
    pts = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs=4326)
    j = gpd.sjoin(pts, counties, how='inner', predicate='within')
    j['obs_on_ag'] = j['count'] * j['ag_frac']
    agg = (j.groupby('FIPS')
           .agg(total_obs=('count', 'sum'), obs_on_ag=('obs_on_ag', 'sum'),
                n_cells=('count', 'size'))
           .reset_index())
    agg['year'] = year
    agg.to_csv(ck, index=False)
    print(f"{year}: {len(df):,} cells, {df['count'].sum():,.0f} obs, "
          f"{100*agg['obs_on_ag'].sum()/agg['total_obs'].sum():.1f}% on ag  [{time.time()-t0:.0f}s]")

# combine checkpoints -> the long panel STEP 5 reads
parts = sorted(glob.glob(os.path.join(CKPT, 'county_obs_*.csv')))
panel = pd.concat([pd.read_csv(p, dtype={'FIPS': str}) for p in parts], ignore_index=True)
panel['FIPS'] = panel['FIPS'].str.zfill(5)
out = os.path.join(DATA, 'county_obs_panel_long.csv')
panel.to_csv(out, index=False)
print(f"\nWrote {out}  ({len(panel)} county-year rows, {panel['year'].nunique()} years)")
print("NOTE: live GBIF counts drift a few percent between harvests, so re-running this will")
print("      shift the absolute observation totals slightly (the disparity ratios are stable).")
