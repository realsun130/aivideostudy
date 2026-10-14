#!/usr/bin/env python3
"""Capture scene.html frames with Playwright Chromium, encode with FFmpeg."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

FPS = 30
DURATION_FRAMES = 90
WIDTH = 640
HEIGHT = 360


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent / "out" / "demo.mp4",
        help="Output mp4 path",
    )
    parser.add_argument(
        "--frames-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "frames",
        help="Temporary PNG frame directory",
    )
    parser.add_argument("--fps", type=int, default=FPS)
    parser.add_argument("--frames", type=int, default=DURATION_FRAMES)
    args = parser.parse_args()

    if shutil.which("ffmpeg") is None:
        print("ffmpeg not found on PATH", file=sys.stderr)
        return 1

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright missing; run: uv sync && uv run playwright install chromium", file=sys.stderr)
        return 1

    scene = Path(__file__).resolve().parent / "scene.html"
    if not scene.is_file():
        print(f"missing scene: {scene}", file=sys.stderr)
        return 1

    frames_dir: Path = args.frames_dir
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True)

    out: Path = args.out
    out.parent.mkdir(parents=True, exist_ok=True)

    print(f"Capturing {args.frames} frames @ {args.fps}fps from {scene.name} …")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})
        page.goto(scene.as_uri())
        page.wait_for_function("() => typeof window.renderFrame === 'function'")

        for i in range(args.frames):
            page.evaluate("(f) => window.renderFrame(f)", i)
            # small settle so canvas paint is flushed
            page.wait_for_timeout(16)
            page.screenshot(path=str(frames_dir / f"frame_{i:05d}.png"), type="png")
            if i % 30 == 0 or i == args.frames - 1:
                print(f"  frame {i + 1}/{args.frames}")

        browser.close()

    pattern = str(frames_dir / "frame_%05d.png")
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(args.fps),
        "-i",
        pattern,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(out),
    ]
    print("Encoding:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"Wrote {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
