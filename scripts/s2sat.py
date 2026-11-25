"""Satellite layer from EOX Sentinel-2 cloudless 2024 (WGS84 WMTS), as the site's plate carree pyramid.

Level k tile = 1024 px square of D_k = 576 / 2**k degrees (origin -180, 90), ppd = 1.7778 * 2**k.
Source zoom z = k + 1 (ppd 1.4222 * 2**z = 1.6x finer), downsampled with Lanczos.

  levels 2-4  whole world, opaque
  levels 5-6  tiles with land, opaque
  level 7     land between 60S and 84N                         (~490 m)   } transparent outside the cells
  level 8     0.25 deg cells with >= 1,000 people              (~245 m)   } they cover, so the coarser
  level 9     cells with >= 200,000 people, plus a ring        (~120 m)   } level shows through
  level 10    cells with >= 1,000,000 people, plus a ring      (~60 m)    }

usage: python3 s2sat.py plan|download|build|pack|all
"""
import os, sys, io, json, math, time, glob, concurrent.futures as cf
import numpy as np, requests
from PIL import Image
from scipy import ndimage

RAW = '/home/claude/raw/s2'
OUT = '/home/claude/build/s2sat'
SITE = '/home/claude/site/data/lay'
SRC = 'https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2024/default/WGS84'
OPAQUE = range(2, 7)
ALPHA = range(7, 11)
Q = {2: 70, 3: 70, 4: 68, 5: 66, 6: 64, 7: 62, 8: 60, 9: 58, 10: 56}


def deg(k): return 576 / 2 ** k
def ppd(k): return 1024 / deg(k)
def sppd(z): return 256 * 2 ** (z + 1) / 360


def masks():
    m = np.load('/home/claude/raw/imagery/landmask_raw.npy'); pop = np.load('/home/claude/raw/imagery/pop025.npy')
    lat = 90 - (np.arange(720) + 0.5) * 0.25
    band = ((lat > -60) & (lat < 84))[:, None] & np.ones((1, 1440), bool)
    st = np.ones((3, 3), bool)
    return {
        7: band & m,
        8: band & m & (pop >= 1e3),
        9: ndimage.binary_dilation(pop >= 2e5, st),
        10: ndimage.binary_dilation(pop >= 1e6, st),
    }, m


def plan():
    M, land = masks(); out = {}
    for k in list(OPAQUE) + list(ALPHA):
        D = deg(k); nx, ny = math.ceil(360 / D), math.ceil(180 / D); lst = []
        for j in range(ny):
            for i in range(nx):
                c0, c1 = int(i * D * 4), min(1440, int(math.ceil((i + 1) * D * 4)))
                r0, r1 = int(j * D * 4), min(720, int(math.ceil((j + 1) * D * 4)))
                if k <= 4: lst.append((i, j)); continue
                if k <= 6:
                    if land[r0:r1, c0:c1].sum() >= 16: lst.append((i, j))
                    continue
                if M[k][r0:r1, c0:c1].any(): lst.append((i, j))
        out[k] = lst
    return out, M


def src_tiles(k, i, j, M):
    """EOX tiles (z, row, col) needed for my tile (k, i, j): all of them for opaque levels, else only under the mask"""
    z = k + 1; P = sppd(z); D = deg(k)
    lon0, lat0 = -180 + i * D, 90 - j * D
    x0, x1 = (lon0 + 180) * P, min(360, lon0 + D + 180) * P
    y0, y1 = (90 - lat0) * P, min(180, 90 - lat0 + D) * P
    cols = range(int(x0 // 256), int(math.ceil(x1 / 256))); rows = range(int(y0 // 256), int(math.ceil(y1 / 256)))
    nC, nR = 2 ** (z + 1), 2 ** z
    out = []
    for r in rows:
        if r >= nR: continue
        for c in cols:
            if c >= nC: continue
            if k in ALPHA:
                # cells under this source tile
                la0 = 90 - r * 256 / P; la1 = 90 - (r + 1) * 256 / P; lo0 = -180 + c * 256 / P; lo1 = -180 + (c + 1) * 256 / P
                cr0, cr1 = int((90 - la0) * 4), int(math.ceil((90 - la1) * 4)); cc0, cc1 = int((lo0 + 180) * 4), int(math.ceil((lo1 + 180) * 4))
                if not M[k][max(0, cr0):min(720, cr1), max(0, cc0):min(1440, cc1)].any(): continue
            out.append((z, r, c))
    return out


def download():
    tiles, M = plan(); need = set()
    for k, lst in tiles.items():
        for i, j in lst: need.update(src_tiles(k, i, j, M))
    need = sorted(t for t in need if not os.path.exists(f'{RAW}/{t[0]}/{t[1]}_{t[2]}.jpg'))
    print('to download', len(need), flush=True)
    s = requests.Session(); s.mount('https://', requests.adapters.HTTPAdapter(pool_connections=32, pool_maxsize=32))
    for z in {t[0] for t in need}: os.makedirs(f'{RAW}/{z}', exist_ok=True)
    def get(t):
        z, r, c = t
        for a in range(5):
            try:
                x = s.get(f'{SRC}/{z}/{r}/{c}.jpg', timeout=60)
                if x.status_code == 200:
                    open(f'{RAW}/{z}/{r}_{c}.jpg', 'wb').write(x.content); return 1
                if x.status_code == 404: return 0
            except Exception: pass
            time.sleep(1 + a * 2)
        return -1
    t0 = time.time(); done = bad = 0
    with cf.ThreadPoolExecutor(24) as ex:
        for res in ex.map(get, need):
            done += 1; bad += res < 0
            if done % 5000 == 0: print(done, 'of', len(need), round(time.time() - t0), 's', 'failed', bad, flush=True)
    print('download done', done, 'failed', bad, round(time.time() - t0), 's')


def build_one(args):
    k, i, j = args
    fp = f'{OUT}/{k}/{i}_{j}.webp'
    if os.path.exists(fp): return os.path.getsize(fp)
    M = MASKS
    z = k + 1; P = sppd(z); D = deg(k); S = P / ppd(k)  # source px per output px (1.6)
    lon0, lat0 = -180 + i * D, 90 - j * D
    w = min(1024, round((360 - i * D) * ppd(k))); h = min(1024, round((180 - j * D) * ppd(k)))
    x0, y0 = (lon0 + 180) * P, (90 - lat0) * P
    x1, y1 = x0 + w * S, y0 + h * S
    c0, r0 = int(x0 // 256), int(y0 // 256); c1, r1 = int(math.ceil(x1 / 256)), int(math.ceil(y1 / 256))
    mos = Image.new('RGB', ((c1 - c0) * 256, (r1 - r0) * 256), (0, 0, 0))
    have = False
    for (zz, r, c) in src_tiles(k, i, j, M):
        p = f'{RAW}/{zz}/{r}_{c}.jpg'
        if not os.path.exists(p): continue
        try: mos.paste(Image.open(p).convert('RGB'), ((c - c0) * 256, (r - r0) * 256)); have = True
        except Exception: pass
    if not have: return 0
    im = mos.resize((w, h), Image.LANCZOS, box=(x0 - c0 * 256, y0 - r0 * 256, x1 - c0 * 256, y1 - r0 * 256))
    if k in ALPHA:
        # the cells this level covers, with soft edges
        cm = M[k].astype(np.float32)
        cx0, cy0 = (lon0 + 180) * 4, (90 - lat0) * 4
        a = Image.fromarray((cm * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR,
                                                               box=(cx0, cy0, cx0 + w / ppd(k) * 4, cy0 + h / ppd(k) * 4))
        a = np.array(a).astype(np.float32)
        a = np.clip((a - 64) * 255 / 128, 0, 255).astype(np.uint8)
        if a.max() == 0: return 0
        im = im.convert('RGBA'); im.putalpha(Image.fromarray(a))
    os.makedirs(f'{OUT}/{k}', exist_ok=True)
    im.save(fp, 'WEBP', quality=Q[k], method=4, alpha_quality=40)
    return os.path.getsize(fp)


MASKS = None
def init():
    global MASKS
    MASKS = masks()[0]


def build(only=None):
    tiles, M = plan()
    jobs = [(k, i, j) for k, lst in tiles.items() if not only or k in only for i, j in lst]
    print('tiles to build', len(jobs), flush=True)
    t0 = time.time(); tot = 0; n = 0
    with cf.ProcessPoolExecutor(2, initializer=init) as ex:
        for b in ex.map(build_one, jobs, chunksize=4):
            tot += b; n += 1
            if n % 500 == 0: print(n, 'of', len(jobs), round(tot / 1e6), 'MB', round(time.time() - t0), 's', flush=True)
    print('build done', round(tot / 1e6), 'MB', round(time.time() - t0), 's')


def morton(i, j):
    r = 0
    for b in range(12): r |= ((i >> b) & 1) << (2 * b) | ((j >> b) & 1) << (2 * b + 1)
    return r


FILE_CAP, ASSET_CAP = 1_500_000, 4_000_000
ASSET_DIR = '/home/claude/build/s2assets'


def pack():
    """Tiles concatenated into packs, in Z-order so a pack holds one area; the manifest gives each tile's pack,
    offset and length. Levels 2-6 are site files (data/lay/sat2/p{k}_0_{n}.webp, ~1.5 MB); levels 7-10 are too big
    for the site's own files and go up as artifact assets (~4 MB each) whose urls fill the level's 'u' list
    (assets.json maps pack name -> url once they are uploaded)."""
    tiles, M = plan()
    os.makedirs(f'{SITE}/sat2', exist_ok=True); os.makedirs(ASSET_DIR, exist_ok=True)
    for f in glob.glob(f'{SITE}/sat2/*.webp') + glob.glob(f'{ASSET_DIR}/*.webp'): os.remove(f)
    urls = json.load(open(f'{ASSET_DIR}/../s2assets.json')) if os.path.exists(f'{ASSET_DIR}/../s2assets.json') else {}
    full = json.load(open('/home/claude/build/s2full.json'))  # s2full.py: 4x4 grid of fully opaque blocks per partial tile
    man = {'tile': 1024, 'levels': {}}; stats = {'file': [0, 0], 'asset': [0, 0]}; missing = 0
    for k, lst in tiles.items():
        asset = k >= 7; cap = ASSET_CAP if asset else FILE_CAP
        have = [(i, j) for i, j in lst if os.path.exists(f'{OUT}/{k}/{i}_{j}.webp') and os.path.getsize(f'{OUT}/{k}/{i}_{j}.webp') > 0]
        have.sort(key=lambda t: morton(*t))
        ent = []; names = []; buf = bytearray()
        def flush():
            nonlocal buf
            if not buf: return
            n = len(names); nm = f'p{k}_0_{n}.webp' if not asset else f's2_{k}_{n}.webp'
            open((f'{ASSET_DIR}/' if asset else f'{SITE}/sat2/') + nm, 'wb').write(buf)
            st = stats['asset' if asset else 'file']; st[0] += 1; st[1] += len(buf)
            names.append(nm); buf = bytearray()
        for i, j in have:
            b = open(f'{OUT}/{k}/{i}_{j}.webp', 'rb').read()
            if buf and len(buf) + len(b) > cap: flush()
            ent.append([i * 1000 + j, len(names), len(buf), len(b)] + ([full[f'{k}/{i}_{j}.webp']] if k in ALPHA else [])); buf += b
        flush()
        L = {'deg': deg(k), 't': ent, **({'a': 1} if k in ALPHA else {})}
        if asset:
            L['u'] = [urls.get(nm) for nm in names]; missing += sum(u is None for u in L['u'])
        man['levels'][k] = L
        print('level', k, len(ent), 'tiles', len(names), 'packs', round(sum(e[3] for e in ent) / 1e6, 1), 'MB', flush=True)
    json.dump(man, open(f'{SITE}/sat2.json', 'w'), separators=(',', ':'))
    print('files', stats['file'][0], round(stats['file'][1] / 2**20, 1), 'MiB; assets', stats['asset'][0], round(stats['asset'][1] / 2**20, 1), 'MiB; urls missing', missing)


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'plan'
    if what == 'plan':
        tiles, M = plan(); tot = 0
        for k, lst in tiles.items():
            n = len({t for i, j in lst for t in src_tiles(k, i, j, M)}); tot += n
            print(k, len(lst), 'tiles', n, 'source tiles', flush=True)
        print('source tiles', tot)
    if what in ('download', 'all'): download()
    if what in ('build', 'all'): build([int(x) for x in sys.argv[2:]] or None)
    if what in ('pack', 'all'): pack()
