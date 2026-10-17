# stolen-night-s45 motion 成片

Frame-driven camera/prop motion over locked illustrated stills (`../stills/01.jpg`…`08.jpg`).

## Render

```bash
python3 render_motion.py
```

Output: `../out/stolen_night_s45_motion.mp4` (45.00s · 1080×1920 · 24fps · h264 yuv420p · silent).
Manifest: `../assembly_manifest.json`.

Timebase is local frame index only (no `Date.now`). Hard cuts between shots; shot 8 fades to black in the last 0.8s.
