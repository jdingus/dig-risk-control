# Independent cross-check of Q1-Q10 from data/cases_clean.csv (stdlib only), revised wording.
# Independent cross-check: written by a separate agent (Claude Haiku 5.5) from questions.md alone, without seeing key/compute_answers.py.
# Does not read anything under the repo's key/ folder.
import csv, json, re
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP

import pathlib as _pl  # paths made repo-relative when committed; logic unchanged
_HERE = _pl.Path(__file__).resolve().parent
CSV_PATH = str(_HERE.parents[1] / "data" / "cases_clean.csv")
OUT_PATH = str(_HERE / "answers.json")

with open(CSV_PATH, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

UTILITY_PREFIXES = [
    "CenterPoint", "Northern Indiana Public Service", "NIPSCO", "Citizens Gas",
    "Citizens Energy", "Vectren", "Indiana American Water", "Ohio Valley Gas",
    "American Electric Power", "Duke Energy", "Community Natural Gas",
    "Midwest Natural Gas", "Frontier Communications",
]
FINAL_WORDS = {"inc", "llc", "co", "corp", "corporation", "company"}
PEN_RE = re.compile(r"\$+\s*(\d{1,3}(?:,\s?\d{3})+|\d+)(\.\d+)?")
QUAL_RE = re.compile(r"\(([A-Za-z][A-Za-z-]*[A-Za-z])\)")  # parenthesized word: 2+ letters, hyphens allowed


def half_up(x, places):
    return Decimal(x).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def pct(num, den, places=1):
    return half_up(Decimal(num) * 100 / Decimal(den), places)


def is_utility(name):
    n = name.lstrip().lower()
    return any(n.startswith(p.lower()) for p in UTILITY_PREFIXES)


def base_and_qual(cite):
    if not cite.strip():
        return "", ""
    assert cite.startswith("IC 8-1-26-"), cite
    s = cite[len("IC 8-1-26-"):]
    quals = QUAL_RE.findall(s)
    base = QUAL_RE.sub("", s).strip()
    return base, (quals[0] if quals else "")


def headline(rec):
    m = PEN_RE.search(rec)
    if not m:
        return Decimal(0)
    whole = m.group(1).replace(",", "").replace(" ", "")
    return Decimal(whole + (m.group(2) or ""))


def normalize_resp(name):
    s = name.lower()
    s = "".join(c for c in s if c.isalnum() or c == " ")  # delete everything else, no replacement
    toks = [t for t in s.split(" ") if t]                  # collapse spaces and trim
    if toks and toks[-1] in FINAL_WORDS:                   # once only
        toks.pop()
    return " ".join(toks)


for r in rows:
    r["year"] = int(r["order_date"][:4])
    r["base"], r["qual"] = base_and_qual(r["violations"])
    r["pen"] = headline(r["recommendation"])
    r["util"] = is_utility(r["respondent"])
    r["rec_l"] = r["recommendation"].lower()

N = len(rows)
nonutil = [r for r in rows if not r["util"]]
util = [r for r in rows if r["util"]]
out = {}

# Q1
b16 = sum(r["base"] == "16(h)" for r in rows)
b20 = sum(r["base"] == "20(a)(2)" for r in rows)
out["Q1"] = {"16(h)_pct": str(pct(b16, N)), "20(a)(2)_pct": str(pct(b20, N)),
             "counts": {"16(h)": b16, "20(a)(2)": b20, "total_cases": N}}

# Q2
per_year = {y: sum(r["year"] == y for r in rows) for y in range(2021, 2026)}
top = max(per_year.values())
out["Q2"] = {"per_year": per_year, "most_cases_year": [y for y, c in per_year.items() if c == top]}

# Q3 (mean, penalty > 0, nearest dollar half-up)
def mean_pen_base(base):
    vals = [r["pen"] for r in rows if r["base"] == base and r["pen"] > 0]
    return str(half_up(sum(vals) / len(vals), 0)), len(vals)
m16, n16 = mean_pen_base("16(h)")
m20, n20 = mean_pen_base("20(a)(2)")
out["Q3"] = {"16(h)_mean": m16, "16(h)_n": n16, "20(a)(2)_mean": m20, "20(a)(2)_n": n20}

# Q4
u_w = sum("warning letter" in r["rec_l"] for r in util)
n_w = sum("warning letter" in r["rec_l"] for r in nonutil)
out["Q4"] = {"utility_pct": str(pct(u_w, len(util))), "nonutility_pct": str(pct(n_w, len(nonutil))),
             "counts": {"utility": [u_w, len(util)], "nonutility": [n_w, len(nonutil)]}}

# Q5
pos = [r for r in rows if r["pen"] > 0]
tr_word = sum(bool(re.search(r"\btraining\b", r["rec_l"])) for r in pos)
out["Q5"] = {"pct": str(pct(tr_word, len(pos))), "counts": {"training": tr_word, "penalty_gt0": len(pos)}}

# Q6 (new normalization)
groups = defaultdict(int)
for r in nonutil:
    groups[normalize_resp(r["respondent"])] += 1
big = {k: v for k, v in groups.items() if v >= 5}
cases6 = sum(big.values())
out["Q6"] = {"distinct_respondents_5plus": len(big), "pct_of_nonutility": str(pct(cases6, len(nonutil))),
             "counts": {"cases_in_those": cases6, "nonutility_total": len(nonutil)},
             "top": sorted(big.items(), key=lambda kv: -kv[1])[:8]}

# Q7
def mean_pen(year):
    vals = [r["pen"] for r in nonutil if r["year"] == year]
    return str(half_up(sum(vals) / len(vals), 0)), len(vals)
m21, n21 = mean_pen(2021)
m25, n25 = mean_pen(2025)
out["Q7"] = {"2021_mean_dollars": m21, "2025_mean_dollars": m25, "counts": {"2021": n21, "2025": n25}}

# Q8
esc = [r for r in rows if "ticket escalation" in r["rec_l"]]
pc = Counter(str(r["pen"]) for r in esc).most_common()
out["Q8"] = {"count": len(esc), "most_common_headline": pc[0][0] if pc else None,
             "tied_modes": [k for k, v in pc if v == pc[0][1]] if pc else [], "distribution": pc}

# Q9
def other_key(s):
    return s.strip().lower()
oc = Counter(other_key(r["other_party"]) for r in nonutil if other_key(r["other_party"]))
best_key, best_n = oc.most_common(1)[0]
display = Counter(r["other_party"].strip() for r in nonutil if other_key(r["other_party"]) == best_key).most_common(1)[0][0]
out["Q9"] = {"other_party": display, "count": best_n, "pct_of_nonutility": str(pct(best_n, len(nonutil)))}

# Q10
b16rows = [r for r in rows if r["base"] == "16(h)"]
exp = sum(r["qual"] == "expire" for r in b16rows)
pri = sum(r["qual"] == "prior" for r in b16rows)
out["Q10"] = {"expire_pct": str(pct(exp, len(b16rows))), "prior_pct": str(pct(pri, len(b16rows))),
              "counts": {"16(h)_total": len(b16rows), "expire": exp, "prior": pri}}

out["_diagnostics"] = {
    "rows": N, "utility_rows": len(util), "nonutility_rows": len(nonutil),
    "base_values": Counter(r["base"] for r in rows).most_common(12),
    "duplicate_case_numbers": sum(1 for v in Counter(r["case_number"] for r in rows).values() if v > 1),
}
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, default=str, ensure_ascii=False)
print(json.dumps(out, indent=2, default=str, ensure_ascii=False))
