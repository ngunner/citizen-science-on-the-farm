# Pseudocode — how the yearly disparity numbers were produced

**File:** `reproduce_disparity_pointmethod.py`
**Invocation (once per year):** `python reproduce_disparity_pointmethod.py --year YYYY --zoom 12`
**Outputs:** `outputs/pointmethod_<year>_z12_RESULT.csv` (one row per year)
**Consolidated:** `outputs/pointmethod_disparity_2015_2024.csv`
**Plotted by:** `06_plot_disparity_over_time.py`

The quantity computed is

```
disparity(year) = (% of CONUS land that is farmland) ÷ (% of observations that fall on farmland)
```

with `> 1` meaning farmland receives less than its land-area share of observations.

---

## Top level

```
INPUT   year, zoom (12 ≈ 19 m cells → exact point classification)
OUTPUT  disparity, % obs on farmland, % farmland, total observations

1.  pct_farmland    ← FARMLAND_SHARE(year)            # Earth Engine, server-side
2.  total, on_farm  ← HARVEST_OBSERVATIONS(year, zoom) # GBIF × NLCD, tile by tile
3.  pct_obs_on_farm ← 100 × on_farm / total
4.  disparity       ← pct_farmland / pct_obs_on_farm
5.  WRITE one-row CSV to outputs/
```

---

## 1. FARMLAND_SHARE(year) — the denominator's numerator

Runs entirely on Earth Engine's servers; nothing is downloaded.

```
nlcd     ← USGS Annual NLCD land-cover image for `year`
              (matched by year token only, so it survives asset re-versioning,
               e.g. the C1V1 → C1V2 release)
ag_mask  ← nlcd == 81 (Hay/Pasture)  OR  nlcd == 82 (Cultivated Crops)

farm_km2 ← SUM of pixel areas WHERE ag_mask, over the CONUS box, at 300 m
land_km2 ← SUM of pixel areas WHERE nlcd is valid land, same box and scale

RETURN 100 × farm_km2 / land_km2          # ≈ 23.7–24.0 % across 2015–2024
```

## 2. HARVEST_OBSERVATIONS(year, zoom) — the observation side

CONUS is covered by ~240,000 web-Mercator tiles at zoom 12. Each tile is processed
independently and its two running sums are accumulated.

```
ag_image ← IF cell_size < 35 m  THEN binary ag mask        # point classification (zoom 12)
                               ELSE 30 m ag FRACTION       # coarse cross-check (zoom 9)

# --- partition work into resumable chunks -------------------------------
tile_rect ← the rectangle of tile indices [x0..x1] × [y0..y1] covering CONUS
chunks    ← split tile_rect into ~390 blocks of tile INDICES
            # NOTE: blocks of tile indices, NOT degree boxes. A degree box gets expanded
            # to every tile it OVERLAPS, so boundary tiles would be emitted by two
            # neighbouring chunks and counted twice (see "Known issues" below).

FOR each chunk:
    IF a checkpoint file for this chunk already exists: SKIP     # resumability
    chunk_total ← 0 ; chunk_on_farm ← 0

    FOR each tile in chunk, IN PARALLEL (24 threads):
        chunk_total, chunk_on_farm += TILE_SUMS(tile)

    WRITE checkpoint CSV (chunk index, chunk_total, chunk_on_farm) to LOCAL disk
          # local disk deliberately, never the cloud-synced project folder

# --- assemble ------------------------------------------------------------
total, on_farm ← SUM over all checkpoint files
```

### TILE_SUMS(tile) — the core overlay

The key idea: fetch GBIF counts and NLCD land cover **on the identical 512×512 grid**, so
cell `(px, py)` in one lines up with array element `[py, px]` in the other — a direct lookup,
with no per-point geometry operations.

```
cells ← GBIF Maps API occurrence-density tile (.mvt), decoded to (px, py, count)
        filters: year, country=US, hasCoordinate, no geospatial issues
        decoded top-origin so its row order matches the raster array
        (retry up to 4×; empty tile → return 0,0)

ag    ← Earth Engine computePixels(ag_image) rendered onto the SAME 512×512 grid
        via the tile's affine transform, in EPSG:3857
        (retry up to 4×, 45 s timeout; on failure return 0,0 — skip rather than misclassify)

FOR each (px, py, count) in cells:
    total   += count
    on_farm += count × ag[py, px]        # ag ∈ {0,1} at zoom 12 → binary point classification
                                          # ag ∈ [0,1] at zoom 9  → fractional weighting
RETURN total, on_farm
```

At zoom 12 each ~19 m cell lies inside a single 30 m NLCD pixel, so `ag[py,px]` is that
pixel's class — i.e. **each observation is labelled by the land cover directly beneath it**,
the same operation as the original R analysis' `exact_extract(obs × ag) / exact_extract(obs)`.

---

## Why it is structured this way

| Choice | Reason |
|---|---|
| GBIF **Maps API** (gridded counts) rather than an occurrence download | ~150 M points/year would be multi-GB; the density tiles give exact per-cell counts with no bulk download |
| Both grids rendered at **512×512 in EPSG:3857** | makes the overlay an array lookup instead of 150 M point-in-polygon tests |
| **Zoom 12 (~19 m)** | forces one cell inside one 30 m NLCD pixel → binary/point classification, matching the manuscript method |
| Per-chunk **checkpoints on local disk** | a multi-hour run survives crashes/sleep; cloud-synced folders intermittently fail on many small writes |
| Farmland share computed **server-side** | avoids downloading a CONUS-wide 30 m raster |

---

## Known issues and limitations

1. **Chunk-boundary double counting (FIXED 2025-07; affects the published run).**
   Chunks were originally degree boxes, and `mercantile.tiles()` returns every tile *overlapping*
   a box, so tiles on shared edges were harvested by both neighbours. Measured: 258,434
   tile-emissions vs 239,644 unique tiles = **+7.84 %**. Consequences:
   - `total_obs` and `obs_on_ag` in the ten `*_RESULT.csv` files are **inflated ≈ 7–8 %**
     (e.g. 2023 reported 150.4 M; the un-chunked zoom-9 harvest gives 139.6 M, −7.7 %).
   - **The disparity ratio is essentially unaffected**: duplicated tiles add to numerator and
     denominator alike, so the bias is only via boundary tiles being atypical in farmland
     share. Chunk boundaries are arbitrary graticule lines, uncorrelated with farmland; even
     if boundary tiles were 1 pp off the national mean, the disparity would move ≈ 0.03.
   The code now partitions **tile indices**, which cannot overlap. Checkpoints from the old
   scheme are named differently (`_t###`) so they are never mixed with new runs.

2. **Tiles where Earth Engine fails are skipped** (contribute 0 to both sums) rather than
   counted as non-farmland. This is the conservative choice — it cannot manufacture a
   disparity — but it means a systematic EE outage over one region would silently shrink
   coverage. Retries (4×) make this rare.

3. **Density-cell centroids, not exact coordinates.** GBIF returns counts per ~19 m cell; the
   whole count is attributed to that cell's land cover. At 19 m inside 30 m pixels this is
   point-equivalent, but it is not literally each record's coordinate.

4. **Live-data drift.** GBIF continuously adds and back-fills records, so re-running a past
   year returns a larger, slightly different total. Report results with a GBIF download DOI
   and access date. Ratios are far more stable than absolute counts.

5. **CONUS is a bounding box**, not a land polygon; the farmland share uses valid-NLCD-land as
   its denominator, which is why it differs by ~0.4 pp from a county-polygon integration.
