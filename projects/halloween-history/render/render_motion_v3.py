#!/usr/bin/env python3
"""Motion cut v3 · voice-driven, beat-snapped (90 BPM = 16 f/beat), cinematic camera.
Frame = f(frame). 24fps, 1792 frames (74.67 s), 1080x1920.
Layers: SCENE (camera, rack focus, bloom, whip) + TEXT (never moves with camera) + SUBTITLES.
Reuses v2 per-element animators via time remap; shot 01 and 05 are rewritten.
Usage: python3 render_motion_v3.py [--start N] [--end N] [--workers K]
"""
import argparse, json, math, os, sys, time
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render_motion_v2 as v2          # sets common.S = 1
from common import *                    # noqa
import render_stills as rs
from motion_lib import (ease_in_out_quart, ease_out_cubic, ease_in_cubic, lerp,
                        light_point, zoom_at, night, RANGES as R2)

PROJ_DIR = PROJ
# v3.1: timeline / frame dir selectable via env (defaults reproduce v3 exactly)
TL = json.load(open(os.path.join(PROJ_DIR, 'audio', os.environ.get('HH_TIMELINE', 'timeline_v3.json')), encoding='utf-8'))
FPS = 24
TOTAL = TL['total_frames']
R3 = {int(k): (v['start'], v['end']) for k, v in TL['shots'].items()}
FRAMES = os.path.join(PROJ_DIR, os.environ.get('HH_FRAMES', 'frames_v3'))
os.makedirs(FRAMES, exist_ok=True)
CREAM, MIST, AMBER = P['paper_cream'], P['mist_grey'], P['ember_amber']

WHIP_OUT, WHIP_IN, RACK = 8, 8, 10        # frames
SUB = 4                                   # subframes, 180° shutter (half a frame)

# ------------------------------------------------------------- text layer capture
_TEXT = {'img': None}
def _finish_scene(fr, path=None, frame_seed=0):
    """Replacement for v2.finish_fast: returns SCENE only; text stashed separately."""
    base = np.asarray(fr.base, np.float32)
    light = np.asarray(fr.light, np.float32)
    out = np.clip(base + light * STYLE['glow']['intensity_max'] * 1.15, 0, 255)
    out *= v2._vignette_mask()[..., None]
    gr = STYLE['grain']
    g = np.random.default_rng(gr['seed'] + frame_seed).normal(0, 1, (H, W)).astype(np.float32)
    g = np.asarray(Image.fromarray(((g * 40) + 128).clip(0, 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(gr['blur_sigma_px'])), np.float32)
    out *= (1 + gr['amplitude'] * 0.85 * (g - 128) / 40)[..., None]
    _TEXT['img'] = fr.top.copy()
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
v2.finish_fast = _finish_scene

# ------------------------------------------------------------- perspective globe (shot 01)
FOCAL = (H / 2) / math.tan(math.radians(16))   # ~32° vertical FOV lens

class Persp:
    """True perspective sphere: camera at distance d (unit sphere), looking at (lon0, lat0)."""
    def __init__(self, lon0, lat0, d, cx, cy):
        self.l0, self.p0, self.d, self.cx, self.cy = math.radians(lon0), math.radians(lat0), d, cx, cy
        self.R = FOCAL / math.sqrt(d * d - 1)      # apparent silhouette radius (px)

    def _view(self, lon, lat):
        l, p = np.radians(lon), np.radians(lat)
        X = np.cos(p) * np.sin(l - self.l0)
        Y = math.cos(self.p0) * np.sin(p) - math.sin(self.p0) * np.cos(p) * np.cos(l - self.l0)
        Z = math.sin(self.p0) * np.sin(p) + math.cos(self.p0) * np.cos(p) * np.cos(l - self.l0)
        return X, Y, Z

    def fwd(self, lon, lat):
        X, Y, Z = self._view(np.asarray(lon, float), np.asarray(lat, float))
        den = self.d - Z
        return self.cx + FOCAL * X / den, self.cy - FOCAL * Y / den, Z > (1 / self.d)

def sphere_dots(spacing_deg, box=None):
    """Equal-area land dots on the sphere (lat, lon arrays), cached per spacing."""
    key = ('dots', round(spacing_deg, 4), box)
    if key in v2._CACHE:
        return v2._CACHE[key]
    m = land_mask()
    la0, la1, lo0, lo1 = box or (-60, 85, -180, 180)
    lats = np.arange(la0, la1, spacing_deg)
    LA, LO = [], []
    for i, la in enumerate(lats):
        step = spacing_deg / max(0.15, math.cos(math.radians(la)))
        lons = np.arange(lo0 + (i % 2) * step / 2, lo1, step)
        mi = int(np.clip((90 - la) / 180 * MH, 0, MH - 1))
        mj = (((lons + 180) % 360) / 360 * MW).astype(int).clip(0, MW - 1)
        ok = m[mi, mj]
        LA.append(np.full(ok.sum(), la)); LO.append(lons[ok])
    out = (np.concatenate(LA), np.concatenate(LO))
    v2._CACHE[key] = out
    return out

def draw_globe(fr, pr):
    d = fr.d
    if pr.R < 2600:
        d.ellipse([pr.cx - pr.R, pr.cy - pr.R, pr.cx + pr.R, pr.cy + pr.R], fill=rgb('#101D30'))
    for lat in range(-80, 90, 10):
        lons = np.linspace(-180, 180, 721)
        x, y, v = pr.fwd(lons, np.full_like(lons, lat)); v2_poly(d, x, y, v)
    for lon in range(-180, 180, 10):
        lats = np.linspace(-89, 89, 357)
        x, y, v = pr.fwd(np.full_like(lats, lon), lats); v2_poly(d, x, y, v)
    # LOD: target 11 px on-screen spacing; crossfade two levels (sphere-locked dots, no crawl)
    target = 11 / pr.R * 57.2958
    levels = [1.40, 0.70, 0.35, 0.175, 0.0875]
    k = int(np.clip(np.searchsorted(-np.array(levels), -target), 1, len(levels) - 1))
    lo_s, hi_s = levels[k - 1], levels[k]
    w_hi = float(np.clip(math.log(lo_s / target) / math.log(lo_s / hi_s), 0, 1))
    col = np.array(rgb(P['land_dot']), np.float32)
    bg = np.array(rgb('#101D30'), np.float32)
    for sp, wgt in ((lo_s, 1.0), (hi_s, w_hi)):
        if wgt <= 0.02:
            continue
        box = None if sp >= 0.7 else (38, 66, -32, 14)
        la, lo = sphere_dots(sp, box)
        x, y, v = pr.fwd(lo, la)
        ok = v & (x > -4) & (x < W + 4) & (y > -4) & (y < H + 4)
        c = tuple(int(a) for a in bg + (col - bg) * wgt)
        for xx, yy in zip(x[ok], y[ok]):
            d.ellipse([xx - 2, yy - 2, xx + 2, yy + 2], fill=c)
    d.ellipse([pr.cx - pr.R - 1, pr.cy - pr.R - 1, pr.cx + pr.R + 1, pr.cy + pr.R + 1],
              outline=rgb(P['veil_moon'], 0.30), width=2)

def v2_poly(d, x, y, v):
    seg = []
    for xi, yi, vi in zip(x, y, v):
        if vi and -200 < xi < W + 200 and -200 < yi < H + 200:
            seg.append((xi, yi))
        else:
            if len(seg) > 1: d.line(seg, fill=rgb(P['graticule'], 0.55), width=1)
            seg = []
    if len(seg) > 1: d.line(seg, fill=rgb(P['graticule'], 0.55), width=1)

IRL = (-7.5, 53.4)
def globe_cam(lf):
    """Shot 01 camera: spin (never parks) then fly-through push into Ireland."""
    d0 = math.sqrt((FOCAL / 460) ** 2 + 1)            # matches still: radius 460
    spin = -35 + 6 * ease_in_out_quart(min(1, lf / 36)) + 0.04 * max(0, lf - 36)
    if lf < 92:
        return Persp(spin, 38, d0, 540, 990)
    u = ease_in_out_quart((lf - 92) / 35)
    d1 = math.sqrt((FOCAL / (460 * 12)) ** 2 + 1)
    d = math.exp(lerp(math.log(d0), math.log(d1), u))
    lon = lerp(spin, IRL[0], u); lat = lerp(38, IRL[1], u)
    # keep Ireland heading to the centre as we fly in
    pr = Persp(lon, lat, d, 540, lerp(990, 960, u))
    return pr

def anim_01(lf, gframe):
    fr = Frame(1032 + int(lf))
    pr = globe_cam(lf)
    draw_globe(fr, pr)
    towns, hubs = v2._town_latlons()
    zoomk = (pr.R / 460) ** 0.35
    lay = Image.new('RGB', (W, H)); g = ImageDraw.Draw(lay)
    for lat, lon, k, order in towns:
        age = lf - order // 40
        if age < 0: continue
        b = ease_out_cubic(min(1, age / 8))
        x, y, v = pr.fwd(lon, lat)
        if not v or not (-10 < x < W + 10 and -10 < y < H + 10): continue
        r = 1.25 * zoomk
        g.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(c * 0.75 * b) for c in rgb(P['ember_core'])))
    fr.add_light_image(lay); fr.add_light_image(lay, blur=4 * zoomk); fr.add_light_image(lay, blur=22)
    for i, (la, lo, k) in enumerate(hubs):
        if k < 0.8: continue
        age = lf - (48 + int(i / len(hubs) * 30))
        if age < 0: continue
        x, y, v = pr.fwd(lo, la)
        if v and -40 < x < W + 40 and -40 < y < H + 40:
            v2.city_light_bloom(fr, float(x), float(y), r=(2.2 + 1.6 * k) * zoomk, strength=1.0,
                                bloom=ease_out_cubic(min(1, age / 10)))
    x, y, v = pr.fwd(IRL[0], IRL[1]); ix, iy = float(x), float(y)
    if lf >= 78:
        u = ease_out_cubic(min(1, (lf - 78) / 12)); s = zoomk
        fr.glow(ix, iy, 5 * s, P['ember_core'], 5 * s, u)
        fr.glow(ix, iy, 12 * s, AMBER, 18 * s, 0.6 * u)
        fr.glow(ix, iy, 30 * s, P['ember_deep'], 40 * s, 0.35 * u)
        fr.d.ellipse([ix - 26 * s, iy - 26 * s, ix + 26 * s, iy + 26 * s], outline=rgb(AMBER, 0.85 * u), width=2)
        fr.d.ellipse([ix - 44 * s, iy - 44 * s, ix + 44 * s, iy + 44 * s], outline=rgb(AMBER, 0.35 * u), width=2)
    ta = 1.0 if lf < 86 else max(0.0, 1 - ease_in_cubic((lf - 86) / 8))
    if ta > 0.01:
        fr.text((540, 260), '10月31日', 'headline', 96, CREAM, anchor='ma', a=ta)
        fr.text((540, 400), '一个夜晚，怎么走到了你身边？', 'body', 52, CREAM, anchor='ma', a=ta)
        fr.text((540, 1500), '万圣节的历史演变', 'caption', 38, AMBER, anchor='ma', a=ta)
        rs.rule(fr, 420, 660, 1565, AMBER, 0.6 * ta)
    return _finish_scene(fr, frame_seed=gframe), (ix, iy)

# ------------------------------------------------------------- shot 05 (long trails; camera sweep done in CAM)
def anim_05(lf, dur, gframe):
    fr = Frame(1036 + lf)
    pr = Ortho(-40, 47, 860, 540, 1000)
    draw_map(fr, pr, dot_spacing=11, coast=True, graticule=True, disk=False, region=(0, 0, W, H))
    routes, srcs, dsts = v2._routes05(pr)
    for ax, ay in routes:
        fr.d.line([(a, b) for a, b in zip(ax, ay)], fill=rgb(AMBER, 0.12), width=1)
    head = Image.new('RGB', (W, H)); trail = Image.new('RGB', (W, H))
    g, tg = ImageDraw.Draw(head), ImageDraw.Draw(trail)
    for i in range(1000):
        age = lf - (10 + i // 6)
        if age < 0: continue
        ax, ay = routes[i % 12]
        sp = 0.011 + (i % 9) * 0.0013
        jit = ((i * 37) % 17 - 8) * 0.25
        def at(tt):
            q = min(1.0, tt) * (len(ax) - 1); j = int(q); j1 = min(len(ax) - 1, j + 1); u = q - j
            return ax[j] * (1 - u) + ax[j1] * u + jit, ay[j] * (1 - u) + ay[j1] * u + jit * 0.4
        t = age * sp
        x, y = at(t)
        if t < 1.0:          # long motion-blur trail: 16 samples over ~2.5 frames of travel
            pts = [at(max(0, t - k * sp * 0.16)) for k in range(16)]
            tg.line(pts, fill=tuple(int(c * 0.55) for c in rgb(AMBER)), width=2)
        g.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=rgb(P['ember_core']))
    fr.add_light_image(trail, blur=1.2); fr.add_light_image(head); fr.add_light_image(head, blur=3)
    fr.scrim(200, 470, 0.75); fr.scrim(1420, 1580, 0.7)
    for la, lo in dsts[:2]:
        x, y, _ = pr.fwd(np.array([lo]), np.array([la])); city_light(fr, float(x[0]), float(y[0]), 3.2)
    for la, lo in srcs[:2]:
        x, y, _ = pr.fwd(np.array([lo]), np.array([la])); city_light(fr, float(x[0]), float(y[0]), 2.6, 0.8)
    x, y, _ = pr.fwd(np.array([-74.0]), np.array([40.71])); fr.text((x[0] - 10, y[0] + 14), '纽约', 'caption', 34, MIST, anchor='ra')
    x, y, _ = pr.fwd(np.array([-8.0]), np.array([53.0])); fr.text((x[0] + 6, y[0] + 40), '爱尔兰', 'caption', 34, MIST, anchor='ma')
    rs.headline_block(fr, 220, '1845–1852 · 爱尔兰大饥荒', '很多人离开故土')
    fr.text((80, 400), '他们把万圣节，也带上了船', 'body', 50, CREAM)
    fr.text((80, 1440), '饥荒夺去了大量生命，很多人移民，多数去了北美', 'caption', 34, MIST)
    return _finish_scene(fr, frame_seed=gframe)

_P05 = Ortho(-40, 47, 860, 540, 1000)
IRL05 = tuple(float(a[0]) for a in _P05.fwd(np.array([-7.0]), np.array([53.2]))[:2])
NY05 = tuple(float(a[0]) for a in _P05.fwd(np.array([-74.0]), np.array([40.71]))[:2])

# v3 local frame -> v2 local frame knots (voice sync). Default: linear.
REMAP = {9: [(0, 0), (54, 54), (62, 150), (210, 264), (255, 286)]}
if 'remap9' in TL:                       # v3.1: knots re-derived from the new VO timing
    REMAP[9] = [tuple(k) for k in TL['remap9']]
N1 = R3[1][1] - R3[1][0] + 1             # shot 01 designed for 128 f; longer -> slow the 36..78 spin phase
def lf01(lf):
    if N1 <= 128 or lf <= 36: return lf
    ext = N1 - 128
    if lf <= 78 + ext: return 36 + (lf - 36) * 42 / (42 + ext)
    return lf - ext

# ------------------------------------------------------------- per-shot camera on SCENE (cx, cy, scale)
def CAM(shot, lf, n):
    u = lf / max(1, n - 1)
    if shot == 1:
        return 540, 990, 1.07 - 0.058 * ease_out_cubic(min(1, lf01(lf) / 60))   # hook: pull-out reveal from f0, then globe flies
    if shot == 5:                                                # sweep across the Atlantic, then push NY
        w = ease_in_out_quart(min(1, lf / (n - 40)))
        cx, cy = lerp(IRL05[0], NY05[0], w), lerp(IRL05[1], NY05[1], w)
        s = 1.30
        if lf > n - 40:
            q = ease_in_out_quart((lf - (n - 40)) / 39); s = lerp(1.30, 2.6, q)
        return cx, cy, s
    if shot == 8:                                                # dolly into the windows
        return lerp(540, 520, u), lerp(1000, 1060, u), 1.0 + 0.07 * ease_in_out_quart(u)
    if shot == 2:
        return 560, lerp(980, 1080, u), 1.02 + 0.03 * u
    if shot == 6:
        return lerp(380, 600, ease_in_out_quart(u)), lerp(820, 1060, ease_in_out_quart(u)), 1.03 + 0.02 * u
    if shot == 7:
        return 540, 900, 1.0 + 0.035 * u
    return 540, 960, 1.0 + 0.025 * u                            # slow ~2.5% push, never parks

def cam_apply(img, cx, cy, s):
    if s <= 1.0005:
        return img
    return zoom_at(img, cx, cy, s)

def bloom(img, amt=0.45):
    small = img.resize((W // 4, H // 4), Image.BILINEAR)
    a = np.asarray(small, np.float32)
    lum = a.mean(axis=2, keepdims=True)
    hi = np.clip((lum - 150) / 105, 0, 1) * a
    b = Image.fromarray(hi.astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR)
    return Image.fromarray(np.clip(np.asarray(img, np.float32) + np.asarray(b, np.float32) * amt, 0, 255).astype(np.uint8))

# ------------------------------------------------------------- handoff anchors (screen px)
OUT_ANCHOR = {1: (540, 960), 2: (540, 1385), 3: (540, 1385), 4: (540, 1270), 5: (540, 960),
              6: (650, 1125), 7: (540, 1000), 8: (540, 900)}
IN_ANCHOR = {2: (520, 1010), 3: (540, 1385), 4: (935, 1000), 5: IRL05, 6: (290, 770),
             7: (330, 820), 8: (200, 900), 9: (250, 330)}

def scene_for(shot, lf, gframe):
    a, b = R3[shot]; n = b - a + 1
    if shot == 1:
        img, _ = anim_01(lf01(lf), gframe)
    else:
        a2, b2 = R2[shot]; d2 = b2 - a2
        knots = REMAP.get(shot, [(0, 0), (n - 1, d2 - 1)])
        xs, ys = zip(*knots)
        lf2 = int(round(float(np.interp(lf, xs, ys))))
        lf2 = min(lf2, d2 - 1)
        fn = anim_05 if shot == 5 else v2.ANIMS[shot]
        img = fn(lf2, d2, gframe) if shot == 5 else fn(lf2, d2, gframe)
    return img, _TEXT['img']

def whip(img, anchor, amount, sub_amounts):
    """Zoom-through-light with 180° shutter: average SUB zooms spread over half a frame."""
    x, y = anchor
    acc = np.zeros((H, W, 3), np.float32)
    for s in sub_amounts:
        acc += np.asarray(zoom_at(img, x, y, 1 + 2.2 * s), np.float32)
    out = Image.fromarray((acc / len(sub_amounts)).astype(np.uint8))
    return light_point(out, W / 2 if amount > 0.5 else x, H / 2 if amount > 0.5 else y,
                       16 + 150 * amount, strength=0.30 + 0.45 * amount)

def text_alpha(shot, lf, n):
    a = 1.0
    if shot > 1 and lf < WHIP_IN + 4:
        a = ease_out_cubic(max(0, lf - 2) / (WHIP_IN + 2))      # no overshoot (ζ=1)
    if shot < 9 and lf > n - 1 - 6:
        a *= 1 - ease_in_cubic((lf - (n - 7)) / 6)
    return a

# ------------------------------------------------------------- subtitles
_SUBS = None
def subs():
    global _SUBS
    if _SUBS is None:
        import re
        _SUBS = []
        for k, sh in TL['shots'].items():
            txt = sh.get('tts_text', sh['text']).replace('——', '，')
            parts = [p for p in re.split(r'(?<=[。？，；、])', txt) if p.strip()]
            # merge tiny parts so each chunk is 6–18 chars
            chunks, cur = [], ''
            for p in parts:
                if len(cur) + len(p) <= 18: cur += p
                else:
                    if cur: chunks.append(cur)
                    cur = p
            if cur: chunks.append(cur)
            total = sum(len(c) for c in chunks)
            f0 = sh['vo_start_frame']; span = sh['vo_frames']
            acc = 0
            for c in chunks:
                s = f0 + int(round(span * acc / total)); acc += len(c)
                e = f0 + int(round(span * acc / total))
                _SUBS.append((s, e, c.rstrip('，、；。')))
        keep = []
        for i, (s, e, c) in enumerate(_SUBS):
            if c not in SHOW_SUBS: continue
            need = int(math.ceil(len(c) / 6 * FPS))          # >= 6 chars/s reading
            nxt = [x[0] for j, x in enumerate(_SUBS) if j > i and x[2] in SHOW_SUBS]
            lim = (nxt[0] - 4) if nxt else e + need
            keep.append((s, min(max(e, s + need), max(e, lim)), c))
        _SUBS = keep
    return _SUBS

# narration chunks that differ from on-screen text (others are already on screen -> no subtitle)
SHOW_SUBS = {'在爱尔兰和苏格兰，这一夜叫萨温节', '教会定下十一月一日为诸圣节', '它的英文名字',
             '源自苏格兰人对「诸圣节前夜」的缩写',              '「不给糖就捣蛋」从报纸上的一句话', '变成全美孩子的夜晚', '再借电影和网络走向世界'}

_SUBFONT = None
def draw_subs(img, frame):
    global _SUBFONT
    if _SUBFONT is None:
        _SUBFONT = ImageFont.truetype(STYLE['fonts']['caption']['file'], 34, index=2)
    for s, e, txt in subs():
        if s - 3 <= frame <= e + 3:
            a = min(1.0, (frame - (s - 3)) / 3, (e + 3 - frame) / 3)
            if a <= 0: continue
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
            tw = d.textlength(txt, font=_SUBFONT)
            x0, y0 = 540 - tw / 2 - 22, 1632
            d.rounded_rectangle([x0, y0, 540 + tw / 2 + 22, y0 + 58], radius=14, fill=(9, 17, 29, int(170 * a)))
            d.text((540, y0 + 9), txt, font=_SUBFONT, fill=rgb(CREAM, a), anchor='ma')
            img = Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')
    return img

# ------------------------------------------------------------- frame
def shot_of(frame):
    for s, (a, b) in R3.items():
        if a <= frame <= b: return s, frame - a, b - a + 1
    return 9, 0, 1

def render_frame(frame):
    shot, lf, n = shot_of(frame)
    fast = (shot == 1 and lf01(lf) >= 92)
    if fast:   # 180° shutter on the fly-through: 4 subframe renders over half a frame
        acc = np.zeros((H, W, 3), np.float32); text = None
        for k in range(SUB):
            img, _ = anim_01(lf01(lf) + (k / SUB) * 0.5, frame)
            acc += np.asarray(img, np.float32); text = _TEXT['img']
        scene = Image.fromarray((acc / SUB).astype(np.uint8))
    else:
        scene, text = scene_for(shot, lf, frame)
    cx, cy, s = CAM(shot, lf, n)
    scene = cam_apply(scene, cx, cy, s)
    if shot > 1 and lf < RACK:                                    # rack focus in
        sig = 7 * (1 - ease_out_cubic(lf / RACK))
        if sig > 0.3: scene = scene.filter(ImageFilter.GaussianBlur(sig))
    scene = bloom(scene)
    if shot < 9 and lf >= n - WHIP_OUT:                           # whip out through the light
        u = (lf - (n - WHIP_OUT)) / WHIP_OUT
        subs_u = [ease_in_cubic(u + k / (SUB * 2 * WHIP_OUT)) for k in range(SUB)]
        scene = whip(scene, OUT_ANCHOR[shot], ease_in_cubic(u), subs_u)
    if shot > 1 and lf < WHIP_IN:                                 # whip in from the light
        u = 1 - lf / WHIP_IN
        subs_u = [ease_in_cubic(max(0, u - k / (SUB * 2 * WHIP_IN))) for k in range(SUB)]
        scene = whip(scene, IN_ANCHOR[shot], ease_in_cubic(u), subs_u)
    out = scene.convert('RGBA')
    ta = text_alpha(shot, lf, n)
    if text is not None and ta > 0.01:
        t = text
        if t.size != (W, H): t = t.resize((W, H), Image.LANCZOS)
        if ta < 0.999:
            arr = np.asarray(t).copy(); arr[..., 3] = (arr[..., 3] * ta).astype(np.uint8); t = Image.fromarray(arr)
        out = Image.alpha_composite(out, t)
    out = out.convert('RGB')
    if shot == 9 and lf > n - 18:
        k = 1 - ease_in_cubic((lf - (n - 18)) / 17)
        out = Image.fromarray((np.asarray(out, np.float32) * k).astype(np.uint8))
    return draw_subs(out, frame)

def _init():
    v2._worker_init()

def _one(frame):
    p = os.path.join(FRAMES, f'{frame:05d}.png')
    if os.path.exists(p) and os.path.getsize(p) > 1000: return frame, 0.0
    t0 = time.time(); render_frame(frame).save(p); return frame, time.time() - t0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', type=int, default=0); ap.add_argument('--end', type=int, default=TOTAL - 1)
    ap.add_argument('--workers', type=int, default=6)
    a = ap.parse_args()
    fr = list(range(a.start, a.end + 1)); t0 = time.time()
    with Pool(a.workers, initializer=_init) as pool:
        for i, (f, dt) in enumerate(pool.imap_unordered(_one, fr, chunksize=2)):
            if (i + 1) % 64 == 0: print(f'{i+1}/{len(fr)} f{f} {dt:.1f}s {time.time()-t0:.0f}s', flush=True)
    print('done', time.time() - t0, flush=True)

if __name__ == '__main__':
    main()
