---
name: goop-campaign-planning-reporting
description: >
  goop kitchen Monday refresh end-to-end. Walks Santi (or whoever runs the refresh)
  through the data inputs needed from Uber Eats, DoorDash, Grubhub, and the
  Weekly Platform Overview sheet; updates the Campaign Sheet v3 (Active Campaigns,
  Ads Reporting, Offers Reporting, Dashboard) and moves closed campaigns into the
  Archive with Learnings; then duplicates the Notion weekly report master template
  and fills the data placeholders for client review. Trigger on "goop weekly refresh",
  "goop Monday refresh", "update goop sheet", "build goop weekly report", "run goop
  weekly reporting", or any request to refresh goop kitchen's reporting stack for a
  given week. GOOP KITCHEN ONLY. For other clients use the generic weekly-reporting skill.
team: marketplace
version: 1.1.0
---

# goop Campaign Planning & Reporting

The Monday refresh. Five phases. Produces two artifacts:

1. **Updated Campaign Sheet v3** — Active Campaigns, Ads Reporting, Offers Reporting, Dashboard tabs refreshed; closed campaigns moved to Archive with Learnings populated.
2. **Updated Notion weekly report** (duplicated from the [master template](https://www.notion.so/373d3ff018e781dabe7fc0a8710af031), data filled, handed to Ro for commentary).

Cadence: Monday. Not Friday. Reasoning is in the memory file and the master template header.

Owner: Santi.

---

## ⚠️ The Campaign Sheet v3 is ONE shared Google Sheet — edit it in place

**Canonical Campaign Sheet v3 (the only copy):**
- **Google Sheet:** https://docs.google.com/spreadsheets/d/1HacQMl83W6YIsKwR1X77cL_L9OXpmcyYJ5WXTQ4Vmv4/edit
- **Sheet ID:** `1HacQMl83W6YIsKwR1X77cL_L9OXpmcyYJ5WXTQ4Vmv4`
- Lives in goop's Drive folder; shared with the whole team (Santi, Daniel, Ro, Maxx all have edit).

**How to edit it:** open this Sheet through the Google Drive connector and update the tabs **in place**. You are editing the one shared file the whole team and (eventually) the client see. The link never changes; history is preserved.

**NEVER do this:**
- ❌ Do not create a new spreadsheet, "save as," or build a fresh `.xlsx`. A new file = broken link + lost history. This was the old failure mode.
- ❌ Do not look for a local file on disk (e.g. `~/Documents/.../goop_kitchen_campaign_template_v3.xlsx`). The local xlsx is **retired** — the Drive Sheet above is the single source of truth.

**FAIL LOUD:** if you cannot open the Drive Sheet at the link above (no access, link dead, connector down), **STOP**. Post in `#int-goop-kitchen`: *"Can't open the goop Campaign Sheet v3 — blocked on the refresh, need access checked."* Do **not** work around it by creating a new file. A duplicate is worse than a delayed refresh.

---

## Phase 1: Confirm Inputs

Before touching anything, confirm:

- **Week date range** (Mon-Sun). Default: the week that ended yesterday (Sunday).
- **Campaign Sheet v3 reachable** — open the [Drive Sheet](https://docs.google.com/spreadsheets/d/1HacQMl83W6YIsKwR1X77cL_L9OXpmcyYJ5WXTQ4Vmv4/edit) and confirm you can edit it. If not, fail loud (see above).
- **A place to drop platform exports** — your Cowork session's working folder / uploads for this run. Files don't need to live on any specific machine; just have them available to this session.
- **Notion master template page** still locked at `https://www.notion.so/373d3ff018e781dabe7fc0a8710af031` (do not modify the master; only duplicate it).

If any of the above is missing, stop and surface to the user.

---

## Phase 2: Pull platform data

This is the data-drop phase. Drop the files into your session's working folder. Use the checklist below — every box is required unless flagged optional. Missing files? Stop and ask.

### Uber Eats (required: 4 files)

- [ ] `ue_transactions_W[XX].csv` — Transaction / Payment export (settlement)
   - Source: Uber Eats Manager → Reports → Payment Details
   - Provides per-order revenue + per-order offer attribution. Primary source for UE numbers.
- [ ] `ue_ads_manager_W[XX].csv` — Campaign Summary by Location export
   - Source: `advertiser.uber.com/reports/create-v2` → Campaign Summary by Location → date-filtered for the week
   - Required for ad attribution. **Without it, ad-driven orders get counted as organic.**
- [ ] `ue_order_accuracy_W[XX].csv` — Order Accuracy export (per-order errors)
   - Source: UE Manager → Reports → Order Accuracy
- [ ] `ue_offers_campaigns_W[XX].csv` — Offers / Campaigns export
   - Source: UE Manager → Marketing → Campaigns → Export
   - Supplementary detail on offer redemptions.

Optional but recommended:
- `ue_menu_downtime_W[XX].csv` — Menu downtime
- `ue_ratings_W[XX].csv` — Customer ratings (if pulling for ratings-flyer cycle)

### DoorDash (required: 5 files)

- [ ] `dd_financial_transactions_W[XX].csv` — Financial Simplified Transactions
   - Source: DD Merchant Portal → Financials → Transactions → Simplified Transactions export
- [ ] `dd_error_charges_W[XX].csv` — Error Charges export
   - Source: DD Merchant Portal → Financials → Error Charges
- [ ] `dd_sl_marketing_W[XX].csv` — Sponsored Listing Marketing export
   - Source: DD Merchant Portal → Marketing → Sponsored Listings → Performance Export
- [ ] `dd_promotions_marketing_W[XX].csv` — Promotions Marketing export
   - Source: DD Merchant Portal → Marketing → Promotions → Performance Export
- [ ] `dd_ops_quality_W[XX].csv` — Ops Quality (aggregate + cancellations)
   - Source: DD Merchant Portal → Operations → Ops Quality → Export

### Grubhub (required: 3 files)

- [ ] `gh_financial_transactions_W[XX].csv`
- [ ] `gh_financial_summary_W[XX].csv`
- [ ] `gh_ops_review_W[XX].csv`
   - Source: GH for Business → Reports

### Reference link (do not modify, just open)

- **Weekly Platform Overview 2.0 sheet:** [`docs.google.com/spreadsheets/d/18we-M-qVdug4LRZiolfScL3emVPE0AuL4Zb9Zqn_A3A`](https://docs.google.com/spreadsheets/d/18we-M-qVdug4LRZiolfScL3emVPE0AuL4Zb9Zqn_A3A/edit)
   - This is the source of truth for portfolio-level weekly metrics (payout $, spend %, ROAS history). The Notion report's Highlights cross-references this for the 13-week trend numbers. Open it to grab the new week's row once Manish has dropped data into it.

---

## Phase 3: Update Campaign Sheet v3

Open the [Campaign Sheet v3 in Drive](https://docs.google.com/spreadsheets/d/1HacQMl83W6YIsKwR1X77cL_L9OXpmcyYJ5WXTQ4Vmv4/edit) **in place** (see the box at the top — never a new file). Work through the tabs in this order:

### 3a. Active Campaigns tab

For every campaign that was live during the reporting week:

- Update WTD columns (Spend / Sales / Orders / New Cx / ROAS) with this week's numbers from the platform exports
- Update Lifetime columns (Spend / Sales / ROAS) — cumulative since campaign start
- Update Status flag column:
   - 🟢 Performing — above target ROAS, no concerns
   - 🟡 Watch — trending down or borderline
   - 🔴 Below target — below ROAS target 2+ weeks running
   - 🧪 Test — active experiment with hypothesis + decide-by date
- For any campaign that ENDED this week: change Status to "Ended" and move to Phase 3d (Archive).

Then update the By Location section underneath:
- Recalculate # Active Campaigns per location
- Update Total Spend WTD / Total Sales WTD / Blended ROAS WTD per location
- Refresh Top Performer / Underperformer / Notes per location

### 3b. Ads Reporting tab

For every Sponsored Listing (UE + DD) that ran this week:
- Update Spend / Impressions / Clicks / CTR / Orders / Sales / ROAS / CPO
- Compare to last week's row, populate WoW ROAS column
- Highlight outliers: top 4 by ROAS, bottom 4 by ROAS

Update the Audience Segment Performance table at the bottom (All / New / Existing / Lapsed).

### 3c. Offers Reporting tab

For every promo (DD + UE Offers) that ran this week:
- Update Spend / Sales / Orders / ROAS / New Cx / % New Cx
- Mark Status (Live / Ended / Pending)
- Update Notes column with anything that changed (depth, threshold, audience)

Update the New vs Existing Customer Split table at the bottom.

### 3d. Archive tab — for any campaigns that closed this week

This is Kelly's experiment discipline ask. **Do not let a campaign leave Active without Learnings populated.**

For each closed campaign, add a row to Archive with:
- Year / Quarter / Week ended / Campaign Name / Type / Platform / Locations / Audience
- Threshold / Discount or Ad Spend
- Start Date / End Date / Status (Ended)
- Total Spend / Total Sales / Total Orders / Avg ROAS / New Cx
- Test? (Y/N)
- **Hypothesis** — what we expected to learn
- **Outcome / Learnings** — what actually happened, in one or two sentences
- **Decided to Continue?** — Y / N / Modified

If the campaign predates Jun 2026 and has no documented hypothesis, populate Outcome with "archived without learnings (predates Jun 2026 discipline)" and move on. Don't fabricate retrospective hypotheses.

### 3e. Dashboard tab

The Dashboard pulls most metrics via formulas from Active Campaigns. After 3a is done, the headline numbers should auto-populate. Manually update:
- Top 5 / Bottom 5 active campaigns lists
- This Week's Changes (3-5 bullets, shipped this week)
- Proposed for Next Week (decisions needed from Lauren)
- Decline Alerts table — populate any triggered by:
   - Location WoW < -10%
   - Campaign ROAS below target 2 consecutive weeks
   - Active test failing hypothesis

The Drive Sheet saves automatically — there is no "save as" and no export step. Just confirm your edits landed in the live Sheet.

---

## Phase 4: Duplicate the Notion master template + fill

1. Open the [Notion master template](https://www.notion.so/373d3ff018e781dabe7fc0a8710af031).
2. **Duplicate** it (don't edit the master) into the goop kitchen Documents Hub.
3. Title the duplicate exactly: `📊 W[XX] Weekly Update — [Mon date]–[Sun date], 2026 | goop kitchen`
4. Fill the data placeholders:

### Agenda section
Skip — Maxx writes this Tuesday AM via `client-call-prep` skill.

### Key Highlights — four locked pillars (fill data, leave commentary blank for Ro)

**💰 Payout growth trend**
- Portfolio payout this week: [pull from Weekly Platform Overview 2.0 sheet], WoW %, vs March baseline %
- Lift from: [identify top 3 contributing locations from Sheet v3 Active Campaigns By Location section]
- Drag this week: [calculate -X pt from Net Payout %, identify UE Other Adjustments + DD Other Adjustments]
- Next: [leave blank for Ro]

**📉 Spend % trend**
- Marketing/sales [X%] portfolio
- Discipline: tier breakdown
- Drag: locations stuck above threshold
- ROAS direction: marketing ROAS [X] (was [Y], WoW %)
- Next: [leave blank for Ro]

**🔴 Struggling location performance**
- San Jose + Pasadena sub-section: pull SJ + PA numbers (WoW, $ amounts, conversion, accuracy, organic %, DD vs UE comparison)
- Ops drag sub-section: list any DD avoidable cancel rate > 0.5%, POS error rate > 1%, UE inaccuracy > 1.5%
- Leave "Why not" + "Next" lines blank for Ro

**📊 Campaigns + launches**
- This week's read: $ spend / $ attributed / blended ROAS / # campaigns live (pull from Sheet v3 Dashboard)
- Ads vs Offers ROAS comparison
- The engine: top SLs by ROAS (from Sheet v3 Ads Reporting)
- Coming next cycle: leave blank for Ro
- Launches: pull NRO status from Q-plan tabs

### Platform Performance tables
Populate UE, DD, GH tables from the platform exports (already aggregated in your Phase 2 work). Add the under-table commentary block but leave it blank for Ro.

### Location Performance table
Pull from Sheet v3 By Location section. Include Tier, Total Sales, WoW, ROAS, Payout %, Mkt Spend %, Notes.

### Performance Flags
Leave blank for Ro. She picks the top 5 from what the data surfaces.

### Operations & Quality tables
Populate DD Ops Quality / UE Cancellations / UE Order Accuracy / GH Ops tables from the platform exports.

### Validation table
Fill in the checks (Net Sales formula, Commission % range, Net Payout % range, etc.) so any anomaly is caught before client share.

Save the page.

---

## Phase 5: Handoff

1. Post in `#int-goop-kitchen`:
   > 📊 W[XX] data is loaded. Sheet v3 refreshed + Notion report duplicated and data-filled. Handing to @Ro for commentary by 9 AM PT Tuesday. @Maxx will QA via client-call-prep after that.
2. Add the Notion report URL to the message.
3. Update the `Goop Kitchen | weekly metrics` Google Sheet if Manish hasn't already added this week's row.

---

## When to Run

- Every Monday for the prior week (Mon-Sun) ending yesterday
- Can also be run mid-week for ad-hoc data pulls (decline-alert pulse check) — in that case, skip Phase 4 and Phase 5; just refresh the sheet and surface anomalies in Slack

---

## When NOT to Run

- For any client other than goop kitchen. Other clients use the generic `weekly-reporting` skill.
- Before Sunday midnight — the reporting week isn't closed yet
- Without the Ads Manager export. UE ad attribution is unreliable without it; rerun once it's available

---

## Key Rules

- **The Campaign Sheet v3 is one shared Drive Sheet. Edit in place, never create a new file.** (See the box at the top.) This is the #1 rule — a duplicate breaks the team's link and loses history.
- Do NOT modify the Notion master template page. Only duplicate it.
- Do NOT fabricate retrospective hypotheses for campaigns that predate Jun 2026 discipline. Use the "archived without learnings" tag.
- Do NOT close a campaign in Active without populating Learnings in Archive. The skill enforces experiment discipline.
- The four Highlights pillars are non-negotiable: Payout $ trend / Spend % trend / Struggling locations / Campaigns + launches. Section order is locked.
- If data is missing from any platform, stop and ask. Do not run on partial data.
- Voice in the data fill is neutral. Commentary (the interpretive lines) is Ro's job — leave those blank.

---

## Related Skills

- `client-call-prep` — Maxx triggers Tuesday AM to QA this skill's output + finalize agenda
- `weekly-reporting` — generic version for non-goop clients
- `campaign-planner` — quarterly + campaign strategy work (separate from weekly refresh)
- `hero-image-review` — when running an A/B test on ad creative; logs to Archive

---

*Updated 2026-06-30. v1.1.0: Campaign Sheet v3 migrated from a Maxx-local xlsx to a shared Google Drive Sheet (`1HacQMl83…`) edited in place — fixes the "new file every run" bug when anyone but Maxx ran the refresh. Source: gk <> Spice 6/2 meeting decisions + memory file [[goop-kitchen-campaign-sheet-v3]].*
