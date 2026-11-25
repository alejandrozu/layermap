import glob, json, sys
import numpy as np, geopandas as gpd, shapely, pandas as pd
sys.path.insert(0, '/home/claude/scripts')
from regions import MERGE, REGION_OF, NAMES, REGIONS, DROP, SPLIT

UN = set("""AFG ALB DZA AND AGO ATG ARG ARM AUS AUT AZE BHS BHR BGD BRB BLR BEL BLZ BEN BTN BOL BIH BWA BRA BRN BGR BFA BDI CPV KHM CMR CAN CAF TCD CHL CHN COL COM COG CRI CIV HRV CUB CYP CZE PRK COD DNK DJI DMA DOM ECU EGY SLV GNQ ERI EST SWZ ETH FJI FIN FRA GAB GMB GEO DEU GHA GRC GRD GTM GIN GNB GUY HTI HND HUN ISL IND IDN IRN IRQ IRL ISR ITA JAM JPN JOR KAZ KEN KIR KWT KGZ LAO LVA LBN LSO LBR LBY LIE LTU LUX MDG MWI MYS MDV MLI MLT MHL MRT MUS MEX FSM MDA MCO MNG MNE MAR MOZ MMR NAM NRU NPL NLD NZL NIC NER NGA MKD NOR OMN PAK PLW PAN PNG PRY PER PHL POL PRT QAT KOR ROU RUS RWA KNA LCA VCT WSM SMR STP SAU SEN SRB SYC SLE SGP SVK SVN SLB SOM ZAF SDS ESP LKA SDN SUR SWE CHE SYR TJK THA TLS TGO TON TTO TUN TUR TKM TUV UGA UKR ARE GBR TZA USA URY UZB VUT VEN VNM YEM ZMB ZWE""".split())
assert len(UN) == 193, len(UN)
OBS = {"PSX", "VAT"}

a = gpd.read_file('/home/claude/raw/ne/admin0/ne_10m_admin_0_countries.shp')
d = gpd.read_file(glob.glob('/home/claude/raw/ne/admin0_deu/*.shp')[0])
d['geometry'] = shapely.make_valid(d.geometry.values); a['geometry'] = shapely.make_valid(a.geometry.values)
ua = shapely.union_all(a.geometry.values); ud = shapely.union_all(d.geometry.values)
diff = ua.difference(ud); extra = []
for p in getattr(diff, 'geoms', [diff]):
    if p.geom_type != 'Polygon' or p.area < 1e-5: continue
    rp = p.representative_point()
    if 35.5 < rp.x < 36.1 and 32.6 < rp.y < 33.4: code = 'SYR'
    else:
        own = a[a.contains(rp)]
        if not len(own): continue
        code = own.iloc[0].ADM0_A3
    extra.append({'ADM0_A3': code, 'geometry': p})
names = dict(zip(a.ADM0_A3, a.NAME)); names.update(dict(zip(d.ADM0_A3, d.NAME)))
g = pd.concat([d[['ADM0_A3', 'geometry']], gpd.GeoDataFrame(extra, crs=d.crs)], ignore_index=True)
g = g.dissolve('ADM0_A3').reset_index().rename(columns={'ADM0_A3': 'id244'})
g = g[~g.id244.isin(DROP)]
g['id'] = g.id244.map(lambda c: MERGE.get(c, c))
g['n244'] = g.id244.map(lambda c: NAMES.get(c, names.get(c, c)))
# split undemarcated areas between neighbours by nearest point
rows = []
for code, (c1, c2) in SPLIT.items():
    if code not in set(g.id244): continue
    geom = g[g.id244 == code].geometry.iloc[0]
    A = shapely.union_all(g[g.id == c1].geometry.values); B = shapely.union_all(g[g.id == c2].geometry.values)
    x0, y0, x1, y1 = geom.bounds; st = 0.01
    cells = {c1: [], c2: []}
    for x in np.arange(x0, x1, st):
        for y in np.arange(y0, y1, st):
            cell = shapely.box(x, y, x + st, y + st).intersection(geom)
            if cell.is_empty: continue
            c = cell.representative_point()
            cells[c1 if A.distance(c) <= B.distance(c) else c2].append(cell)
    for c, cs in cells.items():
        if cs: rows.append({'id244': code + '_' + c, 'id': c, 'n244': names.get(c, c), 'geometry': shapely.union_all(cs)})
    g = g[g.id244 != code]
g = pd.concat([g, gpd.GeoDataFrame(rows, crs=g.crs)], ignore_index=True)
# major lakes are water, not land
lk = gpd.read_file('/home/claude/raw/ne/lakes/ne_10m_lakes.shp')
lk = lk[(lk.scalerank <= 2) & lk.featurecla.isin(['Lake', 'Reservoir'])]
lakes = shapely.union_all(shapely.make_valid(lk.geometry.values))
print('lakes removed:', len(lk))
g['geometry'] = [shapely.make_valid(x.difference(lakes)) for x in g.geometry.values]
g = g[~g.geometry.is_empty]
bad = sorted(set(g.id) - UN - OBS - {'ATA'})
if bad: print('NOT UN:', bad); sys.exit(1)
miss = sorted(UN - set(g.id))
print('UN members missing from map:', miss)
g['n'] = g.id.map(lambda c: NAMES.get(c, names.get(c, c)))
g['r'] = g.id.map(REGION_OF)
if g.r.isna().any(): print('NO REGION', set(g[g.r.isna()].id)); sys.exit(1)
print(len(g), 'pieces ->', g.id.nunique(), 'country-level units')
print(g.groupby('r').id.nunique().to_dict())
g[['id244', 'n244', 'id', 'n', 'r', 'geometry']].to_file('/home/claude/build/world_units.geojson', driver='GeoJSON')
json.dump(REGIONS, open('/home/claude/build/regions.json', 'w'))
