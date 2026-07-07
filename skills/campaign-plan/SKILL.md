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
  campaign plan. ALSO triggers on "plan strategy for [client]", "build the
  [client] roadmap", "tier strategy for [client]", "analyze [client] campaigns" —
  see the Mode router. EXECUTION of new campaigns stays with campaign-ops; this
  skill is the planning + performance-tracking + strategy layer.
version: 0.2.5
---

# Campaign Plan & Performance Tracker

The campaign plan is a living, per-client deliverable. **Internal:** Notion Campaign Planning DB (`collection://1c8d3ff0-18e7-8067-abff-000b54568283`) where the team plans + coordinates. **Client-facing:** a formatted Excel workbook (Dashboard + Campaign Tracker + Legend) shared in the client's Drive folder. This skill keeps the workbook current from weekly platform data.

The whole point: **the team pulls campaign data files, drops them into the skill, and the shared workbook updates.** Easy loop, no hand-formatting.

---

## Mode router (START HERE)

When this skill triggers, resolve to one of three modes. **Route directly when the trigger is explicit; otherwise ask the user to pick.**

| Mode | What it does | Writes | Example triggers |
|---|---|---|---|
| **Update reporting sheet** | The automated weekly refresh (exports → Dashboard/Ads/Offers/History) — Phases 0–3 below | Sheet (reporting tabs) | "refresh campaign plan", "update campaign tracker", "pull campaign data" |
| **Plan campaigns** | Interactive tier → strategy → events → roadmap session — Phase S below | Notion strategy page · Q-plan tabs · Notion DB rows (`Not started`) · client config | "plan strategy for [client]", "build the roadmap", "tier strategy" |
| **Run analysis** | Read-only Q&A over the live sheet + History (declines, incrementality, what's working) | none | "analyze [client]", "why did X drop" |

**Run analysis is purely conversational:** run `strategy_read.py --client <slug>`, read History if the question needs trend, answer in chat citing playbook rules where relevant. No dedicated script, no writes, no artifacts. If the user asks for something that requires writing (a findings doc, a tier change), offer to switch modes.

---

## Phase S: Plan campaigns (interactive strategy + roadmap session)

The strategic layer. Claude drives the conversation; Python does only deterministic I/O
(`references/strategy_read.py` read, `references/strategy_write.py` write). The canonical rubric
lives at `references/tier-framework.md` — **load it before the tier gate.** The design authority is
`specs/2026-06-11-strategy-roadmap-design.md` (edge cases: no diagnostic → propose from
performance only and say so; new client → defaults + more questions; unmatched locations →
surface and ask, never guess; envelope vs %-of-sales conflict → show both, user picks; re-order
stale >1 quarter → flag, proceed on explicit OK only).

**Brand-agnostic rule (binding):** no client names or brand assumptions in any logic — everything
flows from `clients/<slug>.json`. A new client is a config file, nothing else.

### S1. Read

```bash
python3 references/strategy_read.py --client <slug>
```

Returns per-location merged data: `saved` (last session's tier/goal/re-order from config
`tier_strategy`), `diagnostic` (Green/Yellow/Red color), `performance` (canonical ROAS / spend% /
mkt-driven% / sales), `flags` (`reorder_stale`, `perf_above_tier`, `perf_below_tier`), plus
`unmatched` lists. Also read `references/tier-framework.md`.

### S2. Tier gate (approval #1 — nothing proceeds without it)

Render the per-location scorecard as a markdown table:

`Location · Goal (proposed → confirm) · ROAS · Spend% · Menu conv · Ops · Capacity · Re-order (saved → confirm) → Proposed tier · Why`

- Seed tiers via the vocabulary map in tier-framework.md (colors inform, scorecard speaks 5-tier).
- **Always render tiers with their emoji** (🟢 Top · 🔵 Mid · 🟠 Low · 🟣 New · 🔴 Red) in the
  scorecard, the roadmap draft, and the Notion page — the sheet writer paints matching row tints
  automatically. One visual language everywhere (legend in tier-framework.md).
- **Data-source note:** `strategy_read.py` supplies color + ROAS/spend%/mkt-driven%/sales only.
  Menu conv / Ops / Capacity have no wired source — render "—" and ask the GM to fill or confirm
  at the gate. Never invent values.
- Flag movers with reasons; flag stale re-orders; prompt for missing re-order rates (GM captures
  manually from platforms) and `opened` dates for new-looking locations.
- Color-term adjustments ("keep Pico Yellow") get mapped via the table and confirmed back.
- On approval, persist: write `{"locations": {...}}` to a temp JSON and run
  `strategy_write.py --client <slug> --config <file>` (the script merges keys, so each gate's
  write preserves the others).

### S3. Per-tier strategy (approval #2)

For each approved tier, recommend a strategy block — **every line cites its playbook rule**
(`references/playbooks/`):

- **Spend** — default band from tier-framework.md (% of tier sales); if the user gives a budget
  envelope, allocate it instead and show both. 55/45 acquisition/retention baseline tilted by
  re-order logic. Show suggested $ from current sales.
- **Campaign types** — location-based only, never keyword (meta-rule 3); matched to tier + each
  location's goal (Top: loyalty/retention + stepped-pullback tests · Mid: per goal ·
  Low: acquisition offers + ops/menu fix workstream · New: awareness + flyer play · Red: none).
- **Segmentation** — **all non-New stores run ads SPLIT by audience (New/Existing/Lapsed) with a
  budget cap per segment**, never one blended campaign — it's how you separate acquisition from
  cannibalization and protect net payout (cap the existing-customer line on mature stores). New
  tier runs blended/awareness until it has a base (add segmentation at the 60-day re-tier). The
  per-segment caps split the tier's spend band; mix is re-order-adjusted.
- **Cadence/exit** — creative refresh by wk 4–5, spend-down schedule planned at entry (meta-rule 5).

User approves/edits per tier → persist `{"tiers": {...}}` via `--config`.

### S4. Events

Ask: NROs/launches + dates? LTOs/menu drops? Client moments? Blackout weeks? Pre-fill US holidays
inside the window for confirm/add — brand events only ever come from this Q&A, never from code.

### S5. Roadmap gate (approval #3)

Draft the rolling ~90-day (13-week) grid in chat as a markdown table grouped by tier, events band
on top, **one lane per location × platform** (DD/UE/GH — only platforms the location actually
runs). **Cells must be tactical — an ops analyst executes them without asking questions:**
mechanic + actual weekly $ (computed from that location's latest weekly sales × the band %) +
the action verb. `SL $2.2K/wk`, `Cut offers $7.0K→$3.3K/wk`, `TEST: SL cut $2.2K→$1.1K/wk`,
`READ: tot sales vs 4wk base; dip <5% ⇒ keep cut` — never abstract directives like
"Pullback −50%" or "walk down" without the dollar figures. Tests carry their read rule in the
read-week cell. Default platform split per playbook: DD carries offers/depth + loyalty (payout
math), UE carries SLs + first-order, **GH carries Sponsored Placement + GH loyalty for clients
running Grubhub paid** — the GH lane (orange label) appears for any location where the client
runs GH; never silently omit a platform the client is on. Iterate until approved.

**Comp methodology for every test read and baseline (canonical):**
1. **Baseline = clean trailing 4 weeks** — exclude holiday-push weeks, outages, and one-off
   depth promos from the window (a July 4 push in the baseline fakes a dip).
2. **Read deliberate changes as diff-vs-controls, never raw pre/post** — controls = matched
   same-tier/same-goal stores with stable spend through the test window. Effect = test store's
   Δ% minus controls' Δ%; a raw pre/post can't separate "we changed spend" from "the market
   moved." Threshold gaps (e.g. <5% ⇒ non-incremental) live in the read-week cell.
3. **YoY same-weeks is a sanity check only** where clean prior-year data exists — store mix
   and engagement effects distort it as a primary comp.

### S6. Write (only after final approval)

1. Build the grid JSON (spec §Interfaces) →
   `strategy_write.py --client <slug> --grid grid.json --check` first. If any target tab is
   non-empty, show the user what's there and get an explicit confirm, then re-run with
   `--overwrite`. Empty tabs write directly (no `--overwrite` needed). This is the ONE authorized
   writer for Q-plan tabs; the weekly refresh never touches them.
2. **Notion strategy page** (client-shareable) via Notion MCP. **Keep it tight and scannable — a
   client reads it in 2 minutes, it is NOT the full plan (that's the sheet).** Canonical structure,
   in this order, nothing more by default:
   1. **Why this quarter** — 3–4 sentences. The thesis + the ≤X% guardrail.
   2. **Strategy by tier** — ONE table, one row per tier: `Tier · Locations · Goal · Spend band ·
      What runs`. Do **not** write a prose section per tier (that's what bloated goop v4).
   3. **What we're testing** — short list, only the live experiments (skip if none).
   4. **Roadmap** — one line pointing to the sheet's Q-plan tabs for week-by-week detail. Don't
      restate the grid.
   Optional, one line each, only if they apply: a holiday-scheme line; a "vs client forecast" line.
   Everything granular (per-platform cells, $ by week, campaign briefs) lives in the sheet + DB,
   not the page. First run: resolve the client's Documents Hub via Notion search, confirm
   destination with the user, cache `notion_parent_page_id` + `notion_strategy_page_id` via
   `--config`. Later runs update the cached page.
3. **Planning DB**: push each planned campaign through `references/add_campaign.py` with status
   `Not started` and `--notes "Roadmap <window>"` (lands in the "Performance Notes" property) so
   campaign-ops picks them up — no double-entry.
4. Suggest the GM share the Notion page + updated sheet with the client.

---

## Strategy authorship — consult the playbooks every time

**Every campaign plan refresh and every new campaign proposal MUST be checked against the Spice playbooks.** They live at:

- `references/playbooks/what-works.md` — proven plays (data → action → result, with receipts).
- `references/playbooks/marketplace-playbook.md` — the operating framework (foundations, attribution, incrementality, platform intel).

These aren't reference reading; they're the **strategy filter**. When authoring the strategy summary, proposing new campaigns, or refreshing the plan, run the proposal through these rules:

**The Governing Law (above the meta-rules) — the Spend Maturity Curve.** 3P marketing spend is acquisition spend wearing a conversion costume: a dollar's ROI depends on where the location sits on its awareness curve, not how well it performs. Mature → spend cannibalizes (pull it, payout lifts); new/dark → spend is the acquisition engine (pull it, it bleeds). ROAS is a *position on the curve, not a grade* — never rank stores on raw ROAS; locate them with incrementality tests. The whole tier framework operationalizes this. Full statement + proof points: `references/playbooks/marketplace-playbook.md` §0 and `references/tier-framework.md`.

**The 7 Meta-Rules (non-negotiable):**
1. **Fix the menu before spending on ads.** Below 20% menu conversion, the algorithm buries you. Don't propose paid acquisition for a location under threshold.
2. **Ratings velocity > rating score.** Propose the flyer play (Sunnyvale playbook) before propose ad spend for ratings-soft locations.
3. **Location campaigns crush keyword campaigns** (31.5x vs 2.4x). Never propose keyword spend; always location-based.
4. **Retention delivers 14x better ROAS than acquisition.** Default split is 55/45 acquisition/retention, not 80/20. Segment offers by New/Existing/Lapsed.
5. **Every campaign decays — plan exit before entry.** Multi-week campaigns must include creative refresh by week 4-5 + a spend-down schedule.
6. **DoorDash first for new clients** (89% vs 78% UE payout). Don't split spend evenly across platforms; follow the payout math.
7. **Prove causality, not correlation.** Build a measurement test into every meaningful new spend (Counter Service $600-test template).

**Frameworks to apply (from `marketplace-playbook.md`):**
- **Cardinal Rule check** — foundations gate (rating ≥4.5, error <2%, uptime >95%, photos 90%+, +15-20% delivery markup). Block proposals at locations failing the gate; route to ops/menu/photo work first.
- **Attribution decomposition** — never report blended CPO without per-location, per-platform decomposition (the goop UE attribution lesson).
- **Incrementality** — for established locations, propose stepped-pullback tests over more spend.
- **Radius / overlap awareness** — for multi-location urban clients, flag campaigns in overlap zones (the Larchmont 4-way collision lesson).
- **Promo strategy matrix** — match offer mechanic to the goal (new acquisition, reactivation, AOV lift, visibility).

**How this surfaces in the deliverable:**
- The **strategy summary** (section 2 of the plan) cites which playbook rules drove this cycle's choices.
- The **hypotheses** section (section 6) frames tests in the Counter-Service-style causality format.
- **Proposed campaigns** in the Campaign Tracker include a `Notes` annotation citing the proven pattern they apply (e.g., "Sunnyvale flyer play applied at SoMa launch") or the rule they intentionally violate (with justification).

**When refreshing a plan, scan the playbooks for a relevant precedent first.** If goop's SJ won at 25%→33% conversion via aggressive Spend X Save Y, that's the template for the next under-converting location, not a new improvisation.

---

## Two halves: planning, then reporting

The campaign plan has two data flows. Keep them straight:

- **Planning (Phase 0)** builds the *rows* — the campaigns, their statuses, the approval queue. Source of truth is the **Notion Campaign Planning DB**. The skill reads it and projects each campaign into tracker rows. This is what makes the plan a plan.
- **Reporting (Phases 1-2)** fills the *performance columns* on rows that are Live/Ended — Spend / Attributed Sales / Actual ROAS / Incremental Orders. Source is `weekly-reporting`'s output. This is what makes the plan a tracker.

Run Phase 0 first (rows exist), then layer reporting on top. A brand-new client with no performance yet still gets a complete plan from Phase 0 alone.

## Scope: campaigns, not profitability (clarified 2026-06-05)

This Sheet is the **campaign performance** deliverable — what's running, ad/offer spend, attributed sales, ROAS, orders, new-customer acquisition, by-platform, by-segment, the ads funnel, the forward calendar. **Payout, net-payout %, and profitability live in the separate weekly reporting sheet** — not here. The Dashboard carries a subtitle saying so. When refocusing or adding sections, keep this line: campaign metrics here, profitability there.

This scope split also resolves the DoorDash data-settlement timing problem (below).

## Where the implementation plan lives: Notion, NOT the sheet (clarified 2026-06-23)

The sheet holds **reporting** (Dashboard/Active Campaigns/Ads/Offers/History/Experiments) and the **strategy plan grid** (Q-plan tabs). It does **NOT** hold the tactical *implementation / setup plan* — the per-location × platform execution checklist (set up / adjust / pause, in-platform campaign names, budgets, who-does-what). **That lives in Notion**, authored via the **campaign-ops** skill: the Task Tracker ticket (the brief + checklist, assigned to ops with an approval contact) plus the Campaign Planning registry entries. Do **not** create a "Setup"/"Implementation" tab in the campaign tracker — execution belongs in Notion where it's assignable, status-trackable, and notifiable; the sheet stays a clean reporting + plan artifact. The weekly Slack briefing's "changes shipped" bullet (weekly-reporting skill) is the read-out of those Notion records.

## The cadence + the DoorDash settlement timing (refined 2026-06-05)

**The DD settlement reality:** DoorDash financials for a Mon–Sun week don't settle until **Tuesday**. So a Monday refresh has *incomplete DD payout data*. **But** the campaign data this Sheet cares about — ad spend, attributed sales, ROAS, orders — comes from the **Ads Manager + Promotions exports, which ARE available Monday.** It's only net-payout/profitability (the *other* sheet's job) that needs to wait for Tuesday settlement. Because this Sheet is campaign-focused, **Monday works for the campaign plan.**

**Client preference — ask each client, store in config.** Some clients want the Monday flash (campaign read, DD payout still settling); others prefer to wait for Tuesday's complete picture. Per-client config field `"reporting_day": "monday_flash" | "tuesday_complete"`:
- `monday_flash` (default for campaign-focused clients) — refresh Monday on available campaign data; note "DD payout settles Tue" where any payout figure appears.
- `tuesday_complete` — hold the refresh + client note until Tuesday when DD has settled.

**GM question to ask each client** (one time, at kickoff or next sync): *"For your weekly campaign update — do you want it Monday with DoorDash numbers still settling, or Tuesday once everything's final? Campaign performance (spend, ROAS, orders) is ready Monday either way; only DoorDash payout finalizes Tuesday."*

## The cadence

- **Sheet refresh = as-needed when performance warrants** — a campaign hits decline, a new test starts, a launch lands, the data tells a new story. The skill is designed to be invoked any day; there's no fixed "refresh every Monday" rule. The refresh's gate is "did anything change worth communicating?"
- **Communication day = per client's `reporting_day`** (Monday flash or Tuesday complete). The GM sends a short Slack note with the week's plan changes + key moves.
- **Friday is the GM strategy / queueing day.** Review the week, update Notion DB statuses (campaigns moving from Brief → Client Review → Scheduled → Complete), queue Proposed campaigns.
- Weekly-reporting + scorecard remain separate skills / deliverables (those own profitability + settlement-dependent numbers).

## The weekly loop in practice

1. **PLAN (GM, ongoing)** — Notion DB is the source of truth. Every campaign logged with current Status, Segment, Locations, Start/End Date, ROAS Target. Set **Client Review Since** when items enter client review. If it's not in the DB, it's not in the plan.
2. **PULL (Ops, when fresh data is available)** — drop platform exports into the client's **`Campaign Plan Inputs / <weekstart>/`** Drive folder. Typically Sun night or Mon AM after weekly-reporting runs.
3. **RUN (GM, when warranted)** — regenerate the live Sheet in place + **produce a Slack draft** in Ro's format. **⚠ Writing the live Sheet needs the Google service-account key at `~/.config/spice/google-sheets-writer.json`, which the Cowork sandbox does NOT have** — a Cowork run now fails fast with instructions instead of erroring silently. Run where the key + open network live: **`./run_local.sh <client>`** on your own Mac (one-time setup in RUN-LOCALLY.md), or Slack **`@Spicy publish the <client> campaign sheet`** to run it on the always-on Mac Mini. Either way the skill pulls the Drive folder + Notion DB, then writes the Sheet.
4. **COMMUNICATE (GM, Monday)** — review the Slack draft, edit, send to `#ext-[client]-spice`. The Sheet link is stable; the note explains what moved.

### The Monday Slack note (GM-authored from a draft the skill provides)

The skill produces a draft after each refresh in **Ro's bullet format**. The GM edits + sends manually — **no auto-send**. Format:

```
Team sharing campaign updates

• **[bold lead-in with key metric/move].** [Context]. [Recommended action].
• **[Specific result].** [Numbers]. [Hold/shift/test directive].
• **[Campaign wrap or launch].** [Numbers + date]. [Backfill or next step].
• **[Strategic decision or upcoming item].** [Deadline or context].
```

4 bullets max. Bold lead-in = the headline; sentence after = numbers + context; ends with an active-voice verb (hold, shift, pause, approve, review). Strategist voice, not data dump. Reference: Ro's W22 update (Jun 1 — `$93.5K spend → ~$1M sales, 10.9x blended ROAS …`).

Monthly Store-Ops Leaderboard runs the first Monday of the month (separate cadence).

### Where the inputs live (Drive folder, not direct-to-Claude)

```
1. Active /
  └── <Client> /
       ├── Campaign Plan                       (the live Google Sheet — auto-updates)
       └── Campaign Plan Inputs /
            ├── 2026-05-26/                    (W22 — Monday weekstart)
            │    ├── ue_ads_2026-05-26.csv
            │    ├── ue_offers_2026-05-26.csv
            │    ├── dd_ads_2026-05-26.csv
            │    ├── dd_offers_2026-05-26.csv
            │    └── gh_ads_2026-05-26.csv     (if applicable)
            └── 2026-06-02/                    (W23 — next week's drop)
```

The service account already has access via the "1. Active" share. The skill reads from the weekstart folder for the requested week, downloads to a local temp dir, runs the refresh. **Why folder, not direct attachment:** persistent + auditable ("what data fed W22's refresh?" = one folder open). Same pattern as the diagnostic data pull runbook.

### One-command refresh (the repeatable update)

Each client has a config at `clients/<slug>.json` (display name, data dir, input filenames, output path, Drive folder, Slack channel). Once the inputs are in the data dir, the whole update is:

```bash
cd /Users/maxx/Desktop/Cowork/Skills/campaign-plan
python3 references/refresh.py --client <slug> [--as-of YYYY-MM-DD]
```

`refresh.py` runs three steps: `db_to_tracker.py` (planning) → `build_campaign_plan_xlsx.py` (reporting) → `push_to_sheet.py` (publish). It skips any optional input (perf, ads) that isn't present. The only thing it can't do itself is the Notion pull — the skill writes the DB rows to `<data_dir>/<campaigns_json>` first (Phase 0 Step A), because querying Notion needs the MCP. After that, one command, every time.

**Publish to a live Google Sheet (in place).** When the service-account key is present at `~/.config/spice/google-sheets-writer.json`, `refresh.py` auto-pushes the workbook into the client's Drive folder as a **native Google Sheet** and records its `sheet_id` in `clients/<slug>.json`. The first run creates the Sheet; every later run updates that same file — stable link, same sharing, no manual drag. Pass `--no-push` to skip (produces the .xlsx only). Service-account setup is a one-time admin task: see `references/google-service-account-setup.md`. The robot (`spice-sheets-writer@…`) needs Editor on the client's Drive folder (sharing the parent "1. Active" folder once covers every client).

**Onboarding a new client** = one command (writes config, creates data folder, runs first refresh, creates the live Sheet, records sheet_id):

```bash
python3 references/new_client.py \
  --slug <slug> --display-name "<Display Name>" \
  --drive-folder-id <client's Drive folder under 1. Active> \
  --slack-channel '#ext-<client>-spice'
```

After this runs, the client has a live Sheet in their Drive folder and shows up in the standard `refresh.py --client <slug>` flow. To go from empty to populated, the skill queries the Campaign Planning DB for the client's campaigns and writes them into `<data_dir>/<slug>_campaigns.json`.

---

## Phase 0: Build the plan from the Campaign Planning DB (PLANNING)

The **Notion Campaign Planning DB** (`collection://1c8d3ff0-18e7-8067-abff-000b54568283`) is the single source of truth for what's running, proposed, and blocked. Every delivery campaign should be a row there (`Entry Type = Campaign`), created via `campaign-ops`. The skill reads that DB and projects it into the tracker.

**Step A — query the DB for this client.** Use `notion-search` / `notion-fetch` scoped to the data source, filtered to the client (the `Client` relation) and `Entry Type = Campaign`. Normalize each page into a JSON array of objects keyed by DB property name (`Campaign name`, `Channels`, `Campaign Type`, `Offer Details`, `Locations`, `Customer Segment`, `Status`, `Start Date`, `End Date`, `ROAS Target`, `Actual ROAS`, `Performance Notes`, `Client Review Since`). Save to `/tmp/campaign-data-<client>/<client>_campaigns.json`.

**Step B — run the bridge** to produce the tracker CSV:

```bash
python3 references/db_to_tracker.py \
  --db-json /tmp/campaign-data-<client>/<client>_campaigns.json \
  --as-of <YYYY-MM-DD; default today> \
  --output /tmp/campaign-data-<client>/<client>_tracker.csv
```

The bridge (1) expands each campaign into one row per **marketplace** channel (UE/DD/GH — Meta/Instagram is intentionally excluded; the campaign plan tracks marketplace only), (2) drops `Canceled`, (3) maps the DB **Customer Segment** to a client-facing bucket (New Only→New, Existing Only→Existing, Lapsed→Lapsed, DashPass→Existing, else All), and (4) **projects the DB's 14 statuses into 5 client-facing ones**:

| DB Status | Client-facing | In approval queue? |
|---|---|---|
| Not started / Drafting / Brief / Design V.1·V.2 / Internal Review | **Proposed** | no |
| Client Review V.1 / V.2 / Final Client Review | **Blocked-on-client** | **yes** — days-in-queue from `Client Review Since` |
| On Hold | **Blocked-on-client** | flag |
| Client Approved / Scheduled, `today < Start` | **Approved** | no |
| Client Approved / Scheduled, `Start ≤ today ≤ End` (or open end) | **Live** | no |
| Client Approved / Scheduled, `today > End` | **Ended** | no |
| Complete | **Ended** | no |
| Canceled | dropped from client view | — |

**Days in queue** requires the `Client Review Since` date property on the DB (added 2026-05-21). `campaign-ops` sets it when a campaign enters a Client Review status. Without it, days-in-queue is blank.

---

## Enforcing standardized output (how we stop divergence)

The off-by-one bug in Santi's hand-built Sheet (data bled into the "Metric" header row, every label paired with the wrong row's numbers) is exactly what standardization prevents. Four enforcement layers:

1. **The skill is the SOLE producer.** No hand-building these Sheets. The writers (`sheets_writer.py`) emit a fixed header row then data beneath — structurally impossible to get an off-by-one. When a richer layout is wanted, add it to the writer, don't build it by hand.
2. **Writers own structure, callers own data.** Headers, column order, alignment (labels LEFT / metrics RIGHT, auto-detected per column), status colors, section layout are all in code — identical across all clients every run.
3. **Post-write validator** (`sheets_writer.py validate`, auto-run at the end of every v2 refresh). Asserts: required tabs present, Active Campaigns header leads with "Campaign Name", and **no aggregate "Metric" header row contains numeric values** (the exact off-by-one detector). A failure is surfaced in the refresh output, not silently shipped.
4. **One Sheet per client, in the client's `1. Active` folder.** No personal-Drive copies. Stable `sheet_id` in config; refreshed in place.

If Santi wants a section his hand-built version has that the skill doesn't (e.g., the W18–W23 Location Trend tab), the move is to add it to the writer so every client gets it — not to maintain a parallel hand-built Sheet.

## Canonical structure: the 9 tabs (target deliverable)

The canonical campaign plan Sheet has **12 tabs** in this order (9 visible + History hidden + Account Learnings + Experiments). **Reference instance: goop Sheet** (`1YaKsQnbRuKcEGdwfeFRU34HPhLNda8YyQ3HtHdI5yYU`, built by Santi + Ro — this is the spec to match for tabs 1-9).

| # | Tab | Source | Auto / Human | Refresh |
|---|---|---|---|---|
| 1 | **Dashboard** | Aggregated from Active Campaigns + Ads + Offers + Notion DB + diagnostic tiers + History | Auto | Mon |
| 2 | **Active Campaigns** | Notion Campaign Planning DB ∪ UE Ads ∪ UE Offers ∪ DD SLs ∪ DD Promos ∪ GH SLs | Auto | Mon + intraday |
| 3 | **Ads Reporting** | UE Ads Manager export + DD Sponsored Listings export + GH SLs export (per-platform funnel) | Auto | Mon |
| 4 | **Offers Reporting** | UE Offers export + DD Promotions export (per-promo + audience split) | Auto | Mon |
| 5 | **Q2 [year] Plan** | Phase S roadmap grid (events band + per-location weekly grid by tier) | **Session-authored** (Phase S writes on approval; weekly refresh never touches) | Per strategy session |
| 6 | **Q3 [year] Plan** | Same | **Session-authored** (same) | Per strategy session |
| 7 | **Q4 [year] Plan** | Same | **Session-authored** (same) | Per strategy session |
| 8 | **Archive** | Ended campaigns moved from Active + hypothesis/outcome/continue Y/N | Auto-move, human-curate | Within 5 business days of campaign end |
| 9 | **Notes / Triggers / Definitions** | Static (trigger-action automation rules + glossary + status legend + tab index) | One-time template | As needed |
| 10 | **History** (hidden) | Append-only snapshot per (week × campaign) — Spend/Sales/Orders/ROAS/Status per weekstart | **Auto, append-only** | Every refresh |
| 11 | **Account Learnings** | Per-client institutional memory — patterns, client preferences, failed tests, strategic decisions | **Human-authored, never touched by skill** | As insights emerge |
| 12 | **Experiments** | In-flight register of every live test/checkpoint — owner, control, start, **read/decide week**, decision rule, status, **weekly readings**, result | **Phase S registers rows; weekly run logs readings + stamps data freshness + flags reads-due** | Per strategy session + weekly |

### Tab 12 — Experiments (so reads never hide in a week-column, and the data behind them is accountable)

Tests are *designed* in the Q-plan tabs (the `TEST:` / `READ:` cells) but those bury the decision date inside one week's cell — and nothing guarantees the measurement data is captured each week. The **Experiments** tab fixes both: one row per test with `Owner`, `Control`, `Start`, `Read / decide` week, `Decision rule`, `Status` (⚪ Planned · 🟡 Running · 🔵 Read due · 🟢 Concluded), **`Data thru (wk)`**, **`Weekly readings`**, and `Result`. The lifecycle is **Q-plan (designed) → Experiments (in-flight + weekly readings) → Account Learnings (result)**:
- **Phase S6 write:** every `TEST:`/`READ:` (and every 60-day re-tier `CHECK`) you put in a roadmap also gets a row here — `EXP-##` for spend/offer/creative tests, `CHK-##` for re-tier checkpoints. A stepped-pullback test names its control store. **Assign an owner** — the person accountable for the read (default: analysis/reads → the GM running reporting; ops-execution tests → the ops analyst). Accountability is a name, not a process.
- **Weekly run (weekly-reporting), Tuesday:** experiment readings are stamped on the **Tuesday reporting cycle** (once DD has settled), keyed to the just-closed week — **Monday is the forward-planning pass and writes no readings.** The Tuesday run advances Planned→Running when Start passes; **for every Running/Read-due row, logs that week's test-vs-control reading into `Weekly readings` and stamps `Data thru (wk)` = the just-closed week**; flags any row whose `Read / decide` week ≤ that week as 🔵 **Read due**; and on a concluded test writes the `Result` + appends the finding to **Account Learnings**. (Cadence is per the client's `reporting_day`; goop = `tuesday_complete`.)
- **Accountability gate (CRITICAL):** a Running experiment whose `Data thru (wk)` ≠ current week after the run = the read is being built on missing data → flagged against its owner with the validation failures (see `weekly-reporting/references/attribution-and-completeness.md` §6). The read at the decision week is only as good as the interim weekly readings behind it.

### Tab 10 — History (the source of truth for trend math)

Every Monday refresh appends one row per Active Campaign × this week to a hidden `History` tab. Schema: `Weekstart, Campaign, Platform, Location, Spend, Sales, Orders, ROAS, Status`. The skill never deletes — just appends.

Computed views derive from it:
- **Lifetime cols** on Active Campaigns = sum over all History rows for that campaign.
- **L4W / L13W trend columns** = aggregate the last 4 / 13 weekstarts.
- **Decline Alerts** "ROAS <target 3+ weeks" = inspect the last 3 weekstarts.

History is **writer-owned and append-only** — the GM never edits it.

### Tab 11 — Account Learnings (per-client institutional memory)

Distinct from the cross-portfolio playbooks at `references/playbooks/`. This tab captures what we've learned about *this specific account*: client preferences, what's been tried and worked or failed, strategic decisions taken, operational quirks. The GM owns it; the skill never touches it.

Schema:

| Date | Theme | Observation | Action Taken | Result / Status | Tag | Promoted to Playbook? |
|---|---|---|---|---|---|---|

**Tags:** New Pattern · Client Preference · Failed Test · Strategic Decision · Operational Note.
**"Promoted to Playbook?"** (Y/N) = the bridge from account-specific learning → global playbook. Reviewed quarterly at the QBR; promoted learnings get added to `references/playbooks/what-works.md` or `marketplace-playbook.md`.

**Dashboard sections (canonical):** headline KPIs (Total Spend / Sales / Blended ROAS / Orders / New Cx / Active Campaigns with WoW + L4W + L13W) · Top 5 performers · Bottom 5 performers · Changes Shipped This Week · Decline Alerts · Proposed Next Week · Portfolio Trend (W-3 → W) · Location Tier table (every location: tier, # active, WTD spend/sales/ROAS, platform sales, WoW, net payout, top performer, underperformer, notes).

---

## Phase 1: Inputs Wizard — what to grab from each platform (REPORTING)

When you say *"update the campaign plan for [client]"*, the skill walks you through this. Drop everything in **`<data_dir>/inputs/`** (the skill creates the folder). Filenames follow `<platform>_<type>_<weekstart>.csv` (e.g. `ue_ads_2026-05-26.csv`). Skip any export the client doesn't run; the skill will note the skip.

**Window for every export below = the trailing 7 days (Mon → Sun) of the reporting week.** Use the same `<weekstart>` date in every filename so they group together.

### 🟢 Uber Eats

**A. UE Ads Manager — Sponsored Listings performance**
*Feeds: Ads Reporting + Active Campaigns ad rows + Dashboard Top/Bottom 5*

- **Where:** `advertiser.uber.com` → **Reports** → **Create report (v2)** → "Campaign Summary by Location"
- **Date range:** trailing 7 days
- **Required columns:** `Campaign Name`, `Location`, `Impressions`, `Clicks`, `Spend`, `Orders`, `Sales`
- **Save as:** `inputs/ue_ads_<weekstart>.csv`
- **Skip if:** client has `UE Ads Manager Access = No` (note skip; Active Campaigns will mark the row "Tier 1 attribution only").

**B. UE Marketing → Offers performance**
*Feeds: Offers Reporting + Active Campaigns offer rows*

- **Where:** `merchants.ubereats.com` → **Marketing** → **Offers** → All Offers → **Export**
- **Date range:** trailing 7 days
- **Required columns:** `Offer Name`, `Location(s)`, `Threshold`, `Discount`, `Redemptions`, `Discount Spend`, `Attributed Sales`, `New Customers` (if exposed)
- **Save as:** `inputs/ue_offers_<weekstart>.csv`
- **Watch for:** the $0.99 marketing fee on offer redemptions (some clients) — that's offer cost, not ad spend.

**C. UE Sales by Location** *(optional if weekly-reporting already ran this week)*
*Feeds: Location Tier table's "Platform Sales WTD" column*

- **Where:** UE Manager → **Reports** → **Performance** → **Sales** → 7d → Download CSV
- **Required columns:** `Location`, `Net Sales`, `Orders`, `AOV`, `Net Payout`
- **Save as:** `inputs/ue_sales_<weekstart>.csv`
- **Or:** point the skill at `<weekly-reporting>/OUTPUT/by_location.csv` instead.

### 🔴 DoorDash

**A. DD Sponsored Listings performance**
*Feeds: Ads Reporting + Active Campaigns ad rows*

- **Where:** `mxportal.doordash.com` → **Marketing** → **Sponsored Listings** → **Export**
- **Date range:** trailing 7 days
- **Required columns:** `Campaign Name`, `Location`, `Spend`, `Orders`, `Attributed Sales`
- **DD does NOT expose Impressions/Clicks/CTR for SLs** — Ads Reporting marks those `n/a` for DD rows. That's correct, not missing data.
- **Save as:** `inputs/dd_ads_<weekstart>.csv`

**B. DD Promotions performance**
*Feeds: Offers Reporting + Active Campaigns offer rows*

- **Where:** DD Portal → **Marketing** → **Promotions** → **All Promotions** → **Export**
- **Date range:** trailing 7 days
- **Required columns:** `Promotion Name`, `Location(s)`, `Promo Type`, `Threshold`, `Discount`, `Redemptions`, `Promo Spend`, `Attributed Sales`, `New Customers`, `% New`
- **Save as:** `inputs/dd_offers_<weekstart>.csv`
- **Watch for:** `$0.99` flat fee = offer redemption fee, NOT ad spend.

**C. DD Financial Transactions** *(optional if weekly-reporting already ran)*
*Feeds: Location Tier "Platform Sales WTD" column for DD*

- **Where:** DD Portal → **Financials** → **Statements** → 7d → Simplified CSV
- **Or:** weekly-reporting `OUTPUT/by_location.csv`.

### 🟦 Grubhub *(skip if client doesn't run GH paid placement)*

**A. GH Sponsored Listings**
*Feeds: Ads Reporting + Active Campaigns ad rows*

- **Where:** `restaurant.grubhub.com` → **Marketing** → **Sponsored Listings** → **Export**
- **Date range:** trailing 7 days
- **Required columns:** `Campaign Name`, `Location`, `Spend`, `Orders`, `Sales`
- **Save as:** `inputs/gh_ads_<weekstart>.csv`

**B. GH Settlement** *(optional if weekly-reporting ran)*
- **Where:** GH Portal → **Financials** → **Settlement** → 7d → CSV. Or weekly-reporting `OUTPUT/by_location.csv`.

### 📋 Notion Campaign Planning DB *(auto — the skill pulls this for you)*

- The skill queries the Campaign Planning DB filtered to this client + `Entry Type = Campaign` and writes the result to `<data_dir>/<slug>_campaigns.json`. No action from you — but **make sure the DB is current** before triggering the refresh. If a campaign isn't in the DB with the right Status, it won't show.

### 📊 Weekly-reporting outputs *(optional — short-circuit some pulls)*

If `weekly-reporting` already ran for the same week, point the skill at its outputs instead of pulling individual platform sales:
- `OUTPUT/campaign_performance.csv` — fallback for per-campaign spend/sales/ROAS/orders.
- `OUTPUT/by_location.csv` — platform sales by location → drives Location Tier table.
- `OUTPUT/platform_overview.csv` — portfolio-level trend → drives Dashboard Portfolio Trend (W-3 → W).

---

### Per-tab input map (what feeds what)

| Tab | Inputs needed |
|---|---|
| **Dashboard** — KPIs, Top/Bottom 5 | All ads + offers exports aggregated |
| **Dashboard** — Decline Alerts | This week's exports + L4W history *(needs prior weeks pasted; first run lacks the context)* |
| **Dashboard** — Portfolio Trend | `platform_overview.csv` (weekly-reporting) last 4 weeks |
| **Dashboard** — Location Tier table | Notion DB (campaigns) + ue_sales/dd_financials/gh_settlement (platform sales) + latest diagnostic (tier color) |
| **Active Campaigns** | Notion DB ∪ all ads exports ∪ all offers exports, joined by campaign name |
| **Ads Reporting** | `ue_ads_*.csv` + `dd_ads_*.csv` + `gh_ads_*.csv` |
| **Offers Reporting** | `ue_offers_*.csv` + `dd_offers_*.csv` |
| **Q2/Q3/Q4 Plan** | Human-authored. Skill leaves these alone. |
| **Archive** | Ended campaigns from Notion DB + human-typed hypothesis/outcome/continue |
| **Notes** | Static template; one-time setup |

---

## Phase 1 (legacy fallback — kept for reference)

If only platform exports without the wizard's structure are available, the skill still produces the v0.1 4-tab Sheet (Dashboard / Campaign Tracker / Ad Performance / Legend). The v2 9-tab generator is in build (see Build Status).

---

## Phase 2: Run the update

First-time setup (once per machine): `python3 -m pip install --user openpyxl google-auth google-api-python-client` (see `RUN-LOCALLY.md`; run commands with plain `python3`). (The two google packages are only needed for the live-Sheet publish step; openpyxl alone suffices for file-only output.)

The render takes the Phase 0 tracker CSV and (optionally) the performance CSV:

```bash
cd /Users/maxx/Desktop/Cowork/Skills/campaign-plan
python3 references/build_campaign_plan_xlsx.py \
  --client "<display name>" \
  --tracker-csv /tmp/campaign-data-<client>/<client>_tracker.csv \
  --campaign-perf-csv <weekly-reporting OUTPUT/campaign_performance.csv> \
  --ads-detail-csv <ads funnel CSV; see Ads detail below> \
  --output /tmp/<client>_Campaign_Plan.xlsx
```

`--tracker-csv` comes from Phase 0's bridge. Omit it to use the embedded goop sample. Omit `--campaign-perf-csv` for a planning-only render (new client, no performance yet). Omit `--ads-detail-csv` if the client runs no paid placements. Add `--overwrite-perf` to replace existing performance cells (default fills only empty ones, so manual entries survive).

### Ads detail (impressions / clicks / CTR / CPC)

Offers and Ads have different metrics, so paid placements get their own treatment. `--ads-detail-csv` takes the ads funnel export with header `Campaign, Platform, Locations, Status, Impressions, Clicks, Spend, Orders, Attributed Sales` (from the platform Ads Managers — UE Ads Manager, DD Sponsored Listings, GH Sponsored). The generator builds:

- An **Ad Performance** tab — one row per ad campaign with Impressions, Clicks, **CTR**, Spend, **CPC**, Orders, Attributed Sales, ROAS, **CPO** (CTR/CPC/ROAS/CPO computed live in-sheet so they recompute if the client edits).
- A dashboard **Ads — Funnel Detail** block (impression/click/CTR/CPC/spend/sales/ROAS totals), and the Ads-vs-Offers Ad row pulls from the Ad Performance tab so the two never disagree.

Status colours are painted directly onto the cells (not via conditional-formatting rules) so they survive the .xlsx → Google Sheets / Numbers conversion. This was a real bug: CF rules drop on import, leaving white-on-white invisible status text.

The generator:
1. Reads the tracker rows from `--tracker-csv` (the Phase 0 projection of the Campaign Planning DB).
2. If `--campaign-perf-csv` is given, folds weekly-reporting's per-campaign performance into the matching Live/Ended rows' Spend / Attributed Sales / Actual ROAS / Incremental Orders (see matching below).
3. Recomputes the Dashboard rollups (overall via COUNTIF/SUM, by platform + ads-vs-offers via SUMIF) and the spend chart.
4. Writes the formatted 3-tab .xlsx with the 5-status conditional formatting (Live green / Approved teal / Proposed blue / Blocked-on-client amber / Ended gray).

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

- **Dashboard** — Highlights callout (qualitative wins), Overall KPIs (live/proposed/blocked counts, total spend, blended ROAS), By Platform table (UE/DD/GH — marketplace only, no Meta — with spend/sales/ROAS/orders via SUMIF), **By Segment table (New / Existing / Lapsed / All via SUMIF on the Segment column)**, Ads vs Offers table, Ads Funnel Detail, spend-by-platform bar chart. Performance cells auto-compute from the tracker.
- **Campaign Tracker** — one row per (campaign × marketplace platform). Columns: Campaign, Platform, Type (Ad/Offer), Offer/Ad Detail, Locations, **Segment (New/Existing/Lapsed/All)**, Status, Days in Queue, Flight Start/End, Target ROAS, Actual ROAS, Spend, Attributed Sales, Incremental Orders, In-Platform Campaign Name, Notes. Status cells painted directly (5 colors: Live green / Approved teal / Proposed blue / Blocked-on-client amber / Ended gray) so they survive the Sheets conversion.
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

- ✅ **Polish pass (2026-06-05):** alignment convention (labels LEFT, metric columns RIGHT, auto-detected per column); campaign-focus refocus (Dashboard subtitle + Location Tier drops payout/profitability — those live in the weekly report); `validate` command + auto-QA gate at end of v2 refresh (catches off-by-one + header drift); `reporting_day` config (monday_flash vs tuesday_complete) for the DD-settlement timing choice. goop re-rendered + validated ✓.

- ✅ Workbook generator (`references/build_campaign_plan_xlsx.py`) produces the formatted .xlsx (Dashboard + Campaign Tracker + Ad Performance + Legend) with dashboard rollups + chart. Opens cleanly in Google Sheets / Numbers — status colours painted directly on cells (not CF rules, which drop on import). goop's instance built 2026-05-21.
- ✅ **Ads funnel detail (built 2026-05-21).** `--ads-detail-csv` adds the Ad Performance tab (impressions/clicks/CTR/CPC/ROAS/CPO per ad campaign) + a dashboard funnel block. Ads-vs-Offers Ad row reconciles to the funnel. Validated on goop's ad campaigns.
- ✅ **Meta removed + segment reporting added (2026-05-22).** Campaign plan tracks marketplace only (UE/DD/GH); Meta dropped from the bridge, By Platform, and ads funnel. Added a Segment column (New/Existing/Lapsed/All, mapped from the DB Customer Segment) and a By Segment dashboard table. Most platform exports / campaign setup carry the segment.
- ✅ **Live Google Sheet publish (built 2026-05-22).** `references/push_to_sheet.py` pushes the workbook into the client's Drive folder as a native Google Sheet, in place (stable link, recorded as `sheet_id`). Wired into `refresh.py` so the one command now plans → renders → publishes. Service account `spice-sheets-writer@…` set up in the `spice-sheets-writer` Cloud project; key at `~/.config/spice/google-sheets-writer.json`; "1. Active" folder shared. goop's live Sheet: created + update-in-place validated.
- ✅ **Inputs Wizard documented (built 2026-06-03).** Phase 1 in SKILL.md now walks the user through every required export per platform (UE Ads, UE Offers, UE Sales · DD SLs, DD Promos, DD Financials · GH SLs · GH Settlement) with exact paths, filenames, column requirements, and per-tab input map. Skill prompts the user for each at refresh time.
- 🚧 **v2 Generator rewrite (Phase 2).** Current generator produces the v0.1 4-tab Sheet (Dashboard / Campaign Tracker / Ad Performance / Legend). v2 target is the **9-tab canonical structure** matching Santi + Ro's goop Sheet (`1YaKsQnbRuKcEGdwfeFRU34HPhLNda8YyQ3HtHdI5yYU`): Dashboard with KPIs + Top/Bottom 5 + Decline Alerts + Portfolio Trend + Location Tier table · Active Campaigns (21-col tracker, Test? flag, Lifetime cols) · Ads Reporting (per-platform funnel + audience segmentation) · Offers Reporting (per-promo + new/existing split + depth analysis) · Q2/Q3/Q4 Plan (forward calendar + per-location grid, human-authored scaffold) · Archive (hypothesis/outcome/continue) · Notes (trigger-action rules + definitions + status legend + tab index). Auto-generated portions: tabs 1-4 and Archive moves; human-authored portions: tabs 5-7 (forward planning) and Archive hypothesis/outcome curation.
- 🚧 **Phase 2.2 — Notion Campaign Performance section.** **Scope locked (2026-06-04):** the campaign-plan skill produces *only* the Campaign Performance section (Ads summary table, What's Working, What's Not, Reallocation Recommendations) — not the full weekly report. Keeps the client read tight + non-overwhelming. weekly-reporting still owns the financial waterfall + ops quality tables. Reference: the Campaign Performance block in `374d3ff018e781419e6ceb98406e028f` (goop W22). Output: a Notion page or subsection appended to the client's weekly report.
- 🚧 **Phase 2.2 — Notion DB change tracking.** At each refresh, snapshot the current Notion DB state, diff against the previous snapshot, surface "what changed since last refresh" in the Slack draft + Notion report. Likely store snapshots in Drive (`Campaign Plan Inputs / _state/`).
- 🚧 **Phase 2.1 — GM-via-skill campaign input (write to Notion DB through Cowork).** Currently the skill READS the Notion Campaign Planning DB. New capability: the GM can ADD or UPDATE campaigns through Cowork prompts instead of opening Notion. Trigger phrases: *"add a [type] campaign for [client] at [locations]"*, *"log [campaign] for [client]"*, *"move [campaign] to [status]"*, *"set [campaign] segment to [Lapsed]"*. The skill collects missing fields (Customer Segment, ROAS Target, Start/End, Offer Details), validates against the playbook (foundations gate, segment rule, marketplace-only), writes to Notion via `notion-create-pages` or `notion-update-page`, and returns the new/updated page link. Notion DB stays source of truth; the skill becomes the faster input method.
- 🚧 **Slack draft generator (Phase 2.1).** After each refresh, skill produces a 4-bullet Slack draft in Ro's format (bold lead-in + numbers + active-voice verb). GM edits + sends manually — no auto-send.
- ✅ **Phase 2.1 COMPLETE (built 2026-06-05) — full v2 9-tab pipeline, one command.** Set `"v2": true` + a `sheet_id` in a client config and `refresh.py` routes to the Sheets-API path: ensure all 11 tabs → write Dashboard / Active Campaigns / Ads Reporting / Offers Reporting (full-tab rewrite via `sheets_writer.py`) → append History → emit a Slack draft. Validated end-to-end on a test Sheet: KPIs, by-platform/by-segment, Top/Bottom 5 ranking, ads funnel (UE impressions/clicks/CTR; DD `n/a`), offers per-promo all compute from real CSV inputs. Modules: `v2_aggregate.py` (CSV → writer dicts), `slack_draft.py` (Ro's 4-bullet format), `add_campaign.py` (GM-via-skill Notion write), `notion_campaign_perf.py` (Campaign Performance Notion section), `db_to_tracker.py` snapshot/diff (change tracking). **Known refinements:** (1) By-Segment dollar attribution shows $0 until ads/offers→segment join is added (counts are correct); (2) WoW columns need ≥2 weeks of History to populate; (3) decline-alerts + location-tier auto-detection are stubs awaiting History accumulation; (4) `notion_campaign_perf.py` emits markdown, doesn't yet publish to Notion. None block the v2 refresh.
- ✅ **Sheets API writer infrastructure (built 2026-06-03 — Phase 2.0).** `references/sheets_writer.py` replaces the xlsx-import-and-replace flow for v2 clients. Range-based + range-owned: skill writes ONLY canonical named ranges (defined in `NAMED_RANGES`); refuses to touch protected tabs (Q2/Q3/Q4 Plan, Notes, Archive — that's `assert_safe_to_write` guarding every write). Includes auth (service account), low-level helpers (clear/write/append/format), named-range setup (`setup-ranges` CLI command, idempotent), status-pill painter (matches v0.1 palette, supports both text + emoji status), and **Active Campaigns writer fully implemented as the proof-of-concept** (others stubbed for Phase 2.1: Dashboard, Ads Reporting, Offers Reporting). Smoke-tested against goop v0.1 Sheet — auth + meta validation working. **Why this matters:** xlsx-replace would clobber Ro's forward calendars + Santi's archive curation every Friday. Sheets API surgically writes auto ranges only, preserves everything else, preserves client comments. This is the correct architecture for the mixed-auto/human 9-tab structure.
- 🔭 **Comment-persistence caveat.** The publish replaces the Sheet's content each run via Drive import. The link/sharing stay stable; cell-anchored client comments may not survive a full-content replace. If in-sheet commenting becomes load-bearing, upgrade `push_to_sheet.py` to true Sheets-API cell writes (data ranges only) so comments persist. Acceptable for now (approvals captured in Slack/Notion).
- ✅ **Separate-workbook decision locked (2026-05-21).** Campaign plan is its own .xlsx, not tabs in the weekly tracker. Rationale in "Why a separate workbook" above.
- ✅ **Planning bridge built (2026-05-21).** `references/db_to_tracker.py` projects Campaign Planning DB rows into the tracker CSV: per-channel expansion, 14→5 status projection, Live derived from flight window, days-in-queue from `Client Review Since`. Added the `Client Review Since` date property to the DB. Validated on goop's audit set: 7 campaigns → 11 rows, BOGA correctly shows 11 days in queue, Canceled dropped.
- ✅ **Performance auto-feed from `weekly-reporting` (built 2026-05-21).** `--campaign-perf-csv` folds `campaign_performance.csv` into the Live/Ended rows — no double-pull. Match key + safeguards under "Matching" in Phase 2. Validated on goop: 4 live rows filled with correct per-location sums, Blocked/Proposed left empty, concurrent same-platform offers kept separate, unmatched rows surfaced.
- 🚧 **DB population is the real adoption gap.** As of 2026-05-21 goop's live promos aren't in the Campaign Planning DB (the work lives in the GM's head). The bridge can't render what isn't logged. GM Friday discipline: every campaign in the DB with current Status. This is process, not code.
- 🚧 Direct platform-export parsing (raw UE/DD/GH, for weeks `weekly-reporting` hasn't run): still needs real export samples. Largely subsumed by the auto-feed once `campaign_performance.csv` is the source.
- 🚧 `campaign-ops` to set `Client Review Since` when a campaign enters Client Review (so days-in-queue is automatic, not hand-set).
- 🚧 Scripted Drive upload: blocked on MCP binary limit; needs a local Drive-API script.

---

## Anti-patterns

- Don't hand-format the workbook. Run the generator; it formats.
- Don't maintain the plan in two places. Notion DB is internal source; the workbook is the client render. The skill bridges them.
- Don't duplicate execution. Setup stays with `campaign-ops`.
- Don't silently drop unmatched platform campaigns. Surface them for mapping.
- Don't share a stale workbook. Refresh from the latest exports before sending.
