"""Builds folder/examples.md by running the commands, so printed outputs cannot drift."""
import subprocess, sys, os
ROOT = sys.argv[1]
def run(args):
    cmd = ["python3", "reference/tools/cases.py"] + args
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True,
                         env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1")).stdout.rstrip()
    shown = "python3 reference/tools/cases.py " + " ".join(a if " " not in a and "$" not in a and "'" not in a else '"%s"' % a for a in args)
    return "    $ " + shown + "\n" + "\n".join("    " + l for l in out.splitlines())

e1 = [["count","--year","2022,2023","--utility","no","--penalty-min","4000","--receipts","3"],
      ["group","--by","base","--year","2022,2023","--utility","no","--penalty-min","4000"],
      ["count","--year","2022,2023","--utility","no","--penalty-min","4000","--expr","'training' not in r['recommendation'].lower()"],
      ["receipts","--year","2022,2023","--utility","no","--penalty-min","4000","--blank","violations"]]
e2 = [["repeat","--utility","no","--eq","damage_year=2022","--min","9","--top","4","--receipts","1"]]
e3 = [["count","--rec-contains","paid","--receipts","1"],
      ["count","--contains","additional_info=paid","--receipts","1"],
      ["count","--utility","yes","--penalty-min","1"]]
B = lambda L: "\n\n".join(run(a) for a in L)

doc = f"""# Worked examples

The questions below are invented for this folder. Every output is pasted from a run of the tool (`python3 reference/tools/cases.py`).
Do not reuse their numbers for other questions: the filters differ. Copy the shape: answer line, reading taken, command and
output, receipts, caveats.

## Example 1: a threshold count with a composition check

**Question.** For orders dated 2022 and 2023, how many cases with a non-utility respondent had a headline penalty of
at least $4,000, and which base sections make them up?

**Commands and results.**

{B(e1)}

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

{B(e2)}

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

{B(e3)}

**Answer.** It cannot be computed from this folder. There is no payment, appeal or outcome field (SCHEMA.md, "What is NOT in the
data"). The only mentions of payment are free-text notes in 2 of 9,958 rows, and neither has a utility respondent. The nearest
number the data can give is how many utility-respondent cases carry a dollar headline penalty (the last command): that is the
denominator a payment rate would need, and the numerator does not exist.

**Receipts for the two notes.** ord_PSD_042121.pdf p63 case 22614 (recommendation reads "$5,000 (paid)"); ord_PSD_080322.pdf p126 case 26324
(additional_info mentions an earlier payment).

**Caveats.** Any share I gave would be an estimate. If you want one, I would label it "estimate, not from this data"
and say what it rests on.
"""
open(os.path.join(ROOT, "examples.md"), "w").write(doc)
