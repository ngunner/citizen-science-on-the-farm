# 01 — 2023 county-level analysis (Methods 2.1, 2.3, 2.4; Table 1; Figures 2, 4, 5, S1–S3)

Original workflow (R notebooks + Python helpers, May–November 2025), copied here with machine-specific
paths removed and a provenance header added to each file. Logic is unchanged. Step 16 is new.

## Raw inputs (download; not included)

| Input | Source | Expected path (relative to this folder) |
|---|---|---|
| GBIF occurrence download, 133,877,768 human-observation records, USA, 2023 | DOI 10.15468/dl.5h7by2 (GBIF.org, 1 May 2025) | `../GBIF_US_2023/0010290-250426092105405.csv` (unzipped) |
| Annual NLCD land cover 2023, CONUS, 30 m, EPSG:5070 | USGS Annual NLCD Collection 1 (DOI 10.5066/P94UXNTS), file `Annual_NLCD_LndCov_2023_CU_C1V0.tif` | `../NLCD2023/` |
| NWS county boundaries (c_05mr24) | weather.gov/gis/Counties — **included** in `inputs/c_05mr24/` | |
| USDA ERS county-level data (Education, Population, Poverty, Unemployment; 2023 releases) | ers.usda.gov/data-products/county-level-data-sets — **included** in `inputs/ers/` | |
| County FIPS master list | **included** `inputs/county_fips_master.csv` | |

The notebooks were written to run inside a `Raw Data/` tree with sibling folders `GBIF_US_2023/`,
`NLCD2023/`, `US_Counties/` and this folder as `Bridging Gaps Dataset/`. Recreate that layout (or edit
the `../` paths at the top of each notebook).

## Run order

| Step | File | What it does | Output |
|---|---|---|---|
| 01 | `01_gbif_download_to_parquet.Rmd` | Reads the GBIF TSV, keeps `decimalLongitude/decimalLatitude`, writes Parquet | `GBIFUS2023.parquet` |
| 02 | `02_build_county_layer.Rmd` | Joins ERS CSVs to the NWS county shapefile on FIPS | `US_Counties_SocioEconomics.gpkg` |
| 03 | `03_rasterize_and_county_metrics.Rmd` | (a) `ag_raster` = NLCD classes 81 + 82; (b) rasterizes GBIF points to a 30 m count raster `obs_raster`; (c) exports coordinates for Earth Engine; (d) merges the 1 km tiles from step 04; (e) `exact_extract` per county: % farmland, % observations on farmland, % farmland within 1 km; (f) GLM of socioeconomic covariates | `ag_raster.tif`, `obs_raster.tif`, `counties_with_final_metrics.geojson`, `us_counties_ag_observations.csv` |
| 04 | `04_gee_obs_1km_buffer.js` | Earth Engine: distance transform on `obs_raster` → 1 = within 1 km of ≥ 1 observation; exported snapped to the NLCD grid | `obs_1km_raster-*.tif` tiles |
| 05 | `05_county_landcover_percentages.R` | % developed (21–24), % forest (41–43), % water (11) per county | `counties_landcover_percentages_optimized.csv` |
| 06 | `06_county_area_and_obs_count.R` | County area (EPSG:5070) and total observation count / density | `county_area_obs_data.csv` |
| 07 | `07_merge_county_obs.py` | Merge 06 into the metrics table (FIPS zero-padding) | `Finals/…_and_obs_data_FIXED.csv` |
| 08 | `08_add_population_density.py` | Population ÷ area | `Finals/…_with_pop_density.csv` |
| 09 | `09_merge_landcover.py` | Merge 05 | `Finals/…_and_landcover.csv` |
| 10 | `10_verify_areas.py` | Recompute areas/density from shapefile geometry; resolve duplicate-FIPS polygons | `FINAL_CONTUS_GBIF_CORRECTED_FIXED.csv` |
| 11–13 | `11_filter_to_counties.py`, `12_deduplicate_counties.py`, `13_create_final_dataset.py` | Drop non-county NWS zones (e.g. city warning areas), aggregate split counties (e.g. Monroe FL keys) | `FINAL_CONTUS_GBIF_Counties_Only.csv` |
| 14 | `14_join_to_polygons.py` | Join back to polygons (largest polygon per FIPS) | `contus_counties.geojson` |
| 15 | `15_coverage_within_1km.py` | Recomputes % farmland within 1 km per county by pixel counting (`ag_raster × obs_1km_raster_merged`) | `contus_counties_updated_optimized.csv/.geojson` — **shipped** as `../data/contus_counties_updated_optimized.csv` |
| 16 | `16_compute_final_metrics.py` *(new)* | OEI = ∛(P_area · P_coverage · P_obs), disparity = P_area / P_obs, derived areas and counts; verifies against the shipped final table | `../data/CONUS_COUNTIES_WITH_METRICS_recomputed.csv` |

Step 16 runs in seconds from the shipped step-15 output and prints the manuscript's headline numbers
(23.4 % farmland; 7.8 % of observations on farmland; 81.7 % of counties with disparity > 1; 30.5 % of
farmland within 1 km of an observation). See the package README on the treatment of the 80 counties whose
disparity is undefined.

## Software

R 4.4.1 with terra 1.8.54, sf 1.0.21, exactextractr 0.10.0, arrow 19.0.1.1, dplyr 1.1.4, data.table 1.16.0,
doParallel 1.0.17, foreach 1.5.2. Python per `requirements.txt` (pandas, geopandas, rasterio, numpy).
