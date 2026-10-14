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

## 使用顺序

1. **Style Lock** → `style_bible.json`（只画风）
2. **Shot Lock** → `shot_list.json`（语义镜头 + 可选 programmatic 覆盖）
3. Bot D 缺省时查 `cinematography_vocab.json` 补齐 Remotion 参数

回到总览：[STYLE_AND_SHOT_SUMMARY.md](./STYLE_AND_SHOT_SUMMARY.md)
