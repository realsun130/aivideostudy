#!/usr/bin/env python3
"""Compare stroke render vs original: MSE, PSNR, diff heatmap."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--original", type=Path, required=True)
    ap.add_argument("--render", type=Path, required=True)
    ap.add_argument("--out-heatmap", type=Path, required=True)
    ap.add_argument("--out-metrics", type=Path, required=True)
    ap.add_argument("--out-side-by-side", type=Path, default=None)
    args = ap.parse_args()

    a = np.asarray(Image.open(args.original).convert("RGB"), dtype=np.float64)
    b = np.asarray(Image.open(args.render).convert("RGB"), dtype=np.float64)
    if a.shape != b.shape:
        raise SystemExit(f"shape mismatch {a.shape} vs {b.shape}")

    diff = a - b
    mse = float(np.mean(diff ** 2))
    rmse = float(np.sqrt(mse))
    if mse <= 1e-12:
        psnr = 99.0
    else:
        psnr = float(20.0 * np.log10(255.0) - 10.0 * np.log10(mse))
    mae = float(np.mean(np.abs(diff)))

    # heatmap: mean abs channel error, turbo-ish via grayscale stretch + tint
    err = np.mean(np.abs(diff), axis=2)
    err_n = err / (err.max() + 1e-8)
    heat = np.zeros((*err.shape, 3), dtype=np.uint8)
    # black → red → yellow
    heat[..., 0] = np.clip(err_n * 255 * 1.2, 0, 255).astype(np.uint8)
    heat[..., 1] = np.clip((err_n - 0.35) / 0.65 * 255, 0, 255).astype(np.uint8)
    heat[..., 2] = np.clip((err_n - 0.7) / 0.3 * 180, 0, 255).astype(np.uint8)
    args.out_heatmap.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(heat, "RGB").save(args.out_heatmap)

    metrics = {
        "mse": round(mse, 4),
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "psnr_db": round(psnr, 3),
        "original": str(args.original),
        "render": str(args.render),
        "width": int(a.shape[1]),
        "height": int(a.shape[0]),
        "note": "Higher PSNR / lower MSE is better. v1 stroke paint will be well below photo-match.",
    }
    args.out_metrics.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2), flush=True)

    if args.out_side_by_side:
        oa = Image.open(args.original).convert("RGB")
        ob = Image.open(args.render).convert("RGB")
        oh = Image.fromarray(heat, "RGB")
        # scale heatmap labels not needed
        gap = 8
        canvas = Image.new("RGB", (oa.width * 3 + gap * 2, oa.height), (20, 16, 14))
        canvas.paste(oa, (0, 0))
        canvas.paste(ob, (oa.width + gap, 0))
        canvas.paste(oh, (oa.width * 2 + gap * 2, 0))
        canvas.save(args.out_side_by_side)
        print(f"wrote {args.out_side_by_side}", flush=True)


if __name__ == "__main__":
    main()
