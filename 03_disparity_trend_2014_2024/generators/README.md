# generators/ — how the decade panels were produced (the slow, full-provenance path)

STEP 5 (`../05_build_disparity_by_year.py`) builds the decade series
`data/conus_disparity_by_year.csv` in seconds from two per-county panels that are **already
provided** in `../data/`. You do not need anything in this folder to reproduce the paper.

This folder documents where those two panels came from, so the chain is reproducible all the
way back to the raw data sources (USGS Annual NLCD and the live GBIF Maps API).

| Generator | Produces | Source | Runtime |
|---|---|---|---|
| `export_county_landcover_panel.py` | `../data/county_landcover_wide.csv` — per-county `ag_<year>`/`land_<year>`/`ALAND` | USGS Annual NLCD (81+82), Earth Engine zonal reduction | ~a few min (server-side) |
| `build_county_obs_panel.py` | `../data/county_obs_panel_long.csv` — per-county `total_obs`/`obs_on_ag` per year | GBIF Maps API × NLCD overlay (STEP 2's helper, all 10 years) | ~30–90 min |

## The full chain
```
export_county_landcover_panel.py ─┐
                                  ├─► 05_build_disparity_by_year.py ─► data/conus_disparity_by_year.csv ─► 06_plot…
build_county_obs_panel.py ────────┘
```
`build_county_obs_panel.py` reuses the **same** `../gbif_overlay.py` that STEP 2 uses, so the
per-year overlay is computed identically to the single-year 2023 analysis — it is just looped
over 2015–2024 and rolled up per county.

## Important: GBIF counts drift between harvests
The GBIF occurrence-density API returns slightly different totals on different days (records are
continuously added and back-filled). Re-running `build_county_obs_panel.py` will therefore shift
the **absolute** observation counts by a few percent. This moves the ratio metrics only
marginally: across a ~3–4% change in raw counts, the CONUS `%obs_on_ag` moves ~0.1–0.4 pp and
the disparity ratio is stable to ~0.05. The provided `county_obs_panel_long.csv` is one such
harvest (June 2025); the shipped `conus_disparity_by_year.csv` is regenerated from it so that
included data + included scripts reproduce the included result exactly.
