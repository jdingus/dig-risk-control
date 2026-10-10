#!/usr/bin/env python3
"""Scan saved transcripts for any tool call input or tool output that mentions a path outside the
run dir. A clean run reports nothing.

  python3 audit.py [dir-or-.jsonl ...]     default: every <arm>/raw next to this file

Each <qid>-r<n>.jsonl is checked against its .meta.json (run_dir, claude_tmp_dir). Flags:
  - any absolute path (/..., ~/...) in a tool call input or tool result that is not under the run dir
    (harmless system paths such as /usr, /bin, /lib, /etc, /dev, /proc, /sys, /opt are ignored,
    and so is Claude Code's own scratch dir for the run)
  - the marker words dig-risk-control, indiana-dig-law-control, answers.json, compute_answers, key/
  - /home/, /root, /Users/, other /tmp dirs
Exit status 1 if anything is reported.
"""
import json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
MARKERS = ["dig-risk-control", "indiana-dig-law-control", "answers.json", "compute_answers",
           "heldout-questions", "/home/", "/root", "/Users/", "r2-harness", "cases_clean"]
MARKER_RE = [re.compile(r"(?<![\w-])key/")]   # the repo's key/ folder, not "monkey/"
SYSTEM_OK = ("/usr/", "/bin/", "/lib/", "/lib64/", "/etc/", "/dev/", "/proc/", "/sys/", "/opt/", "/sbin/", "/var/lib/")
PATH_RE = re.compile(r"(?<![\w.:/-])(~/[^\s\"'`),;:<>|\\]*|/[A-Za-z0-9_.@+-][^\s\"'`),;:<>|\\]*)")


def texts(ev):
    """Yield (kind, text) for tool inputs and tool outputs in one event. Model prose is not scanned."""
    if ev.get("type") == "assistant":
        for b in ev["message"].get("content", []):
            if b.get("type") == "tool_use":
                yield "tool_call", json.dumps(b.get("input", {}))
    elif ev.get("type") == "user":
        c = ev["message"].get("content")
        if isinstance(c, list):
            for b in c:
                if b.get("type") == "tool_result":
                    x = b.get("content")
                    yield "tool_result", x if isinstance(x, str) else json.dumps(x)


def inside(path, roots):
    return any(path == r or path.startswith(r.rstrip("/") + "/") for r in roots)


def audit_file(jl):
    meta_p = jl.with_suffix("").with_suffix(".meta.json")
    meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
    run_dir = meta.get("run_dir")
    own = [d for d in (run_dir, meta.get("claude_tmp_dir")) if d]
    findings = []
    for n, line in enumerate(jl.read_text().splitlines(), 1):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            findings.append((n, "bad_json", line[:80])); continue
        for kind, text in texts(ev):
            for m in MARKERS:
                if m in text:
                    findings.append((n, kind, f"mentions {m!r}"))
            for rx in MARKER_RE:
                if rx.search(text):
                    findings.append((n, kind, "mentions 'key/'"))
            for p in set(PATH_RE.findall(text)):
                if p.startswith("~/") or (not p.startswith(SYSTEM_OK) and not inside(p, own)):
                    if p in ("/", "/*") or len(p) < 3 or p == "/tmp" or p.startswith("/tool_use_error"):
                        continue
                    findings.append((n, kind, f"path outside run dir: {p[:120]}"))
    if not run_dir:
        findings.append((0, "meta", "no .meta.json with run_dir next to this transcript"))
    return findings


def main():
    args = [pathlib.Path(a) for a in sys.argv[1:]] or [d for d in sorted(HERE.glob("*/raw")) if d.is_dir()]
    files = []
    for a in args:
        files += sorted(a.glob("*.jsonl")) if a.is_dir() else [a]
    bad = 0
    for jl in files:
        f = audit_file(jl)
        if f:
            bad += 1
            print(f"{jl}")
            for n, kind, msg in sorted(set(f)):
                print(f"   line {n} {kind}: {msg}")
    print(f"audited {len(files)} transcripts: {len(files) - bad} clean, {bad} with outside-path mentions")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
