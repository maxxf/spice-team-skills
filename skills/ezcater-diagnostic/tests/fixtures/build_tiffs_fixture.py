#!/usr/bin/env python3
"""Deterministically build the Tiff's Treats regression fixture CSV (v0.2).

Reproduces the ezCater audit + live-portal distribution (Jun 2026) at 175 stores:
  175 total → 106 active → 31 volume-eligible → 16 pass-goals(excl tracking) → 0 badged
  · 69 dark (0 orders) · 75 volume-locked (1–5 orders)
  · of the 31 eligible: 16 pass all badge goals except delivery tracking, 11 fail on-time, 4 fail rejection
  · self-delivery → delivery_tracking 0% everywhere (the badge blocker)
  · 2 PAUSED stores: H4 Westchase (cancellation 11.1%), H14 Cypress (on-time 60%)
  · D19 Kessler Park at-risk (on-time 94% + accuracy 96.3%)
  · every store: $0 PPP / ezRewards / sponsored (promo engine off)

Run:  python3 build_tiffs_fixture.py   → writes tiffs_treats.csv next to this file.
"""
from __future__ import annotations

import csv
from pathlib import Path

COLUMNS = [
    "store", "month", "platform", "status", "gross_sales", "orders",
    "on_time_pct", "on_time_acceptance_pct", "rejection_rate_pct", "order_accuracy_pct",
    "cancellation_pct", "delivery_tracking_pct", "ready_for_dispatch_pct",
    "rating", "review_count", "ppp_bid_pct", "ezrewards_pct",
    "sponsored_spend", "sponsored_attributed_sales", "promo_count_active", "packaging_complete",
]

# Healthy baseline: clean metrics, self-delivery (0% tracking), promo engine off.
HEALTHY = dict(
    status="active", on_time_pct=99.0, on_time_acceptance_pct=99.0, rejection_rate_pct=0.0,
    order_accuracy_pct=99.5, cancellation_pct=0.0, delivery_tracking_pct=0.0, ready_for_dispatch_pct="",
    rating=4.9, review_count=12, ppp_bid_pct=0.0, ezrewards_pct=0.0,
    sponsored_spend=0.0, sponsored_attributed_sales=0.0, promo_count_active=0, packaging_complete=1.0,
)


def row(store, *, orders, gross_sales, review_count=None, **overrides):
    r = {"store": store, "month": 1, "platform": "EZ", "orders": orders, "gross_sales": gross_sales}
    r.update(HEALTHY)
    if review_count is not None:
        r["review_count"] = review_count
    r.update(overrides)
    return r


def build_rows() -> list[dict]:
    rows: list[dict] = []

    # 69 dark stores — 0 orders, no reviews
    for i in range(69):
        rows.append(row(f"DARK-{i+1:02d}", orders=0, gross_sales=0.0, review_count=0))

    # 75 volume-locked — 1–5 orders, healthy, under the review/volume gate
    for i in range(75):
        rows.append(row(f"LOCKED-{i+1:02d}", orders=3, gross_sales=590.0, review_count=4))

    # 16 pass-goals-except-tracking eligible — clean, not badged (tracking 0%)
    for i in range(16):
        rows.append(row(f"PASS-{i+1:02d}", orders=10, gross_sales=2000.0))

    # 8 on-time-watch eligible (95–98.5 band) — at risk, otherwise clean
    for i in range(8):
        rows.append(row(f"ONTIME-W-{i+1:02d}", orders=10, gross_sales=2000.0, on_time_pct=97.0, status="at_risk"))

    # 3 problem children
    rows.append(row("H14 Cypress", orders=8, gross_sales=1600.0, on_time_pct=60.0, status="paused"))
    rows.append(row("D19 Kessler Park", orders=32, gross_sales=2640.0, on_time_pct=94.0, order_accuracy_pct=96.3, status="at_risk"))
    rows.append(row("H4 Westchase", orders=20, gross_sales=2715.0, cancellation_pct=11.1, on_time_acceptance_pct=85.7, status="paused"))

    # 4 rejection-misconfig eligible (0.5–2 band) — at risk, otherwise clean
    for i in range(4):
        rows.append(row(f"REJECT-{i+1:02d}", orders=10, gross_sales=2000.0, rejection_rate_pct=1.0, status="at_risk"))

    return rows


def main() -> None:
    rows = build_rows()
    out = Path(__file__).resolve().parent / "tiffs_treats.csv"
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"wrote {len(rows)} rows → {out}")


if __name__ == "__main__":
    main()
