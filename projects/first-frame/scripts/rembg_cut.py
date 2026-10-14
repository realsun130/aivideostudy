#!/usr/bin/env python3
"""
rembg auto-matting for Frame 01 hero (default: V8).

Produces:
  - assets/layers_alpha/v8_full_rgba.png          (full-frame RGBA matte)
  - assets/layers_alpha/<layer_id>.png            (bbox crop + rembg alpha)

Reads bbox from assets/manifest.json for:
  live_maine_coon, cavalier_subject, phone_back, paw_lamp, wall_photo

Honesty note: rembg is a single-subject saliency matte. On a multi-character
bedroom MCU it often merges Cavalier+Maine (and props) into one blob on the
full frame; per-bbox crops are better but still bleed bedding/paws.

Re-run (from repo root):
  .venv-rembg/bin/python projects/first-frame/scripts/rembg_cut.py
  # optional: --input path/to.jpg --model u2net
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image
from rembg import new_session, remove

REPO = Path(__file__).resolve().parents[3]
FF = REPO / "projects" / "first-frame"
DEFAULT_INPUT = FF / "frame_01_s01_hero_v8.jpg"
MANIFEST = FF / "assets" / "manifest.json"
OUT_DIR = FF / "assets" / "layers_alpha"

# manifest ids to cut from the chosen source (V8 by default)
CUT_IDS = [
    "live_maine_coon",
    "cavalier_subject",
    "phone_back",
    "paw_lamp",
    "wall_photo",
]

# output filenames (stable for compositor)
OUT_NAMES = {
    "live_maine_coon": "live_maine_coon.png",
    "cavalier_subject": "cavalier_subject.png",
    "phone_back": "phone_back.png",
    "paw_lamp": "paw_lamp.png",
    "wall_photo": "wall_photo.png",
}


def load_manifest_bboxes(manifest_path: Path) -> dict[str, dict]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    by_id = {}
    for asset in data.get("assets", []):
        aid = asset["id"]
        if aid in CUT_IDS:
            by_id[aid] = asset["bbox"]
    missing = [i for i in CUT_IDS if i not in by_id]
    if missing:
        raise SystemExit(f"manifest missing bbox for: {missing}")
    return by_id


def crop_box(img: Image.Image, bbox: dict) -> Image.Image:
    x, y, w, h = int(bbox["x"]), int(bbox["y"]), int(bbox["w"]), int(bbox["h"])
    x2 = min(img.width, x + w)
    y2 = min(img.height, y + h)
    x = max(0, x)
    y = max(0, y)
    return img.crop((x, y, x2, y2))


def rembg_rgba(img: Image.Image, session) -> Image.Image:
    """Return RGBA with alpha matte. Input RGB/RGBA."""
    rgb = img.convert("RGB")
    out = remove(rgb, session=session)
    if out.mode != "RGBA":
        out = out.convert("RGBA")
    return out


def alpha_stats(img: Image.Image) -> str:
    a = img.getchannel("A")
    hist = a.histogram()
    total = sum(hist)
    opaque = sum(hist[200:])
    transparent = sum(hist[:16])
    return (
        f"{img.size[0]}x{img.size[1]} "
        f"opaque≈{opaque / total:.1%} transparent≈{transparent / total:.1%}"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="rembg cut Frame 01 layers from V8")
    ap.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Source frame (default: V8 hero jpg)",
    )
    ap.add_argument(
        "--manifest",
        type=Path,
        default=MANIFEST,
        help="manifest.json with rough bboxes",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=OUT_DIR,
        help="Output directory for RGBA PNGs",
    )
    ap.add_argument(
        "--model",
        default="u2net",
        help="rembg model name (u2net, u2netp, isnet-general-use, ...)",
    )
    ap.add_argument(
        "--skip-full",
        action="store_true",
        help="Skip full-frame matte (faster / less RAM)",
    )
    args = ap.parse_args()

    if not args.input.is_file():
        print(f"ERROR: input not found: {args.input}", file=sys.stderr)
        return 1
    if not args.manifest.is_file():
        print(f"ERROR: manifest not found: {args.manifest}", file=sys.stderr)
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    bboxes = load_manifest_bboxes(args.manifest)

    print(f"input:    {args.input}")
    print(f"manifest: {args.manifest}")
    print(f"out_dir:  {args.out_dir}")
    print(f"model:    {args.model}")
    print("loading rembg session…")
    session = new_session(args.model)

    src = Image.open(args.input).convert("RGB")
    print(f"source size: {src.size[0]}x{src.size[1]}")

    report = []

    if not args.skip_full:
        print("rembg full frame…")
        full = rembg_rgba(src, session)
        full_path = args.out_dir / "v8_full_rgba.png"
        full.save(full_path, optimize=True)
        stats = alpha_stats(full)
        print(f"  wrote {full_path.relative_to(REPO)}  ({stats})")
        report.append(("v8_full_rgba", stats))
        del full

    for aid in CUT_IDS:
        bbox = bboxes[aid]
        crop = crop_box(src, bbox)
        print(f"rembg crop {aid}  bbox=({bbox['x']},{bbox['y']},{bbox['w']},{bbox['h']})…")
        rgba = rembg_rgba(crop, session)
        out_name = OUT_NAMES[aid]
        out_path = args.out_dir / out_name
        rgba.save(out_path, optimize=True)
        stats = alpha_stats(rgba)
        print(f"  wrote {out_path.relative_to(REPO)}  ({stats})")
        report.append((aid, stats))
        del rgba, crop

    print("\n=== rembg cut done ===")
    for name, stats in report:
        print(f"  {name}: {stats}")
    print(
        "\nQuality honesty: full-frame matte often merges subjects; "
        "crop mattes still include bedding/paw bleed. Not production cutouts."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
