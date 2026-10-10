#!/usr/bin/env python3
"""Answers for heldout-questions.md (H1-H5), computed from data/cases_clean.csv.
Stdlib only, deterministic. Paths are relative to the repo root (this file's parent's parent).
Rounding: round half up via Decimal."""
import csv, hashlib, json, re
from collections import Counter
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "cases_clean.csv"
OUT = ROOT / "key" / "heldout_answers.json"

UTIL = ["centerpoint", "northern indiana public service", "nipsco", "citizens gas",
        "citizens energy", "vectren", "indiana american water", "ohio valley gas",
        "american electric power", "duke energy", "community natural gas",
        "midwest natural gas", "frontier communications"]
QUALS = ("locator-error", "expire", "prior", "records", "out", "no-response", "other")


def rnd(x, places=0):
    q = Decimal(1).scaleb(-places)
    return float(Decimal(x).quantize(q, rounding=ROUND_HALF_UP)) if places else int(Decimal(x).quantize(q, rounding=ROUND_HALF_UP))


def pct(n, d, places=1):
    return rnd(Decimal(n) * 100 / Decimal(d), places)


def is_util(r):
    return r["respondent"].lstrip().lower().startswith(tuple(UTIL))


def headline(rec):
    m = re.search(r"\$+\s*(\d{1,3}(?:,\s?\d{3})+|\d+)", rec)
    return int(re.sub(r"[,\s]", "", m.group(1))) if m else 0


def qualifier(v):
    m = re.search(r"\((" + "|".join(QUALS) + r")\)\s*$", v.strip())
    return m.group(1) if m else None


rows = list(csv.DictReader(open(CSV, newline="", encoding="utf-8")))
sha = hashlib.sha256(CSV.read_bytes()).hexdigest()
for r in rows:
    r["year"] = r["order_date"][:4]
    r["hp"] = headline(r["recommendation"])
    r["util"] = is_util(r)
    r["qual"] = qualifier(r["violations"])

ans, notes, support = {}, {}, {}

# H1 geography
cities = Counter()
for r in rows:
    loc = r["damage_location"]
    if "," in loc:
        c = loc.rsplit(",", 1)[1].strip().lower()
        if c:
            cities[c] += 1
total_city = sum(cities.values())
top = cities.most_common(6)
top5 = sum(n for _, n in top[:5])
ans["H1"] = {"top_city": top[0][0], "top_city_cases": top[0][1],
             "top5_combined_percent": pct(top5, total_city)}
support["H1"] = {"cases_with_city": total_city, "top5_cases": top5, "top6": top,
                 "distinct_cities": len(cities)}
notes["H1"] = ("City = text after the last comma of damage_location, trimmed and lowercased, spelling variants not merged. "
               "Rows with no comma or an empty city are excluded from numerator and denominator. Rank 5 vs 6 is not a tie.")

# H2 lag
lags, bad = {}, 0
allv = []
for r in rows:
    try:
        d = datetime.strptime(r["damage_date"], "%m/%d/%Y").date()
    except ValueError:
        bad += 1
        continue
    l = (date.fromisoformat(r["order_date"]) - d).days
    lags.setdefault(r["year"], []).append(l)
    allv.append(l)
ans["H2"] = {"mean_lag_days_2023": rnd(Decimal(sum(lags["2023"])) / len(lags["2023"])),
             "mean_lag_days_2024": rnd(Decimal(sum(lags["2024"])) / len(lags["2024"])),
             "percent_lag_over_365_all_years": pct(sum(1 for l in allv if l > 365), len(allv))}
support["H2"] = {"n_2023": len(lags["2023"]), "n_2024": len(lags["2024"]), "n_all": len(allv),
                 "over_365": sum(1 for l in allv if l > 365), "unparseable_damage_date_rows": bad,
                 "negative_lags": sum(1 for l in allv if l < 0),
                 "exact_mean_2023": sum(lags["2023"]) / len(lags["2023"]),
                 "exact_mean_2024": sum(lags["2024"]) / len(lags["2024"])}
notes["H2"] = ("Lag = order_date minus damage_date in calendar days. Year = order year. Rows whose damage_date does not parse "
               "(1 blank row) are excluded. 'Over 365' means strictly more than 365 days.")

# H3 abstentions
ab = {}
for y in ("2021", "2024", "2025"):
    ys = [r for r in rows if r["year"] == y]
    k = sum(1 for r in ys if re.sub(r"additional\s+\w+:?", "", r["abstentions"], flags=re.I).strip())
    ab[y] = (k, len(ys))
ans["H3"] = {f"percent_with_abstention_{y}": pct(k, n) for y, (k, n) in ab.items()}
support["H3"] = {y: {"with_abstention": k, "cases": n} for y, (k, n) in ab.items()}
notes["H3"] = ("A case counts if abstentions has text left after trimming and after deleting any leaked label text "
               "'Additional Infonnation:' / 'Additional Information:' (2 rows, both 2021; one is label-only and is not counted, "
               "the other still has 'Smith').")

# H4 qualifiers
h4 = {}
sup4 = {}
for q in ("expire", "prior", "out"):
    g = [r for r in rows if r["qual"] == q]
    z = sum(1 for r in g if r["hp"] == 0)
    h4[f"percent_zero_penalty_{q}"] = pct(z, len(g))
    sup4[q] = {"cases": len(g), "zero_penalty": z}
ans["H4"] = h4
support["H4"] = sup4
notes["H4"] = "Qualifier is the parenthesized word at the end of the cite, any base section. Cases with no qualifier are not in any group."

# H5 shifts
nu = {}
for y in ("2023", "2024"):
    g = [r for r in rows if r["year"] == y and not r["util"]]
    nu[y] = (sum(1 for r in g if r["hp"] >= 5000), len(g))
ut = {}
for y in ("2023", "2024"):
    g = [r for r in rows if r["year"] == y]
    ut[y] = (sum(1 for r in g if r["util"]), len(g))
ans["H5"] = {"percent_nonutility_penalty_5000plus_2023": pct(*nu["2023"]),
             "percent_nonutility_penalty_5000plus_2024": pct(*nu["2024"]),
             "percent_utility_respondent_cases_2023": pct(*ut["2023"]),
             "percent_utility_respondent_cases_2024": pct(*ut["2024"])}
support["H5"] = {"nonutility_5000plus": nu, "utility_share": ut}
notes["H5"] = "Headline penalty and utility respondent per the preamble. 'At least $5,000' means headline penalty >= 5000. Denominators include $0 cases."

out = {"cases_clean_csv_sha256": sha, "rows": len(rows), "rounding": "half up (Decimal ROUND_HALF_UP)",
       "answers": ans, "interpretation_notes": notes, "supporting_counts": support}
OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(ans, indent=2))
