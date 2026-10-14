# Frame 01 · 代码叠层实验计划（Step 1）

> 目标：把「整图重绘抽卡」改成「锁定底图 + 可命名道具叠层」，局部改只动参数，不再整帧重抽。

## 0. 首选路径（2026-10-14 更新）：Vision → 风格配方卡

用户验证后的先进流程（对齐 [huashu-art-motion](https://github.com/alchaincyf/huashu-art-motion)）：

1. **生图锁定帧**（视觉基调）→ 本实验以 **V8** 为 Vision 源：`frame_01_s01_hero_v8.jpg`
2. **Vision 拆解** → 几何元素 / 图层 z-order / 爪灯主光 / 道具 / 运动热图
3. **风格配方卡（Recipe）** → 存入 `projects/first-frame/recipes/`，作为同类镜头护城河
4. **代码按配方合成** → 只动 `editable_params`（发卡、合影领结、手机背面、爪灯强度）；**角色像素保留锁定帧**

| 产物 | 路径 |
|------|------|
| Vision 拆解 | [`recipes/v8_breakdown.md`](recipes/v8_breakdown.md) |
| 机读配方 | [`recipes/v8_style_recipe.json`](recipes/v8_style_recipe.json) |
| 人读配方卡 | [`recipes/v8_style_recipe.md`](recipes/v8_style_recipe.md) |

**明确降级**：`code_assets/render_cavalier.py` 椭圆自由手绘角色 = 草稿玩具，**不是**最终角色路径。禁止用椭圆代码体替换 V8/V9 锁定角色。


## 1. 第一步就是：抽素材 → 代码化

是的。本实验 **Step 1** 只做两件事：

1. **提取**：从指定源图粗裁可编辑元素，写入 `assets/`（当前全部为 `status: rough_crop`，矩形裁切，**无透明蒙版、不臆造像素**）。
2. **登记**：用 `assets/manifest.json` 记录每个资产的 `id / path / bbox / z_order / source_version / editable_params`。

之后 Step 2 才写真正的合成脚本（Pillow / Canvas / Remotion）。

## 2. 混合路线（Hybrid）

参考 [huashu-art-motion](https://github.com/alchaincyf/huashu-art-motion) 的思路：

| 层 | 谁负责 | 本帧对应 |
|----|--------|----------|
| 角色底图 / 素描气质 | 图像模型出帧（一次锁定） | `base_plate`（v9 全帧）+ `live_maine_coon`（v8）+ `cavalier_subject`（v9） |
| 世界道具 / 灯光 / 可改配件 | **代码叠层** | `paw_lamp`、`phone_back`、`cavalier_ear_bow`、`wall_photo`、合影内领结/发卡 ROI |
| 运动 / 时间线 | 代码（后续 Bot D / Remotion） | 暂不实现；本计划只定图层契约 |

原则：

- **AI 出角色与氛围一次**，不要为改领结/灯/手机朝向再整图抽卡。
- **道具与配件参数化**：可见性、位移、缩放、灯光强度、手机朝向锁等只改 `editable_params`。

## 3. 源图锁定（用户更正）

| 资产 | 源版本 | 原因 |
|------|--------|------|
| `live_maine_coon` | **v8** | 床上缅因主体以 v8 为准 |
| 其余全部（底图、查理王、手机、猫爪灯、墙照合影、发卡等） | **v9** | 其余锁定 v9 |
| `frame_01_s01_hero.jpg`（v10 像素修） | 仅作对照 | **本实验不作为抽取源** |

源文件：

- v8：`projects/first-frame/frame_01_s01_hero_v8.jpg`
- v9：`projects/first-frame/frame_01_s01_hero_v9.jpg`

## 4. 编辑锁（Edit Lock）

规则写进 `manifest.json` 的 `edit_lock_rule`：

> **只改具名资产 / 具名参数；未点名的像素一律保持 `base_plate` 不变。**

对应产品话术：

- 「去掉床上缅因领结」→ 只动 `live_maine_coon`（或该层上的领结子参数），不动查理王/灯/手机。
- 「合影缅加黑领结」→ 只动 `photo_bowtie_black`（或在该 ROI 上用代码画领结），不动合影其余。
- 「手机拿反」→ 只动 `phone_back.orientation_lock` / `rotation_deg`。

手机约定（`phone_convention`）：「玩手机」= 看得见脸 + **手机背面朝镜头**，镜头模组朝床头（上）。

## 5. 图层与 z-order（当前）

从后到前（见 `assets/manifest.json`）：

0. `base_plate`（v9 全帧）
1. `wall_photo`
2. `photo_ear_bow_pink` / `photo_bowtie_black`（合影内 ROI）
3. `live_maine_coon`（**v8**）
4. `cavalier_subject`（v9）
5. `cavalier_ear_bow` / `paw_lamp`
6. `phone_back`（最前道具之一）

主层（缅因/查理王/手机/爪灯/合影）已有 **`alpha_rembg`** 透明 PNG（自 V8）；其余 ROI（发卡/合影领结槽）仍为 rough_crop。rembg 非精修，毛边/合并仍在。

### 已知缺口

- `photo_bowtie_black`：v9 合影缅因胸前未必已有清晰黑领结（黑领结曾在 v10 手修）。本层是 **编辑槽位 ROI**，后续可用代码画参数化领结，**禁止用模型补像素冒充**。
- 画幅：源图为 **1280×720（16:9）**；提示词曾要 9:16。合成器后期可 letterbox/裁竖屏，不在 Step 1 强改源图。

## 6. 目录结构

```text
projects/first-frame/
  COMPOSITOR_PLAN.md          ← 本文件
  frame_01_s01_hero_v8.jpg    ← Vision 源 + 缅因抽取源
  frame_01_s01_hero_v9.jpg    ← 其余抽取源
  recipes/                    ← Vision→配方护城河（首选）
    v8_breakdown.md
    v8_style_recipe.json
    v8_style_recipe.md
  scripts/
    rembg_cut.py              ← rembg 自动抠透明层
    requirements-rembg.txt
  assets/
    manifest.json
    sources/SOURCES.md
    base/base_plate_v9.jpg
    layers/                   ← rough_crop jpg（保留）
    layers_alpha/             ← rembg RGBA PNG（V8）
      v8_full_rgba.png
      live_maine_coon.png
      cavalier_subject.png
      phone_back.png
      paw_lamp.png
      wall_photo.png
```

## 7. 接到 Bot D / Remotion

后续映射建议：

| 本实验 | Bot D / Remotion |
|--------|------------------|
| `manifest.json` 资产 | `<AbsoluteFill>` / `<Img>` / 自定义 Prop 组件的 `src` + `style` |
| `bbox` + `z_order` | `left/top/width/height` + 组件树顺序 |
| `editable_params` | Remotion 输入 props / spring 动画参数 |
| `base_plate` | 时间线第 0 层静帧或 `<OffthreadVideo>` 占位 |
| `paw_lamp.glow_intensity` | 叠加 `mix-blend-mode` / 径向渐变光层 |
| `phone_back.orientation_lock` | 断言：不允许 screen-facing；旋转只在锁内 |

Bot D 仍负责「镜头表 → 时间线 → 成片」；本实验只保证 **单帧可参数改图**，避免为配件再走图像模型。

## 8. rembg 透明层（已完成）→ 下一步合成器

**rembg 已跑通（2026-10-14）**：

- 脚本：`scripts/rembg_cut.py`（依赖见 `scripts/requirements-rembg.txt`）
- 源：仅 **V8** 全帧 + manifest bbox 分块
- 产物：`assets/layers_alpha/*.png`；manifest 对应层 `status: alpha_rembg` + `alpha_path`
- 诚实：全帧易合并主体；分块仍有床品/毛边出血，非正式精修

**合成器 v1（已完成 2026-10-14）**：

- 脚本：`scripts/compose_from_recipe.py`
- 读：`recipes/v8_style_recipe.json` + `assets/manifest.json`（优先 `alpha_path`）→ 按 bbox/z_order Pillow 叠层
- 默认可调：`--paw-lamp-intensity`、`--hide`、`--overlays-only`、`--no-photo-bowtie`、`--base v9|v8|none`
- 默认输出：`code_assets/out/compose_v8_recipe_v1.png`
- 诚实缺口：底图烘焙角色 + 再叠角色 alpha 会重影（日常改道具请用 `--overlays-only`）；matte 未精修；无动画

**下一步**：

1. 精修 matte / 去角色底图，消除双重曝光。
2. 回归：只改 `photo_bowtie` / `paw_lamp_intensity` → 像素 diff 只落在 ROI / 光晕。
3. Remotion `<Frame01>` 镜像 `editable_params` + `glow_pulse`。

---

*Step 1 完成标志：`assets/manifest.json` 存在，且每个可改元素有路径 + bbox + source_version + editable_params。*


## 9. 路径优先级（必读）

| 优先级 | 路径 | 状态 | 用途 |
|--------|------|------|------|
| **P0 · 首选** | **Vision → Recipe → 代码叠层** | ✅ V8 配方已写入 `recipes/` | 最终生产路径：锁定角色帧 + 参数改道具/光 |
| P1 | `assets/` 粗裁 + rembg + compose | ✅ rembg + compose v1 | ROI / bbox + `layers_alpha/` + `compose_from_recipe.py` |
| P2 · 降级 | `code_assets/render_cavalier.py` 椭圆重画 | ⚠️ 已做但观感灾难 | **仅作几何草稿 / 教学**；不得替换锁定英雄帧 |

原则（更新后）：

- **AI 出角色与氛围一次并锁定**（V8/V9），不为改领结/灯/手机整图抽卡。
- **Vision 拆解写入 Recipe**，护城河在 JSON，不在口头 prompt。
- **道具与光参数化**：`ear_bow` / `photo_bowtie` / `phone_back` / `paw_lamp_intensity`。
- **禁止**用椭圆拼形冒充最终查理王/缅因。

`code_assets/` 仍可保留作「线条原语试验床」，但合成器默认读取 `recipes/v8_style_recipe.json` + `assets/manifest.json`。

