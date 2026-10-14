# Local video render (token-saving)

See the full install / render guide:

**[`projects/local-render/README.md`](../projects/local-render/README.md)**

Quick start:

```bash
# A — Remotion
cd projects/local-render/remotion && npm install && npm run render

# B — Playwright + FFmpeg
cd projects/local-render/playwright && uv sync && uv run playwright install chromium && uv run python render.py
```

Outputs: `projects/local-render/remotion/out/demo.mp4` and `projects/local-render/playwright/out/demo.mp4`.
