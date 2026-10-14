# animation-pipeline

风格→剧本→关键帧→纯程序化成片（Remotion/FFmpeg）的流水线文档与 schema。

Bot D 已锁定：不上图生视频，成本优先。

## Schemas

- `schemas/style_bible.schema.json` — **只锁画风**（色、线、光、静帧构图、prompt）
- `schemas/shot_list.schema.json` — 镜头表：FilmGraph 景别/运镜/转场 + 可选 Remotion `programmatic_motion`
- `schemas/cinematography_vocab.json` — FilmGraph 枚举与程序化默认映射
- Examples under `schemas/examples/`

## Adopted styles

- `styles/rough-animation-pet-sketch-storyboard-style/` — mapped from [AI-Visual-Prompt-Cookbook](https://github.com/VigoZhao/AI-Visual-Prompt-Cookbook/tree/main/styles/rough-animation-pet-sketch-storyboard-style) into `style_bible.json` (MIT upstream).
