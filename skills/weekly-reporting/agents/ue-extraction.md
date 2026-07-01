# Uber Eats Weekly Performance Extraction Agent

> ⚠️ **TAX EXCLUSION — READ FIRST**
>
> **Total Sales MUST come from `Sales (excl. tax)`. Period.**
>
> Banned columns: `Sales (incl. tax)`, `merchant_total`, `Order Total`, anything with "Total" or "Gross" in the name. These are tax-inclusive and will inflate sales by ~8-10% (CA sales tax).
>
> Detection fingerprint: if Total Sales is mistakenly summed from a tax-inclusive column, you'll see `commissions_pct < 27%` and AOV jump above benchmark with no business cause. The validator catches both — but use the right column the first time.
>
> Root cause of the May 2026 goop Kitchen incident (3 weeks of inflated reports): summing the wrong column for Total Sales.

Extract weekly performance metrics (Monday-Sunday) from Uber Eats exports using
**Conservative Attribution + Net Ads With Credits** methodology.

## Input Files

1. **Transaction CSV** - UE payment/settlement export (order-level rows) — ALWAYS REQUIRED. Source for all metrics, offer attribution, ad spend totals, and payout.
2. **Offers Export** - Campaign-level offer redemptions (supplementary detail). Optional — warn but continue if missing.
3. **Ads Manager Export** - Campaign Summary by Location performance report, date-filtered to reporting week. OPTIONAL — only available for clients with `UE Ads Manager Access = Yes` in the client registry. Enhances ad attribution when provided.

**Not all clients have Ads Manager access.** When missing, the report runs on offer-only attribution (Tier 1). This is production-ready, not a gap to block on.

---

## Step 0: Load Client Config

**If `OUTPUT/client_profile.json` exists** (written by the orchestrator from the client's Notion Weekly Reporting Profile), read it first. Extract: `ue_attribution_tier` (1 or 2, **default 2** if unset — controls ad attribution, see Step 3b), `ue_ads_access`, UE-specific data quirks (e.g., $0.99 marketing fee active/inactive), and location map. These override the registry values below.

**Otherwise**, check `references/client-registry.md` for `UE Attribution Tier`, `UE Ads Manager Access`, and quirks.

> **Tier is explicit, not inferred.** Default 2. Set Tier 1 ONLY for clients with no UE ad program — never based on whether an export happens to be present this week.

---

## Critical Rule

Only include **COMPLETED** orders in all sales and order calculations.

**Include:** `Order Status = "Completed"`
**Exclude:** Cancelled, Unfulfilled, Refund, Refund Disputed

---

## Step 1: Identify Files & Week

- Confirm which files the user has provided
- Confirm the week date range (Monday-Sunday)
- Filter all transaction rows to only those where `Order Date` falls within the specified Mon-Sun window
- Identify the gross sales column for Net Payout % calculation (see Step 2)

---

## Step 2: Extract Data from Transaction CSV

### Column Identification

Find these columns (check for common variants):
- **Store/Location:** `Store Name`, `Restaurant Name`, `Store`, `Location`
- **Order Status:** `Order Status`, `Status`
- **Order Date:** `Order Date`, `Date`, `Transaction Date`
- **Total Sales:** `Sales (excl. tax)`, `Net Sales`, `Subtotal` — food subtotal excl tax. This is the new top line.
- **Tax (validation only):** `Tax on Sales` — NOT used in reported metrics. For reconciliation only.
- **Marketplace Fee:** `Marketplace Fee` — this is UE's commission. NEW visible metric.
- **Marketplace Fee %:** `Marketplace fee %` — UE's stated commission rate.
- **Delivery Network Fee:** `Delivery Network Fee` — rolls into Other Adjustments.
- **Order Processing Fee:** `Order Processing Fee` — rolls into Other Adjustments.
- **Total Payout:** `Total payout`, `Net Payout`, `Payout` — for VALIDATION only, not reported directly.
- **Marketplace Facilitator Tax:** `Marketplace Facilitator Tax` — for validation only.
- **Offers on items:** `Offers on items (incl. tax)`
- **Delivery Offers:** `Delivery Offer Redemptions (incl. tax)`
- **Other payments:** `Other payments`
- **Other payments description:** `Other payments description`
- **Order Error Adjustments:** `Order Error Adjustments` — rolls into Other Adjustments.

### Order Filtering
- Completed orders only: `Order Status = "Completed"`
- Week filter: `Order Date` within Monday-Sunday of specified week

### Sales Calculation
- **Total Sales:** sum `Sales (excl. tax)` for Completed orders. No "Gross Sales" (tax-inclusive) row.

---

## Step 3: Marketing Attribution (Transaction-Level)

Attribution happens at the **individual order row level** in the transaction CSV. Each Completed order is classified as:

### Offer-Driven Orders
- **Definition:** `Offers on items (incl. tax)` < 0 OR `Delivery Offer Redemptions (incl. tax)` < 0
- **Offer-Driven Sales:** sum `Sales (excl. tax)` for these orders
- **Offer/Discount Value:** sum of abs values: abs(`Offers on items`) + abs(`Delivery Offers`) where each < 0

### Ad-Driven Orders — ⚠️ 2026 CHANGE, READ CAREFULLY
**You cannot identify ad-driven ORDERS from the transaction CSV.** As of Uber's 2026 update (the "W26" change), the per-order `Marketing Adjustment` column is empty and "Ad Spend" appears ONLY on standalone aggregate rows (blank `Order Status`, $0 `Sales`, no `Order ID`) — these are daily ad CHARGES, not order flags. (Verified Jun 2026: `Marketing Adjustment` nonzero on **0 of 300,700** goop orders in 2026, vs 1,313–30,054 in 2025; export headers otherwise identical.)

- The transaction CSV yields **ad SPEND only** (Step 4 netting) — never ad orders.
- Ad-driven **orders and sales come exclusively from the Ads Manager performance export** (Tier 2 — Step 3b).
- Do **not** mark any transaction row as ad-driven and do **not** infer ad orders from "Ad Spend" rows. Offer attribution (above) is unaffected and remains per-order.

### Combined Marketing Attribution
- **Marketing-Driven Orders:** Orders that are offer-driven OR ad-driven (count once if both — no double-counting)
- **Marketing-Driven Sales:** Net sales of those orders
- **Organic Orders:** Total Orders - Marketing-Driven Orders
- **Organic Sales:** Total Sales (Net) - Marketing-Driven Sales

### $0.99 Marketing Fee (CLIENT-DEPENDENT)
UE charges some clients a **$0.99 marketing fee per offer redemption**. Check for this:
- Look for rows where `Other payments description` contains "marketing" or "promo" AND `Other payments` = -0.99
- Also check if `Marketing Adjustment` column exists and has non-zero values
- If found: this is an OFFER cost, NOT ad spend. Add to Offers/Discounts total, NOT to Ad Spend.
- If not found (e.g., goop Kitchen): note in validation that $0.99 fee is inactive for this client.

---

## Step 3b: Marketing Attribution Summary (Tier Selection)

**Use the explicit `UE Attribution Tier` from Step 0 (default 2). Do NOT infer tier from whether an export happens to be present.**

### Tier 2 — client runs UE ads (default)

Ad-driven orders/sales **must** come from the **UE Ads Manager performance export**, date-filtered to the reporting week (Mon–Sun):
- Source: `placement_v2_<dates>.csv` (per campaign/placement; cols `Date`, `Orders`, `Sales`, `Ad spend`) or `campaigns_summary_metrics_<dates>.csv` (`Orders`, `Sales`, `Ad spend (USD)`, `Locations`, `Audience targeted`).
- ⚠️ **NOT** `ads-campaigns-list*.csv` — that is all-time campaign config/totals and is useless for weekly attribution.
- Per store: `ads_attributed_orders` = Σ `Orders`, `ads_attributed_sales` = Σ `Sales` across that store's campaigns for the week (distribute multi-store campaigns proportionally — see below).
- Also use it for campaign-level detail (spend, ROAS, impressions, clicks) and segment breakdowns (new vs returning, audience types).

**If the performance export is missing — or it yields 0 ad orders while ad spend > 0 — STOP. Do NOT publish offer-only numbers.** Set `ad_attributed_orders = 0` and emit a flag; `validate_report.py` will FAIL the run (BLOCKING). Offer-only output here understates ROAS and overstates CPO, because the 2026 settlement CSV no longer carries ad orders (Step 3). Pull the performance export and re-run.

#### Ads Manager Attribution Logic (Tier 2)

Uber's Ads Manager uses view-through attribution — any customer who *saw* a sponsored listing gets counted, even if they later converted via an offer. This means heavy overlap between offer orders and Ads Manager attributed orders.

**Per-store calculation:**
1. Get `offer_orders` from Step 3 (transaction-level offer attribution)
2. Get `ads_attributed_orders` from Ads Manager export (sum of single-store + proportional share of multi-store campaigns)
3. **Overlap = min(offer_orders, ads_attributed_orders)** — assume ALL offer orders were also ad-exposed (conservative: avoids double-counting)
4. **Unique ad orders = max(0, ads_attributed_orders - overlap)**
5. **Combined marketing orders = offer_orders + unique_ad_orders**
6. **Combined marketing sales** = (offer_driven_sales) + (unique_ad_orders × store AOV)
7. **Record `ad_attributed_orders` = Σ unique_ad_orders and `ad_attributed_sales` = Σ (unique_ad_orders × store AOV)** in the output (overview + per location). These are exactly what `validate_report.py`'s ad-attribution gate checks — if ad spend > 0 they must be > 0.

This means: ad orders only add to marketing when Ads Manager claims MORE orders than the offers already captured. If a store has 500 offer orders and 400 Ads Manager orders, unique ad orders = 0 (all ad-attributed orders are already counted via offers).

**Cap:** Combined marketing orders MUST NOT exceed total completed orders. If it does, cap at total and flag.

#### Multi-Store Campaign Distribution

When the Ads Manager `Locations` field shows a count (e.g., "4") instead of a store name:
- Distribute the campaign's orders/sales proportionally by each store's **offer order count** (not total order count)
- Stores running more offers are more likely targets of multi-store campaigns
- If no stores have offer orders, fall back to total order count distribution
- Flag multi-store campaigns and their distribution in validation

**NOTE:** The Ads Manager **campaign list export** (shows campaign configs, statuses, all-time metrics) is NOT useful for weekly attribution. You need the **performance report filtered to the week's date range.**

### Tier 1 — client does NOT run UE ads (set explicitly)

- Offer-only attribution. `ad_attributed_orders = 0`, `ad_attributed_sales = 0`.
- If an Ads Manager export is present, use it for campaign detail only.
- **Sanity flag:** if `ad_spend > 0` for a Tier-1 client, emit a flag — config says no ads but spend exists (misconfigured tier, or ads running unattributed). `validate_report.py` treats UE `ad_spend > 0` with 0 ad-attributed orders as BLOCKING regardless of tier, so either correct the tier or supply the performance export.

---

## Step 4: Ads + Credits Netting (from Transaction CSV)

Ad/credit data lives in `Other payments description` (label) and `Other payments` (amount). These rows typically have **blank Order Status**.

**Ad-Related Row Definition:** treat a row as ad-related if:
- `Other payments description` contains "Ad" (case-insensitive), OR
- `Other payments description` equals "Customer contribution"

**EXCLUDE from ad spend:** $0.99 marketing fees (see Step 3 above).

**Ad Metrics (ALWAYS from transaction CSV, never from Ads Manager):**
- **Gross Ad Spend:** sum abs(`Other payments`) where description == `"Ad Spend"`
- **Ad Credits / Offsets:** sum of positive `Other payments` among ad-related rows where description != `"Ad Spend"`
- **Net Ad Spend Impact (Payout Impact):** sum of signed `Other payments` among ad-related rows (typically negative)
- **Net Ad Spend (Cost):** abs(Net Ad Spend Impact)

**IMPORTANT:** Ad Spend for the tracker/overview MUST come from transaction CSV netting, NOT from Ads Manager totals. Ads Manager reports spend using different attribution windows and may include spend from outside the Mon-Sun reporting period. The transaction CSV reflects actual charges to the merchant's account for the week.

---

## Step 5: Process Offers Export (Campaign Data)

Read the Offers export CSV:
- Group by store/location
- Extract: Redemptions (= order count)
- Spend shows as `--*` (percentage only, no dollar amount in export)
- ROAS shows as `--` (not calculable without spend)

Add to campaigns output as:
- Platform: "Uber Eats"
- Campaign Type: "Offers"
- Location: store name or "All"
- Spend: null (display as "--*")
- Orders: redemptions count
- Sales: attributed sales if available
- ROAS: null (display as "--")

---

## Step 6: Commission, Fees & Net Payout

### Commission Extraction (NEW)
**Commissions:** Sum abs(`Marketplace Fee`) across ALL completed Marketplace orders. This is UE's take rate.
**Commissions %:** Commissions / Total Sales * 100.

### Other Adjustments
Sum of abs(`Delivery Network Fee`) + abs(`Order Processing Fee`) + abs(`Order Error Adjustments`) across ALL Marketplace rows. Report as a single net number.

### Net Payout (Calculated)
**Net Payout = Net Sales - Commissions - Ad Spend - Other Adjustments.** Calculated from components. Do NOT use the `Total payout` column directly.

**Net Sales** = Total Sales - Discounts (Offer/Discount Value from Step 3/4).

### Net Payout Validation
Sum `Total payout` across ALL rows/statuses for the week. Since UE already deducts MF Tax from its payout column, this should approximate the calculated Net Payout. Flag if discrepancy > 2%.

CRITICAL: Each store MUST have its own commissions, other_adjustments, and net_payout computed from ALL rows matching that store name.

---

## Step 7: Key Calculations

| Metric | Formula |
|--------|---------|
| Total Sales | Sum `Sales (excl. tax)` (Completed orders) |
| Discounts | Offer/Discount Value (from Step 3/4) |
| Net Sales | Total Sales - Discounts |
| Commissions | Sum abs(`Marketplace Fee`) (all Marketplace rows) |
| Commissions % | Commissions / Total Sales * 100 |
| Ad Spend | Net Ad Spend (Cost) from transaction netting |
| Other Adjustments | Delivery Network Fee + Processing Fee + Error Adjustments |
| Net Payout | Net Sales - Commissions - Ad Spend - Other Adjustments |
| Net Payout % | Net Payout / Total Sales * 100 |
| Marketing Driven Sales | Sum of net sales for marketing-driven orders (offer OR ad) |
| Organic Sales | Total Sales - Marketing Driven Sales |
| Total Orders | Count of Completed orders |
| Orders from Marketing | Count of marketing-driven orders (offer OR ad, no double-count) |
| Organic Orders | Total Orders - Orders from Marketing |
| AOV | Total Sales / Total Orders |
| Total Marketing Investment | Ad Spend + Discounts |
| Marketing ROAS | Marketing Driven Sales / Total Marketing Investment |

---

## Step 8: Validation

Before outputting results, confirm:
- Marketing Driven Sales + Organic Sales = Total Sales (Net) within $1
- Orders from Marketing + Organic Orders = Total Orders exactly
- Net Payout % is reasonable (typically 50-90% range; flag if outside)
- Note attribution tier used: Tier 1 (offer-only, non-ads client) or Tier 2 (offer + Ads Manager)
- **Ad-attribution gate (BLOCKING):** if UE `ad_spend > 0` and `ad_attributed_orders = 0`, the report is INVALID — do NOT publish. Supply the Ads Manager performance export and re-run. `validate_report.py` enforces this.
- Report attribution breakdown: X offer orders, Y ad orders (if Tier 2), Z overlap (if Tier 2)
- Flag $0.99 marketing fee status (active/inactive for this client)
- Flag any anomalies: unusually large credits/offsets, net ad spend flipping positive, etc.

---

## Step 9: Output

Write standardized JSON to `OUTPUT/ue_results.json`:

```json
{
  "platform": "uber_eats",
  "week_start": "YYYY-MM-DD",
  "week_end": "YYYY-MM-DD",
  "overview": {
    "total_sales": 0.00,
    "discounts": 0.00,
    "net_sales": 0.00,
    "commissions": 0.00,
    "commissions_pct": 0.00,
    "ad_spend": 0.00,
    "other_adjustments": 0.00,
    "net_payout": 0.00,
    "net_payout_pct": 0.00,
    "marketing_driven_sales": 0.00,
    "organic_sales": 0.00,
    "total_orders": 0,
    "orders_from_marketing": 0,
    "ad_attributed_orders": 0,
    "ad_attributed_sales": 0.00,
    "ue_attribution_tier": 2,
    "organic_orders": 0,
    "aov": 0.00,
    "total_marketing_investment": 0.00,
    "marketing_credits": 0.00,
    "marketing_investment_pct": 0.00,
    "marketing_roas": 0.00,
    "marketing_cpo": 0.00,
    "platform_payout_column": 0.00,
    "platform_mf_tax": 0.00
  },
  "by_location": [],
  "campaigns": [],
  "validation": {
    "sales_check": true,
    "orders_check": true,
    "flags": []
  }
}
```

Populate `by_location` with the same metrics **per store**. **CRITICAL: Each store MUST include `total_sales`, `discounts`, `net_sales`, `commissions`, `commissions_pct`, `other_adjustments`, `net_payout`, and `net_payout_pct`.** For each store:
- `total_sales` = sum of `Sales (excl. tax)` for that store (Completed orders)
- `commissions` = sum of abs(`Marketplace Fee`) for that store (all rows)
- `net_payout` = net_sales - commissions - ad_spend - other_adjustments
- `net_payout_pct` = net_payout / total_sales * 100
- Also include `platform_payout_column` (sum of `Total payout`) and `platform_mf_tax` (sum of `Marketplace Facilitator Tax`) per store for validation.

Do NOT leave per-store payout as 0 when the overview has a non-zero total.

Populate `campaigns` with per-store ad summary + Offers export rows + Ads Manager detail (if provided).

---

## Notes

- Settlement files != dashboard data. This report uses transaction/settlement exports which reflect finalized transactions.
- UE Offers spend is percentage-only in the export; dollar amount is not available.
- Ad Spend rows in the transaction CSV typically have blank Order Status — they are daily charge line items, not per-order flags. This is standard UE behavior.
- **Tier 1 (offer-only)** is the default for clients without Ads Manager access. Ad spend is counted in marketing investment but orders/sales are offer-attributed only. This is conservative and production-ready.
- **Tier 2 (offer + Ads Manager)** adds ad-attributed orders via cross-reference. Only available when client has `UE Ads Manager Access = Yes` in the registry AND provides the performance export.
- All monetary values in JSON should be raw numbers (no formatting). Formatting is applied by the aggregation script.
