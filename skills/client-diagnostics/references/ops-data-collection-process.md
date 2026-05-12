# 🔬 Diagnostic Data Pull — Ops Runbook

**Owner:** Ops Analyst (Manish or Dulari)
**Hands off to:** Maxx (for now; future: GM running the diagnostic)
**Time:** 30 to 60 min per client
**Output:** A complete Drive folder ready for the diagnostics skill, plus a Slack ping to the receiver

---

## When you do this

Triggered when:
- Maxx (or a GM) asks you to "pull diagnostic data for [client]"
- A new client kicks off and the kickoff calendar shows "Day 0 baseline diagnostic"
- A 90-day cycle anniversary lands for an existing client
- A client's weekly scorecard flags a sustained downturn and the GM wants a root-cause review

If unsure whether to pull, ask in `#int-[client]` channel or DM Maxx.

---

## Before you start (one-time setup per client)

You need login access to the client's:
- **Uber Eats Manager** (`merchants.ubereats.com`)
- **DoorDash Merchant Portal** (`mxportal.doordash.com`)
- **Grubhub for Restaurants** (`restaurant.grubhub.com`)

Credentials live in **Notion → Spice → Platform Credentials DB → [Client Name]**. If the client isn't in that DB, ping Maxx before continuing. Don't try to guess passwords or share creds outside Comet (Spice's password manager) or the credentials DB.

---

## Step 1: Create the Drive cycle folder

**Start here:** [Spice Digital LLC / 1. Clients / 1. Active](https://drive.google.com/drive/folders/1kIwq7HSW2v427c0XZVynrO8XnAuxvkMO)

Every active client has a folder under `1. Active`. Inside each client folder you'll see the existing numbered subfolders (`1. Client Portal`, `2. Creative`).

**For a new client (not yet in `1. Active`):** create the client folder first at the same level as the others. Use the client's display name as the folder title (e.g., `Daily's`, `Virgil's`).

**For every diagnostic cycle (existing or new client):** create the Diagnostics path:

```
1. Active /
  └── <Client Display Name> /
       ├── 1. Client Portal /            (already exists)
       ├── 2. Creative /                 (already exists)
       └── 3. Diagnostics /              (create if missing)
            └── <YYYY-MM-DD> /           (this cycle's folder, dated today)
                 ├── inputs /
                 │    ├── ue /
                 │    ├── dd /
                 │    ├── gh /
                 │    ├── screenshots /
                 │    └── notes /
                 └── (manifest.md goes inside inputs/ in Step 4)
```

Use today's date as the cycle date (e.g., `2026-05-10`). Set folder sharing on the new Diagnostics folder so the Spice team can edit (inherits from parent in most cases, but double-check).

**If you don't see a client in `1. Active`:** they may have churned and moved to `2. Churned`, or they're brand new and need to be added. Ping Maxx if unsure before creating anything.

---

## Step 1.5: Link the Drive folder into the client's Notion space

The client's Notion portal/wiki should be the single jumping-off point for everything Spice does for them. Drive lives in Drive, but a link to it lives in Notion next to the rest of the client's shared assets.

After creating the new `3. Diagnostics/` folder in Step 1, open the client's Notion portal/wiki page. Find or create a "Resources" / "Shared Assets" / "Links" section (depending on what the page already has). Add (or update) entries for:

- **Drive: Diagnostics folder** (new from Step 1) — link to `3. Diagnostics/` so future cycles are discoverable
- **Drive: Client Portal folder** (`1. Client Portal/` if not already linked)
- **Drive: Creative folder** (`2. Creative/`)
- **Google Sheets tracker** (the client's weekly reporting Sheet, if exists)
- **Storefront URLs** (UE / DD / GH consumer-facing URLs)
- **Slack channel** (`#int-[client]`)
- **Platform credentials** (link to the Platform Credentials DB row, not the credentials themselves)

If the client's Notion page doesn't have a Resources section yet, create one. Use a callout block with 🔗 icon, or a simple H2 + bulleted list. The goal: any Spice teammate landing on the client's Notion page can find every shared asset in one scroll.

If you're unsure what the client's portal page is called or where it lives in Notion, search for `<Client Display Name> Wiki` or `<Client Display Name> Portal` first. Ping Maxx if there's no obvious portal page yet.

---

## Step 2: Confirm the date window

Default: **trailing 90 days from today.** Use exact dates everywhere. Example: today is May 10, so the window is **Feb 9 to May 10, 2026**.

Write the window into `manifest.md`:

```
window_start: 2026-02-09
window_end:   2026-05-10
```

If Maxx specified a different window in the request (e.g., a quarterly review aligned to the client's business cycle), use that instead and note it.

---

## Step 3: Pull the files

Work platform by platform. Use the dropdowns and clicks below verbatim. Drop each file into its `inputs/<platform>/` subfolder. Filenames stay as the platform exports them.

### 🟢 Uber Eats — drop in `inputs/ue/`

| ☐ | File | Path in UE Manager | Notes |
|---|---|---|---|
| ☐ | Financial export | Reports → Payments → custom date 90d → Download CSV | Header has 1 garbage row, that's fine |
| ☐ | Sales by Store | Reports → Performance → Sales → 90d → Download CSV | |
| ☐ | Repeat Customer Rate | Customers tab → Repeat Customers → 90d view → screenshot | Save as `ue-repeat-customers.png` |
| ☐ | Ads campaigns list | Marketing → Ads → All campaigns → Export CSV | Skip if client has no UE Ads access |
| ☐ | Offers campaigns | Marketing → Offers → All offers → Export CSV | |
| ☐ | Conversion funnel (storefront-level) | Insights → Storefront → 90d → screenshot OR CSV | High-level acquisition funnel: impressions → storefront views. Save as `ue-storefront-funnel.png`. |
| ☐ | Menu items performance | Menu → Item performance → 90d → Export | |
| ☐ | **User conversion funnel (brand)** | For each store: Performance → Sales → 90d view → "User conversion funnel" section → screenshot. Sum across all stores manually OR use the `menu-conversion-check` skill output for the brand total | The intent-to-purchase funnel: Viewed Store → Viewed Menu → Added to Cart → Placed Order. Drives `menu_cvr_pct` per the diagnostic framework. UE has NO aggregate view, so brand total = sum of per-location numbers. Save as `ue-menu-conv-brand.png` (or paste numbers into `manifest.md`). |
| ☐ | **User conversion funnel (per-location)** | Same path, one screenshot per store. Save as `ue-menu-conv-<store-slug>.png` | **Pull per-location ONLY if client has <20 locations.** If 20+ locations, pull brand-level only (above) plus a representative 10-store sample (top 5 + bottom 5 by sales). Note in manifest which sample was used. |
| ☐ | **Order Accuracy / Issues** | Reports → Operations → Order Accuracy → 90d → Export (or Insights → Operations) | Drives `error_rate_pct` for UE stores. Includes missing items, wrong items, customer complaints. |
| ☐ | **Menu Downtime / Hours** | Reports → Operations → Menu Downtime → 90d → Export (or Storefront → Online Hours) | Drives `uptime_pct` for UE stores. Time the restaurant was unavailable to take orders. |
| ☐ | **Ratings & Reviews** | Customers → Reviews & Ratings → 90d view → screenshot OR CSV | Per-store rating average. Drives `rating` for UE stores. Save as `ue-ratings.png` if screenshot. |

**Note on UE menu conversion:** UE Manager forces single-store context for analytics (no "All stores" aggregate view). For multi-location clients you must visit each store individually via the store dropdown. The existing `menu-conversion-check` skill automates this in browser via Claude in Chrome. If pulling manually feels painful, run that skill first and just drop its CSV output into `inputs/ue/`.

**The last 3 ops rows** (Order Accuracy, Menu Downtime, Ratings) are UE's ops data. Without them the diagnostic's `diagnostic-ops` sub-skill is UE-blind and the foundation gate may misfire (rating / error / uptime thresholds reference all-platform data).

### 🔴 DoorDash — drop in `inputs/dd/`

| ☐ | File | Path in DD Portal | Notes |
|---|---|---|---|
| ☐ | Financial transactions | Financials → Statements → custom date 90d → Download CSV | Pick "Simplified" view |
| ☐ | Frequent Customers % | Insights → Customer Insights → Frequent customers → screenshot | Save as `dd-frequent-customers.png` |
| ☐ | Sponsored Listings | Marketing → Sponsored Listings → 90d → Export | Skip if not running ads |
| ☐ | Promos | Marketing → Promotions → All promotions → Export | |
| ☐ | Operations Quality | Operations Quality tab → 90d → Export | Often 1 to 4 separate files. Drop them all. |
| ☐ | Store-level errors | Operations → Errors → by store → Export | |

### 🟦 Grubhub — drop in `inputs/gh/`

| ☐ | File | Path in GH Portal | Notes |
|---|---|---|---|
| ☐ | 90d performance export | Reports → Performance → 90d → Download CSV | |
| ☐ | Operations report | Reports → Operations → 90d → Download | Older accounts won't have this. Note in manifest if missing. |
| ☐ | Repeat order rate | Customer Insights tab → screenshot | Newer accounts only. Skip if not visible. |
| ☐ | Sponsored Listings | Marketing → Sponsored Listings → 90d → Export | Skip if not running paid placement. |

If the client doesn't run on Grubhub at all, leave `inputs/gh/` empty and note in manifest: "Client not on Grubhub."

### 📸 Storefront screenshots — drop in `inputs/screenshots/`

Pull from the live public storefront, not the merchant view. You can use Claude in Chrome or just open the consumer app and screenshot manually.

| ☐ | What | Filename | Notes |
|---|---|---|---|
| ☐ | UE hero image | `ue-hero.png` | Top of the storefront, banner image |
| ☐ | UE menu items sample | `ue-menu-items.png` | One screenshot showing ~10 items, photo coverage visible |
| ☐ | DD hero image | `dd-hero.png` | |
| ☐ | DD menu items sample | `dd-menu-items.png` | |
| ☐ | GH hero (if applicable) | `gh-hero.png` | |
| ☐ | Active promo stack | `promo-stack.png` | Full list of what's running where, one screenshot per platform if needed |
| ☐ | Category structure | `categories.png` | Full menu landing page showing all categories |
| ☐ | Top 3 competitors | `comp-1.png`, `comp-2.png`, `comp-3.png` | Same cuisine, same market. Hero + first menu page each. |

### 📋 Internal context — drop in `inputs/notes/`

| ☐ | What | How |
|---|---|---|
| ☐ | Last 2 to 3 Circleback meeting notes | Paste URLs into `manifest.md` (don't download the docs) |
| ☐ | Known issues / open initiatives | Copy the relevant Notion section text or paste links into `manifest.md` |
| ☐ | Location list | If not in client's Notion wiki, paste a CSV of canonical store names + addresses into `manifest.md` |
| ☐ | Prior diagnostic (if exists) | Notion link in `manifest.md` |

---

## Step 4: Fill in the manifest

Open `inputs/manifest.md` and complete:

```markdown
# Diagnostic Data Pull — <Client Display Name>

**Date:** 2026-05-10
**Pulled by:** Manish
**Window:** 2026-02-09 to 2026-05-10
**Platforms in scope:** UE, DD, GH

## Files dropped

### Uber Eats (`inputs/ue/`)
- ✅ Financial export
- ✅ Sales by Store
- ✅ Repeat Customer Rate (screenshot)
- ❌ Ads campaigns list — client has no UE Ads Manager access
- ✅ Offers campaigns
- ✅ Conversion funnel (screenshot)
- ✅ Menu items performance

### DoorDash (`inputs/dd/`)
- ✅ Financial transactions
- ✅ Frequent Customers screenshot
- ✅ Sponsored Listings
- ✅ Promos
- ✅ Operations Quality (3 files)
- ✅ Store-level errors

### Grubhub (`inputs/gh/`)
- ✅ 90d performance export
- ❌ Operations report — older account, not exposed
- ❌ Repeat order rate — older account, Customer Insights tab missing
- ✅ Sponsored Listings

### Screenshots
- ✅ All 11 captured

### Internal
- Last meeting: https://notion.so/...
- Last meeting -1: https://notion.so/...
- Known issues: https://notion.so/...
- Location list: in Notion wiki at https://notion.so/...
- Prior diagnostic: https://notion.so/... (or "first cycle")

## Gaps to flag

- UE Ads Manager not enabled, so attribution will run Tier 1 (offer-only)
- GH ops + repeat data unavailable for this account vintage

## Pre-flight check

- [ ] Every required file is present (or explicitly skipped above with reason)
- [ ] All exports cover the same 90-day window (Feb 9 to May 10)
- [ ] Re-order rate sourced for at least UE OR DD (have both: ✅)
- [ ] Location list matches store names in the platform exports
- [ ] Screenshots are all from today (or within last 3 days)
```

Tick the four pre-flight boxes only after you've actually verified each one.

---

## Step 5: Hand off

When everything is done and the manifest is filled, ping the receiver in Slack. Default receiver = Maxx. Use the `#int-[client]` channel so the GM also sees.

**Slack template:**

```
🔬 Diagnostic data ready for <Client Display Name>

Drive folder: <link to inputs/ folder>
Cycle: 2026-05-10 (window Feb 9 → May 10)
Pulled by: <your name>
Gaps: <one-line summary, or "none">

@maxx — ready when you are.
```

After the diagnostics skill runs and Maxx (or the GM) gets the Notion URL back, your part is done. The Notion page will reference back to the same Drive folder so the audit trail is intact.

---

## Common issues + fixes

| Symptom | What to do |
|---|---|
| Login fails on a platform | Check Notion → Platform Credentials DB → Issues. If creds are stale, ping the account owner (Maxx for new clients, GM for ongoing ones). |
| Date picker won't accept 90 days exactly | Use the closest preset (e.g., "Last 90 days" if available, or "Last 3 months"). Note the actual range you got in `manifest.md`. |
| Export takes >5 min | Wait. Some platforms queue large reports. Don't refresh, you'll lose the queue position. |
| Operations Quality returns empty | Likely the client just got onboarded to Ops Quality. Note in manifest, mark as "data starts <date>". |
| You don't have access to the credentials DB | Ping Maxx in Slack: "Need Platform Credentials DB access for [client]." |
| The client only runs on 1 platform | That's fine. Skip the other two entirely. Note in manifest. |
| Storefront audit screenshot is hard to capture | Use Claude in Chrome (`/claude in chrome` for the URL). Tell it "screenshot the full storefront page visible to a customer." |

---

## Notes for future improvement

- **Wk 5+ goal:** native UE/DD/GH extractors that pull files directly via API or browser automation, eliminating most manual download steps. You'd only do screenshots + internal context.
- **Wk 6+ goal:** auto-trigger this runbook from the cycle calendar (Notion automation pings you 7 days before each diagnostic is due).
- **Until then:** this runbook is the canonical Spice ops process for diagnostic data prep.

---

## Hand-off contract (what Maxx / GM expects to receive)

When ops finishes:

1. **Drive folder** at the canonical path with all subfolders populated
2. **manifest.md** filled in with the 4 pre-flight checks ticked
3. **Slack ping** in `#int-[client]` tagging Maxx (or the GM) with the Drive link

When the diagnostic finishes (Maxx / GM does this part):

1. **Notion page** in the client's wiki with the dual-half diagnostic
2. **Slack reply** in the same `#int-[client]` thread with the Notion URL

The thread becomes the audit trail for the cycle.
