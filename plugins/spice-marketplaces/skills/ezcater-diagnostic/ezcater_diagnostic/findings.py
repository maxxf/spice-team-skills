from __future__ import annotations

"""Catering pattern library → findings (v0.2).

Severities: foundation > high > medium > win. New in v0.2: store_paused (P0),
pause_risk, badge_gap split (tracking vs enrollment), on_time_acceptance_low, and
the optional low_conversion_vs_peer (needs portfolio funnel data).
"""

import math

from ezcater_diagnostic import scorers


def _stores(df) -> list[str]:
    return sorted(str(s) for s in df["store"])


def _isnan(x) -> bool:
    try:
        return math.isnan(float(x))
    except (TypeError, ValueError):
        return False


def detect_findings(by_store, badge_funnel: dict, portfolio: dict | None = None) -> list[dict]:
    findings: list[dict] = []
    active = by_store[by_store["orders"] >= scorers.ACTIVE_MIN_ORDERS]
    status_lc = active["status"].astype(str).str.lower()

    # --- Pause (revenue emergency) ---
    paused = active[status_lc == "paused"]
    if len(paused):
        findings.append({
            "pattern_id": "store_paused", "severity": "foundation", "bucket": "ops",
            "stores": _stores(paused),
            "evidence": {"note": "Paused stores accept ZERO marketplace orders until reinstated."},
            "action": "Complete ezCater's remediation course (cancellations/rejections/on-time) to unpause — top priority, store earns $0 while paused.",
        })

    not_paused = active[status_lc != "paused"]

    def _pause_breach(r):
        if float(r["rejection_rate_pct"]) > scorers.REJECTION_PAUSE:
            return True
        if float(r["cancellation_pct"]) > scorers.CANCELLATION_PAUSE:
            return True
        if float(r["on_time_pct"]) < scorers.ON_TIME_PAUSE:
            return True
        rfd = r.get("ready_for_dispatch_pct")
        if rfd is not None and not _isnan(rfd) and float(rfd) < scorers.READY_FOR_DISPATCH_PAUSE:
            return True
        return False

    pause_risk = not_paused[not_paused.apply(_pause_breach, axis=1)]
    if len(pause_risk):
        findings.append({
            "pattern_id": "pause_risk", "severity": "high", "bucket": "ops",
            "stores": _stores(pause_risk),
            "evidence": {"standards": "rejection≤5%, cancellation≤3%, on-time≥95%, ready-for-dispatch≥95%"},
            "action": "Fix before ezCater pauses the store — breaching an accountability standard.",
        })

    # --- Ops badge-goal misses ---
    low_rating = active[active["rating"] < scorers.RATING_BROKEN]
    if len(low_rating):
        findings.append({
            "pattern_id": "low_rating", "severity": "foundation", "bucket": "ops",
            "stores": _stores(low_rating), "evidence": {"threshold": scorers.RATING_BROKEN},
            "action": "Ratings push — rating below 4.5 caps badge eligibility and ranking.",
        })

    on_time = active[active["on_time_pct"] < scorers.ON_TIME_BADGE]
    if len(on_time):
        findings.append({
            "pattern_id": "on_time_below_badge", "severity": "high", "bucket": "ops",
            "stores": _stores(on_time), "evidence": {"badge_threshold_pct": scorers.ON_TIME_BADGE},
            "action": "Fix on-time delivery to clear the 98.5% badge bar (15-min window).",
        })

    rejection = active[active["rejection_rate_pct"] >= scorers.REJECTION_BADGE]
    if len(rejection):
        findings.append({
            "pattern_id": "rejection_misconfig", "severity": "medium", "bucket": "ops",
            "stores": _stores(rejection), "evidence": {"badge_threshold_pct": scorers.REJECTION_BADGE},
            "action": "Audit rejection/lead-time settings — usually configuration, not demand.",
        })

    accuracy = active[active["order_accuracy_pct"] < scorers.ACCURACY_BADGE]
    if len(accuracy):
        sev = "foundation" if (accuracy["order_accuracy_pct"] < scorers.ACCURACY_BROKEN).any() else "high"
        findings.append({
            "pattern_id": "order_accuracy_low", "severity": sev, "bucket": "ops",
            "stores": _stores(accuracy), "evidence": {"badge_threshold_pct": scorers.ACCURACY_BADGE},
            "action": "Accuracy/QA fix at flagged stores.",
        })

    acceptance = active[active["on_time_acceptance_pct"] < scorers.ON_TIME_ACCEPTANCE_LOW]
    if len(acceptance):
        findings.append({
            "pattern_id": "on_time_acceptance_low", "severity": "medium", "bucket": "ops",
            "stores": _stores(acceptance), "evidence": {"goal_pct": scorers.ON_TIME_ACCEPTANCE_GOAL},
            "action": "Improve order acceptance speed (accept within 15 min) — visible to customers.",
        })

    # --- Packaging ---
    packaging = active[active["packaging_complete"] < scorers.PACKAGING_BROKEN]
    if len(packaging):
        findings.append({
            "pattern_id": "packaging_incomplete", "severity": "foundation", "bucket": "packaging",
            "stores": _stores(packaging), "evidence": {"threshold": scorers.PACKAGING_BROKEN},
            "action": "Build catering packages — per-person pricing, headcount tiers, lead-time-gated bundles.",
        })

    # --- Visibility / badge ---
    if badge_funnel["tracking_blocked_count"] > 0:
        findings.append({
            "pattern_id": "badge_gap_tracking", "severity": "high", "bucket": "visibility",
            "stores": badge_funnel["tracking_blocked_stores"],
            "evidence": {"note": "Pass every badge goal except Delivery Tracking ≥75%."},
            "action": "Enable delivery status updates (driver app / ezDispatch) to unlock the Rockstar badge — free visibility.",
        })

    if badge_funnel["enrollment_gap_count"] > 0:
        findings.append({
            "pattern_id": "badge_gap_enrollment", "severity": "high", "bucket": "visibility",
            "stores": badge_funnel["enrollment_gap_stores"],
            "evidence": {"note": "Meet all badge goals incl. tracking but not badged."},
            "action": "Resolve Reliability Rockstar enrollment/config — badge earned but not displayed.",
        })

    def _no_levers(r):
        return float(r["ppp_bid_pct"]) == 0 and float(r["ezrewards_pct"]) == 0 and float(r["sponsored_spend"]) == 0
    levers_off = active[active.apply(_no_levers, axis=1)]
    if len(levers_off):
        findings.append({
            "pattern_id": "levers_all_off", "severity": "high", "bucket": "visibility",
            "stores": _stores(levers_off),
            "evidence": {"opportunity": "PPP + ezRewards ≈ +30% orders; all levers currently off"},
            "action": "Turn on Preferred Partner + ezRewards (ezManage); pilot a Sponsored Listing.",
        })

    def _low_roas(r):
        spend = float(r["sponsored_spend"])
        return spend > 0 and (float(r["sponsored_attributed_sales"]) / spend) < scorers.ROAS_BROKEN
    low_roas = active[active.apply(_low_roas, axis=1)]
    if len(low_roas):
        findings.append({
            "pattern_id": "low_roas_sponsored", "severity": "high", "bucket": "visibility",
            "stores": _stores(low_roas), "evidence": {"roas_floor": scorers.ROAS_BROKEN},
            "action": "Fix or kill sponsored spend — ROAS below 2.5x.",
        })

    over_promo = active[active["promo_count_active"] >= 3]
    if len(over_promo):
        findings.append({
            "pattern_id": "over_discounting", "severity": "medium", "bucket": "visibility",
            "stores": _stores(over_promo), "evidence": {"promo_count_threshold": 3},
            "action": "Consolidate promos — 3+ active offers stack into margin erosion.",
        })

    # --- Topline / volume ---
    dark = by_store[by_store["orders"] == 0]
    if len(dark):
        findings.append({
            "pattern_id": "dark_stores", "severity": "medium", "bucket": "topline",
            "stores": _stores(dark), "evidence": {"orders": 0},
            "action": "Reactivation push — 0 orders in 90 days.",
        })

    locked = by_store[(by_store["orders"] >= 1) & (by_store["orders"] < scorers.BADGE_VOLUME_MIN_ORDERS)]
    if len(locked):
        findings.append({
            "pattern_id": "volume_locked", "severity": "medium", "bucket": "topline",
            "stores": _stores(locked), "evidence": {"badge_gate_orders": scorers.BADGE_VOLUME_MIN_ORDERS},
            "action": "Awareness investment to cross the 6-order badge eligibility gate.",
        })

    # --- Conversion vs peer (portfolio-level, optional) ---
    if portfolio:
        cr = portfolio.get("conversion_rate_pct")
        bench = portfolio.get("conversion_benchmark_pct")
        if cr is not None and bench is not None and cr < bench:
            findings.append({
                "pattern_id": "low_conversion_vs_peer", "severity": "high", "bucket": "packaging",
                "stores": [], "evidence": {"conversion_rate_pct": cr, "benchmark_pct": bench},
                "action": "Lift Menu-View→Order conversion vs local peers — menu photos, packaging, pricing, promos/ezRewards.",
            })

    return findings


SEVERITY_RANK = {"foundation": 4, "high": 3, "medium": 2, "win": 1}
