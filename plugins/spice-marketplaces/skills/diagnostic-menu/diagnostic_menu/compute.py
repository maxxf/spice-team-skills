"""Menu & storefront computation. Emits sub-skill contract payload.

Owns Conversion + Traffic radar dims and the per-store "menu" tier sub-bucket
(framework lines 79–82 / 89–92). Implements 3 patterns: low_cvr_high_traffic,
low_photo_coverage, sku_sprawl.
"""
from __future__ import annotations

import pandas as pd

# Spice fast-casual default benchmark for menu CVR (framework line 29 / 79).
# Cuisine-aware lookup is a Wk 3+ enhancement.
CVR_BENCHMARK_PCT = 18.0
PHOTO_FOUNDATION_THRESHOLD = 50.0
PHOTO_HEALTHY_THRESHOLD = 80.0
CTR_HIGH_TRAFFIC_THRESHOLD = 9.0
SKU_SPRAWL_CATEGORY_COUNT = 8

# Crude per-store revenue assumption used only for back-of-envelope impact
# estimates on `low_cvr_high_traffic`. Real revenue arrives Wk 3 via topline join.
_DEFAULT_STORE_WEEKLY_REVENUE_USD = 8000.0


def _aggregate_by_store(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse multi-row-per-store input. Numerics → mean, booleans → last, ints → max-of-mean-rounded."""
    grouped = df.groupby("store", as_index=False).agg(
        menu_cvr_pct=("menu_cvr_pct", "mean"),
        photo_coverage_pct=("photo_coverage_pct", "mean"),
        hero_set=("hero_set", "last"),
        categories_count=("categories_count", "max"),
        categories_populated=("categories_populated", "min"),
        storefront_to_menu_ctr_pct=("storefront_to_menu_ctr_pct", "mean"),
    )
    return grouped


def _conversion_band_score(cvr_pct: float) -> float:
    if cvr_pct < 15:
        return 3.0
    if cvr_pct < 18:
        return 4.5
    if cvr_pct < 20:
        return 5.0
    if cvr_pct <= 25:
        return 7.0
    return 8.0


def _traffic_band_score(ctr_pct: float) -> float:
    if ctr_pct < 5:
        return 3.0
    if ctr_pct < 7:
        return 4.0
    if ctr_pct < 9:
        return 6.0
    if ctr_pct <= 12:
        return 7.5
    return 9.0


def _classify_store_tier(row) -> tuple[str, float, list[str]]:
    """Return (flag, score, reasons) for one store. Per framework lines 79–82."""
    cvr = float(row["menu_cvr_pct"])
    photos = float(row["photo_coverage_pct"])
    hero = bool(row["hero_set"])
    cats_total = int(row["categories_count"])
    cats_populated = int(row["categories_populated"])
    empty = cats_total - cats_populated

    cvr_red = cvr < CVR_BENCHMARK_PCT * 0.8  # < 14.4
    cvr_yellow = cvr < CVR_BENCHMARK_PCT  # < 18 but >= 14.4
    photo_red = photos < PHOTO_FOUNDATION_THRESHOLD
    photo_yellow = photos < PHOTO_HEALTHY_THRESHOLD
    cats_red = empty >= 2
    cats_yellow = empty == 1
    hero_red = not hero

    reasons: list[str] = []
    if cvr_red or photo_red or cats_red or hero_red:
        if cvr_red:
            reasons.append(f"CVR {cvr:.1f}% < 14.4% (broken)")
        if photo_red:
            reasons.append(f"photo coverage {photos:.0f}% < 50% (broken)")
        if cats_red:
            reasons.append(f"{empty} categories empty (broken)")
        if hero_red:
            reasons.append("hero image not set (broken)")
        flag = "red"
    elif cvr_yellow or photo_yellow or cats_yellow:
        if cvr_yellow:
            reasons.append(f"CVR {cvr:.1f}% within 20% below 18% benchmark (watch)")
        if photo_yellow:
            reasons.append(f"photo coverage {photos:.0f}% in 50–80% band (watch)")
        if cats_yellow:
            reasons.append("1 category empty (watch)")
        flag = "yellow"
    else:
        reasons.append(f"CVR {cvr:.1f}%, photos {photos:.0f}%, hero set, all categories populated")
        flag = "green"

    # Score: 1–10 blend weighted on CVR (relative to 25% ceiling) + photos (0–100)
    cvr_component = max(0.0, min(1.0, cvr / 25.0))
    photo_component = max(0.0, min(1.0, photos / 100.0))
    score = round(1.0 + 9.0 * (0.6 * cvr_component + 0.4 * photo_component), 2)
    return flag, score, reasons


def run(*, client: str, window_start: str, window_end: str, df: pd.DataFrame) -> dict:
    by_store = _aggregate_by_store(df)

    # Portfolio-level metrics
    portfolio_cvr = float(by_store["menu_cvr_pct"].mean()) if len(by_store) else 0.0
    portfolio_ctr = float(by_store["storefront_to_menu_ctr_pct"].mean()) if len(by_store) else 0.0
    portfolio_photos_mean = float(by_store["photo_coverage_pct"].mean()) if len(by_store) else 0.0
    # Min photo coverage drives the foundation gate — orchestrator fires on any store < 50%
    portfolio_photos_min = float(by_store["photo_coverage_pct"].min()) if len(by_store) else 0.0

    # Tier contributions
    tier_contributions: dict[str, dict] = {}
    red_stores: list[str] = []
    for _, row in by_store.iterrows():
        flag, score, reasons = _classify_store_tier(row)
        store = str(row["store"])
        tier_contributions[store] = {"score": score, "flag": flag, "reasons": reasons}
        if flag == "red":
            red_stores.append(store)

    # Findings
    findings: list[dict] = []

    # 1. low_cvr_high_traffic — per store
    lcht_stores = []
    lcht_impact_total = 0.0
    for _, row in by_store.iterrows():
        cvr = float(row["menu_cvr_pct"])
        ctr = float(row["storefront_to_menu_ctr_pct"])
        if cvr < CVR_BENCHMARK_PCT and ctr > CTR_HIGH_TRAFFIC_THRESHOLD:
            store = str(row["store"])
            lcht_stores.append(store)
            # Back-of-envelope: lift to benchmark on 13 weeks of revenue
            gap_pct = max(0.0, (CVR_BENCHMARK_PCT - cvr) / CVR_BENCHMARK_PCT)
            lcht_impact_total += gap_pct * _DEFAULT_STORE_WEEKLY_REVENUE_USD * 13
    if lcht_stores:
        findings.append({
            "pattern_id": "low_cvr_high_traffic",
            "severity": "high",
            "scope": ",".join(lcht_stores),
            "evidence": {
                "stores": lcht_stores,
                "cvr_benchmark_pct": CVR_BENCHMARK_PCT,
                "ctr_threshold_pct": CTR_HIGH_TRAFFIC_THRESHOLD,
            },
            "estimated_impact_usd": round(lcht_impact_total, 2),
            "deliverable_trigger": {
                "skill": "optimized-menu-sheet",
                "params": {"stores": lcht_stores, "focus": "category_consolidation"},
            },
        })

    # 2. low_photo_coverage — per store, foundation
    photo_bad_stores = []
    for _, row in by_store.iterrows():
        if float(row["photo_coverage_pct"]) < PHOTO_FOUNDATION_THRESHOLD:
            photo_bad_stores.append(str(row["store"]))
    if photo_bad_stores:
        findings.append({
            "pattern_id": "low_photo_coverage",
            "severity": "foundation",
            "scope": ",".join(photo_bad_stores),
            "evidence": {
                "stores": photo_bad_stores,
                "threshold_pct": PHOTO_FOUNDATION_THRESHOLD,
                "note": "Stop Everything threshold per framework foundation gate.",
            },
            "estimated_impact_usd": None,
            "deliverable_trigger": {"skill": "", "params": {}},
        })

    # 3. sku_sprawl — per store
    sprawl_stores = []
    for _, row in by_store.iterrows():
        cats_total = int(row["categories_count"])
        cats_populated = int(row["categories_populated"])
        if cats_total > SKU_SPRAWL_CATEGORY_COUNT and cats_populated < cats_total:
            sprawl_stores.append(str(row["store"]))
    if sprawl_stores:
        findings.append({
            "pattern_id": "sku_sprawl",
            "severity": "medium",
            "scope": ",".join(sprawl_stores),
            "evidence": {
                "stores": sprawl_stores,
                "category_count_threshold": SKU_SPRAWL_CATEGORY_COUNT,
            },
            "estimated_impact_usd": None,
            "deliverable_trigger": {
                "skill": "optimized-menu-sheet",
                "params": {"stores": sprawl_stores, "focus": "sku_rationalization"},
            },
        })

    # Radar
    radar = {
        "Conversion": _conversion_band_score(portfolio_cvr),
        "Traffic": _traffic_band_score(portfolio_ctr),
    }

    # Drafted layer
    n_red = sum(1 for v in tier_contributions.values() if v["flag"] == "red")
    toggle_prose = (
        f"Menu CVR averages {portfolio_cvr:.1f}% across the portfolio "
        f"(benchmark {CVR_BENCHMARK_PCT:.0f}%); photo coverage averages "
        f"{portfolio_photos_mean:.0f}% (min {portfolio_photos_min:.0f}%). "
        f"{n_red} store(s) flagged red on the menu sub-bucket."
    )

    win_risk_opp_candidates: list[dict] = []
    # Risks: one per red-tier store
    for store in red_stores:
        win_risk_opp_candidates.append({
            "type": "risk",
            "headline": f"{store}: menu sub-bucket broken — " + "; ".join(tier_contributions[store]["reasons"][:2]),
            "value_usd": None,
            "pattern_id": "menu_tier_red",
            "severity": "high",
        })
    # Opportunity: room to push CVR if portfolio mean is below a great band (<22%)
    if portfolio_cvr < 22.0 and portfolio_cvr > 0:
        gap = max(0.0, 22.0 - portfolio_cvr)
        opp_value = round(
            (gap / 22.0) * _DEFAULT_STORE_WEEKLY_REVENUE_USD * len(by_store) * 13,
            2,
        )
        win_risk_opp_candidates.append({
            "type": "opportunity",
            "headline": f"Lift portfolio menu CVR from {portfolio_cvr:.1f}% toward 22% via category consolidation and hero/photo refresh",
            "value_usd": opp_value,
            "pattern_id": "cvr_lift_opportunity",
            "severity": "medium",
        })
    # Win: portfolio CVR above benchmark
    if portfolio_cvr >= CVR_BENCHMARK_PCT:
        win_risk_opp_candidates.append({
            "type": "win",
            "headline": f"Portfolio menu CVR {portfolio_cvr:.1f}% is at or above the {CVR_BENCHMARK_PCT:.0f}% benchmark",
            "value_usd": None,
            "pattern_id": "cvr_above_benchmark",
            "severity": "low",
        })

    return {
        "sub_skill": "diagnostic-menu",
        "version": "1.0",
        "client": client,
        "window": {"start": window_start, "end": window_end},
        "computed": {
            "metrics": {
                "menu_cvr_pct": portfolio_cvr,
                "photo_coverage_pct": portfolio_photos_min,  # min — drives foundation gate
                "photo_coverage_pct_mean": portfolio_photos_mean,
                "storefront_to_menu_ctr_pct": portfolio_ctr,
                "store_count": int(len(by_store)),
                "red_menu_store_count": n_red,
            },
            "radar_contributions": radar,
            "tier_contributions": tier_contributions,
            "findings": findings,
            "charts": [],
        },
        "drafted": {
            "toggle_title": "Menu & Storefront",
            "toggle_prose": toggle_prose,
            "win_risk_opp_candidates": win_risk_opp_candidates,
        },
        "data_quality": {"completeness": 1.0, "gaps": []},
    }
