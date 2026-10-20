# 风格参考案例：故事短片 + 历史／文化（AO55B，可选参考 ⚠️ 待测试）

> **这只是一份灵感目录，不是流程，也不是标准。** 每条案例都是可选参考，做片时可以完全不看、不用。想找某类内容的画面参考时，按下面的「内容类型」和「画风」筛一下即可。
> 新增内容，按约定标 ⚠️ 待测试；在至少一次 Track S 跑通前，本文件冻结，只做纠错。

## 来源与许可

- **AO55B**：[athemeroy/awesome-claude-5-5-videos](https://github.com/athemeroy/awesome-claude-5-5-videos)（原名 `awesome-opus-5-5-videos`，旧链接 GitHub 会自动跳转）。文字与图表为 **CC BY 4.0**；本文是对其 `docs/domain-style-atlas.zh-CN.md`、`docs/cases-index.zh-CN.md`、`docs/library.zh-CN.md` 与 `data/cases.csv`、`data/domain-style.csv`、`data/claude55-source-review-*.csv` 的**摘译和删改**，按 CC BY 4.0 署名：© athemeroy 及贡献者，[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。快照取自其 2026-10-11 提交 `87e5cbf`。
- **案例视频与截图的权利归原作者**。这里只放链接，不复制截图或 MP4。
- **和 AO55 的区别**：AO55 是 [yihui-dev/awesome-opus5-5-videos](https://github.com/yihui-dev/awesome-opus5-5-videos)（MIT），是我们讲解类 03/05/09 的可选参考。两个仓库在 GitHub 上都不是 fork（`fork=false`，AO55B 建于 2026-09-25，AO55 建于 2026-09-27）。两者之间是否有镜像或改编关系，从公开信息无法核实，所以这里按两个独立来源处理。

## 使用这些案例前要知道的三条限制（来自 AO55B 原文）

1. **九帧抽样**：仓库只从每条 X 预览视频里抽 9 帧来审读，所以无法验证完整动作、声音，也看不到隐藏的模型调用。
2. **作者自述未经核实**：「一次生成」「零素材」「花了多少钱多少小时」都是作者自己说的，没有源码、账单或日志佐证。
3. **点赞不代表效果**：赞数和浏览数是某一时刻（2026-09-27）的 X 帖子数据，受发帖时间、粉丝量、转发影响，**不能**拿来证明哪种画风、配色或做法更受欢迎。

## 字段说明

- **制作路径**（AO55B 原分类）：`procedural_2d` 程序逐帧绘图；`educational_explainer` 知识讲解；`3d_or_realtime_graphics` 三维与实时图形；`existing_source_transformation` 改编现有素材（参考片、照片、录音等）；`external_video_model` 外部视频模型出最终画面；`mixed_or_not_established` 混合或流程不明。
- **画风**：AO55B 的主画风标签（`style`），每条只算一个。
- **作者披露**：作者自己说的做法，已压缩并译成中文；原文见 AO55B 的 `data/cases.csv`。
- **审读边界**：AO55B 审读者的提醒。

---

## A. 故事短片（story_short）

AO55B 统计（2026-09-26 分类截点）：故事短片里扁平卡通 37 个文件、三维 21 个、像素 12 个、纸片拼贴 12 个、水墨／油彩 9 个、手绘 7 个、动漫 7 个、写实 3 个、动态图形 1 个。以下是其中已人工深读的案例。

| 画风 | 案例 | 制作路径 | 作者披露（摘要） | 审读边界 |
|---|---|---|---|---|
| 扁平卡通 | [@cherry_mx_reds 小怪物蹦跳够糖](https://x.com/cherry_mx_reds/status/2102472218269900876)（30 s） | procedural_2d | 自称 18 分 31 秒一次成片、不用框架的纯代码；但回复里也承认提示带了一张图，磁盘上已有之前的动画文件 | 「单轮提示」也可能受图片和工作区文件影响 |
| 扁平卡通 | [@cherry_mx_reds Oktoberfest](https://x.com/cherry_mx_reds/status/2102493303388475855)（30 s） | procedural_2d | 提示截图里附了角色图，要求 30 秒，并让模型用磁盘上已有的音效采样，不要合成 | 不是零图片，也不是零音频素材 |
| 扁平卡通 | [@ctgptlb 女孩与小机器人](https://x.com/ctgptlb/status/2102726428991373480)（64 s） | procedural_2d | 无图片素材、逐帧代码画面，人一共给了 6 条指令 | 6 轮人工指令，不是一次生成 |
| 扁平卡通 | [@yaakuups 红手套无声短片](https://x.com/yaakuups/status/2103082248320766456)（138 s） | procedural_2d | 自称一次提交、无修订；提示规定无对白无字幕、要有高潮和情绪结尾、「不能只是几件物品的幻灯片」，角色、环境、相机、时间、物理一起叙事 | 文字不长，但叙事和质量约束给得很足 |
| 扁平卡通 | [@onofumi_AI 星星与猫](https://x.com/onofumi_AI/status/2102535945333657960)（18 s） | procedural_2d | 只说「想做动画视频」，零图片／音频输入，视频生成额度为零 | 视频生成额度为零，不代表没有算力或 Claude 成本 |
| 扁平卡通 | [@samspike_ 《终局》改编](https://x.com/samspike_/status/2103171975220781332)（323 s） | procedural_2d | 几千行 Python 画面，ElevenLabs 配音 | 长篇改编有连贯性和版权问题，抽帧看不出来 |
| 三维 | [@Hesamation 2076 年孤独机器人](https://x.com/Hesamation/status/2103457566978162901)（88 s） | procedural_2d | 故事、动画、音效、音乐都由 Claude 做，JavaScript 编码 | 无法验证音效、音乐的来源 |
| 三维 | [@akokoi1 fight](https://x.com/akokoi1/status/2103149275945517546)（60 s） | 3d_or_realtime_graphics | 约 2,000 行代码；[作者补充](https://x.com/akokoi1/status/2103149539880562718)三步：**先用 Three.js 做角色并调到满意**，再基于这个模型要 60 秒电影感打斗，最后加声音导出 | 正式出片前有人工验收角色这一步 → 见[角色动画尝试方向](character-animation-routes.md) (a) |
| 三维 | [@somasoma_blue 猫狗闹剧](https://x.com/somasoma_blue/status/2103039084944138621)（54 s） | mixed | 无视频经验的造型师，用了 Claude、GPT-6 Astra、Seedance 2.5、ZANIMA | 没按工具拆分镜头，画面无法归到某一个模型 |
| 纸片拼贴 | [@ring_hyacinth 中秋猫](https://x.com/ring_hyacinth/status/2102986085328716066)（40 s） | procedural_2d | 脚本和音乐自备；p5.js + p5.brush 逐帧动画；Nano Banana Pro 生成背景底稿和纸材质；Node.js 合成音效 | 代码动画叠加外部生成的静态美术，不是「零素材」 |
| 纸片拼贴 | [@NFT_Chen 猫补月亮](https://x.com/NFT_Chen/status/2103380404791333144)（39 s） | procedural_2d | 同上路线：生成图做背景和撕纸材质，p5.brush 逐帧画 | 同上 |
| 纸片拼贴 | [@x4b47x 什么让一个地方像家](https://x.com/x4b47x/status/2103019799614034026)（57 s） | procedural_2d | 公开提示：纯 JS、30–60 秒**竖屏 9:16** 剪纸皮影戏、代码配乐 | 技术栈、时长、画幅、风格、声音、主题都写清楚的紧凑提示，**竖屏可直接参照** |
| 水墨／油彩 | [@jurlycat 窗外风景](https://x.com/jurlycat/status/2102645793828036643)（78 s） | procedural_2d | 单个 index.html，无图片、无视频、无库；后来说自己跑过并改过 | 有人工修改，不是零编辑 |
| 水墨／油彩 | [@mablesjoseph 女孩与孔明灯](https://x.com/mablesjoseph/status/2103465246014746943)（46 s） | procedural_2d | 笔触、水彩晕染、音效都是代码；163 次模型调用、约 6 h 45 min、人工约 1.5 h、渲染 12 min、约 34 美元等价 | 数字都是作者口径；它公开承认多轮引导 |
| 水墨／油彩 | [@KamStudioLabs 灯塔守夜人](https://x.com/KamStudioLabs/status/2102908742518100086)（46 s） | procedural_2d | 「45 秒无对白、声音讲一半故事」；雨、脚步、钟声、配乐都在浏览器合成 | 音频说法属作者披露 |
| 水墨／油彩 | [@yumaeriel 火的神话](https://x.com/yumaeriel/status/2103053166006657284)（30 s） | procedural_2d | [17,664 字公开提示](https://x.com/yumaeriel/status/2103053172235264150)：p5.js、参考视频为准、粗笔刷、蓝橙窄色板、60 fps 播放上 12–15 fps 换画、逐秒分镜、大量「禁止干净矢量」 | 极端详细的美术指导提示；九帧证明不了还原度 |
| 水墨／油彩 | [@pradeepXkapoor 未完成水墨武士](https://x.com/pradeepXkapoor/status/2102782449478668290)（90 s） | 3d_or_realtime_graphics | 标「UNFINISHED」；Three.js/WebGPU 自写笔刷和墨迹模拟，程序化 Web Audio；决定不再花 token 打磨 | 能出完整长度，不等于作者满意 |
| 手绘 | [@araminta_k AE 线稿合成草稿](https://x.com/araminta_k/status/2103244081388503196)（25 s） | existing_source_transformation | 让模型参照自己的风格图，在 After Effects 里做 x-sheet 曝光节奏和分层合成，人再指导动作，约 1 小时，下一步才上色 | 模型辅助加人工修订；还不是完成的彩色片 |
| 像素 | [@yangfei33113 雨夜浅草](https://x.com/yangfei33113/status/2102611841122017632)（38 s） | existing_source_transformation | 先上网找真实街景照片，再用代码叠雨、倒影、对焦、人物光影和音效，没有视频模型 | 照片来源和授权未公开（**我们不能这样用来路不明的照片**） |
| 动漫 | [@sbalhatlani 阿拉伯语动漫试播](https://x.com/sbalhatlani/status/2103475507471806929)（8 min 33 s） | mixed | 约 14 小时：211 镜规划、自写 2D 动画引擎、300 多张人物／场景图、11 个角色、70 条配音、16 段音乐 | 多资产多工序编排，九帧看不出连贯性 |
| 写实 | [@razeden0 海岸公路](https://x.com/razeden0/status/2103153899431432535)（22 s） | external_video_model | Claude 写故事、角色设定、起始帧、运镜和时长，Seedance 2.5 出画面 | 视频模型渲染，Claude 当导演 |
| 动态图形 | [@KamStudioLabs 不想被修复的 bug](https://x.com/KamStudioLabs/status/2102903173161877996)（90 s） | procedural_2d | 一句话：「做一个 90 秒关于不想被修复的 bug 的动画短片」 | 未说明渲染器和音轨来源 |

## B. 历史／文化（history_culture）——历史线（如 halloween-history）的可选参考

AO55B 统计：历史／文化里动态图形 11、三维 9、扁平卡通 8、水墨／油彩 8、手绘 5、纸片拼贴 4、像素 3、生成艺术 1 个文件。

### B1. 已深读案例（cases-index）

| 画风 | 案例 | 制作路径 | 作者披露（摘要） | 审读边界 |
|---|---|---|---|---|
| 手绘 | [@akokoi1 中国历史简述](https://x.com/akokoi1/status/2102583898865873225)（158 s） | educational_explainer | 说是 Opus 5.5 做的中国历史讲解片，给了订阅用量 | 配音／音频来源待核 |
| 手绘 | [@hanifproduktif 印尼 81 年史](https://x.com/hanifproduktif/status/2102695622042411419)（59 s） | educational_explainer | 公开短提示：不到一分钟的**浅色线描**印尼史，带音乐和旁白；第二版同提示同旁白，只是加了 Tesseract CLI | 左右对比片，不能证明差异全来自这个工具 |
| 手绘 | [@Hectoryu 战略咨询简史](https://x.com/Hectoryu/status/2103130115177898208)（60 s） | educational_explainer | Opus 做内容，再把音频和代码交给 GPT 合成导出 | 「Opus 做的」不代表每一步都是同一个模型 |
| 扁平卡通 | [@JuancaGlez7 地球到人类历史](https://x.com/JuancaGlez7/status/2102890107200229817)（78 s） | educational_explainer | 不生成图片、不调视频模型，SVG/JavaScript 逐帧 | 抽帧证明不了年代和配音准确 |
| 扁平卡通 | [@RetropunkAI 拉斯维加斯 Sphere 简史](https://x.com/RetropunkAI/status/2103237989065277590)（60 s） | educational_explainer | [提示](https://x.com/RetropunkAI/status/2103237991091060898)：三张图片 + 资料文件夹，用 GSAP 做 30–60 秒解释片 | 一轮提示里其实带了图、资料、平台和故事范围 |
| 扁平卡通 | [@makwired Shaml 纸雕短片](https://x.com/makwired/status/2103008945220567166)（20 s） | procedural_2d | 链接了 [opus-js-animations](https://github.com/klsoen/opus-js-animations)：Canvas 2D 逐帧纸雕夜景，现成朗读录音，v1 到 v4.2 的人工美术修订；流程是先问音源、听音、提导演方案、等人批准，再写程序 | 有开源代码支持；「短触发词」不代表全部输入 |
| 三维 | [@tetumemo 坛之浦合战](https://x.com/tetumemo/status/2102652072252584046)（74 s） | 3d_or_realtime_graphics | [提示](https://x.com/tetumemo/status/2102652076702716273)：电视特辑式俯瞰 3D，地形、船、潮流逆转、箭、雾、机位变化 | 史实准确性没查 |
| 水墨／油彩 | [@Michaelzsguo 沙画美国 250 年](https://x.com/Michaelzsguo/status/2102592355165782312)（120 s） | procedural_2d | 两分钟沙画美国史的短提示，带音乐音效；不用 Blender/Three.js，音乐是代码生成 | 「一个提示」与用量是自述 |
| 水墨／油彩 | [@dhruvalgolakiya 人类文明之旅](https://x.com/dhruvalgolakiya/status/2102733714845491558)（124 s） | existing_source_transformation | 3 轮提示、2 小时；有参考视频、6–7 个子代理、单个 JS 文件、ElevenLabs 配音 | 参考视频加外部音频，明确不是一次生成 |
| 水墨／油彩 | [@AxtonLiu 会呼吸的宣纸水墨画](https://x.com/AxtonLiu/status/2103288413969621231)（39 s） | procedural_2d | 开放式提示；HTML/Canvas 在宣纸底纹上逐笔画山水、松、舟、红日 | 未公开源码 |

### B2. 后续收录（library，多为作者披露或九帧取样，未进入上面的深读表）

AO55B 的 library 按模型列出来源。下面这些和历史线相关，但很多不是 Opus 5.5（作者报告为 Fable 5.5、Sonnet 5.5 等），**模型标签都是作者口径**。只作画面和结构的灵感，不作为任何模型能力的证据。

| 案例 | 证据级别 | 摘要（AO55B） | 对我们的意义 |
|---|---|---|---|
| ⭐ [用涂鸦讲述人类史 · Doodle history](https://x.com/oalanicolas/status/2107958931230241037)（89 s，作者报告 Fable 5.5） | 九帧取样 | 88 秒覆盖 16 个时代，**绘画技法和音乐随时代变化**；取样可见**同一个手绘角色贯穿各个年代画框**，画面从纸墨一路变到像素游戏风格 | 历史线可选的一个方向：**一个固定角色穿越年代 + 画风随年代变**。万圣节历史片目前没有贯穿角色，如果下一部历史片想更有看点，可以考虑试试。见[角色动画尝试方向](character-animation-routes.md) (f) |
| [四万年艺术史与猫的支线](https://x.com/cherry_mx_reds/status/2106095190285144331)（作者报告 Fable 5.5） | 九帧取样 | 15 秒四万年艺术史，加一条猫的支线；画家与猫穿过洞穴、埃及、马赛克、文艺复兴、现代 | 同上：固定角色 + 每个年代换画风；还示范了「主线 + 宠物支线」 |
| [钢铁侠与蜘蛛侠穿越历史](https://x.com/imjustnewatai/status/2106162924331180510)（作者报告 Fable 5.5） | 九帧取样 | 两位角色飞过洞穴、埃及、罗马、水墨、文艺复兴、现代城市 | 结构可参考；**角色是他人 IP，我们不能用** |
| [迈克尔·杰克逊月球漫步穿越历史](https://x.com/noclipepe/status/2106105810812112937)（作者报告 Fable 5.5） | 九帧取样 | 公开长提示含参考图、角色、舞步、环境和九个时代要求，最后到月球 | 同上，**真人肖像和 IP 不能用**；只参考「九个时代」的提示写法 |
| [核技术与原子弹的历史](https://x.com/imjustnewatai/status/2106238699872956427)（作者报告 Fable 5.5） | 九帧取样 | 三分钟 3D 历史片，自写渲染器，5,400 帧，合成配乐；时间线、3D 示意、地图 | 地图 + 时间线的讲解结构（09 地图类） |
| [从古代到今天的人类史](https://x.com/blueemi99/status/2106041578204655748)（作者报告 Fable 5.5） | 仅来源 | 约一小时，用代码做动画和模型 | — |
| [从甲骨文开始的动画](https://x.com/MinLiBuilds/status/2106180691344118202)（作者自己对模型版本存疑） | 仅来源 | 从甲骨文开始的动画 | 中文文字史题材可参考 |
| [清明上河图虹桥场景](https://x.com/AISuperDomain/status/2108878175531110875)（作者报告 Fable 5.5） | 仅来源 | 可探索的虹桥场景，有视角切换 | 国风题材、长卷构图（11 号水墨线） |
| [水墨动画与合成声音](https://x.com/gkxspace/status/2108506384711213108)（Opus 5.5） | 仅来源 | 作者说明纸张纤维、笔毛、**角色骨架**，用 Python 合成古琴和箫 | 水墨 + 角色骨架 + 合成国乐，最接近「水墨线 + 角色」的组合 |
| [游戏简史](https://x.com/craigmiller1973/status/2106241923036164535)（作者报告 Sonnet 5.5） | 仅来源 | — | — |

## C. 给 11 号国风水墨线的可选参考（从上面挑出来）

都只是看画面用的灵感，不要求照做：

- **历史 × 水墨／油彩**：@AxtonLiu 宣纸水墨（逐笔展开的绘制过程）、@Michaelzsguo 沙画美国史（一镜到底的沙画流转）、@dhruvalgolakiya 人类文明之旅（参考视频驱动）、清明上河图虹桥（长卷与视角切换）、@gkxspace 水墨 + 角色骨架 + 合成古琴箫。
- **故事 × 水墨／油彩**：@jurlycat 窗外风景（单文件、无素材）、@mablesjoseph 孔明灯（水彩晕染，有成本披露）、@yumaeriel 火的神话（「禁止干净矢量」的写法）、@pradeepXkapoor 水墨武士（自写笔刷与墨迹模拟，作者自认未完成）。
- 竖屏：@x4b47x 剪纸皮影戏是少数明确写 9:16 的案例。

## D. 按需筛选

- 想找某种**内容类型**：看 A（故事短片）或 B（历史／文化）。
- 想找某种**画风**：在表格第一列里找；完整的「内容 × 画风」矩阵见 AO55B [`domain-style-atlas.zh-CN.md`](https://github.com/athemeroy/awesome-claude-5-5-videos/blob/main/docs/domain-style-atlas.zh-CN.md)。
- 想避开视频模型路线（我们的 Bot D 是纯程序化、成本优先）：只看制作路径为 `procedural_2d` 或 `educational_explainer` 的行。`external_video_model` 和 `mixed` 的行只作画面参考。
- 角色动画相关做法单独整理在 [character-animation-routes.md](character-animation-routes.md)。
