"""Hertzmann stroke remake of 《偷来的夜》 still 05, with Ghibli-like style prep.

Style prep (documented in STYLE_PREP.md):
  Borrow painterly warmth + micro-texture from style_ref_ghibli.jpg WITHOUT
  morphing the bedroom into a daylight forest. Dual amber/blue night lighting
  is preserved via a cool-glow mask; only warm regions get Lab warmth transfer.

Pipeline: style_prep(content) -> Hertzmann layered paint -> ink outlines
Outputs land in out/ as s05_v1_*.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from skimage.morphology import skeletonize

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT.parent / "stills" / "05.jpg"
STYLE_REF = ROOT.parent / "stills_src" / "style_ref_ghibli.jpg"
OUT = ROOT / "out"

# Paint at half of delivery size * S == 1080x1920
PAINT_W, PAINT_H = 540, 960
S = 2  # output scale -> 1080x1920
TAG = "s05_v1"


def load_bgr(path: Path) -> np.ndarray:
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(path)
    return img


def cool_glow_mask(bgr: np.ndarray) -> np.ndarray:
    """Soft mask of phone-screen cool light (face/mask/hands/phone).

    High luminance + relatively blue vs warm amber wall light.
    """
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    L, A, B = lab[..., 0], lab[..., 1], lab[..., 2]
    # Cool: high L, B channel toward blue (Lab b* low), A near neutral
    cool = (L > 140).astype(np.float32)
    cool *= np.clip((145 - B) / 40.0, 0, 1)  # bluer than warm wall
    # Also catch very bright white mask even if Lab drifts
    bright = np.clip((L - 170) / 50.0, 0, 1)
    m = np.clip(np.maximum(cool * 0.85, bright * 0.7), 0, 1)
    m = cv2.GaussianBlur(m, (0, 0), 8)
    return m


def style_prep(content: np.ndarray, style: np.ndarray) -> tuple[np.ndarray, dict]:
    """Borrow painterly warmth/texture; keep night dual lighting.

    Method summary (see STYLE_PREP.md):
      1. Resize style to content size for stats only (no spatial warp of style content).
      2. Lab mean/std match on warm regions only; cool-glow mask protects phone light.
      3. Inject desaturated high-pass micro-texture from style at low opacity.
      4. Mild local contrast (unsharp) for oil-paint edge energy — not daylight grade.
    """
    H, W = content.shape[:2]
    style_r = cv2.resize(style, (W, H), interpolation=cv2.INTER_AREA)

    c_lab = cv2.cvtColor(content, cv2.COLOR_BGR2LAB).astype(np.float32)
    s_lab = cv2.cvtColor(style_r, cv2.COLOR_BGR2LAB).astype(np.float32)

    cool = cool_glow_mask(content)
    warm = 1.0 - cool

    # Warm-region Lab stats from style (global), apply only where warm
    eps = 1e-3
    out_lab = c_lab.copy()
    transfer_notes = {}
    for ch in range(3):
        c = c_lab[..., ch]
        s = s_lab[..., ch]
        # Style target for warmth: slightly pull toward style mean on A/B,
        # keep L closer to content so night stays night.
        if ch == 0:
            # Soften flat fills: mild contrast toward style L std, limited
            c_mean = float(c.mean())
            c_std = float(c.std()) + eps
            s_std = float(s.std()) + eps
            # Night: do NOT raise mean L to sunny style mean
            target_std = c_std * 0.65 + s_std * 0.35
            matched = (c - c_mean) * (target_std / c_std) + c_mean
            # Cap: never brighten mean more than +4 Lab L
            matched = matched + min(4.0, max(-2.0, 0.0))
            blend = warm * 0.55  # partial on warm only
            out_lab[..., ch] = c * (1 - blend) + matched * blend
            transfer_notes["L"] = {
                "content_mean": round(c_mean, 1),
                "content_std": round(c_std, 1),
                "style_std": round(s_std, 1),
                "blend_warm": 0.55,
            }
        else:
            # A/B: pull warm regions toward style warmth (golden), protect cool
            c_mean = float((c * warm).sum() / (warm.sum() + eps))
            s_mean = float(s.mean())
            c_std = float((((c - c_mean) ** 2) * warm).sum() / (warm.sum() + eps)) ** 0.5 + eps
            s_std = float(s.std()) + eps
            # Blend style mean gently — style is sunny; only take ~35% of mean shift
            target_mean = c_mean * 0.65 + s_mean * 0.35
            matched = (c - c_mean) * (0.7 * c_std + 0.3 * s_std) / c_std + target_mean
            blend = warm * 0.7
            out_lab[..., ch] = c * (1 - blend) + matched * blend
            transfer_notes[("A", "B")[ch - 1]] = {
                "content_warm_mean": round(c_mean, 1),
                "style_mean": round(s_mean, 1),
                "target_mean": round(target_mean, 1),
                "blend_warm": 0.7,
            }

    out_lab = np.clip(out_lab, 0, 255)
    primed = cv2.cvtColor(out_lab.astype(np.uint8), cv2.COLOR_LAB2BGR)

    # Micro-texture: desaturated high-pass from style, low opacity on warm areas
    s_gray = cv2.cvtColor(style_r, cv2.COLOR_BGR2GRAY).astype(np.float32)
    hp = s_gray - cv2.GaussianBlur(s_gray, (0, 0), 3.5)
    hp = np.clip(hp, -40, 40)
    tex = np.stack([hp, hp, hp], axis=2)
    tex_strength = 0.12
    primed_f = primed.astype(np.float32) + tex * tex_strength * warm[..., None]
    primed = np.clip(primed_f, 0, 255).astype(np.uint8)

    # Unsharp for painterly edge energy (subtle)
    blur = cv2.GaussianBlur(primed, (0, 0), 1.2)
    primed = np.clip(primed.astype(np.float32) * 1.25 - blur.astype(np.float32) * 0.25, 0, 255).astype(
        np.uint8
    )

    # Re-assert cool glow: mix original cool regions back so phone blue survives
    cool3 = cool[..., None]
    primed = np.clip(
        primed.astype(np.float32) * (1 - cool3 * 0.85) + content.astype(np.float32) * (cool3 * 0.85),
        0,
        255,
    ).astype(np.uint8)

    meta = {
        "method": "warm-masked Lab partial match + desaturated style high-pass + unsharp; cool glow restored from content",
        "keeps_night_dual_lighting": True,
        "avoids_daylight_forest_morph": True,
        "transfer": transfer_notes,
        "texture_strength": tex_strength,
        "cool_mask_mean": round(float(cool.mean()), 4),
    }
    return primed, meta


def orient_field(gray, sigma_grad, sigma_tensor, W, H):
    g = cv2.GaussianBlur(gray, (0, 0), sigma_grad)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    jxx = cv2.GaussianBlur(gx * gx, (0, 0), sigma_tensor)
    jxy = cv2.GaussianBlur(gx * gy, (0, 0), sigma_tensor)
    jyy = cv2.GaussianBlur(gy * gy, (0, 0), sigma_tensor)
    tr = jxx + jyy + 1e-3
    A = (jxx - jyy) / tr
    B = 2 * jxy / tr
    A = cv2.resize(A, (W, H), interpolation=cv2.INTER_LINEAR)
    B = cv2.resize(B, (W, H), interpolation=cv2.INTER_LINEAR)
    return A, B


def paint(ref, seed=1, cfg=None):
    rng = np.random.default_rng(seed)
    cfg = cfg or {}
    H0, W0 = ref.shape[:2]
    H, W = H0 * S, W0 * S
    refF = ref.astype(np.float32)
    ref_up = cv2.resize(refF, (W, H), interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY).astype(np.float32)

    # Slightly broader / longer strokes for painterly Ghibli-like feel
    radii = cfg.get("radii", [14, 8, 5, 3.2, 2.1, 1.4])
    thresh = cfg.get("thresh", [0, 24, 18, 14, 10, 7])
    sg = cfg.get("sigma_grad", [2.2, 1.7, 1.3, 1.0, 0.75, 0.6])
    st = cfg.get("sigma_tensor", [4.5, 3.2, 2.4, 1.8, 1.4, 1.1])
    maxlen = cfg.get("maxlen", [80, 58, 42, 32, 24, 18])
    grid = cfg.get("grid", 1.0)
    fs = cfg.get("blur_factor", 0.55)
    default_ang = cfg.get("default_angle", -0.55)
    d0 = np.array([math.cos(default_ang), math.sin(default_ang)], np.float32)
    jitters = cfg.get("jitter", [3, 4, 5, 6, 7, 8])

    canvas = np.empty((H, W, 3), np.uint8)
    canvas[:] = refF.reshape(-1, 3).mean(0).astype(np.uint8)
    strokes = []

    for li, R in enumerate(radii):
        t0 = time.time()
        refb = cv2.GaussianBlur(ref_up, (0, 0), fs * R)
        diff = np.sqrt(((canvas.astype(np.float32) - refb) ** 2).sum(2))
        g = max(2, int(round(R * grid)))
        hc, wc = H // g, W // g
        d = diff[: hc * g, : wc * g].reshape(hc, g, wc, g)
        cell = d.mean(axis=(1, 3))
        am = d.transpose(0, 2, 1, 3).reshape(hc, wc, g * g).argmax(-1)
        cand = np.argwhere(cell > thresh[li])
        rng.shuffle(cand)
        A, B = orient_field(gray, sg[li], st[li], W, H)
        step = max(1.4, R * 0.6)
        nsteps = int(maxlen[li] / step) + 1
        thick = max(1, int(round(2 * R)))
        jitter = jitters[li]
        count = 0
        for cy, cx in cand:
            a = am[cy, cx]
            y = cy * g + a // g
            x = cx * g + a % g
            col = refb[y, x]
            col = np.clip(col + rng.normal(0, jitter, 3), 0, 255)
            pts = [(x, y)]
            fx, fy = float(x), float(y)
            lx, ly = d0[0], d0[1]
            for k in range(nsteps):
                ix, iy = int(fx), int(fy)
                if ix < 0 or iy < 0 or ix >= W or iy >= H:
                    break
                if k >= 2:
                    dc = np.abs(refb[iy, ix] - canvas[iy, ix]).sum()
                    ds = np.abs(refb[iy, ix] - col).sum()
                    if dc < ds:
                        break
                a2, b2 = A[iy, ix], B[iy, ix]
                coh = math.hypot(a2, b2)
                th = 0.5 * math.atan2(b2, a2)
                vx, vy = -math.sin(th), math.cos(th)
                if vx * lx + vy * ly < 0:
                    vx, vy = -vx, -vy
                w = min(1.0, coh * 1.4)
                dx = w * vx + (1 - w) * lx
                dy = w * vy + (1 - w) * ly
                n = math.hypot(dx, dy) or 1.0
                dx /= n
                dy /= n
                lx, ly = dx, dy
                fx += dx * step
                fy += dy * step
                pts.append((fx, fy))
            arr = np.array(pts, np.float32)
            ip = np.round(arr).astype(np.int32)
            c3 = tuple(int(v) for v in col)
            if len(ip) < 2:
                cv2.circle(canvas, (int(ip[0][0]), int(ip[0][1])), thick // 2 or 1, c3, -1, cv2.LINE_AA)
            else:
                cv2.polylines(canvas, [ip.reshape(-1, 1, 2)], False, c3, thick, cv2.LINE_AA)
            strokes.append((li, R, np.array(c3, np.uint8), arr.astype(np.float16)))
            count += 1
        print(f"layer {li} R={R}: {count} strokes, {time.time() - t0:.1f}s", flush=True)
    return canvas, strokes


def ink(canvas, ref, seed=5, alpha=0.5):
    rng = np.random.default_rng(seed)
    H, W = canvas.shape[:2]
    gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY).astype(np.float32)
    dark = cv2.GaussianBlur(gray, (0, 0), 5) - cv2.GaussianBlur(gray, (0, 0), 0.9)
    mask = (dark > 9).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    sk = skeletonize(mask > 0).astype(np.uint8)
    cnts, _ = cv2.findContours(sk, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    overlay = np.zeros_like(canvas)
    m = np.zeros((H, W), np.float32)
    refF = ref.astype(np.float32)
    n = 0
    for c in cnts:
        c = c.reshape(-1, 2)
        if len(c) < 10:
            continue
        half = c[: len(c) // 2 + 1]
        if len(half) < 8:
            continue
        pts = half.astype(np.float32) * S + S / 2
        t = np.arange(len(pts), dtype=np.float32)
        ph = rng.uniform(0, 6.28, 2)
        off = 0.8 * np.sin(t * 0.35 + ph[0]) + 0.5 * np.sin(t * 0.9 + ph[1])
        d = np.gradient(pts, axis=0)
        nrm = np.stack([-d[:, 1], d[:, 0]], 1)
        nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-6
        pts = pts + nrm * off[:, None]
        ys = np.clip(half[:, 1], 0, ref.shape[0] - 1)
        xs = np.clip(half[:, 0], 0, ref.shape[1] - 1)
        col = refF[ys, xs].mean(0) * 0.35
        c3 = tuple(int(v) for v in col)
        ip = np.round(pts).astype(np.int32).reshape(-1, 1, 2)
        th = int(rng.integers(2, 4))
        cv2.polylines(overlay, [ip], False, c3, th, cv2.LINE_AA)
        cv2.polylines(m, [ip], False, 1.0, th, cv2.LINE_AA)
        n += 1
    m = np.clip(m, 0, 1)[..., None] * alpha
    out = canvas.astype(np.float32) * (1 - m) + overlay.astype(np.float32) * m
    print(f"ink: {n} lines", flush=True)
    return np.clip(out, 0, 255).astype(np.uint8)


def metrics(ref, canvas):
    small = cv2.resize(canvas, (ref.shape[1], ref.shape[0]), interpolation=cv2.INTER_AREA)
    mse = float(((small.astype(np.float32) - ref.astype(np.float32)) ** 2).mean())
    s_full = ssim(ref, small, channel_axis=2)
    rb = cv2.GaussianBlur(ref, (0, 0), 2)
    sb = cv2.GaussianBlur(small, (0, 0), 2)
    s_blur = ssim(rb, sb, channel_axis=2)
    return {
        "mse": round(mse, 1),
        "ssim": round(float(s_full), 3),
        "ssim_blur2": round(float(s_blur), 3),
    }, small


def compare(ref, small, path):
    err = np.abs(small.astype(np.int16) - ref.astype(np.int16)).sum(2)
    err = np.clip(err * 2, 0, 255).astype(np.uint8)
    heat = cv2.applyColorMap(err, cv2.COLORMAP_INFERNO)
    top = np.hstack([ref, small, heat])

    def crop(img, x0, y0, x1, y1, z=2):
        return cv2.resize(img[y0:y1, x0:x1], None, fx=z, fy=z, interpolation=cv2.INTER_CUBIC)

    # Face+mask and phone+hands crops for 540x960 prep frame
    rows = []
    for box in [(280, 80, 500, 300), (260, 280, 500, 500)]:
        x0, y0, x1, y1 = box
        x1 = min(x1, ref.shape[1])
        y1 = min(y1, ref.shape[0])
        a = crop(ref, x0, y0, x1, y1)
        b = crop(small, x0, y0, x1, y1)
        rows.append(np.hstack([a, b]))
    bottom = np.hstack(rows)
    bw = top.shape[1]
    if bottom.shape[1] < bw:
        bottom = np.hstack([bottom, np.zeros((bottom.shape[0], bw - bottom.shape[1], 3), np.uint8)])
    elif bottom.shape[1] > bw:
        top = np.hstack([top, np.zeros((top.shape[0], bottom.shape[1] - bw, 3), np.uint8)])
    cv2.imwrite(str(path), np.vstack([top, bottom]))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tag = sys.argv[1] if len(sys.argv) > 1 else TAG

    content_full = load_bgr(CONTENT)
    style = load_bgr(STYLE_REF)
    print(f"content {content_full.shape}, style {style.shape}", flush=True)

    # Style prep at full res, then downscale for paint
    primed_full, prep_meta = style_prep(content_full, style)
    cv2.imwrite(str(OUT / f"{tag}_prep.png"), primed_full)

    ref = cv2.resize(primed_full, (PAINT_W, PAINT_H), interpolation=cv2.INTER_AREA)
    # Also keep original content at paint res for metric against primed path
    content_paint = cv2.resize(content_full, (PAINT_W, PAINT_H), interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(OUT / f"{tag}_prep_paintres.png"), ref)

    t0 = time.time()
    canvas, strokes = paint(ref)
    paint_s = time.time() - t0
    print(f"paint total {paint_s:.1f}s, {len(strokes)} strokes", flush=True)
    cv2.imwrite(str(OUT / f"{tag}_paint.png"), canvas)

    m0, _ = metrics(ref, canvas)
    print("paint only:", m0, flush=True)

    inked = ink(canvas, ref)
    cv2.imwrite(str(OUT / f"{tag}_inked.png"), inked)
    m1, small = metrics(ref, inked)
    print("with ink  :", m1, flush=True)

    # Metrics vs original content (pose fidelity) at paint res
    m_content, _ = metrics(content_paint, inked)
    print("vs content:", m_content, flush=True)

    compare(ref, small, OUT / f"{tag}_compare.png")

    np.savez_compressed(
        str(OUT / f"{tag}_strokes.npz"),
        layer=np.array([s[0] for s in strokes], np.uint8),
        radius=np.array([s[1] for s in strokes], np.float32),
        color=np.stack([s[2] for s in strokes]),
        lens=np.array([len(s[3]) for s in strokes], np.int32),
        pts=np.concatenate([s[3] for s in strokes]),
    )

    # Delivery 9:16 1080x1920
    deliver = inked
    if deliver.shape[1] != 1080 or deliver.shape[0] != 1920:
        deliver = cv2.resize(inked, (1080, 1920), interpolation=cv2.INTER_AREA)
    cv2.imwrite(
        str(OUT / f"{tag}_inked_9x16.jpg"),
        deliver,
        [int(cv2.IMWRITE_JPEG_QUALITY), 92],
    )

    metrics_doc = {
        "tag": tag,
        "content": str(CONTENT),
        "style_ref": str(STYLE_REF),
        "paint_input_size": [PAINT_W, PAINT_H],
        "output_size": [int(canvas.shape[1]), int(canvas.shape[0])],
        "S": S,
        "paint_seconds": round(paint_s, 1),
        "strokes": len(strokes),
        "paint": m0,
        "inked": m1,
        "inked_vs_content": m_content,
        "style_prep": prep_meta,
        "limits": [
            "Stroke remake follows primed content geometry; does not invent Ghibli subject matter.",
            "Style warmth is Lab-stat + texture only — no spatial style warp / NST.",
            "Cel anime source + oil-stroke paint = hybrid look; not full hand-painted plate.",
            "Ink from dark ridges of primed frame; may miss soft edges.",
        ],
    }
    with open(OUT / f"{tag}_metrics.json", "w") as f:
        json.dump(metrics_doc, f, indent=2, ensure_ascii=False)
    print(json.dumps(metrics_doc, indent=2, ensure_ascii=False), flush=True)
    print("done ->", OUT, flush=True)


if __name__ == "__main__":
    main()
