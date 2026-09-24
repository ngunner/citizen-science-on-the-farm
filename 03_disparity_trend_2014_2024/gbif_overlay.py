#!/usr/bin/env python
"""
Combined GBIF-count x NLCD-ag overlay, per tile (no per-point GEE sampling).

For each density tile we (1) fetch GBIF occurrence counts (buffer-filtered) and
(2) fetch the NLCD agricultural-fraction array on the IDENTICAL 512-grid via
ee.data.computePixels. Because both grids align, cell (px,py) -> agfrac[py,px] is a
direct lookup. Returns per-cell rows: lon, lat, count, ag_frac, year.

ag_frac = mean of binary ag mask (NLCD 81+82) within the ~137 m cell (0..1).
obs_on_ag for a region = sum(count * ag_frac)  (unbiased; avoids boundary bias of
point classification). A 0.5 threshold reproduces v1-style point classification.

Run standalone for an Iowa 2023 smoke test.
"""
import warnings; warnings.filterwarnings("ignore")
import math, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests, mercantile, mapbox_vector_tile as mvt, numpy as np, pandas as pd
import ee

EXTENT = 512
BASE = "https://api.gbif.org/v2/map/occurrence/density/{z}/{x}/{y}.mvt"
R = 6378137.0
NLCD_IC = 'projects/sat-io/open-datasets/USGS/ANNUAL_NLCD/LANDCOVER'

def _merc_to_lonlat(mx, my):
    lon = mx / R * 180.0 / math.pi
    lat = (2*math.atan(math.exp(my / R)) - math.pi/2) * 180.0 / math.pi
    return lon, lat

def ag_image(year, scale_m=152.0):
    """Agricultural value (0-100) at the cell scale, for NLCD classes 81+82.
    - If the cell is COARSER than the 30 m NLCD pixel (scale_m >= ~35), return the true ag
      FRACTION (mean of the 30 m mask within the cell) — removes boundary over-assignment.
    - If the cell is FINER than 30 m (e.g. zoom 12 ~19 m), each cell lies within one NLCD
      pixel, so return the BINARY mask directly (point-equivalent classification; no aggregation)."""
    img = (ee.ImageCollection(NLCD_IC)
           # match the year token only, so this survives re-versioning (e.g. C1V1 -> C1V2)
           .filter(ee.Filter.stringContains('system:index', f'Annual_NLCD_LndCov_{year}_CU'))
           .first().select('b1'))
    ag01 = img.eq(81).Or(img.eq(82))
    if scale_m >= 35:
        ag = ag01.reduceResolution(ee.Reducer.mean(), maxPixels=1024).reproject(
             crs='EPSG:3857', scale=scale_m)
    else:
        ag = ag01  # sub-pixel cells: sample native 30 m mask (0/1) — point-equivalent
    return ag.multiply(100).toUint8().rename('agpct')

def _gbif_cells(session, z, x, y, params):
    """Return list of (px, py, count) for buffer-filtered cells."""
    url = BASE.format(z=z, x=x, y=y)
    content = b''
    for attempt in range(4):
        try:
            r = session.get(url, params=params, timeout=60)
            if r.status_code == 200:
                content = r.content; break
            if r.status_code == 404:
                return []
        except requests.RequestException:
            pass
        time.sleep(0.4*(attempt+1))
    if not content:
        return []
    try:
        # y_coord_down=True => top-origin py, matching the computePixels ag array AND the
        # lat formula below (my = top - py/EXTENT*span). The library default (bottom-origin)
        # caused a vertical-flip bug: cells got mirrored ag class + latitude within each tile.
        layer = mvt.decode(content, y_coord_down=True).get('occurrence')
    except Exception:
        return []
    if not layer:
        return []
    out = []
    for f in layer['features']:
        px, py = f['geometry']['coordinates']
        if 0 <= px < EXTENT and 0 <= py < EXTENT:
            c = f['properties'].get('total', 0)
            if c:
                out.append((px, py, c))
    return out

def _ag_array(agimg, z, x, y):
    b = mercantile.xy_bounds(x, y, z)
    sx = (b.right-b.left)/EXTENT; sy = (b.top-b.bottom)/EXTENT
    req = {'expression': agimg, 'fileFormat': 'NUMPY_NDARRAY',
           'grid': {'dimensions': {'width': EXTENT, 'height': EXTENT},
                    'affineTransform': {'scaleX': sx, 'shearX': 0, 'translateX': b.left,
                                        'shearY': 0, 'scaleY': -sy, 'translateY': b.top},
                    'crsCode': 'EPSG:3857'}}
    for attempt in range(4):
        try:
            # per-call timeout so a single stuck Earth Engine request cannot hang the run
            with ThreadPoolExecutor(max_workers=1) as _ex:
                arr = _ex.submit(ee.data.computePixels, req).result(timeout=45)
            return arr['agpct'] if arr.dtype.names else arr
        except Exception:
            time.sleep(0.5*(attempt+1))
    return None

def _process_tile(session, agimg, t, params):
    cells = _gbif_cells(session, t.z, t.x, t.y, params)
    if not cells:
        return []
    ag = _ag_array(agimg, t.z, t.x, t.y)
    b = mercantile.xy_bounds(t.x, t.y, t.z)
    left, top = b.left, b.top
    span_x = b.right-b.left; span_y = b.top-b.bottom
    rows = []
    for px, py, c in cells:
        frac = (ag[py, px]/100.0) if ag is not None else np.nan
        mx = left + (px+0.5)/EXTENT*span_x
        my = top - (py+0.5)/EXTENT*span_y
        lon, lat = _merc_to_lonlat(mx, my)
        rows.append((lon, lat, c, frac))
    return rows

def harvest_overlay(west, south, east, north, year, zoom=9, workers=12, country='US',
                    taxon_key=None, verbose=True):
    cell_m = 40075016.7 / (2**zoom * EXTENT)   # web-mercator cell size at this zoom (equator)
    agimg = ag_image(year, scale_m=cell_m)
    params = {'year': str(year), 'srs': 'EPSG:3857',
              'hasCoordinate': 'true', 'hasGeospatialIssue': 'false'}
    if country:
        params['country'] = country
    if taxon_key is not None:
        params['taxonKey'] = str(taxon_key)
    tiles = list(mercantile.tiles(west, south, east, north, zoom))
    if verbose:
        print(f"  {len(tiles)} tiles @ z{zoom} for {year}")
    rows = []
    with requests.Session() as s, ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_process_tile, s, agimg, t, params): t for t in tiles}
        done = 0
        for fut in as_completed(futs):
            rows.extend(fut.result()); done += 1
            if verbose and done % 500 == 0:
                print(f"    {done}/{len(tiles)} tiles, {len(rows):,} cells")
    df = pd.DataFrame(rows, columns=['lon', 'lat', 'count', 'ag_frac'])
    df['year'] = year
    return df

if __name__ == '__main__':
    ee.Initialize()
    t0 = time.time()
    df = harvest_overlay(-96.7, 40.3, -90.1, 43.6, 2023, zoom=9)  # Iowa-ish
    tot = df['count'].sum()
    on_ag = (df['count']*df['ag_frac']).sum()
    on_ag_pt = df.loc[df['ag_frac'] >= 0.5, 'count'].sum()
    print(f"Iowa-ish 2023: cells={len(df):,} total_obs={tot:,.0f} in {time.time()-t0:.1f}s")
    print(f"  obs_on_ag (fraction-weighted) = {on_ag:,.0f}  ({100*on_ag/tot:.1f}%)")
    print(f"  obs_on_ag (>=0.5 point-class) = {on_ag_pt:,.0f}  ({100*on_ag_pt/tot:.1f}%)")
    print(f"  (Iowa is ~85% ag land; obs typically under-represent ag, so expect < 85%)")
