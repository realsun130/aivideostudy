#!/usr/bin/env python3
"""Frame-driven motion 成片 for stolen-night S45.

Uses locked stills 01..08.jpg. One primary camera/prop move per shot.
Time = local_frame / fps only. Silent h264 1080x1920 @24fps, 45.00s.
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
STILLS = ROOT / "stills"
OUT_DIR = ROOT / "out"
MOTION_DIR = ROOT / "motion"
FPS = 24
W, H = 1080, 1920
DURATIONS_SEC = [4, 5, 5, 6, 6, 7, 6, 6]
DURATIONS_F = [s * FPS for s in DURATIONS_SEC]  # 96,120,120,144,144,168,144,144
TOTAL_F = sum(DURATIONS_F)  # 1080
OUT_MP4 = OUT_DIR / "stolen_night_s45_motion.mp4"
MANIFEST = ROOT / "assembly_manifest.json"


def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def ease_in_out_quart(t: float) -> float:
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        return 8 * t * t * t * t
    return 1 - (-2 * t + 2) ** 4 / 2


def cover_crop(
    img: Image.Image, scale: float, cx: float, cy: float, out_w: int = W, out_h: int = H
) -> Image.Image:
    """Scale image by `scale` (>=1) then crop out_w x out_h at normalized (cx,cy)."""
    sw, sh = img.size
    tw, th = int(round(sw * scale)), int(round(sh * scale))
    tw = max(tw, out_w)
    th = max(th, out_h)
    scaled = img.resize((tw, th), Image.Resampling.LANCZOS)
    cx = max(0.0, min(1.0, cx))
    cy = max(0.0, min(1.0, cy))
    left = int(round(cx * tw - out_w / 2))
    top = int(round(cy * th - out_h / 2))
    left = max(0, min(tw - out_w, left))
    top = max(0, min(th - out_h, top))
    return scaled.crop((left, top, left + out_w, top + out_h))


def apply_rotate(img: Image.Image, degrees: float) -> Image.Image:
    """Rotate then center-crop to WxH. Input should be oversized to avoid black edges."""
    if abs(degrees) < 1e-6:
        if img.size == (W, H):
            return img
        iw, ih = img.size
        left = (iw - W) // 2
        top = (ih - H) // 2
        return img.crop((left, top, left + W, top + H))
    rot = img.rotate(degrees, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=(0, 0, 0))
    iw, ih = rot.size
    left = (iw - W) // 2
    top = (ih - H) // 2
    return rot.crop((left, top, left + W, top + H))


def soft_white_overlay(base: Image.Image, alpha: float) -> Image.Image:
    if alpha <= 0:
        return base
    overlay = Image.new("RGB", (W, H), (255, 252, 248))
    return Image.blend(base, overlay, max(0.0, min(1.0, alpha)))


def cool_dim(base: Image.Image, amount: float) -> Image.Image:
    """Mild cool grade + dim warm side. amount 0..1."""
    if amount <= 0:
        return base
    # Darken slightly
    darkened = ImageEnhance.Brightness(base).enhance(1.0 - 0.12 * amount)
    # Shift toward cool: blend with a cool-tinted version
    r, g, b = darkened.split()
    # reduce red a bit, bump blue
    r2 = r.point(lambda v: int(v * (1.0 - 0.08 * amount)))
    b2 = b.point(lambda v: min(255, int(v * (1.0 + 0.10 * amount))))
    cool = Image.merge("RGB", (r2, g, b2))
    return Image.blend(darkened, cool, 0.55 * amount)


def darken(base: Image.Image, amount: float) -> Image.Image:
    if amount <= 0:
        return base
    black = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.blend(base, black, max(0.0, min(1.0, amount)))


def handheld(frame: int, amp_px: float = 1.5) -> tuple[float, float]:
    """Seeded tiny handheld offset in normalized center shift (~px / size)."""
    # Deterministic phase from frame only
    dx = math.sin(frame * 0.17) * amp_px + math.sin(frame * 0.41) * (amp_px * 0.4)
    dy = math.cos(frame * 0.13) * amp_px + math.sin(frame * 0.29) * (amp_px * 0.35)
    return dx / W, dy / H


def render_shot(shot_idx: int, local_f: int, n_f: int, img: Image.Image) -> Image.Image:
    t = local_f / max(1, n_f - 1)  # 0..1 inclusive over shot
    # Default center
    cx, cy = 0.5, 0.5
    scale = 1.0
    rot = 0.0
    fog = 0.0
    cool = 0.0
    dark = 0.0
    fade_black = 0.0

    if shot_idx == 0:
        # Entry: push-in 1.00→1.06 + slight downward drift (tired weight)
        e = ease_in_out_quart(t)
        scale = 1.00 + 0.06 * e
        cy = 0.48 + 0.045 * e  # drift down into frame weight
        cx = 0.50

    elif shot_idx == 1:
        # Steam: z 1.02 hold, 2px vertical drift, fog pulse 0→0.12→0.08
        scale = 1.02
        # 2px vertical sine drift over shot
        cy = 0.50 + (2.0 * math.sin(t * math.pi * 2)) / H
        # fog: rise to 0.12 at mid-early then settle 0.08
        if t < 0.45:
            fog = 0.12 * ease_out(t / 0.45)
        else:
            fog = 0.12 + (0.08 - 0.12) * ease_in_out((t - 0.45) / 0.55)

    elif shot_idx == 2:
        # Makeup: gentle pan right toward phone on counter
        e = ease_in_out_quart(t)
        scale = 1.05
        cx = 0.42 + 0.16 * e  # pan right
        cy = 0.52

    elif shot_idx == 3:
        # Mask: settle 1.04→1.00 ease-out first 18f, then micro breathing ±0.5%
        if local_f < 18:
            e = ease_out(local_f / 17)
            scale = 1.04 + (1.00 - 1.04) * e
        else:
            # breathing after settle
            phase = (local_f - 18) / FPS  # seconds after settle
            breath = 0.005 * math.sin(phase * 2 * math.pi / 3.2)  # ~3.2s cycle
            scale = 1.00 + breath
        cx, cy = 0.50, 0.48

    elif shot_idx == 4:
        # Scroll: slow upward pan + tiny handheld
        e = ease_in_out(t)
        scale = 1.08
        cy = 0.58 - 0.12 * e  # pan up (content scrolls up feel)
        cx = 0.50
        hx, hy = handheld(local_f, amp_px=1.8)
        cx += hx
        cy += hy

    elif shot_idx == 5:
        # Slow scroll: even slower upward pan; cool grade rises
        e = ease_in_out(t)
        scale = 1.10
        cy = 0.56 - 0.08 * e
        cx = 0.50
        hx, hy = handheld(local_f, amp_px=1.2)
        cx += hx
        cy += hy
        cool = 0.15 + 0.55 * e  # blue dominates gradually

    elif shot_idx == 6:
        # Sleep: ease toward pillow, rotate -1.5°, darken 0→8%
        e = ease_in_out_quart(t)
        scale = 1.06 + 0.02 * e
        cx = 0.50 + 0.04 * e
        cy = 0.45 + 0.10 * e  # toward pillow
        rot = -1.5 * e
        dark = 0.08 * e

    elif shot_idx == 7:
        # Hold: push 1.00→1.03 then fade-to-black last 0.8s (19.2f ≈ 20f)
        e = ease_in_out_quart(t)
        scale = 1.00 + 0.03 * e
        cx, cy = 0.50, 0.50
        fade_frames = int(round(0.8 * FPS))  # 19
        if local_f >= n_f - fade_frames:
            ft = (local_f - (n_f - fade_frames)) / max(1, fade_frames - 1)
            fade_black = ease_in_out(ft)

    else:
        raise ValueError(shot_idx)

    if abs(rot) > 1e-6:
        # Oversized crop → rotate → center WxH (keeps edges filled at ±1.5°)
        over_w, over_h = int(W * 1.12), int(H * 1.12)
        frame = cover_crop(img, scale * 1.12, cx, cy, over_w, over_h)
        frame = apply_rotate(frame, rot)
    else:
        frame = cover_crop(img, scale, cx, cy)

    if fog > 0:
        frame = soft_white_overlay(frame, fog)
    if cool > 0:
        frame = cool_dim(frame, cool)
    if dark > 0:
        frame = darken(frame, dark)
    if fade_black > 0:
        frame = darken(frame, fade_black)

    return frame.convert("RGB")


def load_stills() -> list[Image.Image]:
    imgs = []
    for i in range(1, 9):
        p = STILLS / f"{i:02d}.jpg"
        if not p.exists():
            raise FileNotFoundError(p)
        im = Image.open(p).convert("RGB")
        if im.size != (W, H):
            im = im.resize((W, H), Image.Resampling.LANCZOS)
        imgs.append(im)
    return imgs


def write_manifest(approach: str) -> None:
    shots = []
    t0 = 0.0
    moves = [
        "push-in 1.00→1.06 + downward drift (tired weight)",
        "fog opacity pulse 0→0.12→0.08; z1.02 + 2px vertical drift",
        "gentle pan right toward phone (scale 1.05)",
        "settle scale 1.04→1.00 (18f ease-out) then ±0.5% breath",
        "slow upward pan + tiny handheld (scale 1.08)",
        "slower upward pan + cool grade rise (scale 1.10)",
        "ease toward pillow, rotate -1.5°, darken→8%",
        "near-static push 1.00→1.03; fade-to-black last 0.8s",
    ]
    for i, (sec, nf) in enumerate(zip(DURATIONS_SEC, DURATIONS_F)):
        shots.append(
            {
                "shot": i + 1,
                "still": f"stills/{i+1:02d}.jpg",
                "start_sec": t0,
                "duration_sec": sec,
                "frames": nf,
                "primary_move": moves[i],
                "transition_in": "cut" if i > 0 else "none",
                "transition_out": "fade-to-black" if i == 7 else "cut",
            }
        )
        t0 += sec
    manifest = {
        "project": "stolen-night-s45",
        "title": "偷来的夜 Track S motion 成片",
        "version": "motion-v1",
        "output": "out/stolen_night_s45_motion.mp4",
        "spec": {
            "duration_sec": 45.0,
            "width": W,
            "height": H,
            "fps": FPS,
            "codec": "h264",
            "pix_fmt": "yuv420p",
            "audio": "silent",
        },
        "approach": approach,
        "stills_locked": True,
        "transitions_default": "hard_cut",
        "shots": shots,
        "bans_honored": [
            "no whoosh",
            "no particles",
            "no lens flare",
            "no text/watermark",
            "no Date.now motion",
            "no roof-cam reframe",
        ],
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    imgs = load_stills()
    approach = (
        "Python/PIL frame-driven camera (scale/pan/rotate/fog/grade) "
        "piped raw RGB → ffmpeg libx264 yuv420p; hard cuts; silent"
    )
    write_manifest(approach)

    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}",
        "-r", str(FPS),
        "-i", "pipe:0",
        "-an",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "18",
        "-movflags", "+faststart",
        str(OUT_MP4),
    ]
    print(f"Rendering {TOTAL_F} frames → {OUT_MP4}", flush=True)
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdin is not None

    global_f = 0
    try:
        for si, nf in enumerate(DURATIONS_F):
            for lf in range(nf):
                frame = render_shot(si, lf, nf, imgs[si])
                proc.stdin.write(frame.tobytes())
                global_f += 1
                if global_f % 48 == 0 or global_f == TOTAL_F:
                    print(f"  frame {global_f}/{TOTAL_F} (shot {si+1})", flush=True)
        proc.stdin.close()
        stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
        rc = proc.wait()
        if rc != 0:
            print(stderr[-4000:], file=sys.stderr)
            return rc
    except BrokenPipeError:
        stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
        print("ffmpeg pipe broke:\n", stderr[-4000:], file=sys.stderr)
        return 1

    print("done", OUT_MP4, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
