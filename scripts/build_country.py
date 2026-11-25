"""Build the nested level files for one country.
import warnings; warnings.filterwarnings('ignore')

A country spec is a list of levels, top -> bottom. Each level is a dict:
  {'label': (singular, plural), 'geo': [source, ...]}   polygons (finest level must be geo)
  {'label': ..., 'group': {group_name: [names of the level below]}}  grouping of the level below
Sources: ('gb', ISO, 'ADMk') | ('nuts', year, lvl, CNTR) | ('lau', CNTR) | ('gdf', GeoDataFrame)

Every finest unit is assigned to each geo level independently by its interior point, and the
level keys are cumulative tuples, so the result always nests exactly (an intermediate unit that
straddles a higher boundary is split). Geometry: finest units are simplified (mapshaper,
topology-preserving), clipped to the Natural Earth country frame, and frame gaps are given to
the neighbouring unit; every higher level is the dissolve of its finest units.
"""
import json, os, re, subprocess, sys, unicodedata, math, tempfile
import numpy as np, pandas as pd, geopandas as gpd, shapely
from shapely.affinity import translate

MS = '/home/claude/tools/node_modules/.bin/mapshaper'
RAW = '/home/claude/raw'
OUT = '/home/claude/build/chunks'
FRAME = None

def frame():
    global FRAME
    if FRAME is None:
        FRAME = gpd.read_file('/home/claude/build/frame.geojson').set_index('id')
    return FRAME

def fixname(s):
    s = str(s).strip()
    if 'Ã' in s or 'Â' in s:
        try: s = s.encode('latin1').decode('utf8')
        except Exception: pass
    return re.sub(r'\s+', ' ', s)

def norm(s):
    s = unicodedata.normalize('NFKD', fixname(s)).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()

DEP_NAMES = {'FRO': 'Faroe Islands', 'BLM': 'Saint Barthélemy', 'CUW': 'Curaçao', 'ALD': 'Åland', 'MAF': 'Saint Martin',
             'COK': 'Cook Islands', 'CYM': 'Cayman Islands', 'FLK': 'Falkland Islands', 'PCN': 'Pitcairn Islands',
             'TCA': 'Turks and Caicos Islands', 'MNP': 'Northern Mariana Islands', 'PYF': 'French Polynesia',
             'ESB': 'Dhekelia (Sovereign Base Area)', 'WSB': 'Akrotiri (Sovereign Base Area)', 'CLP': 'Clipperton Island',
             'SHN': 'Saint Helena, Ascension & Tristan da Cunha', 'IOT': 'British Indian Ocean Territory',
             'ATC': 'Ashmore and Cartier Islands', 'CSI': 'Coral Sea Islands', 'IOA': 'Christmas & Cocos Islands',
             'HMD': 'Heard & McDonald Islands', 'SPM': 'Saint Pierre and Miquelon', 'WLF': 'Wallis and Futuna',
             'ATF': 'French Southern & Antarctic Lands', 'UMI': 'U.S. Minor Outlying Islands', 'VIR': 'U.S. Virgin Islands'}
PIECES = None
def pieces():
    global PIECES
    if PIECES is None: PIECES = gpd.read_file('/home/claude/build/pieces.geojson').set_index('id244')
    return PIECES

_cache = {}
def load_src(src):
    key = repr(src) if src[0] != 'gdf' else None
    if key and key in _cache: return _cache[key]
    kind = src[0]
    if kind in ('gb', 'gbh'):
        g = gpd.read_file(f'{RAW}/{kind}/{src[1]}_{src[2]}.geojson')
        g['name'] = g.shapeName.map(fixname)
    elif kind == 'ne1':
        if 'ne1' not in _cache:
            _cache['ne1'] = gpd.read_file(f'{RAW}/ne/admin1/ne_10m_admin_1_states_provinces.shp')
        a = _cache['ne1']
        g = a[a.adm0_a3 == src[1]].copy()
        g['name'] = g.name.map(fixname)
    elif kind == 'file':
        g = gpd.read_file(src[1])
        g = g[g[src[2]].notna()].copy()
        g['name'] = g[src[2]].map(fixname)
    elif kind == 'nuts':
        _, year, lvl, cc = src
        g = gpd.read_file(f'{RAW}/gisco/NUTS_RG_01M_{year}_4326_LEVL_{lvl}.geojson')
        g = g[g.CNTR_CODE == cc].copy()
        g['name'] = g.NAME_LATN.map(fixname)
    elif kind == 'lau':
        if 'lau' not in _cache:
            _cache['lau'] = gpd.read_file(f'{RAW}/gisco/LAU_RG_01M_2023_4326.gpkg')
        l = _cache['lau']
        g = l[l.CNTR_CODE == src[1]].copy()
        g['name'] = g.LAU_NAME.map(fixname)
    elif kind == 'gdf':
        g = src[1].copy()
        extra = [c for c in g.columns if c.startswith('_')]
    elif kind == 'dep':
        p = pieces().loc[[src[1]]]
        g = gpd.GeoDataFrame({'name': [DEP_NAMES.get(src[1], fixname(p.n244.iloc[0]))]}, geometry=[p.geometry.iloc[0]], crs=4326)
    elif kind == 'piecepart':
        _, code, bbox, nm = src
        geom = pieces().loc[code].geometry.intersection(shapely.box(*bbox))
        g = gpd.GeoDataFrame({'name': [nm]}, geometry=[geom], crs=4326)
    elif kind == 'nuts0':
        _, cc, nm = src
        n = gpd.read_file(f'{RAW}/gisco/NUTS_RG_01M_2024_4326_LEVL_1.geojson')
        geom = shapely.union_all(shapely.make_valid(n[n.CNTR_CODE == cc].geometry.values))
        g = gpd.GeoDataFrame({'name': [nm]}, geometry=[geom], crs=4326)
    elif kind == 'nutsids':
        _, year, lvl, cc, ids = src
        g = gpd.read_file(f'{RAW}/gisco/NUTS_RG_01M_{year}_4326_LEVL_{lvl}.geojson')
        g = g[g.NUTS_ID.isin(ids)].copy()
        g['name'] = g.NAME_LATN.map(fixname)
    elif kind in ('chn_prov', 'chn_pref', 'chn_county'):
        a1 = gpd.read_file(f'{RAW}/gbh/CHN_ADM1.geojson'); a1['name'] = a1.shapeName.map(fixname)
        sar = a1[a1.name.str.contains('Special Administrative')].copy()
        sar['name'] = sar.name.str.replace(' Special Administrative Region', '', regex=False)
        if kind == 'chn_prov':
            g = a1
        elif kind == 'chn_pref':
            a2 = gpd.read_file(f'{RAW}/gbh/CHN_ADM2.geojson'); a2['name'] = a2.shapeName.map(fixname)
            a2 = a2[~a2.name.str.lower().str.startswith('taiwan') & ~a2.name.str.contains('Special Administrative')]
            tw = gpd.read_file(f'{RAW}/gb/TWN_ADM1.geojson'); tw['name'] = tw.shapeName.map(fixname)
            g = pd.concat([a2[['name', 'geometry']], tw[['name', 'geometry']], sar[['name', 'geometry']]], ignore_index=True)
        else:
            a3 = gpd.read_file(f'{RAW}/gb/CHN_ADM3.geojson'); a3['name'] = a3.shapeName.map(fixname)
            tw = gpd.read_file(f'{RAW}/gb/TWN_ADM2.geojson'); tw['name'] = tw.shapeName.map(fixname)
            g = pd.concat([a3[['name', 'geometry']], tw[['name', 'geometry']], sar[['name', 'geometry']]], ignore_index=True)
        g = gpd.GeoDataFrame(g, geometry='geometry', crs=4326)
    else:
        raise ValueError(src)
    g = g[['name', 'geometry'] + (extra if kind == 'gdf' else [])].copy()
    g['geometry'] = shapely.make_valid(g.geometry.values)
    g = g[~g.geometry.is_empty].reset_index(drop=True)
    if g.crs is None: g = g.set_crs(4326)
    g = g.to_crs(4326)
    if key: _cache[key] = g
    return g

def load_geo(level):
    parts = [load_src(s) for s in level['geo']]
    return pd.concat(parts, ignore_index=True) if len(parts) > 1 else parts[0]

def polys_only(geom):
    if geom is None or geom.is_empty: return None
    if geom.geom_type in ('Polygon', 'MultiPolygon'): return geom
    ps = [p for p in getattr(geom, 'geoms', []) if p.geom_type in ('Polygon', 'MultiPolygon')]
    if not ps: return None
    return shapely.union_all(ps)

def unwrap_antimeridian(g):
    b = g.bounds
    if b[2] <= 180 and b[0] >= -180: return g
    world = shapely.box(-180, -90, 180, 90)
    parts = [g.intersection(world)]
    if b[2] > 180: parts.append(translate(g.intersection(shapely.box(180, -90, 540, 90)), -360))
    if b[0] < -180: parts.append(translate(g.intersection(shapely.box(-540, -90, -180, 90)), 360))
    return polys_only(shapely.union_all([p for p in parts if not p.is_empty]))

def ms_simplify(g, interval_m, tmpdir):
    src = os.path.join(tmpdir, 'fin.geojson'); dst = os.path.join(tmpdir, 'fin_s.geojson')
    g[['fid', 'geometry']].to_file(src, driver='GeoJSON')
    r = subprocess.run(['node', '--max-old-space-size=6000', MS, '-i', src, '-simplify', 'weighted', f'interval={interval_m}', 'keep-shapes',
                        '-o', dst, 'precision=0.000001'], capture_output=True, text=True)
    if r.returncode: raise RuntimeError(r.stderr[-2000:])
    s = gpd.read_file(dst)
    s = s.set_index('fid').reindex(g.fid)
    out = g.copy(); out['geometry'] = s.geometry.values
    out['geometry'] = [polys_only(g) for g in shapely.make_valid(out.geometry.values)]
    return out

def member(pts, poly, maxd=0.15, force=False):
    """index into poly (or -1) of the polygon containing each point; nearest within maxd as fallback"""
    pg = gpd.GeoDataFrame({'pid': np.arange(len(poly))}, geometry=poly.geometry.values, crs=4326)
    pp = gpd.GeoDataFrame({'qid': np.arange(len(pts))}, geometry=pts, crs=4326)
    j = gpd.sjoin(pp, pg, how='left', predicate='within')
    j = j[~j.index.duplicated()]
    res = np.array(j.pid.fillna(-1).astype(int).values, copy=True)
    miss = np.where(res < 0)[0]
    if len(miss):
        jn = gpd.sjoin_nearest(pp.iloc[miss], pg, how='left', max_distance=maxd)
        jn = jn[~jn.index.duplicated()]
        res[miss] = jn.pid.fillna(-1).astype(int).reindex(pp.index[miss]).values
    miss = np.where(res < 0)[0]
    if force and len(miss):
        jn = gpd.sjoin_nearest(pp.iloc[miss], pg, how='left')
        jn = jn[~jn.index.duplicated()]
        res[miss] = jn.pid.fillna(-1).astype(int).reindex(pp.index[miss]).values
    return res

def conform(fin, outline, log, others=None):
    """clip finest units to the country outline and hand frame gaps to neighbours"""
    geoms = fin.geometry.values
    drop = []
    prep = shapely.prepared.prep(outline) if hasattr(shapely, 'prepared') else None
    shapely.prepare(outline)
    inside = shapely.contains(outline, geoms)
    out = np.array(geoms, dtype=object)
    for i in np.where(~inside)[0]:
        g = geoms[i]
        c = polys_only(shapely.intersection(g, outline))
        a0 = g.area
        if c is None or c.area < 0.1 * a0:
            # unit (mostly) outside the frame: keep it if it is an island missing from the frame,
            # drop it if it lies in another country's frame (disputed / claimed areas)
            ov = 0.0
            if others is not None:
                for k in others[0].query(g, predicate='intersects'):
                    ov += shapely.intersection(g, others[1][k]).area
            if ov > 0.3 * a0: out[i] = None; drop.append(i)
            else: out[i] = g
        else:
            out[i] = c
    fin = fin.copy(); fin['geometry'] = out
    if drop:
        log.append(f'dropped {len(drop)} units lying in other countries')
        fin = fin[fin.geometry.notna()].reset_index(drop=True)
    cover = shapely.union_all(shapely.buffer(fin.geometry.values, 0))
    gaps = polys_only(outline.difference(cover))
    if gaps is not None:
        parts = [p for p in getattr(gaps, 'geoms', [gaps]) if p.area > 1e-10]
        tree = shapely.STRtree(fin.geometry.values)
        add = {}
        for p in parts:
            cand = tree.query(p.buffer(1e-4), predicate='intersects')
            if len(cand) == 1: k = cand[0]
            elif len(cand) > 1:
                pb = p.buffer(1e-4)
                k = cand[int(np.argmax([fin.geometry.values[c].intersection(pb).area for c in cand]))]
            else:
                k = tree.query_nearest(p)[0]
            add.setdefault(int(k), []).append(p)
        geo = fin.geometry.values.copy()
        for k, ps in add.items():
            geo[k] = polys_only(shapely.union_all([geo[k]] + ps))
        fin['geometry'] = geo
        log.append(f'gaps filled: {len(parts)}')
    return fin

def build(iso, levels, frame_id=None, interval=None, log=None, deps=None, cover_min=0.0):
    log = log if log is not None else []
    levels = [dict(L) for L in levels]
    fl = levels[-1]
    fin = load_geo(fl).copy()
    if deps:
        # all of the country's territories become ONE first-level unit that cracks into the territories
        mem_rows = []
        for src in deps['members']:
            dg = load_src(src)
            mem_rows.append({'name': dg.name.iloc[0], 'geometry': polys_only(shapely.make_valid(dg.geometry.iloc[0]))})
        mg = gpd.GeoDataFrame(mem_rows, crs=4326)
        union = shapely.union_all(mg.geometry.values)
        zones = [g.buffer(0.1) for g in mg.geometry.values]
        keep = set(deps.get('keep_finest', []))
        rp = fin.geometry.representative_point().values
        drop = np.zeros(len(fin), bool)
        for nm, z in zip(mg.name, zones):
            if nm not in keep: drop |= shapely.contains(z, rp)
        add = mg[~mg.name.isin(keep)]
        fin = pd.concat([fin[~drop], add], ignore_index=True)
        log.append(f"territories '{deps['name']}': {len(mg)} members, replaced {int(drop.sum())} finest units")
        def minus(gdf):
            out = gdf.copy(); out['geometry'] = [polys_only(shapely.make_valid(x.difference(union))) for x in out.geometry.values]
            return out[out.geometry.notna()]
        grp = gpd.GeoDataFrame({'name': [deps['name']]}, geometry=[union], crs=4326)
        levels[0]['geo'] = [('gdf', minus(load_geo(levels[0]))), ('gdf', grp)]
        levels[0]['_override'] = [(shapely.union_all(zones), deps['name'])]
        if len(levels) > 2 and 'geo' in levels[1]:
            levels[1]['geo'] = [('gdf', minus(load_geo(levels[1]))), ('gdf', mg)]
            levels[1]['_override'] = list(zip(zones, mg.name))
    fin['geometry'] = [unwrap_antimeridian(g) for g in fin.geometry.values]
    fin = fin[fin.geometry.notna() & ~fin.geometry.is_empty].reset_index(drop=True)
    fin['fid'] = np.arange(len(fin))
    # simplification interval from typical unit size
    if interval is None:
        a = fin.to_crs('+proj=eqearth').area.median() / 1e6
        interval = int(min(800, max(40, math.sqrt(max(a, 0.01)) * 1000 / 30)))
    with tempfile.TemporaryDirectory() as td:
        fin = ms_simplify(fin, interval, td)
    fin = fin[fin.geometry.notna() & ~fin.geometry.is_empty].reset_index(drop=True)
    log.append(f'finest {len(fin)} units, interval {interval} m')
    # coverage: big holes in the finest level (partial datasets) become units named after the level above
    fr = frame(); fid0 = frame_id or iso
    if fid0 in fr.index:
        outline0 = polys_only(shapely.make_valid(fr.loc[fid0].geometry))
        cov = shapely.union_all(shapely.buffer(fin.geometry.values, 0))
        miss = polys_only(outline0.difference(cov))
        if miss is not None:
            med = float(np.median(fin.geometry.area))
            big = [p for p in getattr(miss, 'geoms', [miss]) if p.area > max(4 * med, 0.002, cover_min)]
            if big:
                up = None
                for L in reversed(levels[:-1]):
                    if 'geo' in L: up = load_geo(L); break
                newrows = []
                for p in big:
                    nm = fr.loc[fid0].n if 'n' in fr.columns else fid0
                    if up is not None:
                        m = member(np.array([p.representative_point()]), up)[0]
                        if m >= 0: nm = up.name.values[m]
                    newrows.append({'name': nm, 'geometry': p})
                add = gpd.GeoDataFrame(newrows, crs=4326)
                fin = pd.concat([fin, add], ignore_index=True)
                fin['fid'] = np.arange(len(fin))
                log.append(f'coverage: added {len(big)} filler units ({round(sum(p.area for p in big),2)} sq deg)')
    pts = fin.geometry.representative_point().values
    k = len(levels)
    mem = [None] * k
    names = [None] * k
    # a level may give each finest unit's membership as an attribute ('col': finest column holding the index into
    # that level's polygons); levels above it then place the unit by the interior point of that polygon
    jc = min([j for j, L in enumerate(levels[:-1]) if L.get('col')], default=None)
    pts_up = pts
    if jc is not None:
        polyc = load_geo(levels[jc]); rp = polyc.geometry.representative_point().values
        mc = fin[levels[jc]['col']].fillna(-1).astype(int).values
        pts_up = np.array([rp[m] if m >= 0 else q for m, q in zip(mc, pts)], dtype=object)
    for j, L in enumerate(levels[:-1]):
        if 'geo' in L:
            poly = load_geo(L)
            top = all('group' in X for X in levels[:j])
            if L.get('col'):
                m = np.array(fin[L['col']].fillna(-1).astype(int).values, copy=True)
                miss = np.where(m < 0)[0]
                if len(miss) and L.get('missing') != 'own':  # units without the attribute (fillers): by position
                    m[miss] = member(pts[miss], poly, force=top)
            else: m = member(pts_up if jc is not None and j < jc else pts, poly, force=top)
            for zone, nm in L.get('_override', []):
                k_ = list(poly.name.values).index(nm)
                m[shapely.contains(zone, pts)] = k_
            mem[j] = m
            names[j] = list(poly.name.values)
            log.append(f'L{j+1} {L["label"][1]}: {len(poly)} polygons, {int((m < 0).sum())} unmatched')
    # resolve groups (they group the level directly below by name)
    for j in range(k - 2, -1, -1):
        L = levels[j]
        if 'group' in L:
            lut = {norm(n): g for g, ns in L['group'].items() for n in ns}
            below = levels[j + 1]
            if 'geo' not in below: raise ValueError('group must sit on a geo level')
            bn = names[j + 1] if j + 1 < k - 1 else list(fin.name.values)
            bm = mem[j + 1] if j + 1 < k - 1 else np.arange(len(fin))
            gnames = sorted(set(L['group']))
            gi = {g: i for i, g in enumerate(gnames)}
            miss = set()
            m = np.full(len(fin), -1)
            for i, b in enumerate(bm):
                if b < 0: continue
                g = lut.get(norm(bn[b]))
                if g is None: miss.add(bn[b]); continue
                m[i] = gi[g]
            if miss: log.append(f'GROUP MISS L{j+1}: {sorted(miss)}')
            mem[j] = m; names[j] = gnames
    mem[k - 1] = np.arange(len(fin)); names[k - 1] = list(fin.name.values)
    # cumulative keys
    keys = []
    prev = [()] * len(fin)
    ids_per_level, name_per_level, parent_per_level = [], [], []
    P = np.array([(p.x, p.y) for p in pts])
    for j in range(k):
        if 0 < j < k - 1 and 'geo' in levels[j] and not levels[j].get('nodefrag'):
            mj = np.array(mem[j], copy=True)
            key = [(prev[i], int(mj[i])) for i in range(len(fin))]
            cnt = pd.Series(key).value_counts()
            tot = pd.Series(mj).value_counts()
            best = {}
            for (pf, mm), c in cnt.items():
                if mm >= 0 and (mm not in best or c > best[mm][1]): best[mm] = ((pf, mm), c)
            frag = {kk for kk, c in cnt.items() if kk[1] >= 0 and best[kk[1]][0] != kk and c < 0.3 * tot[kk[1]]}
            if frag:
                isfrag = np.array([kk in frag for kk in key])
                byprev = {}
                for i in range(len(fin)):
                    if not isfrag[i] and mj[i] >= 0: byprev.setdefault(prev[i], []).append(i)
                moved = 0
                for i in np.where(isfrag)[0]:
                    cand = byprev.get(prev[i])
                    if not cand: continue
                    cand = np.array(cand)
                    d = ((P[cand] - P[i]) ** 2).sum(1)
                    mj[i] = mj[cand[int(np.argmin(d))]]; moved += 1
                mem[j] = mj
                log.append(f'L{j+1}: merged {len(frag)} stray fragments ({moved} units)')
        cur = []
        for i in range(len(fin)):
            m = mem[j][i]
            cur.append(prev[i] + ((int(m),) if m >= 0 else ('=',)))
        uniq = {}
        # stable ids: order by name within parent
        def nm(t, j=j):
            m = t[-1]
            if m == '=':
                return name_per_level[j - 1][ids_per_level[j - 1][t[:-1]]] if j > 0 else '?'
            return names[j][m]
        order = sorted(set(cur), key=lambda t: (str(t[:-1]), norm(nm(t))))
        idmap = {t: n for n, t in enumerate(order)}
        ids_per_level.append(idmap)
        name_per_level.append({idmap[t]: nm(t) for t in order})
        parent_per_level.append({idmap[t]: (ids_per_level[j - 1][t[:-1]] if j > 0 else None) for t in order})
        fin[f'l{j+1}'] = [idmap[t] for t in cur]
        prev = cur
    counts = [len(x) for x in ids_per_level]
    log.append('level counts: ' + ' > '.join(map(str, counts)))
    # conform to frame
    fr = frame()
    fid = frame_id or iso
    if fid in fr.index:
        outline = polys_only(shapely.make_valid(fr.loc[fid].geometry))
        og = [shapely.make_valid(g) for i, g in zip(fr.index, fr.geometry.values) if i != fid]
        fin = conform(fin, outline, log, (shapely.STRtree(og), og))
    else:
        log.append(f'no frame for {fid}')
    return fin, counts, name_per_level, parent_per_level

def write_parts(iso, d, td, fin, j, by, k, names, parents, q):
    """one level written as one file per unit of level `by` (loaded only where it is needed)"""
    col, bcol = f'l{j+1}', f'l{by+1}'
    single = set(fin.groupby(col).size().pipe(lambda c: c[c == 1]).index) if j < k - 1 else set()
    sizes = {}
    for v in sorted(fin[bcol].unique()):
        sub = fin[fin[bcol] == v][[col, 'geometry']]
        src = os.path.join(td, f'p{j}_{v}.geojson'); sub.to_file(src, driver='GeoJSON')
        ids = sorted(set(sub[col]))
        tbl = os.path.join(td, f'n{j}_{v}.csv')
        pd.DataFrame({'i': ids, 'n': [names[j][x] for x in ids],
                      'p': [parents[j][x] if parents[j][x] is not None else '' for x in ids],
                      'x': ['1' if x in single else '' for x in ids]}).to_csv(tbl, index=False)
        fn = f'{iso}.{j+1}.{v}.json'
        cmd = ['node', '--max-old-space-size=6000', MS, '-i', src, 'name=u', 'precision=0.000001',
               '-dissolve', col, f'name=L{j+1}', '-rename-fields', f'i={col}', '-join', tbl, 'keys=i,i', 'fields=n,p,x', 'string-fields=n,p,x',
               '-o', os.path.join(d, fn), 'format=topojson', f'quantization={q}']
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode: raise RuntimeError(r.stderr[-3000:])
        fp = os.path.join(d, fn); t = json.load(open(fp))
        t['objects'] = {kk[1:]: vv for kk, vv in t['objects'].items()}
        for o in t['objects'].values():
            for g in o.get('geometries', []):
                pr = g.get('properties') or {}
                if pr.get('p') in ('', None): pr.pop('p', None)
                if pr.get('x') in ('', None): pr.pop('x', None)
                else: pr['x'] = 1
        json.dump(t, open(fp, 'w'), separators=(',', ':'), ensure_ascii=False)
        sizes[str(v)] = os.path.getsize(fp)
    return [f'{iso}.{j+1}.{{p}}.json', j + 1, j + 1, sum(sizes.values()), None, {'by': by + 1, 'p': sizes}]

def write(iso, levels, fin, counts, names, parents, heavy=800, log=None, parts=None):
    """dissolve levels with mapshaper and write topojson files; return index entry"""
    d = os.path.join(OUT, iso); os.makedirs(d, exist_ok=True)
    for f in os.listdir(d): os.remove(os.path.join(d, f))
    k = len(levels)
    cols = [f'l{j+1}' for j in range(k)]
    fin = fin[cols + ['geometry']].copy()
    fin = fin[fin.geometry.notna() & ~fin.geometry.is_empty]
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, 'u.geojson')
        fin.to_file(src, driver='GeoJSON')
        # names/parents tables for -join
        groups, cur = [], []
        for j in range(k):
            if counts[j] > heavy:
                if cur: groups.append(cur); cur = []
                groups.append([j])
            else:
                cur.append(j)
        if cur: groups.append(cur)
        files = []
        b = fin.total_bounds
        ext = max(b[2] - b[0], b[3] - b[1], 0.01)
        q = int(min(2e6, max(2e4, ext / 0.00003)))
        parts = parts or {}
        for gi, grp in enumerate(groups):
            if len(grp) == 1 and grp[0] in parts:
                files.append(write_parts(iso, d, td, fin, grp[0], parts[grp[0]], k, names, parents, q))
                continue
            cmd = ['node', '--max-old-space-size=6000', MS, '-i', src, 'name=u', 'precision=0.000001']
            names_out = []
            for j in grp:
                tbl = os.path.join(td, f'n{j}.csv')
                single = set(fin.groupby(f'l{j+1}').size().pipe(lambda c: c[c == 1]).index) if j < k - 1 else set()
                pd.DataFrame({'i': list(names[j].keys()), 'n': list(names[j].values()),
                              'p': [parents[j][x] if parents[j][x] is not None else '' for x in names[j]],
                              'x': ['1' if x in single else '' for x in names[j]]}).to_csv(tbl, index=False)
                cmd += ['-target', 'u', '-dissolve', f'l{j+1}', f'name=L{j+1}', '+',
                        '-rename-fields', f'i=l{j+1}', f'target=L{j+1}',
                        '-join', tbl, 'keys=i,i', 'fields=n,p,x', 'string-fields=n,p,x', f'target=L{j+1}']
                names_out.append(f'L{j+1}')
            fn = f'{iso}.{grp[0]+1}.json'
            cmd += ['-o', os.path.join(d, fn), 'format=topojson', f'quantization={q}', 'target=' + ','.join(names_out)]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode: raise RuntimeError(r.stderr[-3000:])
            fp = os.path.join(d, fn); t = json.load(open(fp))
            t['objects'] = {k[1:]: v for k, v in t['objects'].items()}
            for o in t['objects'].values():
                for g in o.get('geometries', []):
                    pr = g.get('properties') or {}
                    if pr.get('p') in ('', None): pr.pop('p', None)
                    if pr.get('x') in ('', None): pr.pop('x', None)
                    else: pr['x'] = 1
            json.dump(t, open(fp, 'w'), separators=(',', ':'), ensure_ascii=False)
            files.append([fn, grp[0] + 1, grp[-1] + 1, os.path.getsize(os.path.join(d, fn))])
    entry = {'L': [list(L['label']) for L in levels], 'F': files, 'N': counts}
    json.dump(entry, open(os.path.join(d, 'entry.json'), 'w'))
    return entry
