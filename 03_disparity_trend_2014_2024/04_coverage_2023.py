#!/usr/bin/env python
"""
STEP 4 — Observational coverage (2023): how much farmland is within 1 km of an observation?

Computed in Earth Engine: farmland (NLCD 81+82) that lies within 1 km of at least one 2023
GBIF observation. Uses your uploaded 2023 observation-count raster asset (built from GBIF);
if you don't have it, see the note at the bottom.

Run:  python 04_coverage_2023.py
Expected: ~25% of farmland is within 1 km of an observation (a ~75% coverage gap).

CAVEAT (state this in the paper): "within 1 km of a single observation" is a very low bar and
saturates as data accumulate — it measures data volume more than monitoring adequacy.
"""
import warnings; warnings.filterwarnings("ignore")
import ee
ee.Initialize()

YEAR = 2023
CONUS = ee.Geometry.Rectangle([-125, 24, -66.5, 49.5], proj='EPSG:4326', geodesic=False)
OBS_RASTER = 'projects/nicholas-gunner/assets/obs_raster'   # 30 m GBIF-2023 observation counts

nlcd = (ee.ImageCollection('projects/sat-io/open-datasets/USGS/ANNUAL_NLCD/LANDCOVER')
        # match the year token only, so this survives re-versioning (e.g. C1V1 -> C1V2)
        .filter(ee.Filter.stringContains('system:index', f'Annual_NLCD_LndCov_{YEAR}_CU'))
        .first().select('b1'))
ag = nlcd.eq(81).Or(nlcd.eq(82))
obs = ee.Image(OBS_RASTER)
within1km = obs.gt(0).unmask(0).focalMax(radius=1000, units='meters').gt(0)

area = ee.Image.pixelArea()
def km2(mask):
    return ee.Number(area.updateMask(mask).reduceRegion(
        ee.Reducer.sum(), CONUS, scale=300, maxPixels=1e13, bestEffort=True).get('area')).getInfo()/1e6

ag_area = km2(ag)
covered = km2(ag.And(within1km))
print(f"Agricultural land            : {ag_area:,.0f} km^2")
print(f"Farmland within 1 km of obs  : {covered:,.0f} km^2  ({100*covered/ag_area:.1f}%)")
print(f"=> Coverage gap              : {100*(1-covered/ag_area):.1f}% of farmland has NO obs within 1 km")

# If you do not have the obs_raster asset: rerun STEP 2 to harvest 2023 observations, export
# them to a 30 m raster in Earth Engine, and point OBS_RASTER at it. (This coverage metric is
# secondary; the disparity results in STEPS 1-3 are the paper's core finding.)
