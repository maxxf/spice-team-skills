from __future__ import annotations

"""ezCater diagnostic input CSV schema validator (v0.2).

One row per store × month (3 monthly buckets = 90 days). Single platform (EZ).
v0.2 (post live-portal exploration) adds: store `status` (pause modeling),
`delivery_tracking_pct` (the badge gate), `on_time_acceptance_pct`, and optional
`ready_for_dispatch_pct`. See references/ezcater-input-schema.md.
"""

import pandas as pd

REQUIRED_COLUMNS = {
    "store", "month", "platform", "status",
    # topline
    "gross_sales", "orders",
    # ops — accountability (pause) + quality (badge)
    "on_time_pct", "on_time_acceptance_pct", "rejection_rate_pct",
    "order_accuracy_pct", "cancellation_pct", "delivery_tracking_pct",
    "rating", "review_count",
    # visibility levers
    "ppp_bid_pct", "ezrewards_pct", "sponsored_spend",
    "sponsored_attributed_sales", "promo_count_active",
    # packaging
    "packaging_complete",
}

VALID_STATUS = {"active", "at_risk", "paused"}

PCT_COLUMNS = [
    "on_time_pct", "on_time_acceptance_pct", "rejection_rate_pct",
    "order_accuracy_pct", "cancellation_pct", "delivery_tracking_pct",
]


class InputSchemaError(ValueError):
    pass


def validate(df: pd.DataFrame) -> None:
    """Raise InputSchemaError with an actionable message if df is malformed."""
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise InputSchemaError(
            f"ezCater input CSV is missing required columns: {sorted(missing)}. "
            f"See references/ezcater-input-schema.md for the full schema. "
            f"Found columns: {sorted(df.columns)}"
        )
    if df.empty:
        raise InputSchemaError("ezCater input CSV has no rows. Need at least 1 store × 1 month.")
    if not df["month"].between(1, 3).all():
        raise InputSchemaError("'month' column must be integers 1–3 (90-day window = 3 monthly buckets).")
    if not df["rating"].between(0, 5).all():
        raise InputSchemaError(
            f"'rating' column has values outside 0–5: min={df['rating'].min()}, max={df['rating'].max()}"
        )
    if not df["packaging_complete"].between(0, 1).all():
        raise InputSchemaError("'packaging_complete' must be a fraction in 0–1.")
    for col in PCT_COLUMNS:
        if not df[col].between(0, 100).all():
            raise InputSchemaError(f"'{col}' has values outside 0–100.")
    if "ready_for_dispatch_pct" in df.columns:
        rfd = df["ready_for_dispatch_pct"].dropna()
        if len(rfd) and not rfd.between(0, 100).all():
            raise InputSchemaError("'ready_for_dispatch_pct' has values outside 0–100.")
    bad_status = set(df["status"].astype(str).str.lower().unique()) - VALID_STATUS
    if bad_status:
        raise InputSchemaError(f"'status' must be one of {sorted(VALID_STATUS)}. Found: {bad_status}.")
    bad_plats = set(df["platform"].astype(str).unique()) - {"EZ"}
    if bad_plats:
        raise InputSchemaError(f"'platform' must be 'EZ' for ezCater. Found: {bad_plats}.")
