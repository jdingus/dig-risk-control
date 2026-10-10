# Worked examples

These questions are invented for this folder. Every figure was read from the tables in `reference/tables/` and combined by hand as
shown (and re-checked against the raw data when the tables were built). Do not reuse their numbers for other questions. Copy the shape:
answer line, reading taken, where from, arithmetic, caveats.

## Example 1: add cube rows for a count, a dollar total, a mean and a share

**Question.** In the 2023 orders, for non-utility respondents cited under base section 16(h), how many cases were there, what was the
mean headline penalty, and what share were warning letters?

**Where from.** `02_cube.md`, the five N rows with year 2023 and base 16(h) (found with `Grep "^\| 2023 \| 16\(h\) \|"`):

| qual | n | sum | W |
|---|---|---|---|
| - | 624 | 1688000 | 230 |
| expire | 111 | 265500 | 35 |
| prior | 37 | 81500 | 13 |
| out | 34 | 107500 | 4 |
| other | 2 | 5000 | 1 |

**Arithmetic.** n: 624 + 111 + 37 + 34 + 2 = 808. Sum: 1,688,000 + 265,500 + 81,500 + 107,500 + 5,000 = 2,147,500. Mean = 2,147,500 / 808
= 2,657.8. Warning letters: 230 + 35 + 13 + 4 + 1 = 283; 283 of 808 = 35.0%.

**Answer.** 808 cases; mean headline $2,657.8; 283 of 808 (35.0%) were warning letters (headline $0).

**Caveats.** (1) Headline is the first dollar figure as defined; many 16(h) texts read "Training, or $5,000 if respondent fails to
complete training", whose headline is $5,000 although training avoids it. (2) The 2023 U rows for 16(h) (3 cases) are excluded by the question.

## Example 2: merge two lettered sections and take a share

**Question.** In the 2025 orders, what share of the operator-duty cases (base sections 18(h) and 18(j)) had a utility respondent?

**Reading taken.** The question names both sections, so they are added. Where a question names only one, report that one alone.

**Where from.** `02_cube.md`, all 2025 rows with base 18(h) or 18(j). U rows: 2 + 161 + 60 + 11 (18(h)) and 133 + 53 + 16 (18(j)). N rows:
2 + 1 + 2 (18(h)) and 2 + 1 + 1 (18(j)).

**Arithmetic.** U = 2 + 161 + 60 + 11 + 133 + 53 + 16 = 436. N = 2 + 1 + 2 + 2 + 1 + 1 = 9. Total 445. Share = 436 / 445 = 98.0%.

**Answer.** 436 of 445 cases (98.0%) had a utility respondent. Each of the 436 carries a $1,000 headline (U sum 436,000).

**Caveats.** The 9 non-utility respondents are names that do not start with one of the 13 listed prefixes; they are not necessarily excavators.

## Example 3: a threshold count and a median from a histogram

**Question.** Among non-utility cases in the 2024 orders, how many had a headline penalty of at least $4,000, and what was the median
headline?

**Where from.** `04_histograms.md`, row H4 "2024 | N": n = 1421; counts by value: $0 275, $500 3, $1000 7, $1500 255, $3000 88,
$3500 51, $4000 32, $4500 23, $5000 687 (all other columns '.').

**Arithmetic.** At least $4,000: 32 + 23 + 687 = 742; 742 of 1,421 = 52.2%. Median: n is odd, so the middle case is number
(1421 + 1) / 2 = 711. Cumulative counts: 275 ($0), 278 ($500), 285 ($1000), 540 ($1500), 628 ($3000), 679 ($3500), 711 ($4000). The 711th case
is at $4,000, so the median is $4,000. Cross-check: table A3 in `01_overview_time.md`, row 2024 N, lists median 4000.

**Answer.** 742 of 1,421 (52.2%) had a headline of at least $4,000 (inclusive); the median headline is $4,000.

**Caveats.** "At least" is inclusive. Of the 687 cases at $5,000, 518 have the "Training, or $5,000 if respondent fails to complete
training" wording (class TR5 in `03_penalty_stats.md`, O4, row 2024 N), which the headline rule counts as $5,000 although training avoids it.

## Example 4: repeat offenders with a name-spelling caveat

**Question.** Among non-utility respondents, how many names appear in 10 or more cases, and what share of non-utility cases do they cover?

**Where from.** `05_respondents_repeat.md`, T1, row k = 10, column N: "47 / 858" (47 names, 858 cases). Non-utility cases in all:
7,243 (`01_overview_time.md`, year summary, N column, "all" row). Sensitivity: T3, row 10, column N: "49 / 888".

**Arithmetic.** 858 / 7,243 = 11.8%. With obvious spelling variants merged (T3): 888 / 7,243 = 12.3%.

**Answer.** 47 names (exact name after case and spacing normalisation) have 10 or more cases; together 858 of the 7,243 non-utility
cases (11.8%). Merging variants that differ only in punctuation or a corporate suffix gives 49 names and 888 cases (12.3%).

**Caveats.** (1) Counts are floors: other spelling variants are not merged. (2) The names are listed in T5 (non-utility names with 4 or
more cases, most first), with cases by order year. (3) These are cases, not digs: there is no exposure measure in the data.

## Example 5: a trend, with a mix check

**Question.** How did the mean headline penalty change from the 2023 to the 2024 orders, and what happened to the share of cases that
carry a qualifier?

**Where from.** `01_overview_time.md`: A2 (means 2,322.7 for 2023 and 2,652.9 for 2024) and the year summary table A (cases with a
qualifier: 2021 120 of 1,599; 2022 269 of 2,671; 2023 201 of 2,107; 2024 656 of 1,897; 2025 656 of 1,684).

**Arithmetic.** Difference: 2,652.9 - 2,322.7 = 330.2. Ratio: 2,652.9 / 2,322.7 = 1.142 (+14.2%). Qualifier shares: 120/1599 = 7.5%,
269/2671 = 10.1%, 201/2107 = 9.5%, 656/1897 = 34.6%, 656/1684 = 39.0%.

**Answer.** The mean headline per case rose by $330.2 (14.2%), from $2,322.7 to $2,652.9, by order year. The share of cases with a
qualifier jumped from 9.5% (2023) to 34.6% (2024) and 39.0% (2025).

**Caveats.** (1) This is by order year, which reflects when orders were approved, not when damage happened. (2) Part of any change in the mean is
mix: warning letters (headline $0) were 415 of 2,107 cases (19.7%) in 2023 and 274 of 1,897 (14.4%) in 2024 (outcome table O1 in
`03_penalty_stats.md`), which raises the mean. Say the mean is
for all cases including zeros; the "median_of_positive" column in A2 gives severity among penalised cases only.

## Example 6: a cut no table covers (closest figure and a labelled estimate)

**Question.** How many cases with a damage date in 2022 carry the qualifier (expire)?

**First sentence.** No table has damage year x qualifier, so this exact figure is not available.

**Closest available (labelled).** By ORDER year, the 2022 orders contain 157 (expire) cases (`01_overview_time.md`, table C). That is a
different cut: it counts when the order was approved.

**Estimate (labelled).** Table F1 shows where the 2,015 damage-2022 cases were approved: 748 in the 2022 orders and 1,267 in the 2023 orders.
Table C gives (expire) cases by order year (2022: 157 of 2,671 = 5.9%; 2023: 112 of 2,107 = 5.3%). Weight by those shares:
748 x 0.059 + 1,267 x 0.053 = 44.1 + 67.2 = about 111. **Estimate: about 111 cases**, assuming (expire) is spread evenly across the cases of
each order, which the data cannot confirm.

**Caveats.** The estimate rests on that even-spread assumption. Do not present 157 or 111 as the exact count.

## Example 7: a question the data cannot answer

**Question.** What share of penalties recommended against utility respondents were actually paid?

**Answer.** It cannot be computed from this folder: there is no payment, appeal or outcome field (`reference/SCHEMA.md`, "What is NOT in the
data"). The nearest figure is the denominator a payment rate would need: 2,714 of the 2,715 utility-respondent cases have a positive
headline penalty (`06_utility_types_otherparty.md`, table U1, row "ALL utility", columns cases and pos). The numerator does not exist.

**Caveats.** Any share given would be an estimate; if you give one, label it "estimate, not from this data" and say what it rests on.
