"""Motion cut v1 · 《万圣节的历史演变》
Frame = f(frame). 24fps, 2064 frames, 1080×1920, silent.
Uses approved stills as composition truth; animates camera / reveal / handoff.
Usage: python3 render_motion.py [--start N] [--end N] [--workers K]
"""
import argparse, math, os, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from motion_lib import *

OUT_DIR = os.path.join(PROJ, 'out')
FRAMES = os.path.join(PROJ, 'frames')
CUT = os.path.join(PROJ, 'assets', 'cut')

# Hero local frames: blit exact still (key pose match)
HERO = {1: 100, 2: 280, 3: 520 - 408, 4: 720 - 600, 5: 1000 - 840,
        6: 1280 - 1128, 7: 1500 - 1344, 8: 1700 - 1584, 9: 1950 - 1776}

# Handoff anchors (screen px) and outgoing light
HANDOFF = {
    # shot_n → (x, y) light leaving into next
    1: (667, 849),   # Ireland ring
    2: (540, 1385),  # Tlachtga → shot03 fire (approx center bottom after pan)
    3: (540, 960),   # hard-ish → calendar (center)
    4: (540, 1270),  # Halloween word → light
    5: (700, 900),   # NY area on shot05 (approx)
    6: (650, 1125),  # pumpkin
    7: (540, 900),   # globe center → window
    8: (540, 1000),  # three lights gather
}


def local_of(frame):
    for s, (a, b) in RANGES.items():
        if a <= frame <= b:
            return s, frame - a, b - a
    return None, 0, 0


# ---------- shot animations ----------

def anim_01(lf, dur):
    """Lights settle → hold still → push ×12 into Ireland."""
    s = still(1)
    # Appear: fade from black 0-20, while overall brightens as "lights"
    if lf <= 20:
        return soft_grain(fade(s, ease_out_cubic(lf / 20)), lf)
    # City lights metaphor: from dim to full 20-96
    if lf < 96:
        k = lerp(0.55, 1.0, ease_out_cubic((lf - 20) / 76))
        img = multiply_dark(s, k)
        # Ireland ring brightens last
        if lf >= 80:
            u = (lf - 80) / 16
            img = light_point(img, 667, 849, 14 + 20 * u, strength=0.35 * u)
        return soft_grain(img, lf)
    # Hero hold
    if lf < 120:
        return soft_grain(s, lf) if lf != HERO[1] else s
    # Push-in 12× toward Ireland (f120-143)
    u = ease_in_out_quart((lf - 120) / max(1, dur - 120))
    scale = lerp(1.0, 12.0, u)
    img = zoom_at(s, 667, 849, scale)
    # handoff point grows at end
    if u > 0.7:
        img = light_point(img, W / 2, H / 2, 10 + 40 * (u - 0.7) / 0.3, strength=0.6)
    return soft_grain(img, lf)


def anim_02(lf, dur):
    s = still(2)
    # Enter from zoomed Ireland feel: start slightly zoomed, settle to still
    if lf < 18:
        u = ease_out_cubic(lf / 18)
        img = zoom_at(s, 540, 900, lerp(1.35, 1.0, u))
        img = fade(img, 0.5 + 0.5 * u)
        return soft_grain(img, lf + 144)
    # Fires ignite every 3 frames (8 fires) — brighten still + flicker overlay
    # After ignition period, hold with flicker
    ignite_end = 18 + 8 * 3  # 42
    if lf < ignite_end:
        # progressive brighten from 0.7→1.0 as fires light
        n_lit = min(8, (lf - 18) // 3 + 1)
        k = lerp(0.72, 1.0, n_lit / 8)
        img = multiply_dark(s, k)
    else:
        img = s.copy()
    # Flicker 1.5–3 Hz on warm (seeded)
    rng = np.random.default_rng(200 + lf)
    hz = 1.5 + rng.random() * 1.5
    phase = 2 * math.pi * hz * (lf / FPS)
    flick = 1.0 + 0.06 * math.sin(phase)  # ±6% ≈ storyboard 12% on fires only; keep subtle globally
    img = multiply_dark(img, min(1.0, flick))
    # Veil drift: shift a soft horizontal band
    drift = 14 * math.sin(2 * math.pi * lf / (6 * FPS))
    # cheap: paste still with horizontal offset in mid band
    band = s.crop((0, 520, W, 700))
    img.paste(band, (int(drift), 520))
    # Out pan down toward fire f380-407 → local 236-263
    out0 = 380 - 144
    if lf >= out0:
        u = ease_in_out_quart((lf - out0) / max(1, dur - out0))
        # pan up content → fire moves to center (dy negative means image moves up, fire goes down... )
        # Tlachtga around mid-map; shift toward bottom fire position
        dy = int(lerp(0, -280, u))
        img = pan(img, 0, dy)
        img = light_point(img, 540, lerp(1100, 1385, u), 12 + 10 * u, strength=0.4 + 0.4 * u)
    if lf == HERO[2]:
        return still(2)
    return soft_grain(img, lf + 144)


def anim_03(lf, dur):
    s = still(3)
    base = night()
    # columns for 3 masks approx
    cols = [(80, 380), (390, 700), (710, 1000)]
    # appear every 12 frames ease-out
    progresses = []
    for i in range(3):
        start = i * 12
        if lf < start:
            progresses.append(0.0)
        else:
            progresses.append(ease_out_cubic(min(1.0, (lf - start) / 14)))
    img = column_reveal(base, s, cols, progresses)
    # after all in, use full still
    if lf >= 36:
        img = s.copy()
        # fire flicker at bottom
        rng = np.random.default_rng(303 + lf)
        flick = 1.0 + 0.05 * math.sin(2 * math.pi * (2.0 + rng.random()) * lf / FPS)
        # only brighten lower region slightly
        arr = np.asarray(img, np.float32)
        arr[1280:1500] *= flick
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    if lf == HERO[3]:
        return still(3)
    return soft_grain(img, lf + 408)


def anim_04(lf, dur):
    s = still(4)
    # Cards drop: simulate by vertical wipe / slide from above for card bands
    # Card y bands approx 520-930
    if lf < 30:
        # three cards stagger every 6f, 10f fall
        img = night()
        full = s
        for i, (y0, y1) in enumerate([(560, 890), (520, 930), (560, 890)]):
            start = i * 6
            if lf < start:
                continue
            u = ease_out_cubic(min(1.0, (lf - start) / 10))  # spring-ish via overshoot opt
            # slide from y-80
            dy = int(lerp(-90, 0, u))
            strip = full.crop((0, y0, W, y1))
            img.paste(strip, (0, y0 + dy))
        # top text fades
        top = s.crop((0, 200, W, 500))
        img.paste(Image.blend(night().crop((0, 200, W, 500)), top, min(1, lf / 20)), (0, 200))
        # bottom caption later
        if lf > 18:
            bot = s.crop((0, 1400, W, 1600))
            img.paste(Image.blend(night().crop((0, 1400, W, 1600)), bot, ease_out_cubic((lf - 18) / 12)), (0, 1400))
        return soft_grain(img, lf + 600)
    img = s.copy()
    # Candle flicker
    flick = 1.0 + 0.04 * math.sin(2 * math.pi * 2.5 * lf / FPS)
    arr = np.asarray(img, np.float32)
    arr[500:1100, 850:1000] *= flick
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    # Letter collapse into light: last 24 frames
    out0 = dur - 24
    if lf >= out0:
        u = (lf - out0) / 24
        # darken word-chain region, grow point at Halloween
        img = multiply_dark(img, 1 - 0.5 * ease_in_cubic(u))
        img = light_point(img, 540, 1270, lerp(6, 50, ease_out_cubic(u)), strength=0.4 + 0.6 * u)
        if u > 0.6:
            img = multiply_dark(img, 1 - 0.7 * (u - 0.6) / 0.4)
            img = light_point(img, 540, 1270, 28, strength=1.0)
    if lf == HERO[4]:
        return still(4)
    return soft_grain(img, lf + 600)


def anim_05(lf, dur):
    s = still(5)
    # Enter: light point expands into map
    if lf < 16:
        u = ease_out_cubic(lf / 16)
        img = fade(s, u)
        img = light_point(img, 280, 950, 40 * (1 - u) + 8, strength=1 - 0.5 * u)  # Ireland side
        return soft_grain(img, lf + 840)
    # Particles flowing: overlay moving amber dots along arcs (approx paths)
    img = s.copy()
    rng = np.random.default_rng(55)
    # Precompute 12 arc endpoints visually across Atlantic
    # Use still's baked particles as base; animate extra traveling dots
    n_emit = min(1000, max(0, (lf - 20) * 4))
    lay = Image.new('RGB', (W, H), (0, 0, 0))
    g = ImageDraw.Draw(lay)
    # Sample positions along simplified arcs using seeded rng + time
    for i in range(min(n_emit, 400)):  # cap overlay count for speed
        # progress along journey 0..1 with wrap based on birth
        birth = i // 4
        age = lf - 20 - birth
        if age < 0: continue
        speed = 0.012 + (i % 7) * 0.0015  # ~120-220 px/s ≈ 0.01-0.02 /frame of arc
        t = (age * speed) % 1.2
        if t > 1: continue
        # arc family
        fam = i % 12
        x0, y0 = 200 + (fam % 3) * 40, 880 + (fam % 3) * 30
        x1, y1 = 720 + (fam // 3) * 50, 820 + (fam // 3) * 40
        # quadratic bulge north
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2 - 80 - 20 * (fam % 4)
        tt = t
        x = (1 - tt) ** 2 * x0 + 2 * (1 - tt) * tt * mx + tt ** 2 * x1
        y = (1 - tt) ** 2 * y0 + 2 * (1 - tt) * tt * my + tt ** 2 * y1
        x += rng.normal(0, 1.2); y += rng.normal(0, 1.2)
        g.ellipse([x - 1.6, y - 1.6, x + 1.6, y + 1.6], fill=(255, 200, 120))
    lay = lay.filter(ImageFilter.GaussianBlur(1.2))
    a = np.minimum(np.asarray(img, np.uint16) + np.asarray(lay, np.uint16), 255).astype(np.uint8)
    img = Image.fromarray(a)
    # Out: push toward NY ×3, gather light
    out0 = dur - 36
    if lf >= out0:
        u = ease_in_out_quart((lf - out0) / 36)
        img = zoom_at(img, 780, 860, lerp(1.0, 3.0, u))
        img = light_point(img, W / 2, H / 2, lerp(6, 36, u), strength=0.3 + 0.7 * u)
    if lf == HERO[5]:
        return still(5)
    return soft_grain(img, lf + 840)


def anim_06(lf, dur):
    s = still(6)
    # Load cutouts for morph
    try:
        turnip = Image.open(os.path.join(CUT, 'turnip.png')).convert('RGBA')
        pumpkin = Image.open(os.path.join(CUT, 'pumpkin.png')).convert('RGBA')
    except Exception:
        turnip = pumpkin = None
    if lf < 16:
        return soft_grain(fade(s, ease_out_cubic(lf / 16)), lf + 1128)
    # f0-48 only turnip emphasis: darken pumpkin side
    if lf < 48:
        img = s.copy()
        arr = np.asarray(img, np.float32)
        arr[:, 500:] *= lerp(0.35, 0.55, lf / 48)  # pumpkin side dim
        img = Image.fromarray(arr.astype(np.uint8))
        return soft_grain(img, lf + 1128)
    # f48-120 morph: crossfade + arc motion overlay
    if lf < 120:
        u = ease_in_out_quart((lf - 48) / 72)
        img = s.copy()
        # Dim turnip, brighten pumpkin progressively
        arr = np.asarray(img, np.float32)
        arr[:, :500] *= lerp(1.0, 0.25, u)
        arr[:, 500:] *= lerp(0.55, 1.0, u)
        img = Image.fromarray(arr.astype(np.uint8))
        # traveling light on arc
        # arc from (290,770) to (650,1125)
        t = u
        x = (1 - t) ** 2 * 290 + 2 * (1 - t) * t * 480 + t ** 2 * 650
        y = (1 - t) ** 2 * 770 + 2 * (1 - t) * t * 880 + t ** 2 * 1125
        img = light_point(img, x, y, 10, strength=0.7)
        return soft_grain(img, lf + 1128)
    img = s.copy()
    # Out: pumpkin light expands
    out0 = dur - 20
    if lf >= out0:
        u = ease_in_cubic((lf - out0) / 20)
        img = light_point(img, 650, 1125, lerp(12, 90, u), strength=0.4 + 0.5 * u)
        img = fade(img, 1 - 0.3 * u)
    if lf == HERO[6]:
        return still(6)
    return soft_grain(img, lf + 1128)


def anim_07(lf, dur):
    s = still(7)
    if lf < 14:
        u = ease_out_cubic(lf / 14)
        img = fade(s, u)
        img = light_point(img, 540, 900, 50 * (1 - u), strength=0.8 * (1 - u))
        return soft_grain(img, lf + 1344)
    # Timeline rows appear: 4 rows every ~36 frames conceptually
    # Reveal bottom timeline band progressively
    img = s.copy()
    row_starts = [0, 36, 72, 108]  # relative to after intro
    for i, rs in enumerate(row_starts):
        y0 = 1380 + i * 54
        y1 = y0 + 50
        if lf < 14 + rs:
            # black out this row
            night_strip = night().crop((0, y0, W, y1))
            img.paste(night_strip, (0, y0))
        elif lf < 14 + rs + 10:
            u = ease_out_cubic((lf - 14 - rs) / 10)
            full = s.crop((0, y0, W, y1))
            strip = Image.blend(night().crop((0, y0, W, y1)), full, u)
            img.paste(strip, (0, y0))
    # Outgoing arcs metaphor: already in still; fade globe and push light
    out0 = dur - 24
    if lf >= out0:
        u = ease_in_out_quart((lf - out0) / 24)
        img = fade(img, 1 - 0.85 * u)
        img = light_point(img, lerp(540, 540, u), lerp(900, 1000, u), lerp(8, 36, u), strength=0.5 + 0.5 * u)
    if lf == HERO[7]:
        return still(7)
    return soft_grain(img, lf + 1344)


def anim_08(lf, dur):
    s = still(8)
    if lf < 12:
        u = ease_out_cubic(lf / 12)
        img = fade(multiply_dark(s, 0.4), u)
        img = light_point(img, 200, 900, 30 * (1 - u) + 6, strength=1.0 - 0.4 * u)  # first pumpkin window
        # blend up windows
        img = Image.blend(img, s, u * 0.5)
        return soft_grain(Image.blend(fade(s, u * 0.3), s, u * 0.7) if False else crossfade(multiply_dark(s, 0.35), s, u), lf + 1584)
    # Buildings light L→R every 3 frames (7 blocks)
    if lf < 12 + 7 * 3:
        n = min(7, (lf - 12) // 3 + 1)
        img = multiply_dark(s, lerp(0.5, 1.0, n / 7))
        return soft_grain(img, lf + 1584)
    img = s.copy()
    # Cards rise: already in still — simulate by brief slide of card regions
    # Out: gather lights
    out0 = dur - 18
    if lf >= out0:
        u = ease_in_cubic((lf - out0) / 18)
        img = multiply_dark(img, 1 - 0.6 * u)
        for (x, y) in ((860, 640), (200, 760), (920, 1230)):
            img = light_point(img, lerp(x, 540, u), lerp(y, 900, u), 10, strength=0.7)
    if lf == HERO[8]:
        return still(8)
    return soft_grain(img, lf + 1584)


def anim_09(lf, dur):
    s = still(9)
    # Three cards every 18 frames
    bands = [(200, 470), (520, 790), (840, 1110)]
    img = night()
    for i, (y0, y1) in enumerate(bands):
        start = i * 18
        if lf < start:
            continue
        u = ease_out_cubic(min(1.0, (lf - start) / 14))
        strip = s.crop((0, y0, W, y1))
        blended = Image.blend(night().crop((0, y0, W, y1)), strip, u)
        img.paste(blended, (0, y0))
    # Main text appears ~f150 local (after cards)
    text_start = 150
    if lf >= text_start:
        u = ease_out_cubic(min(1.0, (lf - text_start) / 20))
        for y0, y1 in ((1180, 1400), (1400, 1550)):
            strip = s.crop((0, y0, W, y1))
            img.paste(Image.blend(night().crop((0, y0, W, y1)), strip, u), (0, y0))
    elif lf >= 54:
        # cards all in but text not yet — keep lower dark
        pass
    if lf >= 54 and lf < text_start:
        # ensure cards full
        img = s.copy()
        bot = night().crop((0, 1180, W, H))
        img.paste(bot, (0, 1180))
    if lf >= text_start + 20:
        img = s.copy()
    # Last 2s flicker lamps then extinguish f2040-2063 → local 264-287
    out0 = 2040 - 1776  # 264
    if lf >= out0:
        u = (lf - out0) / max(1, dur - out0)
        # extinguish one by one every 8 frames
        img = s.copy()
        for i, (y0, y1) in enumerate(bands):
            extinguish_at = i * 8
            if lf - out0 >= extinguish_at:
                e = min(1.0, (lf - out0 - extinguish_at) / 8)
                strip = multiply_dark(s.crop((0, y0, W, y1)), 1 - e)
                img.paste(strip, (0, y0))
        # fade all to black at end
        if u > 0.7:
            img = fade(img, 1 - (u - 0.7) / 0.3)
    if lf == HERO[9]:
        return still(9)
    return soft_grain(img, lf + 1776)


ANIMS = {1: anim_01, 2: anim_02, 3: anim_03, 4: anim_04, 5: anim_05,
         6: anim_06, 7: anim_07, 8: anim_08, 9: anim_09}


def render_frame(frame):
    shot, lf, dur = local_of(frame)
    if shot is None:
        return night()
    img = ANIMS[shot](lf, dur)
    # Cross-shot handoff: last 12f of shot N blend with first 12f of N+1
    # Handled inside each anim's out + next's in; add explicit bridge for smoothness
    a, b = RANGES[shot]
    # bridge into next
    if shot < 9 and frame >= b - 11:
        t = (frame - (b - 11)) / 12
        next_still = still(shot + 1)
        hx, hy = HANDOFF.get(shot, (540, 960))
        # next shot's first frame preview (dim)
        nxt = ANIMS[shot + 1](0, RANGES[shot + 1][1] - RANGES[shot + 1][0])
        img = handoff_blend(img, nxt, t * 0.85, hx, hy)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--end', type=int, default=TOTAL - 1)
    ap.add_argument('--stride', type=int, default=1)
    ap.add_argument('--no-encode', action='store_true')
    args = ap.parse_args()
    os.makedirs(FRAMES, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    t0 = time.time()
    for f in range(args.start, args.end + 1, args.stride):
        img = render_frame(f)
        img.save(os.path.join(FRAMES, f'{f:05d}.png'), optimize=False)
        if f % 48 == 0 or f == args.end:
            print(f'frame {f}/{TOTAL - 1}  elapsed {time.time() - t0:.1f}s', flush=True)
    print('frames done', time.time() - t0)


if __name__ == '__main__':
    main()
