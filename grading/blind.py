#!/usr/bin/env python3
"""Build the blind grading packet for round 2.

  python3 grading/blind.py

For every question: the question text, its expected answer (from key/), the scoring rule from questions.md,
then every arm's final answer, shuffled under a random label. Writes grading/by-question/<QID>.md and
grading/key.json (label -> arm and run; graders never see it). Fixed seed, so it is reproducible.
"""
import json
import pathlib
import random
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARM_DIRS = {"control": "control/raw", "raw": "raw-files/raw", "folder": "treatment/raw"}
rng = random.Random(14)

qtext = {}
for name in ("questions.md", "heldout-questions.md"):
    for m in re.finditer(r"^## ([QH]\d+)\. (.+)$", (ROOT / name).read_text(), re.M):
        qtext[m.group(1)] = m.group(2).strip()
q = (ROOT / "questions.md").read_text()
scoring = q[q.index("## How answers are scored"):q.index("\n## Q1.")].strip()
h = (ROOT / "heldout-questions.md").read_text()
extra = re.findall(r"^.*(?:[Dd]ays?).*within.*$", h, re.M)
expected = {}
for kf in ("answers.json", "heldout_answers.json"):
    expected.update(json.loads((ROOT / "key" / kf).read_text())["answers"])


def final_answer(path):
    res = [json.loads(l) for l in path.open() if '"type": "result"' in l or '"type":"result"' in l]
    return (res[-1].get("result") or "").strip() if res else "(no final answer)"


out = ROOT / "grading" / "by-question"
out.mkdir(parents=True, exist_ok=True)
key = {}
for qid, text in qtext.items():
    answers = []
    for arm, d in ARM_DIRS.items():
        for p in sorted((ROOT / d).glob(f"{qid}-r*.jsonl")):
            answers.append((arm, p.stem, final_answer(p)))
    rng.shuffle(answers)
    lines = [f"# {qid}", "", f"**Question:** {text}", "",
             "**Expected answer (from the committed key):** "
             + "; ".join(f"{k} = {v}" for k, v in expected[qid].items()), "", scoring, ""]
    if qid.startswith("H") and extra:
        lines += ["Extra rule for the held-out set: " + " ".join(extra), ""]
    for i, (arm, stem, ans) in enumerate(answers, 1):
        label = f"{qid}-{i:02d}"
        key[label] = {"arm": arm, "run": stem}
        lines += [f"## Answer {label}", "", ans, ""]
    (out / f"{qid}.md").write_text("\n".join(lines))
(ROOT / "grading" / "key.json").write_text(json.dumps(key, indent=1))
print(len(key), "answers in", len(qtext), "packets")
