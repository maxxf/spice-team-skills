# Diagnostic Input CSV Schema

Single source of truth for the unified diagnostic input format. The orchestrator reads every `*.csv` in your `--inputs-dir`, concatenates them, and validates against this schema before any sub-skill runs. Bad input fails fast with a named-column error.

**One row = one `(store, week, platform)` combo.** Multiple stores, multiple weeks, multiple platforms — one row each.

**Empty template:** `references/diagnostic-input-template.csv` (header row only — fill in below it).

---

## Column reference

All 22 columns are required. Order doesn't matter.

| Column | Type | Used by | Source |
|---|---|---|---|
| `store` | string | all | Location name (canonical, matches what shows in weekly reporting) |
| `week` | int | topline | Week number 1–13 (90-day window) |
| `gross_sales` | number | topline | Sum across platforms for the store/week |
| `orders` | int | topline | Total orders for the store/week |
| `net_payout` | number | topline | Net payout for the store/week |
| `menu_cvr_pct` | number | menu | UE menu CVR (impressions → orders), 0–100 |
| `photo_coverage_pct` | number | menu | % of menu items with photos |
| `hero_set` | bool | menu | true / false — hero image present |
| `categories_count` | int | menu | Total menu categories |
| `categories_populated` | int | menu | Categories with ≥1 item |
| `storefront_to_menu_ctr_pct` | number | menu | UE storefront → menu CTR |
| `rating` | number | ops | Platform rating, 0–5 |
| `error_rate_pct` | number | ops | Order error rate, 0–100 |
| `cancellation_pct` | number | ops | Order cancellation rate, 0–100 |
| `uptime_pct` | number | ops | Store uptime, 0–100 |
| `hours_accurate` | bool | ops | true / false — listed hours match actual |
| `platform` | string | campaigns | `UE` / `DD` / `GH` (per-row) |
| `spend` | number | campaigns | Weekly ad spend per row |
| `attributed_sales` | number | campaigns | Attributed sales from ads |
| `roas` | number | campaigns | spend / attributed_sales |
| `incremental_orders_per_week` | number | campaigns | Incremental orders attributable to ads |
| `promo_count_active` | int | campaigns | Active promo count |

---

## Filling from platform exports

Source notes for each column. Where a value isn't available, follow the default rule rather than leaving the cell blank — blanks fail validation.

### Topline (`gross_sales`, `orders`, `net_payout`)
- Pull from your existing **weekly-reporting skill outputs** for the client. The weekly tracker already computes per-store totals across UE / DD / GH. Transcribe per-store, per-week into the unified row.
- If a store wasn't live for a given week, write `0` for sales/orders/payout (don't omit the row).

### Menu (`menu_cvr_pct`, `photo_coverage_pct`, `hero_set`, `categories_count`, `categories_populated`, `storefront_to_menu_ctr_pct`)
- `menu_cvr_pct` and `storefront_to_menu_ctr_pct`: **UE Manager → Menu Performance** (last 30 days, per location). Use the trailing-week value as a proxy when only weekly is available.
- `photo_coverage_pct`: count items with photos / total items in the live menu (manual storefront audit if no platform export).
- `hero_set`: `True` if the location has a non-default hero image set on UE / DD / GH; `False` if any of the three is missing.
- `categories_count` / `categories_populated`: count from the live menu structure. If the menu is identical across platforms, use UE.
- **Default when unavailable:** menu metrics rarely move week-to-week — use the same value across all 13 weeks for a store if you only have a single audit snapshot.

### Ops (`rating`, `error_rate_pct`, `cancellation_pct`, `uptime_pct`, `hours_accurate`)
- `rating`: pull from **UE Manager → Reviews** or **DD Merchant Portal → Reviews**. Use the higher-volume platform's rating if you have to pick one.
- `error_rate_pct` / `cancellation_pct`: **DD Merchant Portal → Operations Quality** for the most reliable source; UE Manager → Performance for backup.
- `uptime_pct`: UE Manager → Performance → Uptime card, or DD's Store Hours adherence metric.
- `hours_accurate`: `True` if listed hours on all three platforms match the client's actual operating hours; `False` if any platform is stale.
- **Default when unavailable:** copy the prior week's value, or use the location average for the window.

### Campaigns (`platform`, `spend`, `attributed_sales`, `roas`, `incremental_orders_per_week`, `promo_count_active`)
- One row per `(store, week, platform)` — so a single store with active campaigns on UE + DD = 2 rows per week.
- `spend` / `attributed_sales` / `roas`: **UE Ads Manager**, **DD Promotions / Ads dashboard**, **GH Sponsored Listings** export.
- `incremental_orders_per_week`: from the platform's incremental attribution view. If unavailable, estimate: `attributed_sales / avg_ticket_size`.
- `promo_count_active`: count of distinct promos live during the week (BOGO, % off, free delivery, etc.).
- **Default when no campaigns ran on a platform that week:** write `0` for spend / attributed_sales / incremental_orders / promo_count_active and `0` for roas (the row still needs to exist if the store is live on that platform).

---

## Validation rules (what will fail you)

The orchestrator's `input_schema.validate()` enforces:

- All 22 columns present (named-column error if any are missing)
- At least 1 row
- `week` in range 1–13
- `rating` in range 0–5
- `platform` in `{UE, DD, GH}`

Anything else (e.g. negative spend, ratings = 0 across the board) flows through to the sub-skills, which surface their own findings. The validator is the floor, not the ceiling.

---

## Example row

```
store,week,gross_sales,orders,net_payout,menu_cvr_pct,photo_coverage_pct,hero_set,categories_count,categories_populated,storefront_to_menu_ctr_pct,rating,error_rate_pct,cancellation_pct,uptime_pct,hours_accurate,platform,spend,attributed_sales,roas,incremental_orders_per_week,promo_count_active
BeverlyHills,1,12000,240,8000,22.0,85,True,6,6,10.0,4.6,1.5,1.0,98.0,True,UE,600,3000,5.0,15,2
```
