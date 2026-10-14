#!/usr/bin/env python3
"""Analyze V8 → structure-tensor stroke list (JSON).

Pipeline (Claude / huashu-inspired single-frame validation):
  1. structure tensor → orientation + coherence
  2. coarse region tags (rough AABB)
  3. multi-pass strokes: large color → medium → fine → edge ink
  4. write compact stroke JSON + region debug map

Caps stroke count for a runnable v1 (tens of thousands, not millions).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from lib.regions import build_region_map, region_id_to_name, annotate_stroke_region, region_manifest
from lib.structure_tensor import structure_tensor_field


def load_rgb(path: Path) -> np.ndarray:
    im = Image.open(path).convert("RGB")
    return np.asarray(im, dtype=np.float32)


def luminance(rgb: np.ndarray) -> np.ndarray:
    return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]


def sample_color(rgb: np.ndarray, x: float, y: float) -> tuple[int, int, int]:
    h, w = rgb.shape[:2]
    xi = int(np.clip(round(x), 0, w - 1))
    yi = int(np.clip(round(y), 0, h - 1))
    # small neighborhood median-ish mean for stability
    x0, x1 = max(0, xi - 1), min(w, xi + 2)
    y0, y1 = max(0, yi - 1), min(h, yi + 2)
    patch = rgb[y0:y1, x0:x1].reshape(-1, 3)
    c = patch.mean(axis=0)
    return int(c[0]), int(c[1]), int(c[2])


def paint_stroke_approx(
    canvas: np.ndarray,
    x: float,
    y: float,
    angle: float,
    length: float,
    width: float,
    color: tuple[int, int, int],
    alpha: float,
) -> None:
    """Fast residual update: stamp an oriented ellipse onto float canvas."""
    h, w = canvas.shape[:2]
    ca, sa = math.cos(angle), math.sin(angle)
    half_l = length * 0.5
    half_w = max(0.5, width * 0.5)
    # bbox
    pad = half_l + half_w + 1
    x0 = max(0, int(x - pad))
    x1 = min(w, int(x + pad + 1))
    y0 = max(0, int(y - pad))
    y1 = min(h, int(y + pad + 1))
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    dx = xx - x
    dy = yy - y
    # local coords along / across stroke
    u = dx * ca + dy * sa
    v = -dx * sa + dy * ca
    mask = (u * u) / (half_l * half_l + 1e-6) + (v * v) / (half_w * half_w + 1e-6) <= 1.0
    if not mask.any():
        return
    a = alpha
    col = np.array(color, dtype=np.float32)
    region = canvas[y0:y1, x0:x1]
    region[mask] = region[mask] * (1.0 - a) + col * a


def edge_mask(mag: np.ndarray, q: float = 0.88) -> np.ndarray:
    thr = float(np.quantile(mag, q))
    return mag >= thr


def generate(
    rgb: np.ndarray,
    max_strokes: int = 28000,
    seed: int = 42,
) -> tuple[list[dict], dict]:
    rng = np.random.default_rng(seed)
    h, w = rgb.shape[:2]
    gray = luminance(rgb)
    angle, coherence, mag = structure_tensor_field(gray, sigma=2.5)
    region_map = build_region_map(w, h)
    id_to_name = region_id_to_name()

    # start canvas with dark vignette mean of corners (bedroom void)
    canvas = np.zeros_like(rgb)
    mean_c = rgb.reshape(-1, 3).mean(axis=0)
    # bias toward dark wall sample
    dark = rgb[10:40, 10:40].mean(axis=(0, 1))
    canvas[:] = dark * 0.7 + mean_c * 0.3

    strokes: list[dict] = []

    # layer specs: (name, radius/width, length_scale, step, err_thr, alpha, max_frac)
    layers = [
        ("coarse", 14.0, 2.2, 11, 0.045, 0.55, 0.22),
        ("mid", 8.0, 2.0, 7, 0.035, 0.50, 0.28),
        ("fine", 4.0, 1.8, 4, 0.028, 0.45, 0.30),
        ("detail", 2.2, 1.6, 3, 0.022, 0.40, 0.15),
    ]

    budget_left = max_strokes - 2500  # reserve for ink

    for name, width, len_scale, step, err_thr, alpha, frac in layers:
        layer_budget = int(budget_left * frac / 0.95)
        err = np.mean(np.abs(canvas - rgb), axis=2) / 255.0
        # candidate grid with jitter
        ys = np.arange(step // 2, h, step)
        xs = np.arange(step // 2, w, step)
        candidates = []
        for y in ys:
            for x in xs:
                # jitter
                jx = int(x + rng.integers(-step // 3, step // 3 + 1))
                jy = int(y + rng.integers(-step // 3, step // 3 + 1))
                jx = int(np.clip(jx, 0, w - 1))
                jy = int(np.clip(jy, 0, h - 1))
                e = float(err[jy, jx])
                if e < err_thr:
                    continue
                # prefer high-error + some coherence
                score = e * (0.55 + 0.45 * float(coherence[jy, jx]))
                candidates.append((score, jx, jy))
        candidates.sort(reverse=True)
        take = candidates[:layer_budget]
        for score, x, y in take:
            ang = float(angle[y, x])
            # slight random wobble for sketch feel
            ang += float(rng.normal(0, 0.12))
            coh = float(coherence[y, x])
            length = width * len_scale * (0.85 + 0.5 * coh)
            # shorter strokes in low-coherence noisy areas
            if coh < 0.25:
                length *= 0.7
            r, g, b = sample_color(rgb, x, y)
            # darken slightly for pencil wash
            r = int(r * 0.97)
            g = int(g * 0.97)
            b = int(b * 0.97)
            region = annotate_stroke_region(x, y, region_map, id_to_name)
            strokes.append(
                {
                    "x": round(float(x), 2),
                    "y": round(float(y), 2),
                    "angle": round(ang, 4),
                    "len": round(float(length), 2),
                    "w": round(float(width), 2),
                    "r": r,
                    "g": g,
                    "b": b,
                    "a": round(alpha, 3),
                    "layer": name,
                    "region": region,
                }
            )
            paint_stroke_approx(canvas, x, y, ang, length, width, (r, g, b), alpha)
        budget_left = max_strokes - 2500 - len(strokes)
        if budget_left <= 0:
            break

    # edge ink pass — jittered dark contour strokes
    em = edge_mask(mag, q=0.90)
    ink_budget = min(2500, max_strokes - len(strokes))
    ys, xs = np.where(em)
    if len(xs) > 0 and ink_budget > 0:
        # subsample
        idx = rng.choice(len(xs), size=min(len(xs), ink_budget * 3), replace=False)
        scored = []
        for i in idx:
            x, y = int(xs[i]), int(ys[i])
            scored.append((float(mag[y, x]), x, y))
        scored.sort(reverse=True)
        for _, x, y in scored[:ink_budget]:
            ang = float(angle[y, x]) + float(rng.normal(0, 0.18))
            length = float(rng.uniform(4.0, 10.0))
            width = float(rng.uniform(1.0, 1.8))
            # sample near-black burgundy from local dark
            r0, g0, b0 = sample_color(rgb, x, y)
            # push toward contour ink
            r = int(r0 * 0.25 + 40 * 0.3)
            g = int(g0 * 0.25 + 20 * 0.2)
            b = int(b0 * 0.25 + 25 * 0.15)
            r, g, b = max(10, min(r, 80)), max(5, min(g, 55)), max(5, min(b, 55))
            region = annotate_stroke_region(x, y, region_map, id_to_name)
            strokes.append(
                {
                    "x": round(float(x) + float(rng.normal(0, 0.6)), 2),
                    "y": round(float(y) + float(rng.normal(0, 0.6)), 2),
                    "angle": round(ang, 4),
                    "len": round(length, 2),
                    "w": round(width, 2),
                    "r": r,
                    "g": g,
                    "b": b,
                    "a": 0.55,
                    "layer": "ink",
                    "region": region,
                }
            )
            paint_stroke_approx(canvas, x, y, ang, length, width, (r, g, b), 0.35)

    meta = {
        "width": w,
        "height": h,
        "stroke_count": len(strokes),
        "layers": [L[0] for L in layers] + ["ink"],
        "structure_tensor_sigma": 2.5,
        "max_strokes_cap": max_strokes,
        "seed": seed,
        "regions": region_manifest(),
        "honesty": (
            "v1 validation: orientation from structure tensor; regions are rough AABBs; "
            "bristle render is approximate colored-pencil, not a full ETF/Hertzmann clone; "
            "expect soft mush vs photographic/illustration detail of V8."
        ),
    }
    return strokes, meta


def save_region_debug(path: Path, width: int, height: int) -> None:
    m = build_region_map(width, height)
    # colorize
    rng = np.random.default_rng(0)
    palette = np.zeros((32, 3), dtype=np.uint8)
    for i in range(1, 32):
        palette[i] = rng.integers(40, 230, size=3)
    rgb = palette[m]
    Image.fromarray(rgb, "RGB").save(path)


def save_orientation_debug(path: Path, gray: np.ndarray) -> None:
    angle, coh, mag = structure_tensor_field(gray, sigma=2.5)
    # HSV-like: hue from angle, value from coherence
    h = ((angle % math.pi) / math.pi * 255).astype(np.uint8)
    s = np.full_like(h, 200)
    v = (np.clip(coh, 0, 1) * 255).astype(np.uint8)
    hsv = np.stack([h, s, v], axis=-1)
    im = Image.fromarray(hsv, mode="HSV").convert("RGB")
    im.save(path)


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate structure-tensor stroke list from V8")
    ap.add_argument(
        "--source",
        type=Path,
        default=ROOT.parent / "frame_01_s01_hero_v8.jpg",
    )
    ap.add_argument("--out", type=Path, default=ROOT / "out" / "strokes_v8_v1.json")
    ap.add_argument("--max-strokes", type=int, default=28000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    rgb = load_rgb(args.source)
    print(f"source={args.source} size={rgb.shape[1]}x{rgb.shape[0]}", flush=True)
    strokes, meta = generate(rgb, max_strokes=args.max_strokes, seed=args.seed)
    meta["source"] = str(args.source)
    payload = {"meta": meta, "strokes": strokes}
    with args.out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {args.out} strokes={len(strokes)} bytes={args.out.stat().st_size}", flush=True)

    # debug maps
    save_region_debug(args.out.parent / "debug_regions_v8.png", meta["width"], meta["height"])
    save_orientation_debug(args.out.parent / "debug_orientation_v8.png", luminance(rgb))
    # residual preview from approx canvas not saved — render step is source of truth
    layer_counts = {}
    for s in strokes:
        layer_counts[s["layer"]] = layer_counts.get(s["layer"], 0) + 1
    print("layer_counts", layer_counts, flush=True)
    with (args.out.parent / "strokes_v8_v1_meta.json").open("w", encoding="utf-8") as f:
        json.dump({"meta": meta, "layer_counts": layer_counts}, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
