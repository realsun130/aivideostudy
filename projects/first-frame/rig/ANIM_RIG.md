# Frame 01 · 动画绑定说明（切分 + 骨架）v2

> 源帧：`frame_01_s01_hero_v8_acc_edit.jpg`  
> 笔触：`stroke_paint/out/acc_strokes.npz`（约 49 万笔）  
> 产出目录：`projects/first-frame/rig/`  
> 参考叠图：用户提供的查理王耳链 / 头链 / 颊关节示意

---

## 0. 三拍动画

| 拍 | 内容 | 主要驱动关节 / 部件 |
|----|------|---------------------|
| **Beat 1** | 查理王大笑抖动 + 耳自然甩动 | `cavalier_neck/head/crown/jaw/cheek` + `ear_L0–L3` / `ear_R0–R3` |
| **Beat 2** | 手机凑近给缅因 | `shoulder→elbow→paw_hold→phone` |
| **Beat 3** | 缅因无语转头 | `maine_neck` + `maine_eyes` |

静帧：`paw_lamp`、`wall_photo`、`bed`、`bg`。

---

## 1. 部件遮罩（part_masks）

| 部件 ID | 含义 | 叠层色 |
|---------|------|--------|
| `cavalier_head` | 头颅主体（不含耳/嘴优先层） | 红 |
| `cavalier_ear_L` | 画面左耳（粉发卡）— **多边形∩rembg 贴毛边** | 青 |
| `cavalier_ear_R` | 画面右耳 — 贴毛边 | 青绿 |
| `cavalier_mouth` | 张嘴腔（舌/齿/口腔） | 紫 |
| `phone` | 手机背面 | 蓝紫 |
| `maine_head` / `maine_eyes` | 缅因头 / 眼带 | 青 |
| `wall_photo` / `paw_lamp` / `bed` / `bg` | 静物与背景 | — |

**耳约定**：`L/R` = 屏幕左右；`ear_L` = 粉发卡。

### 质量说明
- 耳/嘴改为 **手绘多边形 ∩ rembg α**（并去掉枕套误检），比椭圆 ROI 更贴毛边；仍非精修 matte。
- `bed`/`bg` 仍为几何分区。
- 够用：笔触标签、骨骼预览、三拍阻塞动画。

生成脚本：`scripts/build_anim_rig.py`。

---

## 2. 骨架（skeleton.json）

坐标系：源图像素，**1280×720**，原点左上。

### 查理王
- **头链（绿）**：`root → neck → head → crown`（竖直穿过颅中线）
- **左耳三节（黄）**：`ear_L0 → L1 → L2 → L3`（沿耳毛；L1 近粉发卡）
- **右耳三节（黄）**：`ear_R0 → R1 → R2 → R3`
- **颌/颊**：`jaw`（张嘴）+ `cheek`（红点，viewer-left 颊铰）
- **手臂（蓝）**：`shoulder → elbow → paw_hold → phone`

### 缅因
`maine_root → neck → head → eyes`

### 静关节
`paw_lamp`、`wall_photo`（parent=null）

---

## 3. 三拍怎么动

### Beat 1 · 大笑抖动
1. `cavalier_neck` 枢轴，头链小幅旋转/位移（spring）
2. `jaw` / `cheek` 微张合
3. 双耳链分段延迟上下甩（secondary）
4. 笔触：变换 head / ear_* / mouth

### Beat 2 · 手机凑近
手臂链整体向缅因方向推；phone 朝向锁（背面朝镜）

### Beat 3 · 缅因转头
`maine_neck` 转开 + `maine_eyes` 视线滑开

---

## 4. 文件清单

| 文件 | 说明 |
|------|------|
| `part_masks/*.png` | 各部件软遮罩 |
| `skeleton.json` | rest pose + bones + drivers |
| `overlay_parts.png` / `overlay_skeleton.png` / `overlay_preview.png` | 预览 |
| `stroke_part_ids.npy` / `stroke_part_counts.json` | 笔触归属 |
| `out/laugh_shake_3s.mp4` | Beat1 预览动画（若已渲） |
| `ANIM_RIG.md` | 本说明 |

---

## 5. 笔触归属统计

| 部件 | 笔数 |
|------|------|
| `bg` | 99583 |
| `bed` | 157784 |
| `wall_photo` | 27817 |
| `paw_lamp` | 26147 |
| `maine_head` | 98011 |
| `maine_eyes` | 14373 |
| `cavalier_head` | 41171 |
| `cavalier_ear_L` | 2863 |
| `cavalier_ear_R` | 12706 |
| `cavalier_mouth` | 6120 |
| `phone` | 4902 |
| `unlabeled` | 11 |

---

## 6. 下一步
1. 微调耳多边形若仍溢边
2. 三拍关键帧（先仿射/旋转笔触）
3. 张嘴/转头露馅补笔
