# Indiana dig-damage enforcement desk

**Start here, in this order.** 1) `python3 reference/tools/cases.py fields` to see what you can filter and group on.
2) Answer with the tool (`count`, `group`, `stat`, `repeat`, `receipts`). Never `head`, `cat` or `grep` `reference/cases.csv`:
to see example rows, use `python3 reference/tools/cases.py receipts [filters]`. Read `rules.md` before you answer.

Ask an actuarial question about the Indiana Utility Regulatory Commission (IURC) orders that approve the
Underground Plant Protection Advisory Committee's penalty recommendations under IC 8-1-26. You get a number
you can recheck: the command that produced it, the numerator and denominator, and example case receipts.

The data is 9,958 recommendation forms (cases) from 58 IURC orders dated 2021-01-01 to 2025-12-31.
`reference/cases.csv` is the only data. Never open it whole: it is about 2 MB. Compute with the tool.
Check the counts: `T count` (9,958 rows), `T distinct --field order_file | head -1` (58 orders), `wc -c reference/cases.csv` (bytes).

## The tool (run from this folder's root)

`T` below means `python3 reference/tools/cases.py`.

    T count|group|stat|distinct|repeat|dupes|receipts|fields|test-parse  [filters]  [--by F] [--stat F] [--field F] [--receipts N] [--top N]

Filters: `--year --base --qual --cite --utility --penalty-min --penalty-max --zero-penalty --rec-contains
--respondent-contains --contains F=TEXT --eq F=V --blank F --notblank F --scan --order-file --exclude-bad --expr "..."`.
It loads the PREAMBLE definitions as code (base section, qualifier, headline penalty, utility respondent, order
year). Each run prints the filters, the kept rows and the total, so the denominator is always on screen.

    T group --by qualifier --base 18(h) --receipts 1      # rows per qualifier, one example each
    T fields                                              # every column and derived field you can group on

## Read order and token budget

| Step | Read | About |
|---|---|---|
| 1 | this README | 1.5k tokens |
| 2 | `rules.md` (how to answer, the traps) | 2.5k |
| 3 | `identity.md` only if unsure the question is in scope | 0.5k |
| 4 | `examples.md` once, to copy the answer shape | 2.5k |
| 5 | run the tool; cap each output with `--top 20` or `\| head -40` | 0.3k per run |
| 6 | only if the question needs it: `reference/glossary.md` (what a section or qualifier is) | 2.5k |

Never load `reference/cases.csv`, `reference/law/ic-8-1-26-2025.txt` (about 53k characters, roughly 13k tokens) or
`reference/SCHEMA.md` (about 16k characters, roughly 4k tokens) whole (`wc -c reference/SCHEMA.md reference/law/ic-8-1-26-2025.txt`). Use `grep -n` on them, then read the few lines around the hit.

## If a question needs X, go to Y

| The question asks about | Go to |
|---|---|
| a count, share, trend, group comparison | `T count` / `T group --by year,...` |
| mean, median, total, spread of penalties | `T stat --field headline` or `T group --by F --stat headline --pcts 25,75` |
| repeat offenders, "same respondent again" | `T repeat --by respondent_norm --min K` and the spelling caveat in `rules.md` |
| utility versus non-utility respondents | `--utility yes|no`; read the respondent trap in `rules.md` |
| what a section or qualifier means | `reference/glossary.md`, then `grep -n "Sec. 20" reference/law/ic-8-1-26-2025.txt` |
| a column's meaning or a known defect | `grep -n -A12 "^### recommendation" reference/SCHEMA.md` |
| duplicates, case 0, blank rows | `T dupes`, `T receipts --eq case_number=0` |
| something a filter cannot say | `T ... --expr "r['headline']>=3000 and r['year']==2023"` (`T fields` lists names) |
| company size, digs, trade, fines paid, who is the excavator | not in the data: say so (`rules.md`, "What the data cannot answer") |
| a test of the tool | `python3 reference/tools/test_cases.py` |

## What is where

    README.md  identity.md  rules.md  examples.md
    reference/cases.csv        the 14-column case table (unchanged copy of the cleaned file)
    reference/SCHEMA.md, schema.json   data dictionary and known defects
    reference/glossary.md      sections and qualifiers, with the evidence level of each statement
    reference/law/             IC 8-1-26 (2025 code year) as text
    reference/tools/           cases.py (helper and CLI), test_cases.py

The question's own definitions always win over this folder. If a question defines a term differently from the
PREAMBLE or from `rules.md`, follow the question and say so in one line.
