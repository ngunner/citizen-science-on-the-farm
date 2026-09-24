#!/usr/bin/env python
"""
STEP 8 — Sensitivity of the 2023 farmland-coverage metric (Methods 2.3) to the buffer radius.

The manuscript counts farmland as "covered" if it lies within 1 km of at least one 2023 GBIF
observation. That radius is a deliberately permissive threshold rather than an ecologically derived
one, so this step recomputes coverage at 500 m, 1 km and 2 km with an identical method
(Earth Engine: distance from the nearest observation on the 30 m observation-count raster, masked to
Annual NLCD 2023 farmland, classes 81+82).

A CONUS-wide neighbourhood computation exceeds Earth Engine's synchronous compute limit, so the
result is produced as a batch export (one-row CSV to Google Drive) and polled here.

Note: the manuscript's 30.5% figure comes from the exact_extract pipeline in 01_county_analysis_2023
(30 m, county-summed); the 1 km row here, computed at the same 30 m resolution, is the cross-check.

Run:    python 08_coverage_radius_sensitivity.py            # starts the export and polls until done
Output: Google Drive  EarthEngineExports/coverage_radius_sensitivity_2023_30m.csv
        (copy it to outputs/coverage_radius_sensitivity_2023.csv)
"""
import warnings; warnings.filterwarnings("ignore")
import time
import ee
ee.Initialize()

YEAR = 2023
RADII_M = [500, 1000, 2000]
SCALE = 30    # native NLCD / obs_raster resolution. A coarser reporting scale resamples the 30 m observation
              # raster before the distance transform, drops isolated observation pixels and understates coverage
              # (a 100 m trial gave 20.8% at 1 km vs the manuscript's 30.5%).
CONUS = ee.Geometry.Rectangle([-125, 24, -66.5, 49.5], proj='EPSG:4326', geodesic=False)
OBS_RASTER = 'projects/nicholas-gunner/assets/obs_raster'   # 30 m GBIF-2023 observation counts

nlcd = (ee.ImageCollection('projects/sat-io/open-datasets/USGS/ANNUAL_NLCD/LANDCOVER')
        .filter(ee.Filter.stringContains('system:index', f'Annual_NLCD_LndCov_{YEAR}_CU'))
        .first().select('b1'))
ag = nlcd.eq(81).Or(nlcd.eq(82))
obs_present = ee.Image(OBS_RASTER).gt(0).unmask(0)
# distance (m) to the nearest observation pixel; 128-px neighbourhood at 30 m covers > 2 km
dist_m = obs_present.fastDistanceTransform(128).sqrt().multiply(ee.Image.pixelArea().sqrt())
area = ee.Image.pixelArea()

img = area.updateMask(ag).rename('ag_area_m2')
for r in RADII_M:
    img = img.addBands(area.updateMask(ag.And(dist_m.lte(r))).rename(f'covered_{r}m_m2'))
stats = img.reduceRegion(ee.Reducer.sum(), CONUS, scale=SCALE, maxPixels=1e13)
fc = ee.FeatureCollection([ee.Feature(None, stats.set('year', YEAR).set('scale_m', SCALE))])

task = ee.batch.Export.table.toDrive(collection=fc, description='coverage_radius_sensitivity_2023_30m',
                                     folder='EarthEngineExports', fileNamePrefix='coverage_radius_sensitivity_2023_30m',
                                     fileFormat='CSV')
task.start()
print("export task started:", task.id)
while True:
    st = task.status(); state = st['state']
    print(time.strftime('%H:%M:%S'), state, flush=True)
    if state in ('COMPLETED', 'FAILED', 'CANCELLED'):
        if state != 'COMPLETED': print(st.get('error_message'))
        break
    time.sleep(60)
