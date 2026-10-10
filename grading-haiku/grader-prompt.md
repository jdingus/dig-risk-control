You are a blind grader. Grade ONLY these files in grading-haiku/by-question/ (repo root: the dig-risk-control folder you were pointed to): {FILES}.
Read each file whole. Each holds one question, its expected answer (from a committed key), the scoring rule,
and 9 answers under random labels. You do not know which system wrote which answer; do not guess, and do not
open any other file in the repo (in particular not grading-haiku/key.json or any other key.json or any transcript folder).

Rules:
- Apply the scoring rule literally, number by number: for each required number, decide full / half / zero by
  the stated tolerance, then the question score: 2 = every number full; 1 = at least half the total credit;
  0 = less. A named answer (a year, a company, a city) must match exactly (ignore capitalization).
- Use only the FINAL number the answer commits to for each part. If an answer gives two different values for
  the same part, use the one it presents as its answer; if it is genuinely ambiguous, take the worse one.
- "Estimate" answers are scored the same way. Refusals score 0 for the parts they refuse.
- Ignore style, length, method and confidence.

Write one JSON file per question to grading-haiku/grades/<QID>.json:
{"qid": "Q1", "grades": {"Q1-01": {"score": 2, "parts": {"<part name>": "full|half|zero"}, "why": "one sentence quoting the decisive numbers"}, ...all 9...}, "notes": "anything odd, or empty"}

Reply with one line per question: QID and the 9 scores in label order.
