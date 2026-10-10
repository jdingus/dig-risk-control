#!/usr/bin/env bash
# Re-run one arm of round 2.   usage: ./rerun.sh <control|raw|folder> [--only Q1] [--reps N] [--dry-run]
# Prints the number of answers first, checks prerequisites, proves the sandbox works with a
# one-call self-test, then runs. Refuses to run if the sandbox cannot start.
set -euo pipefail
cd "$(dirname "$0")"
arm="${1:-}"; [ -n "$arm" ] || { echo "usage: $0 <control|raw|folder> [--only Q1] [--reps N] [--dry-run]"; exit 2; }
shift || true

fail() { echo "REFUSING TO RUN: $*" >&2; exit 1; }

command -v python3 >/dev/null || fail "python3 not found"
command -v claude  >/dev/null || fail "claude CLI not found (install Claude Code 2.1.296 or later)"
claude auth status 2>/dev/null | grep -q '"loggedIn": true' || fail "claude CLI is not logged in (run: claude auth login)"

case "$(uname -s)" in
  Linux)
    command -v bwrap >/dev/null || fail "bubblewrap missing. Install: sudo apt install bubblewrap socat"
    command -v socat >/dev/null || fail "socat missing. Install: sudo apt install bubblewrap socat"
    ;;
  Darwin) : ;;  # Seatbelt is built in; nothing to install
  *) fail "unsupported OS $(uname -s): the sandbox runs on Linux, WSL2 and macOS only" ;;
esac

# 1. cost: how many answers (each answer is one claude -p session on claude-sonnet-5-5)
python3 run.py "$arm" --dry-run "$@"
echo "(each answer is one fresh session; the 'raw' and 'folder' arms read files with tools, so they cost more than 'control')"

# 2. the sandbox must start and must deny a planted file outside the run dir
python3 run.py --preflight

# 3. run, then audit
python3 run.py "$arm" "$@"
python3 audit.py "$arm/raw" || echo "audit: outside-path mentions found; read them before trusting this arm"
