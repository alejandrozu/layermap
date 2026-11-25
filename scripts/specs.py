"""Level chains per country (keyed by world id). Countries not listed here are built
automatically from geoBoundaries levels (see auto_spec in run_all.py)."""
from groups import *
import json
def J(n): return json.load(open('/home/claude/build/groupings/' + n))

def gb(iso, adm, **o): return ('gb', iso, adm) if not o else ('gb', iso, adm, o)
def gbh(iso, adm, **o): return ('gbh', iso, adm) if not o else ('gbh', iso, adm, o)
def nuts(cc, l, year=2024): return ('nuts', year, l, cc)
def lau(cc): return ('lau', cc)
def L(s, p, *src): return {'label': (s, p), 'geo': list(src)}
def G(s, p, mapping): return {'label': (s, p), 'group': mapping}

MUN = ('Municipality', 'Municipalities')

CUSTOM = {
    # ---------------- Europe: NUTS chains ending in LAU (municipalities) ----------------
    'ALB': [L('Region', 'Regions', nuts('AL', 2)), L('County', 'Counties', nuts('AL', 3)), L(*MUN, lau('AL'))],
    'AUT': [L('State', 'States', gb('AUT', 'ADM1')), L('District', 'Districts', gb('AUT', 'ADM2')), L(*MUN, lau('AT'))],
    'BEL': [L('Region', 'Regions', nuts('BE', 1)), L('Province', 'Provinces', nuts('BE', 2)), L('Arrondissement', 'Arrondissements', nuts('BE', 3)), L(*MUN, lau('BE'))],
    'BGR': [L('Planning region', 'Planning regions', nuts('BG', 2)), L('Province', 'Provinces', nuts('BG', 3)), L(*MUN, lau('BG'))],
    'CHE': [L('Greater region', 'Greater regions', nuts('CH', 2)), L('Canton', 'Cantons', nuts('CH', 3)), L('District', 'Districts', gb('CHE', 'ADM2')), L(*MUN, lau('CH'))],
    'CYP': [L('District', 'Districts', gb('CYP', 'ADM1')), L('Community', 'Communities', lau('CY'))],
    'CZE': [L('Region (kraj)', 'Regions (kraje)', nuts('CZ', 3)), L('District (okres)', 'Districts (okresy)', gb('CZE', 'ADM2')), L(*MUN, lau('CZ'))],
    'DEU': [L('State', 'States', nuts('DE', 1)), L('Government region', 'Government regions', nuts('DE', 2)), L('District (Kreis)', 'Districts (Kreise)', nuts('DE', 3)),
            L('Municipal association', 'Municipal associations (Ämter, Verbandsgemeinden…)', ('file', '/home/claude/raw/extra/germany_vwg/vwg_named.gpkg', 'name')),
            L(*MUN, lau('DE'))],
    'DNK': [L('Region', 'Regions', nuts('DK', 2)), L('Province', 'Provinces', nuts('DK', 3)), L(*MUN, lau('DK'), gb('GRL', 'ADM1'))],
    'EST': [L('Statistical region', 'Statistical regions', nuts('EE', 3)), L('County', 'Counties', gb('EST', 'ADM1')), L(*MUN, lau('EE'))],
    'GRC': [L('Region', 'Regions', nuts('EL', 2)), L('Regional unit', 'Regional units', nuts('EL', 3)), L(*MUN, gb('GRC', 'ADM3')), L('Local community', 'Local communities', lau('EL'))],
    'ESP': [L('Autonomous community', 'Autonomous communities', nuts('ES', 2)), L('Province / island', 'Provinces & islands', nuts('ES', 3)),
            L('Comarca', 'Comarcas', ('file', '/home/claude/raw/es/comarcas_mix.gpkg', 'name')), L(*MUN, lau('ES'))],
    'FIN': [L('Major region', 'Major regions', nuts('FI', 2)), L('Region', 'Regions', nuts('FI', 3)), L(*MUN, lau('FI'))],
    'FRA': [L('Region', 'Regions (+ overseas collectivities)', gb('FRA', 'ADM1'), ('nutsids', 2024, 2, 'FR', ['FRY1', 'FRY2', 'FRY3', 'FRY4', 'FRY5'])),
            L('Department', 'Departments', nuts('FR', 3)),
            L('Arrondissement', 'Arrondissements', gb('FRA', 'ADM3')),
            L('Canton', 'Cantons', gb('FRA', 'ADM4')),
            L('Commune', 'Communes', lau('FR'))],
    'HRV': [L('Region', 'Regions', nuts('HR', 2)), L('County', 'Counties', nuts('HR', 3)), L(*MUN, lau('HR'))],
    'HUN': [L('Region', 'Regions', nuts('HU', 2)), L('County', 'Counties', nuts('HU', 3)), L('District (járás)', 'Districts (járások)', gb('HUN', 'ADM2')), L(*MUN, lau('HU'))],
    'IRL': [L('Province', 'Provinces', gb('IRL', 'ADM1')), L('County', 'Counties', ('ne1', 'IRL')), L('Local electoral area', 'Local electoral areas', lau('IE'))],
    'ISL': [L('Region', 'Regions', gb('ISL', 'ADM1')), L(*MUN, lau('IS'))],
    'ITA': [L('Macro-region', 'Macro-regions', nuts('IT', 1)), L('Region', 'Regions', nuts('IT', 2)), L('Province', 'Provinces', nuts('IT', 3)),
            dict(L('Local labour system (SLL)', 'Local labour systems (ISTAT SLL)', ('file', '/home/claude/raw/extra/italy_sll/sll_named.gpkg', 'name')), nodefrag=True),
            L(*MUN, lau('IT'))],
    'LIE': [L(*MUN, lau('LI'))],
    'LTU': [L('County', 'Counties', nuts('LT', 3)), L(*MUN, lau('LT'))],
    'LUX': [L('Canton', 'Cantons', gb('LUX', 'ADM1')), L('Commune', 'Communes', lau('LU'))],
    'LVA': [L('Statistical region', 'Statistical regions', nuts('LV', 3)), L(*MUN, lau('LV'))],
    'MLT': [L('Island group', 'Island groups', nuts('MT', 3)), L('Local council', 'Local councils', lau('MT'))],
    'NLD': [L('Province', 'Provinces', nuts('NL', 2)), L('COROP region', 'COROP regions', nuts('NL', 3)), L(*MUN, lau('NL'))],
    'NOR': [L('Region', 'Regions', nuts('NO', 2)), L('County', 'Counties', nuts('NO', 3)), L(*MUN, lau('NO'))],
    'POL': [L('Voivodeship', 'Voivodeships', gb('POL', 'ADM1')), L('Subregion', 'Subregions', nuts('PL', 3)), L('County (powiat)', 'Counties (powiaty)', gb('POL', 'ADM2')), L('Municipality (gmina)', 'Municipalities (gminy)', lau('PL'))],
    'PRT': [L('Region', 'Regions', nuts('PT', 2)), L('Intermunicipal entity', 'Intermunicipal entities', nuts('PT', 3)), L(*MUN, gb('PRT', 'ADM2')), L('Parish', 'Parishes', lau('PT'))],
    'ROU': [L('Development region', 'Development regions', nuts('RO', 2)), L('County', 'Counties', nuts('RO', 3)), L('Commune / town', 'Communes & towns', lau('RO'))],
    'SWE': [L('National area', 'National areas', nuts('SE', 2)), L('County (län)', 'Counties (län)', nuts('SE', 3)), L(*MUN, lau('SE'))],
    'SVN': [L('Statistical region', 'Statistical regions', nuts('SI', 3)), L(*MUN, lau('SI'))],
    'SVK': [L('Region (kraj)', 'Regions (kraje)', nuts('SK', 3)), L('District (okres)', 'Districts (okresy)', gb('SVK', 'ADM2')), L(*MUN, lau('SK'))],
    'MKD': [L('Statistical region', 'Statistical regions', nuts('MK', 3)), L(*MUN, lau('MK'))],
    'SRB': [L('Region', 'Regions', nuts('RS', 2), ('nuts0', 'XK', 'Kosovo')), L('District', 'Districts', nuts('RS', 3), nuts('XK', 3)),
            L('Municipality / city', 'Municipalities & cities', lau('RS'), gb('XKX', 'ADM2'))],
    'TUR': [L('Statistical region', 'Statistical regions (NUTS 1)', nuts('TR', 1)), L('Province', 'Provinces', gb('TUR', 'ADM1')), L('District', 'Districts', gb('TUR', 'ADM2'))],
    'GBR': [L('Country', 'Countries of the UK (+ territories)', gb('GBR', 'ADM1')), L('Region (ITL 1)', 'Regions (ITL 1)', nuts('UK', 1, 2016)),
            L('ITL 2 area', 'ITL 2 areas', nuts('UK', 2, 2016)), L('Local authority', 'Local authorities', lau('UK'))],
    'UKR': [L('Oblast', 'Oblasts', gbh('UKR', 'ADM1')), L('Raion', 'Raions', gbh('UKR', 'ADM2')), L('Hromada', 'Hromadas', gbh('UKR', 'ADM3'))],
    'MDA': [G('Development region', 'Development regions', MDA_REGIONS), L('District', 'Districts', gb('MDA', 'ADM1'))],
    # ---------------- large countries with legitimate groupings ----------------
    'RUS': [G('Federal district', 'Federal districts', RUS_FD), L('Federal subject', 'Federal subjects', gb('RUS', 'ADM1')), L('Municipal district', 'Municipal districts', gb('RUS', 'ADM2'))],
    'IND': [G('Zonal council', 'Zonal councils', IND_ZONES), L('State / UT', 'States & union territories', gb('IND', 'ADM1')), L('District', 'Districts', gb('IND', 'ADM2')), L('Subdistrict', 'Subdistricts (tehsils)', gb('IND', 'ADM3'))],
    'MEX': [G('Region (Banxico)', 'Regions (Banxico)', MEX_BANXICO), L('State', 'States', gb('MEX', 'ADM1')), L(*MUN, gb('MEX', 'ADM2'))],
    'NGA': [G('Geopolitical zone', 'Geopolitical zones', NGA_ZONES), L('State', 'States', gb('NGA', 'ADM1')), L('Local government area', 'Local government areas', gb('NGA', 'ADM2'))],
    'JPN': [G('Region', 'Regions', JPN_REGIONS), L('Prefecture', 'Prefectures', gb('JPN', 'ADM1')), L(*MUN, gb('JPN', 'ADM2'))],
    'THA': [G('Region', 'Regions', THA_REGIONS), L('Province', 'Provinces', gb('THA', 'ADM1')), L('District (amphoe)', 'Districts (amphoe)', gb('THA', 'ADM2'))],
    'VNM': [G('Socio-economic region', 'Socio-economic regions', VNM_REGIONS), L('Province', 'Provinces (pre-2025)', gb('VNM', 'ADM1')), L('District', 'Districts (pre-2025)', gb('VNM', 'ADM2'))],
    'PHL': [G('Island group', 'Island groups', PHL_ISLANDS), L('Region', 'Regions', gb('PHL', 'ADM1')), L('Province', 'Provinces', gb('PHL', 'ADM2')), L('Municipality / city', 'Municipalities & cities', gb('PHL', 'ADM3'))],
    'IDN': [G('Island group', 'Island groups', IDN_ISLANDS), L('Province', 'Provinces', gbh('IDN', 'ADM1')), L('Regency / city', 'Regencies & cities', gbh('IDN', 'ADM2')), L('District (kecamatan)', 'Districts (kecamatan)', gbh('IDN', 'ADM3'))],
    'KEN': [G('Former province', 'Former provinces', KEN_PROVINCES), L('County', 'Counties', gb('KEN', 'ADM1')), L('Sub-county', 'Sub-counties', gb('KEN', 'ADM2')), L('Ward', 'Wards', gb('KEN', 'ADM3'))],
    'DOM': [G('Development region', 'Development regions', DOM_REGIONS), L('Province', 'Provinces', gb('DOM', 'ADM1')), L(*MUN, gb('DOM', 'ADM2'))],
    'PAK': [L('Province / territory', 'Provinces & territories', gbh('PAK', 'ADM1')), L('District', 'Districts', gbh('PAK', 'ADM2')), L('Tehsil', 'Tehsils', gbh('PAK', 'ADM3'))],
    'CHN': [G('Region', 'Regions', CHN_REGIONS), L('Province', 'Provincial-level divisions', ('chn_prov',)),
            L('Prefecture', 'Prefecture-level divisions', ('chn_pref',)),
            L('County', 'County-level divisions', ('chn_county',))],
    'USA': 'usa', 'BRA': 'bra',
    'AZE': [G('Economic region', 'Economic regions', J('aze_econ.json')), L('District / city', 'Districts & cities', gb('AZE', 'ADM2'))],
    'UGA': [L('Region', 'Regions', gb('UGA', 'ADM1')), G('Sub-region', 'Sub-regions', J('uga_subregions.json')),
            L('District', 'Districts', gb('UGA', 'ADM3')), L('Sub-county', 'Sub-counties', gb('UGA', 'ADM4'))],
    'MLT': [G('District', 'Districts', J('mlt_districts.json')), L('Local council', 'Local councils', lau('MT'))],
    'AFG': [G('Region', 'Regions (CSO)', J('afg.json')), L('Province', 'Provinces', gb('AFG', 'ADM1')), L('District', 'Districts', gb('AFG', 'ADM2'))],
    'IRN': [G('Region', 'Regions (2014)', J('irn.json')), L('Province', 'Provinces', gb('IRN', 'ADM1')), L('County', 'Counties', gb('IRN', 'ADM2')), L('District', 'Districts', gb('IRN', 'ADM3'))],
    'TZA': [G('Zone', 'Zones', J('tza.json')), L('Region', 'Regions', gb('TZA', 'ADM1')), L('District', 'Districts', gb('TZA', 'ADM2')), L('Ward', 'Wards', gb('TZA', 'ADM3'))],
    'COL': [G('Region (DANE)', 'Regions (DANE)', J('col.json')), L('Department', 'Departments', gb('COL', 'ADM1')), L(*MUN, gb('COL', 'ADM2'))],
}

# every country's territories are combined into ONE first-level unit, which cracks into the territories
def pp(code, bbox, name): return ('piecepart', code, bbox, name)
DEPS = {
    'GBR': {'name': 'Crown Dependencies & Overseas Territories', 'members': [('dep', c) for c in
            ['GGY', 'JEY', 'IMN', 'GIB', 'AIA', 'BMU', 'VGB', 'CYM', 'FLK', 'MSR', 'PCN', 'SHN', 'SGS', 'TCA', 'IOT', 'ESB', 'WSB']]},
    'FRA': {'name': 'Overseas collectivities & territories', 'members': [('dep', c) for c in ['NCL', 'PYF', 'WLF', 'SPM', 'BLM', 'MAF', 'ATF', 'CLP']]},
    'AUS': {'name': 'External territories', 'members': [('dep', c) for c in ['NFK', 'IOA', 'HMD', 'ATC', 'CSI']]},
    'NZL': {'name': 'Cook Islands & Niue', 'members': [('dep', 'COK'), ('dep', 'NIU')]},
    'DNK': {'name': 'Greenland & Faroe Islands', 'members': [('dep', 'GRL'), ('dep', 'FRO')], 'keep_finest': ['Greenland']},
    'NLD': {'name': 'Caribbean parts of the Kingdom', 'members': [('dep', 'ABW'), ('dep', 'CUW'), ('dep', 'SXM'),
            pp('NLD', (-68.6, 11.9, -68.0, 12.5), 'Bonaire'), pp('NLD', (-63.1, 17.4, -62.9, 17.55), 'Sint Eustatius'),
            pp('NLD', (-63.3, 17.58, -63.2, 17.7), 'Saba')]},
    'NOR': {'name': 'Svalbard & Jan Mayen', 'members': [pp('NOR', (-10, 70.5, -7, 71.5), 'Jan Mayen'), pp('NOR', (5, 73.5, 36, 81.5), 'Svalbard')]},
}

RENAME = {
    'AUS': {'Other Territories': 'Jervis Bay Territory', 'Unincorp. Other Territories': 'Jervis Bay Territory'},
}
