"""Write one country's built chunks into site/data (gzip+base64) and update its index.json entry.
Split levels (F entries with a part table) are written one file per part."""
import json, os, gzip, base64, sys, glob
B = '/home/claude/build'; S = '/home/claude/site/data'
def gz(src, dst):
    raw = json.dumps(json.load(open(src)), separators=(',', ':'), ensure_ascii=False).encode()
    with open(dst, 'wb') as fh: fh.write(base64.b64encode(gzip.compress(raw, 9, mtime=0)))
    return os.path.getsize(dst)
for cid in sys.argv[1:]:
    e = json.load(open(f'{B}/chunks/{cid}/entry.json'))
    for old in glob.glob(f'{S}/c/{cid}.*.gz.txt'): os.remove(old)
    F = []
    for f in e['F']:
        if len(f) > 5 and f[5]:
            sizes = {}
            for k in f[5]['p']:
                sizes[k] = gz(f'{B}/chunks/{cid}/' + f[0].replace('{p}', k), f'{S}/c/' + f[0].replace('{p}', k).replace('.json', '.gz.txt'))
            F.append(['c/' + f[0].replace('.json', '.gz.txt'), f[1], f[2], sum(sizes.values()), None, {'by': f[5]['by'], 'p': sizes}])
        else:
            F.append(['c/' + f[0].replace('.json', '.gz.txt'), f[1], f[2], gz(f'{B}/chunks/{cid}/{f[0]}', f'{S}/c/' + f[0].replace('.json', '.gz.txt'))])
    idx = json.load(open(S + '/index.json'))
    idx['c'][cid] = {'L': e['L'], 'F': F, 'N': e['N']}
    json.dump(idx, open(S + '/index.json', 'w'), separators=(',', ':'), ensure_ascii=False)
    print(cid, json.dumps(F)[:900])
