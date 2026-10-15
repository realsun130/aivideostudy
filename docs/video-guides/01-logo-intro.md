# Guide Book 01：Logo 片头 / 品牌开场

一段 3–8 秒的短片：品牌标志或名称以一个有记忆点的动作出现，最后落版停住。常见于视频开头、片尾和社交媒体头图视频。

## 一、适用场景
- 系列视频统一开头或结尾；产品发布、活动开场。
- 需要同一个开场换不同标题或副标题批量出版本（用参数驱动）。
- 需要透明背景，叠到别的剪辑里。

## 二、不适用
- 品牌还没定好主色、字体、标志：先定这些，再做动画。
- 想要照片级的 3D 材质流体：可以用 three.js 做（参考 Liquid Chrome 那次实验），但已经超出“片头模板”的范围，按独立项目做。
- 时长超过 10 秒：观众会跳过，应改成 02 动态文字或 05 解说片头。

## 三、实施流程
1. **参考**（FR 第 1 步）：找 1–2 个喜欢的片头，拆解成数字：第一个动作在第几帧、高潮在哪、落版停留多长。
2. **BRAND 块**（BDAY）：标志 SVG、主色 hex、字体、可选的口号，只定义一次，后面全用名字引用。
3. **只选一种性格**（MDS `SKILL.md` Motion Personality）：活泼 / 高级 / 商务 / 有活力，整个片头不混用。
4. **写节拍表**：预备 → 主动作（揭示）→ 次要动作（口号、光效）→ 落版停留。
5. 在 Studio 里搭场景，参数用 Zod schema 暴露（RS `remotion-markup/parameters.md`）。
6. 出静帧：每个节拍前后各看几帧（BDAY CHECKS 的做法），测品牌色。
7. 用话导演、按帧号改 1–2 条（ML §5），直到锁定。
8. 终版：需要时开运动模糊（ML §9），需要透明就出 ProRes 4444 或 WebM。

## 四、技术要点
- 运动：`interpolate()` + `Easing.bezier`；缩放动画用 RS `remotion-markup/timing.md` 里的缩放补偿写法，否则大尺寸时看起来变慢。
- 关键帧直接写在 `style` 里、用独立的 `scale` / `translate` / `rotate` 属性，这样能在 Studio 里拖动修改（RS `remotion-markup/timing.md`）。
- SVG 描边画出：`stroke-dashoffset` 由 `interpolate` 驱动。
- 光效：`remotion-markup/light-leaks.md`、`remotion-markup/effects.md`；用 `TransitionSeries.Overlay` 叠在切点上而不缩短时间线（`remotion-markup/transitions.md`）。
- 音效：`<Audio>`（`remotion-markup/audio.md`），现成音效见 `remotion-markup/sfx.md`（如 whoosh、ding）；要完全干净的版权就按 ML §7 用代码合成。
- 透明输出：`remotion-render/transparent-videos.md`（ProRes 4444 用 `--pixel-format=yuva444p10le --codec=prores --prores-profile=4444`，或 WebM VP9）。
- 字体：`remotion-markup/google-fonts.md` / `local-fonts.md`，确保渲染前字体已加载。

## 五、时间缓动与叙事
| 项 | 数字 | 来源 |
|---|---|---|
| 主揭示时长 | 600–1200 ms（Dramatic reveal） | MDS `reference/timing-easing-tables.md` |
| 主角揭示 | 600–900 ms | ML §3 |
| 性格：高级 | 350–600 ms，回弹 0%，(0.4,0,0.2,1) | MDS `SKILL.md` |
| 性格：活泼 | 150–300 ms，ease-out-back，回弹 10–20% | MDS `SKILL.md` |
| 出场比入场短 | 出场 = 入场的 65–75% | MDS `reference/timing-easing-tables.md` |
| 字母错开 | 每字 1 帧；词 60–120 ms | ML §3 |
| 错开总预算 | < 500 ms | MDS `SKILL.md` |
| 落版停留 | 1.0–1.5 s（**起始值，需调**） | — |
| 冲击感 | scale 1.0→1.08→1.0，6 帧，峰值在拍上 | ML §5 |

叙事上就是 MDS 的微故事：Setup → Action → Resolution（`director/narrative-structure.md`）。一个片头只要一个主动作，其余是次要层和环境层（三层运动）。

## 六、验收清单
- [ ] 静帧 0 / 揭示峰值 / 落版最后一帧都成立（静止也好看）。
- [ ] 落版那一帧的品牌色实测等于 hex（BDAY CHECKS 的做法）。
- [ ] 同时在动的元素不超过 1/3（MDS 1/3 规则）。
- [ ] 没有禁用清单里的默认样式：紫蓝渐变、无意义光晕、装饰粒子、全体同时淡入（ML §2）。
- [ ] 音效峰值比画面事件晚 1 帧；编码后真峰值 < −2 dBTP（ML §7）。
- [ ] 透明版在剪辑软件里边缘无黑边。

## 七、可借鉴资料
- **MDS**：`SKILL.md` 的 Motion Personality 与 Brand Motion Identity（招牌缓动、3 个时长、一种入场方式）；`reference/timing-easing-tables.md` 的时长、贝塞尔、回弹预算（庆祝 15–25%，高级 0%）；`patterns/entrance-exit.md`；`director/disney-principles.md`（预备、跟随）。
- **RS**：`remotion-markup/timing.md`、`parameters.md`、`transitions.md`、`light-leaks.md`、`sfx.md`、`audio.md`、`motion-blur.md`；`remotion-render/transparent-videos.md`。
- **ML**：§1 渲染合同、§2 禁用清单、§3 数字速查、§5 “更有冲击力 / 更高级”的数字翻译、§7 声音、§9 运动模糊。
- **BDAY**：BRAND 块只定义一次；CHECKS 测品牌色。
- **FR**：先喂参考，不要描述风格。
