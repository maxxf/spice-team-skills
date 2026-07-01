"""Operations & quality computation. Emits sub-skill contract payload.

Owns the per-store "ops" tier sub-bucket (framework lines 84–87). Implements 3
patterns: low_rating_below_42, error_spike, cancellation_surge.

Emits NO direct radar dims — the orchestrator composes the Operations radar
dim from this sub-skill's tier_contributions (see cross_cutting.assemble_radar).

CRITICAL: `computed.metrics` MUST include `rating`, `error_rate_pct`, and
`uptime_pct` — the orchestrator's foundation gate reads these.
"""
from __future__ import annotations

import pandas as pd

# Foundation thresholds (framework lines 84–87 + Stop Everything gate)
RATING_FOUNDATION_THRESHOLD = 4.2
ERROR_RATE_FOUNDATION_THRESHOLD = 5.0
CANCELLATION_HIGH_THRESHOLD = 5.0
UPTIME_FOUNDATION_THRESHOLD = 90.0

# Healthy thresholds (Green tier)
ERROR_RATE_HEALTHY_THRESHOLD = 2.0
CANCELLATION_HEALTHY_THRESHOLD = 2.0
UPTIME_HEALTHY_THRESHOLD = 97.0
RATING_HEALTHY_THRESHOLD = 4.5


def _aggregate_by_store(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse multi-row-per-store input. Numerics → mean, hours_accurate → last."""
    grouped = df.groupby("store", as_index=False).agg(
        rating=("rating", "mean"),
        error_rate_pct=("error_rate_pct", "mean"),
        cancellation_pct=("cancellation_pct", "mean"),
        uptime_pct=("uptime_pct", "mean"),
        hours_accurate=("hours_accurate", "last"),
    )
    return grouped


def _classify_store_tier(row) -> tuple[str, float, list[str]]:
    """Return (flag, score, reasons) for one store. Per framework lines 84–87."""
    rating = float(row["rating"])
    error = float(row["error_rate_pct"])
    cancel = float(row["cancellation_pct"])
    uptime = float(row["uptime_pct"])
    hours_ok = bool(row["hours_accurate"])

    error_red = error > ERROR_RATE_FOUNDATION_THRESHOLD
    cancel_red = cancel > CANCELLATION_HIGH_THRESHOLD
    uptime_red = uptime < UPTIME_FOUNDATION_THRESHOLD
    rating_red = rating < RATING_FOUNDATION_THRESHOLD
    hours_red = not hours_ok

    error_yellow = ERROR_RATE_HEALTHY_THRESHOLD <= error <= ERROR_RATE_FOUNDATION_THRESHOLD
    cancel_yellow = CANCELLATION_HEALTHY_THRESHOLD <= cancel <= CANCELLATION_HIGH_THRESHOLD
    uptime_yellow = UPTIME_FOUNDATION_THRESHOLD <= uptime <= UPTIME_HEALTHY_THRESHOLD
    rating_yellow = RATING_FOUNDATION_THRESHOLD <= rating < RATING_HEALTHY_THRESHOLD

    reasons: list[str] = []
    if error_red or cancel_red or uptime_red or rating_red or hours_red:
        if error_red:
            reasons.append(f"error rate {error:.1f}% > 5% (broken)")
        if cancel_red:
            reasons.append(f"cancellation {cancel:.1f}% > 5% (broken)")
        if uptime_red:
            reasons.append(f"uptime {uptime:.1f}% < 90% (broken)")
        if rating_red:
            reasons.append(f"rating {rating:.2f} < 4.2 (broken)")
        if hours_red:
            reasons.append("hours mismatch flagged (broken)")
        flag = "red"
    elif error_yellow or cancel_yellow or uptime_yellow or rating_yellow:
        if error_yellow:
            reasons.append(f"error rate {error:.1f}% in 2–5% band (watch)")
        if cancel_yellow:
            reasons.append(f"cancellation {cancel:.1f}% in 2–5% band (watch)")
        if uptime_yellow:
            reasons.append(f"uptime {uptime:.1f}% in 90–97% band (watch)")
        if rating_yellow:
            reasons.append(f"rating {rating:.2f} in 4.2–4.5 band (watch)")
        flag = "yellow"
    else:
        reasons.append(
            f"rating {rating:.2f}, error {error:.1f}%, cancel {cancel:.1f}%, uptime {uptime:.1f}%, hours accurate"
        )
        flag = "green"

    # Score: 1–10 blend of rating (0..5 → 0..1), inverse error (0..10 → 1..0),
    # uptime (0..100 → 0..1), inverse cancellation (0..10 → 1..0).
    rating_component = max(0.0, min(1.0, rating / 5.0))
    error_component = max(0.0, 1.0 - min(1.0, error / 10.0))
    uptime_component = max(0.0, min(1.0, uptime / 100.0))
    cancel_component = max(0.0, 1.0 - min(1.0, cancel / 10.0))
    blend = (
        0.35 * rating_component
        + 0.25 * error_component
        + 0.25 * uptime_component
        + 0.15 * cancel_component
    )
    score = round(1.0 + 9.0 * blend, 2)
    return flag, score, reasons


def _customer_sentiment(df: pd.DataFrame, rating_mean: float) -> tuple[float, str]:
    """Unified cross-platform Positive Rating Rate (framework: Customer Sentiment).

    If the input carries a pre-blended `customer_sentiment_pct` (built at input
    prep from DD loved/disliked + UE/GH 4–5★, volume-weighted), use it —
    weighted by `rating_count` when present. Otherwise derive it from the
    normalized star-equivalent rating: positive_rate = (rating − 1) / 4.
    """
    if "customer_sentiment_pct" in df.columns:
        s = pd.to_numeric(df["customer_sentiment_pct"], errors="coerce")
        if "rating_count" in df.columns:
            w = pd.to_numeric(df["rating_count"], errors="coerce").fillna(0.0)
            if w.sum() > 0:
                return round(float((s.fillna(0.0) * w).sum() / w.sum()), 1), "unified-positive-rate"
        if s.notna().any():
            return round(float(s.mean()), 1), "unified-positive-rate"
    pct = max(0.0, min(100.0, (rating_mean - 1.0) / 4.0 * 100.0))
    return round(pct, 1), "star-derived"


def run(*, client: str, window_start: str, window_end: str, df: pd.DataFrame) -> dict:
    by_store = _aggregate_by_store(df)

    # Portfolio-level metrics — foundation gate reads min/max per direction.
    if len(by_store):
        portfolio_rating_min = float(by_store["rating"].min())
        portfolio_rating_mean = float(by_store["rating"].mean())
        portfolio_error_max = float(by_store["error_rate_pct"].max())
        portfolio_error_mean = float(by_store["error_rate_pct"].mean())
        portfolio_uptime_min = float(by_store["uptime_pct"].min())
        portfolio_uptime_mean = float(by_store["uptime_pct"].mean())
        portfolio_cancel_max = float(by_store["cancellation_pct"].max())
        portfolio_cancel_mean = float(by_store["cancellation_pct"].mean())
        all_hours_accurate = bool(by_store["hours_accurate"].all())
    else:
        portfolio_rating_min = portfolio_rating_mean = 0.0
        portfolio_error_max = portfolio_error_mean = 0.0
        portfolio_uptime_min = portfolio_uptime_mean = 0.0
        portfolio_cancel_max = portfolio_cancel_mean = 0.0
        all_hours_accurate = True

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

    # 1. low_rating_below_42 — per store, foundation
    low_rating_stores = []
    for _, row in by_store.iterrows():
        if float(row["rating"]) < RATING_FOUNDATION_THRESHOLD:
            low_rating_stores.append(str(row["store"]))
    if low_rating_stores:
        findings.append({
            "pattern_id": "low_rating_below_42",
            "severity": "foundation",
            "scope": ",".join(low_rating_stores),
            "evidence": {
                "stores": low_rating_stores,
                "threshold": RATING_FOUNDATION_THRESHOLD,
                "note": "Stop Everything threshold per framework foundation gate.",
            },
            "estimated_impact_usd": None,
            "deliverable_trigger": {
                "skill": "ratings-flyer",
                "params": {"stores": low_rating_stores},
            },
        })

    # 2. error_spike — per store, foundation
    error_spike_stores = []
    for _, row in by_store.iterrows():
        if float(row["error_rate_pct"]) > ERROR_RATE_FOUNDATION_THRESHOLD:
            error_spike_stores.append(str(row["store"]))
    if error_spike_stores:
        findings.append({
            "pattern_id": "error_spike",
            "severity": "foundation",
            "scope": ",".join(error_spike_stores),
            "evidence": {
                "stores": error_spike_stores,
                "threshold_pct": ERROR_RATE_FOUNDATION_THRESHOLD,
                "note": "Stop Everything threshold per framework foundation gate.",
            },
            "estimated_impact_usd": None,
            "deliverable_trigger": {"skill": "", "params": {}},
        })

    # 3. cancellation_surge — per store, high
    cancel_surge_stores = []
    for _, row in by_store.iterrows():
        if float(row["cancellation_pct"]) > CANCELLATION_HIGH_THRESHOLD:
            cancel_surge_stores.append(str(row["store"]))
    if cancel_surge_stores:
        findings.append({
            "pattern_id": "cancellation_surge",
            "severity": "high",
            "scope": ",".join(cancel_surge_stores),
            "evidence": {
                "stores": cancel_surge_stores,
                "threshold_pct": CANCELLATION_HIGH_THRESHOLD,
            },
            "estimated_impact_usd": None,
            "deliverable_trigger": {"skill": "", "params": {}},
        })

    sentiment_pct, rating_basis = _customer_sentiment(df, portfolio_rating_mean)

    # Drafted layer
    n_red = sum(1 for v in tier_contributions.values() if v["flag"] == "red")
    toggle_prose = (
        f"Average rating {portfolio_rating_mean:.2f} (min {portfolio_rating_min:.2f}); "
        f"avg error rate {portfolio_error_mean:.1f}% (max {portfolio_error_max:.1f}%); "
        f"avg uptime {portfolio_uptime_mean:.1f}% (min {portfolio_uptime_min:.1f}%). "
        f"Customer sentiment {sentiment_pct:.0f}% positive ({rating_basis}). "
        f"{n_red} store(s) flagged red on the ops sub-bucket."
    )

    win_risk_opp_candidates: list[dict] = []
    # Risks: one per red-tier store
    for store in red_stores:
        win_risk_opp_candidates.append({
            "type": "risk",
            "headline": f"{store}: ops sub-bucket broken — " + "; ".join(tier_contributions[store]["reasons"][:2]),
            "value_usd": None,
            "pattern_id": "ops_tier_red",
            "severity": "high",
        })
    # Win: portfolio avg rating ≥ 4.5
    if portfolio_rating_mean >= RATING_HEALTHY_THRESHOLD:
        win_risk_opp_candidates.append({
            "type": "win",
            "headline": f"Portfolio average rating {portfolio_rating_mean:.2f} is at or above the 4.5 healthy threshold",
            "value_usd": None,
            "pattern_id": "rating_above_healthy",
            "severity": "low",
        })
    # Opportunity: uptime is bumpable (mean below healthy threshold but above foundation)
    if UPTIME_FOUNDATION_THRESHOLD <= portfolio_uptime_mean < UPTIME_HEALTHY_THRESHOLD:
        win_risk_opp_candidates.append({
            "type": "opportunity",
            "headline": (
                f"Lift portfolio uptime from {portfolio_uptime_mean:.1f}% toward 97% — "
                "tighten hours, fix downtime triggers, reduce auto-pause incidents"
            ),
            "value_usd": None,
            "pattern_id": "uptime_lift_opportunity",
            "severity": "medium",
        })

    return {
        "sub_skill": "diagnostic-ops",
        "version": "1.0",
        "client": client,
        "window": {"start": window_start, "end": window_end},
        "computed": {
            "metrics": {
                # Foundation gate inputs (CRITICAL — orchestrator depends on these keys)
                "rating": portfolio_rating_min,  # min — gate fires on any store < 4.2
                "error_rate_pct": portfolio_error_max,  # max — gate fires on any store > 5%
                "uptime_pct": portfolio_uptime_min,  # min — gate fires on any store < 90%
                # Additional ops domain metrics
                "rating_mean": portfolio_rating_mean,
                "error_rate_pct_mean": portfolio_error_mean,
                "uptime_pct_mean": portfolio_uptime_mean,
                "cancellation_pct": portfolio_cancel_max,
                "cancellation_pct_mean": portfolio_cancel_mean,
                "all_hours_accurate": all_hours_accurate,
                "store_count": int(len(by_store)),
                "red_ops_store_count": n_red,
                # Unified cross-platform Customer Sentiment (framework spec)
                "customer_sentiment_pct": sentiment_pct,
                "rating_basis": rating_basis,
            },
            # Operations radar dim is a composite computed by orchestrator from tier_contributions
            "radar_contributions": {},
            "tier_contributions": tier_contributions,
            "findings": findings,
            "charts": [],
        },
        "drafted": {
            "toggle_title": "Operations & Quality",
            "toggle_prose": toggle_prose,
            "win_risk_opp_candidates": win_risk_opp_candidates,
        },
        "data_quality": {"completeness": 1.0, "gaps": []},
    }
