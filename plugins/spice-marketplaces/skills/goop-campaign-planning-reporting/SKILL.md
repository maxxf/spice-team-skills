---
name: goop-campaign-planning-reporting
description: >
  goop kitchen Monday refresh end-to-end. Runs the deterministic campaign-plan
  refresh (which updates goop's Campaign Tracker Google Sheet IN PLACE — Dashboard,
  Active Campaigns, Ads/Offers Reporting, History, Archive, Account Learnings, charts,
  QA), then has the GM curate the planning tabs, then duplicates the Notion weekly
  report master template and fills the data placeholders for client review. Trigger on
  "goop weekly refresh", "goop Monday refresh", "update goop sheet", "build goop weekly
  report", "run goop weekly reporting", or any request to refresh goop kitchen's reporting
  stack for a given week. GOOP KITCHEN ONLY. For other clients use the generic
  weekly-reporting / campaign-plan skills.
team: marketplace
version: 2.0.0
---

# goop Campaign Planning & Reporting

The Monday refresh. Produces two artifacts:

1. **Updated Campaign Tracker** (the Google Sheet) — refreshed **in place** by the deterministic `campaign-plan` refresh. Reporting tabs are written programmatically; the GM curates the planning tabs.
2. **Updated Notion weekly report** (duplicated from the [master template](https://www.notion.so/373d3ff018e781dabe7fc0a8710af031), data filled, handed to Ro for commentary).

Cadence: Monday. Not Friday. Reasoning is in the memory file and the master template header.

Owner: Santi.

---

## ⚠️ How goop's sheet actually works — read this first

**The Campaign Tracker is ONE live Google Sheet, updated in place by a script. You never build it by hand and never create a new file.**

- **Canonical sheet:** *goop kitchen — Campaign Tracker* → https://docs.google.com/spreadsheets/d/1C75jl5NBmGjTHOhUcf9Pky9eLzI3uYh4R6JlTT34kZA/edit
  (`sheet_id 1C75jl5NBmGjTHOhUcf9Pky9eLzI3uYh4R6JlTT34kZA`, recorded in `campaign-plan/clients/goop-kitchen.json`.)
- **How it updates:** the `campaign-plan` skill's `refresh.py` runs in **v2 mode** for goop (`"v2": true` in the config). It writes the reporting tabs **directly into that Sheet via the Sheets API** — Dashboard, Active Campaigns, Ads Reporting, Offers Reporting, History, Archive, Account Learnings, embedded charts — and runs a structural QA pass. It does **not** generate an `.xlsx` and does **not** replace the file, so it never touches the GM-owned planning tabs.
- **Two tab families in that one sheet:**
  - *Script-owned (don't hand-edit):* Dashboard, Active Campaigns, Ads Reporting, Offers Reporting, History, Account Learnings (auto-draft), `_Inputs`, `_ChartData`. The refresh overwrites these every run.
  - *GM-owned (you maintain by hand, in the same sheet):* Q2/Q3/Q4 Plan, Experiments, Conversion Rate, Notes & Definitions, and the **curated** Hypothesis/Outcome/Continue? columns in Archive.

**NEVER do this:**
- ❌ Don't open or "save as" a local `.xlsx` (the old `goop_kitchen_campaign_template_v3.xlsx` is **retired**).
- ❌ Don't create a new spreadsheet or duplicate the Tracker. A new file = broken link + lost history. This was the old failure mode that produced "a new file every run."
- ❌ Don't hand-type numbers into the script-owned tabs — they get overwritten. Fix the inputs and re-run instead.

**FAIL LOUD:** if `refresh.py` errors (sheet unreachable, missing service-account key, missing exports), **STOP**. Post in `#int-goop-kitchen` with the error. Do **not** work around it by building a file by hand — a delayed refresh beats a broken duplicate.

---

## Phase 1: Confirm inputs

- **Week date range** (Mon-Sun). Default: the week that ended yesterday (Sunday). The refresh defaults to last completed week; pass `--as-of YYYY-MM-DD` for a specific week.
- **`campaign-plan` skill present** and the Sheets service-account key is on this machine (`~/.config/spice/google-sheets-writer.json`). If the key is missing, the refresh fails loud — get the key, don't work around it.
- **Tracker reachable** — open the [Campaign Tracker](https://docs.google.com/spreadsheets/d/1C75jl5NBmGjTHOhUcf9Pky9eLzI3uYh4R6JlTT34kZA/edit) and confirm you can see it.
- **Notion master template** still locked at `https://www.notion.so/373d3ff018e781dabe7fc0a8710af031` (only duplicate it, never edit the master).

If anything's missing, stop and surface it.

---

## Phase 2: Gather platform exports

Pull the files below and drop them where the refresh reads inputs — either the goop **Drive** folder `Campaign Plan Inputs/<weekstart>/` (the refresh auto-pulls these) or the local `inputs/` folder under the campaign-plan data dir. The refresh parses them by content, so exact filenames are flexible, but pull everything — missing files mean missing attribution.

### Uber Eats (required)
- [ ] Transaction / Payment export (settlement) — UE Manager → Reports → Payment Details. Per-order revenue + offer attribution; primary source for UE numbers.
- [ ] Campaign Summary by Location (ads) — `advertiser.uber.com/reports/create-v2`, date-filtered. **Without it, ad-driven orders count as organic.**
- [ ] Order Accuracy — UE Manager → Reports → Order Accuracy.
- [ ] Offers / Campaigns — UE Manager → Marketing → Campaigns → Export.
- Optional: Menu downtime; Customer ratings (if pulling for a ratings-flyer cycle).

### DoorDash (required)
- [ ] Financial Simplified Transactions — Financials → Transactions.
- [ ] Error Charges — Financials → Error Charges.
- [ ] Sponsored Listing Marketing — Marketing → Sponsored Listings → Performance Export.
- [ ] Promotions Marketing — Marketing → Promotions → Performance Export.
- [ ] Ops Quality (aggregate + cancellations) — Operations → Ops Quality → Export.

### Grubhub (required)
- [ ] Financial transactions, Financial summary, Ops review — GH for Business → Reports.

### Reference (do not modify, just read)
- **Weekly Platform Overview 2.0 sheet** — `18we-M-qVdug4LRZiolfScL3emVPE0AuL4Zb9Zqn_A3A`. Source of truth for portfolio payout $, spend %, ROAS history. The refresh cross-pulls this for the marketing-efficiency metrics; the Notion Highlights cite it for the 13-week trend. Make sure Manish has dropped this week's row.

---

## Phase 3: Run the refresh (updates the Tracker in place)

From the `campaign-plan` skill directory:

```bash
python references/refresh.py --client goop-kitchen
# or for a specific week:
python references/refresh.py --client goop-kitchen --as-of 2026-06-22
```

This pulls inputs (Drive + local), projects the Notion Campaign Planning DB rows, then writes the **script-owned** tabs of `1C75jl5…` in place: Active Campaigns by location, Dashboard (with canonical Mkt Spend % / ROAS / CPO + WoW), Ads Reporting, Offers Reporting, History (this week's snapshot), auto-files ended campaigns to Archive, auto-drafts an Account Learnings signal, embeds charts, and runs a structural QA pass.

**Watch the output:**
- It prints `Live Sheet: https://docs.google.com/spreadsheets/d/1C75jl5…` — confirm that's the canonical Tracker, not a new id.
- It prints `QA: ✓ structure valid` or lists issues. If issues, fix the inputs and re-run before sharing.
- If it errors out, **fail loud** (Phase 0 rule) — don't hand-build anything.

> Note: if `campaigns_json` (the Notion DB pull) isn't present yet, run the campaign-plan skill's Notion pull step first (it writes the DB rows the refresh reads). The skill's Phase 0 covers this.

---

## Phase 3b: GM curation (by hand, in the same sheet)

The refresh handles the reporting tabs. You still own, directly in `1C75jl5…`:

- **Archive Learnings** — the refresh files ended campaigns with the numbers; **you** fill Hypothesis / Outcome / Decided to Continue? This is Kelly's experiment discipline. Don't let a campaign sit in Archive without a Learning. For pre-Jun-2026 campaigns with no documented hypothesis, write "archived without learnings (predates Jun 2026 discipline)" — don't fabricate.
- **Experiments tab** — update status / decide-by dates on active tests.
- **Q2/Q3/Q4 Plan tabs** — reflect anything shipped or newly planned this week.
- **Dashboard narrative cells** the script leaves for you: This Week's Changes (3-5 bullets), Proposed for Next Week (decisions for Lauren), and any Decline Alerts the data triggers (location WoW < -10%, campaign ROAS below target 2 wks, a test failing its hypothesis).

---

## Phase 4: Duplicate the Notion master template + fill

1. Open the [Notion master template](https://www.notion.so/373d3ff018e781dabe7fc0a8710af031).
2. **Duplicate** it (don't edit the master) into the goop kitchen Documents Hub.
3. Title the duplicate exactly: `📊 W[XX] Weekly Update — [Mon date]–[Sun date], 2026 | goop kitchen`
4. Fill the data placeholders (pull from the freshly-refreshed Tracker + the Weekly Platform Overview sheet):

### Agenda section
Skip — Maxx writes this Tuesday AM via `client-call-prep`.

### Key Highlights — four locked pillars (fill data, leave commentary blank for Ro)

**💰 Payout growth trend** — portfolio payout this week (from Weekly Platform Overview 2.0), WoW %, vs March baseline %; top 3 contributing locations (Tracker → Active Campaigns by location); drag (-X pt from Net Payout %, UE + DD Other Adjustments); Next: blank for Ro.

**📉 Spend % trend** — marketing/sales % portfolio; tier discipline breakdown; locations stuck above threshold; marketing ROAS direction (X vs Y, WoW %); Next: blank for Ro.

**🔴 Struggling location performance** — San Jose + Pasadena (WoW, $ amounts, conversion, accuracy, organic %, DD vs UE); ops drag (DD avoidable cancel > 0.5%, POS error > 1%, UE inaccuracy > 1.5%); "Why not" + "Next" blank for Ro.

**📊 Campaigns + launches** — this week's read ($ spend / $ attributed / blended ROAS / # live, from Tracker Dashboard); Ads vs Offers ROAS; top SLs by ROAS (Tracker Ads Reporting); NRO/launch status (Q-Plan tabs); Coming next: blank for Ro.

### Platform Performance tables
Populate UE / DD / GH tables from the exports. Leave the under-table commentary block for Ro.

### Location Performance table
Pull from the Tracker's by-location view: Tier, Total Sales, WoW, ROAS, Payout %, Mkt Spend %, Notes.

### Performance Flags
Leave blank for Ro (she picks the top 5).

### Operations & Quality tables
Populate DD Ops Quality / UE Cancellations / UE Order Accuracy / GH Ops from the exports.

### Validation table
Fill the checks (Net Sales formula, Commission % range, Net Payout % range, etc.) so anomalies are caught before client share.

Save the page.

---

## Phase 5: Handoff

1. Post in `#int-goop-kitchen`:
   > 📊 W[XX] data is loaded. Tracker refreshed in place + Notion report duplicated and data-filled. Handing to @Ro for commentary by 9 AM PT Tuesday. @Maxx will QA via client-call-prep after that.
2. Add the Notion report URL to the message.
3. Confirm this week's row is in the `Goop Kitchen | weekly metrics` sheet (Manish usually adds it).

---

## When to run
- Every Monday for the prior completed week (Mon-Sun).
- Mid-week ad-hoc pulse check: run Phase 3 only (skip Notion + handoff) to refresh the Tracker and surface anomalies.

## When NOT to run
- Any client other than goop kitchen (use generic `weekly-reporting` / `campaign-plan`).
- Before Sunday midnight — the week isn't closed.
- Without the UE Ads Manager export — ad attribution is unreliable; rerun once it's available.

---

## Key rules
- **The Tracker (`1C75jl5…`) is updated in place by `refresh.py`. Never hand-build it, never create a new file.** This is the #1 rule.
- Script-owned tabs are overwritten every run — fix inputs and re-run, don't hand-edit them.
- Don't modify the Notion master template — only duplicate it.
- Don't close a campaign without a curated Learning in Archive (Kelly's discipline).
- Don't fabricate retrospective hypotheses for pre-Jun-2026 campaigns — use the "archived without learnings" tag.
- The four Highlights pillars + their order are locked: Payout $ / Spend % / Struggling locations / Campaigns + launches.
- If data is missing from any platform, stop and ask. No partial runs.
- Data fill is neutral. Interpretive commentary is Ro's job — leave those lines blank.

## Related skills
- `campaign-plan` — the engine behind Phase 3 (the v2 refresh that writes the Tracker). Also handles quarterly strategy.
- `client-call-prep` — Maxx triggers Tuesday AM to QA this output + finalize the agenda.
- `weekly-reporting` — generic version for non-goop clients.
- `hero-image-review` — when A/B testing ad creative; logs to Archive.

---

*Updated 2026-06-30. v2.0.0: rewired from hand-editing a Maxx-local xlsx to running the deterministic `campaign-plan` v2 refresh, which updates the canonical Campaign Tracker Sheet (`1C75jl5…`) in place. Fixes the "new file every run" bug — that was the old prose skill having non-Maxx operators hand-build a file that only existed on Maxx's laptop, not a missing key. Source: gk <> Spice 6/2 decisions + memory [[goop-kitchen-campaign-sheet-v3]].*
