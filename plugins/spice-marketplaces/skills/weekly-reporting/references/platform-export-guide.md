# Platform Data Export Guide

Step-by-step instructions for pulling the weekly data files needed for reporting. Each platform requires specific exports with specific date filters. **Dates must be Monday through Sunday** of the reporting week.

---

## Uber Eats — 3 Files Required

### File 1: Transaction CSV (REQUIRED)
**What it is:** Order-level settlement data — every order, refund, adjustment, and ad charge for the week.

**Where to find it:**
1. Log in to **Uber Eats Manager** → `merchant.uber.com`
2. Select the correct business/brand from the account switcher (top left)
3. Go to **Payments** (left sidebar)
4. Click **Download CSV** or **Export**
5. Set date range: **Monday to Sunday** of the reporting week
6. Make sure **All Stores** is selected (not a single location)
7. Download

**What the file looks like when correct:**
- Filename pattern: varies (often `payments_YYYY-MM-DD.csv` or similar)
- Key columns: `Store Name`, `Order Status`, `Order Date`, `Sales (excl. tax)`, `Total payout`, `Offers on items (incl. tax)`, `Delivery Offer Redemptions (incl. tax)`, `Other payments`, `Other payments description`
- Should have rows for ALL statuses: Completed, Cancelled, Refund, Unfulfilled, etc.
- Should have rows with `Other payments description` = "Ad Spend" (these are daily ad charges per store — blank Order Status is normal)
- Row count: typically 500-5,000+ depending on order volume

**Common mistakes:**
- Filtering to a single store instead of all stores
- Using the wrong date range (check that Monday is correct — use a calendar)
- Downloading the "summary" view instead of the detailed transaction CSV

---

### File 2: Ads Manager Performance Export (REQUIRED for ad attribution)
**What it is:** Campaign-level performance data showing attributed orders, sales, and spend per store. This is the ONLY source for ad-driven order attribution.

**Where to find it:**
1. Go to **Uber Eats Ads Manager** → `advertiser.uber.com`
2. Click **Reports** in the top nav → **Create Report** (or go directly to `advertiser.uber.com/reports/create-v2`)
3. Report type: **Campaign Summary**
4. Group by: **Location** (critical — this gives per-store breakdowns)
5. Date range: **Monday to Sunday** of the reporting week (must match transaction CSV dates exactly)
6. Click **Download** or **Export CSV**

**What the file looks like when correct:**
- Filename pattern: `campaigns_summary_metrics_YYYY-MM-DD_YYYY-MM-DD.csv`
- Key columns: `Campaign name`, `Status`, `Locations`, `Ad spend`, `Sales`, `Orders`, `Return on Ad Spend`, `Impressions`, `Clicks`, `New customers`, `Lapsed customers`, `Existing customers`
- Should show ACTIVE campaigns with non-zero spend/orders
- Multi-store campaigns will show a number in the `Locations` column (e.g., "4") instead of a store name

**Common mistakes:**
- Downloading the **campaign list** export (shows all-time configs, paused campaigns, no date filtering) instead of the **performance report**. The campaign list has columns like `Budget`, `Bid Strategy`, `Start Date` — that's the wrong file.
- Not filtering to the correct week dates
- Not grouping by Location (without this, you lose per-store attribution)

**⚠️ Without this file:** Only offer-driven orders count as marketing. Ad-driven orders fall into "Organic," deflating marketing ROAS and inflating organic metrics. Always pull this file.

---

### File 3: Offers Export (REQUIRED)
**What it is:** Campaign-level offer/promotion redemption data.

**Where to find it:**
1. In **Uber Eats Manager** → `merchant.uber.com`
2. Go to **Marketing** (left sidebar)
3. Find the **Offers** or **Promotions** section
4. Look for **Export** or **Download** option
5. Set date range to the reporting week (Mon-Sun)
6. Download

**What the file looks like when correct:**
- Contains offer/promotion campaign names, redemption counts, store names
- Spend values show as percentages only (no dollar amounts — this is normal for UE offers)

**Note:** Offer attribution also exists per-order in the Transaction CSV. This file provides supplementary campaign-level detail. If unavailable, offer attribution still works from the transaction file.

---

## DoorDash — 1-3 Files

### File 1: Transaction CSV (REQUIRED)
**What it is:** Order-level settlement data for all stores.

**Where to find it:**
1. Log in to **DoorDash Merchant Portal** → `merchant-portal.doordash.com`
2. Go to **Financials** or **Payments** (left sidebar)
3. Click **Download** or **Export Transactions**
4. Set date range: **Monday to Sunday** of the reporting week
5. Select **All Stores**
6. Download CSV

**What the file looks like when correct:**
- Key columns: `Store Name`, `Transaction type`, `Channel`, `Sales (excl. tax)`, `Order Total`, `Marketing fee`, `Customer discounts`, `Net payout`
- `Channel` column should include "Marketplace" rows (filter to these for reporting)
- `Transaction type` includes "Order", "Adjustment", etc.
- Row count: varies by location count and order volume

**Common mistakes:**
- Not selecting all stores
- Wrong date range
- Enterprise clients (like goop Kitchen): ad spend is invoiced separately and will NOT appear in this file

---

### File 2: Sponsored Listing CSV (OPTIONAL — for ad campaign detail)
**What it is:** Performance data for DoorDash Sponsored Listing ad campaigns.

**Where to find it:**
1. In the **DoorDash Merchant Portal**
2. Go to **Marketing** → **Sponsored Listings** (or **Ads**)
3. Set date range to the reporting week
4. Export/Download CSV

**What the file looks like when correct:**
- Contains: `MARKETING_SPONSORED_LISTING` data
- Columns include campaign name, spend, impressions, clicks, orders, sales per store

**Note for Enterprise clients:** Portal exports are the source of truth for marketing attribution and ad spend (since ad spend is invoiced, not in the settlement CSV).

---

### File 3: Promotion CSV (OPTIONAL — for promotion campaign detail)
**What it is:** Performance data for DoorDash promotion campaigns (discounts, offers).

**Where to find it:**
1. In the **DoorDash Merchant Portal**
2. Go to **Marketing** → **Promotions**
3. Set date range to the reporting week
4. Export/Download CSV

**What the file looks like when correct:**
- Contains: `MARKETING_PROMOTION` data
- Columns include promotion type, redemptions, discount value, sales driven

---

## Grubhub — 1 File

### File 1: Settlement CSV (REQUIRED)
**What it is:** Order-level settlement data with all financial details.

**Where to find it:**
1. Log in to **Grubhub for Restaurants** → `restaurant.grubhub.com`
2. Go to **Financials** or **Payments** (left sidebar)
3. Click **Export** or **Download Transactions**
4. Set date range: **Monday to Sunday** of the reporting week
5. Select **All Stores**
6. Download CSV

**What the file looks like when correct:**
- Key columns: `Restaurant Name`, `Order Status`, `Channel`, `Sales (excl. tax)`, `merchant_total`, `Merchant net total`, `Marketing Credits`, `Third-party Contribution`, `merchant_funded_promotion`, `merchant_funded_loyalty`
- `Channel` should include "Marketplace" rows
- `Order Status` includes "Completed", "Cancelled", etc.
- City and address fields are separate columns (used for store name mapping)

**Common mistakes:**
- Not selecting all stores
- Wrong date range
- Note: GH ad spend is NOT in the settlement file. If GH ads are active, that data comes from a separate source.

---

## Optional Operations Files

These provide supplementary quality/operations data for the report. Not required for core financial metrics.

### DoorDash Operations Quality CSV
- From DD Merchant Portal → **Operations** or **Quality** section
- Shows: customer ratings, order accuracy, delivery times per store

### UE Order Accuracy Files
- From UE Manager → **Operations** or **Quality** section
- Shows: order accuracy metrics, missing items, incorrect items

### UE Menu Downtime Files
- From UE Manager → **Operations** or **Hours** section
- Shows: periods when menu was offline/unavailable per store

---

## Prior Week Comparison Data

For WoW (week-over-week) calculations, also provide ONE of:
- **Weekly Tracker Google Sheet export** — download as CSV from the tracker
- **Prior week numbers** — manually provide last week's key metrics

---

## Weekly File Checklist Template

Copy this for each week and check off as files are downloaded:

```
Week: [Mon DD] - [Sun DD], 202X
Client: _______________

Uber Eats:
  [ ] Transaction CSV (all stores, Mon-Sun)
  [ ] Ads Manager Performance Export (Campaign Summary by Location, Mon-Sun)
  [ ] Offers Export (Mon-Sun)

DoorDash:
  [ ] Transaction CSV (all stores, Mon-Sun)
  [ ] Sponsored Listing CSV (optional)
  [ ] Promotion CSV (optional)

Grubhub:
  [ ] Settlement CSV (all stores, Mon-Sun)

Other:
  [ ] Prior week tracker export (for WoW)
  [ ] DD Operations Quality CSV (optional)
  [ ] UE Order Accuracy (optional)
  [ ] UE Menu Downtime (optional)
```

---

## Backfill Instructions

When pulling data for multiple past weeks:

1. Create a folder for each week: `week-01/`, `week-02/`, etc.
2. For each week, pull ALL required files with that week's Mon-Sun date range
3. Name files clearly — include the date range in the filename if the platform doesn't do it automatically
4. The **Ads Manager performance export** is the most commonly missed file. Without it, UE ad attribution is unavailable and marketing metrics will be undercounted.
5. Confirm each week's folder has at minimum: UE Transaction + UE Ads Manager + DD Transaction + GH Settlement

**goop Kitchen tracker week reference (matches sheet column headers):**

| Week | Monday | Sunday | Notes |
|------|--------|--------|-------|
| Week 43 | Oct 20 | Oct 26 | Tracker starts here |
| Week 44 | Oct 27 | Nov 02 | |
| Week 45 | Nov 03 | Nov 09 | |
| Week 46 | Nov 10 | Nov 16 | |
| Week 47 | Nov 17 | Nov 23 | |
| Week 48 | Nov 24 | Nov 30 | |
| Week 49 | Dec 01 | Dec 07 | |
| Week 50 | Dec 08 | Dec 14 | |
| Week 51 | Dec 15 | Dec 21 | |
| Week 52 | Dec 22 | Dec 28 | |
| Week 1 | Dec 29 | Jan 04 | 2026 starts |
| Week 2 | Jan 05 | Jan 11 | |
| Week 3 | Jan 12 | Jan 18 | |
| Week 4 | Jan 19 | Jan 25 | |
| Week 5 | Jan 26 | Feb 01 | |
| Week 6 | Feb 02 | Feb 08 | Larchmont added |
| Week 7 | Feb 09 | Feb 15 | |
| Week 8 | Feb 16 | Feb 22 | |
| Week 9 | Feb 23 | Mar 01 | |
| Week 10 | Mar 02 | Mar 08 | |
| Week 11 | Mar 09 | Mar 15 | |
| Week 12 | Mar 16 | Mar 22 | |
| Week 13 | Mar 23 | Mar 29 | |
| Week 14 | Mar 30 | Apr 05 | Current |

> For other clients, check their tracker for week numbering. The week number in the column header corresponds to the ISO week of the Monday start date.
