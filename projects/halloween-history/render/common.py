"""Shared drawing kit for 《万圣节的历史演变》 stills.
Pure functions of (shot params, seed). No clocks. Same input -> identical pixels.
"""
import json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(ROOT)
REPO = os.path.dirname(os.path.dirname(PROJ))
STYLE = json.load(open(os.path.join(REPO, 'styles/halloween-history-map/style_bible.json'), encoding='utf-8'))
P = {k: v['hex'] for k, v in STYLE['palette'].items()}
W, H = STYLE['canvas']['width'], STYLE['canvas']['height']
S = STYLE['canvas']['supersample']


def rgb(h, a=None):
    h = h.lstrip('#')
    c = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return c if a is None else c + (int(a * 255),)


# ---------------- fonts ----------------
_fc = {}
def font(kind, size):
    key = (kind, size)
    if key not in _fc:
        f = STYLE['fonts'][kind]
        _fc[key] = ImageFont.truetype(f['file'], size * S, index=f.get('index', 0))
    return _fc[key]


# ---------------- canvas ----------------
class Frame:
    def __init__(self, seed):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.base = Image.new('RGB', (W * S, H * S), rgb(P['night_ink']))
        self.d = ImageDraw.Draw(self.base, 'RGBA')
        self.light = Image.new('RGB', (W * S, H * S), (0, 0, 0))   # additive light layer (glow)
        self.ld = ImageDraw.Draw(self.light)
        self.top = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0))   # text layer (never glows)
        self.td = ImageDraw.Draw(self.top)
        self._background()

    def _background(self):
        # radial lift, ΔL small; not a hue gradient
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.45) / (H * 0.6)) ** 2)
        k = np.clip(1 - r, 0, 1) ** 1.6
        a = np.array(rgb(P['night_ink']), np.float32); b = np.array(rgb(P['night_lift']), np.float32)
        img = a[None, None] * (1 - k[..., None]) + b[None, None] * k[..., None]
        self.base = Image.fromarray(img.astype(np.uint8)).resize((W * S, H * S), Image.BILINEAR)
        self.d = ImageDraw.Draw(self.base, 'RGBA')

    # coordinates are given at 1x; scaled here
    def circle(self, x, y, r, fill, light=False):
        dr = self.ld if light else self.d
        dr.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=fill)

    def glow(self, x, y, r_core, color, blur, strength=1.0):
        """Point light: core into light layer + blurred halo. Only for real light sources."""
        lay = Image.new('RGB', (W * S, H * S), (0, 0, 0))
        g = ImageDraw.Draw(lay)
        c = tuple(int(v * strength) for v in rgb(color))
        g.ellipse([(x - r_core) * S, (y - r_core) * S, (x + r_core) * S, (y + r_core) * S], fill=c)
        lay = lay.filter(ImageFilter.GaussianBlur(blur * S))
        self.light = Image.fromarray(np.minimum(np.asarray(self.light, np.uint16) + np.asarray(lay, np.uint16), 255).astype(np.uint8))
        self.ld = ImageDraw.Draw(self.light)

    def add_light_image(self, lay, blur=0):
        if blur:
            lay = lay.filter(ImageFilter.GaussianBlur(blur * S))
        self.light = Image.fromarray(np.minimum(np.asarray(self.light, np.uint16) + np.asarray(lay, np.uint16), 255).astype(np.uint8))
        self.ld = ImageDraw.Draw(self.light)

    def scrim(self, y0, y1, a=0.6, feather=120):
        """Soft ink band behind text so map detail never fights reading (not a hue gradient)."""
        m = np.zeros((H, 1), np.float32)
        yy = np.arange(H)[:, None]
        m = np.clip(np.minimum((yy - (y0 - feather)) / feather, ((y1 + feather) - yy) / feather), 0, 1) * a
        ink = np.array(rgb(P['night_ink']), np.float32)
        arr = np.asarray(self.base, np.float32)
        mm = np.repeat(np.repeat(m, S, 0), 1, 1)[:, :, None]
        arr = arr * (1 - mm) + ink[None, None] * mm
        self.base = Image.fromarray(arr.astype(np.uint8)); self.d = ImageDraw.Draw(self.base, 'RGBA')
        # also dim light layer under text
        la = np.asarray(self.light, np.float32) * (1 - mm)
        self.light = Image.fromarray(la.astype(np.uint8)); self.ld = ImageDraw.Draw(self.light)

    def text(self, xy, s, kind, size, color, anchor='la', spacing=None, a=1.0):
        x, y = xy
        sp = int(size * (STYLE['fonts']['line_height'] - 1) * S) if spacing is None else spacing * S
        self.td.multiline_text((x * S, y * S), s, font=font(kind, size), fill=rgb(color, a), anchor=anchor,
                               spacing=sp, align={'la': 'left', 'ma': 'center', 'ra': 'right', 'mm': 'center'}.get(anchor, 'left'))

    def text_w(self, s, kind, size):
        return self.td.textlength(s, font=font(kind, size)) / S

    def finish(self, path, frame_tag=None):
        base = np.asarray(self.base, np.float32)
        light = np.asarray(self.light, np.float32)
        out = np.clip(base + light * STYLE['glow']['intensity_max'] * 1.15, 0, 255).astype(np.uint8)
        img = Image.fromarray(out).convert('RGBA')
        img.alpha_composite(self.top)
        img = img.convert('RGB').resize((W, H), Image.LANCZOS)
        arr = np.asarray(img, np.float32)
        # vignette
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / math.sqrt(2)
        vg = STYLE['vignette']
        v = 1 - vg['strength'] * np.clip((r - (1 - vg['radius'])) / vg['radius'], 0, 1) ** 2
        arr *= v[..., None]
        # paper grain (luminance), seeded
        gr = STYLE['grain']
        g = np.random.default_rng(gr['seed'] + self.seed).normal(0, 1, (H, W)).astype(np.float32)
        gimg = Image.fromarray(((g * 40) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(gr['blur_sigma_px']))
        g = (np.asarray(gimg, np.float32) - 128) / 40
        arr *= (1 + gr['amplitude'] * g)[..., None]
        # fibres: sparse long faint strokes, seeded
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        if frame_tag:
            ImageDraw.Draw(img).text((W - 20, H - 20), frame_tag, font=ImageFont.truetype(STYLE['fonts']['caption']['file'], 22, index=2), fill=(90, 105, 125), anchor='rd')
        img.save(path, optimize=True)
        return img


# ---------------- geography ----------------
_mask = None
MW, MH = 7200, 3600
def land_mask():
    global _mask
    if _mask is None:
        cache = os.path.join(PROJ, 'data', 'land_mask_7200.png')
        if os.path.exists(cache):
            _mask = np.asarray(Image.open(cache)) > 0
        else:
            gj = json.load(open(os.path.join(PROJ, 'data', 'ne_50m_land.geojson')))
            m = Image.new('L', (MW, MH), 0); dr = ImageDraw.Draw(m)
            for f in gj['features']:
                g = f['geometry']
                polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
                for poly in polys:
                    for k, ring in enumerate(poly):
                        pts = [((lo + 180) / 360 * MW, (90 - la) / 180 * MH) for lo, la in ring]
                        dr.polygon(pts, fill=255 if k == 0 else 0)
            m.save(cache, optimize=True)
            _mask = np.asarray(m) > 0
    return _mask


def coast_rings():
    gj = json.load(open(os.path.join(PROJ, 'data', 'ne_50m_land.geojson')))
    for f in gj['features']:
        g = f['geometry']
        polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        for poly in polys:
            yield poly[0]


class Ortho:
    """Orthographic projection: lon0/lat0 at screen (cx,cy), radius R px (1x)."""
    def __init__(self, lon0, lat0, R, cx, cy):
        self.l0, self.p0 = math.radians(lon0), math.radians(lat0)
        self.R, self.cx, self.cy = R, cx, cy

    def fwd(self, lon, lat):
        l, p = np.radians(lon), np.radians(lat)
        cosc = math.sin(self.p0) * np.sin(p) + math.cos(self.p0) * np.cos(p) * np.cos(l - self.l0)
        x = self.R * np.cos(p) * np.sin(l - self.l0)
        y = self.R * (math.cos(self.p0) * np.sin(p) - math.sin(self.p0) * np.cos(p) * np.cos(l - self.l0))
        return self.cx + x, self.cy - y, cosc > 0

    def inv(self, X, Y):
        x = (X - self.cx) / self.R; y = -(Y - self.cy) / self.R
        rho = np.sqrt(x * x + y * y)
        ok = rho < 1
        rho = np.clip(rho, 1e-9, 1)
        c = np.arcsin(rho)
        lat = np.arcsin(np.cos(c) * math.sin(self.p0) + y * np.sin(c) * math.cos(self.p0) / rho)
        lon = self.l0 + np.arctan2(x * np.sin(c), rho * math.cos(self.p0) * np.cos(c) - y * math.sin(self.p0) * np.sin(c))
        return np.degrees(lon), np.degrees(lat), ok


def draw_map(fr, pr, dot_spacing=None, dot_r=None, coast=False, graticule=True, disk=True, region=(0, 0, W, H)):
    sp = dot_spacing or STYLE['map']['dot_spacing_px']
    rr = dot_r or STYLE['map']['dot_radius_px']
    d = fr.d
    if disk and pr.R < 2000:
        d.ellipse([(pr.cx - pr.R) * S, (pr.cy - pr.R) * S, (pr.cx + pr.R) * S, (pr.cy + pr.R) * S],
                  fill=rgb('#101D30'), outline=rgb(P['graticule'], 0.9), width=int(1.5 * S))
    if graticule:
        for lat in range(-80, 90, 10):
            lons = np.linspace(-180, 180, 721)
            x, y, v = pr.fwd(lons, np.full_like(lons, lat))
            _polyline(d, x, y, v, rgb(P['graticule'], 0.55), 1.0)
        for lon in range(-180, 180, 10):
            lats = np.linspace(-89, 89, 357)
            x, y, v = pr.fwd(np.full_like(lats, lon), lats)
            _polyline(d, x, y, v, rgb(P['graticule'], 0.55), 1.0)
    x0, y0, x1, y1 = region
    X, Y = np.meshgrid(np.arange(x0 + sp / 2, x1, sp), np.arange(y0 + sp / 2, y1, sp))
    # hex offset rows for a printed-halftone look
    X = X + (np.arange(X.shape[0])[:, None] % 2) * sp / 2
    lon, lat, ok = pr.inv(X, Y)
    m = land_mask()
    mi = ((90 - lat) / 180 * MH).astype(int).clip(0, MH - 1)
    mj = (((lon + 180) % 360) / 360 * MW).astype(int).clip(0, MW - 1)
    land = ok & m[mi, mj]
    col = rgb(P['land_dot'])
    for xx, yy in zip(X[land], Y[land]):
        d.ellipse([(xx - rr) * S, (yy - rr) * S, (xx + rr) * S, (yy + rr) * S], fill=col)
    if coast:
        for ring in coast_rings():
            a = np.array(ring)
            if a[:, 0].max() < -180 or len(a) < 3:
                continue
            x, y, v = pr.fwd(a[:, 0], a[:, 1])
            if not (((x > -50) & (x < W + 50) & (y > -50) & (y < H + 50)) & v).any():
                continue
            _polyline(d, x, y, v, rgb(P['coast'], 0.7), STYLE['lines']['coast_px'])
    return land


def _polyline(d, x, y, v, col, w):
    seg = []
    for xi, yi, vi in zip(x, y, v):
        if vi:
            seg.append((xi * S, yi * S))
        else:
            if len(seg) > 1:
                d.line(seg, fill=col, width=max(1, int(w * S)), joint='curve')
            seg = []
    if len(seg) > 1:
        d.line(seg, fill=col, width=max(1, int(w * S)), joint='curve')


# ---------------- light sources ----------------
def fire(fr, x, y, size=1.0, seed=0, embers=14):
    """Bonfire glyph: small flame + embers + halo. All seeded."""
    rng = np.random.default_rng(seed)
    lay = Image.new('RGB', (W * S, H * S), (0, 0, 0)); g = ImageDraw.Draw(lay)
    # flame tongues: teardrops (pointed tip up), back-to-front deep->amber->core
    def tear(cx, cy, w, h, col):
        a = np.linspace(0, 2 * np.pi, 64)
        xs = cx + w * np.sin(a) * np.sin(a / 2) ** 1.4
        ys = cy - h * (0.5 + 0.5 * np.cos(a))
        g.polygon([(px * S, py * S) for px, py in zip(xs, ys)], fill=col)
    for k in range(4):
        ox = (k - 1.5) * 5.0 * size + rng.uniform(-1.5, 1.5) * size
        tear(x + ox, y, (6.5 + rng.uniform(0, 2)) * size, (26 + rng.uniform(0, 14)) * size, rgb(P['ember_deep']))
    for k in range(3):
        ox = (k - 1) * 4.0 * size + rng.uniform(-1, 1) * size
        tear(x + ox, y, (5 + rng.uniform(0, 1.5)) * size, (18 + rng.uniform(0, 10)) * size, rgb(P['ember_amber']))
    tear(x, y, 4.2 * size, 12 * size, rgb(P['ember_core']))
    # log base
    g.line([((x - 12 * size) * S, (y + 2 * size) * S), ((x + 12 * size) * S, (y - 1 * size) * S)], fill=tuple(int(v * 0.5) for v in rgb(P['ember_deep'])), width=max(1, int(3 * size * S)))
    fr.add_light_image(lay)
    fr.add_light_image(lay, blur=3 * size)
    for _ in range(embers):
        ex = x + rng.normal(0, 7 * size); ey = y - rng.uniform(18, 70) * size
        er = rng.uniform(0.8, 1.8) * size
        fr.circle(ex, ey, er, rgb(P['ember_amber']), light=True)
    fr.glow(x, y - 8 * size, 10 * size, P['ember_amber'], 16 * size, 0.55)
    fr.glow(x, y - 8 * size, 26 * size, P['ember_deep'], 34 * size, 0.30)


def city_light(fr, x, y, r=2.6, strength=1.0):
    fr.circle(x, y, r, tuple(int(c * strength) for c in rgb(P['ember_core'])), light=True)
    fr.glow(x, y, r * 2.0, P['ember_amber'], r * 3.5, 0.75 * strength)
    fr.glow(x, y, r * 4.0, P['ember_deep'], r * 9, 0.35 * strength)


def many_lights(fr, pts, r=1.6, blur=5, strength=0.9):
    lay = Image.new('RGB', (W * S, H * S), (0, 0, 0)); g = ImageDraw.Draw(lay)
    c = tuple(int(v * strength) for v in rgb(P['ember_core']))
    for x, y in pts:
        g.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=c)
    fr.add_light_image(lay)
    lay2 = lay.filter(ImageFilter.GaussianBlur(blur * S))
    arr = (np.asarray(lay2, np.float32) * 2.2).clip(0, 255).astype(np.uint8)
    am = np.asarray(Image.new('RGB', (1, 1), rgb(P['ember_amber'])), np.float32)[0, 0] / 255
    arr = (arr.astype(np.float32) * am[None, None]).astype(np.uint8)
    fr.add_light_image(Image.fromarray(arr))


def arc_pts(x0, y0, x1, y1, bulge, n=120):
    t = np.linspace(0, 1, n)
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    nx, ny = -dy / L, dx / L
    cx, cy = mx + nx * bulge * L, my + ny * bulge * L
    x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t ** 2 * x1
    y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t ** 2 * y1
    return x, y
