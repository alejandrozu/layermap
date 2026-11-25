"""US census tracts cut at county subdivision lines.
Every county subdivision (2023 polygons, the map's level 5) is split into the parts of the census tracts that
really lie in it according to the 2020 census blocks (which nest in both); slivers that only come from the two
layers being generalised differently go to the neighbouring part, so each subdivision keeps its exact shape."""
import json, glob, collections, sys, time
import numpy as np, geopandas as gpd, shapely, pandas as pd
sys.path.insert(0, '/home/claude/scripts')
import build_country as bc

R = '/home/claude/raw/us'
t0 = time.time()
cs = gpd.read_file(f'{R}/cousub/cb_2023_us_cousub_500k.shp')[['GEOID', 'NAMELSAD', 'ALAND', 'geometry']].to_crs(4326)
tr = gpd.read_file(f'{R}/tract/cb_2023_us_tract_500k.shp')[['GEOID', 'NAMELSAD', 'geometry']].to_crs(4326)
cs['geometry'] = [bc.polys_only(g) for g in shapely.make_valid(cs.geometry.values)]
tr['geometry'] = [bc.polys_only(g) for g in shapely.make_valid(tr.geometry.values)]
print('loaded', len(cs), len(tr), round(time.time() - t0), 's', flush=True)

# ---- 2020 county subdivision code -> 2023 polygon (same rules as the population matching)
rec = json.load(open('/home/claude/raw/pop/official/us_cousub2020.json'))
G = set(cs.GEOID); aland = dict(zip(cs.GEOID, cs.ALAND))
by_st, by_name = collections.defaultdict(list), collections.defaultdict(list)
for g, n in zip(cs.GEOID, cs.NAMELSAD): by_st[g[:2] + g[5:]].append(g); by_name[(g[:5], n.lower())].append(g)
cmap = {}
for k, (name, cnt, lon, lat, a20) in rec.items():
    if k in G: cmap[k] = k; continue
    alt = by_st.get(k[:2] + k[5:], [])
    if len(alt) == 1: cmap[k] = alt[0]; continue
    alt = by_name.get((k[:5], name.lower()), [])
    if len(alt) == 1 and a20 and abs(aland[alt[0]] / a20 - 1) < 0.03: cmap[k] = alt[0]
T = set(tr.GEOID)
cs_tree = shapely.STRtree(cs.geometry.values); tr_tree = shapely.STRtree(tr.geometry.values)
csg, trg = list(cs.GEOID), list(tr.GEOID)

# ---- blocks -> (cousub 2023, tract 2023)
combo = collections.defaultdict(lambda: [0, 0])   # (cs, tr) -> [pop, aland m2]
nb = nsp_c = nsp_t = 0
for f in sorted(glob.glob(f'{R}/pl/*.750.txt')):
    st = None; rows = []
    for line in open(f):
        co, c, t, pop, al, lat, lon = line.rstrip('\n').split('|')
        rows.append((co, c, t, int(pop), int(al), float(lat), float(lon)))
    stfp = {'al':'01','ak':'02','az':'04','ar':'05','ca':'06','co':'08','ct':'09','de':'10','dc':'11','fl':'12','ga':'13','hi':'15','id':'16','il':'17','in':'18','ia':'19','ks':'20','ky':'21','la':'22','me':'23','md':'24','ma':'25','mi':'26','mn':'27','ms':'28','mo':'29','mt':'30','ne':'31','nv':'32','nh':'33','nj':'34','nm':'35','ny':'36','nc':'37','nd':'38','oh':'39','ok':'40','or':'41','pa':'42','pr':'72','ri':'44','sc':'45','sd':'46','tn':'47','tx':'48','ut':'49','vt':'50','va':'51','wa':'53','wv':'54','wi':'55','wy':'56'}[f.split('/')[-1][:2]]
    need_c, need_t = [], []
    keys = []
    for i, (co, c, t, pop, al, lat, lon) in enumerate(rows):
        kc = cmap.get(stfp + co + c); kt = stfp + co + t
        if kt not in T: kt = None
        if kc is None: need_c.append(i)
        if kt is None: need_t.append(i)
        keys.append([kc, kt])
    for need, tree, ids, j in ((need_c, cs_tree, csg, 0), (need_t, tr_tree, trg, 1)):
        if not need: continue
        pts = shapely.points([rows[i][6] for i in need], [rows[i][5] for i in need])
        a, b = tree.query(pts, predicate='within')
        hit = dict(zip(a, b))
        miss = [q for q in range(len(need)) if q not in hit]
        if miss:
            nn = tree.query_nearest(pts[miss])
            for q, h in zip(nn[0], nn[1]): hit[miss[q]] = h
        for q, i in enumerate(need): keys[i][j] = ids[hit[q]]
        if j == 0: nsp_c += len(need)
        else: nsp_t += len(need)
    for (kc, kt), r in zip(keys, rows):
        v = combo[(kc, kt)]; v[0] += r[3]; v[1] += r[4]
    nb += len(rows)
print('blocks', nb, 'placed by point: cousub', nsp_c, 'tract', nsp_t, 'combos', len(combo), round(time.time() - t0), 's', flush=True)
json.dump({f'{a}|{b}': v for (a, b), v in combo.items()}, open(f'{R}/tract/combos.json', 'w'), separators=(',', ':'))

# ---- pieces
by_cs = collections.defaultdict(dict)
for (a, b), v in combo.items(): by_cs[a][b] = v
trg_idx = {g: i for i, g in enumerate(trg)}
tname = dict(zip(tr.GEOID, tr.NAMELSAD))
rows = []
nsl = nfall = 0
for ci, (cg, cgeom) in enumerate(zip(csg, cs.geometry.values)):
    if cgeom is None: continue
    cand = by_cs.get(cg, {})
    tot_al = sum(v[1] for v in cand.values()) or 1
    kept = []
    for tg, (pop, al) in sorted(cand.items(), key=lambda x: -x[1][1]):
        if tg not in trg_idx: continue
        if not (al >= 50_000 or pop >= 50 or (al >= 0.02 * tot_al and al > 0)): continue
        p = bc.polys_only(shapely.intersection(cgeom, tr.geometry.values[trg_idx[tg]]))
        if p is None or p.is_empty: continue
        akm = p.area * 12391.6 * np.cos(np.radians(p.centroid.y))
        if akm < 0.01: continue
        kept.append([tg, p])
    if not kept:
        # nothing usable: the whole subdivision is one part of its main tract
        best = max(cand.items(), key=lambda x: (x[1][1], x[1][0]))[0] if cand else None
        if best is None or best not in trg_idx:
            h = tr_tree.query(cgeom.representative_point(), predicate='within')
            best = trg[h[0]] if len(h) else trg[tr_tree.query_nearest(cgeom.representative_point())[0]]
        rows.append([cg, best, cgeom]); nfall += 1; continue
    if len(kept) == 1:
        rows.append([cg, kept[0][0], cgeom]); continue
    # leftover slivers go to the part they touch most
    rest = bc.polys_only(shapely.difference(cgeom, shapely.union_all([k[1] for k in kept])))
    if rest is not None:
        for q in getattr(rest, 'geoms', [rest]):
            if q.area <= 0: continue
            qb = q.buffer(1e-5)
            j = int(np.argmax([qb.intersection(k[1]).area for k in kept]))
            kept[j][1] = bc.polys_only(shapely.union_all([kept[j][1], q]))
            nsl += 1
    for tg, p in kept: rows.append([cg, tg, p])
    if ci % 5000 == 0: print(ci, len(rows), round(time.time() - t0), 's', flush=True)
pc = gpd.GeoDataFrame(rows, columns=['cs', 'tr', 'geometry'], crs=4326)
parts = pc.tr.value_counts()
pc['name'] = [tname.get(t, 'Census tract') + (' (part)' if parts[t] > 1 else '') for t in pc.tr]
pc.to_file(f'{R}/tract/pieces.gpkg', driver='GPKG')
a = pc.to_crs('+proj=eqearth').area / 1e6
print('pieces', len(pc), 'tracts', pc.tr.nunique(), 'split tracts', int((parts > 1).sum()), 'slivers merged', nsl, 'fallback', nfall,
      'area km2 median', round(float(a.median()), 2), 'p10', round(float(a.quantile(.1)), 3), round(time.time() - t0), 's')
