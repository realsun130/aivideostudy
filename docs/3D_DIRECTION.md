# 3D 方向备忘（⚠️ 待测试 / 备忘未实施）

> 本文全部内容为备忘，尚未实施、未验证。不属于主流程。验证通过的条目再逐条去掉标记。

## 1. 何时考虑 3D

来源：对《此路未命名》（北京动画周 24h AIGC 挑战赛作品）的镜头分析。2D 代码路线做不好的是 **3D 透视下的复杂动作**：
- 两人旋转跳华尔兹；
- 狗转身、扑球、猛冲；
- 被狗拖着跑。

**先试 2D 绕行方案，不行再上 3D：**
- 剪影 + 几个关键姿势 + 镜头环绕（跳舞）；
- 侧面卷轴视角 + 固定步态循环（遛狗、奔跑）。

## 2. Blender 的角色

- 免费开源；Python `bpy` 可完全脚本控制，可无头（`blender -b`）渲染，兼容代码路线。
- Grease Pencil 与卡通 / NPR 着色（Toon shader、描边）可渲染成手绘 / 插画观感。
- 定位：**按镜头使用的渲染器**，输出分层图像序列（带 alpha 的 PNG），交给 Remotion 合成。
- 渲染在用户 Windows 本机 RTX 4060 Laptop 上进行（win-setup 尚未完成）。
- 暂不纳入主流程。

## 3. 动作库（许可已核实，标 ⚠️ 的未核实）

### 人物：可商用
| 库 | 许可 | 备注 |
|---|---|---|
| Mixamo（Adobe） | 项目中免版税使用 | 不得再分发原始文件 ⚠️；自带自动绑骨，偏游戏风 |
| 100STYLE | CC BY 4.0 | 需署名；同一走路 100 种风格，适合有性格的日常人物 |
| CMU Mocap | 免费，含商用 | 约 2600 段，数据老、有噪声需清理 |

### 人物：避开
- Bandai Namco Motiondataset：CC BY-NC
- Ubisoft LAFAN1：CC BY-NC
- AMASS / HumanML3D / SMPL：非商用
- 文字生成动作：MDM、MoMask、MotionGPT（代码 MIT，但训练于 HumanML3D → 灰色）；HY-Motion 自定义许可 ⚠️。**仅限打草稿，不进成片。**
- Rokoko / ActorCore 免费动作包：⚠️ 未核实

### 猫狗
- 未找到可商用的开源猫狗动作捕捉数据。
- Starke MANN 狗数据（AI4Animation）：仅限研究。
- Quaternius 动画动物包：CC0 类，免费商用，低多边形；是否含猫 / 狗 ⚠️ 待确认。
- Truebones 动物动作包：付费 ⚠️。
- Sketchfab：CC0 需逐个确认。
- Kenney：多为静态模型。

## 4. 工具
- Blender 内置 BVH 导入。
- Rigify（含四足模板）。
- Rokoko Studio Live 插件：LGPL-3.0，用于动作重定向。
- Auto-Rig Pro：付费约 $40 ⚠️。

## 5. 尝试顺序（提议实验 + 通过标准）

| 编号 | 实验 | 通过标准 |
|---|---|---|
| E1 | Windows 装 Blender，`bpy` 无头渲染一个卡通着色立方体 PNG 序列 | 命令行一条命令出完整序列，无需打开界面 |
| E2 | Mixamo 走路套到卡通角色，带 alpha 渲染后在 Remotion 合成 | 透明背景正确、边缘无黑边，合成后与 2D 背景帧对齐 |
| E3 | Rigify 四足 + 代码步态循环，猫走路 3 秒 | 按 MOTION_LESSONS 第 10 节数字：无滑步，着地帧锁定 |
| E4 | 同一镜头对比 3D 与 2D 路线 | 记录耗时、成本、观感，人工选定并写入决策日志 |

## 6. 署名与许可规则
- CC BY 素材写入 `assets_credits.json`。
- NC 素材在代码中拦截禁用，与 Openverse 规则一致（见 MOTION_LESSONS §7）。
