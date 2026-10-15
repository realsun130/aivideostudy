#!/usr/bin/env python3
"""Slideshow-risk score for a shot_list.json (P1-2). Run before Shot Lock.

usage: python3 tools/slideshow_risk.py shot_list.json [--max-score 40] [--json]
Score 0-100 (higher = more slideshow-like). Exit 1 if score > max or any shot lacks intent.
Components (weights): missing/weak intent 30, weak motion 30, repeated layout 20, text-card ratio 20.
"""
import argparse, json, sys
from collections import Counter

WEAK_MOVES = {"static"}
WEAK_PRESETS = {"static", "subtitle_card"}
FILLER = {"tbd later", "filler shot", "tbd", "todo", "n/a", "filler", "transition", "b-roll", "looks nice", "好看", "过渡"}

def analyse(sl):
    shots = sl["shots"]; n = len(shots); issues = []
    no_intent = [s["shot_id"] for s in shots if len((s.get("shot_intent") or "").strip()) < 8
                 or (s.get("shot_intent") or "").strip().lower() in FILLER or not s.get("information_role")]
    weak = []
    for s in shots:
        mv = s.get("cinematography", {}).get("camera_movement", "static")
        pr = (s.get("programmatic_motion") or {}).get("preset")
        if (pr in WEAK_PRESETS if pr else mv in WEAK_MOVES) and not s.get("action"):
            weak.append(s["shot_id"])
        elif (pr in WEAK_PRESETS if pr else mv in WEAK_MOVES):
            weak.append(s["shot_id"] + "(static cam, has action)")
    weak_hard = [w for w in weak if "(" not in w]
    weak_ratio = (len(weak_hard) + 0.5 * (len(weak) - len(weak_hard))) / n
    layouts = [s.get("layout") or f"{s['cinematography'].get('shot_size')}|{s['cinematography'].get('camera_movement')}|{(s.get('programmatic_motion') or {}).get('preset','-')}" for s in shots]
    run_max, run = 1, 1
    for i in range(1, n):
        run = run + 1 if layouts[i] == layouts[i - 1] else 1; run_max = max(run_max, run)
    top = Counter(layouts).most_common(1)[0]
    repeat_ratio = max(top[1] / n if n >= 4 else 0, (run_max - 1) / max(n - 1, 1))
    text = [s["shot_id"] for s in shots if s.get("is_text_card") or (s.get("programmatic_motion") or {}).get("preset") == "subtitle_card"]
    text_ratio = len(text) / n
    score = round(30 * len(no_intent) / n + 30 * weak_ratio + 20 * min(1, repeat_ratio * 1.5) + 20 * min(1, text_ratio / 0.5))
    if no_intent: issues.append(f"shots without real intent/role: {no_intent}")
    if weak: issues.append(f"weak motion shots: {weak}")
    if run_max >= 3: issues.append(f"same layout repeated {run_max}x in a row")
    if top[1] / n > 0.4 and n >= 4: issues.append(f"layout '{top[0]}' used in {top[1]}/{n} shots")
    if text_ratio > 0.3: issues.append(f"text-card ratio {text_ratio:.0%} > 30%: {text}")
    return {"score": score, "components": {"no_intent": len(no_intent) / n, "weak_motion": round(weak_ratio, 3),
            "layout_repeat": round(repeat_ratio, 3), "text_card_ratio": round(text_ratio, 3)},
            "shots": n, "issues": issues, "missing_intent": no_intent}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("shot_list"); ap.add_argument("--max-score", type=int, default=40)
    ap.add_argument("--json", action="store_true"); a = ap.parse_args()
    r = analyse(json.load(open(a.shot_list)))
    r["verdict"] = "block" if r["score"] > a.max_score or r["missing_intent"] else "ok"
    print(json.dumps(r, ensure_ascii=False, indent=2))
    sys.exit(0 if r["verdict"] == "ok" else 1)
