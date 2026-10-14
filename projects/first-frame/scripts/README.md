# Frame 01 scripts

## compose_from_recipe.py

第一版合成器：读 `recipes/v8_style_recipe.json` + `assets/manifest.json`，把 `assets/layers_alpha/` 透明层按 bbox / z_order 叠到底图，输出静帧 PNG。

```bash
# from repo root
python3 projects/first-frame/scripts/compose_from_recipe.py

# 推荐日常改道具（避免角色双重曝光）
python3 projects/first-frame/scripts/compose_from_recipe.py --overlays-only

# 调爪灯强度、藏手机背面
python3 projects/first-frame/scripts/compose_from_recipe.py \
  --overlays-only --paw-lamp-intensity 1.3 --hide phone_back

# 纯透明层堆叠（无底图，看 matte 质量）
python3 projects/first-frame/scripts/compose_from_recipe.py --base none

# 关掉合影黑领结（代码画的参数领结）
python3 projects/first-frame/scripts/compose_from_recipe.py --no-photo-bowtie
```

默认输出：`projects/first-frame/code_assets/out/compose_v8_recipe_v1.png`

| 参数 | 含义 |
|------|------|
| `--base v9\|v8\|none` | 底图：v9 锁定板 / v8 全图 / 深色空画布 |
| `--overlays-only` | 只叠 `paw_lamp` / `phone_back` / `wall_photo` |
| `--paw-lamp-intensity F` | 覆盖 recipe `editable_params.paw_lamp_intensity`（默认 1.0） |
| `--hide ID …` | 隐藏层（如 `phone_back`） |
| `--no-photo-bowtie` | 不画合影胸前黑领结 |
| `--out PATH` | 输出 PNG |

**v1 诚实缺口**：底图已烘焙角色时再叠角色 alpha 会重影；rembg 毛边未精修；无动画；发卡/床上缅因领结尚无独立 alpha。

依赖：Python 3 + Pillow。

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
