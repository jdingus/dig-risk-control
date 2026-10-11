#!/usr/bin/env bash
# Re-run one arm of round 2.
#   usage: ./rerun.sh <control|raw|folder> [--only Q1] [--reps N] [--out DIR] [--dry-run] [--no-sandbox]
# Prints the number of answers first, checks prerequisites, proves the sandbox works with a
# one-call self-test, then runs, then audits what it just wrote (the --out directory, or the
# arm's committed directory if there is no --out). Refuses to run if the sandbox cannot start.
#
# --no-sandbox is the UNSANDBOXED route for machines that cannot install bubblewrap/socat.
# It skips the sandbox checks and the self-test, and nothing then stops the model's shell from
# reading outside its folder. Audit it (this script does) and read the audit.
set -euo pipefail
cd "$(dirname "$0")"
arm="${1:-}"; [ -n "$arm" ] || { echo "usage: $0 <control|raw|folder> [--only Q1] [--reps N] [--out DIR] [--dry-run] [--no-sandbox]"; exit 2; }
shift || true

fail() { echo "REFUSING TO RUN: $*" >&2; exit 1; }

# which flags did the caller pass?
out=""; nosandbox=0; dry=0; prev=""
for a in "$@"; do
  [ "$prev" = "--out" ] && out="$a"
  case "$a" in --out=*) out="${a#--out=}" ;; --no-sandbox) nosandbox=1 ;; --dry-run) dry=1 ;; esac
  prev="$a"
done

# where this arm's committed transcripts live (run.py's OUT_DIR: folder -> treatment, raw -> raw-files)
case "$arm" in
  folder) committed="treatment" ;;
  raw)    committed="raw-files" ;;
  *)      committed="$arm" ;;
esac

command -v python3 >/dev/null || fail "python3 not found"
command -v claude  >/dev/null || fail "claude CLI not found (install Claude Code 2.1.296 or later)"
# A logged-in CLI or ANTHROPIC_API_KEY in the environment is enough. A dry run needs neither.
if [ "$dry" = 0 ] && [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  claude auth status 2>/dev/null | grep -Eq '"loggedIn"[[:space:]]*:[[:space:]]*true' \
    || fail "not logged in: run 'claude auth login', or set ANTHROPIC_API_KEY in the environment"
fi

if [ "$nosandbox" = 0 ]; then
  case "$(uname -s)" in
    Linux)
      command -v bwrap >/dev/null || fail "bubblewrap missing. Install: sudo apt install bubblewrap socat   (or use the UNSANDBOXED route: add --no-sandbox --out DIR)"
      command -v socat >/dev/null || fail "socat missing. Install: sudo apt install bubblewrap socat   (or use the UNSANDBOXED route: add --no-sandbox --out DIR)"
      ;;
    Darwin) : ;;  # Seatbelt is built in; nothing to install
    *) fail "unsupported OS $(uname -s): the sandbox runs on Linux, WSL2 and macOS only (or use the UNSANDBOXED route: add --no-sandbox --out DIR)" ;;
  esac
fi

# 1. cost: how many answers (each answer is one claude -p session on claude-sonnet-5-5)
python3 run.py "$arm" --dry-run "$@"
echo "(each answer is one fresh session; the 'raw' and 'folder' arms read files with tools, so they cost more than 'control')"
[ "$dry" = 1 ] && exit 0

# 2. the sandbox must start and must deny a planted file outside the run dir
if [ "$nosandbox" = 0 ]; then
  python3 run.py --preflight
else
  echo "UNSANDBOXED: skipping the sandbox self-test. Nothing stops the model reading outside its folder." >&2
fi

# 3. run, then audit what was just written
python3 run.py "$arm" "$@"
if [ -n "$out" ]; then target="$out/raw"; else target="$committed/raw"; fi
if [ -d "$target" ]; then
  python3 audit.py "$target" || echo "audit: outside-path mentions found; read them before trusting this arm (audit.py is broad: page text and arithmetic count)"
  python3 audit_strict.py "$target" || echo "audit_strict: a tool call reached outside its run; this run is void"
else
  echo "audit: nothing to audit, $target does not exist" >&2
fi
