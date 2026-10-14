#!/usr/bin/env python3
"""Render stroke list JSON → PNG (no bitmap plate compositing)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from lib.brush import render_strokes_rgba


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strokes", type=Path, default=ROOT / "out" / "strokes_v8_v1.json")
    ap.add_argument("--out", type=Path, default=ROOT / "out" / "stroke_v8_v1.png")
    ap.add_argument("--bg", default="12,8,6", help="RGB background")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    data = json.loads(args.strokes.read_text(encoding="utf-8"))
    meta = data["meta"]
    strokes = data["strokes"]
    w, h = int(meta["width"]), int(meta["height"])
    bg = tuple(int(x) for x in args.bg.split(","))
    print(f"rendering {len(strokes)} strokes @ {w}x{h}", flush=True)
    im = render_strokes_rgba(w, h, strokes, bg_rgb=bg, seed=args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    im.save(args.out, optimize=True)
    print(f"wrote {args.out} size={args.out.stat().st_size}", flush=True)


if __name__ == "__main__":
    main()
