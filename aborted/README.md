# Aborted runs (kept on purpose)

## folder-arm-attempt-1 (2026-10-10, stopped after about a minute)

A harness bug: `run.py` wrote each arm's transcripts to `<arm>/raw/`, so the folder arm wrote into
`folder/raw/`, inside the folder under test. Every later answer copies `folder/` into its sandbox, so later
answers could have seen earlier answers and their settings. Spotted while it ran; stopped by hand.

What finished before the stop: 2 answers (Q1-r1, Q2-r1), plus settings files for answers that had started.
None of this is scored or used. It is kept so the history shows what happened.

Fix (same commit): folder-arm transcripts now go to `treatment/raw/` (the name the brief uses), raw-arm
transcripts to `raw-files/raw/`, and `run.py` refuses to write output inside any arm's input files.
The folder arm was then re-run from scratch.
