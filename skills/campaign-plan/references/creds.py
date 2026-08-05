#!/usr/bin/env python3
"""One place that resolves the Google service-account credential.

Before this, four modules each hardcoded `~/.config/spice/google-sheets-writer.json`,
which meant the only way to run the skill was to have that file on your Mac — the manual
key handoff that made onboarding a teammate a multi-week job.

Resolution order, first hit wins:

  1. `SPICE_SHEETS_KEY_JSON`        — the key's JSON, inline. What CI would use.
  2. `SHARED/GOOGLE_SHEETS_WRITER`  — what `hq secrets exec --only SHARED/GOOGLE_SHEETS_WRITER`
                                      injects. HQ names the env var after the secret path,
                                      slash included, so it is read by exact key rather than
                                      as a normal identifier.
  3. `SPICE_SHEETS_KEY`             — path to a key file, if you keep it somewhere custom.
  4. `~/.config/spice/google-sheets-writer.json` — the historical default.

Env wins over file so `hq run` / `hq secrets exec` beats a stale local copy.
"""
from __future__ import annotations

import json
import os

DEFAULT_KEY_PATH = "~/.config/spice/google-sheets-writer.json"
HQ_SECRET_ENV = "SHARED/GOOGLE_SHEETS_WRITER"
INLINE_JSON_ENV = "SPICE_SHEETS_KEY_JSON"
KEY_PATH_ENV = "SPICE_SHEETS_KEY"


def key_path() -> str:
    """The key file path we would fall back to (whether or not it exists)."""
    return os.path.expanduser(os.environ.get(KEY_PATH_ENV, DEFAULT_KEY_PATH))


def _inline_json(env: dict | None = None) -> str | None:
    env = os.environ if env is None else env
    for name in (INLINE_JSON_ENV, HQ_SECRET_ENV):
        raw = env.get(name)
        if raw and raw.strip():
            return raw
    return None


def resolve(env: dict | None = None) -> tuple[str, str]:
    """Return (source, detail) describing where the credential comes from.

    source is one of: 'env', 'file', 'missing'. Pure, so the doctor can report the
    resolution without building an API client.
    """
    env = os.environ if env is None else env
    raw = _inline_json(env)
    if raw:
        name = INLINE_JSON_ENV if env.get(INLINE_JSON_ENV) else HQ_SECRET_ENV
        return "env", name
    path = os.path.expanduser(env.get(KEY_PATH_ENV, DEFAULT_KEY_PATH))
    if os.path.exists(path):
        return "file", path
    return "missing", path


def describe() -> str:
    """Human-readable one-liner for doctor output and error messages."""
    source, detail = resolve()
    if source == "env":
        return f"injected from HQ secrets (${detail})"
    if source == "file":
        return f"file {detail}"
    return f"NOT FOUND (looked for ${HQ_SECRET_ENV}, ${INLINE_JSON_ENV}, and {detail})"


def service_account_info() -> dict:
    """The parsed service-account key. Raises with an actionable message if absent."""
    source, detail = resolve()
    if source == "env":
        raw = _inline_json()
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"${detail} is set but is not valid JSON ({e}). It should hold the whole "
                "service-account key file, not a path to it."
            ) from e
    if source == "file":
        with open(detail) as fh:
            return json.load(fh)
    raise FileNotFoundError(
        f"Google service-account credential not found. Either run under HQ secrets:\n"
        f"    hq secrets exec --company spice --only {HQ_SECRET_ENV} -- <command>\n"
        f"or place the key file at {detail}. See RUNBOOK.md, one-time setup."
    )


def credentials(scopes: list[str]):
    """A google.oauth2 Credentials object for the given scopes."""
    from google.oauth2 import service_account
    return service_account.Credentials.from_service_account_info(
        service_account_info(), scopes=scopes)


def available() -> bool:
    return resolve()[0] != "missing"


# ---------------------------------------------------------------- Notion

NOTION_TOKEN_PATH = "~/.config/spice/notion-token"
NOTION_HQ_SECRET_ENV = "SHARED/NOTION_SPICY"
NOTION_TOKEN_ENV = "NOTION_TOKEN"


def _clean_notion(raw: str) -> str:
    """The token file is sometimes a bare token and sometimes a JSON blob."""
    raw = raw.strip()
    if raw.startswith("{"):
        try:
            j = json.loads(raw)
            return (j.get("token") or j.get("notion_token")
                    or j.get("NOTION_TOKEN") or raw).strip()
        except json.JSONDecodeError:
            return raw
    return raw


def resolve_notion(env: dict | None = None) -> tuple[str, str]:
    """(source, detail) for the Notion token. Same precedence rule as the Google key."""
    env = os.environ if env is None else env
    for name in (NOTION_TOKEN_ENV, NOTION_HQ_SECRET_ENV):
        if (env.get(name) or "").strip():
            return "env", name
    path = os.path.expanduser(NOTION_TOKEN_PATH)
    if os.path.exists(path):
        return "file", path
    return "missing", path


def notion_token(env: dict | None = None) -> str | None:
    env = os.environ if env is None else env
    source, detail = resolve_notion(env)
    if source == "env":
        return _clean_notion(env[detail])
    if source == "file":
        with open(detail) as fh:
            return _clean_notion(fh.read())
    return None
