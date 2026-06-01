"""Top-line metric computation. Emits sub-skill contract payload."""
from __future__ import annotations

import pandas as pd


def run(*, client: str, window_start: str, window_end: str, df: pd.DataFrame) -> dict:
    gross_sales = float(df["gross_sales"].sum())
    orders = int(df["orders"].sum())
    aov = gross_sales / orders if orders else 0.0
    net_payout = float(df["net_payout"].sum())
    payout_pct = (net_payout / gross_sales * 100) if gross_sales else 0.0

    # Naive radar scoring — Wk 2 will replace with real benchmarking
    aov_score = max(1.0, min(10.0, aov / 5))  # $50 AOV = 10
    reorder_score = 6.0  # placeholder; real metric needs customer-level data

    findings: list[dict] = []
    if payout_pct < 50:
        findings.append({
            "pattern_id": "payout_collapse",
            "severity": "foundation",
            "scope": "portfolio",
            "evidence": {"payout_pct": payout_pct},
            "estimated_impact_usd": (50 - payout_pct) / 100 * gross_sales,
            "deliverable_trigger": {"skill": "campaign-plan", "params": {"focus": "cost_recovery"}},
        })

    return {
        "sub_skill": "diagnostic-topline",
        "version": "1.0",
        "client": client,
        "window": {"start": window_start, "end": window_end},
        "computed": {
            "metrics": {"gross_sales": gross_sales, "orders": orders, "aov": aov, "net_payout": net_payout, "payout_pct": payout_pct},
            "radar_contributions": {"AOV": aov_score, "Re-order Rate": reorder_score},
            "tier_contributions": {},  # topline does not contribute to tier — leave empty
            "findings": findings,
            "charts": [],
        },
        "drafted": {
            "toggle_title": "Top-line Performance",
            "toggle_prose": f"Gross sales: ${gross_sales:,.0f} across {orders:,} orders. AOV: ${aov:.2f}. Net payout: {payout_pct:.1f}%.",
            "win_risk_opp_candidates": [],
        },
        "data_quality": {"completeness": 1.0, "gaps": []},
    }
