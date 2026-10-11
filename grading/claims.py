#!/usr/bin/env python3
"""Recompute, from the committed transcripts, the counts that results.md states.

  python3 grading/claims.py

Each line prints the count, what results.md (or the commit message 5cec281) says, and whether they agree.
Definitions are in the code. Read-only: it never writes anything.
"""
import glob
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def events(f):
    return [json.loads(l) for l in open(f) if l.strip()]


def tool_calls(f):
    return [b for e in events(f) if e["type"] == "assistant" for b in e["message"]["content"] if b["type"] == "tool_use"]


def bash_cmds(f):
    return [b["input"].get("command", "") for b in tool_calls(f) if b["name"] == "Bash"]


def final_text(f):
    return next((e.get("result", "") for e in events(f) if e["type"] == "result"), "")


def files(d):
    return sorted(glob.glob(str(ROOT / d / "raw" / "*.jsonl")))


rows = []


def report(label, got, stated, note=""):
    ok = "agrees" if got == stated else f"DIFFERS (stated {stated})"
    rows.append(got == stated)
    print(f"{label}: {got}   [results.md: {stated}; {ok}]{('  ' + note) if note else ''}")


# 1. answers that read the README within their first two shell commands (treatment v1 and v2)
for d, stated in (("treatment", 4), ("treatment-v2", None)):
    n = sum(any("readme" in c.lower() for c in bash_cmds(f)[:2]) for f in files(d))
    if stated is None:
        print(f"README read in first two shell commands, {d}: {n}/{len(files(d))}   [not stated in results.md]")
    else:
        report(f"README read in first two shell commands, {d}", n, stated, f"(of {len(files(d))} answers)")

# 2. cases.csv peeks: answers with a `head -N` (line-count) command on cases.csv (v1 and v2)
HEAD_N = re.compile(r"head -\d+ [^|;&\n]*cases\.csv")
HEAD_C = re.compile(r"head -c \d+ [^|;&\n]*cases\.csv")
for d in ("treatment", "treatment-v2"):
    fs = files(d)
    hn = sum(any(HEAD_N.search(c) for c in bash_cmds(f)) for f in fs)
    hc = sum(any(HEAD_C.search(c) for c in bash_cmds(f)) for f in fs)
    cat = sum(any(re.search(r"\bcat\b[^|;&\n]*cases\.csv", c) for c in bash_cmds(f)) for f in fs)
    either = sum(any(HEAD_N.search(c) or HEAD_C.search(c) for c in bash_cmds(f)) for f in fs)
    report(f"cases.csv `head -N` peeks, {d}", hn, 32, f"(also `head -c`: {hc}; either kind: {either} of {len(fs)}; answers with `cat` of cases.csv: {cat})")

# 3. answers that never ran the folder's tool (treatment v1; stated in commit 5cec281)
never = sum(not any("tools/cases.py" in json.dumps(b["input"]) for b in tool_calls(f)) for f in files("treatment"))
report("treatment answers that never ran tools/cases.py", never, 5, "(stated in commit 5cec281)")

# 4. control answers mentioning an estimate
fs = files("control")
n = sum("estimate" in final_text(f).lower() for f in fs)
report("control answers whose final text mentions 'estimate'", n, 38, f"(of {len(fs)})")

# 5. shell calls in the no-Python arms (tools Read,Grep,Glob): executed vs attempted
att = ok = tot = 0
for d in ("nocode/raw-files", "nocode/treatment", "nocode/folder-nocode"):
    for f in files(d):
        tot += 1
        ev = events(f)
        ids = {b["id"] for b in tool_calls(f) if b["name"] == "Bash"}
        att += len(ids)
        for e in ev:
            if e["type"] == "user" and isinstance(e["message"]["content"], list):
                for r in e["message"]["content"]:
                    if r.get("type") == "tool_result" and r.get("tool_use_id") in ids and not r.get("is_error"):
                        ok += 1
report("shell calls that EXECUTED in the no-Python arms", ok, 0, f"(of {tot} transcripts; {att} Bash calls were ATTEMPTED and every one was refused as 'No such tool available')")

# 6. tool calls that reached outside their run (audit_strict.py)
p = subprocess.run([sys.executable, str(ROOT / "audit_strict.py")], capture_output=True, text=True, cwd=ROOT)
last = p.stdout.strip().splitlines()[-1]
m = re.match(r"(\d+) transcripts; (\d+) tool calls reached .*; (\d+) tried and were DENIED", last)
print(f"audit_strict.py: {last}")
report("tool calls that reached outside their run", int(m.group(2)), 0, "(results.md also says 'across 225 transcripts'; audit_strict.py now covers %s)" % m.group(1))
print(f"\n{sum(rows)} of {len(rows)} stated counts agree")
