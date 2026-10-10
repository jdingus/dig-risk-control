# SCHEMA: data dictionary for cases.csv and cases_clean.csv

Both files have the same 14 columns in the same order. `cases.csv` is the raw parse. `cases_clean.csv` is `cases.csv` with every row of `corrections.csv` applied (see README.md). The machine-readable form of this page is `schema.json`; `scripts/verify.py` checks `cases_clean.csv` against it and reports the result in `VERIFY.md`.

Counts below are for the raw parse (`cases.csv`) unless a line says otherwise. Defects that the corrections ledger fixes are marked "ledger"; `cases_clean.csv` has them fixed (see the last section). "Page image" means the page rendered from the original PDF and looked at.

## What a case is

One row is one **recommendation form page**: one page of an order PDF that carries the Indiana Underground Plant Protection Advisory Committee "Recommendation to IURC" form. There are 9,958 rows from 58 order PDFs. The cover page and any other page of an order are not rows. Five blank copies of the form are in `dropped.csv`, not in the data.

A row is not one unique case number. 23 case numbers appear in more than one order (46 rows). Two `(order_file, case_number)` pairs appear on two pages of the same order each (4 rows); see `case_number`. The key that is always unique is `(order_file, page)`.

## What is NOT in the data

- Company size (of either party).
- The number of digs or tickets behind a case.
- The trade or kind of work of the respondent (the data has a name only).
- Whether a recommended penalty was paid, trained out, appealed or changed later.
- Which party is the utility and which is the excavator. Either name can appear in either of `respondent` and `other_party`.
- Anything from the cover page or other non-form pages of an order.

## The violation qualifiers seen

A qualifier is a word in parentheses printed after a cite, for example `IC 8-1-26-16(h)(expire)`. Letter or number marks such as `(h)`, `(a)(2)` and `(3)(b)` are part of the section and are not qualifiers. 1,902 cites carry a qualifier. Seven different qualifiers occur:

| qualifier | cites |
|---|---|
| (locator-error) | 600 |
| (expire) | 518 |
| (prior) | 272 |
| (records) | 249 |
| (out) | 191 |
| (no-response) | 52 |
| (other) | 20 |

This page does not say what the qualifiers or cites mean in law. That belongs in the questions step.

## Columns

### order_file
- **Meaning:** the order PDF the page is in.
- **On the page:** not on the page. It is the file name of the PDF.
- **Type and format:** string, matches `ord_PSD_MMDDYY.pdf` (also `ord_PSD_MM.DD.YY.pdf` for one file and `ord_PSDNPT_MMDDYY.pdf` for one file).
- **Allowed:** the 58 file names in `originals/orders/`. Never blank.
- **parse.py:** the name of the text file in `text/`, with `.pdf` in place of `.txt`.
- **Known defects:** none.
- **Treat as:** an identifier. `ord_PSDNPT_040622.pdf` (1 row) and `ord_PSD_040622.pdf` are two files with the same order date.

### order_date
- **Meaning:** the date of the order the page is in.
- **On the page:** not on the page. It is read from the file name.
- **Type and format:** date, ISO `YYYY-MM-DD`. Never blank.
- **Allowed:** 57 distinct values, 2021-02-03 to 2025-12-10.
- **parse.py:** `real_date()`: month, day and year from the six digits in the file name, year read as 20YY.
- **Known defects:** none seen. The date is only as right as the file name.
- **Treat as:** the order date, not the date of the damage or of the committee meeting.

### page
- **Meaning:** the page of the order PDF the form is on. The cover page is page 1.
- **On the page:** not printed. It is the position in the PDF.
- **Type and format:** int, 2 to 346.
- **Allowed:** a positive whole number. Never blank.
- **parse.py:** the number in the `=== page N` marker in `text/`.
- **Known defects:** none.
- **Treat as:** with `order_file`, the unique key of a row. Use it to find the page for a check.

### case_number
- **Meaning:** the case number printed on the form.
- **On the page:** `Case Number:`
- **Type and format:** string of 5 digits.
- **Allowed:** `\d{5}`. Never blank in the data.
- **parse.py:** the text after `Case Number:`; on scan pages that print the values after all the labels, the one bare 3 to 7 digit line.
- **Known defects:**
  - 1 row holds `0` (ord_PSD_020321.pdf page 27). Its text layer reads `Case Number: 0`, `Respondent: 130 2nd St NE`, `Damage Location: Internattional Inc., Indianapolis` and a recommendation of `.5000`. The form looks filled in with values in the wrong boxes. Not corrected: the case number is not known from the page text, and the page image was not part of the ledger job. Treat the row as unusable for case-level counts.
  - 2 duplicate `(order_file, case_number)` pairs, 4 rows. Both were checked on the page image (ledger job):
    - ord_PSD_051822.pdf pages 7 and 346, case 25064: two real forms with the same parties, dates and location and a different cite (`IC 8-1-26-16(h)` and `IC 8-1-26-20(a)(2)`), both with a recommendation of `$10,000`. Abstentions read `Smith` and `Rick Smith`. Kept as two rows.
    - ord_PSD_101525.pdf pages 245 and 246, case 33669: two pages that are identical on the image. Kept as two rows; a reader who counts cases should count them once.
- **Treat as:** an identifier, not a number. Do not count distinct values as distinct cases without reading the duplicate note above.

### respondent
- **Meaning:** the first named party of the form.
- **On the page:** `Respondent:`
- **Type and format:** string, free text, as printed.
- **Allowed:** any text. Blank in 1 row.
- **parse.py:** the text after the label, with a wrapped second line joined by a space (57 rows). Label-first scan pages are assigned by the type of value, which is a heuristic.
- **Known defects:**
  - 2 rows hold form text from the neighbouring label: `Date nf Advisory Meeting: One House At A Time` (ord_PSD_110321.pdf page 124) and `Date of Dam.age: Dam.age Location: Wickey Construction` (page 168). Both are scan pages. Not corrected (outside the ledger job).
  - Spelling variants of one company are not merged. `Internattional Inc.` appears in 16 rows in this column and 7 in `other_party`. Spelling on the page was not checked.
  - 62 rows have the same text in `respondent` and `other_party`.
- **Treat as:** a name for display, not a join key. Clean it before grouping companies.

### other_party
- **Meaning:** the second named party of the form.
- **On the page:** `Other Party:`
- **Type and format:** string, free text, as printed.
- **Allowed:** any text. Blank in 27 rows.
- **parse.py:** as `respondent`; 33 wrapped values joined.
- **Known defects:** 1 row holds the violation heading text (ord_PSD_110321.pdf page 106, a scan page), and its `respondent` holds both names and an address. Not corrected (outside the ledger job).
- **Treat as:** as `respondent`. Blank means nothing was printed or parsed.

### advisory_meeting_date
- **Meaning:** the date of the advisory meeting.
- **On the page:** `Date of Advisory Meeting:`
- **Type and format:** date as printed, month/day/year with no leading zero in all but one row, for example `3/17/2022`.
- **Allowed:** `\d{1,2}/\d{1,2}/\d{4}`, 2019-01-15 to 2025-10-15. 63 distinct values. Blank in 1 row.
- **parse.py:** the date in the text after the label. If no date is printed the printed text is kept.
- **Known defects:** 1 row holds `12:00:00 AM` (ord_PSD_020321.pdf page 27, the case `0` row above). 1 row is blank (ord_PSD_022322.pdf page 129, a form with almost nothing filled in; page image checked, the field is empty on the page).
- **Treat as:** a text date. Parse it with `%m/%d/%Y` and treat the two defects as missing.

### damage_date
- **Meaning:** the date the damage happened.
- **On the page:** `Date of Damage:`
- **Type and format:** date as printed, month/day/year, for example `6/9/2021`.
- **Allowed:** `\d{1,2}/\d{1,2}/\d{4}`, 2018-03-17 to 2025-08-22. By year: 2018 4, 2019 36, 2020 1,630, 2021 1,858, 2022 2,015, 2023 1,970, 2024 1,813, 2025 631. Blank in 1 row.
- **parse.py:** as `advisory_meeting_date`.
- **Known defects:** the one blank row is the same ord_PSD_022322.pdf page 129 (empty on the page image).
- **Treat as:** the damage date. The 40 rows before 2020 are real dates on the page (8 of them are the checkbox-form pages of ord_PSD_042121.pdf, checked on image).

### damage_location
- **Meaning:** the street address and city of the damage.
- **On the page:** `Damage Location:`
- **Type and format:** string, `street, city`.
- **Allowed:** any text with a comma followed by a city. Blank in 9 rows.
- **parse.py:** the text after the label; a wrapped second line joined by a space (50 rows). The printed value is kept: no case change, no abbreviation fix.
- **Known defects:** 4 rows have no city: `3846 Schneider Street` (ord_PSD_101525.pdf pages 245 and 246, no city printed on the page image), `7401 ##` (ord_PSD_100924.pdf page 37) and `IC 8-1-26-16(h)` (ord_PSD_110321.pdf page 106, a scan page). The two last values were not corrected (outside the ledger job).
- **Treat as:** free text. The city is the text after the last comma when there is one. Spelling and abbreviation vary.

### violations
- **Meaning:** the cite(s) the Pipeline Safety Division found, as printed.
- **On the page:** the line after `The IURC Pipeline Safety Division finds the following violation(s):`
- **Type and format:** string, one or more cites joined by `; `. Every row has exactly one cite or none; no row has two.
- **Allowed:** `IC 8-1-26-<section>` with a section of `16(h)`, `16(i)`, `18(h)`, `18(j)`, `19(c)`, `20(a)(1)`, `20(a)(2)`, `20(a)(3)(a)` or `20(a)(3)(b)`, optionally followed by one of the seven qualifiers above. Blank in 1 row.
- **parse.py:** the cites in the block between the `violation(s):` heading and `recommends`. Qualifiers are kept. OCR errors are kept as printed.
- **Known defects:**
  - 16 rows have a cite the OCR misread (all scan pages), for example `IC 8-1-26-lS(h)`, `IC 8-l-26-16(h)`, `IC 8-1-26-20(a)(l)`, `IC8-l-26-16(h)` and `IC 8-1-26-16(b)` (two rows, page image shows `16(h)`). Ledger.
  - 1 row is blank (ord_PSD_022322.pdf page 129): the page image shows the violation line empty on the page. Not a parse error; left blank.
  - Scan rows whose cite is a valid-looking string were not each checked against the page image; only strings that failed the pattern or were rare were.
- **Treat as:** a code string. Split the base section from the qualifier before grouping, and keep rows with no qualifier separate from rows with one.

### recommendation
- **Meaning:** the penalty the committee recommended, as printed.
- **On the page:** the text after `The Advisory Committee recommends the following penalty:` (or `civil penalty:`) up to `Abstentions:`.
- **Type and format:** string, free text. 133 distinct raw values. Wording varies for the same outcome (`Warning letter` 1,386 rows and `Warning Letter` 135 rows; `$1,500, respondent can complete training instead of paying $1,500` and longer versions with extra text).
- **Allowed:** any text. Blank in 2 rows (ord_PSD_022322.pdf page 196 and ord_PSD_110321.pdf page 168; neither was looked at on the page image).
- **parse.py:** the text between the heading and `Abstentions`, spaces collapsed, nothing else changed.
- **Known defects:**
  - 8 rows are the checkbox form (ord_PSD_042121.pdf pages 149 to 156): the text layer holds every option with its box glyph, not the ticked option. Ledger: the ticked option from the page image, worded as printed on the form. Seven are `Training or $5,000 civil penalty if fail to complete training` (this form wording differs from the typed-form wording `Training or $5,000 if respondent fails to complete training` used elsewhere); one is `Civil penalty of $1,500; can mitigate $1,500 by completing training`.
  - 7 rows read `$$1000` (ord_PSD_060822.pdf pages 85 to 88 and 90 to 92). Page image checked: the doubled dollar sign and the missing comma are printed on the page. Not corrected.
  - 1 row reads `$3, 500; no ticket escalation - additional $1,000 ($4,500)` (ord_PSD_122821.pdf page 4). Page image checked: the space after the comma is printed on the page. A parser that reads the first amount gets 3. Not corrected.
  - 3 rows have an amount without a dollar sign: `.5000` (the case `0` row), `3000` (ord_PSD_060822.pdf page 290) and `0` (ord_PSD_080322.pdf page 222). Not corrected (outside the ledger job).
- **Treat as:** text to classify, not a number. Read dollar amounts with a rule that tolerates the printed oddities above, and handle the checkbox pages from the corrected value.

### abstentions
- **Meaning:** the surname(s) printed after `Abstentions:`, one per member who abstained.
- **On the page:** `Abstentions:`
- **Type and format:** string, free text.
- **Allowed:** any text. Blank in 5,035 rows (nothing printed). 15 distinct values; `Smith` 3,824 and `Warren` 1,033 are the most common.
- **parse.py:** the text between `Abstentions:` and `Additional Information:` or `APPROVED:`.
- **Known defects:** 2 rows carry the next label's text, `Smith Additional Infonnation:` and `Additional Infonnation:` (ord_PSD_110321.pdf pages 20 and 53, scan pages). Not corrected (outside the ledger job).
- **Treat as:** names as printed. `Rick Smith`, `Smith & Sontag` and similar variants exist.

### additional_info
- **Meaning:** the free-text note after `Additional Information:`.
- **On the page:** `Additional Information:`
- **Type and format:** string, free text.
- **Allowed:** any text. Blank in 9,803 rows; 155 rows have a note.
- **parse.py:** the text between `Additional Information:` and `APPROVED:`.
- **Known defects:** none counted.
- **Treat as:** a note. Do not assume a blank means anything about the case.

### scan
- **Meaning:** whether the page is a scanned image rather than typed text.
- **On the page:** not printed. It is derived from the PDF.
- **Type and format:** enum.
- **Allowed:** `yes` or `no`. `yes` in 182 rows, `no` in 9,776. Never blank.
- **parse.py:** `yes` when one embedded image covers more than 60 percent of the page (PyMuPDF).
- **Known defects:** none. 173 of the `yes` rows are in ord_PSD_110321.pdf, 8 in ord_PSD_042121.pdf (the checkbox pages) and 1 in ord_PSDNPT_040622.pdf.
- **Treat as:** a warning flag. Scan pages were read from OCR text, so most of the OCR errors and the label-first layout errors above are on scan pages.

## Corrections ledger outcome

`corrections.csv` has 24 rows, each checked on the page image in `evidence/`:

- 8 `recommendation` rows: the checkbox-form pages (ord_PSD_042121.pdf pages 149 to 156). Each now holds the one option that is ticked on the page, worded as on the form.
- 16 `violations` rows: OCR errors in the cite (`lS`, `l` for `1`, `(a)(l)`, a missing space after `IC`, and `16(b)` where the page shows `16(h)`).

Looked at on the page image and left as they are:

- 7 `$$1000` rows and the `$3, 500` row: printed that way on the page.
- The two duplicate `(order_file, case_number)` pairs: two real forms (case 25064) and one identical repeated page (case 33669). Not parse errors.
- The blank `violations` row (ord_PSD_022322.pdf page 129): the violation line is empty on the page, as are `other_party`, both dates and the city of the location.

After the ledger, `verify.py` reports 26 finding cells in 8 columns for `cases_clean.csv` (case_number 1, respondent 2, other_party 1, advisory_meeting_date 1, damage_location 4, recommendation 11, abstentions 2, and 4 rows on the `(order_file, case_number)` key) and no violation of a required column. `violations` has none.
