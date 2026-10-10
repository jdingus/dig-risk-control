# Held-out questions

> Disclosure: the orchestrating session saw these questions and their answers when this file was written. The agent that builds the folder never reads this file or `key/`, and nothing from them goes into its instructions.

Written by a separate agent (Claude Sonnet 5.5) from `data/cases_clean.csv`, `data/SCHEMA.md` and `data/README.md`
only, and from the preamble in `questions.md`, before any other folder file existed (the titles in `questions.md`
were looked at only to avoid their topics). The folder's builders never read this file or `key/heldout_answers.json`
before the runs. Answers are computed by `key/compute_heldout.py`; the SHA-256 of the exact `cases_clean.csv` used is
in `key/heldout_answers.json`.

Every prompt starts with "The preamble every arm gets" in `questions.md`, word for word, then one question below.
Terms used here but not in the preamble are defined inside the question.

Scoring is the same as `questions.md`. Each question has two or more required numbers. Per number: within tolerance =
full, within the wider band = half, otherwise zero. A question scores 2 (all numbers full), 1 (at least half the credit)
or 0. Percentages: full within ±0.5 points, half within ±2 points. Counts: full within ±1%, half within ±5%.
Dollar amounts: full if exact, half within ±10%. Days: full within ±1 day, half within ±5 days. A named answer (a city)
must match exactly, ignoring case. An answer labelled "estimate" is scored the same way.

## H1. Geography: define a case's **city** as the text after the last comma of its damage location, trimmed of spaces and lowercased, with spelling variants not merged; cases whose damage location has no comma or an empty city are left out of this question. Which city has the most cases, how many cases is that, and what percentage of the cases that have a city do the five most common cities together account for? Round the percentage to one decimal.

## H2. Reporting lag: for each case with a parseable damage date (month/day/year), define the **lag** as the number of calendar days from the damage date to the order date. Using the order's year (not the damage year), what is the mean lag in days for cases in 2023 and in 2024, each rounded to the nearest whole day, and what percentage of all such cases (all years) have a lag of more than 365 days? Round the percentage to one decimal.

## H3. Abstentions: a case has a **recorded abstention** if its Abstentions field has any text left after trimming spaces and deleting any stray words "Additional Infonnation:" or "Additional Information:" that leaked into it. What percentage of cases in each of 2021, 2024 and 2025 (by order year) have a recorded abstention? Round each to one decimal.

## H4. Qualifier outcomes: a case has qualifier "expire", "prior" or "out" if its cite ends with that word in parentheses, on any base section. Among cases with each of those three qualifiers separately, what percentage have a headline penalty of $0? Round each to one decimal.

## H5. 2023 to 2024 shift: (a) among non-utility respondent cases, what percentage have a headline penalty of at least $5,000 in 2023 and in 2024; and (b) what percentage of all cases are utility respondent cases in 2023 and in 2024? Denominators include $0 cases. Round each percentage to one decimal.

## Expected answers

Generated from `key/heldout_answers.json` (written by `key/compute_heldout.py`). The arms never see this section.

| H | Expected |
|---|---|
| H1 | top_city = indianapolis; top_city_cases = 1153; top5_combined_percent = 26.2 |
| H2 | mean_lag_days_2023 = 227; mean_lag_days_2024 = 188; percent_lag_over_365_all_years = 12.6 |
| H3 | percent_with_abstention_2021 = 41.4; percent_with_abstention_2024 = 54.0; percent_with_abstention_2025 = 49.8 |
| H4 | percent_zero_penalty_expire = 35.7; percent_zero_penalty_prior = 21.7; percent_zero_penalty_out = 18.3 |
| H5 | percent_nonutility_penalty_5000plus_2023 = 41.5; percent_nonutility_penalty_5000plus_2024 = 48.3; percent_utility_respondent_cases_2023 = 28.7; percent_utility_respondent_cases_2024 = 25.1 |
