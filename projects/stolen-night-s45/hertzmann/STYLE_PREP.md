# Style prep for s05 Hertzmann remake

## Goal
Borrow **painterly warmth and micro-texture** from `stills_src/style_ref_ghibli.jpg`
without turning the bedroom into a daylight forest. Keep 《偷来的夜》 dual lighting:
warm amber lamp + cool phone-screen blue.

## What we do NOT do
- No neural style transfer / AdaIN spatial warp of the Ghibli girl/vine/forest.
- No global mean-L lift toward sunny outdoor Lab stats.
- No palette replacement that kills the cool face/mask glow.

## Method (`style_prep` in `paint_frame.py`)
1. **Cool-glow mask** from content: high Lab L + bluer Lab b*, plus bright white mask;
   Gaussian-softened. Used as protect/restore weight.
2. **Warm-masked Lab match**: on `1 - cool`, partially match A/B toward style means
   (~35% mean pull) and gently blend L std for softer fills. L mean stays night-like
   (no sunny lift).
3. **Desaturated style high-pass** at ~12% opacity on warm regions only — grain/brush
   energy without importing green foliage color.
4. **Mild unsharp** for edge energy before stroke painting.
5. **Cool restore**: re-mix original content into cool-mask regions so phone blue and
   mask brightness survive priming.

## Then
Hertzmann layered strokes paint the primed frame; ink outlines from dark ridges;
`strokes.npz` saved for later animation.
