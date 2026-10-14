#!/usr/bin/env python3
"""
Frame 01 compositor v1 — recipe JSON + rembg alpha layers → still PNG.

Reads:
  projects/first-frame/recipes/v8_style_recipe.json
  projects/first-frame/assets/manifest.json
  projects/first-frame/assets/layers_alpha/*.png

Places each alpha layer at its manifest bbox, sorted by z_order.
Respects a few editable_params from the recipe (CLI overrides):
  --paw-lamp-intensity, --hide / --show layer ids, photo_bowtie draw.

Honesty (v2 gaps):
  - Default base is assets/base/base_plate_clean.jpg (characters/props erased
    via rembg matte + bbox blur-fill). Restacking rembg alphas should NOT
    double-expose. Residual: soft mush holes, lamp-glow smear, possible halos.
  - rembg mattes still bleed bedding/paws; not production cutouts.
  - No motion / glow_pulse animation yet (still frame only).
  - photo_bowtie is a tiny parametric Pillow shape, not a matted asset.
  - ear_bow / live_maine_chest_bowtie have no alpha assets yet.
  - --overlays-only still available for prop-only edits on a baked plate.

From repo root:
  python3 projects/first-frame/scripts/compose_from_recipe.py
  python3 projects/first-frame/scripts/compose_from_recipe.py \\
    --paw-lamp-intensity 1.3 --hide phone_back
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

REPO = Path(__file__).resolve().parents[3]
FF = REPO / "projects" / "first-frame"
DEFAULT_RECIPE = FF / "recipes" / "v8_style_recipe.json"
DEFAULT_MANIFEST = FF / "assets" / "manifest.json"
DEFAULT_OUT = FF / "code_assets" / "out" / "compose_v8_recipe_v2.png"

# Layers treated as "prop overlays" when --overlays-only
OVERLAY_IDS = {"paw_lamp", "phone_back", "wall_photo"}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_asset_path(manifest_dir: Path, rel: str) -> Path:
    """manifest paths are like assets/layers_alpha/foo.png relative to assets/ parent
    (i.e. projects/first-frame/)."""
    p = Path(rel)
    if p.is_absolute():
        return p
    # Try relative to FF (projects/first-frame)
    cand = FF / rel
    if cand.exists():
        return cand
    # Try relative to assets/
    cand2 = manifest_dir / rel
    if cand2.exists():
        return cand2
    # Try stripping leading assets/
    if rel.startswith("assets/"):
        cand3 = FF / rel
        return cand3
    return cand


def recipe_default_params(recipe: dict) -> dict:
    """Flatten editable_params defaults into a simple knobs dict."""
    ep = recipe.get("editable_params", {})
    knobs = {
        "paw_lamp_intensity": float(ep.get("paw_lamp_intensity", {}).get("default", 1.0)),
        "phone_back_visible": bool(
            ep.get("phone_back", {}).get("fields", {}).get("visible", {}).get("default", True)
        ),
        "ear_bow_visible": bool(
            ep.get("ear_bow", {}).get("fields", {}).get("visible", {}).get("default", True)
        ),
        "photo_bowtie_visible": bool(
            ep.get("photo_bowtie", {}).get("fields", {}).get("visible", {}).get("default", True)
        ),
        "photo_bowtie_color": ep.get("photo_bowtie", {})
        .get("fields", {})
        .get("color", {})
        .get("default", "#1A1210"),
        "live_maine_chest_bowtie_visible": bool(
            ep.get("live_maine_chest_bowtie", {})
            .get("fields", {})
            .get("visible", {})
            .get("default", False)
        ),
    }
    return knobs


def apply_intensity(rgba: Image.Image, intensity: float) -> Image.Image:
    """Brighten / dim an RGBA layer; also scale alpha slightly with intensity."""
    if abs(intensity - 1.0) < 1e-3:
        return rgba
    rgba = rgba.convert("RGBA")
    rgb = rgba.convert("RGB")
    # Enhance brightness; clamp factor to a sane range
    factor = max(0.3, min(2.0, intensity))
    rgb = ImageEnhance.Brightness(rgb).enhance(factor)
    r, g, b, a = (*rgb.split(), rgba.split()[-1])
    # Soften / strengthen matte with intensity
    a_factor = max(0.4, min(1.35, 0.55 + 0.45 * intensity))
    a = a.point(lambda p: int(max(0, min(255, p * a_factor))))
    out = Image.merge("RGBA", (r, g, b, a))
    return out


def draw_lamp_glow(
    canvas: Image.Image,
    origin_norm: tuple[float, float],
    intensity: float,
    color_hex: str = "#D09654",
) -> None:
    """Soft radial wash behind the paw lamp (multiply-ish via alpha paste)."""
    if intensity <= 0.01:
        return
    w, h = canvas.size
    ox = int(origin_norm[0] * w)
    oy = int(origin_norm[1] * h)
    radius = int(min(w, h) * 0.28 * max(0.5, intensity))
    glow = Image.new("RGBA", (radius * 2, radius * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    hex_c = color_hex.lstrip("#")
    cr, cg, cb = int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)
    # concentric discs, outer more transparent
    steps = 12
    base_alpha = int(40 * intensity)
    for i in range(steps, 0, -1):
        t = i / steps
        rr = int(radius * t)
        a = int(base_alpha * (1.0 - t) ** 1.4)
        draw.ellipse(
            (radius - rr, radius - rr, radius + rr, radius + rr),
            fill=(cr, cg, cb, a),
        )
    glow = glow.filter(ImageFilter.GaussianBlur(radius=max(4, radius // 8)))
    canvas.alpha_composite(glow, (ox - radius, oy - radius))


def draw_photo_bowtie(
    canvas: Image.Image,
    bbox: dict,
    color_hex: str = "#1A1210",
    scale: float = 1.0,
) -> None:
    """Tiny parametric black bowtie in wall-photo Maine chest ROI."""
    x, y, bw, bh = int(bbox["x"]), int(bbox["y"]), int(bbox["w"]), int(bbox["h"])
    cx = x + bw // 2
    cy = y + bh // 2
    tw = max(8, int(bw * 0.55 * scale))
    th = max(6, int(bh * 0.45 * scale))
    hex_c = color_hex.lstrip("#")
    fill = (int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16), 230)
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # left triangle, right triangle, center knot
    d.polygon(
        [(cx - tw, cy), (cx - 2, cy - th // 2), (cx - 2, cy + th // 2)],
        fill=fill,
    )
    d.polygon(
        [(cx + tw, cy), (cx + 2, cy - th // 2), (cx + 2, cy + th // 2)],
        fill=fill,
    )
    knot = max(3, tw // 8)
    d.ellipse((cx - knot, cy - knot, cx + knot, cy + knot), fill=fill)
    canvas.alpha_composite(layer)


def paste_layer(
    canvas: Image.Image,
    layer_rgba: Image.Image,
    bbox: dict,
    scale: float = 1.0,
) -> None:
    x, y = int(bbox["x"]), int(bbox["y"])
    target_w = max(1, int(bbox["w"] * scale))
    target_h = max(1, int(bbox["h"] * scale))
    layer = layer_rgba.convert("RGBA")
    if layer.size != (target_w, target_h):
        layer = layer.resize((target_w, target_h), Image.Resampling.LANCZOS)
    # Center if scale != 1
    if abs(scale - 1.0) > 1e-3:
        x = x + (int(bbox["w"]) - target_w) // 2
        y = y + (int(bbox["h"]) - target_h) // 2
    canvas.alpha_composite(layer, (x, y))


def compose(
    recipe: dict,
    manifest: dict,
    *,
    base_mode: str = "clean",
    overlays_only: bool = False,
    hide: set[str] | None = None,
    show: set[str] | None = None,
    knobs: dict | None = None,
) -> Image.Image:
    hide = hide or set()
    show = show or set()
    knobs = knobs or recipe_default_params(recipe)
    canvas_meta = manifest.get("canvas", {})
    W = int(canvas_meta.get("width", recipe.get("source_frame", {}).get("width", 1280)))
    H = int(canvas_meta.get("height", recipe.get("source_frame", {}).get("height", 720)))

    assets_by_id = {a["id"]: a for a in manifest.get("assets", [])}

    # --- base ---
    if base_mode == "none":
        canvas = Image.new("RGBA", (W, H), (8, 6, 5, 255))  # void_wall-ish
    elif base_mode == "v8":
        src = FF / "frame_01_s01_hero_v8.jpg"
        canvas = Image.open(src).convert("RGBA")
        if canvas.size != (W, H):
            canvas = canvas.resize((W, H), Image.Resampling.LANCZOS)
    elif base_mode == "v9":
        base_path = FF / "assets" / "base" / "base_plate_v9.jpg"
        if not base_path.exists():
            base_path = FF / "frame_01_s01_hero_v9.jpg"
        canvas = Image.open(base_path).convert("RGBA")
        if canvas.size != (W, H):
            canvas = canvas.resize((W, H), Image.Resampling.LANCZOS)
    else:  # clean (default)
        base_asset = assets_by_id.get("base_plate")
        if base_asset and base_asset.get("path"):
            base_path = resolve_asset_path(FF / "assets", base_asset["path"])
        else:
            base_path = FF / "assets" / "base" / "base_plate_clean.jpg"
        if not base_path.exists():
            # fallback chain
            for cand in (
                FF / "assets" / "base" / "base_plate_clean.jpg",
                FF / "assets" / "base" / "base_plate_v9.jpg",
                FF / "frame_01_s01_hero_v8.jpg",
            ):
                if cand.exists():
                    base_path = cand
                    break
        canvas = Image.open(base_path).convert("RGBA")
        if canvas.size != (W, H):
            canvas = canvas.resize((W, H), Image.Resampling.LANCZOS)

    # Soft lamp glow under overlays (from recipe lighting)
    lighting = recipe.get("lighting", {}).get("key", {})
    origin = tuple(lighting.get("origin_norm", [0.88, 0.42]))
    glow_color = lighting.get("color", "#D09654")
    intensity = float(knobs["paw_lamp_intensity"])
    if "paw_lamp" not in hide:
        draw_lamp_glow(canvas, origin, intensity, glow_color)

    # --- stack alpha layers by z_order ---
    stackable = []
    for asset in manifest.get("assets", []):
        aid = asset["id"]
        if aid == "base_plate":
            continue
        if overlays_only and aid not in OVERLAY_IDS:
            continue
        alpha_rel = asset.get("alpha_path")
        if not alpha_rel:
            continue  # no rembg matte yet
        # visibility
        visible = True
        if aid in hide:
            visible = False
        if aid in show:
            visible = True
        # recipe knobs
        if aid == "phone_back" and not knobs.get("phone_back_visible", True):
            visible = False
        if aid == "paw_lamp" and intensity <= 0.01:
            visible = False
        if not visible:
            continue
        stackable.append(asset)

    stackable.sort(key=lambda a: (a.get("z_order", 0), a["id"]))

    for asset in stackable:
        aid = asset["id"]
        alpha_path = resolve_asset_path(FF / "assets", asset["alpha_path"])
        if not alpha_path.exists():
            print(f"[warn] missing alpha: {alpha_path}", flush=True)
            continue
        layer = Image.open(alpha_path).convert("RGBA")
        if aid == "paw_lamp":
            layer = apply_intensity(layer, intensity)
        paste_layer(canvas, layer, asset["bbox"], scale=1.0)

    # Parametric photo bowtie (no alpha asset)
    if knobs.get("photo_bowtie_visible", True) and "photo_bowtie_black" not in hide:
        bt = assets_by_id.get("photo_bowtie_black")
        if bt:
            draw_photo_bowtie(
                canvas,
                bt["bbox"],
                color_hex=knobs.get("photo_bowtie_color", "#1A1210"),
            )

    # live_maine_chest_bowtie default false — intentionally no draw
    if knobs.get("live_maine_chest_bowtie_visible", False):
        print(
            "[warn] live_maine_chest_bowtie.visible=true but no asset/drawer yet; skipped",
            flush=True,
        )

    return canvas


def main() -> None:
    ap = argparse.ArgumentParser(description="Compose Frame 01 still from recipe + rembg alphas")
    ap.add_argument("--recipe", type=Path, default=DEFAULT_RECIPE)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument(
        "--base",
        choices=["clean", "v9", "v8", "none"],
        default="clean",
        help="Canvas base: clean plate (default), baked v9/v8, or dark void",
    )
    ap.add_argument(
        "--overlays-only",
        action="store_true",
        help="Paste only paw_lamp / phone_back / wall_photo (prop edits; skip character alphas)",
    )
    ap.add_argument(
        "--paw-lamp-intensity",
        type=float,
        default=None,
        help="Override recipe editable_params.paw_lamp_intensity (default 1.0)",
    )
    ap.add_argument(
        "--hide",
        nargs="*",
        default=[],
        help="Layer ids to hide (e.g. phone_back paw_lamp live_maine_coon)",
    )
    ap.add_argument(
        "--show",
        nargs="*",
        default=[],
        help="Force-show layer ids (overrides --hide for those ids)",
    )
    ap.add_argument(
        "--no-photo-bowtie",
        action="store_true",
        help="Skip parametric wall-photo black bowtie",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Output PNG path",
    )
    args = ap.parse_args()

    recipe = load_json(args.recipe)
    manifest = load_json(args.manifest)
    knobs = recipe_default_params(recipe)
    if args.paw_lamp_intensity is not None:
        knobs["paw_lamp_intensity"] = float(args.paw_lamp_intensity)
    if args.no_photo_bowtie:
        knobs["photo_bowtie_visible"] = False

    canvas = compose(
        recipe,
        manifest,
        base_mode=args.base,
        overlays_only=args.overlays_only,
        hide=set(args.hide or []),
        show=set(args.show or []),
        knobs=knobs,
    )

    out = args.out
    if not out.is_absolute():
        out = REPO / out
    out.parent.mkdir(parents=True, exist_ok=True)
    # Save as PNG (RGB if fully opaque base preferred for sharing)
    canvas.convert("RGBA").save(out, "PNG", optimize=True)
    print(f"wrote {out.relative_to(REPO)}  ({canvas.size[0]}x{canvas.size[1]})")
    print(
        f"base={args.base} overlays_only={args.overlays_only} "
        f"paw_lamp_intensity={knobs['paw_lamp_intensity']} "
        f"hide={sorted(args.hide or [])}"
    )


if __name__ == "__main__":
    main()
