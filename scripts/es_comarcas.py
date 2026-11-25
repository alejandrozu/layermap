"""Spain comarca layer: official/functional comarcas (IGN) where the autonomous community has them,
Diputación comarcas for Bizkaia and Gipuzkoa, INE comarcas elsewhere."""
import re, sys, unicodedata
import geopandas as gpd, pandas as pd, shapely
sys.path.insert(0, '/home/claude/scripts')
from build_country import norm
R = '/home/claude/raw/es/'
ine = gpd.read_file(R + 'esp_com_99.gpkg').to_crs(4326)
ign = gpd.read_file(R + 'comarcas_ign.gpkg').to_crs(4326)
USE_IGN = ['Andalucía', 'Aragón', 'Asturias, Principado de', 'Cataluña', 'Galicia', 'Navarra, Comunidad Foral de', 'País Vasco']
ign = ign[ign['ine.ccaa.name'].isin(USE_IGN)]
ign_provs = set(ign['ine.prov.name'])  # includes Araba/Álava for País Vasco
ine = ine[ine['name'].notna() & ~ine['ine.prov.name'].isin(ign_provs | {'Bizkaia', 'Gipuzkoa'})]
# Bizkaia & Gipuzkoa from Wikipedia lists, dissolving GISCO LAU municipalities
lau = gpd.read_file('/home/claude/raw/gisco/LAU_RG_01M_2023_4326.gpkg')
lau = lau[lau.CNTR_CODE == 'ES']
lau = lau[lau.LAU_ID.str[:2].isin(['48', '20'])].copy()
def clean(x): return re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", x).replace("''", '').strip()
rows = []
for line in open(R + 'wiki_vizcaya.txt'):
    if line.startswith('| [[') and '||' in line:
        c = [clean(x) for x in line[1:].split('||')]
        com = clean(c[-1].split('|')[-1])
        for nm in (c[2], c[0], c[1].split(',')[0]):
            rows.append(('48', norm(nm), com))
txt = open(R + 'wiki_gipuzkoa.txt').read()
for m in re.finditer(r'!scope="row"[^|]*\|\s*(.+?)\n\|align=left\|(.+?)\n', txt):
    nm = clean(m.group(1)); com = m.group(2)
    com = re.sub(r'\{\{ill\|([^|}]*).*?\}\}', r'\1', com); com = clean(com)
    rows.append(('20', norm(nm), com))
lut = {}
for p, n, c in rows: lut.setdefault((p, n), c)
def find(r):
    p = r.LAU_ID[:2]
    for cand in [r.LAU_NAME] + r.LAU_NAME.replace('-', '/').split('/'):
        c = lut.get((p, norm(cand)))
        if c: return c
    return None
MANUAL = {'Arrasate': 'Debagoiena', 'Donostia': 'Donostialdea', 'Leaburu': 'Tolosaldea'}
lau['com'] = lau.apply(lambda r: MANUAL.get(r.LAU_NAME) or find(r), axis=1)
miss = lau[lau.com.isna()]
print('BI/GI municipalities', len(lau), 'unmatched', len(miss), list(miss.LAU_NAME))
lau = lau[lau.com.notna()]
bg = lau.dissolve('com').reset_index()[['com', 'geometry']].rename(columns={'com': 'name'})
out = pd.concat([ine[['name', 'geometry']], ign[['name', 'geometry']], bg], ignore_index=True)
out['name'] = out['name'].str.replace(r'^Cuadrilla de ([^/]+)/.*$', r'Cuadrilla de \1', regex=True)
out = gpd.GeoDataFrame(out, geometry='geometry', crs=4326)
out.to_file(R + 'comarcas_mix.gpkg', driver='GPKG')
print(len(out), 'comarcas;', len(ine), 'INE,', len(ign), 'IGN,', len(bg), 'Bizkaia/Gipuzkoa:', sorted(bg.name))
