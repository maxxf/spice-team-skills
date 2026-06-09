#!/usr/bin/env python3
"""Generate the Monday client Slack draft in Ro's 4-bullet format.

The GM reviews + sends manually (no auto-send). This produces a strong starting draft from
the refresh's outputs: the change diff (db_to_tracker), the performance summary, and any
highlights. The skill (Claude) may rewrite bullets for voice; this gives structure + the
numbers so the GM isn't starting from blank.

Ro's format (reference: his Jun 1 W22 update):
  Team sharing campaign updates
  • **$93.5K spend → ~$1M sales, 10.9x blended ROAS.** Ads (15.1x) doubling Offers (8.0x)
    — keep shifting budget toward Sponsored Listings.
  • **Rebuilt DD SLs landed strong week one:** South Bay 15.7x ... Hold budgets.
  • **MDW "$5 off $20+" wrapped 5/26** — DD 1,268 orders/7.4x ... backfill the promo gap.
  • **Review Berkeley launch plan** — opens June 8 (Restaurant #16).

Rules: 4 bullets max · bold lead-in (headline) · numbers + context · end with an active verb.

Usage:
  python slack_draft.py --summary-json summary.json
  (or import build_draft(summary) from the skill)
"""
from __future__ import annotations
import argparse
import json
import sys


def _fmt_money(v):
    try:
        n = float(str(v).replace("$", "").replace(",", ""))
        if n >= 1_000_000:
            return f"${n/1_000_000:.1f}M"
        if n >= 1_000:
            return f"${n/1_000:.1f}K"
        return f"${n:,.0f}"
    except (ValueError, TypeError):
        return str(v)


def _cap(s: str) -> str:
    s = s.strip()
    return s[0].upper() + s[1:] if s else s


def build_draft(summary: dict) -> str:
    """Build the Slack draft from a summary dict. All keys optional — bullets with no data
    are skipped, and the draft caps at 4 bullets.

    summary shape:
      {
        "headline": {"spend": 93459, "sales": 1015607, "blended_roas": 10.9,
                     "ads_roas": 15.1, "offers_roas": 8.0},
        "wins": [{"text": "Rebuilt DD SLs strong week one", "detail": "South Bay 15.7x...",
                  "action": "Hold budgets"}],
        "wraps": [{"text": "MDW $5 off $20 wrapped 5/26", "detail": "DD 1,268 orders/7.4x",
                   "action": "backfill the promo gap"}],
        "decisions": [{"text": "Review Berkeley launch plan", "detail": "opens June 8 (#16)"}],
        "changes_md": "<markdown from db_to_tracker diff>",  # optional context, not a bullet
      }
    """
    bullets = []

    h = summary.get("headline") or {}
    if h:
        parts = []
        if h.get("spend") is not None and h.get("sales") is not None:
            parts.append(f"{_fmt_money(h['spend'])} spend → {_fmt_money(h['sales'])} sales")
        if h.get("blended_roas") is not None:
            parts.append(f"{h['blended_roas']}x blended ROAS")
        lead = ", ".join(parts) if parts else "Week summary"
        ctx = ""
        if h.get("ads_roas") is not None and h.get("offers_roas") is not None:
            ctx = f" Ads ({h['ads_roas']}x) vs Offers ({h['offers_roas']}x) — keep shifting toward the efficient channel."
        bullets.append(f"• **{lead}.**{ctx}")

    for w in (summary.get("wins") or []):
        detail = f" {_cap(w['detail'])}." if w.get("detail") else ""
        action = f" {_cap(w['action'])}." if w.get("action") else ""
        bullets.append(f"• **{w['text']}:**{detail}{action}".rstrip())

    for wr in (summary.get("wraps") or []):
        detail = f" — {wr['detail']}." if wr.get("detail") else ""
        action = f" {_cap(wr['action'])}." if wr.get("action") else ""
        bullets.append(f"• **{wr['text']}**{detail}{action}".rstrip())

    for d in (summary.get("decisions") or []):
        detail = f" — {d['detail']}." if d.get("detail") else ""
        bullets.append(f"• **{d['text']}**{detail}".rstrip())

    bullets = bullets[:4]  # cap at 4
    draft = "Team sharing campaign updates\n\n" + "\n".join(bullets)

    if summary.get("changes_md"):
        draft += ("\n\n---\n_Plan changes this refresh (context — trim before sending):_\n"
                  + summary["changes_md"])
    return draft


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary-json", required=True, help="JSON file with the summary dict")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    with open(args.summary_json) as f:
        summary = json.load(f)
    draft = build_draft(summary)
    if args.out:
        with open(args.out, "w") as f:
            f.write(draft)
        print(f"wrote {args.out}")
    else:
        print(draft)


if __name__ == "__main__":
    main()
