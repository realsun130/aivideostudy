"""Sketch primitives: paper grain, watercolor washes, scratchy polylines."""

from __future__ import annotations

import math
import random
from typing import Iterable, Sequence

from PIL import Image, ImageDraw, ImageFilter


Point = tuple[float, float]
RGB = tuple[int, int, int]
RGBA = tuple[int, int, int, int]


def seeded_rng(seed: int) -> random.Random:
    return random.Random(seed)


def make_paper(
    width: int,
    height: int,
    paper_rgb: RGB,
    grain: float = 0.08,
    seed: int = 42,
) -> Image.Image:
    """Warm beige paper with medium grain (Style Bible texture.paper)."""
    rng = seeded_rng(seed)
    base = Image.new("RGBA", (width, height), (*paper_rgb, 255))
    px = base.load()
    assert px is not None
    for y in range(height):
        for x in range(width):
            # Sparse grain — sample every pixel but cheap noise
            n = rng.gauss(0, grain * 255)
            r, g, b, a = px[x, y]
            px[x, y] = (
                max(0, min(255, int(r + n))),
                max(0, min(255, int(g + n * 0.9))),
                max(0, min(255, int(b + n * 0.7))),
                a,
            )
    # Soft vignette toward edges (storyboard board feel)
    vignette = Image.new("L", (width, height), 0)
    vd = ImageDraw.Draw(vignette)
    vd.ellipse(
        (-width * 0.1, -height * 0.05, width * 1.1, height * 1.05),
        fill=255,
    )
    vignette = vignette.filter(ImageFilter.GaussianBlur(radius=min(width, height) // 6))
    dark = Image.new("RGBA", (width, height), (40, 30, 25, 0))
    dark_px = dark.load()
    vpx = vignette.load()
    assert dark_px is not None and vpx is not None
    for y in range(0, height, 2):
        for x in range(0, width, 2):
            alpha = int((255 - vpx[x, y]) * 0.22)
            dark_px[x, y] = (50, 35, 28, alpha)
            if x + 1 < width:
                dark_px[x + 1, y] = (50, 35, 28, alpha)
            if y + 1 < height:
                dark_px[x, y + 1] = (50, 35, 28, alpha)
                if x + 1 < width:
                    dark_px[x + 1, y + 1] = (50, 35, 28, alpha)
    return Image.alpha_composite(base, dark)


def watercolor_ellipse(
    canvas: Image.Image,
    bbox: tuple[float, float, float, float],
    color: RGB,
    alpha: int = 110,
    blur: float = 6.0,
) -> None:
    """Semi-transparent wash blob (layer: loose color blocks)."""
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.ellipse(bbox, fill=(*color, alpha))
    if blur > 0:
        overlay = overlay.filter(ImageFilter.GaussianBlur(radius=blur))
    canvas.alpha_composite(overlay)


def watercolor_polygon(
    canvas: Image.Image,
    points: Sequence[Point],
    color: RGB,
    alpha: int = 100,
    blur: float = 4.0,
) -> None:
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.polygon([(int(p[0]), int(p[1])) for p in points], fill=(*color, alpha))
    if blur > 0:
        overlay = overlay.filter(ImageFilter.GaussianBlur(radius=blur))
    canvas.alpha_composite(overlay)


def _jitter_points(
    points: Sequence[Point],
    rng: random.Random,
    amp: float,
) -> list[Point]:
    out: list[Point] = []
    for x, y in points:
        out.append((x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)))
    return out


def scratchy_polyline(
    draw: ImageDraw.ImageDraw,
    points: Sequence[Point],
    color: RGB,
    width: int = 2,
    passes: int = 3,
    jitter: float = 1.8,
    seed: int = 0,
    alpha: int = 220,
) -> None:
    """Multi-pass offset contour (dark burgundy scratchy strokes)."""
    rng = seeded_rng(seed)
    rgba = (*color, alpha)
    for p in range(passes):
        pts = _jitter_points(points, rng, jitter * (0.6 + 0.3 * p))
        # Slight systematic offset per pass (correction stroke feel)
        ox = rng.uniform(-1.2, 1.2)
        oy = rng.uniform(-1.2, 1.2)
        xy = [(int(x + ox), int(y + oy)) for x, y in pts]
        if len(xy) >= 2:
            draw.line(xy, fill=rgba, width=max(1, width - (p // 2)), joint="curve")


def scratchy_ellipse(
    draw: ImageDraw.ImageDraw,
    bbox: tuple[float, float, float, float],
    color: RGB,
    width: int = 2,
    passes: int = 2,
    segments: int = 36,
    jitter: float = 2.0,
    seed: int = 0,
    closed: bool = True,
) -> None:
    left, top, right, bottom = bbox
    cx, cy = (left + right) / 2, (top + bottom) / 2
    rx, ry = (right - left) / 2, (bottom - top) / 2
    pts: list[Point] = []
    n = segments + (1 if closed else 0)
    for i in range(n):
        t = 2 * math.pi * i / segments
        pts.append((cx + rx * math.cos(t), cy + ry * math.sin(t)))
    scratchy_polyline(draw, pts, color, width=width, passes=passes, jitter=jitter, seed=seed)


def construction_ellipse(
    draw: ImageDraw.ImageDraw,
    bbox: tuple[float, float, float, float],
    color: RGB,
    width: int = 1,
) -> None:
    """Thin red-brown construction guide (visible under contours)."""
    draw.ellipse(bbox, outline=(*color, 140), width=width)


def wavy_ear_outline(
    tip: Point,
    root: Point,
    bulge: float,
    side: str,
    samples: int = 14,
) -> list[Point]:
    """Simple lobed ear silhouette path tip→root→tip."""
    x0, y0 = tip
    x1, y1 = root
    pts: list[Point] = []
    # Outer edge
    for i in range(samples + 1):
        t = i / samples
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        # Perpendicular bulge
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy) or 1.0
        px, py = -dy / length, dx / length
        sign = 1.0 if side == "left" else -1.0
        wave = math.sin(t * math.pi) * bulge * sign
        pts.append((x + px * wave, y + py * wave))
    # Inner edge back
    for i in range(samples, -1, -1):
        t = i / samples
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy) or 1.0
        px, py = -dy / length, dx / length
        sign = 1.0 if side == "left" else -1.0
        wave = math.sin(t * math.pi) * bulge * 0.35 * sign
        pts.append((x - px * wave * 0.5, y - py * wave * 0.5))
    return pts


def draw_stress_marks(
    draw: ImageDraw.ImageDraw,
    center: Point,
    color: RGB,
    count: int = 5,
    seed: int = 7,
) -> None:
    """Tiny motion / laugh ticks near face."""
    rng = seeded_rng(seed)
    cx, cy = center
    for i in range(count):
        ang = rng.uniform(-0.8, 0.8) + (i - count / 2) * 0.25
        r0 = rng.uniform(8, 14)
        r1 = r0 + rng.uniform(10, 18)
        x0 = cx + math.cos(ang) * r0
        y0 = cy + math.sin(ang) * r0
        x1 = cx + math.cos(ang) * r1
        y1 = cy + math.sin(ang) * r1
        draw.line([(x0, y0), (x1, y1)], fill=(*color, 180), width=2)
