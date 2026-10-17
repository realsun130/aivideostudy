"""笔触重绘：以参考图为输入，用分层笔触重新画出这一帧。

流程：结构张量方向场 -> 由粗到细逐层上笔触（Hertzmann 式）-> 墨线轮廓 -> 误差对比。
所有输出写到 out/ 目录；笔触清单保存为 strokes.npz，供后续渲染器和动画使用。
"""
import sys, time, json, math
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from skimage.morphology import skeletonize

REF = '/mnt/user-data/uploads/1791967461496_image.png'
OUT = '/home/claude/sbr/out'
S = 2  # 输出放大倍数


def load():
    ref = cv2.imread(REF)
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
    cfg = cfg or {}
    H0, W0 = ref.shape[:2]
    H, W = H0 * S, W0 * S
    refF = ref.astype(np.float32)
    ref_up = cv2.resize(refF, (W, H), interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY).astype(np.float32)

    radii = cfg.get('radii', [12, 7, 4.5, 3, 2, 1.3])
    thresh = cfg.get('thresh', [0, 26, 20, 15, 11, 8])
    sg = cfg.get('sigma_grad', [2.0, 1.6, 1.2, 0.9, 0.7, 0.6])
    st = cfg.get('sigma_tensor', [4.0, 3.0, 2.2, 1.7, 1.3, 1.1])
    maxlen = cfg.get('maxlen', [70, 50, 38, 30, 24, 18])
    grid = cfg.get('grid', 1.0)
    fs = cfg.get('blur_factor', 0.5)
    default_ang = cfg.get('default_angle', -0.6)
    d0 = np.array([math.cos(default_ang), math.sin(default_ang)], np.float32)

    canvas = np.empty((H, W, 3), np.uint8)
    canvas[:] = refF.reshape(-1, 3).mean(0).astype(np.uint8)
    strokes = []  # (layer, radius, bgr, pts[N,2] int16)

    for li, R in enumerate(radii):
        t0 = time.time()
        refb = cv2.GaussianBlur(ref_up, (0, 0), fs * R)
        diff = np.sqrt(((canvas.astype(np.float32) - refb) ** 2).sum(2))
        g = max(2, int(round(R * grid)))
        hc, wc = H // g, W // g
        d = diff[:hc * g, :wc * g].reshape(hc, g, wc, g)
        cell = d.mean(axis=(1, 3))
        am = d.transpose(0, 2, 1, 3).reshape(hc, wc, g * g).argmax(-1)
        cand = np.argwhere(cell > thresh[li])
        rng.shuffle(cand)
        A, B = orient_field(gray, sg[li], st[li], W, H)
        step = max(1.4, R * 0.6)
        nsteps = int(maxlen[li] / step) + 1
        thick = max(1, int(round(2 * R)))
        jitter = cfg.get('jitter', [2, 3, 4, 5, 6, 7])[li]
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
        print(f'layer {li} R={R}: {count} strokes, {time.time()-t0:.1f}s', flush=True)
    return canvas, strokes


def ink(canvas, ref, seed=5, alpha=0.55):
    """从原图找出比周围更暗的细线，描成抖动墨线盖在上面。"""
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
        # 一圈轮廓是闭合回路，取一半避免来回重复
        half = c[: len(c) // 2 + 1]
        if len(half) < 8:
            continue
        pts = half.astype(np.float32) * S + S / 2
        # 低频抖动
        t = np.arange(len(pts), dtype=np.float32)
        ph = rng.uniform(0, 6.28, 2)
        off = 0.8 * np.sin(t * 0.35 + ph[0]) + 0.5 * np.sin(t * 0.9 + ph[1])
        d = np.gradient(pts, axis=0)
        nrm = np.stack([-d[:, 1], d[:, 0]], 1)
        nrm /= (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-6)
        pts = pts + nrm * off[:, None]
        # 取线上平均颜色并压暗
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
    print(f'ink: {n} lines', flush=True)
    return np.clip(out, 0, 255).astype(np.uint8)


def metrics(ref, canvas):
    small = cv2.resize(canvas, (ref.shape[1], ref.shape[0]), interpolation=cv2.INTER_AREA)
    mse = float(((small.astype(np.float32) - ref.astype(np.float32)) ** 2).mean())
    s_full = ssim(ref, small, channel_axis=2)
    rb = cv2.GaussianBlur(ref, (0, 0), 2)
    sb = cv2.GaussianBlur(small, (0, 0), 2)
    s_blur = ssim(rb, sb, channel_axis=2)
    return {'mse': round(mse, 1), 'ssim': round(float(s_full), 3), 'ssim_blur2': round(float(s_blur), 3)}, small


def compare(ref, small, path):
    err = np.abs(small.astype(np.int16) - ref.astype(np.int16)).sum(2)
    err = np.clip(err * 2, 0, 255).astype(np.uint8)
    heat = cv2.applyColorMap(err, cv2.COLORMAP_INFERNO)
    top = np.hstack([ref, small, heat])
    # 放大看细节：狗脸、猫脸
    def crop(img, x0, y0, x1, y1, z=2):
        return cv2.resize(img[y0:y1, x0:x1], None, fx=z, fy=z, interpolation=cv2.INTER_CUBIC)
    rows = []
    for box in [(110, 110, 290, 290), (320, 60, 500, 240)]:
        a = crop(ref, *box); b = crop(small, *box)
        rows.append(np.hstack([a, b]))
    bottom = np.hstack(rows)
    bw = top.shape[1]
    pad = np.zeros((bottom.shape[0], bw - bottom.shape[1], 3), np.uint8) if bottom.shape[1] < bw else None
    if pad is not None:
        bottom = np.hstack([bottom, pad])
    elif bottom.shape[1] > bw:
        top = np.hstack([top, np.zeros((top.shape[0], bottom.shape[1] - bw, 3), np.uint8)])
    cv2.imwrite(path, np.vstack([top, bottom]))


if __name__ == '__main__':
    import os
    os.makedirs(OUT, exist_ok=True)
    tag = sys.argv[1] if len(sys.argv) > 1 else 'v1'
    ref = load()
    t0 = time.time()
    canvas, strokes = paint(ref)
    print(f'paint total {time.time()-t0:.1f}s, {len(strokes)} strokes')
    cv2.imwrite(f'{OUT}/{tag}_paint.png', canvas)
    m0, _ = metrics(ref, canvas)
    print('paint only:', m0)
    inked = ink(canvas, ref)
    cv2.imwrite(f'{OUT}/{tag}_inked.png', inked)
    m1, small = metrics(ref, inked)
    print('with ink  :', m1)
    compare(ref, small, f'{OUT}/{tag}_compare.png')
    np.savez_compressed(f'{OUT}/{tag}_strokes.npz',
                        layer=np.array([s[0] for s in strokes], np.uint8),
                        radius=np.array([s[1] for s in strokes], np.float32),
                        color=np.stack([s[2] for s in strokes]),
                        lens=np.array([len(s[3]) for s in strokes], np.int32),
                        pts=np.concatenate([s[3] for s in strokes]))
    json.dump({'paint': m0, 'inked': m1, 'strokes': len(strokes)}, open(f'{OUT}/{tag}_metrics.json', 'w'))
