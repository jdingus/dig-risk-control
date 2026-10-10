#!/usr/bin/env python3
"""Join blind grades with the key; print per-question scores and cost measures per arm.

  python3 grading/score.py > grading/scores.md
"""
import json
import pathlib
import statistics as st

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARMS = ["control", "raw", "folder"]
ARM_DIRS = {"control": "control/raw", "raw": "raw-files/raw", "folder": "treatment/raw"}
key = json.loads((ROOT / "grading" / "key.json").read_text())

scores = {}
for g in sorted((ROOT / "grading" / "grades").glob("*.json")):
    d = json.loads(g.read_text())
    for label, v in d["grades"].items():
        scores.setdefault((d["qid"], key[label]["arm"]), []).append(v["score"])

qids = sorted({q for q, _ in scores}, key=lambda q: (q[0] != "Q", int(q[1:])))
print("| Q | " + " | ".join(ARMS) + " |\n|---|" + "---|" * len(ARMS))
tot = {a: [0, 0] for a in ARMS}
for q in qids:
    row = []
    for a in ARMS:
        s = scores.get((q, a), [])
        tot[a][q[0] != "Q"] += sum(s)
        row.append(f"{sum(s)}/6 ({' '.join(map(str, s))})")
    print(f"| {q} | " + " | ".join(row) + " |")
print("| **Q1-Q10** | " + " | ".join(f"**{tot[a][0]}/60**" for a in ARMS) + " |")
print("| **H1-H5** | " + " | ".join(f"**{tot[a][1]}/30**" for a in ARMS) + " |")
print("\nEach cell: total of three runs out of 6, then the three grades in blind-label order.\n")

print("| Per answer (median unless noted) | " + " | ".join(ARMS) + " |\n|---|" + "---|" * len(ARMS))
rows = {}
for a in ARMS:
    tok, tools, wall, cost = [], [], [], []
    for f in (ROOT / ARM_DIRS[a]).glob("*.jsonl"):
        ev = [json.loads(l) for l in f.open()]
        r = [e for e in ev if e.get("type") == "result"][-1]
        u = r.get("usage", {})
        tok.append(sum(u.get(k, 0) for k in ("input_tokens", "cache_read_input_tokens",
                                              "cache_creation_input_tokens", "output_tokens")))
        tools.append(sum(1 for e in ev if e.get("type") == "assistant"
                         for b in e["message"]["content"] if b.get("type") == "tool_use"))
        wall.append(json.loads(f.with_name(f.stem + ".meta.json").read_text()).get("wall_s", 0))
        cost.append(r.get("total_cost_usd", 0) or 0)
    rows.setdefault("tokens (input incl. cache + output)", {})[a] = f"{st.median(tok):,.0f}"
    rows.setdefault("tool calls", {})[a] = f"{st.median(tools):g}"
    rows.setdefault("wall seconds", {})[a] = f"{st.median(wall):.0f}"
    rows.setdefault("list-price cost, all 45 answers (not billed: subscription)", {})[a] = f"${sum(cost):.2f}"
for name, v in rows.items():
    print(f"| {name} | " + " | ".join(v[a] for a in ARMS) + " |")
