#!/usr/bin/env python
"""
STEP 1 — How much of the Continental US is agricultural land? (2023)

Agriculture = USGS Annual NLCD classes 81 (Hay/Pasture) + 82 (Cultivated Crops).
Computed entirely in Google Earth Engine (no large downloads).

Run:  python 01_ag_area_2023.py
Expected: ~23.8% of CONUS land is agricultural.
"""
import warnings; warnings.filterwarnings("ignore")
import ee
ee.Initialize()

YEAR = 2023
CONUS = ee.Geometry.Rectangle([-125, 24, -66.5, 49.5], proj='EPSG:4326', geodesic=False)

nlcd = (ee.ImageCollection('projects/sat-io/open-datasets/USGS/ANNUAL_NLCD/LANDCOVER')
        # match the year token only, so this survives re-versioning (e.g. C1V1 -> C1V2)
        .filter(ee.Filter.stringContains('system:index', f'Annual_NLCD_LndCov_{YEAR}_CU'))
        .first().select('b1'))
ag = nlcd.eq(81).Or(nlcd.eq(82))          # agricultural land
land = nlcd.mask()                        # all valid (CONUS land) pixels
area = ee.Image.pixelArea()               # m^2 per pixel

def km2(mask):
    m2 = area.updateMask(mask).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=CONUS, scale=300,
        maxPixels=1e13, bestEffort=True).get('area')
    return ee.Number(m2).getInfo() / 1e6

total = km2(land)
ag_km2 = km2(ag)
print(f"CONUS land area       : {total:,.0f} km^2")
print(f"Agricultural land area: {ag_km2:,.0f} km^2")
print(f"=> Agriculture is {100*ag_km2/total:.1f}% of CONUS land (2023)")
