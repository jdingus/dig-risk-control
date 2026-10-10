"""Step 4: check the data and write VERIFY.md.

Usage (from the repo root):
  uv run -q --with pypdf --with pymupdf python -I data/scripts/verify.py
Exits 1 if any check fails (the report is still written).
"""
import csv
import datetime
import glob
import hashlib
import json
import os
import re
import sys
from pathlib import Path

DATA = str(Path(__file__).resolve().parents[1])
ORIG = os.path.join(DATA, "originals")
TEXT = os.path.join(DATA, "text")
EXPECTED_SCAN_YES = 182  # AUDIT.md, whole-set structural count
QUAL = re.compile(r"\([A-Za-z]{2}[A-Za-z-]*\)")  # a word qualifier such as (locator-error); not (a) or (l)
CASE_COLS = ["order_file", "order_date", "page", "case_number", "respondent", "other_party",
             "advisory_meeting_date", "damage_date", "damage_location", "violations",
             "recommendation", "abstentions", "additional_info", "scan"]
results = []  # (name, passed, detail)


def check(name, passed, detail):
    results.append((name, passed, detail))


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def is_case_page(page):
    if re.search(r"IN THE MATTER OF AN ORDER|ORDER OF THE COMMISSION", page):
        return False
    return bool(re.search(r"Case\s+Number\s*:|recommends\s+the\s+following\s+(?:civil\s+)?penalty|Recommendation\s+to\s+IURC",
                          page, re.I))


# 1. originals against SOURCES.csv
sources = read_csv(os.path.join(DATA, "SOURCES.csv"))
bad = []
for s in sources:
    path = os.path.join(DATA, s["file"])
    if not os.path.exists(path):
        bad.append(f"{s['file']} missing")
        continue
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    if digest != s["sha256"] or os.path.getsize(path) != int(s["bytes"]):
        bad.append(f"{s['file']} differs")
on_disk = {os.path.relpath(p, DATA) for p in glob.glob(os.path.join(ORIG, "**", "*.pdf"), recursive=True)}
listed = {s["file"] for s in sources}
if on_disk != listed:
    bad.append(f"files on disk vs SOURCES.csv differ: {sorted(on_disk ^ listed)}")
check("originals sha256 and size match SOURCES.csv", not bad,
      f"{len(sources)} files checked" + (": " + "; ".join(bad) if bad else ""))

# 2. rows point at real order files and pages
cases = read_csv(os.path.join(DATA, "cases.csv"))
dropped = read_csv(os.path.join(DATA, "dropped.csv"))
pages_in_text = {}
for txt in glob.glob(os.path.join(TEXT, "*.txt")):
    raw = open(txt, encoding="utf-8").read()
    nums = {int(n) for n in re.findall(r"^=== page (\d+)$", raw, flags=re.M)}
    pages_in_text[os.path.basename(txt)[:-4] + ".pdf"] = (nums, raw)
missing = []
for r in cases + dropped:
    info = pages_in_text.get(r["order_file"])
    if info is None or int(r["page"]) not in info[0]:
        missing.append((r["order_file"], r["page"]))
check("every row's order_file and page exist in the originals text", not missing,
      f"{len(cases) + len(dropped)} rows checked" + (f"; missing: {missing[:5]}" if missing else ""))

# 3. total case pages = rows + dropped rows
case_pages = 0
for name, (nums, raw) in pages_in_text.items():
    parts = re.split(r"^=== page (\d+)\n", raw, flags=re.M)
    for i in range(1, len(parts), 2):
        if is_case_page(parts[i + 1]):
            case_pages += 1
check("total case pages = cases.csv rows + dropped.csv rows", case_pages == len(cases) + len(dropped),
      f"case pages {case_pages}; rows {len(cases)} + dropped {len(dropped)} = {len(cases) + len(dropped)}")

# 4. no duplicate (order_file, page)
keys = [(r["order_file"], r["page"]) for r in cases + dropped]
dups = len(keys) - len(set(keys))
check("no duplicate (order_file, page) across cases.csv and dropped.csv", dups == 0, f"duplicates: {dups}")

# 5. empty-field counts
empty = {c: sum(1 for r in cases if not r[c]) for c in CASE_COLS}
check("column header matches the spec", list(cases[0].keys()) == CASE_COLS, "cases.csv columns checked")

# 6. violation qualifiers and scan count
with_qual = sum(1 for r in cases if QUAL.search(r["violations"]))
scan_yes = sum(1 for r in cases if r["scan"] == "yes")
check(f"scan=yes count equals the AUDIT.md expectation ({EXPECTED_SCAN_YES})", scan_yes == EXPECTED_SCAN_YES,
      f"scan=yes: {scan_yes}")

# 7. cases_clean.csv is cases.csv plus the ledger and nothing else
ledger = read_csv(os.path.join(DATA, "corrections.csv"))
clean = read_csv(os.path.join(DATA, "cases_clean.csv"))
expected = {}
for e in ledger:
    expected[(e["order_file"], e["page"], e["field"])] = e["new_value"]
stray = []
same_shape = len(clean) == len(cases)
if same_shape:
    for a, b in zip(cases, clean):
        for c in CASE_COLS:
            want = expected.get((a["order_file"], a["page"], c), a[c])
            if b[c] != want:
                stray.append((a["order_file"], a["page"], c))
check("cases_clean.csv equals cases.csv with the ledger applied, and nothing else",
      same_shape and not stray and len(expected) == len(ledger),
      f"corrections: {len(ledger)}; cases_clean rows: {len(clean)}; cells that differ from cases.csv plus ledger: {len(stray)}")

# 7b. ledger rows carry evidence that exists in the repo and a checker
bad_ev = [e["evidence"] for e in ledger
          if not e["evidence"] or not os.path.exists(os.path.join(DATA, "..", e["evidence"])) or not e["checked_by"]]
check("every ledger row has an existing evidence file and a checked_by", not bad_ev,
      f"{len(ledger)} ledger rows checked" + (f"; bad: {bad_ev[:3]}" if bad_ev else ""))

# 8. cases_clean.csv against schema.json
with open(os.path.join(DATA, "schema.json"), encoding="utf-8") as f:
    SCHEMA = json.load(f)
check("schema.json columns match the cases.csv header", [c["name"] for c in SCHEMA["columns"]] == CASE_COLS,
      f"{len(SCHEMA['columns'])} columns in schema.json")
findings = {}   # (column, rule) -> list of (order_file, page)
required_fail = set()  # columns with a required-rule violation


def finding(col, rule, row, required):
    findings.setdefault((col, rule), []).append((row["order_file"], row["page"]))
    if required:
        required_fail.add(col)


for row in clean:
    for col in SCHEMA["columns"]:
        name, v = col["name"], row[col["name"]]
        req = col["required"]
        if v == "":
            if not col["nullable"]:
                finding(name, "empty but not nullable", row, req)
            continue
        if "pattern" in col and not re.fullmatch(col["pattern"], v):
            finding(name, "pattern", row, req)
            continue
        if col["type"] == "enum" and v not in col["values"]:
            finding(name, "enum", row, req)
        elif col["type"] == "int":
            if int(v) < col.get("min", 0):
                finding(name, "below min", row, req)
        elif col["type"] == "date":
            try:
                datetime.datetime.strptime(v, col["format"])
            except ValueError:
                finding(name, "not a real date", row, req)
        for ch in col.get("checks", []):
            if re.search(ch["not_pattern"], v):
                finding(name, ch["name"], row, req)
for key in SCHEMA["keys"]:
    seen = {}
    for row in clean:
        seen.setdefault(tuple(row[c] for c in key["columns"]), []).append((row["order_file"], row["page"]))
    for k, where in seen.items():
        if len(where) > 1:
            for w in where:
                findings.setdefault(("(key " + key["name"] + ")", "duplicate key"), []).append(w)
            if key["required"]:
                required_fail.add("(key " + key["name"] + ")")
check("cases_clean.csv: required schema columns and keys have no violation", not required_fail,
      "required violations: " + (", ".join(sorted(required_fail)) if required_fail else "none")
      + f"; findings (non-required): {sum(len(v) for v in findings.values())} cells in "
      f"{len({k[0] for k in findings})} columns, see Schema findings")

# write VERIFY.md
failed = [r for r in results if not r[1]]
lines = ["# VERIFY: round2 data", "",
         "Generated by `scripts/verify.py`. Each row is one check.", "",
         "| check | result | detail |", "|---|---|---|"]
for name, ok, detail in results:
    lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {detail} |")
lines += ["", "## Counts", "",
          f"- cases.csv rows: {len(cases)}",
          f"- dropped.csv rows: {len(dropped)}",
          f"- scan=yes: {scan_yes}",
          f"- violations with a word qualifier (e.g. locator-error, no-response, expire, prior, records, out, other): {with_qual}",
          f"- corrections applied: {len(ledger)}", "",
          "## Empty fields per column (cases.csv)", "",
          "| column | empty rows |", "|---|---|"]
for c in CASE_COLS:
    lines.append(f"| {c} | {empty[c]} |")
lines += ["", "## Schema findings (cases_clean.csv against schema.json)", "",
          "A finding is a value that breaks a schema rule where the column is not marked required. "
          "It is reported, not fixed here. Rows per column count each row once. "
          "Examples are order_file page.", ""]
if findings:
    lines += ["| column | rows with a finding | rule | rows | examples |", "|---|---|---|---|---|"]
    by_col = {}
    for (c, rule), where in findings.items():
        by_col.setdefault(c, []).append((rule, where))
    order = {c: i for i, c in enumerate(CASE_COLS)}
    for c in sorted(by_col, key=lambda x: order.get(x, 99)):
        distinct_rows = len({w for _, where in by_col[c] for w in where})
        for rule, where in sorted(by_col[c]):
            ex = ", ".join(f"{o[:-4]} p{p}" for o, p in where[:3])
            lines.append(f"| {c} | {distinct_rows} | {rule} | {len(where)} | {ex}{', ...' if len(where) > 3 else ''} |")
else:
    lines.append("No findings.")
lines.append("")
with open(os.path.join(DATA, "VERIFY.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
for name, ok, detail in results:
    print(("PASS" if ok else "FAIL"), name, "-", detail)
print("rows", len(cases), "dropped", len(dropped), "scan_yes", scan_yes, "with_qualifier", with_qual)
sys.exit(1 if failed else 0)
