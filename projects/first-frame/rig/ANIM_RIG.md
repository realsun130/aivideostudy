# Frame 01 · 动画绑定说明（切分 + 骨架）

> 源帧：`frame_01_s01_hero_v8_acc_edit.jpg`（配件已改：床上缅因无结、合影缅黑领结、合影查理王粉发卡）  
> 笔触：`stroke_paint/out/acc_strokes.npz`（约 49 万笔）  
> 产出目录：`projects/first-frame/rig/`

---

## 0. 三拍动画（本绑定服务的镜头）

| 拍 | 内容 | 主要驱动关节 / 部件 |
|----|------|---------------------|
| **Beat 1** | 查理王大笑到抖动 | `cavalier_neck` / `cavalier_head` / `cavalier_jaw` + 双耳；遮罩 `cavalier_head`、`cavalier_mouth`、`cavalier_ear_L/R` |
| **Beat 2** | 把手机凑近给缅因看 | `cavalier_paw_hold` → `phone` 前推；轻带 `cavalier_root`；遮罩 `phone` |
| **Beat 3** | 缅因无语，眼神转走 / 转头 | `maine_neck` 转开 + `maine_eyes` 视线；遮罩 `maine_head`、`maine_eyes` |

静帧不动：`paw_lamp`、`wall_photo`、`bed`、`bg`（爪灯可后续做强度脉冲，但不绑骨骼）。

---

## 1. 部件遮罩（part_masks）

路径：`rig/part_masks/*.png`（单通道 0–255）+ `label_map.png` + `legend.json`。

| 部件 ID | 含义 | 叠层色（预览） |
|---------|------|----------------|
| `cavalier_head` | 查理王头颅主体（不含耳/嘴优先层） | 红 |
| `cavalier_ear_L` | 画面左耳（粉发卡所在） | 粉 |
| `cavalier_ear_R` | 画面右耳 | 橙粉 |
| `cavalier_mouth` | 张嘴/下颌区 | 亮红 |
| `phone` | 手机背面 | 蓝紫 |
| `maine_head` | 缅因头 | 青 |
| `maine_eyes` | 缅因眼带 | 亮青 |
| `wall_photo` | 墙上合影框 | 金 |
| `paw_lamp` | 爪灯 | 琥珀 |
| `bed` | 被窝/床面带 | 褐 |
| `bg` | 墙面与其余背景 | 暗灰 |

**耳约定**：`L/R` = **屏幕左右**（不是解剖左右）。`cavalier_ear_L` = 带粉发卡的那只。

### 质量诚实说明

- 主体来自既有 **rembg** 透明层（`assets/layers_alpha/`），毛边、被褥粘连仍在，**不是**精修 matte。
- 头/耳/嘴/眼是 **椭圆 ROI ∩ rembg**，边界发糊、会互相抢像素；嘴巴张合露出的「新内容」尚未补画。
- `bed` / `bg` 是几何分区，不是语义分割；床头柜并进 `bg`/`paw_lamp` 周边。
- 够用做：**笔触打标签、骨骼驱动预览、三拍阻塞动画**；不够用做：最终成片级抠像。

生成脚本：`scripts/build_anim_rig.py`。

---

## 2. 骨架（skeleton.json）

- 坐标系：源图像素，原点左上，画布 **1280×720**。
- 查理王链：`cavalier_root → neck → head → {ear_L, ear_R, jaw}`；`root → paw_hold → phone`。
- 缅因链：`maine_root → neck → head → eyes`。
- 静关节：`paw_lamp`、`wall_photo`（parent=null）。

Rest pose 已按 acc_edit 手标；误差大约 **±10–20px**，动画前可再微调。

---

## 3. 部件 ↔ 三拍映射（怎么动）

### Beat 1 · 大笑抖动
1. 以 `cavalier_neck` 为枢轴，对 `cavalier_head` 做小幅旋转/位移动画（spring / noise）。
2. `cavalier_jaw` 微张合；遮罩 `cavalier_mouth` 随父级旋转。
3. `cavalier_ear_L/R` 加延迟抖动（secondary）。
4. 笔触：只变换 `part_id ∈ {cavalier_head, ear_*, mouth}` 的笔。

### Beat 2 · 手机凑近
1. `cavalier_paw_hold` 向缅因方向（右上）平移；`phone` 子级跟随。
2. **朝向锁**：手机保持背面朝镜头，禁止翻成屏幕朝镜。
3. 可选：查理王肩 `cavalier_root` 轻跟。
4. 笔触：变换 `phone`（及少量 paw 区若后续加遮罩）。

### Beat 3 · 缅因无语转头
1. `maine_neck` 向右（远离手机/查理王）旋转。
2. `maine_eyes` 视线先瞟手机再滑开；半眯保持。
3. 露出的颈侧若出现空缺，需补笔或拖影（本版 **未** 补画）。
4. 笔触：变换 `maine_head` + `maine_eyes`。

---

## 4. 文件清单

| 文件 | 说明 |
|------|------|
| `part_masks/*.png` | 各部件软遮罩 |
| `part_masks/label_map.png` | 索引图（见 legend.json） |
| `part_masks/legend.json` | 部件 id ↔ 像素值 |
| `skeleton.json` | 关节 rest pose + bones + drivers |
| `overlay_parts.png` | 遮罩彩色叠层预览 |
| `overlay_skeleton.png` | 骨架叠层预览 |
| `overlay_preview.png` | 遮罩+骨架合成预览 |
| `stroke_part_ids.npy` | 每笔部件 id（对 acc_strokes；坐标已 /2，因 sbr `S=2`） |
| `stroke_part_counts.json` | 各部件笔数统计 |
| `ANIM_RIG.md` | 本说明 |

---

## 5. 笔触归属统计（acc_strokes）

| 部件 | 笔数 |
|------|------|
| `bg` | 99137 |
| `bed` | 158224 |
| `wall_photo` | 27817 |
| `paw_lamp` | 26147 |
| `maine_head` | 98011 |
| `maine_eyes` | 14373 |
| `cavalier_head` | 24974 |
| `cavalier_ear_L` | 6882 |
| `cavalier_ear_R` | 17972 |
| `cavalier_mouth` | 11879 |
| `phone` | 4902 |
| `unlabeled` | 1170 |

---

## 6. 下一步

1. 预览 `overlay_preview.png`，必要时改 `build_anim_rig.py` 里椭圆中心再生成。
2. 用 `skeleton.json` drivers 做三拍关键帧（先 2D 仿射/旋转笔触）。
3. 张嘴/转头露馅处再补笔触或 hold-out 层。
