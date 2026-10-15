# Guide Book 02：动态文字（Kinetic Typography）

以文字为主角的视频：金句、歌词、宣言、要点清单，文字按节奏出场、强调、退场。

## 一、适用场景
- 短视频金句、观点卡、发布会口号、歌词视频。
- 有一段配音或音乐，需要文字跟着走（与 05、08 搭配）。
- 需要批量换文案（一个模板出几十条）。

## 二、不适用
- 文字很长、需要读完整段的内容：改成静态图文或 05 解说视频。
- 需要手写字效果、逐笔笔顺：可以做，但要 SVG 路径数据，成本高。

## 三、实施流程
1. 写文本稿，按“意义单元”断句，每一句标出要强调的那个词。
2. 算阅读时间：每句的停留 ≥ 0.3 s/词 + 0.5 s（ML §3）。中文按“词”估计，也可按 4–5 字/秒（**起始值，需调**）。
3. 选性格和一种入场方式（MDS），整片统一。
4. 定排版：字号阶梯、对齐方式、每屏行数。避免“全部居中”这种默认样式（ML §2 禁用清单）。
5. 搭模板：文案作为 props 传入，`calculateMetadata` 按文本长度算总时长（RS `remotion-markup/calculate-metadata.md`）。
6. 出联系表检查阅读停留，再按帧号调。

## 四、技术要点
- 测字宽：`remotion-markup/measuring-text.md`（排版前量字宽，避免溢出），布局需要 DOM 尺寸时用 `measuring-dom-nodes.md`。
- 字体加载：`google-fonts.md` / `local-fonts.md`。
- 强调：`@remotion/rough-notation` 的 `<Highlight>` / `<Circle>` / `<Underline>`，`progress` 用 `interpolate` 写在行内（`remotion-markup/text-highlights.md`）。
- 逐词出场：把句子拆成词数组，每个词 `from = 起点 + i × 错开帧数`；多个句子用 `<Sequence>` 或 `TransitionSeries`（`sequencing.md`）。
- 有配音或歌词时：字幕数据按 `remotion-captions/` 的格式（`display-captions.md`、`import-srt-captions.md`）。

## 五、时间缓动与叙事
| 项 | 数字 | 来源 |
|---|---|---|
| 阅读停留 | ≥ 0.3 s/词 + 0.5 s；停留期 2% 缓推保持画面活 | ML §3 |
| 字母间隔 | 1 帧 | ML §3 |
| 词间隔 | 60–120 ms | ML §3 |
| 错开总预算 | < 500 ms | MDS `SKILL.md` |
| 入场 / 出场 | 入场 ease-out，出场 ease-in 且短 40–50% | ML §3 |
| 文字回弹 | “高级”感：文字不过冲 | ML §5 |
| 对比度 / 闪烁 | 对比 ≥ 4.5:1，闪烁 ≤ 3 次/秒 | ML §3 |
| 有节拍时 | 拍上切，每 4 拍换布局 | ML §3 |

叙事：一屏一个主动作；**阅读中的文字不许移动**（ML §2 禁用清单）。重要变化不能只用透明度，要配合位置或缩放（MDS 质量规则）。

## 六、验收清单
- [ ] 每句停留够读完（按上面的公式核对帧数）。
- [ ] 正在被读的文字是静止的。
- [ ] 没有“每个元素都淡入上滑”这种默认动作。
- [ ] 字没有溢出安全区；换最长的文案测一次。
- [ ] 对比度 ≥ 4.5:1。

## 七、可借鉴资料
- **MDS**：`patterns/entrance-exit.md`、`patterns/multi-element.md`（错开写法）、`director/choreography.md`（主角先出场、同一方向进场、1/3 规则）、错开预算表。
- **RS**：`remotion-markup/measuring-text.md`、`text-highlights.md`、`timing.md`、`sequencing.md`、`calculate-metadata.md`、`parameters.md`、`remotion-captions/display-captions.md`。
- **ML**：§2 禁用清单、§3 阅读停留与错开、§5 “拖沓 / 太乱”的数字翻译。
- **FR**：“描述风格而不是展示风格”是常见错误，先给参考。
