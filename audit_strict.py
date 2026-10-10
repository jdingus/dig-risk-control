#!/usr/bin/env python3
"""The strict audit: does any tool CALL in any transcript name a path outside its own run directory?

audit.py flags every path-like string, including page text and the model's arithmetic. This checks only what the
model asked a tool to do: /home paths, this repo, a clone of it, key/, answers.json, the harness, or another
run's directory. Exit 1 if any call does.

  python3 audit_strict.py
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent
bad = n = 0
for f in sorted(ROOT.glob("**/raw/*.jsonl")):
    if "aborted" in f.parts:
        continue
    n += 1
    own = None
    for line in f.open():
        e = json.loads(line)
        if e.get("type") == "system" and e.get("subtype") == "init":
            own = e.get("cwd")
        if e.get("type") != "assistant":
            continue
        for b in e["message"]["content"]:
            if b.get("type") != "tool_use":
                continue
            s = json.dumps(b["input"])
            hits = re.findall(r"/home/[^\s\"']*|/Users/[^\s\"']*|dig-risk-control|repro-clone|key/|answers\.json|"
                              r"/tmp/r2run-[a-z0-9_]+|r2-harness", s)
            hits = [h for h in hits if not (own and h.startswith("/tmp/r2run-") and own.startswith(h))]
            if hits:
                bad += 1
                print(f.relative_to(ROOT), b["name"], hits[:3])
print(f"{n} transcripts; {bad} tool calls naming a path outside their own run")
sys.exit(1 if bad else 0)
