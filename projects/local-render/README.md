# Local render demos (token-saving)

Two **local** paths that produce a short MP4 without cloud LLM tokens.

| Path | Stack | Best when |
|------|--------|-----------|
| **A** Remotion | Node + Remotion 4 + bundled Chromium | Already on Remotion / React timeline |
| **B** Playwright | `uv` + Playwright Chromium + system FFmpeg | Plain HTML/Canvas, no Remotion deps |

Both demos are intentionally tiny (3s, 640×360, bouncing circle). They are **not** wired to `projects/first-frame/rig`.

---

## Prerequisites

### Linux (this box / most servers)

- Node.js 18+ (demo verified on Node 20)
- `ffmpeg` on `PATH` (path B; Remotion also uses FFmpeg/Chromium via its own install)
- Path B: [`uv`](https://github.com/astral-sh/uv)

```bash
node -v && npm -v
ffmpeg -version | head -1
uv --version
```

### Windows (PowerShell notes)

- Install Node from [nodejs.org](https://nodejs.org/) or `winget install OpenJS.NodeJS.LTS`
- Install FFmpeg: `winget install Gyan.FFmpeg` (or Chocolatey), then open a **new** shell so `ffmpeg` is on `PATH`
- Install uv: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
- Paths below use forward slashes; on Windows you can `cd` the same relative paths from the repo root
- If Playwright Chromium download fails behind a corporate proxy, set `HTTPS_PROXY` / `HTTP_PROXY` before `playwright install`

---

## Path A — Remotion

```bash
cd projects/local-render/remotion
npm install
npm run render
# → out/demo.mp4
```

Optional studio (preview UI):

```bash
npm run studio
```

Composition: `src/Demo.tsx`, id `Demo`, 90 frames @ 30fps.

---

## Path B — uv + Playwright + FFmpeg

```bash
cd projects/local-render/playwright
uv sync
uv run playwright install chromium
uv run python render.py
# → out/demo.mp4
```

Options:

```bash
uv run python render.py --out out/custom.mp4 --frames 60 --fps 30
```

Scene: `scene.html` (`window.renderFrame(n)`). Encoder: system `ffmpeg` → H.264 `yuv420p`.

---

## Efficiency cheat sheet

| | Remotion (A) | Playwright (B) |
|--|--------------|----------------|
| Generate | Official headless pipeline; often faster for React timelines | Self-managed screenshot loop; fine for short demos |
| Edit | Props / studio / same composition | Edit HTML/JS, re-run capture |
| Finish | Timeline, audio, transitions built-in | DIY with FFmpeg for audio/edit |

For this repo’s Remotion-leaning plan, prefer **A** day-to-day; keep **B** when you only have a static HTML/canvas scene.

---

## Layout

```
projects/local-render/
  README.md                 ← this file
  remotion/                 ← Path A
    package.json
    remotion.config.ts
    src/{index.ts,Root.tsx,Demo.tsx}
    out/demo.mp4            ← gitignored
  playwright/               ← Path B
    pyproject.toml
    scene.html
    render.py
    out/demo.mp4            ← gitignored
    frames/                 ← gitignored temp PNGs
```
