#!/usr/bin/env python
"""
GENERATOR (cloud, full-provenance) — build data/county_landcover_wide.csv from scratch.

For every CONUS county (TIGER 2018, keyed by FIPS/GEOID) this computes, per year 2015-2024,
the agricultural area (USGS Annual NLCD classes 81 Hay/Pasture + 82 Cultivated Crops) and the
valid land area, plus 2023 land-cover covariates. It is one server-side zonal reduction in
Earth Engine (Export.table.toAsset) — nothing large is downloaded.

    ag_<year>   = area of NLCD classes 81+82   (m^2, per county)
    land_<year> = area of valid NLCD land       (m^2, per county)  [denominator]
    dev_2023 / forest_2023 / grass_2023         (m^2)              [reference-year covariates]

This is the source of the per-county farmland areas used by STEP 1 (CONUS total) and STEP 5
(per-county share of counties under-observing). You do NOT need to run it to reproduce the
paper: data/county_landcover_wide.csv is already provided.

Run:  python generators/export_county_landcover_panel.py
Then: watch the task in the Earth Engine Tasks tab; when it finishes, export the asset table
      to CSV (Export.table.toDrive with the same collection, or the asset's "Export" button)
      and save it as ../data/county_landcover_wide.csv with columns:
        GEOID, ALAND, INTPTLAT, INTPTLON, ag_2015..ag_2024, land_2015..land_2024,
        dev_2023, forest_2023, grass_2023
Env:  earthengine-api  (run `earthengine authenticate` once)
"""
import warnings; warnings.filterwarnings("ignore")
import ee
ee.Initialize()

YEARS = list(range(2015, 2025))
NON_CONUS = ['02', '15', '60', '66', '69', '72', '78']   # AK, HI, territories
DEST = 'projects/nicholas-gunner/assets/csotf2/county_landcover_panel'   # change to your project

counties = (ee.FeatureCollection('TIGER/2018/Counties')
            .filter(ee.Filter.inList('STATEFP', NON_CONUS).Not()))

NLCD = ee.ImageCollection('projects/sat-io/open-datasets/USGS/ANNUAL_NLCD/LANDCOVER')
def nlcd_year(y):
    # match the year token only, so this survives re-versioning (e.g. C1V1 -> C1V2)
    return NLCD.filter(ee.Filter.stringContains('system:index',
            f'Annual_NLCD_LndCov_{y}_CU')).first().select('b1')

pa = ee.Image.pixelArea()
def in_classes(img, codes):
    m = ee.Image(0)
    for c in codes:
        m = m.Or(img.eq(c))
    return m

bands = []
for y in YEARS:
    img = nlcd_year(y)
    bands.append(pa.updateMask(in_classes(img, [81, 82])).rename(f'ag_{y}'))    # farmland
    bands.append(pa.updateMask(img.mask()).rename(f'land_{y}'))                  # valid land
img23 = nlcd_year(2023)
bands.append(pa.updateMask(in_classes(img23, [21, 22, 23, 24])).rename('dev_2023'))
bands.append(pa.updateMask(in_classes(img23, [41, 42, 43])).rename('forest_2023'))
bands.append(pa.updateMask(in_classes(img23, [71])).rename('grass_2023'))

stack = ee.Image.cat(bands)
table = stack.reduceRegions(collection=counties, reducer=ee.Reducer.sum(),
                            scale=30, tileScale=4)                               # 30 m NLCD native
keep = ['GEOID', 'STATEFP', 'NAME', 'ALAND', 'AWATER', 'INTPTLAT', 'INTPTLON'] \
       + [f'ag_{y}' for y in YEARS] + [f'land_{y}' for y in YEARS] \
       + ['dev_2023', 'forest_2023', 'grass_2023']
table = table.select(keep)

task = ee.batch.Export.table.toAsset(
    collection=table, description='csotf2_county_landcover_panel', assetId=DEST)
task.start()
print(f"Launched export task id={task.id}  -> asset {DEST}")
print(f"  {len(YEARS)} years x (ag,land) + 3 covariates = {len(bands)} bands over ~3108 counties")
print("  Watch the Earth Engine Tasks tab; then export the asset to ../data/county_landcover_wide.csv")
