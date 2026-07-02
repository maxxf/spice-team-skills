# DoorDash Weekly Performance Extraction Agent

> ⚠️ **TAX EXCLUSION — READ FIRST**
>
> **Total Sales MUST come from `Subtotal` (food total excl tax). Period.**
>
> Banned columns: `Sales (incl. tax)`, `Order Total`, `Net total`, any "Total" column containing tax. These will inflate sales by ~8-10% (CA sales tax).
>
> Detection fingerprint: if Total Sales is summed from a tax-inclusive column, `commissions_pct < 25%` and AOV jumps above benchmark with no business cause. Validator catches both.
>
> Root cause of the May 2026 goop Kitchen incident (3 weeks of inflated reports): summing the wrong column for Total Sales.

Extract weekly performance metrics (Monday-Sunday) from DoorDash exports using
**Conservative Attribution** methodology with Marketplace-only filtering.

## Required Input Files

1. **Transaction CSV** - DD payment/settlement export (order-level rows) — REQUIRED
2. **Sponsored Listing CSV** (when available) - from DD Ads Manager portal
3. **Promotion CSV** (when available) - from DD Ads Manager portal

---

## Step 0: Load Client Config & Determine Data Tier

**If `OUTPUT/client_profile.json` exists** (written by the orchestrator from the client's Notion Weekly Reporting Profile), read it first. Extract: `dd_invoicing_tier`, any DD-specific data quirks, and location map. These override the registry values below.

**Otherwise**, check `references/client-registry.md` for the client's `DD Portal Access` flag.

| Tier | Files Available | When to Use |
|------|----------------|-------------|
| **Settlement Only** | Transaction CSV only | Client has no DD Ads Manager portal access, OR is not running campaigns |
| **Settlement + Portal** | Transaction CSV + Sponsored Listings + Promotions | Client has DD portal access AND is actively running ads/promos |
| **Invoiced** | Settlement CSV + Portal exports, but ad spend NOT in settlement | Rare. Ad spend billed via Net 30 invoice instead of settlement deduction. Flag if settlement ad spend = $0 but portal shows spend. |

**Portal exports improve attribution the same way UE Ads Manager does.** When available, they give attributed orders/sales per store that the settlement CSV alone misses. If a client has portal access and is running campaigns, always request these files.

> If portal access is unknown and settlement shows Marketing fees beyond the $0.99 flat fee, the client likely has portal access. Ask the user to confirm and pull exports.

---

## Step 1: Order Status Handling

If the CSV does **not** contain an `Order Status` field, define:
- **Completed-like order:** `Transaction type = "Order"` AND `Subtotal` > 0
- **Refund-like order:** `Transaction type = "Order"` AND `Subtotal` < 0

---

## Step 2: Identify Files & Week

- Confirm which files the user has provided (see Tier table)
- Confirm the week date range (Monday-Sunday)
- Filter all rows to the specified week only (use `Timestamp local time` column)
- Apply `Channel = "Marketplace"` filter throughout

### Column Identification

- **Store/Location:** `Store name`
- **Channel:** `Channel` — MUST filter to "Marketplace"
- **Transaction type:** `Transaction type`
- **Date:** `Timestamp local time`
- **Total Sales:** `Subtotal` (food total excl tax, incl discounts. This is the new top line.)
- **Tax (for validation only):** `Tax (subtotal)` — NOT used in any reported metric. Only for reconciliation.
- **Marketing fee:** `Marketing fees`
- **Customer discounts:** `Customer discounts`
- **DoorDash marketing credit:** `DoorDash marketing credit`
- **Third-party contribution:** `Third-party contribution`
- **Commission:** `Commission` — platform take. NEW visible metric.
- **Merchant fees:** `Merchant fees` — processing/service fees. Rolls into Other Adjustments.
- **Net total:** `Net total` — platform payout per order. Used for VALIDATION only, not reported directly.
- **Error charges:** `Error charges` — rolls into Other Adjustments.
- **Adjustments:** `Adjustments` — rolls into Other Adjustments.

---

## Step 3: Extract Metrics (All Tiers)

### Order Counting (Completed-only)
Count only:
- `Channel = "Marketplace"`
- Completed-like orders only (`Subtotal` > 0)

### Sales Calculation

**Total Sales:** Sum `Subtotal` for ALL Marketplace Order rows including refunds. This is the food subtotal (excl tax, incl discounts). New top-line metric.

**Discounts:** Sum of merchant-funded discount amounts (see Ad Spend & Offer/Discount section below for the $0.99 rule breakdown). This replaces "Offer/Discount Value."

**Net Sales:** Total Sales - Discounts. NEW metric. What the merchant keeps from food sales before platform fees.

**Marketing Driven Sales:** Sum `Subtotal` for completed-like Marketplace orders that are marketing-driven (see Attribution below). Do NOT include refund-like rows.

**Organic Sales:** Total Sales - Marketing Driven Sales

### Commission & Fees Extraction (NEW)

**Commissions:** Sum abs(`Commission`) for ALL Marketplace rows (all transaction types). This is the platform's take rate.

**Commissions %:** Commissions / Total Sales * 100.

**Other Adjustments:** Sum of `Merchant fees` + `Error charges` + `Adjustments` for ALL Marketplace rows. These are processing fees, error charges, and misc credits/debits. Report as a single net number.

### Ad Spend & Offer/Discount — The $0.99 Rule

Look at `Marketing fees` and `Customer discounts` per order:

| Scenario | Marketing Fees | Customer Discounts | Ad Spend to Count | Offers to Count |
|----------|---------------|-------------------|-------------------|-----------------|
| No ad spend | $0.00 | Any | $0 | abs(Customer Discounts) |
| Offer only | Exactly -$0.99 | Any amount | $0 | abs(Customer Discounts) + $0.99 |
| Ad spend only | > $0.99 (e.g. -$5.31) | $0.00 | Full amount (e.g. $5.31) | $0 |
| Ad + offer combined | > $0.99 (e.g. -$5.31) | Has a value | Marketing Fees minus $0.99 (e.g. $4.32) | abs(Customer Discounts) + $0.99 |

> The flat -$0.99 Marketing Fee is always an offer redemption fee — strip it out and add to Offers.

**Offers/Discount Value breakdown (track separately):**
- `Merchant-Funded Discount`: abs(`Customer discounts`) where < 0
- `$0.99 Redemption Fees`: count of promo orders x $0.99
- `DD Marketing Credits`: abs(`DoorDash marketing credit`) where < 0
- `Third-party Contributions`: abs(`Third-party contribution`) where < 0
- `Total Offers`: sum of all four above

Apply to: `Channel = "Marketplace"`, completed-like orders only. EXCLUDE refund-like rows.

**Ad Spend (from settlement):** Sum of ad spend amounts per the table above.

**Total Marketing Investment:** Ad Spend + Total Offers

### Net Payout (Calculated)
**Net Payout = Net Sales - Commissions - Ad Spend - Other Adjustments.** Calculated from components, NOT from the `Net total` column. This strips out sales tax and makes DD comparable to UE and GH.

### Net Payout Validation
Sum ALL `Net total` values for `Channel = "Marketplace"`, ALL transaction types. Then subtract Sum `Tax (subtotal)` for the same rows. The result should approximate the calculated Net Payout (within 2%). Flag if it doesn't.

### Net Payout %
**Net Payout %** = Net Payout / **Total Sales** (Subtotal, excl tax).

### Marketing Attribution (Completed-only)
An order is **Marketing-Driven** if (on a completed-like Marketplace order):
- `Marketing fees` < 0 (any amount), OR
- `Customer discounts` < 0

**Marketing Driven Orders:** count meeting criteria.
**Organic Orders:** all other completed-like Marketplace orders.

---

## Step 4: Portal Cross-Reference (when portal exports provided)

> Skip this step if only settlement CSV is available (no portal exports).

### 4A: Marketing Driven Sales — Portal + Settlement Reconciliation

The settlement CSV underattributes because it only flags orders where a fee/discount was directly deducted. The portal captures the full attributed picture, BUT portal Ad and Promo exports have significant overlap (same orders appear in both).

**Per-store calculation:**

1. **Settlement marketing orders** = orders flagged via the $0.99 rule (Step 3). This is the floor.
2. **Portal Ad Orders** = sum `Orders` from Sponsored Listings export (per store)
3. **Portal Promo Orders** = sum `Orders` from Promotions export (per store)
4. **Portal combined (naive)** = Portal Ad Orders + Portal Promo Orders
5. **Estimated overlap** = max(0, Portal combined - Total Completed Orders at that store) — if combined exceeds total, the excess IS the overlap
6. **Portal marketing orders (deduped)** = min(Portal combined, Total Completed Orders) — HARD CAP at total orders
7. **Marketing orders (final)** = max(Settlement marketing orders, Portal marketing orders deduped) — use whichever is higher, but never exceed total

**For sales — derive from the DEDUPED order count; do NOT sum Ad + Promo sales (mirrors the UE Tier-2 discipline):**
- **Store AOV** = Total Net Sales (settlement) ÷ Total Completed Orders, per store.
- **Marketing Driven Sales** = **Marketing orders (final, deduped — step 7) × Store AOV.** Because the order count is already overlap-deduped and hard-capped at total orders (steps 5–7), this can never exceed total net sales and never double-counts an order that appears in BOTH the Ad and Promo exports.
- **Do NOT compute `Portal Ad Sales + Portal Promo Sales` as Marketing Driven Sales.** Summing them double-counts every order that's in both exports — that is exactly what produced stores reporting >100% of their sales as marketing-driven (goop W26: 5 stores). Portal Ad Sales / Promo Sales are still reported per-campaign in the Ads/Offers tabs for campaign detail; they are NOT summed into the store's Marketing Driven Sales.
- If Marketing orders (final) = Total Completed Orders, the store is fully marketing-driven (MDS = Total Net Sales) — flag for review.

**Organic Sales** = Total Net Sales (settlement) - Marketing Driven Sales

**Discount-Driven Sales (supplementary — the conservative, client-facing cut):**
- **Discount-Driven Sales** = Sum `Subtotal` for completed-like Marketplace orders where `Customer discounts` < 0 (a customer discount was actually given). This EXCLUDES ad-only attribution (orders a Sponsored Listing merely touched). Report it ALONGSIDE Marketing Driven Sales (never replacing it) as `discount_driven_sales` / `discount_driven_pct`.
- This is the honest answer to "what share was *truly promo-driven*" — it runs well below the platform-attributed MDS (goop W26: ~42% vs ~66%), and it's the number to show a client who (rightly) questions why "marketing-driven" looks so high. Platform-attributed MDS = ads + offers the platform credits; discount-driven = orders that actually received a discount. Neither is *incrementality* — that needs a pullback test.

> **Flag when overlap > 20% of portal combined:** "Portal Ad + Promo overlap at [store]: [X] orders overlap out of [Y] combined. Using deduped figure of [Z]."

### 4B: Ad Spend Reconciliation

Compare settlement ad spend to portal ad spend to detect invoicing gaps:

1. **Settlement Ad Spend** = sum from the $0.99 rule table above
2. **Portal Ad Spend** = sum `Marketing Fees | (Including any applicable taxes)` from Sponsored Listings export
3. **Missing Ad Spend** = Portal Ad Spend - Settlement Ad Spend

**If Missing Ad Spend ≈ $0 (within 5%):** Client is on standard billing. Ad spend flows through settlement. Use settlement Ad Spend (more conservative, already deducted from payout).

**If Missing Ad Spend > 10% of Portal Ad Spend:** Client is on invoice billing. Flag: "DD ad spend invoiced separately — not in settlement."
- Use Portal Ad Spend as the Ad Spend figure
- **Adjusted Net Payout** = Original Net Payout - Missing Ad Spend
- **Adjusted Net Payout %** = Adjusted Net Payout / Total Gross Sales

### 4C: Offers Reconciliation

1. **Portal Offers** = sum `Customer Discounts from Marketing | (Funded by you)` from Promotions export
2. **Settlement Offers** = calculated via the $0.99 rule table
3. **Offers Delta** = Portal Offers - Settlement Offers (the delta is typically the $0.99 fees)

Use settlement Offers as the operative number (more conservative).

---

## Step 5: Key Calculations

| Metric | Formula |
|--------|---------|
| Total Sales | Sum `Subtotal` for all Marketplace orders |
| Discounts | Total merchant-funded discounts (from $0.99 rule) |
| Net Sales | Total Sales - Discounts |
| Commissions | Sum abs(`Commission`) for all Marketplace rows |
| Commissions % | Commissions / Total Sales * 100 |
| Other Adjustments | Sum (`Merchant fees` + `Error charges` + `Adjustments`) |
| Ad Spend | From settlement or portal (see tier) |
| Net Payout | Net Sales - Commissions - Ad Spend - Other Adjustments |
| Net Payout % | Net Payout / Total Sales * 100 |
| AOV | Total Sales / Total Orders |
| Marketing ROAS | Marketing Driven Sales / Total Marketing Investment |

Enterprise tier:
| Adjusted Net Payout | Original Net Payout - Missing Ad Spend |
| Adjusted Net Payout % | Adjusted Net Payout / Total Sales * 100 |

---

## Step 6: Validation

- Marketing Driven Sales + Organic Sales = Total Sales (Net) within $1
- Marketing Driven Orders + Organic Orders = Total Orders exactly
- Enterprise: Settlement Ad Spend + Missing Ad Spend = Portal Ad Spend
- If settlement Ad Spend = $0 and portal shows spend: flag invoicing gap

---

## Step 7: Output

Write standardized JSON to `OUTPUT/dd_results.json`:

```json
{
  "platform": "doordash",
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
    "platform_tax_passed": 0.00
  },
  "by_location": [],
  "campaigns": [],
  "reconciliation": {
    "settlement_ad_spend": 0.00,
    "portal_ad_spend": 0.00,
    "missing_ad_spend": 0.00,
    "settlement_offers": 0.00,
    "portal_offers": 0.00,
    "offers_delta": 0.00,
    "original_net_payout": 0.00,
    "adjusted_net_payout": 0.00
  },
  "validation": {
    "sales_check": true,
    "orders_check": true,
    "flags": []
  }
}
```

For Enterprise tier: `ad_spend` in overview should use Portal Ad Spend, and `net_payout` should use Adjusted Net Payout.

Populate `by_location` with the same metrics **per store** — including `total_sales`, `discounts`, `net_sales`, `commissions`, `commissions_pct`, `other_adjustments`, `net_payout`, and `net_payout_pct` for each store. Also include `platform_payout_column` and `platform_tax_passed` per store for validation.

Populate `campaigns` from Sponsored Listing + Promotion CSVs.

---

## Notes

- Settlement files != dashboard data.
- The -$0.99 fee is DoorDash-specific: every promo order has this flat fee.
- DD store names in transactions differ from tracker names. Use client registry mappings.
- All monetary values in JSON should be raw numbers (no formatting).
- **Total Sales = Subtotal** (excl tax). No "Gross Sales" (tax-inclusive) row in the output. Tax is a pass-through.
- **Net Payout is CALCULATED** (Net Sales - Commissions - Ad Spend - Other Adjustments), not from `Net total` column. The `Net total` column + `Tax (subtotal)` are kept as `platform_payout_column` and `platform_tax_passed` for validation only.
