"""Coarse region labels for V8 single-frame stroke validation.

Masks are ROUGH: axis-aligned bboxes from assets/manifest.json + a 4x3
grid fallback for leftover pixels (pillow / duvet / wall / nightstand).
Not pixel-accurate mattes — good enough to tag strokes for later part animation.
"""
from __future__ import annotations

from typing import Any

import numpy as np

# Rough bboxes in source pixels (1280x720), from manifest + visual layout of V8.
# Format: name -> (x0, y0, x1, y1) inclusive-exclusive style half-open.
REGION_BBOXES: dict[str, tuple[int, int, int, int]] = {
    "wall_photo": (250, 20, 700, 220),
    "cavalier": (420, 180, 900, 620),
    "maine": (780, 200, 1180, 620),
    "phone": (560, 340, 720, 560),
    "paw_lamp": (1040, 220, 1250, 460),
    "nightstand": (1100, 430, 1280, 620),
    "pillow": (300, 280, 520, 480),
    "duvet": (200, 480, 1100, 700),
    "wall": (0, 0, 1280, 280),
    "bed_bg": (0, 250, 400, 520),
}

# Paint order for label priority (later overwrites earlier on overlap).
REGION_PRIORITY = [
    "wall",
    "bed_bg",
    "duvet",
    "pillow",
    "nightstand",
    "wall_photo",
    "cavalier",
    "maine",
    "phone",
    "paw_lamp",
]


def build_region_map(width: int = 1280, height: int = 720) -> np.ndarray:
    """HxW uint8 region id map. 0 = unclassified / grid cell."""
    labels = {name: i + 1 for i, name in enumerate(REGION_PRIORITY)}
    m = np.zeros((height, width), dtype=np.uint8)
    for name in REGION_PRIORITY:
        x0, y0, x1, y1 = REGION_BBOXES[name]
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(width, x1), min(height, y1)
        m[y0:y1, x0:x1] = labels[name]
    return m


def region_id_to_name() -> dict[int, str]:
    return {i + 1: name for i, name in enumerate(REGION_PRIORITY)} | {0: "grid_misc"}


def grid_region_name(x: int, y: int, width: int, height: int, gx: int = 4, gy: int = 3) -> str:
    cx = min(gx - 1, int(x / width * gx))
    cy = min(gy - 1, int(y / height * gy))
    return f"grid_{cy}_{cx}"


def annotate_stroke_region(
    x: float,
    y: float,
    region_map: np.ndarray,
    id_to_name: dict[int, str],
) -> str:
    h, w = region_map.shape
    xi = int(np.clip(round(x), 0, w - 1))
    yi = int(np.clip(round(y), 0, h - 1))
    rid = int(region_map[yi, xi])
    name = id_to_name.get(rid, "grid_misc")
    if name == "grid_misc":
        return grid_region_name(xi, yi, w, h)
    return name


def region_manifest() -> dict[str, Any]:
    return {
        "note": "Rough AABB regions from manifest layout + visual V8 read. Not rembg mattes.",
        "priority": REGION_PRIORITY,
        "bboxes_xyxy": {k: list(v) for k, v in REGION_BBOXES.items()},
    }
