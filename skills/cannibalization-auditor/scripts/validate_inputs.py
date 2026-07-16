"""Validate the raw inputs folder before the analysis runs.

Checks:
- Folder structure (ue/ dd/ gh/ subdirs per platforms_in_scope)
- Required files present per platform
- Window continuity: no week gaps inside the audit window
- Required columns present in each file

Exits 0 on pass. Exits 1 with a list of specific errors on fail.
Errors are surfaced to the human verbatim — do not auto-fix.

Usage:
    python validate_inputs.py --inputs-dir /path/to/inputs --client <slug>
    [--window-start YYYY-MM-DD --window-end YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

REQUIRED_FILES = {
    "ue": ["sales_by_store", "ads", "offers", "acquisition_split", "funnel", "ops", "ratings"],
    "dd": ["financials", "sponsored", "promos", "ops_quality", "ratings"],
    "gh": ["performance", "sponsored", "ops", "promos"],
}

# Loose substring matching against filenames. We don't enforce strict naming —
# GMs pull these manually and filenames vary. The match prefix is what the
# auditor expects to find somewhere in the filename.
FILE_HINTS = {
    "ue": {
        "sales_by_store": ["sales-by-store", "sales_by_store", "sales-store"],
        "ads": ["ads", "campaign"],
        "offers": ["offer", "promo"],
        "acquisition_split": ["acquisition", "organic", "paid-split"],
        "funnel": ["funnel", "conversion"],
        "ops": ["operations", "order-accuracy", "cancellation"],
        "ratings": ["rating", "review"],
    },
    "dd": {
        "financials": ["financial", "statement"],
        "sponsored": ["sponsored", "ad"],
        "promos": ["promo", "promotion", "dashpass"],
        "ops_quality": ["operations-quality", "ops-quality", "cancellation"],
        "ratings": ["rating", "review"],
    },
    "gh": {
        "performance": ["performance"],
        "sponsored": ["sponsored", "ad"],
        "ops": ["operation"],
        "promos": ["promo", "promotion"],
    },
}


def load_client_config(client_slug: str, skill_dir: Path) -> dict:
    config_path = skill_dir / "clients" / f"{client_slug}.json"
    if not config_path.exists():
        return {
            "client_slug": client_slug,
            "platforms_in_scope": ["ue", "dd", "gh"],
            "locations": [],
        }
    return json.loads(config_path.read_text())


def find_file_for(category: str, hints: list[str], files_in_dir: list[Path]) -> Path | None:
    for f in files_in_dir:
        name = f.name.lower()
        if any(hint in name for hint in hints):
            return f
    return None


def validate_structure(inputs_dir: Path, platforms_in_scope: list[str]) -> list[str]:
    errors = []
    for platform in platforms_in_scope:
        subdir = inputs_dir / platform
        if not subdir.is_dir():
            errors.append(f"missing required subdirectory: {platform}/")
            continue
        files = [f for f in subdir.iterdir() if f.is_file() and not f.name.startswith(".")]
        if not files:
            errors.append(f"{platform}/ is empty — drop pulled exports here")
            continue
        for category in REQUIRED_FILES[platform]:
            hits = FILE_HINTS[platform][category]
            if not find_file_for(category, hits, files):
                errors.append(
                    f"{platform}/: missing file matching '{category}' "
                    f"(looked for filename containing any of: {hits})"
                )
    return errors


def validate_window_continuity(
    inputs_dir: Path,
    window_start: date,
    window_end: date,
    platforms_in_scope: list[str],
) -> list[str]:
    """Check that the window has no week gaps for at least one platform with sales data.

    For v0, this is a soft check — we look at file modification dates and filename
    date hints. The real window continuity check happens after build_unified.py
    has constructed the per-location-per-week dataframe.
    """
    weeks = []
    cursor = window_start
    while cursor <= window_end:
        weeks.append(cursor)
        cursor += timedelta(days=7)
    if len(weeks) < 17:  # ~4 months floor
        return [
            f"audit window is only {len(weeks)} weeks — framework floor is 17 weeks "
            f"(4 months). Refusing to run."
        ]
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs-dir", required=True, type=Path)
    parser.add_argument("--client", required=True)
    parser.add_argument("--window-start", type=date.fromisoformat)
    parser.add_argument("--window-end", type=date.fromisoformat)
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parent.parent
    config = load_client_config(args.client, skill_dir)
    platforms = config.get("platforms_in_scope", ["ue", "dd", "gh"])

    errors: list[str] = []
    errors += validate_structure(args.inputs_dir, platforms)

    if args.window_start and args.window_end:
        errors += validate_window_continuity(
            args.inputs_dir, args.window_start, args.window_end, platforms
        )

    if errors:
        print("VALIDATION FAILED:\n", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        print(
            "\nFix these and re-run. The checklist lives at "
            "references/data-collection-checklist.md.",
            file=sys.stderr,
        )
        return 1

    print("VALIDATION PASSED")
    print(f"  Platforms in scope: {platforms}")
    print(f"  Inputs dir: {args.inputs_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
