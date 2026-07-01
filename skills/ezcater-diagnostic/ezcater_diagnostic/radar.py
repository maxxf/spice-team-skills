from __future__ import annotations

"""Catering Brand Health radar (v0.2). 6 per-store dims + up to 3 optional
portfolio-funnel dims (Traffic, Conversion, Re-order) when funnel data is supplied.
Each axis 1–10; unmeasurable axes → None (rendered '(pending)', excluded from mean)."""

from ezcater_diagnostic import scorers


def _band(value, bands):
    for upper, score in bands:
        if upper is None or value < upper:
            return score
    return bands[-1][1]


def compute_radar(by_store, per_store_tiers: dict, momentum_pct: float | None, portfolio: dict | None = None) -> dict:
    radar: dict[str, float | None] = {}
    active = by_store[by_store["orders"] >= scorers.ACTIVE_MIN_ORDERS]

    total_orders = float(by_store["orders"].sum())
    total_sales = float(by_store["gross_sales"].sum())
    aov = (total_sales / total_orders) if total_orders else 0.0
    radar["AOV"] = _band(aov, [(100, 3), (150, 5), (200, 6.5), (300, 8), (None, 9.5)])

    if len(active):
        ops_flags = [per_store_tiers[str(s)]["per_bucket_flags"]["ops"] for s in active["store"]]
        not_red = sum(1 for f in ops_flags if f != "broken") / len(ops_flags)
        radar["Operations"] = round(max(1.0, min(10.0, not_red * 10.0)), 2)
    else:
        radar["Operations"] = None

    if len(active):
        any_lever = ((active["ppp_bid_pct"] > 0) | (active["ezrewards_pct"] > 0) | (active["sponsored_spend"] > 0)).mean()
        both = ((active["ppp_bid_pct"] > 0) & (active["ezrewards_pct"] > 0)).mean()
        radar["Visibility"] = round(max(1.0, min(10.0, 2.0 + 5.0 * float(any_lever) + 3.0 * float(both))), 2)
    else:
        radar["Visibility"] = None

    if len(active):
        radar["Customer Sentiment"] = _band(float(active["rating"].mean()), [(4.2, 3), (4.5, 5), (4.8, 7), (None, 9.5)])
    else:
        radar["Customer Sentiment"] = None

    radar["Momentum"] = None if momentum_pct is None else _band(momentum_pct, [(-10, 3), (0, 5), (10, 6.5), (25, 8), (None, 9.5)])

    if len(active):
        radar["Packaging"] = _band(float(active["packaging_complete"].mean()), [(0.6, 3), (0.8, 5), (0.9, 7), (None, 9)])
    else:
        radar["Packaging"] = None

    # --- Optional portfolio-funnel dims ---
    p = portfolio or {}
    sv, mv = p.get("search_views"), p.get("menu_views")
    if sv and mv and sv > 0:
        ctr = mv / sv * 100.0
        radar["Traffic"] = _band(ctr, [(3, 3), (5, 4), (7, 6), (10, 7.5), (None, 9)])
    cr, bench = p.get("conversion_rate_pct"), p.get("conversion_benchmark_pct")
    if cr is not None and bench:
        ratio = cr / bench
        radar["Conversion"] = _band(ratio, [(0.7, 3), (0.9, 5), (1.1, 7), (None, 9)])
    new, exist, lapsed = p.get("new_customers"), p.get("existing_customers"), p.get("lapsed_customers")
    if None not in (new, exist, lapsed) and (new + exist + lapsed) > 0:
        repeat_share = exist / (new + exist + lapsed) * 100.0
        radar["Re-order"] = _band(repeat_share, [(15, 3), (25, 5), (40, 7), (None, 9)])

    measured = [v for v in radar.values() if v is not None]
    overall = round(sum(measured) / len(measured), 2) if measured else None
    return {"axes": radar, "overall": overall, "measured_count": len(measured)}
