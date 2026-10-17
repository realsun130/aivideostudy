# 故事管线合并方案（情感短片体系 × Bot B）⚠️ 待测试

把「AI 情感动画创作体系 V1.0」与现有 Bot B / 灰盒动态分镜流程合成**一条管线、两套成片规格**。传播效果不在创作阶段猜，上传后用真实数据测。

## 1. 一张总流程图

```
观察/访谈/公共主题 → 素材卡（Agent1）
        ↓
情绪洞察 + 12 机制候选（Agent2）→ 人工选 1–2
        ↓
选定规格 Track S 或 Track M
        ↓
三种叙事机制 → 人选一种 → 分镜（Agent3 / Bot B）
        ↓
红队审稿可否决（Agent4 / Bot E）
        ↓
灰盒动态分镜（主迭代环）→ 成片
        ↓
上传真实平台 → 留存/完播/分享/评论回写 STORY_DNA
```

## 2. Agent 对照（不跑两套人）

| 情感体系 | 我们现有 | 合并后职责 |
|---|---|---|
| Agent1 生活观察员 | insight_pool / 真实细节池 | 只产素材卡，禁止写剧情 |
| Agent2 情绪洞察与选题 | 20 条 logline / 选题 | 12 机制候选 + 六维分；人工终选 |
| Agent3 短片编剧 | Bot B 剧本模板 | 按规格分支写分镜（见下） |
| Agent4 红队 | Bot E + 四方评审 | 有否决权；只指问题/给删减 |
| 小样与复盘 | 灰盒 animatic | 灰盒仍是主迭代；上线后再测传播 |

指令原文：`content_brain/emotion_shorts/prompts/FOUR_AGENTS.md`  
Bot B 清单式模板：`prompts/bot_b_script_template.md`（降为 **Track M 可选工具**，不是每部必用）

## 3. 两套制作规格（并存，选题时二选一）

### Track S｜竖屏短打（来自情感体系）
- 时长 30–60 秒；9:16；6–9 镜；1–3 人；1–2 主场景
- 语法：生活细腻 / 现实刺痛 / 荒诞幽默 三选一
- 适合：一个动作即共鸣、低成本代码动画、快测传播
- 高潮：不强制“不可逆选择”；允许留下不舒服余味

### Track M｜叙事中片（来自我们原流程）
- 时长约 90 秒；镜数约 12–14；可横可竖
- 可选清单式母题（Bot B）；可量化参数（亮度/距离）便于代码
- 适合：需要节奏弧线、首尾对照、主动选择的故事
- 高潮：优先主角主动动作；仍禁说教字幕

**选题规则**：同一素材卡可以同时出 S 版与 M 版机制，但**一次只制作一条规格**；两条都试过并有上传数据后，再决定该题材的默认规格。

## 4. 共用硬规则（两套都遵守）

来自情感体系，覆盖旧 Bot B 易说教处：
1. 行为先于情绪标签；道具先于金句。
2. 两个成立却互相妨碍的愿望。
3. 删旁白与片尾金句后故事仍成立。
4. 禁止冒充“真实故事改编”；虚构种子须标注。
5. 红队可一票否决“不值得拍”。

Track M 额外可选：清单式重复、首尾同机位、参考片原则（效果好才用）。

## 5. 文件落点

```
content_brain/emotion_shorts/
  STYLE_BIBLE.md      ← 体系 V1.0
  STORY_SEEDS.md      ← 24 则虚构种子（待真实校验）
  CURRENT_STATE.md
  LIFE_MOMENTS.md     ← 索引；正文 JSON 在 moments/LM-xxxx.json
  STORY_DNA.md        ← schema 指针 + 日志表；总监 DELIVER 后写
  moments/            ← 行为卡 JSON per id
  prompts/FOUR_AGENTS.md
docs/STORY_PIPELINE_MERGED.md  ← 本文
prompts/bot_b_script_template.md  ← Track M 可选
projects/stolen-night/            ← Track M 试验归档，暂不锁版
```

## 6. 逐一尝试的顺序（定案）

1. **第一批 Track S（三风格各一）：** **L04（细腻）+ R02（刺痛）+ H02（荒诞）**。同一批评审池必须覆盖两种以上叙事风格；禁止第一批全做细腻。
2. **第二批：** L01 / L05 等其余细腻种子，以及需要时的 Track M。
3. **上传后**才比传播；创作阶段只看：复述率、假感位置、是否联想到自己的经历。STORY_DNA 由总监在 DELIVER 后按 `schemas/story_dna.schema.json` 回写。

## 7. 与《偷来的夜》的关系

v1–v5 保留作 Track M 试验档案，不再为过 8 分空转结构。重开素材卡已补 LM-0001…0005（见 `moments/`，虚构标+创作者推断）；决定走 S 或 M 后再开拍。第一批成片仍优先 L04/R02/H02，不与重开素材抢批次。

## 桥接详版
字段级 schema、Agent4 闸门、风格/Track 规则：见 [EMOTION_TO_PIPELINE_BRIDGE.md](./EMOTION_TO_PIPELINE_BRIDGE.md)。人类情感 Style Lock：`styles/human-emotion-flat-illustration/`（人读对照 `content_brain/emotion_shorts/style-bible-human-emotion.md`）。
