"""v0.2: real-photo cutouts (assets/cut/*.png, made by prep_assets.py) -> palette-toned layers.
Sources & licenses: ../assets/CREDITS.md
"""
import os
import numpy as np
from PIL import Image, ImageFilter
from common import *

CUT = os.path.join(PROJ, 'assets', 'cut')


def load_cut(name, width=None, height=None):
    """Return (rgb float HxWx3, alpha float HxW 0..1) at supersampled size (S×)."""
    im = Image.open(os.path.join(CUT, name)).convert('RGBA')
    w0, h0 = im.size
    if width:
        w, h = width, width * h0 / w0
    else:
        w, h = height * w0 / h0, height
    im = im.resize((int(round(w * S)), int(round(h * S))), Image.LANCZOS)
    a = np.asarray(im, np.float32)
    return a[..., :3], a[..., 3] / 255.0


def lum(rgbarr):
    return rgbarr[..., 0] * 0.299 + rgbarr[..., 1] * 0.587 + rgbarr[..., 2] * 0.114


def norm_l(L, alpha, lo=2, hi=98):
    m = alpha > 0.5
    a, b = np.percentile(L[m], lo), np.percentile(L[m], hi)
    return np.clip((L - a) / max(b - a, 1), 0, 1)


def ramp(t, stops):
    """t 0..1 -> colour by piecewise-linear hex stops [(pos, '#hex'), ...]."""
    out = np.zeros(t.shape + (3,), np.float32)
    ps = [p for p, _ in stops]; cs = [np.array(rgb(c), np.float32) for _, c in stops]
    for k in range(3):
        out[..., k] = np.interp(t, ps, [c[k] for c in cs])
    return out


def paste(fr, col, alpha, x0, y0):
    """Composite a toned layer onto fr.base; x0,y0 = top-left in 1x px."""
    X, Y = int(round(x0 * S)), int(round(y0 * S))
    h, w = alpha.shape
    base = np.asarray(fr.base, np.float32).copy()
    ys, xs = slice(max(Y, 0), min(Y + h, H * S)), slice(max(X, 0), min(X + w, W * S))
    cy, cx = slice(ys.start - Y, ys.stop - Y), slice(xs.start - X, xs.stop - X)
    a = alpha[cy, cx][..., None]
    base[ys, xs] = base[ys, xs] * (1 - a) + col[cy, cx] * a
    fr.base = Image.fromarray(base.astype(np.uint8)); fr.d = ImageDraw.Draw(fr.base, 'RGBA')


def light_from(fr, lightrgb, x0, y0, blur=0):
    """Place a light-layer patch (HxWx3 0..255) at x0,y0 (1x) into the additive light layer."""
    lay = np.zeros((H * S, W * S, 3), np.float32)
    X, Y = int(round(x0 * S)), int(round(y0 * S))
    h, w = lightrgb.shape[:2]
    ys, xs = slice(max(Y, 0), min(Y + h, H * S)), slice(max(X, 0), min(X + w, W * S))
    lay[ys, xs] = lightrgb[ys.start - Y:ys.stop - Y, xs.start - X:xs.stop - X]
    fr.add_light_image(Image.fromarray(lay.clip(0, 255).astype(np.uint8)), blur=blur)


def soften_alpha(alpha, px=1.0):
    im = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(px * S))
    a = np.asarray(im, np.float32) / 255
    return np.clip((a - 0.15) / 0.7, 0, 1)        # tighten: cleaner silhouette edge


def rim_light(alpha, side='bottom', width=4, color=None, strength=0.7):
    """Amber rim on the lower edge of a silhouette (light from the fire below)."""
    color = color or P['ember_amber']
    a = Image.fromarray((alpha * 255).astype(np.uint8))
    inner = np.asarray(a.filter(ImageFilter.MinFilter(int(width * S) | 1)), np.float32) / 255
    edge = np.clip(alpha - inner, 0, 1)
    h = alpha.shape[0]
    wy = np.clip((np.arange(h) / h - 0.35) / 0.65, 0, 1)[:, None] if side == 'bottom' else 1
    e = edge * wy * strength
    return e[..., None] * np.array(rgb(color), np.float32)[None, None]
