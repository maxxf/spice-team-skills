#!/usr/bin/env python3
"""Holiday lookahead for the Spice team.

Reads team-roster.yaml, looks N days ahead (default 7), and reports any
*national* public holiday landing on the target date for any country a team
member lives in. Prints a JSON array to stdout (empty == nothing to announce).

No Slack logic here on purpose — the skill agent handles posting. This stays
unit-testable: pass --date YYYY-MM-DD to simulate "today".

Usage:
  python check_holidays.py
  python check_holidays.py --date 2026-07-04 --lookahead 7
  python check_holidays.py --roster /path/to/team-roster.yaml
"""

import argparse
import datetime as dt
import json
import os
import sys

DEFAULT_ROSTER = os.path.join(
    os.path.dirname(__file__), "..", "..", "team-roster.yaml"
)
# Manual supplement for countries the `holidays` library can't yet cover for the
# target year (notably LK — Sri Lanka gazettes its lunar Poya holidays late).
MANUAL_FILE = os.path.join(os.path.dirname(__file__), "manual_holidays.yaml")


def load_roster(path):
    import yaml  # PyYAML — ships with most envs; pip install pyyaml if missing

    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}
    members = data.get("team", []) or []
    by_country = {}
    for m in members:
        country = (m.get("country") or "").strip().upper()
        if not country:
            continue
        by_country.setdefault(country, []).append(
            {"name": m.get("name", "?"), "slack": m.get("slack", "")}
        )
    return by_country


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roster", default=DEFAULT_ROSTER)
    ap.add_argument("--date", help="Override today (YYYY-MM-DD) for testing")
    ap.add_argument("--lookahead", type=int, default=7)
    args = ap.parse_args()

    try:
        import holidays  # pip install holidays
    except ImportError:
        print(
            json.dumps({"error": "missing dependency: pip install holidays pyyaml"}),
            file=sys.stderr,
        )
        sys.exit(2)

    today = (
        dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    )
    target = today + dt.timedelta(days=args.lookahead)

    # Optional manual supplement: { "LK": { "2026-02-04": "Independence Day", ... } }
    manual = {}
    if os.path.exists(MANUAL_FILE):
        import yaml

        with open(MANUAL_FILE, "r") as f:
            manual = (yaml.safe_load(f) or {}).get("holidays", {}) or {}

    by_country = load_roster(args.roster)
    results = []
    warnings = []
    for country, members in sorted(by_country.items()):
        name = None
        try:
            # No subdiv => national/federal calendar only.
            cal = holidays.country_holidays(country, years=target.year)
        except NotImplementedError:
            cal = {}
        if len(cal) == 0:
            # Library has no data for this country/year. Fall back to manual list
            # and flag the gap so a human can fill it from the official gazette.
            warnings.append(
                f"{country}: no library holiday data for {target.year} — "
                f"relying on manual_holidays.yaml. Verify it is populated."
            )
        name = cal.get(target) or manual.get(country, {}).get(target.isoformat())
        if name:
            results.append(
                {
                    "country": country,
                    "holiday": name,
                    "date": target.isoformat(),
                    "weekday": target.strftime("%A"),
                    "members": members,
                }
            )

    for w in warnings:
        print(json.dumps({"warning": w}), file=sys.stderr)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
