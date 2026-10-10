#!/usr/bin/env python3
"""make_tables.py - builds folder-nocode/reference/tables/*.md from input/cases_clean.csv.

Standard library only. Run:  python3 -I folder-nocode-build/make_tables.py
Implements the PREAMBLE definitions exactly (base section / qualifier, headline penalty,
utility respondent, order year). Ends with independent spot checks that make the script fail
(non-zero exit) if a table value disagrees with a second computation.
"""
import csv, os, re, sys, math, sqlite3, statistics
from collections import Counter, defaultdict
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(BASE, "data", "cases_clean.csv")  # repo-relative (was the build staging dir)
OUT = os.path.join(BASE, "folder-nocode", "reference", "tables")

# ------------------------------------------------------------------ PREAMBLE definitions
UTILITY_PREFIXES = ["CenterPoint", "Northern Indiana Public Service", "NIPSCO", "Citizens Gas",
                    "Citizens Energy", "Vectren", "Indiana American Water", "Ohio Valley Gas",
                    "American Electric Power", "Duke Energy", "Community Natural Gas",
                    "Midwest Natural Gas", "Frontier Communications"]
QUAL_RE = re.compile(r"\(([A-Za-z][A-Za-z-]+)\)")          # two or more letters, hyphens allowed
MONEY_RE = re.compile(r"\$+\s*(\d+(?:,\s?\d{3})*(?:\.\d+)?)")  # doubled $, space after thousands comma


def qualifier(cite):
    return "+".join(QUAL_RE.findall(cite or ""))


def base_section(cite):
    s = (cite or "").strip()
    if s.startswith("IC 8-1-26-"):
        s = s[len("IC 8-1-26-"):]
    return QUAL_RE.sub("", s).strip()


def headline(rec):
    m = MONEY_RE.search(rec or "")
    return int(round(float(m.group(1).replace(",", "").replace(" ", "")))) if m else 0


def utility_prefix(name):
    s = (name or "").lstrip().casefold()
    for p in UTILITY_PREFIXES:
        if s.startswith(p.casefold()):
            return p
    return ""


def norm_name(name):
    return re.sub(r"\s+", " ", (name or "").strip()).casefold().rstrip(".,")


SUFFIX = {"inc", "llc", "co", "corp", "corporation", "company", "lp", "ltd", "l", "p", "the", "dba"}


def loose_name(name):
    s = re.sub(r"[^a-z0-9 ]", " ", (name or "").casefold())
    w = [x for x in s.split() if x not in SUFFIX]
    return " ".join(w)


def pdate(s):
    for f in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime((s or "").strip(), f).date()
        except ValueError:
            pass
    return None


def outcome(rec, hl):
    low = (rec or "").strip().casefold()
    if low.startswith("warning letter"):
        return "W"
    if "train" in low:
        if hl == 0:
            return "TO"
        return "TR5" if low.startswith("training") else "PT"
    if hl > 0:
        return "F"
    return "X"


OUTCOMES = ["W", "TR5", "TO", "PT", "F", "X"]
OUTCOME_NAMES = {
    "W": "warning letter (text starts 'warning letter', any special instructions)",
    "TR5": "training, or $5,000 if the respondent fails to train (text starts 'Training'; headline is the first $ figure, usually 5000)",
    "TO": "training only, no $ amount (headline 0)",
    "PT": "dollar penalty that the respondent can mitigate or replace by training (text starts with $ and mentions training)",
    "F": "flat dollar penalty, no training mentioned",
    "X": "no $ amount and no warning/training wording: blank, 'Other', 'Violation found; no penalty recommended', bare '0', '3000', '.5000'",
}

NAME_TYPES = ["gov", "telecom", "energy_water", "contractor", "other"]


def name_type(name):
    s = (name or "").casefold()
    if re.search(r"\b(city of|town of|village of|county|township|school|department|dept|board of|commissioners|municipal|authority|state of|indiana department|indot|district|sanitary|conservancy|housing)\b", s):
        return "gov"
    if re.search(r"(telecom|communication|cable|fiber|fibre|broadband|wireless|telephone|\bat&t\b|comcast|spectrum|frontier|verizon|lumen|mediacom|zayo)", s):
        return "telecom"
    if re.search(r"\b(gas|water|electric|energy|power|utilit(y|ies)|rural|rec|remc|pipeline co|pipeline corp|propane)\b", s) and not re.search(r"(construct|excavat|contract|plumb|paving|boring|drilling)", s):
        return "energy_water"
    if re.search(r"(construct|excavat|contract|plumb|paving|asphalt|concrete|boring|drilling|underground|landscap|lawn|fence|fencing|utilities,? llc|utility contract|trench|demolition|building|builders|homes|roofing|electric|pipeline|grading|sewer|septic|tree|drain|earth|dirt|dozing|site work|sitework|mechanical|services)", s):
        return "contractor"
    return "other"


# ------------------------------------------------------------------ load
def load():
    rows = []
    with open(CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["page"] = int(r["page"])
            r["base"] = base_section(r["violations"]) or "(blank)"
            r["qual"] = qualifier(r["violations"]) or "-"
            r["cite"] = r["base"] + ("" if r["qual"] == "-" else "(" + r["qual"] + ")")
            r["hl"] = headline(r["recommendation"])
            r["low"] = r["recommendation"].casefold()
            r["oc"] = outcome(r["recommendation"], r["hl"])
            r["upre"] = utility_prefix(r["respondent"])
            r["u"] = "U" if r["upre"] else "N"
            r["oupre"] = utility_prefix(r["other_party"])
            r["yr"] = int(r["order_date"][:4])
            r["rn"] = norm_name(r["respondent"])
            r["rl"] = loose_name(r["respondent"])
            d, o, m = pdate(r["damage_date"]), pdate(r["order_date"]), pdate(r["advisory_meeting_date"])
            r["dy"] = d.year if d else None
            r["dm"] = d.month if d else None
            r["lag_do"] = (o - d).days if (d and o) else None
            r["lag_mo"] = (o - m).days if (m and o) else None
            r["lag_dm"] = (m - d).days if (d and m) else None
            loc = r["damage_location"]
            r["city"] = loc.rsplit(",", 1)[1].strip().casefold() if "," in loc else ""
            r["q"] = "%d-Q%d" % (r["yr"], (int(r["order_date"][5:7]) - 1) // 3 + 1)
            r["esc"] = ("escalation" in r["low"]) or ("additional" in r["low"])
            r["train"] = "train" in r["low"]
            r["ntype"] = "util" if r["upre"] else name_type(r["respondent"])
            rows.append(r)
    return rows


ROWS = load()
YEARS = sorted({r["yr"] for r in ROWS})
BASES = sorted({r["base"] for r in ROWS if r["base"] != "(blank)"}) + ["(blank)"]
QUALS = ["-"] + [q for q, _ in Counter(r["qual"] for r in ROWS if r["qual"] != "-").most_common()]
VALUES = sorted({r["hl"] for r in ROWS})


# ------------------------------------------------------------------ helpers
def pct(a, b):
    return "%.1f" % (100.0 * a / b) if b else "-"


def nearest_rank(sv, q):
    return sv[max(0, math.ceil(q * len(sv)) - 1)]


def fm(x, d=1):
    if isinstance(x, float):
        return str(int(x)) if x == int(x) else ("%.*f" % (d, x))
    return str(x)


def mdtable(header, body, align=None):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    for row in body:
        out.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(out) + "\n"


def stat_cells(vals):
    """n, zero, sum, mean, median, p25, p75, p90, max, median of positive values."""
    n = len(vals)
    if n == 0:
        return [0, 0, 0, "-", "-", "-", "-", "-", "-", "-"]
    sv = sorted(vals)
    pos = [v for v in sv if v > 0]
    return [n, sum(1 for v in sv if v == 0), sum(sv), "%.1f" % (sum(sv) / n),
            fm(float(statistics.median(sv)), 1),
            nearest_rank(sv, .25), nearest_rank(sv, .75), nearest_rank(sv, .90), sv[-1],
            fm(float(statistics.median(pos)), 1) if pos else "-"]


STAT_HEAD = ["n", "zero", "sum", "mean", "median", "p25", "p75", "p90", "max", "median_of_positive"]


def group(rows, keyf):
    g = defaultdict(list)
    for r in rows:
        g[keyf(r)].append(r)
    return g


def stat_block(rows, title, names, keyf, order=None):
    g = group(rows, keyf)
    keys = order if order else sorted(g)
    body = []
    for k in keys:
        if k not in g:
            continue
        kk = k if isinstance(k, tuple) else (k,)
        body.append(list(kk) + stat_cells([r["hl"] for r in g[k]]))
    return "### %s\n\n" % title + mdtable(names + STAT_HEAD, body) + "\n"


FILES = {}


def put(fname, text):
    FILES.setdefault(fname, []).append(text)


UB = lambda r: (r["u"],)
# ===================================================================== FILE 01: overview, time
f = "01_overview_time.md"
put(f, """# 01 Overview and time cuts

All counts are rows of the case table (one row = one case, as the PREAMBLE defines). `year` = order year (year of the
order date) unless a table says `damage year`. `U` = utility respondent, `N` = non-utility respondent (PREAMBLE prefix test).
`headline` = headline penalty in dollars (PREAMBLE rule). `zero` = rows with headline 0. `pos` = rows with headline > 0.
Outcome codes: W warning letter; TR5 training-or-$5,000; TO training only; PT $ penalty mitigable by training; F flat $ penalty;
X no $ amount and no warning or training wording. Full definitions in INDEX.md.

""")
N = len(ROWS)
put(f, "## Data size and data-quality counts\n\n")
orders = sorted({r["order_file"] for r in ROWS})
dq = [
    ("rows (cases)", N),
    ("order files", len(orders)),
    ("distinct order dates", len({r["order_date"] for r in ROWS})),
    ("rows with blank cite (base section '(blank)')", sum(1 for r in ROWS if r["base"] == "(blank)")),
    ("rows whose case_number is not 5 digits (case '0')", sum(1 for r in ROWS if not re.fullmatch(r"\d{5}", r["case_number"]))),
    ("distinct (order_file, case_number) pairs", len({(r["order_file"], r["case_number"]) for r in ROWS})),
    ("distinct case_number values", len({r["case_number"] for r in ROWS})),
    ("rows with a qualifier on the cite", sum(1 for r in ROWS if r["qual"] != "-")),
    ("rows with headline 0", sum(1 for r in ROWS if r["hl"] == 0)),
    ("rows with headline > 0", sum(1 for r in ROWS if r["hl"] > 0)),
    ("utility-respondent rows (U)", sum(1 for r in ROWS if r["u"] == "U")),
    ("non-utility-respondent rows (N)", sum(1 for r in ROWS if r["u"] == "N")),
    ("rows with a note in additional_info", sum(1 for r in ROWS if r["additional_info"].strip())),
    ("scan-page rows (OCR)", sum(1 for r in ROWS if r["scan"] == "yes")),
    ("sum of all headline penalties ($)", sum(r["hl"] for r in ROWS)),
    ("distinct respondent names (exact, case/space-normalised)", len({r["rn"] for r in ROWS})),
    ("rows with blank respondent", sum(1 for r in ROWS if not r["respondent"].strip())),
]
put(f, mdtable(["measure", "value"], dq) + "\n")
dups = [(k, c) for k, c in Counter((r["order_file"], r["case_number"]) for r in ROWS).items() if c > 1]
put(f, "Duplicate (order_file, case_number) pairs (rows counted twice if you count rows; case numbers are not unique keys): "
       + "; ".join("%s case %s x%d" % (k[0], k[1], c) for k, c in sorted(dups)) + ".\n\n")

# ---- by year
put(f, "## A. Year summary (order year)\n\n")
body = []
for y in YEARS + ["all"]:
    rs = [r for r in ROWS if y == "all" or r["yr"] == y]
    n = len(rs)
    nu = sum(1 for r in rs if r["u"] == "U")
    body.append([y, len({r["order_file"] for r in rs}), len({r["order_date"] for r in rs}), n, nu, n - nu,
                 sum(1 for r in rs if r["hl"] > 0), sum(1 for r in rs if r["hl"] == 0), sum(r["hl"] for r in rs),
                 sum(r["hl"] for r in rs if r["u"] == "U"), sum(r["hl"] for r in rs if r["u"] == "N"),
                 sum(1 for r in rs if r["qual"] != "-"), len({r["rn"] for r in rs}),
                 len({(r["order_file"], r["case_number"]) for r in rs}), len({r["case_number"] for r in rs}),
                 sum(1 for r in rs if r["additional_info"].strip()), sum(1 for r in rs if r["scan"] == "yes")])
put(f, mdtable(["year", "orders", "order_dates", "cases", "U", "N", "pos", "zero", "sum_hl", "sum_hl_U", "sum_hl_N", "with_qual",
                "distinct_names", "distinct_order_case_pairs", "distinct_case_numbers", "with_note", "scan_rows"], body) + "\n")
put(f, stat_block(ROWS, "A2. Headline penalty statistics by year", ["year"], lambda r: r["yr"]))
put(f, stat_block(ROWS, "A3. Headline penalty statistics by year and respondent type", ["year", "resp"], lambda r: (r["yr"], r["u"])))

# ---- year x base counts and shares
put(f, "## B. Cases by year x base section (all respondents) and respondent type\n\n")
body = []
for b in BASES:
    row = [b]
    for y in YEARS:
        row.append(sum(1 for r in ROWS if r["base"] == b and r["yr"] == y))
    row.append(sum(row[1:]))
    body.append(row)
tot = ["all"] + [sum(1 for r in ROWS if r["yr"] == y) for y in YEARS]
tot.append(sum(tot[1:]))
body.append(tot)
put(f, mdtable(["base"] + [str(y) for y in YEARS] + ["all"], body) + "\n")
for ut in ("U", "N"):
    body = []
    for b in BASES:
        row = [b]
        for y in YEARS:
            row.append(sum(1 for r in ROWS if r["base"] == b and r["yr"] == y and r["u"] == ut))
        row.append(sum(row[1:]))
        if row[-1]:
            body.append(row)
    put(f, "B-%s. Cases by base section x year, %s respondents only\n\n" % (ut, "utility" if ut == "U" else "non-utility")
        + mdtable(["base"] + [str(y) for y in YEARS] + ["all"], body) + "\n")


# ---- lettering change
put(f, "## B3. Later subsection letters 16(i) and 18(j): first and last order date, and damage years\n\n")
body = []
for b in ("16(h)", "16(i)", "18(h)", "18(j)"):
    rs = [r for r in ROWS if r["base"] == b]
    dyc = Counter(r["dy"] for r in rs)
    body.append([b, len(rs), min(r["order_date"] for r in rs), max(r["order_date"] for r in rs), "; ".join("%s: %d" % (k, dyc[k]) for k in sorted(dyc, key=lambda x: x or 0))])
put(f, mdtable(["base", "cases", "first_order_date", "last_order_date", "cases by damage year"], body) + "\n")

# qualifier x year
put(f, "## C. Qualifier by year (all base sections; '-' = no qualifier)\n\n")
body = []
for q in QUALS:
    row = [q] + [sum(1 for r in ROWS if r["qual"] == q and r["yr"] == y) for y in YEARS]
    row.append(sum(row[1:]))
    body.append(row)
put(f, mdtable(["qualifier"] + [str(y) for y in YEARS] + ["all"], body) + "\n")
put(f, "C2. Qualifier x base section (all years)\n\n")
body = []
for q in QUALS:
    row = [q] + [sum(1 for r in ROWS if r["qual"] == q and r["base"] == b) for b in BASES]
    row.append(sum(row[1:]))
    body.append(row)
put(f, mdtable(["qualifier"] + BASES + ["all"], body) + "\n")

# ---- per order
put(f, "## D. Every order (58 files): date, cases, mix\n\n")
body = []
for o in orders:
    rs = [r for r in ROWS if r["order_file"] == o]
    body.append([o.replace("ord_", "").replace(".pdf", ""), rs[0]["order_date"], len(rs), sum(1 for r in rs if r["u"] == "U"),
                 sum(1 for r in rs if r["hl"] > 0), sum(1 for r in rs if r["oc"] == "W"), sum(r["hl"] for r in rs)])
body.sort(key=lambda x: (x[1], x[0]))
put(f, mdtable(["order", "date", "cases", "U", "pos", "W", "sum_hl"], body) + "\n")
put(f, "D2. Orders per year with case-count spread (cases per order)\n\n")
body = []
for y in YEARS:
    cs = sorted(Counter(r["order_file"] for r in ROWS if r["yr"] == y).values())
    body.append([y, len(cs), sum(cs), cs[0], statistics.median(cs), cs[-1]])
put(f, mdtable(["year", "orders", "cases", "min_per_order", "median_per_order", "max_per_order"], body) + "\n")

# ---- quarter
put(f, "## E. Order quarter (quarter of the order date)\n\n")
body = []
for q in sorted({r["q"] for r in ROWS}):
    rs = [r for r in ROWS if r["q"] == q]
    body.append([q, len({r["order_file"] for r in rs}), len(rs), sum(1 for r in rs if r["u"] == "U"), sum(1 for r in rs if r["hl"] > 0),
                 sum(r["hl"] for r in rs), sum(1 for r in rs if r["oc"] == "W")])
put(f, mdtable(["quarter", "orders", "cases", "U", "pos", "sum_hl", "W"], body) + "\n")

# ---- damage year
put(f, "## F. Damage year (year of the damage date; the PREAMBLE 'year' is the ORDER year, so use these only if the question says damage year)\n\n")
dys = sorted({r["dy"] for r in ROWS if r["dy"]})
body = []
for dyv in dys:
    row = [dyv] + [sum(1 for r in ROWS if r["dy"] == dyv and r["yr"] == y) for y in YEARS]
    row.append(sum(row[1:]))
    body.append(row)
row = ["(blank)"] + [sum(1 for r in ROWS if r["dy"] is None and r["yr"] == y) for y in YEARS]
row.append(sum(row[1:]))
body.append(row)
put(f, "F1. Cases: damage year (rows) x order year (columns)\n\n" + mdtable(["damage_year"] + [str(y) for y in YEARS] + ["all"], body) + "\n")
body = []
for dyv in dys:
    rs = [r for r in ROWS if r["dy"] == dyv]
    body.append([dyv, len(rs), sum(1 for r in rs if r["u"] == "U"), sum(1 for r in rs if r["hl"] > 0), sum(r["hl"] for r in rs),
                 sum(r["hl"] for r in rs if r["u"] == "U"), "%.1f" % (sum(r["hl"] for r in rs) / len(rs)), sum(1 for r in rs if r["oc"] == "W"),
                 sum(1 for r in rs if r["qual"] != "-")])
put(f, "F2. Damage year totals\n\n" + mdtable(["damage_year", "cases", "U", "pos", "sum_hl", "sum_hl_U", "mean_hl", "W", "with_qual"], body) + "\n")
body = []
for b in BASES:
    row = [b] + [sum(1 for r in ROWS if r["base"] == b and r["dy"] == d) for d in dys if d >= 2019]
    body.append(row)
put(f, "F3. Cases: base section x damage year (damage years 2019 on)\n\n" + mdtable(["base"] + [str(d) for d in dys if d >= 2019], body) + "\n")
body = []
for ut in ("U", "N"):
    body.append([ut] + [sum(1 for r in ROWS if r["u"] == ut and r["dy"] == d) for d in dys if d >= 2019])
put(f, "F4. Cases: respondent type x damage year\n\n" + mdtable(["resp"] + [str(d) for d in dys if d >= 2019], body) + "\n")
body = []
for dyv in [d for d in dys if 2020 <= d <= 2025]:
    row = [dyv] + [sum(1 for r in ROWS if r["dy"] == dyv and r["dm"] == m) for m in range(1, 13)]
    row.append(sum(row[1:]))
    body.append(row)
put(f, "F5. Cases: damage year x damage month (seasonality; cases counted by when approved orders say the damage happened)\n\n"
    + mdtable(["damage_year"] + ["m%d" % m for m in range(1, 13)] + ["all"], body) + "\n")
body = []
for ut in ("U", "N"):
    body.append([ut] + [sum(1 for r in ROWS if r["dy"] and 2020 <= r["dy"] <= 2024 and r["u"] == ut and r["dm"] == m) for m in range(1, 13)])
body.append(["all"] + [sum(1 for r in ROWS if r["dy"] and 2020 <= r["dy"] <= 2024 and r["dm"] == m) for m in range(1, 13)])
put(f, "F6. Cases by damage month, damage years 2020-2024 pooled (the full years)\n\n" + mdtable(["resp"] + ["m%d" % m for m in range(1, 13)], body) + "\n")

# ---- lags
put(f, "## G. Lags in days (rows with both dates parseable)\n\n")


def lag_cells(vals):
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return [0] + ["-"] * 5
    return [len(vals), "%.1f" % (sum(vals) / len(vals)), fm(float(statistics.median(vals)), 1),
            nearest_rank(vals, .25), nearest_rank(vals, .75), nearest_rank(vals, .90)]


body = []
for y in YEARS + ["all"]:
    rs = [r for r in ROWS if y == "all" or r["yr"] == y]
    body.append([y] + lag_cells([r["lag_do"] for r in rs]) + lag_cells([r["lag_mo"] for r in rs])[1:] + lag_cells([r["lag_dm"] for r in rs])[1:])
put(f, mdtable(["year", "n", "damage->order mean", "median", "p25", "p75", "p90", "meeting->order mean", "median", "p25", "p75", "p90",
                "damage->meeting mean", "median", "p25", "p75", "p90"], body) + "\n")
body = []
for b in BASES:
    rs = [r for r in ROWS if r["base"] == b]
    body.append([b] + lag_cells([r["lag_do"] for r in rs]))
put(f, "G2. Damage->order lag by base section\n\n" + mdtable(["base", "n", "mean", "median", "p25", "p75", "p90"], body) + "\n")
bins = [(0, 90), (91, 180), (181, 365), (366, 730), (731, 10 ** 6)]
body = []
for y in YEARS:
    rs = [r for r in ROWS if r["yr"] == y and r["lag_do"] is not None]
    body.append([y] + [sum(1 for r in rs if lo <= r["lag_do"] <= hi) for lo, hi in bins] + [sum(1 for r in rs if r["lag_do"] < 0)])
put(f, "G3. Damage->order lag buckets by order year (counts)\n\n" + mdtable(["year", "0-90d", "91-180d", "181-365d", "366-730d", ">730d", "negative"], body) + "\n")

put(f, "G4. Advisory-meeting year (year of the committee meeting date) x order year, cases\n\n")
mys = sorted({pdate(r["advisory_meeting_date"]).year for r in ROWS if pdate(r["advisory_meeting_date"])})
body = []
for m in mys:
    row = [m] + [sum(1 for r in ROWS if r["yr"] == y and pdate(r["advisory_meeting_date"]) and pdate(r["advisory_meeting_date"]).year == m) for y in YEARS]
    row.append(sum(row[1:]))
    body.append(row)
put(f, mdtable(["meeting_year"] + [str(y) for y in YEARS] + ["all"], body) + "\n")

# ===================================================================== FILE 02: cube
f = "02_cube.md"
put(f, """# 02 Main cube: order year x cite x respondent type

One line per (year, base section, qualifier, resp) that has at least one case. Sum any set of lines to get a count,
a dollar total or an outcome mix for any cut that is a union of these cells (a year, a base section, a qualifier,
utility or not, or combinations). `qual` '-' = no qualifier. `resp` U = utility respondent, N = non-utility.
Columns: n = cases; sum = total headline $; pos = cases with headline > 0; W, TR5, TO, PT, F, X = outcome counts
(they add to n); sum_notrain = sum of headline over cases whose recommendation text does not mention training
(the 'TR5' and 'PT' cases carry headline amounts that training can avoid or reduce, so sum - sum_notrain is the
'training-linked' headline); esc = cases whose recommendation text mentions escalation or 'additional'.
Means = sum / n. Medians are NOT recombinable: see 03 for medians and 04 for histograms.

""")
g = group(ROWS, lambda r: (r["yr"], r["base"], r["qual"], r["u"]))
body = []
for k in sorted(g, key=lambda k: (k[0], BASES.index(k[1]), QUALS.index(k[2]), k[3])):
    rs = g[k]
    c = Counter(r["oc"] for r in rs)
    body.append([k[0], k[1], k[2], k[3], len(rs), sum(r["hl"] for r in rs), sum(1 for r in rs if r["hl"] > 0)]
                + [c.get(o, 0) for o in OUTCOMES]
                + [sum(r["hl"] for r in rs if not r["train"]), sum(1 for r in rs if r["esc"])])
CUBE_ROWS = body
put(f, mdtable(["year", "base", "qual", "resp", "n", "sum", "pos"] + OUTCOMES + ["sum_notrain", "esc"], body) + "\n")

# ===================================================================== FILE 03: penalty stats
f = "03_penalty_stats.md"
put(f, """# 03 Penalty statistics (severity) and outcome mix

Headline penalty in dollars (first $ amount; no $ -> 0). Warning letters and training-only have headline 0.
`zero` = headline-0 rows, `median_of_positive` = median over rows with headline > 0. Percentiles are nearest-rank
(smallest value with at least that share of rows at or below it); median = average of the two middle values when n is even.
Means are sum / n (n includes zeros). To get a mean for a union of rows, add the sums and the ns from the cube (02), not the means.

""")
put(f, stat_block(ROWS, "S0. All cases", ["all"], lambda r: "all"))
put(f, stat_block(ROWS, "S1. By base section", ["base"], lambda r: r["base"], BASES))
put(f, stat_block(ROWS, "S2. By respondent type", ["resp"], lambda r: r["u"]))
put(f, stat_block(ROWS, "S3. By qualifier", ["qual"], lambda r: r["qual"], QUALS))
put(f, stat_block(ROWS, "S4. By cite (base + qualifier)", ["cite"], lambda r: r["cite"],
                  sorted({r["cite"] for r in ROWS}, key=lambda c: (BASES.index(base_section("IC 8-1-26-" + c) or "(blank)") if base_section("IC 8-1-26-" + c) in BASES else 99, c))))
put(f, stat_block(ROWS, "S5. By year x base section", ["year", "base"], lambda r: (r["yr"], r["base"]),
                  [(y, b) for y in YEARS for b in BASES]))
put(f, stat_block(ROWS, "S6. By base section x respondent type", ["base", "resp"], lambda r: (r["base"], r["u"]),
                  [(b, u) for b in BASES for u in ("U", "N")]))
put(f, stat_block(ROWS, "S7. By year x base section x respondent type", ["year", "base", "resp"], lambda r: (r["yr"], r["base"], r["u"]),
                  [(y, b, u) for y in YEARS for b in BASES for u in ("U", "N")]))
put(f, stat_block(ROWS, "S8. By qualifier x respondent type (qualified cites only)", ["qual", "resp"], lambda r: (r["qual"], r["u"]),
                  [(q, u) for q in QUALS[1:] for u in ("U", "N")]))
put(f, stat_block(ROWS, "S9. By outcome class", ["outcome"], lambda r: r["oc"], OUTCOMES))

put(f, "## Outcome classes (what the recommendation text says)\n\n" + "\n".join("- **%s**: %s" % (o, OUTCOME_NAMES[o]) for o in OUTCOMES) + "\n\n")


def oc_table(title, keynames, keyf, keys):
    g = group(ROWS, keyf)
    body = []
    for k in keys:
        rs = g.get(k, [])
        if not rs:
            continue
        kk = k if isinstance(k, tuple) else (k,)
        c = Counter(r["oc"] for r in rs)
        s = defaultdict(int)
        for r in rs:
            s[r["oc"]] += r["hl"]
        body.append(list(kk) + [len(rs)] + ["%d/%d" % (c.get(o, 0), s.get(o, 0)) for o in OUTCOMES])
    return "### %s\n\n" % title + "Cells are count/sum_headline_$. Row n = all cases in the row.\n\n" + mdtable(keynames + ["n"] + OUTCOMES, body) + "\n"


put(f, oc_table("O1. Outcome mix by year", ["year"], lambda r: r["yr"], YEARS))
put(f, oc_table("O2. Outcome mix by base section", ["base"], lambda r: r["base"], BASES))
put(f, oc_table("O3. Outcome mix by respondent type", ["resp"], lambda r: r["u"], ["U", "N"]))
put(f, oc_table("O4. Outcome mix by year x respondent type", ["year", "resp"], lambda r: (r["yr"], r["u"]), [(y, u) for y in YEARS for u in "UN"]))
put(f, oc_table("O5. Outcome mix by base section x respondent type", ["base", "resp"], lambda r: (r["base"], r["u"]), [(b, u) for b in BASES for u in "UN"]))
put(f, oc_table("O6. Outcome mix by qualifier", ["qual"], lambda r: r["qual"], QUALS))

# recommendation text variants
put(f, "## R. Recommendation text variants (every distinct text with 3 or more cases; the rest pooled)\n\n"
       "Text shown trimmed to 100 characters. hl = headline parsed; oc = outcome class. Counts are all years.\n\n")
rc = Counter(r["recommendation"] for r in ROWS)
body = []
small = Counter()
for t, c in rc.most_common():
    if c >= 3:
        body.append([c, headline(t), outcome(t, headline(t)), "`" + (t[:100] or "(blank)") + "`"])
    else:
        small[(outcome(t, headline(t)))] += c
put(f, mdtable(["n", "hl", "oc", "text"], body) + "\n")
put(f, "Texts with fewer than 3 cases, pooled by outcome class: " + ", ".join("%s %d" % (o, small.get(o, 0)) for o in OUTCOMES)
    + ". Distinct recommendation texts in all: %d.\n\n" % len(rc))
# year x warning-text breakdown
put(f, "R2. Warning-letter special instructions (text after 'Special instructions:'), counts by year\n\n")
sp = Counter()
for r in ROWS:
    if r["oc"] == "W":
        m = re.search(r"special instructions:\s*(.*)", r["recommendation"], re.I)
        sp[(m.group(1).strip().casefold() if m else "(none)", r["yr"])] += 1
kinds = sorted({k for k, _ in sp}, key=lambda k: -sum(sp[(k, y)] for y in YEARS))
body = [[k] + [sp.get((k, y), 0) for y in YEARS] + [sum(sp.get((k, y), 0) for y in YEARS)] for k in kinds]
put(f, mdtable(["instruction"] + [str(y) for y in YEARS] + ["all"], body) + "\n")
# training/escalation mention by year x util
put(f, "R3. Text mentions by year x respondent type: cases whose recommendation text mentions training (any), mentions escalation/additional, has a note in additional_info\n\n")
body = []
for y in YEARS:
    for u in "UN":
        rs = [r for r in ROWS if r["yr"] == y and r["u"] == u]
        body.append([y, u, len(rs), sum(1 for r in rs if r["train"]), sum(1 for r in rs if r["esc"]), sum(1 for r in rs if r["additional_info"].strip())])
put(f, mdtable(["year", "resp", "n", "mentions_training", "mentions_escalation_or_additional", "has_note"], body) + "\n")

# ===================================================================== FILE 04: histograms
f = "04_histograms.md"
put(f, """# 04 Headline-penalty histograms (counts per dollar value)

Each row is a segment; columns are the distinct headline values in the data ($0, $100 ... $10000); a '.' is zero cases.
`n` = cases in the segment. With these you can count 'headline >= X' or '> X' by adding columns, find any median or
percentile by walking the cumulative counts, and compute a mean as sum(value x count)/n. Segments can be added across rows.

""")
vh = ["v%d" % v for v in VALUES]


def hist_table(title, keynames, keyf, keys):
    g = group(ROWS, keyf)
    body = []
    for k in keys:
        rs = g.get(k, [])
        if not rs:
            continue
        c = Counter(r["hl"] for r in rs)
        kk = k if isinstance(k, tuple) else (k,)
        body.append(list(kk) + [len(rs)] + [c[v] if c.get(v) else "." for v in VALUES])
    return "### %s\n\n" % title + mdtable(keynames + ["n"] + vh, body) + "\n"


put(f, hist_table("H0. All cases", ["all"], lambda r: "all", ["all"]))
put(f, hist_table("H1. By year", ["year"], lambda r: r["yr"], YEARS))
put(f, hist_table("H2. By base section", ["base"], lambda r: r["base"], BASES))
put(f, hist_table("H3. By respondent type", ["resp"], lambda r: r["u"], ["U", "N"]))
put(f, hist_table("H4. By year x respondent type", ["year", "resp"], lambda r: (r["yr"], r["u"]), [(y, u) for y in YEARS for u in "UN"]))
put(f, hist_table("H5. By year x base section x respondent type", ["year", "base", "resp"], lambda r: (r["yr"], r["base"], r["u"]),
                  [(y, b, u) for y in YEARS for b in BASES for u in "UN"]))
put(f, hist_table("H6. By base section x qualifier x respondent type (all years)", ["base", "qual", "resp"], lambda r: (r["base"], r["qual"], r["u"]),
                  [(b, q, u) for b in BASES for q in QUALS for u in "UN"]))
put(f, hist_table("H7. By outcome class", ["outcome"], lambda r: r["oc"], OUTCOMES))

# ===================================================================== FILE 05: respondents
f = "05_respondents_repeat.md"
put(f, """# 05 Who gets cited, and repeat names

A 'name' is the respondent text lower-cased, spaces collapsed, trailing '.' or ',' removed ('exact name'). Spelling variants
are NOT merged, so every repeat count is a floor (see the loose-name table T3 for a rough sensitivity check). Order of a
name's cases = by order date then page ('occurrence rank'). In the lists, 'cases by order year' = cases in 2021/2022/2023/2024/2025 order years.

""")
cnt_all = Counter(r["rn"] for r in ROWS)
cnt_u = Counter(r["rn"] for r in ROWS if r["u"] == "U")
cnt_n = Counter(r["rn"] for r in ROWS if r["u"] == "N")
scopes = [("all", cnt_all), ("N", cnt_n), ("U", cnt_u)]
# T1 thresholds
ks = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30, 40, 50, 75, 100]
put(f, "## T1. How many names have at least k cases (all years pooled)\n\nCells: names / cases covered by those names.\n\n")
body = []
for k in ks:
    row = [k]
    for nm, c in scopes:
        vs = [v for v in c.values() if v >= k]
        row.append("%d / %d" % (len(vs), sum(vs)))
    body.append(row)
put(f, mdtable(["k (>= k cases)", "all respondents: names / cases", "N: names / cases", "U: names / cases"], body) + "\n")
put(f, "T1b. Names with EXACTLY k cases (all years pooled)\n\n")
mx = 25
body = []
for k in list(range(1, mx + 1)):
    body.append([k] + [sum(1 for v in c.values() if v == k) for _, c in scopes])
body.append(["26+"] + [sum(1 for v in c.values() if v > mx) for _, c in scopes])
put(f, mdtable(["cases per name", "all", "N", "U"], body) + "\n")
put(f, "T1c. Within a single order year: names with at least k cases that year / cases covered (k = 1, 2, 3, 5, 10)\n\n")
body = []
for y in YEARS:
    for nm, flt in (("all", lambda r: True), ("N", lambda r: r["u"] == "N"), ("U", lambda r: r["u"] == "U")):
        c = Counter(r["rn"] for r in ROWS if r["yr"] == y and flt(r))
        body.append([y, nm] + ["%d / %d" % (sum(1 for v in c.values() if v >= k), sum(v for v in c.values() if v >= k)) for k in (1, 2, 3, 5, 10)])
put(f, mdtable(["year", "scope", "k>=1", "k>=2", "k>=3", "k>=5", "k>=10"], body) + "\n")

# T2 span in order years
put(f, "## T2. Names by number of distinct order years they appear in\n\n")
yrs_of = defaultdict(set)
for r in ROWS:
    yrs_of[r["rn"]].add(r["yr"])
body = []
for k in range(1, 6):
    body.append([k] + [sum(1 for n in c if len(yrs_of[n]) == k) for _, c in scopes])
put(f, mdtable(["distinct_order_years", "all", "N", "U"], body) + "\n")
ords_of = defaultdict(set)
for r in ROWS:
    ords_of[r["rn"]].add(r["order_file"])
put(f, "T2b. Names by number of distinct orders they appear in\n\n")
body = []
for k in (1, 2, 3, 4, 5, 6, 8, 10, 15, 20, 30):
    body.append(["%d+" % k] + [sum(1 for n in c if len(ords_of[n]) >= k) for _, c in scopes])
put(f, mdtable(["orders (at least)", "all", "N", "U"], body) + "\n")

# T3 loose names
put(f, "## T3. Sensitivity: 'loose' names (punctuation removed, corporate suffix words inc/llc/co/corp/company/lp/ltd/the/dba dropped)\n\n"
       "Merging obvious suffix/punctuation variants raises repeat counts. Cells: names / cases covered.\n\n")
lall = Counter(r["rl"] for r in ROWS)
ln = Counter(r["rl"] for r in ROWS if r["u"] == "N")
lu = Counter(r["rl"] for r in ROWS if r["u"] == "U")
body = []
for k in (1, 2, 3, 5, 10, 20):
    body.append([k] + ["%d / %d" % (sum(1 for v in c.values() if v >= k), sum(v for v in c.values() if v >= k)) for c in (lall, ln, lu)])
put(f, mdtable(["k (>= k cases)", "all", "N", "U"], body) + "\n")

# T4 rank
put(f, "## T4. Occurrence rank: the 1st, 2nd, 3rd ... case of the same exact name (by order date, then page)\n\n"
       "Rank 1 = the name's first case in the data (a name's first case may be a repeat of an earlier, un-parsed pre-2021 case; the data cannot see that).\n"
       "Cells: n / sum_headline / pos / W. mean = sum/n.\n\n")
ordr = sorted(ROWS, key=lambda r: (r["order_date"], r["order_file"], r["page"]))
seen = Counter()
for r in ordr:
    seen[r["rn"]] += 1
    r["rank"] = seen[r["rn"]]
r_pri = {}
# prior in strictly earlier order date
first_date = {}
for r in ordr:
    first_date.setdefault(r["rn"], r["order_date"])
for r in ROWS:
    r["prior_earlier_order"] = first_date[r["rn"]] < r["order_date"]


def rbin(k):
    return str(k) if k <= 5 else ("6-10" if k <= 10 else ("11-20" if k <= 20 else "21+"))


RB = ["1", "2", "3", "4", "5", "6-10", "11-20", "21+"]
for nm, flt in (("all respondents", lambda r: True), ("N non-utility", lambda r: r["u"] == "N"), ("U utility", lambda r: r["u"] == "U")):
    body = []
    for b in RB:
        rs = [r for r in ROWS if flt(r) and rbin(r["rank"]) == b]
        if rs:
            body.append([b, len(rs), sum(r["hl"] for r in rs), "%.1f" % (sum(r["hl"] for r in rs) / len(rs)), sum(1 for r in rs if r["hl"] > 0), sum(1 for r in rs if r["oc"] == "W")])
    put(f, "T4 - %s\n\n" % nm + mdtable(["rank", "n", "sum_hl", "mean_hl", "pos", "W"], body) + "\n")
put(f, "T4b. Non-utility cases by rank x base section (counts) - does a repeat name change section?\n\n")
body = []
for b in RB:
    body.append([b] + [sum(1 for r in ROWS if r["u"] == "N" and rbin(r["rank"]) == b and r["base"] == bs) for bs in BASES])
put(f, mdtable(["rank"] + BASES, body) + "\n")
put(f, "T4c. By order year x respondent type: cases whose name had an EARLIER case in a STRICTLY EARLIER order (prior_order), cases whose name had any earlier row (rank>=2, may be in same order), and first-ever (rank 1)\n\n")
body = []
for y in YEARS:
    for u in "UN":
        rs = [r for r in ROWS if r["yr"] == y and r["u"] == u]
        body.append([y, u, len(rs), sum(1 for r in rs if r["prior_earlier_order"]), sum(1 for r in rs if r["rank"] >= 2), sum(1 for r in rs if r["rank"] == 1)])
put(f, mdtable(["year", "resp", "cases", "name_seen_in_earlier_order", "rank>=2", "rank=1"], body) + "\n")

# Top lists
names_info = {}
by_name = group(ROWS, lambda r: r["rn"])


def name_row(n, rs=None):
    rs = by_name[n]
    yc = Counter(r["yr"] for r in rs)
    bc = Counter(r["base"] for r in rs)
    disp = Counter(r["respondent"].strip() for r in rs).most_common(1)[0][0]
    return [disp[:48].replace("|", "/"), rs[0]["u"], len(rs), sum(r["hl"] for r in rs), sum(1 for r in rs if r["hl"] > 0),
            "/".join(str(yc.get(y, 0)) for y in YEARS), len({r["order_file"] for r in rs}),
            "%s(%d)" % bc.most_common(1)[0]]


HEAD = ["name (as printed, most common form)", "resp", "n", "sum_hl", "pos", "cases by order year 21/22/23/24/25", "orders", "top_base(n)"]
# choose thresholds
thr_n = 4
lst = [n for n, c in cnt_n.most_common() if c >= thr_n]
put(f, "## T5. Non-utility names with at least %d cases (complete list; %d names), most cases first\n\n" % (thr_n, len(lst))
    + mdtable(HEAD, [name_row(n) for n in sorted(lst, key=lambda n: (-cnt_n[n], n))]) + "\n")
thr_u = 1
lst = [n for n, c in cnt_u.most_common() if c >= thr_u]
put(f, "## T6. Utility-respondent names (every exact name, at least %d case; %d names)\n\n" % (thr_u, len(lst))
    + mdtable(HEAD, [name_row(n) for n in sorted(lst, key=lambda n: (-cnt_u[n], n))]) + "\n")
# top by sum
put(f, "## T7. Top 30 non-utility names by total headline $ (ties by name)\n\n")
sums = {n: sum(r["hl"] for r in by_name[n]) for n in cnt_n}
lst = sorted(cnt_n, key=lambda n: (-sums[n], n))[:30]
put(f, mdtable(HEAD, [name_row(n) for n in lst]) + "\n")
# per-year top
put(f, "## T8. Per order year: top 12 names (all respondents) by cases that year, with ties at the cut included\n\n")
for y in YEARS:
    c = Counter(r["rn"] for r in ROWS if r["yr"] == y)
    top = c.most_common(12)
    cut = top[-1][1]
    keep = sorted([n for n, v in c.items() if v >= cut], key=lambda n: (-c[n], n))
    body = []
    for n in keep:
        rs = [r for r in by_name[n] if r["yr"] == y]
        body.append([by_name[n][0]["respondent"].strip()[:48].replace("|", "/"), rs[0]["u"], c[n], sum(r["hl"] for r in rs), sum(1 for r in rs if r["hl"] > 0)])
    put(f, "T8 - %d\n\n" % y + mdtable(["name", "resp", "cases_that_year", "sum_hl", "pos"], body) + "\n")

# T3b top loose names
put(f, "## T3b. Top 30 non-utility 'loose' names (variants merged) vs how many exact spellings they cover\n\n")
lg = group([r for r in ROWS if r["u"] == "N"], lambda r: r["rl"])
body = []
for k, rs in sorted(lg.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:30]:
    yc = Counter(r["yr"] for r in rs)
    body.append([k[:44], len(rs), len({r["rn"] for r in rs}), sum(r["hl"] for r in rs), "/".join(str(yc.get(y, 0)) for y in YEARS)])
put(f, mdtable(["loose name", "cases", "exact spellings", "sum_hl", "by order year 21/22/23/24/25"], body) + "\n")
# T4d gaps
put(f, "## T4d. Time between consecutive damages of the same exact name (non-utility, damage dates both parseable)\n\n"
       "Gap = days from this name's previous case's damage date to this case's damage date (cases sorted by damage date). 0 = same day.\n\n")
gaps = []
for n, rs in by_name.items():
    rs2 = sorted([r for r in rs if r["u"] == "N" and pdate(r["damage_date"])], key=lambda r: pdate(r["damage_date"]))
    for a, b in zip(rs2, rs2[1:]):
        gaps.append((pdate(b["damage_date"]) - pdate(a["damage_date"])).days)
gaps.sort()
gb = [("0", 0, 0), ("1-30", 1, 30), ("31-90", 31, 90), ("91-180", 91, 180), ("181-365", 181, 365), ("366-730", 366, 730), ("731+", 731, 10 ** 6)]
put(f, mdtable(["gap bucket (days)", "pairs"], [[l, sum(1 for g in gaps if lo <= g <= hi)] for l, lo, hi in gb] + [["all pairs", len(gaps)], ["median gap", statistics.median(gaps)], ["p25", nearest_rank(gaps, .25)], ["p75", nearest_rank(gaps, .75)]]) + "\n")
# T10 top names by base
put(f, "## T10. Top 8 names (all respondents) within each base section (ties at the cut included)\n\n")
for b in BASES[:-1]:
    c = Counter(r["rn"] for r in ROWS if r["base"] == b)
    top = c.most_common(8)
    cut = top[-1][1]
    keep = sorted([n for n, v in c.items() if v >= cut], key=lambda n: (-c[n], n))
    put(f, "T10 - %s\n\n" % b + mdtable(["name", "resp", "cases_in_section", "all_cases_of_name"], [[by_name[n][0]["respondent"].strip()[:48].replace("|", "/"), by_name[n][0]["u"], c[n], len(by_name[n])] for n in keep]) + "\n")

put(f, "## T8N. Per order year: top 12 NON-UTILITY names by cases that year (ties at the cut included)\n\n")
for y in YEARS:
    c = Counter(r["rn"] for r in ROWS if r["yr"] == y and r["u"] == "N")
    top = c.most_common(12)
    cut = top[-1][1]
    keep = sorted([n for n, v in c.items() if v >= cut], key=lambda n: (-c[n], n))
    body = []
    for n in keep:
        rs = [r for r in by_name[n] if r["yr"] == y]
        body.append([by_name[n][0]["respondent"].strip()[:48].replace("|", "/"), c[n], sum(r["hl"] for r in rs), sum(1 for r in rs if r["hl"] > 0)])
    put(f, "T8N - %d\n\n" % y + mdtable(["name", "cases_that_year", "sum_hl", "pos"], body) + "\n")
# concentration
put(f, "## T9. Concentration: share of cases from the k most frequent names (all respondents; N only)\n\n")
body = []
sa = sorted(cnt_all.values(), reverse=True)
sn = sorted(cnt_n.values(), reverse=True)
for k in (1, 2, 5, 10, 20, 50, 100, 200, 500):
    body.append([k, sum(sa[:k]), pct(sum(sa[:k]), N), sum(sn[:k]), pct(sum(sn[:k]), sum(sn))])
put(f, mdtable(["top k names", "cases (all)", "% of all cases", "cases (N)", "% of N cases"], body) + "\n")

# ===================================================================== FILE 06: respondent types, utility, other party
f = "06_utility_types_otherparty.md"
put(f, "# 06 Utility respondents by company, name-keyword types, and the other party\n\n")
put(f, "## U1. The 13 PREAMBLE utility prefixes: cases by prefix and order year\n\n")
body = []
for p in UTILITY_PREFIXES:
    rs = [r for r in ROWS if r["upre"] == p]
    body.append([p, len(rs)] + [sum(1 for r in rs if r["yr"] == y) for y in YEARS]
                + [sum(r["hl"] for r in rs), sum(1 for r in rs if r["hl"] > 0), sum(1 for r in rs if r["oc"] == "W"), len({r["rn"] for r in rs})])
rs = [r for r in ROWS if r["u"] == "U"]
body.append(["ALL utility", len(rs)] + [sum(1 for r in rs if r["yr"] == y) for y in YEARS] + [sum(r["hl"] for r in rs), sum(1 for r in rs if r["hl"] > 0), sum(1 for r in rs if r["oc"] == "W"), len({r["rn"] for r in rs})])
put(f, mdtable(["prefix", "cases"] + [str(y) for y in YEARS] + ["sum_hl", "pos", "W", "distinct_names"], body) + "\n")
put(f, "U2. Cases by prefix x base section\n\n")
body = []
for p in UTILITY_PREFIXES:
    rs = [r for r in ROWS if r["upre"] == p]
    if rs:
        body.append([p] + [sum(1 for r in rs if r["base"] == b) for b in BASES])
put(f, mdtable(["prefix"] + BASES, body) + "\n")
put(f, "U3. Cases by prefix x outcome class (count/sum_hl)\n\n")
body = []
for p in UTILITY_PREFIXES:
    rs = [r for r in ROWS if r["upre"] == p]
    if rs:
        body.append([p, len(rs)] + ["%d/%d" % (sum(1 for r in rs if r["oc"] == o), sum(r["hl"] for r in rs if r["oc"] == o)) for o in OUTCOMES])
put(f, mdtable(["prefix", "n"] + OUTCOMES, body) + "\n")
put(f, stat_block(ROWS, "U4. Headline statistics by prefix (utility respondents)", ["prefix"], lambda r: r["upre"], [p for p in UTILITY_PREFIXES if any(r["upre"] == p for r in ROWS)]))
put(f, "U5. Cases by prefix x qualifier\n\n")
body = []
for p in UTILITY_PREFIXES:
    rs = [r for r in ROWS if r["upre"] == p]
    if rs:
        body.append([p] + [sum(1 for r in rs if r["qual"] == q) for q in QUALS])
put(f, mdtable(["prefix"] + QUALS, body) + "\n")

put(f, """## N. Respondent 'type' by name keywords (a HEURISTIC of mine, not a PREAMBLE definition)

util = PREAMBLE utility prefix. Among the rest, first keyword match wins in this order: gov (city of, town of, county,
school, department, authority, district ...); telecom (telecom, communication, cable, fiber, broadband, wireless, telephone ...);
energy_water (gas, water, electric, energy, power, utility, REMC ... and no contractor word); contractor (construction, excavating,
contracting, plumbing, paving, concrete, boring, underground, landscaping, fence, electric, pipeline, services ...); other
(everything else, including most individuals and unrecognised company names). Treat shares as rough.

""")
body = []
for t in ["util"] + NAME_TYPES:
    rs = [r for r in ROWS if r["ntype"] == t]
    body.append([t, len(rs)] + [sum(1 for r in rs if r["yr"] == y) for y in YEARS] + [sum(r["hl"] for r in rs), sum(1 for r in rs if r["hl"] > 0), sum(1 for r in rs if r["oc"] == "W"), len({r["rn"] for r in rs})])
put(f, mdtable(["type", "cases"] + [str(y) for y in YEARS] + ["sum_hl", "pos", "W", "distinct_names"], body) + "\n")
put(f, "N2. Name type x base section (counts)\n\n")
body = [[t] + [sum(1 for r in ROWS if r["ntype"] == t and r["base"] == b) for b in BASES] for t in ["util"] + NAME_TYPES]
put(f, mdtable(["type"] + BASES, body) + "\n")
put(f, stat_block(ROWS, "N3. Headline statistics by name type", ["type"], lambda r: r["ntype"], ["util"] + NAME_TYPES))
put(f, "N4. Name type x outcome class (count/sum_hl)\n\n")
body = []
for t in ["util"] + NAME_TYPES:
    rs = [r for r in ROWS if r["ntype"] == t]
    body.append([t, len(rs)] + ["%d/%d" % (sum(1 for r in rs if r["oc"] == o), sum(r["hl"] for r in rs if r["oc"] == o)) for o in OUTCOMES])
put(f, mdtable(["type", "n"] + OUTCOMES, body) + "\n")
put(f, "N5. Examples: the 8 most frequent names in each non-utility type (to judge the heuristic)\n\n")
body = []
for t in NAME_TYPES:
    c = Counter(r["rn"] for r in ROWS if r["ntype"] == t)
    body.append([t, "; ".join("%s (%d)" % (by_name[n][0]["respondent"].strip()[:34].replace("|", "/"), v) for n, v in c.most_common(8))])
put(f, mdtable(["type", "top names"], body) + "\n")

put(f, "## P. The other party\n\nThe other party is not necessarily the excavator or the utility (SCHEMA.md). 'oU' = other_party starts with a PREAMBLE utility prefix, 'oN' = it does not, 'blank' = no other party printed.\n\n")


def optype(r):
    return "blank" if not r["other_party"].strip() else ("oU" if r["oupre"] else "oN")


body = []
for u in "UN":
    for o in ("oU", "oN", "blank"):
        rs = [r for r in ROWS if r["u"] == u and optype(r) == o]
        body.append([u, o, len(rs), sum(r["hl"] for r in rs), sum(1 for r in rs if r["hl"] > 0)] + [sum(1 for r in rs if r["base"] == b) for b in BASES])
put(f, mdtable(["resp", "other", "n", "sum_hl", "pos"] + BASES, body) + "\n")
put(f, "P2. Cases where respondent and other_party text are identical (case-insensitive): %d\n\n" % sum(1 for r in ROWS if r["respondent"].strip().casefold() == r["other_party"].strip().casefold()))
put(f, "P3. Top 25 other_party names (exact, normalised), all cases\n\n")
oc2 = Counter(norm_name(r["other_party"]) for r in ROWS if r["other_party"].strip())
body = []
for n, c in oc2.most_common(25):
    rs = [r for r in ROWS if norm_name(r["other_party"]) == n]
    body.append([rs[0]["other_party"].strip()[:48].replace("|", "/"), c, sum(1 for r in rs if r["u"] == "U"), sum(r["hl"] for r in rs)])
put(f, mdtable(["other_party", "cases", "of which resp is U", "sum_hl"], body) + "\n")
put(f, "P4. Cases where the other party is a PREAMBLE utility prefix, by prefix and year\n\n")
body = []
for p in UTILITY_PREFIXES:
    rs = [r for r in ROWS if r["oupre"] == p]
    if rs:
        body.append([p, len(rs)] + [sum(1 for r in rs if r["yr"] == y) for y in YEARS])
put(f, mdtable(["prefix", "cases"] + [str(y) for y in YEARS], body) + "\n")

# ===================================================================== FILE 07: places, committee, notes
f = "07_places_committee_notes.md"
put(f, "# 07 Places, abstentions, notes, scan pages\n\n")
cities = Counter(r["city"] for r in ROWS if r["city"])
put(f, "## L. Damage location: city (text after the last comma of damage_location, lower-cased)\n\n"
       "Distinct cities: %d. Rows with no city: %d. Top 60 cities (ties at the cut included); beyond that every city has fewer cases.\n\n"
    % (len(cities), sum(1 for r in ROWS if not r["city"])))
top = cities.most_common(60)
cut = top[-1][1]
keep = [c for c, v in cities.most_common() if v >= cut]
body = []
for c in keep:
    rs = [r for r in ROWS if r["city"] == c]
    body.append([c, len(rs), sum(1 for r in rs if r["u"] == "U"), sum(r["hl"] for r in rs), sum(1 for r in rs if r["hl"] > 0),
                 "/".join(str(sum(1 for r in rs if r["yr"] == y)) for y in YEARS)])
put(f, mdtable(["city", "cases", "U", "sum_hl", "pos", "by order year 21/22/23/24/25"], body) + "\n")
put(f, "L2. Cities by number of cases: how many cities have exactly k cases (k = 1..5), 6-10, 11-20, 21-50, 51+\n\n")
bk = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 10), (11, 20), (21, 50), (51, 10 ** 6)]
body = [["%d-%d" % (lo, hi) if hi < 10 ** 6 else "%d+" % lo, sum(1 for v in cities.values() if lo <= v <= hi), sum(v for v in cities.values() if lo <= v <= hi)] for lo, hi in bk]
put(f, mdtable(["cases per city", "cities", "cases"], body) + "\n")
put(f, "L3. Five largest cities: cases by base section\n\n")
body = []
for c, _ in cities.most_common(8):
    rs = [r for r in ROWS if r["city"] == c]
    body.append([c, len(rs)] + [sum(1 for r in rs if r["base"] == b) for b in BASES])
put(f, mdtable(["city", "n"] + BASES, body) + "\n")

put(f, "## M. Abstentions (committee members who abstained; blank = none printed)\n\n")
ab = Counter(r["abstentions"].strip() for r in ROWS)
body = []
for a, c in ab.most_common():
    body.append([a or "(blank)", c] + [sum(1 for r in ROWS if r["abstentions"].strip() == a and r["yr"] == y) for y in YEARS])
put(f, mdtable(["abstentions text", "cases"] + [str(y) for y in YEARS], body) + "\n")
put(f, "M2. Abstention (any, vs none) by respondent type and base: cases with any abstention text / all cases\n\n")
body = []
for u in "UN":
    body.append([u, len([r for r in ROWS if r["u"] == u and r["abstentions"].strip()]), len([r for r in ROWS if r["u"] == u])])
put(f, mdtable(["resp", "with abstention", "cases"], body) + "\n")

put(f, "## K. Notes (additional_info) and scan pages\n\n")
keys = ["reset", "window", "penalty schedule", "occupant", "trained", "escalat", "self", "no ticket", "history", "conceal"]
body = []
for k in keys:
    rs = [r for r in ROWS if k in r["additional_info"].casefold()]
    body.append([k, len(rs)] + [sum(1 for r in rs if r["yr"] == y) for y in YEARS])
rs = [r for r in ROWS if r["additional_info"].strip()]
body.append(["ANY note", len(rs)] + [sum(1 for r in rs if r["yr"] == y) for y in YEARS])
put(f, "Case-insensitive substring matches in additional_info; a note can match several keys.\n\n" + mdtable(["key", "cases"] + [str(y) for y in YEARS], body) + "\n")
put(f, "K2. Scan-page rows (OCR text; most field errors are here) by year and by order file\n\n")
body = [[y, sum(1 for r in ROWS if r["yr"] == y and r["scan"] == "yes")] for y in YEARS]
put(f, mdtable(["year", "scan rows"], body) + "\n")
body = [[o.replace("ord_", "").replace(".pdf", ""), c] for o, c in Counter(r["order_file"] for r in ROWS if r["scan"] == "yes").most_common()]
put(f, mdtable(["order with scan rows", "scan rows"], body) + "\n")
put(f, "K3. Headline statistics, scan vs typed pages\n\n")
put(f, stat_block(ROWS, "scan flag", ["scan"], lambda r: r["scan"]))

# ===================================================================== write
os.makedirs(OUT, exist_ok=True)
for fn in os.listdir(OUT):
    if fn.endswith(".md") and fn != "INDEX.md":
        os.remove(os.path.join(OUT, fn))
sizes = {}
for fn, parts in FILES.items():
    text = "".join(parts)
    with open(os.path.join(OUT, fn), "w", encoding="utf-8") as fh:
        fh.write(text)
    sizes[fn] = len(text.encode("utf-8"))
print("tables written:", sizes, "total bytes", sum(sizes.values()))

# ===================================================================== independent spot checks
def run_checks():
    errs = []
    con = sqlite3.connect(":memory:")
    con.execute("create table c(order_date text, violations text, recommendation text, respondent text, damage_date text)")
    with open(CSV, newline="", encoding="utf-8") as fh:
        rd = csv.reader(fh)
        hdr = next(rd)
        ix = {h: i for i, h in enumerate(hdr)}
        con.executemany("insert into c values (?,?,?,?,?)",
                        [(x[ix["order_date"]], x[ix["violations"]], x[ix["recommendation"]], x[ix["respondent"]], x[ix["damage_date"]]) for x in rd])

    # independent headline parser: character scan, no regex
    def hl2(s):
        i = s.find("$")
        if i < 0:
            return 0
        while i < len(s) and s[i] == "$":
            i += 1
        while i < len(s) and s[i] == " ":
            i += 1
        digs = ""
        while i < len(s):
            ch = s[i]
            if ch.isdigit():
                digs += ch
            elif ch == "," and i + 1 < len(s) and (s[i + 1].isdigit() or (s[i + 1] == " " and i + 2 < len(s) and s[i + 2].isdigit())):
                if s[i + 1] == " ":
                    i += 1
            else:
                break
            i += 1
        return int(digs) if digs else 0

    # independent base parser: split on "(" and keep tokens whose closing text is not a 2+ letter word
    def base2(c):
        c = c.strip()
        if c.startswith("IC 8-1-26-"):
            c = c[10:]
        parts = c.split("(")
        out = parts[0]
        for p in parts[1:]:
            inner, _, rest = p.partition(")")
            if len(inner) >= 2 and all(ch.isalpha() or ch == "-" for ch in inner) and inner[0].isalpha():
                out += rest
            else:
                out += "(" + inner + ")" + rest
        return out.strip()

    def util2(n):
        n = n.lstrip().lower()
        return n.startswith(tuple(p.lower() for p in UTILITY_PREFIXES))

    recs = con.execute("select order_date, violations, recommendation, respondent, damage_date from c").fetchall()

    def chk(label, a, b):
        ok = (a == b)
        print("CHECK %-70s table=%s independent=%s %s" % (label, a, b, "OK" if ok else "MISMATCH"))
        if not ok:
            errs.append(label)

    # 1 cases in year 2023 (table: year summary row) vs SQL
    t1 = sum(r[4] for r in CUBE_ROWS if r[0] == 2023)
    chk("cases, order year 2023 (cube sum vs SQL count)", t1, con.execute("select count(*) from c where substr(order_date,1,4)='2023'").fetchone()[0])
    # 2 cases 2022, base 16(h), non-utility (cube) vs independent
    t2 = sum(r[4] for r in CUBE_ROWS if r[0] == 2022 and r[1] == "16(h)" and r[3] == "N")
    chk("cases 2022 base 16(h) non-utility", t2, sum(1 for o, v, rec, rs, d in recs if o[:4] == "2022" and base2(v) == "16(h)" and not util2(rs)))
    # 3 total headline $ 2024 utility (cube) vs independent parser
    t3 = sum(r[5] for r in CUBE_ROWS if r[0] == 2024 and r[3] == "U")
    chk("sum headline $, 2024, utility respondents", t3, sum(hl2(rec) for o, v, rec, rs, d in recs if o[:4] == "2024" and util2(rs)))
    # 4 median headline of non-utility 2023 from histogram H4 path vs sorted list
    hist = Counter(hl2(rec) for o, v, rec, rs, d in recs if o[:4] == "2023" and not util2(rs))
    n = sum(hist.values())
    cum = 0
    med_hist = None
    for v in sorted(hist):
        cum += hist[v]
        if cum * 2 > n:
            med_hist = v
            break
    tab = [r for r in group(ROWS, lambda r: (r["yr"], r["u"]))[(2023, "N")]]
    sv = sorted(r["hl"] for r in tab)
    med_tab = statistics.median(sv)
    # n may be even; histogram walk gives the upper-middle; compare to the table value when middle values equal
    if n % 2 == 0:
        lo = None
        cum = 0
        for v in sorted(hist):
            cum += hist[v]
            if cum >= n // 2 and lo is None:
                lo = v
        med_hist = (lo + med_hist) / 2
    chk("median headline, 2023, non-utility (table stat vs histogram walk)", float(med_tab), float(med_hist))
    # 5 number of non-utility exact names with >= 5 cases vs sqlite group by
    rows_sql = con.execute("select respondent from c").fetchall()
    cn = Counter()
    for (rs,) in rows_sql:
        if not util2(rs):
            cn[" ".join(rs.split()).lower().rstrip(".,")] += 1
    chk("non-utility exact names with >=5 cases", sum(1 for v in cnt_n.values() if v >= 5), sum(1 for v in cn.values() if v >= 5))
    # 6 qualifier '(expire)' cases on 16(h) via SQL LIKE
    t6 = sum(r[4] for r in CUBE_ROWS if r[1] == "16(h)" and r[2] == "expire")
    chk("cases cite 16(h) with qualifier expire (cube vs SQL LIKE)", t6, con.execute("select count(*) from c where violations like 'IC 8-1-26-16(h)(expire)%'").fetchone()[0])
    # 7 headline-parse edge cases
    edge = {"$$1000": 1000, "$3, 500; no ticket escalation - additional $1,000 ($4,500)": 3500, "3000": 0, "Warning letter": 0, "$1,500, respondent can complete training instead of paying $1,500": 1500}
    for s, v in edge.items():
        chk("headline parse of %r" % s[:30], headline(s), v)
    # 8 qualifiers total per SCHEMA (1,902)
    chk("rows with a qualifier (cube vs independent count of '(' words)", sum(r[4] for r in CUBE_ROWS if r[2] != "-"),
        sum(1 for o, v, rec, rs, d in recs if base2(v) != v.strip().replace("IC 8-1-26-", "")))
    # 9 totals
    chk("grand total of cube n", sum(r[4] for r in CUBE_ROWS), len(recs))
    chk("grand total headline $ (cube vs independent parser)", sum(r[5] for r in CUBE_ROWS), sum(hl2(rec) for o, v, rec, rs, d in recs))
    return errs


# ===================================================================== worked-example numbers (hand route vs raw route)
def examples():
    out = {}
    # E1: 2023, base 20(a)(2), non-utility: cube rows summed by hand vs raw
    cells = [r for r in CUBE_ROWS if r[0] == 2023 and r[1] == "16(h)" and r[3] == "N"]
    n_h, s_h = sum(r[4] for r in cells), sum(r[5] for r in cells)
    raw = [r for r in ROWS if r["yr"] == 2023 and r["base"] == "16(h)" and r["u"] == "N"]
    assert (n_h, s_h) == (len(raw), sum(r["hl"] for r in raw))
    out["E1w"] = (sum(r[7] for r in cells), round(100.0 * sum(r[7] for r in cells) / n_h, 1), sum(r[6] for r in cells))
    out["E1"] = (n_h, s_h, round(s_h / n_h, 1), [(r[2], r[4], r[5]) for r in cells])
    # E2: 2024 N headline >= 4000 via histogram columns
    hc = Counter(r["hl"] for r in ROWS if r["yr"] == 2024 and r["u"] == "N")
    by_hist = sum(hc[v] for v in VALUES if v >= 4000)
    assert by_hist == sum(1 for r in ROWS if r["yr"] == 2024 and r["u"] == "N" and r["hl"] >= 4000)
    sv24 = sorted(r["hl"] for r in ROWS if r["yr"] == 2024 and r["u"] == "N")
    out["E2med"] = (statistics.median(sv24), len(sv24), pct(by_hist, len(sv24)))
    out["E2"] = (by_hist, sum(hc.values()), {v: hc[v] for v in VALUES if v >= 4000})
    # E3: N names >= 10
    vs = [v for v in cnt_n.values() if v >= 10]
    nN = sum(1 for r in ROWS if r["u"] == "N")
    lvs = [v for v in ln.values() if v >= 10]
    out["E3"] = (len(vs), sum(vs), nN, pct(sum(vs), nN), len(lvs), sum(lvs), pct(sum(lvs), nN))
    # E4: mean headline 2024 vs 2023 (all cases)
    m = {y: sum(r["hl"] for r in ROWS if r["yr"] == y) / sum(1 for r in ROWS if r["yr"] == y) for y in (2023, 2024)}
    a, b = round(m[2023], 1), round(m[2024], 1)  # the one-decimal means printed in table A2
    out["E4"] = (a, b, round(b - a, 1), round(b / a, 3))
    # E5: qualifier share by year
    out["E5"] = {y: (sum(1 for r in ROWS if r["yr"] == y and r["qual"] != "-"), sum(1 for r in ROWS if r["yr"] == y),
                     pct(sum(1 for r in ROWS if r["yr"] == y and r["qual"] != "-"), sum(1 for r in ROWS if r["yr"] == y))) for y in YEARS}
    # E6: damage-year x qualifier is not tabulated: raw answer for the can't-answer example
    out["E6"] = {q: sum(1 for r in ROWS if r["dy"] == 2022 and r["qual"] == q) for q in QUALS}
    out["E6b"] = sum(1 for r in ROWS if r["dy"] == 2022 and r["qual"] != "-")
    out["E6c"] = {q: sum(1 for r in ROWS if r["yr"] == 2022 and r["qual"] == q) for q in QUALS}
    # E6d: by-hand estimate of damage-2022 'expire' cases = sum over order years (damage-2022 cases in that order year x expire share of that order year)
    est = 0.0
    parts = []
    for y in YEARS:
        k = sum(1 for r in ROWS if r["dy"] == 2022 and r["yr"] == y)
        ex = sum(1 for r in ROWS if r["yr"] == y and r["qual"] == "expire")
        tot = sum(1 for r in ROWS if r["yr"] == y)
        if k:
            parts.append((y, k, ex, tot, round(100.0 * ex / tot, 1), round(k * ex / tot, 1)))
            est += k * ex / tot
    out["E6d"] = (parts, round(est, 1), sum(1 for r in ROWS if r["dy"] == 2022 and r["qual"] == "expire"))
    out["E8"] = (sum(1 for r in ROWS if r["hl"] > 0), len(ROWS), sum(1 for r in ROWS if r["hl"] > 0 and r["u"] == "U"), sum(1 for r in ROWS if r["u"] == "U"))
    # E7: utility share of 18(h)+18(j) cases in 2025 (cube hand route)
    cells = [r for r in CUBE_ROWS if r[0] == 2025 and r[1] in ("18(h)", "18(j)")]
    out["E7"] = (sum(r[4] for r in cells if r[3] == "U"), sum(r[4] for r in cells), sum(r[5] for r in cells if r[3] == "U"))
    return out


EX = examples()
for k, v in EX.items():
    print("EXAMPLE", k, v)

errs = run_checks()
if errs:
    print("SPOT CHECKS FAILED:", errs)
    sys.exit(1)
print("ALL SPOT CHECKS PASSED")
