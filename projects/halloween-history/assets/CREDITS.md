# 素材来源与授权 · 《万圣节的历史演变》 v0.2

`assets/src/` 是下载的原图（未改动）；`assets/cut/` 是由 `render/prep_assets.py` 抠出的透明 PNG；
渲染时（`render/cutouts.py`）再做去色 → 映射到调色板 → 加琥珀火光，所以成片里每张都是**改编作品**。
只用公有领域 / CC0 / CC BY / CC BY-SA（见第 2 条的说明）。

| # | 用在 | 原图（原文件名 → 本地文件） | 作者 | 授权 | 原图实际内容 | 画面标签 |
|---|---|---|---|---|---|---|
| 1 | 镜 03 左 | [File:Mari Lwyd at Llangynwyd in the early 20th century.jpg](https://commons.wikimedia.org/wiki/File:Mari_Lwyd_at_Llangynwyd_in_the_early_20th_century.jpg) → `src/mari_lwyd_llangynwyd_evans_1904-1910.jpg` | Frederic Evans（摄，1904–1910） | **Public domain** | 威尔士格拉摩根 Llangynwyd 村的 Mari Lwyd（披白布、顶装饰马头骨的伪装），由 Sianco'r Castell 牵引；20 世纪初 | 马头伪装 / 威尔士 / 20世纪初 |
| 2 | 镜 03 中 | [File:Irish Halloween Mask at the Horniman Museum.jpg](https://commons.wikimedia.org/wiki/File:Irish_Halloween_Mask_at_the_Horniman_Museum.jpg) → `src/irish_halloween_mask_horniman.jpg` | Ethan Doyle White（摄，2018） | **CC BY-SA 4.0** | 20 世纪初爱尔兰万圣节面具（布面、画眉眼鼻、挖口洞），霍尼曼博物馆藏品 111605 | 万圣节布面具 / 爱尔兰 / 20世纪初 |
| 3 | 镜 03 右 | [Dennison's Bogie Book (1920), p.36「Dennison stock goods for Hallowe'en」](https://commons.wikimedia.org/wiki/File:Dennison%27s_bogie_book_.._(IA_dennisonsbogiebo00denn).pdf)（[Internet Archive](https://archive.org/details/dennisonsbogiebo00denn)）→ `src/dennison_bogie_book_1920_p36_300dpi.jpg`（PDF 第 36 页按 300 dpi 渲染） | Dennison Manufacturing Co.（马萨诸塞州 Framingham，1920） | **Public domain**（1920 年美国出版） | 商品目录页上的黑猫脸纸饰；页面文字未写明它是面具 → 不叫面具 | 黑猫纸饰 / 美国 / 1920 |
| 4 | 镜 06 左 | [File:TurnipJackolantern.jpg](https://commons.wikimedia.org/wiki/File:TurnipJackolantern.jpg) → `src/turnip_jackolantern_geni.jpg` | Geni（英文维基百科用户，2006） | **CC BY 2.5** | 现代家庭用芜菁刻的灯（地点未注明） | 芜菁灯 / 爱尔兰/苏格兰传统（标签指做法的来源，不指照片地点） |
| 5 | 镜 06 右 | [File:Carved pumpkin as face (Unsplash).jpg](https://commons.wikimedia.org/wiki/File:Carved_pumpkin_as_face_(Unsplash).jpg) → `src/carved_pumpkin_teutschmann_cc0.jpg`（取右侧那只） | Beth Teutschmann（摄，2016-10-26，美国威斯康星州 Eau Claire） | **CC0** | 现代刻脸南瓜灯，内部点灯 | 南瓜灯 / 美国 |

## 改动说明（所有素材通用）
裁切 → 抠图（rembg u2net；#2 用 OpenCV GrabCut；#3 用暗部阈值 + 椭圆裁切）→ 去色 → 按亮度映射到
`paper_cream`/`night_ink`（#3 反相：黑猫变纸色）或映射到琥珀色阶（#5）/中性双色（#4）→ 刻孔高光放进加光层发光 → 镜 03 底边加琥珀边缘光。

## 发布时要写的署名（贴到视频简介 / 片尾小字）
> 图片素材：Mari Lwyd 摄影 Frederic Evans（公有领域）；爱尔兰万圣节面具 摄影 Ethan Doyle White，CC BY-SA 4.0，霍尼曼博物馆藏；
> Dennison's Bogie Book（1920，公有领域）；芜菁灯 摄影 Geni，CC BY 2.5；南瓜灯 摄影 Beth Teutschmann（CC0）。均来自 Wikimedia Commons，经去色、抠图、调色改编。

## ⚠️ 需要你决定的一条
- **#2 是 CC BY-SA 4.0（相同方式共享）**：可商用，但改编后的那部分画面（镜 03 的面具画面）按条款要以 CC BY-SA 4.0 提供，并署名。
  不想要这个约束的话，可以换掉：目前在 Commons 上没找到 PD/CC0/CC BY 的苏格兰/爱尔兰「假脸」面具照片。
- 排除过的：Smithsonian NMAH 万圣节面具（CC0 元数据但无图）；Haudenosaunee False Face 面具（宗教圣物，不用）；
  Ben Cooper 面具照片（CC BY-SA 3.0 且面具本身是受版权保护的商业设计）。
