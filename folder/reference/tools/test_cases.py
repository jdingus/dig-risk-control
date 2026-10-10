#!/usr/bin/env python3
"""Tests for cases.py. Run from the folder root:  python3 reference/tools/test_cases.py
Part 1 checks the PREAMBLE definitions on fixed strings. Part 2 checks the CSV against the
counts printed in reference/SCHEMA.md (an independent source). Part 3 runs invented CLI queries
and cross-checks them against a plain csv.DictReader recount that does not use cases.py's parsers."""
import csv
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cases as C  # noqa: E402

CSV = os.path.join(HERE, "..", "cases.csv")
CLI = [sys.executable, os.path.join(HERE, "cases.py")]


def run(*args):
    return subprocess.run(CLI + list(args), capture_output=True, text=True, check=True).stdout


class TestDefinitions(unittest.TestCase):
    def test_base_and_qualifier(self):
        cases = [
            ("IC 8-1-26-16(h)(expire)", "16(h)", "expire"),
            ("IC 8-1-26-16(h)", "16(h)", ""),
            ("IC 8-1-26-20(a)(3)(b)", "20(a)(3)(b)", ""),
            ("IC 8-1-26-20(a)(2)", "20(a)(2)", ""),
            ("IC 8-1-26-18(j)(no-response)", "18(j)", "no-response"),
            ("IC 8-1-26-19(c)", "19(c)", ""),
            ("", "", ""),
        ]
        for cite, b, q in cases:
            self.assertEqual((C.base_section(cite), C.qualifier(cite)), (b, q), cite)

    def test_headline(self):
        cases = [
            ("$1,000", 1000), ("$$1000", 1000), ("$3, 500; no ticket escalation - additional $1,000 ($4,500)", 3500),
            ("Warning letter", 0), ("Warning letter Special instructions: dig tickets", 0),
            ("Training or $5,000 if respondent fails to complete training", 5000),
            ("$1,500, respondent can complete training instead of paying $1,500", 1500),
            ("3000", 0), ("0", 0), (".5000", 0), ("", 0), ("Training (completed 10/1/20)", 0),
            ("$2,500.00", 2500), ("Training + $1,000 $5,000 if", 1000),
        ]
        for rec, v in cases:
            self.assertEqual(C.headline_penalty(rec), v, rec)

    def test_utility(self):
        self.assertTrue(C.is_utility("  CENTERPOINT Energy Indiana"))
        self.assertTrue(C.is_utility("nipsco"))
        self.assertTrue(C.is_utility("Citizens Gas"))
        self.assertFalse(C.is_utility("Miller Pipeline, LLC"))
        self.assertFalse(C.is_utility("The CenterPoint Company"))   # prefix test only
        self.assertFalse(C.is_utility("Citizens Bank"))
        self.assertFalse(C.is_utility(""))

    def test_year(self):
        self.assertEqual(C.order_year({"order_date": "2023-01-18"}), 2023)


class TestAgainstSchemaMd(unittest.TestCase):
    """Counts that reference/SCHEMA.md prints for the data."""
    @classmethod
    def setUpClass(cls):
        cls.rows = C.load(CSV)

    def test_rows(self):
        self.assertEqual(len(self.rows), 9958)
        self.assertEqual(len({r["order_file"] for r in self.rows}), 58)

    def test_qualifier_counts(self):
        from collections import Counter
        c = Counter(r["qualifier"] for r in self.rows if r["qualifier"])
        expect = {"locator-error": 600, "expire": 518, "prior": 272, "records": 249, "out": 191,
                  "no-response": 52, "other": 20}
        self.assertEqual(dict(c), expect)
        self.assertEqual(sum(c.values()), 1902)

    def test_base_sections_are_the_allowed_nine(self):
        allowed = {"16(h)", "16(i)", "18(h)", "18(j)", "19(c)", "20(a)(1)", "20(a)(2)", "20(a)(3)(a)", "20(a)(3)(b)"}
        seen = {r["base"] for r in self.rows}
        self.assertEqual(seen - allowed, {""})        # the one blank-cite row
        self.assertEqual(allowed - seen, set())

    def test_defects_visible(self):
        bad = [r for r in self.rows if r["case_number"] == "0"]
        self.assertEqual(len(bad), 1)
        self.assertEqual(sum(1 for r in self.rows if r["recommendation"] == "$$1000"), 7)
        self.assertEqual(sum(1 for r in self.rows if r["violations"] == ""), 1)


class TestCli(unittest.TestCase):
    """Invented queries; each is recounted with the csv module only (raw strings, no cases.py parsing)."""
    @classmethod
    def setUpClass(cls):
        with open(CSV, newline="", encoding="utf-8") as f:
            cls.raw = list(csv.DictReader(f))

    def test_count_year_and_text(self):
        out = run("count", "--year", "2024", "--rec-contains", "special instructions")
        n = sum(1 for r in self.raw if r["order_date"].startswith("2024") and "special instructions" in r["recommendation"].lower())
        self.assertIn("count = %d of 9958" % n, out)

    def test_group_by_year_sums_to_total(self):
        out = run("group", "--by", "year", "--sort", "key")
        ns = [int(l.split("n=")[1].split()[0]) for l in out.splitlines() if "n=" in l]
        self.assertEqual(sum(ns), 9958)
        self.assertEqual(len(ns), 5)

    def test_stat_median_matches_manual(self):
        import statistics, re
        out = run("stat", "--field", "headline", "--base", "20(a)(1)")
        vals = []
        for r in self.raw:
            if r["violations"].startswith("IC 8-1-26-20(a)(1)"):
                m = re.search(r"\$+\s*(\d[\d,]*)", r["recommendation"])
                vals.append(float(m.group(1).replace(",", "")) if m else 0.0)
        self.assertIn("n = %d" % len(vals), out)
        self.assertIn("median = %s" % C.fmt(statistics.median(vals)), out)

    def test_utility_filter_matches_manual(self):
        out = run("count", "--utility", "yes")
        pre = [p.lower() for p in C.UTILITY_PREFIXES]
        n = sum(1 for r in self.raw if any(r["respondent"].lstrip().lower().startswith(p) for p in pre))
        self.assertIn("count = %d of" % n, out)

    def test_expr_and_receipts(self):
        out = run("count", "--expr", "r['headline'] >= 4000 and r['utility'] == 'no'", "--receipts", "2")
        self.assertEqual(out.count("receipt:"), 2)
        self.assertIn("ord_PSD", out)

    def test_repeat_and_dupes(self):
        out = run("repeat", "--utility", "no", "--min", "30", "--top", "3")
        self.assertIn("spelling variants are NOT merged", out)
        out = run("dupes")
        self.assertIn("2 pairs, 4 rows", out)

    def test_zero_penalty_filter(self):
        out = run("count", "--zero-penalty", "--rec-contains", "warning")
        n = sum(1 for r in self.raw if "warning" in r["recommendation"].lower() and "$" not in r["recommendation"])
        self.assertIn("count = %d of" % n, out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
