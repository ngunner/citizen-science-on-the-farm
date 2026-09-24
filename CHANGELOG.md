# Changelog

## 1.0.0 — 2026-09-24
First public release, accompanying the manuscript as submitted to *Citizen Science: Theory and Practice*.

- `01_county_analysis_2023/` — 2023 county metrics pipeline (R + Python); new step 16 derives and verifies the
  final county table (OEI, disparity, areas, counts).
- `02_coverage_map_2023/` — Earth Engine / R / Python scripts behind the 1 km coverage map (Figure 4).
- `03_disparity_trend_2014_2024/` — exact-point disparity for every year 2014–2024 (GBIF Maps API × Annual NLCD),
  coarse-grid cross-checks, the 2023 method-robustness figure, and the buffer-radius sensitivity (500 m / 1 km / 2 km).
- `04_figures/` — scripts for Figures 2, S1, S2, S3 (S3 is a reconstruction) and the USDA NASS enrichment step.
- `data/` — final county dataset for 3,108 CONUS counties (CSV + GeoJSON), pre-derivation table, top/bottom-30 tables.
