"""Top-line metric computation. Emits sub-skill contract payload."""
from __future__ import annotations

import pandas as pd


def run(*, client: str, window_start: str, window_end: str, df: pd.DataFrame) -> dict:
    gross_sales = float(df["gross_sales"].sum())
    orders = int(df["orders"].sum())
    aov = gross_sales / orders if orders else 0.0
    net_payout = float(df["net_payout"].sum())
    payout_pct = (net_payout / gross_sales * 100) if gross_sales else 0.0

    # Weekly trend (feeds chart_helpers.trend_overlay). Derived from the
    # unified input — no fabrication: GMV/net payout summed per week, ROAS =
    # weekly attributed sales / weekly ad spend (0 when no spend that week).
    trend_weekly: dict = {}
    if "week" in df.columns and len(df):
        g = df.groupby("week", as_index=True)
        wk = sorted(int(w) for w in g.groups)
        gmv_w = g["gross_sales"].sum()
        pay_w = g["net_payout"].sum()

        def _roas_w(w: int) -> float:
            rows = df[df["week"] == w]
            spend = float(rows["spend"].sum()) if "spend" in df.columns else 0.0
            attr = float(rows["attributed_sales"].sum()) if "attributed_sales" in df.columns else 0.0
            return round(attr / spend, 2) if spend > 0 else 0.0

        trend_weekly = {
            "weeks": [f"W{w:02d}" for w in wk],
            "gmv": [round(float(gmv_w[w]), 2) for w in wk],
            "net_payout": [round(float(pay_w[w]), 2) for w in wk],
            "roas": [_roas_w(w) for w in wk],
        }

    # Naive radar scoring — Wk 2 will replace with real benchmarking
    aov_score = max(1.0, min(10.0, aov / 5))  # $50 AOV = 10

    # Re-order Rate — REAL when `reorder_rate_pct` is supplied (UE Repeat
    # Customer Rate + DD Frequent Customers, per framework). When absent we do
    # NOT fabricate a score: the dim is suppressed and a data-quality gap is
    # recorded so the radar/report shows it honestly as unmeasured.
    reorder_gap: str | None = None
    reorder_score: float | None = None
    if "reorder_rate_pct" in df.columns:
        rr = pd.to_numeric(df["reorder_rate_pct"], errors="coerce").dropna()
        if len(rr):
            v = float(rr.mean())
            # Framework scoring band (diagnostic-framework.md · Re-order Rate)
            if v < 15:
                reorder_score = 2.0
            elif v < 25:
                reorder_score = 4.0
            elif v < 35:
                reorder_score = 6.0
            elif v < 45:
                reorder_score = 7.5
            elif v < 55:
                reorder_score = 9.0
            else:
                reorder_score = 10.0
    if reorder_score is None:
        reorder_gap = (
            "Re-order Rate: no repeat-customer data in input "
            "(reorder_rate_pct absent) — radar dim suppressed; supply UE "
            "Repeat Customer Rate + DD Frequent Customers to score it."
        )

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
            "metrics": {"gross_sales": gross_sales, "orders": orders, "aov": aov, "net_payout": net_payout, "payout_pct": payout_pct, "trend_weekly": trend_weekly},
            "radar_contributions": (
                {"AOV": aov_score, "Re-order Rate": reorder_score}
                if reorder_score is not None
                else {"AOV": aov_score}  # Re-order suppressed — see data_quality
            ),
            "tier_contributions": {},  # topline does not contribute to tier — leave empty
            "findings": findings,
            "charts": [],
        },
        "drafted": {
            "toggle_title": "Top-line Performance",
            "toggle_prose": f"Gross sales: ${gross_sales:,.0f} across {orders:,} orders. AOV: ${aov:.2f}. Net payout: {payout_pct:.1f}%.",
            "win_risk_opp_candidates": [],
        },
        "data_quality": {
            "completeness": 1.0 if reorder_gap is None else 0.9,
            "gaps": [reorder_gap] if reorder_gap else [],
        },
    }
