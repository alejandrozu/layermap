"""For each tile of the partial satellite levels: a 16-bit mask of which cells of a 4x4 grid are fully opaque
(alpha 255 and real imagery everywhere), so the client knows where a coarser level must show through."""
import os, glob, json, numpy as np
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
OUT = '/home/claude/build/s2sat'; F = '/home/claude/build/s2full.json'
def one(f):
    a = np.array(Image.open(f).convert('RGBA')); h, w = a.shape[:2]
    ok = (a[..., 3] >= 235) & (a[..., :3].astype(np.int32).sum(-1) >= 12)
    m = 0
    for by in range(4):
        for bx in range(4):
            y0, y1 = by * 256, min(h, (by + 1) * 256); x0, x1 = bx * 256, min(w, (bx + 1) * 256)
            if y0 >= h or x0 >= w or ok[y0:y1, x0:x1].mean() >= 0.985: m |= 1 << (by * 4 + bx)
    return f, m
if __name__ == '__main__':
    res = json.load(open(F)) if os.path.exists(F) else {}
    fs = [f for k in (7, 8, 9, 10) for f in glob.glob(f'{OUT}/{k}/*.webp')]
    todo = [f for f in fs if f[len(OUT) + 1:] not in res]
    with ProcessPoolExecutor(2) as ex:
        for n, (f, m) in enumerate(ex.map(one, todo, chunksize=16)):
            res[f[len(OUT) + 1:]] = m
            if n % 2000 == 0: print(n, len(todo), flush=True)
    json.dump(res, open(F, 'w'))
    v = list(res.values()); print('tiles', len(v), 'all full', sum(x == 65535 for x in v), 'none full', sum(x == 0 for x in v))
