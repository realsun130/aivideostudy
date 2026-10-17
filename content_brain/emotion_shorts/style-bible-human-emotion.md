# Style Bible：人类情感短片（Human Emotion Shorts）⚠️ 待测试

> 纯画风约定。无运镜清单、无分镜时长。叙事语法见同目录 `STYLE_BIBLE.md`；流水线挂载见 `docs/EMOTION_TO_PIPELINE_BRIDGE.md`。  
> **与** `docs/style-bible-rough-pet-sketch.md` **并列，不混用。**

## 元数据

| 字段 | 值 |
|------|-----|
| style_id | `human-emotion-flat-illustration` |
| version | `2026-10-17.1` |
| medium | `2d_illustration` |
| audience | 22–35 城市生活共鸣；竖屏优先 |
| locked_by | `pending_user_style_lock` |

**summary：** 克制的平面插画：少线、干净色块、大胆留白；情绪靠手/道具/环境声，不靠夸张表情口型；室内日常光，禁止网感滤镜和炫光。

## 色板

### Primary（生活底）
| name | hex | role |
|------|-----|------|
| paper_warm | `#F3EEE6` | bg |
| wall_grey | `#E4E0D8` | bg secondary |
| skin_light | `#E8C4B0` | character |
| cloth_ink | `#2C333A` | character |

### Accent（情绪，每片只用 1 个主强调色）
| name | hex | role |
|------|-----|------|
| soft_amber | `#E6A756` | 私密/温暖瞬间 |
| night_blue | `#3D5A73` | 夜、屏幕、疏离 |
| mute_rose | `#C9898F` | 尴尬/心软 |
| system_grey | `#8B939C` | UI、表格、规则 |

### Forbidden
| name | hex | note |
|------|-----|------|
| neon_cyan | `#00E5FF` | 禁止 |
| influencer_pink | `#FF4DA6` | 禁止 |
| hdr_gold | `#FFD700` | 禁止炫光金 |

## 线 / 光 / 质感

| 块 | 约定 |
|----|------|
| line | 均匀细线或色块无轮廓；**不要**宠物风的多层潦草修正线 |
| lighting | 室内窗光/灯下漫射；屏幕允许一块冷色溢光，面积受控 |
| texture | 轻微纸噪即可；禁止厚重水彩晕染抢戏（那是 urban-sketch 另一路） |
| faces | 简化五官；微表情用眉眼点位，不靠泪和水光特写煽情 |
| hands | **优先表现层**：握、撤、挪、删、贴，手可占画面 30%+ |
| props | 每片 1 个核心道具反复出现；道具比脸重要 |
| typography | UI/聊天气泡可读；禁止片尾人生道理大字；字号竖屏 ≥ 画面高约 3% |
| camera_feel | 固定机位为主；推拉极慢；忌手持晃和甩镜 |

## 静帧构图

- 9:16 默认安全区：主体避开顶部 12% / 底部 18%（留给平台 UI）。
- 允许大留白；主体可以偏小，但**动作必须可读**。
- 双人关系优先用距离/朝向，不用对视特写堆情绪。
- 禁止：表情包式大脸、漂浮 emoji、闪光粒子代表“治愈”。

## 动画实现偏好（对接 Bot D）

- 优先：静帧切换、手部 3–4 关键姿态、道具位移、灯光/色温插值、UI 气泡。
- 避免：复杂步态、口型同步、多人物群演、长镜头全身表演。
- 声音：环境声 + 拟音为主；音乐可选，无音乐时故事须仍成立。

## 与宠物 Style Bible 的边界

| | 人类情感 | 宠物素描 |
|--|----------|----------|
| 线 | 干净克制 | 潦草多层 |
| 表情 | 极简 | 夸张喜剧 |
| 主角载体 | 手+道具 | 宠物肢体 |
| 色彩 | 每片一强调色 | 暖米色纸+红棕线 |

## Style Lock

未锁定。选定第一支人类情感成片前，人工确认本 bible；确认后改 `locked_by` 并打待测试撤销条件。
