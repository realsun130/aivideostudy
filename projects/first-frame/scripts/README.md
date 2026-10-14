# Frame 01 scripts

## compose_from_recipe.py

合成器 v2：读 `recipes/v8_style_recipe.json` + `assets/manifest.json`，把 `assets/layers_alpha/` 透明层按 bbox / z_order 叠到**清底图**，输出静帧 PNG。

```bash
# from repo root — 默认 --base clean，全层叠（角色不再双重曝光）
python3 projects/first-frame/scripts/compose_from_recipe.py

# 只改道具层
python3 projects/first-frame/scripts/compose_from_recipe.py --overlays-only

# 调爪灯强度、藏手机背面
python3 projects/first-frame/scripts/compose_from_recipe.py \
  --paw-lamp-intensity 1.3 --hide phone_back

# 对照：旧烘焙底（会重影）
python3 projects/first-frame/scripts/compose_from_recipe.py --base v9

# 纯透明层堆叠（无底图）
python3 projects/first-frame/scripts/compose_from_recipe.py --base none

# 关掉合影黑领结（代码画的参数领结）
python3 projects/first-frame/scripts/compose_from_recipe.py --no-photo-bowtie
```

默认输出：`projects/first-frame/code_assets/out/compose_v8_recipe_v2.png`

| 参数 | 含义 |
|------|------|
| `--base clean\|v9\|v8\|none` | 底图：清底（默认）/ 烘焙 v9 / v8 全图 / 深色空画布 |
| `--overlays-only` | 只叠 `paw_lamp` / `phone_back` / `wall_photo` |
| `--paw-lamp-intensity F` | 覆盖 recipe `editable_params.paw_lamp_intensity`（默认 1.0） |
| `--hide ID …` | 隐藏层（如 `phone_back`） |
| `--no-photo-bowtie` | 不画合影胸前黑领结 |
| `--out PATH` | 输出 PNG |

**v2 诚实缺口**：清底是模糊填洞不是生成式 inpaint（主体洞呈软糊、灯晕可能拖影）；rembg 毛边未精修；无动画；发卡/床上缅因领结尚无独立 alpha。

依赖：Python 3 + Pillow。

## build_clean_plate.py

从 V8 + rembg 全图 matte 生成无角色清底 `assets/base/base_plate_clean.jpg`。

```bash
python3 projects/first-frame/scripts/build_clean_plate.py
```

遮罩 = rembg 前景 ∪ 爪灯 bbox ∪ 角色头顶部；墙照合影 ROI 与左右/底边受保护。填充 = 多尺度高斯模糊 + 墙/枕/床均值色（无 OpenCV）。调试 mask：`assets/base/base_plate_clean_mask.png`。

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
