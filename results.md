# Results

**The question:** can a folder help a model answer actuarial questions about 9,958 Indiana dig-damage
enforcement cases (58 state orders, 2021–2025, about 1.9M tokens: too big to paste into one prompt)?

**Same model** (Claude Sonnet 5.5), **same preamble and questions, same tools** (Read, Grep, Glob, a shell with
Python), **one fresh sandboxed session per answer** that can see only its own arm's files, no web. Three runs
of every question in every arm. Graded blind against an answer key computed by script and committed first.

## The three arms

| Arm | What the model had | Folder? | Transcripts |
|---|---|---|---|
| **control: no folder, no files** | nothing (the brief's required "no folder" run) | no | `control/raw/` |
| **raw files, no folder** | the 58 orders as published (PDF) and their page text | no | `raw-files/raw/` |
| **folder** | `folder/`: README, identity, rules, examples, reference/ (the cleaned table, schema, glossary, law text, a query tool) | yes | `treatment/raw/` |

"No folder, no files" is the literal "no folder" run the brief asks for: here the folder is where the data lives, so
this arm has nothing to compute from and scores 0 by construction. "Raw files, no folder" is the control that matters: the same data
with no map, no definitions and no cleaning. That is the comparison that tests the folder.

## Correctness

0 = wrong or refused, 1 = partial, 2 = full, per the tolerances in `questions.md`. Three runs, so 6 is the
maximum per question. From `grading/scores.md`.

| Q | Topic | no folder, no files | raw files, no folder | folder |
|---|---|---|---|---|
| Q1 | share of 16(h) and 20(a)(2) cases | 0 | 6 | 6 |
| Q2 | cases per year, busiest year | 0 | 6 | 6 |
| Q3 | mean penalty, 16(h) vs 20(a)(2) | 0 | **4** | 6 |
| Q4 | warning-letter rate, utility vs not | 0 | 6 | 6 |
| Q5 | training-option rate | 0 | 6 | 6 |
| Q6 | repeat respondents (5+ cases) | 0 | **5** | 6 |
| Q7 | mean penalty per case, 2021 vs 2025 | 0 | **5** | 6 |
| Q8 | "ticket escalation" count, its usual penalty | 0 | **5** | 6 |
| Q9 | most-hit utility, its share | 0 | **4** | 6 |
| Q10 | expired-ticket and prior shares | 0 | 6 | 6 |
| | **my 10 questions** | **0/60** | **53/60** | **60/60** |
| H1–H5 | held-out: geography, reporting lag, abstentions, outcomes by tag, 2023→24 shift | 0 | 30 | 30 |
| | **5 held-out questions (another author)** | **0/30** | **30/30** | **30/30** |

## Cost and speed

Medians per answer, from the transcripts (`grading/scores.md`). List price as reported by Claude Code; the runs
used a subscription, so nothing was billed.

| | no folder, no files | raw files, no folder | folder |
|---|---|---|---|
| tokens (input incl. cache + output) | 25,180 | 142,817 | 61,662 |
| tool calls | 3 | 9 | 5 |
| seconds | 7 | 30 | 12 |
| list price, all 45 answers | $1.02 | $5.42 | $2.58 |

## What the folder actually won, and why

- **Against "no folder, no files": everything.** 0 vs 60. Not informative: that arm had nothing to compute from. Every control answer said
  it had no data; 38 of 45 mention an estimate, and some declined to give one (`python3 grading/claims.py`
  recomputes this count from the transcripts).
- **Against the raw orders: 7 points of 60, all near-misses on one number.** Every raw-arm miss was a number
  just outside tolerance, never a wrong method or a refusal. The one I traced to the bottom: Q8. The raw arm
  counted **452** "ticket escalation" cases; the key says **446**. The uncorrected parse gives exactly 452. The
  difference is 8 checkbox-style forms that print the whole menu of options; `data/corrections.csv` records what
  was actually ticked, read from the page images (`data/evidence/`). So that win came from **cleaning a person
  checked**, not from the map or the rules. The other misses look like the same kind of thing (a mean penalty
  off by $1–2 from amount parsing; 180 repeat respondents instead of 187 from name variants; 40.6% instead of
  41.6% from other-party name variants), but I did not trace each one.
- **Against the raw orders: about 2.3× fewer tokens, 2.5× faster, half the cost.** The folder's tool and clean
  table replace parsing 10,000 pages per answer.

## Where the folder tied, or lost

1. **Tied on 5 of my 10 questions** (Q1, Q2, Q4, Q5, Q10) **and on all 5 held-out questions.** The judges ask
   whether the folder's advantage holds on a question I did not write. **On correctness, it does not:** on the
   held-out set, the raw orders plus Python scored 30/30, the same as the folder. The advantage that does hold
   there is cost: on the held-out set the raw arm used a median 126,166 tokens and 26 s per answer, the folder
   58,427 and 12 s (2.2×; on my questions, 149,002 vs 62,360).
2. **The folder's own v2 change failed.** After the first run, only 4 of 45 folder answers read the README in
   their first two commands, and they paged through `cases.csv` with `head` 32 times (counting commands; counting
   answers, 33 of 45 did it at least once). I added a "Start here" block
   at the top of the README telling it not to (commit 5cec281, prediction in the commit message: tokens down 15%,
   peeks down to 10 or fewer). Result (`treatment-v2/`): **tokens up 22%** (75,183 vs 61,662), **peeks unchanged**
   (32 commands again; 33 of 45 answers again), correctness unchanged (60/60, 30/30). The README-reading, peek and never-used-the-tool counts are
   recomputed from the transcripts by `python3 grading/claims.py` (it counts answers, which is why it reports 33).
   The prediction in 5cec281 used the command count (32). An instruction in a file did not change what the model did, and
   the extra text cost tokens. I restored v1 (8f50ad0). The shipped folder is v1.
3. **My predictions, scored** (from `questions.md`, written before any run):

   | Prediction | Result |
   |---|---|
   | control 0–2 of 20 per run | right (0) |
   | raw 10–14 of 20 per run | **wrong**: about 18 |
   | folder 17–20 of 20 per run | right (20) |
   | folder uses at least 3× fewer tokens than raw | **wrong**: 2.3× |
   | raw ties the folder on at least one question | right, and far more than I expected (5 + all 5 held-out) |

   I underestimated a model with Python and raw page text by a wide margin.
4. **The folder fails one structural check.** icm-builder's `icm-check.py` wants AGENTS.md and a CLAUDE.md pointer
   at the folder root (rule 1). Adding them would break the brief's five-item shape, so I didn't (`folder-build/README.md`).

## The Haiku pair: where the folder pays (pre-registered in predictions-haiku.md, a1c6ce6)

Same questions, key, preamble, sandbox and arms; only `--model claude-haiku-5-5 --effort low`. Graded blind,
mixed across the three Haiku arms (`grading-haiku/scores.md`).

| Haiku 5.5, low effort | no folder, no files | raw files, no folder | folder |
|---|---|---|---|
| my 10 questions | 0/60 | 55/60 | **60/60** |
| held-out | 0/30 | 28/30 | **30/30** |
| tokens per answer (median) | 16,987 | **401,098** | 84,870 |
| seconds per answer (median) | 5 | 56 | 13 |
| list price, all 45 answers | $0.06 | $0.75 | **$0.20** |

- **The cheap model plus the folder matched the expensive model, for a fraction of the cost.** Haiku with the
  folder scored 60/60 and 30/30, the same as Sonnet with the folder ($2.58) and better than Sonnet with the raw
  orders (53/60, $5.42). List price for the 45 answers: $0.20.
- **Without the folder, Haiku stayed accurate but got expensive.** Haiku's raw arm scored 55/60 (slightly above
  Sonnet's raw arm) by brute force: a median 16 tool calls and 401,098 tokens per answer, 4.7× the folder.
- **On the held-out set the folder's advantage held for Haiku, barely:** 30 vs 28, both points on H1 (the city
  count: 1,124 and 1,139 against 1,153).

**My Haiku predictions, scored:**

| Prediction | Result |
|---|---|
| raw 20–40 of 60, held-out raw 10–20 of 30 | **wrong**: 55 and 28. Haiku brute-forced the raw pages far better than I expected |
| folder 50–60, held-out 25–30 | right: 60 and 30 |
| the folder's advantage holds on the held-out set | right, but by 2 points of 30 |
| every Haiku arm faster than the same Sonnet arm | **wrong**: raw 56 s vs 30 s, folder 13 s vs 12 s; only the empty control was faster |
| Haiku folder uses at most half the Haiku raw tokens | right: about a fifth |

## Take the Python away (pre-registered in predictions-nocode.md, 4820967)

Is the folder's edge the folder, or the Python it lets the model run? Same questions, key and sandbox; Haiku 5.5 at
low effort; tools `Read,Grep,Glob` only (0 shell calls ran in all 135 transcripts: the models tried Bash 71 times and every attempt was refused as an
unavailable tool; counted by `grading/claims.py`). A third folder, `folder-nocode/`,
was built for this by a sealed agent: the same five-item shape with ~37k tokens of pre-computed summary tables and
no table or tool (578f3fc, after the predictions). Graded blind together (`grading-nocode/scores.md`).

**The 2×2 (Haiku):** my 10 questions / held-out / tokens per answer (median)

| | raw files, no folder | folder |
|---|---|---|
| **with Python** | 55/60 · 28/30 · 401,098 | 60/60 · 30/30 · 84,870 |
| **no Python** | 30/60 · 18/30 · 193,367 | shipped folder: 36/60 · 23/30 · 132,038 · **pre-computed folder: 55/60 · 30/30 · 59,924** |

- **Without code, the folder makes the difference, and it holds on questions I did not write:** pre-computed folder
  55/60 and 30/30, raw files 30/60 and 18/30. This is the clearest folder advantage in the whole entry.
- **The folder has to fit the deployment.** The shipped folder relies on its Python tool; without code it barely
  beat raw files (36 vs 30). The folder built for no code nearly matched the with-Python results, and was the
  cheapest and fastest of the no-Python arms (60k tokens, 11 s per answer, $0.26 list for 45 answers, against
  132,038 tokens, 26 s and $0.45 for the shipped folder and 193,367, 44 s and $1.34 for raw files). It is not the
  cheapest arm of the entry: Haiku with the shipped folder and Python scored 60/60 and 30/30 for $0.20, and the
  control arms cost less still but score 0.
- **Where the folder lost to raw files** (the brief's "no folder got it right and the folder got it wrong"):
  without Python, the shipped folder scored below raw files on **Q7** (0/6 vs 1/6) and **Q9** (0/6 vs 3/6). It could
  not run its own tool and had no pre-built table for those cuts; the raw arm salvaged partial answers by searching
  page text. These are the only questions in the whole entry where a folder arm scored below a raw-files arm.
- **Where the pre-computed folder still missed:** cuts nobody pre-built. Q6 (repeat respondents, 4/6) uses the
  question's own name normalisation; the tables have exact and loose spellings. Q8 (escalation count, 3/6).
- **Disclosure:** the pre-computed tables include cuts that match some sealed questions: top cities (H1), damage-to-
  order lag (H2), abstentions by year (H3), names with k+ cases (Q6). The builder never saw the questions; these are
  ordinary actuarial cuts. It is also exactly the trade this test measures: a no-code folder wins where it pre-built
  the cut, and loses where it did not.

**My no-Python predictions, scored: every row wrong, in the same direction.**

| Arm | Predicted (my 10 / held-out) | Result |
|---|---|---|
| raw files, no folder | 5–20 / 0–10 | **30 / 18** |
| shipped folder | 5–20 / 0–10 | **36 / 23** |
| pre-computed folder | 30–50 / 10–25 | **55 / 30** |

I underestimated read-and-search: `grep -c` answers plain counting questions (Q1, Q2, Q10 were full marks in
every arm) without any code. What failed without code were means and medians (Q3, Q7), name grouping (Q6) and
custom cuts (H2): the things a folder can carry pre-computed.

## Reproduction

- **Fresh clone, same commands a judge runs** (`rerun-fresh-clone/`): cloned from GitHub at bec716b, preflight,
  then every question once in every arm. Graded blind together with the v2 run (`grading-2/scores.md`):
  control 0/20, raw **18/20**, folder **20/20**; held-out 0/10, 10/10, 10/10. Raw missed the same kind of
  near-miss on Q6 and Q9 as in the main run. Medians: raw 127,548 tokens, folder 63,776.
- **Not in the cloud.** The plan was to re-run in a Claude Code cloud session. The sandbox could not start there
  (no bubblewrap or socat, and installing socat was refused by the session's safety classifier: issue #1). The
  session stopped instead of running unprotected. So both the committed runs and the re-run are on one Linux machine.
- **Variation run to run:** the folder scored 2 on every run of every question in every set (main, v2, re-run).
  The raw arm's misses moved between questions but stayed one-number near-misses.

## How far to trust this

- **One grader per answer** (Claude Sonnet 5.5), blind to the arm, but folder answers are easy to spot (they cite
  the tool). Graders followed numeric tolerances, so there was little room for taste. I checked every judgment
  call in the `notes` of `grading/grades/*.json` and changed no grade.
- **The answer key and the folder share one table.** `data/cases_clean.csv`, the table the key is computed from, and
  `folder/reference/cases.csv` have the same sha256. So a shared parsing or cleaning error would sit in the key and
  the folder alike, and the folder arm cannot expose it. The raw-files arm, which parsed the PDFs itself, is the only
  independent check on the cleaning (where it disagreed, Q3 and Q6 to Q9, I traced only Q8).
- **The held-out questions were written by a model agent that I, the orchestrating session, directed and saw.**
  They are not questions from a stranger, and I do not claim that. They were committed before the folder and before
  any run, and the folder's builder never saw them.
- **The answer key** was computed twice, by two scripts from two agents who could not see each other's
  (`key/compute_answers.py`, `key/xcheck/`); `python3 key/compare.py` confirms all 31 values agree.
- **The folder was built blind to the questions.** A separate agent built it from the shared definitions and the
  data only, after the questions and the control run were committed. **But two of its examples are close in
  technique to sealed questions:** example 1 (non-utility cases at $4,000+, 2022–23) resembles H5 ($5,000+,
  2023–24), and example 2 (recurring names) resembles Q6. I left them: changing the folder with knowledge of the
  test would be the real violation.
- **The orchestrating session (me) saw the held-out questions and answers** when they were written. The folder's
  builder did not, and nothing from them went into its instructions (`heldout-questions.md` says so at the top).
- **The folder includes a tool that implements the shared definitions.** Every arm got the same definitions in
  its prompt; the raw arm had to implement them itself. That is part of what a folder can carry, and it is a big
  part of why the folder is cheaper.
- **A harness bug, caught and kept.** The first folder-arm attempt wrote its transcripts inside `folder/`, where
  later answers could have seen them. Stopped within a minute, kept in `aborted/` with an explanation, fixed in
  b39ad40, re-run from scratch.
- **Sandbox, audited.** `python3 audit_strict.py`: across all 495 transcripts, **0 tool calls reached a path outside
  their own run** (no /home, no repo, no key, no other run); 2 tried (the model reading Claude Code's own saved-output
  file) and were DENIED by the sandbox. `audit.py`'s broader flags are page text and the
  model's own arithmetic; each arm's `AUDIT.txt` says which.
- **Scope.** Orders 2021–2025 only. The orders carry no company size, number of digs, trade or payment status, so
  none of the questions are true rates per dig. Indiana does not publish yearly ticket totals that we could find
  (`data/external/indiana811-volumes/`).

## Run it yourself

See README.md. One line per arm, about $1–5 of model usage per arm at list price, a few minutes each.

## Errata

- Commit 8432f08's message reads "/usr/bin/zsh.20" where it meant "$0.20": the shell expanded `$0` while committing. The files in that commit are correct. Rewriting a pushed commit would need a force-push, so it stays.
