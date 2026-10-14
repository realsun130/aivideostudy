"""Stroke rasterization: Pillow (small N) or numpy batch stamps (large N)."""
from __future__ import annotations

import math
import random
from typing import Any, Sequence

import numpy as np
from PIL import Image, ImageDraw


def draw_bristle_stroke(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    angle: float,
    length: float,
    width: float,
    rgba: tuple[int, int, int, int],
    bristles: int = 3,
    jitter: float = 0.35,
    rng: random.Random | None = None,
) -> None:
    rng = rng or random.Random(0)
    ca, sa = math.cos(angle), math.sin(angle)
    px, py = -sa, ca
    half = length * 0.5
    n = max(1, bristles)
    for i in range(n):
        off = (i - (n - 1) * 0.5) * (width * 0.35)
        ox = x + px * off + rng.uniform(-jitter, jitter)
        oy = y + py * off + rng.uniform(-jitter, jitter)
        x0, y0 = ox - ca * half, oy - sa * half
        x1, y1 = ox + ca * half, oy + sa * half
        lw = max(1, int(round(width / max(1, n) + rng.uniform(-0.3, 0.3))))
        r, g, b, a = rgba
        rr = max(0, min(255, r + rng.randint(-6, 6)))
        gg = max(0, min(255, g + rng.randint(-6, 6)))
        bb = max(0, min(255, b + rng.randint(-6, 6)))
        draw.line([(x0, y0), (x1, y1)], fill=(rr, gg, bb, a), width=lw)


def _stamp_oriented_capsule(
    canvas: np.ndarray,
    x: float,
    y: float,
    angle: float,
    length: float,
    width: float,
    color: np.ndarray,
    alpha: float,
) -> None:
    """Blend an oriented capsule into float32 HxWx3 canvas in-place."""
    h, w = canvas.shape[:2]
    ca, sa = math.cos(angle), math.sin(angle)
    half_l = max(0.5, length * 0.5)
    half_w = max(0.4, width * 0.5)
    pad = half_l + half_w + 1.0
    x0 = max(0, int(x - pad))
    x1 = min(w, int(x + pad + 1))
    y0 = max(0, int(y - pad))
    y1 = min(h, int(y + pad + 1))
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.ogrid[y0:y1, x0:x1]
    dx = xx.astype(np.float32) - np.float32(x)
    dy = yy.astype(np.float32) - np.float32(y)
    u = dx * ca + dy * sa
    v = -dx * sa + dy * ca
    # capsule: line segment + radius
    u_clamped = np.clip(u, -half_l, half_l)
    dist2 = (u - u_clamped) ** 2 + v * v
    mask = dist2 <= (half_w * half_w)
    if not mask.any():
        return
    a = np.float32(alpha)
    region = canvas[y0:y1, x0:x1]
    # soft edge
    soft = np.clip(1.0 - np.sqrt(dist2) / (half_w + 1e-6), 0.0, 1.0).astype(np.float32)
    wgt = (soft * a)[..., None]
    col = color.reshape(1, 1, 3)
    region[mask] = region[mask] * (1.0 - wgt[mask]) + col * wgt[mask]


def render_strokes_numpy(
    width: int,
    height: int,
    strokes: Sequence[dict[str, Any]] | dict[str, np.ndarray],
    bg_rgb: tuple[int, int, int] = (12, 8, 6),
    seed: int = 42,
    bristle_extra: bool = True,
) -> Image.Image:
    """Fast path for hundreds of thousands of strokes."""
    canvas = np.empty((height, width, 3), dtype=np.float32)
    canvas[:] = np.array(bg_rgb, dtype=np.float32)

    rng = np.random.default_rng(seed)

    if isinstance(strokes, dict) and "x" in strokes:
        n = int(strokes["x"].shape[0])
        xs = strokes["x"]
        ys = strokes["y"]
        angs = strokes["angle"]
        lens = strokes["len"]
        ws = strokes["w"]
        rs = strokes["r"]
        gs = strokes["g"]
        bs = strokes["b"]
        als = strokes["a"]
        layers = strokes.get("layer_id")
        for i in range(n):
            if i > 0 and i % 50000 == 0:
                print(f"  render {i}/{n}", flush=True)
            col = np.array([rs[i], gs[i], bs[i]], dtype=np.float32)
            # light color jitter
            col = np.clip(col + rng.integers(-5, 6, size=3), 0, 255).astype(np.float32)
            _stamp_oriented_capsule(
                canvas, float(xs[i]), float(ys[i]), float(angs[i]),
                float(lens[i]), float(ws[i]), col, float(als[i]),
            )
            if bristle_extra and layers is not None and int(layers[i]) >= 2 and (i % 3 == 0):
                # occasional second bristle offset
                ang = float(angs[i])
                px, py = -math.sin(ang), math.cos(ang)
                off = float(ws[i]) * 0.25
                _stamp_oriented_capsule(
                    canvas,
                    float(xs[i]) + px * off,
                    float(ys[i]) + py * off,
                    ang,
                    float(lens[i]) * 0.95,
                    max(0.6, float(ws[i]) * 0.55),
                    col,
                    float(als[i]) * 0.7,
                )
    else:
        for i, s in enumerate(strokes):
            if i > 0 and i % 50000 == 0:
                print(f"  render {i}/{len(strokes)}", flush=True)
            col = np.array([s["r"], s["g"], s["b"]], dtype=np.float32)
            col = np.clip(col + rng.integers(-5, 6, size=3), 0, 255).astype(np.float32)
            _stamp_oriented_capsule(
                canvas, float(s["x"]), float(s["y"]), float(s["angle"]),
                float(s["len"]), float(s["w"]), col, float(s["a"]),
            )

    out = np.clip(canvas, 0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGB")


def render_strokes_rgba(
    width: int,
    height: int,
    strokes: Sequence[dict],
    bg_rgb: tuple[int, int, int] = (12, 8, 6),
    seed: int = 42,
) -> Image.Image:
    """Pillow path — use for small stroke counts (< ~40k)."""
    if len(strokes) >= 40000:
        return render_strokes_numpy(width, height, strokes, bg_rgb=bg_rgb, seed=seed)

    base = Image.new("RGBA", (width, height), (*bg_rgb, 255))
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    rng = random.Random(seed)
    for s in strokes:
        alpha = int(max(0, min(255, round(float(s["a"]) * 255))))
        rgba = (int(s["r"]), int(s["g"]), int(s["b"]), alpha)
        bristles = 5 if s.get("layer") == "ink" else (4 if s.get("layer") in ("fine", "detail") else 3)
        draw_bristle_stroke(
            draw,
            float(s["x"]),
            float(s["y"]),
            float(s["angle"]),
            float(s["len"]),
            float(s["w"]),
            rgba,
            bristles=bristles,
            jitter=0.45 if s.get("layer") == "ink" else 0.3,
            rng=rng,
        )
    return Image.alpha_composite(base, layer).convert("RGB")
