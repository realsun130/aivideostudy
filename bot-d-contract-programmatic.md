# Bot D 合同 · 纯程序化路线（已锁定）

日期：2026-10-13  
决策：成本优先 → **不上图生视频**；关键帧 + 代码时间线成片。

---

## 1. 锁定栈

```
shot_list.json
frames/<shot_id>/*.png          # Bot C 已确认关键帧（可多层：bg/char/fx）
style_bible.json                # 色板、字体、转场默认、运动偏好
        │
        ▼
Remotion 项目（代码真相源）
  - 每镜 = Composition 或 Sequence
  - 运动 = 程序化（推拉摇移、视差、淡入淡出、切镜、字幕、声画）
        │
        ▼
render → FFmpeg 编码
        │
        ▼
final/<project>_vN.mp4
assembly_manifest.json
```

轻量替代（无 React 时）：`ffmpeg` 脚本直接按 Shot List 做 zoompan / xfade / concat。  
**默认推荐 Remotion**：镜头级参数、版本化和「代码生成视频」更清晰。

---

## 2. Bot D 职责边界

### 做
- 读取锁定版 Shot List + 关键帧包 + Style Bible
- 生成/更新 Remotion（或 FFmpeg）工程
- 按镜应用**程序化运动预设**（见 §4）
- 渲染成片 + 写出 `assembly_manifest.json`
- 单镜/单场局部重渲染（降成本）

### 不做
- 调用 I2V / 文生视频 API
- 改剧本、改风格、擅自增删镜
- 在未 Sample Frame Lock 时全量渲染高分辨率

---

## 3. 输入 / 输出合同

### 输入（全部必须是已锁定版本）

| 字段 | 说明 |
|------|------|
| `project_id` | 项目 ID |
| `style_bible_ver` | 风格圣经版本 |
| `shot_list_ver` | 镜头表版本 |
| `shot_list` | 见 schema；含 duration、camera_move、transition、layers |
| `frames_root` | 关键帧目录；每镜至少 1 张，推荐分层 |
| `audio` | 可选：BGM / VO 路径与入点 |
| `render_profile` | `preview`（便宜快）\| `final`（成片） |

### 输出

| 产物 | 说明 |
|------|------|
| `remotion/` 或 `ffmpeg_plan.json` | 可复现工程 |
| `clips/` 或直接时间线 | 预览可按场输出 |
| `final/<id>_vN.mp4` | 成片 |
| `assembly_manifest.json` | 用了哪些帧、预设、分辨率、耗时、成本估算 |
| `qc_notes.md` | 缺帧、时长合计 vs Shot List 等自动检查 |

---

## 4. 程序化运动库（v1 就这些，够用且便宜）

| 预设 ID | 效果 | 典型用法 |
|---------|------|----------|
| `static` | 静止 | 强插画、停顿 |
| `kenburns_in` / `kenburns_out` | 缓推 / 缓拉 | 单张关键帧叙事 |
| `pan_left` / `pan_right` | 横移 | 场景建立 |
| `parallax` | 多层差速 | bg + char 分层时 |
| `cut` | 硬切 | 默认镜间 |
| `xfade` | 交叉淡化 | 情绪转场 |
| `fade_black` | 淡入黑/出黑 | 场次边界 |
| `subtitle_card` | 字幕/标题卡 | Style Bible 字体色板 |
| `punch_in` | 短促推近 | 重音、笑点 |

**规则：** Shot List 每镜必须带 `motion_preset` + 参数（如 `zoom: 1.0→1.08`）。  
D 只执行预设，不发明新运动——新预设由总监/你升版加入运动库。

---

## 5. 成本控制（写进总监策略）

1. **两级渲染**：`preview`（720p / 低 fps 或低质量）供 E 与你看；`final` 仅 Final Accept 后跑一次  
2. **按镜缓存**：帧与预设未变则跳过重渲染  
3. **禁止**在样帧未锁时全片 final  
4. **E 返工**默认只重渲标红镜头，不整片重来  
5. 运动尽量用 1–3 张静帧 + 相机运动；需要「表演」时优先加关键姿态帧（仍是静帧），而不是上 I2V  

相对图生视频：此路线边际成本≈算力与时间，无按秒 API 费用。

---

## 6. 与上下游的接口要点

- **Bot C**：尽量输出**分层 PNG**（背景/角色/前景），否则 D 只能 Ken Burns，表现力上限明显  
- **Bot B**：Shot List 必须填 `motion_preset`、`duration_sec`、`transition_to_next`；可选 `camera: {from, to}`  
- **Bot E**：对照 Shot List 查时长合计、是否用错预设、是否黑场过长；不要求「物理真实运动」  
- **F 记忆**：记录你喜欢的预设组合（如「对白镜默认 kenburns_in 1.05」）

---

## 7. 成功标准（纯程序化）

- 成片总时长与 Shot List 误差 ≤ 0.1s / 镜（或整片 ≤ 2%）  
- 零外部视频 API 调用  
- 任意只改一镜帧或预设，可只重渲该镜并重链成片  
- 同一 manifest 输入可复现同版本成片  

---

## 8. 何时以后再考虑混合

仅当出现：**分层关键帧 + 全套运动预设仍无法接受的「活物表演」**，且你愿意为单镜付 I2V 成本时——按镜开通 `motion_preset: i2v` 例外，不作为默认。

---

## 9. 建议的下一步

1. 写 `shot_list.schema.json`（含 `motion_preset` 枚举）  
2. 写 `style_bible.schema.json`（字体、色板、默认转场）  
3. 搭一个 **15s Remotion 最小模板**（3 镜：推、切、淡）验证成本与手感  
