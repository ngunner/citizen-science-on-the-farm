# Data sources and the shipped tables

## Primary sources (download; not included)

| Source | Used for | Identifier / retrieval |
|---|---|---|
| **GBIF occurrence download** — 133,877,768 records; filters: BasisOfRecord = Human Observation, Country = United States of America, HasCoordinate = true, HasGeospatialIssue = false, OccurrenceStatus = Present, Year = 2023 | 2023 county analysis (128.3 M records after clipping to CONUS) | GBIF.org (1 May 2025). https://doi.org/10.15468/dl.5h7by2 |
| **GBIF Maps API** occurrence-density tiles (`api.gbif.org/v2/map/occurrence/density/…`, `basisOfRecord=HUMAN_OBSERVATION`, per calendar year) | 2014–2024 disparity series | harvested 2026; query parameters in `03_disparity_trend_2014_2024/reproduce_disparity_pointmethod.py` |
| **USGS Annual NLCD Collection 1**, land cover, CONUS, 30 m — file `Annual_NLCD_LndCov_2023_CU_C1V0.tif` for 2023; Earth Engine mirror `projects/sat-io/open-datasets/USGS/ANNUAL_NLCD/LANDCOVER` for 2015–2024 | Farmland = classes 81 (Pasture/Hay) + 82 (Cultivated Crops) | U.S. Geological Survey (2024). https://doi.org/10.5066/P94UXNTS |
| **NWS county boundaries** `c_05mr24` | County polygons and FIPS | https://www.weather.gov/gis/Counties (included: `01_county_analysis_2023/inputs/c_05mr24/`) |
| **USDA ERS county-level data sets** — Education (2023), Population estimates (2023), Poverty (2023), Unemployment & median household income (2023) | Socioeconomic covariates | https://www.ers.usda.gov/data-products/county-level-data-sets (retrieved May 2025; included: `01_county_analysis_2023/inputs/ers/`) |
| **USDA NASS Quick Stats** — 2022 Census of Agriculture: "CORN, GRAIN – ACRES HARVESTED", "VEGETABLE TOTALS, IN THE OPEN – ACRES HARVESTED" | Figure S3 monoculture axis | https://quickstats.nass.usda.gov/api (retrieved November 2025) |

## Shipped tables

### `CONUS_COUNTIES_WITH_METRICS.csv` / `.geojson` — final county dataset (3,108 counties)

| Column | Meaning |
|---|---|
| `FIPS`, `COUNTYNAME`, `STATE`, `TIME_ZONE`, `CWA`, `FE_AREA`, `LATITUDE`, `LONGITUDE` | NWS county attributes |
| `PERCENTAGE_GBIF_OBS_ON_AG_LAND` | fraction of the county's 2023 observations whose 30 m pixel is farmland (P_obs) |
| `PERCENTAGE_OF_AG_LAND_WITHIN_1KM_GBIF_OBS` | fraction of county farmland within 1 km of ≥ 1 observation (P_coverage) |
| `PERCENT_AGRICULTURE` | fraction of county area that is farmland (P_area) |
| `GEOMEAN_SCORE` | Observational Effort Index = ∛(P_area · P_coverage · P_obs) |
| `TOTAL_GBIF_OBS_COUNT_2023`, `GBIF_AG_OBS_COUNT_2023`, `GBIF_OBS_DENSITY_KM2` | observation counts and density |
| `OBSERVATIONAL_DISPARITY` | P_area / P_obs (> 1 ⇒ farmland under-observed). **0.0 denotes an undefined ratio** (no farmland observations) — see package README |
| `PERCENT_DEVELOPED`, `PERCENT_FOREST` | NLCD 21–24, 41–43 fractions |
| `AREA_KM2`, `AG_AREA_KM2`, `COVERED_AG_AREA_KM2` | areas (EPSG:5070) |
| `POPULATION_DENSITY_2023_KM2`, `POPULATION_ESTIMATE_2023`, `MEDIAN_HOUSEHOLD_INCOME_2022`, `MEDIAN_HOUSEHOLD_INCOME_PERCENT_OF_STATE_TOTAL_2022`, `PERCENT_ADULTS_BACHELORS_DEGREE_2023`, `PERCENT_POVERTY_2023`, `UNEMPLOYMENT_RATE_2023` | USDA ERS covariates |

All fractions are 0–1, not percent.

### `contus_counties_updated_optimized.csv`
Output of `01_county_analysis_2023/15_coverage_within_1km.py` — the final table before the derived
columns were added. Input to step 16.

### `top_bottom_30/`
Top-30 / bottom-30 `GEOMEAN_SCORE` subsets, the combined 60-row table, and the NASS-enriched version
(`counties_enriched_with_usda_data.csv`, adds `RANK`, `CORN_ACRES`, `VEGETABLE_ACRES`).

### `03_disparity_trend_2014_2024/data/` and `outputs/`
See that folder's README: per-county land-cover and observation panels (2015–2024), the coarse-grid
decade table, and the ten exact-point `pointmethod_<year>_z12_RESULT.csv` files behind Figure 3.
