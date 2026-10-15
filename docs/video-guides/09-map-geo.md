# Guide Book 09：地图 / 地理讲解

在地图上画路线、标注地点、比较区域、做飞越镜头。用于旅行路线、物流、门店分布、新闻事件、历史迁徙等。

## 一、适用场景
- 路线动画（从 A 到 B）、地点逐个出现、区域着色。
- 地理数据讲解（与 03 数据讲解结合）。
- 山地、城市的 3D 飞越。

## 二、不适用
- 需要精确测绘或导航级精度：视频地图是示意。
- 不能联网、没有地图服务 key 且需要漂亮底图：只能用静态图方案。

## 三、实施流程
1. 选方案（RS `remotion-maps/REFERENCE.md`）：
   | 方案 | 特点 |
   |---|---|
   | Static map | 抓一张卫星图放 `<Img>`，在上面画动画 |
   | Mapbox | 需要 key，默认样式好看，缩远能显示球体，有 3D 建筑 |
   | MapLibre | 免费、不需要 key，没有 3D 建筑 |
   | MapTiler | 可以在边界、河流、标签等地理要素上做标注 |
   | CesiumJS | 地形、山脉飞越，“飞行模拟”视角 |
2. 准备地理数据：GeoJSON 路线、点位；MapTiler 方案有 `references/map-geo-prep.md` 和 `scripts/prep-geo.mjs`，Cesium 有 `scripts/prep-cesium-path.mjs`。
3. 写镜头路线：每个航点的中心和缩放。
4. 2D 平移缩放用“固定地图底板”（见技术要点）。
5. 先渲一小段 MP4 检查抖动，再做完整片。

## 四、技术要点
- **固定地图底板**（`maptiler/references/render-stability.md`，Mapbox / MapLibre 各有同名文件）：每帧调用 `map.jumpTo()` 会让底图闪烁抖动。正确做法是按最大缩放渲一次大底板、地图相机不动，每帧用 CSS `translate` + `scale` 移动底板，所有标注用同一个变换。
- 底板尺寸：最大边 ≤ 4096 px；1920×1080 用 3840×2160 是安全默认；CSS `scale` 不超过 1。放不下就拆成两个底板，用剪辑转场衔接。
- 俯仰角、方位角保持不变；需要真正变化的俯仰或地形飞越，改用 Cesium。
- 验证渲染：`--gl=angle`、`preserveDrawingBuffer: true`、并发数 1。
- 路线画出：GeoJSON 线按进度截断，或 SVG 路径 `stroke-dashoffset`。
- 讲解型架构：`maptiler/references/map-explainer-architecture.md`；数据来源：`maptiler/references/map-data-sources.md`；Cesium 3D：`cesium/references/3d-flyover-architecture.md`、`3d-troubleshooting.md`。

## 五、时间缓动与叙事
| 项 | 数字 | 来源 |
|---|---|---|
| 镜头曲线 | 最软，ease-in-out-quart | ML §3 |
| 长距离移动 | 超过屏幕 1/3 要加中间关键帧 | MDS 1/3 规则 |
| 距离换算 | 全屏移动 1.8–2.0× 基础时长 | MDS `reference/timing-easing-tables.md` |
| 点位依次出现 | 错开 50–100 ms，总预算 < 500 ms | MDS 错开表 |
| 每段航线 | 2–4 s（**起始值，需调**） | — |
| 地名停留 | ≥ 0.3 s/词 + 0.5 s | ML §3 |

叙事：先全景交代位置 → 推近讲细节 → 拉回总结。同一时间只让一条路线在画。

## 六、验收清单
- [ ] 渲成 MP4 检查，不只看 Studio 预览（render-stability.md 要求）。
- [ ] 平移时底图纹理没有闪烁；有就改用固定底板，不当成小问题放过。
- [ ] 推近时底图不发糊（CSS scale ≤ 1）。
- [ ] 标注和地图同步移动，没有漂移。
- [ ] 地名、边界没有政治敏感错误（人工核对）。

## 七、可借鉴资料
- **RS**：`remotion-markup/remotion-maps/REFERENCE.md`；`techniques/{static-map,mapbox,maplibre,maptiler,cesium}/TECHNIQUE.md`；`maptiler/references/render-stability.md`、`map-geo-prep.md`、`map-data-sources.md`、`map-explainer-architecture.md`；`cesium/references/3d-flyover-architecture.md`、`3d-data-sources.md`、`3d-troubleshooting.md`。
- **ML**：§1 渲染合同、§3 镜头曲线与视差、§9 终版运动模糊。
- **MDS**：1/3 距离规则、距离换算、`director/choreography.md`。
- **FR**：数据核对在先（地理数据同样适用）。
