---
name: uber-eats-extraction
description: >
  Extract weekly performance metrics from Uber Eats CSV exports for any restaurant chain.
  Use this skill whenever the user uploads or references an Uber Eats CSV/export and wants
  weekly metrics, performance numbers, or data extracted from it. Triggers on: "process Uber Eats
  data", "extract UE metrics", "weekly Uber Eats report", "analyze UE CSV", "pull UE numbers",
  "UE extraction for [client]", or whenever a UE transaction/payment file is dropped in with
  context about weekly reporting, performance, or client metrics. Also trigger when the
  weekly-reporting orchestrator delegates UE extraction. Uses Conservative Attribution with
  Net Ads + Credits methodology.
---

# Uber Eats Weekly Performance Extraction

Extract weekly performance metrics (Monday-Sunday) from an Uber Eats CSV export using **Conservative Attribution + Net Ads With Credits** methodology.

## Critical Rule
Only include **COMPLETED** orders in all sales and order calculations.

**Include:** `Order Status = "Completed"`
**Exclude:** Cancelled, Unfulfilled, Refund, Refund Disputed

## Step 1: Identify the File & Week

- Confirm which Uber Eats CSV/export the user has provided
- Ask for the week date range (Monday-Sunday) if not provided
- Filter all rows to only those where `Order Date` falls within the specified Mon-Sun window

## Step 2: Apply Filters & Extract Data

### Order Filtering
- Completed orders only: `Order Status = "Completed"`
- Week filter: `Order Date` within Monday-Sunday of specified week

### Marketing-Driven Order Definition
A Completed order is **Marketing-Driven** if ANY of these are true:
- `Offers on items (incl. tax)` < 0 (item-level offer redeemed)
- `Delivery Offer Redemptions (incl. tax)` < 0 (delivery offer redeemed)
- `Other payments description` contains "Ad" (case-insensitive) on that row (ad-attributed order)
- `Other payments description` equals "Customer contribution" on that row (ad-related credit)

This ensures orders driven by ads are counted as marketing-driven, not just orders with discounts. Without this, ad-only orders (no discount applied, but ad spend recorded) would incorrectly fall into "Organic."

### Sales Calculation (Net)
- **Total Sales (Net):** sum `Sales (excl. tax)` for Completed orders
- **Marketing Driven Sales:** sum `Sales (excl. tax)` for Completed orders matching the Marketing-Driven criteria above
- **Organic Sales:** Total Sales (Net) - Marketing Driven Sales

### Order Counts
- **Total Orders:** count of Completed orders
- **Orders from Marketing:** count of Completed orders matching the Marketing-Driven criteria above
- **Organic Orders:** Total Orders - Orders from Marketing

### Offer / Discount Value
Sum of absolute values for Completed orders:
- abs(`Offers on items (incl. tax)`) where < 0
- PLUS abs(`Delivery Offer Redemptions (incl. tax)`) where < 0

### Ads + Credits (Netting Logic)
Ad/credit data lives in `Other payments description` (label) and `Other payments` (amount).

**Ad-Related Row Definition:** treat a row as ad-related if:
- `Other payments description` contains "Ad" (case-insensitive), OR
- `Other payments description` equals "Customer contribution"

**Ad Metrics:**
- **Gross Ad Spend:** sum abs(`Other payments`) where description == `"Ad Spend"`
- **Ad Credits / Offsets:** sum of positive `Other payments` among ad-related rows where description != `"Ad Spend"`
- **Net Ad Spend Impact (Payout Impact):** sum of signed `Other payments` among ad-related rows (typically negative)
- **Net Ad Spend (Cost):** abs(Net Ad Spend Impact)
- **Credits Offset % (of Gross Ad Spend):** Ad Credits / Offsets / Gross Ad Spend

### Total Marketing Investment
Net Ad Spend (Cost) + Offer/Discount Value

### Net Payout (All Statuses)
- **Net Payout $ (All Statuses):** sum `Total payout` across ALL rows/statuses in the week
  (Completed, Refund, Cancelled, Unfulfilled, Refund Disputed, includes negative payouts)

## Step 3: Key Calculations

| Metric | Formula |
|--------|---------|
| AOV | Total Sales (Net) / Total Orders |
| Marketing Investment / Sales % | Total Marketing Investment / Total Sales (Net) |
| Marketing ROAS | Marketing Driven Sales / Total Marketing Investment |
| Offers ROAS | Marketing Driven Sales / Offer/Discount Value |
| Combined ROAS | Marketing Driven Sales / (Net Ad Spend (Cost) + Offer/Discount Value) |
| Ad Efficiency | Marketing Driven Sales / Net Ad Spend (Cost) |
| Net Payout % | (Net Payout $ / Total Sales (Net)) x 100 |

## Step 4: Validation

Before presenting results, confirm:
- Marketing Driven Sales + Organic Sales = Total Sales (Net)
- Orders from Marketing + Organic Orders = Total Orders
- Flag anomalies: unusually large credits/offsets, net ad spend that flips positive, etc.

## Output Format

### When called standalone:
Present the Platform-Level Overview Table:

| Metric | Value |
|--------|------:|
| Total Sales (Net) | $XXX,XXX.XX |
| Marketing Driven Sales | $XXX,XXX.XX |
| Organic Sales | $XXX,XXX.XX |
| Total Orders | X,XXX |
| Orders from Marketing | XXX |
| Organic Orders | X,XXX |
| AOV | $XX.XX |
| Gross Ad Spend | $X,XXX.XX |
| Ad Credits / Offsets | $X,XXX.XX |
| Net Ad Spend Impact (Payout Impact) | $-X,XXX.XX |
| Net Ad Spend (Cost) | $X,XXX.XX |
| Credits Offset % (of Gross Ad Spend) | XX.XX% |
| Offer/Discount Value | $X,XXX.XX |
| Total Marketing Investment | $X,XXX.XX |
| Marketing Investment / Sales % | X.XX% |
| Marketing ROAS | X.XXx |
| Net Payout $ (All Statuses) | $XX,XXX.XX |
| Net Payout % | XX.XX% |

If a store-level breakdown is requested, produce a second table sorted by Total Sales (Net) descending with the same metrics per store.

### When called by the weekly-reporting orchestrator:
Output a structured JSON object to the output directory specified by the orchestrator, containing:
- `platform`: "UBER EATS"
- `overview`: dict of all metrics above
- `by_location`: dict of location name -> metrics dict
- `campaigns`: list of campaign objects (if ad/offer files provided)

Save as `ue_extraction.json` in the output directory.

## UE Ad Platform Files (Supplementary)

When the UE Ads by Location and/or UE Offers by Location exports are provided (from ads.ubereats.com), use them for campaign-level detail:

**Ads by Location export:**
- Group by store. Spend = sum of "Spend" or "Ad spend (USD)" column. Sales = "Sales" or "Attributed Sales". Orders = "Orders" or "Attributed Orders".
- Known issue: The UE Manager Portal ads campaign list sometimes shows $0 spend. The ads-by-location export from ads.ubereats.com is the reliable source.
- IMPORTANT: Date range must match the exact target week. Wider ranges inflate attribution.

**Offers by Location export:**
- Group by store. Orders = sum of "Redemptions". Spend shows as percentage only (--* for dollar amount).

**Offers Campaign Summary** (from merchants.ubereats.com > Marketing > Offers):
- Provides campaign-level offer details if available.

Include campaign data in the `campaigns` section of the output.

## Notes on Data Source

Settlement files != dashboard data. This report uses **transaction/settlement exports** which reflect finalized transactions. Platform dashboards show real-time attributed performance and will differ. Always include this note in the output footer.

## Store Name Handling
- UE store names typically follow "Brand - Location" pattern
- Strip the brand prefix to get the canonical location name
- If the user provides a location name mapping, use it
