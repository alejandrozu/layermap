"""Build every country.  usage: python3 run_all.py [ISO ...] [--force] [--jobs N]"""
import sys, os, json, re, traceback, time
from multiprocessing import Pool
sys.path.insert(0, '/home/claude/scripts')
import numpy as np, pandas as pd, geopandas as gpd, shapely
from specs import CUSTOM, DEPS, RENAME, L, G, gb
from groups import JPN_REGIONS, MEX_BANXICO
import build_country as bc

B = '/home/claude/build'
LOGS = B + '/logs'; os.makedirs(LOGS, exist_ok=True)
GB_LEVELS = {}
for line in open('/tmp/probe/gb_levels.txt'):
    p = line.split()
    if len(p) < 2 or ':' not in p[1]: continue
    GB_LEVELS[p[0]] = {f'ADM{k}': int(v) for k, v in (x.split(':') for x in p[1:])}
GBMAP = {'KOS': 'XKX', 'PSX': 'PSE', 'SDS': 'SSD', 'SAH': 'ESH'}
LABELS = json.load(open(B + '/labels.json')) if os.path.exists(B + '/labels.json') else {}

def auto_spec(cid):
    iso = GBMAP.get(cid, cid)
    lv = GB_LEVELS.get(iso)
    if not lv: return None
    lab = LABELS.get(iso, {})
    drops = set(LABELS.get('_drop', {}).get(iso, []))
    out, prev = [], 1
    for k in range(1, 6):
        a = f'ADM{k}'
        if a not in lv or a in drops: continue
        if lv[a] <= prev: continue
        s, p = lab.get(a, ['Division', 'Divisions'])
        out.append(L(s, p, gb(iso, a)))
        prev = lv[a]
    return out or None

US_DIV = {
    'New England': ['Connecticut', 'Maine', 'Massachusetts', 'New Hampshire', 'Rhode Island', 'Vermont'],
    'Middle Atlantic': ['New Jersey', 'New York', 'Pennsylvania'],
    'East North Central': ['Illinois', 'Indiana', 'Michigan', 'Ohio', 'Wisconsin'],
    'West North Central': ['Iowa', 'Kansas', 'Minnesota', 'Missouri', 'Nebraska', 'North Dakota', 'South Dakota'],
    'South Atlantic': ['Delaware', 'District of Columbia', 'Florida', 'Georgia', 'Maryland', 'North Carolina', 'South Carolina', 'Virginia', 'West Virginia'],
    'East South Central': ['Alabama', 'Kentucky', 'Mississippi', 'Tennessee'],
    'West South Central': ['Arkansas', 'Louisiana', 'Oklahoma', 'Texas'],
    'Mountain': ['Arizona', 'Colorado', 'Idaho', 'Montana', 'Nevada', 'New Mexico', 'Utah', 'Wyoming'],
    'Pacific': ['Alaska', 'California', 'Hawaii', 'Oregon', 'Washington'],
    'U.S. territories': ['Puerto Rico', 'Guam', 'United States Virgin Islands', 'American Samoa',
                         'Commonwealth of the Northern Mariana Islands', 'U.S. Minor Outlying Islands'],
}

def usa_spec():
    c = gpd.read_file('/home/claude/raw/us/cb_2023_us_county_500k.shp').to_crs(4326)
    c = c.reset_index(drop=True)
    umi = bc.load_src(('dep', 'UMI'))
    c = pd.concat([c, gpd.GeoDataFrame({'STATEFP': ['74'], 'COUNTYFP': ['000'], 'STATE_NAME': ['U.S. Minor Outlying Islands'],
                                        'NAMELSAD': ['U.S. Minor Outlying Islands']}, geometry=umi.geometry.values, crs=4326)], ignore_index=True)
    rows, dn = {}, {}
    for line in open('/home/claude/raw/us/county_list.txt', encoding='latin1'):
        m = re.match(r'^(\d\d)\s+(\d\d)\s+(\d\d\d)\s+(.*?)\s+([12])\s*$', line.rstrip('\n'))
        if not m: continue
        st, di, co, name, fl = m.groups()
        if co == '999': dn[(st, di)] = re.sub(r'^D\d+\s+', '', name.strip())
        elif co not in ('000', '888') and fl == '1': rows[(st, co)] = di
    c['asd'] = [rows.get((s, co)) for s, co in zip(c.STATEFP, c.COUNTYFP)]
    c['geometry'] = shapely.make_valid(c.geometry.values)
    # unmatched counties: join the district whose counties they touch most, else statewide
    for i in np.where(c.asd.isna())[0]:
        st = c.STATEFP[i]; same = c[(c.STATEFP == st) & c.asd.notna()]
        if len(same):
            d = same.geometry.distance(c.geometry[i])
            c.loc[i, 'asd'] = same.asd[d.idxmin()]
        else:
            c.loc[i, 'asd'] = '00'; dn[(st, '00')] = c.STATE_NAME[i] + ('' if int(st) > 56 else ' (statewide)')
    c['asd_key'] = c.STATEFP + c.asd
    asd = c.dissolve('asd_key').reset_index()
    asd['name'] = [dn.get((s, a), f'District {a}') for s, a in zip(asd.STATEFP, asd.asd)]
    st = c.dissolve('STATEFP').reset_index(); st['name'] = st.STATE_NAME
    cn = c.copy(); cn['name'] = cn.NAMELSAD
    # county subdivisions (Census Bureau): census county divisions (CCDs) where there are no legal townships,
    # towns / townships / MCDs elsewhere, barrios in Puerto Rico; a county without any stays whole at this level
    cs = gpd.read_file('/home/claude/raw/us/cousub/cb_2023_us_cousub_500k.shp').to_crs(4326)
    cs['name'] = cs.NAMELSAD
    have = set(cs.STATEFP + cs.COUNTYFP)
    whole = cn[~(cn.STATEFP + cn.COUNTYFP).isin(have)]
    cs_geoid = list(cs.GEOID)
    co_idx = {k: i for i, k in enumerate(cn.STATEFP + cn.COUNTYFP)}
    cs_co = [co_idx[g[:5]] for g in cs.GEOID] + [co_idx[k] for k in (whole.STATEFP + whole.COUNTYFP)]
    cs = pd.concat([cs[['name', 'geometry']], whole[['name', 'geometry']]], ignore_index=True)
    cs['geometry'] = [bc.polys_only(g) for g in shapely.make_valid(cs.geometry.values)]
    assert cs.geometry.notna().all()
    # places (2020 cities, towns, villages, CDPs) in each subdivision plus the rest of it, and census tracts cut at
    # both lines (us_place_pieces.py); counties without subdivisions stay whole at every level
    csi = {g: i for i, g in enumerate(cs_geoid)}
    p6 = gpd.read_file('/home/claude/raw/us/place/pieces6.gpkg')[['name', 'geometry']]
    n6 = len(p6)
    p6 = pd.concat([p6, whole[['name', 'geometry']]], ignore_index=True)
    p6['geometry'] = [bc.polys_only(g) for g in shapely.make_valid(p6.geometry.values)]
    assert p6.geometry.notna().all()
    pc = gpd.read_file('/home/claude/raw/us/place/pieces7.gpkg')[['name', 'cs', 'p6', 'geometry']]
    pc['_l5'] = [csi.get(g, -1) for g in pc.cs]
    pc['_l6'] = pc.p6.astype(int)
    wh = whole[['name', 'geometry']].copy()
    wh['_l5'] = [len(cs_geoid) + i for i in range(len(wh))]; wh['_l6'] = [n6 + i for i in range(len(wh))]
    pc = pd.concat([pc[['name', '_l5', '_l6', 'geometry']], wh], ignore_index=True)
    pc['_l4'] = [cs_co[m] if m >= 0 else -1 for m in pc._l5]
    pc['geometry'] = [bc.polys_only(g) for g in shapely.make_valid(pc.geometry.values)]
    pc = pc[pc.geometry.notna()].reset_index(drop=True)
    return [G('Census division', 'Census divisions', US_DIV),
            L('State', 'States', ('gdf', st[['name', 'geometry']])),
            L('Agricultural statistics district', 'Agricultural statistics districts (USDA)', ('gdf', asd[['name', 'geometry']])),
            dict(L('County', 'Counties', ('gdf', cn[['name', 'geometry']])), col='_l4'),
            dict(L('County subdivision', 'County subdivisions (CCDs, towns & townships)', ('gdf', cs)), col='_l5', missing='own'),
            dict(L('Place', 'Places (cities, towns, villages, CDPs) and the rest of each subdivision', ('gdf', p6)), col='_l6', missing='own'),
            L('Census tract', 'Census tracts (split at place and subdivision lines)', ('gdf', pc))]

def bra_spec():
    R = '/home/claude/raw/br/'
    uf = gpd.read_file(R + 'BR_UF_2023/BR_UF_2023.shp').to_crs(4326)
    reg = uf.dissolve('NM_REGIAO').reset_index(); reg['name'] = reg.NM_REGIAO
    return [L('Region', 'Regions', ('gdf', reg[['name', 'geometry']])),
            L('State', 'States', ('file', R + 'BR_UF_2023/BR_UF_2023.shp', 'NM_UF')),
            L('Intermediate region', 'Intermediate geographic regions (IBGE)', ('file', R + 'BR_RG_Intermediarias_2023/BR_RG_Intermediarias_2023.shp', 'NM_RGINT')),
            L('Immediate region', 'Immediate geographic regions (IBGE)', ('file', R + 'BR_RG_Imediatas_2023/BR_RG_Imediatas_2023.shp', 'NM_RGI')),
            L(*('Municipality', 'Municipalities'), ('file', R + 'BR_Municipios_2023/BR_Municipios_2023.shp', 'NM_MUN'))]

def dissolve_map(src, mapping, within=None, log=None):
    """polygons of `src` (a build_country source) dissolved by a {group: [member names]} table;
    `within`: only members whose interior point lies inside this geometry"""
    g = bc.load_src(src).copy()
    if within is not None:
        g = g[shapely.contains(within, g.geometry.representative_point().values)]
    lut = {bc.norm(n): grp for grp, ns in mapping.items() for n in ns}
    g['grp'] = [lut.get(bc.norm(n)) for n in g.name]
    miss = sorted(g[g.grp.isna()].name)
    if miss and log is not None: log.append(f'dissolve_map unmatched: {miss[:30]}')
    g = g[g.grp.notna()]
    out = g.dissolve('grp').reset_index()[['grp', 'geometry']].rename(columns={'grp': 'name'})
    return out

def cze_spec():
    l = bc.load_src(('lau', 'CZ'))
    raw = gpd.read_file('/home/claude/raw/gisco/LAU_RG_01M_2023_4326.gpkg')
    raw = raw[raw.CNTR_CODE == 'CZ'][['LAU_ID', 'geometry']]
    v = pd.read_csv('/home/claude/raw/extra/czechia_orp/cis65vaz43.csv', dtype=str)
    raw['orp'] = raw.LAU_ID.map(dict(zip(v.chodnota2, v.text1)))
    raw['geometry'] = shapely.make_valid(raw.geometry.values)
    orp = raw.dissolve('orp').reset_index().rename(columns={'orp': 'name'})[['name', 'geometry']]
    return [L('Region (kraj)', 'Regions (kraje)', ('nuts', 2024, 3, 'CZ')),
            L('District (okres)', 'Districts (okresy)', gb('CZE', 'ADM2')),
            L('Administrative district (ORP)', 'Administrative districts (ORP)', ('gdf', orp)),
            L('Municipality', 'Municipalities', ('lau', 'CZ'))]

def can_spec():
    return [L('Province / territory', 'Provinces & territories', gb('CAN', 'ADM1')),
            L('Economic region', 'Economic regions', gb('CAN', 'ADM2')),
            L('Census division', 'Census divisions', ('file', '/home/claude/raw/extra/canada_cd/lcd_000b21s_e_2021_CD_4326.gpkg', 'CDNAME')),
            L('Census subdivision', 'Census subdivisions (municipalities)', gb('CAN', 'ADM3'))]

GRP = '/home/claude/build/groupings/'
def jload(n): return json.load(open(GRP + n))

def dza_spec():
    com = bc.load_src(('gbh', 'DZA', 'ADM2')).copy()
    wil = bc.load_src(('gb', 'DZA', 'ADM1'))
    pts = com.geometry.representative_point().values
    com['wil'] = [wil.name.values[i] if i >= 0 else None for i in bc.member(pts, wil, force=True)]
    t = pd.read_csv(GRP + 'dza_dairas.csv', dtype=str).fillna('')
    lut = {(bc.norm(w), bc.norm(c)): d for w, c, d in zip(t.wilaya, t.commune, t.daira) if d}
    com['dai'] = [lut.get((bc.norm(w or ''), bc.norm(n))) for w, n in zip(com.wil, com.name)]
    # communes without a daira take the daira of the nearest commune of the same wilaya
    P = np.array([(p.x, p.y) for p in pts])
    for i in np.where(com.dai.isna())[0]:
        same = np.where((com.wil.values == com.wil.values[i]) & com.dai.notna().values)[0]
        if len(same): com.iloc[i, com.columns.get_loc('dai')] = com.dai.values[same[np.argmin(((P[same] - P[i]) ** 2).sum(1))]]
    com['key'] = com.wil.fillna('') + '|' + com.dai.fillna(com.name)
    dai = com.dissolve('key').reset_index()
    dai['name'] = dai.key.str.split('|').str[1]
    return [G('Football region', 'Football regions', jload('dza_football.json')),
            L('Province (wilaya)', 'Provinces (wilayas)', gb('DZA', 'ADM1')),
            L('District (daïra)', 'Districts (daïras)', ('gdf', dai[['name', 'geometry']])),
            L('Commune', 'Communes', ('gbh', 'DZA', 'ADM2'))]

def arg_spec():
    prov = bc.load_src(('gbh', 'ARG', 'ADM1'))
    ba = prov[prov.name == 'Buenos Aires'].geometry.iloc[0]
    sec = dissolve_map(('gbh', 'ARG', 'ADM2'), jload('arg_ba_sections.json'), within=ba)
    return [L('Province', 'Provinces', ('gbh', 'ARG', 'ADM1')),
            L('Electoral section', 'Electoral sections (Buenos Aires province)', ('gdf', sec)),
            L('Department / partido', 'Departments & partidos', ('gbh', 'ARG', 'ADM2'))]

HKD_SUB = {'宗谷': 'Soya', '上川': 'Kamikawa', '留萌': 'Rumoi', 'オホーツク': 'Okhotsk', '空知': 'Sorachi', '石狩': 'Ishikari',
           '後志': 'Shiribeshi', '胆振': 'Iburi', '日高': 'Hidaka', '渡島': 'Oshima', '檜山': 'Hiyama', '十勝': 'Tokachi',
           '釧路': 'Kushiro', '根室': 'Nemuro'}
def jpn_spec():
    import pykakasi
    kk = pykakasi.kakasi()
    roma = lambda t: ''.join(x['hepburn'] for x in kk.convert(t)).replace(' ', '').capitalize()
    J = '/home/claude/raw/extra/japan/'
    mun = bc.load_src(('gb', 'JPN', 'ADM2')).copy()
    raw = gpd.read_file('/home/claude/raw/gb/JPN_ADM2.geojson')
    mun['sid'] = raw.shapeID.values
    jn = pd.read_csv(J + 'JPN_ADM2_to_secondary_medical_area_join.csv', dtype=str)
    mun['acode'] = mun.sid.map(dict(zip(jn.shapeID, jn.iryoken2_code)))
    a38 = pd.read_csv(J + 'A38-20_municipality_to_secondary_medical_area.csv', dtype=str)
    def lv(x):  # long vowels as written in English names
        x = bc.norm(x).replace(' ', '')
        for a, b in (('ou', 'o'), ('oo', 'o'), ('uu', 'u'), ('aa', 'a'), ('ii', 'i')): x = x.replace(a, b)
        return x
    def strip(t): return t[:-1] if t and t[-1] in '市町村区郡' else t
    names = {}
    for code, grp in a38.groupby('iryoken2_code'):
        an = grp.iryoken2_name.iloc[0]
        members = list(mun[mun['acode'] == code].name)
        ml = {lv(m): m for m in members}
        cands = [strip(x) for x in an.split('・')]
        cands += [strip(x) for x in grp[grp.muni_name.str.endswith('市')].sort_values('muni_code').muni_name]
        cands += [strip(x) for x in grp.sort_values('muni_code').muni_name]
        label = None
        for c in cands:
            hit = ml.get(lv(roma(c)))
            if hit: label = hit; break
        if not label: label = roma(cands[1] if len(cands) > 1 else cands[0]).capitalize()
        names[code] = f"{an} ({label} area)"
    mun['area_name'] = mun['acode'].map(names)
    med = mun[mun['acode'].notna()].dissolve('acode').reset_index()
    med['name'] = med.area_name
    hk = pd.read_csv(J + 'n03/JPN_ADM2_hokkaido_join.csv', dtype=str)
    def subname(t):
        for k, v in HKD_SUB.items():
            if t.startswith(k): return v + ' Subprefecture'
        return t
    mun['sub'] = mun.sid.map(dict(zip(hk.shapeID, hk.subprefecture.map(subname))))
    sub = mun[mun['sub'].notna()].dissolve('sub').reset_index(); sub['name'] = sub['sub']
    return [G('Region', 'Regions', JPN_REGIONS), L('Prefecture', 'Prefectures', gb('JPN', 'ADM1')),
            L('Subprefecture', 'Subprefectures (Hokkaido)', ('gdf', sub[['name', 'geometry']])),
            L('Secondary medical area', 'Secondary medical areas', ('gdf', med[['name', 'geometry']])),
            L('Municipality', 'Municipalities', gb('JPN', 'ADM2'))]

def aus_spec():
    lga = bc.load_src(('gb', 'AUS', 'ADM2')).copy()
    raw = gpd.read_file('/home/claude/raw/gb/AUS_ADM2.geojson')
    lga['sid'] = raw.shapeID.values
    j = pd.read_csv('/home/claude/raw/extra/australia/AUS_ADM2_to_RDA2025_join.csv', dtype=str)
    lga['rda'] = lga.sid.map(dict(zip(j.shapeID, j.rda)))
    rda = lga[lga.rda.notna()].dissolve('rda').reset_index()
    rda['name'] = 'RDA ' + rda.rda
    return [L('State / territory', 'States & territories', gb('AUS', 'ADM1')),
            L('RDA region', 'Regional Development Australia regions', ('gdf', rda[['name', 'geometry']])),
            L('Local government area', 'Local government areas', gb('AUS', 'ADM2'))]

def mex_spec():
    mun = bc.load_src(('gb', 'MEX', 'ADM2')).copy()
    raw = gpd.read_file('/home/claude/raw/gb/MEX_ADM2.geojson')
    mun['sid'] = raw.shapeID.values
    j = pd.read_csv('/home/claude/raw/extra/mexico/MEX_ADM2_to_DDR_join.csv', dtype=str)
    j['key'] = j.cvegeo.str[:2] + '-' + j.cve_ddr.str.split('|').str[0]
    j['dname'] = j.ddr.str.split('|').str[0]
    mun['ddr'] = mun.sid.map(dict(zip(j.shapeID, j.key)))
    names = dict(zip(j.key, j.dname))
    d = mun[mun.ddr.notna()].dissolve('ddr').reset_index()
    d['name'] = 'DDR ' + d.ddr.map(names).str.title()
    return [G('Region (Banxico)', 'Regions (Banxico)', MEX_BANXICO), L('State', 'States', gb('MEX', 'ADM1')),
            L('Rural development district', 'Rural development districts (DDR)', ('gdf', d[['name', 'geometry']])),
            L('Municipality', 'Municipalities', gb('MEX', 'ADM2'))]

def spec_for(cid):
    if cid == 'MEX': return mex_spec()
    if cid == 'AUS': return aus_spec()
    if cid == 'JPN': return jpn_spec()
    if cid == 'DZA': return dza_spec()
    if cid == 'ARG': return arg_spec()
    if cid == 'CZE': return cze_spec()
    if cid == 'CAN': return can_spec()
    s = CUSTOM.get(cid)
    if s == 'usa': return usa_spec()
    if s == 'bra': return bra_spec()
    if s: return s
    return auto_spec(cid)

INTERVAL = {'USA': 120}
COVER_MIN = {'USA': 0.04}        # only holes this big (sq deg) become filler units          # simplification (m) when the automatic one does not suit
PARTS = {'USA': {4: 0, 5: 0, 6: 0}}     # level index -> split that level's file by this level's units (census divisions)

def run(cid, force=False):
    d = f'{B}/chunks/{cid}'
    if not force and os.path.exists(d + '/entry.json'): return cid, 'cached'
    t = time.time(); log = []
    try:
        levels = spec_for(cid)
        if not levels: return cid, 'leaf'
        fin, counts, names, parents = bc.build(cid, levels, frame_id=cid, log=log, deps=DEPS.get(cid), interval=INTERVAL.get(cid),
                                               cover_min=COVER_MIN.get(cid, 0.0))
        rn = RENAME.get(cid, {})
        if rn: names = [{k: rn.get(v, v) for k, v in lv.items()} for lv in names]
        e = bc.write(cid, levels, fin, counts, names, parents, log=log, parts=PARTS.get(cid))
        log.append(f'files: {e["F"]}')
        msg = f'ok {counts} {round(time.time()-t)}s'
    except Exception as ex:
        log.append(traceback.format_exc()); msg = 'FAIL ' + str(ex)[:200]
    open(f'{LOGS}/{cid}.txt', 'w').write('\n'.join(log) + '\n' + msg + '\n')
    return cid, msg

def run_one(a): return run(*a)

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    force = '--force' in sys.argv
    jobs = 2
    if '--jobs' in sys.argv: jobs = int(sys.argv[sys.argv.index('--jobs') + 1]); args = [a for a in args if a != str(jobs)]
    ids = args or list(gpd.read_file(B + '/frame.geojson').id)
    with Pool(jobs, maxtasksperchild=3) as pool:
        for cid, msg in pool.imap_unordered(run_one, [(i, force) for i in ids]):
            print(cid, msg, flush=True)
