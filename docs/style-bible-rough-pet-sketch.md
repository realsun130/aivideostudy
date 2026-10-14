# Style Bible 深摘要：Rough Animation Pet Sketch Storyboard

> 纯画风。无运镜、无转场、无时长。权威源：[`styles/rough-animation-pet-sketch-storyboard-style/style_bible.json`](../styles/rough-animation-pet-sketch-storyboard-style/style_bible.json)

## 元数据

| 字段 | 值 |
|------|-----|
| project_id | `rough-animation-pet-sketch-storyboard` |
| version | `2026-10-13.2` |
| title | Rough Animation Pet Sketch Storyboard |
| medium | `2d_illustration` |
| cookbook slug | `rough-animation-pet-sketch-storyboard-style` @ `2026.05.15` |
| upstream | [AI-Visual-Prompt-Cookbook](https://github.com/VigoZhao/AI-Visual-Prompt-Cookbook/tree/main/styles/rough-animation-pet-sketch-storyboard-style) |

**summary（原文）：** 松散动画分镜素描风：暖米色纸、红棕结构线、暗红褐潦草轮廓、半透明水色填充、夸张宠物表情与简单室内道具驱动的喜剧节拍。

**medium_notes：** 动画开发草图 / storyboard 完成度，不是精修矢量卡通；保留修正笔触与未完成感。

## 色板

### Primary

| name | hex | role |
|------|-----|------|
| warm_beige | `#E8DCC8` | primary |
| cream | `#F5EDE0` | primary |
| pale_peach | `#F0D5C4` | primary |
| soft_tan | `#D4B896` | primary |

### Accent

| name | hex | role |
|------|-----|------|
| red_brown_pencil | `#8B4513` | accent（结构线） |
| dark_burgundy_ink | `#4A1525` | accent（轮廓） |
| nearly_black_brown | `#2B1A14` | accent |
| muted_gray_blue | `#8FA0B0` | accent |
| peach_blush | `#E8B4A8` | accent |
| orange_food | `#E07A3D` | accent |
| warm_ochre | `#C9953A` | accent |

### Background / Forbidden

| name | hex | role |
|------|-----|------|
| warm_paper | `#E8DCC8` | bg |
| cold_neon | `#00FFCC` | **forbidden** |
| gloss_plastic | `#FF69B4` | **forbidden** |

## 线 / 光 / 质感 / 字体

| 块 | 内容 |
|----|------|
| line | weight=`variable`, style=`sketchy`；红棕结构线可见；暗红褐潦草轮廓多层叠压；允许修正笔触与未完成线 |
| lighting | mood=`soft_diffused`；暖室内漫射；忌电影级硬光与超写实毛发高光 |
| texture | grain=`medium`, paper=`true`；暖米色纸感 + 半透明水色；保留粗糙阴影与碎屑/动势记号 |
| typography | 手写 rough note / tiny production scribble；色 `#4A1525` / `#8B4513`；MAIN_TEXT/SECONDARY_TEXT 通常可空；忌完美排版与密集可读招牌 |

## 静帧构图（非运动）

- **preferred_framings:** `medium`, `close_up`, `wide`
- **aspect_hints:** `9:16 vertical storyboard poster`, `16:9 horizontal animation-board crop`
- **layer_order:**
  1. warm beige paper or interior wash
  2. thin red-brown room construction lines
  3. loose color blocks for characters and prop
  4. dark scratchy contour passes
  5. facial features and exaggerated eyes
  6. foreground crumbs, motion ticks, stress marks, sparks, and rough shadows
- **notes（原文）：** 只描述静帧取景与图层堆叠；运动/转场/时长不在本文件。

> 「motion ticks」在这里是**画面上的手绘动势记号**（草图符号），不是镜头运镜枚举。

## Prompt 块

### positive（可复用）

Create an image in the Rough Animation Pet Sketch Storyboard style. Warm beige paper, loose red-brown construction lines, scratchy dark burgundy contour strokes, semi-transparent watercolor-like color wash, rough animation storyboard finish, lightly sketched interior background, exaggerated original pet expressions, huge oval eyes, tiny pupils, visible correction strokes, one clear comic prop-driven beat. Stage like an animation story artist frame: one character extreme emotion, another deadpan or suspicious; foreground prop explains the joke; leave sketch marks, motion ticks, crumbs, rough shadows, unfinished room lines visible.

### character_lock

original pet/animal characters only; huge oval eyes with tiny pupils; exaggerated comic expressions; sketchy optional collar/scarf/tag; no franchise characters; keep red-brown construction lines on bodies.

### environment_lock

warm simple interiors (kitchen, sofa corner, hallway, dining table); lightly sketched shelves/frames/cabinets/windows; secondary to characters; warm pale unfinished room lines.

## 负面约束

- watermark / username / platform logo / app UI / QR / creator signature / brand logo
- exact reference or franchise characters
- polished vector art / clean corporate mascot
- 3D render / photorealistic pet photo / airbrushed fur / hyperreal lighting / glossy toy look
- anime cel shading
- dense readable signage / perfect typography
- cold neon palette / dark horror / violence
- flat empty background / overfinished lineart

## Likeness 规则

1. 读起来像动画开发帧，不是精修卡通
2. 红棕结构线在角色和背景上都可见
3. 用一个前景道具解释喜剧情境
4. 一体极端表情 + 一体面瘫/怀疑对比
5. 眼睛巨大简单，情绪一眼可读
6. 半透明暖色填充在更深潦草轮廓之下
7. 线条保持凌乱、分层、可修正、未完成
8. 背景暖、淡、轻描、次要

## 变量（Cookbook bridge）

`SUBJECT`, `SUBJECT_ACTION`, `PRODUCT_OR_PROP`, `LOCATION`, `BACKGROUND_ELEMENTS`, `MAIN_TEXT`, `SECONDARY_TEXT`, `ACCENT_SYMBOL`, `WARDROBE_STYLE`, `ASPECT_RATIO`

## Do / Don't

**Do:** 用变量换内容；保留 style_fidelity_anchors；文字短而可读、通常可空。  
**Don't:** 把参考图当场景照抄；洗成精修矢量或写实宠物照片；冷霓虹、恐怖、暴力调性。

## Defaults（静帧画布）

- resolution: 1920×1080
- preview_label: `720p_still_preview`
- final_label: `1080p_still`

无 motion preset。Schema 明确：`defaults` = still/output canvas only。

## 与镜头层的边界

本文件 / Style Bible schema 描述为：**Visual look lock only. Motion, transitions, and timing belong in shot_list / Bot D — not here.**

景别/运镜/转场请看 [cinematography-filmgraph.md](./cinematography-filmgraph.md) 与总览 [STYLE_AND_SHOT_SUMMARY.md](./STYLE_AND_SHOT_SUMMARY.md)。
