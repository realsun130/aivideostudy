# 素材来源与授权 · 《万圣节的历史演变》

`assets/src/` 是下载的原图；`assets/cut/` 是 `render/prep_assets.py` 抠出的透明 PNG。
渲染时（`render/cutouts.py`）再去色 → 映射到调色板 → 加琥珀火光，成片是**改编作品**。

## 镜 03 当前使用（v0.3 · 三件都与万圣夜/萨温季伪装有关）

| # | 位置 | 原图 | 作者 / 日期 | 授权 | 原图实际内容 | 画面标签 |
|---|---|---|---|---|---|---|
| 1 | 左 | [File:Skekler costume.jpg](https://commons.wikimedia.org/wiki/File:Skekler_costume.jpg) → `src/skekler_shetland_museum.jpg` | Northerner（摄，2017-09-30） | **CC BY-SA 4.0** | 设得兰博物馆展出的 Skekler（惊吓人）稻草伪装；设得兰传统在万圣夜前后与新年前后使用 | Skekler 稻草伪装 / 设得兰 |
| 2 | 中 | [File:Irish Halloween Mask at the Horniman Museum.jpg](https://commons.wikimedia.org/wiki/File:Irish_Halloween_Mask_at_the_Horniman_Museum.jpg) → `src/irish_halloween_mask_horniman.jpg` | Ethan Doyle White（摄，2018） | **CC BY-SA 4.0** | 20 世纪初爱尔兰万圣节布面具，霍尼曼博物馆藏品 111605 | 万圣节布面具 / 爱尔兰·霍尼曼 / 20世纪初 |
| 3 | 右 | [File:Traditional-irish-halloween-mask.jpg](https://commons.wikimedia.org/wiki/File:Traditional-irish-halloween-mask.jpg) → `src/traditional_irish_halloween_mask_country_life.jpg` | rannṗáirtí anaiṫnid（摄，约 2009） | **CC BY-SA 3.0** | 20 世纪初爱尔兰传统万圣节面具，摄于爱尔兰乡村生活博物馆（Museum of Country Life） | 万圣节布面具 / 爱尔兰·乡村生活馆 / 20世纪初 |


### 镜 03 左 · Skekler 剪影说明（v0.3.1）
原照片里玻璃反光、展柜立柱、墙面展板和稻草缠在一起，自动抠图去不干净。
成片剪影只保留**外形 + 稻草状明暗**（程序生成的有机轮廓与竖向纤维纹理，种子 1031），
不再带入展柜直线/矩形。标签仍指向设得兰博物馆那件展品与 CC BY-SA 4.0 照片来源。

### ⚠️ BY-SA（相同方式共享）
镜 03 三张现用素材**全部是 CC BY-SA**（4.0 / 4.0 / 3.0）。可商用，但使用它们改编的那段画面（镜 03）须以对应的 CC BY-SA 提供，并署名。
本仓库在 Wikimedia Commons 与博物馆开源库检索后，**未找到**公有领域 / CC0 / 纯 CC BY 的爱尔兰或苏格兰「假脸」面具旧照；设得兰 Skekler 也只有 BY-SA 展品照。

### 发布署名（可贴简介 / 片尾）
> 镜 03 面具素材：Skekler 稻草伪装 摄影 Northerner，CC BY-SA 4.0，设得兰博物馆；爱尔兰万圣节面具 摄影 Ethan Doyle White，CC BY-SA 4.0，霍尼曼博物馆；爱尔兰传统万圣节面具 摄影 rannṗáirtí anaiṫnid，CC BY-SA 3.0，乡村生活博物馆。均来自 Wikimedia Commons，经去色、抠图、调色改编。

### 检索过但未采用（说明）
- Mari Lwyd（威尔士马头伪装）：公有领域，但是圣诞—新年习俗，不是万圣夜/萨温季 → v0.2 用过，v0.3 撤下。
- Dennison's Bogie Book（1920）黑猫纸饰：公有领域，目录未写明是面具 → v0.2 用过，v0.3 撤下。
- Thanksgiving Maskers（国会图书馆，约 1910–1915）：无已知发表限制，有清晰面具，但是**感恩节**面具游行，不是万圣节。
- Souling on Halloween（1882，公有领域）：英格兰讨灵魂糕插图，几乎看不出面具。
- Burns《Halloween》插画（公有领域）：占卜游戏场景，不是伪装。
- Baltasound grölicks（2015，CC BY-SA 2.0）：现代设得兰万圣夜伪装，面部被当代化妆遮住，不如博物馆 Skekler 清楚。
- 美国早期万圣夜戴面具儿童：在 LoC/Commons 未找到 1929 年前、授权明确、且能清楚看到面具的单独照片。

## 镜 06（未改，仍用）

| # | 用在 | 原图 | 作者 | 授权 |
|---|---|---|---|---|
| 4 | 芜菁灯 | [File:TurnipJackolantern.jpg](https://commons.wikimedia.org/wiki/File:TurnipJackolantern.jpg) | Geni，2006 | **CC BY 2.5** |
| 5 | 南瓜灯 | [File:Carved pumpkin as face (Unsplash).jpg](https://commons.wikimedia.org/wiki/File:Carved_pumpkin_as_face_(Unsplash).jpg) | Beth Teutschmann，2016，美国 Eau Claire | **CC0** |

## 改动说明（通用）
裁切 → 抠图 → 去色 → 按亮度映射到 `paper_cream`/`night_ink` → 刻孔/边缘琥珀光进加光层。

## 声音（v3.1 · 当前成片 `out/halloween_history_v3_1.mp4`）

| 用途 | 来源 | 授权 | 说明 |
|---|---|---|---|
| 旁白 TTS | **Fun-CosyVoice3-0.5B-2512**（FunAudioLLM / 通义实验室），零样本模式；代码 https://github.com/FunAudioLLM/CosyVoice ，权重 https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512 | 代码 **Apache-2.0**，模型权重 **Apache-2.0**（模型卡 license 字段） | 本机 CPU 生成（每句约 20–38 s）。可商用；建议简介注明「配音由 CosyVoice3 合成」。权重不入库 |
| 声线参考音 | `audio/ref/ref_voxcpm2_narrator_s9.wav`：用 **VoxCPM2**（openbmb，https://huggingface.co/openbmb/VoxCPM2 ，**Apache-2.0**）仅凭文字描述「中年男性纪录片旁白，温暖低沉，舒缓从容，不像播音腔」生成的**合成声线**（念的是第 9 句前半） | Apache-2.0 模型输出 | **不是任何真人的声音，没有克隆真人**；用户在 A/B/C 试听中选定的 C |
| 配乐 / 音效 | 同 v3：`audio/build_audio_v3.py` 原创程序化合成（种子 1031），按 `timeline_v3_1.json` 重定时；v3.1 另加旁白 100 Hz 高通 + 低频搁架、配乐 120 Hz 以下 -6 dB（手机频段） | 原创，无采样 | 可商用，无第三方权利 |

## 声音（v3 · 记录）

| 用途 | 来源 | 授权 | 说明 |
|---|---|---|---|
| 旁白 TTS | **Kokoro-82M v1.0**（hexgrad/Kokoro-82M），声线 `zm_yunjian`；Python 包 kokoro 0.7.16 + misaki（中文 G2P：jieba / pypinyin / cn2an） | 模型权重 **Apache-2.0**；kokoro / misaki 代码 Apache-2.0 | 本机 CPU 生成（无 GPU）。Apache-2.0 允许商用，生成音频归使用者；无需署名（建议简介注明“配音由 Kokoro-82M 合成”）。每镜单独合成，语速 1.0–1.2 适配拍点镜长 |
| 配乐 | **原创程序化合成**（`audio/build_audio_v3.py`，numpy/scipy，种子 1031）：90 BPM，D 小调铺底 → 教堂五度 → 饥荒低音 → F 大调拨弦 → D 大调八分音符 → 安静钟声收尾 | 原创，无采样 | 可商用，无第三方权利 |
| 音效 | 同上脚本合成：篝火噼啪、8 次点火、烛火、海浪、甩镜呼啸、Ireland 钟声、窗灯“嗒”声、卡片铃、3 次吹灯 | 原创，无采样 | 可商用 |

检索过但未采用：
- **Piper `zh_CN-huayan-medium`**：代码 GPL-3.0（不影响输出），但模型卡写明训练数据 HuaYan **授权 Unknown** → 商用不安全，弃用（`audio/vo/shot*.wav` 为早期试听，未进成片）。
- Kokoro-82M-v1.1-zh：包镜像只有 kokoro 0.7.x（不支持 repo_id），未能加载。
- CosyVoice2 / LuxTTS：无 GPU，未测；F5-TTS（权重 CC-BY-NC）按要求避开；edge-tts / 云服务按要求避开。
- Openverse CC0 音乐/音效：接口超时，未下载任何文件；最终全部自合成。
