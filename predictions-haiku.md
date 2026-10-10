# Predictions for the Haiku pair (written before any Haiku run)

Why this second pair: with Sonnet 5.5, the raw orders plus Python scored 53/60 and tied the folder on the held-out
set. A smaller, cheaper model may not brute-force 10,000 pages as well, and that is where a folder should show up
in accuracy, not only in cost. Same questions, same key, same preamble, same sandbox, same three arms. Only the model
and effort change: `--model claude-haiku-5-5 --effort low`. Transcripts go to `haiku/control/`, `haiku/raw-files/`,
`haiku/treatment/` (the shipped folder, v1). Graded blind, mixed across the three Haiku arms, in `grading-haiku/`.

| Arm | Predicted, my 10 questions (of 60) | Predicted, held-out (of 30) |
|---|---|---|
| control (no data) | 0 | 0 |
| raw orders | 20–40 | 10–20 |
| folder | 50–60 | 25–30 |

Also predicted:
- The folder's accuracy advantage over raw HOLDS on the held-out set for Haiku (unlike Sonnet).
- Every Haiku arm is faster per answer (median seconds) than the same Sonnet arm.
- The Haiku folder arm uses at most half the tokens of the Haiku raw arm.
- If any of these fail, results.md says so.
