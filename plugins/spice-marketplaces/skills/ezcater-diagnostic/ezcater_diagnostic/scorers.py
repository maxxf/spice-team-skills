from __future__ import annotations

"""Per-store aggregation and the three catering sub-bucket scorers (v0.2).

Sub-buckets — Ops · Visibility · Packaging — classified Healthy / Watch / Broken.

v0.2 encodes the TWO threshold systems the live portal exposes:
- **Pause/accountability standards** — breaching these pauses the store (zero orders).
  → drive the Ops **Broken** flag.
- **Badge goals** — stricter; missing these costs visibility but not marketplace access.
  → drive the Ops **Watch** flag.
Delivery tracking is a badge goal handled in badge.py (kept OUT of the ops flag so a
self-delivery client's structural 0% tracking doesn't mark every store Watch).
"""

import math

import pandas as pd

# --- Pause / accountability standards (revenue-gating) ---
REJECTION_PAUSE = 5.0
CANCELLATION_PAUSE = 3.0
ON_TIME_PAUSE = 95.0
READY_FOR_DISPATCH_PAUSE = 95.0

# --- Badge / quality goals (visibility) ---
RATING_HEALTHY = 4.8        # badge bar
RATING_BROKEN = 4.5         # severe
ON_TIME_BADGE = 98.5
REJECTION_BADGE = 0.5
CANCELLATION_BADGE = 0.0    # canceled goal is 0%
ACCURACY_BADGE = 99.0
ACCURACY_BROKEN = 97.0      # severe accuracy miss
DELIVERY_TRACKING_BADGE = 75.0
ON_TIME_ACCEPTANCE_GOAL = 100.0
ON_TIME_ACCEPTANCE_LOW = 95.0  # finding threshold

# --- Visibility thresholds ---
ROAS_HEALTHY = 3.5
ROAS_BROKEN = 2.5

# --- Packaging thresholds ---
PACKAGING_HEALTHY = 0.9
PACKAGING_BROKEN = 0.6

# --- Volume / activity gates ---
ACTIVE_MIN_ORDERS = 1
BADGE_VOLUME_MIN_ORDERS = 6


def _isnan(x) -> bool:
    try:
        return math.isnan(float(x))
    except (TypeError, ValueError):
        return False


def aggregate_by_store(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse multi-month rows to one row per store."""
    agg = dict(
        gross_sales=("gross_sales", "sum"),
        orders=("orders", "sum"),
        on_time_pct=("on_time_pct", "mean"),
        on_time_acceptance_pct=("on_time_acceptance_pct", "mean"),
        rejection_rate_pct=("rejection_rate_pct", "mean"),
        order_accuracy_pct=("order_accuracy_pct", "mean"),
        cancellation_pct=("cancellation_pct", "mean"),
        delivery_tracking_pct=("delivery_tracking_pct", "mean"),
        rating=("rating", "mean"),
        review_count=("review_count", "max"),
        status=("status", "last"),
        ppp_bid_pct=("ppp_bid_pct", "max"),
        ezrewards_pct=("ezrewards_pct", "max"),
        sponsored_spend=("sponsored_spend", "sum"),
        sponsored_attributed_sales=("sponsored_attributed_sales", "sum"),
        promo_count_active=("promo_count_active", "max"),
        packaging_complete=("packaging_complete", "mean"),
    )
    if "ready_for_dispatch_pct" in df.columns:
        agg["ready_for_dispatch_pct"] = ("ready_for_dispatch_pct", "mean")
    grouped = df.groupby("store", as_index=False).agg(**agg)
    if "ready_for_dispatch_pct" not in grouped.columns:
        grouped["ready_for_dispatch_pct"] = float("nan")
    grouped["status"] = grouped["status"].astype(str).str.lower()
    grouped["aov"] = grouped.apply(
        lambda r: (r["gross_sales"] / r["orders"]) if r["orders"] else 0.0, axis=1
    )
    if "badged" in df.columns:
        src = df.assign(badged=(df["badged"] == True))  # noqa: E712
        badged = src.groupby("store")["badged"].max()
        grouped["badged"] = grouped["store"].map(badged) == True  # noqa: E712
    else:
        grouped["badged"] = False
    return grouped


def _breaches_pause_standard(row) -> list[str]:
    reasons = []
    if str(row["status"]).lower() == "paused":
        reasons.append("store PAUSED on marketplace (broken)")
    if float(row["rejection_rate_pct"]) > REJECTION_PAUSE:
        reasons.append(f"rejection {float(row['rejection_rate_pct']):.1f}% > 5% pause standard (broken)")
    if float(row["cancellation_pct"]) > CANCELLATION_PAUSE:
        reasons.append(f"cancellation {float(row['cancellation_pct']):.1f}% > 3% pause standard (broken)")
    if float(row["on_time_pct"]) < ON_TIME_PAUSE:
        reasons.append(f"on-time {float(row['on_time_pct']):.1f}% < 95% pause standard (broken)")
    rfd = row.get("ready_for_dispatch_pct")
    if rfd is not None and not _isnan(rfd) and float(rfd) < READY_FOR_DISPATCH_PAUSE:
        reasons.append(f"ready-for-dispatch {float(rfd):.1f}% < 95% pause standard (broken)")
    if float(row["rating"]) < RATING_BROKEN:
        reasons.append(f"rating {float(row['rating']):.2f} < 4.5 (broken)")
    if float(row["order_accuracy_pct"]) < ACCURACY_BROKEN:
        reasons.append(f"accuracy {float(row['order_accuracy_pct']):.1f}% < 97% (broken)")
    return reasons


def _misses_badge_goal(row) -> list[str]:
    reasons = []
    if str(row["status"]).lower() == "at_risk":
        reasons.append("store At Risk of pause (watch)")
    if float(row["rejection_rate_pct"]) >= REJECTION_BADGE:
        reasons.append(f"rejection {float(row['rejection_rate_pct']):.2f}% ≥ 0.5% badge goal (watch)")
    if float(row["cancellation_pct"]) > CANCELLATION_BADGE:
        reasons.append(f"cancellation {float(row['cancellation_pct']):.2f}% > 0% badge goal (watch)")
    if float(row["on_time_pct"]) < ON_TIME_BADGE:
        reasons.append(f"on-time {float(row['on_time_pct']):.1f}% < 98.5% badge goal (watch)")
    if float(row["order_accuracy_pct"]) < ACCURACY_BADGE:
        reasons.append(f"accuracy {float(row['order_accuracy_pct']):.1f}% < 99% badge goal (watch)")
    if float(row["rating"]) < RATING_HEALTHY:
        reasons.append(f"rating {float(row['rating']):.2f} < 4.8 badge goal (watch)")
    return reasons


def classify_ops(row) -> tuple[str, list[str]]:
    broken = _breaches_pause_standard(row)
    if broken:
        return "broken", broken
    watch = _misses_badge_goal(row)
    if watch:
        return "watch", watch
    return "healthy", [
        f"rating {float(row['rating']):.2f}, on-time {float(row['on_time_pct']):.1f}%, "
        f"rejection {float(row['rejection_rate_pct']):.2f}%, accuracy {float(row['order_accuracy_pct']):.1f}%, "
        f"cancel {float(row['cancellation_pct']):.2f}% — meets all badge goals"
    ]


def sponsored_roas(row) -> float | None:
    spend = float(row["sponsored_spend"])
    if spend <= 0:
        return None
    return float(row["sponsored_attributed_sales"]) / spend


def classify_visibility(row) -> tuple[str, list[str]]:
    """'No levers active' is Watch (opportunity), not Broken — see framework note."""
    ppp_on = float(row["ppp_bid_pct"]) > 0
    rew_on = float(row["ezrewards_pct"]) > 0
    spend = float(row["sponsored_spend"])
    roas = sponsored_roas(row)
    levers_on = sum([ppp_on, rew_on, spend > 0])

    if spend > 0 and roas is not None and roas < ROAS_BROKEN:
        return "broken", [f"sponsored ROAS {roas:.1f}x < 2.5x with spend (broken)"]
    if ppp_on and rew_on and (spend == 0 or (roas is not None and roas >= ROAS_HEALTHY)):
        note = "PPP + ezRewards on" + (f", sponsored ROAS {roas:.1f}x" if roas is not None else "")
        return "healthy", [note + " (healthy)"]
    if levers_on == 0:
        return "watch", ["no visibility levers active — opportunity (watch)"]
    if levers_on == 1:
        return "watch", ["only one visibility lever active (watch)"]
    if roas is not None and ROAS_BROKEN <= roas < ROAS_HEALTHY:
        return "watch", [f"sponsored ROAS {roas:.1f}x in 2.5–3.5x band (watch)"]
    return "watch", ["visibility levers partially active (watch)"]


def classify_packaging(row) -> tuple[str, list[str]]:
    pc = float(row["packaging_complete"])
    if pc < PACKAGING_BROKEN:
        return "broken", [f"packaging completeness {pc:.0%} < 60% (broken)"]
    if pc < PACKAGING_HEALTHY:
        return "watch", [f"packaging completeness {pc:.0%} in 60–90% band (watch)"]
    return "healthy", [f"packaging completeness {pc:.0%} (healthy)"]
