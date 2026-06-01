"""Campaigns & promos computation. Emits sub-skill contract payload.

Owns the per-store "campaigns" tier sub-bucket (framework lines 89–92) and the
"Campaigns / ROAS" radar dim. Implements 3 patterns: low_roas_high_spend,
over_discounting, spend_on_broken_store.

The "Campaigns / ROAS" radar dim uses the framework's blended-ROAS bands
(lines 62–69). Marketing Efficiency is composed by the orchestrator from
`total_marketing_investment` — that metrics key MUST be present.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# chart_helpers lives in the client-diagnostics skill (orchestrator package).
# Import lazily so tests not exercising charts don't pay the matplotlib import cost.
_CHART_HELPERS_PARENT = Path("/Users/maxx/Desktop/Cowork/Skills/client-diagnostics")

# Pattern thresholds
LOW_ROAS_HIGH_SPEND_SPEND_THRESHOLD = 500.0
LOW_ROAS_HIGH_SPEND_ROAS_THRESHOLD = 2.5
OVER_DISCOUNTING_PROMO_COUNT_THRESHOLD = 3

# Tier thresholds (framework lines 89–92)
ROAS_HEALTHY_THRESHOLD = 3.5
ROAS_BROKEN_THRESHOLD = 2.5
INCREMENTAL_ORDERS_HEALTHY_THRESHOLD = 10
PROMO_COUNT_HEALTHY_THRESHOLD = 2  # < 2 means 0 or 1 active promos


def _aggregate_by_store(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse multi-row-per-store input.

    Sums for spend / attributed_sales (additive across platforms+weeks);
    means for roas / incremental_orders_per_week (rate metrics);
    max for promo_count_active (worst-case promo stack).
    """
    grouped = df.groupby("store", as_index=False).agg(
        spend=("spend", "sum"),
        attributed_sales=("attributed_sales", "sum"),
        roas=("roas", "mean"),
        incremental_orders_per_week=("incremental_orders_per_week", "mean"),
        promo_count_active=("promo_count_active", "max"),
    )
    return grouped


def _radar_score_campaigns_roas(blended_roas: float) -> float:
    """Per framework Campaign Verdict Thresholds + radar bands (lines 62–69)."""
    if blended_roas < 2:
        return 3.0
    if blended_roas < 3:
        return 5.0
    if blended_roas < 4:
        return 6.5
    if blended_roas < 5:
        return 8.0
    return 9.0


def _classify_store_tier(row, flagged_stores: list[str]) -> tuple[str, float, list[str]]:
    """Return (flag, score, reasons) for one store. Per framework lines 89–92."""
    store = str(row["store"])
    roas = float(row["roas"])
    spend = float(row["spend"])
    inc_orders = float(row["incremental_orders_per_week"])
    promo_count = int(row["promo_count_active"])

    is_flagged = store in flagged_stores

    roas_red = roas < ROAS_BROKEN_THRESHOLD
    roas_yellow = ROAS_BROKEN_THRESHOLD <= roas < ROAS_HEALTHY_THRESHOLD
    promo_yellow = promo_count >= PROMO_COUNT_HEALTHY_THRESHOLD
    inefficient_yellow = spend > 0 and inc_orders < INCREMENTAL_ORDERS_HEALTHY_THRESHOLD

    reasons: list[str] = []
    if roas_red or is_flagged:
        if roas_red:
            reasons.append(f"blended ROAS {roas:.2f}x < 2.5x (broken)")
        if is_flagged:
            reasons.append("spend running while ops/menu broken (broken)")
        flag = "red"
    elif roas_yellow or promo_yellow or inefficient_yellow:
        if roas_yellow:
            reasons.append(f"blended ROAS {roas:.2f}x in 2.5–3.5x band (watch)")
        if promo_yellow:
            reasons.append(f"{promo_count} active promos stacked (watch)")
        if inefficient_yellow:
            reasons.append(
                f"spend ${spend:.0f} running but only {inc_orders:.1f} incremental orders/week (watch)"
            )
        flag = "yellow"
    else:
        reasons.append(
            f"ROAS {roas:.2f}x, {inc_orders:.1f} incremental orders/wk, {promo_count} active promo(s)"
        )
        flag = "green"

    # Score: 1–10 blend of ROAS (0..6 → 0..1, capped) and incremental orders (0..30 → 0..1, capped)
    roas_component = max(0.0, min(1.0, roas / 6.0))
    orders_component = max(0.0, min(1.0, inc_orders / 30.0))
    blend = 0.65 * roas_component + 0.35 * orders_component
    score = round(1.0 + 9.0 * blend, 2)
    return flag, score, reasons


def run(
    *,
    client: str,
    window_start: str,
    window_end: str,
    df: pd.DataFrame,
    flagged_stores: list[str] | None = None,
    charts_dir: Path | None = None,
) -> dict:
    flagged_stores = flagged_stores or []
    by_store = _aggregate_by_store(df)

    # Portfolio-level metrics
    if len(by_store):
        total_spend = float(by_store["spend"].sum())
        total_attributed_sales = float(by_store["attributed_sales"].sum())
        portfolio_blended_roas = (
            total_attributed_sales / total_spend if total_spend > 0 else 0.0
        )
        portfolio_avg_roas = float(by_store["roas"].mean())
        portfolio_total_incremental_orders = float(
            by_store["incremental_orders_per_week"].sum()
        )
        portfolio_max_promo_count = int(by_store["promo_count_active"].max())
    else:
        total_spend = 0.0
        total_attributed_sales = 0.0
        portfolio_blended_roas = 0.0
        portfolio_avg_roas = 0.0
        portfolio_total_incremental_orders = 0.0
        portfolio_max_promo_count = 0

    # Tier contributions
    tier_contributions: dict[str, dict] = {}
    red_stores: list[str] = []
    green_stores: list[str] = []
    for _, row in by_store.iterrows():
        flag, score, reasons = _classify_store_tier(row, flagged_stores)
        store = str(row["store"])
        tier_contributions[store] = {"score": score, "flag": flag, "reasons": reasons}
        if flag == "red":
            red_stores.append(store)
        elif flag == "green":
            green_stores.append(store)

    # Findings
    findings: list[dict] = []

    # 1. low_roas_high_spend — per store, high
    low_roas_high_spend_stores = []
    for _, row in by_store.iterrows():
        if (
            float(row["spend"]) > LOW_ROAS_HIGH_SPEND_SPEND_THRESHOLD
            and float(row["roas"]) < LOW_ROAS_HIGH_SPEND_ROAS_THRESHOLD
        ):
            low_roas_high_spend_stores.append(str(row["store"]))
    if low_roas_high_spend_stores:
        findings.append({
            "pattern_id": "low_roas_high_spend",
            "severity": "high",
            "scope": ",".join(low_roas_high_spend_stores),
            "evidence": {
                "stores": low_roas_high_spend_stores,
                "spend_threshold_usd": LOW_ROAS_HIGH_SPEND_SPEND_THRESHOLD,
                "roas_threshold": LOW_ROAS_HIGH_SPEND_ROAS_THRESHOLD,
                "note": "Money on fire — spend > $500 with ROAS < 2.5x.",
            },
            "estimated_impact_usd": None,
            "deliverable_trigger": {
                "skill": "campaign-plan",
                "params": {"stores": low_roas_high_spend_stores, "focus": "cost_recovery"},
            },
        })

    # 2. over_discounting — per store, medium
    over_discounting_stores = []
    for _, row in by_store.iterrows():
        if int(row["promo_count_active"]) >= OVER_DISCOUNTING_PROMO_COUNT_THRESHOLD:
            over_discounting_stores.append(str(row["store"]))
    if over_discounting_stores:
        findings.append({
            "pattern_id": "over_discounting",
            "severity": "medium",
            "scope": ",".join(over_discounting_stores),
            "evidence": {
                "stores": over_discounting_stores,
                "promo_count_threshold": OVER_DISCOUNTING_PROMO_COUNT_THRESHOLD,
                "note": "3+ active promos stacked — margin erosion + customer training risk.",
            },
            "estimated_impact_usd": None,
            "deliverable_trigger": {
                "skill": "campaign-plan",
                "params": {"stores": over_discounting_stores, "focus": "promo_consolidation"},
            },
        })

    # 3. spend_on_broken_store — Wk 2 stub: only fires when orchestrator passes flagged_stores
    spend_on_broken_stores = []
    for _, row in by_store.iterrows():
        store = str(row["store"])
        if store in flagged_stores and float(row["spend"]) > 0:
            spend_on_broken_stores.append(store)
    if spend_on_broken_stores:
        findings.append({
            "pattern_id": "spend_on_broken_store",
            "severity": "foundation",
            "scope": ",".join(spend_on_broken_stores),
            "evidence": {
                "stores": spend_on_broken_stores,
                "note": "Ad spend running on stores flagged red in ops/menu — pause until fixed.",
            },
            "estimated_impact_usd": None,
            "deliverable_trigger": {"skill": "", "params": {}},
        })

    # Radar contribution
    radar_contributions = {
        "Campaigns / ROAS": _radar_score_campaigns_roas(portfolio_blended_roas),
    }

    # Drafted layer
    n_red = len(red_stores)
    toggle_prose = (
        f"Portfolio blended ROAS {portfolio_blended_roas:.2f}x on ${total_spend:,.0f} total spend "
        f"(${total_attributed_sales:,.0f} attributed sales). "
        f"{n_red} store(s) flagged red on the campaigns sub-bucket."
    )

    win_risk_opp_candidates: list[dict] = []
    # Risks: one per red-tier store
    for store in red_stores:
        win_risk_opp_candidates.append({
            "type": "risk",
            "headline": f"{store}: campaigns sub-bucket broken — "
            + "; ".join(tier_contributions[store]["reasons"][:2]),
            "value_usd": None,
            "pattern_id": "campaigns_tier_red",
            "severity": "high",
        })
    # Win: portfolio blended ROAS >= 4.0
    if portfolio_blended_roas >= 4.0:
        win_risk_opp_candidates.append({
            "type": "win",
            "headline": (
                f"Portfolio blended ROAS {portfolio_blended_roas:.2f}x is at or above 4.0x — "
                "campaign engine is paying out"
            ),
            "value_usd": None,
            "pattern_id": "blended_roas_above_4",
            "severity": "low",
        })
    # Opportunity: green stores ready to scale
    if green_stores:
        win_risk_opp_candidates.append({
            "type": "opportunity",
            "headline": (
                f"Scale spend on {len(green_stores)} green store(s) "
                f"({', '.join(green_stores[:3])}{'…' if len(green_stores) > 3 else ''}) — "
                "fundamentals + ROAS both healthy"
            ),
            "value_usd": None,
            "pattern_id": "green_store_scale_opportunity",
            "severity": "medium",
        })

    # Charts: emit campaign_2x2 if a charts_dir was provided
    charts: list[dict] = []
    if charts_dir is not None and len(by_store):
        charts_dir = Path(charts_dir)
        charts_dir.mkdir(parents=True, exist_ok=True)
        try:
            if str(_CHART_HELPERS_PARENT) not in sys.path:
                sys.path.insert(0, str(_CHART_HELPERS_PARENT))
            from orchestrator import chart_helpers

            # Build per-row campaign records. Each store/platform combo from the
            # aggregated input becomes one bubble in the 2x2 (name = store/platform).
            campaigns_payload: list[dict] = []
            # Use the original (pre-aggregation) df so we keep the platform dimension.
            for _, row in df.iterrows():
                store = str(row["store"])
                platform = str(row.get("platform", ""))
                campaigns_payload.append({
                    "name": f"{store}/{platform}" if platform else store,
                    "spend": float(row["spend"]),
                    "roas": float(row["roas"]),
                    "orders": float(row["incremental_orders_per_week"]),
                    "platform": platform,
                })
            chart_path = chart_helpers.campaign_2x2(
                {"campaigns": campaigns_payload}, charts_dir
            )
            if chart_path is not None:
                charts.append({"id": "campaign_2x2", "path": str(chart_path)})
        except Exception:
            # Fail-open: chart errors should not break the sub-skill payload.
            pass

    return {
        "sub_skill": "diagnostic-campaigns",
        "version": "1.0",
        "client": client,
        "window": {"start": window_start, "end": window_end},
        "computed": {
            "metrics": {
                # Marketing Efficiency composite input (CRITICAL — orchestrator depends on this)
                "total_marketing_investment": total_spend,
                # Additional campaigns domain metrics
                "portfolio_blended_roas": portfolio_blended_roas,
                "portfolio_avg_roas": portfolio_avg_roas,
                "total_attributed_sales": total_attributed_sales,
                "total_incremental_orders_per_week": portfolio_total_incremental_orders,
                "max_promo_count_active": portfolio_max_promo_count,
                "store_count": int(len(by_store)),
                "red_campaigns_store_count": n_red,
                "green_campaigns_store_count": len(green_stores),
            },
            "radar_contributions": radar_contributions,
            "tier_contributions": tier_contributions,
            "findings": findings,
            "charts": charts,
        },
        "drafted": {
            "toggle_title": "Campaigns & Promos",
            "toggle_prose": toggle_prose,
            "win_risk_opp_candidates": win_risk_opp_candidates,
        },
        "data_quality": {"completeness": 1.0, "gaps": []},
    }
