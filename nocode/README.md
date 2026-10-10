# No-Python test (pre-registered in predictions-nocode.md, commit 4820967)

Haiku 5.5, low effort, tools `Read,Grep,Glob` only: no shell, no Python (0 shell calls in all 135 transcripts).
Arms: `raw-files/` (the orders, no folder), `treatment/` (the shipped folder, whose tool it cannot run),
`folder-nocode/` (pre-computed tables, built in 578f3fc after the predictions). Graded blind together: `grading-nocode/`.
Two Read calls tried to open the session's own saved-output file and were DENIED by the sandbox
(audit_strict.py lists them).
