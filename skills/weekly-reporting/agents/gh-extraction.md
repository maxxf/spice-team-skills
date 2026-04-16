# Grubhub Weekly Performance Extraction Agent

Extract weekly performance metrics (Monday-Sunday) from a Grubhub CSV export using
**Conservative Attribution** methodology.

## Required Input Files

1. **Settlement CSV** - Grubhub/Seamless settlement report (order-level rows)

---

## Step 0: Load Client Config

**If `OUTPUT/client_profile.json` exists** (written by the orchestrator from the client's Notion Weekly Reporting Profile), read it first. Extract: `gh_excluded_locations`, GH-specific data quirks, and location map. These override the registry values below.

**Otherwise**, check `references/client-registry.md` for client-specific config.

## Critical Filters

- Only completed Marketplace orders in sales/order calculations (except Net Payout which uses all statuses)
- Apply client-specific store exclusions from the profile or `references/client-registry.md` (e.g., exclude Wing Zone for Capriotti's)

---

## Step 1: Identify File & Week

- Confirm the Grubhub CSV provided
- Confirm the week date range (Monday-Sunday)
- Filter by `order_date` to the specified week
- Apply `transaction_type` filter for completed orders (typically "Order" or similar — check actual values)
- Apply any client-specific store exclusions from the registry

### Column Identification

- **Store/Location:** `store_name`
- **City:** `city` (useful for location disambiguation)
- **Address:** `street_address` (useful for location disambiguation)
- **Transaction type:** `transaction_type` — use to identify completed vs refunds/adjustments
- **Order Date:** `order_date`
- **Total Sales:** `subtotal` — food subtotal excl tax. This is the new top line.
- **Tax (validation only):** `subtotal_sales_tax` — NOT used in reported metrics. For reconciliation.
- **merchant_total:** `merchant_total` — tax-inclusive total. For validation only (should ≈ subtotal + tax).
- **Platform payout (validation only):** `merchant_net_total` — for validation, not reported directly.
- **Commission:** `commission` — platform commission. NEW visible metric.
- **Delivery Commission:** `delivery_commission` — delivery commission. Combined with `commission` for total Commissions.
- **Processing Fee:** `processing_fee` — rolls into Other Adjustments.
- **Withheld Tax:** `withheld_tax` — backup withholding. Rolls into Other Adjustments.
- **Merchant funded promotion:** `merchant_funded_promotion`
- **Merchant funded loyalty:** `merchant_funded_loyalty`

---

## Step 2: Extract Metrics

### Order Filtering
- Count only completed orders (check `transaction_type` values — typically "Order" rows with positive subtotal)
- Exclude refunds, adjustments, cancellations, credits from order/sales counts

### Sales Calculation

**Total Sales:** Sum `subtotal` for completed orders. No "Gross Sales" (tax-inclusive) row.

**Discounts:** Sum of merchant-funded discount amounts (see Marketing Investment Components below).

**Net Sales:** Total Sales - Discounts.

**Marketing Driven Sales:** Sum `subtotal` for completed orders that are marketing-driven (see Attribution below).

**Organic Sales:** Total Sales - Marketing Driven Sales.

### Commission & Fees Extraction (NEW)

**Commissions:** Sum abs(`commission`) + abs(`delivery_commission`) for ALL rows (all transaction types). This is GH's total take rate.

**Commissions %:** Commissions / Total Sales * 100.

**Other Adjustments:** Sum of abs(`processing_fee`) + abs(`withheld_tax`) for ALL rows. Report as a single net number.

### Marketing Attribution

An order is **Marketing-Driven** if it has ANY of:
- `merchant_funded_promotion` < 0 or != 0
- `merchant_funded_loyalty` < 0 or != 0

> If `merchant_funded_promotion` and `merchant_funded_loyalty` are both $0 across all rows for the period, the client ran no merchant-funded promos. Marketing Driven Sales, ROAS, and CPO should all be null — this is correct, not a data gap.

**Organic:** All other completed orders without any of the above.

### Marketing Investment Components

**Ad Spend:** NOT present in the Grubhub transaction settlement CSV. Grubhub ad spend must be sourced from a separate invoicing/ads report. Leave Ad Spend as $0 if no separate report is available. Do NOT substitute commission fields for ad spend.

**Offer/Discount Value:**
Sum absolute value of:
- `merchant_funded_promotion` where != 0
- `merchant_funded_loyalty` where != 0

**Total Marketing Investment:** Ad Spend ($0 unless separate report) + Offer/Discount Value

### Net Payout (Calculated)
**Net Payout = Net Sales - Commissions - Ad Spend - Other Adjustments.** Calculated from components, NOT from `merchant_net_total`. This strips out sales tax and makes GH comparable to UE and DD.

### Net Payout Validation
Sum `merchant_net_total` across ALL transaction types. Then subtract Sum `subtotal_sales_tax` for the same rows. The result should approximate the calculated Net Payout (within 2%). Flag if it doesn't.

### Net Payout %
**Net Payout %** = Net Payout / Total Sales (`subtotal`, excl tax).

---

## Step 3: Key Calculations

| Metric | Formula |
|--------|---------|
| Total Sales | Sum `subtotal` (completed orders) |
| Discounts | Sum merchant-funded promos/loyalty |
| Net Sales | Total Sales - Discounts |
| Commissions | Sum abs(`commission` + `delivery_commission`) (all rows) |
| Commissions % | Commissions / Total Sales * 100 |
| Other Adjustments | Sum abs(`processing_fee` + `withheld_tax`) |
| Ad Spend | $0 unless separate ad report provided |
| Net Payout | Net Sales - Commissions - Ad Spend - Other Adjustments |
| Net Payout % | Net Payout / Total Sales * 100 |
| AOV | Total Sales / Total Orders |
| Marketing ROAS | Marketing Driven Sales / Total Marketing Investment (null if $0 spend) |

---

## Step 4: Validation

- Marketing Driven Sales + Organic Sales = Total Sales (Net) within $1
- Orders from Marketing + Organic Orders = Total Orders exactly
- Net Payout % should be in 50-90% range (flag if outside)
- If marketing spend = $0 for all stores, note that GH marketing is inactive
- ROAS/CPO should show as null (not #DIV/0!) when marketing spend = $0

---

## Step 5: Output

Write standardized JSON to `OUTPUT/gh_results.json`:

```json
{
  "platform": "grubhub",
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
    "organic_orders": 0,
    "aov": 0.00,
    "total_marketing_investment": 0.00,
    "marketing_investment_pct": 0.00,
    "marketing_roas": null,
    "marketing_cpo": null,
    "platform_payout_column": 0.00,
    "platform_tax_passed": 0.00
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

Populate `by_location` with the same metrics **per store** (sorted by Total Sales descending). **Each store MUST include `total_sales`, `discounts`, `net_sales`, `commissions`, `commissions_pct`, `other_adjustments`, `net_payout`, and `net_payout_pct`.** Also include `platform_payout_column` and `platform_tax_passed` per store for validation.

Use `store_name` as the location key. Include `city` and `street_address` fields in each location entry for disambiguation when building store name mappings.

---

## Notes

- Settlement data may differ from real-time dashboard figures.
- `merchant_net_total` is the platform payout column. Used for VALIDATION only, not reported directly.
- `subtotal` is Total Sales (excl tax). No "Gross Sales" (tax-inclusive) row. `merchant_total` kept for validation only.
- **Net Payout is CALCULATED** (Net Sales - Commissions - Ad Spend - Other Adjustments), not from `merchant_net_total`.
- When GH marketing is inactive ($0 spend), ROAS and CPO should be null (not #DIV/0!).
- Ad Spend is NOT in the settlement CSV — do not confuse commission with ad spend.
- All monetary values in JSON should be raw numbers (no formatting).
