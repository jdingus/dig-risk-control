#!/usr/bin/env python3
"""Check that the answer key (answers.json) agrees with the independent cross-check (xcheck/answers.json).

For every question, every value in the key must appear among the cross-check's values for that question
(numbers compared as numbers, names compared ignoring case). Exit 1 on any disagreement.
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PAIRS = [("answers.json", "xcheck/answers.json"), ("heldout_answers.json", "xcheck/heldout_answers.json")]


def flat(v):
    if isinstance(v, dict):
        for x in v.values():
            yield from flat(x)
    elif isinstance(v, list):
        for x in v:
            yield from flat(x)
    else:
        yield v


def norm(v):
    try:
        return ("n", float(str(v).replace(",", "").replace("$", "").replace("%", "")))
    except ValueError:
        return ("s", str(v).strip().lower())


bad = 0
for kf, xf in PAIRS:
  key = json.loads((HERE / kf).read_text())["answers"]
  xc = json.loads((HERE / xf).read_text())
  xc = xc.get("answers", xc)
  for q, ans in key.items():
    have = {norm(v) for v in flat(xc.get(q, {}))}
    for name, v in ans.items():
        ok = norm(v) in have
        bad += not ok
        print(f"{q:4} {name:34} {str(v):45} {'agree' if ok else 'DISAGREE'}")
print("all agree" if not bad else f"{bad} disagreement(s)")
raise SystemExit(1 if bad else 0)
