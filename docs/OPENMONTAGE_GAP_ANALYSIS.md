# OpenMontage 对照查漏（Gap Analysis）

来源：[calesthio/OpenMontage](https://github.com/calesthio/OpenMontage)（AGPLv3）。本文只借鉴**思路与字段名**，不复制代码或大段原文。
前提：我们走纯程序化（Remotion / HTML+FFmpeg），不用图生视频，成本优先；当前风格 rough-animation-pet-sketch，Style Lock 未定。

## 1. 它是什么 / 与 A–F 对应

AI 编码助手本身当“制片人”，按 `pipeline_defs/*.yaml`（阶段、产物、审核焦点、成功标准、是否需人工批准）+ `skills/*.md`（每阶段怎么做）推进；每阶段产出 JSON 产物并写 checkpoint；`styles/*.yaml` 是风格手册（playbook）。

| OpenMontage | 我们 |
|---|---|
| executive-producer（编排，预算/修订上限） | 总监 + `DISPATCH_CONVENTIONS.md` |
| styles/ playbook + taste-direction | Bot A：Style Bible |
| research → proposal → script → scene_plan | Bot B：Story Card / shot_list |
| asset 阶段（多用 image/video provider） | Bot C：关键帧 / 程序化素材 |
| edit → compose（Remotion / HyperFrames / FFmpeg） | Bot D |
| reviewer meta-skill + final_review 自检 | Bot E |
| decision_log、taste profile | Bot F（偏好记忆） |
| video-reference-analyst | 暂无（Bot A/F 可吸收） |

## 2. Style Bible 字段对照

我们的 Style Bible 只锁**画风**；动效/节奏/音频在 OM 写进同一 playbook，我们分散在 MOTION_LESSONS 与 guide book 里。

| OM 字段 | 我们 | 状态 | 建议 |
|---|---|---|---|
| identity.name/category/mood/best_for | title / summary / medium | 部分 | 加 `best_for` / `not_for` 一行，方便总监按题材选风格 |
| identity.pace | 无 | 缺 | 放 motion profile（见下），不进画风 Bible |
| visual_language.color_palette (primary/accent/background/text/muted) | palette.primary/accent/background + typography.*_color | 部分 | 补 `muted`；`forbidden` 我们有、OM 没有，保留 |
| composition / texture | composition.* / texture.* / line.* | 有（更细） | 保持 |
| typography headings/body 字体 | typography.title_font/body_font | 部分 | 补 weight、tracking、line_height、scale_system 数字 |
| motion.transitions | shot_list 转场枚举（FilmGraph） | 部分 | 在风格级给“允许转场白名单” |
| motion.animation_style（spring 参数） | MOTION_LESSONS §3 通用数值 | 部分 | 每风格指定弹簧阻尼比/缓动名 |
| pacing_rules（min/max_scene_hold、text_card_hold、transition_duration） | MOTION_LESSONS §3 文字停留公式 | 缺（风格级） | 新增 `motion_profile.pacing` 数字 |
| entrance / exit | MOTION_LESSONS §3 通用 | 部分 | 风格级覆盖 |
| audio（music_volume、sfx_style、ducking_threshold_db） | MOTION_LESSONS §7 声音合同 | 部分 | 风格级 `audio_profile`：sfx 气质 + 音量/闪避数字 |
| asset_generation.image_prompt_prefix / negative | prompt_blocks.positive / negative_constraints | 有 | 保持 |
| consistency_anchors | prompt_blocks.character_lock / likeness_rules / anchor_refs | 有（更强） | 保持 |
| overlays（字卡/标注的底色/圆角/描边） | 无 | 缺 | 02/03/05 类需要时再加 `overlays` |
| quality_rules（对比度、屏上色数、每镜有动元素…） | MOTION_LESSONS 散条 | 部分 | 风格级可机检规则列表 `quality_rules` |
| chart_palette | 无 | 缺 | 03 数据类用；宠物风暂不需要 |
| color_rules（harmony_type、contrast_validation、colorblind_safe） | 无 | 缺 | 加布尔开关，交给代码校验 |
| （无） | locked_at/locked_by、preference_appendix、cookbook_bridge | 我们独有 | 保留，OM 没有锁版本概念 |

结论：画风部分我们更细；缺的是**风格级动效/节奏/音频数字**。建议新建独立的 `motion_profile`（不改现有 Bible 值），与 Style Bible 一对一挂钩。

## 3. 审核门对照

| OM 检查 | 时机 | 我们 | 状态 |
|---|---|---|---|
| slideshow risk 评分（重复版式、装饰性画面、弱运动、缺 shot_intent、字卡过多、空喊“电影感”）≥3 告警 | scene_plan、edit | 无 | **缺**（shot_list 无 `shot_intent`） |
| delivery promise（动态为主时 motion 镜头比例 ≥50%，禁止静默降级成静帧） | edit、compose | 无 | **缺** |
| renderer/runtime governance（渲染器换了必须有决策记录） | edit、compose | Bot D 合同定了路线，无换引擎记录 | 部分 |
| 场景多样性检查 | scene_plan | 无 | 缺 |
| 预算漂移 >30% 判严重 | 每阶段 | 无 | 缺 |
| 每条意见必须指向字段/行号/帧；严重项必须给修法 | 全程 | Bot E 帧号规则 + auto_fix/ask_user | 有 |
| 判定 PASS / REVISE / PASS_WITH_WARNINGS | 全程 | 合格 / 要修 / 重做 + 置信度 | 有 |
| final_review.technical_probe（ffprobe：容器、时长、分辨率、fps、编码） | 渲染后 | 手工 ffprobe | 部分（未成固定脚本） |
| visual_spotcheck（≥4 帧；黑帧、文字不可读、叠层坏、素材缺） | 渲染后 | MOTION_LESSONS §5 联系表 | 部分（无黑帧/可读性自动检） |
| audio_spotcheck（有无音轨、削波、意外静音、混音可懂度） | 渲染后 | §7 LUFS / 真峰值 / 编码后复测 | 部分（缺静音段与削波检测） |
| subtitle_check / transcript 对照 | 渲染后 | 无 | 缺（05 解说类需要） |
| promise_preservation（是否兑现承诺、无偷换引擎） | 渲染后 | 无 | 缺 |
| 无 final_review 不得交付 | 交付 | Final Accept 人工闸 | 部分 |
| （OM 无）拉伸 ±12%/面积 ±10%、滑步、循环接缝、帧确定性 | 渲染后 | MOTION_LESSONS §1/§10 | 我们独有 |

## 4. Checkpoint / 决策日志 / 成本

| OM | 我们 | 状态 |
|---|---|---|
| checkpoint JSON：stage、status(completed/failed/awaiting_human/in_progress)、artifacts、时间戳，可断点续跑 | `projects/<id>/` 目录约定 + 4 个人工闸 | 部分（无机器可读状态） |
| decision_log：decision_id、stage、category（runtime/渲染器/风格/降级/预算…）、options_considered、selected、reason、confidence、user_visible | DISPATCH_CONVENTIONS 置信度路由 | 缺（无持久日志） |
| “只考虑一个选项”“全部置信度 1.0”判为可疑 | 无 | 缺 |
| cost_log：estimated/reserved/actual、status、预算总额 | 无 | 缺（纯程序化花费主要是模型 token + 渲染时长，也应记） |
| 每阶段 max_revisions / max_send_backs / max_wall_time | MOTION_LESSONS “2–4 轮修正” | 部分 |
| render_report（时长、分辨率、fps、渲染耗时、slideshow 分） | 无 | 缺 |

## 5. 参考视频优先流程（Bot A/F）

OM 流程：拆参考片 → 能力核对（哪些我们做不到）→ 关键提问 → 2–3 个方案 → **先做 10–15 s 样片并报成本** → 再进正式流水线。拆片按 5 维度逐镜输出：主体、主体动作、场景（叠层单列）、空间构图、镜头；不适用必须写 N/A，不可省略。

对我们：
- Bot A：参考片 → 5 维度表 → 映射到 Style Bible 字段 + `motion_profile` 数字 + FilmGraph 枚举。
- 能力核对要写“纯程序化做不到/代价高”的项（如写实毛发、真实皮肤拉伸）。
- 样片门 = 我们的 Sample Frame Lock，升级为“10–15 s 动态样片”。
- Bot F：用户对样片的取舍写进 decision_log（user_visible），蒸馏进 taste_profile。

## 6. 流水线对照（OM 13 条 vs 我们 01–10）

| OM pipeline | 我们 guide | 备注 |
|---|---|---|
| animated-explainer | 05 explainer-narrated、03 data | 加拆题卡 + slideshow 风险 |
| animation | 01 logo、02 kinetic、07 loop、08 beat | 预算 $2、修订 3 次的上限思路可借 |
| character-animation（rig_plan / pose_library / action_timeline / character_qa_report） | 06 character-short | **最值得细看**：我们有骨架，缺 pose_library 与角色 QA 报告 |
| screen-demo | 04 ui-product-demo | — |
| documentary-montage、hybrid、cinematic | 10 live-footage-assist | 依赖素材/生成视频，仅借结构 |
| talking-head、avatar-spokesperson、podcast-repurpose、clip-factory、localization-dub | 无 | 非我们方向，跳过 |
| （无） | 09 map-geo | 我们独有 |

## 7. 待办（按优先级）

> 2026-10-15：P0 全部与 P1 全部已实现（✅），见 `tools/`、`schemas/`、`config/dispatch_questions.yaml`。P2 未动（P2-1 等 Style Lock）。

**P0**
- ✅ P0-1 在 shot_list 增加 `shot_intent`（这一镜为何存在）与 `information_role` 字段 → `schemas/shot_list.schema.json`
- ✅ P0-2 新建渲染后自检脚本：ffprobe 参数、≥4 帧抽帧联系表、黑帧、静音段、削波、编码后真峰值，输出 final_review JSON → `tools/final_review.py` + `schemas/final_review.schema.json`
- ✅ P0-3 新建决策日志 schema（options_considered / selected / reason / confidence / user_visible），总监每个关键选择必须记一条 → `schemas/decision_log.schema.json` + `docs/DISPATCH_CONVENTIONS.md`
- ✅ P0-4 Bot E 交付规则：无 final_review 或 status≠pass 不得进入 Final Accept → `docs/DISPATCH_CONVENTIONS.md`

**P1**
- ✅ P1-1 风格级动效/节奏/音频数字（pacing hold、转场时长、弹簧、入出场、sfx 气质、ducking）作为独立文件，不改 Bible 值 → `styles/<slug>/motion_profile.json` + `schemas/motion_profile.schema.json`
- ✅ P1-2 slideshow 风险评分（重复版式、无意图镜头、字卡占比、弱运动）在 Shot Lock 前跑 → `tools/slideshow_risk.py` + `docs/video-guides/README.md`
- ✅ P1-3 delivery promise：Story Card 写明“动态为主/静帧为主”与最低运动镜头比例，自检核对 → `framework-v1.md` §2.3 + final_review
- ✅ P1-4 checkpoint JSON（stage/status/artifacts/时间戳）支持断点续跑 → `schemas/checkpoint.schema.json` + `projects/<id>/checkpoints/`
- ✅ P1-5 参考视频 5 维度拆片模板 + 10–15 s 动态样片门 → `docs/REFERENCE_VIDEO_INTAKE.md`
- ✅ P1-6 成本日志（模型 token、渲染分钟、估算/实际），每阶段修订上限与预算漂移 >30% 告警 → `schemas/cost_log.schema.json`

**P2**
- P2-1 Style Bible 补 `best_for/not_for`、`palette.muted`、字体字重数字、`color_rules` 开关（需 Style Lock 时一并确认）→ `schemas/style_bible.schema.json`
- P2-2 character 管线：pose_library、角色 QA 报告 → `docs/video-guides/06-character-short.md`
- P2-3 overlays / chart_palette（02/03/05 用）→ `motion_profile` 或 guide 03
- P2-4 字幕/转写对照检查（05 解说类）→ `tools/final_review.py`
- P2-5 工具选择加权打分思路（task_fit、quality、control、reliability、cost_efficiency、latency、continuity）用于选渲染路线/TTS → `bot-d-tech-route.md`

## 8. 不借鉴的

- 图生视频 / 文生图 provider（Kling、Veo、FLUX、HeyGen 等）及其选择器：与纯程序化 + 成本优先冲突。
- 数字人、口播、播客切条、本地化配音管线：非我们方向。
- 任何 OM 代码（`lib/*.py`、tools、Remotion 组件）：AGPLv3，只借字段名与流程思路，自写实现。
- 其 5 套通用风格的具体配色/字体值：与手绘宠物风无关。
- “atelier 默认、禁止 stock 场景类型”的强治理：我们目前单人小流水线，先不引入。
