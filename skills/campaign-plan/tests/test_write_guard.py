#!/usr/bin/env python3
"""Tests for the write-safety gate.

The regression these exist for: on 2026-06-16 the first live campaign-plan run wrote
goop's Sheet blank, because `write_full_tab` cleared the tab before checking whether
it had anything to write. `test_empty_matrix_over_populated_tab_is_blocked` is that
bug. If it ever goes green-to-red, the blank-write path is back.

Run: python3 -m pytest tests/test_write_guard.py -q
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "references"))

import write_guard  # noqa: E402


POPULATED = [["Campaign", "Spend", "ROAS"]] + [[f"c{i}", f"${i}00", f"{i}.1"] for i in range(1, 50)]


class TestGate(unittest.TestCase):
    def test_empty_matrix_over_populated_tab_is_blocked(self):
        """The goop blank-write. An empty result over real data is an upstream failure."""
        v = write_guard.evaluate("Active Campaigns", POPULATED, [])
        self.assertFalse(v["allow"])
        self.assertIn("empty", v["reason"])
        self.assertEqual(v["before_rows"], 50)
        self.assertEqual(v["after_rows"], 0)

    def test_whitespace_only_matrix_counts_as_empty(self):
        """Blank strings are not data — a matrix of empties must not slip past the gate."""
        v = write_guard.evaluate("Dashboard", POPULATED, [["", "  ", ""], ["", "", ""]])
        self.assertFalse(v["allow"])

    def test_empty_over_empty_is_allowed(self):
        """A new or already-empty tab has nothing to lose."""
        self.assertTrue(write_guard.evaluate("New Tab", [], [])["allow"])
        self.assertTrue(write_guard.evaluate("New Tab", [["", ""]], [["a"]])["allow"])

    def test_growth_is_allowed(self):
        after = POPULATED + [["c99", "$9900", "9.9"]]
        self.assertTrue(write_guard.evaluate("Active Campaigns", POPULATED, after)["allow"])

    def test_modest_shrink_is_allowed(self):
        """50 -> 35 is a 30% drop: campaigns ending, not a failure."""
        v = write_guard.evaluate("Active Campaigns", POPULATED, POPULATED[:35])
        self.assertTrue(v["allow"], v["reason"])

    def test_severe_shrink_is_blocked(self):
        """50 -> 12 is a 76% drop. Partial-extraction failures look exactly like this."""
        v = write_guard.evaluate("Active Campaigns", POPULATED, POPULATED[:12])
        self.assertFalse(v["allow"])
        self.assertIn("--force-shrink", v["reason"])

    def test_severe_shrink_passes_with_force(self):
        v = write_guard.evaluate("Active Campaigns", POPULATED, POPULATED[:12], force_shrink=True)
        self.assertTrue(v["allow"])

    def test_force_shrink_does_not_permit_a_blank_write(self):
        """--force-shrink is an escape hatch for real shrinkage, never for emptiness."""
        v = write_guard.evaluate("Active Campaigns", POPULATED, [], force_shrink=True)
        self.assertFalse(v["allow"])

    def test_threshold_boundary_is_not_off_by_one(self):
        """Exactly at the threshold passes; one row past it blocks."""
        before = [[f"r{i}"] for i in range(100)]
        self.assertTrue(write_guard.evaluate("t", before, before[:60])["allow"])
        self.assertFalse(write_guard.evaluate("t", before, before[:59])["allow"])


class TestSnapshots(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._orig = write_guard.STATE_DIR
        write_guard.STATE_DIR = self.tmp

    def tearDown(self):
        write_guard.STATE_DIR = self._orig

    def test_roundtrip(self):
        write_guard.save_snapshot("sheet1", "Dashboard", POPULATED, "2026-08-05T18:00:00Z")
        snap = write_guard.load_snapshot("sheet1", "Dashboard")
        self.assertIsNotNone(snap)
        self.assertEqual(snap["values"], POPULATED)
        self.assertEqual(snap["rows"], 50)

    def test_prune_keeps_newest(self):
        for i in range(15):
            write_guard.save_snapshot("sheet1", "Dashboard", [[f"v{i}"]], f"2026-08-{i + 1:02d}T00:00:00Z")
        paths = write_guard.list_snapshots("sheet1", "Dashboard")
        self.assertEqual(len(paths), write_guard.RETAIN_PER_TAB)
        newest = write_guard.load_snapshot("sheet1", "Dashboard")
        self.assertEqual(newest["values"], [["v14"]])

    def test_missing_snapshot_returns_none(self):
        self.assertIsNone(write_guard.load_snapshot("nope", "nope"))

    def test_tab_names_with_slashes_do_not_escape_the_state_dir(self):
        """A tab named '../../etc' must not write outside STATE_DIR."""
        write_guard.save_snapshot("s", "../../evil", [["x"]], "2026-08-05T00:00:00Z")
        for root, _dirs, files in os.walk(self.tmp):
            for f in files:
                self.assertTrue(os.path.realpath(os.path.join(root, f)).startswith(
                    os.path.realpath(self.tmp)))

    def test_snapshot_failure_does_not_raise(self):
        """A snapshot that cannot be written must not block a legitimate refresh."""
        write_guard.STATE_DIR = "/proc/nonexistent-and-unwritable"
        self.assertIsNone(write_guard.save_snapshot("s", "t", [["x"]], "2026-08-05T00:00:00Z"))


class TestDiff(unittest.TestCase):
    def test_reports_shape_change(self):
        out = write_guard.render_diff("Dashboard", POPULATED, POPULATED[:20])
        self.assertIn("50 -> 20 rows", out)
        self.assertIn("-30", out)

    def test_empty_target_is_labelled(self):
        self.assertIn("(empty)", write_guard.render_diff("Dashboard", POPULATED, []))


if __name__ == "__main__":
    unittest.main()
