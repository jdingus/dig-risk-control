# Predictions for the no-Python test (written before the no-code folder exists and before any run)

**Question:** is the folder's edge the folder, or the Python it lets the model run? With the shell available, the
model on raw files wrote its own parser and scored 53/60 (Sonnet) and 55/60 (Haiku). Many real deployments have no
code execution (chat apps, Claude Projects without the analysis tool, locked-down agents), and unstructured data
cannot be parsed into a table anyway. So: take the shell away (`--tools "Read,Grep,Glob"`: read and search only).

Model: Haiku 5.5, low effort (as in the Haiku pair). Same questions, key, preamble and sandbox. Three runs each.

| Arm (no shell, no Python) | What it has | Predicted, my 10 (of 60) | Predicted, held-out (of 30) |
|---|---|---|---|
| raw files, no folder | the 58 orders (PDF + page text) | 5–20 | 0–10 |
| folder (as shipped) | `folder/`: the case table, schema, glossary, law, tool (but it cannot run the tool) | 5–20 | 0–10 |
| pre-computed folder | `folder-nocode/`: the same five-item shape, plus summary tables built ahead of time | 30–50 | 10–25 |

Why: without code, nobody can average or group 9,958 rows; reading 2 MB of CSV or 10,000 pages does not fit in
context. A folder that carries the answers to general cuts (counts, sums, means by year, section, outcome,
respondent type ...) should hold on questions those cuts cover and miss the ones that need a cut nobody pre-built.

**How the pre-computed folder is built (so it is not built to pass):** a separate agent that never sees
`questions.md`, `heldout-questions.md` or `key/` gets only the shared preamble, the data and its schema, and builds
general summary tables an actuary would want, choosing the cuts itself. Its build script is committed beside it.

If any prediction fails, results.md says so.
