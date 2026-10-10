"""Step 3: apply corrections.csv to cases.csv and write cases_clean.csv.

Usage (from the repo root):
  uv run -q --with pypdf --with pymupdf python -I data/scripts/apply_corrections.py
Every ledger row must name an existing (order_file, page, case_number) row,
an existing column, and an old_value equal to the value at that point.
Anything else stops the script with an error and writes nothing.
"""
import csv
import os
from pathlib import Path

DATA = str(Path(__file__).resolve().parents[1])
CASES = os.path.join(DATA, "cases.csv")
LEDGER = os.path.join(DATA, "corrections.csv")
OUT = os.path.join(DATA, "cases_clean.csv")
LEDGER_FIELDS = ["order_file", "page", "case_number", "field", "old_value", "new_value", "evidence", "checked_by"]


def main():
    with open(CASES, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
    index = {(r["order_file"], r["page"]): r for r in rows}
    with open(LEDGER, newline="", encoding="utf-8") as f:
        ledger = csv.DictReader(f)
        if ledger.fieldnames != LEDGER_FIELDS:
            raise SystemExit(f"corrections.csv header must be {LEDGER_FIELDS}, got {ledger.fieldnames}")
        entries = list(ledger)
    applied = 0
    for n, e in enumerate(entries, 2):  # line 2 is the first data line
        row = index.get((e["order_file"], e["page"]))
        if row is None:
            raise SystemExit(f"corrections.csv line {n}: no case row for {e['order_file']} page {e['page']}")
        if row["case_number"] != e["case_number"]:
            raise SystemExit(f"corrections.csv line {n}: case_number {e['case_number']} does not match {row['case_number']}")
        if e["field"] not in fields or e["field"] in ("order_file", "page", "order_date"):
            raise SystemExit(f"corrections.csv line {n}: field {e['field']!r} is not an editable column")
        if row[e["field"]] != e["old_value"]:
            raise SystemExit(f"corrections.csv line {n}: old_value {e['old_value']!r} does not match current {row[e['field']]!r}")
        row[e["field"]] = e["new_value"]
        applied += 1
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"{applied} corrections applied; {len(rows)} rows written to {OUT}")


if __name__ == "__main__":
    main()
