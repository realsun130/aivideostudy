#!/usr/bin/env python3
"""Local accessory edit on Frame01 V8 (no whole-frame regen).

Edits (edit-lock: only named accessory ROIs):
1. Remove ALL bows on live Maine Coon (hair bow near ear / wall-edge tuft).
2. Remove wall-frame Maine hair bow (蝴蝶结).
3. Wall-frame Maine neck: recolor original bow shape → black 领结.
4. Wall-frame Cavalier: add pink butterfly ear bow (from v9 ROI).
5. Live Cavalier pink ear bow left untouched.

Method: feather-paste cleaned fur from v9 into removal ROIs; recolor v8 red
neck-bow chroma mask to near-black with preserved shading; paste v9 pink ear
bow onto wall Cavalier. Then optional sbr re-stroke is a separate step.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

FF = Path(__file__).resolve().parents[1]
OUTD = FF / "stroke_paint" / "out"


def feather_paste(dst, src_img, x0, y0, x1, y1, feather=16):
    H, W = dst.shape[:2]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(W, x1), min(H, y1)
    roi_s = src_img[y0:y1, x0:x1].astype(np.float32)
    h, w = roi_s.shape[:2]
    alpha = np.ones((h, w), np.float32)
    f = max(1, feather)
    for i in range(f):
        a = (i + 1) / (f + 1.0)
        alpha[i, :] *= a
        alpha[h - 1 - i, :] *= a
        alpha[:, i] *= a
        alpha[:, w - 1 - i] *= a
    a3 = alpha[..., None]
    dst[y0:y1, x0:x1] = np.clip(
        roi_s * a3 + dst[y0:y1, x0:x1].astype(np.float32) * (1 - a3), 0, 255
    ).astype(np.uint8)


def black_bowtie_from_red(out, v8, v9, box=(400, 100, 535, 185)):
    """Clean neck via v9, then recolor v8 red-bow shape to black 领结."""
    x0, y0, x1, y1 = box
    feather_paste(out, v9, x0, y0, x1, y1, feather=14)

    lab8 = cv2.cvtColor(v8, cv2.COLOR_BGR2LAB).astype(np.float32)
    lab9 = cv2.cvtColor(v9, cv2.COLOR_BGR2LAB).astype(np.float32)
    da = lab8[:, :, 1] - lab9[:, :, 1]
    dl = np.abs(lab8[:, :, 0] - lab9[:, :, 0])
    z = (
        (da[y0:y1, x0:x1] > 5)
        | ((dl[y0:y1, x0:x1] > 12) & (da[y0:y1, x0:x1] > 2))
    ).astype(np.uint8) * 255
    roi = v8[y0:y1, x0:x1]
    b, g, r = roi[:, :, 0], roi[:, :, 1], roi[:, :, 2]
    rd = (
        (r.astype(np.int16) > g.astype(np.int16) + 25)
        & (r.astype(np.int16) > b.astype(np.int16) + 20)
        & (r > 60)
    ).astype(np.uint8) * 255
    z = cv2.bitwise_or(z, rd)
    z = cv2.morphologyEx(z, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    z = cv2.morphologyEx(z, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(z, 8)
    keep = np.zeros_like(z)
    items = sorted([(stats[i, 4], i) for i in range(1, n)], reverse=True)
    for area, i in items[:2]:
        if area < 80:
            continue
        keep[labels == i] = 255
    keep = cv2.dilate(keep, np.ones((2, 2), np.uint8), 1)

    H, W = out.shape[:2]
    mask = np.zeros((H, W), np.uint8)
    mask[y0:y1, x0:x1] = keep
    OUTD.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUTD / "dbg_acc_bowmask.jpg"), keep)

    src = v8.astype(np.float32)
    Y = 0.114 * src[:, :, 0] + 0.587 * src[:, :, 1] + 0.299 * src[:, :, 2]
    sel = mask > 0
    if not np.any(sel):
        return out
    ymin, ymax = float(Y[sel].min()), float(Y[sel].max())
    Yn = (Y - ymin) / (ymax - ymin + 1e-6)
    bgr_new = np.stack([12 + Yn * 28, 10 + Yn * 22, 14 + Yn * 30], axis=2)
    alpha = cv2.GaussianBlur(mask, (0, 0), 1.2).astype(np.float32) / 255.0
    a3 = alpha[..., None]
    out = np.clip(out.astype(np.float32) * (1 - a3) + bgr_new * a3, 0, 255).astype(
        np.uint8
    )
    edges = cv2.Canny(mask, 50, 120)
    edges = cv2.dilate(edges, np.ones((2, 2), np.uint8), 1)
    out[edges > 0] = (
        out[edges > 0].astype(np.float32) * 0.35
        + np.array([20, 15, 25], np.float32) * 0.65
    ).astype(np.uint8)
    return out


def save_strips(v8, out, v9):
    OUTD.mkdir(parents=True, exist_ok=True)

    def strip(box, name):
        x0, y0, x1, y1 = box
        parts = [
            cv2.resize(im[y0:y1, x0:x1], None, fx=3, fy=3)
            for im in (v8, out, v9)
        ]
        gap = np.full((parts[0].shape[0], 6, 3), 40, np.uint8)
        side = parts[0]
        for p in parts[1:]:
            side = np.concatenate([side, gap, p], 1)
        cv2.imwrite(str(OUTD / f"dbg_acc_{name}.jpg"), side)

    strip((640, 130, 820, 280), "live_maine")
    strip((440, 38, 535, 108), "wall_maine_hair")
    strip((400, 100, 535, 185), "wall_maine_neck")
    strip((292, 40, 398, 120), "wall_cav_ear")
    wp = np.concatenate(
        [
            cv2.resize(v8[20:230, 250:700], None, fx=2, fy=2),
            np.full((420, 8, 3), 40, np.uint8),
            cv2.resize(out[20:230, 250:700], None, fx=2, fy=2),
        ],
        1,
    )
    cv2.imwrite(str(OUTD / "dbg_acc_wall_full.jpg"), wp)
    diff = np.abs(out.astype(np.float32) - v8.astype(np.float32)).sum(2)
    heat = cv2.applyColorMap(
        (diff / (diff.max() + 1e-6) * 255).astype(np.uint8), cv2.COLORMAP_INFERNO
    )

    def fit(im, w=640):
        h = int(im.shape[0] * w / im.shape[1])
        return cv2.resize(im, (w, h))

    cv2.imwrite(
        str(OUTD / "compare_acc_edit_v8.jpg"),
        np.concatenate([fit(v8), fit(out), fit(heat)], 1),
        [cv2.IMWRITE_JPEG_QUALITY, 92],
    )


def edit(v8_path: Path, v9_path: Path, out_path: Path) -> dict:
    v8 = cv2.imread(str(v8_path))
    v9 = cv2.imread(str(v9_path))
    if v8 is None or v9 is None:
        raise SystemExit(f"missing source: {v8_path} or {v9_path}")
    out = v8.copy()

    # 1) live Maine bows (head + wall-edge tuft)
    feather_paste(out, v9, 640, 130, 820, 280, feather=18)
    # 2) wall Maine hair bow
    feather_paste(out, v9, 440, 38, 535, 108, feather=14)
    # 3) wall Maine neck → black 领结
    out = black_bowtie_from_red(out, v8, v9)
    # 4) wall Cavalier pink ear bow
    feather_paste(out, v9, 292, 40, 398, 120, feather=14)

    cv2.imwrite(str(out_path), out, [cv2.IMWRITE_JPEG_QUALITY, 95])
    save_strips(v8, out, v9)

    diff = np.abs(out.astype(np.float32) - v8.astype(np.float32)).sum(2)
    cav = np.abs(
        out[260:370, 280:400].astype(np.float32)
        - v8[260:370, 280:400].astype(np.float32)
    ).mean()
    return {
        "out": str(out_path),
        "changed_px": int((diff > 12).sum()),
        "mean_diff": float(diff.mean()),
        "live_cav_bow_mean_diff": float(cav),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--v8", type=Path, default=FF / "frame_01_s01_hero_v8.jpg")
    ap.add_argument("--v9", type=Path, default=FF / "frame_01_s01_hero_v9.jpg")
    ap.add_argument(
        "--out", type=Path, default=FF / "frame_01_s01_hero_v8_acc_edit.jpg"
    )
    args = ap.parse_args()
    info = edit(args.v8, args.v9, args.out)
    print(info, flush=True)


if __name__ == "__main__":
    main()
