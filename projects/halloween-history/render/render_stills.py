"""Render one key still per shot (9 shots) -> ../stills/NN.png + contact sheet.
Usage: python render_stills.py [shot_no ...]
Deterministic: seed per shot = 1031 + shot_no. No clocks.
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import *
from cutouts import *

OUT = os.path.join(PROJ, 'stills')
CREAM, MIST, AMBER, VEIL = P['paper_cream'], P['mist_grey'], P['ember_amber'], P['veil_moon']
SIDE = 80


def headline_block(fr, y, kicker, title, kicker_color=AMBER):
    fr.text((SIDE, y), kicker, 'caption', 36, kicker_color)
    fr.text((SIDE, y + 56), title, 'headline', 84, CREAM)


def rule(fr, x0, x1, y, col=MIST, a=0.5, w=1.5):
    fr.d.line([(x0 * S, y * S), (x1 * S, y * S)], fill=rgb(col, a), width=int(w * S))


# ---------------------------------------------------------------- shot 01
# v0.2: same composition/text; ~70 city hubs + ~1,500 town lights (seeded), stronger two-layer glow,
# cool moon-lit limb line, Ireland = brighter core + double ring.
CITIES01 = [  # (lat, lon, weight)  weight ~ relative night-light size
    (53.35, -6.26, 1.6), (54.6, -5.93, 0.6), (51.9, -8.47, 0.5), (53.27, -9.05, 0.4), (55.95, -3.19, 1.2), (55.86, -4.25, 1.0),
    (57.15, -2.1, 0.4), (51.5, -0.12, 2.2), (53.48, -2.24, 1.0), (52.48, -1.9, 0.9), (53.8, -1.55, 0.7), (51.45, -2.58, 0.5),
    (48.85, 2.35, 1.8), (45.76, 4.84, 0.7), (43.3, 5.37, 0.6), (52.37, 4.9, 0.9), (50.85, 4.35, 0.8), (51.22, 6.77, 1.0),
    (52.52, 13.40, 1.1), (48.14, 11.58, 0.8), (50.11, 8.68, 0.8), (53.55, 9.99, 0.7), (40.42, -3.70, 1.2), (41.39, 2.17, 0.9),
    (38.72, -9.14, 0.6), (41.9, 12.5, 0.9), (45.46, 9.19, 1.0), (59.33, 18.07, 0.5), (55.68, 12.57, 0.5), (59.91, 10.75, 0.4),
    (60.17, 24.94, 0.4), (52.23, 21.01, 0.7), (48.21, 16.37, 0.7), (50.08, 14.44, 0.5), (47.5, 19.04, 0.6), (33.57, -7.59, 0.6),
    (36.75, 3.06, 0.5), (14.69, -17.44, 0.4), (6.52, 3.38, 0.8), (40.71, -74.0, 2.4), (42.36, -71.06, 1.1), (39.95, -75.17, 1.0),
    (38.9, -77.03, 1.0), (41.88, -87.63, 1.6), (43.65, -79.38, 1.2), (45.5, -73.57, 0.9), (46.81, -71.21, 0.4), (44.65, -63.57, 0.3),
    (47.56, -52.71, 0.2), (42.33, -83.05, 0.8), (39.96, -82.99, 0.5), (40.44, -79.99, 0.6), (35.23, -80.84, 0.6), (33.75, -84.39, 1.0),
    (25.76, -80.19, 1.0), (28.54, -81.38, 0.6), (29.76, -95.37, 1.1), (32.78, -96.8, 1.1), (39.1, -94.58, 0.5), (38.63, -90.2, 0.6),
    (44.98, -93.27, 0.6), (39.74, -104.99, 0.6), (23.13, -82.38, 0.5), (19.43, -99.13, 1.4), (18.47, -69.9, 0.4), (10.48, -66.9, 0.6),
    (4.71, -74.07, 0.7), (-23.55, -46.63, 1.6), (-22.9, -43.2, 1.1), (-15.79, -47.88, 0.4), (-12.97, -38.5, 0.5), (-8.05, -34.9, 0.5),
    (-3.73, -38.52, 0.5), (-34.6, -58.38, 1.0), (64.15, -21.94, 0.2),
]


def shot01():
    fr = Frame(1032)
    pr = Ortho(-35, 38, 460, 540, 990)
    draw_map(fr, pr)
    rng = np.random.default_rng(101)
    m = land_mask()
    pts = []
    for la, lo, k in CITIES01:                 # town clusters around each hub (only on visible land)
        n = int(14 + 26 * k)
        sl = 0.55 + 0.75 * k
        lat = la + rng.normal(0, sl * 0.75, n); lon = lo + rng.normal(0, sl, n)
        x, y, v = pr.fwd(lon, lat)
        mi = ((90 - lat) / 180 * MH).astype(int).clip(0, MH - 1); mj = (((lon + 180) % 360) / 360 * MW).astype(int).clip(0, MW - 1)
        ok = v & m[mi, mj]
        pts += list(zip(x[ok], y[ok]))
    many_lights(fr, pts, r=1.25, blur=4, strength=0.75)
    # wider warm haze over dense regions (light from many towns), blur 26
    many_lights(fr, pts, r=2.0, blur=26, strength=0.22)
    for la, lo, k in CITIES01:
        x, y, v = pr.fwd(np.array([lo]), np.array([la]))
        if v[0] and k >= 0.8:
            city_light(fr, float(x[0]), float(y[0]), r=2.2 + 1.6 * k, strength=1.0)
    # moon-lit limb: thin cool line on the globe edge (base layer, no glow)
    fr.d.ellipse([(540 - 461) * S, (990 - 461) * S, (540 + 461) * S, (990 + 461) * S], outline=rgb(VEIL, 0.30), width=int(2 * S))
    # Ireland: the origin — brighter core + double ring
    x, y, _ = pr.fwd(np.array([-7.5]), np.array([53.4]))
    x, y = float(x[0]), float(y[0])
    fr.glow(x, y, 5, P['ember_core'], 5, 1.0)
    fr.glow(x, y, 12, AMBER, 18, 0.6)
    fr.glow(x, y, 30, P['ember_deep'], 40, 0.35)
    fr.d.ellipse([(x - 26) * S, (y - 26) * S, (x + 26) * S, (y + 26) * S], outline=rgb(AMBER, 0.85), width=int(2 * S))
    fr.d.ellipse([(x - 44) * S, (y - 44) * S, (x + 44) * S, (y + 44) * S], outline=rgb(AMBER, 0.35), width=int(1.5 * S))
    fr.text((540, 260), '10月31日', 'headline', 96, CREAM, anchor='ma')
    fr.text((540, 400), '一个夜晚，怎么走到了你身边？', 'body', 52, CREAM, anchor='ma')
    fr.text((540, 1500), '万圣节的历史演变', 'caption', 38, AMBER, anchor='ma')
    rule(fr, 420, 660, 1565, AMBER, 0.6)
    return fr


# ---------------------------------------------------------------- shot 02
def shot02():
    fr = Frame(1033)
    pr = Ortho(-5.6, 55.0, 5600, 600, 1000)
    draw_map(fr, pr, dot_spacing=10, dot_r=2.0, coast=True, graticule=True, disk=False, region=(0, 0, W, H))
    # veil: 3 faint sine lines across the upper map
    fr.scrim(200, 470, 0.75); fr.scrim(1420, 1580, 0.7)
    veil = Image.new('RGB', (W * S, H * S), (0, 0, 0)); vg = ImageDraw.Draw(veil)
    xs = np.linspace(-20, W + 20, 300)
    top = 560 + 22 * np.sin(xs / 160) ; bot = top + 70 + 18 * np.sin(xs / 90 + 1)
    vg.polygon([(a * S, b * S) for a, b in zip(xs, top)] + [(a * S, b * S) for a, b in zip(xs[::-1], bot[::-1])], fill=tuple(int(v * 0.10) for v in rgb(VEIL)))
    fr.add_light_image(veil, blur=14)
    for k in range(2):
        ys = 580 + k * 34 + 14 * np.sin(xs / 140 + k * 1.3) + 6 * np.sin(xs / 47 + k)
        pts = [(a * S, b * S) for a, b in zip(xs, ys)]
        fr.d.line(pts, fill=rgb(VEIL, 0.22 - 0.05 * k), width=int((2.2 - 0.5 * k) * S))
    # early-modern bonfire regions (Hutton p.369): Scottish Highlands, Isle of Man, N/mid Wales, Ulster; + Tlachtga
    fires = [(53.62, -6.89, 1.25), (54.65, -6.6, 0.9), (54.95, -7.6, 0.8), (57.15, -4.6, 1.0), (57.6, -5.6, 0.85),
             (56.7, -4.0, 0.9), (54.23, -4.55, 0.85), (52.9, -3.75, 0.8)]
    for i, (la, lo, s) in enumerate(fires):
        x, y, _ = pr.fwd(np.array([lo]), np.array([la]))
        fire(fr, float(x[0]), float(y[0]), size=s, seed=200 + i)
    x, y, _ = pr.fwd(np.array([-6.89]), np.array([53.62]))
    fr.text((x[0] - 26, y[0] + 6), 'Tlachtga 山', 'caption', 34, MIST, anchor='ra')
    headline_block(fr, 220, '爱尔兰 · 苏格兰', '萨温节 Samhain')
    fr.text((SIDE, 400), '冬天开始的那一夜', 'body', 48, MIST)
    fr.text((SIDE, 1440), '人们点起山顶的篝火，相信这一夜\n生者与亡者之间的那层纱，最薄', 'body', 46, CREAM)
    return fr


# ---------------------------------------------------------------- shot 03 masks
# v0.2: silhouettes from real photos (assets/cut, credits in assets/CREDITS.md); desaturated,
# toned to paper colour on ink; amber rim from the fire below. Labels describe what each photo shows.
def mask_cut(fr, name, cx, bottom, width=None, height=None, invert=False, lo=0.50):
    col, a = load_cut(name, width=width, height=height)
    a = soften_alpha(a, 0.8)
    t = norm_l(lum(col), a)
    if invert:
        t = 1 - t
    tone = ramp(lo + (1 - lo) * t, [(0, P['night_ink']), (1, CREAM)])
    h, w = a.shape
    x0, y0 = cx - w / S / 2, bottom - h / S
    paste(fr, tone, a, x0, y0)
    light_from(fr, rim_light(a, width=3, strength=0.55), x0, y0, blur=1.5)


MASKS03 = [  # (cutout, cx, size kw, invert, tone floor, label) — all Halloween/Samhain-season guising
    ('skekler.png', 225, dict(height=480), False, 0.38, 'Skekler 稻草伪装\n设得兰'),
    ('irish_mask.png', 540, dict(width=270), False, 0.42, '万圣节布面具\n爱尔兰·霍尼曼\n20世纪初'),
    ('irish_mask_country_life.png', 860, dict(width=280), False, 0.42, '万圣节布面具\n爱尔兰·乡村生活馆\n20世纪初'),
]


def shot03():
    fr = Frame(1034)
    for name, x, kw, inv, lo, lab in MASKS03:
        mask_cut(fr, name, x, 1035, invert=inv, lo=lo, **kw)
        fr.text((x, 1075), lab, 'caption', 34, MIST, anchor='ma', spacing=10)
    rule(fr, SIDE, W - SIDE, 1240, MIST, 0.35)
    for x in (225, 540, 860):
        fr.circle(x, 1240, 5, rgb(AMBER))
    fire(fr, 540, 1385, size=2.0, seed=303, embers=16)
    headline_block(fr, 220, '伪装', '戴上面具')
    fr.text((SIDE, 400), '让游荡的亡灵，认不出你', 'body', 50, CREAM)
    fr.text((SIDE, 1450), '这一说法来自民俗传说，学界并无定论', 'caption', 34, MIST)
    return fr


# ---------------------------------------------------------------- shot 04 calendar
# v0.2: parchment cards (seeded fibre/stain texture, deckled edges), faint manuscript ruling + Latin rubric
# behind, a candle as the only light source (warm pool on the centre card). Text unchanged.
def parchment(w, h, seed, tone='#E6D8BA', bright=1.0):
    """RGBA parchment patch at S×: value noise + fibres + edge darkening + deckled alpha."""
    rng = np.random.default_rng(seed)
    W2, H2 = int(w * S), int(h * S)
    def noise(sc):
        n = rng.normal(0, 1, (max(2, H2 // sc), max(2, W2 // sc))).astype(np.float32)
        return np.asarray(Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8)).resize((W2, H2), Image.BICUBIC), np.float32) / 128 - 1
    n = 0.55 * noise(60) + 0.30 * noise(16) + 0.15 * noise(4)
    yy, xx = np.mgrid[0:H2, 0:W2].astype(np.float32)
    ex = np.minimum(xx, W2 - 1 - xx) / (W2 / 2); ey = np.minimum(yy, H2 - 1 - yy) / (H2 / 2)
    edge = np.clip(np.minimum(ex, ey) * 3.0, 0, 1) ** 0.6           # darker toward the edge
    base = np.array(rgb(tone), np.float32)
    col = base[None, None] * (0.80 + 0.10 * n[..., None]) * (0.78 + 0.22 * edge[..., None])
    # stains: 3 soft blots, warm-brown
    for _ in range(3):
        cx, cy, r = rng.uniform(0, W2), rng.uniform(0, H2), rng.uniform(0.15, 0.35) * W2
        k = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r)))
        col *= (1 - 0.10 * k[..., None])
    img = Image.fromarray(np.clip(col * bright, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img, 'RGBA')
    for _ in range(int(w * h / 900)):                               # fibres
        x0, y0 = rng.uniform(0, W2), rng.uniform(0, H2); L = rng.uniform(8, 30) * S; a = rng.uniform(-0.4, 0.4)
        d.line([(x0, y0), (x0 + L * math.cos(a), y0 + L * math.sin(a))], fill=(70, 50, 30, int(rng.uniform(10, 26))), width=1)
    # deckled alpha: rectangle with noisy edge (±3 px)
    al = Image.new('L', (W2, H2), 0); ad = ImageDraw.Draw(al)
    m = 4 * S
    top = [(x, m + rng.uniform(-3, 3) * S) for x in np.linspace(m, W2 - m, 40)]
    right = [(W2 - m + rng.uniform(-3, 3) * S, y) for y in np.linspace(m, H2 - m, 40)]
    bot = [(x, H2 - m + rng.uniform(-3, 3) * S) for x in np.linspace(W2 - m, m, 40)]
    left = [(m + rng.uniform(-3, 3) * S, y) for y in np.linspace(H2 - m, m, 40)]
    ad.polygon(top + right + bot + left, fill=255)
    al = al.filter(ImageFilter.GaussianBlur(0.8 * S))
    img.putalpha(al)
    return img


def parch_card(fr, x, y, w, h, top, big, sub, seed, hot=False):
    bright = 1.12 if hot else 0.42
    img = parchment(w, h, seed, bright=bright)
    fr.base.paste(img, (int(x * S), int(y * S)), img); fr.d = ImageDraw.Draw(fr.base, 'RGBA')
    ink = '#2A2118'
    if hot:   # rubric month in ember_deep, numerals/sub in iron-gall ink
        fr.text((x + w / 2, y + 26), top, 'caption', 34, P['ember_deep'], anchor='ma')
        fr.text((x + w / 2, y + 80), big, 'headline', 96, ink, anchor='ma')
        fr.text((x + w / 2, y + h - 66), sub, 'caption', 34, ink, anchor='ma')
        fr.d.line([((x + 40) * S, (y + 72) * S), ((x + w - 40) * S, (y + 72) * S)], fill=rgb(P['ember_deep'], 0.55), width=int(1.5 * S))
    else:
        fr.text((x + w / 2, y + 26), top, 'caption', 34, MIST, anchor='ma')
        fr.text((x + w / 2, y + 80), big, 'headline', 72, CREAM, anchor='ma', a=0.9)
        fr.text((x + w / 2, y + h - 66), sub, 'caption', 34, MIST, anchor='ma')


def candle(fr, cx, base_y, s=1.0):
    d = fr.d
    h = 110 * s; w = 30 * s
    d.rounded_rectangle([(cx - w / 2) * S, (base_y - h) * S, (cx + w / 2) * S, base_y * S], radius=int(4 * S), fill=rgb('#CDBFA4'))
    d.rectangle([(cx - w / 2) * S, (base_y - h) * S, (cx - w / 2 + 6 * s) * S, base_y * S], fill=rgb('#B3A68E'))   # shaded side
    d.ellipse([(cx - 46 * s) * S, (base_y - 8 * s) * S, (cx + 46 * s) * S, (base_y + 10 * s) * S], fill=rgb('#2A2622'))  # holder
    d.line([(cx * S, (base_y - h) * S), (cx * S, (base_y - h - 9 * s) * S)], fill=rgb('#1A1410'), width=int(2 * S))       # wick
    fy = base_y - h - 10 * s
    lay = Image.new('RGB', (W * S, H * S), (0, 0, 0)); g = ImageDraw.Draw(lay)
    a = np.linspace(0, 2 * np.pi, 64)
    for ww, hh, col in ((7.5, 30, P['ember_amber']), (4.5, 20, P['ember_core'])):
        xs = cx + ww * s * np.sin(a) * np.sin(a / 2) ** 1.4; ys = fy + 4 * s - hh * s * (0.5 + 0.5 * np.cos(a))
        g.polygon([(px * S, py * S) for px, py in zip(xs, ys)], fill=rgb(col))
    fr.add_light_image(lay); fr.add_light_image(lay, blur=4 * s)
    fr.glow(cx, fy - 8 * s, 12 * s, P['ember_core'], 16 * s, 0.8)
    fr.glow(cx, fy - 8 * s, 40 * s, AMBER, 60 * s, 0.32)
    fr.glow(cx, fy, 120 * s, P['ember_deep'], 140 * s, 0.10)


def shot04():
    fr = Frame(1035)
    # manuscript ruling + Latin rubric (faint, behind everything; Latin = "On the Kalends of November, the feast of All Saints")
    lat = 'In Kalendis Novembris · festivitas omnium sanctorum · '
    tm = Image.new('L', (W * S, H * S), 0); td = ImageDraw.Draw(tm)
    for i, y in enumerate(range(520, 980, 44)):
        rule(fr, 40, W - 40, y + 36, '#2C4260', 0.35, 1.0)
        off = (i * 137) % 400
        td.text((40 * S - off * S, y * S), lat * 3, font=font('latin_italic', 30), fill=255)
    tm = Image.fromarray((np.asarray(tm, np.float32) * 0.06).astype(np.uint8))
    fr.base.paste(Image.new('RGB', tm.size, rgb(CREAM)), (0, 0), tm); fr.d = ImageDraw.Draw(fr.base, 'RGBA')
    # warm pool from the candle onto the table/cards
    pool = Image.new('RGB', (W * S, H * S), (0, 0, 0)); pg = ImageDraw.Draw(pool)
    pg.ellipse([440 * S, 620 * S, 1160 * S, 1180 * S], fill=tuple(int(v * 0.15) for v in rgb(AMBER)))
    fr.add_light_image(pool, blur=90)
    parch_card(fr, 70, 560, 280, 330, '10月', '31', '前夜', seed=41)
    parch_card(fr, 380, 520, 320, 410, '11月', '1', '万圣节', seed=42, hot=True)
    parch_card(fr, 730, 560, 280, 330, '11月', '2', '万灵节', seed=43)
    candle(fr, 935, 1045, 1.0)
    # word chain
    y0 = 1030
    words = [("All Hallows' Eve", MIST, 48), ("Hallowe'en", MIST, 54), ('Halloween', CREAM, 72)]
    for i, (w, c, sz) in enumerate(words):
        fr.text((540, y0 + i * 120), w, 'latin_italic', sz, c, anchor='ma')
        if i < 2:
            fr.text((540, y0 + i * 120 + 78), '↓', 'caption', 34, AMBER, anchor='ma')
    headline_block(fr, 220, '公元 9 世纪', '教会定下 11月1日')
    fr.text((SIDE, 400), '“万圣节”的前一晚，就是今天的万圣夜', 'body', 46, CREAM)
    fr.text((SIDE, 1440), "835年起，11月1日成为整个法兰克帝国的诸圣节\n“Halloween”源自苏格兰对 All Hallows' Eve 的缩写", 'caption', 34, MIST)
    return fr


# ---------------------------------------------------------------- shot 05 famine crossing
def shot05():
    fr = Frame(1036)
    pr = Ortho(-40, 47, 860, 540, 1000)
    draw_map(fr, pr, dot_spacing=11, coast=True, graticule=True, disk=False, region=(0, 0, W, H))
    srcs = [(51.9, -8.47), (53.35, -6.26), (53.41, -2.98)]           # Cork, Dublin, Liverpool
    dsts = [(40.71, -74.0), (42.36, -71.06), (46.81, -71.21), (39.95, -75.17)]  # NY, Boston, Quebec, Philadelphia
    rng = np.random.default_rng(55)
    pts = []
    for si, s in enumerate(srcs):
        for di, t in enumerate(dsts):
            x0, y0, _ = pr.fwd(np.array([s[1]]), np.array([s[0]])); x1, y1, _ = pr.fwd(np.array([t[1]]), np.array([t[0]]))
            bulge = 0.07 + 0.06 * di + 0.025 * si
            ax, ay = arc_pts(float(x0[0]), float(y0[0]), float(x1[0]), float(y1[0]), bulge)
            fr.d.line([(a * S, b * S) for a, b in zip(ax, ay)], fill=rgb(AMBER, 0.16), width=int(1.2 * S))
            n = 1000 // 12 + (1 if si * 4 + di < 1000 % 12 else 0)
            tt = rng.uniform(0, 1, n)
            idx = (tt * (len(ax) - 1)).astype(int)
            for k, ii in enumerate(idx):
                pts.append((ax[ii] + rng.normal(0, 1.6), ay[ii] + rng.normal(0, 1.6)))
    many_lights(fr, pts, r=1.4, blur=4, strength=0.8)
    fr.scrim(200, 470, 0.75); fr.scrim(1420, 1580, 0.7)
    for la, lo in dsts[:2]:
        x, y, _ = pr.fwd(np.array([lo]), np.array([la])); city_light(fr, float(x[0]), float(y[0]), 3.2)
    for la, lo in srcs[:2]:
        x, y, _ = pr.fwd(np.array([lo]), np.array([la])); city_light(fr, float(x[0]), float(y[0]), 2.6, 0.8)
    x, y, _ = pr.fwd(np.array([-74.0]), np.array([40.71])); fr.text((x[0] - 10, y[0] + 14), '纽约', 'caption', 34, MIST, anchor='ra')
    x, y, _ = pr.fwd(np.array([-71.06]), np.array([42.36])); pass
    x, y, _ = pr.fwd(np.array([-8.0]), np.array([53.0])); fr.text((x[0] + 6, y[0] + 40), '爱尔兰', 'caption', 34, MIST, anchor='ma')
    headline_block(fr, 220, '1845–1852 · 爱尔兰大饥荒', '一百万人离开')
    fr.text((SIDE, 400), '他们把万圣节，也带上了船', 'body', 50, CREAM)
    fr.text((SIDE, 1440), '约100万人死于饥荒，另有100多万人移民，多数去了北美\n画面中每个光点 ≈ 1000 人', 'caption', 34, MIST)
    return fr


# ---------------------------------------------------------------- shot 06 turnip -> pumpkin
def carved_holes(g, cx, cy, s, col):
    for sgn in (-1, 1):
        g.polygon([((cx + sgn * 48 * s) * S, (cy - 52 * s) * S), ((cx + sgn * 20 * s) * S, (cy - 8 * s) * S), ((cx + sgn * 76 * s) * S, (cy - 8 * s) * S)], fill=col)
    g.polygon([((cx - 22 * s) * S, (cy + 10 * s) * S), ((cx + 22 * s) * S, (cy + 10 * s) * S), ((cx) * S, (cy + 36 * s) * S)], fill=col)
    mouth = [(-90, 50), (-60, 70), (-40, 56), (-20, 78), (0, 60), (20, 78), (40, 56), (60, 70), (90, 50), (70, 104), (0, 124), (-70, 104)]
    g.polygon([((cx + a * s) * S, (cy + b * s) * S) for a, b in mouth], fill=col)


def pumpkin(fr, px, py, ps, holes=True):
    d = fr.d
    sil = Image.new('L', (W * S, H * S), 0); sd = ImageDraw.Draw(sil)
    ribs = [(-108, 0.60, '#B9592A'), (108, 0.60, '#B9592A'), (-60, 0.76, '#CC6A30'), (60, 0.76, '#CC6A30'), (0, 0.88, '#DA7A38')]
    for ox, wk, col in ribs:
        box = [(px + ox * ps - 95 * wk * ps) * S, (py - 122 * ps) * S, (px + ox * ps + 95 * wk * ps) * S, (py + 118 * ps) * S]
        d.ellipse(box, fill=rgb(col), outline=rgb('#7E3A1C'), width=int(2.5 * S))
        sd.ellipse(box, fill=255)
        # rib highlight (upper-left), thin
        hb = [(px + ox * ps - 40 * wk * ps) * S, (py - 108 * ps) * S, (px + ox * ps - 8 * wk * ps) * S, (py - 30 * ps) * S]
        d.ellipse(hb, fill=rgb('#EE9A58', 0.35))
    # bottom shade
    shade = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0)); sh = ImageDraw.Draw(shade)
    sh.ellipse([(px - 170 * ps) * S, (py + 20 * ps) * S, (px + 170 * ps) * S, (py + 170 * ps) * S], fill=(40, 12, 4, 110))
    shade = shade.filter(ImageFilter.GaussianBlur(18 * S))
    al = np.minimum(np.asarray(shade)[..., 3], np.asarray(sil)).astype(np.uint8)
    shade.putalpha(Image.fromarray(al))
    fr.base = Image.alpha_composite(fr.base.convert('RGBA'), shade).convert('RGB'); fr.d = ImageDraw.Draw(fr.base, 'RGBA'); d = fr.d
    d.rounded_rectangle([(px - 11 * ps) * S, (py - 158 * ps) * S, (px + 11 * ps) * S, (py - 112 * ps) * S], radius=int(6 * S), fill=rgb('#5F7A4C'))
    d.line([((px + 8 * ps) * S, (py - 150 * ps) * S), ((px + 34 * ps) * S, (py - 170 * ps) * S)], fill=rgb('#5F7A4C'), width=int(4 * S))
    if holes:
        carved_holes(d, px, py, ps, rgb('#2A1408'))
        lay = Image.new('RGB', (W * S, H * S), (0, 0, 0)); g = ImageDraw.Draw(lay)
        carved_holes(g, px, py, ps * 0.96, rgb(P['ember_core']))
        fr.add_light_image(lay)
        fr.add_light_image(Image.fromarray((np.asarray(lay, np.float32) * 0.9).astype(np.uint8)), blur=10 * ps)
        # skin lit from inside: faint warm light masked to silhouette
        warm = Image.new('RGB', (W * S, H * S), (0, 0, 0)); wg = ImageDraw.Draw(warm)
        wg.ellipse([(px - 90 * ps) * S, (py - 60 * ps) * S, (px + 90 * ps) * S, (py + 100 * ps) * S], fill=tuple(int(v * 0.35) for v in rgb(AMBER)))
        warm = warm.filter(ImageFilter.GaussianBlur(30 * ps * S))
        warm = Image.fromarray((np.asarray(warm, np.float32) * (np.asarray(sil, np.float32)[..., None] / 255)).astype(np.uint8))
        fr.add_light_image(warm)
        # light pool on the ground
        pool = Image.new('RGB', (W * S, H * S), (0, 0, 0)); pg = ImageDraw.Draw(pool)
        pg.ellipse([(px - 200 * ps) * S, (py + 105 * ps) * S, (px + 200 * ps) * S, (py + 150 * ps) * S], fill=tuple(int(v * 0.30) for v in rgb(AMBER)))
        fr.add_light_image(pool, blur=16 * ps)


def photo_lantern(fr, name, cx, cy, width, body_stops, hot_thr, seed_blur=8):
    """Real-photo lantern -> palette: body via luminance ramp, carved holes (hot, saturated pixels) -> light layer."""
    col, a = load_cut(name, width=width)
    a = soften_alpha(a, 0.6)
    L = lum(col)
    r, g, b = col[..., 0], col[..., 1], col[..., 2]
    hot = np.clip((L - hot_thr) / 40, 0, 1) * np.clip((r - b - 40) / 60, 0, 1) * a      # orange-bright = candle light
    hot = np.asarray(Image.fromarray((hot * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6 * S)), np.float32) / 255
    t = norm_l(L, a)
    body = ramp(t, body_stops)
    tone = body * (1 - hot[..., None]) + np.array(rgb(P['ember_deep']), np.float32) * hot[..., None]
    h, w = a.shape
    x0, y0 = cx - w / S / 2, cy - h / S / 2
    paste(fr, tone, a, x0, y0)
    core = hot[..., None] * np.array(rgb(P['ember_core']), np.float32)[None, None]
    light_from(fr, core, x0, y0)
    light_from(fr, core * 0.9, x0, y0, blur=seed_blur)
    return x0, y0, w / S, h / S, a


def shot06():
    fr = Frame(1037)
    # turnip (CC BY 2.5, Geni): neutral duotone ink->paper, mauve-grey mid
    photo_lantern(fr, 'turnip.png', 290, 770, 250, [(0, '#1E2433'), (0.55, '#968A8E'), (1, '#E2D8C4')], hot_thr=140, seed_blur=8)
    fr.text((290, 905), '芜菁灯\n爱尔兰/苏格兰传统', 'caption', 34, MIST, anchor='ma', spacing=8)
    ax, ay = arc_pts(400, 820, 560, 940, -0.30, 60)
    for i in range(0, 60, 4):
        fr.circle(ax[i], ay[i], 2.6, rgb(AMBER, 0.30 + 0.6 * i / 60))
    # pumpkin (CC0, Teutschmann, Eau Claire US 2016): body lit from inside -> deep ember ramp
    x0, y0, w, h, a = photo_lantern(fr, 'pumpkin.png', 650, 1125, 380, [(0, '#2A160E'), (0.40, '#8A3C1A'), (1, '#D9793A')], hot_thr=150, seed_blur=12)
    pool = Image.new('RGB', (W * S, H * S), (0, 0, 0)); pg = ImageDraw.Draw(pool)
    pg.ellipse([(650 - 230) * S, (y0 + h - 60) * S, (650 + 230) * S, (y0 + h - 16) * S], fill=tuple(int(v * 0.30) for v in rgb(AMBER)))
    fr.add_light_image(pool, blur=18)
    fr.text((650, 1330), '南瓜灯 · 美国', 'caption', 34, CREAM, anchor='ma')
    headline_block(fr, 220, '灯，换了', '芜菁 → 南瓜')
    fr.text((SIDE, 400), '在家乡，灯是用芜菁刻的\n到了美洲，换成了更大的南瓜', 'body', 46, CREAM)
    fr.text((SIDE, 1440), "1837年，美国英语首次把南瓜灯叫作 jack-o'-lantern\n（据《牛津英语词典》）", 'caption', 34, MIST)
    return fr


# ---------------------------------------------------------------- shot 07 America -> world
def shot07():
    fr = Frame(1038)
    pr = Ortho(-50, 38, 450, 540, 900)
    draw_map(fr, pr, graticule=True)
    rng = np.random.default_rng(77)
    hubs = [(40.71, -74.0, 60), (42.36, -71.06, 30), (41.88, -87.63, 40), (34.05, -118.24, 40), (29.76, -95.37, 25), (33.75, -84.39, 25),
            (39.95, -75.17, 25), (47.6, -122.33, 15), (39.74, -104.99, 15), (43.65, -79.38, 25), (45.5, -73.57, 15), (25.76, -80.19, 20),
            (44.98, -93.27, 15), (38.63, -90.2, 15), (36.17, -86.78, 12), (32.78, -96.8, 20), (49.28, -123.12, 10), (19.43, -99.13, 12)]
    pts = []
    for la, lo, n in hubs:
        for _ in range(n):
            x, y, v = pr.fwd(np.array([lo + rng.normal(0, 1.6)]), np.array([la + rng.normal(0, 1.2)]))
            if v[0]:
                pts.append((float(x[0]), float(y[0])))
    many_lights(fr, pts, r=1.5, blur=4, strength=0.8)
    # outgoing arcs to the world (film / TV / internet)
    x0, y0, _ = pr.fwd(np.array([-95.0]), np.array([38.0]))
    for k, (la, lo) in enumerate([(51.5, -0.12), (48.85, 2.35), (59.33, 18.07), (40.42, -3.70), (41.0, 28.97)]):
        x1, y1, v = pr.fwd(np.array([lo]), np.array([la]))
        ax, ay = arc_pts(float(x0[0]), float(y0[0]), float(x1[0]), float(y1[0]), -0.22)
        fr.d.line([(a * S, b * S) for a, b in zip(ax, ay)], fill=rgb(AMBER, 0.35), width=int(2 * S))
        city_light(fr, float(x1[0]), float(y1[0]), 2.4, 0.8)
    headline_block(fr, 220, '20世纪 · 北美', '不给糖就捣蛋')
    # timeline list
    fr.scrim(1380, 1600, 0.7)
    items = [('1917', '“trick or treat” 首次见报（加拿大）'), ('1950s', '讨糖成为全美孩子的夜晚'),
             ('2023', '美国万圣节消费预计 122 亿美元'), ('今天', '电影、电视、互联网，把它带向世界')]
    y = 1400
    for yr, s in items:
        fr.text((SIDE, y), yr, 'caption', 34, AMBER)
        fr.text((SIDE + 120, y), s, 'caption', 34, CREAM)
        y += 54
    return fr


# ---------------------------------------------------------------- shot 08 today: city windows (v0.2, no map)
def phone_card(fr, x, y, w, h, ang, seed):
    lay = Image.new('RGBA', (int(w * S) + 40, int(h * S) + 40), (0, 0, 0, 0)); g = ImageDraw.Draw(lay)
    g.rounded_rectangle([20, 20, 20 + w * S, 20 + h * S], radius=int(18 * S), fill=rgb('#16263B', 0.92), outline=rgb(CREAM, 0.8), width=int(2.5 * S))
    # tiny lit pumpkin inside (object, no person)
    cx, cy = 20 + w * S / 2, 20 + h * S * 0.42
    r = w * S * 0.22
    g.ellipse([cx - r, cy - r * 0.85, cx + r, cy + r * 0.85], fill=rgb('#D9793A'))
    g.polygon([(cx - r * 0.5, cy - r * 0.2), (cx - r * 0.2, cy - r * 0.2), (cx - r * 0.35, cy - r * 0.5)], fill=rgb(P['ember_core']))
    g.polygon([(cx + r * 0.5, cy - r * 0.2), (cx + r * 0.2, cy - r * 0.2), (cx + r * 0.35, cy - r * 0.5)], fill=rgb(P['ember_core']))
    g.rectangle([cx - r * 0.5, cy + r * 0.2, cx + r * 0.5, cy + r * 0.38], fill=rgb(P['ember_core']))
    for k in range(3):
        yy = 20 + h * S * (0.72 + 0.08 * k)
        g.rounded_rectangle([20 + w * S * 0.14, yy, 20 + w * S * (0.86 - 0.22 * k), yy + 6 * S], radius=int(3 * S), fill=rgb(MIST, 0.6))
    lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    fr.base.paste(lay, (int(x * S - lay.width / 2), int(y * S - lay.height / 2)), lay)


def skyline(fr, seed=808):
    """Generic apartment blocks with window grids (no landmarks, no map). Returns list of pumpkin-window centres."""
    rng = np.random.default_rng(seed)
    d = fr.d
    lay = Image.new('RGB', (W * S, H * S), (0, 0, 0)); g = ImageDraw.Draw(lay)
    warm = [P['ember_core'], P['ember_amber'], '#E8C38A']
    # far layer: low, dim, small windows
    x = -20
    while x < W + 20:
        bw = rng.uniform(70, 140); top = rng.uniform(820, 980)
        d.rectangle([x * S, top * S, (x + bw) * S, H * S], fill=rgb('#0F1A2B'))
        for wy in np.arange(top + 14, 1380, 18):
            for wx in np.arange(x + 8, x + bw - 10, 14):
                if rng.uniform() < 0.12:
                    c = tuple(int(v * 0.35) for v in rgb(warm[rng.integers(3)]))
                    g.rectangle([wx * S, wy * S, (wx + 7) * S, (wy + 9) * S], fill=c)
        x += bw + rng.uniform(4, 14)
    # near layer: 7 blocks
    blocks = [(-10, 150, 700), (150, 175, 860), (335, 140, 760), (485, 190, 640), (690, 150, 880), (850, 120, 720), (978, 130, 800)]
    pumpkins = []
    for bi, (bx, bw, top) in enumerate(blocks):
        d.rectangle([bx * S, top * S, (bx + bw) * S, H * S], fill=rgb('#101C2E'))
        d.line([(bx * S, top * S), ((bx + bw) * S, top * S)], fill=rgb('#22344E'), width=int(2 * S))        # roof edge
        d.rectangle([(bx + bw * 0.62) * S, (top - 22) * S, (bx + bw * 0.62 + 26) * S, top * S], fill=rgb('#101C2E'))  # roof box
        ww, wh, gx, gy = 16, 22, 10, 14
        cols = int((bw - 24) // (ww + gx)); x0 = bx + (bw - (cols * (ww + gx) - gx)) / 2
        for r, wy in enumerate(np.arange(top + 24, 1400, wh + gy)):
            for c in range(cols):
                wx = x0 + c * (ww + gx)
                box = [wx * S, wy * S, (wx + ww) * S, (wy + wh) * S]
                p = rng.uniform() + max(0, (wy - 1200) / 400)     # fewer lit floors toward the street
                if p < 0.24:
                    k = rng.uniform(0.45, 0.80)
                    col = tuple(int(v * k) for v in rgb(warm[rng.integers(3)]))
                    d.rectangle(box, fill=tuple(int(v * 0.55) for v in col))
                    g.rectangle(box, fill=tuple(int(v * 0.55) for v in col))
                elif p < 0.255:     # a few cool TV-lit windows (≤5% cool rule)
                    d.rectangle(box, fill=tuple(int(v * 0.35) for v in rgb(VEIL)))
                else:
                    d.rectangle(box, fill=rgb('#0B1422'))
    # pumpkin windows: fixed list (block, col-fraction, row) -> tiny lit pumpkin on the sill
    for bx, bw, top, frac, row in ((150, 175, 860, 0.3, 4), (335, 140, 760, 0.7, 9), (485, 190, 640, 0.5, 6), (690, 150, 880, 0.25, 3),
                                   (850, 120, 720, 0.6, 12), (-10, 150, 700, 0.6, 7), (978, 130, 800, 0.4, 5), (485, 190, 640, 0.2, 15)):
        ww, wh, gx, gy = 16, 22, 10, 14
        cols = int((bw - 24) // (ww + gx)); x0 = bx + (bw - (cols * (ww + gx) - gx)) / 2
        c = int(frac * (cols - 1)); wx = x0 + c * (ww + gx); wy = top + 24 + row * (wh + gy)
        box = [wx * S, wy * S, (wx + ww) * S, (wy + wh) * S]
        d.rectangle(box, fill=rgb('#4A2512'))
        g.rectangle(box, fill=tuple(int(v * 0.30) for v in rgb(P['ember_deep'])))
        pcx, pcy = wx + ww / 2, wy + wh - 7
        d.ellipse([(pcx - 7) * S, (pcy - 6) * S, (pcx + 7) * S, (pcy + 6) * S], fill=rgb('#D9793A'))
        d.line([(pcx * S, (pcy - 6) * S), (pcx * S, (pcy - 9) * S)], fill=rgb('#5F7A4C'), width=int(2 * S))
        g.ellipse([(pcx - 6) * S, (pcy - 5) * S, (pcx + 6) * S, (pcy + 5) * S], fill=tuple(int(v * 0.6) for v in rgb(AMBER)))
        for sx in (-3, 3):     # two eyes + mouth glow
            g.rectangle([(pcx + sx - 1.2) * S, (pcy - 2.5) * S, (pcx + sx + 1.2) * S, (pcy - 0.5) * S], fill=rgb(P['ember_core']))
        g.rectangle([(pcx - 3.5) * S, (pcy + 1) * S, (pcx + 3.5) * S, (pcy + 2.5) * S], fill=rgb(P['ember_core']))
        fr.glow(pcx, pcy, 8, AMBER, 14, 0.75)
        fr.glow(pcx, pcy, 20, P['ember_deep'], 30, 0.35)
        pumpkins.append((pcx, pcy))
    fr.add_light_image(lay)
    fr.add_light_image(lay, blur=3)
    return pumpkins


def shot08():
    fr = Frame(1039)
    pk = skyline(fr)
    # three social-post cards rising from pumpkin windows (thin amber tether)
    for (pi, cx, cy, ang, sd) in ((2, 860, 640, -6, 1), (5, 200, 760, 5, 2), (4, 920, 1230, 4, 3)):
        sx, sy = pk[pi]
        fr.d.line([(sx * S, sy * S), (cx * S, (cy + 80) * S)], fill=rgb(AMBER, 0.45), width=int(1.5 * S))
        phone_card(fr, cx, cy, 130, 220, ang, sd)
    fr.scrim(200, 470, 0.75); fr.scrim(1420, 1580, 0.7)
    headline_block(fr, 220, '今天', '它也来到了这里')
    fr.text((SIDE, 400), '主题乐园、变装派对、朋友圈', 'body', 50, CREAM)
    fr.text((SIDE, 1440), '每到秋天，不少主题乐园都会办万圣节活动', 'caption', 34, MIST)
    return fr


# ---------------------------------------------------------------- shot 09 three nights
def river_lantern(fr, cx, cy, s):
    d = fr.d
    # water lines
    for k in range(4):
        y = cy + 40 * s + k * 12 * s
        d.line([((cx - 150 * s + k * 20 * s) * S, y * S), ((cx + 150 * s - k * 20 * s) * S, y * S)], fill=rgb(VEIL, 0.18 - 0.03 * k), width=int(2 * S))
    # lotus petals (paper)
    for a in (-60, -30, 0, 30, 60):
        t = math.radians(a)
        px, py = cx + math.sin(t) * 55 * s, cy - math.cos(t) * 20 * s
        d.polygon([((cx + math.sin(t) * 20 * s) * S, (cy + 20 * s) * S), ((px - 18 * s) * S, (py) * S), ((px + math.sin(t) * 18 * s) * S, (py - 45 * s) * S), ((px + 18 * s) * S, py * S)],
                  fill=rgb(CREAM, 0.9))
    d.ellipse([(cx - 75 * s) * S, (cy + 8 * s) * S, (cx + 75 * s) * S, (cy + 38 * s) * S], fill=rgb('#D9CFBE'))
    fr.glow(cx, cy - 18 * s, 9 * s, P['ember_core'], 8 * s, 0.9)
    fr.glow(cx, cy - 10 * s, 30 * s, AMBER, 30 * s, 0.35)
    # reflection
    fr.glow(cx, cy + 66 * s, 6 * s, AMBER, 10 * s, 0.25)


def paper_clothes(fr, cx, cy, s):
    d = fr.d
    pts = [(-70, -60), (-30, -75), (-14, -62), (14, -62), (30, -75), (70, -60), (105, -10), (75, 8), (55, -18), (55, 80), (-55, 80), (-55, -18), (-75, 8), (-105, -10)]
    d.polygon([((cx + a * s) * S, (cy + b * s) * S) for a, b in pts], fill=rgb(CREAM, 0.9))
    for k in range(3):
        y = cy + (-10 + 26 * k) * s
        d.line([((cx - 50 * s) * S, y * S), ((cx + 50 * s) * S, y * S)], fill=rgb('#B9AE9A'), width=int(1.5 * S))
    # burning lower-right corner
    d.polygon([((cx + 20 * s) * S, (cy + 80 * s) * S), ((cx + 55 * s) * S, (cy + 40 * s) * S), ((cx + 55 * s) * S, (cy + 80 * s) * S)], fill=rgb('#0D1828'))
    fire(fr, cx + 48 * s, cy + 84 * s, size=0.9 * s, seed=909, embers=12)


def small_pumpkin(fr, cx, cy, s):
    pumpkin(fr, cx, cy + 6, 0.5 * s)


def shot09():
    fr = Frame(1040)
    rows = [(330, '10月31日', '万圣夜', '为亡灵点一盏灯', small_pumpkin),
            (650, '农历七月十五', '中元节', '放一盏河灯', river_lantern),
            (970, '农历十月初一', '寒衣节', '给远方的人送冬衣', paper_clothes)]
    for y, date, name, act, fn in rows:
        fr.d.rounded_rectangle([SIDE * S, (y - 130) * S, (W - SIDE) * S, (y + 140) * S], radius=int(16 * S), fill=rgb('#111F33'),
                               outline=rgb('#2C4260', 0.9), width=int(1.5 * S))
        fn(fr, 250, y, 0.95)
        fr.text((420, y - 92), date, 'caption', 36, AMBER)
        fr.text((420, y - 38), name, 'headline', 72, CREAM)
        fr.text((420, y + 62), act, 'caption', 36, MIST)
    fr.text((540, 1230), '每个文化，', 'headline', 76, CREAM, anchor='ma')
    fr.text((540, 1340), '都给想念留了一个夜晚', 'headline', 76, CREAM, anchor='ma')
    fr.text((540, 1470), '今年的寒衣节：11月9日', 'caption', 36, AMBER, anchor='ma')
    return fr


SHOTS = {1: shot01, 2: shot02, 3: shot03, 4: shot04, 5: shot05, 6: shot06, 7: shot07, 8: shot08, 9: shot09}


def contact_sheet():
    files = [os.path.join(OUT, f'{i:02d}.png') for i in SHOTS]
    tw, th, pad, cols = 300, 533, 16, 5
    rows = math.ceil(len(files) / cols)
    sheet = Image.new('RGB', (cols * tw + (cols + 1) * pad, rows * (th + 46) + (rows + 1) * pad), rgb('#0A1220'))
    dr = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(STYLE['fonts']['caption']['file'], 24, index=2)
    for i, p in enumerate(files):
        im = Image.open(p).resize((tw, th), Image.LANCZOS)
        x = pad + (i % cols) * (tw + pad); y = pad + (i // cols) * (th + 46 + pad)
        sheet.paste(im, (x, y))
        dr.text((x, y + th + 8), f'{i + 1:02d}', font=f, fill=rgb(MIST))
    out = os.path.join(PROJ, 'contact_sheet.jpg')
    sheet.save(out, quality=85, optimize=True)
    print('contact', out, os.path.getsize(out))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    ids = [int(a) for a in sys.argv[1:]] or list(SHOTS)
    for i in ids:
        fr = SHOTS[i]()
        fr.finish(os.path.join(OUT, f'{i:02d}.png'))
        print('wrote', i)
    if not sys.argv[1:]:
        contact_sheet()
