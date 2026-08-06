#!/usr/bin/env python3
"""Publish HQ client configs into the plugin bundle, so teammates aren't missing clients.

The problem this solves: configs are authoritative in HQ (US-003, so adding a client no
longer needs a plugin release), but teammates install the skill from the plugin and have no
HQ checkout. client_config.py falls back to the plugin's clients/ directory — which on
2026-08-05 held 6 stale configs while HQ held 11. Manish could not have run capriottis,
abbys-bagels, counter-service, menya-ultra or mbfs at all: no config, no client.

So HQ stays the one place you edit, and this copies a generated snapshot into the plugin.
Editing the plugin copy by hand is pointless — the next publish overwrites it.

Usage:
  python3 references/publish_configs.py --check     # what would change, change nothing
  python3 references/publish_configs.py             # write the snapshot
  python3 references/publish_configs.py --repo /path/to/spice-team-skills

It writes files and stops. Committing and pushing stays a human decision.
"""
from __future__ import annotations

import argparse
import filecmp
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import client_config  # noqa: E402

DEFAULT_REPOS = [
    "~/hq/repos/private/spice-team-skills",
    "~/Desktop/spice-team-skills",
]
REL_CLIENTS = os.path.join("skills", "campaign-plan", "clients")

# Written beside the snapshot so the next person to open the folder knows not to edit it.
README = """# Generated — do not edit

These client configs are a published snapshot. The authoritative copies live in HQ at
`companies/spice/skills/campaign-plan/clients/`, and `client_config.py` prefers those when
an HQ checkout is present.

They are shipped here because teammates install the skill from this plugin and have no HQ
checkout — without the snapshot, a client that exists in HQ simply does not exist for them.

To change a client: edit it in HQ (or re-run `provision.py`), then run

    python3 references/publish_configs.py

and commit the result. Editing a file in this directory by hand will be overwritten by the
next publish.
"""


def hq_clients_dir() -> str | None:
    """The authoritative HQ clients directory, if this checkout has one."""
    for path, origin in client_config.search_path():
        if origin == "hq" and os.path.isdir(path):
            return path
    return None


def find_repo(explicit: str | None) -> str | None:
    for cand in ([explicit] if explicit else []) + DEFAULT_REPOS:
        if not cand:
            continue
        p = os.path.expanduser(cand)
        if os.path.isdir(os.path.join(p, "skills", "campaign-plan")):
            return p
    return None


# Keys whose values are specific to the machine that wrote them. `output` is the worst
# offender: every HQ config points at /Users/maxx/Downloads/..., a path that does not exist
# on a teammate's Mac. Stripped on publish so the skill falls back to the client's data dir.
MACHINE_SPECIFIC_KEYS = ("output",)


def sanitize(cfg: dict) -> dict:
    """The config as teammates should receive it — no paths from someone else's laptop."""
    return {k: v for k, v in cfg.items() if k not in MACHINE_SPECIFIC_KEYS}


def _read_sanitized(path: str) -> dict:
    with open(path) as fh:
        return sanitize(json.load(fh))


def _write(path: str, cfg: dict) -> None:
    with open(path, "w") as fh:
        json.dump(cfg, fh, indent=2)
        fh.write("\n")


def plan(src: str, dst: str) -> tuple[list, list, list]:
    """(added, changed, unchanged) config filenames, comparing HQ against the snapshot."""
    added, changed, unchanged = [], [], []
    for name in sorted(os.listdir(src)):
        if not name.endswith(".json"):
            continue
        a, b = os.path.join(src, name), os.path.join(dst, name)
        if not os.path.exists(b):
            added.append(name)
            continue
        # Compare the sanitized forms — an `output` path that differs only because it names
        # someone's home directory is not a real change to publish.
        try:
            with open(b) as fh:
                current = json.load(fh)
            # A snapshot still carrying a stripped key was published before sanitizing and
            # must be rewritten, even though the sanitized forms compare equal.
            dirty = any(k in current for k in MACHINE_SPECIFIC_KEYS)
            same = not dirty and _read_sanitized(a) == sanitize(current)
        except json.JSONDecodeError:
            same = filecmp.cmp(a, b, shallow=False)
        (unchanged if same else changed).append(name)
    return added, changed, unchanged


def stale_in_snapshot(src: str, dst: str) -> list:
    """Configs in the snapshot that no longer exist in HQ — reported, never auto-deleted."""
    if not os.path.isdir(dst):
        return []
    hq = {n for n in os.listdir(src) if n.endswith(".json")}
    return sorted(n for n in os.listdir(dst) if n.endswith(".json") and n not in hq)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=None, help="path to the spice-team-skills checkout")
    ap.add_argument("--check", action="store_true", help="report only, change nothing")
    args = ap.parse_args()

    src = hq_clients_dir()
    if not src:
        sys.exit("no HQ clients directory found — run this from an HQ checkout.")

    repo = find_repo(args.repo)
    if not repo:
        sys.exit("no spice-team-skills checkout found. Pass --repo /path/to/spice-team-skills.")
    dst = os.path.join(repo, REL_CLIENTS)

    added, changed, unchanged = plan(src, dst)
    stale = stale_in_snapshot(src, dst)

    print(f"HQ:       {src}")
    print(f"snapshot: {dst}")
    for name in added:
        print(f"  + {name[:-5]}  (teammates cannot run this client today)")
    for name in changed:
        print(f"  ~ {name[:-5]}")
    if unchanged:
        print(f"  = {len(unchanged)} already current")
    for name in stale:
        print(f"  ! {name[:-5]} is in the snapshot but not in HQ — remove it by hand if the "
              "client is gone; not deleted automatically in case HQ is the incomplete one")

    if not added and not changed:
        print("\nnothing to publish.")
        return 0
    if args.check:
        print(f"\n--check: nothing was written. {len(added) + len(changed)} file(s) would change.")
        return 0

    os.makedirs(dst, exist_ok=True)
    for name in added + changed:
        _write(os.path.join(dst, name), _read_sanitized(os.path.join(src, name)))
    with open(os.path.join(dst, "README.md"), "w") as fh:
        fh.write(README)

    print(f"\npublished {len(added) + len(changed)} config(s) + README.md")
    print("Review and commit in the plugin repo — this script does not commit or push.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
