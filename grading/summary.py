#!/usr/bin/env python3
"""Collect every graded arm into one JSON for the results page (assets/results-data.json).

  python3 grading/summary.py > assets/results-data.json

Reads the committed grades and keys only; no number is typed by hand.
"""
import json
import pathlib
import statistics as st

ROOT = pathlib.Path(__file__).resolve().parents[1]
SETS = [  # (grading dir, arm label in that key, condition, arm, transcript dir)
    ("grading", "control", "Sonnet 5.5 + Python", "no folder, no files", "control/raw"),
    ("grading", "raw", "Sonnet 5.5 + Python", "raw files, no folder", "raw-files/raw"),
    ("grading", "folder", "Sonnet 5.5 + Python", "folder", "treatment/raw"),
    ("grading-haiku", "control", "Haiku 5.5 + Python", "no folder, no files", "haiku/control/raw"),
    ("grading-haiku", "raw", "Haiku 5.5 + Python", "raw files, no folder", "haiku/raw-files/raw"),
    ("grading-haiku", "folder", "Haiku 5.5 + Python", "folder", "haiku/treatment/raw"),
    ("grading-nocode", "raw", "Haiku 5.5, no Python", "raw files, no folder", "nocode/raw-files/raw"),
    ("grading-nocode", "folder", "Haiku 5.5, no Python", "shipped folder (cannot run its tool)", "nocode/treatment/raw"),
    ("grading-nocode", "folder-nocode", "Haiku 5.5, no Python", "pre-computed folder", "nocode/folder-nocode/raw"),
    ("grading-2", "rerun-control", "Fresh-clone re-run (Sonnet + Python)", "no folder, no files", "rerun-fresh-clone/control/raw"),
    ("grading-2", "rerun-raw", "Fresh-clone re-run (Sonnet + Python)", "raw files, no folder", "rerun-fresh-clone/raw/raw"),
    ("grading-2", "rerun-folder", "Fresh-clone re-run (Sonnet + Python)", "folder", "rerun-fresh-clone/folder/raw"),
]

out = []
for gdir, label, cond, arm, tdir in SETS:
    key = json.loads((ROOT / gdir / "key.json").read_text())
    per_q = {}
    for g in (ROOT / gdir / "grades").glob("*.json"):
        d = json.loads(g.read_text())
        for lab, v in d["grades"].items():
            if key[lab]["arm"] == label:
                per_q.setdefault(d["qid"], []).append(v["score"])
    qs = sorted(per_q, key=lambda q: (q[0] != "Q", int(q[1:])))
    main = [s for q in qs if q[0] == "Q" for s in per_q[q]]
    held = [s for q in qs if q[0] == "H" for s in per_q[q]]
    tok, wall = [], []
    for f in (ROOT / tdir).glob("*.jsonl"):
        r = [json.loads(l) for l in f.open()]
        r = [e for e in r if e.get("type") == "result"][-1]
        u = r.get("usage", {})
        tok.append(sum(u.get(k, 0) for k in ("input_tokens", "cache_read_input_tokens",
                                              "cache_creation_input_tokens", "output_tokens")))
        wall.append(json.loads(f.with_name(f.stem + ".meta.json").read_text())["wall_s"])
    out.append({
        "condition": cond, "arm": arm, "runs_per_question": len(per_q[qs[0]]),
        "main_score": sum(main), "main_max": 2 * len(main),
        "heldout_score": sum(held), "heldout_max": 2 * len(held),
        "per_question": {q: {"score": sum(per_q[q]), "max": 2 * len(per_q[q])} for q in qs},
        "median_tokens": round(st.median(tok)), "median_seconds": round(st.median(wall), 1),
    })

predictions = [  # copied from the committed prediction files, each with its source
    {"what": "Sonnet raw, my 10 (of 60)", "low": 30, "high": 42, "source": "questions.md (10-14 of 20 per run)"},
    {"what": "Sonnet folder, my 10 (of 60)", "low": 51, "high": 60, "source": "questions.md (17-20 of 20 per run)"},
    {"what": "Haiku raw, my 10 (of 60)", "low": 20, "high": 40, "source": "predictions-haiku.md"},
    {"what": "Haiku folder, my 10 (of 60)", "low": 50, "high": 60, "source": "predictions-haiku.md"},
    {"what": "No-Python raw, my 10 (of 60)", "low": 5, "high": 20, "source": "predictions-nocode.md"},
    {"what": "No-Python shipped folder, my 10 (of 60)", "low": 5, "high": 20, "source": "predictions-nocode.md"},
    {"what": "No-Python pre-computed folder, my 10 (of 60)", "low": 30, "high": 50, "source": "predictions-nocode.md"},
]
actual = {"Sonnet raw": ("Sonnet 5.5 + Python", "raw files, no folder"),
          "Sonnet folder": ("Sonnet 5.5 + Python", "folder"),
          "Haiku raw": ("Haiku 5.5 + Python", "raw files, no folder"),
          "Haiku folder": ("Haiku 5.5 + Python", "folder"),
          "No-Python raw": ("Haiku 5.5, no Python", "raw files, no folder"),
          "No-Python shipped folder": ("Haiku 5.5, no Python", "shipped folder (cannot run its tool)"),
          "No-Python pre-computed folder": ("Haiku 5.5, no Python", "pre-computed folder")}
for p in predictions:
    cond, arm = actual[p["what"].split(",")[0]]
    p["actual"] = next(o["main_score"] for o in out if o["condition"] == cond and o["arm"] == arm)
    p["hit"] = p["low"] <= p["actual"] <= p["high"]

print(json.dumps({"arms": out, "predictions": predictions}, indent=1))
