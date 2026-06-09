#!/usr/bin/env python3
"""Aggregate raw inputs into the v2 Sheets-writer dicts.

Turns the tracker CSV (from db_to_tracker) + ads/offers CSVs (from the Drive inputs folder)
into the structured dicts that sheets_writer's write_dashboard / write_ads_reporting /
write_offers_reporting / write_active_campaigns consume.

Current-week computations are deterministic. WoW columns need prior-week data — passed in
via `prior` (read from the History tab) and left "—" when absent.

This is the connective tissue between the data and the v2 tabs. Pure functions, no network.
"""
from __future__ import annotations
import csv


def _num(v):
    if v is None:
        return 0.0
    s = str(v).replace("$", "").replace(",", "").replace("x", "").replace("%", "").strip()
    if s in ("", "--", "--*", "n/a", "—"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def read_csv(path: str) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _wow(cur, prev) -> str:
    """Week-over-week % change, signed. '—' when there's no prior value to compare."""
    cur, prev = _num(cur), _num(prev)
    if not prev:
        return "—"
    return f"{(cur - prev) / prev * 100:+.1f}%"


def history_weekly_rollup(history_rows: list[dict]) -> dict:
    """Group History rows into per-week totals, split by kind (Ad vs Offer).
    Returns {weekstart: {'ads': {spend,sales,orders}, 'offers': {...}}}. The History 'Status'
    column carries the kind ('Ad'/'Offer')."""
    weeks: dict = {}
    for r in history_rows:
        wk = r.get("Weekstart") or r.get("weekstart") or ""
        if not wk:
            continue
        kind = str(r.get("Status") or r.get("status") or "").strip().lower()
        bucket = "ads" if kind == "ad" else ("offers" if kind == "offer" else "ads")
        w = weeks.setdefault(wk, {"ads": {"spend": 0.0, "sales": 0.0, "orders": 0.0},
                                  "offers": {"spend": 0.0, "sales": 0.0, "orders": 0.0}})
        w[bucket]["spend"] += _num(r.get("Spend"))
        w[bucket]["sales"] += _num(r.get("Sales"))
        w[bucket]["orders"] += _num(r.get("Orders"))
    return weeks


# ---- Active Campaigns (from tracker rows) ----

def active_campaigns_from_tracker(tracker_rows: list[dict]) -> list[dict]:
    """Map tracker CSV rows (TRACKER_COLS) → Active Campaigns writer dicts."""
    out = []
    for r in tracker_rows:
        out.append({
            "Campaign Name": r.get("Campaign", ""),
            "Type": r.get("Type", ""),
            "Platform": r.get("Platform", ""),
            "Locations": r.get("Locations", ""),
            "Audience": r.get("Segment", "All"),
            "Status": r.get("Status", ""),
            "Start Date": r.get("Flight Start", ""),
            "End Date": r.get("Flight End", ""),
            "Target ROAS": r.get("Target ROAS", ""),
            "WTD Spend": r.get("Spend ($)", ""),
            "WTD Sales": r.get("Attributed Sales ($)", ""),
            "WTD Orders": r.get("Incremental Orders", ""),
            "WTD ROAS": r.get("Actual ROAS", ""),
            "Owner": "Ro",
            "Last Updated": "",
        })
    return out


# ---- Dashboard ----

def dashboard_from_data(tracker_rows: list[dict], ads_rows: list[dict],
                        offers_rows: list[dict], history_rollup: dict | None = None,
                        weekstart: str | None = None) -> dict:
    """Build the dashboard dict: KPIs, by-platform, by-segment, top/bottom 5, and (when
    prior weeks exist in History) a 4-week Portfolio Trend with WoW."""
    live = sum(1 for r in tracker_rows if r.get("Status") == "Live")
    proposed = sum(1 for r in tracker_rows if r.get("Status") == "Proposed")
    blocked = sum(1 for r in tracker_rows if r.get("Status") == "Blocked-on-client")

    # All performance rows = ads + offers combined (campaign-level)
    perf = []
    for a in ads_rows:
        perf.append({"campaign": a.get("Campaign", ""), "platform": a.get("Platform", ""),
                     "location": a.get("Locations") or a.get("Location", ""),
                     "spend": _num(a.get("Spend")), "sales": _num(a.get("Attributed Sales") or a.get("Sales")),
                     "orders": _num(a.get("Orders")), "kind": "Ad"})
    for o in offers_rows:
        perf.append({"campaign": o.get("Promotion") or o.get("Offer") or o.get("Campaign", ""),
                     "platform": o.get("Platform", ""),
                     "location": o.get("Locations") or o.get("Location", ""),
                     "spend": _num(o.get("Promo Spend") or o.get("Discount Spend") or o.get("Spend")),
                     "sales": _num(o.get("Attributed Sales") or o.get("Sales")),
                     "orders": _num(o.get("Redemptions") or o.get("Orders")), "kind": "Offer"})

    total_spend = sum(p["spend"] for p in perf)
    total_sales = sum(p["sales"] for p in perf)
    blended = round(total_sales / total_spend, 1) if total_spend else 0

    # By platform
    plat = {}
    for p in perf:
        d = plat.setdefault(p["platform"], {"spend": 0, "sales": 0, "orders": 0})
        d["spend"] += p["spend"]; d["sales"] += p["sales"]; d["orders"] += p["orders"]
    by_platform = [{"platform": k, "spend": v["spend"], "sales": v["sales"],
                    "roas": round(v["sales"] / v["spend"], 1) if v["spend"] else 0,
                    "orders": int(v["orders"])} for k, v in sorted(plat.items())]

    # By segment (from tracker Segment col, folding any perf we can map by campaign name)
    seg = {}
    for r in tracker_rows:
        s = r.get("Segment", "All") or "All"
        d = seg.setdefault(s, {"spend": 0, "sales": 0, "count": 0})
        d["spend"] += _num(r.get("Spend ($)")); d["sales"] += _num(r.get("Attributed Sales ($)"))
        d["count"] += 1
    by_segment = [{"segment": k, "spend": v["spend"], "sales": v["sales"],
                   "roas": round(v["sales"] / v["spend"], 1) if v["spend"] else 0,
                   "count": v["count"]} for k, v in sorted(seg.items())]
    # Suppress the whole section when no segment-level spend exists (planned-only campaigns) —
    # an all-$0/0.0x block reads as broken to the client. Comes back automatically once perf
    # is mapped per segment.
    if not any(s["spend"] for s in by_segment):
        by_segment = []

    # Top / bottom 5 by ROAS (only rows with spend)
    ranked = sorted([p for p in perf if p["spend"] > 0],
                    key=lambda p: -(p["sales"] / p["spend"]))
    def card(p):
        return {"campaign": p["campaign"], "platform": p["platform"], "location": p["location"],
                "spend": p["spend"], "sales": p["sales"],
                "roas": round(p["sales"] / p["spend"], 1) if p["spend"] else 0}
    top_five = [card(p) for p in ranked[:5]]
    bottom_five = [card(p) for p in ranked[-5:][::-1]] if len(ranked) > 5 else []

    # New customers — sum from the offers export (the only source that reports it).
    new_cx = sum(_num(o.get("New Customers")) for o in offers_rows)

    # Portfolio Trend — last 4 weeks of total spend / sales / blended ROAS, from History plus
    # the current week. Only built when at least one PRIOR week exists (a single week has no
    # trend). Current week is computed here (it isn't in History yet at render time).
    portfolio_trend = []
    if history_rollup and weekstart:
        prior_weeks = sorted(w for w in history_rollup if w < weekstart)
        if prior_weeks:
            series = []  # (spend, sales)
            for w in prior_weeks[-3:]:
                a = history_rollup[w]
                series.append((a["ads"]["spend"] + a["offers"]["spend"],
                               a["ads"]["sales"] + a["offers"]["sales"]))
            series.append((total_spend, total_sales))  # current week
            series = [None] * (4 - len(series)) + series[-4:]  # left-pad to 4
            spend_v = [s[0] if s else None for s in series]
            sales_v = [s[1] if s else None for s in series]
            roas_v = [(s[1] / s[0] if s and s[0] else None) for s in series]
            mon = lambda v: f"${v:,.0f}" if v is not None else "—"
            rx = lambda v: f"{v:.1f}x" if v is not None else "—"
            cols = ("w_3", "w_2", "w_1", "w_0")
            portfolio_trend = [
                {"metric": "Spend", **dict(zip(cols, map(mon, spend_v))), "wow": _wow(spend_v[3], spend_v[2])},
                {"metric": "Attributed Sales", **dict(zip(cols, map(mon, sales_v))), "wow": _wow(sales_v[3], sales_v[2])},
                {"metric": "Blended ROAS", **dict(zip(cols, map(rx, roas_v))), "wow": _wow(roas_v[3], roas_v[2])},
            ]

    return {
        "kpis": {"live": live, "proposed": proposed, "blocked": blocked,
                 "total_spend": total_spend, "total_sales": total_sales,
                 "blended_roas": blended, "new_cx": int(new_cx) if new_cx else "—"},
        "by_platform": by_platform,
        "by_segment": by_segment,
        "top_five": top_five,
        "bottom_five": bottom_five,
        "portfolio_trend": portfolio_trend,
    }


# ---- Ads Reporting ----

def ads_reporting_from_csv(ads_rows: list[dict], prior: dict | None = None) -> dict:
    """Per-campaign funnel + aggregate + audience segmentation from the ads CSV.
    `prior` = prior-week ads totals {spend,sales,orders} (from History) for the WoW column."""
    per = []
    for a in ads_rows:
        imp, clk = _num(a.get("Impressions")), _num(a.get("Clicks"))
        spend = _num(a.get("Spend"))
        sales = _num(a.get("Attributed Sales") or a.get("Sales"))
        orders = _num(a.get("Orders"))
        plat = a.get("Platform", "")
        is_ue = "uber" in plat.lower()
        per.append({
            "campaign": a.get("Campaign", ""), "platform": plat,
            "audience": a.get("Audience", "All"), "location": a.get("Locations") or a.get("Location", ""),
            "impressions": int(imp) if (is_ue and imp) else "n/a",
            "clicks": int(clk) if clk else "—",
            "ctr": f"{clk/imp*100:.1f}%" if (is_ue and imp) else "n/a",
            "spend": spend, "cpc": f"${spend/clk:.2f}" if (is_ue and clk) else "n/a",
            "orders": int(orders) if orders else "—", "sales": sales,
            "roas": round(sales / spend, 1) if spend else 0,
            "cpo": f"${spend/orders:.2f}" if orders else "—",
        })
    tot_spend = sum(_num(a.get("Spend")) for a in ads_rows)
    tot_sales = sum(_num(a.get("Attributed Sales") or a.get("Sales")) for a in ads_rows)
    tot_orders = sum(_num(a.get("Orders")) for a in ads_rows)
    p = prior or {}
    p_spend, p_sales, p_orders = _num(p.get("spend")), _num(p.get("sales")), _num(p.get("orders"))
    p_roas = (p_sales / p_spend) if p_spend else 0
    p_cpo = (p_spend / p_orders) if p_orders else 0
    cur_roas = tot_sales / tot_spend if tot_spend else 0
    cur_cpo = tot_spend / tot_orders if tot_orders else 0
    aggregate = [
        {"metric": "Total Ad Spend", "current": f"${tot_spend:,.0f}",
         "prior": f"${p_spend:,.0f}" if p_spend else "—", "wow": _wow(tot_spend, p_spend)},
        {"metric": "Total Ad Sales (attributed)", "current": f"${tot_sales:,.0f}",
         "prior": f"${p_sales:,.0f}" if p_sales else "—", "wow": _wow(tot_sales, p_sales)},
        {"metric": "Ad ROAS", "current": f"{cur_roas:.1f}x" if tot_spend else "—",
         "prior": f"{p_roas:.1f}x" if p_spend else "—", "wow": _wow(cur_roas, p_roas)},
        {"metric": "Total Ad Orders", "current": f"{int(tot_orders):,}",
         "prior": f"{int(p_orders):,}" if p_orders else "—", "wow": _wow(tot_orders, p_orders)},
        {"metric": "CPO", "current": f"${cur_cpo:.2f}" if tot_orders else "—",
         "prior": f"${p_cpo:.2f}" if p_orders else "—", "wow": _wow(cur_cpo, p_cpo)},
    ]
    # Audience segmentation
    aud = {}
    for a in ads_rows:
        k = a.get("Audience", "All") or "All"
        d = aud.setdefault(k, {"campaigns": 0, "spend": 0, "sales": 0})
        d["campaigns"] += 1; d["spend"] += _num(a.get("Spend"))
        d["sales"] += _num(a.get("Attributed Sales") or a.get("Sales"))
    audience = [{"segment": k, "campaigns": v["campaigns"], "spend": v["spend"], "sales": v["sales"],
                 "roas": round(v["sales"] / v["spend"], 1) if v["spend"] else 0,
                 "pct": f"{v['spend']/tot_spend*100:.1f}%" if tot_spend else "—"}
                for k, v in sorted(aud.items())]
    # A one-row "Audience Segmentation: All / 100%" adds nothing — suppress it.
    if len(audience) <= 1:
        audience = []
    # Funnel columns are only meaningful when the export carries impressions (UE Sponsored
    # Listings). Flag it so the writer can drop Impressions/Clicks/CTR/CPC otherwise.
    has_funnel = any(p["impressions"] != "n/a" for p in per)
    return {"aggregate": aggregate, "per_campaign": per, "audience": audience,
            "has_funnel": has_funnel}


# ---- Offers Reporting ----

def offers_reporting_from_csv(offers_rows: list[dict], prior: dict | None = None) -> dict:
    """Per-promo + aggregate + new/existing split from the offers CSV.
    `prior` = prior-week offers totals {spend,sales,orders} (from History) for the WoW column."""
    per = []
    for o in offers_rows:
        spend = _num(o.get("Promo Spend") or o.get("Discount Spend") or o.get("Spend"))
        sales = _num(o.get("Attributed Sales") or o.get("Sales"))
        per.append({
            "promo": o.get("Promotion") or o.get("Offer") or o.get("Campaign", ""),
            "platform": o.get("Platform", ""), "locations": o.get("Locations") or o.get("Location", ""),
            "audience": o.get("Audience", "All"), "threshold": o.get("Threshold", "—"),
            "discount": o.get("Discount", "—"), "orders": o.get("Redemptions") or o.get("Orders", "—"),
            "sales": sales, "spend": spend, "roas": round(sales / spend, 1) if spend else 0,
            "new_cx": o.get("New Customers", "—"), "pct_new": o.get("% New", "—"),
            "status": o.get("Status", "Live"),
        })
    tot_spend = sum(p["spend"] for p in per)
    tot_sales = sum(p["sales"] for p in per)
    tot_orders = sum(_num(p["orders"]) for p in per)
    p = prior or {}
    p_spend, p_sales, p_orders = _num(p.get("spend")), _num(p.get("sales")), _num(p.get("orders"))
    p_roas = (p_sales / p_spend) if p_spend else 0
    cur_roas = tot_sales / tot_spend if tot_spend else 0
    aggregate = [
        {"metric": "Total Offer Spend (merchant-funded)", "current": f"${tot_spend:,.0f}",
         "prior": f"${p_spend:,.0f}" if p_spend else "—", "wow": _wow(tot_spend, p_spend)},
        {"metric": "Total Offer-Attributed Sales", "current": f"${tot_sales:,.0f}",
         "prior": f"${p_sales:,.0f}" if p_sales else "—", "wow": _wow(tot_sales, p_sales)},
        {"metric": "Offer ROAS", "current": f"{cur_roas:.1f}x" if tot_spend else "—",
         "prior": f"{p_roas:.1f}x" if p_spend else "—", "wow": _wow(cur_roas, p_roas)},
        {"metric": "Total Offer Orders", "current": f"{int(tot_orders):,}",
         "prior": f"{int(p_orders):,}" if p_orders else "—", "wow": _wow(tot_orders, p_orders)},
    ]
    return {"aggregate": aggregate, "per_promo": per, "audience": []}


# ---- History rows (for the append-only tab) ----

def history_rows(weekstart: str, perf_rows: list[dict]) -> list[dict]:
    """Build History snapshot rows from combined ads+offers perf for this week."""
    rows = []
    for p in perf_rows:
        rows.append({"Weekstart": weekstart, "Campaign": p.get("campaign", ""),
                     "Platform": p.get("platform", ""), "Location": p.get("location", ""),
                     "Spend": p.get("spend", ""), "Sales": p.get("sales", ""),
                     "Orders": p.get("orders", ""),
                     "ROAS": round(p["sales"] / p["spend"], 1) if p.get("spend") else "",
                     "Status": p.get("kind", "")})
    return rows
