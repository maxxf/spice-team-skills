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
                        offers_rows: list[dict]) -> dict:
    """Build the dashboard dict: KPIs, by-platform, by-segment, top/bottom 5."""
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

    # Top / bottom 5 by ROAS (only rows with spend)
    ranked = sorted([p for p in perf if p["spend"] > 0],
                    key=lambda p: -(p["sales"] / p["spend"]))
    def card(p):
        return {"campaign": p["campaign"], "platform": p["platform"], "location": p["location"],
                "spend": p["spend"], "sales": p["sales"],
                "roas": round(p["sales"] / p["spend"], 1) if p["spend"] else 0}
    top_five = [card(p) for p in ranked[:5]]
    bottom_five = [card(p) for p in ranked[-5:][::-1]] if len(ranked) > 5 else []

    return {
        "kpis": {"live": live, "proposed": proposed, "blocked": blocked,
                 "total_spend": total_spend, "total_sales": total_sales,
                 "blended_roas": blended, "new_cx": "—"},
        "by_platform": by_platform,
        "by_segment": by_segment,
        "top_five": top_five,
        "bottom_five": bottom_five,
    }


# ---- Ads Reporting ----

def ads_reporting_from_csv(ads_rows: list[dict]) -> dict:
    """Per-campaign funnel + aggregate + audience segmentation from the ads CSV."""
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
    aggregate = [
        {"metric": "Total Ad Spend", "current": f"${tot_spend:,.0f}"},
        {"metric": "Total Ad Sales (attributed)", "current": f"${tot_sales:,.0f}"},
        {"metric": "Ad ROAS", "current": f"{tot_sales/tot_spend:.1f}x" if tot_spend else "—"},
        {"metric": "Total Ad Orders", "current": f"{int(tot_orders):,}"},
        {"metric": "CPO", "current": f"${tot_spend/tot_orders:.2f}" if tot_orders else "—"},
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
    return {"aggregate": aggregate, "per_campaign": per, "audience": audience}


# ---- Offers Reporting ----

def offers_reporting_from_csv(offers_rows: list[dict]) -> dict:
    """Per-promo + aggregate + new/existing split from the offers CSV."""
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
    aggregate = [
        {"metric": "Total Offer Spend (merchant-funded)", "current": f"${tot_spend:,.0f}"},
        {"metric": "Total Offer-Attributed Sales", "current": f"${tot_sales:,.0f}"},
        {"metric": "Offer ROAS", "current": f"{tot_sales/tot_spend:.1f}x" if tot_spend else "—"},
        {"metric": "Total Offer Orders", "current": f"{int(tot_orders):,}"},
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
