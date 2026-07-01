# ezCater Partner Portal — Export SOP

ezCater has no partner API. Pull all diagnostic data by browsing the client's account at
**`partnerportal.ezcater.com`** (Chrome + browser automation, same pattern as Uber Eats).
You need the client's portal login or delegated access.

Drop every export into the cycle's `inputs/` folder, then build the unified CSV
(`references/ezcater-input-schema.md`).

## The four exports

### 1. Operational Metrics — `/operational-metrics`
The ops ground truth, per store, trailing 90 days.
- **On-time delivery %** — delivered inside the 15-min window
- **Rejection rate %** — orders not accepted within 15 min
- **Order accuracy %**
- **Cancellation %**
- **Star rating** + **review count** (badge needs rating ≥4.8 after ≥8 reviews)
- (If shown) average **response time**
- Export the per-store table; note the window.

### 2. Performance / Reliability
- Reliability **Rockstar / At-Risk / Paused** flag per store
- Whether each store currently **carries the badge** (→ `badged` column; default 0 if not shown)

### 3. Finance / Payout
- Sales + payout **history** (broader than the 90-day ops window — use for momentum / YoY)
- Per-store sales where available

### 4. 30-day Sales
- Per-store **orders**, **sales**, **AOV**
- **Sponsored-listing** contribution (→ `sponsored_spend`, `sponsored_attributed_sales`)

## Lever settings (for the Visibility bucket)

Capture the current state of each visibility lever per store (Rankings / ezRewards /
Sponsored / Promotions screens):
- **Preferred Partner Program** bid % → `ppp_bid_pct` (0 = off)
- **ezRewards** % → `ezrewards_pct` (0 = off)
- **Sponsored Listings** running? → spend/attributed above
- **Active promo codes / offers** count → `promo_count_active`

## Packaging audit (for the Packaging bucket)

ezCater exposes no menu funnel, so packaging is a quick manual audit per store/menu:
score 0–1 on whether the catering menu has per-person pricing, headcount-tier pricing,
"Feeds 10/25/50" bundles, lead-time-gated packages, and the required catering fields filled.
→ `packaging_complete`. If you can't audit it this cycle, default it and flag the gap.

## Cadence

Monthly. Pull exports once a month; re-diagnose fully each quarter. Do **not** run weekly —
the catering service is priced and staffed for a monthly rhythm.
