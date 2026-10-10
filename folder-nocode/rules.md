# Rules: how to answer

You have Read, Grep and Glob only. All numbers come from `reference/tables/`. Legend and table finder: `reference/tables/INDEX.md`.

## 1. Look up, then combine; never guess
1. Find the table that holds the figure (INDEX.md). Use Grep to jump: for a table id, `Grep "### S7"` with context lines (`-A 30`);
   for a cube row, `Grep` a pattern such as `^\| 2023 \| 16\(h\) \|` in `02_cube.md` (escape the parentheses).
   Read only the window you need.
2. If one table row is the answer, copy it. If the answer is a sum, difference, ratio or share of rows, do the arithmetic by hand
   (section 3) and show the pieces.
3. Do not recall, round in your head or extrapolate from a sample. If no table supports the cut, follow section 4.
4. Counts, dollar sums and histogram columns can be added across rows. **Medians, percentiles, means (use sum / n instead), shares,
   and distinct-name counts cannot be added or averaged across rows.** A mean of a union = (sum of the sums) / (sum of the ns).
   A median of a union needs a histogram (04): add the histogram counts, then walk the cumulative counts to the middle position.

## 2. Apply the question's definitions literally
- The PREAMBLE and the question define case, year, cite, base section, qualifier, headline penalty and utility respondent. The tables
  were built from exactly those definitions. The question wins over this folder; if it differs, say so in one line.
- Case = one row (one form page), so counts are rows. Two case numbers are repeated on two pages of one order each (the data-size block
  in `01_overview_time.md` lists them); if a question says "distinct case numbers", use the distinct counts in table A and say so.
- Year = ORDER year. A question about damage year needs tables F1-F6 (01); they are thinner (only some cuts exist).
- When wording allows two readings (inclusive or exclusive threshold, "penalty" with or without escalation or training wording,
  per-year over all rows or only qualified rows), take the literal one, give the other if a table makes it cheap, and write one line:
  "Reading taken: ...; the other reading gives ...".
- Percentages always name their denominator: "n of N (x%)".

## 3. Doing arithmetic without a tool
- Write every cell you use with its table id and row label, then the sum. Example: "2023 16(h) N: 624 + 111 + 37 + 34 + 2 = 808".
- Add in small groups and check each subtotal. Do each calculation twice. Where a second route exists, use it: N + U must equal the
  all-respondent row; year cells must add to the 'all' column; outcome counts (W + TR5 + TO + PT + F + X) must add to n. A mismatch
  means a misread cell: find it before answering.
- Round only at the end, as the question says; otherwise one decimal for percentages and for dollar means.
- Shares: say numerator and denominator, then the share. Differences between two means use the printed means; say the figures
  are from the tables.
- If a calculation needs more than about twenty cells, look for a table that already holds the total (the year, base-section and
  respondent-type tables 01/03/06 hold many pre-summed cuts) before adding by hand.

## 4. When no table covers the cut
Say so in the first sentence ("No table has damage year x qualifier"), then give, in this order, whichever applies:
1. **Exact by hand**: the cut is a union of cells you can add (the cube is year x base x qualifier x resp). Do that.
2. **Closest table figure**, labelled "closest available, not the cut asked": the nearest cut, and what differs (for example order year
   instead of damage year, all respondents instead of non-utility, all qualifiers instead of one).
3. **Labelled estimate**, only if useful and only if you can show a method from table figures (for example weighting by shares). Write
   "estimate" next to the number and state the method in one line. The PREAMBLE asks for this label.
Never present a closest figure or an estimate as the exact answer. Do not reach for the raw data; you do not have it.

## 5. The traps (each with where to check)
| Trap | What to do | Check in |
|---|---|---|
| The respondent is not always the excavator. Under sections 18 (operator duties) the respondent is usually the utility or operator; under 16, 19 and 20 usually the excavator. | Never write "utilities were cited for damaging lines". Say "cases with a utility respondent". Which party dug is not in the data. | 01 B-U, B-N; 03 S6; 06 P |
| "Utility respondent" is a prefix test on the PREAMBLE's list of 13 names, nothing more. A town, a municipal gas system, a gas corporation not on the list, a telecom contractor are non-utility under the definition. | Use the U/N split as built. Do not move companies by judgment. The keyword types in 06 (N-N5) are a rough heuristic, not the definition. | 06 U1; N5 |
| Cites use the committee's labels. Qualifiers are not terms of the statute. | Report them as printed; for meaning use `reference/glossary.md` and respect its evidence tags. A row with no qualifier ('-') is its own group. | 01 C, C2 |
| Subsection letters moved: 16(h) and 18(h) for damages to 2024, 16(i) and 18(j) for damages in 2025 (plus one 18(j) markings case with a 2021 damage date). The same duty appears to sit under both lettering schemes. | Group by base section as printed; add one line saying 16(h) and 16(i) (and 18(h) and 18(j)) may be one duty under two letters. Merge only if asked or if a trend would otherwise mislead (a "16(h) fell in 2025" reading is mostly the letter change). | 01 B3, B |
| The headline penalty is the first `$` figure, whatever the condition. "Training or $5,000 if respondent fails to complete training" has headline $5,000 although training avoids it. Warning letters, training-only and text with no `$` have headline 0. Escalations ("additional $1,000") come after the first amount and are ignored. | Say "headline (as defined)", not "fine" or "paid". If the choice matters, use `sum_notrain` in the cube (headline only for texts that do not mention training), or the outcome tables O1-O6. | 02 columns sum, sum_notrain; 03 O |
| Odd amounts: `$$1000` reads as $1,000 and `$3, 500` as $3,500 (the PREAMBLE says so). A bare number with no `$` ('3000', '0', '.5000') has headline 0. | Leave as the definition says. Mention only if the question's rows include them. | 03 R, class X |
| Duplicates and bad rows: two case numbers repeat on two pages of one order each; some case numbers appear in more than one order; one row has case number 0; one row has a blank cite (base '(blank)'). | Count rows by default. A question about "distinct case numbers" uses the distinct counts in table A. Mention the blank-cite row only when a base-section total would otherwise look short by one. | 01 data-size block, A |
| Repeat names are free text; spelling variants are not merged, so every repeat count is a floor. A respondent may also be a person or an address. | Say "exact name after case and spacing normalisation". Give the loose-name sensitivity (T3) when the answer depends on a threshold. Never merge by guess. | 05 T1, T3, T3b |
| A "top" list is complete only down to its stated cut (T5: non-utility names with 4+ cases; T6: all utility names; T8, T8N: top 12 per year; T10: top 8 per section). | For "names with k or more", if k is at or above the cut, list from the table; if below, give the count from T1/T1b and say the names are not listed. | 05 headers |
| Order years are batches. Orders are dated unevenly (orders per year and cases per order vary) and the last order is dated 2025-12-10. A year count is cases approved that year, not damages that year. | Say "by order year". Do not call a year-to-year change a change in dig damage. For damage-year views use table F and note that early and late damage years are thin. | 01 A, D, D2, F1 |
| A big share of the movement across years is mix: the qualified cites and the 16(i)/18(j) letters appear mostly in later orders. | When asked about a trend in severity or counts, also look at the base-section or qualifier split before explaining it. | 01 B, C; 03 S5 |
| Scan pages (OCR) carry most field errors, and they are concentrated in one 2021 order. | If a result depends on names or cites and scan rows matter, say the scan share (07 K2). | 07 K2, K3 |
| Recommendation wording varies for the same outcome (capitals, added notes). | The tables already group them into outcome classes W, TR5, TO, PT, F, X (definitions in INDEX.md); use those, and table R to see the raw wording. | 03 R |

## 6. What the data cannot answer
Say so in one sentence, then give the nearest computable thing from the tables.
- Company size, number of digs or tickets, miles, trade or kind of work: no exposure base, so no rate per dig. Counts per year and per order
  are the nearest frequency measure.
- Whether a penalty was paid, trained out, appealed or changed: only the recommendation exists. Cases with a positive headline (01 data-size block)
  are the denominator a payment rate would need; the numerator does not exist.
- Which party is the excavator and which the utility; fault shares; claim cost, injuries or repair cost.
- Anything from order cover pages or non-form pages; any year before the 58 orders or after them.
- Statistical claims (significance, forecasts): give counts and shares, and offer a labelled estimate only if asked.

## 7. Answer shape (also in `examples.md`)
1. Answer line first, with the number(s) and denominator.
2. Reading taken (one line, only if it matters).
3. Where from: table ids and the rows used, then the arithmetic.
4. Caveats (at most three, only those that apply); say clearly if any part is closest-available or an estimate.
Do not add advice, a model, or a recommendation the question did not ask for.
