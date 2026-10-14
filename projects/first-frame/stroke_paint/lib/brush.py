"""Bristle-ish stroke rasterization with Pillow."""
from __future__ import annotations

import math
import random
from typing import Sequence

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
    """Draw a short stroke as several slightly offset thin lines (colored pencil feel)."""
    rng = rng or random.Random(0)
    ca, sa = math.cos(angle), math.sin(angle)
    # perpendicular for bristle spread
    px, py = -sa, ca
    half = length * 0.5
    n = max(1, bristles)
    for i in range(n):
        off = (i - (n - 1) * 0.5) * (width * 0.35)
        ox = x + px * off + rng.uniform(-jitter, jitter)
        oy = y + py * off + rng.uniform(-jitter, jitter)
        x0 = ox - ca * half
        y0 = oy - sa * half
        x1 = ox + ca * half
        y1 = oy + sa * half
        # thin line width; at least 1
        lw = max(1, int(round(width / max(1, n) + rng.uniform(-0.3, 0.3))))
        r, g, b, a = rgba
        # slight color jitter per bristle
        rr = max(0, min(255, r + rng.randint(-6, 6)))
        gg = max(0, min(255, g + rng.randint(-6, 6)))
        bb = max(0, min(255, b + rng.randint(-6, 6)))
        draw.line([(x0, y0), (x1, y1)], fill=(rr, gg, bb, a), width=lw)


def render_strokes_rgba(
    width: int,
    height: int,
    strokes: Sequence[dict],
    bg_rgb: tuple[int, int, int] = (12, 8, 6),
    seed: int = 42,
) -> Image.Image:
    """Composite all strokes onto an RGBA canvas; return RGB image."""
    base = Image.new("RGBA", (width, height), (*bg_rgb, 255))
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    rng = random.Random(seed)

    # batch: draw in list order (coarse → fine → ink already sorted by generator)
    for s in strokes:
        a = float(s["a"])
        alpha = int(max(0, min(255, round(a * 255))))
        rgba = (int(s["r"]), int(s["g"]), int(s["b"]), alpha)
        bristles = 5 if s.get("layer") == "ink" else (4 if s.get("layer") == "fine" else 3)
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
        # flush periodically to keep memory calm — actually one layer is fine

    out = Image.alpha_composite(base, layer)
    return out.convert("RGB")
