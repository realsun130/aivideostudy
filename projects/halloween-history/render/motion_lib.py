"""Frame-driven motion helpers. All time from frame index; seeded RNG only."""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageChops, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
STILLS = os.path.join(PROJ, 'stills')
W, H, FPS = 1080, 1920, 24

# Shot ranges (inclusive), matching storyboard v0.2
RANGES = {
    1: (0, 143), 2: (144, 407), 3: (408, 599), 4: (600, 839),
    5: (840, 1127), 6: (1128, 1343), 7: (1344, 1583), 8: (1584, 1775), 9: (1776, 2063),
}
TOTAL = 2064

_still_cache = {}

def still(n):
    if n not in _still_cache:
        _still_cache[n] = Image.open(os.path.join(STILLS, f'{n:02d}.png')).convert('RGB')
    return _still_cache[n].copy()


def ease_in_out_quart(t):
    t = float(np.clip(t, 0, 1))
    return 8 * t * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 4 / 2


def ease_out_cubic(t):
    t = float(np.clip(t, 0, 1)); return 1 - (1 - t) ** 3


def ease_in_cubic(t):
    t = float(np.clip(t, 0, 1)); return t ** 3


def ease_out_quint(t):
    t = float(np.clip(t, 0, 1)); return 1 - (1 - t) ** 5


def lerp(a, b, t):
    return a + (b - a) * t


def black():
    return Image.new('RGB', (W, H), (13, 24, 40))


def night():
    return Image.new('RGB', (W, H), (13, 24, 40))


def fade(img, a):
    a = float(np.clip(a, 0, 1))
    if a >= 1: return img
    if a <= 0: return night()
    base = night()
    return Image.blend(base, img, a)


def multiply_dark(img, k):
    """Darken RGB by factor k in [0,1]."""
    k = float(np.clip(k, 0, 1))
    if k >= 1: return img
    arr = (np.asarray(img, np.float32) * k).astype(np.uint8)
    return Image.fromarray(arr)


def zoom_at(img, cx, cy, scale, out_size=(W, H)):
    """Zoom into (cx,cy) by scale (>=1). scale=1 → identity crop of full frame."""
    scale = max(1.0, float(scale))
    iw, ih = img.size
    vw, vh = iw / scale, ih / scale
    left = cx - vw / 2
    top = cy - vh / 2
    # clamp
    left = max(0, min(left, iw - vw))
    top = max(0, min(top, ih - vh))
    crop = img.crop((left, top, left + vw, top + vh))
    return crop.resize(out_size, Image.LANCZOS)


def pan(img, dx, dy):
    """Translate content; fill with night."""
    out = night()
    out.paste(img, (int(dx), int(dy)))
    return out


def light_point(img, x, y, r, strength=1.0, color=(242, 165, 65)):
    """Additive amber glow on copy of img."""
    lay = Image.new('RGB', img.size, (0, 0, 0))
    g = ImageDraw.Draw(lay)
    c = tuple(int(v * strength) for v in color)
    for rad, s in ((r, 1.0), (r * 2.2, 0.45), (r * 4.5, 0.18)):
        cc = tuple(int(v * s) for v in c)
        g.ellipse([x - rad, y - rad, x + rad, y + rad], fill=cc)
    lay = lay.filter(ImageFilter.GaussianBlur(max(1, r * 0.6)))
    a = np.asarray(img, np.uint16) + np.asarray(lay, np.uint16)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def soft_grain(img, frame, amp=0.02):
    """Deterministic luminance grain from frame."""
    rng = np.random.default_rng(1031 + frame)
    arr = np.asarray(img, np.float32)
    g = rng.normal(0, 1, (H, W)).astype(np.float32)
    g = np.asarray(Image.fromarray(((g * 40) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), np.float32)
    g = (g - 128) / 40
    arr *= (1 + amp * g)[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def wipe_reveal(base, full, progress, direction='ltr', feather=40):
    """Reveal full over base with horizontal wipe. progress 0..1."""
    p = float(np.clip(progress, 0, 1))
    if p <= 0: return base
    if p >= 1: return full
    edge = p * (W + 2 * feather) - feather
    xs = np.arange(W, dtype=np.float32)
    if direction == 'ltr':
        a = np.clip((edge - xs) / feather, 0, 1)
    else:
        a = np.clip((xs - (W - edge)) / feather, 0, 1)
    aa = a[None, :, None]
    out = np.asarray(base, np.float32) * (1 - aa) + np.asarray(full, np.float32) * aa
    return Image.fromarray(out.astype(np.uint8))


def column_reveal(base, full, columns, progress_per_col, feather=30):
    """columns: list of (x0,x1); progress_per_col: list of 0..1."""
    out = np.asarray(base, np.float32).copy()
    full_a = np.asarray(full, np.float32)
    for (x0, x1), p in zip(columns, progress_per_col):
        p = float(np.clip(p, 0, 1))
        if p <= 0: continue
        # vertical reveal bottom-up within column, or opacity
        h_edge = p * (H + feather)
        ys = np.arange(H, dtype=np.float32)
        # appear from center-ish: opacity fade
        a = p  # simple opacity for column
        # soft horizontal edges
        xs = np.arange(x0, x1)
        out[:, x0:x1] = out[:, x0:x1] * (1 - a) + full_a[:, x0:x1] * a
    return Image.fromarray(out.astype(np.uint8))


def crossfade(a, b, t):
    t = float(np.clip(t, 0, 1))
    return Image.blend(a, b, t)


def overlay_opacity(base, overlay, a, mask_bbox=None):
    a = float(np.clip(a, 0, 1))
    if a <= 0: return base
    if mask_bbox:
        x0, y0, x1, y1 = mask_bbox
        out = base.copy()
        region = Image.blend(base.crop((x0, y0, x1, y1)), overlay.crop((x0, y0, x1, y1)), a)
        out.paste(region, (x0, y0))
        return out
    return Image.blend(base, overlay, a)


# Chinese reading: ~6 chars/sec → frames hold
def hold_frames_for(text, fps=FPS):
    n = max(1, len([c for c in text if c.strip()]))
    return max(12, int(math.ceil(n / 6.0 * fps)))


def handoff_blend(prev_img, next_img, t, x, y, r0=8, r1=80):
    """Signature transition: scene A darkens, amber point grows, scene B rises from the point.
    t in 0..1 over the handoff window."""
    t = float(np.clip(t, 0, 1))
    if t <= 0: return prev_img
    if t >= 1: return next_img
    # phase 0-0.45: prev darkens + point grows
    # phase 0.45-1: next fades in from point radius wipe
    if t < 0.45:
        u = t / 0.45
        img = multiply_dark(prev_img, 1 - 0.55 * ease_in_cubic(u))
        r = lerp(r0, r1 * 0.5, ease_out_cubic(u))
        return light_point(img, x, y, r, strength=0.5 + 0.5 * u)
    else:
        u = (t - 0.45) / 0.55
        # radial reveal of next
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        dist = np.sqrt((xx - x) ** 2 + (yy - y) ** 2)
        rad = lerp(r1 * 0.4, math.hypot(W, H), ease_in_out_quart(u))
        a = np.clip((rad - dist) / 60.0, 0, 1)[..., None]
        prev = multiply_dark(prev_img, 0.45)
        prev = light_point(prev, x, y, r1 * 0.5 * (1 - u * 0.5), strength=1.0 - 0.5 * u)
        out = np.asarray(prev, np.float32) * (1 - a) + np.asarray(next_img, np.float32) * a
        return Image.fromarray(out.astype(np.uint8))
