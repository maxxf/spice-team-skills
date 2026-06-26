from __future__ import annotations

"""Reliability Rockstar badge eligibility funnel (v0.2).

Confirmed badge goals (live portal): order volume ≥6, rejected ≤0.5%, canceled 0%,
accuracy ≥99%, on-time ≥98.5%, **delivery tracking ≥75%** (+ rating ≥4.8 after ≥8 reviews).

Delivery tracking is the gate self-delivery clients fail (0% tracking). So the funnel
splits the gap two ways:
- **tracking-blocked** — passes every goal EXCEPT delivery tracking (operational fix:
  enable driver status updates / ezDispatch). This is the Tiff's case.
- **enrollment** — passes everything incl. tracking but isn't badged (enrollment/config).
"""

from ezcater_diagnostic import scorers

BADGE_MIN_REVIEWS = 8


def _meets_excl_tracking(row) -> bool:
    return (
        float(row["rating"]) >= scorers.RATING_HEALTHY
        and int(row["review_count"]) >= BADGE_MIN_REVIEWS
        and float(row["on_time_pct"]) >= scorers.ON_TIME_BADGE
        and float(row["rejection_rate_pct"]) < scorers.REJECTION_BADGE
        and float(row["order_accuracy_pct"]) >= scorers.ACCURACY_BADGE
        and float(row["cancellation_pct"]) <= scorers.CANCELLATION_BADGE
    )


def _tracking_ok(row) -> bool:
    return float(row["delivery_tracking_pct"]) >= scorers.DELIVERY_TRACKING_BADGE


def compute_badge_funnel(by_store) -> dict:
    total = len(by_store)
    active = by_store[by_store["orders"] >= scorers.ACTIVE_MIN_ORDERS]
    volume_eligible = by_store[by_store["orders"] >= scorers.BADGE_VOLUME_MIN_ORDERS]

    if len(volume_eligible):
        excl_mask = volume_eligible.apply(_meets_excl_tracking, axis=1)
        pass_excl = volume_eligible[excl_mask]
    else:
        pass_excl = volume_eligible

    if len(pass_excl):
        tracking_ok_mask = pass_excl.apply(_tracking_ok, axis=1)
        full_pass = pass_excl[tracking_ok_mask]
        tracking_blocked = pass_excl[~tracking_ok_mask]
    else:
        full_pass = pass_excl
        tracking_blocked = pass_excl

    badged = by_store[by_store["badged"] == True]  # noqa: E712
    enrollment_gap = full_pass[full_pass["badged"] == False]  # noqa: E712
    tracking_gap = tracking_blocked[tracking_blocked["badged"] == False]  # noqa: E712

    return {
        "total": total,
        "active": len(active),
        "volume_eligible": len(volume_eligible),
        "pass_excl_tracking": len(pass_excl),
        "full_pass": len(full_pass),
        "badged": len(badged),
        "tracking_blocked_count": len(tracking_gap),
        "tracking_blocked_stores": sorted(str(s) for s in tracking_gap["store"]),
        "enrollment_gap_count": len(enrollment_gap),
        "enrollment_gap_stores": sorted(str(s) for s in enrollment_gap["store"]),
    }
