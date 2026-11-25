"""Recompute the km² of every subdivision exactly (geodesic, WGS84) and keep small areas to 3 significant
figures, so population densities are right for tiny units and for multi-part territories."""
import json, sys, math, shutil
ONLY = sys.argv[1:]
sys.argv = [sys.argv[0]]
import population as P
from pyproj import Geod
G = Geod(ellps='WGS84')

def polys(g):
    if g is None or g.is_empty: return []
    t = g.geom_type
    if t == 'Polygon': return [g]
    if hasattr(g, 'geoms'): return [p for x in g.geoms for p in polys(x)]
    return []

def km2(g):
    a = 0.0
    for p in polys(g):
        a += abs(G.geometry_area_perimeter(p)[0])
    return a / 1e6

def r3(x):
    if x <= 0: return 0
    if x >= 1000: return round(x)
    return float(f'{x:.3g}')

part = json.load(open('/home/claude/build/pop_part_all.json'))
shutil.copy('/home/claude/build/pop_part_all.json', '/home/claude/build/pop_part_all.bak.json')
changed = 0
for cid, c in part.items():
    if ONLY and cid not in ONLY: continue
    e, lv = P.levels_of(cid)
    for k, L in enumerate(sorted(lv)):
        if k >= len(c['L']): break
        arr = c['L'][k]
        for i, u in lv[L].items():
            if i >= len(arr): continue
            a = r3(km2(u['g']))
            if arr[i][4] != a: changed += 1
            arr[i][4] = a
    print(cid, sum(u[4] for u in c['L'][0]), flush=True)
json.dump(part, open('/home/claude/build/pop_part_all.json', 'w'), separators=(',', ':'))
print('changed', changed)
