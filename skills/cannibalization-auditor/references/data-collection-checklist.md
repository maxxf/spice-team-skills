# Data Collection Checklist — Cannibalization Audit

**For the GM:** print this before pulling. The auditor needs 6 months of continuous data across every platform the client runs on. Skip platforms the client doesn't use (note in the cycle folder `manifest.md`).

**Window:** trailing 26 weeks from today (use exact dates, not "last 6 months", to avoid timezone quirks). Confirm with the team before pulling. If anchoring to a specific event (e.g., engagement start), use that as the start date and pad with prior-period baseline if possible.

**Drop zone:** Google Drive. Folder convention:

```
Spice Digital LLC / 1. Clients / 1. Active / <Client Display Name> / 4. Audits / <YYYY-MM-DD>-cannibalization / inputs/
  ├── ue/          (Uber Eats files)
  ├── dd/          (DoorDash files)
  └── gh/          (Grubhub files)
```

**3P-only.** This audit answers a 3P question — did 3P marketing spend produce incremental 3P sales — and the counterfactual is built from other 3P locations. No 1P / POS data needed.

The skill creates this folder structure when invoked. Drop files into the right subfolder.

**File naming:** lowercase, dashes for spaces, include the window in the filename:
- `ue_spend_by_location_2025-11-25_to_2026-05-25.csv`
- `dd_financials_2025-11-25_to_2026-05-25.csv`
- etc.

---

## Uber Eats — UE Manager (`merchants.ubereats.com`)

Drop into `ue/`.

| ☐ | File | Where | Notes |
|---|---|---|---|
| ☐ | **Sales by Store, weekly** | Reports → Performance → Sales → 26w, group by Store → Download CSV | One row per (store × week). Gross sales, orders, net payout. |
| ☐ | **Basic ad spend by location, weekly** | Marketing → Ads → All campaigns → 26w → Export | Sponsored Listings (auction). Spend per (campaign × week). Map campaign → store via the naming convention in the client config. |
| ☐ | **⭐ Advanced ad spend — Uber Eats Ad Manager** | Uber Eats Ad Manager console (separate self-serve platform) → Campaigns → 26w → Export | **Sponsored items + display/brand campaigns live here, NOT in the basic Marketing → Ads tab.** Spend + attributed sales per campaign per week. If the brand runs this console, its spend is part of total marketing spend — missing it under-counts cannibalization. See the advanced-ads note below. |
| ☐ | **Offers spend by location, weekly** | Marketing → Offers → All offers → 26w → Export | Promo depth × redemptions × store. |
| ☐ | **Organic vs paid sales split** | Per-store, Performance → Acquisition → 26w → CSV or screenshot | Required for mix shift. If unavailable as CSV, screenshot each store and we'll OCR. |
| ☐ | **Conversion funnel per location** | Insights → Storefront → per store → 26w → Export | Impressions → views → menu views → orders. Drives `menu_cvr_pct`. |
| ☐ | **Order accuracy / issues** | Reports → Operations → Order Accuracy → 26w → Export | Cancel rate per store per week. |
| ☐ | **Ratings & reviews** | Customers → Reviews & Ratings → 26w → CSV | Rating per store per week. Drives `ratings_velocity`. |

If UE Ads Manager access is restricted, note it. Without ad spend by location the audit is degraded — flag the gap loudly in the manifest.

## DoorDash — Merchant Portal (`mxportal.doordash.com`)

Drop into `dd/`.

| ☐ | File | Where | Notes |
|---|---|---|---|
| ☐ | **Financials, weekly by store** | Financials → Statements → 26w → Download | One row per (store × week). Gross sales, orders, net payout. |
| ☐ | **Sponsored Listings performance** | Marketing → Sponsored Listings → 26w → Export | The basic auction ads. Spend, attributed sales, ROAS per (store × week). |
| ☐ | **⭐ Advanced ad spend — DoorDash Ads Manager** | DoorDash Ads Manager console (self-serve) → Campaigns → 26w → Export | **Sponsored products + display/brand campaigns live here, separate from the portal's Sponsored Listings.** Spend + attributed sales per campaign per week. If the brand runs this console, include it — total marketing spend = Sponsored Listings + Ads Manager + promos. See the advanced-ads note below. |
| ☐ | **DashPass / promos spend** | Marketing → Promotions → 26w → Export | Promo type, depth, dates, attributed sales per store. |
| ☐ | **Operations Quality** | Operations Quality tab → 26w → Export | Cancellations, errors per store per week. Often 1–4 separate files; drop them all. |
| ☐ | **Ratings** | Operations → Reviews → 26w → CSV | Per-store rating + count of new reviews per week. |

For enterprise restaurants where ad spend invoices separately from the financial statement, the Marketing/Sponsored exports are the source of truth for ad spend — the financial CSV alone will understate it. Flag this in the config's `data_quirks` if it applies.

## ⭐ Total marketing spend = ads + offers — read this before pulling

A location's weekly `spend` is **everything the brand spent to drive demand**, summed:

```
spend = basic ads + advanced ads + merchant-funded offers/promos
```

All of it is real cost and all of it belongs in the audit. An audit that counts ads but not promo discounts understates the waste. Three rules:

1. **Offers are required, not optional.** Pull UE Offers, DD Promotions, GH Promotions every time. The build step sums them into `spend` automatically.
2. **Only merchant-funded offers count.** Platform-co-funded promos (Uber Member Days, DashPass marketing fund, GH-funded boosts) are NOT the brand's cost — exclude them or the spend is overstated. When an export mixes funded and co-funded, keep only the merchant-funded portion and note it in the manifest.
3. **UE offer *cost* is often unexportable.** The UE Merchant Portal exposes redemptions but frequently no discount-cost column. When that happens, derive it (redemptions × discount depth) where the depth is known, or mark it `n/a` in the manifest — never enter `$0`, which would silently hide real spend. (DD and GH usually expose promo cost directly.)
4. **⭐ Ad spend must be NET of platform credits.** The same co-funding logic applies to *ads*, not just offers. Uber, DoorDash, and Grubhub routinely credit back a large share of ad spend (promotional ad budget, make-goods, launch credits). Exports often carry a **`Gross Ad Spend`**, an **`Ad Credits`**, and a **`Net Ad Spend`** column — you MUST use net. A gross "Total Ad Spend" column that hasn't subtracted credits will roughly double spend and halve ROAS. (Real example: a Sweetfin UE export showed $308K gross basic ad spend with $306K credited back — net cost was $1.6K. Using gross made stores look like they spent >100% of sales on marketing.) When only a gross column exists, pull the credits/adjustments separately and net them yourself. The engine flags any location above 60% marketing as a likely un-netted-gross error — but catch it at the source.

### Why this is safe re: double-counting

Summing ad spend + offer spend on the same order is **correct** — they're two separate real costs, both paid. The thing you must NOT sum is *attributed sales*: the ads console and the offers report each claim the same order's revenue, so summing them double-counts. The audit handles this automatically — it caps attributed sales at actual sales and builds the cannibalization finding on the gross-sales counterfactual (ground truth, can't be double-counted). You just pull every spend source; the engine sorts out the attribution.

## ⭐ Advanced ad platforms — read this before pulling

Both UE and DD now run **two** ad surfaces, and a sophisticated brand may spend on both:

| Platform | Basic (merchant portal) | Advanced (separate console) |
|---|---|---|
| Uber Eats | Marketing → Ads (Sponsored Listings, auction) | **Uber Eats Ad Manager** — sponsored items, display/brand, audience targeting |
| DoorDash | Marketing → Sponsored Listings | **DoorDash Ads Manager** — sponsored products, display/brand |

**Why this matters for the audit.** Total marketing spend on a location = basic + advanced + promos. If the brand runs the advanced console and we only pull the basic export, we under-count spend — which under-counts cannibalization and can flip a routing call. Always ask the brand (or check the console) whether the advanced platform is in use.

**Two rules when both surfaces exist:**
1. **Sum the spend.** A location's weekly `spend` is basic ad + advanced ad + offers/promos, all added together. The build step does this automatically if every source is dropped — your job is just to pull all of them.
2. **Don't double-count attributed sales.** The two consoles report attribution independently and can claim the same order. We use `attributed_sales` only to compute platform-reported ROAS for context — the cannibalization finding comes from the counterfactual on *gross sales*, which can't be double-counted. So summing spend is safe; just note in the manifest that attribution overlaps if both consoles are active.

If the brand does **not** use the advanced console, skip those rows and note "basic ads only" in the manifest.

## Grubhub — Grubhub for Restaurants (`restaurant.grubhub.com`)

Drop into `gh/`. Skip entirely if the client has no GH presence.

| ☐ | File | Where | Notes |
|---|---|---|---|
| ☐ | **Performance export, weekly** | Reports → Performance → 26w → Download CSV | Orders, sales per (store × week). |
| ☐ | **Sponsored Listings spend** | Marketing → Sponsored Listings → 26w → Export | Spend × attributed sales per store, weekly. |
| ☐ | **Operations report** | Reports → Operations → 26w → Download | Cancel rate, downtime per store. Older accounts may not expose this — note in manifest. |
| ☐ | **Promotions** | Marketing → Promotions → 26w → Export | Promo type, spend, attributed sales. |
| ☐ | **Loyalty / Grubhub+** | Marketing → Grubhub+ → 26w → Export | If client opts into the loyalty program. |

## Location metadata

For each location in scope, confirm with the client:
- Open date (so we can exclude location-weeks pre-opening)
- Market (city/DMA — used for comp-store baselines)
- Comp set within the brand (which locations are "comparable" — usually same market or same size)
- Any structural events in the window (closure, remodel, new format)

If a `client-diagnostics/clients/<slug>.json` already has this, mirror it. Otherwise capture in `clients/<slug>.json` under `locations`.

## What you can skip

- Storefront screenshots (not needed — the audit is data-only)
- Hero image audits (separate skill: `hero-image-review`)
- Menu item performance (separate skill: `menu-conversion-check`)
- Customer-level data (out of scope for v0)

## When the run starts

Once the folder is populated, the skill validates structure + columns + window continuity. If anything is wrong it surfaces specifically what's missing. Don't proceed until validation passes — the analysis depends on column shape.
