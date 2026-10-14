#!/usr/bin/env python3
"""Hertzmann-style painterly strokes for V8 (v3).

Coarse-to-fine layers; orientation from multi-scale structure tensor;
color sampled from the source (no darkening); curved strokes follow the
isophote field; highlight/edge regions get denser coverage.
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

LAYER_NAMES = ["coarse", "mid", "fine", "detail", "micro", "highlight", "ink"]
LAYER_TO_ID = {n: i for i, n in enumerate(LAYER_NAMES)}


def load_rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)


def luminance(rgb: np.ndarray) -> np.ndarray:
    return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]


def gaussian_blur_rgb(rgb: np.ndarray, sigma: float) -> np.ndarray:
    """Approx separable Gaussian via PIL (fast, good enough for ref blur)."""
    if sigma <= 0.35:
        return rgb.copy()
    rad = max(1, int(round(sigma * 2)))
    im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")
    # Box blur iterations approximate Gaussian
    from PIL import ImageFilter

    out = im
    # radius ~ sigma * 0.85 empirically for box
    r = max(1, int(round(sigma * 0.9)))
    for _ in range(2):
        out = out.filter(ImageFilter.BoxBlur(r))
    return np.asarray(out, dtype=np.float32)


def stamp_layer_cv2(
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
    """Composite strokes onto canvas (RGB float) matching final AA line look."""
    import cv2

    h, w = canvas.shape[:2]
    base = np.clip(canvas, 0, 255).astype(np.uint8)
    # work in BGR for cv2
    bgr = base[:, :, ::-1].copy()
    n = len(xs)
    batch = 20000
    for start in range(0, n, batch):
        end = min(n, start + batch)
        layer = np.zeros((h, w, 4), dtype=np.uint8)
        for i in range(start, end):
            ang = float(angs[i])
            ca, sa = math.cos(ang), math.sin(ang)
            half = float(lens[i]) * 0.5
            x, y = float(xs[i]), float(ys[i])
            x0, y0 = int(round(x - ca * half)), int(round(y - sa * half))
            x1, y1 = int(round(x + ca * half)), int(round(y + sa * half))
            a = int(max(0, min(255, round(float(als[i]) * 255))))
            color = (
                int(bs[i]),
                int(gs[i]),
                int(rs[i]),
                a,
            )
            lw = max(1, int(round(float(ws[i]))))
            cv2.line(layer, (x0, y0), (x1, y1), color, thickness=lw, lineType=cv2.LINE_AA)
        rgb = layer[..., 2::-1].astype(np.float32)  # BGR A -> R,G,B via reverse of BGR
        # layer is BGRA; convert properly
        bgr_l = layer[..., :3].astype(np.float32)
        a = layer[..., 3:4].astype(np.float32) / 255.0
        bgr = bgr.astype(np.float32) * (1.0 - a) + bgr_l * a
        bgr = np.clip(bgr, 0, 255)
    return bgr[:, :, ::-1].astype(np.float32)


def area_error(err: np.ndarray, y0: int, x0: int, y1: int, x1: int) -> float:
    patch = err[y0:y1, x0:x1]
    if patch.size == 0:
        return 0.0
    return float(patch.mean())


def pick_grid_seeds(
    err: np.ndarray,
    highlight: np.ndarray,
    edge: np.ndarray,
    step: int,
    err_thr: float,
    budget: int,
    rng: np.random.Generator,
    highlight_boost: float = 1.6,
    edge_boost: float = 1.35,
) -> tuple[np.ndarray, np.ndarray]:
    """Hertzmann grid: one candidate per cell if area error > T; score by peak*boosts."""
    h, w = err.shape
    cells = []
    scores = []
    for y0 in range(0, h, step):
        for x0 in range(0, w, step):
            y1 = min(h, y0 + step)
            x1 = min(w, x0 + step)
            ae = area_error(err, y0, x0, y1, x1)
            if ae < err_thr:
                continue
            patch = err[y0:y1, x0:x1]
            # max-error pixel inside cell (classic Hertzmann)
            flat = int(np.argmax(patch))
            py = y0 + flat // (x1 - x0)
            px = x0 + flat % (x1 - x0)
            sc = float(err[py, px])
            sc *= 1.0 + (highlight_boost - 1.0) * float(highlight[py, px])
            sc *= 1.0 + (edge_boost - 1.0) * float(edge[py, px])
            # slight jitter inside cell
            jx = int(np.clip(px + rng.integers(-max(1, step // 5), max(2, step // 5 + 1)), 0, w - 1))
            jy = int(np.clip(py + rng.integers(-max(1, step // 5), max(2, step // 5 + 1)), 0, h - 1))
            cells.append((jx, jy))
            scores.append(sc)
    if not cells:
        return np.zeros(0, dtype=np.int32), np.zeros(0, dtype=np.int32)
    xs = np.array([c[0] for c in cells], dtype=np.int32)
    ys = np.array([c[1] for c in cells], dtype=np.int32)
    score = np.array(scores, dtype=np.float32)
    if xs.size > budget:
        # keep top scores, then fill remaining with random high-ish
        idx = np.argpartition(-score, budget)[:budget]
        xs, ys, score = xs[idx], ys[idx], score[idx]
    order = np.argsort(-score)
    return xs[order], ys[order]


def pick_dense_boosted(
    err: np.ndarray,
    highlight: np.ndarray,
    edge: np.ndarray,
    coherence: np.ndarray,
    err_thr: float,
    budget: int,
    rng: np.random.Generator,
    stride: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    h, w = err.shape
    if stride > 1:
        sub = err[::stride, ::stride]
        ys, xs = np.where(sub >= err_thr)
        if xs.size == 0:
            return np.zeros(0, dtype=np.int32), np.zeros(0, dtype=np.int32)
        xs = np.clip(xs * stride + rng.integers(0, stride, size=xs.shape[0]), 0, w - 1)
        ys = np.clip(ys * stride + rng.integers(0, stride, size=ys.shape[0]), 0, h - 1)
    else:
        ys, xs = np.where(err >= err_thr)
        if xs.size == 0:
            return np.zeros(0, dtype=np.int32), np.zeros(0, dtype=np.int32)
    score = (
        err[ys, xs]
        * (0.45 + 0.55 * coherence[ys, xs])
        * (1.0 + 1.1 * highlight[ys, xs])
        * (1.0 + 0.7 * edge[ys, xs])
    )
    if xs.size > budget * 4:
        pick = rng.choice(xs.size, size=budget * 4, replace=False)
        xs, ys, score = xs[pick], ys[pick], score[pick]
    if xs.size > budget:
        idx = np.argpartition(-score, budget)[:budget]
        xs, ys = xs[idx], ys[idx]
    return xs.astype(np.int32), ys.astype(np.int32)


def sample_color(rgb: np.ndarray, x: int, y: int, radius: int = 0) -> np.ndarray:
    """Sample source color; small neighborhood median for coarse brushes."""
    h, w = rgb.shape[:2]
    if radius <= 0:
        return rgb[y, x].copy()
    x0, x1 = max(0, x - radius), min(w, x + radius + 1)
    y0, y1 = max(0, y - radius), min(h, y + radius + 1)
    patch = rgb[y0:y1, x0:x1].reshape(-1, 3)
    return np.median(patch, axis=0).astype(np.float32)


def align_angle(prev: float, new: float) -> float:
    """Flip new by pi if needed so it continues prev direction."""
    d = new - prev
    while d > math.pi / 2:
        new -= math.pi
        d = new - prev
    while d < -math.pi / 2:
        new += math.pi
        d = new - prev
    return new


def trace_curve(
    x0: float,
    y0: float,
    angle_field: np.ndarray,
    rgb: np.ndarray,
    color0: np.ndarray,
    max_half_len: float,
    step: float,
    color_thr: float,
) -> list[tuple[float, float]]:
    """Walk both directions along isophote; stop on OOB or color jump."""
    h, w = angle_field.shape
    pts_f: list[tuple[float, float]] = []
    pts_b: list[tuple[float, float]] = []

    def walk(forward: bool) -> list[tuple[float, float]]:
        pts: list[tuple[float, float]] = []
        cx, cy = float(x0), float(y0)
        ix, iy = int(round(cx)), int(round(cy))
        ix = min(max(ix, 0), w - 1)
        iy = min(max(iy, 0), h - 1)
        prev_a = float(angle_field[iy, ix])
        if not forward:
            prev_a += math.pi
        traveled = 0.0
        max_steps = max(1, int(math.ceil(max_half_len / max(step, 0.5))))
        for _ in range(max_steps):
            ix, iy = int(round(cx)), int(round(cy))
            if ix < 1 or iy < 1 or ix >= w - 1 or iy >= h - 1:
                break
            a = align_angle(prev_a, float(angle_field[iy, ix]))
            prev_a = a
            cx += math.cos(a) * step
            cy += math.sin(a) * step
            traveled += step
            if traveled > max_half_len:
                break
            ix2, iy2 = int(round(cx)), int(round(cy))
            if ix2 < 0 or iy2 < 0 or ix2 >= w or iy2 >= h:
                break
            c = rgb[iy2, ix2]
            if float(np.mean(np.abs(c - color0))) > color_thr:
                break
            pts.append((cx, cy))
        return pts

    pts_f = walk(True)
    pts_b = walk(False)
    # reverse back, center, forward
    chain = list(reversed(pts_b)) + [(float(x0), float(y0))] + pts_f
    return chain


def segments_from_curve(
    chain: list[tuple[float, float]],
    color: np.ndarray,
    width: float,
    alpha: float,
    layer_id: int,
    region_id: int,
) -> dict[str, list]:
    """Emit short straight segments along the curve (fits NPZ renderer)."""
    out: dict[str, list] = {k: [] for k in ("x", "y", "angle", "len", "w", "r", "g", "b", "a", "layer_id", "region_id")}
    if len(chain) < 2:
        # single dab
        x, y = chain[0]
        out["x"].append(x)
        out["y"].append(y)
        out["angle"].append(0.0)
        out["len"].append(max(1.0, width * 0.8))
        out["w"].append(width)
        out["r"].append(int(np.clip(color[0], 0, 255)))
        out["g"].append(int(np.clip(color[1], 0, 255)))
        out["b"].append(int(np.clip(color[2], 0, 255)))
        out["a"].append(alpha)
        out["layer_id"].append(layer_id)
        out["region_id"].append(region_id)
        return out
    # stride along chain so we don't over-segment
    stride = 1 if len(chain) < 6 else 2
    for i in range(0, len(chain) - 1, stride):
        x0, y0 = chain[i]
        x1, y1 = chain[min(i + stride, len(chain) - 1)]
        dx, dy = x1 - x0, y1 - y0
        seg_len = math.hypot(dx, dy)
        if seg_len < 0.4:
            continue
        ang = math.atan2(dy, dx)
        mx, my = (x0 + x1) * 0.5, (y0 + y1) * 0.5
        out["x"].append(mx)
        out["y"].append(my)
        out["angle"].append(ang)
        out["len"].append(max(seg_len, 1.0))
        out["w"].append(width)
        out["r"].append(int(np.clip(round(float(color[0])), 0, 255)))
        out["g"].append(int(np.clip(round(float(color[1])), 0, 255)))
        out["b"].append(int(np.clip(round(float(color[2])), 0, 255)))
        out["a"].append(alpha)
        out["layer_id"].append(layer_id)
        out["region_id"].append(region_id)
    return out


def dict_lists_to_arrays(d: dict[str, list]) -> dict[str, np.ndarray]:
    return {
        "x": np.asarray(d["x"], dtype=np.float32),
        "y": np.asarray(d["y"], dtype=np.float32),
        "angle": np.asarray(d["angle"], dtype=np.float32),
        "len": np.asarray(d["len"], dtype=np.float32),
        "w": np.asarray(d["w"], dtype=np.float32),
        "r": np.asarray(d["r"], dtype=np.uint8),
        "g": np.asarray(d["g"], dtype=np.uint8),
        "b": np.asarray(d["b"], dtype=np.uint8),
        "a": np.asarray(d["a"], dtype=np.float32),
        "layer_id": np.asarray(d["layer_id"], dtype=np.uint8),
        "region_id": np.asarray(d["region_id"], dtype=np.uint8),
    }


def concat_stroke_dicts(parts: list[dict[str, np.ndarray]]) -> dict[str, np.ndarray]:
    if not parts:
        raise ValueError("no strokes")
    keys = parts[0].keys()
    return {k: np.concatenate([p[k] for p in parts], axis=0) for k in keys}


def empty_stroke_lists() -> dict[str, list]:
    return {k: [] for k in ("x", "y", "angle", "len", "w", "r", "g", "b", "a", "layer_id", "region_id")}


def merge_lists(dst: dict[str, list], src: dict[str, list]) -> None:
    for k in dst:
        dst[k].extend(src[k])


def build_straight_batch(
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
    color_radius: int = 0,
    angle_jitter: float = 0.08,
    brighten: float = 1.0,
) -> dict[str, np.ndarray]:
    """Fast vectorized placement for dense layers (still oriented by tensor)."""
    n = xs.shape[0]
    h, w = rgb.shape[:2]
    angs = angle[ys, xs].astype(np.float32) + rng.normal(0, angle_jitter, size=n).astype(np.float32)
    coh = coherence[ys, xs].astype(np.float32)
    lens = (width * len_scale * (0.75 + 0.65 * coh)).astype(np.float32)
    lens = np.where(coh < 0.22, lens * 0.55, lens).astype(np.float32)
    # colors
    if color_radius <= 0:
        cols = rgb[ys, xs].astype(np.float32) * brighten
    else:
        cols = np.zeros((n, 3), dtype=np.float32)
        for i in range(n):
            cols[i] = sample_color(rgb, int(xs[i]), int(ys[i]), color_radius) * brighten
    cols = np.clip(cols, 0, 255)
    return {
        "x": xs.astype(np.float32) + rng.normal(0, 0.25, size=n).astype(np.float32),
        "y": ys.astype(np.float32) + rng.normal(0, 0.25, size=n).astype(np.float32),
        "angle": angs,
        "len": lens,
        "w": np.full(n, width, dtype=np.float32),
        "r": cols[:, 0].astype(np.uint8),
        "g": cols[:, 1].astype(np.uint8),
        "b": cols[:, 2].astype(np.uint8),
        "a": np.full(n, alpha, dtype=np.float32),
        "layer_id": np.full(n, layer_id, dtype=np.uint8),
        "region_id": region_map[ys, xs].astype(np.uint8),
    }


def generate(
    rgb: np.ndarray,
    max_strokes: int = 450000,
    seed: int = 47,
) -> tuple[dict[str, np.ndarray], dict]:
    rng = np.random.default_rng(seed)
    h, w = rgb.shape[:2]
    gray = luminance(rgb)
    print("structure tensor (multi-scale)…", flush=True)
    # scales roughly matching brush radii
    angle_c, coh_c, mag = structure_tensor_field(gray, sigma=4.0)
    angle_m, coh_m, _ = structure_tensor_field(gray, sigma=2.5)
    angle_f, coh_f, _ = structure_tensor_field(gray, sigma=1.4)

    region_map = build_region_map(w, h)

    # highlight / edge weight maps in [0,1]
    lum = gray / 255.0
    highlight = np.clip((lum - 0.42) / 0.45, 0.0, 1.0).astype(np.float32)
    # phone / lamp / eyes tend to be bright — also boost local contrast
    mag_n = mag / (np.percentile(mag, 99) + 1e-6)
    edge = np.clip(mag_n, 0.0, 1.0).astype(np.float32)

    # canvas init: blurred reference (Hertzmann often starts blank/avg; blur helps coverage)
    canvas = gaussian_blur_rgb(rgb, sigma=18.0)
    # pull slightly toward mean so first strokes matter
    mean_c = rgb.reshape(-1, 3).mean(axis=0)
    canvas = canvas * 0.55 + mean_c.reshape(1, 1, 3) * 0.45

    # Hertzmann radii (brush width) coarse → fine
    # (name, width, len_scale, grid_step, T_err, alpha, frac, mode, sigma_blur, angle_field)
    # mode: "grid" | "denseN"
    paint_reserve_hl = min(60000, max_strokes // 7)
    paint_reserve_ink = min(35000, max_strokes // 12)
    paint_budget = max_strokes - paint_reserve_hl - paint_reserve_ink

    specs = [
        # name, R, len_scale, step/mode, T, alpha, frac, ref_blur_sigma, which_angle, color_radius, curve?
        ("coarse", 14.0, 2.4, 10, 0.045, 0.62, 0.06, 6.0, "c", 2, True),
        ("mid", 8.0, 2.2, 5, 0.032, 0.55, 0.12, 3.5, "m", 1, True),
        ("fine", 4.2, 2.0, 3, 0.022, 0.48, 0.20, 1.8, "f", 0, True),
        ("detail", 2.4, 1.75, "dense2", 0.014, 0.44, 0.28, 0.8, "f", 0, False),
        ("micro", 1.35, 1.45, "dense1", 0.008, 0.40, 0.34, 0.0, "f", 0, False),
    ]

    angle_map = {"c": (angle_c, coh_c), "m": (angle_m, coh_m), "f": (angle_f, coh_f)}

    parts: list[dict[str, np.ndarray]] = []
    used_segments = 0

    for name, width, len_scale, step, err_thr, alpha, frac, blur_s, ang_key, col_r, do_curve in specs:
        budget_seeds = int(paint_budget * frac)
        # for curved layers, each seed → several segments; leave headroom
        seg_factor = 4.0 if do_curve else 1.0
        seed_budget = max(1, int(budget_seeds / seg_factor))
        remaining = paint_budget - used_segments
        if remaining <= 0:
            break
        # cap expected segments
        seed_budget = min(seed_budget, max(1, int(remaining / seg_factor)))

        ref = gaussian_blur_rgb(rgb, blur_s) if blur_s > 0.2 else rgb
        err = np.mean(np.abs(canvas - ref), axis=2) / 255.0
        ang, coh = angle_map[ang_key]
        print(
            f"layer {name}: seeds≈{seed_budget} T={err_thr} err_mean={err.mean():.4f} "
            f"err_p90={np.percentile(err,90):.4f}",
            flush=True,
        )

        if isinstance(step, str) and step.startswith("dense"):
            stride = int(step.replace("dense", "") or "1")
            xs, ys = pick_dense_boosted(err, highlight, edge, coh, err_thr, seed_budget, rng, stride=stride)
            if xs.size < seed_budget * 0.7:
                xs, ys = pick_dense_boosted(
                    err, highlight, edge, coh, err_thr * 0.55, seed_budget, rng, stride=1
                )
        else:
            xs, ys = pick_grid_seeds(err, highlight, edge, int(step), err_thr, seed_budget, rng)
            if xs.size < seed_budget * 0.5:
                # relax T once
                xs, ys = pick_grid_seeds(
                    err, highlight, edge, max(2, int(step) - 1), err_thr * 0.65, seed_budget, rng
                )

        if xs.size == 0:
            print(f"  skip empty {name}", flush=True)
            continue

        lid = LAYER_TO_ID[name]
        color_thr = 28.0 + width * 2.5  # allow more color drift on big brushes

        if do_curve:
            lists = empty_stroke_lists()
            max_half = width * len_scale * 0.55
            step_len = max(1.2, width * 0.45)
            for i in range(xs.shape[0]):
                if used_segments + len(lists["x"]) >= remaining:
                    break
                xi, yi = int(xs[i]), int(ys[i])
                col = sample_color(ref, xi, yi, col_r)
                # slight lift so we don't systematically underrun bright paint
                col = np.clip(col * 1.02, 0, 255)
                chain = trace_curve(
                    float(xi), float(yi), ang, ref, col, max_half, step_len, color_thr
                )
                segs = segments_from_curve(
                    chain, col, width, alpha, lid, int(region_map[yi, xi])
                )
                merge_lists(lists, segs)
            chunk = dict_lists_to_arrays(lists)
        else:
            # take only as many as remaining
            n_take = min(xs.shape[0], remaining)
            chunk = build_straight_batch(
                xs[:n_take],
                ys[:n_take],
                ref,
                ang,
                coh,
                width,
                len_scale,
                alpha,
                lid,
                region_map,
                rng,
                color_radius=col_r,
                angle_jitter=0.07,
                brighten=1.03,
            )

        if chunk["x"].shape[0] == 0:
            print(f"  no segments {name}", flush=True)
            continue

        parts.append(chunk)
        used_segments += int(chunk["x"].shape[0])
        print(f"  segments={chunk['x'].shape[0]} total={used_segments}", flush=True)

        canvas = stamp_layer_cv2(
            canvas,
            chunk["x"],
            chunk["y"],
            chunk["angle"],
            chunk["len"],
            chunk["w"],
            chunk["r"],
            chunk["g"],
            chunk["b"],
            chunk["a"],
        )

    # --- highlight pass: dense short strokes on bright residual ---
    hl_budget = min(paint_reserve_hl, max_strokes - used_segments)
    if hl_budget > 0:
        err = np.mean(np.abs(canvas - rgb), axis=2) / 255.0
        # focus where source is bright AND error remains
        bright_err = err * (0.35 + 0.65 * highlight) * (0.5 + 0.5 * edge)
        thr = max(0.01, float(np.percentile(bright_err, 70)))
        ys_b, xs_b = np.where(bright_err >= thr)
        print(f"layer highlight: candidates={xs_b.size} budget={hl_budget} thr={thr:.4f}", flush=True)
        if xs_b.size:
            score = bright_err[ys_b, xs_b]
            if xs_b.size > hl_budget * 3:
                pick = rng.choice(xs_b.size, size=hl_budget * 3, replace=False)
                xs_b, ys_b, score = xs_b[pick], ys_b[pick], score[pick]
            if xs_b.size > hl_budget:
                idx = np.argpartition(-score, hl_budget)[:hl_budget]
                xs_b, ys_b = xs_b[idx], ys_b[idx]
            cols = rgb[ys_b, xs_b].astype(np.float32)
            # boost highlights toward source (fix underrun)
            cols = np.clip(cols * 1.06 + 4.0, 0, 255)
            n = xs_b.shape[0]
            angs = angle_f[ys_b, xs_b] + rng.normal(0, 0.1, size=n).astype(np.float32)
            coh = coh_f[ys_b, xs_b]
            lens = (1.8 * (0.9 + 0.5 * coh)).astype(np.float32)
            hl = {
                "x": xs_b.astype(np.float32) + rng.normal(0, 0.2, size=n).astype(np.float32),
                "y": ys_b.astype(np.float32) + rng.normal(0, 0.2, size=n).astype(np.float32),
                "angle": angs.astype(np.float32),
                "len": lens,
                "w": rng.uniform(1.0, 1.8, size=n).astype(np.float32),
                "r": cols[:, 0].astype(np.uint8),
                "g": cols[:, 1].astype(np.uint8),
                "b": cols[:, 2].astype(np.uint8),
                "a": np.full(n, 0.55, dtype=np.float32),
                "layer_id": np.full(n, LAYER_TO_ID["highlight"], dtype=np.uint8),
                "region_id": region_map[ys_b, xs_b].astype(np.uint8),
            }
            parts.append(hl)
            used_segments += n
            canvas = stamp_layer_cv2(
                canvas, hl["x"], hl["y"], hl["angle"], hl["len"], hl["w"],
                hl["r"], hl["g"], hl["b"], hl["a"],
            )
            print(f"  highlight placed {n} total={used_segments}", flush=True)

    # --- soft ink: edge-aligned, color from source (NOT forced dark) ---
    ink_budget = min(paint_reserve_ink, max_strokes - used_segments)
    if ink_budget > 0:
        thr = float(np.quantile(mag, 0.88))
        ys_e, xs_e = np.where(mag >= thr)
        if xs_e.size:
            if xs_e.size > ink_budget * 4:
                pick = rng.choice(xs_e.size, size=ink_budget * 4, replace=False)
                xs_e, ys_e = xs_e[pick], ys_e[pick]
            score = mag[ys_e, xs_e] * (0.7 + 0.3 * edge[ys_e, xs_e])
            if xs_e.size > ink_budget:
                idx = np.argpartition(-score, ink_budget)[:ink_budget]
                xs_e, ys_e = xs_e[idx], ys_e[idx]
            n = xs_e.shape[0]
            cols = rgb[ys_e, xs_e].astype(np.float32)
            # ink = darkened local color (preserves hue of fur edges), not pure black
            cols = np.clip(cols * 0.55 + np.array([8, 5, 4], dtype=np.float32), 0, 255)
            # but on bright edges keep more of the source
            br = highlight[ys_e, xs_e][:, None]
            cols = cols * (1.0 - 0.65 * br) + rgb[ys_e, xs_e].astype(np.float32) * (0.65 * br)
            cols = np.clip(cols, 0, 255)
            angs = angle_f[ys_e, xs_e] + rng.normal(0, 0.14, size=n).astype(np.float32)
            ink = {
                "x": xs_e.astype(np.float32) + rng.normal(0, 0.4, size=n).astype(np.float32),
                "y": ys_e.astype(np.float32) + rng.normal(0, 0.4, size=n).astype(np.float32),
                "angle": angs.astype(np.float32),
                "len": rng.uniform(2.8, 7.5, size=n).astype(np.float32),
                "w": rng.uniform(0.8, 1.5, size=n).astype(np.float32),
                "r": cols[:, 0].astype(np.uint8),
                "g": cols[:, 1].astype(np.uint8),
                "b": cols[:, 2].astype(np.uint8),
                "a": np.full(n, 0.42, dtype=np.float32),
                "layer_id": np.full(n, LAYER_TO_ID["ink"], dtype=np.uint8),
                "region_id": region_map[ys_e, xs_e].astype(np.uint8),
            }
            parts.append(ink)
            used_segments += n
            print(f"layer ink: placed {n} total={used_segments}", flush=True)

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
        "structure_tensor_sigmas": [4.0, 2.5, 1.4],
        "max_strokes_cap": max_strokes,
        "seed": seed,
        "storage": "npz",
        "regions": region_manifest(),
        "region_id_to_name": region_id_to_name(),
        "method": "Hertzmann-style coarse-to-fine + structure-tensor curves + highlight pass",
        "honesty": (
            "v3: Hertzmann grid residual, multi-scale ETF, curved strokes on coarse/mid/fine, "
            "source-sampled color (no *0.97 darken), highlight density pass, soft local-color ink. "
            "Still not illustration-perfect; regions remain rough AABBs."
        ),
        "version": "v3",
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
    ap.add_argument("--out", type=Path, default=ROOT / "out" / "strokes_v8_v3.json")
    ap.add_argument("--max-strokes", type=int, default=450000)
    ap.add_argument("--seed", type=int, default=47)
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
