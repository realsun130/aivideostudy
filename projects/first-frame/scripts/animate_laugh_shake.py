#!/usr/bin/env python3
"""Beat 1 preview: Cavalier laugh + body shake + ears waving (3s mp4)."""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
RIG = ROOT / "rig"
OUT = RIG / "out"
PAINT = ROOT / "stroke_paint" / "out" / "acc_paint.png"
EDIT = ROOT / "frame_01_s01_hero_v8_acc_edit.jpg"
W, H = 1280, 720
FPS = 24
DURATION = 3.0
NFRAMES = int(FPS * DURATION)


def load_mask(name: str) -> np.ndarray:
    return np.array(Image.open(RIG / "part_masks" / f"{name}.png")).astype(np.float32) / 255.0


def blur_m(m: np.ndarray, r: float = 1.5) -> np.ndarray:
    im = Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8), "L")
    return np.array(im.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255.0


def warp_rotate(img: np.ndarray, angle_deg: float, cx: float, cy: float, mask: np.ndarray):
    """Inverse-map rotate; returns premultiplied RGB and coverage."""
    ang = math.radians(angle_deg)
    cos_a, sin_a = math.cos(ang), math.sin(ang)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx, dy = xx - cx, yy - cy
    xs = cos_a * dx + sin_a * dy + cx
    ys = -sin_a * dx + cos_a * dy + cy
    x0 = np.floor(xs).astype(np.int32)
    y0 = np.floor(ys).astype(np.int32)
    x1, y1 = x0 + 1, y0 + 1
    wx, wy = xs - x0, ys - y0
    valid = (x0 >= 0) & (x1 < W) & (y0 >= 0) & (y1 < H)

    def gather(ch):
        def at(xa, ya):
            return ch[np.clip(ya, 0, H - 1), np.clip(xa, 0, W - 1)]

        return (
            at(x0, y0) * (1 - wx) * (1 - wy)
            + at(x1, y0) * wx * (1 - wy)
            + at(x0, y1) * (1 - wx) * wy
            + at(x1, y1) * wx * wy
        )

    wout = np.where(valid, gather(mask), 0.0).astype(np.float32)
    out = np.zeros_like(img, dtype=np.float32)
    for c in range(3):
        out[:, :, c] = np.where(valid, gather(img[:, :, c].astype(np.float32) * mask), 0.0)
    return out, wout


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frames_dir = OUT / "frames_laugh"
    frames_dir.mkdir(exist_ok=True)

    paint_path = PAINT if PAINT.exists() else EDIT
    paint = np.array(Image.open(paint_path).convert("RGB").resize((W, H), Image.Resampling.LANCZOS))
    jp = json.loads((RIG / "skeleton.json").read_text())["rest_pose"]

    neck = (float(jp["cavalier_neck"]["x"]), float(jp["cavalier_neck"]["y"]))
    ear_L0 = (float(jp["cavalier_ear_L0"]["x"]), float(jp["cavalier_ear_L0"]["y"]))
    ear_R0 = (float(jp["cavalier_ear_R0"]["x"]), float(jp["cavalier_ear_R0"]["y"]))
    chin_p = (float(jp["cavalier_chin"]["x"]), float(jp["cavalier_chin"]["y"]))

    m_head = blur_m(load_mask("cavalier_head"), 1.5)
    m_mouth = blur_m(load_mask("cavalier_mouth"), 1.2)
    m_ear_L = blur_m(load_mask("cavalier_ear_L"), 1.2)
    m_ear_R = blur_m(load_mask("cavalier_ear_R"), 1.2)
    m_body = np.clip(m_head + m_mouth * 0.5, 0, 1)
    rest_move = np.clip(m_body + m_ear_L + m_ear_R + m_mouth, 0, 1)
    blur_plate = np.array(Image.fromarray(paint).filter(ImageFilter.GaussianBlur(4))).astype(np.float32)

    print(f"rendering {NFRAMES} frames @ {FPS}fps from {paint_path.name}")
    for i in range(NFRAMES):
        t = i / FPS
        # Body shake (~4 Hz laugh) + bounce
        shake_ang = 3.2 * math.sin(2 * math.pi * 4.0 * t) + 1.0 * math.sin(2 * math.pi * 2.0 * t)
        # Neck pivot drifts slightly for body feel
        ncx = neck[0] + 2.0 * math.sin(2 * math.pi * 3.5 * t)
        ncy = neck[1] + 4.0 * math.sin(2 * math.pi * 4.0 * t + 0.15)
        chin_ang = 2.0 * math.sin(2 * math.pi * 4.0 * t)
        wave = math.sin(2 * math.pi * 2.8 * t)
        ear_L_ang = 12.0 * wave + 4.0 * math.sin(2 * math.pi * 4.5 * t)
        ear_R_ang = -11.0 * wave + 3.5 * math.sin(2 * math.pi * 4.5 * t + 0.8)

        body_rgb, body_w = warp_rotate(paint, shake_ang, ncx, ncy, m_body)
        mouth_rgb, mouth_w = warp_rotate(paint, shake_ang + chin_ang, chin_p[0], chin_p[1], m_mouth)
        earL_rgb, earL_w = warp_rotate(paint, shake_ang * 0.5 + ear_L_ang, ear_L0[0], ear_L0[1], m_ear_L)
        earR_rgb, earR_w = warp_rotate(paint, shake_ang * 0.5 + ear_R_ang, ear_R0[0], ear_R0[1], m_ear_R)

        base = paint.astype(np.float32)
        damp = np.clip(rest_move * 0.9, 0, 1)[..., None]
        base = base * (1.0 - damp) + blur_plate * damp

        for rgb, w, gain in (
            (body_rgb, body_w, 0.95),
            (mouth_rgb, mouth_w, 0.92),
            (earL_rgb, earL_w, 1.0),
            (earR_rgb, earR_w, 1.0),
        ):
            a = np.clip(w * gain, 0, 1)[..., None]
            base = base * (1.0 - a) + rgb * a

        frame = np.clip(base, 0, 255).astype(np.uint8)
        Image.fromarray(frame).save(frames_dir / f"f_{i:04d}.png")
        if i % 12 == 0:
            print(f"  frame {i}/{NFRAMES}")

    mp4 = OUT / "laugh_shake_3s.mp4"
    subprocess.check_call(
        [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", str(frames_dir / "f_%04d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            "-movflags", "+faststart",
            str(mp4),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print("wrote", mp4, "bytes", mp4.stat().st_size)


if __name__ == "__main__":
    main()
