# Canonical Methodology Reference

Mirrors the [Delivery Marketplaces | Weekly Reporting Skill](https://www.notion.so/spice-digital/Delivery-Marketplaces-Weekly-Reporting-Skill-30cd3ff018e781028137de464c4894d8) (updated April 2026).

## Core formulas

| # | Metric | Formula |
| :-: | :-- | :-- |
| 1 | **Total Sales** | Sum of subtotal / Sales (excl. tax) column. **Completed orders only.** Tax-excluded everywhere for cross-platform comparability. |
| 2 | **Net Sales** | Total Sales − Discounts (Offers) |
| 3 | **Commissions** | UE: abs(Marketplace Fee). DD: abs(Commission). GH: abs(commission + delivery_commission) |
| 4 | **Other Adjustments** | Sum of non-commission, non-ad fee columns. Varies by platform: see per-platform notes below. |
| 5 | **Net Payout** | Net Sales − Commissions − Ad Spend − Other Adjustments |
| 6 | **Net Payout %** | Net Payout ÷ Total Sales × 100 |
| 7 | **Ad Spend** | abs(sum of ad-related payments) net of credits |
| 8 | **Discounts (Offers)** | abs(offer/discount columns) + $0.99 fees if offer is active |
| 9 | **Total Marketing Investment (TMI)** | Ad Spend + Discounts |
| 10 | **Marketing Spend / Sales %** | TMI ÷ Total Sales × 100 |
| 11 | **Marketing-Driven Sales** | Sum of net sales for orders flagged offer-driven OR ad-driven (no double-count) |
| 12 | **Organic Sales** | Total Sales − Marketing-Driven Sales |
| 13 | **Marketing ROAS** | Marketing-Driven Sales ÷ TMI |
| 14 | **Marketing CPO** | TMI ÷ Orders from Marketing |

## Per-platform notes for Other Adjustments

### Uber Eats
Columns to include in Other Adjustments (varies by client setup, but commonly):
- Delivery Network Fee
- Order Processing Fee
- Container Deposit Fee
- Tax adjustment fields where the merchant is liable
- Backup Withholding Tax

Do NOT include in Other Adjustments (canonical treats these separately):
- Marketplace Facilitator Tax (pass-through, collected by UE, not a goop deduction)
- Capital payments (separate accounting)
- Bag Fee (positive line, not a deduction)

### DoorDash
Other Adjustments commonly includes:
- Merchant fees
- Error charges
- Less: Adjustments (signed; can be positive credit)

### Grubhub
Other Adjustments commonly includes:
- Processing fees
- Refund withholdings
- Delivery commission (when not bundled into Commission row)

## Why this matters for YoY analysis

If you sum UE's per-order "Total payout" field or DD's per-order "Net total" field directly, you'll get a number roughly 3% higher than canonical Net Payout. That's because those per-order net fields include line items (capital payments, customer fees flowing to merchant, certain tips, bag fees) that the canonical formula doesn't.

**For YoY apples-to-apples, always apply the canonical formula to BOTH years' raw CSVs.** Don't mix raw per-order sums with canonical tab values. The YoY % growth tends to hold across methodologies, but the absolute dollars will diverge.

## Naming consistency

Use these exact terms in the output doc: they match what the GMs and clients see in the tracker:

- "Total Sales" not "Gross Sales" (Gross Sales was removed April 2026)
- "Net Payout" not "Net Income" or "Profit"
- "TMI" or "Total Marketing Investment" not "Marketing Spend" when both ads + offers are included
- "Ad Spend" specifically when isolating paid placement (excludes offer/promo discounts)
- "Marketing-Driven Sales" not "Paid Sales" or "Attributed Sales"

## Common reconciliation gotchas

1. **UE 2025 vs 2026 column differences.** UE added a "Marketplace Facilitator Tax Adjustment" column in 2026 that didn't exist in 2025. Ignore it on 2025 data, include in Other Adjustments on 2026 data if material.

2. **DD historical columns.** DD has "Merchant fees (for historical reference only)" columns in 2025 data. Don't double-count with the current Merchant fees column.

3. **Beverly Hills-style closures.** Wind-down stores will appear in both 2025 and 2026 same-store sums but their 2026 numbers will be a fraction of 2025. Decide before running: include with caveat, or exclude same-store ex-closing-stores.

4. **NYC / new-launch stores.** Stores that opened mid-period will skew weekly averages. Exclude from same-store comp; include in §4 Portfolio Context.

5. **Tax treatment.** UE Sales (excl. tax) and DD Subtotal both exclude tax. GH varies by report type: verify before summing.
