#!/usr/bin/env python3
"""Tests for publishing HQ client configs into the plugin snapshot.

The gap these close: configs are authoritative in HQ, but teammates install from the plugin
and have no HQ checkout, so client_config falls back to the plugin's clients/ directory. On
2026-08-05 HQ had 11 configs and the plugin had 6 — five clients that simply did not exist
for anyone but Maxx.

Run:  python -m unittest discover -s companies/spice/skills/campaign-plan/tests -p 'test_publish_configs.py'
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(os.path.dirname(HERE), "references")
sys.path.insert(0, REFS)

import publish_configs as pc  # noqa: E402


def write(d: str, name: str, payload: dict) -> None:
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name), "w") as fh:
        json.dump(payload, fh, indent=2)


class PlanTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.src = os.path.join(self.tmp.name, "hq")
        self.dst = os.path.join(self.tmp.name, "snapshot")
        os.makedirs(self.src); os.makedirs(self.dst)

    def tearDown(self):
        self.tmp.cleanup()


class TestPlan(PlanTestCase):
    def test_config_missing_from_snapshot_is_added(self):
        write(self.src, "capriottis.json", {"v2": True})
        added, changed, unchanged = pc.plan(self.src, self.dst)
        self.assertEqual(added, ["capriottis.json"])
        self.assertEqual(changed, [])

    def test_identical_config_is_unchanged(self):
        write(self.src, "goop.json", {"v2": True})
        write(self.dst, "goop.json", {"v2": True})
        added, changed, unchanged = pc.plan(self.src, self.dst)
        self.assertEqual((added, changed), ([], []))
        self.assertEqual(unchanged, ["goop.json"])

    def test_differing_config_is_changed(self):
        write(self.src, "westville.json", {"net_sales_sheet_id": "new"})
        write(self.dst, "westville.json", {"net_sales_sheet_id": None})
        added, changed, _ = pc.plan(self.src, self.dst)
        self.assertEqual(changed, ["westville.json"])
        self.assertEqual(added, [])

    def test_results_are_sorted(self):
        for n in ("c.json", "a.json", "b.json"):
            write(self.src, n, {"x": 1})
        added, _, _ = pc.plan(self.src, self.dst)
        self.assertEqual(added, ["a.json", "b.json", "c.json"])

    def test_non_json_files_are_ignored(self):
        write(self.src, "goop.json", {"v2": True})
        with open(os.path.join(self.src, "sample.csv"), "w") as fh:
            fh.write("a,b\n")
        added, _, _ = pc.plan(self.src, self.dst)
        self.assertEqual(added, ["goop.json"])

    def test_empty_hq_dir_produces_no_work(self):
        self.assertEqual(pc.plan(self.src, self.dst), ([], [], []))


class TestStaleDetection(PlanTestCase):
    def test_snapshot_only_config_is_reported(self):
        write(self.src, "goop.json", {"v2": True})
        write(self.dst, "goop.json", {"v2": True})
        write(self.dst, "churned.json", {"v2": True})
        self.assertEqual(pc.stale_in_snapshot(self.src, self.dst), ["churned.json"])

    def test_nothing_stale_when_snapshot_is_a_subset(self):
        write(self.src, "a.json", {}); write(self.src, "b.json", {})
        write(self.dst, "a.json", {})
        self.assertEqual(pc.stale_in_snapshot(self.src, self.dst), [])

    def test_missing_snapshot_dir_is_not_an_error(self):
        self.assertEqual(pc.stale_in_snapshot(self.src, "/nonexistent/dir"), [])

    def test_stale_is_reported_but_plan_does_not_delete(self):
        """Deleting on HQ's say-so would drop a client if HQ were the incomplete side."""
        write(self.dst, "churned.json", {"v2": True})
        added, changed, _ = pc.plan(self.src, self.dst)
        self.assertEqual((added, changed), ([], []))
        self.assertTrue(os.path.exists(os.path.join(self.dst, "churned.json")))


class TestRepoDiscovery(unittest.TestCase):
    def test_explicit_repo_wins_when_it_looks_right(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "skills", "campaign-plan"))
            self.assertEqual(pc.find_repo(d), d)

    def test_directory_without_the_skill_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertNotEqual(pc.find_repo(d), d)

    def test_none_when_nothing_matches(self):
        self.assertNotEqual(pc.find_repo("/nonexistent/path"), "/nonexistent/path")




class TestSanitize(unittest.TestCase):
    """Machine-specific paths must not travel to other people's laptops."""

    def test_output_is_stripped(self):
        cfg = {"v2": True, "output": "/Users/maxx/Downloads/goop_Campaign_Plan.xlsx"}
        self.assertNotIn("output", pc.sanitize(cfg))

    def test_everything_else_survives(self):
        cfg = {"v2": True, "sheet_id": "abc", "drive_folder_id": "def",
               "output": "/Users/maxx/Downloads/x.xlsx"}
        self.assertEqual(pc.sanitize(cfg), {"v2": True, "sheet_id": "abc",
                                            "drive_folder_id": "def"})

    def test_config_without_output_is_unchanged(self):
        cfg = {"v2": True, "sheet_id": "abc"}
        self.assertEqual(pc.sanitize(cfg), cfg)

    def test_output_only_difference_is_not_a_change_to_publish(self):
        with tempfile.TemporaryDirectory() as d:
            src, dst = os.path.join(d, "hq"), os.path.join(d, "snap")
            os.makedirs(src); os.makedirs(dst)
            write(src, "goop.json", {"v2": True, "output": "/Users/maxx/Downloads/a.xlsx"})
            write(dst, "goop.json", {"v2": True})
            added, changed, unchanged = pc.plan(src, dst)
            self.assertEqual((added, changed), ([], []))
            self.assertEqual(unchanged, ["goop.json"])


class TestOutputFallback(unittest.TestCase):
    """A published config has no `output`, so the code must pick a sane path itself."""

    def setUp(self):
        sys.path.insert(0, REFS)
        import refresh
        self.refresh = refresh

    def test_falls_back_to_data_dir_when_output_absent(self):
        got = self.refresh._output_path({}, "goop-kitchen", "/tmp/campaign-data-goop")
        self.assertEqual(got, "/tmp/campaign-data-goop/goop-kitchen_Campaign_Plan.xlsx")

    def test_falls_back_when_configured_dir_does_not_exist_here(self):
        cfg = {"output": "/Users/someone-else/Downloads/x.xlsx"}
        got = self.refresh._output_path(cfg, "goop", "/tmp/campaign-data-goop")
        self.assertEqual(got, "/tmp/campaign-data-goop/goop_Campaign_Plan.xlsx")

    def test_honours_a_configured_path_that_exists_here(self):
        with tempfile.TemporaryDirectory() as d:
            target = os.path.join(d, "mine.xlsx")
            self.assertEqual(self.refresh._output_path({"output": target}, "g", "/tmp/x"), target)

class TestSnapshotRepair(unittest.TestCase):
    def test_snapshot_still_carrying_a_stripped_key_is_rewritten(self):
        """Published before sanitizing existed — the sanitized forms match, but the file on
        disk still leaks /Users/maxx, so it must be republished rather than skipped."""
        with tempfile.TemporaryDirectory() as d:
            src, dst = os.path.join(d, "hq"), os.path.join(d, "snap")
            os.makedirs(src); os.makedirs(dst)
            write(src, "goop.json", {"v2": True, "output": "/Users/maxx/Downloads/a.xlsx"})
            write(dst, "goop.json", {"v2": True, "output": "/Users/maxx/Downloads/a.xlsx"})
            _, changed, _ = pc.plan(src, dst)
            self.assertEqual(changed, ["goop.json"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
