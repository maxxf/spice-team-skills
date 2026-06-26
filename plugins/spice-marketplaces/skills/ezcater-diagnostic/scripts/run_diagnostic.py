#!/usr/bin/env python3
"""CLI runner for the ezCater catering diagnostic.

    python3 scripts/run_diagnostic.py --client tiffs-treats --inputs-dir <dir> [--json out.json]

Writes a markdown report to stdout (and optional JSON result to --json).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running from the skill root without install.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ezcater_diagnostic import report, run  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--inputs-dir", required=True, type=Path)
    ap.add_argument("--json", type=Path, default=None, help="optional path to write the full result JSON")
    args = ap.parse_args()

    result = run.run_from_inputs_dir(args.inputs_dir, client=args.client)
    if args.json:
        args.json.write_text(json.dumps(result, indent=2, sort_keys=True))
    print(report.render_markdown(result))


if __name__ == "__main__":
    main()
