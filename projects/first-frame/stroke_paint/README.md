# 笔触重绘 · V8 单帧验证（stroke_paint）

按 Claude 建议的路径做**单帧验证**：用结构张量从 V8 提取笔触方向与颜色，生成可版本控制的笔触清单，再用 Python 纯代码渲染——**不叠位图素材**。

## 目标

- 输出：笔触清单 JSON + 渲染图 + 与原图误差（MSE / PSNR / 热力图）
- 验证「原图 → 笔触数据 → 代码重绘」能否逼近锁定帧
- 满意后再拆部件做动画（本目录 v1 **不做动画**）

## 流程

1. **结构张量**：算每像素笔触走向（沿等照线 / 毛发切向）与相干度  
2. **粗分区**：用 AABB 粗标狗 / 猫 / 手机 / 爪灯 / 床 / 墙等（**粗糙，不是精抠**）  
3. **分层下笔**：大笔色块 → 中笔 → 细笔 → 边缘墨线  
4. **渲染**：Pillow 多鬃毛笔触（彩铅感近似）  
5. **对比**：对 V8 算 MSE / RMSE / MAE / PSNR，出误差热力图

## 怎么跑

依赖：Python 3 + `Pillow` + `numpy`（无需 OpenCV / scipy / rembg）

```bash
# 一键
python3 projects/first-frame/stroke_paint/run_v8_validation.py

# 或分步
python3 projects/first-frame/stroke_paint/generate_strokes.py \
  --source projects/first-frame/frame_01_s01_hero_v8.jpg \
  --out projects/first-frame/stroke_paint/out/strokes_v8_v1.json \
  --max-strokes 28000

python3 projects/first-frame/stroke_paint/render_strokes.py \
  --strokes projects/first-frame/stroke_paint/out/strokes_v8_v1.json \
  --out projects/first-frame/stroke_paint/out/stroke_v8_v1.png

python3 projects/first-frame/stroke_paint/compare.py \
  --original projects/first-frame/frame_01_s01_hero_v8.jpg \
  --render projects/first-frame/stroke_paint/out/stroke_v8_v1.png \
  --out-heatmap projects/first-frame/stroke_paint/out/diff_heatmap_v8_v1.png \
  --out-metrics projects/first-frame/stroke_paint/out/metrics_v8_v1.json \
  --out-side-by-side projects/first-frame/stroke_paint/out/compare_side_v8_v1.jpg
```

## 产出路径

| 文件 | 含义 |
|------|------|
| `out/strokes_v8_v1.json` | 笔触清单（含 meta） |
| `out/strokes_v8_v1_meta.json` | 精简 meta + 分层计数 |
| `out/stroke_v8_v1.png` | 代码渲染结果 |
| `out/metrics_v8_v1.json` | MSE / PSNR 等 |
| `out/diff_heatmap_v8_v1.png` | 误差热力图 |
| `out/compare_side_v8_v1.jpg` | 原图 \| 渲染 \| 热力图 |
| `out/debug_orientation_v8.png` | 结构张量方向可视化 |
| `out/debug_regions_v8.png` | 粗分区可视化 |

## 诚实说明（v1 质量）

- **不是** huashu 全量 ETF / 几十万笔 WebGL 级；为了可跑通，笔触上限约 **2.8 万**。
- 分区是 **AABB 粗框**，不是像素级遮罩；只够给笔触打 region 标签，不能当精修 matte。
- 渲染是 Pillow 短线鬃毛近似，毛发细度、眼神高光、爪灯光晕会明显糊于 V8。
- 预期 PSNR 不会接近「照片级」；本步目标是**闭环可复现**，用误差指导下一轮（加笔、改层、补遮罩）。
- 同 `seed` + 同 JSON → 渲染可复现（鬃毛抖动由 seed 固定）。

## 和抠图叠层路线的关系

| 路线 | 本质 | 本验证中的位置 |
|------|------|----------------|
| rembg + 合成器 | 位图透明贴纸叠层 | **本目录不使用** |
| 笔触重绘 | 画面变成笔触数据 + 代码 | **当前主线** |

## 下一步（验证满意后）

- 提高笔触密度 / 按误差图自适应加笔  
- 用更好的区域遮罩拆部件（狗头、下巴、猫眼皮…）  
- 迁到 Canvas/WebGL 批量绘制并做部件动画

## v1 实测指标（2026-10-14）

对 `frame_01_s01_hero_v8.jpg`（1280×720），`--max-strokes 28000`（实际 **19441** 笔）：

| 指标 | 值 |
|------|-----|
| MSE | 851.11 |
| RMSE | 29.17 |
| MAE | 19.02 |
| PSNR | **18.83 dB** |

分层计数：coarse 4440 / mid 6207 / fine 4690 / detail 1604 / ink 2500。

读法：能认出查理王、缅因、手机、爪灯与合影，但整体偏暗糊、毛发与眼神远不及 V8。PSNR≈19 dB 说明这是**可跑通的逼近草稿**，不是成片；下一轮应加笔、提高亮部采样、收紧分区。
