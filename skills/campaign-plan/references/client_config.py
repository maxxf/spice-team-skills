#!/usr/bin/env python3
"""Client config resolution — HQ first, plugin bundle as fallback.

Why this exists: configs used to live only inside the plugin bundle, so adding a
client meant committing to both shipped paths and bumping the plugin version.
Santi built three configs on 2026-06-26 and could not ship them himself. Now the
HQ copy wins and is editable in place by whoever onboards the client.

Resolution order (first hit wins):

  1. $SPICE_CAMPAIGN_CLIENTS            — explicit override, for tests
  2. <hq_root>/companies/spice/skills/campaign-plan/clients/   — HQ, authoritative
  3. <skill_dir>/clients/               — plugin bundle, legacy fallback

The HQ root is found by walking up from this file looking for companies/manifest.yaml,
then falling back to $HQ_ROOT and ~/hq. When this file already lives under HQ, step 2
and step 3 are the same directory and resolution is trivially correct.

Usage:
    from client_config import resolve, load, available
    path, source = resolve("goop-kitchen")
    cfg = load("goop-kitchen")
    for slug, path, source in available(): ...
"""
from __future__ import annotations

import json
import os
from typing import Iterator, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)

REL_HQ_CLIENTS = os.path.join("companies", "spice", "skills", "campaign-plan", "clients")


def _hq_root() -> Optional[str]:
    """Locate the HQ root: walk up for companies/manifest.yaml, then $HQ_ROOT, then ~/hq."""
    d = HERE
    while True:
        if os.path.isfile(os.path.join(d, "companies", "manifest.yaml")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent

    for cand in (os.environ.get("HQ_ROOT"), os.path.expanduser("~/hq")):
        if cand and os.path.isfile(os.path.join(cand, "companies", "manifest.yaml")):
            return cand
    return None


def search_path() -> list[Tuple[str, str]]:
    """Ordered [(directory, source_label)] the resolver will consult.

    Duplicate directories are collapsed, keeping the highest-priority label — so a
    skill installed inside HQ reports 'hq' rather than 'plugin'.
    """
    candidates: list[Tuple[str, str]] = []

    override = os.environ.get("SPICE_CAMPAIGN_CLIENTS")
    if override:
        candidates.append((os.path.expanduser(override), "env"))

    root = _hq_root()
    if root:
        candidates.append((os.path.join(root, REL_HQ_CLIENTS), "hq"))

    candidates.append((os.path.join(SKILL, "clients"), "plugin"))

    seen: dict[str, str] = {}
    ordered: list[Tuple[str, str]] = []
    for path, label in candidates:
        real = os.path.realpath(path)
        if real in seen:
            continue
        seen[real] = label
        ordered.append((path, label))
    return ordered


def resolve(slug: str) -> Tuple[Optional[str], Optional[str]]:
    """Return (config_path, source_label) for a client slug, or (None, None)."""
    for directory, label in search_path():
        candidate = os.path.join(directory, f"{slug}.json")
        if os.path.isfile(candidate):
            return candidate, label
    return None, None


def load(slug: str) -> dict:
    """Load a client config. Raises FileNotFoundError naming every place we looked."""
    path, source = resolve(slug)
    if not path:
        looked = "\n  ".join(f"{lbl}: {d}" for d, lbl in search_path())
        raise FileNotFoundError(
            f"no config for client '{slug}'. Looked in:\n  {looked}\n"
            f"Create one with: python3 references/new_client.py --slug {slug} ..."
        )
    with open(path) as f:
        cfg = json.load(f)
    cfg.setdefault("client_slug", slug)
    cfg["_config_path"] = path
    cfg["_config_source"] = source
    return cfg


def write_dir() -> str:
    """Directory new configs should be written to — HQ when available, else the bundle."""
    for directory, label in search_path():
        if label in ("env", "hq"):
            return directory
    return os.path.join(SKILL, "clients")


def available() -> Iterator[Tuple[str, str, str]]:
    """Yield (slug, path, source) for every resolvable client, highest priority first.

    A slug found in more than one directory is yielded once, from the winning source.
    """
    seen: set[str] = set()
    for directory, label in search_path():
        if not os.path.isdir(directory):
            continue
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".json"):
                continue
            slug = name[:-5]
            if slug in seen:
                continue
            seen.add(slug)
            yield slug, os.path.join(directory, name), label


if __name__ == "__main__":
    print("resolution order:")
    for directory, label in search_path():
        marker = "OK " if os.path.isdir(directory) else "-- "
        print(f"  {marker}{label:7} {directory}")
    print("\nclients:")
    for slug, path, source in available():
        print(f"  {slug:16} [{source}]")
