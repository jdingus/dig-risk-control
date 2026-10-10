# Independent cross-check of the held-out key: written by a separate agent (Claude Haiku 5.5) from the questions alone, without seeing key/.
# Paths made repo-relative when committed; logic unchanged.
import pathlib as _pl
import csv
import datetime
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP

CSV_PATH = str(_pl.Path(__file__).resolve().parents[2] / "data" / "cases_clean.csv")
OUT_PATH = str(_pl.Path(__file__).resolve().parent / "heldout_answers.json")

UTILITY_PREFIXES = [
    "CenterPoint", "Northern Indiana Public Service", "NIPSCO", "Citizens Gas",
    "Citizens Energy", "Vectren", "Indiana American Water", "Ohio Valley Gas",
    "American Electric Power", "Duke Energy", "Community Natural Gas",
    "Midwest Natural Gas", "Frontier Communications",
]


def pct(num, den, places="0.1"):
    return float((Decimal(num) * 100 / Decimal(den)).quantize(Decimal(places), rounding=ROUND_HALF_UP))


def headline(rec):
    # first "$" amount as printed; doubled "$" tolerated; spaces/commas inside the number removed
    m = re.search(r"\$+(\d+(?:,\s?\d{3})*)", rec)
    if not m:
        return 0
    return int(re.sub(r"[,\s]", "", m.group(1)))


def is_utility(name):
    n = name.lstrip(" ").lower()
    return any(n.startswith(p.lower()) for p in UTILITY_PREFIXES)


def qualifier(cite):
    m = re.search(r"\(([A-Za-z][A-Za-z-]+)\)$", cite)
    return m.group(1).lower() if m else None


def parse_damage(s):
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s.strip())
    if not m:
        return None
    try:
        return datetime.date(int(m[3]), int(m[1]), int(m[2]))
    except ValueError:
        return None


with open(CSV_PATH, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

for r in rows:
    r["_year"] = int(r["order_date"][:4])
    r["_head"] = headline(r["recommendation"])
    r["_util"] = is_utility(r["respondent"])

out = {}

# H1: city = text after last comma of damage location, stripped, lowercased
city_counts = Counter()
for r in rows:
    loc = r["damage_location"]
    if "," not in loc:
        continue
    city = loc.rsplit(",", 1)[1].strip().lower()
    if city:
        city_counts[city] += 1
with_city = sum(city_counts.values())
top = city_counts.most_common(6)
top5_sum = sum(c for _, c in city_counts.most_common(5))
out["H1"] = {
    "top_city": city_counts.most_common(1)[0][0],
    "top_city_cases": city_counts.most_common(1)[0][1],
    "cases_with_city": with_city,
    "top5_share_pct": pct(top5_sum, with_city),
    "top5": city_counts.most_common(5),
    "tie_at_5_6": top[4][1] == top[5][1] if len(top) > 5 else None,
    "tie_at_1_2": top[0][1] == top[1][1],
}

# H2: lag in days from damage date to order date (parseable damage dates only)
lag_by_year = defaultdict(list)
all_lags = []
for r in rows:
    d = parse_damage(r["damage_date"])
    if d is None:
        continue
    o = datetime.date.fromisoformat(r["order_date"])
    lag = (o - d).days
    all_lags.append(lag)
    lag_by_year[o.year].append(lag)


def mean_round(xs):
    return int((Decimal(sum(xs)) / Decimal(len(xs))).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


out["H2"] = {
    "mean_lag_2023": mean_round(lag_by_year[2023]),
    "mean_lag_2024": mean_round(lag_by_year[2024]),
    "n_2023": len(lag_by_year[2023]),
    "n_2024": len(lag_by_year[2024]),
    "n_parseable_all": len(all_lags),
    "pct_lag_gt_365": pct(sum(1 for x in all_lags if x > 365), len(all_lags)),
    "negative_lags": sum(1 for x in all_lags if x < 0),
}

# H3: recorded abstention = abstentions text left after stripping stray labels
STRAY = ["Additional Infonnation:", "Additional Information:"]


def has_abstention(text):
    t = text
    for s in STRAY:
        t = t.replace(s, "")
    return t.strip() != ""


h3 = {}
for y in (2021, 2024, 2025):
    ys = [r for r in rows if r["_year"] == y]
    h3[str(y)] = pct(sum(1 for r in ys if has_abstention(r["abstentions"])), len(ys))
out["H3"] = h3

# H4: qualifier outcomes, share with headline penalty $0
h4 = {}
for q in ("expire", "prior", "out"):
    qs = [r for r in rows if qualifier(r["violations"]) == q]
    h4[q] = {"n": len(qs), "pct_zero": pct(sum(1 for r in qs if r["_head"] == 0), len(qs))}
out["H4"] = h4

# H5: 2023 vs 2024 shift
h5 = {}
for y in (2023, 2024):
    ys = [r for r in rows if r["_year"] == y]
    nonutil = [r for r in ys if not r["_util"]]
    h5[str(y)] = {
        "n_all": len(ys),
        "n_nonutility": len(nonutil),
        "a_pct_nonutil_headline_ge_5000": pct(sum(1 for r in nonutil if r["_head"] >= 5000), len(nonutil)),
        "b_pct_all_utility": pct(sum(1 for r in ys if r["_util"]), len(ys)),
    }
out["H5"] = h5

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)
print(json.dumps(out, indent=2))
