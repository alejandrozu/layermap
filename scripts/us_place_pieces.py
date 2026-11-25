"""US places (2020 cities, towns, villages, CDPs) inside each county subdivision, plus the rest of the subdivision,
and census tracts cut at both lines.  Which pieces are real is decided by the 2020 census blocks (they nest in
subdivisions, places and tracts); slivers from the layers being generalised differently go to a neighbour, so every
subdivision and every place piece is split exactly, with no gaps or overlaps."""
import json, glob, collections, sys, time
import numpy as np, geopandas as gpd, shapely
sys.path.insert(0, '/home/claude/scripts')
import build_country as bc

R = '/home/claude/raw/us'
t0 = time.time()
def lap(*a): print(*a, round(time.time() - t0), 's', flush=True)
def clean(g): return [bc.polys_only(x) for x in shapely.make_valid(g.geometry.values)]
cs = gpd.read_file(f'{R}/cousub/cb_2023_us_cousub_500k.shp')[['GEOID', 'NAMELSAD', 'ALAND', 'geometry']].to_crs(4326); cs['geometry'] = clean(cs)
pl = gpd.read_file(f'{R}/place/cb_2020_us_place_500k.shp')[['GEOID', 'NAMELSAD', 'geometry']].to_crs(4326); pl['geometry'] = clean(pl)
tr = gpd.read_file(f'{R}/tract/cb_2023_us_tract_500k.shp')[['GEOID', 'NAMELSAD', 'geometry']].to_crs(4326); tr['geometry'] = clean(tr)
lap('loaded', len(cs), len(pl), len(tr))

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
T = set(tr.GEOID); P = set(pl.GEOID)
cs_tree = shapely.STRtree(cs.geometry.values); tr_tree = shapely.STRtree(tr.geometry.values)
csg, trg = list(cs.GEOID), list(tr.GEOID)
ST = {'al':'01','ak':'02','az':'04','ar':'05','ca':'06','co':'08','ct':'09','de':'10','dc':'11','fl':'12','ga':'13','hi':'15','id':'16','il':'17','in':'18','ia':'19','ks':'20','ky':'21','la':'22','me':'23','md':'24','ma':'25','mi':'26','mn':'27','ms':'28','mo':'29','mt':'30','ne':'31','nv':'32','nh':'33','nj':'34','nm':'35','ny':'36','nc':'37','nd':'38','oh':'39','ok':'40','or':'41','pa':'42','pr':'72','ri':'44','sc':'45','sd':'46','tn':'47','tx':'48','ut':'49','vt':'50','va':'51','wa':'53','wv':'54','wi':'55','wy':'56'}
c3 = collections.defaultdict(lambda: [0, 0])   # (cousub, place or '', tract) -> [pop, land m2]
for f in sorted(glob.glob(f'{R}/pl/*.750.txt')):
    stfp = ST[f.split('/')[-1][:2]]
    A = [l.rstrip('\n').split('|') for l in open(f)]
    B = [l.rstrip('\n').split('|') for l in open(f.replace('.750.txt', '.750p.txt'))]
    assert len(A) == len(B)
    keys, need_c, need_t = [], [], []
    for i, ((co, c, t, pop, al, lat, lon), b) in enumerate(zip(A, B)):
        kc = cmap.get(stfp + co + c); kt = stfp + co + t
        if kt not in T: kt = None
        kp = stfp + b[2] if b[2] != '99999' else ''
        if kp and kp not in P: kp = ''
        if kc is None: need_c.append(i)
        if kt is None: need_t.append(i)
        keys.append([kc, kp, kt])
    for need, tree, ids, j in ((need_c, cs_tree, csg, 0), (need_t, tr_tree, trg, 2)):
        if not need: continue
        pts = shapely.points([float(A[i][6]) for i in need], [float(A[i][5]) for i in need])
        a, b = tree.query(pts, predicate='within'); hit = dict(zip(a, b))
        miss = [q for q in range(len(need)) if q not in hit]
        if miss:
            nn = tree.query_nearest(pts[miss])
            for q, h in zip(nn[0], nn[1]): hit[miss[q]] = h
        for q, i in enumerate(need): keys[i][j] = ids[hit[q]]
    for k, r in zip(keys, A):
        v = c3[tuple(k)]; v[0] += int(r[3]); v[1] += int(r[4])
lap('blocks ->', len(c3), 'subdivision/place/tract combos')
json.dump({'|'.join(k): v for k, v in c3.items()}, open(f'{R}/place/combos3.json', 'w'), separators=(',', ':'))
c2 = collections.defaultdict(lambda: [0, 0])
for (a, p, t), v in c3.items(): w = c2[(a, p)]; w[0] += v[0]; w[1] += v[1]
by_cs = collections.defaultdict(dict)
for (a, p), v in c2.items(): by_cs[a][p] = v
by_cp = collections.defaultdict(dict)
for (a, p, t), v in c3.items(): by_cp[(a, p)][t] = v
plg = dict(zip(pl.GEOID, pl.geometry.values)); trgeo = dict(zip(tr.GEOID, tr.geometry.values))
pname = dict(zip(pl.GEOID, pl.NAMELSAD)); tname = dict(zip(tr.GEOID, tr.NAMELSAD)); csname = dict(zip(cs.GEOID, cs.NAMELSAD))

def km2(p): return p.area * 12391.6 * np.cos(np.radians(p.centroid.y))
def absorb(whole, kept):
    """slivers of `whole` outside every kept piece go to the piece they touch most"""
    rest = bc.polys_only(shapely.difference(whole, shapely.union_all([k[1] for k in kept])))
    if rest is None: return 0
    n = 0
    for q in getattr(rest, 'geoms', [rest]):
        if q.area <= 0: continue
        qb = q.buffer(1e-5)
        j = int(np.argmax([qb.intersection(k[1]).area for k in kept]))
        kept[j][1] = bc.polys_only(shapely.union_all([kept[j][1], q])); n += 1
    return n

# ---- level 6: places in each subdivision, and the rest of it
L6 = []
for cg, cgeom in zip(csg, cs.geometry.values):
    if cgeom is None: continue
    cand = by_cs.get(cg, {})
    kept = []
    for p, (pop, al) in sorted(cand.items(), key=lambda x: -x[1][1]):
        if not p or not (pop >= 1 or al >= 20_000): continue
        g = bc.polys_only(shapely.intersection(cgeom, plg[p]))
        if g is None or g.is_empty or km2(g) < 0.002: continue
        kept.append([p, g])
    rv = cand.get('')
    if rv and (rv[0] >= 1 or rv[1] >= 20_000) and kept:
        g = bc.polys_only(shapely.difference(cgeom, shapely.union_all([k[1] for k in kept])))
        if g is not None and km2(g) >= 0.002: kept.append(['', g])
    if not kept:
        best = max(cand.items(), key=lambda x: (x[1][1], x[1][0]))[0] if cand else ''
        kept = [[best, cgeom]]
    elif len(kept) == 1: kept[0][1] = cgeom
    else: absorb(cgeom, kept)
    for p, g in kept: L6.append([cg, p, g])
lap('level 6 pieces', len(L6))
pc6 = collections.Counter(p for _, p, _ in L6 if p)
n6 = collections.Counter(c for c, _, _ in L6)
def name6(c, p):
    if p: return pname[p] + (' (part)' if pc6[p] > 1 else '')
    return ('Rest of ' if n6[c] > 1 else '') + csname[c]

# ---- level 7: tracts in each of those pieces
L7 = []
for i6, (cg, p, g6) in enumerate(L6):
    cand = by_cp.get((cg, p), {})
    tot = sum(v[1] for v in cand.values()) or 1
    kept = []
    for t, (pop, al) in sorted(cand.items(), key=lambda x: -x[1][1]):
        if t not in trgeo or not (al >= 50_000 or pop >= 50 or (al > 0 and al >= 0.02 * tot)): continue
        g = bc.polys_only(shapely.intersection(g6, trgeo[t]))
        if g is None or g.is_empty or km2(g) < 0.01: continue
        kept.append([t, g])
    if not kept:
        best = max(cand.items(), key=lambda x: (x[1][1], x[1][0]))[0] if cand else None
        if best is None or best not in trgeo:
            pt = g6.representative_point(); h = tr_tree.query(pt, predicate='within')
            best = trg[h[0]] if len(h) else trg[tr_tree.query_nearest(pt)[0]]
        kept = [[best, g6]]
    elif len(kept) == 1: kept[0][1] = g6
    else: absorb(g6, kept)
    for t, g in kept: L7.append([i6, t, g])
    if i6 % 10000 == 0: lap(i6, len(L7))
pc7 = collections.Counter(t for _, t, _ in L7)
out6 = gpd.GeoDataFrame([[c, p, name6(c, p), g] for c, p, g in L6], columns=['cs', 'pl', 'name', 'geometry'], crs=4326)
out7 = gpd.GeoDataFrame([[L6[i][0], L6[i][1], t, tname[t] + (' (part)' if pc7[t] > 1 else ''), i, g] for i, t, g in L7],
                        columns=['cs', 'pl', 'tr', 'name', 'p6', 'geometry'], crs=4326)
out6.to_file(f'{R}/place/pieces6.gpkg', driver='GPKG'); out7.to_file(f'{R}/place/pieces7.gpkg', driver='GPKG')
lap('wrote level 6', len(out6), 'level 7', len(out7), 'split tracts', sum(1 for v in pc7.values() if v > 1))
