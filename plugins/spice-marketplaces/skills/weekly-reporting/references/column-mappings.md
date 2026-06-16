# Column Mappings

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
