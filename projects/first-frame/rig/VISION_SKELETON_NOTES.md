# Vision skeleton proposal (vision_v1b)

**Source:** `projects/first-frame/frame_01_s01_hero_v8_acc_edit.jpg`  
**Outputs:** `skeleton_vision.json`, `overlay_skeleton_vision.png`, `overlay_preview_vision.png`

## Method
No Claude/Qwen-VL API on box. Used: (1) multimodal Read of hero + face/ear/mouth/phone crops; (2) part_masks geometry (medial ear chains, mouth extrema, mask centroids); (3) color landmarks (black nose above mouth, dusty-pink bow for ear_L0).

No Anthropic/OpenAI/Qwen VL API keys on the box — proposal is **mask geometry + color landmarks + multimodal crop reads**.

## Key corrections vs prior v3
- **ear_L0** (228,265) sat in near-black void outside masks → now on **pink bow**
- **crown** (322,228) off-head → on head-mask top
- **phone** (450,562) right of device → phone-mask centroid
- Mouth diamond from mouth-mask extrema; ears from medial mask samples
- Head re-interpolated crown→nose (mask mid fell into muzzle)
- Arm: anatomical up-right shoulder (still **dubious**)

## Cavalier joints (vision_v1b)

| Joint | x | y | conf |
|-------|---|---|------|
| `cavalier_root` | 363.9 | 490.8 | medium |
| `cavalier_neck` | 341.4 | 447.7 | medium |
| `cavalier_head` | 341.1 | 292.3 | medium |
| `cavalier_crown` | 355.2 | 262.5 | high |
| `cavalier_nose` | 323.8 | 328.8 | high |
| `cavalier_mouth_L` | 282.0 | 377.0 | high |
| `cavalier_mouth_R` | 358.0 | 375.0 | high |
| `cavalier_chin` | 320.2 | 426.7 | high |
| `cavalier_ear_L0` | 240.1 | 305.8 | high |
| `cavalier_ear_L1` | 208.5 | 352.7 | high |
| `cavalier_ear_L2` | 179.1 | 400.8 | high |
| `cavalier_ear_R0` | 416.9 | 259.5 | high |
| `cavalier_ear_R1` | 452.1 | 327.0 | high |
| `cavalier_ear_R2` | 473.0 | 394.8 | high |
| `cavalier_shoulder` | 382.1 | 468.8 | low |
| `cavalier_elbow` | 385.9 | 515.7 | low |
| `cavalier_wrist` | 389.0 | 547.0 | medium |
| `phone` | 415.9 | 553.0 | high |

## Dubious
- cavalier_shoulder — long fur + phone occlusion; anatomical up-right of chest
- cavalier_elbow — no visible joint; geometric interp only
- cavalier_root — chest under duvet/fur; bright-band estimate
- cavalier_head — mask mid fell into muzzle; re-interpolated crown→nose
- ear_L mask starts y≈293; pink bow (~240,308) pins L0 (old L0 at 228,265 was off-mask)
