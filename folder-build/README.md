# How the folder was built

The folder was built after `questions.md` (commit 134737f) and after the control run (9ca642a), by a separate
agent (Claude Sonnet 5.5) working in a sealed staging copy. Its inputs were only: the shared preamble (the
definitions every arm gets), `data/cases_clean.csv`, `data/SCHEMA.md`, `data/schema.json`, `data/README.md`,
`data/SOURCES.csv`, the 2025 law PDF, and a list of competition-building habits (icm-builder's winning-patterns,
used as guidance only). It never saw the 10 questions, the held-out questions or `key/`.

These scripts are the ones it used outside the folder: `extract_law.py` (the law PDF to text) and
`build_examples.py` (runs the tool and pastes its real output into `examples.md`).

Checked with icm-builder's `icm-check.py`: 10 PASS, 1 FAIL. The FAIL is rule 1 (it wants AGENTS.md and a
CLAUDE.md pointer at the folder root); adding them would break the brief's "usual five", so README.md is the
front door instead.
