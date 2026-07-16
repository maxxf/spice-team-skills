# Unified Input Schema — `unified.csv`

The single intermediate dataset that drives all five analytical passes. Produced by `scripts/build_unified.py` from the platform CSVs in `inputs/`. One row per (location × week).

## Required columns

| Column | Type | Source | Notes |
|---|---|---|---|
| `location_id` | str | derived | slug; stable across the run |
| `location_name` | str | client config | display name |
| `comp_set` | str | client config | e.g. "LA-westside", "NYC-launch-2026" |
| `market` | str | client config | city / DMA |
| `week_starting` | date (YYYY-MM-DD) | derived | Monday of the week |
| `week_index` | int | derived | 1..26 |
| `platform` | str | derived | `ue`, `dd`, `gh`, or `all` (rolled up) — one row per platform per location-week, plus one rolled-up `all` row |
| `gross_sales` | float | platform financials | $ |
| `net_payout` | float | **calculated** (not the platform payout column) | $ = Net Sales − Commissions − Ad Spend − **Other Adjustments** (refunds, error charges, processing/merchant fees). Tax-normalized, comparable across platforms. Feeds `payout_pct`, the routing thresholds, and the CONCENTRATE projection — so adjustments must be netted in here. When sourced from canonical weekly-reporting this is already done; for a raw pull, compute it from the components, don't grab the platform's payout column. |
| `orders` | int | platform financials | count |
| `organic_sales` | float | platform acquisition split | $ (sales attributed to organic discovery) |
| `paid_sales` | float | platform acquisition split | $ (sales attributed to paid placements) |
| `spend` | float | basic ads + advanced ads + merchant-funded offers | $ (total marketing investment; sum all sources). **Must be NET of platform contributions**: exclude platform-co-funded promos AND net ad credits out of ad spend (use `Net Ad Spend`, never `Gross Ad Spend` — Uber/DD/GH credit back a large share). A gross figure roughly doubles spend and halves ROAS; the engine flags any location >60% marketing as a likely un-netted-gross error. Summing ad + offer on one order is correct: two real costs. |
| `spend_gross` | float | *optional* — gross marketing cost | $ BEFORE platform funding (gross ad spend + gross offer discount, i.e. credits and co-funded portions NOT removed). When present, the engine reports ROAS two ways — net (`roas`, on `spend`) and gross (`roas_gross`, on `spend_gross`) — so the deliverable can show efficiency with and without platform funding. Routing still uses net `spend`. Omit if you only have net figures. |
| `attributed_sales` | float | platform ads + offers | $ (platform-attributed; **double-counts** — ads and offers each claim the same order. `analyze.py` caps this at `gross_sales` per row before computing ROAS. Context only; the finding uses the gross-sales counterfactual.) |
| `cancel_rate` | float | platform ops | 0..1 (canceled orders / total) |
| `menu_cvr` | float | platform funnel | 0..1 (orders / menu views) |
| `menu_views` | int | platform funnel | count |
| `new_reviews` | int | platform ratings | count per week |
| `avg_rating` | float | platform ratings | 1..5 |

## Derived columns (added by `analyze.py`, not in unified.csv)

| Column | Formula |
|---|---|
| `roas` | attributed_sales / spend (NaN if spend == 0) |
| `payout_pct` | net_payout / gross_sales |
| `marketing_pct` | spend / gross_sales |
| `organic_share` | organic_sales / (organic_sales + paid_sales) |
| `ratings_velocity` | new_reviews (4-week trailing average) |

## The "all" rollup row

For each (location × week), in addition to per-platform rows, emit one row with `platform = "all"`:
- Additive metrics (`gross_sales`, `net_payout`, `orders`, `organic_sales`, `paid_sales`, `spend`, `attributed_sales`, `menu_views`, `new_reviews`) sum across platforms
- Rates (`cancel_rate`, `menu_cvr`, `avg_rating`) are volume-weighted averages

All five analytical passes operate on `platform = "all"` rows by default. The per-platform rows exist for drill-down in the deliverable.

## Missing data handling

- **Missing platform**: skip rows. Note in `clients/<slug>.json` → `platforms_in_scope`.
- **Missing organic/paid split**: set `organic_sales` and `paid_sales` to NaN; Pass 4 (Mix Shift) suppresses that location's trajectory call.
- **Missing spend**: 0, not NaN. (A week with no campaigns is a real 0.)
- **Missing ops data (cancel_rate, menu_cvr)**: NaN. Pass 1 will not classify the location as BROKEN-OPS without the data — instead surface as "ops data missing" in the per-location card.
- **Missing ratings velocity**: NaN. Same treatment.

## Validation rules (enforced by `validate_inputs.py`)

- ≥4 months continuous data per location in scope (the framework floor)
- No week gaps inside the window (every Monday between window_start and window_end must be present)
- `gross_sales ≥ 0`, `orders ≥ 0`, `spend ≥ 0` on every row
- `payout_pct` between 0 and 1 (a payout >100% signals a sign error in the source CSV)
- Per-platform rows sum to within 0.5% of the `all` rollup row (else log a reconciliation warning)
