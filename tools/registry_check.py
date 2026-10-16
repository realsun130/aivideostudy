#!/usr/bin/env python3
"""registry_check.py — 工具清单防漂移检查（⚠️ 待测试）。
tools/ 下的 .py/.sh/.mjs/.js/.ts 脚本必须在 tools/registry.json 登记；登记的 path 必须存在；
registry.json 按 schemas/tool_registry.schema.json 校验（装了 jsonschema 时）。
用法: python3 tools/registry_check.py    退出码: 0 = 一致, 1 = 有问题
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTS = {".py", ".sh", ".mjs", ".js", ".ts"}

def main():
    errs = []
    reg = json.loads((ROOT / "tools/registry.json").read_text(encoding="utf-8"))
    try:
        import jsonschema
        schema = json.loads((ROOT / "schemas/tool_registry.schema.json").read_text(encoding="utf-8"))
        for e in jsonschema.Draft202012Validator(schema).iter_errors(reg):
            errs.append(f"schema: {list(e.path)} {e.message}")
    except ImportError:
        print("[registry_check] 未装 jsonschema，跳过 schema 校验")
    paths, ids = set(), set()
    for t in reg.get("tools", []):
        if t["id"] in ids: errs.append(f"重复 id: {t['id']}")
        ids.add(t["id"]); paths.add(t["path"])
        if not (ROOT / t["path"]).is_file(): errs.append(f"登记路径不存在: {t['path']}")
    for f in sorted((ROOT / "tools").iterdir()):
        if f.is_file() and f.suffix in EXTS:
            rel = f.relative_to(ROOT).as_posix()
            if rel not in paths: errs.append(f"未登记: {rel}")
    for e in errs: print("✗", e)
    print(f"[registry_check] 登记 {len(paths)} 个工具, 问题 {len(errs)} 处")
    return 1 if errs else 0

if __name__ == "__main__":
    sys.exit(main())
