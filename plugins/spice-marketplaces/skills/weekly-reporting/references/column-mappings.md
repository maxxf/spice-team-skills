# Column Mappings

## ⚠ ENFORCE — canonical metric definitions (per Notion "Delivery Marketplaces | Weekly Reporting Skill")
These must be identical across the weekly tracker AND the campaign dashboard. Two recurring violations:

**1. Total Sales = food subtotal EXCLUDING tax, Completed orders only.**
- UE → `Sales (excl. tax)` column. **NEVER** `Total item sales incl. tax`.
- DD → `Subtotal`. Do **not** add `Subtotal tax passed to merchant`.
- GH → `subtotal_sales` (excl tax).
- *goop W24 bug:* UE was pulled tax-inclusive → UE overstated $787,639 → $859,913 (+$72K), inflating the Overview. Tell: UE AOV jumped to ~$51 vs the usual ~$47.

**2. Marketing-Driven Sales = NET sales per Completed order, offer-driven OR ad-driven, deduped (count once).** Net = Total Sales − that order's offer discount.
- **Offer-driven** (order-level, both platforms): discount columns < 0 — UE `Offers on items (incl. tax)` < 0; DD `Customer discounts (funded by you)` < 0.
- **Ad-driven — DoorDash:** `Marketing fees` < 0 (order-level → dedupes cleanly against offers).
- **Ad-driven — Uber Eats:** the order-level signal is the `Marketing Adjustment` / co-funding column, but it ONLY populates when **Uber co-funding % > 0**. When co-funding = 0 (e.g. goop's current sponsored listings), that column is empty → there is **no order-level UE ad signal**; UE ad attribution must then come from the **Ads-Manager export (campaign-level)**, which can't be order-deduped against UE offers. So: co-funded → order-level; not co-funded → campaign-level from Ads Manager.
- **Merging campaign-level UE ad with UE offers = full-overlap dedup: take the LARGER of {offer-driven, ad-attributed} per store — do NOT sum.** Summing double-counts orders that both came from an ad and redeemed an offer, and can push a store's Marketing-Driven Sales **above its Total Sales** (goop W24: naive sum put Pasadena at 126% — impossible). **Hard check: per-store Marketing-Driven Sales must be ≤ that store's Total Sales** — if it isn't, you're double-counting.
- Apply ad attribution whenever ad data exists — do **not** default to offer-only (Tier 1). *goop W24: offer-only $430,869 vs offer+DD-ad ~$469K net; UE ad ($336K Ads-Mgr attributed) is campaign-level only because co-funding is off.*


## UE Transaction: Total=Net Sales, Order ID=orders, Total Payout=payout, Store Name=location
## UE Ads (ads-campaigns-list*.csv): Spend, Sales/Attributed Sales, Orders/Attributed Orders
## UE Offers (offers-campaigns*.csv): Funded by You (pct only), Redemptions=orders
## DD: Sales=net sales, Marketing spend=ad spend, Promotion=offers, Merchant fees, Net payout, Store Name=location, Timestamp (UTC)

### ⚠ DoorDash — map columns by HEADER NAME, never by fixed index
The DD **Sponsored Listing** (ads) and **Promotion** (offers) exports do NOT share a column order — the Promotion file has an extra `Type of promotion` column that shifts everything right:

| Field | SPONSORED_LISTING | PROMOTION |
|---|---|---|
| Store name | 7 | 8 |
| Orders | 11 | 10 |
| Sales | 12 | 11 |
| Spend (ad: `Marketing fees` / offer: `Customer discounts (funded by you)`) | 13 | 12 |
| ROAS | 18 | **19** |
| New customers acquired | **19** | **20** |

Column 19 is **New customers** in the SL file but **ROAS** in the Promotion file. Reading new-customers by a fixed index across both silently sums ROAS as customers — this corrupted goop W24 (NEW CX showed 2,566 / CAC $35; correct was 1,998 / $45). Always resolve DD columns by matching the header string, not position.
## GH: Food Sales/Net Revenue=sales, Orders section, Marketing Sales, Sponsored Listings=ad spend, Promotion Cost=offers, Net Payout, Restaurant Name=location
