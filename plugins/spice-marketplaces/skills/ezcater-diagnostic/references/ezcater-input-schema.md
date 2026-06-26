# ezCater Diagnostic — Input CSV Schema

One row per **store × month**. The 90-day window = 3 monthly buckets (`month` 1–3).
Single platform, so `platform` is always `EZ`. Build this unified CSV from the four
browser exports (see `ezcater-export-sop.md`).

This is the catering analog of the delivery 22-column schema. Delivery's menu-funnel
columns (`menu_cvr_pct`, `photo_coverage_pct`, `storefront_to_menu_ctr_pct`,
`categories_*`, `hero_set`) are **dropped** — catering has no browse funnel. They're
replaced by `packaging_complete` and the visibility-lever columns.

## Required columns

| Column | Type | Source export | Notes |
|---|---|---|---|
| `store` | str | all | Store name/ID, stable across exports |
| `month` | int 1–3 | derived | Monthly bucket within the 90-day window |
| `platform` | str | — | Always `EZ` |
| `status` | str | Operational Metrics | `active` / `at_risk` / `paused` — paused = zero orders (P0) |
| `gross_sales` | float | Finance / 30-day sales | Catering sales for the bucket |
| `orders` | int | 30-day sales / ops | Order count for the bucket |
| `on_time_pct` | float 0–100 | Operational Metrics | % delivered inside the 15-min window |
| `on_time_acceptance_pct` | float 0–100 | Operational Metrics | % orders accepted within 15 min (distinct from on-time delivery) |
| `rejection_rate_pct` | float 0–100 | Operational Metrics | % orders rejected / not accepted |
| `order_accuracy_pct` | float 0–100 | Operational Metrics | % accurate orders |
| `cancellation_pct` | float 0–100 | Operational Metrics | % cancelled |
| `delivery_tracking_pct` | float 0–100 | Operational Metrics | % orders with delivery status updates — **the badge gate (≥75%)**; self-delivery = 0% |
| `rating` | float 0–5 | Operational Metrics / reviews | Star rating (badge bar = 4.8) |
| `review_count` | int | reviews | Reviews in 90d; badge needs ≥8 |
| `ppp_bid_pct` | float 0–20 | ezManage Rankings | Preferred Partner bid %; 0 = off |
| `ezrewards_pct` | float 0–20 | ezManage ezRewards | Reward %; 0 = off |
| `sponsored_spend` | float | Sponsored Listings | $ spent; 0 = not running |
| `sponsored_attributed_sales` | float | Sponsored Listings | $ attributed; ROAS = this / spend |
| `promo_count_active` | int | ezManage Promotions | Active promo codes/offers |
| `packaging_complete` | float 0–1 | Menu / manual audit | Completeness: per-person pricing, headcount tiers, lead-time packages, required fields |

## Optional columns (pass through when available)

| Column | Type | Notes |
|---|---|---|
| `ready_for_dispatch_pct` | float 0–100 | Pause standard (≥95%); leave blank → N/A for self-delivery |
| `aov` | float | If omitted, computed as `gross_sales / orders` |
| `response_time_min` | float | Avg order response time |
| `badged` | bool/int | Currently carrying the Reliability Rockstar badge; default 0 if unknown |

## Optional portfolio funnel input — `portfolio.json`

The Sales Performance page exposes a portfolio-level funnel + customer mix that the per-store
exports don't. Drop a `portfolio.json` in the inputs dir to light up the Traffic / Conversion /
Re-order radar dims and the `low_conversion_vs_peer` finding:

```json
{
  "search_views": 35674, "menu_views": 2471, "orders": 238,
  "conversion_rate_pct": 9.6, "conversion_benchmark_pct": 10.0,
  "new_customers": 163, "existing_customers": 36, "lapsed_customers": 27
}
```

If absent, those three radar dims render `(pending)` and drop from the overall mean.

## Validation rules (mirrors delivery `input_schema.py`)

- All required columns present; ≥1 row.
- `month` ∈ 1–3.
- `rating` ∈ 0–5; percentage columns ∈ 0–100; `packaging_complete` ∈ 0–1.
- `platform` == `EZ`.
- Multi-month rows per store are aggregated by the scorer (numerics → mean, sales/orders → sum).

## Data gaps

If a column genuinely can't be exported (e.g. `packaging_complete` requires a manual menu
audit), use the framework default and stamp a `data_quality` gap note. Never type a guessed
number — an unmeasurable radar axis renders `(pending)` and drops out of the overall mean.
