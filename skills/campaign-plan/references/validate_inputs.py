#!/usr/bin/env python3
"""Input-validation gate for the campaign-plan refresh — refuses to publish when a required
platform export is missing, the wrong report type, or truncated. The enforcement point: we can't
stop a bad file landing in Drive, but we can stop it reaching the client Sheet.

Recognition is delegated to `export_router` (by COLUMN SIGNATURE, not filename) — the same module
the loader uses, so the gate and the loader can never disagree about what a file is. A wrong-type
upload (e.g. the UE by-location summary instead of the per-campaign daily export) shows up as the
required export MISSING plus a named explanation of what was actually uploaded.

Enforcement is opt-in per client: `required_exports` in the client config lists the keys that MUST
be present (errors → no publish). Absent → advisory (warnings only), so clients running fewer
platforms aren't wrongly blocked.
"""
from __future__ import annotations
import csv
import os

import export_router as er

# Name column per consumable export, for the truncation check.
NAME_COL = {"ue_sl": "Campaign name", "dd_sl": "Campaign name",
            "dd_promo": "Campaign name", "ue_offers": "Offer type"}
LABELS = {k: lbl for (k, role, lbl, _m, _n) in er.SIGNATURES if role}  # consumable labels


def _names_and_count(path, name_col):
    """Return (list of values in the name column, row count). Case-insensitive column lookup."""
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as fh:
        r = csv.DictReader(fh)
        cols = [c.strip() for c in (r.fieldnames or [])]
        col = {c.lower(): c for c in cols}.get((name_col or "").lower())
        names, n = [], 0
        for row in r:
            n += 1
            if col:
                names.append((row.get(col) or "").strip())
        return names, n


def validate(inputs_dir: str, required_exports=None) -> dict:
    """Returns {ok, errors, warnings, report}. errors non-empty → refuse to publish.
    required_exports: consumable keys that MUST be present (default: all four)."""
    required = required_exports if required_exports is not None else sorted(er.CONSUMABLE)
    matched, problems = er.route(inputs_dir)
    errors, warnings, lines = [], [], []

    for key in sorted(er.CONSUMABLE):
        lbl = LABELS.get(key, key)
        is_req = key in required
        if key in matched:
            path = matched[key][0]
            fname = os.path.basename(path)
            names, nrows = _names_and_count(path, NAME_COL.get(key, ""))
            probs = []
            if nrows == 0:
                probs.append("no data rows")
            trunc = [x for x in names if x.count("(") > x.count(")")]
            if trunc:
                probs.append(f"{len(trunc)} truncated name(s) (e.g. '{trunc[0][:36]}…') — report cut off, re-export")
            if probs:
                (errors if is_req else warnings).append(f"BAD {lbl} ({fname}): {'; '.join(probs)}")
                lines.append(f"  ❌ {lbl}: {fname} — {'; '.join(probs)}")
            else:
                lines.append(f"  ✅ {lbl}: {fname} ({nrows} rows)")
        else:
            (errors if is_req else warnings).append(f"MISSING {lbl} — export from {er.SOURCE.get(key, '')}")
            lines.append(f"  {'❌' if is_req else '⚠️ '} {lbl}: not found")

    for pr in problems:  # wrong-type + unrecognized files surfaced by the router
        warnings.append(pr)
        lines.append(f"  ⚠️  {pr}")

    ok = not errors
    report = "Input validation (recognized by content, not filename):\n" + "\n".join(lines)
    if errors:
        report += ("\n\nREFUSING TO PUBLISH — fix the input(s) above and re-run:\n"
                   + "\n".join(f"  • {e}" for e in errors))
    if warnings:
        report += "\n\nWarnings (not blocking):\n" + "\n".join(f"  • {w}" for w in warnings)
    return {"ok": ok, "errors": errors, "warnings": warnings, "report": report}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", required=True, help="inputs dir to validate")
    ap.add_argument("--required", default=None, help="comma-sep export keys (default: all four)")
    args = ap.parse_args()
    req = args.required.split(",") if args.required else None
    res = validate(args.inputs, req)
    print(res["report"])
    raise SystemExit(0 if res["ok"] else 2)


if __name__ == "__main__":
    main()
