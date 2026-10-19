# halloween-history · 《万圣节的历史演变》

纯代码动画（无角色），9:16，约 86 秒。本轮只做到静帧，等用户锁定 Style Lock 后再做动效。

- `research/facts.md`：事实核查表（来源、信心、争议点）
- `story_card.md` / `storyboard.md`：故事卡和分镜（9 镜，帧号按 24fps 计）
- `stills/01–09.png`：每镜一张关键帧；`contact_sheet.jpg`：联系表
- `render/render_stills.py`：复现方法是 `cd render && python3 render_stills.py`。种子固定，同一镜重复渲染像素完全一致（已用 md5 校验）
- 画风：`styles/halloween-history-map/style_bible.json`（locked_by=pending_user_style_lock）
- 依赖：Python 3、Pillow、numpy、Noto Serif/Sans CJK；地图来自 Natural Earth 1:50m land（公有领域）
