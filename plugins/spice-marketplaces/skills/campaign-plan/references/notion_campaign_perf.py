#!/usr/bin/env python3
"""Publish a Campaign Performance section to Notion (Phase 2.2).

**Scope (locked 2026-06-04):** this module publishes ONLY the Campaign Performance section
of the weekly Notion report — not the full report. weekly-reporting still owns the financial
waterfall + ops quality tables. This keeps the client read tight + non-overwhelming.

What it produces (matches the Campaign Performance block in `374d3ff018e781419e6ceb98406e028f`):

  ### Ads Summary (Wxx)
  | Metric | Wxx | Wxx-1 | WoW |
  ...

  ### What's Working
  | Campaign | Platform | Spend | ROAS | Notes |
  ...

  ### What's Not Working
  | Campaign | Platform | Spend | ROAS | Issue |
  ...

  ### Reallocation Recommendations
  1. ...

The publisher takes joined data (ads + offers + Notion DB) and writes the section as a child
page under the client's Documents Hub, OR as an inline section appended to an existing
weekly report page.

Usage (CLI for testing; the skill calls the function directly in a normal refresh):
  python notion_campaign_perf.py \\
    --client-page-url <Notion client page URL> \\
    --ads-csv <ads detail CSV> \\
    --week 23 \\
    --week-start 2026-06-08

Phase 2.2 status: SCAFFOLD. Publishes a placeholder page with correct structure + headers;
auto-populate logic (ranking by ROAS, classifying What's Working / Not Working, generating
Reallocation Recs) is the build-out.
"""
from __future__ import annotations
import argparse
import csv
import sys


# ---- Data shapes (what the publisher expects) ----

ADS_SUMMARY_COLS = ["Metric", "Wxx", "Wxx-1", "WoW"]
WORKING_COLS = ["Campaign", "Platform", "Spend", "ROAS", "Notes"]
NOT_WORKING_COLS = ["Campaign", "Platform", "Spend", "ROAS", "Issue"]


def classify_campaigns(ads_rows: list[dict], target_roas: float = 8.0) -> tuple[list[dict], list[dict]]:
    """Sort ad campaigns into What's Working (above target) vs What's Not Working (below).
    Each input row: {Campaign, Platform, Spend, ROAS, ...}. Returns (working, not_working)."""
    working, not_working = [], []
    for r in ads_rows:
        try:
            roas = float(str(r.get("ROAS", "0")).replace("x", "").replace("$", "").strip() or 0)
        except ValueError:
            roas = 0
        if roas >= target_roas:
            working.append({**r, "_roas": roas})
        else:
            not_working.append({**r, "_roas": roas})
    working.sort(key=lambda x: -x["_roas"])
    not_working.sort(key=lambda x: x["_roas"])
    return working[:6], not_working[:6]  # Top + bottom 6


def generate_reallocation_recs(ads_rows: list[dict], decline_alerts: list[dict],
                                 top_performers: list[dict]) -> list[str]:
    """Heuristic-based reallocation recommendations from the playbook:
    - Pause campaigns flagged in decline alerts (ROAS < target sustained)
    - Test +20% on top performers (room to scale)
    - Shift offer depth before cutting ad budget on RED tier

    TODO: integrate with playbook + Notion DB to make these recs precise per client.
    Currently emits stub recs from the classification + alerts.
    """
    recs = []
    for alert in decline_alerts[:3]:
        loc = alert.get("location", "?")
        trigger = alert.get("trigger", "ROAS below target")
        action = alert.get("action", "pause and reallocate")
        recs.append(f"**{loc}** — {trigger}. {action}.")
    if top_performers:
        names = ", ".join(p.get("Campaign", "?") for p in top_performers[:4])
        recs.append(f"**+20% spend test on top 4 performers** ({names}). "
                    f"All at scalable ROAS with headroom.")
    return recs


def render_markdown_section(week: int, week_start: str, ads_summary: dict,
                              working: list[dict], not_working: list[dict],
                              reallocation_recs: list[str]) -> str:
    """Render the Campaign Performance section as Notion-flavored markdown."""
    lines = [f"## Campaign Performance — W{week} (week of {week_start})", ""]

    # Ads summary
    lines.append(f"### Ads Summary (W{week})")
    lines.append("| Metric | This Week | Last Week | WoW |")
    lines.append("|---|---|---|---|")
    for metric in ["Total Ad Spend", "Total Ad Sales (attributed)", "Ad ROAS",
                    "Total Ad Orders", "CPO", "CTR (UE only)"]:
        v = ads_summary.get(metric, {})
        lines.append(f"| {metric} | {v.get('current','—')} | {v.get('prior','—')} | {v.get('wow','—')} |")
    lines.append("")

    # What's Working
    lines.append("### What's Working")
    lines.append("| Campaign | Platform | Spend | ROAS | Notes |")
    lines.append("|---|---|---|---|---|")
    for r in working:
        lines.append(f"| {r.get('Campaign','?')} | {r.get('Platform','?')} | "
                     f"{r.get('Spend','?')} | {r.get('ROAS','?')} | {r.get('Notes','')} |")
    lines.append("")

    # What's Not Working
    lines.append("### What's Not Working")
    lines.append("| Campaign | Platform | Spend | ROAS | Issue |")
    lines.append("|---|---|---|---|---|")
    for r in not_working:
        lines.append(f"| {r.get('Campaign','?')} | {r.get('Platform','?')} | "
                     f"{r.get('Spend','?')} | {r.get('ROAS','?')} | {r.get('Issue','')} |")
    lines.append("")

    # Reallocation
    if reallocation_recs:
        lines.append("### Reallocation Recommendations")
        for i, rec in enumerate(reallocation_recs, 1):
            lines.append(f"{i}. {rec}")
        lines.append("")

    return "\n".join(lines)


def read_ads_csv(path: str) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ads-csv", required=True, help="Per-campaign ads detail CSV")
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--week-start", required=True, help="YYYY-MM-DD")
    ap.add_argument("--target-roas", type=float, default=8.0)
    ap.add_argument("--out", default=None, help="Output markdown path (default stdout)")
    args = ap.parse_args()

    ads = read_ads_csv(args.ads_csv)
    working, not_working = classify_campaigns(ads, target_roas=args.target_roas)

    # Skeleton ads_summary — would be computed from current vs prior week in real flow.
    # For Phase 2.2: pull from History tab via sheets_writer to compute WoW.
    ads_summary = {
        "Total Ad Spend": {"current": "—", "prior": "—", "wow": "—"},
        "Total Ad Sales (attributed)": {"current": "—", "prior": "—", "wow": "—"},
        "Ad ROAS": {"current": "—", "prior": "—", "wow": "—"},
        "Total Ad Orders": {"current": "—", "prior": "—", "wow": "—"},
        "CPO": {"current": "—", "prior": "—", "wow": "—"},
        "CTR (UE only)": {"current": "—", "prior": "—", "wow": "—"},
    }
    md = render_markdown_section(args.week, args.week_start, ads_summary,
                                   working, not_working, reallocation_recs=[])
    if args.out:
        with open(args.out, "w") as f:
            f.write(md)
        print(f"wrote {args.out}")
    else:
        print(md)


if __name__ == "__main__":
    main()
