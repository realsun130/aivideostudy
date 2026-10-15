# 风格候选库（Style Library Candidates）

> 目的：不只做宠物，覆盖「现代人有共鸣的短片」及解说/产品/文字动效等类型。
> 路线：图像模型出关键帧 + Remotion/代码动画，不用图生视频，成本优先。
> 本文件只是候选，**不改动现有 Style Bible**（`styles/rough-animation-pet-sketch-storyboard-style`，Style Lock 待定）。选定后再按 `style_bible.json` 结构单独映射。

## 来源
| 来源 | 链接 | 许可 | 规模 | 用法 |
|---|---|---|---|---|
| OpenMontage styles | https://github.com/calesthio/OpenMontage/tree/main/styles | AGPLv3 | 5 套 YAML（anime-ghibli / clean-professional / flat-motion-graphics / minimalist-diagram / premium-minimalist） | 只借字段思路（停留秒数、转场时长、弹簧、音量、闪避），文字为本文自述，不复制 |
| AI-Visual-Prompt-Cookbook | https://github.com/VigoZhao/AI-Visual-Prompt-Cookbook/tree/main/styles | MIT | 169 个 style.json（含 part-02 等分卷），多为静态海报风 | 画风锚点 + 提示词模板；动效参数需我们自己补 |

**OpenMontage 字段思路（自述）**：每套风格都把动效写成数字——最短/最长镜头停留、文字卡与数据卡停留、转场时长、入场/出场方式、弹簧或缓动类型、音乐音量（0.07–0.15）、闪避阈值（-2 到 -4 dB）、同屏颜色上限、对比度 ≥4.5:1、「生成图里不烧字，字由代码叠加」。这些是 Cookbook 缺的部分，候选表的「锁定参数」栏按这套补。

**Cookbook 扫描结论**：169 个里大半是运动/潮牌/杂志海报（megatype、fisheye、chrome、manga 等），适合封面和缩略图，不适合叙事短片。与「日常共鸣」相关的有：everyday-riso、sky-blue-home-life-doodle、cozy-bedroom-doodle-companion、urban-transit / metro-doodle diary、loose-scribble-riso、kinetic-geometric-doodle-cutouts、school-grid-paper-cutout、naive-marker-quote-card、memory-fragment-portrait、annotated-absence。

## 候选清单（13 个）
可行性：高 = 平涂/少色/大色块，易拆层、易用代码做位移/形变/叠纹理；中 = 需要多张关键帧交叉淡化或局部拆层；低 = 依赖真实照片或复杂光影，代码难动。指南编号见 `docs/video-guides/`。

### A. 现代共鸣短片
| # | 风格 | 来源 | 一句话画面 | 适配指南 | 情绪 | 可行性 | 需锁定的数字 | 风险 |
|---|---|---|---|---|---|---|---|---|
| 1 | Everyday Riso 日常孔版 | [Cookbook](https://github.com/VigoZhao/AI-Visual-Prompt-Cookbook/tree/main/styles/everyday-riso) | 奶油纸上三色油墨（橙/橄榄/近黑），圆胖小人做日常动作，一个物件被夸张放大，套印错位 + 网点 | 06、07、05 | 温暖、自嘲、轻幽默 | **高**：3 色平涂好拆层；错位/颗粒可代码实时叠加 | 色数=3+纸色；错位 1–3 px 随帧种子；颗粒强度；描边 0（色块为主）；弹簧中阻尼；停留 2.5–5 s | 角色一致性（同一小人多关键帧）；「物件放大」梗易重复 |
| 2 | Loose Scribble Riso 松散涂鸦孔版 | [Cookbook](https://github.com/VigoZhao/AI-Visual-Prompt-Cookbook/tree/main/styles/loose-scribble-riso-print-style) | 米白粗纸、单一大主体、抖动黑线，蓝+珊瑚红两色套印，手写边注 | 06、05、02 | 安静、孤独、诗意 | **高**：线稿可做 boiling line（每 2–3 帧换一次抖动种子） | 色数=2+黑；线宽 3–5 px@1080；抖动周期 2–3 帧；留白 ≥40%；慢缓出无回弹；停留 3.5–7 s | 太空会显得没做完；手写字须代码叠加 |
| 3 | Sky Blue Home Life Doodle 天蓝居家涂鸦 | [Cookbook](https://github.com/VigoZhao/AI-Visual-Prompt-Cookbook/tree/main/styles/sky-blue-home-life-doodle-poster-style) | 满屏天蓝底、白色房形内框、粗黑马克笔卡通居家场景、大号歪手写字 | 06、02、07 | 天真、治愈、家庭 | **高**：粗描边平涂，最适合拆层做骨骼/挤压 | 底色 1 + 黑 + 白 + 1 点缀；描边 6–8 px；字由代码画；弹簧轻回弹（overshoot ≤5%）；停留 2–4 s | 幼稚感，严肃题材不合适 |
| 4 | Kinetic Geometric Doodle Cutouts 几何剪纸涂鸦 | [Cookbook](https://github.com/VigoZhao/AI-Visual-Prompt-Cookbook/tree/main/styles/kinetic-geometric-doodle-cutouts) | 暖奶油底，角色由大块几何色片拼成 + 松散黑线 + 纸纹，构图偏心有动势 | 06、02、08、01 | 轻快、俏皮、都市 | **高**：每个色片就是一个图层，天然适合代码组装/拆散 | 色片 4–5 色；纸纹强度；黑线 2–3 px；弹簧偏活泼（参考 OpenMontage 快节奏档：回弹明显，转场 ~0.3 s）；停留 1.5–3 s | 情绪偏轻，难承载沉重题材 |
| 5 | School Grid Paper Cutout 方格纸撕纸 | [Cookbook](https://github.com/VigoZhao/AI-Visual-Prompt-Cookbook/tree/main/styles/school-grid-paper-cutout-poster) | 暖色作业方格纸 + 竖排手写 + 中央一个撕纸拼贴物，真实纸影 | 06、05、10 | 怀旧、成长、学生时代 | **中**：撕纸物件好拆，纸影需固定方向的代码阴影 | 网格间距固定；阴影角度/模糊 1 组；物件 ≤1 个/镜；停顿式 step 动画（12 fps 感）；停留 3–5 s | 网格与物件透视要一致；中文竖排字体需选定 |
| 6 | Naive Marker Quote Card 稚拙马克笔金句卡 | [Cookbook](https://github.com/VigoZhao/AI-Visual-Prompt-Cookbook/tree/main/styles/naive-marker-quote-card-style) | 粗黑马克笔描边、浅粉彩面板、块状蓝色字、歪标签，中间一个物件拟人小梗 | 02、07、06 | 荒诞、解压、打工人梗 | **高**：卡片式结构=天然分镜，字和标签全代码 | 粉彩 3 色 + 蓝字；描边 5–7 px；标签旋转 ±3–6°；入场弹出回弹；停留按字数 ≈ 0.25 s/字 + 1 s | 金句写不好就很空；系列感强但易审美疲劳 |
| 7 | Cozy Bedroom Doodle Companion 夜晚卧室涂鸦伙伴 | [Cookbook](https://github.com/VigoZhao/AI-Visual-Prompt-Cookbook/tree/main/styles/cozy-bedroom-doodle-companion-snapshot-style) | 低光居家照片 + 前景一只扁平 2D 布偶伙伴 + 屏幕微光 + 小手写涂鸦 | 06、10 | 深夜、独处、陪伴 | **中低**：底图是照片感，只能做推拉/光闪/前景伙伴动；伙伴层可代码动 | 底图仅 Ken Burns（缩放 ≤6%/镜）；屏幕光闪频率；伙伴描边 4 px；停留 4–7 s | 照片底图难统一；真人脸一致性 |
| 8 | Metro / Urban Transit Doodle Diary 通勤涂鸦日记 | [Cookbook](https://github.com/VigoZhao/AI-Visual-Prompt-Cookbook/tree/main/styles/metro-doodle-snapshot-diary-style)（姊妹：[urban-transit](https://github.com/VigoZhao/AI-Visual-Prompt-Cookbook/tree/main/styles/urban-transit-doodle-diary-style)） | 拥挤地铁实拍 + 马克笔卡通涂鸦叠加 + 白色手写日记字 | 10、06、08 | 通勤疲惫、都市烟火 | **中**：涂鸦层全代码手绘生长（stroke-dashoffset），照片层静止/慢推 | 涂鸦色 2–3 饱和色；描边生长 8–12 帧；白字描边；手持晃动幅度 ≤4 px；停留 2–4 s | 依赖照片素材（版权/自拍）；纯生成照片易假 |
| 9 | Memory Fragment Portrait 记忆碎片肖像 | [Cookbook](https://github.com/VigoZhao/AI-Visual-Prompt-Cookbook/tree/main/styles/memory-fragment-portrait) | 粗网点黑白肖像被白网格切开，部分格子换成褪色生活照，一格荧光粉关键记忆 | 05、06（片尾/高潮镜） | 怀念、亲情、失去 | **中**：网格翻转/替换非常适合代码；肖像和碎片需多张图 | 网格行列数；翻格节奏（stagger ≤500 ms 总长）；点缀粉 1 色；网点大小；停留 4–6 s | 只适合单个高潮镜，不能撑整片 |
| 10 | Annotated Absence 标注的缺席 | [Cookbook](https://github.com/VigoZhao/AI-Visual-Prompt-Cookbook/tree/main/styles/annotated-absence) | 照片主体渐渐褪成白纸上的手描轮廓 + 小写词标签 + 灰色残片 | 06、05 | 留白、失落、反思 | **中高**：「照片→线稿」可用遮罩擦除做，标签代码写 | 灰阶 + 黑线；擦除时长 1–2 s；标签字号/位置；无回弹；停留 4–7 s | 情绪很重，节奏慢，短视频平台留存风险 |

### B. 解说 / 数据 / 产品 / 文字动效
| # | 风格 | 来源 | 一句话画面 | 适配指南 | 情绪 | 可行性 | 需锁定的数字 | 风险 |
|---|---|---|---|---|---|---|---|---|
| 11 | Minimalist Diagram 极简图解 | [OpenMontage](https://github.com/calesthio/OpenMontage/blob/main/styles/minimalist-diagram.yaml) | 近白纸底、深藏青线条、一点红强调，可带手绘线质 | 03、05、09 | 专注、清楚 | **高**：纯矢量 | 色数 ≤4；留白 ≥30%；缓出无回弹；每步图解停留 ≥3 s；转场 ~0.5 s；音乐极低 | 太素；需要拆题卡先做好 |
| 12 | Premium Minimalist 高级极简 | [OpenMontage](https://github.com/calesthio/OpenMontage/blob/main/styles/premium-minimalist.yaml) | 米白底、炭黑字、一抹钴蓝，杂志式非对称网格，一镜一个焦点 | 04、03、01、05 | 冷静、可信 | **高** | 同屏强调色 ≤2；入场上移 ~12 px 淡入；无回弹；停留 2.75–12 s；转场 ~0.45 s；音乐 ~0.07 | 易变成「企业蓝模板」——它自己列为反模式 |
| 13 | Flat Motion Graphics 扁平动效 | [OpenMontage](https://github.com/calesthio/OpenMontage/blob/main/styles/flat-motion-graphics.yaml) | 深石板底、紫/粉/青高饱和几何平涂 | 02、08、04、01 | 有劲、年轻 | **高** | 同屏 ≤4 色；强回弹弹簧；转场 ~0.3 s；每 2–3 s 一个新元素；每次大转场配音效 | 很「模板味」，和共鸣短片调性冲突 |

另参考（未入选）：OpenMontage 的 **anime-ghibli**（水彩、慢、多图交叉淡化模拟运动，可行性中低，且有借名风险）和 **clean-professional**（企业蓝，和 #12 重叠）；Cookbook 的 **monochrome-tech-grid-editorial**（适合 03/09 的标题卡）、**acid-burst-motion-type** 等运动海报类（只适合封面）。

## 推荐：现代共鸣短片前三
1. **Everyday Riso（#1）**——最平衡。三色平涂 + 纸纹，拆层和代码动画成本最低；「普通人 + 一个被放大的物件」本身就是共鸣短片的叙事钩子（被放大的手机、堆成山的工作邮件、巨大的闹钟），一个风格就能做成系列。
2. **Loose Scribble Riso（#2）**——负责安静、孤独、城市夜晚这类情绪。两色 + 抖动线条，boiling line 用代码几乎零成本就有「活着」的手绘感，留白多，生成关键帧失败率低。
3. **Kinetic Geometric Doodle Cutouts（#4）**——负责轻快、节奏感、卡点类（08）。角色由色片组成，代码可以拆开再拼回，转场天然好看，和前两个形成「暖/静/动」三档。

备选：要做家庭/治愈题材换 **#3 天蓝居家涂鸦**；要做金句/打工人梗系列用 **#6 金句卡**；高潮回忆镜头穿插 **#9 记忆碎片**。

## 下一步（未做）
- 选 1 个后，按 `style_bible.json` 结构映射到 `styles/<slug>/`，并按 OpenMontage 字段思路补一份动效节奏配置（停留、转场、弹簧、音量、闪避）。
- 每个入选风格先出 1 张关键帧 + 3 s 代码动画样片，再定 Style Lock。
