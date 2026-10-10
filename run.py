#!/usr/bin/env python3
"""Round 2 run harness: one fresh sandboxed `claude -p` session per answer.

  python3 run.py <arm> [--only Q1] [--reps N] [--workers N]
  python3 run.py --preflight          prove the sandbox starts and denies (tiny model call)
  python3 run.py <arm> --dry-run      print the jobs and the estimated cost, run nothing

Arms (ARMS below) are lists of repo-relative paths copied into an empty temp dir. A session
can use Read/Grep/Glob/Bash (Python) and can see ONLY that temp dir: Bash runs in the
Claude Code OS sandbox (bubblewrap on Linux/WSL2, Seatbelt on macOS) with reads of /home,
/root, /Users, the rest of /tmp, the harness dir and $HOME denied and no network; the file
tools are fenced by permission rules. Every event is saved untouched to
<arm>/raw/<qid>-r<n>.jsonl; run settings, the exact command and timing go in
<arm>/raw/<qid>-r<n>.meta.json. Nothing already saved is overwritten. audit.py checks the
transcripts for any path outside the run dir.
"""
import argparse
import concurrent.futures as cf
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
# The data repo. If run.py lives inside it, that is HERE; otherwise DIG_REPO or the default.
REPO = pathlib.Path(os.environ.get("DIG_REPO") or HERE).resolve()  # the repo root: where run.py lives

MODEL = "claude-sonnet-5-5"
EFFORT = None  # set by --effort; None = the CLI default
REPS = 3
WORKERS = 4
TIMEOUT_S = 1200
PERMISSION_MODE = "default"  # pinned so a run does not inherit the caller's mode (it was auto)
MAX_TURNS = None  # None = no cap; set an int to pass --max-turns

# arm -> repo-relative paths (files or directories) copied into the run dir, keeping their
# relative path. A glob (*) is allowed. "folder" does not exist in the repo yet: until it does,
# running that arm stops with a clear message instead of running an empty folder arm.
# Where each arm's transcripts go. The brief names the with-folder run "treatment/".
OUT_DIR = {"folder": "treatment", "raw": "raw-files"}

ARMS = {
    "control": [],
    "raw": ["data/originals/orders/*.pdf", "data/text/*.txt"],
    "folder": ["folder"],
}

SYSTEM_PROMPT = (
    "You are a careful analyst. You can use the Read, Grep, Glob and Bash tools (Bash has "
    "Python 3). Your working directory is the only place you may look for files; use only "
    "files in it. Show the number or answer each question asks for in your final reply."
)


# ---------- prompts ----------
def preamble():
    text = (REPO / "questions.md").read_text()
    m = re.search(r"^## The preamble every arm gets\s*\n(.*?)(?=^## )", text, re.M | re.S)
    if not m:
        sys.exit("preamble section not found in questions.md")
    lines = [l for l in m.group(1).splitlines() if l.startswith(">")]
    return "\n".join(re.sub(r"^> ?", "", l) for l in lines).strip()


def questions():
    out = []
    for name in ("questions.md", "heldout-questions.md"):
        p = REPO / name
        if not p.exists():
            print(f"note: {name} not found, skipping", file=sys.stderr)
            continue
        for m in re.finditer(r"^## ([QH]\d+)\. (.+)$", p.read_text(), re.M):
            out.append((m.group(1), m.group(2).strip()))
    return out


def build_prompt(pre, q):
    return pre + "\n\n" + q


# ---------- run dir + settings ----------
def copy_arm_files(arm, dest):
    n = 0
    for spec in ARMS[arm]:
        hits = sorted(REPO.glob(spec))
        if not hits:
            sys.exit(f"arm {arm!r}: nothing matches {spec!r} in {REPO} "
                     f"(the arm's files do not exist yet)")
        for src in hits:
            rel = src.relative_to(REPO)
            tgt = dest / rel
            tgt.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(src, tgt)
            else:
                shutil.copy2(src, tgt)
            n += 1
    return n


def settings_for(rundir):
    """Per-run settings. Key names are from code.claude.com/docs/en/sandboxing and
    settings-reference (checked 2026-10-10, Claude Code 2.1.296)."""
    rd = str(pathlib.Path(rundir).resolve())
    home = str(pathlib.Path.home().resolve())
    uid = os.getuid() if hasattr(os, "getuid") else 0
    deny_read = ["/home", "/root", "/Users", "/tmp", "/private/tmp", home, str(HERE), str(REPO),
                 "/tmp/claude", f"/tmp/claude-{uid}", f"/private/tmp/claude-{uid}"]
    # macOS: realpath of /tmp is /private/tmp; Linux: same path. Keep both spellings of the run dir.
    allow_read = sorted({rd, str(rundir)})
    deny_read = sorted({p for p in deny_read if os.path.exists(p)})
    return {
        "sandbox": {
            "enabled": True,
            "failIfUnavailable": True,
            "allowUnsandboxedCommands": False,
            "autoAllowBashIfSandboxed": True,
            "filesystem": {"denyRead": deny_read, "allowRead": allow_read},
            "network": {"allowedDomains": [], "strictAllowlist": True},
        },
        "permissions": {
            "blockReadsOutsideWorkingDirectories": True,
            "deny": [
                "WebFetch", "WebSearch",
                # Read deny rules also cover Grep and Glob; // = absolute path.
                "Read(//home/**)", "Read(//root/**)", "Read(//Users/**)",
                "Read(//private/tmp/**)", "Read(//tmp/claude/**)", f"Read(//tmp/claude-{uid}/**)",
                "Read(~/**)",
                f"Read(//{HERE.as_posix().lstrip('/')}/**)",
                f"Read(//{REPO.as_posix().lstrip('/')}/**)",
            ],
        },
    }


def child_env(tmpdir):
    env = dict(os.environ)
    # Claude Code keeps its scratch files in <TMPDIR>/claude-<uid>/ and the sandbox re-opens that for
    # Bash. The default (/tmp/claude-<uid>) holds EVERY earlier session on the machine, so give each
    # run its own empty one.
    env["CLAUDE_CODE_TMPDIR"] = str(tmpdir)
    env["CLAUDE_CODE_DISABLE_CLAUDE_MDS"] = "1"       # no user/project CLAUDE.md or memory
    env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"
    return env


ENV_OVERRIDES = {"CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1", "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
                 "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"}


def make_command(settings_path, system_prompt, prompt, permission_mode=None):
    cmd = ["claude", "-p", "--model", MODEL, "--output-format", "stream-json", "--verbose",
           "--tools", "Read,Grep,Glob,Bash", "--allowedTools", "Read,Grep,Glob,Bash",
           "--setting-sources", "", "--settings", str(settings_path),
           "--strict-mcp-config", "--no-session-persistence", "--disable-slash-commands",
           "--permission-mode", permission_mode or PERMISSION_MODE]
    if EFFORT:
        cmd += ["--effort", EFFORT]
    if MAX_TURNS:
        cmd += ["--max-turns", str(MAX_TURNS)]
    return cmd + ["--system-prompt", system_prompt, prompt]


def run_one(arm, qid, rep, prompt, outdir, files=None, system_prompt=SYSTEM_PROMPT, force=False,
            tweak=None, permission_mode=None):
    """One fresh session. Returns a status string. Never overwrites a saved run unless force."""
    outdir = pathlib.Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    stem = f"{qid}-r{rep}"
    out, meta_p, set_p = outdir / f"{stem}.jsonl", outdir / f"{stem}.meta.json", outdir / f"{stem}.settings.json"
    if out.exists() and not force:
        return f"{out.name} (kept)"
    rundir = pathlib.Path(tempfile.mkdtemp(prefix="r2run-", dir="/tmp")).resolve()
    tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="r2tmp-", dir="/tmp")).resolve()
    try:
        if files is None:
            copy_arm_files(arm, rundir)
        else:
            for name, content in files.items():
                (rundir / name).write_text(content)
        settings = settings_for(rundir)
        if tweak:  # test hook only: lets sandbox_test.py isolate one layer
            tweak(settings)
        set_p.write_text(json.dumps(settings, indent=1))
        cmd = make_command(set_p, system_prompt, prompt, permission_mode)
        t0 = time.time()
        try:
            p = subprocess.run(cmd, cwd=rundir, capture_output=True, text=True,
                               timeout=TIMEOUT_S, env=child_env(tmpdir), stdin=subprocess.DEVNULL)
            rc, stdout, stderr = p.returncode, p.stdout, p.stderr
        except subprocess.TimeoutExpired as e:
            rc, stdout, stderr = "timeout", (e.stdout or ""), (e.stderr or "")
            if isinstance(stdout, bytes):
                stdout = stdout.decode(errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode(errors="replace")
        wall = round(time.time() - t0, 1)
        listing = sorted(str(f.relative_to(rundir)) for f in rundir.rglob("*") if f.is_file())
        meta = {"arm": arm, "qid": qid, "rep": rep, "model": MODEL, "effort": EFFORT, "wall_s": wall,
                "returncode": rc, "run_dir": str(rundir), "claude_tmp_dir": str(tmpdir), "files_in_run_dir_at_end": len(listing),
                "command": cmd, "env_overrides": ENV_OVERRIDES, "system_prompt": system_prompt,
                "prompt": prompt, "settings": settings, "stderr": stderr[-2000:]}
        meta_p.write_text(json.dumps(meta, indent=1))
        out.write_text(stdout)  # every event, untouched
        ok = rc == 0 and '"type":"result"' in stdout.replace('": "', '":"')
        return f"{out.name} {'ok' if ok else 'FAILED rc=%s' % rc} {wall}s"
    finally:
        shutil.rmtree(rundir, ignore_errors=True)
        shutil.rmtree(tmpdir, ignore_errors=True)


# ---------- preflight ----------
def preflight():
    """Plant a secret outside the run dir, ask the model to read it every way it can.
    Passes only if the token never appears in the transcript and the sandbox started."""
    if sys.platform.startswith("linux") and not shutil.which("bwrap"):
        sys.exit("PREFLIGHT FAIL: bubblewrap (bwrap) not found. Linux/WSL2 needs: bubblewrap socat")
    if shutil.which("claude") is None:
        sys.exit("PREFLIGHT FAIL: claude CLI not found")
    token = "CANARY-" + os.urandom(8).hex()
    plant = pathlib.Path(tempfile.mkdtemp(prefix="r2plant-", dir="/tmp")).resolve()
    (plant / "secret.txt").write_text(token + "\n")
    prompt = (f"Sandbox self-test. Try to read {plant}/secret.txt with the Read tool, then with "
              f"Bash `cat {plant}/secret.txt`, then Bash `ls {pathlib.Path.home()}`. Report what "
              f"each attempt returned. Then run Bash `echo hello > ok.txt && cat ok.txt` and report it.")
    out = pathlib.Path(tempfile.mkdtemp(prefix="r2pre-", dir="/tmp"))
    try:
        msg = run_one("preflight", "PRE", 1, prompt, out, files={"readme.txt": "preflight\n"})
        raw = (out / "PRE-r1.jsonl").read_text() if (out / "PRE-r1.jsonl").exists() else ""
        meta = json.loads((out / "PRE-r1.meta.json").read_text())
    finally:
        shutil.rmtree(plant, ignore_errors=True)
        shutil.rmtree(out, ignore_errors=True)
    if token in raw:
        sys.exit("PREFLIGHT FAIL: the sandbox let the model read a file outside the run dir")
    if meta["returncode"] != 0:
        sys.exit(f"PREFLIGHT FAIL: claude exited {meta['returncode']}: {meta['stderr'][:500]}")
    if "hello" not in raw:
        sys.exit("PREFLIGHT FAIL: sandboxed Bash could not run inside the run dir")
    print("PREFLIGHT OK: sandbox started, outside read denied, run-dir Bash works")


# ---------- main ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("arm", nargs="?")
    ap.add_argument("--only")
    ap.add_argument("--reps", type=int, default=REPS)
    ap.add_argument("--workers", type=int, default=WORKERS)
    ap.add_argument("--preflight", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--model", help="model id (default claude-sonnet-5-5)")
    ap.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"])
    ap.add_argument("--out", help="write transcripts to <OUT>/raw instead of the committed arm folder (for re-runs)")
    a = ap.parse_args()
    global MODEL, EFFORT
    MODEL = a.model or MODEL
    EFFORT = a.effort or EFFORT
    if a.preflight:
        return preflight()
    if a.arm not in ARMS:
        sys.exit(f"arm must be one of {list(ARMS)}")
    qs = [(i, q) for i, q in questions() if not a.only or i == a.only]
    if not qs:
        sys.exit("no questions matched")
    pre = preamble()
    jobs = [(qid, q, r) for qid, q in qs for r in range(1, a.reps + 1)]
    print(f"{a.arm}: {len(jobs)} answers ({len(qs)} questions x {a.reps} reps), model {MODEL}, effort {EFFORT or 'default'}", flush=True)
    if ARMS[a.arm]:  # fail early if the arm's files are missing
        probe = pathlib.Path(tempfile.mkdtemp(prefix="r2probe-", dir="/tmp"))
        try:
            copy_arm_files(a.arm, probe)
        finally:
            shutil.rmtree(probe, ignore_errors=True)
    if a.dry_run:
        return
    outdir = (pathlib.Path(a.out) / "raw") if a.out else HERE / OUT_DIR.get(a.arm, a.arm) / "raw"
    # Never write inside any arm's input files: a later run would copy earlier answers (aborted/folder-arm-attempt-1).
    for paths in ARMS.values():
        for pat in paths:
            top = (HERE / pat.split("/")[0]).resolve()
            if top != HERE.resolve() and (outdir.resolve() == top or top in outdir.resolve().parents):
                raise SystemExit(f"refusing to write output inside arm input {top}")
    with cf.ThreadPoolExecutor(a.workers) as ex:
        for msg in ex.map(lambda j: run_one(a.arm, j[0], j[2], build_prompt(pre, j[1]), outdir), jobs):
            print(msg, flush=True)


if __name__ == "__main__":
    main()
