"""CLI entry. Orchestrator dispatches via subprocess."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from diagnostic_ops import compute


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--window-start", required=True)
    ap.add_argument("--window-end", required=True)
    ap.add_argument("--inputs-dir", required=True, type=Path)
    ap.add_argument("--output-path", required=True, type=Path)
    args = ap.parse_args()

    csvs = sorted(args.inputs_dir.glob("*.csv"))
    if not csvs:
        raise SystemExit(f"no input CSVs found in {args.inputs_dir}")
    df = pd.concat([pd.read_csv(c) for c in csvs], ignore_index=True)

    payload = compute.run(
        client=args.client,
        window_start=args.window_start,
        window_end=args.window_end,
        df=df,
    )
    args.output_path.write_text(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
