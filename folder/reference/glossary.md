# Glossary: sections and qualifiers

Run commands from the folder root. `T` = `python3 reference/tools/cases.py`.
Law text: `reference/law/ic-8-1-26-2025.txt` (IC 8-1-26, 2025 code year, extracted from the PDF). Find a passage with
`grep -n -A8 "^IC 8-1-26-20 " reference/law/ic-8-1-26-2025.txt`.

## Evidence tags (read before quoting anything below)
- **LAW**: the 2025 law text says it (the section heading and subsection are quoted or paraphrased).
- **INFERRED**: my matching of an order cite to a 2025 subsection, by content, penalty amount or timing. Say "appears to".
- **LABEL ONLY**: the orders' own word is the only evidence. Do not state a legal meaning.

## Letters in the orders versus the 2025 text (INFERRED)
The 2025 text places the penalty for failing to give notice at 16(i) and the operator's pipeline penalty at 18(j).
The orders print 16(h) and 18(h) for damages up to 2024 and also print 16(i) and 18(j), only in orders from 2025-05 on, for
damages dated 2025. Check: `T group --by base,damage_year --sort key` (the 16(i) and 18(j) rows have damage year 2025 only,
apart from one 18(j) row with damage year 2021, below). Reading: the same duty under older and newer subsection letters. Merge them only when asked,
and then say so. A 2025 order may also still cite 16(h) or 18(h) for a 2024 damage.

## Base sections in the data (one row per section; counts: `T group --by base`)
| Base section | What the law section is about | Tag | Penalty ceiling in the 2025 text |
|---|---|---|---|
| 16(h) | Section 16, notice to excavate: a person who damages a pipeline facility and was required to give the one-call notice but did not; civil penalty recommended by the committee and approved by the commission. Appears to be the 2025 16(i). | LAW for the section; INFERRED for the letter | $10,000 |
| 16(i) | Same duty under the later lettering (damages in 2025). In the 2025 text, 16(j) is the white-lining penalty (no row uses 16(j)). | INFERRED | $10,000 |
| 18(h) | Section 18, operator's duties: an operator of a pipeline facility that did not supply locate information or markings, or the electronic positive response, and whose pipeline facility was then damaged. Appears to be the 2025 18(j). | LAW for the section; INFERRED for the letter | $1,000 |
| 18(j) | Same operator duty under the later lettering (damages in 2025). One 2022 order row (`T receipts --base 18(j) --year 2022`; damage year 2021) has an excavator respondent, a $10,000 recommendation, and an additional_info note about video of the excavator changing the markings; it matches the 2025 18(l) (knowingly moving or altering locate markings, ceiling $10,000). | INFERRED | $1,000 (operator duty), $10,000 (markings) |
| 19(c) | Section 19, emergency excavation: knowingly giving false notice of an emergency excavation. | LAW | $1,000 |
| 20(a)(1) | Section 20, excavator's duties: plan the excavation to avoid damage or minimize interference. | LAW | $10,000 (section 20(b)) |
| 20(a)(2) | Same section: keep the tolerance-zone clearance from a marked facility; expose by hand, air cutting or vacuum within it or under pavement. | LAW | $10,000 (20(b)) |
| 20(a)(3)(a) | Same section: notify the association when there is evidence of an unmarked facility. In the 2025 text this is 20(a)(3)(A). | LAW (letters match by position) | $10,000 (20(b)) |
| 20(a)(3)(b) | Same section: notify the association when markings have become illegible. In the 2025 text this is 20(a)(3)(B). | LAW (letters match by position) | $10,000 (20(b)) |

Notes. In section 20 the penalty provision is subsection (b) and applies to a person who violates (a) and damages a pipeline facility; the order cite names the subsection (a) duty.
Ceilings are the law's "not to exceed" amounts, not the amounts recommended. Compare with the data: `T stat --field headline --base 19(c)`.
One row has a blank cite (`T receipts --blank violations`) and has no section.
Respondent mix by section (utility versus non-utility): `T group --by base,utility --sort key`. Operator sections (18) are almost all utility respondents; the others almost all non-utility.

## Qualifiers (a word in parentheses after the cite; `T group --by qualifier`)
The orders add these words. The 2025 law does not define any of them. Apart from the two noted, the only evidence is the label.
| Qualifier | Seen with | Tag | Plain reading to use |
|---|---|---|---|
| (expire) | 16(h), 16(i), one 20(a)(2) | LABEL ONLY, with a LAW hint | The 2025 16(g) says a notice expires after 20 days. The label fits "the locate request had expired", but the orders do not say so. Write "the orders' (expire) label". |
| (prior) | 16(h), 16(i) | LABEL ONLY | No meaning given. Do not expand it. |
| (out) | 16(h), 16(i) | LABEL ONLY | No meaning given. Do not expand it. |
| (locator-error) | 18(h), 18(j) | LABEL ONLY | Name suggests the locate marking was wrong or missing; the orders give no text. |
| (records) | 18(h), 18(j) | LABEL ONLY | Name suggests a records problem; the orders give no text. |
| (no-response) | 18(h), 18(j) | LABEL ONLY | Name suggests no positive response was given (compare 2025 18(c)); the orders give no text. |
| (other) | 16(h), 16(i) | LABEL ONLY | A catch-all label. |

Check which sections carry which qualifier: `T group --by base,qualifier --sort key`. Qualifiers never appear on 19(c) and, apart from one `(expire)` row, never on section 20.
A parenthesized single letter or digit, such as (h), (a)(2), (3)(b), is part of the section, not a qualifier (PREAMBLE).

## Recommendation wording (what the penalty text looks like)
`T distinct --field recommendation --top 25`. The committee recommends a civil penalty, a warning letter, or
training (with a penalty if the respondent does not complete it); the 2025 law lists those options at 23(h). Escalation
wording ("no ticket escalation - additional $1,000", "concealment", "self-repair") adds to the first amount and the headline
ignores it. "Special instructions: ..." after a warning letter is a note on the letter. Who may be recommended what, and the
first-time homeowner limit, is in 23(i) and 23(j): `grep -n -B2 -A12 "^(i) The advisory board" reference/law/ic-8-1-26-2025.txt`.
