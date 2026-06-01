# Data Collection Checklist — Client Diagnostic

**For the GM:** print or copy this checklist before pulling data. The diagnostic skill needs everything below for a complete 90-day picture. Skip platforms the client doesn't run on (note when skipped).

**Window:** trailing 90 days from today (use exact dates, not "last 90 days", to avoid platform timezone quirks). Confirm the window with the team before pulling.

**Drop zone:** Google Drive. Folder convention:

```
My Drive / Spice / Clients / <Client Display Name> / Diagnostics / <YYYY-MM-DD> / inputs/
  ├── ue/         (Uber Eats files)
  ├── dd/         (DoorDash files)
  ├── gh/         (Grubhub files)
  ├── screenshots/  (storefront audit pics)
  └── notes/      (Circleback / context)
```

The skill creates this folder structure when invoked. Just drop files into the right subfolder.

---

## Uber Eats — UE Manager (`merchants.ubereats.com`)

Drop into `ue/`.

| ☐ | File | Where | Notes |
|---|---|---|---|
| ☐ | **Financial export (orders)** | Reports → Payments → custom date 90d → Download CSV | Use `skiprows=1` when reading. One row per order. |
| ☐ | **Sales by Store** | Reports → Performance → Sales → 90d → Download CSV | Aggregate net payout per store. |
| ☐ | **Repeat Customer Rate** | Customers tab → Repeat Customers → 90d view | Screenshot or CSV. **Required for the radar's Re-order dim.** |
| ☐ | **Ads campaigns list** | Marketing → Ads → All campaigns → Export CSV | Filename like `ads-campaigns-list*.csv`. |
| ☐ | **Offers campaigns** | Marketing → Offers → All offers → Export CSV | Filename like `offers-campaigns*.csv`. |
| ☐ | **Conversion funnel (storefront)** | Insights → Storefront → 90d | Impressions → storefront views (acquisition top-of-funnel). Screenshot OR CSV. |
| ☐ | **Menu items performance** | Menu → Item performance → 90d → Export | Top SKUs, item-level errors. |
| ☐ | **User conversion funnel (brand)** | Per-store, Performance → Sales → 90d → "User conversion funnel" section → screenshot. Sum across stores OR run `menu-conversion-check` skill | Viewed Store → Viewed Menu → Added to Cart → Placed Order. Drives `menu_cvr_pct`. UE has no aggregate view, so brand = sum of per-location. |
| ☐ | **User conversion funnel (per-location)** | Same path, one screenshot per store | **Pull per-location ONLY if client has <20 locations.** If 20+, brand-level + 10-store sample (top 5 + bottom 5 by sales). Note sample in manifest. |
| ☐ | **Order Accuracy / Issues** | Reports → Operations → Order Accuracy → 90d → Export | Drives `error_rate_pct` for UE stores. Without this, UE ops data is missing. |
| ☐ | **Menu Downtime / Hours** | Reports → Operations → Menu Downtime → 90d → Export | Drives `uptime_pct` for UE stores. |
| ☐ | **Ratings & Reviews** | Customers → Reviews & Ratings → 90d → screenshot OR CSV | Per-store rating. Drives `rating` for UE stores. Required for foundation gate. |

If the client has **UE Ads Manager Access = No**, skip the Ads campaigns list (skill runs Tier 1 offer-only attribution). Note in the manifest.

## DoorDash — Merchant Portal (`mxportal.doordash.com`)

Drop into `dd/`.

| ☐ | File | Where | Notes |
|---|---|---|---|
| ☐ | **Financial simplified transactions (PER-ORDER)** | Financials → Statements → custom date 90d → Download CSV | "Simplified" view. **One row per order. REQUIRED** — must include the per-order local timestamp column (`Timestamp local time` / order datetime). This file is the source for the weekly **trend** chart AND the **daypart heatmap**. A store-aggregated summary export does NOT substitute. |
| ☐ | **Frequent Customers %** | Insights → Customer Insights → Frequent customers | Screenshot if no CSV. **Required for radar's Re-order dim.** |
| ☐ | **Sponsored Listings performance** | Marketing → Sponsored Listings → 90d → Export | ROAS, spend, attributed sales. |
| ☐ | **Promos export** | Marketing → Promotions → All promotions → Export | Promo type, depth, dates. |
| ☐ | **Operations Quality** | Operations Quality tab → 90d → Export | Cancellations, errors, downtime. Usually 1 to 4 separate files. Drop them all. |
| ☐ | **Store-level errors** | Operations → Errors → by store → Export | Drives the per-store error breakdown. |

Note: enterprise clients (e.g., goop) get ad spend invoiced separately. The portal exports are source-of-truth for marketing attribution + ad spend. The financial CSV alone won't have ads.

## Grubhub — Grubhub for Restaurants (`restaurant.grubhub.com`)

Drop into `gh/`.

| ☐ | File | Where | Notes |
|---|---|---|---|
| ☐ | **Finance / orders export (PER-ORDER)** | Reports → Finance → 90d → Download CSV | **One row per order. REQUIRED** — must include `order_date` + `order_hour_of_day` (or an order datetime). Combined with the DD per-order file, this is the source for the weekly **trend** chart AND **daypart heatmap**. |
| ☐ | **90d performance export** | Reports → Performance → 90d → Download CSV | Orders, sales, AOV per location. |
| ☐ | **Operations report** | Reports → Operations → 90d → Download | If available. Older accounts may not expose this. |
| ☐ | **Repeat order rate** | Customer Insights tab (newer accounts only) | Skip if not exposed. Mark in manifest. |
| ☐ | **Sponsored Listings** | Marketing → Sponsored Listings → 90d | If client uses paid placement on GH. |

If the client has no Grubhub presence, note it in the run-folder `manifest.md` and skip this section entirely.

## Storefront Audit — Live screenshots

Drop into `screenshots/`. Take from the **public-facing storefront** (use Claude in Chrome where possible, otherwise the client app or web view). Filename them clearly: `ue-hero.png`, `dd-photo-coverage.png`, etc.

| ☐ | Capture | Why |
|---|---|---|
| ☐ | **Hero image (current)** for each platform | Drives the menu radar dim and hero refresh recommendations |
| ☐ | **Sample menu items** showing photo coverage | Photo coverage % per platform. Take 2 to 3 representative shots per platform. |
| ☐ | **Active promo stack** (full list, what's running where) | Promo cannibalization checks |
| ☐ | **Category structure** (full menu landing page screenshot) | Category sprawl / empty categories |
| ☐ | **Top 3 competitors** in the same cuisine + same market (one screenshot each, showing their hero + first menu page) | Competitive benchmark |

## Internal context

Drop into `notes/` (or paste links into `manifest.md`).

| ☐ | What | Where |
|---|---|---|
| ☐ | **Last 2 to 3 Circleback meeting notes** for the client | Notion or Slack links work. Drop URLs in `manifest.md`. |
| ☐ | **Known issues / open initiatives** | Paste a paragraph or link to the relevant Notion page. |
| ☐ | **Location list** (canonical store names + addresses) | If not already in the client's Notion wiki, paste in `manifest.md`. Used for join validation. |
| ☐ | **Prior diagnostics** (if any) | Notion link. Powers the "what moved since last cycle" panel. |

## REQUIRED: Re-order + conversion-funnel captures (per location)

These regressed to "data-pending" on a live client because they weren't
captured legibly. They are **REQUIRED captures**, one per location, saved
machine-readable. Re-order Rate being unscored in the diagnostic is a
**data-pull failure, not an analysis choice.**

| ☐ | Capture | Save path | Notes |
|---|---|---|---|
| ☐ | **UE Repeat Customers** (per location) | `inputs/screenshots/reorder/ue-<store>-repeat.png` | UE Manager → Customers → Repeat Customers, 90d, one per store. Full panel, legible. |
| ☐ | **DD Frequent Customers %** (per store) | `inputs/screenshots/reorder/dd-<store>-frequent.png` | DD Portal → Insights → Customer Insights → Frequent customers. |
| ☐ | **GH repeat-customer view** (if exposed) | `inputs/screenshots/reorder/gh-<store>-repeat.png` | If GH Customer Insights exposes it; else note "not available" in manifest. |
| ☐ | **UE conversion funnel** (per location) | `inputs/screenshots/funnel/ue-<store>-funnel.png` | Impressions → storefront → menu → orders, per store. Without this, the radar's Conversion/Traffic axes are ad proxies. |

**Pre-flight legibility check (do this before saying "done"):** open each
reorder/funnel screenshot and confirm the numbers are sharp and the full
panel is in frame. A blurry / cropped / truncated capture is a FAIL — re-pull
it. These must be machine-readable so the next cycle actually scores Re-order
Rate instead of carrying a data-pending flag.

## REQUIRED: Per-order transaction exports (trend + daypart source)

The weekly **90-Day Trend** chart and the **Daypart heatmap** are NOT
optional analyst flourishes — they are **derived deterministically from the
per-order transaction exports** above. If those files are present, both
charts MUST be produced. They are only legitimately deferred when the
per-order exports are *genuinely absent* (e.g., a platform that won't expose
per-order data for this account vintage).

| ☐ | Capture | Why |
|---|---|---|
| ☐ | **DoorDash per-order financial transactions** w/ local timestamp | Bucketed to ISO week → weekly GMV/orders; bucketed to day×hour → daypart matrix |
| ☐ | **Grubhub per-order finance export** w/ `order_date` + `order_hour_of_day` | Blended with DD into the same weekly + daypart series |

**Rule (state this to the GM):** "Trend + daypart are derivable whenever the
per-order DD/GH transaction exports exist. Only mark them deferred if those
per-order files are genuinely missing — never because deriving them felt
like extra work." A store-aggregated summary CSV does NOT substitute (it has
no per-order timestamp to bucket).

## Pre-flight check before saying "done"

Confirm all of the following before telling Claude the folder is ready:

- [ ] Every file above exists in its subfolder (or is explicitly skipped in `manifest.md` with a reason)
- [ ] All exports cover the **same 90-day window** (mismatched windows produce bad blends)
- [ ] **UE Repeat Customers, DD Frequent Customers %, and UE conversion funnel are captured per location, legible and machine-readable** (the required captures above). GH repeat is optional but note if unavailable.
- [ ] Re-order rate is sourced for at least UE OR DD (GH optional). If neither, flag as a critical gap (the diagnostic will surface "no organic moat" patterns differently)
- [ ] **Per-order DD financial-transactions + GH finance exports are present and carry a per-order timestamp** (so weekly trend + daypart heatmap are derivable). If a per-order file is genuinely unavailable for a platform, note it explicitly in `manifest.md` — that, and only that, justifies deferring trend/daypart
- [ ] Location list matches store names appearing in the platform exports (so joins work)
- [ ] **Source-export date stamps reviewed** — if they disagree with the manifest/Slack window header, the export dates win; note the discrepancy in `manifest.md`
- [ ] Screenshots are dated within the last 7 days (so the storefront audit reflects current state)

Once everything is in place, return to the Claude session and say "done" or "files are ready". Claude will read the folder, validate completeness, and run the diagnostic.

## What the skill produces from this

- **Notion page** in the client's wiki with the dual-half diagnostic (dashboard + collapsed toggles)
- **Action plan kanban** grouped by location tier (Red/Yellow/Green/New)
- **5 deliverable triggers** (menu sheet, leaderboard, campaign plan, hero image, ratings flyer) prepopulated for the worst stores
- **Foundation gate** banner if any "Stop Everything" thresholds are tripped (rating <4.2, error >5%, uptime <90%, CVR <15%, photos <50%)
- **Drive folder** stays as the audit trail for what data went into this diagnostic
