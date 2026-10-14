#!/usr/bin/env python3
"""Analyze V8 → structure-tensor stroke list (JSON meta + NPZ arrays).

v2 supports >=400k strokes via vectorized candidate picking and
layer-wise residual updates (no per-stroke mgrid during selection).
"""
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

from lib.regions import build_region_map, region_id_to_name, region_manifest
from lib.structure_tensor import structure_tensor_field

LAYER_NAMES = ["coarse", "mid", "fine", "detail", "micro", "ink"]
LAYER_TO_ID = {n: i for i, n in enumerate(LAYER_NAMES)}


def load_rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)


def luminance(rgb: np.ndarray) -> np.ndarray:
    return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]


def stamp_layer_pil(
    canvas: np.ndarray,
    xs: np.ndarray,
    ys: np.ndarray,
    angs: np.ndarray,
    lens: np.ndarray,
    ws: np.ndarray,
    rs: np.ndarray,
    gs: np.ndarray,
    bs: np.ndarray,
    als: np.ndarray,
) -> np.ndarray:
    """Composite a whole layer onto canvas using PIL lines (fast enough for residual)."""
    base = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    # draw in chunks to limit peak memory of draw state
    from PIL import ImageDraw

    draw = ImageDraw.Draw(overlay)
    n = len(xs)
    for i in range(n):
        ca, sa = math.cos(float(angs[i])), math.sin(float(angs[i]))
        half = float(lens[i]) * 0.5
        x, y = float(xs[i]), float(ys[i])
        x0, y0 = x - ca * half, y - sa * half
        x1, y1 = x + ca * half, y + sa * half
        a = int(max(0, min(255, round(float(als[i]) * 255))))
        lw = max(1, int(round(float(ws[i]))))
        draw.line([(x0, y0), (x1, y1)], fill=(int(rs[i]), int(gs[i]), int(bs[i]), a), width=lw)
    out = Image.alpha_composite(base, overlay).convert("RGB")
    return np.asarray(out, dtype=np.float32)


def pick_candidates(
    err: np.ndarray,
    coherence: np.ndarray,
    step: int,
    err_thr: float,
    budget: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Return x,y int arrays of up to `budget` candidates on a jittered grid."""
    h, w = err.shape
    # build grid indices
    ys = np.arange(step // 2, h, step, dtype=np.int32)
    xs = np.arange(step // 2, w, step, dtype=np.int32)
    yy, xx = np.meshgrid(ys, xs, indexing="ij")
    yy = yy.ravel()
    xx = xx.ravel()
    # jitter
    jx = xx + rng.integers(-max(1, step // 3), max(2, step // 3 + 1), size=xx.shape[0])
    jy = yy + rng.integers(-max(1, step // 3), max(2, step // 3 + 1), size=yy.shape[0])
    jx = np.clip(jx, 0, w - 1)
    jy = np.clip(jy, 0, h - 1)
    e = err[jy, jx]
    mask = e >= err_thr
    jx, jy, e = jx[mask], jy[mask], e[mask]
    if jx.size == 0:
        return np.zeros(0, dtype=np.int32), np.zeros(0, dtype=np.int32)
    score = e * (0.55 + 0.45 * coherence[jy, jx])
    if jx.size > budget:
        # partial top-k via argpartition
        idx = np.argpartition(-score, budget)[:budget]
        jx, jy, score = jx[idx], jy[idx], score[idx]
    # shuffle high scores slightly so spatial order isn't pure raster
    order = np.argsort(-score)
    return jx[order].astype(np.int32), jy[order].astype(np.int32)


def pick_dense_error(
    err: np.ndarray,
    coherence: np.ndarray,
    err_thr: float,
    budget: int,
    rng: np.random.Generator,
    stride: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    h, w = err.shape
    if stride > 1:
        sub = err[::stride, ::stride]
        coh = coherence[::stride, ::stride]
        ys, xs = np.where(sub >= err_thr)
        if xs.size == 0:
            return np.zeros(0, dtype=np.int32), np.zeros(0, dtype=np.int32)
        xs = xs * stride + rng.integers(0, stride, size=xs.shape[0])
        ys = ys * stride + rng.integers(0, stride, size=ys.shape[0])
        xs = np.clip(xs, 0, w - 1)
        ys = np.clip(ys, 0, h - 1)
    else:
        ys, xs = np.where(err >= err_thr)
        if xs.size == 0:
            return np.zeros(0, dtype=np.int32), np.zeros(0, dtype=np.int32)
    score = err[ys, xs] * (0.5 + 0.5 * coherence[ys, xs])
    if xs.size > budget * 3:
        # random pre-subsample then top-k
        pick = rng.choice(xs.size, size=budget * 3, replace=False)
        xs, ys, score = xs[pick], ys[pick], score[pick]
    if xs.size > budget:
        idx = np.argpartition(-score, budget)[:budget]
        xs, ys = xs[idx], ys[idx]
    return xs.astype(np.int32), ys.astype(np.int32)


def build_strokes_at(
    xs: np.ndarray,
    ys: np.ndarray,
    rgb: np.ndarray,
    angle: np.ndarray,
    coherence: np.ndarray,
    width: float,
    len_scale: float,
    alpha: float,
    layer_id: int,
    region_map: np.ndarray,
    rng: np.random.Generator,
    angle_jitter: float = 0.12,
) -> dict[str, np.ndarray]:
    n = xs.shape[0]
    angs = angle[ys, xs].astype(np.float32) + rng.normal(0, angle_jitter, size=n).astype(np.float32)
    coh = coherence[ys, xs].astype(np.float32)
    lens = (width * len_scale * (0.85 + 0.5 * coh)).astype(np.float32)
    lens = np.where(coh < 0.25, lens * 0.7, lens).astype(np.float32)
    # color from rgb with tiny neighborhood via direct sample
    cols = rgb[ys, xs]
    rs = np.clip(cols[:, 0] * 0.97, 0, 255).astype(np.uint8)
    gs = np.clip(cols[:, 1] * 0.97, 0, 255).astype(np.uint8)
    bs = np.clip(cols[:, 2] * 0.97, 0, 255).astype(np.uint8)
    regions = region_map[ys, xs].astype(np.uint8)
    return {
        "x": xs.astype(np.float32) + rng.normal(0, 0.35, size=n).astype(np.float32),
        "y": ys.astype(np.float32) + rng.normal(0, 0.35, size=n).astype(np.float32),
        "angle": angs,
        "len": lens,
        "w": np.full(n, width, dtype=np.float32),
        "r": rs,
        "g": gs,
        "b": bs,
        "a": np.full(n, alpha, dtype=np.float32),
        "layer_id": np.full(n, layer_id, dtype=np.uint8),
        "region_id": regions,
    }


def concat_stroke_dicts(parts: list[dict[str, np.ndarray]]) -> dict[str, np.ndarray]:
    keys = parts[0].keys()
    return {k: np.concatenate([p[k] for p in parts], axis=0) for k in keys}


def generate(
    rgb: np.ndarray,
    max_strokes: int = 420000,
    seed: int = 42,
) -> tuple[dict[str, np.ndarray], dict]:
    rng = np.random.default_rng(seed)
    h, w = rgb.shape[:2]
    gray = luminance(rgb)
    print("structure tensor…", flush=True)
    angle, coherence, mag = structure_tensor_field(gray, sigma=2.5)
    region_map = build_region_map(w, h)

    dark = rgb[10:40, 10:40].mean(axis=(0, 1))
    mean_c = rgb.reshape(-1, 3).mean(axis=0)
    canvas = np.zeros_like(rgb)
    canvas[:] = dark * 0.7 + mean_c * 0.3

    ink_reserve = min(50000, max(8000, max_strokes // 9))
    paint_budget = max_strokes - ink_reserve

    # (name, width, len_scale, step_or_mode, err_thr, alpha, frac_of_paint_budget)
    # step int => grid; "denseN" => dense with stride N
    specs = [
        ("coarse", 12.0, 2.1, 7, 0.035, 0.52, 0.05),
        ("mid", 7.0, 2.0, 3, 0.026, 0.48, 0.11),
        ("fine", 3.8, 1.85, 2, 0.018, 0.42, 0.20),
        ("detail", 2.2, 1.65, "dense2", 0.012, 0.38, 0.28),
        ("micro", 1.35, 1.45, "dense1", 0.007, 0.34, 0.36),
    ]

    parts: list[dict[str, np.ndarray]] = []
    used = 0

    for name, width, len_scale, step, err_thr, alpha, frac in specs:
        budget = int(paint_budget * frac)
        budget = min(budget, paint_budget - used)
        if budget <= 0:
            break
        err = np.mean(np.abs(canvas - rgb), axis=2) / 255.0
        print(f"layer {name}: budget={budget} err_mean={err.mean():.4f}", flush=True)
        if isinstance(step, str) and step.startswith("dense"):
            stride = int(step.replace("dense", "") or "1")
            xs, ys = pick_dense_error(err, coherence, err_thr, budget, rng, stride=stride)
        else:
            xs, ys = pick_candidates(err, coherence, int(step), err_thr, budget, rng)
        if xs.size == 0:
            print(f"  skip empty {name}", flush=True)
            continue
        # if still under budget and dense, relax threshold once
        if xs.size < budget * 0.85 and isinstance(step, str):
            xs2, ys2 = pick_dense_error(err, coherence, err_thr * 0.6, budget, rng, stride=1)
            xs, ys = xs2, ys2
        lid = LAYER_TO_ID[name]
        chunk = build_strokes_at(
            xs, ys, rgb, angle, coherence, width, len_scale, alpha, lid, region_map, rng,
            angle_jitter=0.10 if name != "micro" else 0.08,
        )
        parts.append(chunk)
        used += chunk["x"].shape[0]
        print(f"  placed {chunk['x'].shape[0]} (total {used})", flush=True)
        # layer-wise residual update
        canvas = stamp_layer_pil(
            canvas,
            chunk["x"], chunk["y"], chunk["angle"], chunk["len"], chunk["w"],
            chunk["r"], chunk["g"], chunk["b"], chunk["a"],
        )

    # edge ink
    thr = float(np.quantile(mag, 0.86))
    em = mag >= thr
    ys_e, xs_e = np.where(em)
    ink_n = min(ink_reserve, max_strokes - used)
    if xs_e.size and ink_n > 0:
        if xs_e.size > ink_n * 4:
            pick = rng.choice(xs_e.size, size=ink_n * 4, replace=False)
            xs_e, ys_e = xs_e[pick], ys_e[pick]
        score = mag[ys_e, xs_e]
        if xs_e.size > ink_n:
            idx = np.argpartition(-score, ink_n)[:ink_n]
            xs_e, ys_e = xs_e[idx], ys_e[idx]
        n = xs_e.shape[0]
        angs = angle[ys_e, xs_e] + rng.normal(0, 0.18, size=n).astype(np.float32)
        cols = rgb[ys_e, xs_e]
        rs = np.clip(cols[:, 0] * 0.25 + 12, 10, 80).astype(np.uint8)
        gs = np.clip(cols[:, 1] * 0.25 + 8, 5, 55).astype(np.uint8)
        bs = np.clip(cols[:, 2] * 0.25 + 8, 5, 55).astype(np.uint8)
        ink = {
            "x": xs_e.astype(np.float32) + rng.normal(0, 0.6, size=n).astype(np.float32),
            "y": ys_e.astype(np.float32) + rng.normal(0, 0.6, size=n).astype(np.float32),
            "angle": angs.astype(np.float32),
            "len": rng.uniform(3.5, 9.5, size=n).astype(np.float32),
            "w": rng.uniform(0.9, 1.7, size=n).astype(np.float32),
            "r": rs,
            "g": gs,
            "b": bs,
            "a": np.full(n, 0.50, dtype=np.float32),
            "layer_id": np.full(n, LAYER_TO_ID["ink"], dtype=np.uint8),
            "region_id": region_map[ys_e, xs_e].astype(np.uint8),
        }
        parts.append(ink)
        used += n
        print(f"layer ink: placed {n} (total {used})", flush=True)

    strokes = concat_stroke_dicts(parts)
    layer_counts = {
        LAYER_NAMES[i]: int(np.sum(strokes["layer_id"] == i)) for i in range(len(LAYER_NAMES))
    }
    meta = {
        "width": w,
        "height": h,
        "stroke_count": int(strokes["x"].shape[0]),
        "layers": LAYER_NAMES,
        "layer_counts": layer_counts,
        "structure_tensor_sigma": 2.5,
        "max_strokes_cap": max_strokes,
        "seed": seed,
        "storage": "npz",
        "regions": region_manifest(),
        "region_id_to_name": region_id_to_name(),
        "honesty": (
            "v2 high-density validation: >=400k strokes, vectorized placement, "
            "layer-wise residual. Regions still rough AABBs. Expect better PSNR than v1 "
            "but still below illustration-perfect match."
        ),
        "version": "v2",
    }
    return strokes, meta


def save_strokes(out_json: Path, strokes: dict[str, np.ndarray], meta: dict) -> Path:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    npz_path = out_json.with_suffix(".npz")
    np.savez_compressed(npz_path, **strokes)
    payload = {
        "meta": meta,
        "storage": "npz",
        "npz": npz_path.name,
        "fields": list(strokes.keys()),
    }
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    meta_path = out_json.parent / (out_json.stem + "_meta.json")
    meta_path.write_text(
        json.dumps({"meta": meta, "layer_counts": meta["layer_counts"]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return npz_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=ROOT.parent / "frame_01_s01_hero_v8.jpg")
    ap.add_argument("--out", type=Path, default=ROOT / "out" / "strokes_v8_v2.json")
    ap.add_argument("--max-strokes", type=int, default=420000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rgb = load_rgb(args.source)
    print(f"source={args.source} size={rgb.shape[1]}x{rgb.shape[0]} cap={args.max_strokes}", flush=True)
    strokes, meta = generate(rgb, max_strokes=args.max_strokes, seed=args.seed)
    meta["source"] = str(args.source)
    npz = save_strokes(args.out, strokes, meta)
    print(
        f"wrote {args.out} + {npz} strokes={meta['stroke_count']} "
        f"npz_bytes={npz.stat().st_size}",
        flush=True,
    )
    print("layer_counts", meta["layer_counts"], flush=True)


if __name__ == "__main__":
    main()
