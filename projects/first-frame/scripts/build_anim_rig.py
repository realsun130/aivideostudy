#!/usr/bin/env python3
"""Build Frame 01 part masks + skeleton for 3-beat animation.

Source: frame_01_s01_hero_v8_acc_edit.jpg + rembg alphas + geometric ROIs.
Honest quality: rembg mattes are fuzzy; ear/mouth/eyes are ROI∩alpha, not hand-painted.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]  # projects/first-frame
REPO = ROOT.parent.parent
OUT = ROOT / "rig"
MASK_DIR = OUT / "part_masks"
EDIT = ROOT / "frame_01_s01_hero_v8_acc_edit.jpg"
ALPHA_DIR = ROOT / "assets" / "layers_alpha"
STROKES = ROOT / "stroke_paint" / "out" / "acc_strokes.npz"
W, H = 1280, 720

# Part id order for label map (0 = none)
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
PART_ID = {n: i + 1 for i, n in enumerate(PARTS)}  # 1..N; 0 unused leftover

# Distinct overlay colors (RGB)
COLORS = {
    "bg": (40, 40, 50),
    "bed": (90, 60, 40),
    "wall_photo": (180, 140, 60),
    "paw_lamp": (255, 180, 40),
    "maine_head": (80, 160, 200),
    "maine_eyes": (40, 255, 220),
    "cavalier_head": (220, 100, 80),
    "cavalier_ear_L": (255, 120, 200),
    "cavalier_ear_R": (255, 160, 120),
    "cavalier_mouth": (255, 60, 60),
    "phone": (120, 120, 255),
}

# Manifest placements for rembg crops
PLACE = {
    "cavalier_subject": (80, 200),
    "live_maine_coon": (560, 200),
    "phone_back": (360, 440),
    "paw_lamp": (1030, 230),
    "wall_photo": (250, 20),
}


def load_alpha(name: str) -> tuple[np.ndarray, tuple[int, int]]:
    im = np.array(Image.open(ALPHA_DIR / f"{name}.png"))
    a = im[..., 3].astype(np.float32) / 255.0
    return a, PLACE[name]




def ellipse_mask(cx: float, cy: float, rx: float, ry: float) -> np.ndarray:
    yy, xx = np.mgrid[0:H, 0:W]
    return (((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0).astype(np.float32)


def soft_ellipse(cx: float, cy: float, rx: float, ry: float, feather: float = 0.15) -> np.ndarray:
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    m = np.clip(1.0 - (d - 1.0) / max(feather, 1e-6), 0, 1)
    m[d <= 1.0] = 1.0
    return m.astype(np.float32)


def dilate(mask: np.ndarray, px: int = 3) -> np.ndarray:
    im = Image.fromarray((np.clip(mask, 0, 1) * 255).astype(np.uint8), "L")
    im = im.filter(ImageFilter.MaxFilter(px * 2 + 1))
    return np.array(im).astype(np.float32) / 255.0


def erode(mask: np.ndarray, px: int = 2) -> np.ndarray:
    im = Image.fromarray((np.clip(mask, 0, 1) * 255).astype(np.uint8), "L")
    im = im.filter(ImageFilter.MinFilter(px * 2 + 1))
    return np.array(im).astype(np.float32) / 255.0


def build_masks() -> dict[str, np.ndarray]:
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

    # Threshold soft alphas for hard-ish mattes
    cav_h = (cav > 0.25).astype(np.float32)
    maine_h = (maine > 0.25).astype(np.float32)
    phone_h = (phone > 0.2).astype(np.float32)
    lamp_h = (lamp > 0.2).astype(np.float32)
    wall_h = (wall > 0.2).astype(np.float32)

    # --- Cavalier subdivisions (screen L/R; ear_L has pink bow) ---
    # Head: upper torso of cavalier alpha ∩ head ellipse
    cav_head_ell = soft_ellipse(335, 315, 230, 195, 0.22)
    cavalier_head = cav_h * cav_head_ell
    # exclude lower grip / phone zone from head
    cavalier_head *= (1.0 - soft_ellipse(420, 560, 130, 140, 0.1) * 0.95)

    # Ears: side lobes ∩ cav alpha
    ear_L = soft_ellipse(185, 280, 80, 110, 0.18) * cav_h
    ear_R = soft_ellipse(470, 285, 70, 105, 0.18) * cav_h
    # Mouth / jaw open region (keep smaller than head so head remains majority)
    mouth = soft_ellipse(318, 390, 78, 58, 0.12) * cav_h
    # Head keeps base; ears/mouth painted later with higher label priority
    cavalier_head = np.clip(cavalier_head, 0, 1)

    # Phone: rembg phone, priority
    phone_m = phone_h
    # Also claim phone-colored core inside cavalier bbox if rembg thin
    phone_boost = soft_ellipse(420, 555, 70, 95, 0.1)
    # only where dark-ish in edit? skip color — keep rembg + small boost ∩ cav lower
    phone_m = np.clip(phone_m + phone_boost * (cav_h > 0) * 0.35, 0, 1)

    # --- Maine ---
    maine_head_ell = soft_ellipse(790, 300, 195, 175, 0.2)
    maine_head = maine_h * maine_head_ell
    # eyes band (half-lidded looking left)
    maine_eyes = soft_ellipse(755, 295, 95, 40, 0.15) * maine_h
    maine_head = np.clip(maine_head - maine_eyes * 0.7, 0, 1)

    # --- Props ---
    paw_lamp = lamp_h
    wall_photo = wall_h

    # --- Bed: lower band minus subjects ---
    bed_band = np.zeros((H, W), dtype=np.float32)
    bed_band[480:H, :] = 1.0
    bed_band[420:480, :] = np.linspace(0, 1, 60)[:, None]
    subjects = np.clip(cav_h + maine_h + phone_m + lamp_h, 0, 1)
    bed = np.clip(bed_band * (1.0 - subjects * 0.85), 0, 1)
    # keep some duvet under subjects soft edge
    bed = np.clip(bed + bed_band * 0.25 * (subjects > 0), 0, 1)
    bed = np.clip(bed, 0, 1)

    # --- BG: rest of frame ---
    occupied = np.clip(
        cavalier_head + ear_L + ear_R + mouth + phone_m + maine_head + maine_eyes + paw_lamp + wall_photo + bed,
        0,
        1,
    )
    bg = np.clip(1.0 - occupied, 0, 1)
    # force upper wall as bg where not wall_photo
    bg[0:200, :] = np.clip(bg[0:200, :] + 0.5 * (1 - wall_photo[0:200, :]), 0, 1)

    masks = {
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
    # normalize lightly where overlapping priority later handles labeling
    return masks


def _paste(a: np.ndarray, xy: tuple[int, int]) -> np.ndarray:
    x0, y0 = xy
    h, w = a.shape
    out = np.zeros((H, W), dtype=np.float32)
    x1, y1 = min(W, x0 + w), min(H, y0 + h)
    out[y0:y1, x0:x1] = a[: y1 - y0, : x1 - x0]
    return out


def masks_to_label(masks: dict[str, np.ndarray]) -> np.ndarray:
    """Priority paint: later parts in PARTS win on overlap (phone/mouth/eyes on top)."""
    # paint order: bg first → phone last
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
        m = masks[name]
        lab[m > 0.35] = PART_ID[name]
    return lab


def save_masks(masks: dict[str, np.ndarray], label: np.ndarray) -> None:
    MASK_DIR.mkdir(parents=True, exist_ok=True)
    for name, m in masks.items():
        Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8), "L").save(MASK_DIR / f"{name}.png")
    Image.fromarray(label, "L").save(MASK_DIR / "label_map.png")
    # legend json
    legend = {"width": W, "height": H, "parts": {n: PART_ID[n] for n in PARTS}, "zero": "unlabeled"}
    (MASK_DIR / "legend.json").write_text(json.dumps(legend, indent=2), encoding="utf-8")


def build_overlay(edit: Image.Image, label: np.ndarray, masks: dict[str, np.ndarray]) -> Image.Image:
    base = edit.convert("RGBA")
    color = np.zeros((H, W, 4), dtype=np.uint8)
    for name in PARTS:
        pid = PART_ID[name]
        r, g, b = COLORS[name]
        sel = label == pid
        color[sel, 0] = r
        color[sel, 1] = g
        color[sel, 2] = b
        color[sel, 3] = 110
    overlay = Image.alpha_composite(base, Image.fromarray(color, "RGBA"))
    draw = ImageDraw.Draw(overlay)
    # legend strip
    x0, y0 = 10, H - 28 * ((len(PARTS) + 1) // 2) - 10
    for i, name in enumerate(PARTS):
        col = i % 2
        row = i // 2
        x = 12 + col * 280
        y = H - 14 - (row + 1) * 26
        r, g, b = COLORS[name]
        draw.rectangle([x, y, x + 18, y + 18], fill=(r, g, b, 220), outline=(255, 255, 255, 200))
        draw.text((x + 24, y + 2), name, fill=(255, 255, 240, 255))
    return overlay.convert("RGB")


def skeleton_dict() -> dict:
    """Rest-pose joints aligned to acc_edit frame. Coords in source pixels."""
    # Naming: ear_L / ear_R = SCREEN left/right (ear_L carries pink bow).
    joints = {
        "cavalier_root": {"x": 340, "y": 520, "parent": None, "note": "chest under duvet"},
        "cavalier_neck": {"x": 340, "y": 445, "parent": "cavalier_root", "note": "laugh-shake pivot"},
        "cavalier_head": {"x": 325, "y": 300, "parent": "cavalier_neck", "note": "skull center"},
        "cavalier_ear_L": {"x": 185, "y": 280, "parent": "cavalier_head", "note": "screen-left ear + pink bow"},
        "cavalier_ear_R": {"x": 470, "y": 285, "parent": "cavalier_head", "note": "screen-right ear"},
        "cavalier_jaw": {"x": 320, "y": 385, "parent": "cavalier_head", "note": "mouth open / laugh"},
        "cavalier_paw_hold": {"x": 400, "y": 530, "parent": "cavalier_root", "note": "both paws grip phone"},
        "phone": {"x": 420, "y": 555, "parent": "cavalier_paw_hold", "note": "phone back center; orientation lock"},
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
        ["cavalier_head", "cavalier_ear_L"],
        ["cavalier_head", "cavalier_ear_R"],
        ["cavalier_head", "cavalier_jaw"],
        ["cavalier_root", "cavalier_paw_hold"],
        ["cavalier_paw_hold", "phone"],
        ["maine_root", "maine_neck"],
        ["maine_neck", "maine_head"],
        ["maine_head", "maine_eyes"],
    ]
    return {
        "frame": "s01_hero",
        "source": "projects/first-frame/frame_01_s01_hero_v8_acc_edit.jpg",
        "canvas": {"width": W, "height": H},
        "coord_space": "source_px",
        "ear_convention": "L/R = screen left/right; cavalier_ear_L has pink bow (= anatomical right if facing camera)",
        "rest_pose": joints,
        "bones": bones,
        "drivers": {
            "beat1_laugh_shake": ["cavalier_neck", "cavalier_head", "cavalier_jaw", "cavalier_ear_L", "cavalier_ear_R"],
            "beat2_push_phone": ["cavalier_paw_hold", "phone", "cavalier_root"],
            "beat3_maine_lookaway": ["maine_neck", "maine_head", "maine_eyes"],
        },
        "stroke_coord_scale": 2,
        "stroke_coord_note": "acc_strokes.npz pts are in 2560x1440 (sbr S=2); divide by 2 for source px",
        "quality": "hand-placed rest joints on acc_edit; not auto-tracked. ±10–20px expected. Masks = rembg∩ROI, rough.",
    }


def draw_skeleton_overlay(edit: Image.Image, skel: dict) -> Image.Image:
    im = edit.convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    joints = skel["rest_pose"]
    for a, b in skel["bones"]:
        xa, ya = joints[a]["x"], joints[a]["y"]
        xb, yb = joints[b]["x"], joints[b]["y"]
        d.line([(xa, ya), (xb, yb)], fill=(0, 255, 180, 200), width=3)
    for name, j in joints.items():
        x, y = j["x"], j["y"]
        r = 7 if j["parent"] else 9
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 0, 230), outline=(0, 0, 0, 200))
        d.text((x + 10, y - 8), name.replace("cavalier_", "c_").replace("maine_", "m_"), fill=(255, 255, 220, 255))
    return Image.alpha_composite(im, layer).convert("RGB")


def tag_strokes(label: np.ndarray) -> None:
    if not STROKES.exists():
        return
    z = np.load(STROKES)
    # pts are in sbr upsample space (S=2 → 2560x1440); map back to source 1280x720
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
    out = OUT / "stroke_part_ids.npy"
    np.save(out, part_ids.astype(np.uint8))
    # counts
    counts = {n: int((part_ids == PART_ID[n]).sum()) for n in PARTS}
    counts["unlabeled"] = int((part_ids == 0).sum())
    (OUT / "stroke_part_counts.json").write_text(json.dumps(counts, indent=2), encoding="utf-8")


def write_anim_rig_md(skel: dict, counts: dict | None) -> None:
    md = f"""# Frame 01 · 动画绑定说明（切分 + 骨架）

> 源帧：`frame_01_s01_hero_v8_acc_edit.jpg`（配件已改：床上缅因无结、合影缅黑领结、合影查理王粉发卡）  
> 笔触：`stroke_paint/out/acc_strokes.npz`（约 49 万笔）  
> 产出目录：`projects/first-frame/rig/`

---

## 0. 三拍动画（本绑定服务的镜头）

| 拍 | 内容 | 主要驱动关节 / 部件 |
|----|------|---------------------|
| **Beat 1** | 查理王大笑到抖动 | `cavalier_neck` / `cavalier_head` / `cavalier_jaw` + 双耳；遮罩 `cavalier_head`、`cavalier_mouth`、`cavalier_ear_L/R` |
| **Beat 2** | 把手机凑近给缅因看 | `cavalier_paw_hold` → `phone` 前推；轻带 `cavalier_root`；遮罩 `phone` |
| **Beat 3** | 缅因无语，眼神转走 / 转头 | `maine_neck` 转开 + `maine_eyes` 视线；遮罩 `maine_head`、`maine_eyes` |

静帧不动：`paw_lamp`、`wall_photo`、`bed`、`bg`（爪灯可后续做强度脉冲，但不绑骨骼）。

---

## 1. 部件遮罩（part_masks）

路径：`rig/part_masks/*.png`（单通道 0–255）+ `label_map.png` + `legend.json`。

| 部件 ID | 含义 | 叠层色（预览） |
|---------|------|----------------|
| `cavalier_head` | 查理王头颅主体（不含耳/嘴优先层） | 红 |
| `cavalier_ear_L` | 画面左耳（粉发卡所在） | 粉 |
| `cavalier_ear_R` | 画面右耳 | 橙粉 |
| `cavalier_mouth` | 张嘴/下颌区 | 亮红 |
| `phone` | 手机背面 | 蓝紫 |
| `maine_head` | 缅因头 | 青 |
| `maine_eyes` | 缅因眼带 | 亮青 |
| `wall_photo` | 墙上合影框 | 金 |
| `paw_lamp` | 爪灯 | 琥珀 |
| `bed` | 被窝/床面带 | 褐 |
| `bg` | 墙面与其余背景 | 暗灰 |

**耳约定**：`L/R` = **屏幕左右**（不是解剖左右）。`cavalier_ear_L` = 带粉发卡的那只。

### 质量诚实说明

- 主体来自既有 **rembg** 透明层（`assets/layers_alpha/`），毛边、被褥粘连仍在，**不是**精修 matte。
- 头/耳/嘴/眼是 **椭圆 ROI ∩ rembg**，边界发糊、会互相抢像素；嘴巴张合露出的「新内容」尚未补画。
- `bed` / `bg` 是几何分区，不是语义分割；床头柜并进 `bg`/`paw_lamp` 周边。
- 够用做：**笔触打标签、骨骼驱动预览、三拍阻塞动画**；不够用做：最终成片级抠像。

生成脚本：`scripts/build_anim_rig.py`。

---

## 2. 骨架（skeleton.json）

- 坐标系：源图像素，原点左上，画布 **1280×720**。
- 查理王链：`cavalier_root → neck → head → {{ear_L, ear_R, jaw}}`；`root → paw_hold → phone`。
- 缅因链：`maine_root → neck → head → eyes`。
- 静关节：`paw_lamp`、`wall_photo`（parent=null）。

Rest pose 已按 acc_edit 手标；误差大约 **±10–20px**，动画前可再微调。

---

## 3. 部件 ↔ 三拍映射（怎么动）

### Beat 1 · 大笑抖动
1. 以 `cavalier_neck` 为枢轴，对 `cavalier_head` 做小幅旋转/位移动画（spring / noise）。
2. `cavalier_jaw` 微张合；遮罩 `cavalier_mouth` 随父级旋转。
3. `cavalier_ear_L/R` 加延迟抖动（secondary）。
4. 笔触：只变换 `part_id ∈ {{cavalier_head, ear_*, mouth}}` 的笔。

### Beat 2 · 手机凑近
1. `cavalier_paw_hold` 向缅因方向（右上）平移；`phone` 子级跟随。
2. **朝向锁**：手机保持背面朝镜头，禁止翻成屏幕朝镜。
3. 可选：查理王肩 `cavalier_root` 轻跟。
4. 笔触：变换 `phone`（及少量 paw 区若后续加遮罩）。

### Beat 3 · 缅因无语转头
1. `maine_neck` 向右（远离手机/查理王）旋转。
2. `maine_eyes` 视线先瞟手机再滑开；半眯保持。
3. 露出的颈侧若出现空缺，需补笔或拖影（本版 **未** 补画）。
4. 笔触：变换 `maine_head` + `maine_eyes`。

---

## 4. 文件清单

| 文件 | 说明 |
|------|------|
| `part_masks/*.png` | 各部件软遮罩 |
| `part_masks/label_map.png` | 索引图（见 legend.json） |
| `part_masks/legend.json` | 部件 id ↔ 像素值 |
| `skeleton.json` | 关节 rest pose + bones + drivers |
| `overlay_parts.png` | 遮罩彩色叠层预览 |
| `overlay_skeleton.png` | 骨架叠层预览 |
| `overlay_preview.png` | 遮罩+骨架合成预览 |
| `stroke_part_ids.npy` | 每笔部件 id（对 acc_strokes；坐标已 /2，因 sbr `S=2`） |
| `stroke_part_counts.json` | 各部件笔数统计 |
| `ANIM_RIG.md` | 本说明 |

---

## 5. 笔触归属统计（acc_strokes）

"""
    if counts:
        md += "| 部件 | 笔数 |\n|------|------|\n"
        for k, v in counts.items():
            md += f"| `{k}` | {v} |\n"
    else:
        md += "_（未找到 acc_strokes.npz，未写归属）_\n"

    md += """
---

## 6. 下一步

1. 预览 `overlay_preview.png`，必要时改 `build_anim_rig.py` 里椭圆中心再生成。
2. 用 `skeleton.json` drivers 做三拍关键帧（先 2D 仿射/旋转笔触）。
3. 张嘴/转头露馅处再补笔触或 hold-out 层。
"""
    (OUT / "ANIM_RIG.md").write_text(md, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    edit = Image.open(EDIT).convert("RGB")
    assert edit.size == (W, H), edit.size

    masks = build_masks()
    label = masks_to_label(masks)
    save_masks(masks, label)

    parts_overlay = build_overlay(edit, label, masks)
    parts_overlay.save(OUT / "overlay_parts.png", optimize=True)

    skel = skeleton_dict()
    (OUT / "skeleton.json").write_text(json.dumps(skel, indent=2, ensure_ascii=False), encoding="utf-8")
    skel_overlay = draw_skeleton_overlay(edit, skel)
    skel_overlay.save(OUT / "overlay_skeleton.png", optimize=True)

    # combined preview: parts tint + skeleton on top
    combined = build_overlay(edit, label, masks).convert("RGBA")
    skel_only = draw_skeleton_overlay(Image.new("RGB", (W, H), (0, 0, 0)), skel).convert("RGBA")
    # redraw skeleton on combined more cleanly
    combined_rgb = draw_skeleton_overlay(parts_overlay, skel)
    combined_rgb.save(OUT / "overlay_preview.png", optimize=True)

    tag_strokes(label)
    counts = None
    cpath = OUT / "stroke_part_counts.json"
    if cpath.exists():
        counts = json.loads(cpath.read_text())
    write_anim_rig_md(skel, counts)

    # coverage report
    total = H * W
    print("label coverage:")
    for n in PARTS:
        c = int((label == PART_ID[n]).sum())
        print(f"  {n:18s} {c:7d}  {100*c/total:5.1f}%")
    print(f"  unlabeled         {int((label==0).sum()):7d}")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
