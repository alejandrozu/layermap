"""Assemble site/data/pop.gz.txt from build/pop_part_all.json + country/region label points."""
import json, gzip, base64, sys
sys.argv = ['x']; sys.path.insert(0, '/home/claude/scripts')
import population as P

part = json.load(open('/home/claude/build/pop_part_all.json'))
W = json.load(open('/home/claude/build/world.json'))
geom = P.decode(W)
cc = P.CC
out = {'c': part, 'w': {}, 'cl': {}, 'rl': {}, 'src': 'UN Population and Vital Statistics Report (Jan 2026), latest census per country; subdivisions: GHS-POP 2020 (JRC) shares'}
for g in W['objects']['countries']['geometries']:
    p = g['properties']; cid = p['id']
    out['cl'][cid] = P.label_area(geom(g))
    if cid not in part:  # no subdivisions: census total only
        if cid in cc: out['w'][cid] = [cc[cid][2], cc[cid][1]]
        elif cid == 'VAT': r = P.UNROW[P.norm('Holy See')]; out['w'][cid] = [r[3], r[1]]
        else:
            z = P.zonal([geom(g)])[0]; out['w'][cid] = [round(z), '']
            print('no census for', cid, 'grid', round(z))
for g in W['objects']['regions']['geometries']:
    out['rl'][g['properties']['r']] = P.label_area(geom(g))
# land areas (Wikidata P2046) for atoll and micro states whose drawn outlines take in lagoons or are too
# coarse for their real size: densities would be far off otherwise. Subdivision areas are scaled to match.
AREA_FIX = {'MDV': 298.0, 'MHL': 181.0, 'PLW': 465.55, 'MCO': 2.08, 'VAT': 0.44}
for cid, a in AREA_FIX.items():
    if cid in out['c']:
        tot = sum(u[4] for u in out['c'][cid]['L'][0]) or 1
        for lev in out['c'][cid]['L']:
            for u in lev: u[4] = round(u[4] * a / tot, 3)
    if cid in out['cl']: out['cl'][cid][2] = a
# levels whose geometry is split into one file per unit of a higher level get their numbers split the same way:
# data/pop/<cid>.<part>.gz.txt = {level: [[id, count, zone, x, y, km2], ...]}, loaded with that part
import os, glob as _g
os.makedirs('/home/claude/site/data/pop', exist_ok=True)
for f in _g.glob('/home/claude/site/data/pop/*.gz.txt'): os.remove(f)
for cid in list(out['c']):
    ep = f'/home/claude/build/chunks/{cid}/entry.json'
    if not os.path.exists(ep): continue
    F = [f for f in json.load(open(ep))['F'] if len(f) > 5 and f[5]]
    if not F: continue
    c = out['c'][cid]; first = min(f[1] for f in F); by = F[0][5]['by']
    parts = {}
    for f in F:
        for k in f[5]['p']:
            t = json.load(open(f'/home/claude/build/chunks/{cid}/' + f[0].replace('{p}', k)))
            for key, o in t['objects'].items():
                lvl = int(key); rows = c['L'][lvl - 1]
                parts.setdefault(k, {})[str(lvl)] = [[int(g['properties']['i'])] + rows[int(g['properties']['i'])] for g in o['geometries']]
    sizes = {}
    for k, d in parts.items():
        b = base64.b64encode(gzip.compress(json.dumps(d, separators=(',', ':')).encode(), 9, mtime=0))
        open(f'/home/claude/site/data/pop/{cid}.{k}.gz.txt', 'wb').write(b); sizes[k] = len(b)
    c['L'] = c['L'][:first - 1]
    c['X'] = {'by': by, 'from': first, 'p': sizes}
    print(cid, 'split numbers for levels', first, '+ into', len(sizes), 'files', sum(sizes.values()) // 1000, 'KB')
js = json.dumps(out, separators=(',', ':'), ensure_ascii=False)
gz = gzip.compress(js.encode(), 9)
open('/home/claude/site/data/pop.gz.txt', 'w').write(base64.b64encode(gz).decode())
print('countries', len(part), '+', len(out['w']), 'json', len(js) // 1000, 'KB gz', len(gz) // 1000, 'KB')
