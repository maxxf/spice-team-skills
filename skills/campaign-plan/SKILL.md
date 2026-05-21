---
name: campaign-plan
description: >
  Maintain a per-client campaign plan + performance tracker. Internal planning
  lives in the Notion Campaign Planning DB; the client-facing deliverable is a
  formatted Excel workbook (Dashboard + Campaign Tracker + Legend) that rolls up
  performance overall, by platform, and ads vs offers. Triggers on "update
  campaign plan for [client]", "refresh campaign tracker", "campaign performance
  for [client]", "pull campaign data for [client]", "build campaign plan for
  [client]", or when the user drops platform campaign exports and mentions the
  campaign plan. EXECUTION of new campaigns stays with campaign-ops; this skill
  is the planning + performance-tracking layer.
version: 0.1.0
---

# Campaign Plan & Performance Tracker

The campaign plan is a living, per-client deliverable. **Internal:** Notion Campaign Planning DB (`collection://1c8d3ff0-18e7-8067-abff-000b54568283`) where the team plans + coordinates. **Client-facing:** a formatted Excel workbook (Dashboard + Campaign Tracker + Legend) shared in the client's Drive folder. This skill keeps the workbook current from weekly platform data.

The whole point: **the team pulls campaign data files, drops them into the skill, and the shared workbook updates.** Easy loop, no hand-formatting.

---

## The weekly loop (what the GM actually does)

1. **PULL** the campaign performance files (checklist below).
2. **DROP** them in `/tmp/campaign-data-<client>/` (or any folder; point the skill at it).
3. **RUN** the update (one command). The skill matches each platform campaign to a tracker row, updates Spend / Attributed Sales / Actual ROAS / Incremental Orders, pulls any new campaigns from the Campaign Planning DB, and regenerates the formatted workbook.
4. **SHARE** the refreshed workbook (drop into the client's Drive folder, ping the client channel).

Steps 1, 2, 4 are the only manual parts. Step 3 is the skill.

---

## Phase 1: Pull the campaign data files

One folder per client per refresh. Drop these:

### Uber Eats (UE Manager / Ads Manager)
- [ ] **Ads campaign performance** — Marketing → Ads → date range → Export. Per-campaign: spend, attributed sales, ROAS, orders. (Only if `UE Ads Manager Access = Yes`.)
- [ ] **Offers performance** — Marketing → Offers → All offers → Export. Per-offer: redemptions, discount spend, attributed orders.

### DoorDash (Merchant Portal)
- [ ] **Sponsored Listings performance** — Marketing → Sponsored Listings → date range → Export. Spend, attributed sales, ROAS per campaign.
- [ ] **Promotions performance** — Marketing → Promotions → All promotions → Export. Promo type, redemptions, attributed orders.

### Grubhub (for Restaurants)
- [ ] **Sponsored Listings** — Marketing → Sponsored → date range → Export. (If client runs GH paid placement.)

Skip any platform/type the client doesn't run. Note skips in the run.

**Window:** match the campaign plan's reporting cadence (weekly for the Monday refresh; can also run a 30/90-day pull for a fuller dashboard).

---

## Phase 2: Run the update

First-time setup (once per machine): `python3 -m venv .venv && .venv/bin/pip install openpyxl`.

```bash
cd /Users/maxx/Desktop/Cowork/Skills/campaign-plan
.venv/bin/python references/build_campaign_plan_xlsx.py \
  --client "<display name>" \
  --tracker-csv <current tracker rows CSV; omit to use embedded goop sample> \
  --campaign-perf-csv <weekly-reporting OUTPUT/campaign_performance.csv> \
  --output /tmp/<client>_Campaign_Plan.xlsx
```

Add `--overwrite-perf` to replace existing performance cells (default fills only empty ones, so manual entries survive).

The generator:
1. Reads the current tracker state from `--tracker-csv` (or the embedded goop sample if omitted).
2. If `--campaign-perf-csv` is given, folds weekly-reporting's per-campaign performance into the matching tracker rows' Spend / Attributed Sales / Actual ROAS / Incremental Orders (see matching below).
3. Recomputes the Dashboard rollups (overall via COUNTIF/SUM, by platform + ads-vs-offers via SUMIF) and the spend chart.
4. Writes the formatted 3-tab .xlsx.

### Matching weekly-reporting performance to tracker campaigns

The performance source is weekly-reporting's `OUTPUT/campaign_performance.csv` (`Platform, Campaign Type, Location, Spend, Sales, Orders, ROAS`). It carries no in-platform campaign name, so the fold-in matches on a composite key with safeguards:

- **Platform** must match.
- **Type** must match — perf `Campaign Type` is mapped to Ad (contains sponsor/featured/ad/paid/listing) vs Offer.
- **Location overlap** — the perf row's single Location must token-overlap the tracker row's Locations cell (`San Jose / Pasadena` → matches a `San Jose` perf row). Tracker rows targeting `All`/blank match any location.
- **Campaign-name token overlap** — perf `Campaign Type` must share a meaningful token with the tracker row's Campaign or In-Platform Campaign Name. This is what keeps two concurrent live offers on the same platform+stores (e.g. `Spend X Save Y` vs `Friday Depth`) from bleeding into each other.
- **Status gate** — only `Live` and `Ended` rows receive performance. A `Proposed` or `Blocked-on-client` campaign hasn't run, so it stays empty even if a perf row would otherwise match.

All perf rows matching a tracker row are **summed** into it (so per-location perf rolls up to a multi-location campaign). Any perf row that matches **no** tracker row is printed as unmatched for the GM to map to an existing row or add as a new campaign. Never silently drop performance data.

---

## Phase 3: Share

The .xlsx can't be pushed to Drive via MCP (binary upload limit). Two paths:
1. **Manual (today):** the file lands in `/tmp/<client>_Campaign_Plan.xlsx`; copy to `~/Downloads/` and drag into the client's Drive folder. Opens in Sheets or Excel, formatting intact.
2. **Scripted (target):** a local Drive-API upload script (Wk5 infra item) pushes the .xlsx directly, bypassing MCP. Until built, manual.

Then post a one-line heads-up in the client Slack channel pointing at the updated workbook.

---

## The workbook (what the generator produces)

Three tabs:

- **Dashboard** — Highlights callout (qualitative wins), Overall KPIs (live/proposed/blocked counts, total spend, blended ROAS), By Platform table (UE/DD/GH/Meta with spend/sales/ROAS/orders via SUMIF), Ads vs Offers table, spend-by-platform bar chart. Performance cells auto-compute from the tracker.
- **Campaign Tracker** — one row per (campaign × platform). Columns: Campaign, Platform, Type (Ad/Offer), Offer/Ad Detail, Locations, Status, Days in Queue, Flight Start/End, Target ROAS, Actual ROAS, Spend, Attributed Sales, Incremental Orders, In-Platform Campaign Name, Notes. Conditional formatting on Status (Live green / Proposed blue / Blocked-on-client amber / Ended gray).
- **Legend & Cadence** — status + type definitions, the working agreement (Friday update, 24h tactical SLA).

---

## Per-client config (`clients/<slug>.json`)

```json
{
  "client_slug": "goop-kitchen",
  "client_display_name": "goop Kitchen",
  "drive_folder_id": "1UZ2ZX0ntPDGeLai8Dsf7coJFT2i_j0Gs",
  "slack_channel": "#ext-goopkitchen-spice",
  "active_platforms": ["Uber Eats", "DoorDash", "Grubhub"],
  "portfolio_roas_target": 3.5,
  "campaign_db_filter": "goop Kitchen"
}
```

---

## How it connects to the rest of the system

- **Internal planning → Notion Campaign Planning DB.** When Spice plans + adds a campaign, it goes here first (via `campaign-ops` or manually). This skill reads new campaigns from the DB into the tracker.
- **Execution → `campaign-ops`.** A Proposed campaign, once client-approved, hands to `campaign-ops` for in-platform setup. The in-platform name campaign-ops assigns is what this skill matches performance on. No double-entry: plan proposes, campaign-ops executes, this skill tracks.
- **Diagnostic triggers → Proposed campaigns.** Diagnostic findings emit `{skill: "campaign-plan", params: {focus: cost_recovery|scale|awareness|promo_consolidation, stores}}`. These become Proposed rows in the tracker.
- **Performance feed → `weekly-reporting` outputs.** Weekly-reporting already parses every platform's transaction + sponsored-listing + promotion exports and emits `OUTPUT/campaign_performance.csv` (per-campaign spend / attributed sales / ROAS / orders, all platforms). The campaign plan **reads that file as its primary performance source** so the team never double-pulls the same exports. The Phase 1 raw exports are the fallback for clients/weeks where weekly-reporting hasn't run.

---

## Why a separate workbook, not the weekly tracker

The team already maintains a per-client **weekly tracker** Google Sheet (Weekly Platform Overview + By Location tabs, fed by `weekly-reporting`). The campaign plan is a **separate** workbook, not new tabs in that sheet. Three reasons this is deliberate:

1. **Different artifact lifecycle.** The weekly tracker is *append-only history* — Ops pastes one new value column every week and the WoW / 4-week-avg formulas depend on that intact history. The campaign plan is *regenerated wholesale* by the generator on every refresh. Embedding a regenerated artifact inside an append-only one means a campaign refresh could clobber weeks of tracker history. Structurally incompatible.
2. **Different owner + cadence.** Weekly tracker = Ops (Manish/Dulari), pasted Mon as part of weekly-reporting. Campaign plan = GM (Ro), refreshed Fri. Two owners writing the same file = collisions and unclear accountability.
3. **Different layer.** The weekly tracker / scorecard is the **performance layer** (what happened across the whole account). The campaign plan is the **campaign layer** (what we're running, proposing, blocked on, and why). Keep the layers separate and *link* them — don't fuse them. The two stay consistent because the campaign plan sources its numbers from weekly-reporting's `campaign_performance.csv` (above), not from a parallel pull.

To kill link sprawl: link the campaign plan workbook and the weekly tracker to each other from the client's Drive folder + Notion client page, so the client has one place to find both.

---

## Build status (v0.1.0)

- ✅ Workbook generator (`references/build_campaign_plan_xlsx.py`) produces the formatted 3-tab .xlsx with dashboard rollups + chart + conditional formatting. goop's instance built 2026-05-21.
- ✅ **Separate-workbook decision locked (2026-05-21).** Campaign plan is its own .xlsx, not tabs in the weekly tracker. Rationale in "Why a separate workbook" above.
- ✅ **Performance auto-feed from `weekly-reporting` (built 2026-05-21).** `--campaign-perf-csv` folds weekly-reporting's `campaign_performance.csv` into the tracker performance columns — no double-pull. Match key + safeguards documented under "Matching" in Phase 2. Validated on goop: 4 live rows filled with correct per-location sums, Blocked/Proposed rows left empty, concurrent same-platform offers kept separate, unmatched perf rows surfaced.
- 🚧 Direct platform-export parsing (the raw UE/DD/GH exports, for clients/weeks where weekly-reporting hasn't run): still needs real export samples. Largely subsumed by the auto-feed above once `campaign_performance.csv` is the source.
- 🚧 Per-client config intake + Campaign Planning DB read: design in this SKILL.md, wiring pending.
- 🚧 Scripted Drive upload: blocked on MCP binary limit; needs a local Drive-API script.

---

## Anti-patterns

- Don't hand-format the workbook. Run the generator; it formats.
- Don't maintain the plan in two places. Notion DB is internal source; the workbook is the client render. The skill bridges them.
- Don't duplicate execution. Setup stays with `campaign-ops`.
- Don't silently drop unmatched platform campaigns. Surface them for mapping.
- Don't share a stale workbook. Refresh from the latest exports before sending.
