"""Step 2: parse text/ into cases.csv, dropped.csv (blank template pages).

Usage (from the repo root):
  uv run -q --with pypdf --with pymupdf python -I data/scripts/parse.py

Writes data/cases.csv and data/dropped.csv.
Values are kept as printed. The only change to a value is joining the
lines of a value that wraps (respondent, other_party, damage_location),
and violation cites keep their qualifiers. No other normalising or
correcting happens here; OCR errors stay in place (see corrections.csv).
"""
import csv
import datetime
import glob
import os
import re
from pathlib import Path

import pymupdf

DATA = Path(__file__).resolve().parents[1]
PDF_DIR, TEXT_DIR, OUT_DIR = DATA / "originals" / "orders", DATA / "text", DATA

FIELDS = ["order_file", "order_date", "page", "case_number", "respondent", "other_party",
          "advisory_meeting_date", "damage_date", "damage_location", "violations",
          "recommendation", "abstentions", "additional_info", "scan"]
DROP_FIELDS = ["order_file", "page", "reason"]

LABEL_RE = {
    "respondent": r"Respondent\s*:",
    "other_party": r"Other\s+Party\s*:",
    "case_number": r"Case\s+Number\s*:",
    "advisory_meeting_date": r"Date\s+of\s+Advisory\s+Meeting\s*:",
    "damage_date": r"Date\s+of\s+Damage\s*:",
    "damage_location": r"Damage\s+Location\s*:",
}
LABEL_LINE = re.compile(
    r"^(?:Respondent|Other\s+Party|Case\s+Number|Date\s+of\s+Advisory\s+Meeting|Date\s+of\s+Damage|Damage\s+Location)\s*:")
# lines that start a new block, so they can never be the second line of a wrapped value
BOUNDARY = re.compile(
    r"^(?:Respondent|Other\s+Party|Case\s+Number|Date\s+of|Damage\s+Location|The\s+(?:IURC|Advisory)|"
    r"Recommendation|Abstentions|Additional|APPROVED|IC\s?8|\$|\d+_Recommendation)", re.I)
CITE = re.compile(r"IC\s?8\s?-\s?[1lI]\s?-\s?26\s?-\s?[0-9A-Za-z]+(?:\([^()\s]+\))*")


def collapse(s):
    return re.sub(r"\s+", " ", s).strip()


def real_date(name):
    m = re.match(r"ord_PSD(?:NPT)?_(\d{2})\.(\d{2})\.(\d{2})\.pdf$", name)
    if not m:
        m = re.match(r"ord_PSD(?:NPT)?_(\d{2})(\d{2})(\d{2})\.pdf$", name)
    if not m:
        return ""
    mm, dd, yy = (int(x) for x in m.groups())
    return datetime.date(2000 + yy, mm, dd).isoformat()


TEXT_KEYS = ("respondent", "other_party", "damage_location")  # the only fields that wrap
DATE_RE = re.compile(r"\d{1,2}/\d{1,2}/\d{2,4}")


def field_value(lines, key):
    """Printed value after the label, plus wrapped continuation lines (text fields only).

    Returns (value, consumed line indexes). The value is "" when the label line is empty
    (label-first scan layout), or when the printed value has no word characters."""
    pat = re.compile(LABEL_RE[key], re.I)
    for i, line in enumerate(lines):
        m = pat.search(line)
        if not m:
            continue
        value = collapse(line[m.end():])
        consumed = set()
        if not value:
            return "", consumed
        if key in TEXT_KEYS:
            j = i + 1
            while j < len(lines):
                nxt = lines[j].strip()
                if not nxt or BOUNDARY.match(nxt) or LABEL_LINE.match(nxt):
                    break
                value = value + " " + collapse(nxt)
                consumed.add(j)
                j += 1
        return (value if re.search(r"\w", value) else ""), consumed
    return "", set()


def orphan_values(lines, consumed):
    """Label-first layout (scans): bare value lines printed after the labels, not used as wraps."""
    start = next((i for i, l in enumerate(lines) if re.match(r"Respondent\s*:", l.strip())), None)
    if start is None:
        return []
    out = []
    for j in range(start + 1, len(lines)):
        s = lines[j].strip()
        if re.match(r"The\s+(IURC|Advisory)", s):
            break
        if s and j not in consumed and not LABEL_LINE.match(s):
            out.append(collapse(s))
    return out


def date_of(v):
    """Date fields: the date when one is printed (drops label text that OCR put on the same line), else the printed value."""
    m = DATE_RE.search(v)
    return m.group(0) if m else v


def is_case_page(page):
    if re.search(r"IN THE MATTER OF AN ORDER|ORDER OF THE COMMISSION", page):
        return False
    return bool(re.search(r"Case\s+Number\s*:|recommends\s+the\s+following\s+(?:civil\s+)?penalty|Recommendation\s+to\s+IURC",
                          page, re.I))


def parse_page(page, order_file, pno):
    lines = page.split("\n")
    flat = collapse(page)
    row = {"order_file": order_file, "order_date": real_date(order_file), "page": pno}
    vals, consumed = {}, set()
    for k in LABEL_RE:
        vals[k], used = field_value(lines, k)
        consumed |= used
    if any(not vals[k] for k in LABEL_RE) and any(re.match(r"Respondent\s*:", l.strip()) for l in lines):
        orph = orphan_values(lines, consumed)
        if orph:
            if not vals["case_number"]:
                c = next((o for o in orph if re.fullmatch(r"\d{3,7}", o)), "")
                if c:
                    vals["case_number"] = c
                    orph.remove(c)
            dates = [o for o in orph if DATE_RE.search(o)]
            for k, d in zip([k for k in ("advisory_meeting_date", "damage_date") if not vals[k]], dates):
                vals[k] = d
                orph.remove(d)
            text_fields = [k for k in ("respondent", "other_party", "damage_location") if not vals[k]]
            if text_fields and orph:
                if len(orph) > len(text_fields):  # wrapped name/address line: merge the surplus into the first value
                    k = len(orph) - len(text_fields)
                    orph = [" ".join(orph[:k + 1])] + orph[k + 1:]
                for k, v in zip(text_fields, orph):
                    vals[k] = v
    for k in LABEL_RE:
        row[k] = vals[k]
    row["advisory_meeting_date"] = date_of(vals["advisory_meeting_date"]) if vals["advisory_meeting_date"] else ""
    row["damage_date"] = date_of(vals["damage_date"]) if vals["damage_date"] else ""
    # violations: cites inside the block between the 'violation(s):' heading and the recommendation
    cites = []
    vm = re.search(r"violations?\s*(?:\(\s*s?\s*\))?\s*:", flat, re.I)
    if vm:
        rest = flat[vm.end():]
        end = re.search(r"recommends", rest, re.I)
        block = rest[:end.start()] if end else rest
        cites = CITE.findall(block)
    row["violations"] = "; ".join(cites)
    m = re.search(r"recommends\s+the\s+following\s+(?:civil\s+)?penalty\s*:?(.*?)Abstentions", flat, re.I)
    row["recommendation"] = m.group(1).strip() if m else ""
    m = re.search(r"Abstentions\s*:(.*?)(?:Additional\s+Information\s*:|APPROVED\s*:|$)", flat, re.I)
    row["abstentions"] = m.group(1).strip() if m else ""
    m = re.search(r"Additional\s+Information\s*:(.*?)(?:APPROVED\s*:|$)", flat, re.I)
    row["additional_info"] = m.group(1).strip() if m else ""
    return row


def big_image_pages(pdf_path):
    """Map page number -> share of the page covered by its largest embedded image."""
    out = {}
    doc = pymupdf.open(pdf_path)
    for i, pg in enumerate(doc, 1):
        R = pg.rect
        area = R.width * R.height
        big = 0.0
        for im in pg.get_image_info():
            b = pymupdf.Rect(im["bbox"])
            big = max(big, (b & R).get_area() / area)
        out[i] = big
    doc.close()
    return out


rows, dropped = [], []
for txt_path in sorted(glob.glob(os.path.join(TEXT_DIR, "*.txt"))):
    name = os.path.basename(txt_path)[:-4] + ".pdf"
    raw = open(txt_path, encoding="utf-8").read()
    parts = re.split(r"^=== page (\d+)\n", raw, flags=re.M)
    pages = [(int(parts[i]), parts[i + 1]) for i in range(1, len(parts), 2)]
    img = big_image_pages(os.path.join(PDF_DIR, name))
    for pno, body in pages:
        if not is_case_page(body):
            continue
        row = parse_page(body, name, pno)
        row["scan"] = "yes" if img.get(pno, 0) > 0.6 else "no"
        blank = not any(row[k] for k in ("case_number", "respondent", "other_party", "advisory_meeting_date",
                                         "damage_date", "damage_location", "violations"))
        if blank:
            dropped.append({"order_file": name, "page": pno,
                            "reason": "blank Recommendation Form template: no case number, parties, dates, location or violation printed"})
        else:
            rows.append(row)

with open(os.path.join(OUT_DIR, "cases.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in FIELDS})
with open(os.path.join(OUT_DIR, "dropped.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=DROP_FIELDS)
    w.writeheader()
    w.writerows(dropped)
print("rows", len(rows), "dropped", len(dropped))
