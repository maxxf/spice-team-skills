#!/usr/bin/env python3
"""Build a client Campaign Plan & Performance Tracker .xlsx.

Reads campaign rows from a tracker CSV (produced by the team from platform exports,
or exported from the Campaign Planning DB) and renders a formatted 3-tab workbook:
Dashboard (rollups overall / by platform / ads vs offers + chart) + Campaign Tracker
(conditional-formatted status) + Legend.

Usage:
  python build_campaign_plan_xlsx.py --client "goop Kitchen" --tracker-csv rows.csv --output out.xlsx
  python build_campaign_plan_xlsx.py --client "goop Kitchen" --output out.xlsx   # uses embedded goop sample

Tracker CSV columns (header row, in this order):
  Campaign, Platform, Type, Offer/Ad Detail, Locations, Status, Days in Queue,
  Flight Start, Flight End, Target ROAS, Actual ROAS, Spend, Attributed Sales,
  Incremental Orders, In-Platform Campaign Name, Notes

Status values: Live | Proposed | Blocked-on-client | Ended
Type values: Offer | Ad
"""
from __future__ import annotations
import argparse
import csv
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import CellIsRule
from openpyxl.utils import get_column_letter

CHARCOAL, SAGE, RED, AMBER, BLUE, GRAY, WHITE = "1F2937", "84CC16", "B91C1C", "F59E0B", "2563EB", "9CA3AF", "FFFFFF"
thin = Side(style="thin", color="D1D5DB")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
hdr_font = Font(name="Arial", size=10, bold=True, color=WHITE)
hdr_fill = PatternFill("solid", fgColor=CHARCOAL)
title_font = Font(name="Arial", size=16, bold=True, color=CHARCOAL)
sub_font = Font(name="Arial", size=9, italic=True, color="6B7280")
cell_font = Font(name="Arial", size=10, color=CHARCOAL)
kpi_label = Font(name="Arial", size=9, bold=True, color="6B7280")
kpi_value = Font(name="Arial", size=20, bold=True, color=CHARCOAL)
section_font = Font(name="Arial", size=12, bold=True, color=CHARCOAL)
center = Alignment(horizontal="center", vertical="center", wrap_text=True)
left = Alignment(horizontal="left", vertical="center", wrap_text=True)

TRACKER_COLS = ["Campaign", "Platform", "Type", "Offer / Ad Detail", "Locations",
                "Status", "Days in Queue", "Flight Start", "Flight End",
                "Target ROAS", "Actual ROAS", "Spend ($)", "Attributed Sales ($)",
                "Incremental Orders", "In-Platform Campaign Name", "Notes"]

# Embedded goop sample (used when no --tracker-csv given). Mirrors the audit data.
GOOP_SAMPLE = [
    ["Spend X Save Y (aggressive)", "Uber Eats", "Offer", "Tiered spend/save, lowered thresholds", "San Jose / Pasadena", "Live", "", "2026-05-15", "ongoing", 3.5, "", "", "", "", "San Jose | Spend X Save Y | All", "Drove San Jose conversion 25%->33%"],
    ["Spend X Save Y (aggressive)", "DoorDash", "Offer", "Tiered spend/save, lowered thresholds", "San Jose / Pasadena", "Live", "", "2026-05-15", "ongoing", 3.5, "", "", "", "", "San Jose | Spend X Save Y | All", "Second-best sales week of year ($50K SJ)"],
    ["Friday aggression tweak", "Uber Eats", "Offer", "Higher Friday promo depth", "San Jose / Pasadena", "Live", "", "2026-05-16", "ongoing", "", "", "", "", "", "Pasadena | Friday Depth | All", "Pasadena best delivery week of year"],
    ["Friday aggression tweak", "DoorDash", "Offer", "Higher Friday promo depth", "San Jose / Pasadena", "Live", "", "2026-05-16", "ongoing", "", "", "", "", "", "Pasadena | Friday Depth | All", "Ratings velocity 38 (from 20-22 baseline)"],
    ["SJ + Pasadena BOGA", "Uber Eats", "Offer", "Buy one get one add-on", "San Jose / Pasadena", "Blocked-on-client", 11, "TBD", "", 3.0, "", "", "", "", "San Jose | BOGA | All", "Awaiting goop sign-off, 11 days in queue"],
    ["SJ + Pasadena BOGA", "DoorDash", "Offer", "Buy one get one add-on", "San Jose / Pasadena", "Blocked-on-client", 11, "TBD", "", 3.0, "", "", "", "", "San Jose | BOGA | All", "Awaiting goop sign-off, 11 days in queue"],
    ["Berkeley launch", "Uber Eats", "Offer", "New-market intro offer", "Berkeley", "Proposed", "", "2026-06-08", "", "", "", "", "", "", "Berkeley | Intro Offer | New", "New market launch, spec ready"],
    ["Berkeley launch", "DoorDash", "Offer", "New-market intro offer", "Berkeley", "Proposed", "", "2026-06-08", "", "", "", "", "", "", "Berkeley | Intro Offer | New", "New market launch, spec ready"],
    ["Berkeley launch", "Grubhub", "Offer", "New-market intro offer", "Berkeley", "Proposed", "", "2026-06-08", "", "", "", "", "", "", "Berkeley | Intro Offer | New", "New market launch, spec ready"],
    ["Studio softness test", "Uber Eats", "Offer", "Spend $15 get $5 off + increased ad spend", "Studio City", "Proposed", "", "TBD", "", 3.0, "", "", "", "", "Studio City | Spend 15 Save 5 | All", "Requested by Lauren 5/21"],
    ["Meta ads", "Meta", "Ad", "Paid social", "San Jose / Pasadena", "Ended", "", "prior", "2026-05-13", "", "", 0, "", "", "Meta | Paid Social | All", "Killed 5/13. Freed $1,150/wk, no demand loss"],
]


def _perf_num(s):
    """Parse a weekly-reporting formatted value ('$1,234', '6.2', '--', '--*') to float or None."""
    if s is None:
        return None
    s = str(s).strip().replace("$", "").replace(",", "").replace("x", "")
    if s in ("", "--", "--*", "-"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _derive_type(campaign_type: str) -> str:
    """Map weekly-reporting 'Campaign Type' to the tracker's Ad/Offer dimension."""
    t = (campaign_type or "").lower()
    if any(k in t for k in ("sponsor", "featured", "ad", "paid", "listing")):
        return "Ad"
    return "Offer"


def _loc_tokens(locations: str) -> list[str]:
    """Split a tracker Locations cell ('San Jose / Pasadena') into normalized tokens."""
    raw = str(locations or "").replace(",", "/").split("/")
    return [t.strip().lower() for t in raw if t.strip()]


def _loc_match(tracker_locs: str, perf_loc: str) -> bool:
    """A perf row's single Location matches a tracker row if it overlaps any token,
    or the tracker row targets All/blank/whole-account."""
    toks = _loc_tokens(tracker_locs)
    pl = str(perf_loc or "").strip().lower()
    if not toks or "all" in toks:
        return True
    if not pl or pl in ("all", "total"):
        return True
    return any(t in pl or pl in t for t in toks)


# Tokens that don't identify a campaign — drop them before name-overlap matching.
_NAME_STOPWORDS = {"all", "the", "and", "new", "aggressive", "tweak", "test", "promo",
                   "depth", "launch", "ads", "ad", "offer", "listing", "sponsored", "paid"}


def _name_tokens(*parts: str) -> set:
    out = set()
    for part in parts:
        for raw in str(part or "").replace("|", " ").replace("/", " ").replace("(", " ").replace(")", " ").split():
            t = raw.strip().lower()
            if len(t) >= 3 and t not in _NAME_STOPWORDS:
                out.add(t)
    return out


def _name_match(tracker_campaign: str, tracker_inplatform: str, perf_campaign_type: str) -> bool:
    """Require a meaningful token overlap between the perf row's Campaign Type and the
    tracker row's Campaign name or In-Platform Campaign Name. Disambiguates concurrent
    live campaigns on the same platform+locations (e.g. Spend X Save Y vs Friday Depth)."""
    perf_toks = _name_tokens(perf_campaign_type)
    if not perf_toks:
        return True  # perf row has no identifying name; fall back to platform+type+location
    track_toks = _name_tokens(tracker_campaign, tracker_inplatform)
    return bool(perf_toks & track_toks)


def apply_campaign_perf(tracker_rows: list[list], perf_rows: list[dict], overwrite: bool = False):
    """Fold weekly-reporting campaign_performance.csv rows into the tracker's performance
    columns. Match key: Platform + derived Type + Location overlap + campaign-name token
    overlap, restricted to tracker rows whose Status is Live or Ended (Proposed/Blocked
    campaigns haven't run, so they get no performance). Sums all matching perf rows into
    each tracker row. Returns (matched_tracker_count, unmatched_perf_rows).

    Columns filled (0-indexed): 10 Actual ROAS, 11 Spend, 12 Attributed Sales, 13 Incremental Orders.
    Only fills empty cells unless overwrite=True. Never silently drops perf rows — anything that
    matched no tracker row is returned for the GM to map.
    """
    used = [False] * len(perf_rows)
    matched_tracker = 0
    for row in tracker_rows:
        platform, ttype, locs, status = row[1], row[2], row[4], row[5]
        if str(status).strip() not in ("Live", "Ended"):
            continue  # no performance for campaigns that haven't run
        spend = sales = orders = 0.0
        hit = False
        for i, p in enumerate(perf_rows):
            if str(p.get("Platform", "")).strip().lower() != str(platform).strip().lower():
                continue
            if _derive_type(p.get("Campaign Type", "")) != str(ttype).strip():
                continue
            if not _loc_match(locs, p.get("Location", "")):
                continue
            if not _name_match(row[0], row[14], p.get("Campaign Type", "")):
                continue
            sp, sa, od = _perf_num(p.get("Spend")), _perf_num(p.get("Sales")), _perf_num(p.get("Orders"))
            if sp is None and sa is None and od is None:
                continue
            spend += sp or 0.0
            sales += sa or 0.0
            orders += od or 0.0
            used[i] = True
            hit = True
        if not hit:
            continue
        matched_tracker += 1
        roas = round(sales / spend, 2) if spend else None
        fills = {11: round(spend, 2), 12: round(sales, 2), 13: int(round(orders)), 10: roas}
        for col, val in fills.items():
            if val is None:
                continue
            if overwrite or row[col] in ("", None):
                row[col] = val
    unmatched = [perf_rows[i] for i in range(len(perf_rows)) if not used[i]]
    return matched_tracker, unmatched


def read_perf_csv(path: str) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def read_tracker_csv(path: str) -> list[list]:
    rows = []
    with open(path, newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # header
        for row in reader:
            row = (row + [""] * len(TRACKER_COLS))[:len(TRACKER_COLS)]
            for i in (9, 10, 11, 12, 13):  # numeric-ish columns
                if row[i] not in ("", None):
                    try:
                        row[i] = float(row[i])
                    except (ValueError, TypeError):
                        pass
            rows.append(row)
    return rows


def build(client: str, tracker_rows: list[list], highlights: list[str], out: str):
    wb = Workbook()
    tr = wb.active
    tr.title = "Campaign Tracker"
    for c, h in enumerate(TRACKER_COLS, start=1):
        cell = tr.cell(row=1, column=c, value=h)
        cell.font, cell.fill, cell.alignment, cell.border = hdr_font, hdr_fill, center, border
    for r, row in enumerate(tracker_rows, start=2):
        for c, val in enumerate(row, start=1):
            cell = tr.cell(row=r, column=c, value=val)
            cell.font = cell_font
            cell.alignment = left if c in (1, 4, 5, 15, 16) else center
            cell.border = border
            if c in (10, 11):
                cell.number_format = '0.0"x"'
            if c in (12, 13):
                cell.number_format = '$#,##0'
    widths = [26, 11, 8, 28, 16, 17, 9, 12, 11, 10, 10, 11, 14, 12, 26, 30]
    for i, w in enumerate(widths, start=1):
        tr.column_dimensions[get_column_letter(i)].width = w
    tr.freeze_panes = "A2"
    tr.row_dimensions[1].height = 30
    last = len(tracker_rows) + 1
    rng = f"F2:F{last}"
    tr.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"Live"'], fill=PatternFill("solid", fgColor=SAGE), font=Font(color=WHITE, bold=True)))
    tr.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"Proposed"'], fill=PatternFill("solid", fgColor=BLUE), font=Font(color=WHITE, bold=True)))
    tr.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"Blocked-on-client"'], fill=PatternFill("solid", fgColor=AMBER), font=Font(color=WHITE, bold=True)))
    tr.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"Ended"'], fill=PatternFill("solid", fgColor=GRAY), font=Font(color=WHITE, bold=True)))

    db = wb.create_sheet("Dashboard", 0)
    db.sheet_view.showGridLines = False
    db["B2"] = f"{client} | Campaign Performance Dashboard"; db["B2"].font = title_font
    db["B3"] = "Rolling 90-day window. Performance cells auto-populate from weekly platform exports."; db["B3"].font = sub_font
    db["B5"] = "Highlights this cycle"; db["B5"].font = section_font
    for i, h in enumerate(highlights):
        c = db.cell(row=6 + i, column=2, value="• " + h); c.font = cell_font; c.alignment = left
        db.merge_cells(start_row=6 + i, start_column=2, end_row=6 + i, end_column=8)
    base = 6 + len(highlights) + 1
    db.cell(row=base, column=2, value="Overall").font = section_font
    kpis = [("Campaigns Live", '=COUNTIF(\'Campaign Tracker\'!F:F,"Live")', None),
            ("Proposed", '=COUNTIF(\'Campaign Tracker\'!F:F,"Proposed")', None),
            ("Blocked", '=COUNTIF(\'Campaign Tracker\'!F:F,"Blocked-on-client")', None),
            ("Total Spend", "=SUM('Campaign Tracker'!L:L)", '$#,##0'),
            ("Blended ROAS", '=IFERROR(SUM(\'Campaign Tracker\'!M:M)/SUM(\'Campaign Tracker\'!L:L),"--")', '0.0"x"')]
    for i, (label, formula, fmt) in enumerate(kpis):
        col = 2 + i * 2
        lc = db.cell(row=base + 1, column=col, value=label); lc.font = kpi_label; lc.alignment = center
        vc = db.cell(row=base + 2, column=col, value=formula); vc.font = kpi_value; vc.alignment = center
        if fmt:
            vc.number_format = fmt
        db.merge_cells(start_row=base + 1, start_column=col, end_row=base + 1, end_column=col + 1)
        db.merge_cells(start_row=base + 2, start_column=col, end_row=base + 2, end_column=col + 1)
    pr = base + 5
    db.cell(row=pr, column=2, value="By Platform").font = section_font
    for c, h in enumerate(["Platform", "Spend ($)", "Attributed Sales ($)", "ROAS", "Incremental Orders"], start=2):
        cell = db.cell(row=pr + 1, column=c, value=h); cell.font = hdr_font; cell.fill = hdr_fill; cell.alignment = center; cell.border = border
    for i, p in enumerate(["Uber Eats", "DoorDash", "Grubhub", "Meta"]):
        r = pr + 2 + i
        db.cell(row=r, column=2, value=p).font = cell_font
        db.cell(row=r, column=3, value=f'=SUMIF(\'Campaign Tracker\'!B:B,"{p}",\'Campaign Tracker\'!L:L)').number_format = '$#,##0'
        db.cell(row=r, column=4, value=f'=SUMIF(\'Campaign Tracker\'!B:B,"{p}",\'Campaign Tracker\'!M:M)').number_format = '$#,##0'
        db.cell(row=r, column=5, value=f'=IFERROR(SUMIF(\'Campaign Tracker\'!B:B,"{p}",\'Campaign Tracker\'!M:M)/SUMIF(\'Campaign Tracker\'!B:B,"{p}",\'Campaign Tracker\'!L:L),"--")').number_format = '0.0"x"'
        db.cell(row=r, column=6, value=f'=SUMIF(\'Campaign Tracker\'!B:B,"{p}",\'Campaign Tracker\'!N:N)')
        for c in range(2, 7):
            db.cell(row=r, column=c).border = border
            db.cell(row=r, column=c).alignment = center if c > 2 else left
    yr = pr + 7
    db.cell(row=yr, column=2, value="Ads vs Offers").font = section_font
    for c, h in enumerate(["Type", "Spend ($)", "Attributed Sales ($)", "ROAS", "Count"], start=2):
        cell = db.cell(row=yr + 1, column=c, value=h); cell.font = hdr_font; cell.fill = hdr_fill; cell.alignment = center; cell.border = border
    for i, t in enumerate(["Offer", "Ad"]):
        r = yr + 2 + i
        db.cell(row=r, column=2, value=t).font = cell_font
        db.cell(row=r, column=3, value=f'=SUMIF(\'Campaign Tracker\'!C:C,"{t}",\'Campaign Tracker\'!L:L)').number_format = '$#,##0'
        db.cell(row=r, column=4, value=f'=SUMIF(\'Campaign Tracker\'!C:C,"{t}",\'Campaign Tracker\'!M:M)').number_format = '$#,##0'
        db.cell(row=r, column=5, value=f'=IFERROR(SUMIF(\'Campaign Tracker\'!C:C,"{t}",\'Campaign Tracker\'!M:M)/SUMIF(\'Campaign Tracker\'!C:C,"{t}",\'Campaign Tracker\'!L:L),"--")').number_format = '0.0"x"'
        db.cell(row=r, column=6, value=f'=COUNTIF(\'Campaign Tracker\'!C:C,"{t}")')
        for c in range(2, 7):
            db.cell(row=r, column=c).border = border
            db.cell(row=r, column=c).alignment = center if c > 2 else left
    chart = BarChart(); chart.title = "Spend by Platform"; chart.type = "col"; chart.height = 7; chart.width = 12
    chart.add_data(Reference(db, min_col=3, min_row=pr + 1, max_row=pr + 5), titles_from_data=True)
    chart.set_categories(Reference(db, min_col=2, min_row=pr + 2, max_row=pr + 5))
    db.add_chart(chart, f"H{pr}")
    for i, w in enumerate([3, 18, 16, 18, 12, 16], start=1):
        db.column_dimensions[get_column_letter(i)].width = w

    lg = wb.create_sheet("Legend & Cadence")
    lg.sheet_view.showGridLines = False
    lg["B2"] = "Legend & How We Work This"; lg["B2"].font = title_font
    legend = [("Status: Live", "Running now"),
              ("Status: Proposed", "Spice recommends; not yet approved"),
              ("Status: Blocked-on-client", "Waiting on your team's sign-off (see Days in Queue)"),
              ("Status: Ended", "Completed or killed; outcome in Notes"),
              ("", ""),
              ("Type: Offer", "Merchant-funded promo (spend/save, BOGA, % off)"),
              ("Type: Ad", "Paid placement (sponsored listing, featured, paid social)"),
              ("", ""),
              ("Dashboard", "Auto-rolls up performance overall, by platform, ads vs offers from the Tracker"),
              ("Performance cells", "Populated weekly from UE/DD/GH platform exports. Empty = not yet pulled."),
              ("", ""),
              ("Cadence", "Updated every Friday. Blocked items need your sign-off. Tactical tweaks acknowledged 24h, shipped 48h unless they need your approval.")]
    for i, (k, v) in enumerate(legend):
        rk = lg.cell(row=4 + i, column=2, value=k); rk.font = Font(name="Arial", size=10, bold=True, color=CHARCOAL); rk.alignment = left
        rv = lg.cell(row=4 + i, column=3, value=v); rv.font = cell_font; rv.alignment = left
        lg.merge_cells(start_row=4 + i, start_column=3, end_row=4 + i, end_column=7)
    lg.column_dimensions["B"].width = 22
    lg.column_dimensions["C"].width = 62

    wb.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--tracker-csv", default=None, help="CSV of campaign rows (see header spec). Omit to use embedded goop sample.")
    ap.add_argument("--campaign-perf-csv", default=None, help="weekly-reporting OUTPUT/campaign_performance.csv. Folds Spend/Sales/ROAS/Orders into matching tracker rows (no double-pull).")
    ap.add_argument("--overwrite-perf", action="store_true", help="Overwrite existing performance cells. Default fills only empty cells.")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    if args.tracker_csv:
        rows = read_tracker_csv(args.tracker_csv)
        highlights = ["Performance highlights populated from this cycle's results."]
    else:
        rows = GOOP_SAMPLE
        highlights = [
            "San Jose: $50K, second-best sales week of the year. Conversion 25% to 33%.",
            "Pasadena: best delivery sales week of the year. Conversion 34%. Ratings velocity 38 (from 20-22).",
            "Meta ads killed 5/13: freed $1,150/wk with no measurable demand loss, reallocated to promos.",
        ]

    if args.campaign_perf_csv:
        perf = read_perf_csv(args.campaign_perf_csv)
        matched, unmatched = apply_campaign_perf(rows, perf, overwrite=args.overwrite_perf)
        print(f"campaign perf: {len(perf)} rows in, {matched} tracker rows updated.")
        if unmatched:
            print(f"⚠️  {len(unmatched)} perf rows matched NO tracker row — map or add as new campaigns:")
            for u in unmatched:
                print(f"    {u.get('Platform','?')} | {u.get('Campaign Type','?')} | {u.get('Location','?')} "
                      f"| spend {u.get('Spend','--')} | sales {u.get('Sales','--')}")

    out = build(args.client, rows, highlights, args.output)
    print(f"saved {out}: {os.path.getsize(out):,} bytes")


if __name__ == "__main__":
    main()
