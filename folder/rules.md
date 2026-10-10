# Rules: how to answer

`T` = `python3 reference/tools/cases.py` (run from the folder root).

## 1. Compute, never estimate
1. If the data can answer, run the tool. Do not recall, round in your head or extrapolate from a sample.
2. Do arithmetic in the tool (`count`, `group`, `stat`), not in prose. Copy numbers from its output.
3. Only if the data cannot answer: say so, then give a best estimate labelled "estimate" (the PREAMBLE asks for this).

## 2. Apply the question's definitions literally
- The PREAMBLE and the question define case, year, cite, base section, qualifier, headline penalty and utility
  respondent. The tool implements them (`T test-parse "<text>"` shows one string parsed). The question wins.
- Case = one row (one form page), so count rows. `reference/SCHEMA.md` suggests counting case 33669 once;
  the PREAMBLE's definition says one form is one case. Count rows, and note the alternative only if it changes the answer.
- Year = year of the order date (`--year`). A question about damage years needs `--eq damage_year=2022`.
- When wording allows two readings (inclusive or exclusive threshold, "per year" over all rows or only
  rows with a qualifier, "penalty" with or without escalations), take the literal one, run the other if
  cheap, and write one line: "Reading taken: ...; the other reading gives ...".
- Percentages always name their denominator: "n of N (x%)".

## 3. Show the computation
For every key number give, in this order: (a) the command, (b) the output line with numerator and
denominator, (c) the answer in a sentence, (d) receipts. Keep the command copy-pasteable from the folder root.

## 4. Receipts
For each key number add `--receipts 3` (or `T receipts ... --n 3`): the count plus 2-3 example rows, each as
`order_file, page, case_number`. For a group result, receipts for the top group are enough.

## 5. The traps (each with its check)
| Trap | What to do | Check |
|---|---|---|
| The respondent is not always the excavator. Under sections 18 the respondent is usually the utility or operator; under 16, 19, 20 usually the excavator. | Never write "utilities were cited for damaging lines". Say "cases with a utility respondent". Which party dug is not in the data. | `T group --by base,utility --sort key` |
| "Utility respondent" is a prefix test on the PREAMBLE's list of 13 names (`grep -n -A6 UTILITY_PREFIXES reference/tools/cases.py`), nothing more. Municipal and small operators (a town, a named gas corporation) are non-utility under the definition. | Use `--utility yes|no`; do not add companies by judgment. | `T receipts --base 18(h) --utility no --n 3` |
| Cites use the committee's labels. Qualifiers (expire, prior, out, records, locator-error, no-response, other) are not terms of the statute. | Report them as the orders print them; for meaning use `reference/glossary.md` and respect its evidence tags. A row with no qualifier is its own group. | `T group --by qualifier` |
| Subsection letters moved. The orders use 16(h) and 18(h) for older damages and 16(i) and 18(j) for 2025 damages; the 2025 law text appears to list the same duties under the later letters (inference; see glossary). | Group by base section as printed; add one line saying 16(h) and 16(i) (and 18(h) and 18(j)) may describe one duty under two lettering schemes. Merge only if asked. | `T group --by base,damage_year --sort key` |
| Headline penalty is the first `$` figure, whatever the condition. "Training or $5,000 if respondent fails to complete training" has headline 5,000 although training avoids it. Warning letters, training-only and text with no `$` have headline 0. Escalations ("additional $1,000") come after the first amount and are ignored. | Say "headline (as defined)" not "fine" or "paid". If the choice matters, also run with `--expr "'training' not in r['recommendation'].lower()"`. | `T count --rec-contains "Training or $5,000"` ; `T count --zero-penalty` |
| Odd amounts: `$$1000` and `$3, 500` parse to 1,000 and 3,500. `3000`, `0`, `.5000` have no `$`, so 0. | Leave as the definition says; mention only if the question's rows include them. | `T count --expr "re.fullmatch(r'[\d.]+', r['recommendation'])"` |
| Duplicates and bad rows: 2 case numbers repeat on two pages of the same order (4 rows); 23 case numbers appear in more than one order; one row has case number 0; one row has a blank cite. | Counting rows is the default. If a question says "distinct case numbers", use `T count --distinct-key case_number`. Use `--exclude-bad` when the question needs a clean cite. | `T dupes` ; `T receipts --eq case_number=0` ; `T receipts --blank violations` |
| Repeat offenders: names are free text; spelling variants are not merged (SCHEMA.md gives one example). A repeat count is a floor. Also, a respondent may be a person or an address (a mis-parsed row). | State "exact name after case and spacing normalisation". Show the top names with `--receipts 2` and list variants you see; never merge by guess. | `T repeat --utility no --min 5 --top 15` |
| Order years are batches. Orders are dated unevenly and the last order is 2025-12-10. A year count is cases approved that year, not damages that year. | Say "by order year". Do not call a year-to-year change a change in dig damage. For damage-year views use damage_date and note that early and late damage years are thin. | `T group --by year --sort key` ; `T group --by damage_year --sort key` |
| Scan pages (OCR and heuristic parsing) carry most field errors. | If a result depends on names or cites on scan pages, rerun with `--scan no` and say whether it changed. | `T count --scan yes` |
| The recommendation text is wording that varies for the same outcome (capital letters, added notes). | Classify with `--rec-contains` (case-insensitive) and check the distinct values first. | `T distinct --field recommendation --top 30` |

## 6. What the data cannot answer (say so, in one sentence, then give the nearest computable thing)
- Company size, number of digs or tickets, miles, trade or kind of work: so no rate per dig and no exposure base.
- Whether a penalty was paid, trained out, appealed or changed: only the recommendation exists. Two free-text notes mention
  payment (`T count --rec-contains paid`; `T count --contains additional_info=paid`: one row each); they are anecdotes, not a payment field.
- Which party is the excavator and which the utility; fault shares; claim cost, injuries or repair cost.
- Anything from order cover pages or non-form pages; any year before the 58 orders or after them.
- Statistical claims (significance, forecasts): give counts and shares; offer a labelled estimate only if asked.

## 7. Answer shape (also in `examples.md`)
Answer line first. Then: Reading taken. Command and output. Receipts. Caveats (at most 3, only those that apply).
Do not add advice, a model, or a recommendation the question did not ask for.
