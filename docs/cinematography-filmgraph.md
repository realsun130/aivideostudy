# 镜头词表深摘要：FilmGraph → Shot List / Bot D

> 权威源：[`schemas/cinematography_vocab.json`](../schemas/cinematography_vocab.json)  
> 合约：[`schemas/shot_list.schema.json`](../schemas/shot_list.schema.json)  
> 上游：[FilmGraph](https://github.com/gokaykucuk/filmgraph)（MIT）  
> 词表 note：Controlled vocabularies adapted for shot_list. **Style/look stays in style_bible.**

本文件只谈**怎么拍、怎么接、程序怎么执行**；色板/线稿/角色长相不在这里。

## Shot List 合约要点

每个 shot 至少需要：`shot_id`, `duration_sec`, `cinematography`（含 `shot_size` + `camera_movement`）, `transition_to_next`, `frames.hero`。

可选：`shot_type`, `camera_angle`, `programmatic_motion`, `transition_programmatic`, `transition_sec`, dialogue/subtitle/audio 等。

`style_bible_ver` 在整表级锁定：镜头表写在哪一版 Style Bible 之上。

## 景别 `shot_size`

| 枚举 | 中文 | 简释 |
|------|------|------|
| ECU | Extreme Close-Up 大特写 | 眼睛、毛发、局部细节 |
| BCU | Big Close-Up 大近景 | 脸部极近，几乎填满 |
| CU | Close-Up 特写 | 脸或手等局部 |
| MCU | Medium Close-Up 中近景 | 胸口以上 |
| MS | Medium Shot 中景 | 约膝盖以上 |
| MLS | Medium Long Shot 中全景 | 膝下到全身之间 |
| MWS | Medium Wide Shot 中远景 | 人完整且环境较多 |
| WS | Wide Shot 全景 | 整个人/物都在画面里 |
| EWS | Extreme Wide Shot 大远景 | 人很小，主要看环境 |
| INSERT | 插入镜头 | 物件/细节特写插入叙事 |
| AERIAL | 航拍 | 高空俯视 |
| OTHER | 其他 | 自定义；在 notes 说明 |

第一帧拿不准时常用 **MS** 或 **MCU**。

## 镜头类型 `shot_type`

| 枚举 | 中文 | 简释 |
|------|------|------|
| single | 单人镜 | 一个主体 |
| two-shot | 双人镜 | 两人同框 |
| group | 群戏 | 多人 |
| over-the-shoulder | 过肩 | 从一人肩后看另一人 |
| point-of-view | 主观 | 角色视角 |
| reaction | 反应镜 | 表情/反应为主 |
| establishing | 建立镜头 | 交代环境 |
| insert | 插入 | 物件细节 |
| cutaway | 切出 | 切到相关旁物 |
| master | 主镜头 | 整场覆盖 |
| other | 其他 | — |

## 机位角度 `camera_angle`

| 枚举 | 中文 | 简释 |
|------|------|------|
| eye-level | 平视 | 与眼睛同高 |
| high-angle | 俯拍 | 机位高于主体 |
| low-angle | 仰拍 | 机位低于主体 |
| birds-eye | 鸟瞰 | 正上向下 |
| worms-eye | 虫视 | 极低仰视 |
| dutch-angle | 荷兰角 | 画面倾斜 |
| overhead | 顶视 | 正上方 |
| ground-level | 地面高度 | 贴近地面 |
| other | 其他 | — |

## 运镜 `camera_movement`（语义意图）

写在 shot list 里的是**导演意图**；Bot D 再映射到 Remotion 预设。

| 枚举 | 中文 | 简释 |
|------|------|------|
| static | 固定 | 机位不动 |
| pan | 摇镜 | 水平转动镜头 |
| tilt | 俯仰 | 垂直转动镜头 |
| dolly | 推轨 | 机位前后移动 |
| truck | 横移 | 机位左右平移 |
| tracking | 跟踪 | 跟随主体 |
| handheld | 手持 | 轻微晃动 |
| crane | 摇臂 | 升降大动作 |
| drone | 无人机 | 空中移动 |
| zoom | 变焦 | 焦距变化（机位可不动） |
| whip-pan | 甩镜 | 快速水平甩 |
| push-in | 推进 | 逼近主体 |
| pull-out | 拉出 | 远离主体 |
| arc | 弧移 | 绕主体圆弧 |
| rack-focus | 跟焦切换 | 焦点在前后景间切换 |
| steadicam | 稳定器 | 平滑跟拍 |
| other | 其他 | — |

## 转场 `transition_to_next`

| 枚举 | 中文 | 简释 |
|------|------|------|
| cut | 硬切 | 直接切 |
| dissolve | 叠化 | 交叉淡入淡出 |
| fade-in | 淡入 | 从黑/空淡入 |
| fade-out | 淡出 | 淡出离开 |
| fade-to-black | 淡出到黑 | 收束 |
| wipe | 擦除 | 一边推开露出下一镜 |
| match-cut | 匹配剪 | 形状/动作匹配 |
| jump-cut | 跳切 | 同机位时间跳 |
| j-cut | J切 | 下一镜声音先入 |
| l-cut | L切 | 本镜声音拖入下一镜画面 |
| smash-cut | 猛切 | 情绪/场景突然硬切 |
| other | 其他 | — |

## 程序化运动预设 `programmatic_motion.preset`

Bot D Remotion 可执行层（与语义运镜分离）：

`static`, `kenburns_in`, `kenburns_out`, `pan_left`, `pan_right`, `parallax`, `punch_in`, `subtitle_card`

若 shot 省略 `programmatic_motion`，用词表默认映射：

| camera_movement | → preset |
|-----------------|----------|
| static | static |
| push-in | kenburns_in |
| pull-out | kenburns_out |
| zoom | kenburns_in |
| dolly | kenburns_in |
| pan | pan_left |
| tilt | kenburns_in |
| truck | pan_left |
| tracking | pan_left |
| whip-pan | punch_in |
| arc | parallax |
| crane | kenburns_out |
| drone | kenburns_out |
| handheld | static |
| steadicam | kenburns_in |
| rack-focus | static |
| other | static |

## 程序化转场 `transition_programmatic`

可执行值：`cut`, `xfade`, `fade_black`

默认映射：

| transition_to_next | → programmatic |
|--------------------|-----------------|
| cut, match-cut, jump-cut, j-cut, l-cut, smash-cut, other | cut |
| dissolve, wipe | xfade |
| fade-in, fade-out, fade-to-black | fade_black |

## 2.5D 视差镜头与转场合同（⚠️ 待测试）

> 来源：[Leonxlnx/shanshui](https://github.com/Leonxlnx/shanshui)（MIT）`docs/ENGINE.md`、`docs/FILM.md`、`docs/STYLE.md`。原片 1920×1080 / 60 fps；下面的数字已换算到我们的 **9:16 1080×1920**（短边同为 1080，水平量照抄；竖向量按画面高度比 ×1.78 放大，标「起始值，需调」的为换算值）。与引擎无关：Remotion、PIL/numpy 逐帧渲染都适用。

### 1. 分层卡片 + 一台相机
- 每个画面 = 一叠「卡片」，从后往前排，每张有深度 `z`：`z=1` 是画面平面（最近的前景），`z=2–4` 中景，`z=6–15` 远景，天空/纸底 `z=1e5`（永不动）。
- 一台相机 `{x, y, dolly, zoom, roll}`。卡片上静止点 P 的屏幕位置：`screen = C + ((P − C)·z − [x, y]) / (z − dolly) · zoom`，再绕画面中心 C 旋转 `roll`。
  - 平移：`z=1` 卡片移动 `−x` px，`z=4` 只移动 `−x/4` → 视差自动成立，不用给每层单独写动画。
  - `dolly` 往前推：`z=1` 卡片放大 `1/(1−dolly)`，远景几乎不变。`z=1` 卡片 dolly < 0.5；每镜自身 dolly ≤ 0.08。
  - `zoom` 是变焦：所有层等比放大，没有视差。想要纵深感用 dolly，不用 zoom。
- 镜头速度：画面平面上 8–35 px/s（慢推、横移）；镜头曲线最软（ML §3）。
- 每张卡片「静止时放在哪就看到哪」：先按镜头静止时构图，再加镜头运动。

### 2. 出血（overscan）合同
- 规则：**任何时刻都不能露出卡片边缘**。每张卡片在画框外多画的像素 ≥ `|该方向相机最大偏移| / z` + 余量。
- 余量：近景卡片默认在它接触的每条画框边外多出 8–15%：左右 86–162 px，上下 154–288 px（9:16 换算）。
- 转场会把相机推出画框，要在镜头表里写清「哪一镜、哪一边、多画多少」。参考值（`z=1` 卡片，起始值，需调）：
  | 转场 | 相机偏移 | `z=1` 需多画 | `z=4` 需多画 |
  |---|---|---|---|
  | 竖向升镜（穿云上升） | y 到 ±460 px | 对应一侧 ~530 px | ~130 px |
  | 横向卷轴平移 | x 到 ±125 px | 对应一侧 ~150 px | ~40 px |
  | 拉远（负 dolly） | dolly 到 −0.1 | 四周各 `(−dolly)/2` 画框 ≈ 5%：左右 ~55 px、上下 ~100 px | 很小 |
  | 推进（正 dolly） | dolly 到 0.3 | 不需要出血，但要提高烘焙密度（见下条） | — |
- 推进镜头里的近景卡片要多烘焙像素密度：放大 1.25–1.5 倍再烘焙，避免推近发糊。
- **可见窗口**：一镜的本地时间 `t=0` 从它的入场转场开始算。它在 `t ∈ [−入场时长, 镜长 + 出场时长]` 内都可能被看到（运动模糊还要再往前多留几帧），整个窗口里必须连续在动、构图成立、不露边。shanshui 约定每镜在 t ∈ [−3, 14] s 内都可渲染，主构图在 t = 2–4 s 最接近参考图。
- 检查：渲染每个转场的首帧、中帧、末帧，用联系表看四边；再跑 `tools/forensics.py`（ML §5）。

### 3. 有动机的转场（由画面里的东西带出来）
- 不用默认淡入淡出；转场由场景里本来就有的元素完成，和我们「镜头交接光点」是同一个思路。shanshui 的 10 种：
  | 转场 | 怎么做 | 时长 |
  |---|---|---|
  | 墨晕开场 | 从白纸长出画面，最深的墨先出现，从种子点向外湿润晕开 | 3.0 s |
  | 雾幕 | 上一镜的河雾升起，变成下一镜瀑布的水雾 | 1.8 s |
  | 穿云上升 | 相机升过云层，到云海之上 | 2.0 s |
  | 穿过水雾 | 推进上一镜瀑布，从下一镜瀑布里出来 | 1.6 s |
  | 风卷落叶 | 一阵落叶横扫带过接缝 | 1.6–2.0 s |
  | 卷轴平移 | 画卷继续向右展开 | 2.2 s |
  | 日轮匹配 | 金色太阳滑到下一镜红日的位置 | 2.0 s |
  | 暮色晕染 | 墨从湿天空往下渗，入夜 | 2.2 s |
  | 雪幕 | 雪越下越密，盖过月湖 | 2.2 s |
  | 蒸发收尾 | 浅墨先蒸发、最深的墨最后消失，回到白纸，只留印章 | 1.8 s |
- 匹配类转场（日轮、穿雾、光点）要在镜头表里写出两镜的锚点坐标，渲染后报告实际位置。

### 4. 单一时钟：BPM 管画面和声音
- 画面和声音共用一个时钟文件（BPM、FPS、bar/beat 换算、每镜 start、命名提示点 CUE）。音乐脚本和渲染脚本都从这里读，不各写一份时间。
- shanshui：80 BPM，一拍 0.75 s，一小节 3 s；每幅画占 2 小节；**每个转场以小节线为中心**：`start = 小节线 − 转场时长/2`。
- 换算到 24 fps：80 BPM 一拍 18 帧、一小节 72 帧；每拍帧号从时间算再取整，不累加取整值（ML §3）。
- 声音的关键事件（风声、盖印）作为命名 CUE 写在同一文件里，画面事件和音效都引用 CUE 名。

### 5. 子帧运动模糊
- 每个输出帧在快门时间内取 N 个子帧平均：`ts = T + ((i + 0.5)/N − 0.5) · (快门/fps)`，快门 0.5 帧。
- 迭代期 N=1；成片 N=2（shanshui 默认出片值）；慢速漂移镜头 N=2–4 足够；甩镜、快速推进按 ML §9 用 16 次、快门 0.45。
- 子帧会往 T 之前取样，所以每镜开头要多留一点可渲染时间（见可见窗口）。

### 6. 静态层先烘焙 + 质感处理
- 不动的笔触（山石、树干、建筑）只画一次，烘焙成纹理卡片；每帧只合成和移动卡片。会动的（雾、水、雪、鸟、落叶）每帧按 t 纯函数绘制，卡片范围尽量小。
- 烘焙后统一过一遍质感处理，去掉电脑矢量感：边缘颜料淤积（wet edge）、颗粒渗进纸纹（granulation）、轻微晕开（bleed）。shanshui 默认值 edge 0.45 / granulation 0.22 / bleed 1.2 px；建筑类更轻：0.25 / 0.12 / 0.7。
- 全局后期每帧都做：静态纸纹（屏幕空间）、调色、暗角、TPDF 抖色（防柔和雾气渐变出色带）。
- 预算（参考值）：每镜烘焙 < 4 s，单帧合成 < 40 ms；全屏程序化层 ≤ 6 层，每镜卡片 ≤ 30 张，单张宽 ≤ 4000 px，超出要写理由。

## 使用顺序

1. **Style Lock** → `style_bible.json`（只画风）
2. **Shot Lock** → `shot_list.json`（语义镜头 + 可选 programmatic 覆盖）
3. Bot D 缺省时查 `cinematography_vocab.json` 补齐 Remotion 参数

回到总览：[STYLE_AND_SHOT_SUMMARY.md](./STYLE_AND_SHOT_SUMMARY.md)
