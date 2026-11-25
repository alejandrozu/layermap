"""Build self-hosted raster layers (plate carree pyramids) from NASA GIBS EPSG:4326 tiles.

My tile (level k, col i, row j) = 1024 px square covering D_k = 576 / 2**k degrees,
origin at (-180, 90).  It is exactly 2x2 GIBS tiles of the same level, so
pixels per degree = 1024 / D_k = 1.7778 * 2**k (k=6 -> 113.8 px/deg, ~1 km).
Tiles are cropped at the world edge (lon 180, lat -90).

usage: python3 imagery.py <layer> [download|build|all]
"""
import os, sys, io, json, math, concurrent.futures as cf
import numpy as np, requests
from PIL import Image, ImageDraw, ImageFilter
import geopandas as gpd

RAW = '/home/claude/raw/imagery'
OUT = '/home/claude/site/data/lay'
GIBS = 'https://gibs.earthdata.nasa.gov/wmts/epsg4326/best'
LAYERS = {
    # satellite: Blue Marble with bathymetry; whole world down to L4, land only above
    'sat': dict(gibs='BlueMarble_ShadedRelief_Bathymetry/default/2004-08-01/500m', levels=range(2, 7), full_upto=4, q=70),
    # elevation: ASTER GDEM colour shaded relief; only land matters (layer is clipped to land)
    'elev': dict(gibs='ASTER_GDEM_Color_Shaded_Relief/default/default/31.25m', levels=range(2, 7), full_upto=2, q=72),
}
GW = {k: (2, 3, 5, 10, 20, 40, 80)[k] for k in range(7)}
GH = {k: (1, 2, 3, 5, 10, 20, 40)[k] for k in range(7)}


def deg(k): return 576 / 2 ** k


def land_mask():
    p = RAW + '/landmask_raw.npy'  # 0.25 deg land raster (no margin)
    if os.path.exists(p): return np.load(p)
    g = gpd.read_file('/home/claude/raw/ne/ne_10m_admin_0_countries.zip')
    W, H = 1440, 720  # 0.25 deg
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    for geom in g.geometry:
        for poly in getattr(geom, 'geoms', [geom]):
            pts = [((x + 180) * 4, (90 - y) * 4) for x, y in poly.exterior.coords]
            d.polygon(pts, fill=255)
    m = np.array(im) > 0
    np.save(p, m); return m


def my_tiles(name):
    cfg = LAYERS[name]; m = land_mask(); out = {}
    for k in cfg['levels']:
        D = deg(k); nx, ny = math.ceil(360 / D), math.ceil(180 / D); lst = []
        for j in range(ny):
            for i in range(nx):
                if k > cfg['full_upto']:
                    x0, y0 = int(i * D * 4), int(j * D * 4)
                    # needs at least ~1 square degree of land; smaller islands use the level below
                    if m[y0:min(720, int((j + 1) * D * 4)), x0:min(1440, int((i + 1) * D * 4))].sum() < 16: continue
                lst.append((i, j))
        out[k] = lst
    return out


def gibs_needed(tiles):
    need = set()
    for k, lst in tiles.items():
        for i, j in lst:
            for dj in (0, 1):
                for di in (0, 1):
                    r, c = 2 * j + dj, 2 * i + di
                    if r < GH[k] and c < GW[k]: need.add((k, r, c))
    return sorted(need)


def download(name):
    cfg = LAYERS[name]; need = gibs_needed(my_tiles(name))
    s = requests.Session()
    def get(t):
        k, r, c = t; p = f'{RAW}/{name}/{k}/{r}_{c}.jpg'
        if os.path.exists(p) and os.path.getsize(p) > 0: return 0
        os.makedirs(os.path.dirname(p), exist_ok=True)
        for attempt in range(4):
            try:
                resp = s.get(f'{GIBS}/{cfg["gibs"]}/{k}/{r}/{c}.jpeg', timeout=60)
                if resp.status_code == 200:
                    open(p, 'wb').write(resp.content); return len(resp.content)
            except Exception as e:
                pass
        print('FAILED', t, flush=True); return 0
    tot = 0; n = 0
    with cf.ThreadPoolExecutor(16) as ex:
        for b in ex.map(get, need):
            tot += b; n += 1
            if n % 200 == 0: print(name, n, '/', len(need), round(tot / 1e6, 1), 'MB', flush=True)
    print(name, 'downloaded', len(need), 'tiles', round(tot / 1e6, 1), 'MB new')


def polar_patch(im, k, i, j, D, ppd):
    """ASTER GDEM is broken over Antarctica and missing beyond 83N: use Blue Marble ice there."""
    lat_top = 90 - j * D; lat_bot = lat_top - D
    if lat_bot > -58 and lat_top < 82: return im
    sat = Image.new('RGB', (1024, 1024))
    for dj in (0, 1):
        for di in (0, 1):
            r, c = 2 * j + dj, 2 * i + di
            p = f'{RAW}/sat/{k}/{r}_{c}.jpg'
            if r < GH[k] and c < GW[k]:
                if not os.path.exists(p):
                    resp = requests.get(f'{GIBS}/{LAYERS["sat"]["gibs"]}/{k}/{r}/{c}.jpeg', timeout=60)
                    os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'wb').write(resp.content)
                sat.paste(Image.open(p).convert('RGB'), (512 * di, 512 * dj))
    lat = lat_top - (np.arange(1024) + 0.5) / ppd
    # weight of Blue Marble: 1 south of -61 and north of 83, ramps over 3 degrees
    w = np.clip((-58 - lat) / 3, 0, 1) + np.clip((lat - 82) / 1, 0, 1)
    a = np.array(im, dtype=np.float32); b = np.array(sat, dtype=np.float32)
    # tint the ice slightly so it reads as terrain, not as satellite
    b = b * np.array([0.93, 0.95, 0.98], dtype=np.float32)
    w = np.clip(w, 0, 1)[:, None, None]
    return Image.fromarray((a * (1 - w) + b * w).astype(np.uint8))


# the places on Earth with land below sea level (lon0, lon1, lat0, lat1)
DEPRESSIONS = [(2.4, 7.6, 50.9, 53.8), (-0.6, 0.6, 52.2, 52.9), (7.8, 9.2, 53.3, 54.6), (10.5, 12.8, 54.6, 56.2), (11.9, 12.8, 44.6, 45.5),
               (43.5, 56.5, 36, 48.8), (55.5, 59.5, 39.5, 42.5), (34.8, 36.2, 29.4, 33.5), (24.5, 30.5, 28.4, 31.2), (4.5, 10.5, 32.8, 35),
               (39.3, 43.2, 10.5, 15.2), (87.8, 91.2, 42, 43.6), (-117.8, -114.6, 32, 36.8), (135.5, 139.8, -30.5, -27.3), (68, 72, 37, 41),
               (-64.5, -63, -44, -42), (27.5, 31.5, 31, 31.7), (47, 50, 33, 37)]


def below_sea_fix(im, lon0=None, lat0=None, ppd=None):
    """ASTER paints land below sea level (Netherlands, Caspian, Dead Sea...) flat neutral grey: make it lowland green."""
    if lon0 is not None:
        lon1, lat1 = lon0 + im.width / ppd, lat0 - im.height / ppd
        boxes = [b for b in DEPRESSIONS if b[0] < lon1 and b[1] > lon0 and b[2] < lat0 and b[3] > lat1]
        if not boxes: return im
    a = np.array(im, dtype=np.int16)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    mean = (R + G + B) / 3
    m = (abs(R - G) <= 6) & (abs(G - B) <= 7) & (abs(R - B) <= 9) & (mean >= 70) & (mean <= 150)
    if m.mean() < 0.002: return im
    # only solid grey patches (mountain tops mix grey with purple and white)
    from PIL import ImageFilter
    dens = np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(5))) / 255.0
    m &= dens >= 0.7
    # ... and flat ones: high plateaus (Tibet, Altiplano) are grey too, but textured by the relief shading
    gx = np.abs(np.diff(mean, axis=1, append=mean[:, -1:])); gy = np.abs(np.diff(mean, axis=0, append=mean[-1:, :]))
    g = np.clip(gx + gy, 0, 255).astype(np.uint8)
    tex = np.array(Image.fromarray(g).filter(ImageFilter.BoxBlur(6))).astype(np.float32)
    m &= tex <= 5
    if lon0 is not None:
        lons = lon0 + (np.arange(im.width) + 0.5) / ppd; lats = lat0 - (np.arange(im.height) + 0.5) / ppd
        inb = np.zeros(m.shape, bool)
        for x0, x1, y0, y1 in boxes: inb |= ((lats >= y0) & (lats <= y1))[:, None] & ((lons >= x0) & (lons <= x1))[None, :]
        m &= inb
    if not m.any(): return im
    # grow the solid cores into the ragged grey edges around them
    loose = (abs(R - G) <= 11) & (abs(G - B) <= 11) & (abs(R - B) <= 13) & (mean >= 55) & (mean <= 165)
    for _ in range(5):  # geodesic growth: only through grey pixels
        m = loose & (np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(11))) > 0)
    if lon0 is not None: m &= inb
    lum = mean[m] / 124.0
    a[m] = np.clip(np.stack([74 * lum, 92 * lum, 58 * lum], 1), 0, 255).astype(np.int16)
    return Image.fromarray(a.astype(np.uint8))


def build(name):
    cfg = LAYERS[name]; tiles = my_tiles(name); man = {'levels': {}, 'tile': 1024}
    total = 0
    for k, lst in tiles.items():
        D = deg(k); ppd = 1024 / D; od = f'{OUT}/{name}/{k}'; os.makedirs(od, exist_ok=True)
        for i, j in lst:
            im = Image.new('RGB', (1024, 1024))
            for dj in (0, 1):
                for di in (0, 1):
                    r, c = 2 * j + dj, 2 * i + di
                    p = f'{RAW}/{name}/{k}/{r}_{c}.jpg'
                    if r < GH[k] and c < GW[k] and os.path.exists(p):
                        im.paste(Image.open(p).convert('RGB'), (512 * di, 512 * dj))
            if name == 'elev': im = below_sea_fix(polar_patch(im, k, i, j, D, ppd), -180 + i * D, 90 - j * D, ppd)
            w = min(1024, round((360 - i * D) * ppd)); h = min(1024, round((180 - j * D) * ppd))
            if (w, h) != (1024, 1024): im = im.crop((0, 0, w, h))
            fp = f'{od}/{i}_{j}.webp'
            im.save(fp, 'WEBP', quality=cfg['q'], method=4)
            total += os.path.getsize(fp)
        man['levels'][k] = {'deg': D, 't': [i * 1000 + j for i, j in lst]}
        print(name, 'level', k, len(lst), 'tiles', round(total / 1e6, 1), 'MB so far', flush=True)
    json.dump(man, open(f'{OUT}/{name}.json', 'w'), separators=(',', ':'))
    print(name, 'TOTAL', round(total / 1e6, 1), 'MB')


def pack(name):
    """Concatenate tiles into a few pack files (the host allows ~500 files per artifact).
    Each pack is plain concatenated WebP files (the first is a valid WebP); offsets live in the manifest."""
    man = json.load(open(f'{OUT}/{name}.json')); out = {'tile': man['tile'], 'levels': {}}
    total = 0; files = []
    for k, lv in man['levels'].items():
        k = int(k); sh = 4 if k <= 3 else 2
        packs = {}
        for code in lv['t']:
            i, j = code // 1000, code % 1000
            packs.setdefault((i >> sh, j >> sh), []).append(code)
        ent = []
        for (pi, pj), codes in sorted(packs.items()):
            fn = f'p{k}_{pi}_{pj}.webp'; off = 0; buf = bytearray()
            for code in codes:
                b = open(f'{OUT}/{name}/{k}/{code // 1000}_{code % 1000}.webp', 'rb').read()
                ent.append([code, pi * 1000 + pj, off, len(b)]); buf += b; off += len(b)
            open(f'{OUT}/{name}/{fn}', 'wb').write(buf); total += len(buf); files.append(fn)
        out['levels'][k] = {'deg': lv['deg'], 'sh': sh, 't': ent}
    json.dump(out, open(f'{OUT}/{name}.json', 'w'), separators=(',', ':'))
    print(name, len(files), 'packs', round(total / 1e6, 1), 'MB', 'largest', max(os.path.getsize(f'{OUT}/{name}/{f}') for f in files) // 1000, 'KB')


if __name__ == '__main__':
    name = sys.argv[1]; what = sys.argv[2] if len(sys.argv) > 2 else 'all'
    if what == 'count':
        t = my_tiles(name); print({k: len(v) for k, v in t.items()}, 'gibs', len(gibs_needed(t)))
    if what in ('download', 'all'): download(name)
    if what in ('build', 'all'): build(name)
    if what in ('pack', 'all'): pack(name)

