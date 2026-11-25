"""Collect built country chunks into site/data: small countries bundled per region, all gzipped."""
import json, os, glob, gzip, shutil, collections
B = '/home/claude/build'; S = '/home/claude/site/data'
shutil.rmtree(S + '/c', ignore_errors=True); os.makedirs(S + '/c', exist_ok=True)
R = json.load(open(B + '/regions.json'))
world = json.load(open(B + '/world.json'))
region_of = {g['properties']['id']: g['properties']['r'] for g in world['objects']['countries']['geometries']}
idx = {'v': 2, 'regions': R, 'c': {}}
bundles = collections.defaultdict(dict)
SMALL = 120_000

import base64
def gz_write(path, obj):
    raw = json.dumps(obj, separators=(',', ':'), ensure_ascii=False).encode()
    with open(path, 'wb') as f: f.write(base64.b64encode(gzip.compress(raw, 9)))
    return len(raw), os.path.getsize(path)

tot_raw = tot_gz = 0
for d in sorted(glob.glob(B + '/chunks/*/entry.json')):
    cid = os.path.basename(os.path.dirname(d))
    if cid not in region_of: continue
    e = json.load(open(d)); F = []
    for f in e['F']:
        t = json.load(open(os.path.join(os.path.dirname(d), f[0])))
        if f[3] < SMALL:
            bundles[region_of[cid]][cid + '.' + str(f[1])] = t
            F.append(['c/' + region_of[cid] + '.gz.txt', f[1], f[2], f[3], cid + '.' + str(f[1])])
        else:
            name = f[0].replace('.json', '.gz.txt')
            r, g = gz_write(f'{S}/c/{name}', t); tot_raw += r; tot_gz += g
            F.append(['c/' + name, f[1], f[2], g])
    idx['c'][cid] = {'L': e['L'], 'F': F, 'N': e['N']}
for reg, b in bundles.items():
    r, g = gz_write(f'{S}/c/{reg}.gz.txt', b); tot_raw += r; tot_gz += g
    for cid, e in idx['c'].items():
        for f in e['F']:
            if f[0] == f'c/{reg}.gz.txt': f[3] = g
r, g = gz_write(S + '/world.gz.txt', world); tot_raw += r; tot_gz += g
json.dump(idx, open(S + '/index.json', 'w'), separators=(',', ':'), ensure_ascii=False)
for p in [S + '/world.json']:
    if os.path.exists(p): os.remove(p)
files = glob.glob(S + '/**/*.*', recursive=True)
print(f"{len(idx['c'])} countries, {len(files)} files, raw {tot_raw/1e6:.1f} MB, gz {tot_gz/1e6:.1f} MB, biggest:",
      sorted(((os.path.getsize(p), os.path.basename(p)) for p in files), reverse=True)[:5])
