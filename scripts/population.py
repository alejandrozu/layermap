"""Population for every unit at every level.

Each country's latest census total (UN Population and Vital Statistics Report, Jan 2026, table 2)
is spread over its subdivisions in proportion to the GHS-POP 2020 grid (1 km, JRC; itself built
from national census counts).  Dependent territories that the UN lists separately (Puerto Rico,
Hong Kong, Greenland, Réunion, ...) get their own census totals ("zones").

Output: site/data/pop.gz.txt  (base64 gzip JSON)
  {"c": {ISO3: {"z": [[label, census, date, grid], ...],       zone 0 = the country itself
                "L": [[[grid, zone, lon*100, lat*100, km2], ...] per level]}},   index = unit i
   "w": {ISO3: [census, date] for countries without subdivisions}}
"""
import json, gzip, base64, math, re, sys, os, unicodedata
import numpy as np, shapely, rasterio
from rasterio import features
from rasterio.windows import Window
from shapely.ops import polylabel

CH = '/home/claude/build/chunks'
GHS = '/home/claude/raw/pop/GHS_POP_E2020_GLOBE_R2023A_4326_30ss_V1_0.tif'
UN = json.load(open('/home/claude/raw/pop/un_census.json'))
CC = json.load(open('/home/claude/raw/pop/census_country.json'))
CC.update({k: v for k, v in json.load(open('/home/claude/raw/pop/census_extra.json')).items()})


def norm(s): return re.sub(r'[^a-z]', '', unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower())


UNROW = {norm(r[0]): r for r in UN}
# territories with their own census, matched to unit names inside the sovereign country
ZONES = {
    'USA': [('Puerto Rico', ['Puerto Rico']), ('United States Virgin Islands', ['U.S. Virgin Islands', 'United States Virgin Islands', 'Virgin Islands']),
            ('Guam', ['Guam']), ('American Samoa', ['American Samoa']), ('Northern Mariana Islands', ['Commonwealth of the Northern Mariana Islands', 'Northern Mariana Islands'])],
    'CHN': [('China, Hong Kong SAR', ['Hong Kong Special Administrative Region', 'Hong Kong']), ('China, Macao SAR', ['Macao Special Administrative Region', 'Macao']), ('Taiwan', ['Taiwan Province', 'Taiwan'])],
    'FRA': [('Guadeloupe', ['Guadeloupe']), ('Martinique', ['Martinique']), ('French Guiana', ['Guyane', 'French Guiana']),
            ('Reunion', ['La Réunion', 'Réunion', 'Reunion']), ('Mayotte', ['Mayotte']), ('New Caledonia', ['New Caledonia']),
            ('French Polynesia', ['French Polynesia']), ('Wallis and Futuna Islands', ['Wallis and Futuna']),
            ('Saint Pierre and Miquelon', ['Saint Pierre and Miquelon']), ('Saint Barthélemy', ['Saint Barthélemy']),
            ('Saint-Martin (French part)', ['Saint Martin'])],
    'GBR': [(n, [m]) for n, m in [('Anguilla', 'Anguilla'), ('Bermuda', 'Bermuda'), ('British Virgin Islands', 'British Virgin Islands'),
            ('Cayman Islands', 'Cayman Islands'), ('Montserrat', 'Montserrat'), ('Turks and Caicos Islands', 'Turks and Caicos Islands'),
            ('Falkland Islands (Malvinas)', 'Falkland Islands'), ('Gibraltar', 'Gibraltar'), ('Guernsey', 'Guernsey'),
            ('Isle of Man', 'Isle of Man'), ('Jersey', 'Jersey'), ('Pitcairn', 'Pitcairn Islands'),
            ('Saint Helena ex. dep.', 'Saint Helena, Ascension & Tristan da Cunha')]],
    'NLD': [('Aruba', ['Aruba']), ('Curaçao', ['Curaçao']), ('Sint Maarten (Dutch part)', ['Sint Maarten'])],
    'DNK': [('Greenland', ['Greenland']), ('Faroe Islands', ['Faroe Islands'])],
    'NOR': [('Svalbard and Jan Mayen Islands', ['Svalbard'])],
    'NZL': [('Cook Islands', ['Cook Islands']), ('Niue', ['Niue'])],
    'AUS': [('Norfolk Island', ['Norfolk Island'])],
}
EXTRA_ROWS = {'Taiwan': ('Taiwan', '1 Nov 2020', 'DJ', None)}  # filled from census_extra.json
SH_EXTRA = ['Saint Helena: Ascension', 'Saint Helena: Tristan da Cunha']  # added to Saint Helena


def decode(topo):
    t = topo.get('transform'); sx, sy = t['scale']; tx, ty = t['translate']
    arcs = []
    for a in topo['arcs']:
        x = y = 0; pts = []
        for dx, dy in a:
            x += dx; y += dy; pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)
    def ring(idx):
        out = []
        for ai in idx:
            pts = arcs[ai] if ai >= 0 else arcs[~ai][::-1]
            out.extend(pts if not out else pts[1:])
        return out
    def geom(g):
        polys = []
        if g['type'] == 'Polygon': parts = [g['arcs']]
        elif g['type'] == 'MultiPolygon': parts = g['arcs']
        else: return None
        for p in parts:
            rs = [ring(r) for r in p]
            if len(rs[0]) >= 4: polys.append(shapely.Polygon(rs[0], [r for r in rs[1:] if len(r) >= 4]))
        if not polys: return None
        return shapely.make_valid(shapely.MultiPolygon(polys) if len(polys) > 1 else polys[0])
    return geom


def levels_of(cid):
    e = json.load(open(f'{CH}/{cid}/entry.json'))
    out = {}
    for fn, l0, l1, *rest in e['F']:
        fns = [fn.replace('{p}', k) for k in rest[2]['p']] if len(rest) > 2 and rest[2] else [fn]
        for fn1 in fns:
            t = json.load(open(f'{CH}/{cid}/{fn1}'))
            g = decode(t)
            for k, o in t['objects'].items():
                lv = int(k.split('.')[-1])
                units = out.setdefault(lv, {})
                for gg in o['geometries']:
                    p = gg['properties']
                    units[int(p['i'])] = dict(n=p['n'], p=int(p['p']) if p.get('p') not in (None, '') else None, g=g(gg))
    return e, out


R = rasterio.open(GHS)


def zonal(geoms):
    """Sum of GHS-POP 2020 inside each geometry (supersampled so small units get their share)."""
    b = shapely.union_all([x for x in geoms if x is not None]).bounds
    t = R.transform; cw = t.a
    c0 = max(0, int((b[0] - t.c) / cw) - 1); c1 = min(R.width, int((b[2] - t.c) / cw) + 2)
    r0 = max(0, int((t.f - b[3]) / cw) - 1); r1 = min(R.height, int((t.f - b[1]) / cw) + 2)
    H, Wd = r1 - r0, c1 - c0
    if H <= 0 or Wd <= 0: return np.zeros(len(geoms))
    f = int(max(1, min(5, math.sqrt(4e7 / (H * Wd)))))
    sums = np.zeros(len(geoms) + 1)
    shapes = [(g, i + 1) for i, g in enumerate(geoms) if g is not None and not g.is_empty]
    step = max(1, int(2.5e7 / (Wd * f * f)))
    for rs in range(r0, r1, step):
        re_ = min(r1, rs + step)
        pop = R.read(1, window=Window(c0, rs, Wd, re_ - rs)).astype(np.float32)
        pop[pop < 0] = 0
        if pop.sum() == 0: continue
        tr = rasterio.Affine(cw / f, 0, t.c + c0 * cw, 0, -cw / f, t.f - rs * cw)
        lab = features.rasterize(shapes, out_shape=((re_ - rs) * f, Wd * f), transform=tr, fill=0, dtype='int32')
        w = np.repeat(np.repeat(pop / (f * f), f, 0), f, 1)
        sums += np.bincount(lab.ravel(), weights=w.ravel(), minlength=len(geoms) + 1)[:len(geoms) + 1]
    return sums[1:]


PS = {'USA': 10000}   # label point precision (1/degree) where units get small; 100 elsewhere


def label_area(g, ps=100):
    if g is None or g.is_empty: return [0, 0, 0]
    parts = list(getattr(g, 'geoms', [g]))
    parts = [p for p in parts if p.geom_type == 'Polygon']
    if not parts: c = g.representative_point(); return [round(c.x * ps), round(c.y * ps), 0]
    big = max(parts, key=lambda p: p.area)
    try:
        s = max(big.bounds[2] - big.bounds[0], big.bounds[3] - big.bounds[1])
        lp = polylabel(big, tolerance=max(s / 60, 1e-4))
    except Exception:
        lp = big.representative_point()
    lat = g.centroid.y
    km2 = g.area * 12391.6 * math.cos(math.radians(lat))
    return [round(lp.x * ps), round(lp.y * ps), round(km2)]


def run(cids):
    out = {}
    for cid in cids:
        e, lv = levels_of(cid)
        fin = max(lv)
        ids = sorted(lv[fin])
        g = zonal([lv[fin][i]['g'] for i in ids])
        pop = {fin: dict(zip(ids, g))}
        for L in range(fin, 1, -1):  # roll up
            up = {i: 0.0 for i in lv[L - 1]}
            for i, u in lv[L].items():
                if u['p'] in up: up[u['p']] += pop[L].get(i, 0)
            pop[L - 1] = up
        # zones: territories with their own census
        zl = [[CC[cid][0], CC[cid][2], CC[cid][1], 0.0]] if cid in CC else [['', 0, '', 0.0]]
        zone = {L: {i: 0 for i in lv[L]} for L in lv}
        for unrow, names in ZONES.get(cid, []):
            row = UNROW.get(norm(unrow)) or (EXTRA.get(unrow) and (unrow, EXTRA[unrow][1], '', EXTRA[unrow][0]))
            if not row: print(cid, 'no census row for', unrow); continue
            tot = row[3]
            if unrow == 'Saint Helena ex. dep.': tot += sum(UNROW[norm(x)][3] for x in SH_EXTRA if norm(x) in UNROW)
            hit = None
            for L in sorted(lv):
                for i, u in lv[L].items():
                    if norm(u['n']) in [norm(x) for x in names]: hit = (L, i); break
                if hit: break
            if not hit: print(cid, 'zone unit not found:', names); continue
            zi = len(zl); zl.append([names[0], tot, row[1], 0.0])
            # mark the unit and all its descendants
            mark = {hit[0]: {hit[1]}}
            for L in range(hit[0] + 1, fin + 1):
                mark[L] = {i for i, u in lv[L].items() if u['p'] in mark[L - 1]}
            for L in range(hit[0] - 0, fin + 1):
                for i in mark[L]: zone[L][i] = zi
        for i, z in zone[fin].items(): zl[z][3] += pop[fin].get(i, 0)
        # census value of each finest unit = its grid share of its zone's census total (grid if no census)
        fac = [(z[1] / z[3]) if z[1] and z[3] > 0 else 1.0 for z in zl]
        cen = {fin: {i: pop[fin].get(i, 0) * fac[zone[fin][i]] for i in lv[fin]}}
        zon = {fin: dict(zone[fin])}
        exact_at = apply_official(cid, lv, fin, pop, cen, zon, zl) if cid in OFFICIAL else {}
        for L in range(fin, 1, -1):
            up = {i: 0.0 for i in lv[L - 1]}; zu = {}
            for i, u in lv[L].items():
                if u['p'] in up:
                    up[u['p']] += cen[L][i]
                    zu[u['p']] = zon[L][i] if zu.get(u['p'], zon[L][i]) == zon[L][i] else -1
            cen[L - 1] = up; zon[L - 1] = {i: zu.get(i, 0) for i in lv[L - 1]}
            for i, z in exact_at.get(L - 1, {}).items(): zon[L - 1][i] = z   # counted at this level: exact here
        Ls = []
        for L in sorted(lv):
            n = max(lv[L]) + 1
            arr = [[0, 0, 0, 0, 0] for _ in range(n)]
            for i, u in lv[L].items():
                arr[i] = [round(cen[L].get(i, 0)), zon[L][i]] + label_area(u['g'], PS.get(cid, 100))
            Ls.append(arr)
        out[cid] = {'z': [[z[0], z[1], z[2], round(z[3])] + z[4:] for z in zl], 'L': Ls}
        if cid in PS: out[cid]['ps'] = PS[cid]
        tot_c = sum(z[1] for z in zl); tot_g = sum(z[3] for z in zl)
        print(cid, 'levels', len(Ls), 'units', sum(len(x) for x in Ls), 'grid', round(tot_g / 1e6, 2), 'M', 'census', round(tot_c / 1e6, 2), 'M', zl[0][2], flush=True)
    return out


EXTRA = json.load(open('/home/claude/raw/pop/census_extra.json'))
OFF = '/home/claude/raw/pop/official'


def us_records():
    import csv
    for r in csv.DictReader(open(f'{OFF}/us_cenpop2020_co.txt', encoding='utf-8-sig')):
        yield r['STNAME'], r['COUNAME'], int(r['POPULATION']), float(r['LONGITUDE']), float(r['LATITUDE'])


def br_records():
    m = {str(x['id']): x for x in json.load(open(f'{OFF}/br_mun.json'))}
    for x in json.load(open(f'{OFF}/br_pop2022.json'))[0]['resultados'][0]['series']:
        mid = x['localidade']['id']; v = x['serie'].get('2022', '')
        if mid not in m or not v.isdigit(): continue
        mu = m[mid]; uf = (mu.get('microrregiao') or {}).get('mesorregiao', {}).get('UF', {}).get('nome') or mu['regiao-imediata']['regiao-intermediaria']['UF']['nome']
        yield uf, mu['nome'], int(v), None, None


ES_AC = {1: 'País Vasco', 2: 'Castilla-La Mancha', 3: 'Comunitat Valenciana', 4: 'Andalucía', 5: 'Castilla y León', 6: 'Extremadura',
         7: 'Illes Balears', 8: 'Cataluña', 9: 'Castilla y León', 10: 'Extremadura', 11: 'Andalucía', 12: 'Comunitat Valenciana',
         13: 'Castilla-La Mancha', 14: 'Andalucía', 15: 'Galicia', 16: 'Castilla-La Mancha', 17: 'Cataluña', 18: 'Andalucía',
         19: 'Castilla-La Mancha', 20: 'País Vasco', 21: 'Andalucía', 22: 'Aragón', 23: 'Andalucía', 24: 'Castilla y León', 25: 'Cataluña',
         26: 'La Rioja', 27: 'Galicia', 28: 'Comunidad de Madrid', 29: 'Andalucía', 30: 'Región de Murcia', 31: 'Comunidad Foral de Navarra',
         32: 'Galicia', 33: 'Principado de Asturias', 34: 'Castilla y León', 35: 'Canarias', 36: 'Galicia', 37: 'Castilla y León',
         38: 'Canarias', 39: 'Cantabria', 40: 'Castilla y León', 41: 'Andalucía', 42: 'Castilla y León', 43: 'Cataluña', 44: 'Aragón',
         45: 'Castilla-La Mancha', 46: 'Comunitat Valenciana', 47: 'Castilla y León', 48: 'País Vasco', 49: 'Castilla y León', 50: 'Aragón',
         51: 'Ciudad de Ceuta', 52: 'Ciudad de Melilla'}


def es_records():
    import csv
    for r in csv.reader(open(f'{OFF}/es_censo2021.csv', encoding='utf-8-sig'), delimiter=';'):
        if len(r) < 4 or r[1] != 'Ambos sexos' or not re.match(r'^\d{5} ', r[0]): continue
        code, name = r[0][:5], r[0][6:]
        names = [name] + [x.strip() for x in name.split('/')]
        yield ES_AC[int(code[:2])], names, int(r[3].replace('.', '')), None, None


def fr_records():  # INSEE populations légales 2021 (municipal population), by commune code
    import csv
    for r in csv.DictReader(open(f'{OFF}/fr/donnees_communes.csv', encoding='utf-8'), delimiter=';'):
        c = r['COM']  # Paris, Lyon and Marseille are listed by arrondissement; the map has the whole city
        c = '75056' if c.startswith('751') else '69123' if c.startswith('6938') else '13055' if c.startswith('132') else c
        yield 'FR_' + c, int(r['PMUN'])


def de_records():  # Zensus 2022, by municipality (ARS 12 -> AGS 8)
    import openpyxl
    ws = openpyxl.load_workbook(f'{OFF}/de_zensus2022.xlsx', read_only=True)['Bevölkerung']
    for r in ws.iter_rows(min_row=5, values_only=True):
        ars, lvl, pop = r[0], r[2], r[3]
        if not ars or not isinstance(pop, (int, float)) or len(str(ars)) != 12 or 'Gemeinde' not in str(lvl): continue
        ars = str(ars); yield 'DE_' + ars[:5] + ars[9:], int(pop)


def mx_records():  # INEGI Censo 2020, municipal totals, via the geoBoundaries -> CVEGEO join used to build the map
    import csv
    join = {r['cvegeo']: r for r in csv.DictReader(open('/home/claude/raw/extra/mexico/MEX_ADM2_to_DDR_join.csv'))}
    state_of = {}
    for r in join.values():
        if r['state']: state_of.setdefault(r['cvegeo'][:2], r['state'])
    for cve, ent, mun, pop, lon, lat in json.load(open(f'{OFF}/mx_mun2020.json')):
        j = join.get(cve)
        if j: yield j['state'] or state_of.get(cve[:2], ent), j['shapeName'], pop, None, None
        else: yield state_of.get(cve[:2], ent), mun, pop, lon, lat   # created after the map's boundaries: placed by its seat


def jp_canon(s):  # Hepburn vs Nihon-shiki spellings ('Oita'/'Ooita', 'Numazu'/'Numadu', 'Gotemba'/'Gotenba')
    s = re.sub(r'(cho|machi|mura|son)$', '', s) if len(s) > 6 else s
    for a, b in (('du', 'zu'), ('di', 'zi'), ('tsu', 'tu'), ('shi', 'si'), ('chi', 'ti'), ('fu', 'hu'), ('ji', 'zi'), ('sh', 'sy'), ('ch', 'ty'),
                 ('ou', 'o'), ('oo', 'o'), ('uu', 'u'), ('ii', 'i'), ('mb', 'nb'), ('mp', 'np'), ('mm', 'nm')):
        s = s.replace(a, b)
    return s


JP_SUF = re.compile(r'-(shi|cho|machi|mura|son|ku)$', re.I)


def jp_records():  # 2025 census (Oct 2025), municipalities; Tokyo's 23 wards count as municipalities
    import openpyxl
    ws = openpyxl.load_workbook(f'{OFF}/jp2025.xlsx', read_only=True).worksheets[0]
    pref = {}
    for r in ws.iter_rows(min_row=10, values_only=True):
        if not r[1] or not isinstance(r[4], (int, float)): continue
        code, en, kind = r[1][:5], r[2] or '', r[3]
        if kind == 'a':
            pref[code[:2]] = re.sub(r'-(ken|to|fu)$', '', en).replace('Gumma', 'Gunma'); continue
        if kind == 0 and code[:2] != '13': continue      # wards of designated cities: the city row has them
        if code == '13100': continue                      # Tokyo ward area total
        nm = JP_SUF.sub('', en.split(' ')[-1] if kind == 0 else en)
        yield pref[code[:2]], [nm, en], int(r[4]), None, None


IN_TELANGANA = {'adilabad', 'nizamabad', 'karimnagar', 'medak', 'hyderabad', 'rangareddy', 'mahbubnagar', 'nalgonda', 'warangal', 'khammam'}
IN_STATE = {'NCT OF DELHI': 'Delhi', 'ORISSA': 'Odisha', 'PONDICHERRY': 'Puducherry', 'DADRA AND NAGAR HAVELI': 'Dādra and Nagar Haveli and Damān and Diu',
            'DAMAN AND DIU': 'Dādra and Nagar Haveli and Damān and Diu'}


def in_records():  # Census 2011 districts, regrouped into today's states (Telangana 2014, Ladakh 2019, DNH&DD 2020)
    import csv
    for r in csv.DictReader(open(f'{OFF}/in_districts2011.csv')):
        st, d, pop = r['State name'], norm(r['District name']), int(r['Population'])
        if st == 'ANDHRA PRADESH' and d in IN_TELANGANA: st = 'Telangāna'
        elif st == 'JAMMU AND KASHMIR' and ('leh' in d or d == 'kargil'): st = 'Ladākh'
        yield IN_STATE.get(st, st), pop


def ca_records():  # 2021 census, provinces & territories (Statistics Canada, via Wikidata; StatCan blocks scripted downloads)
    seen = set()
    for b in json.load(open(f'{OFF}/ca_prov.json'))['results']['bindings']:
        k = b['pLabel']['value']
        if k in seen: continue
        seen.add(k); yield k, int(float(b['pop']['value']))


US_SUF = re.compile(r'\s+(county|parish|borough|city and borough|census area|municipality|municipio|city)$', re.I)
OFFICIAL = {
    'FRA': dict(records=fr_records, codes='FR', date='1 Jan 2021', label='2021 census (municipal populations)'),
    'DEU': dict(records=de_records, codes='DE', date='15 May 2022', label='Zensus 2022 (municipal counts)'),
    'MEX': dict(records=mx_records, group=2, date='15 Mar 2020', label='2020 census (municipal counts)'),
    'JPN': dict(records=jp_records, group=2, date='1 Oct 2025', label='2025 census (municipal counts)',
                clean=lambda n: re.sub(r'\s+prefecture$', '', n, flags=re.I), canon=jp_canon),
    'CAN': dict(records=ca_records, level=1, date='11 May 2021', label='2021 census (province counts)'),
    'IND': dict(records=in_records, level=2, date='1 Mar 2011', label='2011 census (state counts)'),
    'ESP': dict(records=es_records, group=1, date='1 Jan 2021', label='2021 census (municipal counts)'),
    'BRA': dict(records=br_records, group=2, date='1 Aug 2022', label='2022 census (municipal counts)'),
    'USA': dict(custom='us_cousub', cs_level=5, date='1 Apr 2020', label='2020 census (county subdivision counts)'),
}

US_CB = '/home/claude/raw/us/cousub/cb_2023_us_cousub_500k.shp'


def poly_units(codes, names, geoms, lv, fin):
    """statistical code -> our finest unit, for units built from these very polygons: the name decides, the
    polygon's interior point picks among namesakes (and places a unit whose name differs)"""
    ids = [i for i in lv[fin] if lv[fin][i]['g'] is not None]
    tree = shapely.STRtree([lv[fin][i]['g'] for i in ids])
    byname = {}
    for i in ids: byname.setdefault(norm(lv[fin][i]['n']), []).append(i)
    out, taken, later = {}, set(), []
    for code, name, geom in zip(codes, names, geoms):
        if geom is None or geom.is_empty: continue
        pt = geom.representative_point(); c = byname.get(norm(name or ''), [])
        if len(c) > 1:
            near = set(ids[h] for h in tree.query(pt, predicate='intersects'))
            c = [i for i in c if i in near] or sorted(c, key=lambda i: lv[fin][i]['g'].distance(pt))[:1]
        if c and c[0] not in taken: out[code] = c[0]; taken.add(c[0])
        else: later.append((code, pt))
    for code, pt in later:
        hit = [ids[h] for h in tree.query(pt, predicate='intersects') if ids[h] not in taken]
        if hit: out[code] = hit[0]; taken.add(hit[0])
    return out


def apply_us_cousub(o, lv, fin, pop, cen, zon, zl):
    """2020 census counts of every county subdivision (P.L. 94-171), matched by FIPS code to the 2023 polygons
    the map was built from.  Connecticut's towns changed county codes in 2022 (planning regions), so they match by
    state + town code.  Counts of subdivisions redrawn since 2020 are given to their county and shared there."""
    import geopandas as gpd
    rec = json.load(open(f'{OFF}/us_cousub2020.json'))
    cb = gpd.read_file(US_CB, columns=['GEOID', 'STATEFP', 'COUSUBFP', 'NAMELSAD', 'ALAND'])
    FT = fin; fin = o['cs_level']   # county subdivisions; places and census tract parts (finest) below them
    unit = poly_units(list(cb.GEOID), list(cb.NAMELSAD), list(cb.geometry), lv, fin)
    by_st, by_name, aland = {}, {}, dict(zip(cb.GEOID, cb.ALAND))
    for g, n in zip(cb.GEOID, cb.NAMELSAD):
        by_st.setdefault(g[:2] + g[5:], []).append(g); by_name.setdefault((g[:5], n.lower()), []).append(g)
    L4 = fin - 1
    ids4 = [i for i in lv[L4] if lv[L4][i]['g'] is not None]
    tree4 = shapely.STRtree([lv[L4][i]['g'] for i in ids4])
    county = {i: lv[fin][i]['p'] for i in lv[fin]}
    got, pool, n_match = {}, {}, 0
    for geoid, (name, cnt, lon, lat, a20) in rec.items():
        g = geoid if geoid in unit else None
        if g is None:
            alt = by_st.get(geoid[:2] + geoid[5:], [])
            if len(alt) == 1 and alt[0] in unit: g = alt[0]
        if g is None:  # recoded since 2020 (Arkansas): same name in the same county and the same land area
            alt = by_name.get((geoid[:5], name.lower()), [])
            if len(alt) == 1 and alt[0] in unit and a20 and abs(aland[alt[0]] / a20 - 1) < 0.03: g = alt[0]
        if g is not None:
            i = unit[g]; got[i] = got.get(i, 0) + cnt; n_match += 1; continue
        pt = shapely.Point(lon, lat)
        h = [ids4[k] for k in tree4.query(pt, predicate='intersects')]
        if not h: h = [ids4[tree4.query_nearest(pt)[0]]]
        pool[h[0]] = pool.get(h[0], 0) + cnt
    zi = len(zl); zl.append([o['label'], 0, o['date'], 0.0, 1])
    zd = len(zl); zl.append([o['label'], 0, o['date'], 0.0, 0])
    est = set()
    for c4, tot in pool.items():
        kids = [i for i in lv[fin] if county[i] == c4]
        rest = [i for i in kids if i not in got]
        if rest:
            w = sum(pop[fin].get(i, 0) for i in rest) or len(rest)
            for i in rest: got[i] = tot * ((pop[fin].get(i, 0) or (1 if w == len(rest) else 0)) / w); est.add(i)
        else:
            w = sum(got[i] for i in kids) or 1
            for i in kids: got[i] += tot * got[i] / w; est.add(i)
    # subdivisions created since 2020 (Essex Junction, West Peoria…): their people were counted in the unit they
    # split from, so they and their neighbours in the county share those neighbours' counts by the grid
    kids_of = {}
    for i in lv[fin]: kids_of.setdefault(county[i], []).append(i)
    kidsT = {}   # county subdivision -> its finest units
    for k, u in lv[FT].items():
        c = u['p']
        for L in range(FT - 1, fin, -1): c = lv[L][c]['p'] if c is not None and c in lv[L] else None
        kidsT.setdefault(c, []).append(k)
    z5 = {c: zon[FT][ks[0]] for c, ks in kidsT.items()}
    orphans = [i for i in lv[fin] if i not in got and z5.get(i, -1) == 0 and any(k in got for k in kids_of[county[i]])]
    for u in orphans:
        gu = lv[fin][u]['g']
        nb = [k for k in kids_of[county[u]] if k in got and k != u and lv[fin][k]['g'] is not None and gu is not None
              and lv[fin][k]['g'].intersects(gu.buffer(0.002))] or [k for k in kids_of[county[u]] if k in got]
        grp = nb + [u]; tot = sum(got[k] for k in nb)
        w = sum(pop[fin].get(k, 0) for k in grp) or len(grp)
        for k in grp: got[k] = tot * ((pop[fin].get(k, 0) or (1 if w == len(grp) else 0)) / w); est.add(k)
    # tract parts in place parts: the 2020 blocks of each (subdivision, place, tract), scaled to the subdivision's count
    import geopandas as gpd
    blk = {tuple(k.split('|')): v[0] for k, v in json.load(open('/home/claude/raw/us/place/combos3.json')).items()}
    p6 = gpd.read_file('/home/claude/raw/us/place/pieces6.gpkg', ignore_geometry=True)
    p7 = gpd.read_file('/home/claude/raw/us/place/pieces7.gpkg', ignore_geometry=True)
    sv = lambda x: x if isinstance(x, str) else ''
    k6 = {(unit[c], n): (c, sv(q)) for c, q, n in zip(p6.cs, p6.pl, p6.name) if c in unit}
    k7 = {(c, sv(q), n): t for c, q, t, n in zip(p7.cs, p7.pl, p7.tr, p7.name)}
    def bkey(k):
        u6 = lv[FT - 1].get(lv[FT][k]['p'])
        cp = k6.get((u6['p'], u6['n'])) if u6 else None
        t = k7.get((cp[0], cp[1], lv[FT][k]['n'])) if cp else None
        return (cp[0], cp[1], t) if t else None
    blk_cs = {}
    for key, v in blk.items(): blk_cs.setdefault(key[0], []).append((key, v))
    n_ex6 = n_sh6 = 0; exact5 = {}
    for c5, v in got.items():
        ks = kidsT.get(c5, [])
        if not ks: continue
        keys = {k: bkey(k) for k in ks}
        b = {k: (blk.get(keys[k], 0) if keys[k] else 0) for k in ks}
        moved = set()
        cg = next((kk[0] for kk in keys.values() if kk), None)
        if cg:
            # blocks of pairs too small to draw went into a neighbouring part: their people go with them
            have = set(kk for kk in keys.values() if kk)
            for key, pv in blk_cs.get(cg, []):
                if key in have or pv <= 0: continue
                same = [k for k in ks if keys[k] and keys[k][1] == key[1]] or ks
                t = max(same, key=lambda k: b[k]); b[t] += pv; moved.add(t)
        sb = sum(b.values())
        whole = c5 not in est and sb > 0 and abs(sb - v) < 0.5
        if sb > 0:
            for k in ks: cen[FT][k] = v * b[k] / sb; zon[FT][k] = zi if whole and k not in moved else zd
        else:
            w = sum(pop[FT].get(k, 0) for k in ks) or len(ks)
            for k in ks: cen[FT][k] = v * ((pop[FT].get(k, 0) or (1 if w == len(ks) else 0)) / w); zon[FT][k] = zi if (v == 0 and c5 not in est) else zd
        for k in ks:
            if zon[FT][k] == zi: n_ex6 += 1; zl[zi][1] += cen[FT][k]; zl[zi][3] += pop[FT].get(k, 0)
            else: n_sh6 += 1; zl[zd][1] += cen[FT][k]; zl[zd][3] += pop[FT].get(k, 0)
        if c5 not in est: exact5[c5] = zi
    print('USA new since 2020:', len(orphans), 'subdivisions; tract parts exact', n_ex6, 'scaled', n_sh6)
    print('USA official:', n_match, 'of', len(rec), 'records matched by code;', len(got) - len(est), 'units exact,', len(est),
          'shared;', len(pool), 'counties got redrawn-subdivision counts', round(sum(pool.values())), flush=True)
    return {fin: exact5}


LAU = '/home/claude/raw/gisco/LAU_RG_01M_2023_4326.gpkg'


def apply_official_level(o, lv, fin, pop, cen, zon, zl):
    Lo = o['level']
    def anc(i):
        L, j = fin, i
        while L > Lo: j = lv[L][j]['p']; L -= 1
        return j
    idx = {norm(u['n']): i for i, u in lv[Lo].items()}
    got = {}
    for name, cnt in o['records']():
        i = idx.get(norm(name))
        if i is None: print('  no unit for', name); continue
        got[i] = got.get(i, 0) + cnt
    zi = len(zl); zl.append([o['label'], sum(got.values()), o['date'], 0.0, 1])
    zd = len(zl); zl.append([o['label'], 0, o['date'], 0.0, 0])
    under = {}
    for d in lv[fin]: under.setdefault(anc(d), []).append(d)
    for i, v in got.items():
        ds = under.get(i, []); w = sum(pop[fin].get(d, 0) for d in ds) or len(ds)
        for d in ds:
            cen[fin][d] = v * ((pop[fin].get(d, 0) or (1 if w == len(ds) else 0)) / w); zon[fin][d] = zd
        zl[zi][3] += sum(pop[fin].get(d, 0) for d in ds)
    print('official at level', Lo, ':', len(got), 'of', len(lv[Lo]), 'units exact', flush=True)
    return {Lo: {i: zi for i in got}}


def lau_units(iso2, lv, fin):
    """GISCO LAU code -> our finest unit.  The map's municipalities were built from these polygons, so the name
    decides; the polygon's position only breaks ties between namesakes (or helps when a name was changed)."""
    import geopandas as gpd
    g = gpd.read_file(LAU, where=f"CNTR_CODE = '{iso2}'")
    ids = [i for i in lv[fin] if lv[fin][i]['g'] is not None]
    tree = shapely.STRtree([lv[fin][i]['g'] for i in ids])
    byname = {}
    for i in ids: byname.setdefault(norm(lv[fin][i]['n']), []).append(i)
    out, taken, later = {}, set(), []
    for code, name, geom in zip(g.GISCO_ID, g.LAU_NAME, g.geometry):
        if geom is None: continue
        pt = geom.representative_point(); c = byname.get(norm(name or ''), [])
        if len(c) > 1:
            near = [ids[h] for h in tree.query(pt, predicate='intersects')]
            c = [i for i in c if i in near] or sorted(c, key=lambda i: lv[fin][i]['g'].distance(pt))[:1]
        if c and c[0] not in taken: out[code] = c[0]; taken.add(c[0])
        else: later.append((code, pt))
    for code, pt in later:
        hit = [ids[h] for h in tree.query(pt, predicate='intersects') if ids[h] not in taken]
        if hit: out[code] = hit[0]; taken.add(hit[0])
    return out


def apply_official(cid, lv, fin, pop, cen, zon, zl):
    """Replace the grid estimate of the finest units with official census counts.
    Name mode: matched by name within a group (e.g. county within state).  Code mode: by statistical code via the
    LAU polygons.  Counts that cannot be matched stay in their group and are shared by the unmatched units in
    proportion to the grid; if every unit there is matched they go to the unit that contains them (when known)."""
    o = OFFICIAL[cid]; G = o.get('group'); clean = o.get('clean', lambda n: n); canon = o.get('canon', lambda k: k)
    if o.get('level'): return apply_official_level(o, lv, fin, pop, cen, zon, zl)
    if o.get('custom') == 'us_cousub': return apply_us_cousub(o, lv, fin, pop, cen, zon, zl)
    got = {}; est = set(); pool = {}; seen_groups = set(); n_rec = n_match = 0
    if 'codes' in o:
        cu = lau_units(o['codes'], lv, fin)
        gname = {i: '*' for i in lv[fin]}
        for code, cnt in o['records']():
            n_rec += 1; seen_groups.add('*')
            i = cu.get(code)
            if i is None: pool['*'] = pool.get('*', 0) + cnt
            else: got[i] = got.get(i, 0) + cnt; n_match += 1
    else:
        def anc(i):
            L, j = fin, i
            while L > G: j = lv[L][j]['p']; L -= 1
            return j
        gname = {i: norm(clean(lv[G][anc(i)]['n'])) for i in lv[fin]}
        idx = {}
        for i, u in lv[fin].items():
            for k in {canon(norm(clean(u['n']))), canon(norm(u['n']))}: idx.setdefault((gname[i], k), []).append(i)
        extra = []
        for grp, name, cnt, lon, lat in o['records']():
            g = norm(clean(grp)); seen_groups.add(g); n_rec += 1
            c = []
            for nm in (name if isinstance(name, list) else [name]):
                c = idx.get((g, canon(norm(nm))), []) or idx.get((g, canon(norm(clean(nm)))), [])
                if c: break
            c = list(dict.fromkeys(c))
            if len(c) > 1 and lon is not None:
                pt = shapely.Point(lon, lat)
                c = [i for i in c if lv[fin][i]['g'] is not None and lv[fin][i]['g'].contains(pt)] or c
            if len(c) > 1:  # same name twice in the group (or one municipality drawn in pieces): share by the grid
                w = sum(pop[fin].get(i, 0) for i in c) or len(c)
                for i in c: got[i] = got.get(i, 0) + cnt * ((pop[fin].get(i, 0) or (w == len(c))) / w); est.add(i)
                n_match += 1
            elif c: got[c[0]] = got.get(c[0], 0) + cnt; n_match += 1
            elif lon is not None: extra.append((g, cnt, shapely.Point(lon, lat)))
            else: pool[g] = pool.get(g, 0) + cnt
        for g, cnt, pt in extra:  # unmatched but located: goes to the area that contains it, if that area has its count
            hit = [i for i in lv[fin] if gname[i] == g and i in got and lv[fin][i]['g'] is not None and lv[fin][i]['g'].contains(pt)]
            if hit and not [i for i in lv[fin] if gname[i] == g and i not in got]: got[hit[0]] += cnt; n_match += 1
            else: pool[g] = pool.get(g, 0) + cnt
    zi = len(zl); zl.append([o['label'], 0, o['date'], 0.0, 1])
    zd = len(zl); zl.append([o['label'], 0, o['date'], 0.0, 0])  # same census, shared out (estimate)
    for i, v in got.items():
        cen[fin][i] = v; z = zd if i in est else zi; zon[fin][i] = z; zl[z][1] += v; zl[z][3] += pop[fin].get(i, 0)
    lost = 0
    for g in seen_groups:
        rest = [i for i in lv[fin] if gname[i] == g and i not in got]
        tot = pool.get(g, 0)
        if not rest:
            # every unit already has its count: spread the extra over the group (new municipalities split off old ones)
            if tot:
                grp = [i for i in lv[fin] if gname[i] == g]; w = sum(cen[fin][i] for i in grp) or 1
                for i in grp: cen[fin][i] += tot * cen[fin][i] / w
            continue
        w = sum(pop[fin].get(i, 0) for i in rest) or len(rest)
        for i in rest:
            cen[fin][i] = tot * ((pop[fin].get(i, 0) or (1 if w == len(rest) else 0)) / w); zon[fin][i] = zd
            zl[zd][1] += cen[fin][i]; zl[zd][3] += pop[fin].get(i, 0)
    print(cid, 'official:', n_match, 'of', n_rec, 'records matched;', sum(1 for i in got if i not in est), 'units exact,',
          len([i for i in lv[fin] if gname[i] in seen_groups and i not in got]), 'shared; unmatched pools',
          {k: v for k, v in pool.items() if v}, flush=True)
    return {}

if __name__ == '__main__':
    I = json.load(open('/home/claude/site/data/index.json'))
    cids = sys.argv[1:] or sorted(I['c'])
    res = run(cids)
    part = '/home/claude/build/pop_part_' + ('all' if not sys.argv[1:] else '_'.join(sys.argv[1:4])) + '.json'
    json.dump(res, open(part, 'w'), separators=(',', ':'))
    print('wrote', part)
