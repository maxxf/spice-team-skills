# Uber Eats Weekly Performance Extraction Agent

Extract weekly performance metrics (Monday-Sunday) from Uber Eats exports using
**Conservative Attribution + Net Ads With Credits** methodology.

## Input Files

1. **Transaction CSV** - UE payment/settlement export (order-level rows) — ALWAYS REQUIRED. Source for all metrics, offer attribution, ad spend totals, and payout.
2. **Offers Export** - Campaign-level offer redemptions (supplementary detail). Optional — warn but continue if missing.
3. **Ads Manager Export** - Campaign Summary by Location performance report, date-filtered to reporting week. OPTIONAL — only available for clients with `UE Ads Manager Access = Yes` in the client registry. Enhances ad attribution when provided.

**Not all clients have Ads Manager access.** When missing, the report runs on offer-only attribution (Tier 1). This is production-ready, not a gap to block on.

---

## Step 0: Load Client Config

**If `OUTPUT/client_profile.json` exists** (written by the orchestrator from the client's Notion Weekly Reporting Profile), read it first. Extract: `ue_ads_access` (determines Tier 1 vs Tier 2), UE-specific data quirks (e.g., $0.99 marketing fee active/inactive), and location map. These override the registry values below.

**Otherwise**, check `references/client-registry.md` for `UE Ads Manager Access` and quirks.

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

### Ad-Driven Orders
- **Definition:** Any row where `Other payments description` = "Ad Spend" AND `Other payments` < 0 AND the row has order data (non-zero `Sales (excl. tax)` or a non-blank `Order ID`)
- These are orders where UE attributed ad spend directly to a specific order — the ad cost and the order exist on the same row.
- **Two patterns exist across clients:**
  1. **Per-order ad attribution:** Ad Spend appears on a Completed order row WITH sales, Order ID, etc. That order is ad-driven. (Common for most active-ads clients)
  2. **Standalone spend rows:** Ad Spend appears on rows with blank Order Status, $0 sales, no Order ID. These are daily aggregate ad charges per store — NOT tied to specific orders. (Seen when campaigns are paused or UE isn't attributing per-order)
- **How to handle:** Check ALL rows with "Ad Spend" description. If the row has net_sales > 0 or a non-blank Order ID, it's an ad-attributed order. If it has $0 sales and no Order ID, it's a standalone spend charge (still count toward ad spend, but can't attribute orders without Ads Manager cross-reference).

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

**Check the client registry for `UE Ads Manager Access`.**

### Tier 1: Transaction CSV Only (default)

If `UE Ads Manager Access = No` or `TBD`, or if no Ads Manager export was provided:

- **Marketing-Driven Orders** = offer-driven orders from Step 3 (offer OR per-order ad-attributed)
- **Marketing-Driven Sales** = net sales of those orders
- **Ad Spend** = from transaction CSV netting (Step 4) — counted in Total Marketing Investment
- **No ad-attributed orders/sales added** beyond what's already in the transaction CSV
- Add validation flag: `"UE attribution: Tier 1 (offer-only). Ad spend included in marketing investment but ad-driven orders not attributed. ROAS is conservative."`
- Do NOT warn or block. This is the standard path for most clients.

### Tier 2: Transaction CSV + Ads Manager Export (enhanced)

If `UE Ads Manager Access = Yes` AND an Ads Manager **performance export** is provided (date-filtered, with actual spend/sales/orders data):

- Use it for **campaign-level detail** in the campaigns output (spend, ROAS, impressions, clicks per store)
- Use it for **segment breakdowns** (new vs returning customers, audience types)
- Use Ads Manager attributed orders/sales for the enhanced marketing split (see below)

#### Ads Manager Attribution Logic

Uber's Ads Manager uses view-through attribution — any customer who *saw* a sponsored listing gets counted, even if they later converted via an offer. This means heavy overlap between offer orders and Ads Manager attributed orders.

**Per-store calculation:**
1. Get `offer_orders` from Step 3 (transaction-level offer attribution)
2. Get `ads_attributed_orders` from Ads Manager export (sum of single-store + proportional share of multi-store campaigns)
3. **Overlap = min(offer_orders, ads_attributed_orders)** — assume ALL offer orders were also ad-exposed (conservative: avoids double-counting)
4. **Unique ad orders = max(0, ads_attributed_orders - overlap)**
5. **Combined marketing orders = offer_orders + unique_ad_orders**
6. **Combined marketing sales** = (offer_driven_sales) + (unique_ad_orders × store AOV)

This means: ad orders only add to marketing when Ads Manager claims MORE orders than the offers already captured. If a store has 500 offer orders and 400 Ads Manager orders, unique ad orders = 0 (all ad-attributed orders are already counted via offers).

**Cap:** Combined marketing orders MUST NOT exceed total completed orders. If it does, cap at total and flag.

#### Multi-Store Campaign Distribution

When the Ads Manager `Locations` field shows a count (e.g., "4") instead of a store name:
- Distribute the campaign's orders/sales proportionally by each store's **offer order count** (not total order count)
- Stores running more offers are more likely targets of multi-store campaigns
- If no stores have offer orders, fall back to total order count distribution
- Flag multi-store campaigns and their distribution in validation

**NOTE:** The Ads Manager **campaign list export** (shows campaign configs, statuses, all-time metrics) is NOT useful for weekly attribution. You need the **performance report filtered to the week's date range.**

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
- Note attribution tier used: Tier 1 (offer-only) or Tier 2 (offer + Ads Manager)
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
