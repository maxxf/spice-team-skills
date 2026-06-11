#!/usr/bin/env python3
"""Sheets API writer for the campaign plan v2 — range-based, range-owned.

Replaces the v0.1 xlsx-import-and-replace flow (`push_to_sheet.py`) for clients on the v2
9-tab canonical structure. The contract is explicit:

  - The skill OWNS the named ranges in NAMED_RANGES (overwritten on every refresh).
  - The skill NEVER touches PROTECTED_TABS (Q2/Q3/Q4 forward plans, Notes) or rows
    already in Archive (it only appends new ended campaigns).

This preserves Ro's forward planning, Santi's archive curation, and any client comments
across refreshes — which xlsx-replace would clobber every Friday.

Auth: service account key at ~/.config/spice/google-sheets-writer.json. The robot needs
Editor on the client's Drive folder (granted by sharing "1. Active" once).

Setup (one-time per client Sheet):
  python sheets_writer.py setup-ranges --sheet-id <id>

Smoke test:
  python sheets_writer.py meta --sheet-id <id>
"""
from __future__ import annotations
import argparse
import os
import sys
import warnings
from typing import Any

warnings.filterwarnings("ignore")  # silence py3.9 EOL FutureWarnings

KEY = os.path.expanduser("~/.config/spice/google-sheets-writer.json")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

_GID_CACHE: dict = {}  # sheet_id -> {tab_title: gid}; cleared when tabs are added

# Canonical named ranges for the v2 9-tab structure (Santi + Ro's goop Sheet as the
# reference: 1YaKsQnbRuKcEGdwfeFRU34HPhLNda8YyQ3HtHdI5yYU). These are the ONLY ranges
# the skill writes. Indices are (start_row, end_row, start_col, end_col), 0-indexed,
# half-open (matches Google Sheets API). Adjust as the template stabilizes.
NAMED_RANGES: dict[str, dict[str, Any]] = {
    # Dashboard
    "Dashboard_KPIs":                 {"tab": "Dashboard",        "rows": (1, 3),    "cols": (0, 7)},
    "Dashboard_TopFive":              {"tab": "Dashboard",        "rows": (11, 17),  "cols": (0, 7)},
    "Dashboard_BottomFive":           {"tab": "Dashboard",        "rows": (18, 24),  "cols": (0, 7)},
    "Dashboard_DeclineAlerts":        {"tab": "Dashboard",        "rows": (25, 36),  "cols": (0, 6)},
    "Dashboard_ProposedNextWeek":     {"tab": "Dashboard",        "rows": (37, 46),  "cols": (0, 7)},
    "Dashboard_PortfolioTrend":       {"tab": "Dashboard",        "rows": (47, 53),  "cols": (0, 7)},
    "Dashboard_LocationTier":         {"tab": "Dashboard",        "rows": (54, 80),  "cols": (0, 12)},
    # Active Campaigns
    "Active_Campaigns_Data":          {"tab": "Active Campaigns", "rows": (1, 500),  "cols": (0, 21)},
    # Ads Reporting
    "Ads_Reporting_Aggregate":        {"tab": "Ads Reporting",    "rows": (1, 8),    "cols": (0, 7)},
    "Ads_Reporting_PerCampaign":      {"tab": "Ads Reporting",    "rows": (10, 100), "cols": (0, 15)},
    "Ads_Reporting_AudienceSegment":  {"tab": "Ads Reporting",    "rows": (102, 110),"cols": (0, 6)},
    # Offers Reporting
    "Offers_Reporting_Aggregate":     {"tab": "Offers Reporting", "rows": (1, 8),    "cols": (0, 6)},
    "Offers_Reporting_PerPromo":      {"tab": "Offers Reporting", "rows": (10, 100), "cols": (0, 14)},
    "Offers_Reporting_Audience":      {"tab": "Offers Reporting", "rows": (102, 110),"cols": (0, 5)},
}

# Tabs the writer NEVER touches.
#   - Forward planning (Q2/Q3/Q4 Plan) — GM-owned strategy.
#   - Notes / Triggers / Definitions — static template.
#   - Archive — append-only (handled via append_archive, not write_range).
#   - Account Learnings — per-client institutional memory, GM-owned, promoted to global playbook at QBR.
# Match by case-insensitive substring so naming variants don't trip us up.
PROTECTED_TAB_SUBSTRINGS = ["q2 ", "q3 ", "q4 ", "plan", "notes", "trigger", "definition",
                            "archive", "learning"]

# Spice Digital brand palette (Brand/tokens.json, locked 2026-04-21).
SPICE_ORANGE = {"red": 1.0,   "green": 0.290, "blue": 0.110}  # #FF4A1C — the one accent
SPICE_CREAM  = {"red": 0.988, "green": 0.961, "blue": 0.925}  # #FCF5EC — warm off-white band
INK_900      = {"red": 0.094, "green": 0.094, "blue": 0.106}  # #18181B — primary text
WHITE        = {"red": 1, "green": 1, "blue": 1}

# Status pill colors — match the painted-cell palette from v0.1 (sage / teal / blue / amber / gray).
STATUS_COLORS = {
    "Live":              {"red": 0.518, "green": 0.800, "blue": 0.086},  # #84CC16
    "Approved":          {"red": 0.051, "green": 0.580, "blue": 0.533},  # #0D9488
    "Proposed":          {"red": 0.145, "green": 0.388, "blue": 0.922},  # #2563EB
    "Blocked-on-client": {"red": 0.961, "green": 0.620, "blue": 0.043},  # #F59E0B
    "Ended":             {"red": 0.612, "green": 0.639, "blue": 0.686},  # #9CA3AF
}

# Status emojis used in Santi's Sheet — map to colors so the writer accepts either form.
STATUS_EMOJI_MAP = {"🟢": "Live", "🟦": "Approved", "🔵": "Proposed", "🟠": "Blocked-on-client",
                    "⚪": "Ended", "🧪": "Test"}


# ---- auth + low-level helpers ----

_SVC_CACHE = None

def _service():
    """Return the cached Sheets API client (built once per process)."""
    global _SVC_CACHE
    if _SVC_CACHE is None:
        if not os.path.exists(KEY):
            raise FileNotFoundError(
                f"service-account key missing at {KEY}. See references/google-service-account-setup.md."
            )
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
        _SVC_CACHE = build("sheets", "v4", credentials=creds, cache_discovery=False)
    return _SVC_CACHE


def get_metadata(sheet_id: str) -> dict:
    """Read tab names → gid + named ranges. Cheap, used for setup + dry-run validation."""
    svc = _service()
    meta = svc.spreadsheets().get(
        spreadsheetId=sheet_id,
        fields="sheets.properties,namedRanges",
    ).execute()
    tabs = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta.get("sheets", [])}
    nr = {n["name"]: n for n in meta.get("namedRanges", [])}
    return {"tabs": tabs, "named_ranges": nr}


def _add_tab(svc, sheet_id: str, title: str, headers: list[str], hidden: bool = False) -> int:
    """Create a tab with the given title + a header row. Returns the new sheetId (gid).
    Hidden tabs (History) start collapsed; visible tabs (Account Learnings) are normal."""
    req = {"addSheet": {"properties": {"title": title, "hidden": hidden, "gridProperties": {
        "rowCount": 1000, "columnCount": max(8, len(headers))
    }}}}
    r = svc.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": [req]}).execute()
    gid = r["replies"][0]["addSheet"]["properties"]["sheetId"]
    # Write the header row
    if headers:
        svc.spreadsheets().values().update(
            spreadsheetId=sheet_id, range=f"'{title}'!A1",
            valueInputOption="USER_ENTERED", body={"values": [headers]},
        ).execute()
        # Bold + freeze the header row
        svc.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": [
            {"repeatCell": {
                "range": {"sheetId": gid, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {"userEnteredFormat": {
                    "backgroundColor": SPICE_ORANGE,
                    "textFormat": {"bold": True, "foregroundColor": WHITE},
                }},
                "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat",
            }},
            {"updateSheetProperties": {
                "properties": {"sheetId": gid, "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount",
            }},
        ]}).execute()
    return gid


# Canonical template tabs. Data tabs (Dashboard / Active Campaigns / Ads Reporting /
# Offers Reporting) are created empty — the writers fill them each refresh. The rest get
# headers/scaffolding. Tab order in a fresh Sheet follows insertion order here.
TEMPLATE_TABS = {
    "Dashboard":         {"hidden": False, "headers": []},   # filled by write_dashboard
    "Active Campaigns":  {"hidden": False, "headers": []},   # filled by write_active_campaigns
    "Ads Reporting":     {"hidden": False, "headers": []},   # filled by write_ads_reporting
    "Offers Reporting":  {"hidden": False, "headers": []},   # filled by write_offers_reporting
    "Archive": {
        "hidden": False,
        "headers": ["Year", "Quarter", "Week", "Campaign Name", "Type", "Platform",
                    "Locations", "Audience", "Threshold", "Discount", "Start Date", "End Date",
                    "Status", "Total Spend", "Total Sales", "Total Orders", "Avg ROAS",
                    "New Cx", "Test?", "Hypothesis", "Outcome / Learnings", "Continue?"],
    },
    "History": {
        "hidden": True,
        "headers": ["Weekstart", "Campaign", "Platform", "Location", "Spend",
                    "Sales", "Orders", "ROAS", "Status"],
    },
    "Account Learnings": {
        "hidden": False,
        "headers": ["Date", "Theme", "Observation", "Action Taken",
                    "Result / Status", "Tag", "Promoted to Playbook?"],
    },
    "Notes & Definitions": {
        "hidden": False,
        "headers": ["Item", "Definition"],
    },
}

# Forward-planning tabs created blank for the GM (skill never writes them).
FORWARD_PLAN_TABS = ["Q2 Plan", "Q3 Plan", "Q4 Plan"]


def ensure_template_tabs(sheet_id: str, dry_run: bool = False, include_forward: bool = True) -> dict:
    """Idempotent: ensure all canonical v2 tabs exist. Data tabs created empty (writers fill
    them); Archive/History/Account Learnings/Notes get headers; Q2/Q3/Q4 Plan created blank
    for the GM. Returns {created, existing}. Skill calls once per client Sheet at onboarding."""
    meta = get_metadata(sheet_id)
    svc = _service()
    created, existing = [], []
    for title, spec in TEMPLATE_TABS.items():
        if title in meta["tabs"]:
            existing.append(title); continue
        if dry_run:
            created.append(f"{title} (dry run)"); continue
        _add_tab(svc, sheet_id, title, spec["headers"], hidden=spec["hidden"])
        _GID_CACHE.pop(sheet_id, None)
        created.append(title)
    if include_forward:
        for title in FORWARD_PLAN_TABS:
            if title in meta["tabs"]:
                existing.append(title); continue
            if dry_run:
                created.append(f"{title} (dry run)"); continue
            _add_tab(svc, sheet_id, title, [], hidden=False)
            _GID_CACHE.pop(sheet_id, None)
            created.append(title)
    return {"created": created, "existing": existing}


def setup_named_ranges(sheet_id: str, dry_run: bool = False) -> dict:
    """Define the canonical named ranges on a Sheet. Idempotent: skips ranges already present.
    Skips ranges whose tab doesn't exist in the Sheet (logs which tabs are missing).
    """
    meta = get_metadata(sheet_id)
    tabs, existing = meta["tabs"], meta["named_ranges"]

    requests, created, exist_list, missing_tab = [], [], [], []
    for name, spec in NAMED_RANGES.items():
        if name in existing:
            exist_list.append(name); continue
        if spec["tab"] not in tabs:
            missing_tab.append((name, spec["tab"])); continue
        requests.append({"addNamedRange": {"namedRange": {
            "name": name,
            "range": {
                "sheetId": tabs[spec["tab"]],
                "startRowIndex": spec["rows"][0], "endRowIndex": spec["rows"][1],
                "startColumnIndex": spec["cols"][0], "endColumnIndex": spec["cols"][1],
            },
        }}})
        created.append(name)

    if requests and not dry_run:
        _service().spreadsheets().batchUpdate(
            spreadsheetId=sheet_id, body={"requests": requests},
        ).execute()

    return {"created": created, "skipped_existing": exist_list, "skipped_missing_tab": missing_tab}


def assert_safe_to_write(sheet_id: str, range_or_name: str, allow_protected: bool = False) -> None:
    """Guardrail: refuse to write a range whose tab is on the protected list.
    allow_protected=True is the explicit opt-in used ONLY by strategy_write.py — the
    Plan-campaigns session is the one authorized writer for Q-plan tabs. Every other
    call site (refresh.py and friends) stays default-False."""
    if allow_protected:
        return
    tab = range_or_name.split("!", 1)[0].strip("'") if "!" in range_or_name else None
    # If it's a named range, look up the tab.
    if tab is None:
        meta = get_metadata(sheet_id)
        nr = meta["named_ranges"].get(range_or_name)
        if nr:
            for name, gid in meta["tabs"].items():
                if gid == nr["range"]["sheetId"]:
                    tab = name; break
    if tab is None:
        return  # unknown — let the API decide
    t = tab.lower()
    if any(p in t for p in PROTECTED_TAB_SUBSTRINGS):
        raise PermissionError(
            f"refusing to write '{range_or_name}' — tab '{tab}' matches a PROTECTED pattern "
            f"({PROTECTED_TAB_SUBSTRINGS}). Forward calendars, Archive, and Notes are human-owned."
        )


def read_range(sheet_id: str, range_a1: str) -> list:
    """Read values from a range. Reads are never guarded."""
    r = _service().spreadsheets().values().get(spreadsheetId=sheet_id, range=range_a1).execute()
    return r.get("values", [])


def create_tab(sheet_id: str, title: str, allow_protected: bool = False) -> int:
    """Create a new tab; returns its gid. Guarded like writes (Q-plan creation needs the opt-in)."""
    assert_safe_to_write(sheet_id, f"'{title}'!A1", allow_protected=allow_protected)
    r = _service().spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={
        "requests": [{"addSheet": {"properties": {"title": title}}}]}).execute()
    return r["replies"][0]["addSheet"]["properties"]["sheetId"]


def clear_range(sheet_id: str, range_or_name: str, allow_protected: bool = False) -> None:
    """Clear values in a range (named or A1)."""
    assert_safe_to_write(sheet_id, range_or_name, allow_protected=allow_protected)
    _service().spreadsheets().values().clear(
        spreadsheetId=sheet_id, range=range_or_name, body={},
    ).execute()


def write_range(sheet_id: str, range_or_name: str, values: list[list[Any]],
                allow_protected: bool = False) -> int:
    """Write a 2D array of values. USER_ENTERED so formulas/dates parse like a human typed them.
    Returns rows updated.
    """
    assert_safe_to_write(sheet_id, range_or_name, allow_protected=allow_protected)
    if not values:
        return 0
    r = _service().spreadsheets().values().update(
        spreadsheetId=sheet_id, range=range_or_name,
        valueInputOption="USER_ENTERED", body={"values": values},
    ).execute()
    return r.get("updatedRows", 0)


def append_rows(sheet_id: str, tab: str, rows: list[list[Any]]) -> int:
    """Append rows to the bottom of a tab. Used for Archive (append-only)."""
    if not rows:
        return 0
    r = _service().spreadsheets().values().append(
        spreadsheetId=sheet_id, range=f"'{tab}'!A:Z",
        valueInputOption="USER_ENTERED", body={"values": rows},
    ).execute()
    return r.get("updates", {}).get("updatedRows", 0)


def apply_status_pills(sheet_id: str, tab: str, col_letter: str,
                        start_row: int, statuses: list[str]) -> None:
    """Paint status cells with pill colors. col_letter like 'F'; start_row is 1-indexed.
    Empty/unknown status leaves the cell unstyled (white).
    """
    svc = _service()
    meta = svc.spreadsheets().get(spreadsheetId=sheet_id, fields="sheets.properties").execute()
    gid = next((s["properties"]["sheetId"] for s in meta["sheets"]
                if s["properties"]["title"] == tab), None)
    if gid is None:
        raise ValueError(f"tab not found: {tab}")
    col_index = ord(col_letter.upper()) - ord("A")

    rows = []
    for st in statuses:
        st_norm = STATUS_EMOJI_MAP.get(st, st)
        if st_norm in STATUS_COLORS:
            rows.append({"values": [{"userEnteredFormat": {
                "backgroundColor": STATUS_COLORS[st_norm],
                "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                "horizontalAlignment": "CENTER",
            }}]})
        else:
            rows.append({"values": [{"userEnteredFormat": {
                "backgroundColor": {"red": 1, "green": 1, "blue": 1},
                "textFormat": {"bold": False},
            }}]})

    svc.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": [{
        "updateCells": {
            "range": {
                "sheetId": gid,
                "startRowIndex": start_row - 1, "endRowIndex": start_row - 1 + len(rows),
                "startColumnIndex": col_index, "endColumnIndex": col_index + 1,
            },
            "rows": rows,
            "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.horizontalAlignment",
        }
    }]}).execute()


# ---- full-tab helpers ----
# The 4 data tabs (Dashboard / Active Campaigns / Ads Reporting / Offers Reporting) are
# FULLY skill-owned — no human content interleaved — so the robust pattern is clear + full
# rewrite each refresh, not fragile fixed-offset named ranges. (Named ranges are kept for
# back-compat but the writers below build the whole tab from scratch.)

def _tab_gid(sheet_id: str, tab: str) -> int:
    cache = _GID_CACHE.setdefault(sheet_id, {})
    if tab not in cache:
        meta = _service().spreadsheets().get(spreadsheetId=sheet_id, fields="sheets.properties").execute()
        for s in meta["sheets"]:
            cache[s["properties"]["title"]] = s["properties"]["sheetId"]
    if tab not in cache:
        raise ValueError(f"tab not found: {tab}")
    return cache[tab]


def write_full_tab(sheet_id: str, tab: str, matrix: list[list[Any]],
                   section_header_rows: list[int] | None = None,
                   col_header_rows: list[int] | None = None,
                   value_input: str = "RAW",
                   freeze_rows: int = 0, freeze_cols: int = 0, title_rows: int = 0,
                   allow_protected: bool = False) -> int:
    """Clear a skill-owned tab and write `matrix` from A1. Applies light formatting:
    section_header_rows (0-indexed) get a bold cream band; col_header_rows get the Spice
    Orange header style. freeze_rows/freeze_cols pin headers/labels while scrolling.
    Refuses protected tabs unless allow_protected (strategy_write.py's Q-plan opt-in).

    value_input defaults to RAW — these are presentation tabs of pre-formatted strings
    ($, %, ROAS-x), so RAW prevents Sheets coercing e.g. "+2.8%" → 0.028. Pass
    "USER_ENTERED" only when you want Sheets to parse numbers/formulas (e.g. Active
    Campaigns, where WTD numeric columns should stay sortable)."""
    assert_safe_to_write(sheet_id, f"'{tab}'!A1", allow_protected=allow_protected)
    svc = _service()
    gid = _tab_gid(sheet_id, tab)
    # Clear the whole tab's values (formatting persists, but we re-apply below).
    svc.spreadsheets().values().clear(spreadsheetId=sheet_id, range=f"'{tab}'!A1:Z1000", body={}).execute()
    # Unmerge any leftover merged cells from a prior layout BEFORE writing. Writing a 2D array
    # into a merged range only fills the merge's anchor cell and silently drops the rest of the
    # row — that's what blanked the KPI row (B6:H6 was merged) and the per-platform Sales/Orders
    # cells. unmergeCells over a range with no merges is a safe no-op.
    try:
        svc.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": [
            {"unmergeCells": {"range": {"sheetId": gid, "startRowIndex": 0, "endRowIndex": 1000,
                                        "startColumnIndex": 0, "endColumnIndex": 26}}},
        ]}).execute()
    except Exception:
        pass  # no merges present, or API declined — writing proceeds regardless
    if not matrix:
        return 0
    # Pad rows to equal width so the API doesn't choke on ragged rows.
    width = max(len(r) for r in matrix)
    padded = [list(r) + [""] * (width - len(r)) for r in matrix]
    svc.spreadsheets().values().update(
        spreadsheetId=sheet_id, range=f"'{tab}'!A1",
        valueInputOption=value_input, body={"values": padded},
    ).execute()
    # Formatting passes
    reqs = []
    # Reset stale formatting FIRST. write_full_tab clears cell VALUES, but Sheets keeps cell
    # FORMAT across refreshes — so a prior layout's oversized hero-number font, or white text
    # left over from a charcoal header, bleeds into the new content (invisible KPIs rendered
    # white-on-white, giant cells overflowing their neighbors). Wipe the whole skill-owned
    # region back to a clean default, THEN layer section/header/alignment on top.
    reqs.append({"repeatCell": {
        "range": {"sheetId": gid, "startRowIndex": 0, "endRowIndex": 1000,
                  "startColumnIndex": 0, "endColumnIndex": 26},
        "cell": {"userEnteredFormat": {
            "backgroundColor": {"red": 1, "green": 1, "blue": 1},
            "horizontalAlignment": "LEFT", "verticalAlignment": "BOTTOM",
            "textFormat": {"bold": False, "italic": False, "fontSize": 10,
                           "foregroundColor": {"red": 0, "green": 0, "blue": 0}},
        }},
        "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment,textFormat)",
    }})
    # Alignment convention: text labels LEFT, numeric metric columns RIGHT.
    # Auto-detect per column — a column is numeric if the majority of its non-empty data
    # cells parse as a number (after stripping $ , % x). Headers/section rows excluded.
    body_rows = set(range(len(padded))) - set(col_header_rows or []) - set(section_header_rows or [])
    def _is_num(v):
        s = str(v).replace("$", "").replace(",", "").replace("%", "").replace("x", "").strip()
        if s in ("", "—", "n/a", "--"):
            return None  # neutral — doesn't count either way
        try:
            float(s); return True
        except ValueError:
            return False
    # default everything LEFT, then flip numeric columns to RIGHT
    reqs.append({"repeatCell": {
        "range": {"sheetId": gid, "startRowIndex": 0, "endRowIndex": len(padded),
                  "startColumnIndex": 0, "endColumnIndex": width},
        "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}},
        "fields": "userEnteredFormat.horizontalAlignment",
    }})
    for col in range(1, width):  # never right-align col A (always the label column)
        votes = [_is_num(padded[r][col]) for r in body_rows if col < len(padded[r])]
        votes = [v for v in votes if v is not None]
        if votes and sum(votes) / len(votes) >= 0.5:
            reqs.append({"repeatCell": {
                "range": {"sheetId": gid, "startRowIndex": 0, "endRowIndex": len(padded),
                          "startColumnIndex": col, "endColumnIndex": col + 1},
                "cell": {"userEnteredFormat": {"horizontalAlignment": "RIGHT"}},
                "fields": "userEnteredFormat.horizontalAlignment",
            }})
    # Column-header rows: Spice Orange band, white bold text (replaces the old charcoal).
    for r in (col_header_rows or []):
        reqs.append({"repeatCell": {
            "range": {"sheetId": gid, "startRowIndex": r, "endRowIndex": r + 1,
                      "startColumnIndex": 0, "endColumnIndex": width},
            "cell": {"userEnteredFormat": {
                "backgroundColor": SPICE_ORANGE,
                "textFormat": {"bold": True, "foregroundColor": WHITE, "fontSize": 10},
            }},
            "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat",
        }})
    # Section-header rows: full-width warm cream band, bold ink text (groups the section,
    # no dark grey/black bars).
    for r in (section_header_rows or []):
        reqs.append({"repeatCell": {
            "range": {"sheetId": gid, "startRowIndex": r, "endRowIndex": r + 1,
                      "startColumnIndex": 0, "endColumnIndex": width},
            "cell": {"userEnteredFormat": {
                "backgroundColor": SPICE_CREAM,
                "textFormat": {"bold": True, "fontSize": 12, "foregroundColor": INK_900},
            }},
            "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat",
        }})
    # Title block: big bold title on row 0, muted subtitle on the rest of the block.
    if title_rows:
        reqs.append({"repeatCell": {
            "range": {"sheetId": gid, "startRowIndex": 0, "endRowIndex": 1,
                      "startColumnIndex": 0, "endColumnIndex": width},
            "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "fontSize": 15, "foregroundColor": INK_900}}},
            "fields": "userEnteredFormat.textFormat"}})
        if title_rows > 1:
            reqs.append({"repeatCell": {
                "range": {"sheetId": gid, "startRowIndex": 1, "endRowIndex": title_rows,
                          "startColumnIndex": 0, "endColumnIndex": width},
                "cell": {"userEnteredFormat": {"textFormat": {"italic": True, "fontSize": 10,
                         "foregroundColor": {"red": 0.42, "green": 0.42, "blue": 0.45}}}},
                "fields": "userEnteredFormat.textFormat"}})
    if reqs:
        svc.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": reqs}).execute()
    # Auto-fit columns to content (fixes ragged/truncated widths from the 100px default).
    svc.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": [
        {"autoResizeDimensions": {"dimensions": {"sheetId": gid, "dimension": "COLUMNS",
                                                  "startIndex": 0, "endIndex": width}}},
    ]}).execute()
    # Freeze header rows / label columns so they stay pinned while scrolling. The title block
    # is always frozen so it stays visible.
    eff_freeze_rows = max(freeze_rows, title_rows)
    if eff_freeze_rows or freeze_cols:
        svc.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": [
            {"updateSheetProperties": {
                "properties": {"sheetId": gid, "gridProperties": {
                    "frozenRowCount": eff_freeze_rows, "frozenColumnCount": freeze_cols}},
                "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount"}},
        ]}).execute()
    return len(padded)


def paint_status_column(sheet_id: str, tab: str, col_index: int, start_row: int, statuses: list[str]) -> None:
    """Paint a status column with pill colors. col_index + start_row are 0-indexed."""
    gid = _tab_gid(sheet_id, tab)
    rows = []
    for st in statuses:
        st_norm = STATUS_EMOJI_MAP.get(st, st)
        if st_norm in STATUS_COLORS:
            rows.append({"values": [{"userEnteredFormat": {
                "backgroundColor": STATUS_COLORS[st_norm],
                "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                "horizontalAlignment": "LEFT"}}]})
        else:
            rows.append({"values": [{"userEnteredFormat": {"backgroundColor": {"red": 1, "green": 1, "blue": 1}}}]})
    if not rows:
        return
    _service().spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": [{
        "updateCells": {
            "range": {"sheetId": gid, "startRowIndex": start_row, "endRowIndex": start_row + len(rows),
                      "startColumnIndex": col_index, "endColumnIndex": col_index + 1},
            "rows": rows,
            "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.horizontalAlignment",
        }}]}).execute()


def paint_status_cells(sheet_id: str, tab: str, col_index: int, cells: list) -> None:
    """Paint status pills on scattered (non-contiguous) rows. cells = [(row_0idx, status), ...]."""
    if not cells:
        return
    gid = _tab_gid(sheet_id, tab)
    reqs = []
    for r, st in cells:
        stn = STATUS_EMOJI_MAP.get(st, st)
        if stn in STATUS_COLORS:
            fmt = {"backgroundColor": STATUS_COLORS[stn],
                   "textFormat": {"bold": True, "foregroundColor": WHITE}}
        else:
            fmt = {"backgroundColor": WHITE}
        reqs.append({"repeatCell": {
            "range": {"sheetId": gid, "startRowIndex": r, "endRowIndex": r + 1,
                      "startColumnIndex": col_index, "endColumnIndex": col_index + 1},
            "cell": {"userEnteredFormat": fmt},
            "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat"}})
    _service().spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": reqs}).execute()


def paint_cell_bg(sheet_id: str, tab: str, row: int, col: int, bg: dict) -> None:
    """Set one cell's background color (0-indexed row/col). Used for the 3%-target signal."""
    gid = _tab_gid(sheet_id, tab)
    _service().spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": [{
        "repeatCell": {
            "range": {"sheetId": gid, "startRowIndex": row, "endRowIndex": row + 1,
                      "startColumnIndex": col, "endColumnIndex": col + 1},
            "cell": {"userEnteredFormat": {"backgroundColor": bg}},
            "fields": "userEnteredFormat.backgroundColor"}}]}).execute()


def write_active_campaigns_by_location(sheet_id: str, groups: list, week: str = "") -> int:
    """Render Active Campaigns grouped by location: a cream band per location, then the running
    campaigns under it (ads + offers) with performance. Status pills in the Status column."""
    m: list[list[Any]] = []
    section_rows, header_rows = [], []

    def section(t): m.append([t]); section_rows.append(len(m) - 1)
    def header(c): m.append(c); header_rows.append(len(m) - 1)

    title = "Active Campaigns by Location"
    if week:
        title += f" — {week}"
    m.append([title]); m.append([])

    COLS = ["Campaign", "Type", "Platform", "Status", "Spend", "Attributed Sales", "ROAS", "Orders"]
    status_cells = []  # (row_0idx, status)
    for g in groups:
        section(f"📍 {g['location']}  ·  {g['count']} campaign(s)")
        header(COLS)
        for c in g["campaigns"]:
            status_cells.append((len(m), c.get("status", "Live")))  # Status is col index 3
            m.append([c.get("campaign"), c.get("type"), c.get("platform"), c.get("status", "Live"),
                      _money(c.get("spend")), _money(c.get("sales")), _roas(c.get("roas")),
                      int(c["orders"]) if c.get("orders") else "—"])
        m.append([])

    n = write_full_tab(sheet_id, "Active Campaigns", m, section_header_rows=section_rows,
                       col_header_rows=header_rows, freeze_cols=1, title_rows=1)
    paint_status_cells(sheet_id, "Active Campaigns", col_index=3, cells=status_cells)
    return n


def _money(v) -> str:
    try:
        return f"${float(str(v).replace('$','').replace(',','')):,.0f}"
    except (ValueError, TypeError):
        return str(v) if v not in (None, "") else "—"


def _money_short(v) -> str:
    """Abbreviated currency for KPI tiles: $1.40M / $940K / $680."""
    try:
        n = float(str(v).replace("$", "").replace(",", ""))
    except (ValueError, TypeError):
        return str(v) if v not in (None, "") else "—"
    if abs(n) >= 1_000_000:
        return f"${n / 1_000_000:.2f}M"
    if abs(n) >= 1_000:
        return f"${n / 1_000:.0f}K"
    return f"${n:,.0f}"


def _roas(v) -> str:
    try:
        return f"{float(str(v).replace('x','')):.1f}x"
    except (ValueError, TypeError):
        return str(v) if v not in (None, "") else "—"


# ---- per-tab writers (full-tab rewrite) ----

def apply_number_format(sheet_id: str, tab: str, col_index: int, start_row: int,
                        end_row: int, pattern: str, ntype: str = "NUMBER") -> None:
    """Apply a numberFormat (e.g. currency, ROAS-x) to one column. 0-indexed col + rows."""
    gid = _tab_gid(sheet_id, tab)
    _service().spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": [{
        "repeatCell": {
            "range": {"sheetId": gid, "startRowIndex": start_row, "endRowIndex": end_row,
                      "startColumnIndex": col_index, "endColumnIndex": col_index + 1},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": ntype, "pattern": pattern}}},
            "fields": "userEnteredFormat.numberFormat",
        }}]}).execute()


# Active Campaigns is the PLANNING registry (what's running / proposed / blocked + targets).
# Per-campaign performance lives in the Ads/Offers Reporting tabs — the planned campaigns and
# the platform's actual sponsored-listings/promos don't map 1:1, so WTD/Lifetime actuals are
# intentionally NOT shown here (they'd be all-blank). They return if/when perf joins by ID.
ACTIVE_CAMPAIGNS_COLS = [
    "Campaign Name", "Type", "Platform", "Locations", "Audience", "Status",
    "Start Date", "End Date", "Target ROAS", "Owner", "Last Updated",
]


def write_active_campaigns(sheet_id: str, rows: list[dict], last_updated: str = "") -> int:
    """Full-tab rewrite of Active Campaigns (planning registry). Header + one row per campaign.
    Status pills painted in column F (index 5); Target ROAS formatted as Nx; header row + the
    campaign-name column frozen. Returns rows written (incl. header)."""
    matrix = [ACTIVE_CAMPAIGNS_COLS]
    for r in rows:
        rr = dict(r)
        if last_updated and not rr.get("Last Updated"):
            rr["Last Updated"] = last_updated
        matrix.append([rr.get(c, "") for c in ACTIVE_CAMPAIGNS_COLS])
    n = write_full_tab(sheet_id, "Active Campaigns", matrix, col_header_rows=[0],
                       value_input="USER_ENTERED", freeze_rows=1, freeze_cols=1)
    if rows:
        paint_status_column(sheet_id, "Active Campaigns", col_index=5, start_row=1,
                            statuses=[r.get("Status", "") for r in rows])
        # Target ROAS (index 8) → "3.5x"
        apply_number_format(sheet_id, "Active Campaigns", col_index=8, start_row=1,
                            end_row=1 + len(rows), pattern='0.0"x"')
    return n


HISTORY_COLS = ["Weekstart", "Campaign", "Platform", "Location", "Spend",
                "Sales", "Orders", "ROAS", "Status"]


def write_history(sheet_id: str, rows: list[dict]) -> int:
    """Upsert this week's snapshot into History. Append-only ACROSS weeks, but idempotent
    WITHIN a week: re-running a refresh replaces the current week's rows instead of stacking
    duplicates. Keeps History at one row per (week, campaign) — the basis for Lifetime cols +
    L4W/L13W trends. Prior weeks are never touched.
    """
    if not rows:
        return 0
    svc = _service()
    weeks = {str(r.get("Weekstart", "")) for r in rows}
    existing = svc.spreadsheets().values().get(
        spreadsheetId=sheet_id, range="History!A1:I100000").execute().get("values", [])
    header = existing[0] if existing else HISTORY_COLS
    body = [r for r in existing[1:] if not (r and str(r[0]) in weeks)] if len(existing) > 1 else []
    new = [[r.get(c, "") for c in HISTORY_COLS] for r in rows]
    out = [header] + body + new
    # Resilient write: UPDATE (overwrite) first, then clear only the tail beyond the new content.
    # If a call fails between the two, History still has data (never an empty-then-failed clear).
    svc.spreadsheets().values().update(
        spreadsheetId=sheet_id, range="History!A1", valueInputOption="USER_ENTERED",
        body={"values": out}).execute()
    prev_len = len(existing)
    if prev_len > len(out):
        svc.spreadsheets().values().clear(
            spreadsheetId=sheet_id, range=f"History!A{len(out) + 1}:I{prev_len + 1}", body={}).execute()
    return len(new)


def read_history(sheet_id: str) -> list[dict]:
    """Read the History tab back as a list of dicts (keyed by HISTORY_COLS). Source for
    prior-week WoW + the Dashboard Portfolio Trend. Returns [] if History is empty."""
    svc = _service()
    v = svc.spreadsheets().values().get(
        spreadsheetId=sheet_id, range="History!A1:I100000").execute().get("values", [])
    if not v or len(v) < 2:
        return []
    hdr = v[0]
    out = []
    for row in v[1:]:
        row = (row + [""] * len(hdr))[:len(hdr)]
        out.append(dict(zip(hdr, row)))
    return out


DEFINITIONS = [
    ["Metric", "Definition (Spice weekly-reporting methodology)"],
    ["Total Sales", "Food subtotal excluding tax — the top line before deductions. Denominator for the % metrics."],
    ["Net Sales", "Total Sales minus merchant-funded discounts."],
    ["Marketing Spend", "Total Marketing Investment = ad spend + offer/discount spend for the week."],
    ["Mkt Spend %", "Marketing Spend / Total Sales. North-star target 3% (green <=3%, amber <=4%, red >4%)."],
    ["Marketing-Driven Sales", "Net sales from orders attributed to a campaign (ad OR offer). Deduped — an order is counted once even if it used both an ad and an offer."],
    ["Mkt-Driven Sales %", "Marketing-Driven Sales / Total Sales. The rest is Organic."],
    ["Organic Sales", "Sales from orders with no marketing attribution (Total Sales - Marketing-Driven)."],
    ["Marketing ROAS", "Marketing-Driven Sales / Marketing Spend. 3.0+ is generally healthy. The standard, deduped measure."],
    ["Blended ROAS", "Client-defined ROAS (goop) that credits marketing more broadly than the deduped Marketing ROAS. Tracked alongside it, not a replacement."],
    ["Marketing vs Organic", "Marketing-Driven vs Organic share of Total Sales, with a weekly trend — the incrementality read: is marketing additive or cannibalizing organic?"],
    ["CPO", "Marketing CPO = Marketing Spend / Orders from Marketing (deduped marketing orders)."],
    ["New-Cust CAC", "Marketing Spend / new customers acquired (from offer data)."],
    ["Store Tier", "Red / Yellow / Green from the sales sheet, grouping stores by health and priority."],
    ["Action", "Scale up = efficient (<=3% spend, ROAS >=6). Pull back = heavy overspend (>10%). Watch = above the 3% target. Hold = on track."],
    ["WoW", "Week-over-week change vs the prior week. Fills in as weekly history accumulates."],
    ["Source", "Efficiency metrics are cross-pulled from the weekly sales sheet (canonical weekly-reporting numbers). Per-campaign detail (Ads / Offers tabs) comes from the platform campaign exports."],
]


def seed_definitions(sheet_id: str) -> int:
    """Seed the Notes & Definitions tab with the metric glossary — ONLY if it's still empty
    (header row or blank), so any human edits are never overwritten. Returns rows written."""
    svc = _service()
    try:
        cur = svc.spreadsheets().values().get(
            spreadsheetId=sheet_id, range="'Notes & Definitions'!A1:B100").execute().get("values", [])
    except Exception:
        return 0
    if len([r for r in cur if any(str(c).strip() for c in r)]) > 1:
        return 0  # already has content beyond the header — leave it alone
    svc.spreadsheets().values().update(
        spreadsheetId=sheet_id, range="'Notes & Definitions'!A1",
        valueInputOption="RAW", body={"values": DEFINITIONS}).execute()
    svc.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": [{
        "repeatCell": {"range": {"sheetId": _tab_gid(sheet_id, "Notes & Definitions"),
                                 "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 2},
                       "cell": {"userEnteredFormat": {"backgroundColor": SPICE_ORANGE,
                                "textFormat": {"bold": True, "foregroundColor": WHITE}}},
                       "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat"}}]}).execute()
    return len(DEFINITIONS)


def append_weekly_learning(sheet_id: str, weekstart: str, theme: str, observation: str) -> int:
    """Append a dated, data-derived 'auto-draft' learning to Account Learnings so learnings
    accumulate week over week (the GM curates / promotes them). Idempotent: skips if this
    week's auto-draft already exists; never touches GM-authored rows."""
    if not observation:
        return 0
    svc = _service()
    cur = svc.spreadsheets().values().get(
        spreadsheetId=sheet_id, range="'Account Learnings'!A2:F1000").execute().get("values", [])
    for r in cur:
        if len(r) > 5 and str(r[0]) == weekstart and str(r[5]).strip().lower() == "auto-draft":
            return 0  # already logged this week
    svc.spreadsheets().values().append(
        spreadsheetId=sheet_id, range="'Account Learnings'!A:G", valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [[weekstart, theme, observation, "", "", "auto-draft", ""]]}).execute()
    return 1


def write_dashboard(sheet_id: str, data: dict, client: str = "", week: str = "") -> int:
    """Full-tab rewrite of the Dashboard. Sections, in order:
      title · Overall KPIs · By Platform · By Segment · Top 5 · Bottom 5 ·
      Decline Alerts · Proposed Next Week · Portfolio Trend · Location Tier.

    Data shape (all keys optional — sections with no data are skipped):
      {
        "kpis": {"live": 4, "proposed": 4, "blocked": 2, "total_spend": 93459,
                 "total_sales": 1015607, "blended_roas": 10.9, "new_cx": 2639},
        "by_platform": [{"platform","spend","sales","roas","orders"}, ...],
        "by_segment":  [{"segment","spend","sales","roas","count"}, ...],
        "top_five":    [{"campaign","platform","location","spend","sales","roas"}, ...],
        "bottom_five": [...same...],
        "decline_alerts": [{"location","trigger","severity","owner","action"}, ...],
        "proposed":    [{"proposal","where","target_roas","decision_by","owner"}, ...],
        "portfolio_trend": [{"metric","w_3","w_2","w_1","w_0","wow"}, ...],
        "location_tier": [{"location","tier","spend","sales","roas","payout_pct","mkt_pct","notes"}, ...],
      }
    Returns total rows written.
    """
    m: list[list[Any]] = []
    section_rows: list[int] = []
    header_rows: list[int] = []

    def section(title: str):
        m.append([title]); section_rows.append(len(m) - 1)

    def header(cols: list[str]):
        m.append(cols); header_rows.append(len(m) - 1)

    title = f"{client} | Campaign Performance Dashboard"
    if week:
        title += f" — {week}"
    m.append([title])
    m.append(["Campaign focus — payout lives in the weekly report"])
    m.append([])

    mkt_pct_cell = None  # (row, col, value%) — painted vs the 3% target after the write
    heat_cells = []      # (row, col, value, kind) — threshold-colored after the write
    tile_rows = None     # (label_row, value_row) for the KPI hero strip
    k = data.get("kpis") or {}
    if k:
        # KPI hero strip — 5 cards in cols B..K (col A is frozen, kept out of the merges).
        # Three rows per card: label · big value · WoW delta. Replaces the old Overall section.
        tile_rows = (len(m), len(m) + 1, len(m) + 2)
        m.append(["", "TOTAL SALES", "", "MKT SPEND %", "", "MKT ROAS", "", "BLENDED ROAS", "", "NEW CX", ""])
        m.append(["", _money_short(k.get("total_sales_display")), "", k.get("mkt_spend_pct", "—"), "",
                  _roas(k.get("marketing_roas")), "", _roas(k.get("blended_roas")), "", k.get("new_cx", "—"), ""])
        m.append(["", k.get("total_sales_wow", "—"), "", k.get("mkt_spend_pct_wow", "—"), "",
                  k.get("roas_wow", "—"), "", k.get("blended_roas_wow", "—"), "", k.get("new_cx_wow", "—"), ""])
        m.append([])

        # Marketing efficiency vs Total Sales — the 3% north-star metric (canonical).
        # Track both Marketing ROAS (deduped, standard) and Blended ROAS (client-defined).
        section("Marketing Efficiency")
        header(["Total Sales", "Marketing Spend", "Mkt Spend %", "Mkt-Driven Sales %",
                "Marketing ROAS", "Blended ROAS", "CPO", "New-Cust CAC"])
        mkt_pct_cell = (len(m), 2, k.get("mkt_spend_pct_val"))  # color this cell vs 3%
        m.append([_money(k.get("total_sales_display")), _money(k.get("total_spend")),
                  k.get("mkt_spend_pct", "—"), k.get("mkt_driven_pct", "—"),
                  _roas(k.get("marketing_roas")), _roas(k.get("blended_roas")),
                  _money(k.get("cpo")), _money(k.get("new_cust_cac"))])
        m.append([])

        # Ad vs Promo investment split (spend only — canonical marketing-driven sales is deduped
        # and not split by channel).
        section("Ads vs Promos")
        header(["Channel", "Marketing Spend", "% of Mktg Spend"])
        _tot = k.get("total_spend") or 0
        _shr = lambda v: f"{(v / _tot * 100):.0f}%" if _tot else "—"
        m.append(["Ads (Sponsored Listings)", _money(k.get("ad_spend")), _shr(k.get("ad_spend") or 0)])
        m.append(["Promos (Offers)", _money(k.get("promo_spend")), _shr(k.get("promo_spend") or 0)])
        m.append([])

    # Marketing vs Organic (canonical, deduped). Replaces the muddy double-dip section: the
    # weekly-reporting methodology counts an order once even if it used both an ad and an offer,
    # so there's no double-count to surface.
    if data.get("by_marketing_organic"):
        section("Marketing vs Organic")
        header(["Source", "Net Sales", "% of Total Sales"])
        for r in data["by_marketing_organic"]:
            m.append([r.get("label"), _money(r.get("sales")), r.get("pct", "—")])
        m.append([])

    if data.get("marketing_organic_trend"):
        # Incrementality read: watch whether organic erodes as marketing-driven scales.
        section("Marketing vs Organic — Trend")
        header(["Week", "Marketing-Driven", "Organic", "Total Sales", "Mkt-Driven %"])
        for t in data["marketing_organic_trend"]:
            md, org = t.get("mktg_driven", 0), t.get("organic", 0)
            tot = md + org
            m.append([t.get("week"), _money(md), _money(org), _money(tot),
                      f"{md / tot * 100:.0f}%" if tot else "—"])
        m.append([])

    if data.get("by_tier"):
        section("By Store Tier")
        header(["Tier", "Mktg Spend", "Mktg-Driven Sales", "ROAS", "Orders", "Mkt Spend %", "Mkt-Driven Sales %"])
        for r in data["by_tier"]:
            heat_cells.append((len(m), 3, r.get("roas"), "roas"))
            heat_cells.append((len(m), 5, r.get("mkt_spend_pct_val"), "mktpct"))
            m.append([r.get("tier"), _money(r.get("spend")), _money(r.get("sales")),
                      _roas(r.get("roas")), r.get("orders", "—"),
                      r.get("mkt_spend_pct", "—"), r.get("mkt_driven_pct", "—")])
        m.append([])

    if data.get("by_platform"):
        section("By Platform")
        header(["Platform", "Mktg Spend", "Mktg-Driven Sales", "ROAS", "Orders", "CPO",
                "Mkt Spend %", "Mkt-Driven Sales %"])
        for r in data["by_platform"]:
            heat_cells.append((len(m), 3, r.get("roas"), "roas"))
            heat_cells.append((len(m), 6, r.get("mkt_spend_pct_val"), "mktpct"))
            m.append([r.get("platform"), _money(r.get("spend")), _money(r.get("sales")),
                      _roas(r.get("roas")), r.get("orders", "—"), _money(r.get("cpo")),
                      r.get("mkt_spend_pct", "—"), r.get("mkt_driven_pct", "—")])
        m.append([])

    if data.get("by_location"):
        section("By Location")
        # Trend hierarchy: WoW alerts -> L4W Trend confirms direction -> vs Tier assigns
        # ownership (a store isn't "declining" if its whole tier moved the same way).
        header(["Location", "Tier", "Mktg Spend", "Mktg-Driven Sales", "ROAS", "Orders", "CPO",
                "Mkt Spend %", "Mkt-Driven Sales %", "L4W Trend", "vs Tier", "Action"])
        for r in data["by_location"]:
            heat_cells.append((len(m), 4, r.get("roas"), "roas"))
            heat_cells.append((len(m), 7, r.get("mkt_spend_pct_val"), "mktpct"))
            heat_cells.append((len(m), 9, r.get("l4w_mom_heat"), "mom"))
            heat_cells.append((len(m), 10, r.get("vs_tier_heat"), "mom"))
            heat_cells.append((len(m), 11, r.get("flag"), "flag"))
            m.append([r.get("location"), r.get("tier", ""), _money(r.get("spend")), _money(r.get("sales")),
                      _roas(r.get("roas")), r.get("orders", "—"), _money(r.get("cpo")),
                      r.get("mkt_spend_pct", "—"), r.get("mkt_driven_pct", "—"),
                      r.get("l4w_mom", "—"), r.get("vs_tier", "—"), r.get("flag", "")])
        m.append([])

    if data.get("by_audience"):
        section("Customer Segmentation (by Audience)")
        header(["Audience", "Spend", "Attributed Sales", "ROAS", "Orders", "% of Spend"])
        for r in data["by_audience"]:
            m.append([r.get("segment"), _money(r.get("spend")), _money(r.get("sales")),
                      _roas(r.get("roas")), r.get("orders", "—"), r.get("pct_spend", "—")])
        m.append([])

    if data.get("by_segment"):
        section("By Segment")
        header(["Segment", "Spend", "Attributed Sales", "ROAS", "Count"])
        for r in data["by_segment"]:
            m.append([r.get("segment"), _money(r.get("spend")), _money(r.get("sales")),
                      _roas(r.get("roas")), r.get("count", "—")])
        m.append([])

    for key, label in (("top_five", "Top 5 Performers"), ("bottom_five", "Bottom 5 Performers")):
        if data.get(key):
            section(label)
            header(["Campaign", "Platform", "Location", "Spend", "Sales", "ROAS"])
            for r in data[key]:
                m.append([r.get("campaign"), r.get("platform"), r.get("location"),
                          _money(r.get("spend")), _money(r.get("sales")), _roas(r.get("roas"))])
            m.append([])

    if data.get("decline_alerts"):
        section("Decline Alerts")
        header(["Location / Campaign", "Trigger", "Severity", "Owner", "Action"])
        for r in data["decline_alerts"]:
            m.append([r.get("location"), r.get("trigger"), r.get("severity", ""),
                      r.get("owner", ""), r.get("action", "")])
        m.append([])

    if data.get("proposed"):
        section("Proposed Next Week")
        header(["Proposal", "Where", "Target ROAS", "Decision By", "Owner"])
        for r in data["proposed"]:
            m.append([r.get("proposal"), r.get("where", ""), _roas(r.get("target_roas")),
                      r.get("decision_by", ""), r.get("owner", "")])
        m.append([])

    if data.get("portfolio_trend"):
        section("Portfolio Trend")
        header(["Metric", "W-3", "W-2", "W-1", "This Week", "WoW"])
        for r in data["portfolio_trend"]:
            m.append([r.get("metric"), r.get("w_3", "—"), r.get("w_2", "—"),
                      r.get("w_1", "—"), r.get("w_0", "—"), r.get("wow", "—")])
        m.append([])

    if data.get("location_tier"):
        # Campaign-focused location view (payout/profitability lives in the weekly report).
        section("Location Tier — Campaign View")
        header(["Location", "Tier", "# Active", "Campaign Spend WTD", "Campaign Sales WTD",
                "Campaign ROAS", "Mkt Spend %", "Notes"])
        for r in data["location_tier"]:
            m.append([r.get("location"), r.get("tier", ""), r.get("active", "—"),
                      _money(r.get("spend")), _money(r.get("sales")), _roas(r.get("roas")),
                      r.get("mkt_pct", "—"), r.get("notes", "")])

    n = write_full_tab(sheet_id, "Dashboard", m,
                       section_header_rows=section_rows, col_header_rows=header_rows,
                       freeze_cols=1, title_rows=2)
    gid = _tab_gid(sheet_id, "Dashboard")
    reqs = []
    GREEN = {"red": 0.80, "green": 0.92, "blue": 0.80}
    AMBER = {"red": 0.99, "green": 0.96, "blue": 0.83}
    RED = {"red": 0.97, "green": 0.82, "blue": 0.82}

    def _bg(row, col, color):
        reqs.append({"repeatCell": {
            "range": {"sheetId": gid, "startRowIndex": row, "endRowIndex": row + 1,
                      "startColumnIndex": col, "endColumnIndex": col + 1},
            "cell": {"userEnteredFormat": {"backgroundColor": color}},
            "fields": "userEnteredFormat.backgroundColor"}})

    # Mkt Spend % cell vs the 3% north star.
    if mkt_pct_cell and mkt_pct_cell[2] is not None:
        v = mkt_pct_cell[2]
        _bg(mkt_pct_cell[0], mkt_pct_cell[1], GREEN if v <= 3 else AMBER if v <= 4 else RED)

    # Heat-color the ROAS / Mkt Spend % columns + the Action flag across the breakdown tables.
    for row, col, val, kind in heat_cells:
        if kind == "roas" and val is not None:
            _bg(row, col, GREEN if val >= 6 else AMBER if val >= 3 else RED)
        elif kind == "mktpct" and val is not None:
            _bg(row, col, GREEN if val <= 3 else AMBER if val <= 4 else RED)
        elif kind == "mom" and val is not None:
            # symmetric momentum heat: ±5% is signal, in between is noise-neutral
            if val >= 5:
                _bg(row, col, GREEN)
            elif val <= -5:
                _bg(row, col, RED)
        elif kind == "flag" and val:
            if "Scale" in val:
                _bg(row, col, GREEN)
            elif "Pull" in val:
                _bg(row, col, RED)
            elif "Watch" in val:
                _bg(row, col, AMBER)

    # KPI hero tiles: merge each 2-col card, big centered value, cream band, label muted.
    if tile_rows:
        lrow, vrow, wrow = tile_rows
        for c0 in (1, 3, 5, 7, 9):
            for rr in (lrow, vrow, wrow):
                reqs.append({"mergeCells": {"mergeType": "MERGE_ALL", "range": {
                    "sheetId": gid, "startRowIndex": rr, "endRowIndex": rr + 1,
                    "startColumnIndex": c0, "endColumnIndex": c0 + 2}}})

        def _tile_fmt(rr, size, color, bold=True):
            reqs.append({"repeatCell": {
                "range": {"sheetId": gid, "startRowIndex": rr, "endRowIndex": rr + 1,
                          "startColumnIndex": 1, "endColumnIndex": 11},
                "cell": {"userEnteredFormat": {"backgroundColor": SPICE_CREAM, "horizontalAlignment": "CENTER",
                         "verticalAlignment": "MIDDLE",
                         "textFormat": {"bold": bold, "fontSize": size, "foregroundColor": color}}},
                "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment,textFormat)"}})

        muted = {"red": 0.42, "green": 0.42, "blue": 0.45}
        _tile_fmt(lrow, 8, muted)          # label
        _tile_fmt(vrow, 18, INK_900)       # big value
        _tile_fmt(wrow, 9, muted, bold=False)  # WoW delta (vs last week)
        # Flag the Mkt Spend % hero tile (cols 3-4) against the 3% north star.
        msv = k.get("mkt_spend_pct_val")
        if msv is not None:
            _bg(vrow, 3, GREEN if msv <= 3 else AMBER if msv <= 4 else RED)

    if reqs:
        _service().spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": reqs}).execute()
    return n


def write_charts(sheet_id: str, data: dict) -> int:
    """Add embedded charts to the Dashboard (Spend vs Sales by platform + by location, ROAS by
    platform). Numeric source lands on a hidden _ChartData tab; existing Dashboard charts are
    deleted first so re-runs don't stack. Returns the number of charts added."""
    svc = _service()
    # Ensure the hidden data tab.
    meta = get_metadata(sheet_id)
    if "_ChartData" not in meta["tabs"]:
        svc.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": [
            {"addSheet": {"properties": {"title": "_ChartData", "hidden": True,
                                         "gridProperties": {"rowCount": 60, "columnCount": 12}}}}]}).execute()
        _GID_CACHE.pop(sheet_id, None)
    cd = _tab_gid(sheet_id, "_ChartData")
    dash = _tab_gid(sheet_id, "Dashboard")

    plats = data.get("by_platform", []) or []
    locs = (data.get("by_location", []) or [])[:8]
    pmat = [["Platform", "Spend", "Attributed Sales", "ROAS"]] + \
           [[p.get("platform"), round(p.get("spend", 0)), round(p.get("sales", 0)), p.get("roas", 0)] for p in plats]
    lmat = [["Location", "Spend", "Attributed Sales"]] + \
           [[l.get("location"), round(l.get("spend", 0)), round(l.get("sales", 0))] for l in locs]
    svc.spreadsheets().values().clear(spreadsheetId=sheet_id, range="_ChartData!A1:Z100", body={}).execute()
    svc.spreadsheets().values().update(spreadsheetId=sheet_id, range="_ChartData!A1",
                                       valueInputOption="RAW", body={"values": pmat}).execute()
    svc.spreadsheets().values().update(spreadsheetId=sheet_id, range="_ChartData!F1",
                                       valueInputOption="RAW", body={"values": lmat}).execute()
    trend = data.get("marketing_organic_trend") or []
    tmat = [["Week", "Marketing-Driven", "Organic"]] + \
           [[t.get("week"), round(t.get("mktg_driven", 0)), round(t.get("organic", 0))] for t in trend]
    if len(tmat) > 1:
        svc.spreadsheets().values().update(spreadsheetId=sheet_id, range="_ChartData!K1",
                                           valueInputOption="RAW", body={"values": tmat}).execute()

    # Delete existing Dashboard charts.
    full = svc.spreadsheets().get(spreadsheetId=sheet_id,
                                  fields="sheets(properties(sheetId),charts(chartId))").execute()
    dels = [{"deleteEmbeddedObject": {"objectId": c["chartId"]}}
            for s in full["sheets"] if s["properties"]["sheetId"] == dash
            for c in s.get("charts", [])]
    if dels:
        svc.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": dels}).execute()

    def _src(r0, r1, c0, c1):
        return {"sources": [{"sheetId": cd, "startRowIndex": r0, "endRowIndex": r1,
                             "startColumnIndex": c0, "endColumnIndex": c1}]}

    def _col_chart(title, nrows, dom_c, series_cs, anchor_row, ctype="COLUMN", stacked=False):
        bc = {"chartType": ctype, "legendPosition": "BOTTOM_LEGEND", "headerCount": 1,
              "domains": [{"domain": {"sourceRange": _src(0, nrows, dom_c, dom_c + 1)}}],
              "series": [{"series": {"sourceRange": _src(0, nrows, c, c + 1)}, "targetAxis": "LEFT_AXIS"}
                         for c in series_cs]}
        if stacked:
            bc["stackedType"] = "STACKED"
        return {"addChart": {"chart": {
            "spec": {"title": title, "basicChart": bc},
            "position": {"overlayPosition": {
                "anchorCell": {"sheetId": dash, "rowIndex": anchor_row, "columnIndex": 11},
                "widthPixels": 460, "heightPixels": 280}}}}}

    adds = []
    if len(pmat) > 1:
        adds.append(_col_chart("Spend vs Attributed Sales by Platform", len(pmat), 0, [1, 2], 3))
        adds.append(_col_chart("ROAS by Platform", len(pmat), 0, [3], 19))
    if len(lmat) > 1:
        adds.append(_col_chart("Spend vs Sales by Location (Top 8)", len(lmat), 5, [6, 7], 35))
    if len(tmat) > 1:
        adds.append(_col_chart("Marketing-Driven vs Organic (weekly)", len(tmat), 10, [11, 12], 51, stacked=True))
    if adds:
        svc.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": adds}).execute()
    return len(adds)


def write_placeholder(sheet_id: str, tab: str, title: str, lines: list) -> int:
    """Write a clean title + note to a tab when there's no real data to show — used instead of
    leaving stale/dummy numbers in the per-campaign tabs."""
    m = [[title], []] + [[ln] for ln in lines]
    return write_full_tab(sheet_id, tab, m, title_rows=1)


def write_ads_reporting(sheet_id: str, data: dict) -> int:
    """Full-tab rewrite of Ads Reporting. Sections: Aggregate (WoW) · Per-Campaign funnel ·
    Audience Segmentation.

    Data shape:
      {
        "aggregate": [{"metric","current","prior","wow"}, ...],
        "per_campaign": [{"campaign","platform","audience","location","impressions","clicks",
                          "ctr","spend","cpc","orders","sales","roas","cpo"}, ...],
        "audience": [{"segment","campaigns","spend","sales","roas","pct"}, ...],
      }
    """
    m: list[list[Any]] = []
    section_rows, header_rows = [], []

    def section(t): m.append([t]); section_rows.append(len(m) - 1)
    def header(c): m.append(c); header_rows.append(len(m) - 1)

    m.append(["Ads Reporting (Sponsored Listings)"])
    m.append(["Platform-reported attribution — totals differ from the Dashboard's settled figures."])

    if data.get("aggregate"):
        section("Ads Summary")
        header(["Metric", "This Week", "Last Week", "WoW"])
        for r in data["aggregate"]:
            m.append([r.get("metric"), r.get("current", "—"), r.get("prior", "—"), r.get("wow", "—")])
        m.append([])

    if data.get("per_campaign"):
        # Drop the funnel columns (Impressions/Clicks/CTR/CPC) when the export carries no
        # impression data — otherwise they're a wall of "n/a". They reappear automatically
        # once an export includes impressions.
        funnel = data.get("has_funnel", False)
        section("Per-Campaign Funnel" if funnel else "Per-Campaign Performance")
        cols = ["Campaign", "Platform", "Audience", "Location"]
        if funnel:
            cols += ["Impressions", "Clicks", "CTR"]
        cols += ["Spend"]
        if funnel:
            cols += ["CPC"]
        cols += ["Orders", "Sales", "ROAS", "CPO"]
        header(cols)
        for r in data["per_campaign"]:
            row = [r.get("campaign"), r.get("platform"), r.get("audience", "All"), r.get("location")]
            if funnel:
                row += [r.get("impressions", "n/a"), r.get("clicks", "—"), r.get("ctr", "n/a")]
            row += [_money(r.get("spend"))]
            if funnel:
                row += [r.get("cpc", "n/a")]
            row += [r.get("orders", "—"), _money(r.get("sales")), _roas(r.get("roas")), r.get("cpo", "—")]
            m.append(row)
        m.append([])

    if data.get("audience"):
        section("Audience Segmentation")
        header(["Segment", "Campaigns", "Spend", "Sales", "ROAS", "% of Total"])
        for r in data["audience"]:
            m.append([r.get("segment"), r.get("campaigns", "—"), _money(r.get("spend")),
                      _money(r.get("sales")), _roas(r.get("roas")), r.get("pct", "—")])

    return write_full_tab(sheet_id, "Ads Reporting", m,
                          section_header_rows=section_rows, col_header_rows=header_rows,
                          freeze_cols=1, title_rows=2)


def write_offers_reporting(sheet_id: str, data: dict) -> int:
    """Full-tab rewrite of Offers Reporting. Sections: Aggregate (WoW) · Per-Promo · Audience split.

    Data shape:
      {
        "aggregate": [{"metric","current","prior","wow"}, ...],
        "per_promo": [{"promo","platform","locations","audience","threshold","discount",
                       "orders","sales","spend","roas","new_cx","pct_new","status"}, ...],
        "audience": [{"audience","orders","sales","aov","pct"}, ...],
      }
    """
    m: list[list[Any]] = []
    section_rows, header_rows = [], []

    def section(t): m.append([t]); section_rows.append(len(m) - 1)
    def header(c): m.append(c); header_rows.append(len(m) - 1)

    m.append(["Offers Reporting (Promotions)"])
    m.append(["Platform-reported attribution — totals differ from the Dashboard's settled figures. UE offers carry no spend."])

    if data.get("aggregate"):
        section("Offers Summary")
        header(["Metric", "This Week", "Last Week", "WoW"])
        for r in data["aggregate"]:
            m.append([r.get("metric"), r.get("current", "—"), r.get("prior", "—"), r.get("wow", "—")])
        m.append([])

    if data.get("per_promo"):
        section("Per-Promo")
        header(["Promo", "Platform", "Locations", "Audience", "Threshold", "Discount",
                "Orders", "Sales", "Spend", "ROAS", "New Cx", "% New", "Status"])
        for r in data["per_promo"]:
            reported = r.get("spend_reported", True)
            spend_cell = _money(r.get("spend")) if reported else "n/a"
            roas_cell = _roas(r.get("roas")) if reported else "n/a"
            m.append([r.get("promo"), r.get("platform"), r.get("locations"), r.get("audience", "All"),
                      r.get("threshold", "—"), r.get("discount", "—"), r.get("orders", "—"),
                      _money(r.get("sales")), spend_cell, roas_cell,
                      r.get("new_cx", "—"), r.get("pct_new", "—"), r.get("status", "")])
        m.append([])

    if data.get("audience"):
        section("New vs Existing Split")
        header(["Audience", "Orders", "Sales", "AOV", "% of Total"])
        for r in data["audience"]:
            m.append([r.get("audience"), r.get("orders", "—"), _money(r.get("sales")),
                      _money(r.get("aov")), r.get("pct", "—")])

    return write_full_tab(sheet_id, "Offers Reporting", m,
                          section_header_rows=section_rows, col_header_rows=header_rows,
                          freeze_cols=1, title_rows=2)


ARCHIVE_COLS = ["Year", "Quarter", "Week", "Campaign Name", "Type", "Platform",
                "Locations", "Audience", "Threshold", "Discount", "Start Date", "End Date",
                "Status", "Total Spend", "Total Sales", "Total Orders", "Avg ROAS", "New Cx",
                "Test?", "Hypothesis", "Outcome / Learnings", "Continue?"]


def append_archive(sheet_id: str, ended_rows: list[dict]) -> int:
    """Append Ended campaigns to Archive. NEVER clears — existing curation is preserved.
    Idempotent: skips campaigns already archived (keyed on Campaign Name + End Date), so
    re-runs don't double-archive. Hypothesis/Outcome/Continue stay blank for the GM.
    """
    if not ended_rows:
        return 0
    existing = _service().spreadsheets().values().get(
        spreadsheetId=sheet_id, range="Archive!A2:L100000").execute().get("values", [])
    # Campaign Name = col D (idx 3), End Date = col L (idx 11)
    seen = {(r[3], r[11] if len(r) > 11 else "") for r in existing if len(r) > 3}
    fresh = [r for r in ended_rows if (r.get("Campaign Name", ""), r.get("End Date", "")) not in seen]
    if not fresh:
        return 0
    matrix = [[r.get(c, "") for c in ARCHIVE_COLS] for r in fresh]
    return append_rows(sheet_id, "Archive", matrix)


# ---- CLI ----

def _cmd_meta(args):
    m = get_metadata(args.sheet_id)
    print(f"TABS ({len(m['tabs'])}):")
    for name, gid in m["tabs"].items():
        flag = "  ⛔ protected" if any(p in name.lower() for p in PROTECTED_TAB_SUBSTRINGS) else ""
        print(f"  {name:34s} gid={gid}{flag}")
    print(f"\nNAMED RANGES ({len(m['named_ranges'])}):")
    if not m["named_ranges"]:
        print("  (none — run `setup-ranges` to create the canonical set)")
    else:
        for name in sorted(m["named_ranges"]):
            print(f"  ✓ {name}")
    missing = [n for n in NAMED_RANGES if n not in m["named_ranges"]]
    if missing:
        print(f"\nMISSING canonical named ranges ({len(missing)}):")
        for n in missing:
            tab = NAMED_RANGES[n]["tab"]
            tab_present = "✓ tab exists" if tab in m["tabs"] else f"✗ tab missing: {tab!r}"
            print(f"  • {n:34s} ({tab_present})")


def validate_sheet(sheet_id: str) -> dict:
    """Post-write structural QA. Returns {ok: bool, errors: [...], warnings: [...]}.

    Catches the failure modes that hand-building introduces:
      - missing canonical tabs
      - a data-tab header row that's numeric (the off-by-one bug — Santi's Offers Totals)
      - Active Campaigns header drift (column count / first header mismatch)
    The skill runs this after a refresh; a non-ok result is surfaced, not silently shipped.
    """
    meta = get_metadata(sheet_id)
    tabs = meta["tabs"]
    errors, warnings = [], []

    required = ["Dashboard", "Active Campaigns", "Ads Reporting", "Offers Reporting",
                "Archive", "History", "Account Learnings"]
    for t in required:
        if t not in tabs:
            errors.append(f"missing canonical tab: {t}")

    svc = _service()

    def _row(tab, a1):
        try:
            v = svc.spreadsheets().values().get(spreadsheetId=sheet_id, range=f"'{tab}'!{a1}").execute()
            return (v.get("values") or [[]])[0]
        except Exception:
            return []

    # Active Campaigns: accept either the flat planning registry (A1 = "Campaign Name") or the
    # by-location view (A1 = the "Active Campaigns by Location…" title). Either is valid; a
    # blank/numeric A1 would signal drift.
    if "Active Campaigns" in tabs:
        h = _row("Active Campaigns", "A1:U1")
        a1 = h[0] if h else ""
        if a1 and not (a1 == "Campaign Name" or a1.startswith("Active Campaigns")):
            errors.append(f"Active Campaigns header drift: A1 = {a1!r}, expected 'Campaign Name' "
                          f"or an 'Active Campaigns…' title")

    # Off-by-one detector: in the reporting tabs, scan for a row whose first cell is a known
    # aggregate-table header label ("Metric") followed by NUMERIC cells in the same row —
    # that means values bled into the header row.
    def _is_num(x):
        s = str(x).replace("$", "").replace(",", "").replace("%", "").replace("x", "").strip()
        if s in ("", "—", "n/a"):
            return False
        try:
            float(s); return True
        except ValueError:
            return False
    for tab in ("Ads Reporting", "Offers Reporting", "Dashboard"):
        if tab not in tabs:
            continue
        block = svc.spreadsheets().values().get(spreadsheetId=sheet_id, range=f"'{tab}'!A1:H80").execute().get("values", [])
        for row in block:
            if row and str(row[0]).strip() == "Metric":
                # the cells after "Metric" should be text labels (This Week / Last Week / WoW), NOT numbers
                if any(_is_num(c) for c in row[1:4]):
                    errors.append(f"{tab}: off-by-one — 'Metric' header row contains numeric values "
                                  f"({[c for c in row[1:4]]}). Data bled into the header; shift down one row.")
                break

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def _cmd_validate(args):
    r = validate_sheet(args.sheet_id)
    print("VALIDATION:", "✓ PASS" if r["ok"] else "✗ FAIL")
    for e in r["errors"]:
        print("  ✗", e)
    for w in r["warnings"]:
        print("  ⚠", w)
    if not r["ok"]:
        sys.exit(1)


def delete_tabs(sheet_id: str, titles: list[str]) -> list[str]:
    """Delete tabs by title. Returns the titles actually deleted. Use for retiring
    superseded v0.1 tabs (Campaign Tracker, Legend & Cadence) when migrating to v2."""
    meta = get_metadata(sheet_id)
    svc = _service()
    reqs, deleted = [], []
    for t in titles:
        if t in meta["tabs"]:
            reqs.append({"deleteSheet": {"sheetId": meta["tabs"][t]}})
            deleted.append(t)
    if reqs:
        svc.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": reqs}).execute()
        _GID_CACHE.pop(sheet_id, None)
    return deleted


def _cmd_delete_tabs(args):
    d = delete_tabs(args.sheet_id, args.titles)
    print(f"deleted {len(d)} tab(s): {', '.join(d) if d else '(none matched)'}")


def _cmd_ensure_tabs(args):
    r = ensure_template_tabs(args.sheet_id, dry_run=args.dry_run)
    tag = " (DRY RUN)" if args.dry_run else ""
    print(f"created {len(r['created'])} tab(s){tag}:")
    for n in r["created"]:
        print(f"  + {n}")
    if r["existing"]:
        print(f"\nalready existed ({len(r['existing'])}):")
        for n in r["existing"]:
            print(f"  = {n}")


def _cmd_setup_ranges(args):
    r = setup_named_ranges(args.sheet_id, dry_run=args.dry_run)
    tag = " (DRY RUN)" if args.dry_run else ""
    print(f"created {len(r['created'])} named ranges{tag}:")
    for n in r["created"]:
        print(f"  + {n}")
    if r["skipped_existing"]:
        print(f"\nalready existed ({len(r['skipped_existing'])}):")
        for n in r["skipped_existing"]:
            print(f"  = {n}")
    if r["skipped_missing_tab"]:
        print(f"\nSKIPPED ({len(r['skipped_missing_tab'])}) — tab not in Sheet:")
        for n, t in r["skipped_missing_tab"]:
            print(f"  ✗ {n}  needs tab: '{t}'")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    p_meta = sub.add_parser("meta", help="read tabs + named ranges (smoke test, read-only)")
    p_meta.add_argument("--sheet-id", required=True)
    p_setup = sub.add_parser("setup-ranges", help="define the canonical named ranges (one-time per Sheet)")
    p_setup.add_argument("--sheet-id", required=True)
    p_setup.add_argument("--dry-run", action="store_true")
    p_tabs = sub.add_parser("ensure-tabs", help="create the canonical v2 tabs if missing")
    p_tabs.add_argument("--sheet-id", required=True)
    p_tabs.add_argument("--dry-run", action="store_true")
    p_del = sub.add_parser("delete-tabs", help="delete tabs by title (retire superseded v0.1 tabs)")
    p_del.add_argument("--sheet-id", required=True)
    p_del.add_argument("--titles", nargs="+", required=True)
    p_val = sub.add_parser("validate", help="post-write structural QA (catches off-by-one + drift)")
    p_val.add_argument("--sheet-id", required=True)
    args = ap.parse_args()
    {"meta": _cmd_meta, "setup-ranges": _cmd_setup_ranges, "ensure-tabs": _cmd_ensure_tabs,
     "delete-tabs": _cmd_delete_tabs, "validate": _cmd_validate}[args.command](args)


if __name__ == "__main__":
    main()
