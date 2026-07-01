#!/usr/bin/env python3
"""Content-based recognition + routing for campaign platform exports.

The pipeline used to match exports by FILENAME (campaigns_summary_metrics*, marketing_promotion*,
...). That only worked for clients whose files happened to be named that way — everyone else's
exports (UberEats_Ads.csv, Doordash_Promos.csv, ...) matched nothing and silently produced an
empty Sheet. Worse, a file can match a name but be the WRONG export type (UE by-location summary
instead of the per-campaign daily one), which corrupts the numbers.

This module recognizes each CSV by its COLUMN SIGNATURE instead, so naming is irrelevant and
wrong-type files are caught and named. It's the single source of truth for "what export is this?"
— both export_adapters.load_campaign_exports and validate_inputs use it. Self-contained (only csv +
stdlib) so weekly-reporting can import it too.

Signatures are checked most-specific-first. Column matching is case-insensitive exact (so
"Campaign Name" == "Campaign name") but NOT substring (so "Ad spend" != "Ad spend (USD)").
"""
from __future__ import annotations
import csv
import glob
import os

# (key, role, label, must_have_cols, must_NOT_have_cols)
#   role: "ad" | "offer" | None (None = recognized but not a consumable export → wrong-type flag)
SIGNATURES = [
    ("dd_promo", "offer", "DoorDash Promotions",
     ["Campaign name", "Store name", "Type of promotion",
      "Customer discounts from marketing | (Funded by you)"], []),
    ("dd_sl", "ad", "DoorDash Sponsored Listings",
     ["Campaign name", "Store name", "Marketing fees | (including any applicable taxes)", "Impressions"],
     ["Type of promotion"]),
    ("ue_sl", "ad", "Uber Eats Sponsored Listings (per-campaign daily Campaign Summary)",
     ["Campaign name", "Date", "Ad spend"], ["Store name", "Location name", "Offer type"]),
    ("ue_offers", "offer", "Uber Eats Offers",
     ["Offer type", "Sales (USD)"], []),
    # ── recognized-but-WRONG-type (named so we can tell the user exactly what they uploaded) ──
    ("ue_by_location", None, "Uber Eats by-LOCATION summary (need the per-CAMPAIGN daily export instead)",
     ["Location name", "Exposed ROAS"], ["Campaign name"]),
    ("ue_ads_list", None, "Uber Eats ad campaign LIST (need the Offers export instead)",
     ["Campaign UUID", "Ad spend (USD)", "Audience targeted"], []),
]
CONSUMABLE = {"ue_sl", "dd_sl", "ue_offers", "dd_promo"}
SOURCE = {
    "ue_sl": "advertiser.uber.com → Reports → Create report (v2) → Campaign Summary, daily, trailing 7d",
    "dd_sl": "mxportal.doordash.com → Marketing → Sponsored Listings → Performance Export, trailing 7d",
    "ue_offers": "merchants.ubereats.com → Marketing → Offers → Export, trailing 7d",
    "dd_promo": "mxportal.doordash.com → Marketing → Promotions → Performance Export, trailing 7d",
}


def _cols(path) -> list:
    try:
        with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
            return next(csv.reader(f), [])
    except Exception:
        return []


def recognize(path):
    """Return (key, role, label) for a CSV by its columns, or (None, None, None) if unrecognized."""
    have = {c.strip().lower() for c in _cols(path)}
    for key, role, label, must, mustnot in SIGNATURES:
        if all(c.lower() in have for c in must) and not any(c.lower() in have for c in mustnot):
            return key, role, label
    return None, None, None


def route(inputs_dir: str):
    """Scan a dir of CSVs → ({consumable_key: [paths]}, [problem strings]).
    Problems = wrong-type files and unrecognized files, each with an actionable message."""
    matched, problems = {}, []
    for p in sorted(glob.glob(os.path.join(inputs_dir, "*.csv"))):
        name = os.path.basename(p)
        key, role, label = recognize(p)
        if key in CONSUMABLE:
            matched.setdefault(key, []).append(p)
        elif key is not None:  # recognized but wrong type
            problems.append(f"{name}: looks like the {label} — not a consumable campaign export. Skipped.")
        else:
            problems.append(f"{name}: unrecognized export (no known column signature). Skipped — "
                            f"map it or drop the right file.")
    return matched, problems
