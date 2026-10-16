#!/usr/bin/env python3
"""提示词回归测试打分器（⚠️ 待测试）。只打分，不调模型。
用法: python3 tools/prompt_eval.py evals/bot_x.yaml --outputs DIR [--json]
DIR/<case_id>.txt 或 .json（Bot E 含 "verdict"）。机判 must_contain / must_not_contain / expect_verdict；
expect 列表需人工/审核模型判定，记为 manual。退出码 0=机判全过 1=有失败 2=参数错误。"""
import argparse, json, os, sys
import yaml

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("evalset"); ap.add_argument("--outputs", required=True); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not os.path.isfile(a.evalset) or not os.path.isdir(a.outputs):
        print("路径不存在", file=sys.stderr); return 2
    spec = yaml.safe_load(open(a.evalset, encoding="utf-8"))
    results = []
    for c in spec.get("cases", []):
        cid, fails = c["id"], []
        txt_p, js_p = os.path.join(a.outputs, cid + ".txt"), os.path.join(a.outputs, cid + ".json")
        text, verdict = None, None
        if os.path.isfile(js_p):
            text = open(js_p, encoding="utf-8").read()
            try: verdict = json.loads(text).get("verdict")
            except Exception: fails.append("json 解析失败")
        elif os.path.isfile(txt_p):
            text = open(txt_p, encoding="utf-8").read()
        else:
            fails.append("缺输出文件")
        if text is not None:
            fails += [f"缺: {s}" for s in c.get("must_contain", []) if s not in text]
            fails += [f"不应含: {s}" for s in c.get("must_not_contain", []) if s in text]
            ev = c.get("expect_verdict")
            if ev and verdict != ev: fails.append(f"verdict={verdict} 期望 {ev}")
        results.append({"id": cid, "pass": not fails, "fails": fails, "manual": c.get("expect", [])})
    n, p = len(results), sum(r["pass"] for r in results)
    out = {"evalset": a.evalset, "passed": p, "total": n, "pass_rate": round(p / n, 3) if n else None, "cases": results}
    if a.json: print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        for r in results: print(("PASS " if r["pass"] else "FAIL ") + r["id"], "; ".join(r["fails"]))
        print(f"机判通过 {p}/{n}；expect 项需人工判定")
    return 0 if p == n else 1

if __name__ == "__main__":
    sys.exit(main())
