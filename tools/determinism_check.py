#!/usr/bin/env python3
"""determinism_check.py — 扫描动画代码中的非确定性调用（⚠️ 待测试）。
动画必须是时间的纯函数：Frame = f(frame)。禁止计时器/系统时间/无种子随机。
用法: python tools/determinism_check.py [dir_or_file ...]   (默认 projects/ src/)
行内豁免: 在该行加 `// determinism-ok`
退出码: 0 = 干净, 1 = 发现违规, 2 = 路径不存在
"""
import re, sys
from pathlib import Path

EXTS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", "out", ".venv", ".venv-rembg", "site-packages", ".remotion"}
BANNED = [
    ("setTimeout", re.compile(r"\bsetTimeout\s*\(")),
    ("setInterval", re.compile(r"\bsetInterval\s*\(")),
    ("requestAnimationFrame", re.compile(r"\brequestAnimationFrame\s*\(")),
    ("Date.now", re.compile(r"\bDate\.now\s*\(")),
    ("new Date(", re.compile(r"\bnew\s+Date\s*\(")),
    ("performance.now", re.compile(r"\bperformance\.now\s*\(")),
    # 无种子 Math.random；Remotion 的 random(seed) 不匹配
    ("Math.random", re.compile(r"\bMath\.random\s*\(")),
]
ALLOW = "determinism-ok"

def iter_files(p: Path):
    if p.is_file():
        if p.suffix in EXTS: yield p
        return
    for f in p.rglob("*"):
        if f.suffix in EXTS and f.is_file() and not (set(f.parts) & SKIP_DIRS):
            yield f

def strip_line_comment(line: str) -> str:
    i = line.find("//")
    return line if i < 0 else line[:i]

def main(argv):
    targets = argv or ["projects", "src"]
    hits, scanned, missing = [], 0, 0
    for t in targets:
        p = Path(t)
        if not p.exists():
            if argv: print(f"[warn] 路径不存在: {t}", file=sys.stderr); missing += 1
            continue
        for f in iter_files(p):
            scanned += 1
            for n, line in enumerate(f.read_text(errors="ignore").splitlines(), 1):
                if ALLOW in line: continue
                code = strip_line_comment(line)
                for name, rx in BANNED:
                    if rx.search(code):
                        hits.append(f"{f}:{n}: {name}: {line.strip()[:120]}")
    for h in hits: print(h)
    print(f"[determinism_check] 扫描 {scanned} 个文件, 违规 {len(hits)} 处", file=sys.stderr)
    if hits: return 1
    return 2 if missing and not scanned else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
