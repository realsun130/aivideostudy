# Guide Book 07：无缝循环 / 贴纸 / GIF

1–6 秒、首尾无缝接上的循环动画：表情贴纸、加载动画、网页背景、社交平台 GIF、展会屏幕循环。

## 一、适用场景
- 聊天贴纸、表情包、头像动画。
- 网页或屏幕背景循环、加载动画。
- 需要透明背景叠到别处。

## 二、不适用
- 有开头和结尾的故事：用 01 或 06。
- 很长的循环（> 10 s）：GIF 体积会爆，改 MP4 / WebM 循环。

## 三、实施流程
1. 定周期 N 帧（如 60fps × 2 s = 120 帧），所有运动写成相位 `phase = frame / N` 的函数（ML §1）。
2. 每个周期运动用整数圈：`sin(2π × k × phase)`，k 为整数。
3. 只渲 0..N−1，不渲第 N 帧（ML §1）。
4. 确定输出：透明 WebM / ProRes 4444，或 GIF，或 MP4。
5. 拼成“最后一帧 + 第一帧”对比，检查接缝。

## 四、技术要点
- 循环：组件内部只依赖 `phase`；带种子的噪声也要用周期化的输入（比如在圆上采样噪声），不然首尾不接。
- 透明输出：`remotion-render/transparent-videos.md`（ProRes 4444 或 WebM VP9）。
- GIF 导出要求（ML §7 导出）：全片单一调色板；24 fps 时帧延迟按 40,40,40,40,40,50 ms 循环，防止漂移；X 的 GIF 上限 350 帧。
- 在别的作品里引用 GIF / APNG / WebP：`remotion-markup/gifs.md`（这是“显示动图”，不是导出）。
- Lottie 素材可以嵌入：`remotion-markup/lottie.md`。
- 慢速有机形变（液态金属一类）终版只开抗锯齿采样，不要开满快门（ML §9）。

## 五、时间缓动与叙事
| 项 | 数字 | 来源 |
|---|---|---|
| 循环缓动 | sine ease-in-out；线性只给旋转和循环相位 | MDS / ML §3 |
| 环境类时长 | 2000–20000 ms | MDS `reference/timing-easing-tables.md` |
| 呼吸 / 漂浮 / 视差 / 闪光 / 粒子 | 见配方 | MDS `patterns/ambient-continuous.md` |
| 下雪粒子 | 10–20 个，20–60 px/s 向下，±10–20 px 漂移 | MDS `patterns/ambient-continuous.md` |
| 视差 | 前 1.0 / 中 0.5 / 后 0.2 | ML §3 |
| 闪烁 | ≤ 3 次/秒 | ML §3 |
| 贴纸周期 | 1–2 s（**起始值，需调**） | — |

叙事：循环也是一个微故事——起势、峰值、回落（MDS Setup → Action → Resolution），回落的状态必须正好等于起势。

## 六、验收清单
- [ ] 第 0 帧与“第 N 帧”逐像素一致（渲第 N 帧只用于检查，不放进成品）。
- [ ] 连续播放 5 圈看不出接缝。
- [ ] 透明版边缘无黑边、无白边。
- [ ] GIF 体积符合平台限制；色带可接受。
- [ ] 开了运动模糊后，首尾仍无缝（ML §9 验收）。

## 七、可借鉴资料
- **ML**：§1（只渲 0..N−1、相位整数圈）、§7 导出（GIF 调色板、帧延迟、350 帧上限）、§9（循环片采样后仍须无缝；慢形变只开抗锯齿）。
- **MDS**：`patterns/ambient-continuous.md`（呼吸、漂浮、渐变、视差、旋转、闪光、粒子）、循环用 sine 的方向规则、材质表（液体 1.5×、回弹 5%）。
- **RS**：`remotion-render/transparent-videos.md`、`remotion-markup/lottie.md`、`gifs.md`、`motion-blur.md`。
