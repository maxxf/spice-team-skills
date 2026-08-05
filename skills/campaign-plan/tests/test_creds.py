#!/usr/bin/env python3
"""Tests for Google credential resolution (US-001).

Four modules used to hardcode ~/.config/spice/google-sheets-writer.json, so the only way
to run the skill was to have that file on your Mac — the manual key handoff that made
onboarding a teammate take weeks. These lock down the resolution order that lets
`hq secrets exec` work instead.

Run:  python -m unittest discover -s companies/spice/skills/campaign-plan/tests -p 'test_creds.py'
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

import creds  # noqa: E402

FAKE_KEY = {"client_email": "robot@example.iam.gserviceaccount.com",
            "private_key": "-----BEGIN PRIVATE KEY-----\nx\n-----END PRIVATE KEY-----\n",
            "type": "service_account"}


class TestResolutionOrder(unittest.TestCase):
    def test_inline_json_env_wins(self):
        env = {creds.INLINE_JSON_ENV: json.dumps(FAKE_KEY)}
        self.assertEqual(creds.resolve(env), ("env", creds.INLINE_JSON_ENV))

    def test_hq_secret_env_is_used(self):
        """hq secrets exec names the variable after the secret path, slash and all."""
        env = {creds.HQ_SECRET_ENV: json.dumps(FAKE_KEY)}
        self.assertEqual(creds.resolve(env), ("env", creds.HQ_SECRET_ENV))

    def test_inline_json_beats_hq_secret(self):
        env = {creds.INLINE_JSON_ENV: json.dumps(FAKE_KEY),
               creds.HQ_SECRET_ENV: json.dumps(FAKE_KEY)}
        self.assertEqual(creds.resolve(env)[1], creds.INLINE_JSON_ENV)

    def test_env_beats_an_existing_key_file(self):
        """Otherwise a stale local copy silently overrides what HQ injected."""
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(FAKE_KEY, fh); path = fh.name
        try:
            env = {creds.HQ_SECRET_ENV: json.dumps(FAKE_KEY), creds.KEY_PATH_ENV: path}
            self.assertEqual(creds.resolve(env)[0], "env")
        finally:
            os.unlink(path)

    def test_file_used_when_no_env(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(FAKE_KEY, fh); path = fh.name
        try:
            self.assertEqual(creds.resolve({creds.KEY_PATH_ENV: path}), ("file", path))
        finally:
            os.unlink(path)

    def test_missing_when_neither(self):
        env = {creds.KEY_PATH_ENV: "/nonexistent/nope.json"}
        source, detail = creds.resolve(env)
        self.assertEqual(source, "missing")
        self.assertEqual(detail, "/nonexistent/nope.json")

    def test_empty_env_var_is_ignored_not_treated_as_present(self):
        """An exported-but-empty var must not shadow a working key file."""
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(FAKE_KEY, fh); path = fh.name
        try:
            env = {creds.HQ_SECRET_ENV: "  ", creds.KEY_PATH_ENV: path}
            self.assertEqual(creds.resolve(env)[0], "file")
        finally:
            os.unlink(path)


class TestServiceAccountInfo(unittest.TestCase):
    def setUp(self):
        self._saved = dict(os.environ)

    def tearDown(self):
        os.environ.clear(); os.environ.update(self._saved)

    def test_parses_from_env(self):
        os.environ[creds.HQ_SECRET_ENV] = json.dumps(FAKE_KEY)
        self.assertEqual(creds.service_account_info()["client_email"],
                         FAKE_KEY["client_email"])

    def test_bad_json_in_env_names_the_variable(self):
        os.environ[creds.HQ_SECRET_ENV] = "not json"
        with self.assertRaises(ValueError) as cm:
            creds.service_account_info()
        self.assertIn(creds.HQ_SECRET_ENV, str(cm.exception))

    def test_missing_error_tells_you_both_ways_to_fix_it(self):
        for k in (creds.HQ_SECRET_ENV, creds.INLINE_JSON_ENV):
            os.environ.pop(k, None)
        os.environ[creds.KEY_PATH_ENV] = "/nonexistent/nope.json"
        with self.assertRaises(FileNotFoundError) as cm:
            creds.service_account_info()
        msg = str(cm.exception)
        self.assertIn("hq secrets exec", msg)
        self.assertIn("/nonexistent/nope.json", msg)

    def test_available_reflects_resolution(self):
        os.environ[creds.HQ_SECRET_ENV] = json.dumps(FAKE_KEY)
        self.assertTrue(creds.available())
        os.environ.pop(creds.HQ_SECRET_ENV)
        os.environ[creds.KEY_PATH_ENV] = "/nonexistent/nope.json"
        self.assertFalse(creds.available())


class TestNotionResolution(unittest.TestCase):
    def test_notion_token_env_wins(self):
        env = {creds.NOTION_TOKEN_ENV: "ntn_direct"}
        self.assertEqual(creds.resolve_notion(env), ("env", creds.NOTION_TOKEN_ENV))

    def test_hq_notion_secret_is_used(self):
        env = {creds.NOTION_HQ_SECRET_ENV: "ntn_from_hq"}
        self.assertEqual(creds.resolve_notion(env), ("env", creds.NOTION_HQ_SECRET_ENV))
        self.assertEqual(creds.notion_token(env), "ntn_from_hq")

    def test_json_wrapped_token_is_unwrapped(self):
        env = {creds.NOTION_HQ_SECRET_ENV: json.dumps({"token": "ntn_inner"})}
        self.assertEqual(creds.notion_token(env), "ntn_inner")

    def test_bare_token_passes_through(self):
        self.assertEqual(creds.notion_token({creds.NOTION_TOKEN_ENV: " ntn_x \n"}), "ntn_x")

    def test_malformed_json_returns_raw_rather_than_crashing(self):
        env = {creds.NOTION_TOKEN_ENV: "{not json"}
        self.assertEqual(creds.notion_token(env), "{not json")

    def test_missing_when_no_env_and_no_file(self):
        """resolve_notion is pure, so assert on it rather than on the machine's token file."""
        original = creds.NOTION_TOKEN_PATH
        creds.NOTION_TOKEN_PATH = "/nonexistent/notion-token"
        try:
            self.assertEqual(creds.resolve_notion({})[0], "missing")
            self.assertIsNone(creds.notion_token({}))
        finally:
            creds.NOTION_TOKEN_PATH = original


if __name__ == "__main__":
    unittest.main(verbosity=2)
