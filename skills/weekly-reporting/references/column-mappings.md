# Column Mappings

## UE Transaction: Total=Net Sales, Order ID=orders, Total Payout=payout, Store Name=location
## UE Ads — ad-attributed ORDERS/SALES come ONLY from the Ads Manager PERFORMANCE export, date-filtered to the week: `placement_v2_<dates>.csv` (cols: Date, Orders, Sales, Ad spend) or `campaigns_summary_metrics_<dates>.csv` (Orders, Sales, Ad spend (USD), Locations, Audience targeted). ⚠️ NOT `ads-campaigns-list*.csv` (all-time config/totals — useless for weekly attribution). 2026 CHANGE: the settlement/transaction CSV no longer carries per-order ad attribution (Marketing Adjustment emptied) — it yields ad SPEND only.
## UE Offers (offers-campaigns*.csv): Funded by You (pct only), Redemptions=orders
## DD: Sales=net sales, Marketing spend=ad spend, Promotion=offers, Merchant fees, Net payout, Store Name=location, Timestamp (UTC)
## GH: Total Sales=`order_subtotal_before_adjustments` (NOT `subtotal` — that's post-adjustment, undercounts ~5-8%, see methodology §1). Commissions=abs(`commission`)+abs(`delivery_commission`). Other Adjustments=abs(`processing_fee`)+abs(`withheld_tax`). Discounts=abs(`merchant_funded_promotion`)+abs(`merchant_funded_loyalty`). Platform payout (validation)=`merchant_net_total`. Store key=`Restaurant|City|Address` (pipe-delimited).
