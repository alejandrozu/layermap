"""Settlement layer: GHSL GHS-SMOD 2020 (Degree of Urbanisation, 1 km) as the site's raster pyramid.

Classes drawn (everything else transparent):
  30 urban centre · 23 dense urban cluster · 22 semi-dense urban cluster · 21 suburban / peri-urban ·
  13 rural cluster · 12 low-density rural · 11 very-low-density rural where GHS-POP 2020 counts at least one person
Levels 2-6 (L6 = 113.8 px/deg, about the 1 km source), packed like the other layers.
"""
import os, sys, json, math, glob, time
import numpy as np, rasterio
from rasterio.windows import Window
from PIL import Image
from pyproj import Transformer

OUT = '/home/claude/build/urb'
SITE = '/home/claude/site/data/lay'
SMOD = '/home/claude/raw/smod/GHS_SMOD_E2020_GLOBE_R2023A_54009_1000_V2_0.tif'
POP = '/home/claude/raw/pop/GHS_POP_E2020_GLOBE_R2023A_4326_30ss_V1_0.tif'
COL = {30: (178, 24, 43), 23: (227, 74, 51), 22: (244, 132, 72), 21: (253, 196, 112),
       13: (49, 163, 84), 12: (120, 198, 121), 11: (194, 230, 153)}


def deg(k): return 576 / 2 ** k


def main():
    sys.path.insert(0, '/home/claude/scripts')
    import s2sat
    tiles6 = s2sat.plan()[0][6]
    t0 = time.time()
    sm = rasterio.open(SMOD); A = sm.read(1); T = sm.transform
    A = np.where(A < 0, 0, A).astype(np.uint8)
    pop = rasterio.open(POP); PT = pop.transform
    tr = Transformer.from_crs('EPSG:4326', 'ESRI:54009', always_xy=True)
    lut = np.zeros((256, 4), np.uint8)
    for c, rgb in COL.items(): lut[c] = (*rgb, 255)
    os.makedirs(f'{OUT}/6', exist_ok=True)
    D = deg(6); ppd = 1024 / D
    for n, (i, j) in enumerate(tiles6):
        lon0, lat0 = -180 + i * D, 90 - j * D
        w = min(1024, round((360 - i * D) * ppd)); h = min(1024, round((180 - j * D) * ppd))
        lon = lon0 + (np.arange(w) + 0.5) / ppd; lat = lat0 - (np.arange(h) + 0.5) / ppd
        LO, LA = np.meshgrid(lon, lat)
        x, y = tr.transform(LO, LA)
        c = ((x - T[2]) / T[0]).astype(np.int64); r = ((y - T[5]) / T[4]).astype(np.int64)
        ok = (c >= 0) & (c < A.shape[1]) & (r >= 0) & (r < A.shape[0]) & np.isfinite(x)
        cls = np.zeros((h, w), np.uint8); cls[ok] = A[r[ok], c[ok]]
        # people in the 30" cell under each pixel (for the very-low-density class)
        pc = ((LO - PT[2]) / PT[0]).astype(np.int64); pr = ((LA - PT[5]) / PT[4]).astype(np.int64)
        c0, c1 = max(0, pc.min()), min(pop.width - 1, pc.max()); r0, r1 = max(0, pr.min()), min(pop.height - 1, pr.max())
        if c1 >= c0 and r1 >= r0:
            P = pop.read(1, window=Window(c0, r0, c1 - c0 + 1, r1 - r0 + 1))
            pv = np.zeros((h, w)); okp = (pc >= c0) & (pc <= c1) & (pr >= r0) & (pr <= r1)
            pv[okp] = P[pr[okp] - r0, pc[okp] - c0]
        else: pv = np.zeros((h, w))
        cls[(cls == 11) & ~(pv >= 1)] = 0
        rgba = lut[cls]
        if rgba[..., 3].max() == 0: continue
        Image.fromarray(rgba, 'RGBA').save(f'{OUT}/6/{i}_{j}.webp', 'WEBP', lossless=True, method=4)
        if n % 50 == 0: print('L6', n, 'of', len(tiles6), round(time.time() - t0), 's', flush=True)
    # coarser levels: 2x2 children averaged
    for k in range(5, 1, -1):
        os.makedirs(f'{OUT}/{k}', exist_ok=True)
        Dk = deg(k); nx, ny = math.ceil(360 / Dk), math.ceil(180 / Dk)
        for j in range(ny):
            for i in range(nx):
                kids = [(2 * i + a, 2 * j + b) for b in (0, 1) for a in (0, 1)]
                if not any(os.path.exists(f'{OUT}/{k + 1}/{a}_{b}.webp') for a, b in kids): continue
                w = min(1024, round((360 - i * Dk) * 1024 / Dk)); h = min(1024, round((180 - j * Dk) * 1024 / Dk))
                mos = Image.new('RGBA', (2048, 2048), (0, 0, 0, 0))
                for (a, b) in kids:
                    p = f'{OUT}/{k + 1}/{a}_{b}.webp'
                    if os.path.exists(p): mos.paste(Image.open(p).convert('RGBA'), ((a - 2 * i) * 1024, (b - 2 * j) * 1024))
                im = mos.resize((1024, 1024), Image.BOX).crop((0, 0, w, h))
                im.save(f'{OUT}/{k}/{i}_{j}.webp', 'WEBP', quality=88, method=4, alpha_quality=90)
        print('level', k, 'done', round(time.time() - t0), 's', flush=True)
    # pack (one level per pack set, ~8 MB packs)
    os.makedirs(f'{SITE}/urb', exist_ok=True)
    for f in glob.glob(f'{SITE}/urb/*.webp'): os.remove(f)
    man = {'tile': 1024, 'levels': {}}; total = 0; files = 0
    for k in range(2, 7):
        have = sorted((tuple(map(int, os.path.basename(f)[:-5].split('_'))) for f in glob.glob(f'{OUT}/{k}/*.webp')), key=lambda t: s2sat.morton(*t))
        ent = []; n = 0; buf = bytearray()
        for i, j in have:
            b = open(f'{OUT}/{k}/{i}_{j}.webp', 'rb').read()
            if buf and len(buf) + len(b) > 8_000_000:
                open(f'{SITE}/urb/p{k}_0_{n}.webp', 'wb').write(buf); total += len(buf); files += 1; n += 1; buf = bytearray()
            ent.append([i * 1000 + j, n, len(buf), len(b)]); buf += b
        if buf: open(f'{SITE}/urb/p{k}_0_{n}.webp', 'wb').write(buf); total += len(buf); files += 1
        man['levels'][k] = {'deg': deg(k), 't': ent}
    json.dump(man, open(f'{SITE}/urb.json', 'w'), separators=(',', ':'))
    print('urban layer', files, 'packs', round(total / 1e6, 1), 'MB', round(time.time() - t0), 's')


if __name__ == '__main__':
    main()
