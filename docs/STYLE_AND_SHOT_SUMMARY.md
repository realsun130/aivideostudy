# 风格 + 镜头：两部分总览

> 本页是人读摘要。权威数据在 JSON；改锁定物请改源文件并升版，不要只改本文。

## 分离原则

| 锁定物 | 管什么 | 不管什么 |
|--------|--------|----------|
| **Style Bible** | 画风外观：媒介、色板、线稿、光影、材质、静帧构图、prompt、负面约束 | 运镜、转场、时长、剪辑节奏 |
| **Shot List / FilmGraph** | 景别、镜头类型、机位角度、运镜意图、转场、时长；可选 Remotion `programmatic_motion` | 色板、线条、角色长相、禁止色 |

一句话：**Style Bible = 长什么样；Shot List = 怎么拍、怎么接。**

第一帧出图：只吃 Style Bible + 你填的画面变量（谁/在哪/干什么/景别等静帧信息）。运镜留给后面 Shot List / Bot D。

---

## 当前锁定风格

**slug:** `rough-animation-pet-sketch-storyboard-style`  
**版本:** `2026-10-13.2`  
**标题:** Rough Animation Pet Sketch Storyboard  
**媒介:** `2d_illustration`（动画开发草图 / storyboard 完成度，不是精修矢量）

### 一句话

松散动画分镜素描风：暖米色纸、红棕结构线、暗红褐潦草轮廓、半透明水色填充、夸张宠物表情与简单室内道具驱动的喜剧节拍。

### 色板（摘要）

| 角色 | 名称 | Hex |
|------|------|-----|
| 主色 / 纸底 | warm_beige | `#E8DCC8` |
| 主色 | cream | `#F5EDE0` |
| 主色 | pale_peach | `#F0D5C4` |
| 主色 | soft_tan | `#D4B896` |
| 结构线 | red_brown_pencil | `#8B4513` |
| 轮廓墨 | dark_burgundy_ink | `#4A1525` |
| 深褐 | nearly_black_brown | `#2B1A14` |
| 点缀 | muted_gray_blue / peach_blush / orange_food / warm_ochre | 见源文件 |
| **禁止主导** | cold_neon / gloss_plastic | `#00FFCC` / `#FF69B4` |

### 线 / 光 / 质感

- **线:** `variable` + `sketchy`；红棕结构线可见；暗红褐轮廓多层叠压；允许修正笔触
- **光:** `soft_diffused` 暖室内漫射；忌电影硬光、超写实毛发高光
- **质感:** medium grain + 纸感 + 半透明水色；保留粗糙阴影与动势记号

### 角色与画面规则（likeness）

- 读起来像动画开发帧，不是精修卡通
- 原创宠物/动物；巨大椭圆眼睛 + 小瞳孔；夸张表情
- 一体极端情绪 + 一体面瘫/怀疑对比
- 用一个前景道具解释喜剧情境
- 背景暖、淡、轻描、次要
- 无 franchise 角色；忌水印 / App UI / 完美排版 / 冷霓虹 / 3D / 写实照片

更深摘要 → [style-bible-rough-pet-sketch.md](./style-bible-rough-pet-sketch.md)  
源文件 → [styles/rough-animation-pet-sketch-storyboard-style/style_bible.json](../styles/rough-animation-pet-sketch-storyboard-style/style_bible.json)

---

## 镜头词表概要（FilmGraph）

词表来源：[FilmGraph](https://github.com/gokaykucuk/filmgraph)（MIT），落在本仓 `schemas/cinematography_vocab.json`，并写入 `shot_list.schema.json` 枚举。

### 景别 `shot_size`

| 枚举 | 中文 | 简释 |
|------|------|------|
| ECU | 大特写 | 眼睛/细节局部 |
| BCU | 大近景 | 脸部极近 |
| CU | 特写 | 脸或手等局部 |
| MCU | 中近景 | 胸口以上 |
| MS | 中景 | 约膝盖以上 |
| MLS | 中全景 | 膝下到全身之间 |
| MWS | 中远景 | 人完整且环境较多 |
| WS | 全景 | 整个人/物都在画面里 |
| EWS | 大远景 | 人很小，主要看环境 |
| INSERT | 插入镜头 | 物件/细节特写插入 |
| AERIAL | 航拍 | 高空俯视 |
| OTHER | 其他 | 自定义 |

### 机位角度 `camera_angle`

| 枚举 | 中文 | 简释 |
|------|------|------|
| eye-level | 平视 | 与眼睛同高 |
| high-angle | 俯拍 | 机位高于主体 |
| low-angle | 仰拍 | 机位低于主体 |
| birds-eye | 鸟瞰 | 正上向下看 |
| worms-eye | 虫视 | 极低仰视 |
| dutch-angle | 荷兰角 | 画面倾斜 |
| overhead | 顶视 | 正上方 |
| ground-level | 地面高度 | 贴近地面 |
| other | 其他 | — |

### 运镜 `camera_movement`（语义意图）

| 枚举 | 中文 | 简释 |
|------|------|------|
| static | 固定 | 机位不动 |
| pan | 摇镜 | 水平转动 |
| tilt | 俯仰 | 垂直转动 |
| dolly | 推轨 | 前后移动机位 |
| truck | 横移 | 左右平移机位 |
| tracking | 跟踪 | 跟随主体移动 |
| handheld | 手持 | 轻微晃动感 |
| crane | 摇臂 | 升降大弧线 |
| drone | 无人机 | 空中移动 |
| zoom | 变焦 | 镜头焦距变化 |
| whip-pan | 甩镜 | 快速水平甩 |
| push-in | 推进 | 逼近主体 |
| pull-out | 拉出 | 远离主体 |
| arc | 弧移 | 绕主体圆弧 |
| rack-focus | 跟焦切换 | 焦点在前后景间切换 |
| steadicam | 稳定器 | 平滑跟拍 |
| other | 其他 | — |

### 转场 `transition`

| 枚举 | 中文 | 简释 |
|------|------|------|
| cut | 硬切 | 直接切下一镜 |
| dissolve | 叠化 | 两镜交叉淡入淡出 |
| fade-in / fade-out | 淡入 / 淡出 | 从黑/到透明等 |
| fade-to-black | 淡出到黑 | 收束 |
| wipe | 擦除 | 一边推开露出下一镜 |
| match-cut | 匹配剪 | 形状/动作匹配衔接 |
| jump-cut | 跳切 | 同机位时间跳跃 |
| j-cut / l-cut | J切 / L切 | 声画交错切入 |
| smash-cut | 猛切 | 情绪/场景突然硬切 |
| other | 其他 | — |

### Bot D 程序化默认（摘要）

语义运镜 → Remotion 预设的默认映射在词表里，例如：

- `static` → `static`
- `push-in` / `zoom` / `dolly` → `kenburns_in`
- `pull-out` → `kenburns_out`
- `pan` / `truck` / `tracking` → `pan_left`
- `whip-pan` → `punch_in`
- `arc` → `parallax`

转场默认：`cut`/`jump-cut`/… → `cut`；`dissolve`/`wipe` → `xfade`；`fade-*` → `fade_black`。

更深摘要 → [cinematography-filmgraph.md](./cinematography-filmgraph.md)  
源文件 → [schemas/cinematography_vocab.json](../schemas/cinematography_vocab.json) · [schemas/shot_list.schema.json](../schemas/shot_list.schema.json)

---

## 文件索引

| 用途 | 路径 |
|------|------|
| 本总览 | [docs/STYLE_AND_SHOT_SUMMARY.md](./STYLE_AND_SHOT_SUMMARY.md) |
| 风格深摘要 | [docs/style-bible-rough-pet-sketch.md](./style-bible-rough-pet-sketch.md) |
| 镜头词表深摘要 | [docs/cinematography-filmgraph.md](./cinematography-filmgraph.md) |
| Style Bible 源 | [styles/rough-animation-pet-sketch-storyboard-style/style_bible.json](../styles/rough-animation-pet-sketch-storyboard-style/style_bible.json) |
| Style Bible schema | [schemas/style_bible.schema.json](../schemas/style_bible.schema.json) |
| Shot List schema | [schemas/shot_list.schema.json](../schemas/shot_list.schema.json) |
| FilmGraph 词表 | [schemas/cinematography_vocab.json](../schemas/cinematography_vocab.json) |
| Schema 分离说明 | [schemas/README.md](../schemas/README.md) |

## 确认

- Style Bible **不含**运镜 / 转场 / 时长字段；`composition` 只描述静帧取景与图层堆叠。
- 运动与剪辑只出现在 Shot List / `cinematography_vocab.json` / Bot D 执行层。
