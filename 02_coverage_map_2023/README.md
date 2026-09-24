# 02 — 1 km observational-coverage map (Figure 4; Methods 2.3)

Figure 4 shows CONUS farmland coloured by whether it lies within 1 km of at least one 2023 GBIF
observation (30.5 % does). Inputs are the two 30 m rasters produced in `01_county_analysis_2023`
(`ag_raster.tif`, `obs_1km_raster_merged.tif`), uploaded as Earth Engine assets.

* `gee_figure4_neglected_ag_1km.js` — **the script used for the published figure**: reprojects both
  rasters to a 1 km grid (EPSG:3857), flags farmland pixels with no coverage, and exports the result.
  The export was styled (colours, legend, basemap) in Adobe Illustrator.
* `agricultural_gaps_gee.js` / `agricultural_gaps_gee.py` — earlier 30 m Earth Engine versions of the
  same operation (`ag == 1 AND obs_1km == 0`).
* `create_agricultural_gaps.R` / `create_agricultural_gaps.py` — local (terra / rasterio) equivalents
  for machines without Earth Engine access; slow at CONUS scale.
* `inspect_rasters.py` — checks raster value ranges before upload.
* `docs/` — the original setup and troubleshooting notes.

The county-level coverage statistic itself (`PERCENTAGE_OF_AG_LAND_WITHIN_1KM_GBIF_OBS`) is computed
in `01_county_analysis_2023` (notebook step 03 and script 15), not here.
