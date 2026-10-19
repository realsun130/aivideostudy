#!/usr/bin/env python3
"""Motion cut v2 · full Frame-driven procedural animation.
Frame = f(frame). 24fps, 2064 frames, 1080×1920, silent.
S=1 for speed; multiprocessing; seeded RNG; hero frames = approved stills.
Usage: python3 render_motion_v2.py [--start N] [--end N] [--workers K]
"""
from __future__ import annotations
import argparse, math, os, sys, time, functools
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# --- force S=1 before importing drawing kit ---
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as C
C.S = 1
C._fc.clear()

from common import *
from cutouts import *
import render_stills as rs
from motion_lib import (
    RANGES, TOTAL, FPS, ease_in_out_quart, ease_out_cubic, ease_in_cubic,
    ease_out_quint, lerp, still as load_still, handoff_blend, light_point,
    soft_grain, zoom_at, night, fade, multiply_dark,
)

OUT_DIR = os.path.join(PROJ, 'out')
FRAMES = os.path.join(PROJ, 'frames_v2')
CACHE = os.path.join(PROJ, 'render', 'cache_v2')
os.makedirs(FRAMES, exist_ok=True)
os.makedirs(CACHE, exist_ok=True)

CREAM, MIST, AMBER, VEIL = P['paper_cream'], P['mist_grey'], P['ember_amber'], P['veil_moon']
SIDE = 80

# Hero local frames (match still composition exactly)
HERO = {1: 100, 2: 160, 3: 112, 4: 120, 5: 160, 6: 152, 7: 156, 8: 116, 9: 174}

# Handoff light anchors (screen px leaving shot N)
HANDOFF = {
    1: (540, 960), 2: (540, 1385), 3: (540, 960), 4: (540, 1270),
    5: (540, 960), 6: (650, 1125), 7: (540, 1000), 8: (540, 900),
}

# ---------- fast finish (no PNG optimize) ----------
_VIGNETTE = None

def _vignette_mask():
    global _VIGNETTE
    if _VIGNETTE is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / math.sqrt(2)
        vg = STYLE['vignette']
        _VIGNETTE = 1 - vg['strength'] * np.clip((r - (1 - vg['radius'])) / vg['radius'], 0, 1) ** 2
    return _VIGNETTE


def finish_fast(fr, path=None, frame_seed=0):
    base = np.asarray(fr.base, np.float32)
    light = np.asarray(fr.light, np.float32)
    out = np.clip(base + light * STYLE['glow']['intensity_max'] * 1.15, 0, 255).astype(np.uint8)
    img = Image.fromarray(out).convert('RGBA')
    img.alpha_composite(fr.top)
    img = img.convert('RGB')
    if img.size != (W, H):
        img = img.resize((W, H), Image.LANCZOS)
    arr = np.asarray(img, np.float32)
    arr *= _vignette_mask()[..., None]
    gr = STYLE['grain']
    g = np.random.default_rng(gr['seed'] + frame_seed).normal(0, 1, (H, W)).astype(np.float32)
    g = np.asarray(Image.fromarray(((g * 40) + 128).clip(0, 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(gr['blur_sigma_px'])), np.float32)
    g = (g - 128) / 40
    arr *= (1 + gr['amplitude'] * 0.85 * g)[..., None]
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    if path:
        img.save(path)  # no optimize
    return img


def cam_drift(lf, seed=0, amp=0.018):
    """Subtle continuous camera life: ±amp of frame (1–3%). Returns (dx, dy, scale)."""
    # slow periods so motion is always alive but never dizzy
    dx = amp * W * 0.55 * math.sin(2 * math.pi * lf / (7.5 * FPS) + seed * 0.7)
    dy = amp * H * 0.35 * math.sin(2 * math.pi * lf / (9.0 * FPS) + seed * 1.1)
    sc = 1.0 + amp * 0.4 * math.sin(2 * math.pi * lf / (11 * FPS) + seed)
    return dx, dy, sc


def apply_cam(img, dx, dy, sc, cx=W / 2, cy=H / 2):
    """No-op on full frames (text must stay pixel-stable). Camera life is applied
    upstream via Ortho cx/cy shifts and per-element offsets only."""
    return img


def text_alpha(fr_top_draw_fn, a):
    """Helper: call draw into a temp Frame.top then blend by a — used rarely."""
    pass


# ============================================================ caches
_CACHE = {}


def _map_plate(key, lon0, lat0, R, cx, cy, **kw):
    path = os.path.join(CACHE, f'map_{key}.png')
    if key in _CACHE:
        return _CACHE[key]
    if os.path.exists(path):
        im = Image.open(path).convert('RGB')
        _CACHE[key] = im
        return im
    fr = Frame(9000 + hash(key) % 1000)
    pr = Ortho(lon0, lat0, R, cx, cy)
    draw_map(fr, pr, **kw)
    # bake base only (no lights yet)
    im = fr.base.copy()
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    im.save(path)
    _CACHE[key] = im
    return im


def _town_latlons():
    if 'towns' in _CACHE:
        return _CACHE['towns'], _CACHE['hubs']
    rng = np.random.default_rng(101)
    m = land_mask()
    towns = []  # (lat, lon, weight, birth_order)
    hubs = []
    order = 0
    # small towns first
    for la, lo, k in rs.CITIES01:
        n = int(14 + 26 * k)
        sl = 0.55 + 0.75 * k
        lat = la + rng.normal(0, sl * 0.75, n)
        lon = lo + rng.normal(0, sl, n)
        # land check at default projection
        pr = Ortho(-35, 38, 460, 540, 990)
        x, y, v = pr.fwd(lon, lat)
        mi = ((90 - lat) / 180 * MH).astype(int).clip(0, MH - 1)
        mj = (((lon + 180) % 360) / 360 * MW).astype(int).clip(0, MW - 1)
        ok = v & m[mi, mj]
        for i in np.where(ok)[0]:
            towns.append((float(lat[i]), float(lon[i]), float(k) * 0.35, order))
            order += 1
        hubs.append((la, lo, k))
    # shuffle appearance order of towns with seed, but keep hubs for later
    rng2 = np.random.default_rng(202)
    idx = rng2.permutation(len(towns))
    towns = [towns[i] for i in idx]
    for i, t in enumerate(towns):
        towns[i] = (t[0], t[1], t[2], i)
    _CACHE['towns'] = towns
    _CACHE['hubs'] = hubs
    return towns, hubs


def fire_flicker(fr, x, y, size, seed, lf, embers=14):
    """Bonfire with independent 1.5–3 Hz flicker ±12% and rising embers."""
    rng = np.random.default_rng(seed)
    hz = 1.5 + (seed % 17) / 17 * 1.5
    phase0 = (seed % 100) / 100 * 2 * math.pi
    phase = phase0 + 2 * math.pi * hz * (lf / FPS)
    flick = 1.0 + 0.12 * math.sin(phase)
    # flame tongues with height modulated by flicker
    lay = Image.new('RGB', (W * S, H * S), (0, 0, 0))
    g = ImageDraw.Draw(lay)

    def tear(cx, cy, w, h, col):
        a = np.linspace(0, 2 * np.pi, 48)
        xs = cx + w * np.sin(a) * np.sin(a / 2) ** 1.4
        ys = cy - h * (0.5 + 0.5 * np.cos(a))
        g.polygon([(px * S, py * S) for px, py in zip(xs, ys)], fill=col)

    hmul = flick
    for k in range(4):
        ox = (k - 1.5) * 5.0 * size + rng.uniform(-1.5, 1.5) * size
        tear(x + ox, y, (6.5 + rng.uniform(0, 2)) * size,
             (26 + rng.uniform(0, 14)) * size * hmul, rgb(P['ember_deep']))
    for k in range(3):
        ox = (k - 1) * 4.0 * size + rng.uniform(-1, 1) * size
        tear(x + ox, y, (5 + rng.uniform(0, 1.5)) * size,
             (18 + rng.uniform(0, 10)) * size * hmul, rgb(P['ember_amber']))
    tear(x, y, 4.2 * size, 12 * size * hmul, rgb(P['ember_core']))
    g.line([((x - 12 * size) * S, (y + 2 * size) * S),
            ((x + 12 * size) * S, (y - 1 * size) * S)],
           fill=tuple(int(v * 0.5) for v in rgb(P['ember_deep'])),
           width=max(1, int(3 * size * S)))
    # scale light by flick
    arr = (np.asarray(lay, np.float32) * flick).clip(0, 255).astype(np.uint8)
    lay = Image.fromarray(arr)
    fr.add_light_image(lay)
    fr.add_light_image(lay, blur=3 * size)
    # rising embers: positions advance with lf
    for i in range(embers):
        life = ((lf * 2 + i * 17 + seed) % 48) / 48.0
        ex = x + rng.normal(0, 7 * size) + 3 * size * math.sin(life * 6 + i)
        ey = y - life * 70 * size
        er = rng.uniform(0.8, 1.8) * size * (1 - life * 0.6)
        a = (1 - life) * flick
        fr.circle(ex, ey, er, tuple(int(c * a) for c in rgb(P['ember_amber'])), light=True)
    fr.glow(x, y - 8 * size, 10 * size, P['ember_amber'], 16 * size, 0.55 * flick)
    fr.glow(x, y - 8 * size, 26 * size, P['ember_deep'], 34 * size, 0.30 * flick)
    return flick


def veil_ribbon(fr, lf, y0=560, amp=14, period=6 * FPS):
    """Procedural soft drifting moon-veil ribbon (no paste seams)."""
    drift = amp * math.sin(2 * math.pi * lf / period)
    veil = Image.new('RGB', (W * S, H * S), (0, 0, 0))
    vg = ImageDraw.Draw(veil)
    xs = np.linspace(-40, W + 40, 320)
    top = y0 + 22 * np.sin((xs + drift) / 160) + drift * 0.3
    bot = top + 70 + 18 * np.sin((xs + drift) / 90 + 1)
    vg.polygon([(a * S, b * S) for a, b in zip(xs, top)] +
               [(a * S, b * S) for a, b in zip(xs[::-1], bot[::-1])],
               fill=tuple(int(v * 0.10) for v in rgb(VEIL)))
    fr.add_light_image(veil, blur=14)
    for k in range(2):
        ys = 580 + k * 34 + 14 * np.sin((xs + drift) / 140 + k * 1.3) + 6 * np.sin((xs + drift) / 47 + k) + drift * 0.25
        pts = [(a * S, b * S) for a, b in zip(xs, ys)]
        fr.d.line(pts, fill=rgb(VEIL, 0.22 - 0.05 * k), width=int((2.2 - 0.5 * k) * S))


def city_light_bloom(fr, x, y, r, strength, bloom=1.0):
    """City light with ease-out bloom (bloom 0..1 during appear)."""
    s = strength * bloom
    if s <= 0.01:
        return
    city_light(fr, x, y, r=r, strength=s)
    if bloom < 1.0:
        # extra soft bloom ring that shrinks as it settles
        fr.glow(x, y, r * (4 + 8 * (1 - bloom)), P['ember_amber'], r * (10 + 14 * (1 - bloom)), 0.25 * (1 - bloom) * strength)


def glyph_widths(text, kind, size):
    """Return list of (char, width) and total width using Frame text metrics."""
    fr = Frame(0)
    widths = []
    for ch in text:
        widths.append((ch, fr.text_w(ch, kind, size)))
    return widths, sum(w for _, w in widths)


# ============================================================ SHOT 01
def anim_01(lf, dur, gframe):
    fr = Frame(1032 + lf)
    # camera: slow rotate lon0 by 6° over f0-36, then hold; push later
    if lf < 36:
        u = ease_in_out_quart(lf / 36)
        lon0 = -35 + 6 * u
    else:
        lon0 = -29
    # continuous life + push
    dx, dy, sc = cam_drift(lf, 1, amp=0.015)
    push = 1.0
    ireland_xy = None
    if lf >= 120:
        u = ease_in_out_quart((lf - 120) / max(1, dur - 120))
        push = lerp(1.0, 12.0, u)
        # fade text before / during push to avoid cropped glyphs at f143
    pr = Ortho(lon0, 38, 460 * (1 if push < 1.01 else 1), 540, 990)
    # For push we zoom after compose; map drawn at base scale
    draw_map(fr, pr)
    towns, hubs = _town_latlons()
    # appear: ~40 towns every frame starting f0, bloom 8f; big hubs f60-96; Ireland f96
    lit_pts = []
    bloom_pts = []
    for lat, lon, k, order in towns:
        birth = order // 40  # ~40 per frame
        age = lf - birth
        if age < 0:
            continue
        bloom = ease_out_cubic(min(1.0, age / 8.0))
        x, y, v = pr.fwd(np.array([lon]), np.array([lat]))
        if not v[0]:
            continue
        lit_pts.append((float(x[0]), float(y[0]), bloom * (0.55 + 0.45 * min(1, k + 0.5))))
    # batch draw small lights
    if lit_pts:
        lay = Image.new('RGB', (W * S, H * S), (0, 0, 0))
        g = ImageDraw.Draw(lay)
        for x, y, s in lit_pts:
            if s < 0.05:
                continue
            r = 1.25
            c = tuple(int(v * 0.75 * s) for v in rgb(P['ember_core']))
            g.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=c)
        fr.add_light_image(lay)
        fr.add_light_image(lay.filter(ImageFilter.GaussianBlur(4 * S)))
        # wide haze
        haz = Image.new('RGB', (W * S, H * S), (0, 0, 0))
        hg = ImageDraw.Draw(haz)
        for x, y, s in lit_pts[::3]:
            if s < 0.3:
                continue
            r = 2.0
            c = tuple(int(v * 0.22 * s) for v in rgb(P['ember_amber']))
            hg.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=c)
        fr.add_light_image(haz, blur=26)

    # big city hubs last
    for i, (la, lo, k) in enumerate(hubs):
        if k < 0.8:
            continue
        birth = 60 + int((i / max(1, len(hubs))) * 36)
        age = lf - birth
        if age < 0:
            continue
        bloom = ease_out_cubic(min(1.0, age / 10.0))
        x, y, v = pr.fwd(np.array([lo]), np.array([la]))
        if v[0]:
            city_light_bloom(fr, float(x[0]), float(y[0]), r=2.2 + 1.6 * k, strength=1.0, bloom=bloom)

    # limb
    fr.d.ellipse([(540 - 461) * S, (990 - 461) * S, (540 + 461) * S, (990 + 461) * S],
                 outline=rgb(VEIL, 0.30), width=int(2 * S))
    # Ireland ring last
    x, y, _ = pr.fwd(np.array([-7.5]), np.array([53.4]))
    ix, iy = float(x[0]), float(y[0])
    ireland_xy = (ix, iy)
    ire_age = lf - 96
    if ire_age >= 0:
        u = ease_out_cubic(min(1.0, ire_age / 12.0))
        fr.glow(ix, iy, 5, P['ember_core'], 5, 1.0 * u)
        fr.glow(ix, iy, 12, AMBER, 18, 0.6 * u)
        fr.glow(ix, iy, 30, P['ember_deep'], 40, 0.35 * u)
        fr.d.ellipse([(ix - 26) * S, (iy - 26) * S, (ix + 26) * S, (iy + 26) * S],
                     outline=rgb(AMBER, 0.85 * u), width=int(2 * S))
        fr.d.ellipse([(ix - 44) * S, (iy - 44) * S, (ix + 44) * S, (iy + 44) * S],
                     outline=rgb(AMBER, 0.35 * u), width=int(1.5 * S))

    # text: stable positions; fade out before push (f110+) so f143 has no cropped glyphs
    text_a = 1.0
    if lf >= 110:
        text_a = max(0.0, 1.0 - (lf - 110) / 10.0)
    if text_a > 0.02:
        fr.text((540, 260), '10月31日', 'headline', 96, CREAM, anchor='ma', a=text_a)
        fr.text((540, 400), '一个夜晚，怎么走到了你身边？', 'body', 52, CREAM, anchor='ma', a=text_a)
        fr.text((540, 1500), '万圣节的历史演变', 'caption', 38, AMBER, anchor='ma', a=text_a)
        if text_a > 0.5:
            rs.rule(fr, 420, 660, 1565, AMBER, 0.6 * text_a)

    img = finish_fast(fr, frame_seed=gframe)
    # camera drift on content (text already baked — acceptable small drift on text during early; push overrides)
    if lf < 110:
        img = apply_cam(img, dx, dy, sc, 540, 990)
    if lf >= 120:
        u = ease_in_out_quart((lf - 120) / max(1, dur - 120))
        scale = lerp(1.0, 12.0, u)
        img = zoom_at(img, ix, iy, scale)
        if u > 0.55:
            img = light_point(img, W / 2, H / 2, 10 + 50 * (u - 0.55) / 0.45, strength=0.5 + 0.5 * u)
    return img


# ============================================================ SHOT 02
FIRES02 = [(53.62, -6.89, 1.25), (54.65, -6.6, 0.9), (54.95, -7.6, 0.8), (57.15, -4.6, 1.0),
           (57.6, -5.6, 0.85), (56.7, -4.0, 0.9), (54.23, -4.55, 0.85), (52.9, -3.75, 0.8)]


def anim_02(lf, dur, gframe):
    fr = Frame(1033 + lf)
    # pan down toward Tlachtga at end
    cy = 1000
    if lf >= 380 - 144:
        u = ease_in_out_quart((lf - (380 - 144)) / max(1, dur - (380 - 144)))
        cy = lerp(1000, 1180, u)
    dx, dy, sc = cam_drift(lf, 2, amp=0.012)
    pr = Ortho(-5.6, 55.0, 5600, 600 + dx * 0.02, cy + dy * 0.02)
    draw_map(fr, pr, dot_spacing=10, dot_r=2.0, coast=True, graticule=True, disk=False, region=(0, 0, W, H))
    fr.scrim(200, 470, 0.75)
    fr.scrim(1420, 1580, 0.7)
    veil_ribbon(fr, lf)
    # ignite every 3 frames
    for i, (la, lo, s) in enumerate(FIRES02):
        birth = 18 + i * 3
        if lf < birth:
            continue
        age = lf - birth
        appear = ease_out_cubic(min(1.0, age / 8.0))
        x, y, _ = pr.fwd(np.array([lo]), np.array([la]))
        # temporarily scale glow via flicker fn; multiply appear into glow by drawing then...
        fire_flicker(fr, float(x[0]), float(y[0]), size=s * (0.7 + 0.3 * appear), seed=200 + i, lf=lf, embers=14)
    x, y, _ = pr.fwd(np.array([-6.89]), np.array([53.62]))
    fr.text((x[0] - 26, y[0] + 6), 'Tlachtga 山', 'caption', 34, MIST, anchor='ra')
    rs.headline_block(fr, 220, '爱尔兰 · 苏格兰', '萨温节 Samhain')
    fr.text((SIDE, 400), '冬天开始的那一夜', 'body', 48, MIST)
    fr.text((SIDE, 1440), '人们点起山顶的篝火，相信这一夜\n生者与亡者之间的那层纱，最薄', 'body', 46, CREAM)
    img = finish_fast(fr, frame_seed=gframe)
    img = apply_cam(img, dx * 0.3, dy * 0.3, sc, 540, 1000)
    # outgoing light at Tlachtga
    if lf >= 380 - 144:
        u = ease_in_out_quart((lf - (380 - 144)) / max(1, dur - (380 - 144)))
        img = light_point(img, 540, lerp(1200, 1385, u), 12 + 20 * u, strength=0.4 + 0.5 * u)
    return img


# ============================================================ SHOT 03
def anim_03(lf, dur, gframe):
    fr = Frame(1034 + lf)
    dx, dy, sc = cam_drift(lf, 3, amp=0.01)
    # fire first (bottom) so rim light syncs
    flick = fire_flicker(fr, 540, 1385, size=2.0, seed=303, lf=lf, embers=16)
    for i, (name, x, kw, inv, lo, lab) in enumerate(rs.MASKS03):
        start = i * 12
        if lf < start:
            continue
        u = ease_out_cubic(min(1.0, (lf - start) / 14))
        rise = (1 - u) * 40  # gentle rise
        bottom = 1035 - rise
        # opacity via paste strength: draw full then we can't easily alpha — use rise only + early skip
        rs.mask_cut(fr, name, x + dx * 0.02, bottom + dy * 0.02, invert=inv, lo=lo, **kw)
        # flicker rim boost: extra glow under mask
        fr.glow(x, 1035 - 40, 20, AMBER, 30, 0.08 * flick * u)
        lab_a = u
        if lab_a > 0.3:
            fr.text((x, 1075), lab, 'caption', 34, MIST, anchor='ma', spacing=10, a=lab_a)
    rs.rule(fr, SIDE, W - SIDE, 1240, MIST, 0.35)
    for x in (225, 540, 860):
        fr.circle(x, 1240, 5, rgb(AMBER))
    rs.headline_block(fr, 220, '伪装', '戴上面具')
    fr.text((SIDE, 400), '让游荡的亡灵，认不出你', 'body', 50, CREAM)
    fr.text((SIDE, 1450), '这一说法来自民俗传说，学界并无定论', 'caption', 34, MIST)
    img = finish_fast(fr, frame_seed=gframe)
    return apply_cam(img, dx * 0.25, dy * 0.25, sc, 540, 900)


# ============================================================ SHOT 04
def anim_04(lf, dur, gframe):
    fr = Frame(1035 + lf)
    dx, dy, sc = cam_drift(lf, 4, amp=0.01)
    # manuscript
    lat = 'In Kalendis Novembris · festivitas omnium sanctorum · '
    tm = Image.new('L', (W * S, H * S), 0)
    td = ImageDraw.Draw(tm)
    for i, y in enumerate(range(520, 980, 44)):
        rs.rule(fr, 40, W - 40, y + 36, '#2C4260', 0.35, 1.0)
        off = (i * 137) % 400
        td.text((40 * S - off * S, y * S), lat * 3, font=font('latin_italic', 30), fill=255)
    tm = Image.fromarray((np.asarray(tm, np.float32) * 0.06).astype(np.uint8))
    fr.base.paste(Image.new('RGB', tm.size, rgb(CREAM)), (0, 0), tm)
    fr.d = ImageDraw.Draw(fr.base, 'RGBA')
    pool = Image.new('RGB', (W * S, H * S), (0, 0, 0))
    pg = ImageDraw.Draw(pool)
    pg.ellipse([440 * S, 620 * S, 1160 * S, 1180 * S], fill=tuple(int(v * 0.15) for v in rgb(AMBER)))
    fr.add_light_image(pool, blur=90)

    cards = [
        (70, 560, 280, 330, '10月', '31', '前夜', 41, False),
        (380, 520, 320, 410, '11月', '1', '万圣节', 42, True),
        (730, 560, 280, 330, '11月', '2', '万灵节', 43, False),
    ]
    for i, (x, y, w, h, top, big, sub, seed, hot) in enumerate(cards):
        start = i * 6
        if lf < start:
            continue
        u = ease_out_cubic(min(1.0, (lf - start) / 10))
        # spring-ish overshoot
        drop = lerp(-90, 0, u) + (8 * math.sin(u * math.pi) if u < 1 else 0) * 0.3
        rs.parch_card(fr, x, y + drop, w, h, top, big, sub, seed=seed, hot=hot)

    # candle flicker 2–3 Hz ±8%
    hz = 2.5
    flick = 1.0 + 0.08 * math.sin(2 * math.pi * hz * lf / FPS)
    # draw candle with scaled glow via temporary — use rs.candle then multiply light region
    rs.candle(fr, 935, 1045, 1.0)
    # word chain with per-glyph collapse
    # Timeline: hold all three → collapse All Hallows' Eve glyphs → then Hallowe'en → then Halloween → light
    y0 = 1030
    words = [("All Hallows' Eve", MIST, 48), ("Hallowe'en", MIST, 54), ('Halloween', CREAM, 72)]
    # collapse starts at lf = dur - 72
    collapse0 = dur - 72
    # phases: 0-24 collapse word0 glyph by glyph; 24-40 collapse word1; 40-56 collapse word2 into point; 56-72 point grows
    for wi, (wtxt, col, sz) in enumerate(words):
        # draw arrows between
        if wi < 2:
            fr.text((540, y0 + wi * 120 + 78), '↓', 'caption', 34, AMBER, anchor='ma')
        widths, total = glyph_widths(wtxt, 'latin_italic', sz)
        x_left = 540 - total / 2
        # how many glyphs still visible
        if lf < collapse0:
            n_hide = 0
        else:
            tcol = lf - collapse0
            if wi == 0:
                n_hide = min(len(wtxt), max(0, tcol // 1))  # 1 frame per glyph
            elif wi == 1:
                n_hide = min(len(wtxt), max(0, (tcol - 24) // 1)) if tcol >= 24 else 0
            else:
                # Halloween: after word1 gone, glyphs condense (fade+move to center) over 16f then point
                n_hide = 0
                if tcol >= 40:
                    # fade whole word toward center
                    u = min(1.0, (tcol - 40) / 16)
                    # draw shrinking toward center as light
                    if u < 1:
                        fr.text((540, y0 + wi * 120), wtxt, 'latin_italic', max(12, int(sz * (1 - 0.7 * u))),
                                col, anchor='ma', a=1 - u)
                    continue
                else:
                    n_hide = 0
        # draw remaining glyphs
        x = x_left
        for gi, (ch, cw) in enumerate(widths):
            if gi < n_hide:
                # falling glyph
                age = 1
                if wi == 0 and lf >= collapse0:
                    age = lf - collapse0 - gi
                elif wi == 1 and lf >= collapse0 + 24:
                    age = lf - collapse0 - 24 - gi
                fall = min(40, age * 3)
                fa = max(0, 1 - age / 8)
                if fa > 0.05:
                    fr.text((x + cw / 2, y0 + wi * 120 + fall), ch, 'latin_italic', sz, col, anchor='ma', a=fa)
            else:
                fr.text((x + cw / 2, y0 + wi * 120), ch, 'latin_italic', sz, col, anchor='ma')
            x += cw

    # final light point from Halloween
    if lf >= collapse0 + 56:
        u = (lf - collapse0 - 56) / max(1, dur - collapse0 - 56)
        fr.glow(540, 1270, lerp(8, 40, u), P['ember_core'], 12, 1.0)
        fr.glow(540, 1270, lerp(20, 80, u), AMBER, 40, 0.6)

    rs.headline_block(fr, 220, '公元 9 世纪', '教会定下 11月1日')
    fr.text((SIDE, 400), '“万圣节”的前一晚，就是今天的万圣夜', 'body', 46, CREAM)
    fr.text((SIDE, 1440), "835年起，11月1日成为整个法兰克帝国的诸圣节\n“Halloween”源自苏格兰对 All Hallows' Eve 的缩写", 'caption', 34, MIST)
    img = finish_fast(fr, frame_seed=gframe)
    # apply candle flick globally mild
    if abs(flick - 1) > 0.01:
        arr = np.asarray(img, np.float32)
        # only warm region
        arr[500:1100, 850:1000] = np.clip(arr[500:1100, 850:1000] * flick, 0, 255)
        img = Image.fromarray(arr.astype(np.uint8))
    img = apply_cam(img, dx * 0.2, dy * 0.2, sc, 540, 800)
    if lf >= collapse0 + 56:
        u = (lf - collapse0 - 56) / max(1, dur - collapse0 - 56)
        img = light_point(img, 540, 1270, lerp(10, 55, u), strength=0.5 + 0.5 * u)
        if u > 0.5:
            img = multiply_dark(img, 1 - 0.55 * (u - 0.5) / 0.5)
            img = light_point(img, 540, 1270, 30, strength=1.0)
    return img


# ============================================================ SHOT 05
def _routes05(pr):
    srcs = [(51.9, -8.47), (53.35, -6.26), (53.41, -2.98)]
    dsts = [(40.71, -74.0), (42.36, -71.06), (46.81, -71.21), (39.95, -75.17)]
    routes = []
    for si, s in enumerate(srcs):
        for di, t in enumerate(dsts):
            x0, y0, _ = pr.fwd(np.array([s[1]]), np.array([s[0]]))
            x1, y1, _ = pr.fwd(np.array([t[1]]), np.array([t[0]]))
            bulge = 0.07 + 0.06 * di + 0.025 * si
            ax, ay = arc_pts(float(x0[0]), float(y0[0]), float(x1[0]), float(y1[0]), bulge, n=160)
            routes.append((ax, ay))
    return routes, srcs, dsts


def anim_05(lf, dur, gframe):
    fr = Frame(1036 + lf)
    dx, dy, sc = cam_drift(lf, 5, amp=0.012)
    pr = Ortho(-40, 47, 860, 540 + dx * 0.01, 1000 + dy * 0.01)
    draw_map(fr, pr, dot_spacing=11, coast=True, graticule=True, disk=False, region=(0, 0, W, H))
    routes, srcs, dsts = _routes05(pr)
    # faint arc guides
    for ax, ay in routes:
        fr.d.line([(a * S, b * S) for a, b in zip(ax, ay)], fill=rgb(AMBER, 0.14), width=int(1.2 * S))
    # 1000 particles, staggered departures from f20, ~4/frame
    rng = np.random.default_rng(55)
    n_part = 1000
    # pre-assign route & speed & lateral
    lay = Image.new('RGB', (W * S, H * S), (0, 0, 0))
    trail = Image.new('RGB', (W * S, H * S), (0, 0, 0))
    g = ImageDraw.Draw(lay)
    tg = ImageDraw.Draw(trail)
    arrived = []
    for i in range(n_part):
        birth = 20 + i // 4
        age = lf - birth
        if age < 0:
            continue
        route = routes[i % 12]
        ax, ay = route
        speed = 0.010 + (i % 9) * 0.0012  # fraction of arc per frame ≈ 120-220 px/s
        t = age * speed
        lat = (rng.normal(0, 1.6) if False else ((i * 37) % 17 - 8) * 0.25)  # deterministic jitter
        if t >= 1.0:
            # stay at destination
            x, y = ax[-1] + lat, ay[-1] + lat * 0.5
            arrived.append((x, y))
            g.ellipse([x - 1.4, y - 1.4, x + 1.4, y + 1.4], fill=rgb(P['ember_core']))
            continue
        idx = t * (len(ax) - 1)
        i0 = int(idx); i1 = min(len(ax) - 1, i0 + 1); u = idx - i0
        x = ax[i0] * (1 - u) + ax[i1] * u + lat
        y = ay[i0] * (1 - u) + ay[i1] * u + lat * 0.4
        # trail: previous positions
        for k in range(1, 6):
            tt = t - k * speed * 0.8
            if tt < 0:
                break
            jdx = tt * (len(ax) - 1)
            j0 = int(jdx); j1 = min(len(ax) - 1, j0 + 1); uu = jdx - j0
            tx = ax[j0] * (1 - uu) + ax[j1] * uu + lat
            ty = ay[j0] * (1 - uu) + ay[j1] * uu + lat * 0.4
            a = 0.35 * (1 - k / 6)
            c = tuple(int(v * a) for v in rgb(AMBER))
            tg.ellipse([tx - 1.0, ty - 1.0, tx + 1.0, ty + 1.0], fill=c)
        g.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=rgb(P['ember_core']))
    fr.add_light_image(trail, blur=1.5)
    fr.add_light_image(lay)
    fr.add_light_image(lay, blur=3)
    fr.scrim(200, 470, 0.75)
    fr.scrim(1420, 1580, 0.7)
    for la, lo in dsts[:2]:
        x, y, _ = pr.fwd(np.array([lo]), np.array([la]))
        city_light(fr, float(x[0]), float(y[0]), 3.2)
    for la, lo in srcs[:2]:
        x, y, _ = pr.fwd(np.array([lo]), np.array([la]))
        city_light(fr, float(x[0]), float(y[0]), 2.6, 0.8)
    x, y, _ = pr.fwd(np.array([-74.0]), np.array([40.71]))
    fr.text((x[0] - 10, y[0] + 14), '纽约', 'caption', 34, MIST, anchor='ra')
    x, y, _ = pr.fwd(np.array([-8.0]), np.array([53.0]))
    fr.text((x[0] + 6, y[0] + 40), '爱尔兰', 'caption', 34, MIST, anchor='ma')
    rs.headline_block(fr, 220, '1845–1852 · 爱尔兰大饥荒', '一百万人离开')
    fr.text((SIDE, 400), '他们把万圣节，也带上了船', 'body', 50, CREAM)
    fr.text((SIDE, 1440), '约100万人死于饥荒，另有100多万人移民，多数去了北美\n画面中每个光点 ≈ 1000 人', 'caption', 34, MIST)
    img = finish_fast(fr, frame_seed=gframe)
    img = apply_cam(img, dx * 0.25, dy * 0.25, sc, 540, 1000)
    # out: push NY ×3
    out0 = dur - 36
    if lf >= out0:
        u = ease_in_out_quart((lf - out0) / 36)
        x, y, _ = Ortho(-40, 47, 860, 540, 1000).fwd(np.array([-74.0]), np.array([40.71]))
        img = zoom_at(img, float(x[0]), float(y[0]), lerp(1.0, 3.0, u))
        img = light_point(img, W / 2, H / 2, lerp(8, 40, u), strength=0.4 + 0.6 * u)
    return img


# ============================================================ SHOT 06 — morph without dark bands
def _lantern_rgba(name, width, body_stops, hot_thr, seed_blur):
    """Pre-render lantern to RGBA at S=1."""
    col, a = load_cut(name, width=width)
    a = soften_alpha(a, 0.6)
    L = lum(col)
    r, g, b = col[..., 0], col[..., 1], col[..., 2]
    hot = np.clip((L - hot_thr) / 40, 0, 1) * np.clip((r - b - 40) / 60, 0, 1) * a
    hot = np.asarray(Image.fromarray((hot * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6 * S)), np.float32) / 255
    t = norm_l(L, a)
    body = ramp(t, body_stops)
    tone = body * (1 - hot[..., None]) + np.array(rgb(P['ember_deep']), np.float32) * hot[..., None]
    core = hot[..., None] * np.array(rgb(P['ember_core']), np.float32)[None, None]
    rgba = np.concatenate([tone, a[..., None] * 255], axis=-1).astype(np.uint8)
    light = core.astype(np.uint8)
    return Image.fromarray(rgba, 'RGBA'), Image.fromarray(light, 'RGB'), a.shape


def anim_06(lf, dur, gframe):
    fr = Frame(1037 + lf)
    dx, dy, sc = cam_drift(lf, 6, amp=0.012)
    # load lanterns once per process
    if 'turnip_rgba' not in _CACHE:
        tr, tl, _ = _lantern_rgba('turnip.png', 250, [(0, '#1E2433'), (0.55, '#968A8E'), (1, '#E2D8C4')], 140, 8)
        pr, pl, _ = _lantern_rgba('pumpkin.png', 380, [(0, '#2A160E'), (0.40, '#8A3C1A'), (1, '#D9793A')], 150, 12)
        _CACHE['turnip_rgba'] = tr
        _CACHE['turnip_light'] = tl
        _CACHE['pump_rgba'] = pr
        _CACHE['pump_light'] = pl
    turnip = _CACHE['turnip_rgba']
    pumpkin = _CACHE['pump_rgba']
    tlight = _CACHE['turnip_light']
    plight = _CACHE['pump_light']

    # path arc from turnip center to pumpkin center
    x0, y0 = 290, 770
    x1, y1 = 650, 1125
    ax, ay = arc_pts(x0, y0, x1, y1, -0.22, n=80)

    def paste_lantern(fr, rgba, light, cx, cy, scale=1.0, alpha=1.0):
        im = rgba
        li = light
        if abs(scale - 1) > 0.01:
            nw, nh = int(im.width * scale), int(im.height * scale)
            im = im.resize((nw, nh), Image.LANCZOS)
            li = li.resize((nw, nh), Image.LANCZOS)
        if alpha < 0.99:
            a = np.asarray(im, np.float32)
            a[..., 3] *= alpha
            im = Image.fromarray(a.astype(np.uint8))
            li = Image.fromarray((np.asarray(li, np.float32) * alpha).astype(np.uint8))
        x0p = int((cx - im.width / (2 * S)) * S)
        y0p = int((cy - im.height / (2 * S)) * S)
        fr.base.paste(im, (x0p, y0p), im)
        fr.d = ImageDraw.Draw(fr.base, 'RGBA')
        # light
        lay = Image.new('RGB', (W * S, H * S), (0, 0, 0))
        lay.paste(li, (x0p, y0p))
        fr.add_light_image(lay)
        fr.add_light_image(lay, blur=8)

    if lf < 48:
        # only turnip, with slight bob
        bob = 3 * math.sin(2 * math.pi * lf / (2.5 * FPS))
        paste_lantern(fr, turnip, tlight, x0 + dx * 0.05, y0 + bob + dy * 0.05, 1.0, 1.0)
        fr.text((290, 905), '芜菁灯\n爱尔兰/苏格兰传统', 'caption', 34, MIST, anchor='ma', spacing=8)
        # faint arc dots ahead
        for i in range(0, 40, 4):
            fr.circle(ax[i], ay[i], 2.0, rgb(AMBER, 0.15))
    elif lf < 120:
        u = ease_in_out_quart((lf - 48) / 72)
        # position along arc
        idx = u * (len(ax) - 1)
        i0 = int(idx); i1 = min(len(ax) - 1, i0 + 1); uu = idx - i0
        cx = ax[i0] * (1 - uu) + ax[i1] * uu
        cy = ay[i0] * (1 - uu) + ay[i1] * uu
        # scale: turnip 1.0 → pumpkin size ratio ~380/250
        sc_t = lerp(1.0, 0.55, u)
        sc_p = lerp(0.55, 1.0, u)
        # crossfade alphas — NO vertical dark bands
        a_t = 1.0 - u
        a_p = u
        paste_lantern(fr, turnip, tlight, cx, cy, sc_t, a_t)
        paste_lantern(fr, pumpkin, plight, cx, cy, sc_p, a_p)
        # glow bridge
        fr.glow(cx, cy, 18 + 20 * u, AMBER, 28, 0.35)
        fr.glow(cx, cy, 8, P['ember_core'], 10, 0.7)
        # arc breadcrumbs
        for i in range(0, int(u * 80), 3):
            fr.circle(ax[i], ay[i], 2.2, rgb(AMBER, 0.25 + 0.5 * i / 80))
        if u < 0.5:
            fr.text((290, 905), '芜菁灯\n爱尔兰/苏格兰传统', 'caption', 34, MIST, anchor='ma', spacing=8, a=1 - u * 2)
        if u > 0.45:
            fr.text((650, 1330), '南瓜灯 · 美国', 'caption', 34, CREAM, anchor='ma', a=(u - 0.45) / 0.55)
    else:
        paste_lantern(fr, pumpkin, plight, x1, y1, 1.0, 1.0)
        pool = Image.new('RGB', (W * S, H * S), (0, 0, 0))
        pg = ImageDraw.Draw(pool)
        pg.ellipse([(650 - 230) * S, (1125 + 80) * S, (650 + 230) * S, (1125 + 140) * S],
                   fill=tuple(int(v * 0.30) for v in rgb(AMBER)))
        fr.add_light_image(pool, blur=18)
        fr.text((650, 1330), '南瓜灯 · 美国', 'caption', 34, CREAM, anchor='ma')
        # subtle flicker
        flick = 1.0 + 0.06 * math.sin(2 * math.pi * 2.2 * lf / FPS)
        fr.glow(x1, y1, 20, AMBER, 30, 0.15 * flick)

    rs.headline_block(fr, 220, '灯，换了', '芜菁 → 南瓜')
    fr.text((SIDE, 400), '在家乡，灯是用芜菁刻的\n到了美洲，换成了更大的南瓜', 'body', 46, CREAM)
    fr.text((SIDE, 1440), "1837年，美国英语首次把南瓜灯叫作 jack-o'-lantern\n（据《牛津英语词典》）", 'caption', 34, MIST)
    img = finish_fast(fr, frame_seed=gframe)
    img = apply_cam(img, dx * 0.2, dy * 0.2, sc, 470, 950)
    out0 = dur - 20
    if lf >= out0:
        u = ease_in_cubic((lf - out0) / 20)
        img = light_point(img, 650, 1125, lerp(14, 90, u), strength=0.4 + 0.5 * u)
        img = fade(img, 1 - 0.25 * u)
    return img


# ============================================================ SHOT 07
def anim_07(lf, dur, gframe):
    fr = Frame(1038 + lf)
    dx, dy, sc = cam_drift(lf, 7, amp=0.014)
    pr = Ortho(-50, 38, 450, 540, 900)
    draw_map(fr, pr, graticule=True)
    rng = np.random.default_rng(77)
    hubs = [(40.71, -74.0, 60), (42.36, -71.06, 30), (41.88, -87.63, 40), (34.05, -118.24, 40),
            (29.76, -95.37, 25), (33.75, -84.39, 25), (39.95, -75.17, 25), (47.6, -122.33, 15),
            (39.74, -104.99, 15), (43.65, -79.38, 25), (45.5, -73.57, 15), (25.76, -80.19, 20),
            (44.98, -93.27, 15), (38.63, -90.2, 15), (36.17, -86.78, 12), (32.78, -96.8, 20),
            (49.28, -123.12, 10), (19.43, -99.13, 12)]
    # particle count scales with timeline rows
    row_starts = [14, 50, 86, 122]
    n_mul = 1
    for rs_ in row_starts:
        if lf >= rs_:
            n_mul *= 2
    n_mul = min(n_mul, 16)
    pts = []
    for la, lo, n in hubs:
        nn = max(1, int(n * n_mul / 8))
        for j in range(nn):
            pulse = 0.75 + 0.25 * math.sin(2 * math.pi * (lf / FPS) * 1.2 + j * 0.4)
            x, y, v = pr.fwd(np.array([lo + rng.normal(0, 1.6)]), np.array([la + rng.normal(0, 1.2)]))
            if v[0]:
                pts.append((float(x[0]), float(y[0]), pulse))
    if pts:
        lay = Image.new('RGB', (W * S, H * S), (0, 0, 0))
        g = ImageDraw.Draw(lay)
        for x, y, pulse in pts:
            r = 1.5
            c = tuple(int(v * 0.8 * pulse) for v in rgb(P['ember_core']))
            g.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=c)
        fr.add_light_image(lay)
        fr.add_light_image(lay, blur=4)

    # arcs draw out from NA to Europe, 36f each, traveling head
    x0, y0, _ = pr.fwd(np.array([-95.0]), np.array([38.0]))
    dests = [(51.5, -0.12), (48.85, 2.35), (59.33, 18.07), (40.42, -3.70), (41.0, 28.97)]
    for k, (la, lo) in enumerate(dests):
        start = 30 + k * 36
        age = lf - start
        if age < 0:
            continue
        u = ease_out_cubic(min(1.0, age / 36))
        x1, y1, v = pr.fwd(np.array([lo]), np.array([la]))
        ax, ay = arc_pts(float(x0[0]), float(y0[0]), float(x1[0]), float(y1[0]), -0.22, n=100)
        n_draw = max(2, int(u * len(ax)))
        fr.d.line([(a * S, b * S) for a, b in zip(ax[:n_draw], ay[:n_draw])],
                  fill=rgb(AMBER, 0.35), width=int(2 * S))
        # traveling head
        hx, hy = ax[n_draw - 1], ay[n_draw - 1]
        fr.glow(hx, hy, 5, P['ember_core'], 6, 0.9)
        fr.glow(hx, hy, 12, AMBER, 16, 0.4)
        if u >= 1:
            city_light(fr, float(x1[0]), float(y1[0]), 2.4, 0.8)

    rs.headline_block(fr, 220, '20世纪 · 北美', '不给糖就捣蛋')
    fr.scrim(1380, 1600, 0.7)
    items = [('1917', '“trick or treat” 首次见报（加拿大）'), ('1950s', '讨糖成为全美孩子的夜晚'),
             ('2023', '美国万圣节消费预计 122 亿美元'), ('今天', '电影、电视、互联网，把它带向世界')]
    for i, (yr, s) in enumerate(items):
        start = row_starts[i]
        if lf < start:
            continue
        u = ease_out_cubic(min(1.0, (lf - start) / 10))
        y = 1400 + i * 54
        # slide up slightly
        yy = y + (1 - u) * 16
        fr.text((SIDE, yy), yr, 'caption', 34, AMBER, a=u)
        fr.text((SIDE + 120, yy), s, 'caption', 34, CREAM, a=u)

    img = finish_fast(fr, frame_seed=gframe)
    img = apply_cam(img, dx * 0.25, dy * 0.25, sc, 540, 900)
    out0 = dur - 24
    if lf >= out0:
        u = ease_in_out_quart((lf - out0) / 24)
        img = fade(img, 1 - 0.85 * u)
        img = light_point(img, 540, lerp(900, 1000, u), lerp(8, 36, u), strength=0.5 + 0.5 * u)
    return img


# ============================================================ SHOT 08
def anim_08(lf, dur, gframe):
    fr = Frame(1039 + lf)
    dx, dy, sc = cam_drift(lf, 8, amp=0.016)
    # parallax: far layer drifts less
    rng = np.random.default_rng(808)
    d = fr.d
    lay = Image.new('RGB', (W * S, H * S), (0, 0, 0))
    g = ImageDraw.Draw(lay)
    warm = [P['ember_core'], P['ember_amber'], '#E8C38A']
    # far buildings
    x = -20 + dx * 0.15
    while x < W + 20:
        bw = rng.uniform(70, 140)
        top = rng.uniform(820, 980) + dy * 0.1
        d.rectangle([x * S, top * S, (x + bw) * S, H * S], fill=rgb('#0F1A2B'))
        for wy in np.arange(top + 14, 1380, 18):
            for wx in np.arange(x + 8, x + bw - 10, 14):
                if rng.uniform() < 0.12:
                    c = tuple(int(v * 0.35) for v in rgb(warm[rng.integers(3)]))
                    g.rectangle([wx * S, wy * S, (wx + 7) * S, (wy + 9) * S], fill=c)
        x += bw + rng.uniform(4, 14)

    blocks = [(-10, 150, 700), (150, 175, 860), (335, 140, 760), (485, 190, 640),
              (690, 150, 880), (850, 120, 720), (978, 130, 800)]
    # seeded random order for windows turning on (not L→R)
    win_list = []
    for bi, (bx, bw, top) in enumerate(blocks):
        bx2 = bx + dx * 0.35
        top2 = top + dy * 0.25
        d.rectangle([bx2 * S, top2 * S, (bx2 + bw) * S, H * S], fill=rgb('#101C2E'))
        d.line([(bx2 * S, top2 * S), ((bx2 + bw) * S, top2 * S)], fill=rgb('#22344E'), width=int(2 * S))
        ww, wh, gx, gy = 16, 22, 10, 14
        cols = int((bw - 24) // (ww + gx))
        x0 = bx2 + (bw - (cols * (ww + gx) - gx)) / 2
        for r, wy in enumerate(np.arange(top2 + 24, 1400, wh + gy)):
            for c in range(cols):
                wx = x0 + c * (ww + gx)
                win_list.append((bi, wx, wy, ww, wh, r, c))
                d.rectangle([wx * S, wy * S, (wx + ww) * S, (wy + wh) * S], fill=rgb('#0B1422'))

    # turn-on order seeded
    rng_on = np.random.default_rng(909)
    order = rng_on.permutation(len(win_list))
    # ~24% eventually lit; stagger
    n_lit_target = int(len(win_list) * 0.24)
    for rank, oi in enumerate(order[:n_lit_target]):
        birth = 12 + (rank * 2) // max(1, n_lit_target // 80)  # spread over ~80f
        if lf < birth:
            continue
        bi, wx, wy, ww, wh, r, c = win_list[oi]
        age = lf - birth
        bloom = ease_out_cubic(min(1.0, age / 6.0))
        k = 0.45 + 0.35 * bloom
        # fewer low floors
        if wy > 1200:
            k *= 0.55
        col = tuple(int(v * k) for v in rgb(warm[oi % 3]))
        d.rectangle([wx * S, wy * S, (wx + ww) * S, (wy + wh) * S], fill=tuple(int(v * 0.55) for v in col))
        g.rectangle([wx * S, wy * S, (wx + ww) * S, (wy + wh) * S], fill=tuple(int(v * 0.55 * bloom) for v in col))

    # pumpkin windows with flicker
    pumpkins = []
    for bx, bw, top, frac, row in ((150, 175, 860, 0.3, 4), (335, 140, 760, 0.7, 9), (485, 190, 640, 0.5, 6),
                                   (690, 150, 880, 0.25, 3), (850, 120, 720, 0.6, 12), (-10, 150, 700, 0.6, 7),
                                   (978, 130, 800, 0.4, 5), (485, 190, 640, 0.2, 15)):
        bx2 = bx + dx * 0.35
        top2 = top + dy * 0.25
        ww, wh, gx, gy = 16, 22, 10, 14
        cols = int((bw - 24) // (ww + gx))
        x0 = bx2 + (bw - (cols * (ww + gx) - gx)) / 2
        c = int(frac * (cols - 1))
        wx = x0 + c * (ww + gx)
        wy = top2 + 24 + row * (wh + gy)
        flick = 1.0 + 0.10 * math.sin(2 * math.pi * (1.8 + (frac * 3) % 1.2) * lf / FPS + row)
        d.rectangle([wx * S, wy * S, (wx + ww) * S, (wy + wh) * S], fill=rgb('#4A2512'))
        g.rectangle([wx * S, wy * S, (wx + ww) * S, (wy + wh) * S],
                    fill=tuple(int(v * 0.30 * flick) for v in rgb(P['ember_deep'])))
        pcx, pcy = wx + ww / 2, wy + wh - 7
        d.ellipse([(pcx - 7) * S, (pcy - 6) * S, (pcx + 7) * S, (pcy + 6) * S], fill=rgb('#D9793A'))
        g.ellipse([(pcx - 6) * S, (pcy - 5) * S, (pcx + 6) * S, (pcy + 5) * S],
                  fill=tuple(int(v * 0.6 * flick) for v in rgb(AMBER)))
        fr.glow(pcx, pcy, 8, AMBER, 14, 0.75 * flick)
        fr.glow(pcx, pcy, 20, P['ember_deep'], 30, 0.35 * flick)
        pumpkins.append((pcx, pcy))

    fr.add_light_image(lay)
    fr.add_light_image(lay, blur=3)

    # cards slide in with lines drawing
    cards = ((2, 860, 640, -6, 1), (5, 200, 760, 5, 2), (4, 920, 1230, 4, 3))
    for ci, (pi, cx, cy, ang, sd) in enumerate(cards):
        start = 40 + ci * 14
        if lf < start:
            continue
        u = ease_out_cubic(min(1.0, (lf - start) / 14))
        sx, sy = pumpkins[pi]
        # line draws
        lx = sx + (cx - sx) * u
        ly = sy + ((cy + 80) - sy) * u
        fr.d.line([(sx * S, sy * S), (lx * S, ly * S)], fill=rgb(AMBER, 0.45 * u), width=int(1.5 * S))
        # card rises 60px
        cy_a = cy + (1 - u) * 60
        if u > 0.15:
            rs.phone_card(fr, cx, cy_a, 130, 220, ang, sd)

    fr.scrim(200, 470, 0.75)
    fr.scrim(1420, 1580, 0.7)
    rs.headline_block(fr, 220, '今天', '它也来到了这里')
    fr.text((SIDE, 400), '主题乐园、变装派对、朋友圈', 'body', 50, CREAM)
    fr.text((SIDE, 1440), '每到秋天，不少主题乐园都会办万圣节活动', 'caption', 34, MIST)
    img = finish_fast(fr, frame_seed=gframe)
    out0 = dur - 18
    if lf >= out0:
        u = ease_in_cubic((lf - out0) / 18)
        img = multiply_dark(img, 1 - 0.55 * u)
        for (x, y) in ((860, 640), (200, 760), (920, 1230)):
            img = light_point(img, lerp(x, 540, u), lerp(y, 900, u), 10, strength=0.7)
    return img


# ============================================================ SHOT 09
def anim_09(lf, dur, gframe):
    fr = Frame(1040 + lf)
    dx, dy, sc = cam_drift(lf, 9, amp=0.01)
    rows = [(330, '10月31日', '万圣夜', '为亡灵点一盏灯', rs.small_pumpkin),
            (650, '农历七月十五', '中元节', '放一盏河灯', rs.river_lantern),
            (970, '农历十月初一', '寒衣节', '给远方的人送冬衣', rs.paper_clothes)]
    for i, (y, date, name, act, fn) in enumerate(rows):
        start = i * 18
        if lf < start and lf < 2040 - 1776:
            continue
        u = ease_out_cubic(min(1.0, max(0, lf - start) / 14)) if lf < 2040 - 1776 else 1.0
        rise = (1 - u) * 50
        yy = y - rise + dy * 0.05
        # extinguish?
        out0 = 2040 - 1776
        ext_a = 1.0
        if lf >= out0:
            extinguish_at = i * 8
            if lf - out0 >= extinguish_at:
                e = min(1.0, (lf - out0 - extinguish_at) / 8)
                ext_a = 1 - e
                # smoke wisps
                for s in range(5):
                    sx = 250 + (s - 2) * 12 + 8 * math.sin((lf + s * 5) / 6)
                    sy = yy - 40 - e * 80 - s * 10
                    fr.d.ellipse([(sx - 6) * S, (sy - 10) * S, (sx + 6) * S, (sy + 10) * S],
                                 fill=rgb(MIST, 0.12 * (1 - e) * ext_a + 0.08 * e))
        if ext_a < 0.02:
            continue
        fr.d.rounded_rectangle([SIDE * S, (yy - 130) * S, (W - SIDE) * S, (yy + 140) * S],
                               radius=int(16 * S), fill=rgb('#111F33'),
                               outline=rgb('#2C4260', 0.9 * ext_a), width=int(1.5 * S))
        if u > 0.2 and ext_a > 0.3:
            fn(fr, 250, yy, 0.95)
        fr.text((420, yy - 92), date, 'caption', 36, AMBER, a=u * ext_a)
        fr.text((420, yy - 38), name, 'headline', 72, CREAM, a=u * ext_a)
        fr.text((420, yy + 62), act, 'caption', 36, MIST, a=u * ext_a)
        # lamp glow flicker while alive
        if ext_a > 0.5:
            flick = 1.0 + 0.08 * math.sin(2 * math.pi * (1.7 + i * 0.3) * lf / FPS)
            fr.glow(250, yy, 30, AMBER, 40, 0.12 * flick * ext_a)

    # main text ~lf150
    text_start = 150
    if lf >= text_start:
        # char by char every 2 frames
        line1 = '每个文化，'
        line2 = '都给想念留了一个夜晚'
        n1 = min(len(line1), max(0, (lf - text_start) // 2))
        n2 = min(len(line2), max(0, (lf - text_start - len(line1) * 2) // 2))
        if n1:
            fr.text((540, 1230), line1[:n1], 'headline', 76, CREAM, anchor='ma')
        if n2:
            fr.text((540, 1340), line2[:n2], 'headline', 76, CREAM, anchor='ma')
        if n1 >= len(line1) and n2 >= len(line2):
            fr.text((540, 1470), '今年的寒衣节：11月9日', 'caption', 36, AMBER, anchor='ma')

    img = finish_fast(fr, frame_seed=gframe)
    out0 = 2040 - 1776
    if lf >= out0:
        u = (lf - out0) / max(1, dur - out0)
        if u > 0.7:
            img = fade(img, 1 - (u - 0.7) / 0.3)
    return img


ANIMS = {1: anim_01, 2: anim_02, 3: anim_03, 4: anim_04, 5: anim_05,
         6: anim_06, 7: anim_07, 8: anim_08, 9: anim_09}


def local_of(frame):
    for s, (a, b) in RANGES.items():
        if a <= frame <= b:
            return s, frame - a, b - a
    return None, 0, 0


def render_frame(frame):
    shot, lf, dur = local_of(frame)
    if shot is None:
        return night()
    # exact still at hero
    if lf == HERO[shot]:
        return load_still(shot)
    img = ANIMS[shot](lf, dur, frame)
    # light-point handoff bridge last 12f
    a, b = RANGES[shot]
    if shot < 9 and frame >= b - 11:
        t = (frame - (b - 11)) / 12.0
        hx, hy = HANDOFF.get(shot, (540, 960))
        nxt = ANIMS[shot + 1](0, RANGES[shot + 1][1] - RANGES[shot + 1][0], b + 1)
        img = handoff_blend(img, nxt, t * 0.85, hx, hy)
    return img


def _worker_init():
    # ensure S=1 in worker
    C.S = 1
    C._fc.clear()
    land_mask()
    _vignette_mask()
    _town_latlons()


def _render_one(frame):
    path = os.path.join(FRAMES, f'{frame:05d}.png')
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return frame, 'skip'
    t0 = time.time()
    img = render_frame(frame)
    img.save(path)
    return frame, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--end', type=int, default=TOTAL - 1)
    ap.add_argument('--workers', type=int, default=max(1, min(6, os.cpu_count() or 4)))
    ap.add_argument('--encode', action='store_true')
    args = ap.parse_args()
    frames = list(range(args.start, args.end + 1))
    print(f'render v2 frames {args.start}..{args.end} workers={args.workers} S={C.S}', flush=True)
    t0 = time.time()
    if args.workers <= 1:
        _worker_init()
        for f in frames:
            i, dt = _render_one(f)
            if i % 24 == 0:
                print(f'  f{i} {dt if isinstance(dt, float) else dt}', flush=True)
    else:
        with Pool(args.workers, initializer=_worker_init) as pool:
            done = 0
            for i, dt in pool.imap_unordered(_render_one, frames, chunksize=2):
                done += 1
                if done % 48 == 0 or done == len(frames):
                    elapsed = time.time() - t0
                    rate = done / max(elapsed, 0.1)
                    eta = (len(frames) - done) / max(rate, 0.01)
                    print(f'  {done}/{len(frames)} last=f{i} {dt if not isinstance(dt, str) else dt} '
                          f'{rate:.2f} f/s eta={eta:.0f}s', flush=True)
    print(f'done frames in {time.time() - t0:.1f}s', flush=True)
    if args.encode or (args.start == 0 and args.end == TOTAL - 1):
        encode()


def encode():
    import subprocess
    out = os.path.join(OUT_DIR, 'halloween_history_v2.mp4')
    cmd = [
        'ffmpeg', '-y', '-framerate', '24',
        '-i', os.path.join(FRAMES, '%05d.png'),
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20',
        '-movflags', '+faststart', '-an', out,
    ]
    print('encode', ' '.join(cmd), flush=True)
    subprocess.check_call(cmd)
    print('wrote', out, os.path.getsize(out), flush=True)


if __name__ == '__main__':
    main()
