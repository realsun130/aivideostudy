#!/usr/bin/env python3
"""Check a cost_log.json (P1-6): budget drift > drift_alert_pct and revision caps. Exit 1 on any alert.
usage: python3 tools/cost_check.py projects/<id>/cost_log.json"""
import json, sys
c = json.load(open(sys.argv[1])); alerts = []; pct = c.get("drift_alert_pct", 30) / 100
for s in c["stages"]:
    if s["estimate"] > 0 and s["actual"] > s["estimate"] * (1 + pct):
        alerts.append(f"budget_drift: {s['stage']} actual {s['actual']} > estimate {s['estimate']} +{pct:.0%}")
    if s["revisions"] > s["revision_cap"]:
        alerts.append(f"revision_cap: {s['stage']} {s['revisions']} > cap {s['revision_cap']}")
tot = sum(s["actual"] for s in c["stages"])
if tot > c["budget_total"] * (1 + pct): alerts.append(f"budget_drift: total {tot} > budget {c['budget_total']} +{pct:.0%}")
print(json.dumps({"total_actual": tot, "budget_total": c["budget_total"], "alerts": alerts}, indent=2)); sys.exit(1 if alerts else 0)
