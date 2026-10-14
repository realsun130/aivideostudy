#!/usr/bin/env bash
# Claude-parity Hertzmann stroke repaint (sbr.py), 8 layers, ~490k, no ink.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$ROOT/../../.." && pwd)"
PY="${REPO}/.venv/bin/python"
if [[ ! -x "$PY" ]]; then PY=python3; fi
"$PY" "$ROOT/sbr.py" v4
echo DONE
"$PY" -c "
import json
from pathlib import Path
out = Path(r'$ROOT/out')
v3, v4 = out/'metrics_v8_v3.json', out/'metrics_v8_v4.json'
a, b = json.loads(v3.read_text()), json.loads(v4.read_text())
print(f\"PSNR v3={a['psnr_db']} -> v4={b['psnr_db']}  (delta {b['psnr_db']-a['psnr_db']:+.3f} dB)\")
print(f\"MSE  v3={a['mse']} -> v4={b['mse']}\")
print(f\"SSIM={b.get('ssim')}  SSIM_blur2={b.get('ssim_blur2')}  strokes={b.get('stroke_count')}\")
"
