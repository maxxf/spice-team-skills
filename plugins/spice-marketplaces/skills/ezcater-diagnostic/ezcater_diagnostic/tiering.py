from __future__ import annotations

"""Tier rollup + foundation gate (v0.2).

Rollup: paused stores are Red (revenue emergency) regardless of volume; then the
New override (orders < 6); then worst-flag across the 3 sub-buckets (matches the
deployed delivery cross_cutting.rollup_tiers — no '2+ watch → red' for catering).
Foundation gate keys off the pause/accountability standards (the loose, revenue-
gating set), not the strict badge goals.
"""

import math

from ezcater_diagnostic import scorers


def _isnan(x) -> bool:
    try:
        return math.isnan(float(x))
    except (TypeError, ValueError):
        return False


def rollup_store(*, orders: int, status: str, ops_flag: str, visibility_flag: str, packaging_flag: str) -> dict:
    bucket_flags = {"ops": ops_flag, "visibility": visibility_flag, "packaging": packaging_flag}
    status = str(status).lower()

    if status == "paused":
        return {"tier": "red", "worst_bucket": "ops", "per_bucket_flags": bucket_flags,
                "reason": "store PAUSED — cannot accept orders"}

    if orders < scorers.BADGE_VOLUME_MIN_ORDERS:
        return {"tier": "new", "worst_bucket": None, "per_bucket_flags": bucket_flags,
                "reason": "dark store (0 orders)" if orders == 0 else f"volume-locked ({orders} orders < 6 in 90d)"}

    if any(f == "broken" for f in bucket_flags.values()):
        tier = "red"
    elif any(f == "watch" for f in bucket_flags.values()):
        tier = "yellow"
    else:
        tier = "green"

    worst_bucket = None
    for severity in ("broken", "watch"):
        for bucket, flag in bucket_flags.items():
            if flag == severity:
                worst_bucket = bucket
                break
        if worst_bucket:
            break

    return {"tier": tier, "worst_bucket": worst_bucket, "per_bucket_flags": bucket_flags, "reason": None}


def compute_foundation_gate(by_store) -> dict:
    """Trigger if ANY active store is paused or breaches a pause/accountability standard.

    Active = orders >= 1; dark/volume-locked stores don't gate the portfolio's spend.
    """
    active = by_store[by_store["orders"] >= scorers.ACTIVE_MIN_ORDERS]
    triggers: list[dict] = []
    if len(active) == 0:
        return {"triggered": False, "triggers": [], "override_action_plan": False}

    paused = active[active["status"].astype(str).str.lower() == "paused"]
    if len(paused):
        triggers.append({"metric": "status", "value": "paused", "scope": "portfolio",
                         "stores": sorted(str(s) for s in paused["store"])})

    checks = [
        ("rejection_rate_pct", ">", scorers.REJECTION_PAUSE),
        ("cancellation_pct", ">", scorers.CANCELLATION_PAUSE),
        ("on_time_pct", "<", scorers.ON_TIME_PAUSE),
        ("rating", "<", scorers.RATING_BROKEN),
        ("order_accuracy_pct", "<", scorers.ACCURACY_BROKEN),
    ]
    for col, op, threshold in checks:
        if op == "<":
            offenders = active[active[col] < threshold]
            value = float(active[col].min())
        else:
            offenders = active[active[col] > threshold]
            value = float(active[col].max())
        if len(offenders) > 0:
            triggers.append({"metric": col, "value": value, "threshold": threshold,
                             "operator": op, "scope": "portfolio",
                             "stores": sorted(str(s) for s in offenders["store"])})

    # ready_for_dispatch only where reported (self-delivery → NaN, skip)
    if "ready_for_dispatch_pct" in active.columns:
        rfd = active[~active["ready_for_dispatch_pct"].apply(_isnan)]
        offenders = rfd[rfd["ready_for_dispatch_pct"] < scorers.READY_FOR_DISPATCH_PAUSE]
        if len(offenders) > 0:
            triggers.append({"metric": "ready_for_dispatch_pct", "value": float(offenders["ready_for_dispatch_pct"].min()),
                             "threshold": scorers.READY_FOR_DISPATCH_PAUSE, "operator": "<", "scope": "portfolio",
                             "stores": sorted(str(s) for s in offenders["store"])})

    return {"triggered": bool(triggers), "triggers": triggers, "override_action_plan": bool(triggers)}
