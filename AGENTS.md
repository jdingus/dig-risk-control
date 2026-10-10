# AGENTS.md: dig-risk-control

## What this is
An entry for Clief Notes Weekly Comp #14, "The Control". Can a folder help a model answer actuarial questions
(frequency, severity, repeat rate, trend) about 9,958 Indiana dig-damage enforcement cases (state orders,
2021-2025)? That is about 1.9M tokens, too big to paste into one prompt. Round 1, the pilot on the dig law
itself, is a separate repo: indiana-dig-law-control.

## Stack
Python 3 scripts. The data steps use pypdf and PyMuPDF via `uv run --with`. Answers come from the Claude Code
CLI (`claude -p`). Checks: `data/scripts/verify.py`, plus the answer-key and grading scripts once they exist.

## How to run
- Data pipeline: see `data/README.md` (step order, exact commands).

## Key files
- `data/originals/`: the 58 state orders and the 2025 law, unchanged; `data/SOURCES.csv` has their URLs and SHA-256.
- `data/cases_clean.csv`: one row per case = `cases.csv` plus the rows in `corrections.csv`.

## Conventions / what to avoid
- Originals are never edited. Every change after parsing is a row in `data/corrections.csv`, with evidence.
- Questions, the answer-key script and its answers are committed before any folder file and before any run.
- Runs happen in an empty temporary directory, never inside this repo: Claude Code loads CLAUDE.md and
  AGENTS.md from every parent directory, and that would contaminate the arms.
- Never edit, drop or re-run over a committed raw run. Never force-push. This repo will be public.

## Where it's tracked
The Comp #14 entry on the brain's icm-builder project page. No issue tracker yet.
