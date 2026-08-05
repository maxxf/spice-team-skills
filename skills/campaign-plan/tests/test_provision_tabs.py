#!/usr/bin/env python3
"""Tests for tracker tab selection during provisioning (US-007).

The bug these lock down: Abby's Bagels tracker carries BOTH 'Monthly Platform Overview'
and 'Weekly Platform Overview'. The original matcher iterated tabs and took the first one
matching any hint, so workbook order beat hint priority and provisioning wired the
MONTHLY tab into a weekly refresh — wrong period, no error.

Run:  python -m unittest discover -s companies/spice/skills/campaign-plan/tests -p 'test_provision_tabs.py'
"""
from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(os.path.dirname(HERE), "references")
sys.path.insert(0, REFS)

import provision as pr  # noqa: E402

PLATFORM = pr.TRACKER_PLATFORM_HINTS
LOCATION = pr.TRACKER_LOCATION_HINTS


class TestPlatformTabPriority(unittest.TestCase):
    def test_weekly_wins_even_when_monthly_comes_first(self):
        """The exact Abby's Bagels tab order that caused the bug."""
        tabs = ["Monthly Platform Overview", "Weekly Platform Overview",
                "OPS_From W16", "Ops Overview"]
        self.assertEqual(pr._pick_tab(tabs, PLATFORM), "Weekly Platform Overview")

    def test_monthly_is_never_chosen_even_when_it_is_the_only_match(self):
        """Better to report no platform tab than to silently use the wrong period."""
        self.assertIsNone(pr._pick_tab(["Monthly Platform Overview"], PLATFORM))

    def test_generic_platform_overview_used_when_no_weekly_exists(self):
        self.assertEqual(pr._pick_tab(["Platform Overview", "Notes"], PLATFORM),
                         "Platform Overview")

    def test_versioned_weekly_tab_still_matches(self):
        """Capriotti's real tab name."""
        tabs = ["Weekly Platform Overview 2.0", "By Location 2.0"]
        self.assertEqual(pr._pick_tab(tabs, PLATFORM), "Weekly Platform Overview 2.0")

    def test_case_insensitive(self):
        self.assertEqual(pr._pick_tab(["weekly platform overview"], PLATFORM),
                         "weekly platform overview")

    def test_none_when_nothing_matches(self):
        self.assertIsNone(pr._pick_tab(["Instructions", "Location_Map"], PLATFORM))

    def test_empty_tab_list(self):
        self.assertIsNone(pr._pick_tab([], PLATFORM))


class TestExcludedTabs(unittest.TestCase):
    def test_template_tab_is_not_chosen(self):
        self.assertIsNone(pr._pick_tab(["Template Platform Overview"], PLATFORM))

    def test_raw_tab_is_not_chosen(self):
        self.assertIsNone(pr._pick_tab(["UE_Raw_Ads By Location"], LOCATION))

    def test_archive_tab_is_not_chosen(self):
        self.assertIsNone(pr._pick_tab(["Archive By Location"], LOCATION))

    def test_real_tab_still_wins_alongside_an_excluded_one(self):
        tabs = ["Archive By Location", "By Location"]
        self.assertEqual(pr._pick_tab(tabs, LOCATION), "By Location")


class TestLocationTab(unittest.TestCase):
    def test_plain_by_location(self):
        self.assertEqual(pr._pick_tab(["By Location", "Notes"], LOCATION), "By Location")

    def test_versioned_by_location(self):
        """goop uses 'By Location 2.0', Tiff's uses 'By Location' — both must resolve."""
        self.assertEqual(pr._pick_tab(["By Location 2.0"], LOCATION), "By Location 2.0")

    def test_absent_location_tab_returns_none_not_a_guess(self):
        tabs = ["Monthly Platform Overview", "Weekly Platform Overview", "Ops Overview"]
        self.assertIsNone(pr._pick_tab(tabs, LOCATION))


class TestNarrowTabDetection(unittest.TestCase):
    """Locks down the Abby's Bagels first-refresh crash: tabs created 8 columns wide
    while write_dashboard merges J4:K4 (columns 10-11)."""

    def setUp(self):
        sys.path.insert(0, REFS)
        import sheets_writer as sw
        self.sw = sw

    def _meta(self, widths):
        return {"tabs": {t: i for i, t in enumerate(widths)}, "widths": widths}

    def test_eight_column_tab_is_flagged(self):
        meta = self._meta({"Dashboard": 8})
        self.assertEqual(self.sw._narrow_tabs(meta), ["Dashboard"])

    def test_wide_enough_tab_is_not_flagged(self):
        meta = self._meta({"Dashboard": self.sw.MIN_TAB_COLUMNS})
        self.assertEqual(self.sw._narrow_tabs(meta), [])

    def test_wider_than_minimum_is_left_alone(self):
        meta = self._meta({"Dashboard": 60})
        self.assertEqual(self.sw._narrow_tabs(meta), [])

    def test_only_canonical_tabs_are_touched(self):
        """A GM's own tab is none of our business, however narrow."""
        meta = self._meta({"Some GM Scratch Tab": 4})
        self.assertEqual(self.sw._narrow_tabs(meta), [])

    def test_unknown_width_is_not_flagged(self):
        """Width 0 means the API did not report it — do not guess and rewrite the grid."""
        meta = self._meta({"Dashboard": 0})
        self.assertEqual(self.sw._narrow_tabs(meta), [])

    def test_multiple_narrow_tabs_all_returned_sorted(self):
        meta = self._meta({"Dashboard": 8, "Archive": 8, "History": 9})
        self.assertEqual(self.sw._narrow_tabs(meta), ["Archive", "Dashboard", "History"])

    def test_minimum_covers_the_widest_writer_range(self):
        """Archive spans A:L (12) and the append paths use A:Z (26)."""
        self.assertGreaterEqual(self.sw.MIN_TAB_COLUMNS, 26)


if __name__ == "__main__":
    unittest.main(verbosity=2)
