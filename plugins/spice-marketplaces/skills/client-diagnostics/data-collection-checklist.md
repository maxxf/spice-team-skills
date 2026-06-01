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
| ☐ | **Conversion funnel** | Insights → Storefront → 90d | Impressions, storefront views, menu views, orders. Screenshot OR CSV. |
| ☐ | **Menu items performance** | Menu → Item performance → 90d → Export | Top SKUs, item-level errors. |

If the client has **UE Ads Manager Access = No**, skip the Ads campaigns list (skill runs Tier 1 offer-only attribution). Note in the manifest.

## DoorDash — Merchant Portal (`mxportal.doordash.com`)

Drop into `dd/`.

| ☐ | File | Where | Notes |
|---|---|---|---|
| ☐ | **Financial simplified transactions** | Financials → Statements → custom date 90d → Download CSV | "Simplified" view. One row per order. |
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

## Pre-flight check before saying "done"

Confirm all of the following before telling Claude the folder is ready:

- [ ] Every file above exists in its subfolder (or is explicitly skipped in `manifest.md` with a reason)
- [ ] All exports cover the **same 90-day window** (mismatched windows produce bad blends)
- [ ] Re-order rate is sourced for at least UE OR DD (GH optional). If neither, flag as a critical gap (the diagnostic will surface "no organic moat" patterns differently)
- [ ] Location list matches store names appearing in the platform exports (so joins work)
- [ ] Screenshots are dated within the last 7 days (so the storefront audit reflects current state)

Once everything is in place, return to the Claude session and say "done" or "files are ready". Claude will read the folder, validate completeness, and run the diagnostic.

## What the skill produces from this

- **Notion page** in the client's wiki with the dual-half diagnostic (dashboard + collapsed toggles)
- **Action plan kanban** grouped by location tier (Red/Yellow/Green/New)
- **5 deliverable triggers** (menu sheet, leaderboard, campaign plan, hero image, ratings flyer) prepopulated for the worst stores
- **Foundation gate** banner if any "Stop Everything" thresholds are tripped (rating <4.2, error >5%, uptime <90%, CVR <15%, photos <50%)
- **Drive folder** stays as the audit trail for what data went into this diagnostic
