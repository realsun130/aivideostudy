# Frame 01 scripts

## rembg_cut.py

对 `frame_01_s01_hero_v8.jpg` 做 rembg 自动抠图，输出 `assets/layers_alpha/`。

```bash
# from repo root
python3 -m venv .venv-rembg
.venv-rembg/bin/pip install -r projects/first-frame/scripts/requirements-rembg.txt
.venv-rembg/bin/python projects/first-frame/scripts/rembg_cut.py
# optional: --model u2netp  (smaller)  --skip-full
```

venv 目录 `.venv-rembg/` 已进 `.gitignore`，勿提交。
