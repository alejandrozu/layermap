import json, os, subprocess
from concurrent.futures import ThreadPoolExecutor
d = json.load(open('/tmp/probe/gbh_all.json'))
jobs = []
for r in d:
    if int(r['admUnitCount']) > 40000 or r['boundaryType'] == 'ADM0': continue
    url = r['simplifiedGeometryGeoJSON'].replace('https://github.com/wmgeolab/geoBoundaries/raw/', 'https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/')
    out = f"/home/claude/raw/gbh/{r['boundaryISO']}_{r['boundaryType']}.geojson"
    if not os.path.exists(out): jobs.append((url, out))
def get(j):
    for _ in range(3):
        if subprocess.run(['curl', '-sL', '-m', '600', '-o', j[1], j[0]]).returncode == 0 and os.path.getsize(j[1]) > 100: return None
    return j[0]
print('fails', [x for x in ThreadPoolExecutor(8).map(get, jobs) if x])
