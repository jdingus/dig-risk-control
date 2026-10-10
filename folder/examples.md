# Worked examples

The questions below are invented for this folder. Every output is pasted from a run of the tool (`python3 reference/tools/cases.py`).
Do not reuse their numbers for other questions: the filters differ. Copy the shape: answer line, reading taken, command and
output, receipts, caveats.

## Example 1: a threshold count with a composition check

**Question.** For orders dated 2022 and 2023, how many cases with a non-utility respondent had a headline penalty of
at least $4,000, and which base sections make them up?

**Commands and results.**

    $ python3 reference/tools/cases.py count --year 2022,2023 --utility no --penalty-min 4000 --receipts 3
    # csv rows: 9958 | filters: year in [2022, 2023]; utility respondent = no; headline >= 4000 | rows kept: 1497
    count = 1497 of 9958 rows (15.03%)
        receipt: ord_PSD_011823.pdf p3 case 27494 | IC 8-1-26-16(h) | rec='Training or $5,000 if respondent fails to complete training' | headline=5000 | resp='Quality Excavating Corp'
        receipt: ord_PSD_060822.pdf p202 case 25918 | IC 8-1-26-16(h) | rec='Training or $5,000 if respondent fails to complete training' | headline=5000 | resp='Expert Lawn & Landscape LLC'
        receipt: ord_PSD_122822.pdf p168 case 27188 | IC 8-1-26-20(a)(2) | rec='$5,000' | headline=5000 | resp='MAC Construction & Excavating, Inc.'

    $ python3 reference/tools/cases.py group --by base --year 2022,2023 --utility no --penalty-min 4000
    # csv rows: 9958 | filters: year in [2022, 2023]; utility respondent = no; headline >= 4000 | rows kept: 1497
    group by base: 7 groups; denominator for shares = 1497 kept rows
    16(h)                                    n=899 (60.05%)
    20(a)(2)                                 n=454 (30.33%)
    20(a)(1)                                 n=98 (6.55%)
    20(a)(3)(b)                              n=35 (2.34%)
    20(a)(3)(a)                              n=9 (0.60%)
    (blank)                                  n=1 (0.07%)
    18(j)                                    n=1 (0.07%)

    $ python3 reference/tools/cases.py count --year 2022,2023 --utility no --penalty-min 4000 --expr "'training' not in r['recommendation'].lower()"
    # csv rows: 9958 | filters: year in [2022, 2023]; utility respondent = no; headline >= 4000; expr: 'training' not in r['recommendation'].lower() | rows kept: 448
    count = 448 of 9958 rows (4.50%)

    $ python3 reference/tools/cases.py receipts --year 2022,2023 --utility no --penalty-min 4000 --blank violations
    # csv rows: 9958 | filters: year in [2022, 2023]; utility respondent = no; headline >= 4000; violations is blank | rows kept: 1
        receipt: ord_PSD_022322.pdf p129 case 24409 |  | rec='Training or $5,000 if respondent fails to complete training' | headline=5000 | resp='Cobalt Civil, LLC'

**Answer.** 1,497 of the 9,958 cases (15.03%) are non-utility cases in the 2022 and 2023 orders with a headline
penalty of at least $4,000. By base section: 16(h) 899, 20(a)(2) 454, 20(a)(1) 98, 20(a)(3)(b) 35, 20(a)(3)(a) 9,
18(j) 1, and 1 row with a blank cite (shares are of the 1,497).

**Reading taken.** "At least" is inclusive (>= 4000); headline penalty is the first dollar figure as the PREAMBLE defines it.

**Receipts.** ord_PSD_011823.pdf p3 case 27494; ord_PSD_060822.pdf p202 case 25918; ord_PSD_122822.pdf p168 case 27188.

**Caveats.** (1) Many 16(h) rows read "Training or $5,000 if respondent fails to complete training", whose headline is $5,000
although training avoids it. Excluding every recommendation that mentions training leaves 448 cases. (2) One qualifying row has a blank cite (last command: ord_PSD_022322.pdf p129);
`--exclude-bad` drops it. (3) This is the committee's recommendation, not an amount paid.

## Example 2: names that recur, with a damage-year filter the question supplied

**Question.** Among non-utility respondents, which names have at least nine cases whose damage date is in 2022?

**Command and result.**

    $ python3 reference/tools/cases.py repeat --utility no --eq damage_year=2022 --min 9 --top 4 --receipts 1
    # csv rows: 9958 | filters: utility respondent = no; damage_year == '2022' | rows kept: 1428
    keys (respondent_norm) with >= 9 rows: 4 of 1102 distinct keys; rows covered = 54 of 1428
    note: keys are exact after case/space normalisation; spelling variants are NOT merged.
        23  miller pipeline, llc                               order_years=[2022, 2023] orders=11
        receipt: ord_PSD_011823.pdf p95 case 27783 | IC 8-1-26-20(a)(2) | rec='$5,000' | headline=5000 | resp='Miller Pipeline, LLC'
        11  calumet civil contractors, inc                     order_years=[2022, 2023] orders=5
        receipt: ord_PSD_032923.pdf p148 case 28418 | IC 8-1-26-20(a)(2) | rec='$5,000' | headline=5000 | resp='Calumet Civil Contractors, Inc.'
        11  milestone contractors, l.p                         order_years=[2023] orders=5
        receipt: ord_PSD_020823.pdf p6 case 27020 | IC 8-1-26-20(a)(1) | rec='$5,000' | headline=5000 | resp='Milestone Contractors, L.P.'
         9  crider & crider construction                       order_years=[2022, 2023] orders=7
        receipt: ord_PSD_032923.pdf p142 case 28397 | IC 8-1-26-16(h)(out) | rec='$5,000' | headline=5000 | resp='Crider & Crider Construction'

**Answer.** Four exact names (after case and spacing normalisation) have nine or more such cases, out of 1,428 non-utility cases with a
2022 damage date: Miller Pipeline, LLC 23, Calumet Civil Contractors, Inc. 11, Milestone Contractors, L.P. 11 and Crider & Crider Construction 9. Together they cover 54 of the 1,428 rows.

**Reading taken.** "Damage date in 2022" is the question's own definition, so `--eq damage_year=2022` replaces the default order-year
filter. The `order_years=[...]` column in the output is the order year of those cases (the orders that approved them), not the damage year.

**Receipts.** Miller Pipeline, LLC: ord_PSD_011823.pdf p95 case 27783; ord_PSD_122822.pdf p50 case 27637.

**Caveats.** (1) Spelling variants of one company are not merged (SCHEMA.md), so each count is a floor. (2) The count is of
cases, not of digs: the data holds no exposure measure.

## Example 3: a question the data cannot answer

**Question.** What share of the penalties recommended against utility respondents were actually paid?

**Commands and results.**

    $ python3 reference/tools/cases.py count --rec-contains paid --receipts 1
    # csv rows: 9958 | filters: recommendation contains 'paid' (any case) | rows kept: 1
    count = 1 of 9958 rows (0.01%)
        receipt: ord_PSD_042121.pdf p63 case 22614 | IC 8-1-26-20(a)(2) | rec='$5,000 (paid)' | headline=5000 | resp='Watson Excavating, Inc. (Redkey)'

    $ python3 reference/tools/cases.py count --contains additional_info=paid --receipts 1
    # csv rows: 9958 | filters: additional_info contains 'paid' (any case) | rows kept: 1
    count = 1 of 9958 rows (0.01%)
        receipt: ord_PSD_080322.pdf p126 case 26324 | IC 8-1-26-16(h)(other) | rec='$1,500; respondent can complete training instead of paying $1,500' | headline=1500 | resp='Petry Excavating, Inc.'

    $ python3 reference/tools/cases.py count --utility yes --penalty-min 1
    # csv rows: 9958 | filters: utility respondent = yes; headline >= 1 | rows kept: 2714
    count = 2714 of 9958 rows (27.25%)

**Answer.** It cannot be computed from this folder. There is no payment, appeal or outcome field (SCHEMA.md, "What is NOT in the
data"). The only mentions of payment are free-text notes in 2 of 9,958 rows, and neither has a utility respondent. The nearest
number the data can give is how many utility-respondent cases carry a dollar headline penalty (the last command): that is the
denominator a payment rate would need, and the numerator does not exist.

**Receipts for the two notes.** ord_PSD_042121.pdf p63 case 22614 (recommendation reads "$5,000 (paid)"); ord_PSD_080322.pdf p126 case 26324
(additional_info mentions an earlier payment).

**Caveats.** Any share I gave would be an estimate. If you want one, I would label it "estimate, not from this data"
and say what it rests on.
