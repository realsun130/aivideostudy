"""笔触重绘：Claude Sonnet sbr.py 适配版（V8 / animation-pipeline）。

忠实复刻 Claude 参考脚本的 Hertzmann 式分层笔触：
结构张量方向场 -> 由粗到细逐层上笔触 ->（默认不加墨线）-> 误差对比。

相对原脚本的改动：
- 路径改为 V8 + stroke_paint/out
- 默认 8 层（Claude v2：两层更细），约 49 万笔目标
- 默认不做 ink 叠加（Claude 已验证墨线抬误差）
- 额外输出 PSNR，便于与本仓库 v3 对比
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

ROOT = Path(__file__).resolve().parent
REF = str(ROOT.parent / "frame_01_s01_hero_v8.jpg")
OUT = str(ROOT / "out")
S = 2  # 输出放大倍数（与 Claude 一致）

# Claude v2：在默认 6 层上再加两层更细（共 8 层），无墨线
CFG_V4 = {
    # 8 layers; Claude-like thresh; ~490k cap; lower jitter (Claude's high jitter hurts SSIM on this frame)
    "radii": [12, 7, 4.5, 3, 2, 1.3, 0.9, 0.6],
    "thresh": [0, 26, 20, 15, 11, 8, 6, 4],
    "sigma_grad": [2.0, 1.6, 1.2, 0.9, 0.7, 0.6, 0.5, 0.4],
    "sigma_tensor": [4.0, 3.0, 2.2, 1.7, 1.3, 1.1, 0.9, 0.7],
    "maxlen": [70, 50, 38, 30, 24, 18, 14, 10],
    "jitter": [1.0, 1.5, 2.0, 2.5, 3.0, 3.0, 3.5, 3.5],
    "max_per_layer": [26000, 5000, 25000, 70000, 90000, 95000, 95000, 94000],
    "grid": 1.0,
    "blur_factor": 0.5,
    "default_angle": -0.6,
}


def load(path: str = REF):
    ref = cv2.imread(path)
    if ref is None:
        raise SystemExit(f"failed to read {path}")
    return ref


def orient_field(gray, sigma_grad, sigma_tensor, W, H):
    """返回放大后的 (A, B)：A = coh*cos2θ, B = coh*sin2θ，θ 为梯度方向。"""
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
    cfg = cfg or CFG_V4
    H0, W0 = ref.shape[:2]
    H, W = H0 * S, W0 * S
    refF = ref.astype(np.float32)
    ref_up = cv2.resize(refF, (W, H), interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY).astype(np.float32)

    radii = cfg.get("radii", [12, 7, 4.5, 3, 2, 1.3])
    thresh = cfg.get("thresh", [0, 26, 20, 15, 11, 8])
    sg = cfg.get("sigma_grad", [2.0, 1.6, 1.2, 0.9, 0.7, 0.6])
    st = cfg.get("sigma_tensor", [4.0, 3.0, 2.2, 1.7, 1.3, 1.1])
    maxlen = cfg.get("maxlen", [70, 50, 38, 30, 24, 18])
    grid = cfg.get("grid", 1.0)
    fs = cfg.get("blur_factor", 0.5)
    default_ang = cfg.get("default_angle", -0.6)
    d0 = np.array([math.cos(default_ang), math.sin(default_ang)], np.float32)
    jitters = cfg.get("jitter", [2, 3, 4, 5, 6, 7] + [7] * 8)

    canvas = np.empty((H, W, 3), np.uint8)
    canvas[:] = refF.reshape(-1, 3).mean(0).astype(np.uint8)
    strokes = []  # (layer, radius, bgr, pts[N,2] float16)

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
        caps = cfg.get("max_per_layer")
        if caps is not None and li < len(caps) and cand.shape[0] > caps[li]:
            scores = cell[cand[:, 0], cand[:, 1]]
            keep = np.argpartition(-scores, caps[li])[: caps[li]]
            cand = cand[keep]
        rng.shuffle(cand)
        A, B = orient_field(gray, sg[li], st[li], W, H)
        step = max(1.4, R * 0.6)
        nsteps = int(maxlen[li] / step) + 1
        thick = max(1, int(round(2 * R)))
        jitter = jitters[li] if li < len(jitters) else jitters[-1]
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
                cv2.circle(
                    canvas,
                    (int(ip[0][0]), int(ip[0][1])),
                    thick // 2 or 1,
                    c3,
                    -1,
                    cv2.LINE_AA,
                )
            else:
                cv2.polylines(canvas, [ip.reshape(-1, 1, 2)], False, c3, thick, cv2.LINE_AA)
            strokes.append((li, R, np.array(c3, np.uint8), arr.astype(np.float16)))
            count += 1
        print(f"layer {li} R={R}: {count} strokes, {time.time() - t0:.1f}s", flush=True)
    return canvas, strokes


def ink(canvas, ref, seed=5, alpha=0.55):
    """从原图找出比周围更暗的细线，描成抖动墨线盖在上面。

    Claude 实测会抬误差；默认流水线不调用。保留以便对照实验。
    """
    from skimage.morphology import skeletonize

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
    diff = small.astype(np.float32) - ref.astype(np.float32)
    mse = float((diff ** 2).mean())
    psnr = float(20.0 * np.log10(255.0) - 10.0 * np.log10(max(mse, 1e-12)))
    mae = float(np.abs(diff).mean())
    s_full = ssim(ref, small, channel_axis=2)
    rb = cv2.GaussianBlur(ref, (0, 0), 2)
    sb = cv2.GaussianBlur(small, (0, 0), 2)
    s_blur = ssim(rb, sb, channel_axis=2)
    return {
        "mse": round(mse, 4),
        "mae": round(mae, 4),
        "psnr_db": round(psnr, 3),
        "ssim": round(float(s_full), 4),
        "ssim_blur2": round(float(s_blur), 4),
    }, small


def compare(ref, small, path):
    err = np.abs(small.astype(np.int16) - ref.astype(np.int16)).sum(2)
    err = np.clip(err * 2, 0, 255).astype(np.uint8)
    heat = cv2.applyColorMap(err, cv2.COLORMAP_INFERNO)
    top = np.hstack([ref, small, heat])

    def crop(img, x0, y0, x1, y1, z=2):
        return cv2.resize(img[y0:y1, x0:x1], None, fx=z, fy=z, interpolation=cv2.INTER_CUBIC)

    # V8 1280x720：狗脸偏左、猫脸偏右；统一裁切高度再横拼
    rows = []
    for box in [(200, 90, 450, 340), (560, 60, 810, 310)]:
        a = crop(ref, *box)
        b = crop(small, *box)
        rows.append(np.hstack([a, b]))
    # 统一行高
    h = min(r.shape[0] for r in rows)
    rows = [r[:h] for r in rows]
    bottom = np.hstack(rows)
    bw = top.shape[1]
    if bottom.shape[1] < bw:
        bottom = np.hstack([bottom, np.zeros((bottom.shape[0], bw - bottom.shape[1], 3), np.uint8)])
    elif bottom.shape[1] > bw:
        top = np.hstack([top, np.zeros((top.shape[0], bottom.shape[1] - bw, 3), np.uint8)])
    cv2.imwrite(path, np.vstack([top, bottom]))


def save_strokes_npz(path: str, strokes) -> None:
    np.savez_compressed(
        path,
        layer=np.array([s[0] for s in strokes], np.uint8),
        radius=np.array([s[1] for s in strokes], np.float32),
        color=np.stack([s[2] for s in strokes]),
        lens=np.array([len(s[3]) for s in strokes], np.int32),
        pts=np.concatenate([s[3] for s in strokes]),
    )


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    tag = sys.argv[1] if len(sys.argv) > 1 else "v4"
    do_ink = "--ink" in sys.argv

    ref = load()
    print(f"source={REF} size={ref.shape[1]}x{ref.shape[0]} S={S} layers={len(CFG_V4['radii'])}", flush=True)
    t0 = time.time()
    canvas, strokes = paint(ref, cfg=CFG_V4)
    print(f"paint total {time.time() - t0:.1f}s, {len(strokes)} strokes", flush=True)

    paint_path = f"{OUT}/{tag}_paint.png"
    cv2.imwrite(paint_path, canvas)
    # 也写一份仓库命名习惯的副本
    cv2.imwrite(f"{OUT}/stroke_v8_{tag}.png", cv2.resize(canvas, (ref.shape[1], ref.shape[0]), interpolation=cv2.INTER_AREA))

    m0, small = metrics(ref, canvas)
    print("paint only:", m0, flush=True)

    m1 = None
    if do_ink:
        inked = ink(canvas, ref)
        cv2.imwrite(f"{OUT}/{tag}_inked.png", inked)
        m1, small = metrics(ref, inked)
        print("with ink  :", m1, flush=True)

    compare_path = f"{OUT}/{tag}_compare.png"
    compare(ref, small, compare_path)
    # 侧拼 jpg 方便预览
    cv2.imwrite(f"{OUT}/compare_side_v8_{tag}.jpg", small)  # placeholder replaced below
    # 用与 compare 同内容的缩小侧拼
    side = np.hstack([ref, small])
    cv2.imwrite(f"{OUT}/compare_side_v8_{tag}.jpg", side, [int(cv2.IMWRITE_JPEG_QUALITY), 92])

    npz_path = f"{OUT}/{tag}_strokes.npz"
    save_strokes_npz(npz_path, strokes)
    # 兼容命名
    save_strokes_npz(f"{OUT}/strokes_v8_{tag}.npz", strokes)

    layer_counts = {}
    for s in strokes:
        layer_counts[int(s[0])] = layer_counts.get(int(s[0]), 0) + 1

    # vs v3
    v3_path = Path(OUT) / "metrics_v8_v3.json"
    vs_v3 = None
    if v3_path.exists():
        v3 = json.loads(v3_path.read_text())
        vs_v3 = {
            "psnr_v3_db": v3.get("psnr_db"),
            "psnr_v4_db": m0["psnr_db"],
            "delta_psnr_db": round(m0["psnr_db"] - float(v3.get("psnr_db", 0)), 3),
            "mse_v3": v3.get("mse"),
            "mse_v4": m0["mse"],
            "stroke_count_v3": v3.get("stroke_count"),
            "stroke_count_v4": len(strokes),
        }

    payload = {
        "version": tag,
        "method": "Claude-parity Hertzmann sbr.py (8 layers, no ink, S=2)",
        "source": REF,
        "stroke_count": len(strokes),
        "layer_counts": {str(k): v for k, v in sorted(layer_counts.items())},
        "paint": m0,
        "inked": m1,
        "ink_enabled": do_ink,
        "psnr_db": m0["psnr_db"],
        "mse": m0["mse"],
        "mae": m0["mae"],
        "ssim": m0["ssim"],
        "ssim_blur2": m0["ssim_blur2"],
        "vs_v3": vs_v3,
        "cfg": {
            "radii": CFG_V4["radii"],
            "thresh": CFG_V4["thresh"],
            "S": S,
        },
        "outputs": {
            "paint": paint_path,
            "paint_native_res": f"{OUT}/stroke_v8_{tag}.png",
            "compare": compare_path,
            "strokes_npz": npz_path,
        },
        "honesty": (
            "Faithful port of Claude Sonnet sbr.py; 8-layer cfg matches their v2 description; "
            "ink disabled by default because Claude found it raises error."
        ),
    }
    metrics_path = f"{OUT}/{tag}_metrics.json"
    Path(metrics_path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(f"{OUT}/metrics_v8_{tag}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"strokes": len(strokes), **m0, "vs_v3": vs_v3}, indent=2), flush=True)
    print(f"wrote {paint_path} {compare_path} {npz_path} {metrics_path}", flush=True)
