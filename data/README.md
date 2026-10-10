# data: IURC dig-law orders, parsed and checked

Source: 58 Indiana Utility Regulatory Commission (IURC) order PDFs (`originals/orders/`, one case per page after a cover page), plus the 2025 Indiana Code 8-1-26 PDF (`originals/law/ic-8-1-26-2025.pdf`). The fixes that are in code are listed under step 2. Every path below is relative to this `data/` folder, and the commands are run from the repo root.

## Files

| File | What it is |
|---|---|
| `originals/orders/*.pdf` | The 58 order PDFs, byte-for-byte copies. Never edited. |
| `originals/law/ic-8-1-26-2025.pdf` | Indiana Code 8-1-26 (2025 code year), byte-for-byte copy. Never edited. |
| `SOURCES.csv` | One row per original: path (relative to `data/`), source URL, fetch date (2026-10-10), bytes, sha256, order date from the filename, note on how it was captured. |
| `text/<order>.txt` | Raw pypdf text per order, `=== page N` before each page. No cleaning. |
| `cases.csv` | One row per case page (9,958 rows). Columns: order_file, order_date, page, case_number, respondent, other_party, advisory_meeting_date, damage_date, damage_location, violations, recommendation, abstentions, additional_info, scan. |
| `dropped.csv` | Blank Recommendation Form template pages that are not cases (5 rows), with a reason. |
| `corrections.csv` | The hand-correction ledger. Header only for now. Every change after parsing is a row here. |
| `cases_clean.csv` | `cases.csv` with every ledger row applied. Equal to `cases.csv` while the ledger is empty. |
| `VERIFY.md` | Output of the checks in step 4. |
| `scripts/extract.py` | Step 1: writes text/. |
| `scripts/parse.py` | Step 2: writes cases.csv and dropped.csv. |
| `scripts/apply_corrections.py` | Step 3: writes cases_clean.csv from cases.csv and corrections.csv. |
| `scripts/verify.py` | Step 4: writes VERIFY.md and exits 1 if a check fails. |

Each script finds the `data/` folder from its own location, so no script takes a path argument.

`SOURCES.csv` was first written by a helper that read the download folder of the original capture. That helper is not in this repo; `SOURCES.csv` is copied, and its sha256 and byte values are checked in step 4.

## Step order and re-run

Run from the repo root. Python runs with `-I`. The PDFs are data: nothing in them is executed.

0. Originals and SOURCES.csv: copied byte-for-byte from the round2 capture. Check: `verify.py` (step 4) recomputes every sha256 and size against SOURCES.csv.
1. Text: `uv run -q --with pypdf --with pymupdf python -I data/scripts/extract.py`
2. Parse: `uv run -q --with pypdf --with pymupdf python -I data/scripts/parse.py`
3. Corrections: `uv run -q --with pypdf --with pymupdf python -I data/scripts/apply_corrections.py`
4. Verify: `uv run -q --with pypdf --with pymupdf python -I data/scripts/verify.py`

## Step 2 rules (in code)

- Violation cites are taken from the block after the "violation(s):" heading and before the recommendation. Each cite is kept as printed, including qualifiers such as `(locator-error)`, `(no-response)`, `(expire)`, `(prior)`, `(records)`, `(out)`, and joined with `; `. OCR forms such as `8-l-26` and `(a)(l)` are kept as printed.
- Wrapped respondent, other_party and damage_location values are joined to the line after the label. Joins: respondent 57, other_party 33, damage_location 50. An earlier audit counted 56 for damage_location; no blank-line gaps were found, so the difference is not explained yet.
- Label-first scan pages (values printed after all the labels) are assigned by value type: case number, then dates, then names and location in order. This is a heuristic; the scan rows should be checked by hand.
- Dates: when a date is printed, the date is kept. Otherwise the printed value is kept (for example `12:00:00 AM`).
- A field whose printed value has no word characters (such as a bare comma on a blank form) is left empty.
- Blank template pages (no case number, parties, dates, location or violation) go to dropped.csv, not cases.csv.
- scan = yes when one embedded image covers more than 60 percent of the page (PyMuPDF).
- Nothing else is normalised: case numbers, spacing, and OCR errors are kept as printed.

## Rule

The originals are never edited. Every change after parsing is a row in `corrections.csv` (order_file, page, case_number, field, old_value, new_value, evidence, checked_by). `apply_corrections.py` stops if a row's old_value does not match the current value.
