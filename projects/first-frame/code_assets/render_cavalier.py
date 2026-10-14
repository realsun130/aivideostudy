#!/usr/bin/env python3
"""Procedural Cavalier King Charles Spaniel — Style Bible sketch (no image-model).

Inspired by huashu-art-motion: style recipe → parametric draw → deterministic re-render.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.sketch_draw import (  # noqa: E402
    construction_ellipse,
    draw_stress_marks,
    make_paper,
    scratchy_ellipse,
    scratchy_polyline,
    watercolor_ellipse,
    watercolor_polygon,
    wavy_ear_outline,
)
from lib.style_params import BIBLE_PATH, load_bible, palette_from_bible  # noqa: E402


ASPECTS = {
    "1:1": (1024, 1024),
    "9:16": (720, 1280),
    "16:9": (1280, 720),
}


def _parse_size(size: str | None, aspect: str) -> tuple[int, int]:
    if size:
        w, h = size.lower().split("x")
        return int(w), int(h)
    return ASPECTS.get(aspect, ASPECTS["1:1"])


def _layout(w: int, h: int) -> dict[str, float]:
    """Normalized layout anchors (character-centric MCU-ish)."""
    cx, cy = w * 0.50, h * 0.46
    scale = min(w, h) / 1024.0
    return {
        "cx": cx,
        "cy": cy,
        "s": scale,
        "head_rx": 210 * scale,
        "head_ry": 200 * scale,
        "body_rx": 260 * scale,
        "body_ry": 200 * scale,
        "body_cy": cy + 210 * scale,
    }


def draw_phone_back(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    colors: dict,
    cx: float,
    cy: float,
    scale: float,
    seed: int = 90,
) -> None:
    """Phone BACK facing camera; dual camera bump toward top (bedhead / up)."""
    pw, ph = 95 * scale, 170 * scale
    left, top = cx - pw / 2, cy - ph / 2
    right, bottom = cx + pw / 2, cy + ph / 2
    # Soft glow wash (screen bleed from edges — optional comic prop light)
    watercolor_ellipse(
        canvas,
        (left - 30 * scale, top - 20 * scale, right + 30 * scale, bottom + 40 * scale),
        (240, 230, 210),
        alpha=50,
        blur=12 * scale,
    )
    body = [
        (left + 8 * scale, top),
        (right - 8 * scale, top),
        (right, top + 12 * scale),
        (right, bottom - 12 * scale),
        (right - 8 * scale, bottom),
        (left + 8 * scale, bottom),
        (left, bottom - 12 * scale),
        (left, top + 12 * scale),
    ]
    watercolor_polygon(canvas, body, colors["phone_body"], alpha=200, blur=1.5)
    # Contour
    scratchy_polyline(
        draw,
        body + [body[0]],
        colors["contour"],
        width=max(2, int(2.5 * scale)),
        passes=2,
        jitter=1.2 * scale,
        seed=seed,
    )
    # Camera bump — TOP of phone (orientation lock)
    bump_w, bump_h = 48 * scale, 48 * scale
    bx0 = cx - bump_w / 2
    by0 = top + 14 * scale
    bx1, by1 = bx0 + bump_w, by0 + bump_h
    watercolor_ellipse(
        canvas, (bx0, by0, bx1, by1), (40, 38, 36), alpha=220, blur=1.0
    )
    scratchy_ellipse(
        draw,
        (bx0, by0, bx1, by1),
        colors["contour"],
        width=max(1, int(1.5 * scale)),
        passes=2,
        jitter=0.8 * scale,
        seed=seed + 1,
    )
    # Two lenses + flash
    for i, (lx, ly) in enumerate(
        [
            (bx0 + bump_w * 0.32, by0 + bump_h * 0.35),
            (bx0 + bump_w * 0.68, by0 + bump_h * 0.35),
            (bx0 + bump_w * 0.50, by0 + bump_h * 0.72),
        ]
    ):
        r = (7 if i < 2 else 4) * scale
        draw.ellipse(
            (lx - r, ly - r, lx + r, ly + r),
            fill=(*colors["phone_lens"], 240),
            outline=(*colors["contour"], 200),
            width=1,
        )


def draw_ear_bow(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    colors: dict,
    root_x: float,
    root_y: float,
    scale: float,
    seed: int = 50,
) -> None:
    """Small pink four-loop bow at right-ear root (viewer LEFT)."""
    s = scale
    loops = [
        (-22 * s, -6 * s, 16 * s, 12 * s),
        (6 * s, -8 * s, 16 * s, 12 * s),
        (-18 * s, 8 * s, 14 * s, 11 * s),
        (4 * s, 10 * s, 14 * s, 11 * s),
    ]
    for i, (ox, oy, rw, rh) in enumerate(loops):
        bbox = (root_x + ox, root_y + oy, root_x + ox + rw, root_y + oy + rh)
        watercolor_ellipse(canvas, bbox, colors["bow_pink"], alpha=170, blur=1.5)
        scratchy_ellipse(
            draw,
            bbox,
            colors["bow_pink_dark"],
            width=max(1, int(1.5 * s)),
            passes=2,
            jitter=0.9 * s,
            seed=seed + i,
        )
    # Center knot
    kx, ky = root_x - 2 * s, root_y + 4 * s
    watercolor_ellipse(
        canvas,
        (kx - 6 * s, ky - 5 * s, kx + 6 * s, ky + 5 * s),
        colors["bow_pink_dark"],
        alpha=200,
        blur=1.0,
    )


def draw_face(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    colors: dict,
    cx: float,
    cy: float,
    scale: float,
    expression: str,
    seed: int,
) -> None:
    s = scale
    # Blush
    watercolor_ellipse(
        canvas,
        (cx - 120 * s, cy + 10 * s, cx - 50 * s, cy + 55 * s),
        colors["blush"],
        alpha=70,
        blur=8 * s,
    )
    watercolor_ellipse(
        canvas,
        (cx + 50 * s, cy + 10 * s, cx + 120 * s, cy + 55 * s),
        colors["blush"],
        alpha=70,
        blur=8 * s,
    )

    # Eyes — huge ovals, tiny pupils (Style Bible character_lock)
    eye_rx, eye_ry = 48 * s, 58 * s
    eye_y = cy - 25 * s
    eyes = [
        (cx - 78 * s, eye_y),  # left eye (viewer left)
        (cx + 78 * s, eye_y),
    ]
    for i, (ex, ey) in enumerate(eyes):
        bbox = (ex - eye_rx, ey - eye_ry, ex + eye_rx, ey + eye_ry)
        watercolor_ellipse(canvas, bbox, colors["eye_white"], alpha=230, blur=1.0)
        # Soft chestnut lid wash
        watercolor_ellipse(
            canvas,
            (ex - eye_rx, ey - eye_ry, ex + eye_rx, ey - eye_ry * 0.1),
            colors["fur_chestnut_wash"],
            alpha=80,
            blur=3 * s,
        )
        scratchy_ellipse(
            draw,
            bbox,
            colors["contour"],
            width=max(2, int(2.5 * s)),
            passes=3,
            jitter=1.5 * s,
            seed=seed + 10 + i,
        )
        # Tiny pupil
        pr = 7 * s
        # Look slightly toward phone / down-center when laughing
        px = ex + (4 * s if i == 0 else -4 * s)
        py = ey + (6 * s if expression == "laughing" else 0)
        draw.ellipse(
            (px - pr, py - pr, px + pr, py + pr),
            fill=(*colors["ink_near_black"], 255),
        )
        # Spec catch
        draw.ellipse(
            (px - pr * 0.35, py - pr * 0.55, px - pr * 0.05, py - pr * 0.2),
            fill=(255, 250, 240, 200),
        )
        if expression == "laughing":
            # Squint tick under eye
            scratchy_polyline(
                draw,
                [
                    (ex - eye_rx * 0.7, ey + eye_ry * 0.85),
                    (ex, ey + eye_ry * 1.05),
                    (ex + eye_rx * 0.7, ey + eye_ry * 0.85),
                ],
                colors["contour"],
                width=max(1, int(2 * s)),
                passes=2,
                jitter=1.0 * s,
                seed=seed + 20 + i,
            )

    # Muzzle cream disc (Cavalier white blaze / muzzle)
    watercolor_ellipse(
        canvas,
        (cx - 70 * s, cy + 20 * s, cx + 70 * s, cy + 110 * s),
        colors["fur_cream"],
        alpha=150,
        blur=5 * s,
    )

    # Nose
    nx, ny = cx, cy + 55 * s
    nose = [
        (nx - 22 * s, ny - 8 * s),
        (nx + 22 * s, ny - 8 * s),
        (nx + 18 * s, ny + 16 * s),
        (nx, ny + 22 * s),
        (nx - 18 * s, ny + 16 * s),
    ]
    watercolor_polygon(canvas, nose, colors["ink_near_black"], alpha=235, blur=1.0)
    scratchy_polyline(
        draw,
        nose + [nose[0]],
        colors["contour"],
        width=max(1, int(2 * s)),
        passes=2,
        jitter=1.0 * s,
        seed=seed + 30,
    )

    # Mouth
    my = cy + 95 * s
    if expression == "laughing":
        # Wide open laugh
        mouth = [
            (cx - 70 * s, my - 10 * s),
            (cx - 40 * s, my + 35 * s),
            (cx, my + 48 * s),
            (cx + 40 * s, my + 35 * s),
            (cx + 70 * s, my - 10 * s),
            (cx + 35 * s, my - 22 * s),
            (cx, my - 18 * s),
            (cx - 35 * s, my - 22 * s),
        ]
        watercolor_polygon(canvas, mouth, colors["ink_near_black"], alpha=230, blur=1.5)
        # Tongue
        tongue = [
            (cx - 22 * s, my + 8 * s),
            (cx + 22 * s, my + 8 * s),
            (cx + 18 * s, my + 40 * s),
            (cx, my + 48 * s),
            (cx - 18 * s, my + 40 * s),
        ]
        watercolor_polygon(canvas, tongue, colors["tongue"], alpha=210, blur=2.0)
        scratchy_polyline(
            draw,
            mouth + [mouth[0]],
            colors["contour"],
            width=max(2, int(2.5 * s)),
            passes=3,
            jitter=1.4 * s,
            seed=seed + 40,
        )
        draw_stress_marks(
            draw,
            (cx + 110 * s, cy - 40 * s),
            colors["construction"],
            count=5,
            seed=seed + 41,
        )
        draw_stress_marks(
            draw,
            (cx - 110 * s, cy - 40 * s),
            colors["construction"],
            count=4,
            seed=seed + 42,
        )
    elif expression == "neutral":
        scratchy_polyline(
            draw,
            [
                (cx - 40 * s, my),
                (cx - 10 * s, my + 8 * s),
                (cx + 10 * s, my + 8 * s),
                (cx + 40 * s, my),
            ],
            colors["contour"],
            width=max(2, int(2.5 * s)),
            passes=2,
            jitter=1.2 * s,
            seed=seed + 40,
        )
    else:  # deadpan / mild smile
        scratchy_polyline(
            draw,
            [
                (cx - 35 * s, my + 5 * s),
                (cx, my + 12 * s),
                (cx + 35 * s, my + 5 * s),
            ],
            colors["contour"],
            width=max(2, int(2 * s)),
            passes=2,
            jitter=1.0 * s,
            seed=seed + 40,
        )


def draw_cavalier(
    width: int,
    height: int,
    *,
    expression: str = "laughing",
    show_phone: bool = True,
    show_ear_bow: bool = True,
    seed: int = 42,
) -> Image.Image:
    bible = load_bible()
    colors = palette_from_bible(bible)
    canvas = make_paper(width, height, colors["paper"], grain=0.07, seed=seed)
    draw = ImageDraw.Draw(canvas, "RGBA")
    L = _layout(width, height)
    cx, cy, s = L["cx"], L["cy"], L["s"]

    # --- Layer order mirrors Style Bible composition.layer_order ---
    # 1) Thin red-brown construction
    head_bbox = (
        cx - L["head_rx"],
        cy - L["head_ry"],
        cx + L["head_rx"],
        cy + L["head_ry"],
    )
    body_bbox = (
        cx - L["body_rx"],
        L["body_cy"] - L["body_ry"],
        cx + L["body_rx"],
        L["body_cy"] + L["body_ry"],
    )
    construction_ellipse(draw, head_bbox, colors["construction"], width=max(1, int(1.5 * s)))
    construction_ellipse(draw, body_bbox, colors["construction"], width=max(1, int(1.5 * s)))
    # Guide crosses
    scratchy_polyline(
        draw,
        [(cx - L["head_rx"] * 0.9, cy), (cx + L["head_rx"] * 0.9, cy)],
        colors["construction"],
        width=1,
        passes=1,
        jitter=0.5,
        seed=seed + 1,
        alpha=100,
    )

    # 2) Loose watercolor fur washes
    watercolor_ellipse(canvas, body_bbox, colors["fur_cream"], alpha=130, blur=10 * s)
    watercolor_ellipse(canvas, head_bbox, colors["fur_cream"], alpha=140, blur=8 * s)
    # Blenheim chestnut patches (ears + eye patches + back)
    for bbox, a in [
        (
            (cx - 200 * s, cy - 160 * s, cx - 40 * s, cy + 40 * s),
            120,
        ),  # left ear/cheek
        (
            (cx + 40 * s, cy - 160 * s, cx + 200 * s, cy + 40 * s),
            120,
        ),  # right
        (
            (cx - 90 * s, cy - 90 * s, cx - 20 * s, cy - 10 * s),
            90,
        ),  # eye patch L
        (
            (cx + 20 * s, cy - 90 * s, cx + 90 * s, cy - 10 * s),
            90,
        ),
        (
            (cx - 160 * s, L["body_cy"] - 120 * s, cx + 160 * s, L["body_cy"] + 80 * s),
            100,
        ),
    ]:
        watercolor_ellipse(canvas, bbox, colors["fur_chestnut_wash"], alpha=a, blur=7 * s)

    # Ears as wavy lobes
    left_ear = wavy_ear_outline(
        (cx - 195 * s, cy + 40 * s),
        (cx - 120 * s, cy - 90 * s),
        bulge=55 * s,
        side="left",
    )
    right_ear = wavy_ear_outline(
        (cx + 195 * s, cy + 40 * s),
        (cx + 120 * s, cy - 90 * s),
        bulge=55 * s,
        side="right",
    )
    watercolor_polygon(canvas, left_ear, colors["fur_chestnut_wash"], alpha=150, blur=4 * s)
    watercolor_polygon(canvas, right_ear, colors["fur_chestnut_wash"], alpha=150, blur=4 * s)

    # 3) Scratchy burgundy contours
    scratchy_ellipse(
        draw,
        head_bbox,
        colors["contour"],
        width=max(2, int(3 * s)),
        passes=3,
        jitter=2.2 * s,
        seed=seed + 2,
    )
    scratchy_ellipse(
        draw,
        body_bbox,
        colors["contour"],
        width=max(2, int(2.5 * s)),
        passes=2,
        jitter=2.0 * s,
        seed=seed + 3,
    )
    scratchy_polyline(
        draw,
        left_ear + [left_ear[0]],
        colors["contour"],
        width=max(2, int(2.5 * s)),
        passes=3,
        jitter=2.0 * s,
        seed=seed + 4,
    )
    scratchy_polyline(
        draw,
        right_ear + [right_ear[0]],
        colors["contour"],
        width=max(2, int(2.5 * s)),
        passes=3,
        jitter=2.0 * s,
        seed=seed + 5,
    )
    # Chest fur ticks
    for i, xoff in enumerate([-80, -40, 0, 40, 80]):
        scratchy_polyline(
            draw,
            [
                (cx + xoff * s, L["body_cy"] - 40 * s),
                (cx + xoff * s + 8 * s, L["body_cy"] + 30 * s),
            ],
            colors["construction"],
            width=1,
            passes=1,
            jitter=1.5 * s,
            seed=seed + 60 + i,
            alpha=120,
        )

    # Paws holding phone (simplified mittens)
    paw_y = L["body_cy"] + 20 * s
    for i, px in enumerate([cx - 70 * s, cx + 70 * s]):
        pb = (px - 35 * s, paw_y - 25 * s, px + 35 * s, paw_y + 40 * s)
        watercolor_ellipse(canvas, pb, colors["fur_cream"], alpha=160, blur=3 * s)
        scratchy_ellipse(
            draw,
            pb,
            colors["contour"],
            width=max(2, int(2 * s)),
            passes=2,
            jitter=1.5 * s,
            seed=seed + 70 + i,
        )

    # Props
    if show_phone:
        draw_phone_back(
            canvas,
            draw,
            colors,
            cx=cx,
            cy=paw_y + 10 * s,
            scale=s,
            seed=seed + 90,
        )

    # Face on top of most body
    draw_face(canvas, draw, colors, cx, cy, s, expression, seed)

    # Ear bow — right ear root = animal's right = viewer LEFT
    if show_ear_bow:
        draw_ear_bow(
            canvas,
            draw,
            colors,
            root_x=cx - 125 * s,
            root_y=cy - 95 * s,
            scale=s,
            seed=seed + 50,
        )

    # Foreground rough shadow under body
    watercolor_ellipse(
        canvas,
        (
            cx - 200 * s,
            height - 80 * s,
            cx + 200 * s,
            height - 20 * s,
        ),
        colors["ink_near_black"],
        alpha=40,
        blur=15 * s,
    )

    return canvas.convert("RGB")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Code-draw Cavalier (Style Bible sketch) — deterministic, no image model."
    )
    parser.add_argument(
        "--expression",
        choices=("laughing", "neutral", "smile"),
        default="laughing",
        help="Facial expression preset",
    )
    parser.add_argument(
        "--show-phone",
        dest="show_phone",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Draw phone BACK facing camera (default: on)",
    )
    parser.add_argument(
        "--show-ear-bow",
        dest="show_ear_bow",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Pink bow on right-ear root / viewer left (default: on)",
    )
    parser.add_argument(
        "--aspect",
        choices=tuple(ASPECTS.keys()),
        default="1:1",
        help="Canvas aspect preset",
    )
    parser.add_argument(
        "--size",
        default=None,
        help="Override WxH, e.g. 1024x1024",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="RNG seed for scratchy strokes (deterministic)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "out" / "cavalier_code_v1.png",
        help="Output PNG path",
    )
    parser.add_argument(
        "--also-9x16",
        action="store_true",
        help="Also write a 9:16 plate next to --out",
    )
    args = parser.parse_args()

    w, h = _parse_size(args.size, args.aspect)
    img = draw_cavalier(
        w,
        h,
        expression=args.expression,
        show_phone=args.show_phone,
        show_ear_bow=args.show_ear_bow,
        seed=args.seed,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    img.save(args.out, "PNG")
    print(f"Wrote {args.out} ({w}x{h})")
    print(f"Style Bible: {BIBLE_PATH.relative_to(BIBLE_PATH.parents[2])}")

    if args.also_9x16:
        plate = draw_cavalier(
            720,
            1280,
            expression=args.expression,
            show_phone=args.show_phone,
            show_ear_bow=args.show_ear_bow,
            seed=args.seed,
        )
        plate_path = args.out.with_name(args.out.stem + "_9x16.png")
        plate.save(plate_path, "PNG")
        print(f"Wrote {plate_path} (720x1280)")


if __name__ == "__main__":
    main()
