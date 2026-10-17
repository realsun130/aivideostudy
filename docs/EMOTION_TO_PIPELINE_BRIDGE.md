# 情感体系 → 流水线桥接 ⚠️ 待测试

把 `content_brain/emotion_shorts/` 接到 A–F 流水线。传播指标等上传后再测；本文件只定**字段、闸门、风格选择、规格分流**。

相关：`docs/STORY_PIPELINE_MERGED.md` · `content_brain/emotion_shorts/STYLE_BIBLE.md` · `styles/human-emotion-flat-illustration/` · `prompts/bot_b_script_template.md`

## 1. 素材卡 schema（Agent1 唯一产出）

机器可读副本：`schemas/life_moment_card.schema.json`

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | string | ✓ | `LM-xxxx` |
| scene | string | ✓ | 时间+地点+环境声线索 |
| observed_behavior | string | ✓ | 可见动作，禁止纯心理形容词 |
| exact_words | string | | 仅授权可用时的原话 |
| visible_object | string | ✓ | 核心道具（可多个，逗号分隔） |
| apparent_goal | string | ✓ | 表面愿望 |
| hidden_need_hypothesis | string | ✓ | 隐秘愿望（须标 confidence） |
| conflict | string | ✓ | 两个愿望如何互相妨碍 |
| source_type | enum | ✓ | `自我观察` / `授权访谈` / `公共主题观察` / `原创虚构` |
| source_date | string | | ISO 日期 |
| source_reference | string | | 内部编号，不含私人身份 |
| consent_or_usage | string | ✓ | 授权状态；虚构写 `n/a-fiction` |
| privacy_notes | string | ✓ | 去身份化说明 |
| confidence | enum | ✓ | `观察到的事实` / `采访者陈述` / `创作者推断` |
| track_hint | enum | | 可选 `S` / `M` / `either`，不替代人工选型 |
| style_hint | enum | | 可选 `细腻` / `刺痛` / `荒诞` / `unset` |
| emotion_tags | string[] | | 可选封闭列表：温暖/尴尬/难堪/犹疑/恼怒/荒谬/惭愧/松弛/孤独/心软/疲惫/侥幸/克制 |

**闸门（进 Agent2 前）**：缺 `observed_behavior` 或 `visible_object` → 退回；`source_type=原创虚构` 未标注 → 退回；可识别隐私未处理 → 退回。

**语义检查（定案）：** 由 **Agent2 首轮复核**执行——`observed_behavior` 须含具体动词；纯心理形容词（如「她很孤独」无动作）→ 退回 Agent1。不要只写「自动/人工」而不指名。

**存储定案（不再留「或」）：**
- **JSON per id**：`content_brain/emotion_shorts/moments/LM-xxxx.json`（校验 schema）
- **`LIFE_MOMENTS.md`**：仅索引表，不写完整字段

## 2. Agent 在流水线中的位置

```
Agent1 观察员 ──卡片──► [卡闸] ──► Agent2 选题 ──12机制──► 人工选1–2
                                              │
                                    选 Track S 或 Track M
                                              │
                         Agent3 编剧 / Bot B ◄─┘
                                              │
                                    [Agent4 红队闸]  ← 可一票否决
                                              │
                         灰盒动态分镜 → Bot D 成片 → Bot E 成片审
                                              │
                                    上传 → STORY_DNA 回写（总监 DELIVER 后）
```

| 步骤 | 谁 | 放行条件 |
|---|---|---|
| 卡闸 | schema + Agent2 首轮语义检查 | 必填齐；虚构已标；隐私 OK；行为含动词 |
| 选题后 | 人 | 选定故事 ID + Track + 风格语法 |
| **Agent4 闸** | 红队 | 结论必须是 `放行` / `返修` / `淘汰`；**淘汰不得进入灰盒**；返修最多 2 轮再淘汰 |
| 灰盒后 | 人+小样 | 复述率、假感位置、联想到的经历；不在此猜转发量 |
| 成片 Bot E | 检查项 | MOTION_LESSONS + lemo 审核清单 |
| STORY_DNA | 总监 after DELIVER | 字段见 `schemas/story_dna.schema.json`；索引表见 `STORY_DNA.md` |

Agent4 检查顺序见 `prompts/FOUR_AGENTS.md`。与 Bot E 分工：Agent4 管**故事真假与套路**；Bot E 管**运动/声音/技术合同**。

## 3. 风格选择规则（叙事语法，不是画风）

先选**叙事风格**，再挂**视觉 Style Bible**。

| 选这个 | 当素材里… | 不要选如果… |
|---|---|---|
| **生活细腻** | 一个下意识小动作就能说明关系/缺席 | 需要重大事故或金句才懂 |
| **现实刺痛** | 两边都有理，资源/规则逼出不体面选择 | 能简化成「多沟通就好了」或纯坏人 |
| **荒诞幽默** | 一条可升级的怪规则，摘掉后现实心理仍成立 | 需要两条以上怪规则，或笑点靠羞辱角色 |

**批次约束：** 同一批评审池至少覆盖两种叙事风格；禁止整批都是父母和解或纯催泪。  
**第一批定案：** **L04（细腻）+ R02（刺痛）+ H02（荒诞）** 各一支。L01 / L05 留第二批。

## 4. Track 选择规则（制作规格）

| 选 Track S（30–60s / 6–9 镜 / 9:16） | 选 Track M（~90s / 12–14 镜） |
|---|---|
| 一个道具/一个动作撑全片 | 需要多次重复或明显情绪弧线 |
| 静帧+手部+环境声即可 | 需要可量化参数曲线（亮度/距离等） |
| 先做传播小样 | 已通过 S 或明确要中片结构 |

同一素材卡可写两套机制，**一次只制作一条 Track**。

## 5. 视觉 Style Bible 挂载

| 内容类型 | Style Lock（`styles/` 菜单可见） |
|---|---|
| 人类情感短片（本桥接默认） | `styles/human-emotion-flat-illustration/`（`style_bible.json` + `motion_profile.json`） |
| 宠物潦草素描 | `styles/rough-animation-pet-sketch-storyboard-style/` |

人读对照：`content_brain/emotion_shorts/style-bible-human-emotion.md`（与 JSON 同步，**非** canonical lock）。

Bot A 出风格锁定时：人类情感题材**禁止**默认套用 pet sketch；须显式选用 `human-emotion-flat-illustration`。`locked_by` 仍为 `pending_user_style_lock`。双色冷暖对抗须 Story Card 声明 `dual_accent_conflict: true`。

## 6. 最小开工清单

1. 至少 5 张合规素材卡（JSON per id；含真实观察或明确虚构标）— 《偷来的夜》重开已有 LM-0001…0005  
2. Agent2 → 人选定：故事 ID + 叙事风格 + Track（第一批优先 L04/R02/H02）  
3. Agent3 分镜 → **Agent4 放行**  
4. 灰盒 → 成片 → 上传后总监写 `STORY_DNA`（schema 校验）

## 7. 文档冻结

本轮契约落地后：**冻结新规则文档**，直到跑完一支 Track S 全流程（素材卡 → Agent4 → 灰盒 → 成片 → 上传 → STORY_DNA 回写）再用成片验证桥接。见 `content_brain/emotion_shorts/CURRENT_STATE.md`。
