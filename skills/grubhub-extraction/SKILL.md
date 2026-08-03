---
name: grubhub-extraction
description: >
  Extract weekly performance metrics from Grubhub CSV exports for any restaurant chain.
  Use this skill whenever the user uploads or references a Grubhub CSV/export and wants
  weekly metrics, performance numbers, or data extracted from it. Triggers on: "process Grubhub
  data", "extract GH metrics", "weekly Grubhub report", "analyze GH CSV", "pull GH numbers",
  "GH extraction for [client]", or whenever a Grubhub/Seamless transaction/payment file is
  dropped in with context about weekly reporting, performance, or client metrics. Also trigger
  when the weekly-reporting orchestrator delegates GH extraction. Uses Conservative Attribution,
  Marketplace-only filtering, and includes Marketing Credits and Third-party Contribution in
  offer calculations.
---

# Grubhub Weekly Performance Extraction

Extract weekly performance metrics (Monday-Sunday) from a Grubhub CSV export using **Conservative Attribution** methodology.

**Critical Filters:**
- Only `Channel = "Marketplace"` AND `Order Status = "Completed"` in all calculations
- If the user specifies store inclusions or exclusions (e.g., "only include Brand X stores", "exclude Wing Zone"), apply those filters. Otherwise include all stores in the file.

## Step 1: Identify the File & Week

- Confirm the Grubhub CSV provided
- Ask for the week date range (Monday-Sunday) if not provided
- Apply filters: `Channel = "Marketplace"`, `Order Status = "Completed"`
- Apply any user-specified store filters

## Step 2: Attribution Methodology

### Order Filtering
- ONLY count `Channel = "Marketplace"` AND `Order Status = "Completed"`
- Exclude: Cancelled, Unfulfilled, other channels (white-label, corporate, etc.)

### Sales Calculation
- **Total Sales (Net):** Sum `Sales (excl. tax)` -- matches Grubhub merchant reporting
- **Marketing Driven Sales:** Sum `Sales (excl. tax)` for orders with promotional offers (all offer types and credits, see Attribution below)
- **Organic Sales:** Sum `Sales (excl. tax)` for orders without promotional offers

### Marketing Investment Components

**Ad Spend (All Misc Payments):**
Sum absolute value of ALL `Other Payments` where `Other Payments Description` is not null.
Includes: Ad Spend, Ad Credits, Accelerated Remittance Fees, Reverse Charges, etc.

**Offer/Discount Value:**
Sum absolute value of all promotional discounts PLUS credits from:
- All standard promotional discounts (item offers, delivery offers)
- `Marketing Credits` field (credits applied)
- `Third-party Contribution` field (credits applied)

**Total Marketing Investment:** Ad Spend (All Misc Payments) + Offer/Discount Value

### Gross Sales
- **Gross Sales:** Sum `Sales (incl. tax)` or the pre-deduction sales total for Completed Marketplace orders. This is the customer-facing price before any platform fees, commissions, or adjustments. Used as the denominator for Net Payout % to avoid inflated percentages.
- If `Sales (incl. tax)` is not available, use `Sales (excl. tax)` + `Tax` columns summed.

### Net Payout (All Statuses)
- **Net Payout $:** Sum of `Merchant net total` column across ALL rows/statuses in the week (Completed, Refund, Cancelled, Unfulfilled, Disputed). Includes negative payouts.
- The column is called `Merchant net total` in GH exports. Do NOT use `Total Payout` if `Merchant net total` is available, as they may differ.
- *(No channel or store filter on payout -- include all statuses)*

### Marketing Attribution
An order is **Marketing-Driven** if it has ANY of:
- `Offers on items (incl. tax)` < 0
- `Delivery Offer Redemptions (incl. tax)` < 0
- Credits from `Marketing Credits` field
- Credits from `Third-party Contribution` field

**Organic:** All other completed Marketplace orders without any of the above.

## Step 3: Key Calculations

| Metric | Formula |
|--------|---------|
| AOV | Total Sales (Net) / Total Orders |
| Marketing Investment / Sales % | Total Marketing Investment / Total Sales (Net) |
| Marketing ROAS | Marketing Driven Sales / Total Marketing Investment |
| Offers ROAS | Marketing Driven Sales / Offer/Discount Value |
| Combined ROAS | Marketing Driven Sales / (Ad Spend + Offer/Discount Value) |
| Ad Efficiency | Marketing Driven Sales / Ad Spend |
| Net Payout % | (Net Payout $ / Gross Sales) x 100 |

## Step 4: Validation

Before presenting results, confirm:
- Marketing Driven Sales + Organic Sales = Total Sales (Net)
- Orders from Marketing + Organic Orders = Total Orders

## Output Format

### When called standalone:
Present the Platform-Level Overview Table, then optionally the Store-Level Analysis Table sorted by Total Sales (Net) descending.

### When called by the weekly-reporting orchestrator:
Output a structured JSON object to the output directory specified by the orchestrator, containing:
- `platform`: "GRUBHUB"
- `overview`: dict of all metrics
- `by_location`: dict of location name -> metrics dict
- `campaigns`: list (typically empty for GH unless ad data present)

Save as `gh_extraction.json` in the output directory.

### Offers vs Ads Performance (when standalone and detailed breakdown requested)

**Offers Performance:**
Include all promotional discounts, Marketing Credits, and Third-party Contributions.

| Metric | Value |
|--------|-------|
| Total Orders with Offers | XXX |
| - Item Offers | XXX |
| - Delivery Offers | XXX |
| Sales from Offers (Net) | $XX,XXX.XX |
| Total Discount Value | $X,XXX.XX |
| Discount as % of Offer Sales | XX.XX% |
| Average Discount per Order | $XX.XX |
| Net Payout from Offer Orders | $XX,XXX.XX |
| Offers ROAS (Sales/Discount) | X.XXx |

**Ads Performance:**

| Metric | Value |
|--------|-------|
| Total Ad Spend (All Misc Payments) | $X,XXX.XX |
| - Ad Spend | $X,XXX.XX |
| - Ad Credits & Other Fees | $XXX.XX |
| Ad Spend Net Payout Impact | $-X,XXX.XX |
| Stores Running Ads | XXX/XXX (XX.X%) |
| Average Daily Ad Spend | $XXX.XX |
| Average Ad Spend per Store | $XX.XX |

## Notes on Data Source

Grubhub marketing data in settlement files is generally clean but may lag 1-2 days on promo attribution. Always note that settlement data may differ from real-time dashboard figures.

## Store Name Handling
- GH store names typically follow "Brand - Location" pattern
- Normalize to canonical location names
- If the user provides a location name mapping, use it
- Apply any user-specified store inclusion/exclusion filters
