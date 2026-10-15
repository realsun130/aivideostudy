# Guide Book 10：实拍素材辅助（剪辑 + 图形包装）

已有实拍或录屏素材，用代码完成剪辑、去停顿、加字幕、加图形包装（标题条、注释、数据卡、画中画）。

## 一、适用场景
- 口播、访谈、vlog、课程录像、播客视频版。
- 系列栏目统一包装（片头、标题条、字幕样式）批量出片。
- 需要在人物说到某个词时弹出卡片或注释。

## 二、不适用
- 需要精细调色、复杂多机位剪辑：用专业剪辑软件，代码只出包装素材（透明视频）。
- 素材分辨率或格式很杂：先统一转码。

## 三、实施流程
1. 收素材，读出每段的时长和尺寸（`remotion-multimedia/get-video-duration.md`、`get-video-dimensions.md`）。
2. 去掉头尾和中间静音：`silence-detection.md`（用 FFmpeg loudnorm 测响度，再用自适应阈值做 silencedetect）。
3. 转写字幕：`remotion-captions/transcribe-captions.md`，或导入 SRT。
4. 搭剪辑时间线：`video-editing.md`（字幕与覆盖层同步的片段、独立定位的片段、`TransitionSeries` 连续片段）。
5. 写包装：标题条、注释卡在对应词的时间点出现。
6. 预览校对，按“第几秒、哪句话”改。

## 四、技术要点
- 视频：`<Video>` 来自 `@remotion/media`，支持裁剪、延迟、音量、速度、循环（`remotion-markup/embedding-videos.md`）；画面裁切见 `cropping.md`。
- 剪辑时间线写法：`video-editing.md`。
- 字幕：`remotion-captions/display-captions.md`；关键词高亮可用 `text-highlights.md`。
- 时长自适应：`calculateMetadata` 按素材时长设定总帧数（`calculate-metadata.md`）。
- 预挂载：每个视频片段 `premountFor={fps}`（`sequencing.md`）。
- 需要额外 FFmpeg 处理时参考 `remotion-markup/ffmpeg.md`。
- 只出包装、交给剪辑软件：透明 ProRes 4444（`remotion-render/transparent-videos.md`）。

## 五、时间缓动与叙事
| 项 | 数字 | 来源 |
|---|---|---|
| 卡片进出 | 200–350 ms，入场 ease-out | MDS `reference/timing-easing-tables.md` |
| 出场 | 入场的 65–75% | 同上 |
| 字幕停留 | ≥ 0.3 s/词 + 0.5 s | ML §3 |
| 注释出现 | 对准说到的那个词（**起始值**：提前 2–4 帧，需调） | — |
| 性格 | 商务：(0.2,0,0,1)，回弹 0–3% | MDS `SKILL.md` |
| 响度 | 约 −14 LUFS，成品真峰值 < −2 dBTP | ML §7 |

叙事：人是主角，图形是次要层，幅度和数量都要克制；同一时间只有一个图形在动。

## 六、验收清单
- [ ] 去静音后没有切掉词头词尾。
- [ ] 字幕和口型对齐。
- [ ] 包装不挡人脸和关键画面。
- [ ] 换一段新素材，模板自动适应时长。
- [ ] 成品上复测响度。

## 七、可借鉴资料
- **RS**：`remotion-markup/video-editing.md`、`embedding-videos.md`、`silence-detection.md`、`cropping.md`、`ffmpeg.md`、`calculate-metadata.md`、`text-highlights.md`；`remotion-captions/`；`remotion-multimedia/`；`remotion-render/transparent-videos.md`。
- **FR**：HyperFrames Student Kit（专门剪你自己拍的素材：去停顿、加字幕）；Barty-Bart Motion Graphics（说到某个词时让卡片出现）；剪辑间的思路。
- **MDS**：商务性格、卡片入场配方、三层运动（实拍是主层，包装是次要层）。
- **ML**：§3 停留时间、§5 审核循环、§7 响度。
