"""Load Style Bible palette / line notes into render constants."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Repo root: .../animation-pipeline
REPO_ROOT = Path(__file__).resolve().parents[4]
BIBLE_PATH = (
    REPO_ROOT
    / "styles"
    / "rough-animation-pet-sketch-storyboard-style"
    / "style_bible.json"
)


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def load_bible(path: Path | None = None) -> dict[str, Any]:
    p = path or BIBLE_PATH
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def palette_from_bible(bible: dict[str, Any] | None = None) -> dict[str, tuple[int, int, int]]:
    """Map Style Bible names → RGB tuples used by the Cavalier renderer."""
    b = bible or load_bible()
    pal = b["palette"]
    named: dict[str, tuple[int, int, int]] = {}
    for bucket in ("primary", "accent"):
        for swatch in pal.get(bucket, []):
            named[swatch["name"]] = _hex_to_rgb(swatch["hex"])
    bg = pal.get("background")
    if bg:
        named[bg["name"]] = _hex_to_rgb(bg["hex"])
        named["paper"] = named[bg["name"]]

    # Character fill aliases (not in bible as named fur, derived from warm primaries + accents)
    named.setdefault("warm_beige", named.get("paper", (232, 220, 200)))
    named["fur_cream"] = named.get("cream", (245, 237, 224))
    named["fur_chestnut"] = named.get("red_brown_pencil", (139, 69, 19))
    named["fur_chestnut_wash"] = (180, 110, 70)  # lighter wash of chestnut
    named["construction"] = named.get("red_brown_pencil", (139, 69, 19))
    named["contour"] = named.get("dark_burgundy_ink", (74, 21, 37))
    named["ink_near_black"] = named.get("nearly_black_brown", (43, 26, 20))
    named["blush"] = named.get("peach_blush", (232, 180, 168))
    named["tongue"] = (220, 120, 130)
    named["bow_pink"] = (232, 150, 170)  # soft sketch pink; avoid forbidden gloss plastic neon
    named["bow_pink_dark"] = (190, 100, 120)
    named["phone_body"] = (55, 52, 50)
    named["phone_lens"] = (30, 28, 28)
    named["eye_white"] = (250, 245, 235)
    return named


# Bible → code param mapping (documented for README)
BIBLE_TO_CODE = {
    "palette.background / warm_beige": "paper fill + grain",
    "palette.accent.red_brown_pencil": "construction lines (layer 1)",
    "palette.accent.dark_burgundy_ink": "scratchy contour passes (layer 3)",
    "palette.primary cream / soft_tan / pale_peach": "watercolor fur washes (layer 2)",
    "line.style=sketchy + variable weight": "jittered polylines, multi-pass offset",
    "texture.paper + grain=medium": "noise on paper + wash alpha < 1",
    "character_lock huge oval eyes tiny pupils": "draw_eyes()",
    "composition.layer_order": "paper → construction → wash → contour → face → props",
}
