"""List the biggest jumps between consecutive levels (average children per parent and worst single parent)."""
import json, glob, os, collections, sys
B = '/home/claude/build'
world = json.load(open(B + '/world.json'))
R = dict(map(tuple, json.load(open(B + '/regions.json'))))
cname = {g['properties']['id']: g['properties']['n'] for g in world['objects']['countries']['geometries']}
creg = collections.Counter(g['properties']['r'] for g in world['objects']['countries']['geometries'])
rows = []
# earth -> regions, regions -> countries
rows.append(dict(where='Earth', frm='Earth', to='Regional unions', n0=1, n1=len(R), avg=len(R), mx=len(R), worst='Earth'))
rows.append(dict(where='All regions', frm='Regional unions', to='Countries', n0=len(R), n1=sum(creg.values()),
                 avg=sum(creg.values()) / len(R), mx=max(creg.values()), worst=R[creg.most_common(1)[0][0]]))
for d in sorted(glob.glob(B + '/chunks/*/entry.json')):
    cid = os.path.basename(os.path.dirname(d)); e = json.load(open(d))
    labels = [l[1] for l in e['L']]
    names = {}; kids = collections.defaultdict(list)
    for f in e['F']:
        t = json.load(open(os.path.join(os.path.dirname(d), f[0])))
        for L, o in t['objects'].items():
            L = int(L)
            for g in o['geometries']:
                pr = g['properties']; names[(L, pr['i'])] = pr['n']
                kids[(L - 1, pr.get('p'))].append(pr['i'])
    counts = [len({k for k in names if k[0] == L}) for L in range(1, len(labels) + 1)]
    prev_label, prev_n = 'Country', 1
    for L in range(1, len(labels) + 1):
        if L == 1:
            mx, worst = counts[0], cname.get(cid, cid)
        else:
            per = [(len(v), k) for k, v in kids.items() if k[0] == L - 1]
            mx, wk = max(per)
            worst = names.get((L - 1, int(wk[1]) if wk[1] not in (None, '') else None), '?')
        rows.append(dict(where=cname.get(cid, cid), frm=prev_label, to=labels[L - 1], n0=prev_n, n1=counts[L - 1],
                         avg=counts[L - 1] / prev_n, mx=mx, worst=worst))
        prev_label, prev_n = labels[L - 1], counts[L - 1]
json.dump(rows, open(B + '/jumps.json', 'w'), ensure_ascii=False, indent=0)
rows.sort(key=lambda r: -r['avg'])
for r in rows[:int(sys.argv[1]) if len(sys.argv) > 1 else 40]:
    print(f"{r['avg']:7.1f}x  max {r['mx']:5d}  {r['where']}: {r['frm']} ({r['n0']}) → {r['to']} ({r['n1']})  [worst: {r['worst']}]")
