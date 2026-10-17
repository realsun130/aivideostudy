#个人学习使用

# animation-pipeline

风格→剧本→关键帧→纯程序化成片（Remotion/FFmpeg）的流水线文档与 schema。

Bot D 已锁定：不上图生视频，成本优先。

## 人读总览（中文）

- [`docs/STYLE_AND_SHOT_SUMMARY.md`](docs/STYLE_AND_SHOT_SUMMARY.md) — **风格 + 镜头两部分总览**（分离原则、当前 Style Bible 摘要、FilmGraph 词表中文释义）
- [`docs/style-bible-rough-pet-sketch.md`](docs/style-bible-rough-pet-sketch.md) — 当前锁定风格深摘要（纯画风）
- [`docs/cinematography-filmgraph.md`](docs/cinematography-filmgraph.md) — FilmGraph 景别/运镜/转场 + Remotion 映射

- [`docs/DISPATCH_CONVENTIONS.md`](docs/DISPATCH_CONVENTIONS.md) — **调度约定：扇出提问 + 置信度路由**（导演分派 / Bot E 审片门）
- [`docs/OPENMONTAGE_GAP_ANALYSIS.md`](docs/OPENMONTAGE_GAP_ANALYSIS.md) — OpenMontage 对照查漏 + P0/P1/P2 待办
- [`docs/STYLE_LIBRARY_CANDIDATES.md`](docs/STYLE_LIBRARY_CANDIDATES.md) — 风格候选库（共鸣短片/解说/产品/文字动效，13 个候选 + 前三推荐）

## Schemas

- `schemas/style_bible.schema.json` — **只锁画风**（色、线、光、静帧构图、prompt）
- `schemas/shot_list.schema.json` — 镜头表：FilmGraph 景别/运镜/转场 + 可选 Remotion `programmatic_motion`
- `schemas/cinematography_vocab.json` — FilmGraph 枚举与程序化默认映射
- Examples under `schemas/examples/`
- 分离说明：[`schemas/README.md`](schemas/README.md)

## Adopted styles

- `styles/rough-animation-pet-sketch-storyboard-style/` — mapped from [AI-Visual-Prompt-Cookbook](https://github.com/VigoZhao/AI-Visual-Prompt-Cookbook/tree/main/styles/rough-animation-pet-sketch-storyboard-style) into `style_bible.json` (MIT upstream).
