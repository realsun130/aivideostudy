# Guide Book 05：解说视频（配音 + 字幕）

由一条配音讲完一个主题，画面是图表、图示、文字和简单动画的组合。时长由配音决定。

## 一、适用场景
- 知识科普、产品原理、教程、内部培训。
- 需要多语言版本（换配音和字幕，画面模板不变）。

## 二、不适用
- 没有稿子：先写稿，配音是最后才确定时长的东西。
- 情绪表演为主、靠角色动作讲故事：用 06 角色短片。
- 真人出镜讲解：用 10 实拍辅助。

## 三、实施流程（FR：故事先行，留空位）
1. **写稿**：按场景分段，每段一个观点；在需要画面的地方留 `[画面：xx]`。
2. **生成配音**：每个场景一个音频文件。RS `remotion-markup/voiceover.md` 默认用 ElevenLabs TTS（需要 `ELEVENLABS_API_KEY`），可以换成任何能出音频文件的 TTS 或真人录音。
3. **用配音长度定画面时长**：`calculateMetadata` 读取每段音频时长，动态设定总帧数（`voiceover.md`、`calculate-metadata.md`、`remotion-multimedia/get-audio-duration.md`）。
4. **字幕**：转写得到逐词时间（`remotion-captions/transcribe-captions.md`），或导入 SRT（`import-srt-captions.md`），再显示（`display-captions.md`）。
5. **画面**：每个场景一个组件，把画面关键动作对齐到配音里对应的词。
6. 背景音乐和音效最后叠，配音期间压低音乐。
7. 静帧 + 听一遍，按“第几秒、哪句话、画面晚了几帧”改。

## 四、技术要点
- 音频：`<Audio>` 来自 `@remotion/media`，支持裁剪、音量、速度（`remotion-markup/audio.md`）。
- 场景串联：`TransitionSeries`，每个 `Sequence` 的 `durationInFrames` 来自对应配音长度（`multi-scene-video.md`）。
- 去掉配音头尾静音：`silence-detection.md`。
- 字幕逐词高亮：用转写得到的词级时间戳，当前词放大或变色。
- 音效：`sfx.md`；完全自制音效见 ML §7。
- 预挂载：每个 `Sequence` 设 `premountFor={fps}`（`sequencing.md`），避免音频首帧卡顿。

## 五、时间缓动与叙事
| 项 | 数字 | 来源 |
|---|---|---|
| 画面动作对齐 | 关键动作落在对应词开始处（**起始值**：提前 2–4 帧，需调） | — |
| 音效晚画面 | 1 帧（≈17 ms @60fps） | ML §7 / BDAY |
| 响度 | 约 −14 LUFS；编码后真峰值 < −2 dBTP | ML §7 |
| 限幅 | 单次压限 ≤ 3 dB | ML §7 |
| 字幕停留 | ≥ 0.3 s/词 + 0.5 s | ML §3 |
| 场景切换 | 默认硬切，转场必须是有理由的决定 | ML §2 |
| 性格 | 商务 / 平静：sine ease-in-out，500–1000 ms | MDS `SKILL.md` 情绪表 |

叙事：一段一个观点；先给问题再给答案。画面不要和配音抢：配音讲的时候，画面里同时只一个主动作。

## 六、验收清单
- [ ] 改一句稿子、重新生成配音后，画面时长自动跟着变（证明 calculateMetadata 生效）。
- [ ] 字幕和声音对齐，误差不超过 2 帧（**起始值**）。
- [ ] 成品 MP4 上复测响度和真峰值（ML §7：AAC 会冒峰）。
- [ ] 配音期间音乐不盖过人声。
- [ ] 静音观看时，字幕也能讲清内容。

## 七、可借鉴资料
- **RS**：`remotion-markup/voiceover.md`、`calculate-metadata.md`、`audio.md`、`silence-detection.md`、`sfx.md`、`multi-scene-video.md`、`sequencing.md`；`remotion-captions/`（`transcribe-captions.md`、`import-srt-captions.md`、`display-captions.md`）；`remotion-multimedia/get-audio-duration.md`。
- **FR**：剪辑间“先写好故事、留空位”；工作流第 3 步；Barty-Bart 的 Motion Graphics 技能（让卡片在说到某个词时出现）。
- **ML**：§2 导演模板、§3 停留时间、§7 声音合同（响度、峰值、晚 1 帧）。
- **MDS**：情绪表（平静 / 优雅）、`director/narrative-structure.md`。
