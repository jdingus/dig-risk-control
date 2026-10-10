#!/usr/bin/env python3
"""Answer key for questions.md (Q1-Q10). Python 3 standard library only.

Run:  python3 key/compute_answers.py      (no arguments; any working directory)
Reads: data/cases_clean.csv   Writes: key/answers.json

Every definition is implemented literally as worded in questions.md. Where the wording
leaves a choice, the most literal reading is taken, written as a comment next to the code
and recorded in answers.json under "interpretations".

Rounding: ROUND_HALF_UP (as a human rounds), on the exact fraction (numerator/denominator
computed with Decimal at 60 digits, so true ties are exact). This is NOT Python's round()
(half to even). supporting_counts also records whether half-even would give a different
number for each rounded value ("half_even_differs").
"""
import csv
import hashlib
import json
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN, getcontext
import re
from pathlib import Path

getcontext().prec = 60

HERE = Path(__file__).resolve().parent
CSV_PATH = HERE.parent / "data" / "cases_clean.csv"
OUT_PATH = HERE / "answers.json"

INTERPRETATIONS = {}


def interp(key, text):
    INTERPRETATIONS[key] = text


# ---------------------------------------------------------------- load
raw_bytes = CSV_PATH.read_bytes()
SHA = hashlib.sha256(raw_bytes).hexdigest()
with open(CSV_PATH, newline="", encoding="utf-8") as fh:
    ROWS = list(csv.DictReader(fh))

interp("cases",
       "A case is one row of cases_clean.csv (9,958 rows). No de-duplication: the duplicate case numbers "
       "(e.g. 33669 twice in one order), the case-number '0' row and the blank-violation row all count as cases.")

# ---------------------------------------------------------------- rounding
SPLIT_DIFF = []  # records of rounded values where half-even would differ


def ratio(num, den):
    return Decimal(num) / Decimal(den)


def rnd(value, places, label):
    """ROUND_HALF_UP of a Decimal to `places` decimals; returns (float, differs_from_half_even)."""
    q = Decimal(1).scaleb(-places)
    up = value.quantize(q, rounding=ROUND_HALF_UP)
    ev = value.quantize(q, rounding=ROUND_HALF_EVEN)
    if up != ev:
        SPLIT_DIFF.append(label)
    return (int(up) if places == 0 else float(up)), up != ev


interp("rounding",
       "Rounded values use Decimal ROUND_HALF_UP (a human's rounding) on the exact ratio, not Python's "
       "round() (half to even). Percentages are 100*numerator/denominator rounded to 1 decimal; Q7 means "
       "are rounded to whole dollars. supporting_counts records where half-even would differ.")

# ---------------------------------------------------------------- field parsing
YEAR = lambda r: int(r["order_date"][:4])  # "Year": the year of the order's date (order_date column)
interp("year", "Year = the year of order_date (the order's date), as the preamble says; damage_date is not used.")

CITE_PREFIX = "IC 8-1-26-"
QUAL_RE = re.compile(r"\(([A-Za-z][A-Za-z-]+)\)")  # parenthesized word of 2+ letters (hyphen allowed)


def split_cite(cite):
    """Return (base_section, qualifier). qualifier '' if none."""
    s = cite.strip()
    # Literal reading: remove the prefix "IC 8-1-26-" (cleaned data has no OCR-variant prefixes).
    if s.startswith(CITE_PREFIX):
        s = s[len(CITE_PREFIX):]
    m = QUAL_RE.search(s)
    qual = m.group(1) if m else ""
    # Remove the parenthesized word wherever it sits (it is trailing in all rows).
    base = QUAL_RE.sub("", s).strip()
    return base, qual


interp("base_section_qualifier",
       "Qualifier = a parenthesized group of 2+ letters (hyphens allowed), e.g. (expire), (locator-error), as the "
       "preamble now states; single-letter or digit groups such as (h), (i), (a)(2), (3)(b) are part of the base "
       "section, so 20(a)(3)(b) is its own base section, not 20(a)(2). "
       "Base section = cite minus 'IC 8-1-26-' minus the qualifier. Base section 16(h) therefore includes "
       "16(h) with any qualifier; 16(i) is a different base section. The one blank-cite row has base '' and "
       "stays in 'all cases' denominators.")

# Headline penalty: first "$" amount.
# Literal reading: find the first "$" (a run of "$" counts as one doubled sign); read digits after it,
# allowing a comma followed by an optional single space before exactly three digits ("$3, 500" -> 3500);
# keep any ".dd" decimal part. No "$" in the text -> 0 (so "3000", "0", ".5000" are $0).
AMT_RE = re.compile(r"\$+\s*(\d{1,3}(?:, ?\d{3})+|\d+)(\.\d+)?")


def headline(rec):
    m = AMT_RE.search(rec)
    if not m:
        return Decimal(0)
    whole = m.group(1).replace(",", "").replace(" ", "")
    return Decimal(whole + (m.group(2) or ""))


interp("headline_penalty",
       "Headline penalty = the first '$' amount in the recommendation text as printed, no other arithmetic. "
       "'Training or $5,000 if respondent fails to complete training' therefore has headline $5,000 (the "
       "first $ amount, even though the sentence is a fallback penalty). '$$1000' = 1000; '$3, 500' = 3500; "
       "'$1,500, respondent can complete training ...' = 1500; '$3,000+ training...' = 3000; "
       "'$1,500 fine plus ...' = 1500. Text with no '$' (Warning letter..., Training (completed ...), "
       "'3000', '0', '.5000', 'Other', 'Violation found; no penalty recommended', blank) = $0. "
       "Totals/parentheticals later in the text ('($4,500)') are ignored.")

# Utility respondents.
UTILITY_PREFIXES = [
    "CenterPoint", "Northern Indiana Public Service", "NIPSCO", "Citizens Gas", "Citizens Energy",
    "Vectren", "Indiana American Water", "Ohio Valley Gas", "American Electric Power", "Duke Energy",
    "Community Natural Gas", "Midwest Natural Gas", "Frontier Communications",
]
_UP = tuple(p.lower() for p in UTILITY_PREFIXES)


def is_utility(r):
    # Literal: ignore case and LEADING spaces only (lstrip(" ")); plain str.startswith on the
    # prefix, no word-boundary test, no whitespace collapsing, no punctuation removal. Checked: the
    # data has no leading spaces or tabs in respondent, so lstrip(" ") and lstrip() agree.
    return r["respondent"].lstrip(" ").lower().startswith(_UP)


interp("utility_respondent",
       "Utility respondent = respondent.lstrip(' ').lower().startswith(prefix.lower()) for any of the 13 "
       "prefixes; plain prefix test (no word boundary, no punctuation or inner-space normalising). "
       "A blank respondent is a non-utility respondent ('every other case').")

# Text containment: case-insensitive substring on the recommendation text as stored (spaces already
# collapsed by the parser; no further whitespace normalising).
interp("contains_phrase",
       "'contains the words/word X (any capitalization)' = X.lower() is a substring of recommendation.lower(). "
       "Substring, not whole-word: 'Trainingalready completed' and 'trainingIt is very...' count for "
       "'training'. Variants such as 'trained', 'Train' do not match. 'no ticket escalation' and 'No ticket "
       "escalation' both count for 'ticket escalation'. Whole-word counts are in supporting_counts for sensitivity.")


def has(r, phrase):
    return phrase in r["recommendation"].lower()


def has_word(r, phrase):
    return re.search(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])", r["recommendation"].lower()) is not None


# annotate rows
for r in ROWS:
    r["_year"] = YEAR(r)
    r["_base"], r["_qual"] = split_cite(r["violations"])
    r["_pen"] = headline(r["recommendation"])
    r["_util"] = is_utility(r)

N = len(ROWS)
NONUTIL = [r for r in ROWS if not r["_util"]]
UTIL = [r for r in ROWS if r["_util"]]
POS = [r for r in ROWS if r["_pen"] > 0]


def pct(num, den, label):
    v, differs = rnd(ratio(100 * num, den), 1, label)
    return v


def pct_support(num, den, label):
    exact = ratio(100 * num, den)
    _, differs = rnd(exact, 1, label)
    return {"numerator": num, "denominator": den, "exact_percent": str(exact.quantize(Decimal("0.000001"))),
            "half_even_differs": differs}


def money(d):
    """Dollar value as int if whole else float."""
    return int(d) if d == d.to_integral_value() else float(d)


ANS = {}
SUP = {}

# ---------------------------------------------------------------- Q1
# Denominator: all cases (9,958), "across all five years".
n16h = sum(1 for r in ROWS if r["_base"] == "16(h)")
n20a2 = sum(1 for r in ROWS if r["_base"] == "20(a)(2)")
ANS["Q1"] = {"pct_16h": pct(n16h, N, "Q1 16(h)"), "pct_20a2": pct(n20a2, N, "Q1 20(a)(2)")}
SUP["Q1"] = {"all_cases": N, "base_16h": pct_support(n16h, N, "Q1 16(h)"),
             "base_20a2": pct_support(n20a2, N, "Q1 20(a)(2)")}
interp("Q1", "Denominator = all 9,958 cases (including the blank-cite row); numerators count 16(h) / 20(a)(2) "
             "with or without a qualifier.")

# ---------------------------------------------------------------- Q2
yc = Counter(r["_year"] for r in ROWS)
years = [2021, 2022, 2023, 2024, 2025]
mx = max(yc[y] for y in years)
top = [y for y in years if yc[y] == mx]
ANS["Q2"] = {"cases_2021": yc[2021], "cases_2022": yc[2022], "cases_2023": yc[2023],
             "cases_2024": yc[2024], "cases_2025": yc[2025],
             "year_with_most": top[0] if len(top) == 1 else top}
SUP["Q2"] = {"counts_by_year": {str(y): yc[y] for y in sorted(yc)}, "total": sum(yc.values())}
interp("Q2", "Year counts include every row (duplicates and unusable rows included). Year is order year.")

# ---------------------------------------------------------------- Q3
def mean_for(base):
    vals = [r["_pen"] for r in POS if r["_base"] == base]
    tot = sum(vals, Decimal(0))
    return tot, len(vals)


s16, c16 = mean_for("16(h)")
s20, c20 = mean_for("20(a)(2)")
mean16, d16 = rnd(s16 / c16, 0, "Q3 16(h)")
mean20, d20 = rnd(s20 / c20, 0, "Q3 20(a)(2)")
ANS["Q3"] = {"mean_16h": mean16, "mean_20a2": mean20}
SUP["Q3"] = {"16h": {"sum_headline": money(s16), "n_positive": c16, "exact_mean": str((s16 / c16).quantize(Decimal("0.0001"))),
                     "half_even_differs": d16},
             "20a2": {"sum_headline": money(s20), "n_positive": c20, "exact_mean": str((s20 / c20).quantize(Decimal("0.0001"))),
                      "half_even_differs": d20},
             "n_16h_all": n16h, "n_20a2_all": n20a2}
interp("Q3", "Mean (arithmetic) of headline penalties over cases with headline penalty > $0 and base section 16(h) "
             "(any qualifier) / 20(a)(2); sum / count, rounded half-up to whole dollars. statistics.median is no "
             "longer used.")

# ---------------------------------------------------------------- Q4
PH = "warning letter"
u_w = sum(1 for r in UTIL if has(r, PH))
n_w = sum(1 for r in NONUTIL if has(r, PH))
ANS["Q4"] = {"pct_utility_warning_letter": pct(u_w, len(UTIL), "Q4 util"),
             "pct_nonutility_warning_letter": pct(n_w, len(NONUTIL), "Q4 nonutil")}
SUP["Q4"] = {"utility": pct_support(u_w, len(UTIL), "Q4 util"),
             "non_utility": pct_support(n_w, len(NONUTIL), "Q4 nonutil"),
             "whole_word_warning_letter_utility": sum(1 for r in UTIL if has_word(r, PH)),
             "whole_word_warning_letter_nonutility": sum(1 for r in NONUTIL if has_word(r, PH))}

# ---------------------------------------------------------------- Q5
t_n = sum(1 for r in POS if has(r, "training"))
ANS["Q5"] = {"pct_training": pct(t_n, len(POS), "Q5")}
SUP["Q5"] = {"training": pct_support(t_n, len(POS), "Q5"),
             "whole_word_training_numerator": sum(1 for r in POS if has_word(r, "training"))}
interp("Q5", "Denominator = cases with headline penalty > 0 (any respondent type); numerator = those whose "
             "recommendation contains 'training' (substring, case-insensitive).")

# ---------------------------------------------------------------- Q6
SUFFIXES = {"inc", "llc", "co", "corp", "corporation", "company"}


def norm_name(s):
    # Steps in the stated order (questions.md Q6):
    # 1. lowercase
    s = s.lower()
    # 2. delete every character that is not a letter, a digit or a space, with NO replacement
    #    ("c s u, inc." -> "c s u inc"; "o'brien" -> "obrien"). Letter/digit = str.isalpha()/isdigit()/isalnum();
    #    "space" = the space character only (the data has no tabs or other whitespace in respondent).
    s = "".join(ch for ch in s if ch == " " or ch.isalnum())
    # 3. collapse runs of spaces to one and trim
    s = re.sub(" +", " ", s).strip(" ")
    # 4. once, drop a final whole word if it is exactly one of the six suffix words (single pass).
    parts = s.split(" ")
    if parts and parts[-1] in SUFFIXES:
        parts = parts[:-1]
    return " ".join(parts)


interp("Q6",
       "Normalisation exactly as worded: lowercase; delete every character that is not a letter, a digit or a "
       "space (str.isalnum() or ' '), no replacement, so 'C S U, Inc.' -> 'c s u inc'; collapse runs of spaces "
       "to one and trim; then once drop a final whole word if it is exactly inc/llc/co/corp/corporation/company "
       "('x co inc' -> 'x co'; a name that is only a suffix word becomes ''). No other merging (spelling variants "
       "stay separate). Percent denominator = all non-utility cases (blank respondent included); numerator = "
       "non-utility cases whose normalized name has >= 5 non-utility cases. Counting is of case rows, not "
       "unique case numbers.")
groups = Counter(norm_name(r["respondent"]) for r in NONUTIL)
big = {k: v for k, v in groups.items() if v >= 5}
big_cases = sum(big.values())
ANS["Q6"] = {"distinct_respondents_5plus": len(big),
             "pct_of_nonutility_cases": pct(big_cases, len(NONUTIL), "Q6")}
SUP["Q6"] = {"nonutility_cases": len(NONUTIL), "distinct_normalized_nonutility": len(groups),
             "cases_in_5plus_groups": big_cases, "pct": pct_support(big_cases, len(NONUTIL), "Q6"),
             "empty_normalized_name_cases": groups.get("", 0),
             "top10_groups": sorted(big.items(), key=lambda kv: (-kv[1], kv[0]))[:10]}

# ---------------------------------------------------------------- Q7
def mean_pen(year):
    rs = [r for r in NONUTIL if r["_year"] == year]
    tot = sum((r["_pen"] for r in rs), Decimal(0))
    return tot, len(rs)


t21, n21 = mean_pen(2021)
t25, n25 = mean_pen(2025)
v21, d21 = rnd(t21 / n21, 0, "Q7 2021")
v25, d25 = rnd(t25 / n25, 0, "Q7 2025")
ANS["Q7"] = {"mean_2021": v21, "mean_2025": v25}
SUP["Q7"] = {"2021": {"sum_headline": money(t21), "cases": n21, "exact_mean": str((t21 / n21).quantize(Decimal("0.0001"))),
                      "half_even_differs": d21},
             "2025": {"sum_headline": money(t25), "cases": n25, "exact_mean": str((t25 / n25).quantize(Decimal("0.0001"))),
                      "half_even_differs": d25}}
interp("Q7", "Mean = sum of headline penalties (all non-utility cases of that order year, $0 cases included) / "
             "number of those cases; rounded half-up to whole dollars.")

# ---------------------------------------------------------------- Q8
esc = [r for r in ROWS if has(r, "ticket escalation")]
pc = Counter(r["_pen"] for r in esc)
mxc = max(pc.values())
modes = sorted(k for k, v in pc.items() if v == mxc)
ANS["Q8"] = {"count_ticket_escalation": len(esc),
             "most_common_headline_penalty": money(modes[0]) if len(modes) == 1 else [money(m) for m in modes]}
SUP["Q8"] = {"cases": len(esc), "headline_penalty_distribution": {str(money(k)): v for k, v in sorted(pc.items())},
             "mode_count": mxc, "whole_word_count": sum(1 for r in ROWS if has_word(r, "ticket escalation"))}
interp("Q8", "Counts all respondent types and all years (no filter). Matches 'no ticket escalation' as well as any "
             "other mention (the question says 'containing'). Mode of the headline penalty (first $ amount) "
             "among those cases; a tie would be reported as a list.")

# ---------------------------------------------------------------- Q9
# "exact text, ignoring case and surrounding spaces": key = other_party.strip().lower(); nothing else
# (punctuation, inner spaces, spelling variants stay distinct). A blank other_party is not a name
# and is not eligible to be the winner, but stays in the denominator.
op = Counter(r["other_party"].strip().lower() for r in NONUTIL)
blank_op = op.get("", 0)
named = {k: v for k, v in op.items() if k != ""}
mx9 = max(named.values())
winners = sorted(k for k, v in named.items() if v == mx9)
display = Counter(r["other_party"].strip() for r in NONUTIL if r["other_party"].strip().lower() == winners[0])
ANS["Q9"] = {"most_common_other_party": winners[0] if len(winners) == 1 else winners,
             "pct_of_nonutility_cases": pct(mx9, len(NONUTIL), "Q9")}
SUP["Q9"] = {"count": mx9, "nonutility_cases": len(NONUTIL), "pct": pct_support(mx9, len(NONUTIL), "Q9"),
             "blank_other_party_nonutility_cases": blank_op,
             "printed_forms_of_winner": dict(display),
             "top5_other_party": sorted(named.items(), key=lambda kv: (-kv[1], kv[0]))[:5]}
interp("Q9", "Key = other_party.strip().lower() only (no punctuation or inner-space changes). The answer is "
             "given lowercased; the printed capitalisations are in supporting_counts. Blank other_party is "
             "not a name (cannot win) but stays in the denominator (all non-utility cases). Percent = "
             "cases with that other party / all non-utility cases.")

# ---------------------------------------------------------------- Q10
R16 = [r for r in ROWS if r["_base"] == "16(h)"]
ex = sum(1 for r in R16 if r["_qual"] == "expire")
pr = sum(1 for r in R16 if r["_qual"] == "prior")
ANS["Q10"] = {"pct_expire": pct(ex, len(R16), "Q10 expire"), "pct_prior": pct(pr, len(R16), "Q10 prior")}
SUP["Q10"] = {"base_16h_cases": len(R16), "expire": pct_support(ex, len(R16), "Q10 expire"),
              "prior": pct_support(pr, len(R16), "Q10 prior"),
              "qualifier_counts_16h": dict(sorted(Counter(r["_qual"] or "(none)" for r in R16).items()))}
interp("Q10", "Denominator = all base-16(h) cases, including those with no qualifier; 16(i) cases are excluded.")

# ---------------------------------------------------------------- general supporting counts
SUP["general"] = {
    "rows": N, "utility_cases": len(UTIL), "nonutility_cases": len(NONUTIL),
    "cases_headline_penalty_gt0": len(POS), "cases_headline_penalty_0": N - len(POS),
    "base_section_counts": dict(sorted(Counter(r["_base"] for r in ROWS).items())),
    "qualifier_counts": dict(sorted(Counter(r["_qual"] or "(none)" for r in ROWS).items())),
    "rounded_values_where_half_even_differs": SPLIT_DIFF,
}

out = {
    "cases_clean_sha256": SHA,
    "rows": N,
    "answers": ANS,
    "interpretations": INTERPRETATIONS,
    "supporting_counts": SUP,
}
OUT_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
print(f"wrote {OUT_PATH}")
