# How folder-nocode/ was built

For the no-Python test (predictions-nocode.md, committed first in 4820967). A separate agent (Claude Sonnet 5.5)
that never saw the questions, the held-out questions or key/ built it from: the shared preamble, the data and
its schema, the 2025 law, and the shipped folder as a starting point. It chose the summary cuts itself.

`make_tables.py` (stdlib only) regenerates every table in `folder-nocode/reference/tables/` from
`data/cases_clean.csv` (adjust its input path) and runs 14 spot checks against independent re-computations
(SQLite, a regex-free parser, a histogram walk); it exits non-zero if any disagree. INDEX.md is hand-written.

Re-running regenerates every value identically. Rows that tie on their sort key can come out in a different
order between runs (Python's per-process string hashing); set PYTHONHASHSEED=0 for a fixed order. The committed
tables are this script's output when run from the repo.
