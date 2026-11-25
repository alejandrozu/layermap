import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
d = json.load(open('/tmp/probe/gb_all.json'))
jobs = []
for r in d:
    n = int(r['admUnitCount'])
    if n > 40000: continue
    url = r['simplifiedGeometryGeoJSON'].replace('https://github.com/wmgeolab/geoBoundaries/raw/', 'https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/')
    out = f"/home/claude/raw/gb/{r['boundaryISO']}_{r['boundaryType']}.geojson"
    if os.path.exists(out) and os.path.getsize(out) > 100: continue
    jobs.append((url, out))
print(len(jobs), 'downloads', flush=True)
def get(j):
    url, out = j
    for _ in range(3):
        rc = subprocess.run(['curl', '-sL', '-m', '600', '-o', out, url]).returncode
        if rc == 0 and os.path.getsize(out) > 100: return None
    return url
fails = [x for x in ThreadPoolExecutor(8).map(get, jobs) if x]
print('fails', len(fails)); print('\n'.join(fails))
