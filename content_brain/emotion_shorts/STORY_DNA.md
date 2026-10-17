# STORY_DNA 上线复盘 ⚠️ 待测试

机器可读 schema：[`schemas/story_dna.schema.json`](../../schemas/story_dna.schema.json)

**写入人：** 总监（director）在 **DELIVER 之后**追加一行/一条 JSON。  
**时机：** 上传真实平台并有可填数据后；创作阶段不猜完播/转发。

## 必填字段（摘要）

| 字段 | 说明 |
|------|------|
| story_id | 故事 ID |
| track | `S` / `M` |
| narrative_style | `细腻` / `刺痛` / `荒诞` |
| style_slug | 如 `human-emotion-flat-illustration` |
| retell_rate | 0–1，可后补 |
| fake_spots | 假感位置列表 |
| personal_association | 是否联想到自己 |
| completion_rate / share_rate | 有数据再填 |
| comment_mood | 评论情绪摘要 |
| keep_or_kill | `keep` / `iterate` / `kill` |
| written_by | 须为 director after DELIVER |
| uploaded_at | ISO 时间 |
| notes | 自由备注 |

## 日志（空表，上传后追加）

| story_id | track | narrative_style | style_slug | keep_or_kill | uploaded_at | notes |
|----------|-------|-----------------|------------|--------------|-------------|-------|
| — | — | — | — | — | — | 尚无上传 |

单条完整记录可另存 `content_brain/emotion_shorts/story_dna/<story_id>.json`（校验同上 schema）。
