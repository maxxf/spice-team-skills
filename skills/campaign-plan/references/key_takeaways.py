#!/usr/bin/env python3
"""Generate the internal weekly "key takeaways" digest — the team handoff posted to the
client's INTERNAL channel after each refresh (distinct from the client-facing slack_draft).

Client-agnostic by design: every value is derived from the dashboard data dict + the client
display name passed in. No brand names, no per-client logic — a new client gets this for free
(the binding brand-agnostic rule). Channel resolves to config `internal_channel`, falling back
to `slack_channel`. The GM reviews + sends — no auto-send.

Usage:
  python key_takeaways.py --dash-json dash.json --client "goop Kitchen" --week "W26 (Jun 22–Jun 28)"
  (or import build(dash, client, week) from the skill / refresh.py)
"""
from __future__ import annotations
import argparse
import json


def _num(v):
    try:
        return float(str(v).replace("$", "").replace(",", "").replace("%", ""))
    except (ValueError, TypeError):
        return 0.0


def _money(v):
    try:
        n = float(str(v).replace("$", "").replace(",", ""))
        if abs(n) >= 1_000_000:
            return f"${n / 1_000_000:.1f}M"
        if abs(n) >= 1_000:
            return f"${n / 1_000:.0f}K"
        return f"${n:,.0f}"
    except (ValueError, TypeError):
        return str(v)


def _roas(v):
    try:
        return f"{float(str(v).replace('x', '')):.1f}x"
    except (ValueError, TypeError):
        return str(v)


def _campaigns(ads_rows, offers_rows):
    """Flatten ad + offer export rows into a uniform campaign list. ROAS computed here (reliable),
    since the canonical KPI path doesn't carry per-channel attributed sales. Client-agnostic."""
    out = []
    for a in (ads_rows or []):
        sp = _num(a.get("Spend")); sa = _num(a.get("Attributed Sales") or a.get("Sales"))
        out.append({"name": (a.get("Campaign") or "").strip(), "plat": a.get("Platform", ""), "kind": "Ad",
                    "spend": sp, "sales": sa, "roas": (sa / sp) if sp else 0, "newcx": _num(a.get("New Customers"))})
    for o in (offers_rows or []):
        sp = _num(o.get("Promo Spend") or o.get("Spend")); sa = _num(o.get("Attributed Sales") or o.get("Sales"))
        out.append({"name": (o.get("Promotion") or o.get("Offer") or "").strip(), "plat": o.get("Platform", ""),
                    "kind": "Offer", "spend": sp, "sales": sa, "roas": (sa / sp) if sp else 0,
                    "newcx": _num(o.get("New Customers"))})
    return out


def _nm(s, n=46):
    """Tidy a campaign name for chat display: pipes → middots, trimmed, no dangling separators."""
    return str(s or "").replace("|", "·").strip()[:n].rstrip(" ·-/")


def _line(c, flag_inflated=True):
    tag = " _(low base — directional)_" if (flag_inflated and c["roas"] > 25) else ""
    return f"{_nm(c['name'])} — *{_roas(c['roas'])}* on {_money(c['spend'])} {c['plat']}{tag}"


def _suggestions(k, by_tier, tier_bands, guardrail, ad_roas, offers_roas, bottom, acq) -> list:
    """Strategy-aligned improvement suggestions, derived from the config (tier spend bands +
    goals, portfolio guardrail) applied to this week's data. Client-agnostic — every rule reads
    from tier_strategy, not brand assumptions. The GM edits; this gives a concrete starting set."""
    s = []
    msp = k.get("mkt_spend_pct_val")
    over = []  # tiers over their band, for the guardrail callout's "start here"
    for r in by_tier or []:
        key = (r.get("tier", "") or "").split()[-1]
        band = (tier_bands.get(key) or {}).get("spend_pct") if tier_bands else None
        pctv = r.get("mkt_spend_pct_val")
        if band and pctv is not None and pctv > band[1] + 0.5:
            over.append(r.get("tier"))
    if guardrail and msp and msp > guardrail:
        tail = f" — start with {', '.join(over)}" if over else ""
        s.append(f"Portfolio marketing at {msp:.1f}% vs the ≤{guardrail}% guardrail — trim toward {guardrail}%{tail}.")
    for r in by_tier or []:
        key = (r.get("tier", "") or "").split()[-1]
        meta = (tier_bands or {}).get(key) or {}
        band = meta.get("spend_pct"); pctv = r.get("mkt_spend_pct_val")
        if band and pctv is not None and pctv > band[1] + 0.5:
            act = ("pull spend to protect payout" if meta.get("goal") == "payout"
                   else f"keep walking spend down toward {band[1]}%")
            s.append(f"{r.get('tier')} running {pctv:.1f}% (band {band[0]}–{band[1]}%) — {act}.")
    if ad_roas and offers_roas:
        if ad_roas > offers_roas * 1.15:
            s.append(f"Ads ({_roas(ad_roas)}) outpacing offers ({_roas(offers_roas)}) — shift marginal budget "
                     f"to Sponsored Listings.")
        elif offers_roas > ad_roas * 1.15:
            s.append(f"Offers ({_roas(offers_roas)}) outpacing ads ({_roas(ad_roas)}) — protect promo depth, "
                     f"trim the weakest SLs.")
    if bottom:
        w = bottom[0]
        s.append(f"Review {_nm(w['name'])} ({_roas(w['roas'])} on {_money(w['spend'])}) — lowest real-spend ROAS; "
                 f"cut or reallocate to a higher-ROAS lane.")
    if acq and acq.get("newcx", 0) > 0:
        s.append(f"Scale/replicate {_nm(acq['name'])} — {int(acq['newcx']):,} new customers at {_roas(acq['roas'])}; "
                 f"strongest acquisition lever this week.")
    return s[:5]


def build(dash: dict, client: str, week: str, ads_rows=None, offers_rows=None, tier_strategy=None) -> str:
    """Internal campaign-takeaways digest for the team handoff, in three sections:
      1) Reporting takeaways (key metrics)   2) Campaign-level insights   3) Suggested improvements.
    All client-agnostic — metrics/insights from the campaign rows + dashboard, suggestions from the
    client's tier_strategy config (bands, goals, guardrail). Framed as a review-before-send draft."""
    k = dash.get("kpis") or {}
    tier_bands = (tier_strategy or {}).get("tiers") or {}
    guardrail = ((tier_strategy or {}).get("portfolio_guardrail") or {}).get("blended_mkt_spend_pct_max")
    camps = _campaigns(ads_rows, offers_rows)

    ad = [c for c in camps if c["kind"] == "Ad" and c["spend"] > 0]
    off = [c for c in camps if c["kind"] == "Offer" and c["spend"] > 0]
    a_sp, a_sa = sum(c["spend"] for c in ad), sum(c["sales"] for c in ad)
    o_sp, o_sa = sum(c["spend"] for c in off), sum(c["sales"] for c in off)
    ar = a_sa / a_sp if a_sp else 0
    orr = o_sa / o_sp if o_sp else 0
    pos = [c for c in camps if c["spend"] > 0]
    top = bot = []
    if pos:
        floor = max(300.0, 0.05 * max(c["spend"] for c in pos))
        real = [c for c in pos if c["spend"] >= floor]
        top = sorted(real, key=lambda c: -c["roas"])[:3]
        bot = sorted(real, key=lambda c: c["roas"])[:3]
    acq = max(camps, key=lambda c: c["newcx"], default=None)

    L = [f"📊 *{client} — {week}* — campaign data loaded, Sheet refreshed. "
         f"*👀 GM: review, add launches + the client note, then send.*"]

    # ── 1) Reporting takeaways ──────────────────────────────────────────────
    L.append("\n*1) Reporting takeaways*")
    ts = k.get("total_sales_display")
    if ts not in (None, "—", 0):
        wow = k.get("total_sales_wow")
        wowtxt = f" ({wow} WoW)" if wow not in (None, "—") else ""
        L.append(f"• {_money(ts)} total sales{wowtxt} · marketing {k.get('mkt_spend_pct', '—')} of sales · "
                 f"{_roas(k.get('marketing_roas'))} marketing / {_roas(k.get('blended_roas'))} blended ROAS.")
    if ad or off:
        read = " — ads more efficient" if ar > orr else " — offers more efficient" if orr > ar else ""
        L.append(f"• Channel mix: Ads {_money(a_sp)} ({_roas(ar)}) vs Offers {_money(o_sp)} ({_roas(orr)}){read}.")
    bt = dash.get("by_tier") or []
    if bt:
        segs = []
        for r in bt:
            lab = r.get("tier", ""); pctv = r.get("mkt_spend_pct_val"); flag = ""
            band = (tier_bands.get(lab.split()[-1]) or {}).get("spend_pct") if tier_bands else None
            if band and pctv is not None and pctv > band[1] + 0.5:
                flag = f" ⚠️ over {band[0]}–{band[1]}%"
            segs.append(f"{lab} {r.get('mkt_spend_pct')} ({_roas(r.get('roas'))}){flag}")
        L.append("• Tier discipline: " + " · ".join(segs))

    # ── 2) Campaign-level insights ──────────────────────────────────────────
    L.append("\n*2) Campaign insights*")
    if top:
        L.append("• Working: " + "; ".join(_line(c) for c in top))
    if bot:
        L.append("• Watch: " + "; ".join(_line(c, flag_inflated=False) for c in bot)
                 + "  _(some are acquisition plays — read with new-cust)_")
    if acq and acq.get("newcx", 0) > 0:
        L.append(f"• Top acquisition: {_nm(acq['name'])} — *{int(acq['newcx']):,} new customers* "
                 f"({_money(acq['spend'])}, {_roas(acq['roas'])}).")

    # ── 3) Suggested improvements (vs strategy/goals) ───────────────────────
    sug = _suggestions(k, bt, tier_bands, guardrail, ar, orr, bot, acq)
    if sug:
        L.append("\n*3) Suggested improvements (vs strategy/goals)*")
        L += [f"• {x}" for x in sug]

    L.append("\n_GM: add launches / NRO pipeline + the client-facing note before sending. "
             "New/low-spend store ROAS is attribution-inflated — read directionally._")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dash-json", required=True)
    ap.add_argument("--client", required=True)
    ap.add_argument("--week", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    with open(args.dash_json) as f:
        dash = json.load(f)
    out = build(dash, args.client, args.week)
    if args.out:
        open(args.out, "w").write(out)
        print(f"wrote {args.out}")
    else:
        print(out)


if __name__ == "__main__":
    main()
