#!/usr/bin/env python3
"""Cross-pull net sales (the denominator for the marketing-efficiency % metrics) from the
client's weekly sales sheet.

The sales sheet is wide-format: ISO week numbers across the columns, metric rows grouped under
section headers. We map the target weekstart -> its ISO-week column, then read the "Net Sales"
row under each section:
  - platform tab ("Weekly Platform Overview 2.0"): Overview (= total) + UBER EATS / DOORDASH / GRUBHUB
  - location tab ("By Location 2.0"): one section per store

Returns {"total": N, "platform": {canonical: N}, "location": {store: N}} — the exact shape
v2_aggregate.dashboard_from_data expects for net_sales. Read-only; uses the same service account.
"""
from __future__ import annotations
import datetime as dt
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sheets_writer as sw  # reuse the cached service-account client

PLATFORM_CANON = {"UBER EATS": "Uber Eats", "DOORDASH": "DoorDash", "GRUBHUB": "Grubhub"}
_SKIP_SECTIONS = {"platform", "goop kitchen", "notes"}


def _num(v) -> float:
    s = str(v).replace("$", "").replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return 0.0


def _read(sheet_id: str, tab: str) -> list:
    return sw._service().spreadsheets().values().get(
        spreadsheetId=sheet_id, range=f"'{tab}'!A1:BZ400").execute().get("values", [])


def _week_col(rows: list, iso_week: int) -> int | None:
    """Find the column index for an ISO week. The header row is the one whose col B is 'Week'."""
    for r in rows:
        if len(r) > 1 and str(r[1]).strip().lower() == "week":
            for i, c in enumerate(r):
                if str(c).strip() == str(iso_week):
                    return i
    return None


def _extract(rows: list, week_col: int, canon: dict | None = None) -> dict:
    """Walk section headers; capture each section's 'Net Sales' value at week_col."""
    out, cur = {}, None
    for r in rows:
        a = r[0].strip() if len(r) > 0 and r[0] else ""
        b = r[1].strip() if len(r) > 1 and r[1] else ""
        if a and not b and a.lower() not in _SKIP_SECTIONS:
            cur = a
        elif a == "Net Sales" and cur and week_col is not None and week_col < len(r):
            name = (canon or {}).get(cur.upper(), cur)
            out[name] = _num(r[week_col])
    return out


def pull_net_sales(sheet_id: str, weekstart: str,
                   platform_tab: str = "Weekly Platform Overview 2.0",
                   location_tab: str = "By Location 2.0") -> dict:
    iso = dt.date.fromisoformat(weekstart).isocalendar()[1]
    out = {"total": 0.0, "platform": {}, "location": {}}

    pv = _read(sheet_id, platform_tab)
    pcol = _week_col(pv, iso)
    if pcol is not None:
        psec = _extract(pv, pcol, PLATFORM_CANON)
        out["total"] = psec.get("Overview", 0)
        out["platform"] = {k: v for k, v in psec.items() if k in PLATFORM_CANON.values()}

    lv = _read(sheet_id, location_tab)
    lcol = _week_col(lv, iso)
    if lcol is not None:
        out["location"] = _extract(lv, lcol)

    if not out["total"] and out["platform"]:
        out["total"] = sum(out["platform"].values())
    return out


# Canonical metric labels (weekly-reporting methodology) -> our keys.
METRIC_KEYS = {
    "total sales": "total_sales", "net sales": "net_sales", "discounts": "discounts",
    "ad spend": "ad_spend", "marketing driven sales": "mktg_driven_sales",
    "organic sales": "organic_sales", "total orders": "total_orders",
    "orders from marketing": "mktg_orders", "organic orders": "organic_orders", "aov": "aov",
    "total marketing investment": "mktg_investment", "marketing spend / sales %": "mkt_spend_pct",
    "marketing roas": "roas", "marketing cpo": "cpo", "blended roas": "blended_roas",
}


def _extract_all(rows: list, week_col: int) -> dict:
    """Walk section headers; capture EVERY canonical metric (raw display string) at week_col.
    Returns {section_name: {metric_key: raw_string}}."""
    out, cur = {}, None
    for r in rows:
        a = r[0].strip() if len(r) > 0 and r[0] else ""
        b = r[1].strip() if len(r) > 1 and r[1] else ""
        if a and not b and a.lower() not in _SKIP_SECTIONS:
            cur = a
            out.setdefault(cur, {})
        elif cur and a.lower() in METRIC_KEYS and week_col is not None and week_col < len(r):
            out[cur][METRIC_KEYS[a.lower()]] = r[week_col]
    return out


def pull_sales_metrics(sheet_id: str, weekstart: str,
                       platform_tab: str = "Weekly Platform Overview 2.0",
                       location_tab: str = "By Location 2.0") -> dict:
    """Cross-pull the canonical weekly-reporting metrics (already deduped + correct) per scope.
    Returns {"overview": {...}, "platform": {canonical_name: {...}}, "location": {store: {...}}}
    where each inner dict maps metric_key -> raw display string."""
    iso = dt.date.fromisoformat(weekstart).isocalendar()[1]
    pv = _read(sheet_id, platform_tab)
    psec = _extract_all(pv, _week_col(pv, iso))
    lv = _read(sheet_id, location_tab)
    lsec = _extract_all(lv, _week_col(lv, iso))
    platform = {PLATFORM_CANON.get(k.upper(), k): v for k, v in psec.items() if k.upper() in PLATFORM_CANON}
    return {"overview": psec.get("Overview", {}), "platform": platform, "location": lsec}


def pull_overview_trend(sheet_id: str, weekstart: str, n: int = 6,
                        platform_tab: str = "Weekly Platform Overview 2.0") -> list:
    """Pull the last n weeks of overall Marketing-Driven vs Organic sales (the incrementality
    read: is marketing additive or cannibalizing organic?). Returns oldest→newest list of
    {week, mktg_driven, organic}."""
    iso = dt.date.fromisoformat(weekstart).isocalendar()[1]
    rows = _read(sheet_id, platform_tab)
    wcol = _week_col(rows, iso)
    if wcol is None:
        return []
    date_row = next((r for r in rows if len(r) > 1 and str(r[1]).strip().lower() == "metric"), None)
    cur, mds_row, org_row = None, None, None
    for r in rows:
        a = r[0].strip() if r and r[0] else ""
        b = r[1].strip() if len(r) > 1 and r[1] else ""
        if a and not b and a.lower() not in _SKIP_SECTIONS:
            if cur == "Overview":
                break  # passed the Overview block
            cur = a
        elif cur == "Overview":
            if a.lower() == "marketing driven sales":
                mds_row = r
            elif a.lower() == "organic sales":
                org_row = r
    out = []
    for c in range(max(2, wcol - (n - 1)), wcol + 1):
        wk = date_row[c] if date_row and c < len(date_row) else str(c)
        out.append({"week": wk,
                    "mktg_driven": _num(mds_row[c]) if mds_row and c < len(mds_row) else 0,
                    "organic": _num(org_row[c]) if org_row and c < len(org_row) else 0})
    return out


def pull_tier_map(sheet_id: str, tier_tab: str = "By Tier") -> dict:
    """Parse the By Tier tab's section headers (e.g. '🔴 RED | San Jose, Pasadena') into a
    {location: tier} map so the campaign dashboard can segment by store tier. Tier is one of
    Red / Yellow / Green."""
    rows = _read(sheet_id, tier_tab)
    out = {}
    for r in rows:
        a = (r[0].strip() if r and r[0] else "")
        if "|" not in a:
            continue
        left, right = a.split("|", 1)
        low = left.lower()
        tier = ("Red" if "red" in low else "Yellow" if "yellow" in low
                else "Green" if "green" in low else None)
        if not tier:
            continue
        for loc in [x.strip() for x in right.replace(";", ",").split(",") if x.strip()]:
            out[loc] = tier
    return out


if __name__ == "__main__":
    import argparse
    import json
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet-id", required=True)
    ap.add_argument("--weekstart", required=True)
    args = ap.parse_args()
    print(json.dumps(pull_net_sales(args.sheet_id, args.weekstart), indent=2))
