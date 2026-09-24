# 04 — figure scripts

Run from this folder (`MPLBACKEND=Agg python <script>` for headless use). Inputs come from `../data/`,
outputs go to `../figures/`.

| Manuscript figure | Script | Input | Output |
|---|---|---|---|
| Figure 2 | `fig2_disparity_distribution.py` | `data/CONUS_COUNTIES_WITH_METRICS.csv` | `observational_disparity_distribution.png/.pdf` |
| Figure S1 | `figS1_top30_vs_bottom30.py` | `data/top_bottom_30/*TOP30.csv`, `*BOTTOM30.csv` | `comprehensive_geomean_comparison.png/.pdf` |
| Figure S2 | `figS2_county_spotlight.py` | same | `county_spotlight_comparison.png/.pdf` |
| Figure S3 | `figS3_spider_plot.py` *(reconstruction)* | `data/top_bottom_30/counties_enriched_with_usda_data.csv` | `figS3_spider_plot_reconstructed.png` |
| — | `extra_top_bottom_boxplots.py` | top/bottom 30 | earlier 3-panel comparison, not in the manuscript |
| — | `fetch_usda_nass_acres.py` | `*COMBINED_TOP_BOTTOM.csv` | adds `CORN_ACRES`, `VEGETABLE_ACRES` from USDA NASS Quick Stats (needs `USDA_NASS_API_KEY`) |

**Top/bottom 30 tables.** `data/top_bottom_30/*.csv` are the 30 highest- and 30 lowest-`GEOMEAN_SCORE`
rows of `CONUS_COUNTIES_WITH_METRICS.csv` (exported from a spreadsheet; they can be regenerated with
`df.nlargest(30, 'GEOMEAN_SCORE')` / `nsmallest`).

**Figure 5 (OEI map)** was produced in QGIS from `data/CONUS_COUNTIES_WITH_METRICS.geojson`
(`GEOMEAN_SCORE`, equal-interval classes; top 30 in blue, bottom 30 in magenta) and finished in
Illustrator. No script exists; the attribute table is the reproducible artefact.

**Figure S3 caveat.** The published spider plot was made interactively; no script survived.
`figS3_spider_plot.py` rebuilds it from the shipped data. The six axes follow the Figure S3 caption
(development, forest, log population density, corn acres) plus log observation density and farmland
coverage — check the last two against the published figure before reuse.

**Figure 1** is an illustration (Google Gemini-assisted) with no code. **Table S1** is qualitative.
