#!/usr/bin/env python3
"""Strategy-session write layer — the ONE authorized writer for Q-plan tabs.

Writes the approved rolling roadmap grid into the Q-plan tab(s) its window spans,
and persists the approved tier_strategy block to clients/<slug>.json.

Safety protocol (spec §6.2):
  --check          dry run: report each target tab's existing content ("empty" or rows),
                   write NOTHING.
  (default)        write tabs that are empty; REFUSE non-empty tabs.
  --overwrite      write all target tabs (Claude must have shown the user the diff and
                   gotten an explicit confirm in chat before passing this).

Usage:
  python strategy_write.py --client <slug> --grid grid.json [--check|--overwrite]
  python strategy_write.py --client <slug> --config tier_strategy.json   # config only
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import re
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TIER_ORDER = ["Top", "Mid", "Low", "New", "Red"]
FIRST_WEEK_COL = 3  # cols: 0=Tier 1=Location 2=Platform 3..=weeks
PLATFORM_ORDER = ["DD", "UE", "GH", "1P", "—"]
PLATFORM_COLORS = {  # brand-colored platform labels inside the tier tint bands
    "DD": {"red": 0.78, "green": 0.10, "blue": 0.10},
    "UE": {"red": 0.02, "green": 0.43, "blue": 0.13},
    "GH": {"red": 0.85, "green": 0.40, "blue": 0.00},
}

# Visual tier coding — emoji in the Tier column + a soft row tint per tier block, so the
# grid reads at a glance. Same emoji set as the Notion strategy page.
TIER_META = {
    "Top": ("🟢", {"red": 0.85, "green": 0.94, "blue": 0.83}),
    "Mid": ("🔵", {"red": 0.84, "green": 0.90, "blue": 0.97}),
    "Low": ("🟠", {"red": 1.00, "green": 0.93, "blue": 0.80}),
    "New": ("🟣", {"red": 0.93, "green": 0.88, "blue": 0.96}),
    "Red": ("🔴", {"red": 0.98, "green": 0.86, "blue": 0.84}),
}


def tier_label(tier: str) -> str:
    emoji = TIER_META.get(tier, ("", None))[0]
    return f"{emoji} {tier}".strip()


def tier_row_spans(matrix: list) -> list:
    """[(tier, start_row, end_row_exclusive), ...] — 0-indexed rows of each tier block in a
    built tab matrix (data starts at row 3; a block runs until the next tier label)."""
    spans, cur, start = [], None, None
    for i in range(3, len(matrix)):
        label = str(matrix[i][0]).strip() if matrix[i] else ""
        tier = label.split()[-1] if label else None  # '🟢 Top' -> 'Top'
        if tier:
            if cur:
                spans.append((cur, start, i))
            cur, start = tier, i
    if cur:
        spans.append((cur, start, len(matrix)))
    return spans


def window_weeks(start: str, n_weeks: int = 13) -> list[str]:
    d = dt.date.fromisoformat(start)
    d -= dt.timedelta(days=d.weekday())          # snap to Monday
    return [(d + dt.timedelta(weeks=i)).isoformat() for i in range(n_weeks)]


def split_by_quarter(weeks: list[str]) -> dict:
    """{ 'Q3 Plan': [mondays...] } — tab names match FORWARD_PLAN_TABS convention.
    NOTE: keys carry no year — a window reaching January targets 'Q1 Plan' of whatever
    year's tab exists; the --check/--overwrite protocol surfaces any collision."""
    out: dict = {}
    for w in weeks:
        q = (dt.date.fromisoformat(w).month - 1) // 3 + 1
        out.setdefault(f"Q{q} Plan", []).append(w)
    return out


def _wk_label(w: str) -> str:
    d = dt.date.fromisoformat(w)
    return f"W{d.isocalendar()[1]} {d.strftime('%-m/%-d')}"


def build_tab_matrix(tab: str, weeks: list[str], grid: dict, client: str, year: int) -> list:
    """Canonical Q-plan grid (spec §6.2 pinned format). Rows carry an optional "platform"
    key ("DD"/"UE"/"GH"/"1P") — each location renders one lane per platform it runs, so every
    cell maps 1:1 to a per-platform campaign. Rows without "platform" get a single "—" lane."""
    events = {e["week"]: e["label"] for e in grid.get("events", [])}
    head = [f"{tab.split(' ')[0]} {year} Plan — {client}  (roadmap {grid['window']['start']} → {grid['window']['end']})"]
    band = ["", "Events:", ""] + [events.get(w, "") for w in weeks]
    hdr = ["Tier", "Location", "Platform"] + [_wk_label(w) for w in weeks]
    m = [head, band, hdr]
    rows = grid.get("rows", [])

    def _pkey(r):
        p = r.get("platform", "—")
        return PLATFORM_ORDER.index(p) if p in PLATFORM_ORDER else len(PLATFORM_ORDER)

    for tier in TIER_ORDER:
        trows = [r for r in rows if r.get("tier") == tier]
        if not trows:
            continue
        first_of_tier = True
        for loc in sorted({r["location"] for r in trows}):
            lrows = sorted([r for r in trows if r["location"] == loc], key=_pkey)
            for j, r in enumerate(lrows):
                cells = r.get("cells", {})
                m.append([tier_label(tier) if (first_of_tier and j == 0) else "",
                          loc if j == 0 else "", r.get("platform", "—")]
                         + [cells.get(w, "—") for w in weeks])
            first_of_tier = False
    return m


def paint_tier_bands(sw, sheet_id: str, tab: str, matrix: list, n_cols: int) -> None:
    """Apply each tier block's soft tint across its rows, plus brand-colored bold platform
    labels (DD red / UE green / GH orange). Runs AFTER write_full_tab (which format-resets
    the tab), so this layers on top of the standard header styling."""
    gid = sw._tab_gid(sheet_id, tab)
    reqs = []
    for tier, r0, r1 in tier_row_spans(matrix):
        color = TIER_META.get(tier, (None, None))[1]
        if not color:
            continue
        reqs.append({"repeatCell": {
            "range": {"sheetId": gid, "startRowIndex": r0, "endRowIndex": r1,
                      "startColumnIndex": 0, "endColumnIndex": n_cols},
            "cell": {"userEnteredFormat": {"backgroundColor": color}},
            "fields": "userEnteredFormat.backgroundColor"}})
    for i in range(3, len(matrix)):
        plat = str(matrix[i][2]).strip() if len(matrix[i]) > 2 else ""
        fg = PLATFORM_COLORS.get(plat)
        if not fg:
            continue
        reqs.append({"repeatCell": {
            "range": {"sheetId": gid, "startRowIndex": i, "endRowIndex": i + 1,
                      "startColumnIndex": 2, "endColumnIndex": 3},
            "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": fg}}},
            "fields": "userEnteredFormat.textFormat"}})
    # ---- Layout polish (same batch): merged title, sized columns, wrapped cells,
    # centered platform labels, divider border under each tier block ----
    n_rows = len(matrix)
    widths = [(0, 1, 80), (1, 2, 150), (2, 3, 64), (3, n_cols, 170)]  # Tier·Loc·Platform·weeks
    for c0, c1, px in widths:
        reqs.append({"updateDimensionProperties": {
            "range": {"sheetId": gid, "dimension": "COLUMNS", "startIndex": c0, "endIndex": c1},
            "properties": {"pixelSize": px}, "fields": "pixelSize"}})
    reqs.append({"mergeCells": {"mergeType": "MERGE_ALL", "range": {
        # merge can't cross the frozen-column boundary; title text overflows past it anyway
        "sheetId": gid, "startRowIndex": 0, "endRowIndex": 1,
        "startColumnIndex": 0, "endColumnIndex": FIRST_WEEK_COL}}})
    reqs.append({"repeatCell": {  # week cells: wrap + top-align so tactical strings read fully
        "range": {"sheetId": gid, "startRowIndex": 3, "endRowIndex": n_rows,
                  "startColumnIndex": FIRST_WEEK_COL, "endColumnIndex": n_cols},
        "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP", "verticalAlignment": "TOP",
                                       "textFormat": {"fontSize": 9}}},
        "fields": "userEnteredFormat(wrapStrategy,verticalAlignment,textFormat.fontSize)"}})
    reqs.append({"repeatCell": {  # events band wraps too
        "range": {"sheetId": gid, "startRowIndex": 1, "endRowIndex": 2,
                  "startColumnIndex": FIRST_WEEK_COL, "endColumnIndex": n_cols},
        "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP", "textFormat": {"italic": True, "fontSize": 9}}},
        "fields": "userEnteredFormat(wrapStrategy,textFormat)"}})
    reqs.append({"repeatCell": {  # platform labels centered
        "range": {"sheetId": gid, "startRowIndex": 3, "endRowIndex": n_rows,
                  "startColumnIndex": 2, "endColumnIndex": 3},
        "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER", "verticalAlignment": "TOP"}},
        "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment)"}})
    for _, _, r1 in tier_row_spans(matrix):  # divider under each tier block
        reqs.append({"updateBorders": {
            "range": {"sheetId": gid, "startRowIndex": r1 - 1, "endRowIndex": r1,
                      "startColumnIndex": 0, "endColumnIndex": n_cols},
            "bottom": {"style": "SOLID_MEDIUM", "color": {"red": 0.55, "green": 0.55, "blue": 0.55}}}})
    if reqs:
        sw._service().spreadsheets().batchUpdate(spreadsheetId=sheet_id,
                                                 body={"requests": reqs}).execute()


def _resolve_tab(sw, sheet_id: str, q_tab: str) -> str:
    """Map a computed 'Q3 Plan' name onto the sheet's actual tab if it exists under a naming
    variant ('Q3 Plan', 'Q3 2026 Plan', 'Q3 Plan 2026'). Returns the existing name, or q_tab
    unchanged (caller will create it)."""
    qn = q_tab.split(" ")[0]  # 'Q3'
    pat = re.compile(rf"^{qn}\s*(20\d\d)?\s*Plan(\s*20\d\d)?$", re.I)
    for name in sw.get_metadata(sheet_id)["tabs"]:
        if pat.match(name.strip()):
            return name
    return q_tab


def _existing(sw, sheet_id: str, tab: str):
    """Current content of a tab, or None ONLY if the tab doesn't exist. Auth/quota errors
    must surface, not silently route into tab creation."""
    try:
        vals = sw.read_range(sheet_id, f"'{tab}'!A1:Z60")
    except Exception as e:
        if "Unable to parse range" in str(e) or getattr(getattr(e, "resp", None), "status", None) == 400:
            return None  # tab genuinely missing
        raise
    return [r for r in (vals or []) if any(str(c).strip() for c in r)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--grid", help="path to grid JSON (spec §Interfaces)")
    ap.add_argument("--config", help="path to tier_strategy JSON to persist")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg_path = os.path.join(root, "clients", f"{args.client}.json")
    cfg = json.load(open(cfg_path))

    if args.config:
        block = json.load(open(args.config))
        # MERGE into the existing block — Phase S calls --config several times (tier gate
        # writes `locations`, strategy gate writes `tiers`, write phase caches Notion ids);
        # a replace here would clobber the earlier gates' output.
        cur = cfg.get("tier_strategy") or {}
        cur.update(block)
        cur["updated"] = dt.date.today().isoformat()
        cfg["tier_strategy"] = cur
        json.dump(cfg, open(cfg_path, "w"), indent=2)
        print(f"config: tier_strategy keys merged: {sorted(block.keys())}")

    if not args.grid:
        return
    import sheets_writer as sw
    grid = json.load(open(args.grid))
    weeks = grid.get("weeks") or window_weeks(grid["window"]["start"])
    sheet_id = cfg["sheet_id"]
    client = cfg.get("client_display_name", args.client)
    by_tab = split_by_quarter(weeks)

    for q_tab, tab_weeks in by_tab.items():
        year = dt.date.fromisoformat(tab_weeks[0]).year
        tab = _resolve_tab(sw, sheet_id, q_tab)
        existing = _existing(sw, sheet_id, tab)
        if args.check:
            n = len(existing) if existing else 0
            print(f"{tab}: {'MISSING (will create)' if existing is None else ('empty' if n == 0 else f'{n} non-empty rows')}")
            if existing:
                for r in existing[:6]:
                    print("   |", " · ".join(str(c) for c in r[:6]))
            continue
        if existing and not args.overwrite:
            sys.exit(f"REFUSING: '{tab}' has {len(existing)} non-empty rows. Re-run with "
                     f"--overwrite after the user confirms replacement (show them --check first).")
        if existing is None:
            sw.create_tab(sheet_id, tab, allow_protected=True)
        matrix = build_tab_matrix(tab, tab_weeks, grid, client, year)
        n = sw.write_full_tab(sheet_id, tab, matrix, section_header_rows=[1],
                              col_header_rows=[2], freeze_rows=3, freeze_cols=3,
                              title_rows=1, allow_protected=True)
        paint_tier_bands(sw, sheet_id, tab, matrix, n_cols=FIRST_WEEK_COL + len(tab_weeks))
        print(f"{tab}: wrote {n} rows ({len(tab_weeks)} weeks, tier bands painted)")


if __name__ == "__main__":
    main()
