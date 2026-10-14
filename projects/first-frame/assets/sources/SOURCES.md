# Asset source versions (Frame 01)

| version | project path | agent asset sha256 prefix | role |
|---------|--------------|---------------------------|------|
| v8 | `projects/first-frame/frame_01_s01_hero_v8.jpg` | `6ed9c7f1359927ce…` | LIVE Maine Coon (bed subject)；**全部 rembg alpha 也从 V8 切** |
| v9 | `projects/first-frame/frame_01_s01_hero_v9.jpg` | `fbd82c3ad8d781ee…` | base plate + 旧版 rough_crop 其余层（jpg） |

Canonical locked hero (post pixel-edit) remains `frame_01_s01_hero.jpg` (= v10 edit) for reference, but **extraction sources for this experiment are v8/v9 as above**.

## rembg 透明层（2026-10-14）

- **已完成**：对 V8 跑 `scripts/rembg_cut.py`（模型 `u2net`）。
- 全帧：`assets/layers_alpha/v8_full_rgba.png`
- 按 manifest bbox 裁切再抠：`live_maine_coon` / `cavalier_subject` / `phone_back` / `paw_lamp` / `wall_photo` → `assets/layers_alpha/*.png`
- manifest 中对应条目 `status: alpha_rembg`，字段 `alpha_path`
- **诚实**：rembg 是单主体显著性抠图；全帧常把查理王+缅因+手机+灯糊成一块；分块仍会带床品/毛边出血，**不是精修生产级抠图**。
- **下一步**：写合成器读 `recipes/v8_style_recipe.json` + `manifest.json` 的 alpha 层叠层。

重跑：

```bash
python3 -m venv .venv-rembg
.venv-rembg/bin/pip install -r projects/first-frame/scripts/requirements-rembg.txt
.venv-rembg/bin/python projects/first-frame/scripts/rembg_cut.py
```
