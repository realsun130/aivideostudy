# Frame 01 · 代码重绘实验（查理王 Cavalier）

参考 [huashu-art-motion](https://github.com/alchaincyf/huashu-art-motion)：**风格配方 → 参数化绘制 → 确定性再渲**，不走图像模型抽卡。

本目录是第一只代码素材：**拟人查理王（主体）**。

## Style Bible → 代码参数

源文件：`styles/rough-animation-pet-sketch-storyboard-style/style_bible.json`

| Style Bible | 代码落点 |
|-------------|----------|
| `palette.background` / warm_beige `#E8DCC8` | 纸底 + 中等颗粒（`make_paper`） |
| `palette.accent.red_brown_pencil` `#8B4513` | 红棕结构线（construction ellipses / ticks） |
| `palette.accent.dark_burgundy_ink` `#4A1525` | 多层抖动轮廓（`scratchy_*`） |
| cream / soft_tan / pale_peach | 半透明水色毛发块（`watercolor_*`，alpha &lt; 1） |
| `line.style=sketchy` + variable weight | 多 pass + jitter + 修正偏移 |
| `texture.paper` + `grain=medium` | 纸噪 + 淡 vignette |
| `character_lock`：巨大椭圆眼、小瞳孔 | `draw_face` 固定几何，不读参考像素 |
| `composition.layer_order` | 纸 → 结构线 → 水色 → 轮廓 → 五官 → 道具/发卡 |

CLI 开关（不改 Bible 也能改「这一次」）：

| 参数 | 含义 | 默认 |
|------|------|------|
| `--expression` | `laughing` / `neutral` / `smile` | `laughing` |
| `--show-phone` / `--no-show-phone` | 手机**背面**朝镜头，镜头模组朝上 | on |
| `--show-ear-bow` / `--no-show-ear-bow` | 粉色发卡在**右耳根**（画面左侧） | on |
| `--aspect` | `1:1` / `9:16` / `16:9` | `1:1` |
| `--size WxH` | 覆盖宽高 | — |
| `--seed` | 潦草笔触种子（同 seed = 同像素） | `42` |

## 怎么跑

```bash
cd /path/to/animation-pipeline   # 或本仓库根目录

# 默认：大笑 + 手机背面 + 粉色发卡 → out/cavalier_code_v1.png
python3 projects/first-frame/code_assets/render_cavalier.py

# 同时出 9:16 竖板
python3 projects/first-frame/code_assets/render_cavalier.py --also-9x16

# 只改表情 / 关掉道具
python3 projects/first-frame/code_assets/render_cavalier.py \
  --expression neutral --no-show-phone --out projects/first-frame/code_assets/out/cav_neutral.png
```

依赖：Python 3 + Pillow（已在环境里可用）。

## 输出

| 文件 | 说明 |
|------|------|
| `out/cavalier_code_v1.png` | 1024×1024 主静帧 |
| `out/cavalier_code_v1_9x16.png` | 720×1280 竖板（`--also-9x16`） |

## 目录

```text
code_assets/
  README.md                 ← 本文件
  render_cavalier.py        ← CLI + 查理王绘制
  lib/
    style_params.py         ← 读 Bible 调色板
    sketch_draw.py          ← 纸/水色/潦草线原语
  out/
    cavalier_code_v1.png
    cavalier_code_v1_9x16.png
```

## 诚实质量说明

- **成功点**：可识别的素描风查理王；巨大眼+小瞳孔；粉色发卡位置对；手机背面+顶部镜头模组；同 `--seed` 像素级可复现。
- **未追求**：与 v9 裁切像素对齐（任务明确不要求）；毛发仍是椭圆水色块，不是真实长耳卷毛；身体偏「两个椭圆」几何感，故事板完成度够、精修卡通不够（这符合 Bible「未完成感」）。
- **和抠图路线的关系**：这条是 **纯代码重画**，不依赖 `assets/layers/*` 的矩形粗裁；粗裁库仍可用于混合合成对照。

## 合成器（recipe + rembg）

静帧合成已接到 `scripts/compose_from_recipe.py`：读 `recipes/v8_style_recipe.json` + `assets/layers_alpha/`，按 manifest bbox/z_order 叠层。

```bash
python3 projects/first-frame/scripts/compose_from_recipe.py
# 改参数示例（少重影用 --overlays-only）
python3 projects/first-frame/scripts/compose_from_recipe.py \
  --overlays-only --paw-lamp-intensity 1.3 --hide phone_back
```

输出：`out/compose_v8_recipe_v1.png`。说明见 `scripts/README.md`。

## 下一步

1. 精修 rembg matte（或二次抠）减少床品粘连；底图去角色版 plate，避免双重曝光。
2. 发卡 / 合影领结独立透明层或纯代码画（合成器已支持参数黑领结开关）。
3. 读 recipe `layer_motion_rules` 出短循环（glow_pulse），接 Remotion。
4. 椭圆查理王草稿仅作对照；正式角色像素继续锁 v8/v9 plate。

---

*与 `COMPOSITOR_PLAN.md` 同步：代码重绘路径已从查理王起步。*
