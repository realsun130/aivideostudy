#!/usr/bin/env python3
"""Build Frame 01 part masks + skeleton for 3-beat animation.

Cavalier focus (v3 — user bone chains):
- Mouth diamond: nose tip → mouth_L / mouth_R → chin lowest
- Each ear = 3 joints: root → midpoint → lowest edge (L0–L2 / R0–R2)
- Arm: chest(root) → shoulder → elbow → wrist → phone
- Keep vertical head chain (root→neck→head→crown) for laugh pivot
- Ear/mouth masks: hand polygons ∩ rembg (tight to fur)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "rig"
MASK_DIR = OUT / "part_masks"
EDIT = ROOT / "frame_01_s01_hero_v8_acc_edit.jpg"
ALPHA_DIR = ROOT / "assets" / "layers_alpha"
STROKES = ROOT / "stroke_paint" / "out" / "acc_strokes.npz"
W, H = 1280, 720

PARTS = [
    "bg",
    "bed",
    "wall_photo",
    "paw_lamp",
    "maine_head",
    "maine_eyes",
    "cavalier_head",
    "cavalier_ear_L",
    "cavalier_ear_R",
    "cavalier_mouth",
    "phone",
]
PART_ID = {n: i + 1 for i, n in enumerate(PARTS)}

COLORS = {
    "bg": (40, 40, 50),
    "bed": (90, 60, 40),
    "wall_photo": (180, 140, 60),
    "paw_lamp": (255, 180, 40),
    "maine_head": (80, 160, 200),
    "maine_eyes": (40, 255, 220),
    "cavalier_head": (220, 100, 80),
    "cavalier_ear_L": (0, 200, 200),
    "cavalier_ear_R": (0, 220, 170),
    "cavalier_mouth": (200, 60, 200),
    "phone": (120, 120, 255),
}

PLACE = {
    "cavalier_subject": (80, 200),
    "live_maine_coon": (560, 200),
    "phone_back": (360, 440),
    "paw_lamp": (1030, 230),
    "wall_photo": (250, 20),
}

# Hand-fitted polygons hugging ear fur / open jaw (screen coords) — v3 tighter
EAR_L_POLY = [
    (238, 250), (225, 242), (210, 240), (192, 250), (172, 268), (155, 292),
    (145, 318), (138, 345), (140, 370), (148, 390), (160, 405), (178, 412),
    (195, 408), (210, 390), (220, 365), (228, 340), (234, 310), (238, 280),
    (240, 258),
]
EAR_R_POLY = [
    (398, 250), (412, 242), (430, 248), (450, 262), (468, 285), (482, 310),
    (492, 338), (498, 362), (500, 385), (492, 400), (475, 408), (455, 400),
    (440, 380), (428, 355), (416, 328), (408, 300), (402, 275), (398, 258),
]
MOUTH_POLY = [
    (288, 358), (305, 348), (318, 345), (332, 348), (348, 360), (358, 375),
    (355, 395), (342, 415), (325, 430), (310, 434), (295, 422), (285, 400),
    (282, 378),
]


def load_alpha(name: str) -> tuple[np.ndarray, tuple[int, int]]:
    im = np.array(Image.open(ALPHA_DIR / f"{name}.png"))
    a = im[..., 3].astype(np.float32) / 255.0
    return a, PLACE[name]


def _paste(a: np.ndarray, xy: tuple[int, int]) -> np.ndarray:
    x0, y0 = xy
    h, w = a.shape
    out = np.zeros((H, W), dtype=np.float32)
    x1, y1 = min(W, x0 + w), min(H, y0 + h)
    out[y0:y1, x0:x1] = a[: y1 - y0, : x1 - x0]
    return out


def soft_ellipse(cx: float, cy: float, rx: float, ry: float, feather: float = 0.15) -> np.ndarray:
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    m = np.clip(1.0 - (d - 1.0) / max(feather, 1e-6), 0, 1)
    m[d <= 1.0] = 1.0
    return m.astype(np.float32)


def poly_mask(poly: list[tuple[int, int]]) -> np.ndarray:
    im = Image.new("L", (W, H), 0)
    ImageDraw.Draw(im).polygon(poly, fill=255)
    return (np.array(im).astype(np.float32) / 255.0)


def erode(mask: np.ndarray, px: int = 2) -> np.ndarray:
    im = Image.fromarray((np.clip(mask, 0, 1) * 255).astype(np.uint8), "L")
    im = im.filter(ImageFilter.MinFilter(px * 2 + 1))
    return np.array(im).astype(np.float32) / 255.0


def dilate(mask: np.ndarray, px: int = 2) -> np.ndarray:
    im = Image.fromarray((np.clip(mask, 0, 1) * 255).astype(np.uint8), "L")
    im = im.filter(ImageFilter.MaxFilter(px * 2 + 1))
    return np.array(im).astype(np.float32) / 255.0


def feather(mask: np.ndarray, radius: float = 1.5) -> np.ndarray:
    im = Image.fromarray((np.clip(mask, 0, 1) * 255).astype(np.uint8), "L")
    im = im.filter(ImageFilter.GaussianBlur(radius=radius))
    return np.array(im).astype(np.float32) / 255.0


def build_masks(edit: np.ndarray) -> dict[str, np.ndarray]:
    cav_raw, cav_xy = load_alpha("cavalier_subject")
    maine_raw, maine_xy = load_alpha("live_maine_coon")
    phone_raw, phone_xy = load_alpha("phone_back")
    lamp_raw, lamp_xy = load_alpha("paw_lamp")
    wall_raw, wall_xy = load_alpha("wall_photo")

    cav = _paste(cav_raw, cav_xy)
    maine = _paste(maine_raw, maine_xy)
    phone = _paste(phone_raw, phone_xy)
    lamp = _paste(lamp_raw, lamp_xy)
    wall = _paste(wall_raw, wall_xy)

    cav_h = (cav > 0.2).astype(np.float32)
    maine_h = (maine > 0.25).astype(np.float32)
    phone_h = (phone > 0.2).astype(np.float32)
    lamp_h = (lamp > 0.2).astype(np.float32)
    wall_h = (wall > 0.2).astype(np.float32)

    r = edit[:, :, 0].astype(np.int16)
    g = edit[:, :, 1].astype(np.int16)
    b = edit[:, :, 2].astype(np.int16)
    brown = (
        (r > 28) & (r < 165) & (g < (r * 0.78).astype(np.int16)) & (b < (r * 0.72).astype(np.int16))
        & (r > g + 6) & (r > b + 6) & (g < 95)
    )
    pink = (r > 150) & (g > 50) & (g < 170) & (b > 70) & (b < 190) & (r > g + 30) & (r > b + 15)
    # warm pillow / duvet (exclude from ears)
    pillow = (r > 55) & (r < 145) & (np.abs(r - g) < 38) & (b < r) & (b > 18) & (g > 38)

    pL = poly_mask(EAR_L_POLY)
    pR = poly_mask(EAR_R_POLY)
    # hug fur: polygon ∩ (rembg | brown/pink); only reject pillow outside alpha
    hard_pillow = pillow & (cav < 0.15)
    ear_L = pL * np.clip(
        cav * 0.85 + ((brown | pink) & (cav > 0.05)).astype(np.float32) * 0.7
        + ((brown | pink) & (cav <= 0.05)).astype(np.float32) * 0.35,
        0,
        1,
    )
    ear_L = ear_L * (1.0 - hard_pillow.astype(np.float32))
    ear_L = feather(ear_L, 0.9)

    ear_R = pR * np.clip(
        cav * 0.85 + (brown & (cav > 0.05)).astype(np.float32) * 0.7
        + (brown & (cav <= 0.05)).astype(np.float32) * 0.25,
        0,
        1,
    )
    ear_R = ear_R * (1.0 - hard_pillow.astype(np.float32))
    ear_R = feather(ear_R, 0.9)

    # Mouth: open jaw cavity (dark + tongue + teeth) inside polygon
    pM = poly_mask(MOUTH_POLY)
    dark = (r < 85) & (g < 55) & (b < 50)
    tongue = (r > 90) & (g > 35) & (g < 130) & (b > 35) & (b < 130) & (r > g + 10)
    teeth = (r > 170) & (g > 170) & (b > 160)
    mouth = pM * np.clip(
        0.4 + 0.6 * ((dark | tongue | teeth) | (cav > 0.25)).astype(np.float32), 0, 1
    )
    mouth = feather(mouth, 1.0)

    # Head: rembg ∩ head ellipse, minus ears/mouth/phone grip
    cav_head_ell = soft_ellipse(325, 310, 200, 175, 0.2)
    cavalier_head = cav_h * cav_head_ell
    cavalier_head *= 1.0 - np.clip(ear_L * 1.1, 0, 1)
    cavalier_head *= 1.0 - np.clip(ear_R * 1.1, 0, 1)
    cavalier_head *= 1.0 - np.clip(mouth * 0.95, 0, 1)
    cavalier_head *= 1.0 - soft_ellipse(450, 562, 95, 110, 0.1) * 0.95
    cavalier_head = np.clip(cavalier_head, 0, 1)

    phone_m = np.clip(phone_h + soft_ellipse(450, 562, 55, 75, 0.08) * (cav_h > 0) * 0.3, 0, 1)

    maine_head_ell = soft_ellipse(790, 300, 195, 175, 0.2)
    maine_head = maine_h * maine_head_ell
    maine_eyes = soft_ellipse(755, 295, 95, 40, 0.15) * maine_h
    maine_head = np.clip(maine_head - maine_eyes * 0.7, 0, 1)

    paw_lamp = lamp_h
    wall_photo = wall_h

    bed_band = np.zeros((H, W), dtype=np.float32)
    bed_band[480:H, :] = 1.0
    bed_band[420:480, :] = np.linspace(0, 1, 60)[:, None]
    subjects = np.clip(cav_h + maine_h + phone_m + lamp_h, 0, 1)
    bed = np.clip(bed_band * (1.0 - subjects * 0.85) + bed_band * 0.25 * (subjects > 0), 0, 1)

    occupied = np.clip(
        cavalier_head + ear_L + ear_R + mouth + phone_m + maine_head + maine_eyes + paw_lamp + wall_photo + bed,
        0,
        1,
    )
    bg = np.clip(1.0 - occupied, 0, 1)
    bg[0:200, :] = np.clip(bg[0:200, :] + 0.5 * (1 - wall_photo[0:200, :]), 0, 1)

    return {
        "bg": bg,
        "bed": bed,
        "wall_photo": wall_photo,
        "paw_lamp": paw_lamp,
        "maine_head": maine_head,
        "maine_eyes": maine_eyes,
        "cavalier_head": cavalier_head,
        "cavalier_ear_L": ear_L,
        "cavalier_ear_R": ear_R,
        "cavalier_mouth": mouth,
        "phone": phone_m,
    }


def masks_to_label(masks: dict[str, np.ndarray]) -> np.ndarray:
    order = [
        "bg",
        "bed",
        "wall_photo",
        "paw_lamp",
        "maine_head",
        "cavalier_head",
        "cavalier_ear_L",
        "cavalier_ear_R",
        "maine_eyes",
        "cavalier_mouth",
        "phone",
    ]
    lab = np.zeros((H, W), dtype=np.uint8)
    for name in order:
        lab[masks[name] > 0.35] = PART_ID[name]
    return lab


def save_masks(masks: dict[str, np.ndarray], label: np.ndarray) -> None:
    MASK_DIR.mkdir(parents=True, exist_ok=True)
    for name, m in masks.items():
        Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8), "L").save(MASK_DIR / f"{name}.png")
    Image.fromarray(label, "L").save(MASK_DIR / "label_map.png")
    legend = {"width": W, "height": H, "parts": {n: PART_ID[n] for n in PARTS}, "zero": "unlabeled"}
    (MASK_DIR / "legend.json").write_text(json.dumps(legend, indent=2), encoding="utf-8")


def build_overlay(edit: Image.Image, label: np.ndarray) -> Image.Image:
    base = edit.convert("RGBA")
    color = np.zeros((H, W, 4), dtype=np.uint8)
    for name in PARTS:
        pid = PART_ID[name]
        rr, gg, bb = COLORS[name]
        sel = label == pid
        color[sel, 0] = rr
        color[sel, 1] = gg
        color[sel, 2] = bb
        color[sel, 3] = 120
    overlay = Image.alpha_composite(base, Image.fromarray(color, "RGBA"))
    draw = ImageDraw.Draw(overlay)
    for i, name in enumerate(PARTS):
        col = i % 2
        row = i // 2
        x = 12 + col * 280
        y = H - 14 - (row + 1) * 26
        rr, gg, bb = COLORS[name]
        draw.rectangle([x, y, x + 18, y + 18], fill=(rr, gg, bb, 220), outline=(255, 255, 255, 200))
        draw.text((x + 24, y + 2), name, fill=(255, 255, 240, 255))
    return overlay.convert("RGB")


def skeleton_dict() -> dict:
    """Rest pose: user chains — mouth diamond, 3-joint ears, chest→phone arm."""
    joints = {
        # Spine (laugh pivot) — kept, not redesigned
        "cavalier_root": {"x": 340, "y": 500, "parent": None, "note": "chest (arm chain start + torso root)"},
        "cavalier_neck": {"x": 325, "y": 448, "parent": "cavalier_root", "note": "laugh-shake pivot (throat under chin)"},
        "cavalier_head": {"x": 325, "y": 298, "parent": "cavalier_neck", "note": "skull center"},
        "cavalier_crown": {"x": 322, "y": 228, "parent": "cavalier_head", "note": "forehead top"},
        # Mouth diamond: nose tip → two corners → chin lowest
        "cavalier_nose": {"x": 318, "y": 345, "parent": "cavalier_head", "note": "nose tip"},
        "cavalier_mouth_L": {"x": 288, "y": 370, "parent": "cavalier_nose", "note": "viewer-left mouth corner"},
        "cavalier_mouth_R": {"x": 348, "y": 370, "parent": "cavalier_nose", "note": "viewer-right mouth corner"},
        "cavalier_chin": {"x": 318, "y": 432, "parent": "cavalier_nose", "note": "chin lowest point / jaw"},
        # Ear L — 3 joints: root → mid → lowest edge (pink bow near root)
        "cavalier_ear_L0": {"x": 228, "y": 265, "parent": "cavalier_head", "note": "L ear root (pink bow)"},
        "cavalier_ear_L1": {"x": 175, "y": 335, "parent": "cavalier_ear_L0", "note": "L ear midpoint"},
        "cavalier_ear_L2": {"x": 155, "y": 405, "parent": "cavalier_ear_L1", "note": "L ear lowest edge"},
        # Ear R — 3 joints
        "cavalier_ear_R0": {"x": 405, "y": 258, "parent": "cavalier_head", "note": "R ear root"},
        "cavalier_ear_R1": {"x": 462, "y": 332, "parent": "cavalier_ear_R0", "note": "R ear midpoint"},
        "cavalier_ear_R2": {"x": 498, "y": 400, "parent": "cavalier_ear_R1", "note": "R ear lowest edge"},
        # Arm: chest → shoulder → elbow → wrist → phone
        "cavalier_shoulder": {"x": 358, "y": 470, "parent": "cavalier_root", "note": "shoulder toward phone"},
        "cavalier_elbow": {"x": 392, "y": 522, "parent": "cavalier_shoulder", "note": "elbow bend"},
        "cavalier_wrist": {"x": 422, "y": 552, "parent": "cavalier_elbow", "note": "wrist / paw grip"},
        "phone": {"x": 450, "y": 562, "parent": "cavalier_wrist", "note": "phone back center; orientation lock"},
        # Maine (unchanged)
        "maine_root": {"x": 790, "y": 500, "parent": None, "note": "chest / ruff under duvet"},
        "maine_neck": {"x": 790, "y": 410, "parent": "maine_root", "note": "head-turn pivot"},
        "maine_head": {"x": 790, "y": 300, "parent": "maine_neck", "note": "skull center"},
        "maine_eyes": {"x": 755, "y": 295, "parent": "maine_head", "note": "gaze; look-away target"},
        "paw_lamp": {"x": 1144, "y": 346, "parent": None, "note": "static practical key"},
        "wall_photo": {"x": 475, "y": 120, "parent": None, "note": "static; accessory already edited"},
    }
    bones = [
        ["cavalier_root", "cavalier_neck"],
        ["cavalier_neck", "cavalier_head"],
        ["cavalier_head", "cavalier_crown"],
        # mouth diamond
        ["cavalier_head", "cavalier_nose"],
        ["cavalier_nose", "cavalier_mouth_L"],
        ["cavalier_nose", "cavalier_mouth_R"],
        ["cavalier_mouth_L", "cavalier_chin"],
        ["cavalier_mouth_R", "cavalier_chin"],
        # ears 3-joint
        ["cavalier_head", "cavalier_ear_L0"],
        ["cavalier_ear_L0", "cavalier_ear_L1"],
        ["cavalier_ear_L1", "cavalier_ear_L2"],
        ["cavalier_head", "cavalier_ear_R0"],
        ["cavalier_ear_R0", "cavalier_ear_R1"],
        ["cavalier_ear_R1", "cavalier_ear_R2"],
        # arm
        ["cavalier_root", "cavalier_shoulder"],
        ["cavalier_shoulder", "cavalier_elbow"],
        ["cavalier_elbow", "cavalier_wrist"],
        ["cavalier_wrist", "phone"],
        ["maine_root", "maine_neck"],
        ["maine_neck", "maine_head"],
        ["maine_head", "maine_eyes"],
    ]
    return {
        "frame": "s01_hero",
        "source": "projects/first-frame/frame_01_s01_hero_v8_acc_edit.jpg",
        "canvas": {"width": W, "height": H},
        "coord_space": "source_px",
        "ear_convention": "L/R = screen left/right; cavalier_ear_L* has pink bow; each ear = 3 joints root→mid→lowest (L0–L2 / R0–R2)",
        "rest_pose": joints,
        "bones": bones,
        "bone_colors": {
            "head_chain": ["cavalier_root", "cavalier_neck", "cavalier_head", "cavalier_crown"],
            "mouth": ["cavalier_nose", "cavalier_mouth_L", "cavalier_mouth_R", "cavalier_chin"],
            "ear_L": ["cavalier_ear_L0", "cavalier_ear_L1", "cavalier_ear_L2"],
            "ear_R": ["cavalier_ear_R0", "cavalier_ear_R1", "cavalier_ear_R2"],
            "arm": ["cavalier_root", "cavalier_shoulder", "cavalier_elbow", "cavalier_wrist", "phone"],
        },
        "drivers": {
            "beat1_laugh_shake": [
                "cavalier_neck",
                "cavalier_head",
                "cavalier_crown",
                "cavalier_nose",
                "cavalier_mouth_L",
                "cavalier_mouth_R",
                "cavalier_chin",
                "cavalier_ear_L0",
                "cavalier_ear_L1",
                "cavalier_ear_L2",
                "cavalier_ear_R0",
                "cavalier_ear_R1",
                "cavalier_ear_R2",
            ],
            "beat2_push_phone": [
                "cavalier_root",
                "cavalier_shoulder",
                "cavalier_elbow",
                "cavalier_wrist",
                "phone",
            ],
            "beat3_maine_lookaway": ["maine_neck", "maine_head", "maine_eyes"],
        },
        "stroke_coord_scale": 2,
        "stroke_coord_note": "acc_strokes.npz pts are in 2560x1440 (sbr S=2); divide by 2 for source px",
        "quality": "v3: mouth diamond nose→corners→chin; 3-joint ears; chest→shoulder→elbow→wrist→phone; tight poly∩rembg",
    }


def draw_skeleton_overlay(edit: Image.Image, skel: dict) -> Image.Image:
    im = edit.convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    joints = skel["rest_pose"]
    # Color bones by group
    ear_joints = set(skel["bone_colors"]["ear_L"] + skel["bone_colors"]["ear_R"])
    head_set = set(skel["bone_colors"]["head_chain"])
    arm_set = set(skel["bone_colors"]["arm"])
    mouth_set = set(skel["bone_colors"]["mouth"])

    def bone_color(a: str, b: str):
        if a in ear_joints or b in ear_joints:
            return (255, 220, 40, 220)  # yellow ear chains
        if a in arm_set and b in arm_set:
            return (80, 180, 255, 220)  # blue arm
        if a in mouth_set or b in mouth_set:
            return (255, 60, 180, 220)  # magenta mouth diamond
        if a in head_set and b in head_set:
            return (40, 255, 120, 220)  # green vertical head
        return (0, 255, 180, 200)

    for a, b in skel["bones"]:
        xa, ya = joints[a]["x"], joints[a]["y"]
        xb, yb = joints[b]["x"], joints[b]["y"]
        d.line([(xa, ya), (xb, yb)], fill=bone_color(a, b), width=3)

    for name, j in joints.items():
        x, y = j["x"], j["y"]
        if name in ("cavalier_nose", "cavalier_chin"):
            fill = (255, 40, 120, 240)
            r = 8
        elif name in ("cavalier_mouth_L", "cavalier_mouth_R"):
            fill = (255, 80, 40, 240)
            r = 7
        elif name == "phone":
            fill = (255, 255, 255, 240)
            r = 8
        elif name.startswith("cavalier_ear_"):
            fill = (255, 255, 255, 230)
            r = 6
        else:
            fill = (255, 255, 255, 230)
            r = 7 if j["parent"] else 9
        d.ellipse([x - r, y - r, x + r, y + r], fill=fill, outline=(0, 0, 0, 200))
        label = (
            name.replace("cavalier_", "c_")
            .replace("maine_", "m_")
            .replace("ear_L", "eL")
            .replace("ear_R", "eR")
            .replace("mouth_", "m")
        )
        d.text((x + 9, y - 7), label, fill=(255, 255, 220, 255))
    return Image.alpha_composite(im, layer).convert("RGB")


def tag_strokes(label: np.ndarray) -> None:
    if not STROKES.exists():
        return
    z = np.load(STROKES)
    STROKE_SCALE = 2.0
    lens = z["lens"]
    pts = z["pts"]
    starts = np.zeros(len(lens), dtype=np.int64)
    starts[1:] = np.cumsum(lens[:-1])
    idx = starts + (lens // 2)
    idx = np.clip(idx, 0, len(pts) - 1)
    xy = pts[idx].astype(np.float32) / STROKE_SCALE
    xi = np.clip(np.round(xy[:, 0]).astype(np.int32), 0, W - 1)
    yi = np.clip(np.round(xy[:, 1]).astype(np.int32), 0, H - 1)
    part_ids = label[yi, xi]
    np.save(OUT / "stroke_part_ids.npy", part_ids.astype(np.uint8))
    counts = {n: int((part_ids == PART_ID[n]).sum()) for n in PARTS}
    counts["unlabeled"] = int((part_ids == 0).sum())
    (OUT / "stroke_part_counts.json").write_text(json.dumps(counts, indent=2), encoding="utf-8")


def write_anim_rig_md(counts: dict | None) -> None:
    md = """# Frame 01 · 动画绑定说明（切分 + 骨架）v3

> 源帧：`frame_01_s01_hero_v8_acc_edit.jpg`  
> 笔触：`stroke_paint/out/acc_strokes.npz`（约 49 万笔）  
> 产出目录：`projects/first-frame/rig/`  
> 参考：用户点名 — 鼻尖→两嘴角→下巴；耳根→中→最下缘；胸口→肩→肘→腕→手机

---

## 0. 三拍动画

| 拍 | 内容 | 主要驱动关节 / 部件 |
|----|------|---------------------|
| **Beat 1** | 查理王大笑抖动 + 耳自然甩动 | `neck/head/crown` + mouth diamond `nose/mouth_L/R/chin` + `ear_L0–L2` / `ear_R0–R2` |
| **Beat 2** | 手机凑近给缅因 | `chest(root)→shoulder→elbow→wrist→phone` |
| **Beat 3** | 缅因无语转头 | `maine_neck` + `maine_eyes` |

静帧：`paw_lamp`、`wall_photo`、`bed`、`bg`。

---

## 1. 部件遮罩（part_masks）

| 部件 ID | 含义 | 叠层色 |
|---------|------|--------|
| `cavalier_head` | 头颅主体（不含耳/嘴优先层） | 红 |
| `cavalier_ear_L` | 画面左耳（粉发卡）— **多边形∩rembg 贴毛边** | 青 |
| `cavalier_ear_R` | 画面右耳 — 贴毛边 | 青绿 |
| `cavalier_mouth` | 张嘴腔（舌/齿/口腔） | 紫 |
| `phone` | 手机背面 | 蓝紫 |
| `maine_head` / `maine_eyes` | 缅因头 / 眼带 | 青 |
| `wall_photo` / `paw_lamp` / `bed` / `bg` | 静物与背景 | — |

**耳约定**：`L/R` = 屏幕左右；`ear_L` = 粉发卡。

### 质量说明
- 耳/嘴改为 **手绘多边形 ∩ rembg α**（并去掉枕套误检），比椭圆 ROI 更贴毛边；仍非精修 matte。
- `bed`/`bg` 仍为几何分区。
- 够用：笔触标签、骨骼预览、三拍阻塞动画。

生成脚本：`scripts/build_anim_rig.py`。

---

## 2. 骨架（skeleton.json）

坐标系：源图像素，**1280×720**，原点左上。

### 查理王（用户点名三链）
- **嘴菱形（品红）**：`nose → mouth_L / mouth_R → chin`（鼻尖→两嘴角→下巴最低点）
- **左耳三关节（黄）**：`ear_L0 → L1 → L2`（根→中→最下缘；L0 近粉发卡）
- **右耳三关节（黄）**：`ear_R0 → R1 → R2`
- **手臂（蓝）**：`root(chest) → shoulder → elbow → wrist → phone`
- **头链（绿，保留）**：`root → neck → head → crown`（大笑枢轴）

### 缅因
`maine_root → neck → head → eyes`

### 静关节
`paw_lamp`、`wall_photo`（parent=null）

---

## 3. 三拍怎么动

### Beat 1 · 大笑抖动
1. `cavalier_neck` 枢轴，头链小幅旋转/位移（spring）
2. mouth diamond：`chin` / 嘴角微张合
3. 双耳三关节分段延迟上下甩（secondary）
4. 笔触：变换 head / ear_* / mouth

### Beat 2 · 手机凑近
手臂链整体向缅因方向推；phone 朝向锁（背面朝镜）

### Beat 3 · 缅因转头
`maine_neck` 转开 + `maine_eyes` 视线滑开

---

## 4. 文件清单

| 文件 | 说明 |
|------|------|
| `part_masks/*.png` | 各部件软遮罩 |
| `skeleton.json` | rest pose + bones + drivers |
| `overlay_parts.png` / `overlay_skeleton.png` / `overlay_preview.png` | 预览 |
| `stroke_part_ids.npy` / `stroke_part_counts.json` | 笔触归属 |
| `out/laugh_shake_3s.mp4` | Beat1 预览动画（若已渲） |
| `ANIM_RIG.md` | 本说明 |

---

## 5. 笔触归属统计

"""
    if counts:
        md += "| 部件 | 笔数 |\n|------|------|\n"
        for k, v in counts.items():
            md += f"| `{k}` | {v} |\n"
    md += """
---

## 6. 下一步
1. 微调耳多边形若仍溢边
2. 三拍关键帧（先仿射/旋转笔触）
3. 张嘴/转头露馅补笔
"""
    (OUT / "ANIM_RIG.md").write_text(md, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    edit_im = Image.open(EDIT).convert("RGB")
    assert edit_im.size == (W, H), edit_im.size
    edit = np.array(edit_im)

    masks = build_masks(edit)
    label = masks_to_label(masks)
    save_masks(masks, label)

    parts_overlay = build_overlay(edit_im, label)
    parts_overlay.save(OUT / "overlay_parts.png", optimize=True)

    skel = skeleton_dict()
    (OUT / "skeleton.json").write_text(json.dumps(skel, indent=2, ensure_ascii=False), encoding="utf-8")
    skel_overlay = draw_skeleton_overlay(edit_im, skel)
    skel_overlay.save(OUT / "overlay_skeleton.png", optimize=True)
    combined = draw_skeleton_overlay(parts_overlay, skel)
    combined.save(OUT / "overlay_preview.png", optimize=True)

    tag_strokes(label)
    counts = None
    cpath = OUT / "stroke_part_counts.json"
    if cpath.exists():
        counts = json.loads(cpath.read_text())
    write_anim_rig_md(counts)

    total = H * W
    print("label coverage:")
    for n in PARTS:
        c = int((label == PART_ID[n]).sum())
        print(f"  {n:18s} {c:7d}  {100 * c / total:5.1f}%")
    print(f"  unlabeled         {int((label == 0).sum()):7d}")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
