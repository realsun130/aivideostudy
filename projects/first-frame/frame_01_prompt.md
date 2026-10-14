# Frame 01 — Assembled Image Prompt

- `frame_id`: `s01_hero`
- `project_id`: `test_1st`
- Style Bible: `styles/rough-animation-pet-sketch-storyboard-style/style_bible.json` (v2026-10-13.2)
- Aspect: **9:16** · Shot: **MCU** · Angle: **eye-level**
- Source fill: local MD `FRAME_01_TEMPLATE.md` (unpushed commit `6b11b28` at repo root on laptop). Canonical `projects/first-frame/frame_01.fill.json` on GitHub was still empty; JSON variables below are reconstructed from the MD.
- Note: `PRODUCT_OR_PROP` was blank in the MD; prompt uses the **phone** from `SUBJECT_ACTION` as the comic prop.

## Positive (paste to image model)

```text
Create a 9:16 vertical image in the "Rough Animation Pet Sketch Storyboard" style.

Subject: an original anthropomorphic Cavalier King Charles Spaniel and an original anthropomorphic blue-tabby Maine Coon cat.
Subject action: both pets lounging side-by-side on a bed; the spaniel is glued to a smartphone scrolling short videos and laughing hard; the Maine Coon stays completely indifferent / deadpan.
Product or prop: a smartphone showing a short-video feed (the comic prop that explains the beat).
Location: on a bedroom bed.
Background elements: lightly sketched bedroom: wall, a framed wedding-style photo of the two pets, nightstand, a small cat-paw-shaped night light, dim warm night-light glow.
Main text: (none).
Secondary text: (none).
Accent symbol: optional tiny motion ticks near the laughing spaniel and phone glow; keep sparse.
Wardrobe or visual styling: none (no collar/scarf).

Composition: medium close-up (MCU), eye-level camera, both characters equally staged in frame. Extreme emotional character: the Cavalier laughing hard. Deadpan / indifferent reaction character: the Maine Coon.

Use the reference only as a style reference, not as a scene to copy. Preserve the visual language: warm beige paper (#E8DCC8), loose red-brown construction lines (#8B4513), scratchy dark burgundy contour strokes (#4A1525), semi-transparent watercolor-like color wash, rough animation storyboard finish, lightly sketched interior background, exaggerated original pet expressions, huge oval eyes, tiny pupils, visible correction strokes, and one clear comic prop-driven beat (the phone).

Stage the scene like an animation story artist frame. Keep the spaniel in an extreme laughing pose and the Maine Coon in a contrasting deadpan or unimpressed reaction. Make the foreground smartphone explain the joke. Leave sketch marks, motion ticks, rough shadows, and unfinished room lines visible. Soft diffused warm indoor night-light mood — not cinematic hard light. Do not include platform UI, watermarks, creator IDs, logos, QR codes, app buttons, readable TikTok/Douyin chrome, or franchise characters.
```

## Negative (paste)

```text
watermark, username, platform logo, app UI, button overlay, QR code, creator signature, brand logo, exact reference characters, copied franchise character, polished vector art, clean corporate mascot, 3D render, photorealistic pet photo, airbrushed fur, hyperreal lighting, glossy toy look, anime cel shading, dense readable signage, perfect typography, cold neon palette, dark horror mood, violent scene, flat empty background, overfinished lineart, readable social-app interface text
```

## Chinese scene summary

```text
【中文场景摘要 · 可对照】
项目：test_1st / 帧：s01_hero / 画幅：9:16 / 景别：MCU / 机位：平视
主体：一只查理王骑士小猎犬和一只蓝虎斑缅因猫
动作：两只动物拟人化趴在床上，查理王玩手机（刷抖音），大笑，缅因猫无动于衷
道具：手机（刷抖音）（MD 未填 PRODUCT，从动作推断）
地点：卧室床上
背景：墙面、挂画（两只动物结婚照合影），床头柜，小猫爪形状夜灯，晚上昏暗的夜灯灯光
配饰：无
极端表情：查理王（大笑）｜面瘫反应：缅因猫｜前后：同等
```

## Reconstructed fill snapshot (for reference; not committed as overwrite)

```json
{
  "frame_id": "s01_hero",
  "project_id": "test_1st",
  "aspect_ratio": "9:16",
  "duration_sec_hint": null,
  "variables": {
    "SUBJECT": "一只查理王骑士小猎犬和一只蓝虎斑缅因猫",
    "SUBJECT_ACTION": "两只动物拟人化趴在床上，查理王玩手机（刷抖音），大笑，缅因猫无动于衷",
    "PRODUCT_OR_PROP": "手机（刷抖音）",
    "LOCATION": "卧室床上",
    "BACKGROUND_ELEMENTS": "墙面、挂画（两只动物结婚照合影），床头柜，小猫爪形状夜灯，晚上昏暗的夜灯灯光",
    "MAIN_TEXT": "",
    "SECONDARY_TEXT": "",
    "ACCENT_SYMBOL": "",
    "WARDROBE_STYLE": "无",
    "ASPECT_RATIO": "9:16"
  },
  "composition": {
    "shot_size": "MCU",
    "camera_angle": "eye-level",
    "extreme_expression_character": "查理王（大笑）",
    "deadpan_reaction_character": "缅因猫",
    "who_in_front": "同等"
  },
  "style_bible_ref": "styles/rough-animation-pet-sketch-storyboard-style/style_bible.json",
  "style_bible_ver": "2026-10-13.2",
  "notes_for_me": "Source of truth: local unpushed MD at D:\\aivideotest\\grokbot_github\\aivideostudy\\FRAME_01_TEMPLATE.md (commit 6b11b28 '1st' at repo root, not pushed). frame_01.fill.json was empty; PRODUCT_OR_PROP inferred from action (phone)."
}
```
