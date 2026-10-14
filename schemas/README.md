# Schemas

## Separation of concerns

| File | Owns | Does **not** own |
|------|------|------------------|
| `style_bible.schema.json` | Look: medium, palette, line, light, still composition, prompts | Motion, transitions, timing |
| `shot_list.schema.json` | Shots: duration, FilmGraph cinematography, transitions, frames | Visual DNA |
| `cinematography_vocab.json` | FilmGraph enums + map → Remotion presets | Style look |

## Sources

- Style packs: [AI-Visual-Prompt-Cookbook](https://github.com/VigoZhao/AI-Visual-Prompt-Cookbook) (MIT)
- Cinematography enums: [FilmGraph](https://github.com/gokaykucuk/filmgraph) (MIT)
- Remotion motion/transition implementations: see [remotion-templates](https://github.com/reactvideoeditor/remotion-templates)

## Flow

1. **Style Lock** → `style_bible.json` (visual only)
2. **Shot Lock** → `shot_list.json` (cinematography semantic + optional programmatic overrides)
3. Bot D maps `camera_movement` / `transition_to_next` via `cinematography_vocab.json` when programmatic fields are omitted
