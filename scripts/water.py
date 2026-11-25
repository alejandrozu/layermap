"""Rivers + small lakes for the elevation layer -> site/data/lay/water.gz.txt
Format (after base64 + gunzip): {"r": [[minzoom, weight, coords...]], "l": [[minzoom, ring, ring...]]}
coords: ints in 1/1000 degree, first pair absolute, then deltas (lon, lat interleaved).
"""
import json, gzip, base64, shapely
import geopandas as gpd
import pandas as pd

R = '/home/claude/raw/ne'
riv = pd.concat([gpd.read_file(f'{R}/rivers/{f}.zip')[['min_zoom', 'strokeweig', 'featurecla', 'geometry']]
                 for f in ('ne_10m_rivers_lake_centerlines_scale_rank', 'ne_10m_rivers_europe', 'ne_10m_rivers_north_america')])
lk = pd.concat([gpd.read_file(f'{R}/lakes/ne_10m_lakes.shp').query('scalerank > 2 or featurecla not in ["Lake", "Reservoir"]'),
                gpd.read_file(f'{R}/rivers/ne_10m_lakes_europe.zip'), gpd.read_file(f'{R}/rivers/ne_10m_lakes_north_america.zip')])
lk = lk[['min_zoom', 'geometry']]


def enc(coords):
    out = []; px = py = 0
    for x, y in coords:
        ix, iy = round(x * 1000), round(y * 1000)
        if out and ix == px and iy == py: continue
        out += [ix - px, iy - py] if out else [ix, iy]
        px, py = ix, iy
    return out


r_out = []
for mz, w, fc, g in riv.itertuples(index=False):
    if g is None or (isinstance(w, float) and w != w): w = 0.2
    if g is None: continue
    tol = 0.002 if mz >= 6 else 0.003
    for line in getattr(g, 'geoms', [g]):
        line = line.simplify(tol)
        c = enc(line.coords)
        if len(c) >= 4: r_out.append([round(float(mz), 1), round(float(w), 2)] + c)
l_out = []
for mz, g in lk.itertuples(index=False):
    if g is None: continue
    g = shapely.make_valid(g)
    for poly in getattr(g, 'geoms', [g]):
        if poly.geom_type != 'Polygon' or poly.area < 1e-5: continue
        poly = poly.simplify(0.002)
        if poly.is_empty or poly.geom_type != 'Polygon': continue
        rings = [enc(poly.exterior.coords)] + [enc(i.coords) for i in poly.interiors]
        rings = [r for r in rings if len(r) >= 6]
        if rings: l_out.append([round(float(mz if mz == mz else 7), 1)] + rings)
js = json.dumps({'r': r_out, 'l': l_out}, separators=(',', ':'))
gz = gzip.compress(js.encode(), 9)
open('/home/claude/site/data/lay/water.gz.txt', 'w').write(base64.b64encode(gz).decode())
print('rivers', len(r_out), 'lakes', len(l_out), 'json', len(js) // 1000, 'KB', 'gz', len(gz) // 1000, 'KB')
