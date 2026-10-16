# evals/ 提示词回归测试集（⚠️ 待测试）

规则见 `docs/DISPATCH_CONVENTIONS.md` §14。每个 Bot 提示词一个 YAML 文件，5–10 条固定用例。

## 格式（schema-light）
```yaml
bot: B                 # Bot 代号
prompt_ref: prompts/bot_b_script.md   # 被测提示词路径（尚未建时可留占位）
status: 待测试
cases:
  - id: b01
    tag: 示例          # 示例 / 边界 / 回归（来自真实失败）
    input: {...}       # 喂给 Bot 的输入，自由结构
    expect:            # 期望性质，逐条判定
      - "人能读懂的通过标准"
    must_contain: []   # 可选：输出必须含的字符串（代码可判）
    must_not_contain: []  # 可选：输出不得含的字符串（代码可判）
    expect_verdict: reject  # 仅 Bot E：accept / reject
```
`expect` 由人或审核模型判定；`must_contain` / `must_not_contain` / `expect_verdict` 由 `tools/prompt_eval.py` 机判。

## 运行
```
python3 tools/prompt_eval.py evals/bot_b_script.yaml --outputs out_dir/
```
`out_dir/` 下放每条用例的模型输出 `<case_id>.txt`（Bot E 为 `<case_id>.json`，含 `verdict`）。runner 只做打分，不调模型。改提示词前后各跑一次，把两次通过率写进决策日志。
