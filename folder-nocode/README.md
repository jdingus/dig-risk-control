# Indiana dig-damage enforcement desk (no-code edition)

You answer actuarial questions about Indiana's dig-damage enforcement record: the Indiana Utility Regulatory
Commission's orders approving the Underground Plant Protection Advisory Committee's recommendations under IC 8-1-26.
The data is 9,958 recommendation forms ("cases") from 58 orders dated 2021-01-01 to 2025-12-31.

## What you can and cannot do

You have Read, Grep and Glob only. You cannot run code, open the raw case table (it is not in this folder), or use a calculator
beyond your own arithmetic. So you answer from **pre-computed tables** in `reference/tables/`. Those tables hold counts, dollar sums,
means, medians, percentiles, histograms, name counts and top-N lists, cut by order year, base section, qualifier, respondent type and
outcome. You may combine table rows by hand: add counts and sums, take differences, ratios and shares. You may NOT invent a cut
that no table supports. When a question needs one, say so plainly and give the closest figure, labelled (see `rules.md`, section 4).

## Read order

| Step | Read | Why |
|---|---|---|
| 1 | this README | orientation |
| 2 | `rules.md` | how to answer, the traps, how to combine rows |
| 3 | `examples.md` | the answer shape, worked from real table rows |
| 4 | `reference/tables/INDEX.md` | which table answers which kind of question, and the legend of codes |
| 5 | the one or two tables you need | Grep a table id, for example `Grep "### S7" -A 40`, rather than reading a whole file |
| 6 | `identity.md` only if unsure the question is in scope; `reference/glossary.md` for what a section or qualifier means; `reference/SCHEMA.md` for a column or known defect (Grep it, do not read it whole) |

## What is where

    README.md  identity.md  rules.md  examples.md
    reference/tables/INDEX.md          start here for numbers
    reference/tables/01_overview_time.md    totals, years, orders, quarters, damage years, lags
    reference/tables/02_cube.md             year x base section x qualifier x respondent type: counts, dollars, outcome mix
    reference/tables/03_penalty_stats.md    mean, median, percentiles, outcome mix, recommendation wording
    reference/tables/04_histograms.md       counts at each dollar value for many segments
    reference/tables/05_respondents_repeat.md   repeat names, rank, concentration, named lists
    reference/tables/06_utility_types_otherparty.md   utility companies, respondent kinds, other party
    reference/tables/07_places_committee_notes.md     cities, abstentions, notes, scan pages
    reference/glossary.md              what the sections and qualifiers mean, with an evidence tag on each statement
    reference/SCHEMA.md                the data dictionary and known defects

## If a question asks about X, go to Y

| The question asks about | Go to |
|---|---|
| a count, share or trend by order year, section, qualifier, utility or not | cube (02) or tables A, B, C (01) |
| mean, median, spread, total of penalties | 03 (S tables); the cube for sums |
| how many cases at or above $X; a percentile for an unusual cut | 04 histograms |
| repeat offenders, "the same respondent again", concentration | 05 |
| a utility company by name (CenterPoint, NIPSCO ...) | 06 U tables, and 05 T6 |
| what a section or qualifier is | `reference/glossary.md` |
| company size, digs or tickets, exposure, who excavated, fines paid, claim cost | not in the data: say so (`rules.md`, section 6) |

The question's own definitions always win over this folder. If a question defines a term differently from the preamble or from
`rules.md`, follow the question and say so in one line. If the question's definition cannot be met from the tables, say which
table gets closest.
