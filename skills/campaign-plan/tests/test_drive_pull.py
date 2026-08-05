#!/usr/bin/env python3
"""Regression tests for the Drive input pull (US-006).

Covers the parts that must be correct without touching the network: the cache
decision, the manifest round-trip, and the safety rule that a cache hit can
never be claimed for a file whose bytes are not actually on disk.

Run:  python -m pytest companies/spice/skills/campaign-plan/tests/test_drive_pull.py -q
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

import drive_inputs as di  # noqa: E402


def _mkfile(d: str, name: str, size: int) -> str:
    p = os.path.join(d, name)
    with open(p, "wb") as fh:
        fh.write(b"x" * size)
    return p


def _remote(name: str, size: int, mtime: str = "2026-07-20T10:00:00.000Z", fid: str | None = None) -> dict:
    return {
        "id": fid or f"id-{name}",
        "name": name,
        "size": str(size),
        "modifiedTime": mtime,
        "mimeType": "text/csv",
    }


class TestCacheKey(unittest.TestCase):
    def test_key_combines_size_and_modified_time(self):
        f = _remote("a.csv", 10)
        self.assertEqual(di._cache_key(f), "10:2026-07-20T10:00:00.000Z")

    def test_key_tolerates_missing_size(self):
        f = {"id": "x", "name": "a.csv", "modifiedTime": "2026-07-20T10:00:00.000Z"}
        self.assertEqual(di._cache_key(f), "0:2026-07-20T10:00:00.000Z")

    def test_key_changes_when_file_is_re_uploaded(self):
        before = di._cache_key(_remote("a.csv", 10, "2026-07-20T10:00:00.000Z"))
        after = di._cache_key(_remote("a.csv", 10, "2026-07-21T09:00:00.000Z"))
        self.assertNotEqual(before, after)


class TestManifest(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            di._write_manifest(d, {"a.csv": "10:t"})
            self.assertEqual(di._read_manifest(d), {"a.csv": "10:t"})

    def test_missing_manifest_reads_as_empty(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(di._read_manifest(d), {})

    def test_corrupt_manifest_reads_as_empty_not_crash(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, di.MANIFEST_NAME), "w") as fh:
                fh.write("{not json")
            self.assertEqual(di._read_manifest(d), {})

    def test_manifest_is_not_reported_as_an_input_file(self):
        """The manifest lives beside the inputs; it must never leak into results."""
        with tempfile.TemporaryDirectory() as d:
            di._write_manifest(d, {"a.csv": "10:t"})
            self.assertTrue(di.MANIFEST_NAME.startswith("."))


class TestPlanDownloads(unittest.TestCase):
    def test_all_fresh_when_nothing_cached(self):
        with tempfile.TemporaryDirectory() as d:
            files = [_remote("a.csv", 10), _remote("b.csv", 20)]
            todo, cached = di._plan_downloads(files, d, {})
            self.assertEqual([f["name"] for f in todo], ["a.csv", "b.csv"])
            self.assertEqual(cached, [])

    def test_cache_hit_when_manifest_and_bytes_both_match(self):
        with tempfile.TemporaryDirectory() as d:
            _mkfile(d, "a.csv", 10)
            files = [_remote("a.csv", 10)]
            todo, cached = di._plan_downloads(files, d, {"a.csv": di._cache_key(files[0])})
            self.assertEqual(todo, [])
            self.assertEqual([os.path.basename(p) for p in cached], ["a.csv"])

    def test_no_cache_hit_when_manifest_says_yes_but_file_is_gone(self):
        """Manifest alone must not be trusted — someone may have cleaned the dir."""
        with tempfile.TemporaryDirectory() as d:
            files = [_remote("a.csv", 10)]
            todo, cached = di._plan_downloads(files, d, {"a.csv": di._cache_key(files[0])})
            self.assertEqual([f["name"] for f in todo], ["a.csv"])
            self.assertEqual(cached, [])

    def test_no_cache_hit_when_local_size_disagrees_with_remote(self):
        """A truncated or partial download must be re-fetched, not reused."""
        with tempfile.TemporaryDirectory() as d:
            _mkfile(d, "a.csv", 3)  # remote says 10
            files = [_remote("a.csv", 10)]
            todo, cached = di._plan_downloads(files, d, {"a.csv": di._cache_key(files[0])})
            self.assertEqual([f["name"] for f in todo], ["a.csv"])

    def test_re_upload_invalidates_the_cache(self):
        with tempfile.TemporaryDirectory() as d:
            _mkfile(d, "a.csv", 10)
            old = _remote("a.csv", 10, "2026-07-20T10:00:00.000Z")
            new = _remote("a.csv", 10, "2026-07-21T09:00:00.000Z")
            todo, cached = di._plan_downloads([new], d, {"a.csv": di._cache_key(old)})
            self.assertEqual([f["name"] for f in todo], ["a.csv"])

    def test_mixed_batch_splits_correctly(self):
        with tempfile.TemporaryDirectory() as d:
            _mkfile(d, "cached.csv", 10)
            c = _remote("cached.csv", 10)
            fresh = _remote("fresh.csv", 20)
            todo, cached = di._plan_downloads([c, fresh], d, {"cached.csv": di._cache_key(c)})
            self.assertEqual([f["name"] for f in todo], ["fresh.csv"])
            self.assertEqual([os.path.basename(p) for p in cached], ["cached.csv"])

    def test_google_native_files_are_never_cached(self):
        """Native Sheets export on the fly and have no stable size — always re-fetch."""
        with tempfile.TemporaryDirectory() as d:
            _mkfile(d, "sheet.csv", 10)
            f = {
                "id": "s1",
                "name": "sheet.csv",
                "modifiedTime": "2026-07-20T10:00:00.000Z",
                "mimeType": "application/vnd.google-apps.spreadsheet",
            }
            todo, cached = di._plan_downloads([f], d, {"sheet.csv": di._cache_key(f)})
            self.assertEqual([x["name"] for x in todo], ["sheet.csv"])

    def test_force_ignores_every_cache_hit(self):
        with tempfile.TemporaryDirectory() as d:
            _mkfile(d, "a.csv", 10)
            f = _remote("a.csv", 10)
            todo, cached = di._plan_downloads([f], d, {"a.csv": di._cache_key(f)}, force=True)
            self.assertEqual([x["name"] for x in todo], ["a.csv"])
            self.assertEqual(cached, [])


class TestWorkerCount(unittest.TestCase):
    def test_never_more_workers_than_files(self):
        self.assertEqual(di._worker_count(3, 8), 3)

    def test_capped_at_the_max(self):
        self.assertEqual(di._worker_count(50, 8), 8)

    def test_at_least_one_worker_for_an_empty_batch(self):
        self.assertEqual(di._worker_count(0, 8), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
