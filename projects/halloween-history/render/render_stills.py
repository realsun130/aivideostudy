"""Render one key still per shot (9 shots) -> ../stills/NN.png + contact sheet.
Usage: python render_stills.py [shot_no ...]
Deterministic: seed per shot = 1031 + shot_no. No clocks.
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import *

OUT = os.path.join(PROJ, 'stills')
CREAM, MIST, AMBER, VEIL = P['paper_cream'], P['mist_grey'], P['ember_amber'], P['veil_moon']
SIDE = 80


def headline_block(fr, y, kicker, title, kicker_color=AMBER):
    fr.text((SIDE, y), kicker, 'caption', 36, kicker_color)
    fr.text((SIDE, y + 56), title, 'headline', 84, CREAM)


def rule(fr, x0, x1, y, col=MIST, a=0.5, w=1.5):
    fr.d.line([(x0 * S, y * S), (x1 * S, y * S)], fill=rgb(col, a), width=int(w * S))


# ---------------------------------------------------------------- shot 01
def shot01():
    fr = Frame(1032)
    pr = Ortho(-35, 38, 460, 540, 990)
    draw_map(fr, pr)
    cities = [(53.35, -6.26, 1.6), (55.95, -3.19, 1.2), (51.5, -0.12, 0.9), (40.71, -74.0, 1.3), (42.36, -71.06, 1.0),
              (41.88, -87.63, 0.9), (43.65, -79.38, 0.9), (34.05, -118.24, 0.8), (19.43, -99.13, 0.8),
              (48.85, 2.35, 0.7), (52.52, 13.40, 0.7), (40.42, -3.70, 0.6), (-23.55, -46.63, 0.6), (45.5, -73.57, 0.8),
              (29.76, -95.37, 0.7), (33.75, -84.39, 0.7), (38.9, -77.03, 0.8), (47.6, -122.33, 0.6), (59.33, 18.07, 0.5)]
    for la, lo, k in cities:
        x, y, v = pr.fwd(np.array([lo]), np.array([la]))
        if v[0]:
            city_light(fr, float(x[0]), float(y[0]), r=2.6 + 1.8 * k, strength=1.0)
    # Ireland: the origin, a ring
    x, y, _ = pr.fwd(np.array([-7.5]), np.array([53.4]))
    fr.d.ellipse([(x[0] - 26) * S, (y[0] - 26) * S, (x[0] + 26) * S, (y[0] + 26) * S], outline=rgb(AMBER, 0.8), width=int(2 * S))
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
def mask_glyph(fr, kind, cx, cy, s):
    d = fr.d
    c = rgb(CREAM)
    hole = rgb('#0D1828')
    if kind == 'antler':      # folk disguise: hood with antlers
        for sgn in (-1, 1):
            base = (cx + sgn * 60 * s, cy - 120 * s)
            pts = [base, (cx + sgn * 110 * s, cy - 230 * s), (cx + sgn * 150 * s, cy - 300 * s)]
            d.line([(a * S, b * S) for a, b in pts], fill=c, width=int(9 * s * S), joint='curve')
            for t, l in ((0.45, 60), (0.8, 50)):
                bx = pts[0][0] + (pts[2][0] - pts[0][0]) * t; by = pts[0][1] + (pts[2][1] - pts[0][1]) * t
                d.line([(bx * S, by * S), ((bx + sgn * l * s * 0.9) * S, (by - l * s * 0.6) * S)], fill=c, width=int(7 * s * S))
        d.polygon([((cx + a * s) * S, (cy + b * s) * S) for a, b in
                   [(-95, -130), (95, -130), (110, 10), (60, 150), (0, 185), (-60, 150), (-110, 10)]], fill=c)
    elif kind == 'false_face':  # Scots 'fause-face': plain card mask
        d.ellipse([(cx - 100 * s) * S, (cy - 140 * s) * S, (cx + 100 * s) * S, (cy + 150 * s) * S], fill=c)
        d.line([((cx - 100 * s) * S, (cy - 20 * s) * S), ((cx - 170 * s) * S, (cy - 40 * s) * S)], fill=rgb(MIST), width=int(3 * S))
        d.line([((cx + 100 * s) * S, (cy - 20 * s) * S), ((cx + 170 * s) * S, (cy - 40 * s) * S)], fill=rgb(MIST), width=int(3 * S))
    else:                       # 20th-c moulded plastic cat mask
        d.polygon([((cx + a * s) * S, (cy + b * s) * S) for a, b in
                   [(-105, -150), (-55, -95), (55, -95), (105, -150), (115, 0), (70, 110), (0, 140), (-70, 110), (-115, 0)]], fill=c)
    # eye holes (objects only — no faces/expressions)
    for sgn in (-1, 1):
        d.ellipse([(cx + sgn * 42 * s - 20 * s) * S, (cy - 30 * s - 12 * s) * S, (cx + sgn * 42 * s + 20 * s) * S, (cy - 30 * s + 12 * s) * S], fill=hole)
    # warm rim from the fire below: thin amber arc at bottom edge
    lay = Image.new('RGB', (W * S, H * S), (0, 0, 0)); g = ImageDraw.Draw(lay)
    g.arc([(cx - 112 * s) * S, (cy - 140 * s) * S, (cx + 112 * s) * S, (cy + 190 * s) * S], 35, 145, fill=tuple(int(v * 0.7) for v in rgb(AMBER)), width=int(5 * S))
    fr.add_light_image(lay, blur=2)


def shot03():
    fr = Frame(1034)
    xs = [225, 540, 860]
    kinds = ['antler', 'false_face', 'plastic']
    labels = ['兽皮与鹿角\n古代 · 传说', '“假脸” fause-face\n1890 · 苏格兰', '塑料面具\n20世纪 · 美国']
    for x, k, lab in zip(xs, kinds, labels):
        mask_glyph(fr, k, x, 900, 0.82)
        fr.text((x, 1110), lab, 'caption', 34, MIST, anchor='ma')
    rule(fr, SIDE, W - SIDE, 1240, MIST, 0.35)
    for x in xs:
        fr.circle(x, 1240, 5, rgb(AMBER))
    fire(fr, 540, 1385, size=2.0, seed=303, embers=16)
    headline_block(fr, 220, '伪装', '戴上面具')
    fr.text((SIDE, 400), '让游荡的亡灵，认不出你', 'body', 50, CREAM)
    fr.text((SIDE, 1450), '这一说法来自民俗传说，学界并无定论', 'caption', 34, MIST)
    return fr


# ---------------------------------------------------------------- shot 04 calendar
def card(fr, x, y, w, h, top, big, sub, hot=False):
    d = fr.d
    d.rounded_rectangle([x * S, y * S, (x + w) * S, (y + h) * S], radius=int(14 * S), fill=rgb('#16263B'),
                        outline=rgb(AMBER if hot else '#2C4260', 0.95), width=int((3 if hot else 1.5) * S))
    fr.text((x + w / 2, y + 26), top, 'caption', 34, AMBER if hot else MIST, anchor='ma')
    fr.text((x + w / 2, y + 80), big, 'headline', 96 if hot else 72, CREAM if hot else MIST, anchor='ma')
    fr.text((x + w / 2, y + h - 66), sub, 'caption', 34, CREAM if hot else MIST, anchor='ma')


def shot04():
    fr = Frame(1035)
    card(fr, 70, 560, 280, 330, '10月', '31', '前夜')
    card(fr, 380, 520, 320, 410, '11月', '1', '万圣节', hot=True)
    card(fr, 730, 560, 280, 330, '11月', '2', '万灵节')
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


def turnip(fr, tx, ty, ts, alpha=1.0):
    d = fr.d
    a = np.linspace(0, 2 * np.pi, 160)
    # bulb with tapered root at the bottom (teardrop pointing down)
    xs = tx + 118 * ts * np.sin(a) * (np.sin(a / 2) ** 0.35) * (0.82 + 0.18 * np.cos(a))
    ys = ty + 120 * ts * np.cos(a) * -1 * 0.95
    poly = [(x * S, y * S) for x, y in zip(xs, ys)]
    body = Image.new('L', (W * S, H * S), 0); ImageDraw.Draw(body).polygon(poly, fill=255)
    cream = Image.new('RGB', (W * S, H * S), rgb('#E2D8C4'))
    mauve = Image.new('RGB', (W * S, H * S), rgb('#8E7C93'))
    band = Image.new('L', (W * S, H * S), 0); ImageDraw.Draw(band).rectangle([0, 0, W * S, (ty - 40 * ts) * S], fill=255)
    band = band.filter(ImageFilter.GaussianBlur(22 * ts * S))
    col = Image.composite(mauve, cream, band)
    m = Image.fromarray((np.asarray(body, np.float32) * alpha).astype(np.uint8))
    fr.base.paste(col, (0, 0), m); fr.d = ImageDraw.Draw(fr.base, 'RGBA'); d = fr.d
    # root tail + leaves
    d.line([(tx * S, (ty + 114 * ts) * S), ((tx + 6 * ts) * S, (ty + 170 * ts) * S)], fill=rgb('#CFC3AC'), width=int(3 * S))
    for dx, dy in ((-24, -205), (6, -220), (34, -195)):
        d.line([(tx * S, (ty - 112 * ts) * S), ((tx + dx * ts) * S, (ty + dy * ts) * S)], fill=rgb('#6E8A5A'), width=int(6 * S))
    d2 = ImageDraw.Draw(fr.base); carved_holes(d2, tx, ty + 6 * ts, ts * 0.8, rgb('#2A1408'))
    lay = Image.new('RGB', (W * S, H * S), (0, 0, 0)); g = ImageDraw.Draw(lay)
    carved_holes(g, tx, ty + 6 * ts, ts * 0.77, tuple(int(v * 0.95) for v in rgb(P['ember_core'])))
    fr.add_light_image(lay); fr.add_light_image(lay, blur=7)


def shot06():
    fr = Frame(1037)
    turnip(fr, 290, 760, 0.72)
    fr.text((290, 920), '芜菁灯 · 爱尔兰/苏格兰', 'caption', 34, MIST, anchor='ma')
    ax, ay = arc_pts(400, 820, 560, 940, -0.30, 60)
    for i in range(0, 60, 4):
        fr.circle(ax[i], ay[i], 2.6, rgb(AMBER, 0.30 + 0.6 * i / 60))
    pumpkin(fr, 650, 1130, 1.22)
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


# ---------------------------------------------------------------- shot 08 China today
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


def shot08():
    fr = Frame(1039)
    pr = Ortho(112, 31, 1500, 560, 1000)
    draw_map(fr, pr, dot_spacing=11, coast=True, graticule=True, disk=False, region=(0, 0, W, H))
    cities = {'北京': (39.9, 116.4), '上海': (31.23, 121.47), '广州': (23.13, 113.26), '成都': (30.66, 104.07), '深圳': (22.54, 114.06),
              '杭州': (30.27, 120.15), '武汉': (30.59, 114.3), '西安': (34.34, 108.94), '重庆': (29.56, 106.55), '南京': (32.06, 118.8),
              '长沙': (28.23, 112.94), '香港': (22.32, 114.17), '天津': (39.13, 117.2), '厦门': (24.48, 118.09)}
    pos = {}
    for name, (la, lo) in cities.items():
        x, y, _ = pr.fwd(np.array([lo]), np.array([la])); pos[name] = (float(x[0]), float(y[0]))
        big = name in ('北京', '上海', '广州', '成都')
        rng = np.random.default_rng(800 + len(pos))
        n = 60 if big else 22
        xs, ys, _ = pr.fwd(lo + rng.normal(0, 0.45, n), la + rng.normal(0, 0.35, n))
        many_lights(fr, list(zip(xs, ys)), r=1.5, blur=4, strength=0.85)
        city_light(fr, *pos[name], r=3.2 if big else 2.2, strength=1.0)
    for name, dx, dy, anc in (('北京', 14, -46, 'la'), ('上海', 18, -10, 'la'), ('成都', -16, -12, 'ra')):
        fr.text((pos[name][0] + dx, pos[name][1] + dy), name, 'caption', 34, MIST, anchor=anc)
    fr.text((pos['广州'][0] - 16, pos['广州'][1] + 6), '广州', 'caption', 34, MIST, anchor='ra')
    # three social-post cards rising from cities (thin amber tether)
    for (name, cx, cy, ang, sd) in (('北京', 860, 640, -6, 1), ('成都', 200, 760, 5, 2), ('上海', 920, 1230, 4, 3)):
        sx, sy = pos[name]
        fr.d.line([(sx * S, sy * S), (cx * S, (cy + 80) * S)], fill=rgb(AMBER, 0.35), width=int(1.5 * S))
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
