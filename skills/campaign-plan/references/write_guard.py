#!/usr/bin/env python3
"""Write safety for the Sheets writer — snapshot, sanity gate, dry-run.

Why this exists: on 2026-06-16 the first live campaign-plan run wrote goop's Sheet
blank and was recovered only because someone noticed and used Google's version
history. The mechanism is still in `write_full_tab`, which clears a tab's values
*before* checking whether it has anything to write. This module makes that class
of failure unreachable.

Three guarantees, all enforced at the one chokepoint every destructive write goes
through:

  1. SNAPSHOT — the region is read and written to local disk before it is cleared.
  2. GATE     — a write that would empty a populated tab, or shrink it past a
                threshold, is refused before the clear happens.
  3. DRY RUN  — the whole thing can be rendered as a diff with nothing written.

Snapshots are local, not in Drive, deliberately. The service account is a
Contributor on the shared drive: it can create and trash but `canDelete` is false,
so Drive-side snapshots would pile up in a trash the robot cannot empty. Local
files prune cleanly. Google's own version history remains the deep backstop; these
snapshots exist for fast programmatic restore.

CLI:
  python3 write_guard.py list    --sheet-id <id> [--tab <tab>]
  python3 write_guard.py show    --sheet-id <id> --tab <tab> [--at <stamp>]
  python3 write_guard.py restore --sheet-id <id> --tab <tab> [--at <stamp>] [--yes]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Optional

# Fraction of rows that may disappear in one write before the gate refuses.
# 0.40 => a tab going 50 rows -> 28 passes, 50 -> 12 is blocked. Campaign tabs
# legitimately shrink as campaigns end, so a stricter setting trains people to
# reach for --force-shrink, which defeats the gate.
SHRINK_THRESHOLD = 0.40

# Snapshots retained per (sheet, tab). ~2 months of weekly refreshes.
RETAIN_PER_TAB = 10

STATE_DIR = os.path.expanduser(
    os.environ.get(
        "SPICE_SNAPSHOT_DIR", "~/.local/state/spice/campaign-plan/snapshots"
    )
)


class WriteBlocked(Exception):
    """Raised instead of performing a write that fails the sanity gate."""


# ---------------------------------------------------------------- helpers


def _slug(s: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in s)[:80]


def _tab_dir(sheet_id: str, tab: str) -> str:
    return os.path.join(STATE_DIR, _slug(sheet_id), _slug(tab))


def _nonempty_rows(values: list) -> int:
    """Rows containing at least one non-blank cell. Trailing blanks are not data."""
    return sum(1 for row in (values or []) if any(str(c).strip() for c in row))


def stamp(now: str) -> str:
    """Caller supplies the timestamp so this module stays deterministic and testable."""
    return now.replace(":", "").replace("-", "").replace(" ", "-")


# ---------------------------------------------------------------- snapshots


def save_snapshot(sheet_id: str, tab: str, values: list, when: str,
                  note: str = "") -> Optional[str]:
    """Persist the pre-write contents of a region. Returns the file path.

    Never raises into the caller's write path — a snapshot failure is logged and the
    gate still runs. Losing a snapshot is bad; blocking a legitimate refresh because
    the disk is full is worse.
    """
    try:
        d = _tab_dir(sheet_id, tab)
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, f"{stamp(when)}.json")
        with open(path, "w") as f:
            json.dump(
                {
                    "sheet_id": sheet_id,
                    "tab": tab,
                    "captured_at": when,
                    "note": note,
                    "rows": _nonempty_rows(values),
                    "values": values or [],
                },
                f,
            )
        prune(sheet_id, tab)
        return path
    except OSError as e:
        print(f"  warn: snapshot failed for '{tab}' ({e}) — write gate still applies",
              file=sys.stderr)
        return None


def list_snapshots(sheet_id: str, tab: str) -> list[str]:
    """Snapshot file paths for a tab, newest first."""
    d = _tab_dir(sheet_id, tab)
    if not os.path.isdir(d):
        return []
    names = sorted((n for n in os.listdir(d) if n.endswith(".json")), reverse=True)
    return [os.path.join(d, n) for n in names]


def prune(sheet_id: str, tab: str, keep: int = RETAIN_PER_TAB) -> int:
    """Delete all but the newest `keep` snapshots. Returns how many were removed.

    These are ordinary local files, so a real delete is correct here — unlike Drive,
    where the robot can only trash.
    """
    removed = 0
    for path in list_snapshots(sheet_id, tab)[keep:]:
        try:
            os.remove(path)
            removed += 1
        except OSError as e:
            print(f"  warn: could not prune {path}: {e}", file=sys.stderr)
    return removed


def load_snapshot(sheet_id: str, tab: str, at: Optional[str] = None) -> Optional[dict]:
    """Load a snapshot by timestamp, or the newest one when `at` is omitted."""
    paths = list_snapshots(sheet_id, tab)
    if not paths:
        return None
    if at:
        want = stamp(at)
        paths = [p for p in paths if want in os.path.basename(p)]
        if not paths:
            return None
    with open(paths[0]) as f:
        snap = json.load(f)
    snap["_path"] = paths[0]
    return snap


# ---------------------------------------------------------------- the gate


def evaluate(tab: str, before: list, after: list,
             force_shrink: bool = False) -> dict:
    """Decide whether a write may proceed. Pure — no I/O, so it is trivially testable.

    Returns {"allow": bool, "reason": str, "before_rows": int, "after_rows": int}.
    """
    b, a = _nonempty_rows(before), _nonempty_rows(after)

    if b == 0:
        return {"allow": True, "reason": "target is empty or new — nothing to lose",
                "before_rows": b, "after_rows": a}

    if a == 0:
        return {
            "allow": False,
            "reason": (f"refusing to write '{tab}': the new content is empty but the tab "
                       f"currently holds {b} rows. This is the failure that blanked goop's "
                       f"Sheet on 2026-06-16 — it almost always means an upstream extraction "
                       f"returned nothing, not that the tab should be emptied."),
            "before_rows": b, "after_rows": a,
        }

    if a < b:
        drop = (b - a) / b
        if drop > SHRINK_THRESHOLD and not force_shrink:
            return {
                "allow": False,
                "reason": (f"refusing to write '{tab}': row count drops {b} -> {a} "
                           f"({drop:.0%}, threshold {SHRINK_THRESHOLD:.0%}). If this shrink "
                           f"is real — campaigns ended, locations closed — re-run with "
                           f"--force-shrink."),
                "before_rows": b, "after_rows": a,
            }

    return {"allow": True, "reason": "ok", "before_rows": b, "after_rows": a}


def render_diff(tab: str, before: list, after: list, preview_rows: int = 3) -> str:
    """Human-readable diff for --dry-run. Shows shape plus the first few rows."""
    b, a = _nonempty_rows(before), _nonempty_rows(after)
    delta = a - b
    arrow = f"{b} -> {a} rows" + (f" ({delta:+d})" if delta else " (unchanged)")
    out = [f"  {tab}: {arrow}"]
    for label, values in (("was", before), ("now", after)):
        rows = [r for r in (values or []) if any(str(c).strip() for c in r)][:preview_rows]
        if not rows:
            out.append(f"    {label}: (empty)")
            continue
        for r in rows:
            cells = " | ".join(str(c)[:18] for c in r[:6])
            out.append(f"    {label}: {cells}")
    return "\n".join(out)


# ---------------------------------------------------------------- CLI


def _fmt_snapshot_line(path: str) -> str:
    try:
        with open(path) as f:
            s = json.load(f)
        return f"  {os.path.basename(path)[:-5]:20} {s.get('rows', '?'):>5} rows  {s.get('note', '')}"
    except (OSError, json.JSONDecodeError) as e:
        return f"  {os.path.basename(path)} (unreadable: {e})"


def _cmd_list(args):
    if args.tab:
        tabs = [args.tab]
    else:
        d = os.path.join(STATE_DIR, _slug(args.sheet_id))
        if not os.path.isdir(d):
            print(f"no snapshots for {args.sheet_id}")
            return 0
        tabs = sorted(os.listdir(d))
    for t in tabs:
        paths = list_snapshots(args.sheet_id, t)
        print(f"{t} ({len(paths)})")
        for p in paths:
            print(_fmt_snapshot_line(p))
    return 0


def _cmd_show(args):
    snap = load_snapshot(args.sheet_id, args.tab, args.at)
    if not snap:
        print(f"no snapshot found for '{args.tab}'", file=sys.stderr)
        return 1
    print(f"{snap['_path']}\ncaptured {snap['captured_at']} — {snap['rows']} rows\n")
    for row in snap["values"][:25]:
        print("  " + " | ".join(str(c)[:20] for c in row[:8]))
    if len(snap["values"]) > 25:
        print(f"  ... {len(snap['values']) - 25} more rows")
    return 0


def _cmd_restore(args):
    snap = load_snapshot(args.sheet_id, args.tab, args.at)
    if not snap:
        print(f"no snapshot found for '{args.tab}'", file=sys.stderr)
        return 1

    print(f"Restoring '{args.tab}' from {snap['captured_at']} ({snap['rows']} rows).")
    print("This overwrites the tab's current contents.")
    if not args.yes:
        reply = input("Type the tab name to confirm: ").strip()
        if reply != args.tab:
            print("aborted — no changes made")
            return 1

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import sheets_writer as sw

    # Snapshot what we are about to overwrite, so a restore is itself reversible.
    current = sw.read_range(args.sheet_id, f"'{args.tab}'!A1:Z1000")
    save_snapshot(args.sheet_id, args.tab, current, args.now, note="pre-restore")

    sw.write_full_tab(args.sheet_id, args.tab, snap["values"],
                      skip_guard=True, now=args.now)
    print(f"restored '{args.tab}' — {snap['rows']} rows")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="list snapshots")
    p_list.add_argument("--sheet-id", required=True)
    p_list.add_argument("--tab", default=None)

    p_show = sub.add_parser("show", help="print a snapshot's contents")
    p_show.add_argument("--sheet-id", required=True)
    p_show.add_argument("--tab", required=True)
    p_show.add_argument("--at", default=None, help="timestamp (default: newest)")

    p_rest = sub.add_parser("restore", help="write a snapshot back into the Sheet")
    p_rest.add_argument("--sheet-id", required=True)
    p_rest.add_argument("--tab", required=True)
    p_rest.add_argument("--at", default=None, help="timestamp (default: newest)")
    p_rest.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    p_rest.add_argument("--now", default="restore", help="timestamp label for the pre-restore snapshot")

    args = ap.parse_args()
    return {"list": _cmd_list, "show": _cmd_show, "restore": _cmd_restore}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
