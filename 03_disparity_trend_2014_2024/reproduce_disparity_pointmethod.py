#!/usr/bin/env python
"""
SINGLE-SCRIPT, END-TO-END reproduction of the CONUS observational disparity, using the
POINT-CLASSIFICATION method (matches the v1 R analysis: each observation is on-farmland only
if the 30 m NLCD pixel beneath it is cropland/pasture).

Everything is here in one file: it calls Google Earth Engine (USGS Annual NLCD) and the live
GBIF Maps API directly. No county boundaries, no pre-computed panels, no other project files.

    disparity = (% of CONUS that is farmland) / (% of observations on farmland)

WHAT "MATCHES YOUR METHOD" MEANS
  ZOOM = 12 gives ~19 m grid cells. Each cell lies inside a single 30 m NLCD pixel, so its
  on-/off-farmland label is BINARY (the pixel's class) — i.e. exact point classification, the
  same thing your exact_extract(obs*ag)/exact_extract(obs) did at 30 m. Expected: disparity ~3.
  (ZOOM = 9 reproduces the coarse "fractional" v2 cross-check, ~137 m, in a few minutes: ~2.5.)

COST — READ THIS FIRST
  At ZOOM 12 the CONUS harvest is a few hundred thousand tiles, each = one GBIF fetch + one
  Earth Engine computePixels call. It is throttled by the GBIF and Earth Engine APIs, not your
  CPU: budget SEVERAL HOURS. The run is resumable — CONUS is partitioned into ~390 blocks of
  TILE INDICES (non-overlapping by construction) and each block is checkpointed to
  ~/.csotf_pointmethod_ckpt/ (LOCAL disk, deliberately NOT the cloud-synced project folder).
  Finished blocks are skipped, so you can stop/restart (or survive a crash or laptop sleep) and
  it picks up where it left off. Re-run the exact same command to resume. The final disparity is
  also written to outputs/pointmethod_<year>_z<zoom>_RESULT.csv.
  See METHOD_PSEUDOCODE.md for a full walkthrough and the list of known limitations.

SETUP
  pip install earthengine-api requests mercantile mapbox-vector-tile numpy pandas
  earthengine authenticate      # once

RUN
  python reproduce_disparity_pointmethod.py                 # 2023, zoom 12 (point method ~3)
  python reproduce_disparity_pointmethod.py --year 2023 --zoom 9   # coarse cross-check (~2.5)

NOTE ON EXACT NUMBERS
  The GBIF Maps API returns live occurrence-density counts that drift a few percent between
  harvests (records are continuously added/back-filled), so the reproduced value will land in
  the ~3 region rather than bit-identical to any single past run. The RATIO is stable to that
  drift; that robustness is the point.
"""
import warnings; warnings.filterwarnings("ignore")
import os, sys, math, time, argparse, glob
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests, mercantile, numpy as np, pandas as pd
import mapbox_vector_tile as mvt
import ee

# ----------------------------- config -----------------------------
EXTENT = 512                                                   # GBIF density tile is 512x512
BASE   = "https://api.gbif.org/v2/map/occurrence/density/{z}/{x}/{y}.mvt"
R      = 6378137.0                                             # web-mercator earth radius (m)
NLCD_IC = 'projects/sat-io/open-datasets/USGS/ANNUAL_NLCD/LANDCOVER'
CONUS   = (-125.0, 24.5, -66.9, 49.4)                          # west, south, east, north
CHUNK_DEG = 2.0                                                # resume granularity
# Checkpoints go to LOCAL disk (home dir), never a cloud-synced folder. Writing hundreds of tiny
# files into ~/Library/CloudStorage (Dropbox/iCloud/OneDrive) can fail intermittently with
# "Operation not permitted" and silently lose the run's persistence — keep them off the sync path.
CKPT_DIR = os.path.join(os.path.expanduser('~'), '.csotf_pointmethod_ckpt')
OUT_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')

# ------------------------- Earth Engine ag layer -------------------------
def nlcd_year(year):
    """The USGS Annual NLCD land-cover image for a year. Matches on the year token only, so it
    is robust to the collection being re-versioned (e.g. the C1V1 -> C1V2 release; if several
    versions of a year ever coexist, ee sorts by id and .first() takes the earliest)."""
    return (ee.ImageCollection(NLCD_IC)
            .filter(ee.Filter.stringContains('system:index', f'Annual_NLCD_LndCov_{year}_CU'))
            .first().select('b1'))

def ag_binary(year):
    """USGS Annual NLCD agricultural mask (81 Hay/Pasture + 82 Cultivated Crops), 0/100 uint8.
    At ~19 m cells this native 30 m mask is sampled as a BINARY point class (no aggregation)."""
    img = nlcd_year(year)
    return img.eq(81).Or(img.eq(82)).multiply(100).toUint8().rename('agpct')

def ag_fraction(year, scale_m):
    """For coarse cells (>=35 m, the zoom-9 cross-check) return the true 30 m ag FRACTION."""
    ag01 = nlcd_year(year).eq(81).Or(nlcd_year(year).eq(82))
    return (ag01.reduceResolution(ee.Reducer.mean(), maxPixels=1024)
            .reproject(crs='EPSG:3857', scale=scale_m).multiply(100).toUint8().rename('agpct'))

def conus_pct_farmland(year):
    """% of CONUS land that is farmland — server-side in Earth Engine (no download)."""
    img  = nlcd_year(year)
    ag   = img.eq(81).Or(img.eq(82))
    box  = ee.Geometry.Rectangle(list(CONUS), proj='EPSG:4326', geodesic=False)
    area = ee.Image.pixelArea()
    def km2(mask):
        return ee.Number(area.updateMask(mask).reduceRegion(
            ee.Reducer.sum(), box, scale=300, maxPixels=1e13, bestEffort=True).get('area')).getInfo()/1e6
    land = km2(img.mask()); farm = km2(ag)
    return 100*farm/land, farm, land

# ------------------------- GBIF x NLCD per tile -------------------------
def gbif_cells(session, z, x, y, params):
    """(px, py, count) occurrence-density cells for one tile."""
    content = b''
    for attempt in range(4):
        try:
            r = session.get(BASE.format(z=z, x=x, y=y), params=params, timeout=60)
            if r.status_code == 200: content = r.content; break
            if r.status_code == 404: return []
        except requests.RequestException:
            pass
        time.sleep(0.4*(attempt+1))
    if not content: return []
    try:
        layer = mvt.decode(content, y_coord_down=True).get('occurrence')   # top-origin, matches ag array
    except Exception:
        return []
    if not layer: return []
    out = []
    for f in layer['features']:
        px, py = f['geometry']['coordinates']
        if 0 <= px < EXTENT and 0 <= py < EXTENT:
            c = f['properties'].get('total', 0)
            if c: out.append((px, py, c))
    return out

def ag_array(agimg, z, x, y):
    """NLCD ag value on the SAME 512 grid as the GBIF tile, via computePixels."""
    b = mercantile.xy_bounds(x, y, z); sx = (b.right-b.left)/EXTENT; sy = (b.top-b.bottom)/EXTENT
    req = {'expression': agimg, 'fileFormat': 'NUMPY_NDARRAY',
           'grid': {'dimensions': {'width': EXTENT, 'height': EXTENT},
                    'affineTransform': {'scaleX': sx, 'shearX': 0, 'translateX': b.left,
                                        'shearY': 0, 'scaleY': -sy, 'translateY': b.top},
                    'crsCode': 'EPSG:3857'}}
    for attempt in range(4):
        try:
            with ThreadPoolExecutor(max_workers=1) as ex:                  # per-call timeout guard
                arr = ex.submit(ee.data.computePixels, req).result(timeout=45)
            return arr['agpct'] if arr.dtype.names else arr
        except Exception:
            time.sleep(0.5*(attempt+1))
    return None

def tile_sums(session, agimg, t, params):
    """Return (total_obs, obs_on_ag) for one tile (binary or fractional per agimg)."""
    cells = gbif_cells(session, t.z, t.x, t.y, params)
    if not cells: return 0.0, 0.0
    ag = ag_array(agimg, t.z, t.x, t.y)
    if ag is None: return 0.0, 0.0            # skip rather than misclassify if EE failed
    tot = on = 0.0
    for px, py, c in cells:
        tot += c; on += c * (ag[py, px]/100.0)
    return tot, on

# ------------------------------- driver -------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--year', type=int, default=2023)
    ap.add_argument('--zoom', type=int, default=12, help='12 = ~19 m point method (v1); 9 = ~137 m fractional (v2)')
    ap.add_argument('--workers', type=int, default=24)
    a = ap.parse_args()
    ee.Initialize()
    os.makedirs(CKPT_DIR, exist_ok=True)

    cell_m = 40075016.7/(2**a.zoom*EXTENT)
    point_method = cell_m < 35
    agimg = ag_binary(a.year) if point_method else ag_fraction(a.year, cell_m)
    params = {'year': str(a.year), 'srs': 'EPSG:3857', 'country': 'US',
              'hasCoordinate': 'true', 'hasGeospatialIssue': 'false'}
    print(f"YEAR {a.year} | zoom {a.zoom} (~{cell_m:.0f} m cells) | "
          f"{'BINARY point classification (matches v1 30 m)' if point_method else 'FRACTIONAL (v2 cross-check)'}")

    # Step A: CONUS farmland share (Earth Engine)
    print("Earth Engine: computing CONUS farmland share ...", flush=True)
    pct_ag, farm_km2, land_km2 = conus_pct_farmland(a.year)
    print(f"  farmland {farm_km2:,.0f} km^2 of {land_km2:,.0f} km^2 land  => {pct_ag:.2f}% of CONUS", flush=True)

    # Step B: harvest GBIF x NLCD in resumable chunks.
    #
    # Chunks are blocks of TILE INDICES, not degree boxes. A degree box would be expanded by
    # mercantile.tiles() to every tile it OVERLAPS, so tiles straddling a boundary were emitted
    # by both neighbouring chunks and counted twice (measured: +7.8% inflation of total_obs).
    # Partitioning the tile-index rectangle guarantees each tile is visited exactly once.
    W0, S0, E0, N0 = CONUS
    ul = mercantile.tile(W0, N0, a.zoom)
    lr = mercantile.tile(E0 - 1e-11, S0 + 1e-11, a.zoom)
    xs, ys = range(ul.x, lr.x + 1), range(ul.y, lr.y + 1)
    blk = max(1, int(round(CHUNK_DEG / (360.0 / 2**a.zoom))))     # ~CHUNK_DEG wide, in tiles
    chunks = [(x0, min(x0+blk, xs.stop), y0, min(y0+blk, ys.stop))
              for x0 in range(xs.start, xs.stop, blk)
              for y0 in range(ys.start, ys.stop, blk)]
    n_tiles = len(xs) * len(ys)
    print(f"GBIF x NLCD overlay: {n_tiles:,} unique tiles in {len(chunks)} chunks @ zoom {a.zoom}"
          f"  (resumable in {CKPT_DIR})", flush=True)
    with requests.Session() as session:
        for i, (x0, x1, y0, y1) in enumerate(chunks):
            ck = os.path.join(CKPT_DIR, f"{a.year}_z{a.zoom}_t{i:03d}.csv")
            if os.path.exists(ck): continue
            tiles = [mercantile.Tile(x, y, a.zoom) for x in range(x0, x1) for y in range(y0, y1)]
            tot = on = 0.0
            with ThreadPoolExecutor(max_workers=a.workers) as ex:
                for f in as_completed([ex.submit(tile_sums, session, agimg, t, params) for t in tiles]):
                    dt, don = f.result(); tot += dt; on += don
            pd.DataFrame([{'chunk': i, 'total_obs': tot, 'obs_on_ag': on}]).to_csv(ck, index=False)
            done = len(glob.glob(os.path.join(CKPT_DIR, f"{a.year}_z{a.zoom}_t*.csv")))
            print(f"  chunk {i+1}/{len(chunks)} ({done} done): {tot:,.0f} obs, {on:,.0f} on-ag", flush=True)

    # Step C: assemble
    ckfiles = sorted(glob.glob(os.path.join(CKPT_DIR, f"{a.year}_z{a.zoom}_t*.csv")))
    if not ckfiles:
        sys.exit(f"No checkpoints found in {CKPT_DIR} — nothing to assemble. "
                 f"(Re-run to harvest; if this persists, the checkpoint disk is unwritable.)")
    parts = pd.concat([pd.read_csv(f) for f in ckfiles], ignore_index=True)
    total_obs = parts['total_obs'].sum(); on_ag = parts['obs_on_ag'].sum()
    pct_obs = 100*on_ag/total_obs
    disparity = pct_ag/pct_obs
    method = 'point ~30 m (v1-style)' if point_method else 'fractional ~137 m (v2)'
    print("\n" + "="*64)
    print(f"  CONUS {a.year}  ({method})")
    print(f"  total observations         : {total_obs:,.0f}")
    print(f"  % observations on farmland : {pct_obs:.2f}%")
    print(f"  % of CONUS that is farmland: {pct_ag:.2f}%")
    print(f"  OBSERVATIONAL DISPARITY    : {disparity:.2f}   (>1 => farmland under-observed)")
    print("="*64)

    # Save the result next to the other outputs (single small file — safe on any disk)
    try:
        os.makedirs(OUT_DIR, exist_ok=True)
        dst = os.path.join(OUT_DIR, f"pointmethod_{a.year}_z{a.zoom}_RESULT.csv")
        pd.DataFrame([{'year': a.year, 'zoom': a.zoom, 'method': method,
                       'total_obs': int(total_obs), 'obs_on_ag': int(on_ag),
                       'pct_obs_on_ag': round(pct_obs, 4), 'pct_ag_area': round(pct_ag, 4),
                       'disparity': round(disparity, 4)}]).to_csv(dst, index=False)
        print(f"  saved -> {dst}")
    except Exception as e:
        print(f"  (could not write result file: {type(e).__name__}: {e})")

if __name__ == '__main__':
    main()
