"""Build the unified per-location-per-week dataset from raw platform exports.

Reads CSVs in inputs/<platform>/, normalizes each to the unified schema (see
references/input-csv-schema.md), and writes a single unified.csv.

This is a v0 scaffold. The platform CSV column names vary by export and by
account configuration, so column mapping is config-driven (clients/<slug>.json
→ column_mappings.<platform>). When the auditor runs against a new client, the
GM provides a column mapping the first time, then reuses it.

If column_mappings is empty in the client config, this script reads
references/default_column_mappings.json (TODO: ship this file once we've
validated against a couple of real restaurant exports).

Usage:
    python build_unified.py --client <slug> --inputs-dir <path> --output <path>/unified.csv
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

UNIFIED_COLUMNS = [
    "location_id",
    "location_name",
    "comp_set",
    "market",
    "week_starting",
    "week_index",
    "platform",
    "gross_sales",
    "net_payout",
    "orders",
    "organic_sales",
    "paid_sales",
    "spend",
    "attributed_sales",
    "cancel_rate",
    "menu_cvr",
    "menu_views",
    "new_reviews",
    "avg_rating",
]


@dataclass
class LocationMeta:
    location_id: str
    location_name: str
    comp_set: str
    market: str


def load_client_config(client_slug: str, skill_dir: Path) -> dict:
    config_path = skill_dir / "clients" / f"{client_slug}.json"
    if not config_path.exists():
        raise FileNotFoundError(f"No client config at {config_path}")
    return json.loads(config_path.read_text())


def load_locations(config: dict) -> dict[str, LocationMeta]:
    out: dict[str, LocationMeta] = {}
    for loc in config.get("locations", []):
        meta = LocationMeta(
            location_id=loc["location_id"],
            location_name=loc.get("location_name", loc["location_id"]),
            comp_set=loc.get("comp_set", "default"),
            market=loc.get("market", "unknown"),
        )
        out[meta.location_id] = meta
        # also allow lookup by display name
        out[meta.location_name.lower()] = meta
    return out


def monday_of(d: date | datetime) -> date:
    if isinstance(d, datetime):
        d = d.date()
    return d - timedelta(days=d.weekday())


def read_platform_files(
    platform: str, inputs_dir: Path, mapping: dict
) -> pd.DataFrame:
    """Read all CSVs for a platform, apply column mapping, return long-format rows.

    Returns a dataframe with the unified columns for this platform. Missing
    metrics get NaN.

    The mapping dict has shape:
        {
            "financials": {"file_hint": ["financial"], "columns": {"gross_sales": "Gross Sales", ...}},
            "ads": {...},
            ...
        }
    """
    subdir = inputs_dir / platform
    if not subdir.is_dir():
        return pd.DataFrame(columns=UNIFIED_COLUMNS)

    files = [f for f in subdir.iterdir() if f.is_file() and f.suffix.lower() in (".csv", ".xlsx")]
    out = pd.DataFrame(columns=UNIFIED_COLUMNS)

    for category, cfg in mapping.items():
        hits = cfg.get("file_hint", [])
        matched = next(
            (f for f in files if any(h in f.name.lower() for h in hits)),
            None,
        )
        if matched is None:
            print(f"  [warn] {platform}/{category}: no matching file found", file=sys.stderr)
            continue
        try:
            if matched.suffix == ".xlsx":
                df = pd.read_excel(matched)
            else:
                df = pd.read_csv(matched, skiprows=cfg.get("skiprows", 0))
        except Exception as e:
            print(f"  [warn] failed to read {matched}: {e}", file=sys.stderr)
            continue

        # Apply column rename per mapping
        rename = {v: k for k, v in cfg.get("columns", {}).items() if v in df.columns}
        df = df.rename(columns=rename)

        # Normalize the week column
        if "week_starting" in df.columns:
            df["week_starting"] = pd.to_datetime(df["week_starting"]).dt.date
            df["week_starting"] = df["week_starting"].apply(monday_of)

        # Tag the platform and category
        df["platform"] = platform
        df["_source_category"] = category

        # Keep only columns we know about; pad missing ones with NaN
        for col in UNIFIED_COLUMNS:
            if col not in df.columns:
                df[col] = pd.NA

        out = pd.concat([out, df[UNIFIED_COLUMNS + ["_source_category"]]], ignore_index=True)

    return out


def collapse_to_location_week(df: pd.DataFrame) -> pd.DataFrame:
    """For each (location × week × platform), sum additive metrics across source
    categories (financials + ads + offers within one platform all contribute).
    """
    if df.empty:
        return df
    additive = ["gross_sales", "net_payout", "orders", "organic_sales", "paid_sales",
                "spend", "attributed_sales", "menu_views", "new_reviews"]
    rate = ["cancel_rate", "menu_cvr", "avg_rating"]
    meta = ["location_name", "comp_set", "market"]

    key = ["location_id", "week_starting", "platform"]
    agg = {c: "sum" for c in additive if c in df.columns}
    for c in rate:
        if c in df.columns:
            agg[c] = "mean"
    for c in meta:
        if c in df.columns:
            agg[c] = "first"

    return df.groupby(key, as_index=False).agg(agg)


def build_all_rollup(df: pd.DataFrame) -> pd.DataFrame:
    """Add platform=='all' rows that sum additive metrics across platforms."""
    if df.empty:
        return df
    additive = ["gross_sales", "net_payout", "orders", "organic_sales", "paid_sales",
                "spend", "attributed_sales", "menu_views", "new_reviews"]
    # Volume-weighted averages for rates
    df_copy = df.copy()
    df_copy["_orders_w"] = df_copy["orders"].fillna(0)

    grp = df.groupby(["location_id", "week_starting"], as_index=False)
    additive_sum = grp[additive].sum(min_count=1)

    # Rate weighted-avg
    def _wmean(col: str):
        def _f(sub: pd.DataFrame):
            if sub["orders"].sum() == 0:
                return sub[col].mean()
            return (sub[col].fillna(0) * sub["orders"].fillna(0)).sum() / sub["orders"].fillna(0).sum()
        return _f

    rate_rows = []
    for (loc, wk), sub in df.groupby(["location_id", "week_starting"]):
        row = {"location_id": loc, "week_starting": wk}
        for c in ["cancel_rate", "menu_cvr", "avg_rating"]:
            row[c] = _wmean(c)(sub) if c in sub.columns else pd.NA
        for c in ["location_name", "comp_set", "market"]:
            if c in sub.columns:
                row[c] = sub[c].iloc[0]
        rate_rows.append(row)

    rate_df = pd.DataFrame(rate_rows)
    rollup = additive_sum.merge(rate_df, on=["location_id", "week_starting"], how="left")
    rollup["platform"] = "all"
    return rollup


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", required=True)
    parser.add_argument("--inputs-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parent.parent
    config = load_client_config(args.client, skill_dir)

    locations = load_locations(config)
    if not locations:
        print(
            "No locations defined in clients/<slug>.json. Fill in the `locations` array "
            "(see clients/_template.json) before re-running.",
            file=sys.stderr,
        )
        return 1

    column_mappings = config.get("column_mappings", {})
    platforms = config.get("platforms_in_scope", ["ue", "dd", "gh"])

    frames = []
    for platform in platforms:
        mapping = column_mappings.get(platform, {})
        if not mapping:
            print(
                f"  [warn] no column_mappings defined for {platform} in client config. "
                f"This run will skip {platform}.",
                file=sys.stderr,
            )
            continue
        df = read_platform_files(platform, args.inputs_dir, mapping)
        df = collapse_to_location_week(df)
        frames.append(df)

    if not frames:
        print("No platform data ingested. Configure column_mappings.", file=sys.stderr)
        return 1

    per_platform = pd.concat(frames, ignore_index=True)

    # Attach location metadata
    def _attach_meta(row):
        meta = locations.get(row.get("location_id")) or locations.get(
            str(row.get("location_name") or "").lower()
        )
        if meta:
            row["location_id"] = meta.location_id
            row["location_name"] = meta.location_name
            row["comp_set"] = meta.comp_set
            row["market"] = meta.market
        return row

    per_platform = per_platform.apply(_attach_meta, axis=1)
    per_platform["week_index"] = (
        pd.to_datetime(per_platform["week_starting"])
        - pd.to_datetime(per_platform["week_starting"]).min()
    ).dt.days // 7 + 1

    rollup = build_all_rollup(per_platform)
    rollup["week_index"] = (
        pd.to_datetime(rollup["week_starting"])
        - pd.to_datetime(rollup["week_starting"]).min()
    ).dt.days // 7 + 1

    unified = pd.concat([per_platform, rollup], ignore_index=True)
    unified = unified[UNIFIED_COLUMNS]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    unified.to_csv(args.output, index=False)
    print(f"Wrote {len(unified):,} rows to {args.output}")
    print(f"  Locations: {unified['location_id'].nunique()}")
    print(f"  Weeks: {unified['week_starting'].nunique()}")
    print(f"  Platforms: {sorted(unified['platform'].unique())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
