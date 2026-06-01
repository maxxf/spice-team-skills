from __future__ import annotations

"""Diagnostic input CSV schema validator.

Single source of truth for the unified diagnostic input shape consumed by all
sub-skills (topline, menu, ops, campaigns). Run by the orchestrator's Phase 1
pre-flight; raises InputSchemaError with actionable messages.
"""

import pandas as pd

REQUIRED_COLUMNS = {
    "store", "week",
    # topline
    "gross_sales", "orders", "net_payout",
    # menu
    "menu_cvr_pct", "photo_coverage_pct", "hero_set",
    "categories_count", "categories_populated", "storefront_to_menu_ctr_pct",
    # ops
    "rating", "error_rate_pct", "cancellation_pct", "uptime_pct", "hours_accurate",
    # campaigns
    "platform", "spend", "attributed_sales", "roas",
    "incremental_orders_per_week", "promo_count_active",
}


class InputSchemaError(ValueError):
    pass


def validate(df: pd.DataFrame) -> None:
    """Raise InputSchemaError with actionable message if df is malformed."""
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise InputSchemaError(
            f"Diagnostic input CSV is missing required columns: {sorted(missing)}. "
            f"See references/input-csv-schema.md for the full schema. "
            f"Found columns: {sorted(df.columns)}"
        )
    if df.empty:
        raise InputSchemaError("Diagnostic input CSV has no rows. Need at least 1 store × 1 week × 1 platform.")
    # Spot-check a few hard requirements
    if not df["week"].between(1, 13).all():
        raise InputSchemaError("'week' column must be integers 1–13 (90-day window = 13 weeks).")
    if not df["rating"].between(0, 5).all():
        raise InputSchemaError(f"'rating' column has values outside 0–5: min={df['rating'].min()}, max={df['rating'].max()}")
    valid_platforms = {"UE", "DD", "GH"}
    bad_plats = set(df["platform"].unique()) - valid_platforms
    if bad_plats:
        raise InputSchemaError(f"'platform' column has invalid values: {bad_plats}. Must be UE / DD / GH.")
