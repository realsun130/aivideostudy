#!/usr/bin/env python3
"""Render stroke list (JSON dicts or NPZ columnar) → PNG."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def load_strokes(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    meta = data.get("meta", data)
    if data.get("storage") == "npz" or "npz" in data:
        npz_name = data.get("npz") or path.with_suffix(".npz").name
        npz_path = path.parent / npz_name
        return meta, dict(np.load(npz_path))
    return meta, data["strokes"]


def tone_match(render: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Per-channel affine match of mean/std toward reference (light correction)."""
    out = render.astype(np.float64)
    ref = reference.astype(np.float64)
    for c in range(3):
        m_o, s_o = out[..., c].mean(), out[..., c].std() + 1e-6
        m_r, s_r = ref[..., c].mean(), ref[..., c].std() + 1e-6
        # blend match so we don't overfit noise
        matched = (out[..., c] - m_o) * (s_r / s_o) + m_r
        out[..., c] = out[..., c] * 0.25 + matched * 0.75
    return np.clip(out, 0, 255).astype(np.uint8)


def render_cv2(
    width: int,
    height: int,
    strokes: dict,
    bg: tuple[int, int, int],
    seed: int,
    color_jitter: int = 3,
) -> Image.Image:
    import cv2

    canvas = np.zeros((height, width, 3), dtype=np.float32)
    canvas[:] = (bg[2], bg[1], bg[0])  # BGR
    rng = np.random.default_rng(seed)

    n = int(strokes["x"].shape[0])
    xs, ys = strokes["x"], strokes["y"]
    angs, lens, ws = strokes["angle"], strokes["len"], strokes["w"]
    rs, gs, bs, als = strokes["r"], strokes["g"], strokes["b"], strokes["a"]
    layer_ids = strokes.get("layer_id")

    batch = 25000
    for start in range(0, n, batch):
        end = min(n, start + batch)
        if start and start % 100000 == 0:
            print(f"  render {start}/{n}", flush=True)
        layer = np.zeros((height, width, 4), dtype=np.uint8)
        for i in range(start, end):
            ang = float(angs[i])
            ca, sa = math.cos(ang), math.sin(ang)
            half = float(lens[i]) * 0.5
            x, y = float(xs[i]), float(ys[i])
            x0, y0 = int(round(x - ca * half)), int(round(y - sa * half))
            x1, y1 = int(round(x + ca * half)), int(round(y + sa * half))
            a = int(max(0, min(255, round(float(als[i]) * 255))))
            if color_jitter > 0:
                j = rng.integers(-color_jitter, color_jitter + 1, size=3)
            else:
                j = (0, 0, 0)
            bgr = (
                int(np.clip(int(bs[i]) + int(j[2]), 0, 255)),
                int(np.clip(int(gs[i]) + int(j[1]), 0, 255)),
                int(np.clip(int(rs[i]) + int(j[0]), 0, 255)),
            )
            lw = max(1, int(round(float(ws[i]))))
            cv2.line(layer, (x0, y0), (x1, y1), (*bgr, a), thickness=lw, lineType=cv2.LINE_AA)
            # light bristle twin on fine+ layers (less often than v2 to protect PSNR)
            if layer_ids is not None and int(layer_ids[i]) >= 2 and (i % 6 == 0):
                px, py = -sa, ca
                off = float(ws[i]) * 0.28
                cv2.line(
                    layer,
                    (int(round(x0 + px * off)), int(round(y0 + py * off))),
                    (int(round(x1 + px * off)), int(round(y1 + py * off))),
                    (*bgr, max(1, (a * 2) // 3)),
                    thickness=max(1, lw - 1),
                    lineType=cv2.LINE_AA,
                )
        rgb = layer[..., :3].astype(np.float32)
        a = layer[..., 3:4].astype(np.float32) / 255.0
        canvas = canvas * (1.0 - a) + rgb * a

    out = np.clip(canvas, 0, 255).astype(np.uint8)[:, :, ::-1]
    return Image.fromarray(out, "RGB")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strokes", type=Path, default=ROOT / "out" / "strokes_v8_v2.json")
    ap.add_argument("--out", type=Path, default=ROOT / "out" / "stroke_v8_v2.png")
    ap.add_argument("--bg", default="12,8,6")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--color-jitter", type=int, default=3)
    ap.add_argument(
        "--tone-match",
        type=Path,
        default=None,
        help="Optional reference image for light per-channel mean/std match",
    )
    args = ap.parse_args()

    meta, strokes = load_strokes(args.strokes)
    w, h = int(meta["width"]), int(meta["height"])
    bg = tuple(int(x) for x in args.bg.split(","))
    n = int(strokes["x"].shape[0]) if isinstance(strokes, dict) else len(strokes)
    print(f"rendering {n} strokes @ {w}x{h}", flush=True)

    if isinstance(strokes, dict):
        try:
            im = render_cv2(w, h, strokes, bg, args.seed, color_jitter=args.color_jitter)
        except Exception as e:
            print(f"cv2 failed ({e}); numpy fallback", flush=True)
            from lib.brush import render_strokes_numpy

            im = render_strokes_numpy(w, h, strokes, bg_rgb=bg, seed=args.seed)
    else:
        from lib.brush import render_strokes_rgba

        im = render_strokes_rgba(w, h, strokes, bg_rgb=bg, seed=args.seed)

    if args.tone_match is not None:
        ref = np.asarray(Image.open(args.tone_match).convert("RGB"))
        arr = tone_match(np.asarray(im), ref)
        im = Image.fromarray(arr, "RGB")
        print(f"tone-matched to {args.tone_match}", flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    im.save(args.out, optimize=True)
    print(f"wrote {args.out} size={args.out.stat().st_size}", flush=True)


if __name__ == "__main__":
    main()
