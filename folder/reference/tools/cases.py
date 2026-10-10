#!/usr/bin/env python3
"""cases.py - general helper for reference/cases.csv (Indiana dig-damage enforcement cases).

Standard library only. No precomputed answers: every figure comes from running a command.
The definitions below follow the PREAMBLE text word for word (see README.md for the text itself):
  case = one row; year = year of order_date; cite/base section/qualifier; headline penalty;
  utility respondent (prefix test, ignoring case and leading spaces).

Usage (run from the folder root):
  python3 reference/tools/cases.py [--csv PATH] COMMAND [filters] [options]

Commands:
  fields                     list columns and derived fields
  count                      number of rows that pass the filters (with the denominator)
  group  --by F[,F2]         rows per group; add --stat F for n/sum/mean/median per group
  stat   --field F           n, sum, mean, median, min, max (and --pcts) of a numeric field
  distinct --field F         distinct values of a field with counts
  repeat --by F --min K      keys that occur at least K times (default F=respondent_norm)
  dupes                      duplicate (order_file, case_number) and multi-order case numbers
  receipts [--n N]           example rows (order_file, page, case_number, cite, penalty, respondent)
  test-parse "TEXT"          show how one cite / recommendation / respondent string is parsed

Filters (all combine with AND; every command takes them):
  --year Y[,Y2]  --base S[,S2]  --qual Q[,Q2]|none|any  --cite TEXT  --utility yes|no
  --penalty-min N --penalty-max N  --zero-penalty  --rec-contains TEXT  --respondent-contains TEXT
  --contains FIELD=TEXT  --eq FIELD=VALUE  --blank FIELD  --notblank FIELD  --scan yes|no
  --order-file NAME  --exclude-bad     (drops rows whose case_number is not 5 digits or whose cite is blank)
  --expr "PYTHON BOOLEAN EXPRESSION over r"   (r is a row dict with the derived fields; builtins limited)
"""
import argparse
import csv
import os
import re
import statistics
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(HERE, "..", "cases.csv")

# ---- PREAMBLE definitions -------------------------------------------------------------

UTILITY_PREFIXES = [
    "CenterPoint", "Northern Indiana Public Service", "NIPSCO", "Citizens Gas",
    "Citizens Energy", "Vectren", "Indiana American Water", "Ohio Valley Gas",
    "American Electric Power", "Duke Energy", "Community Natural Gas",
    "Midwest Natural Gas", "Frontier Communications",
]

CITE_PREFIX = "IC 8-1-26-"
# A parenthesized word is two or more letters (hyphens allowed). (h), (a)(2), (3)(b) are not.
_QUAL_RE = re.compile(r"\(([A-Za-z][A-Za-z-]+)\)")
# First dollar amount: one or more "$", digits with optional thousands commas (a space after a
# comma is ignored), optional decimals. A recommendation with no "$" amount has penalty 0.
_MONEY_RE = re.compile(r"\$+\s*(\d+(?:,\s?\d{3})*(?:\.\d+)?)")


def qualifier(cite):
    """The parenthesized word(s) of a cite ('' if none). Two qualifiers would be joined with '+'."""
    return "+".join(_QUAL_RE.findall(cite or ""))


def base_section(cite):
    """Cite without 'IC 8-1-26-' and without any parenthesized word."""
    s = (cite or "").strip()
    if s.startswith(CITE_PREFIX):
        s = s[len(CITE_PREFIX):]
    return _QUAL_RE.sub("", s).strip()


def headline_penalty(rec):
    """First dollar amount in the recommendation as printed; doubled '$' and a space after a
    thousands comma are ignored. No '$' amount -> 0.0. (Unconditional: 'Training or $5,000 if ...'
    has headline 5000 by this rule.)"""
    m = _MONEY_RE.search(rec or "")
    if not m:
        return 0.0
    return float(m.group(1).replace(",", "").replace(" ", ""))


def is_utility(respondent):
    """Respondent name, ignoring case and leading spaces, starts with one of UTILITY_PREFIXES."""
    s = (respondent or "").lstrip().casefold()
    return any(s.startswith(p.casefold()) for p in UTILITY_PREFIXES)


def order_year(row):
    return int(row["order_date"][:4])


def norm_name(name):
    """Display-safe grouping key: case-folded, whitespace collapsed, trailing . , stripped.
    Does NOT merge spelling variants or corporate suffixes (see rules.md)."""
    return re.sub(r"\s+", " ", (name or "").strip()).casefold().rstrip(".,")


def _date(s):
    from datetime import datetime
    for f in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime((s or "").strip(), f).date()
        except ValueError:
            pass
    return None


def city(location):
    loc = (location or "")
    return loc.rsplit(",", 1)[1].strip() if "," in loc else ""


def enrich(r):
    r["cite"] = r["violations"]
    r["base"] = base_section(r["violations"])
    r["qualifier"] = qualifier(r["violations"])
    r["headline"] = headline_penalty(r["recommendation"])
    r["utility"] = "yes" if is_utility(r["respondent"]) else "no"
    r["year"] = order_year(r)
    r["respondent_norm"] = norm_name(r["respondent"])
    r["other_party_norm"] = norm_name(r["other_party"])
    d = _date(r["damage_date"])
    o = _date(r["order_date"])
    r["damage_year"] = d.year if d else ""
    r["order_month"] = r["order_date"][:7]
    r["lag_days"] = (o - d).days if (d and o) else ""
    r["city"] = city(r["damage_location"])
    r["case_key"] = r["order_file"] + "|" + r["case_number"]
    return r


def load(path=None):
    path = path or DEFAULT_CSV
    with open(path, newline="", encoding="utf-8") as f:
        rows = [enrich(r) for r in csv.DictReader(f)]
    for r in rows:
        r["page"] = int(r["page"])
    return rows


# ---- filtering ------------------------------------------------------------------------

def _csvlist(s):
    return [x.strip() for x in s.split(",")] if s else []


def build_filter(a):
    desc = []
    preds = []
    if a.year:
        ys = {int(y) for y in _csvlist(a.year)}
        preds.append(lambda r: r["year"] in ys); desc.append("year in %s" % sorted(ys))
    if a.base:
        bs = set(_csvlist(a.base))
        preds.append(lambda r: r["base"] in bs); desc.append("base in %s" % sorted(bs))
    if a.qual:
        if a.qual == "none":
            preds.append(lambda r: r["qualifier"] == "")
        elif a.qual == "any":
            preds.append(lambda r: r["qualifier"] != "")
        else:
            qs = set(_csvlist(a.qual))
            preds.append(lambda r: r["qualifier"] in qs)
        desc.append("qualifier = %s" % a.qual)
    if a.cite:
        preds.append(lambda r: r["cite"] == a.cite); desc.append("cite == %r" % a.cite)
    if a.utility:
        preds.append(lambda r: r["utility"] == a.utility); desc.append("utility respondent = %s" % a.utility)
    if a.penalty_min is not None:
        preds.append(lambda r: r["headline"] >= a.penalty_min); desc.append("headline >= %g" % a.penalty_min)
    if a.penalty_max is not None:
        preds.append(lambda r: r["headline"] <= a.penalty_max); desc.append("headline <= %g" % a.penalty_max)
    if a.zero_penalty:
        preds.append(lambda r: r["headline"] == 0); desc.append("headline == 0")
    if a.rec_contains:
        t = a.rec_contains.casefold()
        preds.append(lambda r: t in r["recommendation"].casefold()); desc.append("recommendation contains %r (any case)" % a.rec_contains)
    if a.respondent_contains:
        t = a.respondent_contains.casefold()
        preds.append(lambda r: t in r["respondent"].casefold()); desc.append("respondent contains %r (any case)" % a.respondent_contains)
    for kv in a.contains or []:
        k, _, v = kv.partition("="); t = v.casefold()
        preds.append(lambda r, k=k, t=t: t in str(r.get(k, "")).casefold()); desc.append("%s contains %r (any case)" % (k, v))
    for kv in a.eq or []:
        k, _, v = kv.partition("=")
        preds.append(lambda r, k=k, v=v: str(r.get(k, "")) == v); desc.append("%s == %r" % (k, v))
    for k in a.blank or []:
        preds.append(lambda r, k=k: str(r.get(k, "")).strip() == ""); desc.append("%s is blank" % k)
    for k in a.notblank or []:
        preds.append(lambda r, k=k: str(r.get(k, "")).strip() != ""); desc.append("%s is not blank" % k)
    if a.scan:
        preds.append(lambda r: r["scan"] == a.scan); desc.append("scan == %s" % a.scan)
    if a.order_file:
        preds.append(lambda r: r["order_file"] == a.order_file); desc.append("order_file == %s" % a.order_file)
    if a.exclude_bad:
        preds.append(lambda r: re.fullmatch(r"\d{5}", r["case_number"]) is not None and r["cite"] != "")
        desc.append("exclude rows with non-5-digit case_number or blank cite")
    if a.expr:
        code = compile(a.expr, "<expr>", "eval")
        safe = {"len": len, "int": int, "float": float, "str": str, "abs": abs, "min": min, "max": max,
                "any": any, "all": all, "sum": sum, "set": set, "re": re}
        preds.append(lambda r: bool(eval(code, {"__builtins__": {}}, dict(safe, r=r)))); desc.append("expr: %s" % a.expr)
    return (lambda r: all(p(r) for p in preds)), desc


# ---- output helpers -------------------------------------------------------------------

def fmt(x):
    if isinstance(x, float):
        return ("%.2f" % x).rstrip("0").rstrip(".") if x != int(x) else "%d" % x
    return str(x)


def quantile(xs, q):
    """Linear interpolation between order statistics (same as Excel PERCENTILE.INC / numpy default)."""
    s = sorted(xs)
    if not s:
        return float("nan")
    pos = (len(s) - 1) * q
    lo = int(pos); hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def summarize(vals, pcts=None):
    out = [("n", len(vals))]
    if not vals:
        return out
    out += [("sum", sum(vals)), ("mean", sum(vals) / len(vals)), ("median", statistics.median(vals)),
            ("min", min(vals)), ("max", max(vals))]
    for p in pcts or []:
        out.append(("p%g" % p, quantile(vals, p / 100.0)))
    return out


def header(a, total, kept, desc):
    print("# csv rows: %d | filters: %s | rows kept: %d" % (total, "; ".join(desc) or "none", kept))


def row_line(r):
    return "%s p%d case %s | %s | rec=%r | headline=%s | resp=%r" % (
        r["order_file"], r["page"], r["case_number"], r["cite"], r["recommendation"][:70],
        fmt(r["headline"]), r["respondent"][:45])


def numeric(r, field):
    v = r.get(field, "")
    if v == "" or v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def print_receipts(rows, n):
    # spread across the sorted list so examples are not all from one order
    rows = sorted(rows, key=lambda r: (r["order_file"], r["page"]))
    if len(rows) <= n:
        pick = rows
    else:
        step = (len(rows) - 1) / float(max(n - 1, 1))
        pick = [rows[int(round(i * step))] for i in range(n)]
    for r in pick:
        print("    receipt: " + row_line(r))


def key_of(r, by):
    return tuple(str(r.get(f, "")) for f in by)


# ---- commands -------------------------------------------------------------------------

def cmd_fields(a, rows):
    print("columns + derived fields available to --by/--field/--eq/--contains/--expr:")
    print(", ".join(rows[0].keys()))
    print("derived: cite base qualifier headline utility year respondent_norm other_party_norm "
          "damage_year order_month lag_days city case_key")


def cmd_count(a, all_rows, rows, desc):
    header(a, len(all_rows), len(rows), desc)
    print("count = %d of %d rows (%.2f%%)" % (len(rows), len(all_rows), 100.0 * len(rows) / len(all_rows)))
    if a.distinct_key:
        print("distinct %s among kept rows = %d" % (a.distinct_key, len({r.get(a.distinct_key) for r in rows})))
    if a.receipts:
        print_receipts(rows, a.receipts)


def cmd_group(a, all_rows, rows, desc):
    header(a, len(all_rows), len(rows), desc)
    by = _csvlist(a.by)
    groups = defaultdict(list)
    for r in rows:
        groups[key_of(r, by)].append(r)
    items = list(groups.items())
    items.sort(key=(lambda kv: kv[0]) if a.sort == "key" else (lambda kv: (-len(kv[1]), kv[0])))
    if a.top:
        items = items[: a.top]
    print("group by %s: %d groups; denominator for shares = %d kept rows" % (",".join(by), len(groups), len(rows)))
    for k, rs in items:
        line = "%-40s n=%d (%.2f%%)" % ("|".join(k) or "(blank)", len(rs), 100.0 * len(rs) / max(len(rows), 1))
        if a.stat:
            vals = [numeric(r, a.stat) for r in rs]
            vals = [v for v in vals if v is not None]
            line += " | " + " ".join("%s=%s" % (n, fmt(v)) for n, v in summarize(vals, a.pcts_list)[1:])
            line += " (of %d values)" % len(vals)
        print(line)
        if a.receipts:
            print_receipts(rs, a.receipts)


def cmd_stat(a, all_rows, rows, desc):
    header(a, len(all_rows), len(rows), desc)
    vals = [numeric(r, a.field) for r in rows]
    missing = sum(1 for v in vals if v is None)
    vals = [v for v in vals if v is not None]
    print("field %s: values used = %d, missing/non-numeric skipped = %d" % (a.field, len(vals), missing))
    for n, v in summarize(vals, a.pcts_list):
        print("  %s = %s" % (n, fmt(v)))
    if a.field == "headline":
        print("  zero values (headline $0: warning letters, training-only, no $ amount) = %d" % sum(1 for v in vals if v == 0))
    if a.receipts and vals:
        mx = max(vals)
        print("  rows at the maximum (%s):" % fmt(mx))
        print_receipts([r for r in rows if numeric(r, a.field) == mx], a.receipts)


def cmd_distinct(a, all_rows, rows, desc):
    header(a, len(all_rows), len(rows), desc)
    c = Counter(str(r.get(a.field, "")) for r in rows)
    print("distinct %s: %d values" % (a.field, len(c)))
    for v, n in c.most_common(a.top or None):
        print("  %6d  %r" % (n, v))


def cmd_repeat(a, all_rows, rows, desc):
    header(a, len(all_rows), len(rows), desc)
    by = _csvlist(a.by or "respondent_norm")
    groups = defaultdict(list)
    for r in rows:
        groups[key_of(r, by)].append(r)
    rep = [(k, rs) for k, rs in groups.items() if len(rs) >= a.min and any(k)]
    rep.sort(key=lambda kv: (-len(kv[1]), kv[0]))
    print("keys (%s) with >= %d rows: %d of %d distinct keys; rows covered = %d of %d" % (
        ",".join(by), a.min, len(rep), len(groups), sum(len(rs) for _, rs in rep), len(rows)))
    print("note: keys are exact after case/space normalisation; spelling variants are NOT merged.")
    for k, rs in rep[: a.top or 25]:
        yrs = sorted({r["year"] for r in rs})
        print("%6d  %-50s order_years=%s orders=%d" % (len(rs), "|".join(k), yrs, len({r['order_file'] for r in rs})))
        if a.receipts:
            print_receipts(rs, a.receipts)


def cmd_dupes(a, all_rows, rows, desc):
    header(a, len(all_rows), len(rows), desc)
    pairs = defaultdict(list)
    nums = defaultdict(set)
    for r in rows:
        pairs[(r["order_file"], r["case_number"])].append(r)
        nums[r["case_number"]].add(r["order_file"])
    dp = {k: v for k, v in pairs.items() if len(v) > 1}
    multi = {k: v for k, v in nums.items() if len(v) > 1}
    print("(order_file, case_number) pairs on more than one page: %d pairs, %d rows" % (len(dp), sum(len(v) for v in dp.values())))
    for k, v in dp.items():
        print("   %s case %s pages %s" % (k[0], k[1], [r["page"] for r in v]))
    print("case_numbers that appear in more than one order file: %d (rows: %d)" % (
        len(multi), sum(1 for r in rows if r["case_number"] in multi)))
    if a.top:
        for k in sorted(multi)[: a.top]:
            print("   case %s in %s" % (k, sorted(multi[k])))


def cmd_receipts(a, all_rows, rows, desc):
    header(a, len(all_rows), len(rows), desc)
    print_receipts(rows, a.n)


def cmd_test_parse(a):
    s = a.text
    print("cite %r -> base=%r qualifier=%r" % (s, base_section(s), qualifier(s)))
    print("as recommendation -> headline_penalty=%s" % fmt(headline_penalty(s)))
    print("as respondent -> is_utility=%s" % is_utility(s))


def build_parser():
    p = argparse.ArgumentParser(description="Helper for reference/cases.csv", usage=(
        "cases.py [--csv PATH] {fields,count,group,stat,distinct,repeat,dupes,receipts,test-parse} "
        "[filters] [--by F] [--stat F] [--field F] [--receipts N] [--top N]"))
    p.add_argument("--csv")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--year"); sp.add_argument("--base"); sp.add_argument("--qual")
        sp.add_argument("--cite"); sp.add_argument("--utility", choices=["yes", "no"])
        sp.add_argument("--penalty-min", type=float); sp.add_argument("--penalty-max", type=float)
        sp.add_argument("--zero-penalty", action="store_true")
        sp.add_argument("--rec-contains"); sp.add_argument("--respondent-contains")
        sp.add_argument("--contains", action="append"); sp.add_argument("--eq", action="append")
        sp.add_argument("--blank", action="append"); sp.add_argument("--notblank", action="append")
        sp.add_argument("--scan", choices=["yes", "no"]); sp.add_argument("--order-file")
        sp.add_argument("--exclude-bad", action="store_true"); sp.add_argument("--expr")
        sp.add_argument("--receipts", type=int, default=0, help="print N example rows (per group)")
        sp.add_argument("--top", type=int, default=0)
        sp.add_argument("--pcts", default="", help="comma list of percentiles, e.g. 25,75,90")
    for name in ["fields", "count", "group", "stat", "distinct", "repeat", "dupes", "receipts"]:
        sp = sub.add_parser(name); common(sp)
        if name == "count":
            sp.add_argument("--distinct-key", help="also count distinct values of this field among kept rows")
        if name == "group":
            sp.add_argument("--by", required=True); sp.add_argument("--stat")
            sp.add_argument("--sort", choices=["count", "key"], default="count")
        if name in ("stat", "distinct"):
            sp.add_argument("--field", required=True)
        if name == "repeat":
            sp.add_argument("--by"); sp.add_argument("--min", type=int, default=2)
        if name == "receipts":
            sp.add_argument("--n", type=int, default=3)
    tp = sub.add_parser("test-parse"); tp.add_argument("text")
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    if a.cmd == "test-parse":
        return cmd_test_parse(a)
    a.pcts_list = [float(x) for x in _csvlist(getattr(a, "pcts", ""))]
    all_rows = load(a.csv)
    if a.cmd == "fields":
        return cmd_fields(a, all_rows)
    pred, desc = build_filter(a)
    rows = [r for r in all_rows if pred(r)]
    {"count": cmd_count, "group": cmd_group, "stat": cmd_stat, "distinct": cmd_distinct,
     "repeat": cmd_repeat, "dupes": cmd_dupes, "receipts": cmd_receipts}[a.cmd](a, all_rows, rows, desc)


if __name__ == "__main__":
    main()
