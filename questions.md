# Questions

Ten actuarial questions about Indiana dig-damage enforcement, 2021–2025. Every expected answer is
computed by `key/compute_answers.py` from `data/cases_clean.csv`, both committed with this file and before
any folder file or run. The SHA-256 of the exact `cases_clean.csv` used is recorded in `key/answers.json`.

Five more questions, written by a separate agent, are in `heldout-questions.md`. The folder's builders
never read that file or `key/` before the runs.

## The preamble every arm gets

Every prompt, in every arm, starts with this text, word for word. Then comes one question.

> You are answering an actuarial question about Indiana's dig-damage enforcement record: the Indiana
> Utility Regulatory Commission's orders approving the Underground Plant Protection Advisory Committee's
> recommendations under Indiana Code chapter 8-1-26, for the 58 orders dated 2021-01-01 through 2025-12-31.
> Definitions used in every question:
> - **Case:** one recommendation form in an order (one case number on one page).
> - **Year:** the year of the order's date, not the damage date, unless the question says otherwise.
> - **Cite:** the IC 8-1-26 citation under "finds the following violation(s)". Every case has exactly one.
>   **Base section:** the cite without "IC 8-1-26-" and without any parenthesized word. Example:
>   "IC 8-1-26-16(h)(expire)" has base section "16(h)" and qualifier "expire". A parenthesized word is
>   two or more letters (hyphens allowed); single letters or digits in parentheses, like (h) or (a)(2), are
>   part of the base section, so "20(a)(3)(b)" is its own base section, not "20(a)(2)".
> - **Headline penalty:** the first dollar amount in the committee's recommendation, read as printed but
>   ignoring a doubled "$" and any space after a thousands comma ("$$1000" is $1,000; "$3, 500" is $3,500).
>   A recommendation with no "$" amount has a headline penalty of $0.
> - **Utility respondent:** a case whose respondent name, ignoring case and leading spaces, starts with one of:
>   "CenterPoint", "Northern Indiana Public Service", "NIPSCO", "Citizens Gas", "Citizens Energy",
>   "Vectren", "Indiana American Water", "Ohio Valley Gas", "American Electric Power", "Duke Energy",
>   "Community Natural Gas", "Midwest Natural Gas", "Frontier Communications". Every other case is a
>   **non-utility respondent**.
> Give each number exactly as the question asks (rounding stated). If you cannot compute it from data you
> have, say so and give your best estimate, labelled as an estimate.

## How answers are scored

Each question has two or more required numbers. Per number: within tolerance = full, within the wider band
= half, otherwise zero. A question scores 2 (all numbers full), 1 (at least half the credit) or 0.
Percentages: full within ±0.5 points, half within ±2 points. Counts: full within ±1%, half within ±5%.
Dollar amounts: full if exact, half within ±10%. A named answer (a year, a company) must match exactly.
An answer labelled "estimate" is scored the same way: no credit for refusing, no penalty for saying so.

## Q1. Frequency: across all five years, what percentage of cases have base section 16(h), and what percentage have base section 20(a)(2)? Round to one decimal.

## Q2. Trend: how many cases are there in each year 2021, 2022, 2023, 2024 and 2025, and which year has the most?

## Q3. Severity by violation: among cases with a headline penalty above $0, what is the mean headline penalty for base section 16(h), and for base section 20(a)(2)? Round each to the nearest dollar.

## Q4. Warnings: what percentage of utility-respondent cases, and what percentage of non-utility-respondent cases, have a recommendation containing the words "warning letter" (any capitalization)? Round to one decimal.

## Q5. Training option: among cases with a headline penalty above $0, what percentage have a recommendation that contains the word "training" (any capitalization)? Round to one decimal.

## Q6. Repeat concentration: take non-utility-respondent cases only. Normalize each respondent name, in this order: lowercase; delete every character that is not a letter, a digit or a space (no replacement); collapse runs of spaces to one and trim; then, once, drop a final whole word if it is exactly "inc", "llc", "co", "corp", "corporation" or "company". How many distinct normalized respondents have 5 or more cases, and what percentage of non-utility-respondent cases do they account for? Round the percentage to one decimal.

## Q7. Expected cost per case: what is the mean headline penalty per case for non-utility-respondent cases in 2021, and in 2025? Include $0 cases. Round to the nearest dollar.

## Q8. Escalation: how many cases have a recommendation containing "ticket escalation" (any capitalization), and what is the most common headline penalty among those cases?

## Q9. Who gets hit: among non-utility-respondent cases, which "other party" name appears most often (exact text, ignoring case and surrounding spaces), and in what percentage of non-utility-respondent cases? Round to one decimal.

## Q10. Expired tickets: among cases with base section 16(h), what percentage have the qualifier "expire", and what percentage have the qualifier "prior"? Round to one decimal.

## Expected answers

Generated from `key/answers.json`, which `key/compute_answers.py` writes from `data/cases_clean.csv` (SHA-256 `5a1ddf901efe33b98818820e159f7940701d95a746acea4066a0ce9023a7dedc`, 9958 rows). An independent script written by a separate agent (`key/xcheck/answers.py`) agrees on every value; `python3 key/compare.py` checks that. The arms never see this section: their prompts are the preamble plus one question heading.

| Q | Expected |
|---|---|
| Q1 | pct_16h = 39.6; pct_20a2 = 22.9 |
| Q2 | cases_2021 = 1599; cases_2022 = 2671; cases_2023 = 2107; cases_2024 = 1897; cases_2025 = 1684; year_with_most = 2022 |
| Q3 | mean_16h = 4199; mean_20a2 = 3787 |
| Q4 | pct_utility_warning_letter = 0.0; pct_nonutility_warning_letter = 28.1 |
| Q5 | pct_training = 44.7 |
| Q6 | distinct_respondents_5plus = 187; pct_of_nonutility_cases = 24.3 |
| Q7 | mean_2021 = 2375; mean_2025 = 3041 |
| Q8 | count_ticket_escalation = 446; most_common_headline_penalty = 1500 |
| Q9 | most_common_other_party = northern indiana public service company; pct_of_nonutility_cases = 41.6 |
| Q10 | pct_expire = 12.3; pct_prior = 6.0 |

## Arms

Same model (Claude Sonnet 5.5), same preamble and questions, same tools (Read, Grep, Glob and a shell with
Python), each answer in a fresh sandboxed session that can see only its own arm's files. No web access.

- **control:** no files. The literal "no folder" run the brief asks for.
- **raw:** the state's 58 orders as published (PDF), plus their page text as extracted by `data/scripts/extract.py`,
  with no other help. The Marcelo-style control: same data, no map.
- **folder:** the folder (`folder/`), built after this file was committed.

## Predictions (written before any run)

| Arm | Predicted score, Q1–Q10 (of 20) | Why |
|---|---|---|
| control | 0–2 | It has no data. Any credit is a lucky estimate. |
| raw | 10–14 | Counting and amounts from page text are doable with Python. Most misses expected on Q6 (name normalization), Q9 (respondent vs other party), Q3/Q7 (parsing amounts, e.g. "$3, 500") and base-section grouping. Slow and token-heavy: it must parse ~10,000 pages first. |
| folder | 17–20 | The clean table, the definitions and the traps are written down. Expected loss, if any: the folder still has to apply the question's own definitions, which may differ from the folder's conveniences. |

Second prediction: the folder arm uses at least 3× fewer tokens than the raw arm per answer.
Third: on at least one question the raw arm ties the folder (most likely Q2, counting cases per year).
