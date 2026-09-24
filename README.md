# Citizen Science on the Farm — replication code and data

[![DOI](https://img.shields.io/badge/DOI-pending%20Zenodo%20release-lightgrey)](https://zenodo.org/) <!-- replace with the Zenodo badge after the first release -->
[![License: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE) [![Data: CC BY 4.0](https://img.shields.io/badge/data%20%26%20figures-CC%20BY%204.0-lightblue.svg)](LICENSE)

Replication package for ***Citizen Science on the Farm: Shared Observational Effort is Lacking on Agricultural Lands***

Nicholas Gunner, Yu Jiang, Kaitlin Gold, Sara Emery & Terence Bates (Cornell AgriTech, Cornell University). Manuscript submitted to *Citizen Science: Theory and Practice*, 2026.

This package contains every script, intermediate table, and derived dataset needed to regenerate the
manuscript's results: the 2023 county-level analysis (observational disparity, 1 km coverage, and the
Observational Effort Index), the 2014–2023 disparity time series (2024 is also measured), and all script-generated figures.
Raw inputs that are large and freely downloadable (the 133.9 M-record GBIF download, the 30 m NLCD
raster) are **not** included; `data/DATA_SOURCES.md` gives their DOIs, filters, and retrieval dates.

## What reproduces what

| Manuscript element | Where it comes from |
|---|---|
| Table 1 — 23.4 % farmland, 7.8 % of observations on farmland, disparity ≈ 3.0 | `01_county_analysis_2023/` (steps 03 → 15), summarised by `16_compute_final_metrics.py` |
| Figure 2 — county disparity distribution, 81.7 % of counties > 1 | `04_figures/fig2_disparity_distribution.py` on `data/CONUS_COUNTIES_WITH_METRICS.csv` |
| Figure 3 — 2014–2023 disparity trend (2.71× → 3.25×) | `03_disparity_trend_2014_2024/reproduce_disparity_pointmethod.py` (one run per year) → `06_plot_disparity_over_time.py` |
| Figure 3 caption — 3.0 vs 3.25 for 2023 | `03_disparity_trend_2014_2024/07_disparity_robustness_2023.py` |
| Methods 2.3 — coverage sensitivity to the buffer radius (500 m / 1 km / 2 km) | `03_disparity_trend_2014_2024/08_coverage_radius_sensitivity.py` → `outputs/coverage_radius_sensitivity_2023.csv` |
| Figure 4 — farmland within / beyond 1 km of an observation (30 % covered) | `01_county_analysis_2023/04_gee_obs_1km_buffer.js` → `02_coverage_map_2023/gee_figure4_neglected_ag_1km.js` |
| Figure 5 — OEI map, top/bottom 30 counties | `GEOMEAN_SCORE` in `data/CONUS_COUNTIES_WITH_METRICS.geojson`, mapped in QGIS (no script; see `04_figures/README.md`) |
| Figures S1, S2 | `04_figures/figS1_top30_vs_bottom30.py`, `figS2_county_spotlight.py` |
| Figure S3 | `04_figures/figS3_spider_plot.py` (a reconstruction — see caveat in `04_figures/README.md`) |
| Table S1 | qualitative; no code |
| Supplementary socioeconomic comparison | `01_county_analysis_2023/03_rasterize_and_county_metrics.Rmd` (GLM section) |

## Layout

```
.
├── 01_county_analysis_2023/   R notebooks + Python helpers for the 2023 county metrics (steps 01–16)
├── 02_coverage_map_2023/      Earth Engine / R / Python scripts for the 1 km coverage raster and Figure 4
├── 03_disparity_trend_2014_2024/  self-contained GBIF-API + Earth Engine pipeline for the decade series
├── 04_figures/                figure scripts (Figure 2, S1, S2, S3) and the USDA NASS enrichment script
├── data/                      final county dataset (CSV + GeoJSON), the pre-derivation table, top/bottom-30 tables
└── figures/                   script-generated figure files
```

Each sub-folder has its own README with run order, inputs and outputs.

## Quick start (minutes, no cloud accounts)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Final county table and headline numbers (Table 1, Figure 2 statistic, 30 % coverage)
python 01_county_analysis_2023/16_compute_final_metrics.py

# Decade series and its figures (from the included per-year results)
cd 03_disparity_trend_2014_2024 && python 05_build_disparity_by_year.py && python 06_plot_disparity_over_time.py && python 07_disparity_robustness_2023.py && cd ..

# Manuscript figures 2, S1, S2, S3
cd 04_figures && for s in fig2_disparity_distribution.py figS1_top30_vs_bottom30.py figS2_county_spotlight.py figS3_spider_plot.py; do MPLBACKEND=Agg python "$s"; done
```

## Full reproduction (hours; needs downloads and a Google Earth Engine account)

1. **2023 county analysis** — download the GBIF occurrence file (DOI 10.15468/dl.5h7by2) and the Annual
   NLCD 2023 land-cover raster, then follow `01_county_analysis_2023/README.md` (R 4.4 with `terra`,
   `sf`, `exactextractr`; one Earth Engine step for the 1 km buffer).
2. **Decade series** — `03_disparity_trend_2014_2024/reproduce_disparity_pointmethod.py --year YYYY --zoom 12`
   for each year 2014–2024 (several hours per year; resumable). Requires `earthengine authenticate`.

## Environment

* Python 3.9+ — pinned versions in `requirements.txt` (the versions used for the shipped results).
* R 4.4.1 — package versions in `R-requirements.txt`.
* Google Earth Engine — any account; the scripts read public assets only
  (`projects/sat-io/open-datasets/USGS/ANNUAL_NLCD/LANDCOVER`, `USGS/NLCD_RELEASES/2021_REL`).
* USDA NASS Quick Stats key (free) only for `04_figures/fetch_usda_nass_acres.py`; set `USDA_NASS_API_KEY`.

## Things to know before relying on a re-run

* **GBIF counts drift.** The GBIF Maps API and occurrence index are back-filled continuously, so
  re-harvesting shifts absolute observation counts by a few percent between passes. Ratio metrics
  (disparity, share on farmland, share of counties) are stable to this. The 3.0 (original 2023
  download, May 2025) versus 3.25 (API harvest, 2026) difference in Figure 3 is documented in
  `03_disparity_trend_2014_2024/README.md` and by `07_disparity_robustness_2023.py`.
* **Start year matters for the trend headline.** The series now begins in 2014 (2.71×), which is *above* 2015 (2.22×):
  the farmland share of observations rose transiently in 2015–16 before declining steadily. Endpoint framing therefore
  depends on the start year (2014→2023 +20 %; 2015→2023 +47 %); the fitted linear trend (+0.09 per year, R² 0.72) is the
  robust statement. The dip is confirmed at coarse resolution and is not explained by dataset composition — see
  `03_disparity_trend_2014_2024/README.md`.
* **NLCD asset re-versioning.** The Earth Engine mirror of the Annual NLCD was re-versioned (C1V1 → C1V2)
  during the project; the scripts select the image by year token so they keep working, but a re-run may
  differ marginally from the shipped results.
* **One spreadsheet step is now scripted.** In the original workflow the OEI, disparity ratio and derived
  area/count columns of the final county table were computed in a spreadsheet from the output of step 15.
  `16_compute_final_metrics.py` reproduces that step and verifies it against the shipped table (all
  columns agree to ≤ 5 × 10⁻⁶; counts to the integer).
* **Undefined disparities.** 80 counties have farmland but zero farmland observations in 2023, so their
  disparity ratio is undefined (infinite). The shipped table and the manuscript's "81.7 % of counties"
  code these as 0.0 — a division-by-zero convention — which *excludes* them from the under-observed
  share. Counting them, 84.3 % of all counties (84.6 % of counties with any farmland) are under-observed.
  `16_compute_final_metrics.py` prints both figures; `--legacy-zero` reproduces the shipped coding.
* **Maps were finished by hand.** Figure 4 and Figure 5 are Earth Engine / QGIS exports styled in Adobe
  Illustrator; the scripts here produce the underlying rasters and attributes, not the final artwork.
  Figure 1 is an illustration (Google Gemini-assisted) and has no code.
* **Figure S3 is a reconstruction.** The original spider plot was made interactively and the script did not
  survive; `figS3_spider_plot.py` regenerates it from the shipped data with the axis choices documented in
  its header.
* **AI-assisted code.** Several helper scripts in `01_county_analysis_2023/` carry an "Author: AI Assistant"
  header from their original generation; all were run and their outputs checked by the first author, and
  their outputs are verified here by step 16.
* **Not included.** Work-in-progress code for a follow-up re-analysis (the project's "2.0" folder) is
  outside the scope of this record.

## Licence

Code is released under the MIT Licence (see `LICENSE`). The derived tables in `data/` and the figures
are released under CC BY 4.0. Underlying GBIF records carry their own licences (CC0 / CC BY / CC BY-NC by
dataset); NLCD, NWS and USDA ERS/NASS data are U.S. Government public domain.

## How to cite

Software/data (this repository — see `CITATION.cff`; the Zenodo concept DOI replaces the URL once minted):

> Gunner, N. (2026). *Replication code and data for: Citizen Science on the Farm — Shared Observational Effort is Lacking on Agricultural Lands* (Version 1.0.0) [Computer software]. https://github.com/ngunner/citizen-science-on-the-farm

Primary data (cite alongside): GBIF.org (2025) occurrence download https://doi.org/10.15468/dl.5h7by2 · U.S. Geological Survey (2024) Annual NLCD Collection 1 https://doi.org/10.5066/P94UXNTS — full list in `data/DATA_SOURCES.md`.

## Questions

Open an issue on this repository or contact the corresponding author (nrg42@cornell.edu).
