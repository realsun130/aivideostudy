# Schemas

## Separation of concerns

| File | Owns | Does **not** own |
|------|------|------------------|
| `style_bible.schema.json` | Look: medium, palette, line, light, still composition, prompts | Motion, transitions, timing |
| `shot_list.schema.json` | Shots: duration, FilmGraph cinematography, transitions, frames | Visual DNA |
| `motion_profile.schema.json` | Per-style pacing/transition/spring/audio numbers (`styles/<slug>/motion_profile.json`) | Look |
| `final_review.schema.json` | Output of `tools/final_review.py` (delivery gate) | — |
| `decision_log.schema.json` | Director key decisions | — |
| `checkpoint.schema.json` | `projects/<id>/checkpoints/<NN>_<stage>.json` resume points | — |
| `cost_log.schema.json` | Per-stage cost, revision caps, >30% drift alert (`tools/cost_check.py`) | — |
| `cinematography_vocab.json` | FilmGraph enums + map → Remotion presets | Style look |

## Sources

- Style packs: [AI-Visual-Prompt-Cookbook](https://github.com/VigoZhao/AI-Visual-Prompt-Cookbook) (MIT)
- Cinematography enums: [FilmGraph](https://github.com/gokaykucuk/filmgraph) (MIT)
- Remotion motion/transition implementations: see [remotion-templates](https://github.com/reactvideoeditor/remotion-templates)

## Flow

1. **Style Lock** → `style_bible.json` (visual only)
2. **Shot Lock** → `shot_list.json` (cinematography semantic + optional programmatic overrides)
3. Bot D maps `camera_movement` / `transition_to_next` via `cinematography_vocab.json` when programmatic fields are omitted
