#!/usr/bin/env python3
"""Tests that --dry-run cannot write, at the API chokepoint.

The bug these lock down: dry-run was honoured only by writers that individually remembered
to check the flag. write_history, append_archive, append_rows, append_weekly_learning and
write_dashboard did not, so `refresh.py --dry-run` against Capriotti's on 2026-08-05 wrote
826 History rows and filed 2 Archive entries into a live Sheet while reporting itself as a
dry run.

Run:  python -m unittest discover -s companies/spice/skills/campaign-plan/tests -p 'test_dry_run_guard.py'
"""
from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(os.path.dirname(HERE), "references")
sys.path.insert(0, REFS)

import sheets_writer as sw  # noqa: E402


class FakeExecutable:
    """Mimics a googleapiclient request: .execute() performs the write."""

    def __init__(self, log, label):
        self._log, self._label = log, label

    def execute(self, *_a, **_kw):
        self._log.append(self._label)
        return {"updates": {"updatedRows": 99}}


class FakeValues:
    def __init__(self, log):
        self._log = log

    def get(self, **_kw):
        return FakeExecutable(self._log, "values.get")

    def update(self, **_kw):
        return FakeExecutable(self._log, "values.update")

    def append(self, **_kw):
        return FakeExecutable(self._log, "values.append")

    def clear(self, **_kw):
        return FakeExecutable(self._log, "values.clear")


class FakeSpreadsheets:
    def __init__(self, log):
        self._log = log

    def values(self):
        return FakeValues(self._log)

    def get(self, **_kw):
        return FakeExecutable(self._log, "spreadsheets.get")

    def batchUpdate(self, **_kw):  # noqa: N802 — matches the Google API name
        return FakeExecutable(self._log, "spreadsheets.batchUpdate")


class FakeService:
    def __init__(self, log):
        self._log = log

    def spreadsheets(self):
        return FakeSpreadsheets(self._log)


class GuardTestCase(unittest.TestCase):
    def setUp(self):
        self.log = []
        self.guard = sw._DryRunGuard(FakeService(self.log))
        sw._DRY_RUN_BLOCKED.clear()

    def tearDown(self):
        sw._DRY_RUN_BLOCKED.clear()


class TestReadsPassThrough(GuardTestCase):
    def test_values_get_still_executes(self):
        """A dry run must still read current state to build its diff."""
        self.guard.spreadsheets().values().get(spreadsheetId="x", range="A1").execute()
        self.assertEqual(self.log, ["values.get"])

    def test_spreadsheets_get_still_executes(self):
        self.guard.spreadsheets().get(spreadsheetId="x").execute()
        self.assertEqual(self.log, ["spreadsheets.get"])

    def test_read_returns_real_payload(self):
        r = self.guard.spreadsheets().values().get(spreadsheetId="x", range="A1").execute()
        self.assertEqual(r["updates"]["updatedRows"], 99)


class TestWritesAreBlocked(GuardTestCase):
    def test_values_update_is_blocked(self):
        """The History write path."""
        self.guard.spreadsheets().values().update(
            spreadsheetId="x", range="History!A1", body={}).execute()
        self.assertEqual(self.log, [])

    def test_values_append_is_blocked(self):
        """The Archive and Account Learnings write path."""
        self.guard.spreadsheets().values().append(
            spreadsheetId="x", range="Archive!A:Z", body={}).execute()
        self.assertEqual(self.log, [])

    def test_values_clear_is_blocked(self):
        self.guard.spreadsheets().values().clear(spreadsheetId="x", range="A1:Z").execute()
        self.assertEqual(self.log, [])

    def test_batch_update_is_blocked(self):
        """The Dashboard write path."""
        self.guard.spreadsheets().batchUpdate(spreadsheetId="x", body={}).execute()
        self.assertEqual(self.log, [])

    def test_blocked_write_returns_empty_dict_not_none(self):
        """Callers do r.get(...) on the result; None would crash instead of no-op."""
        r = self.guard.spreadsheets().values().append(
            spreadsheetId="x", range="A:Z", body={}).execute()
        self.assertEqual(r, {})
        self.assertEqual(r.get("updates", {}).get("updatedRows", 0), 0)

    def test_mixed_sequence_reads_run_writes_do_not(self):
        ss = self.guard.spreadsheets()
        ss.values().get(spreadsheetId="x", range="History!A1:I10").execute()
        ss.values().update(spreadsheetId="x", range="History!A1", body={}).execute()
        ss.values().append(spreadsheetId="x", range="Archive!A:Z", body={}).execute()
        ss.batchUpdate(spreadsheetId="x", body={}).execute()
        self.assertEqual(self.log, ["values.get"])


class TestBlockedCallsAreReported(GuardTestCase):
    def test_blocked_calls_are_recorded(self):
        self.guard.spreadsheets().values().update(spreadsheetId="x", range="A1", body={}).execute()
        self.guard.spreadsheets().batchUpdate(spreadsheetId="x", body={}).execute()
        self.assertEqual(len(sw.dry_run_blocked()), 2)

    def test_recorded_labels_name_the_method(self):
        self.guard.spreadsheets().values().append(spreadsheetId="x", range="A:Z", body={}).execute()
        self.assertTrue(any("append" in lbl for lbl in sw.dry_run_blocked()))

    def test_reads_are_not_recorded_as_blocked(self):
        self.guard.spreadsheets().values().get(spreadsheetId="x", range="A1").execute()
        self.assertEqual(sw.dry_run_blocked(), [])


class TestServiceSelection(unittest.TestCase):
    """_service() must hand back the guard in dry-run and the raw client otherwise."""

    def setUp(self):
        self._saved_cache = sw._SVC_CACHE
        self._saved_mode = dict(sw._WRITE_MODE)
        sw._SVC_CACHE = FakeService([])

    def tearDown(self):
        sw._SVC_CACHE = self._saved_cache
        sw._WRITE_MODE.clear()
        sw._WRITE_MODE.update(self._saved_mode)

    def test_dry_run_mode_returns_the_guard(self):
        sw.set_write_mode(dry_run=True)
        self.assertIsInstance(sw._service(), sw._DryRunGuard)

    def test_normal_mode_returns_the_raw_client(self):
        sw.set_write_mode(dry_run=False)
        self.assertNotIsInstance(sw._service(), sw._DryRunGuard)

    def test_mode_is_read_at_call_time_not_import_time(self):
        sw.set_write_mode(dry_run=False)
        self.assertNotIsInstance(sw._service(), sw._DryRunGuard)
        sw.set_write_mode(dry_run=True)
        self.assertIsInstance(sw._service(), sw._DryRunGuard)


if __name__ == "__main__":
    unittest.main(verbosity=2)
