"""record uploaded asset ids: args are sha256-prefix:opaque_id pairs; matched to the local pack files by content hash"""
import sys, os, json, hashlib
D = '/home/claude/build/s2assets'; M = '/home/claude/build/s2assets.json'
m = json.load(open(M)) if os.path.exists(M) else {}
cache = '/home/claude/build/s2sha.json'
sh = json.load(open(cache)) if os.path.exists(cache) else {}
for n in os.listdir(D):
    st = os.stat(f'{D}/{n}'); key = f'{n}:{st.st_size}:{int(st.st_mtime)}'
    if key not in sh: sh[key] = hashlib.sha256(open(f'{D}/{n}', 'rb').read()).hexdigest()
json.dump(sh, open(cache, 'w'))
by = {v: k.split(':')[0] for k, v in sh.items()}
for a in sys.argv[1:]:
    p, i = a.split(':'); hit = [n for h, n in by.items() if h.startswith(p)]
    assert len(hit) == 1, (a, hit); m[hit[0]] = '/_blob/' + i
json.dump(m, open(M, 'w'), indent=0)
print(len(m), 'recorded')
