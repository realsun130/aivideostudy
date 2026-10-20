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

## Style Bible 编写指南：从参考图实测（⚠️ 待测试）

> 来源：[Leonxlnx/shanshui](https://github.com/Leonxlnx/shanshui)（MIT）`docs/STYLE.md` 的写法。目标：静帧放在参考图旁边，看起来像同一个画师画的。所有外观数字从参考图**量出来**，不凭感觉写形容词。可选字段已加进 schema（不影响现有文件校验）：外观数字写 `style_bible.json` 的 `measured_reference`；运动数字写 `motion_profile.json` 的 `element_motion`（Style Bible 不管运动，见上面分离原则）。

### 1. 实测色板（sRGB 0–255）
对每张参考图量，再写区间：
| 项 | 怎么量 | shanshui 实测（示例） |
|---|---|---|
| 纸色 / 底色 `paper_rgb` | 亮度最高 8% 像素的平均 RGB | 239, 231, 220 |
| 墨色 / 最深色 `ink_rgb` | 亮度最低 1% 像素的平均 RGB | 8–13, 7–11, 4–8（偏暖的黑） |
| 亮度分位 `luminance_percentiles` | 灰度 p10 / 中位 / p90 | p10 66–118，中位 180–219，p90 224–235（画面以亮为主） |
| 强调色 `accents` | 按色相范围数像素，写平均 RGB 和占画面百分比上限 | 朱红 < 2% 像素（最多的两张 1.3–1.6%） |
- 分场景变体（夜景偏冷、雪景偏灰、黄昏偏金）单列一行，不混进主色板。
- 量法示例（Python）：`g = 0.299R+0.587G+0.114B`；`paper = rgb[g >= 分位92].mean(0)`；`ink = rgb[g <= 分位1].mean(0)`；`np.percentile(g, [10, 50, 90])`。
- 渲染后用同一段代码量自己的静帧，和参考值并排写进审核记录；不在区间内就调，直到读数一致（同 ML §8 的 CHECKS 做法）。

### 2. 按景深的明度阶梯 `value_ladder`
- 写成数字：tone 0 = 最深色，1 = 纸色。shanshui：近景真黑（rgb ≈ 10）且细节最锐；中景顶部 tone 0.35–0.55；远景 tone 0.65–0.85，几乎没有内部细节。
- 对比度和边缘锐度随距离一起下降；每层之间用「纸色的雾」隔开，山体底部化进白里。
- 与 2.5D 分层（[cinematography-filmgraph.md](./cinematography-filmgraph.md)「2.5D 视差镜头」）一一对应：每个 `z` 区间对应阶梯的一档。

### 3. 「看起来假」清单 `fake_tells`
每个风格必须单列一张，审核时逐条对照。shanshui 的清单：
- 边缘完全干净、没有纸纹的矢量渐变或形状。
- 规律重复：一排一样的树、等距的山峰、对称的形状。
- 处处中灰：参考图既有真黑，也有大片留白。
- 高饱和色、辉光/泛光、镜头光效、所有东西都描边。
- 没有笔触逻辑的噪声（读不出是笔触、石头还是树叶的 fbm 斑块）。
本项目的风格按同样格式写自己的条目（例如万圣节片：发光只能来自真实光源）。

### 4. 运动参数写成 px/s 和 Hz `element_motion`
- 环境元素一律写速度（px/s）、频率（Hz）、幅度（px），不写「缓缓飘动」。shanshui「会呼吸的画」参数（原片 1920×1080；9:16 短边同为 1080，水平速度照抄，竖向行程可按画面高度放大）：
  | 元素 | 参数 |
  |---|---|
  | 雾 | 漂移 5–25 px/s，形状随时间变（3D 噪声），随深度视差 |
  | 松 / 竹 | 枝梢摆幅 1–5 px，0.15–0.35 Hz，外加细微抖动；竹叶略活泼 |
  | 水面 | 倒影波动幅度 1.5–4 px，水纹慢漂，高光闪烁 |
  | 瀑布 | 水纹下落 150–400 px/s（按大小和距离缩放），底部水雾翻涌 |
  | 鹤 / 鸟 | 扇翅 0.8–1.1 Hz，滑翔弧线，轻微起伏，横穿 40–90 px/s |
  | 落叶 | 40–110 px/s，带翻转摆动；雪 20–60 px/s，带横向漂移 |
  | 相机 | 画面平面 8–35 px/s，每镜 dolly ≤ 0.08 |
- 原则：一切慢慢呼吸，任何东西都不抖。

### 5. 逐区域对比参考图 `comparison`
- 每张参考图写一份「元素坐标表」：主要元素在设计坐标里的位置范围（如「松树 x 0–850, y 20–380」），按它搭构图。
- 对比方式四种，都按固定 t 渲染静帧：
  - `side`：参考图 | 渲染，左右并排；
  - `compare`：参考在上、渲染在下；
  - `crop`：同一区域（设计坐标）放大并排，按 1:1 比——画面质感的胜负在这里；
  - `sheet`：同一镜多个时间点的联系表（如 t = 0, 2, 4, 6, 8）。
- 输出图宽 640 px 足够看（省审核成本）；一块一块追参考，每轮只改一块。参考图只用于对比，不进成片（授权见各项目 CREDITS）。

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
