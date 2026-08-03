---
name: doordash-extraction
description: >
  Extract weekly performance metrics from DoorDash CSV exports for any restaurant chain.
  Use this skill whenever the user uploads or references a DoorDash CSV/export and wants
  weekly metrics, performance numbers, or data extracted from it. Triggers on: "process DoorDash
  data", "extract DD metrics", "weekly DoorDash report", "analyze DD CSV", "pull DD numbers",
  "DD extraction for [client]", or whenever a DoorDash transaction/payment file is dropped in
  with context about weekly reporting, performance, or client metrics. Also trigger when the
  weekly-reporting orchestrator delegates DD extraction. Uses Conservative Attribution methodology
  with Marketplace-only filtering and completed-only order logic.
---

# DoorDash Weekly Performance Extraction

Extract weekly performance metrics (Monday-Sunday) from a DoorDash CSV export using **Conservative Attribution** methodology.

**Critical Filter:** Only include rows where `Channel = "Marketplace"` -- applies everywhere unless a section explicitly states otherwise.

## Step 0: Order Status Handling

If the CSV does **not** contain an `Order Status` field, define:
- **Completed-like order:** `Transaction type = "Order"` AND `Sales (excl. tax)` > 0
- **Refund-like order:** `Transaction type = "Order"` AND `Sales (excl. tax)` < 0

Use these definitions anywhere the methodology references Completed vs. Refund.

## Step 1: Identify the File & Week

- Confirm the DoorDash CSV provided
- Ask for the week date range (Monday-Sunday) if not provided
- Filter all rows to the specified week only
- Apply `Channel = "Marketplace"` filter throughout

## Step 2: Extract Metrics

### Order Counting (Completed-only)
Count only:
- `Channel = "Marketplace"`
- Completed-like orders only (`Transaction type = "Order"` AND `Sales (excl. tax)` > 0)

Exclude refund-like orders from all order counts.

### Sales Calculation (Net)

**Total Sales (Net):** Sum `Sales (excl. tax)` for ALL Marketplace Order rows including refunds:
- `Channel = "Marketplace"`, `Transaction type = "Order"`
- Includes both positive and negative values (refunds reduce net)

**Marketing Driven Sales:** Sum `Sales (excl. tax)` for completed-like Marketplace orders that are marketing-driven (see Attribution below). Do NOT include refund-like rows.

**Organic Sales:** Total Sales (Net) - Marketing Driven Sales

> Note: Refunds reduce Organic Sales by default (refunds are not marketing-attributed).

### Marketing Investment Components

**Ad Spend (All Misc Payments):**
Sum abs value of marketing-related misc payments where:
- `Channel = "Marketplace"`
- Completed-like orders only (`Sales (excl. tax)` > 0)
- Marketing-related (Marketing fee / Other payments, etc.)
- Amount is NOT equal to -0.99
- EXCLUDE marketing fees tied to refund-like orders

**Offer/Discount Value (Completed-only):**
Sum absolute value of:
- `Customer discounts` where < 0
- `Marketing Credits` (credits applied)
- `Third-party Contribution` (credits applied)
- PLUS any Marketing fee exactly = -0.99 (counted as offers, not ad spend)

**Total Marketing Investment:** Ad Spend (All Misc Payments) + Offer/Discount Value

### Net Payout (All Statuses)
Sum ALL `Total payout` values for:
- `Channel = "Marketplace"`
- ALL transaction/order types and statuses (includes negative payouts for refunds/chargebacks)

### Marketing Attribution (Completed-only)
An order is **Marketing-Driven** if (on a completed-like Marketplace order):
- `Marketing fee` < 0, OR
- `Customer discounts` < 0

**Marketing Driven Orders:** count of completed-like Marketplace orders meeting criteria.
**Organic Orders:** all other completed-like Marketplace orders.

## Step 3: Key Calculations

| Metric | Formula |
|--------|---------|
| AOV | Total Sales (Net) / Total Orders |
| Marketing Investment / Sales % | Total Marketing Investment / Total Sales (Net) |
| Marketing ROAS | Marketing Driven Sales / Total Marketing Investment |
| Offers ROAS | Marketing Driven Sales / Offer/Discount Value |
| Combined ROAS | Marketing Driven Sales / (Ad Spend + Offer/Discount Value) |
| Ad Efficiency | Marketing Driven Sales / Ad Spend |
| Net Payout % | (Net Payout $ / Total Sales (Net)) x 100 |

## Step 4: Validation

Before presenting results, confirm:
- Marketing Driven Sales + Organic Sales = Total Sales (Net)
- Marketing Driven Orders + Organic Orders = Total Orders

## Output Format

### When called standalone:
Present the Platform-Level Overview Table with all metrics.

### When called by the weekly-reporting orchestrator:
Output a structured JSON object to the output directory specified by the orchestrator, containing:
- `platform`: "DOORDASH"
- `overview`: dict of all metrics
- `by_location`: dict of location name -> metrics dict
- `campaigns`: list of campaign objects (if marketing files provided)

Save as `dd_extraction.json` in the output directory.

## Notes on Data Source

Settlement files != dashboard data. DoorDash spend figures usually align between settlement and dashboard, but Sales/Orders may diverge because the dashboard includes active/pending orders. Always include a data source note in the output footer.

## Store Name Handling
- DD store names typically follow "Brand Location" pattern (no dash)
- Normalize to canonical location names
- If the user provides a location name mapping, use it

## DoorDash Ad Platform Files (Supplementary)

If DoorDash ad platform files are provided (MARKETING_SPONSORED_LISTING and MARKETING_PROMOTION CSVs):
- **Sponsored Listings**: Group by "Store name". Spend = abs("Marketing fees | (including any applicable taxes)"). Sales = "Sales". Orders = "Orders".
- **Promotions**: Spend = abs("Customer discounts from marketing | (Funded by you)") + abs("Marketing fees | (including any applicable taxes)").
- Include these in the campaigns output.
