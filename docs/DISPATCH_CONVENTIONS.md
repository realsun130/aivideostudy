# 调度约定：扇出提问 + 置信度路由

> 适用于导演（调度）与 Bot E（审美审片）等所有“让模型做判断”的环节。思路来自一篇结构化决策模型的用法文章，已泛化，**不绑定任何具体产品**。动效相关任务仍先读 [`MOTION_LESSONS.md`](MOTION_LESSONS.md)。

## 0. 三条总原则
1. **一份状态，一次调用，扇出所有问题。** 可能用到的题（包括“万一不合格才需要的严重度”）全塞进同一次调用，答案回来后由**代码**决定用哪些。原文实测：13 题拆 13 次 vs 合 1 次，贵 12.2 倍、慢 10 倍，答案一样。
2. **答案必须有类型**，只允许三种：
   - `choice`：从封闭选项里选一个
   - `score`：2–10 个有序等级里选一档
   - `yesno`：0–1 的“是”概率
3. **每个答案带置信度 0–1**。答案说“是什么”，置信度说“能不能照做”。

## 1. 置信度分档
| 置信度 | 只读 / 低风险（打标、排序、生成预览静帧） | 破坏性 / 昂贵（重渲全片、覆盖关键帧、push、改 Style Bible） |
|---|---|---|
| < 0.5 | 转人工 | 转人工 |
| 0.5–0.9 | 自动执行 | 转人工确认 |
| > 0.9 | 自动执行 | 自动执行（仍需代码验证副作用） |

## 2. 坑（必须遵守）
- **题与题互相看不见答案**（并行）。下一题依赖上一题结果 → 开第二次调用。
- **选项菜单按当前现实重建**：视频类型从 `docs/video-guides/` 实时列，风格从 `styles/` 实时列；不要写死旧列表。长列表先在代码里过滤。
- **置信度 ≠ 事情做成了**：说“已修复”不算，代码重测通过才算。
- `yesno = 0.5` 是“不确定”，不是“中等程度”；程度问题用 `score`。
- **给证据，不给摘要**：帧号、测量值、检查脚本输出、联系表路径；来源/发现/缺口分开写。
- **有类型 ≠ 判断对**：格式永远合法，但仍要兜底（抽检、人工复核样本）。
- **模型不数数、不算术、不比日期**：拉伸百分比、帧计数、时长、LUFS、首尾像素差全部在代码里算，只把结果当证据喂进去。
- **状态只留相关字段**：无关细节越多准确率越低；state 也要当成可能被注入的输入。
- **固定模型版本**，每条答案记录 `model` + `version` + 时间，进 Bot F 收据。
- **所有问题和阈值放一个可审文件**：`config/dispatch_questions.yaml`，改阈值走 commit。

## 3. 导演：分派 brief（一次调用）
```yaml
# config/dispatch_questions.yaml
director_route:
  state_fields: [brief_text, target_platform, has_voiceover, has_music, has_data, ref_links]
  questions:
    video_type:
      type: choice
      options: from_dir("docs/video-guides", "0*.md")   # 01-logo-intro … 10-live-footage-assist
    style:
      type: choice
      options: from_dir("styles/") + ["new_style_needed"]
    length_tier:
      type: choice
      options: ["<=6s", "6-15s", "15-60s", "1-5min"]
    abstractness:            # 抽象题材必须先填“拆题卡”（部件/谁带动谁/哪个数是真的）
      type: score
      levels: [concrete_mechanism, mixed, abstract_concept]
    needs_voiceover: {type: yesno}
    needs_beat_sync: {type: yesno}
    # 投机题：只有 type=03/05 才用，但照样一起问
    data_source_reliability: {type: score, levels: [none, unverified, cited, first_party]}
```
代码侧路由：
```python
a = ask(state, Q["director_route"])
if min(a[k].conf for k in ["video_type", "style", "length_tier"]) < 0.5:
    return to_human("brief 不清楚", a)
guide = f"docs/video-guides/{a.video_type.value}"
if a.abstractness.value == "abstract_concept":
    require("拆题卡")               # Bot B 先拆题，不得直接进 D
if a.style.value == "new_style_needed":
    route("Bot A")
```

## 4. Bot E：每个镜头审片门（一次调用）
**先跑代码检查，结果作为证据**；模型只做审美判断。
```python
evidence = {
  "contact_sheet": "out/shot03_contact.png",      # 12 帧联系表
  "frames": [0, 24, 48, 72, 96],
  "checks": {                                       # 全部代码算，见 MOTION_LESSONS §10/§7/§9
    "max_edge_stretch": 0.14,   # 上限 ±12%
    "max_area_change": 0.07,    # 上限 ±10%
    "foot_contact_drift_px": [0,0,3,0],   # 着地帧爪尖位移（>0 = 滑步）
    "loop_first_last_diff": 0.0,
    "lufs": -14.2, "true_peak_db": -1.1,
  },
  "forbidden_list": "styles/<id>/forbidden.md",
}
```
```yaml
bot_e_shot_review:
  state_fields: [shot_spec, style_bible_excerpt, evidence]
  questions:
    verdict: {type: choice, options: [pass, fix, redo]}
    motion_naturalness: {type: score, levels: [broken, stiff, ok, natural, great]}
    sliding_feet:       {type: score, levels: [none, subtle, visible, severe]}
    stretch_look:       {type: score, levels: [rigid, ok, rubbery, broken]}
    style_match:        {type: score, levels: [off, drifting, on_style]}
    timing:             {type: score, levels: [rushed, ok, draggy]}
    forbidden_hit:      {type: yesno}
    # 投机题：只有 fix 才用
    fix_scope: {type: choice, options: [easing_only, pose_keyframe, rig_weights, layer_asset, sound]}
    worst_frame: {type: choice, options: evidence.frames}   # 菜单从证据现建
  rules:
    - 意见必须带帧号；没帧号的意见丢弃
    - 每轮只取 1–2 条意见（MOTION_LESSONS §5）
```
**硬规则在代码里，不问模型**：`max_edge_stretch > 0.12`、`max_area_change > 0.10`、着地漂移 > 0、循环首尾不一致、true peak > −1 dB → 直接判 `fix`，与模型答案无关。

### 路由表
| 代码硬检查 | verdict | 置信度 | 动作 |
|---|---|---|---|
| 不通过 | — | — | `fix`，自动回 D 改对应参数（只读改动以外仍走下行规则） |
| 通过 | pass | > 0.9 | 进入下一镜头；记收据 |
| 通过 | pass | 0.5–0.9 | 进入下一镜头，标记“待抽检” |
| 通过 | fix | > 0.5 | 按 `fix_scope` 只改变化部分，重渲**该镜头预览**（低成本） |
| 通过 | redo | > 0.9 | 覆盖关键帧 / 全镜头重渲 |
| 通过 | redo | 0.5–0.9 | 转人工确认后再重做 |
| 任意 | 任意 | < 0.5 | 转人工，附联系表 + 证据 |
| — | forbidden_hit ≥ 0.5 | — | 视为 fix；把命中项写入禁用清单（Bot F） |

push / 终版 16 采样渲染（§9）属于昂贵动作：需全部镜头 pass 且置信度 > 0.9，或人工放行。

## 5. 收据格式（给 Bot F）
```json
{"call":"bot_e_shot_review","shot":"03","model":"<name>@<pinned-version>",
 "answers":{"verdict":["fix",0.82]},"evidence_hash":"…","action":"rerender_preview",
 "verified_by_code":true,"ts":"2026-10-15T02:30-07:00"}
```
