#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$ROOT/../../.." && pwd)"
PY="${REPO}/.venv/bin/python"
if [[ ! -x "$PY" ]]; then PY=python3; fi
OUT="$ROOT/out"
SRC="$ROOT/../frame_01_s01_hero_v8.jpg"
"$PY" "$ROOT/generate_strokes.py" --source "$SRC" --out "$OUT/strokes_v8_v2.json" --max-strokes 420000
"$PY" "$ROOT/render_strokes.py" --strokes "$OUT/strokes_v8_v2.json" --out "$OUT/stroke_v8_v2.png"
"$PY" "$ROOT/compare.py" \
  --original "$SRC" \
  --render "$OUT/stroke_v8_v2.png" \
  --out-heatmap "$OUT/diff_heatmap_v8_v2.png" \
  --out-metrics "$OUT/metrics_v8_v2.json" \
  --out-side-by-side "$OUT/compare_side_v8_v2.jpg"
echo DONE
