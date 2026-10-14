#!/usr/bin/env python3
"""
Build a character-free background plate for the Frame 01 compositor.

Source: V8 hero.
Hole mask: rembg full-frame matte ∪ paw_lamp bbox ∪ subject head-tops,
with wall_photo ROI + thin left/bottom strips protected.

Fill: multi-scale Gaussian blur seeded with wall/pillow/bed means + mild
noise/hatch (Pillow/numpy only — no OpenCV).

Residual: soft mush in subject holes, lamp-glow smear, possible ear/edge
halos. Good enough to stop character double-exposure when rembg alphas stack.

From repo root:
  python3 projects/first-frame/scripts/build_clean_plate.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

REPO = Path(__file__).resolve().parents[3]
FF = REPO / "projects" / "first-frame"
DEFAULT_SRC = FF / "frame_01_s01_hero_v8.jpg"
DEFAULT_MATTE = FF / "assets" / "layers_alpha" / "v8_full_rgba.png"
DEFAULT_MANIFEST = FF / "assets" / "manifest.json"
DEFAULT_OUT = FF / "assets" / "base" / "base_plate_clean.jpg"
DEFAULT_MASK_DEBUG = FF / "assets" / "base" / "base_plate_clean_mask.png"


def build_mask(
    alpha: np.ndarray,
    manifest: dict,
    *,
    alpha_thresh: int = 18,
) -> Image.Image:
    h, w = alpha.shape
    m = (alpha > alpha_thresh).astype(np.uint8) * 255
    mask = Image.fromarray(m, mode="L")

    assets = {a["id"]: a for a in manifest.get("assets", [])}
    bb = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(bb)

    if "paw_lamp" in assets:
        lamp = assets["paw_lamp"]["bbox"]
        d.rectangle(
            (
                lamp["x"] - 6,
                lamp["y"] - 6,
                lamp["x"] + lamp["w"] + 6,
                lamp["y"] + lamp["h"] + 6,
            ),
            fill=255,
        )

    # head-top pads only — catch ears without huge rectangles
    for aid in ("live_maine_coon", "cavalier_subject"):
        if aid not in assets:
            continue
        b = assets[aid]["bbox"]
        top_h = int(b["h"] * 0.35)
        d.rectangle(
            (b["x"] + 20, b["y"] - 8, b["x"] + b["w"] - 20, b["y"] + top_h),
            fill=255,
        )

    mask = Image.fromarray(np.maximum(np.array(mask), np.array(bb)), mode="L")
    mask = mask.filter(ImageFilter.MaxFilter(7))
    mask = mask.filter(ImageFilter.MaxFilter(7))
    mask = mask.filter(ImageFilter.GaussianBlur(radius=3))

    prot = Image.new("L", (w, h), 0)
    pd = ImageDraw.Draw(prot)
    if "wall_photo" in assets:
        wp = assets["wall_photo"]["bbox"]
        pd.rectangle(
            (
                wp["x"] - 12,
                wp["y"] - 12,
                wp["x"] + wp["w"] + 12,
                min(wp["y"] + wp["h"] + 8, 225),
            ),
            fill=255,
        )
    pd.rectangle((0, h - 40, w, h), fill=255)
    pd.rectangle((0, 0, 35, h), fill=255)

    mask_arr = np.array(mask, dtype=np.float64) * (
        1.0 - np.array(prot, dtype=np.float64) / 255.0
    )
    return Image.fromarray(np.clip(mask_arr, 0, 255).astype(np.uint8), mode="L")


def blur_fill(rgb: np.ndarray, hole: np.ndarray, mask_img: Image.Image) -> np.ndarray:
    h, w, _ = rgb.shape
    known = ~hole

    def mean_or(region_rgb, region_known, fallback):
        if region_known.any():
            return region_rgb[region_known].mean(axis=0)
        return np.asarray(fallback, dtype=np.float64)

    wall_mean = mean_or(rgb[0:100, 80:500], known[0:100, 80:500], [12, 8, 8])
    pillow_fallback = np.array([72.0, 52.0, 48.0])
    mid_mean = mean_or(rgb[300:520], known[300:520], pillow_fallback)
    mid_mean = 0.35 * mid_mean + 0.65 * pillow_fallback
    bed_mean = mean_or(rgb[580:720], known[580:720], [58, 40, 36])

    yy = np.linspace(0, 1, h)[:, None]
    seed = np.zeros_like(rgb, dtype=np.float64)
    for c in range(3):
        seed[:, :, c] = np.where(
            yy < 0.22,
            wall_mean[c],
            np.where(yy < 0.58, mid_mean[c], bed_mean[c]),
        )
    rng = np.random.default_rng(42)
    seed = np.clip(seed + rng.normal(0, 6, size=rgb.shape), 0, 255)

    work = rgb.astype(np.float64).copy()
    work[hole] = seed[hole]

    feather = mask_img.filter(ImageFilter.GaussianBlur(radius=8))
    a = np.clip(np.array(feather, dtype=np.float64) / 255.0, 0, 1)

    out = work.copy()
    for r in (40, 24, 12, 6, 3):
        pil = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), mode="RGB")
        blurred = np.array(
            pil.filter(ImageFilter.GaussianBlur(radius=r)), dtype=np.float64
        )
        for c in range(3):
            out[:, :, c] = np.where(
                a > 0.01,
                blurred[:, :, c] * a + out[:, :, c] * (1 - a),
                out[:, :, c],
            )
            out[:, :, c] = np.where(hole, out[:, :, c], rgb[:, :, c])

    for c in range(3):
        out[:, :, c] = rgb[:, :, c] * (1 - a) + out[:, :, c] * a

    # mild hatch from source detail into holes
    wall_blur = np.array(
        Image.fromarray(rgb).filter(ImageFilter.GaussianBlur(5)), dtype=np.float64
    )
    detail = rgb.astype(np.float64) - wall_blur
    for c in range(3):
        out[:, :, c] = np.where(
            hole, np.clip(out[:, :, c] + detail[:, :, c] * 0.25, 0, 255), out[:, :, c]
        )
    return np.clip(out, 0, 255).astype(np.uint8)


def main() -> None:
    ap = argparse.ArgumentParser(description="Build clean base plate (no characters)")
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC)
    ap.add_argument("--matte", type=Path, default=DEFAULT_MATTE)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--mask-debug", type=Path, default=DEFAULT_MASK_DEBUG)
    ap.add_argument("--alpha-thresh", type=int, default=18)
    args = ap.parse_args()

    src = Image.open(args.src).convert("RGB")
    matte = Image.open(args.matte).convert("RGBA")
    if matte.size != src.size:
        matte = matte.resize(src.size, Image.Resampling.LANCZOS)
    alpha = np.array(matte.split()[-1])
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))

    mask_img = build_mask(alpha, manifest, alpha_thresh=args.alpha_thresh)
    hole = np.array(mask_img) > 36
    print(
        f"src={args.src.name} size={src.size} hole_coverage={hole.mean()*100:.1f}%",
        flush=True,
    )

    filled = blur_fill(np.array(src), hole, mask_img)
    out = Image.fromarray(filled, mode="RGB")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.save(args.out, "JPEG", quality=92, optimize=True)
    mask_img.save(args.mask_debug, "PNG", optimize=True)
    print(f"wrote {args.out.relative_to(REPO)}")
    print(f"wrote mask debug {args.mask_debug.relative_to(REPO)}")
    print(
        "honesty: subject holes are soft pillow/wall mush (blur fill, not generative "
        "inpaint); nightstand/lamp glow may smear; ear edges may halo. "
        "Stops baked-character double-exposure when rembg alphas are restacked.",
        flush=True,
    )


if __name__ == "__main__":
    main()
