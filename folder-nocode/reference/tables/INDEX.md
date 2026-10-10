# Table index: which table answers which question

Seven files, all generated from the cleaned case table by one script. Every table is Markdown; use Grep on a table id
(for example `Grep "### S7"`) to jump to it, then Read a window of the file. Do not read a whole file unless you need it
(`05` and `03` are the biggest).

## Legend used in every table

- **case** = one row = one recommendation form (PREAMBLE). **year** = ORDER year (the order date's year). A table says
  "damage year" when it is not.
- **base**: base section after the PREAMBLE rule (`16(h)`, `16(i)`, `18(h)`, `18(j)`, `19(c)`, `20(a)(1)`, `20(a)(2)`,
  `20(a)(3)(a)`, `20(a)(3)(b)`, and `(blank)` for the one row with no cite). **qual**: the qualifier word (`expire`, `prior`, `out`,
  `other`, `locator-error`, `records`, `no-response`); `-` means no qualifier. **cite** = base plus qualifier, for example `16(h)(expire)`.
- **resp**: `U` = utility respondent (PREAMBLE prefix list), `N` = non-utility respondent (everything else).
- **hl** = headline penalty in dollars (first `$` amount, doubled `$` and a space after a thousands comma tolerated; no `$` = 0).
  **pos** = cases with hl > 0; **zero** = cases with hl = 0; **sum** (or sum_hl) = total hl in dollars; **mean** = sum / n.
- **Outcome class** of the recommendation text (my grouping, from the wording): **W** warning letter (any "Special instructions");
  **TR5** "Training, or $5,000 if the respondent fails to train" (hl = 5000 although training avoids it); **TO** training only
  (hl 0); **PT** a dollar penalty the respondent may mitigate or replace by training (for example "$1,500, respondent can complete
  training instead of paying $1,500"); **F** a flat dollar penalty with no training wording; **X** none of those (no `$`, no
  warning, no training: 'Other', blank, a bare number). W, TR5, TO, PT, F, X add up to n.
- Percentiles are nearest-rank; the median of an even n is the average of the two middle values.
- Medians, percentiles and distinct-name counts CANNOT be added across rows. Counts, sums and histogram columns can.

## By kind of question

| Question is about | Table(s) | File |
|---|---|---|
| Total cases, orders, utility vs non-utility, data-quality counts, duplicates | Data-size block, A | 01 |
| Frequency by order year; cases per order; orders per year | A, D, D2 | 01 |
| Trend by quarter | E | 01 |
| Cases by base section and year (all, U only, N only) | B, B-U, B-N | 01 |
| Which section letters exist when (16(h) vs 16(i), 18(h) vs 18(j)) | B3 | 01 |
| Qualifier counts, qualifier by year, qualifier by base section | C, C2 | 01 |
| Damage year, seasonality (damage month), cases by damage year x base or resp | F1-F6 | 01 |
| Lags: damage to order, meeting to order; committee-meeting year | G, G2, G3, G4 | 01 |
| **Any count / sum / outcome mix for year x base x qualifier x resp** (recombine by hand) | the cube | 02 |
| Severity: mean, median, quartiles, p90, max, zero share, by year, base, qualifier, cite, resp and combinations | S0-S9 | 03 |
| Share of warnings / training / flat penalties; $ by outcome | O1-O6 | 03 |
| What the recommendation text actually says; warning-letter instructions | R, R2, R3 | 03 |
| Number of cases at or above a dollar threshold; any percentile or median for a custom cut | histograms H0-H7 (add the columns) | 04 |
| Repeat offenders: how many names have k+ cases, how concentrated | T1, T1b, T1c, T9 | 05 |
| Names present in several years / orders | T2, T2b | 05 |
| Effect of merging name spellings | T3, T3b | 05 |
| Does the 2nd / 3rd case of a name get a different penalty; share of cases that are repeats | T4, T4b, T4c | 05 |
| Time between repeat damages | T4d | 05 |
| Named lists: non-utility names with 4+ cases (T5), every utility name (T6), top by $ (T7), top names per year (T8, and non-utility only T8N), per section (T10) | T5-T8, T8N, T10 | 05 |
| Utility respondents by company: cases, years, sections, outcomes, severity | U1-U5 | 06 |
| Kinds of respondent (government, telecom, energy/water, contractor, other) by keyword | N-N5 | 06 |
| The other party (who was on the other side; utility other party) | P-P4 | 06 |
| Cities and places | L, L2, L3 | 07 |
| Abstentions, notes in additional_info, scan pages | M, M2, K, K2, K3 | 07 |

## How to pick

1. Count or total on year / section / qualifier / resp: sum cells of the cube (02), or read 01.
2. Mean = sum / n from the cube or from a stats table. Median, quartile or "share above $X": stats tables (03) when the cut is listed
   there; otherwise a histogram (04): walk the cumulative counts.
3. Names: file 05 (exact names). A "top" list is complete down to the stated cut; below it, say you cannot list them.
4. If no table has the cut, say so and give the closest labelled figure (see rules.md, section 4).
