# Liquid Chrome (Motion Lab reproduction)
- `liquid_chrome.html`: spec-exact defaults (1080x1080, 60 fps, 6 s). `?t=` / `?frame=` freeze (no rAF). Preview-only flags: `?scale=`, `?steps=` (default 128), `?debug=sdf`.
- `render.py`: Playwright + SwiftShader, frames 0..359 -> `frames/` (gitignored), then ffmpeg.
  `../local-render/playwright/.venv/bin/python render.py` ; stills: `render.py times=0,1.2 out=/tmp/x`
- Render: full 1080, 60 fps, ~5.1 s/frame avg on box CPU (~31 min).

## Lab-loop log
1. Frames 132-288 (t 2.2-4.8): adjacent letters fused (P-U-S) because smooth-min k=0.1 also applied between finished glyphs -> per-glyph k = smK*(1-K^2), so formed letters union with hard min.
2. Frames 174-288: stair-step banding on letter side walls from 2048x512 SDF texel (1/512 u) vs normal eps 0.0008 -> normal eps 0.002.
3. Checked: chrome reads as mirror (not white plastic); glint (frames 198-246) crosses faces without erasing letters; droplets stay in frame; seam 359->0 mean abs diff 2.79/255 = same as neighbouring frame pairs (no pop).
## Interpretation notes
- "Cross-fade to real mesh 3.3-4.7 s": SDF->mesh fade-in 3.3-3.6, mesh fade-out 4.4-4.7 (slump at 4.8 is SDF-driven).
- Orbit: 7 deg * sin(2pi(t-3.85)/6), zero at hold centre. Droplet radius 0.215*sqrt(area/maxArea). Roughness 0.04 approximated by soft env-light edges (2.3 deg), not sampled.
- Jitter offsets index floor(frac(t*60)*4); at integer frames this is always offset 0.
