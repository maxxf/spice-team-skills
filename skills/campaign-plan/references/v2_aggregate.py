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


def _pct(num, den) -> str:
    """num as a % of den, e.g. marketing spend % of net sales. '—' when den is missing."""
    num, den = _num(num), _num(den)
    if not den:
        return "—"
    return f"{num / den * 100:.1f}%"


def _cnum(v):
    """Parse a canonical sales-sheet display string ($1,460,007 / 6% / 5.1 / 29,105) to float.
    Returns None for blanks, '#DIV/0!', '—', etc."""
    if v is None:
        return None
    s = str(v).replace("$", "").replace(",", "").replace("%", "").replace("x", "").strip()
    if s in ("", "—", "--", "n/a") or "DIV" in s.upper() or s.startswith("#"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _canon_locations(raw, aliases) -> list:
    """Resolve a campaign's freeform location label into canonical store name(s) so it joins
    to weekly-reporting's net-sales-by-location. `aliases` maps a raw label (whole string or
    a comma-piece) to a canonical name or list of names. Falls back to the literal piece."""
    aliases = aliases or {}
    raw = str(raw).strip()
    if not raw:
        return ["(unspecified)"]
    if raw in aliases:  # whole-string match wins (e.g. "SJ + Pasadena" -> [San Jose, Pasadena])
        v = aliases[raw]
        return list(v) if isinstance(v, list) else [v]
    out = []
    for piece in [x.strip() for x in raw.replace(";", ",").replace(" + ", ",").split(",") if x.strip()]:
        v = aliases.get(piece, piece)
        out.extend(v if isinstance(v, list) else [v])
    return out or ["(unspecified)"]


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


def active_campaigns_by_location(ads_rows: list[dict], offers_rows: list[dict],
                                 location_aliases: dict | None = None) -> list[dict]:
    """Group the running campaigns (ads + offers) by canonical location for a clean
    'what's live where' view. A campaign that spans multiple locations appears under each.
    Returns [{location, count, total_spend, campaigns:[{campaign,type,platform,status,
    spend,sales,roas,orders}]}], sorted by location spend desc, campaigns by spend desc."""
    items = []
    for a in ads_rows:
        sp, sa = _num(a.get("Spend")), _num(a.get("Attributed Sales") or a.get("Sales"))
        items.append({"campaign": a.get("Campaign", ""), "type": "Ad",
                      "platform": a.get("Platform", ""), "status": a.get("Status", "Live") or "Live",
                      "raw_loc": a.get("Locations") or a.get("Location", ""),
                      "spend": sp, "sales": sa, "orders": _num(a.get("Orders")),
                      "roas": round(sa / sp, 1) if sp else 0})
    for o in offers_rows:
        sp, sa = _num(o.get("Promo Spend") or o.get("Discount Spend") or o.get("Spend")), \
            _num(o.get("Attributed Sales") or o.get("Sales"))
        items.append({"campaign": o.get("Promotion") or o.get("Offer") or o.get("Campaign", ""),
                      "type": "Offer", "platform": o.get("Platform", ""),
                      "status": o.get("Status", "Live") or "Live",
                      "raw_loc": o.get("Locations") or o.get("Location", ""),
                      "spend": sp, "sales": sa, "orders": _num(o.get("Redemptions") or o.get("Orders")),
                      "roas": round(sa / sp, 1) if sp else 0})
    groups: dict = {}
    for it in items:
        for loc in _canon_locations(it["raw_loc"], location_aliases):
            groups.setdefault(loc, []).append(it)
    out = []
    for loc, camps in groups.items():
        out.append({"location": loc, "count": len(camps),
                    "total_spend": sum(c["spend"] for c in camps),
                    "campaigns": sorted(camps, key=lambda c: -c["spend"])})
    out.sort(key=lambda g: -g["total_spend"])
    return out


# ---- Dashboard ----

def dashboard_from_data(tracker_rows: list[dict], ads_rows: list[dict],
                        offers_rows: list[dict], history_rollup: dict | None = None,
                        weekstart: str | None = None, net_sales: dict | None = None,
                        location_aliases: dict | None = None, tier_map: dict | None = None,
                        prior_net_total: float | None = None, sales_metrics: dict | None = None,
                        prior_overview: dict | None = None) -> dict:
    """Build the dashboard dict: KPIs, by-platform, by-location, top/bottom 5, ad/promo split,
    and (when prior weeks exist in History) a 4-week Portfolio Trend with WoW.

    `net_sales` (from weekly-reporting) drives the marketing-spend-% and marketing-driven-
    sales-% columns. Shape: {"total": N, "platform": {name: N}, "location": {name: N}}.
    When absent, those % columns read '—'."""
    ns = net_sales or {}
    ns_total = _num(ns.get("total"))
    ns_plat = ns.get("platform") or {}
    ns_loc = ns.get("location") or {}
    live = sum(1 for r in tracker_rows if r.get("Status") == "Live")
    proposed = sum(1 for r in tracker_rows if r.get("Status") == "Proposed")
    blocked = sum(1 for r in tracker_rows if r.get("Status") == "Blocked-on-client")

    # All performance rows = ads + offers combined (campaign-level)
    perf = []
    for a in ads_rows:
        perf.append({"campaign": a.get("Campaign", ""), "platform": a.get("Platform", ""),
                     "location": a.get("Locations") or a.get("Location", ""),
                     "audience": a.get("Audience", "All") or "All",
                     "spend": _num(a.get("Spend")), "sales": _num(a.get("Attributed Sales") or a.get("Sales")),
                     "orders": _num(a.get("Orders")), "kind": "Ad"})
    for o in offers_rows:
        perf.append({"campaign": o.get("Promotion") or o.get("Offer") or o.get("Campaign", ""),
                     "platform": o.get("Platform", ""),
                     "location": o.get("Locations") or o.get("Location", ""),
                     "audience": o.get("Audience", "All") or "All",
                     "spend": _num(o.get("Promo Spend") or o.get("Discount Spend") or o.get("Spend")),
                     "sales": _num(o.get("Attributed Sales") or o.get("Sales")),
                     "orders": _num(o.get("Redemptions") or o.get("Orders")), "kind": "Offer"})

    total_spend = sum(p["spend"] for p in perf)
    total_sales = sum(p["sales"] for p in perf)
    total_orders = sum(p["orders"] for p in perf)
    blended = round(total_sales / total_spend, 1) if total_spend else 0
    cpo_total = total_spend / total_orders if total_orders else 0

    # Ad vs Promo split (kind = Ad / Offer) — clearer headline than one blended number.
    ad_spend = sum(p["spend"] for p in perf if p["kind"] == "Ad")
    ad_sales = sum(p["sales"] for p in perf if p["kind"] == "Ad")
    promo_spend = sum(p["spend"] for p in perf if p["kind"] == "Offer")
    promo_sales = sum(p["sales"] for p in perf if p["kind"] == "Offer")

    # By platform (with marketing-spend-% and marketing-driven-sales-% vs net sales)
    plat = {}
    for p in perf:
        d = plat.setdefault(p["platform"], {"spend": 0, "sales": 0, "orders": 0})
        d["spend"] += p["spend"]; d["sales"] += p["sales"]; d["orders"] += p["orders"]
    def _pctval(num, den):
        num, den = _num(num), _num(den)
        return (num / den * 100) if den else None

    by_platform = [{"platform": k, "spend": v["spend"], "sales": v["sales"],
                    "roas": round(v["sales"] / v["spend"], 1) if v["spend"] else 0,
                    "orders": int(v["orders"]),
                    "cpo": v["spend"] / v["orders"] if v["orders"] else 0,
                    "mkt_spend_pct": _pct(v["spend"], ns_plat.get(k)),
                    "mkt_spend_pct_val": _pctval(v["spend"], ns_plat.get(k)),
                    "mkt_driven_pct": _pct(v["sales"], ns_plat.get(k))}
                   for k, v in sorted(plat.items())]

    # By location (marketing spend/sales/ROAS per location + % vs net sales). Locations can be
    # comma-joined on a row ("San Jose, Pasadena"); split so each location gets credit.
    loc = {}
    for p in perf:
        names = _canon_locations(p["location"], location_aliases)
        for nm in names:
            d = loc.setdefault(nm, {"spend": 0, "sales": 0, "orders": 0})
            # split spend/sales evenly across the row's locations to avoid double-counting
            d["spend"] += p["spend"] / len(names)
            d["sales"] += p["sales"] / len(names)
            d["orders"] += p["orders"] / len(names)
    def _eff_flag(mkt_val, roas):
        """Recommend an action vs the 3% spend north star: scale efficient winners, pull back
        heavy overspend, watch the in-between."""
        if mkt_val is None:
            return ""
        if mkt_val > 10:
            return "⚠ Pull back"
        if mkt_val <= 3 and roas >= 6:
            return "▲ Scale up"
        if mkt_val > 4:
            return "Watch"
        return "Hold"

    by_location = []
    for k, v in sorted(loc.items(), key=lambda kv: -kv[1]["spend"]):
        roas = round(v["sales"] / v["spend"], 1) if v["spend"] else 0
        mkt_val = _pctval(v["spend"], ns_loc.get(k))
        by_location.append({"location": k, "spend": v["spend"], "sales": v["sales"],
                            "roas": roas, "orders": int(round(v["orders"])),
                            "cpo": v["spend"] / v["orders"] if v["orders"] else 0,
                            "mkt_spend_pct": _pct(v["spend"], ns_loc.get(k)),
                            "mkt_spend_pct_val": mkt_val,
                            "mkt_driven_pct": _pct(v["sales"], ns_loc.get(k)),
                            "tier": (tier_map or {}).get(k, ""),
                            "flag": _eff_flag(mkt_val, roas)})

    # By tier (segment locations into Red/Yellow/Green using the sales sheet's tier map).
    by_tier = []
    if tier_map:
        tg = {}
        for r in by_location:
            t = r.get("tier")
            if not t:
                continue
            d = tg.setdefault(t, {"spend": 0, "sales": 0, "orders": 0, "net": 0})
            d["spend"] += r["spend"]; d["sales"] += r["sales"]; d["orders"] += r["orders"]
            d["net"] += _num(ns_loc.get(r["location"]))
        for t in ("Red", "Yellow", "Green"):
            if t in tg:
                d = tg[t]
                by_tier.append({"tier": t, "spend": d["spend"], "sales": d["sales"],
                                "roas": round(d["sales"] / d["spend"], 1) if d["spend"] else 0,
                                "orders": int(d["orders"]),
                                "mkt_spend_pct": _pct(d["spend"], d["net"]),
                                "mkt_spend_pct_val": _pctval(d["spend"], d["net"]),
                                "mkt_driven_pct": _pct(d["sales"], d["net"])})

    # Customer segmentation — by targeted audience (All / New / Lapsed), from the campaign data.
    aud = {}
    for p in perf:
        kx = p.get("audience") or "All"
        d = aud.setdefault(kx, {"spend": 0, "sales": 0, "orders": 0})
        d["spend"] += p["spend"]; d["sales"] += p["sales"]; d["orders"] += p["orders"]
    by_audience = [{"segment": kx, "spend": v["spend"], "sales": v["sales"],
                    "roas": round(v["sales"] / v["spend"], 1) if v["spend"] else 0,
                    "orders": int(v["orders"]), "pct_spend": _pct(v["spend"], total_spend)}
                   for kx, v in sorted(aud.items(), key=lambda kv: -kv[1]["spend"])]
    if len(by_audience) <= 1:  # a single "All" bucket isn't a segmentation — suppress
        by_audience = []

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
    new_cust_cac = total_spend / new_cx if new_cx else None  # blended cost per new cust; None -> "—"

    # Prior-week totals (from History) for WoW on the headline KPIs.
    pt = {"spend": 0, "sales": 0, "orders": 0}
    if history_rollup and weekstart:
        pws = sorted(w for w in history_rollup if w < weekstart)
        if pws:
            a = history_rollup[pws[-1]]
            pt["spend"] = a["ads"]["spend"] + a["offers"]["spend"]
            pt["sales"] = a["ads"]["sales"] + a["offers"]["sales"]
            pt["orders"] = a["ads"]["orders"] + a["offers"]["orders"]
    prior_roas = pt["sales"] / pt["spend"] if pt["spend"] else 0
    prior_cpo = pt["spend"] / pt["orders"] if pt["orders"] else 0
    cur_mkt_pct = (total_spend / ns_total * 100) if ns_total else 0
    prior_mkt_pct = (pt["spend"] / prior_net_total * 100) if prior_net_total else 0

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

    # ---- Canonical override (weekly-reporting methodology) ----
    # When the sales sheet's pre-computed metrics are available, use them for the efficiency
    # sections: Total Sales denominator, deduped Marketing Driven Sales/Orders, canonical
    # Marketing ROAS/CPO. Per-campaign tabs (Ads/Offers/Top-Bottom/Audience) stay export-derived.
    denom_sales = ns_total           # % denominator (canonical = Total Sales)
    net_sales_display = ns_total     # the "Net Sales" tile
    organic_sales = None
    by_marketing_organic = []
    mktg_roas = blended              # Marketing ROAS (default = export blended)
    blended_roas_disp = blended      # Blended ROAS (goop-specific, client-defined)
    ov = (sales_metrics or {}).get("overview")
    if ov:
        _ts = _cnum(ov.get("total_sales")); _ns = _cnum(ov.get("net_sales"))
        _inv = _cnum(ov.get("mktg_investment")); _mds = _cnum(ov.get("mktg_driven_sales"))
        _org = _cnum(ov.get("organic_sales")); _mo = _cnum(ov.get("mktg_orders"))
        _roas = _cnum(ov.get("roas")); _cpo = _cnum(ov.get("cpo")); _bl = _cnum(ov.get("blended_roas"))
        if _ts:
            denom_sales = _ts
        if _ns is not None:
            net_sales_display = _ns
        if _inv is not None:
            total_spend = _inv
        if _mds is not None:
            total_sales = _mds
        if _mo:
            total_orders = int(_mo)
        if _roas is not None:
            mktg_roas = _roas
        if _bl is not None:
            blended_roas_disp = _bl
        if _cpo is not None:
            cpo_total = _cpo
        organic_sales = _org
        new_cust_cac = (total_spend / new_cx) if new_cx else None
        # Ads-vs-Promos investment split from canonical (ad spend vs discounts). Deduped
        # marketing-driven sales can't be split by channel, so this view is spend-only.
        _adsp = _cnum(ov.get("ad_spend")); _disc = _cnum(ov.get("discounts"))
        if _adsp is not None:
            ad_spend = _adsp
        if _disc is not None:
            promo_spend = _disc
        ad_sales = promo_sales = 0
        if _mds is not None and _org is not None and _ts:
            by_marketing_organic = [
                {"label": "Marketing-Driven", "sales": _mds, "pct": _pct(_mds, _ts)},
                {"label": "Organic", "sales": _org, "pct": _pct(_org, _ts)}]

        def _cb(namekey, name, c):
            ts = _cnum(c.get("total_sales")); inv = _cnum(c.get("mktg_investment"))
            mds = _cnum(c.get("mktg_driven_sales")); mo = _cnum(c.get("mktg_orders"))
            roas = _cnum(c.get("roas")); cpo = _cnum(c.get("cpo")); msp = _cnum(c.get("mkt_spend_pct"))
            return {namekey: name, "spend": inv or 0, "sales": mds or 0,
                    "roas": roas if roas is not None else 0, "orders": int(mo) if mo else 0,
                    "cpo": cpo if cpo is not None else 0,
                    "mkt_spend_pct": (f"{msp:.0f}%" if msp is not None else "—"),
                    "mkt_spend_pct_val": msp, "mkt_driven_pct": _pct(mds, ts),
                    "tier": (tier_map or {}).get(name, ""),
                    "flag": _eff_flag(msp, roas if roas is not None else 0)}

        pm = sales_metrics.get("platform") or {}
        by_platform = [_cb("platform", k, v) for k, v in sorted(pm.items())
                       if (_cnum(v.get("mktg_investment")) or 0) > 0]
        lm = sales_metrics.get("location") or {}
        by_location = sorted([_cb("location", k, v) for k, v in lm.items()
                              if (_cnum(v.get("mktg_investment")) or 0) > 0], key=lambda r: -r["spend"])
        by_tier = []
        if tier_map:
            tg = {}
            for k, v in lm.items():
                t = tier_map.get(k)
                if not t:
                    continue
                d = tg.setdefault(t, {"ts": 0, "inv": 0, "mds": 0, "mo": 0})
                d["ts"] += _cnum(v.get("total_sales")) or 0
                d["inv"] += _cnum(v.get("mktg_investment")) or 0
                d["mds"] += _cnum(v.get("mktg_driven_sales")) or 0
                d["mo"] += _cnum(v.get("mktg_orders")) or 0
            for t in ("Red", "Yellow", "Green"):
                if t in tg:
                    d = tg[t]
                    by_tier.append({"tier": t, "spend": d["inv"], "sales": d["mds"],
                                    "roas": round(d["mds"] / d["inv"], 1) if d["inv"] else 0,
                                    "orders": int(d["mo"]),
                                    "mkt_spend_pct": _pct(d["inv"], d["ts"]),
                                    "mkt_spend_pct_val": (d["inv"] / d["ts"] * 100) if d["ts"] else None,
                                    "mkt_driven_pct": _pct(d["mds"], d["ts"])})

    cur_mkt_pct = (total_spend / denom_sales * 100) if denom_sales else 0

    # Prior-week canonical values for correct (canonical-to-canonical) WoW on the headline.
    po = prior_overview or {}
    po_ts = _cnum(po.get("total_sales")); po_inv = _cnum(po.get("mktg_investment"))
    po_roas = _cnum(po.get("roas")); po_cpo = _cnum(po.get("cpo")); po_bl = _cnum(po.get("blended_roas"))
    po_mktpct = (po_inv / po_ts * 100) if (po_inv and po_ts) else None
    if ov:  # canonical mode — the History/reconstruction Portfolio Trend would conflict
        portfolio_trend = []

    return {
        "kpis": {"live": live, "proposed": proposed, "blocked": blocked,
                 "total_spend": total_spend, "total_sales": total_sales,
                 "total_orders": int(total_orders), "cpo": cpo_total,
                 "marketing_roas": mktg_roas, "blended_roas": blended_roas_disp,
                 "new_cx": int(new_cx) if new_cx else "—",
                 "new_cust_cac": new_cust_cac,
                 # Headline WoW — canonical-to-canonical (vs the prior week's sales-sheet metrics)
                 "total_sales_wow": _wow(denom_sales, po_ts) if po_ts else "—",
                 "mkt_spend_pct_wow": _wow(cur_mkt_pct, po_mktpct) if po_mktpct else "—",
                 "roas_wow": _wow(mktg_roas, po_roas) if po_roas else "—",
                 "blended_roas_wow": _wow(blended_roas_disp, po_bl) if po_bl else "—",
                 "cpo_wow": _wow(cpo_total, po_cpo) if po_cpo else "—",
                 "new_cx_wow": "—",
                 # Ad vs Promo split (campaign-export attributed)
                 "ad_spend": ad_spend, "ad_sales": ad_sales,
                 "ad_roas": round(ad_sales / ad_spend, 1) if ad_spend else 0,
                 "promo_spend": promo_spend, "promo_sales": promo_sales,
                 "promo_roas": round(promo_sales / promo_spend, 1) if promo_spend else 0,
                 # Marketing efficiency vs Total Sales (3% north star) — canonical when available
                 "net_sales": net_sales_display or "—",
                 "total_sales_display": denom_sales or "—",
                 "mkt_spend_pct": _pct(total_spend, denom_sales),
                 "mkt_driven_pct": _pct(total_sales, denom_sales),
                 "mkt_spend_pct_val": (total_spend / denom_sales * 100) if denom_sales else None,
                 "organic_sales": organic_sales,
                 "organic_pct": _pct(organic_sales, denom_sales) if organic_sales else "—"},
        "by_platform": by_platform,
        "by_location": by_location,
        "by_tier": by_tier,
        "by_audience": by_audience,
        "by_segment": by_segment,
        "by_marketing_organic": by_marketing_organic,
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
        per.append({
            "campaign": a.get("Campaign", ""), "platform": plat,
            "audience": a.get("Audience", "All"), "location": a.get("Locations") or a.get("Location", ""),
            "impressions": int(imp) if imp else "n/a",
            "clicks": int(clk) if clk else "—",
            "ctr": f"{clk/imp*100:.1f}%" if imp else "n/a",
            "spend": spend, "cpc": f"${spend/clk:.2f}" if clk else "n/a",
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
