# key: the answer key for questions.md

`compute_answers.py` computes the expected answer to Q1-Q10 in `questions.md` from `data/cases_clean.csv`.
`answers.json` is its output: `cases_clean_sha256` (SHA-256 of the exact CSV used), `rows`, `answers`
(the named numbers per question), `interpretations` (every place the wording left a choice, and what was
chosen), and `supporting_counts` (the numerators and denominators behind each number).

Python 3, standard library only. Revised after questions.md was revised (Q3 is now a mean; Q6 normalisation re-worded; base-section definition clarified). No arguments; paths come from the script's own location.

    python3 key/compute_answers.py

The output is deterministic: a second run gives a byte-identical `answers.json`. If `cases_clean.csv`
changes, the recorded SHA-256 changes, and the key no longer matches the data the runs were scored against.

Rounding is ROUND_HALF_UP (as a human rounds), not Python's half-to-even `round()`. `supporting_counts`
shows no rounded value where the two differ.

This key was committed together with `questions.md` before any folder file or run existed. The builders of
the folder never read `key/` or `heldout-questions.md` before the runs.
