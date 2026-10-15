# 代码视频 Guide Books 索引（Remotion）

每类视频一本独立的 Guide Book，章节统一为：适用场景 / 不适用 / 实施流程 / 技术要点 / 时间缓动与叙事 / 验收清单 / 可借鉴资料。

## 引用约定
- **ML §n**：本仓库 `docs/MOTION_LESSONS.md` 第 n 节。
- **MDS**：LottieFiles/motion-design-skill，路径相对 `skills/motion-design/`。注意：它的时长表是按界面元素（按钮、卡片、弹窗）写的，角色表演和叙事节拍要更长。
- **RS**：remotion-dev/skills，路径相对 `skills/remotion-best-practices/`（如 `remotion-markup/timing.md`）。
- **BDAY**：Motion Lab「Birthday Surprise」Prompt Pack（BRAND / FORMAT / LOOK / BEATS / CAMERA / CHECKS）。
- **FR**：Francesco 的文章（数据间 / 动效间 / 剪辑间；参考 → 数据 → 留空位的故事 → 动效 → 用话导演 → 组装）。
- 标注「**起始值，需调**」的数字不是出自资料，是第一次渲染用的起点，按帧号调整。

## 通用前提（所有类型）
1. 渲染合同 ML §1：画面只由帧号决定，随机数带种子，循环片只渲 0..N−1。
2. RS 默认做法：先开 Studio 预览、不明确要求就不渲染、发现手改代码就保留。
3. 动画用 `interpolate()` 加 `Easing.bezier` / `Easing.spring`（RS `remotion-markup/timing.md`），不另起 GSAP 时钟（ML §6）。
4. 迭代期只出静帧和联系表（ML §5），终版才开运动模糊（ML §9）。

## 目录

| # | 类型 | 典型时长 | 核心难点 | 文件 |
|---|---|---|---|---|
| 01 | Logo 片头 / 品牌开场 | 3–8 s | 一个记忆点 + 落版停留，克制不炫技 | [01-logo-intro.md](01-logo-intro.md) |
| 02 | 动态文字（Kinetic Typography） | 10–60 s | 阅读时间与节奏的平衡，字测量与排版 | [02-kinetic-typography.md](02-kinetic-typography.md) |
| 03 | 数据讲解 / 动态图表 | 20–90 s | 数字正确、可追溯，动画服务于结论 | [03-data-explainer-charts.md](03-data-explainer-charts.md) |
| 04 | UI / 产品演示 | 15–60 s | 光标与界面状态同步，注意力引导 | [04-ui-product-demo.md](04-ui-product-demo.md) |
| 05 | 解说视频（配音 + 字幕） | 30 s–5 min | 画面跟着配音长度走，字幕对齐 | [05-explainer-narrated.md](05-explainer-narrated.md) |
| 06 | 角色短片 | 8–30 s | 表演、光、镜头与反应时机 | [06-character-short.md](06-character-short.md) |
| 07 | 无缝循环 / 贴纸 / GIF | 1–6 s | 首尾无缝、透明通道、文件体积 | [07-seamless-loop-sticker.md](07-seamless-loop-sticker.md) |
| 08 | 音乐卡点 / 可视化 | 10–60 s | 节拍网格精确、不累积误差 | [08-music-beat-sync.md](08-music-beat-sync.md) |
| 09 | 地图 / 地理讲解 | 10–60 s | 底图抖动、镜头路径、地理数据准备 | [09-map-geo.md](09-map-geo.md) |
| 10 | 实拍素材辅助（剪辑 + 图形包装） | 30 s–10 min | 素材时长、静音裁剪、图形与人物同步 | [10-live-footage-assist.md](10-live-footage-assist.md) |
