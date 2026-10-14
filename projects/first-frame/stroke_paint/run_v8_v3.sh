#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$ROOT/../../.." && pwd)"
PY="${REPO}/.venv/bin/python"
if [[ ! -x "$PY" ]]; then PY=python3; fi
OUT="$ROOT/out"
SRC="$ROOT/../frame_01_s01_hero_v8.jpg"
"$PY" "$ROOT/generate_strokes_v3.py" --source "$SRC" --out "$OUT/strokes_v8_v3.json" --max-strokes 450000
"$PY" "$ROOT/render_strokes.py" \
  --strokes "$OUT/strokes_v8_v3.json" \
  --out "$OUT/stroke_v8_v3.png" \
  --color-jitter 2 \
  --tone-match "$SRC"
"$PY" "$ROOT/compare.py" \
  --original "$SRC" \
  --render "$OUT/stroke_v8_v3.png" \
  --out-heatmap "$OUT/diff_heatmap_v8_v3.png" \
  --out-metrics "$OUT/metrics_v8_v3.json" \
  --out-side-by-side "$OUT/compare_side_v8_v3.jpg"
echo DONE
"$PY" -c "
import json
from pathlib import Path
out = Path(r'$OUT')
v2, v3 = out/'metrics_v8_v2.json', out/'metrics_v8_v3.json'
if v2.exists() and v3.exists():
    a, b = json.loads(v2.read_text()), json.loads(v3.read_text())
    print(f\"PSNR v2={a['psnr_db']} -> v3={b['psnr_db']}  (delta {b['psnr_db']-a['psnr_db']:+.3f} dB)\")
    print(f\"MSE  v2={a['mse']} -> v3={b['mse']}\")
"
