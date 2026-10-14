#!/usr/bin/env python3
"""One-shot: generate strokes → render → compare vs V8."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent / "frame_01_s01_hero_v8.jpg"
OUT = ROOT / "out"
PY = sys.executable


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    strokes = OUT / "strokes_v8_v1.json"
    render = OUT / "stroke_v8_v1.png"
    run(
        [
            PY,
            str(ROOT / "generate_strokes.py"),
            "--source",
            str(SRC),
            "--out",
            str(strokes),
            "--max-strokes",
            "28000",
        ]
    )
    run(
        [
            PY,
            str(ROOT / "render_strokes.py"),
            "--strokes",
            str(strokes),
            "--out",
            str(render),
        ]
    )
    run(
        [
            PY,
            str(ROOT / "compare.py"),
            "--original",
            str(SRC),
            "--render",
            str(render),
            "--out-heatmap",
            str(OUT / "diff_heatmap_v8_v1.png"),
            "--out-metrics",
            str(OUT / "metrics_v8_v1.json"),
            "--out-side-by-side",
            str(OUT / "compare_side_v8_v1.jpg"),
        ]
    )
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
