---
name: weekly-reporting
description: >
  Process weekly delivery marketplace reports from Uber Eats, DoorDash, and Grubhub.
  Dispatches platform-specific extraction agents, aggregates results, produces paste-ready
  tracker updates and Notion weekly reports. Triggers on: "weekly report", "weekly reporting",
  "process weekly data", "run reporting", or when multiple platform CSV exports are provided
  with context about weekly performance or client metrics.
---

# Weekly Reporting

Orchestrate weekly delivery marketplace reporting for Spice clients. Dispatches platform-specific extraction agents, aggregates results, updates tracker, and produces Notion report.

**Run pre-built scripts for aggregation and Notion generation. Do NOT write extraction code inline — the agents handle that.**

---

## Phase 1: Input Collection & Validation

### 1a: Identify Client & Week
1. Ask for client name
2. **Fetch the client's Weekly Reporting Profile from Notion:**
   - Search Notion for the client's project page using `notion-search` with the client name
   - Navigate to the client's Wiki database and find the "Weekly Reporting Profile" page
   - Fetch the profile page content using `notion-fetch`
   - Extract: active platforms, DD invoicing tier, UE ads access, data quirks, location map, KPI targets, last week baseline, **tracker URL from `Report Writer Notes`**
   - If no profile page exists, fall back to `references/client-registry.md` (legacy path)
3. Look up client in `references/client-registry.md` for any data NOT in the Notion profile (store maps, tracker URL). The Notion profile is authoritative for platform config and quirks; the registry is a backup and holds static reference data.
4. Ask for week date range (Monday-Sunday) if not provided
5. Create a temp output directory: `OUTPUT/` in the working directory
6. Write the fetched profile data to `OUTPUT/client_profile.json` for downstream scripts (validate_report.py uses this for KPI target soft-checks). Include the resolved `tracker_url` field so downstream phases can reference it.

### 1b: Collect Required Files

**Try Google Drive MCP first (auto-fetch). Fall back to manual upload only if Drive returns nothing.** See "Google Drive Integration" section below for the full flow and tool usage.

For each platform the client is on, require these specific files:

**Uber Eats (1-3 files):**
- [ ] Transaction CSV (payment/settlement export) — REQUIRED. Source for all metrics. Offer attribution is per-order (offers columns). Ad spend appears as standalone rows (blank Order Status, $0 sales) — gives per-store spend totals.
- [ ] Ads Manager performance export — OPTIONAL. Only collect if `UE Ads Manager Access = Yes` in client registry. Date-filtered Campaign Summary by Location from `advertiser.uber.com/reports/create-v2`. Enhances ad attribution with order/sales cross-reference.
- [ ] Offers export (campaign-level offer redemptions — supplementary detail). Optional.
- **If client has `UE Ads Manager Access = No` or `TBD`:** Do NOT ask for or warn about Ads Manager. Run Tier 1 (offer-only attribution). This is the default path.
- **If client has `UE Ads Manager Access = Yes` but export not provided:** Note it as available but missing. Offer to proceed with Tier 1 or wait for the export.
- Watch for **$0.99 marketing fee** on offer redemptions (active for most clients, not all). This is an offer cost, NOT ad spend.

**DoorDash (1-3 files):**
- [ ] Transaction CSV (payment/settlement export)
- [ ] Sponsored Listing CSV (optional — `MARKETING_SPONSORED_LISTING`)
- [ ] Promotion CSV (optional — `MARKETING_PROMOTION`)

**Grubhub (1 file):**
- [ ] Settlement CSV

**Tracker Exports (for WoW + 4-week rolling average):**
- [ ] Weekly Platform Overview tab — pulled directly from the client's Google Sheet tracker via Drive MCP (or manual CSV export as fallback)
- [ ] By Location tab — pulled directly from the client's Google Sheet tracker via Drive MCP (or manual CSV export as fallback)
- [ ] Current week number (e.g., 14 for Week 14)
- These enable WoW change and vs-4-week-avg columns in every platform and location table. **Always collect these** — the report is significantly more useful with trend context. With the Drive integration this is automatic when the tracker URL is known. If the tracker is unreachable, proceed without them but flag it.

**Operations Files (optional):**
- [ ] DD Operations Quality CSVs
- [ ] UE Order Accuracy files
- [ ] UE Menu Downtime files

### 1c: Validate
- Confirm all required files are present for each active platform (whether sourced from Drive or manual upload)
- Surface what's missing with specific file names AND say where the skill looked (Drive folder vs. waiting on manual upload)
- Do NOT proceed to extraction until core transaction files are confirmed

---

## Google Drive Integration

The skill auto-fetches inputs from Google Drive when the Drive MCP is available. Manual upload is the fallback, not the default.

**Tools used (all `mcp__3cfdef12-aed5-469f-904c-ae7eaeff04dd__*`):**
- `search_files` — find platform CSV exports by client/platform/date pattern
- `read_file_content` — read Sheet tabs directly (used for trackers); also reads CSV/Doc content
- `download_file_content` — pull binary file content if `read_file_content` doesn't return parseable text
- `get_file_metadata` — confirm file modification time matches the reporting week
- `list_recent_files` — used as a sanity check when `search_files` returns ambiguous matches
- `create_file` — used in Phase 5 to optionally drop the generated `tracker_update.csv` into the client's Drive folder

**Availability check:** at the start of Phase 1b, confirm Drive tools are exposed in the current session. If they're not, skip the auto-fetch path and ask for manual uploads. Do NOT block — the manual path still works.

### Auto-fetch flow (per client, per week)

**Step 1 — Locate the client's tracker folder:**
1. The tracker URL is already resolved in 1a (Notion `Report Writer Notes` → `client-registry.md` fallback). Extract the file ID from the URL pattern `https://docs.google.com/spreadsheets/d/<ID>/edit`.
2. Call `get_file_metadata` on the tracker file ID to confirm it exists and grab its parent folder ID. The platform CSVs for the same client typically live in or near that folder.

**Step 2 — Fetch tracker tabs (replaces manual CSV export):**
1. Use `read_file_content` against the tracker file ID and request the `Weekly Platform Overview` tab. Save the returned content to `OUTPUT/tracker_platform_overview.csv` in the same shape the aggregator expects (`Section, Metric, Value` columns).
2. Repeat for the `By Location` tab → `OUTPUT/tracker_by_location.csv` (`Location, Metric, Value`).
3. If `read_file_content` returns the entire Sheet without per-tab filtering, parse the response, isolate the two tabs by name, and write the CSVs locally.
4. If the read fails (permissions, tab renamed, sheet structure changed), fall back to manual: ask the user to export the two tabs as CSV and upload them. Note the failure reason in `OUTPUT/drive_fetch.log` so the team can fix the underlying issue.

**Step 3 — Search for the week's platform exports:**
For each active platform, run `search_files` with the patterns below. Use the client name canonical form (the one in `client-registry.md`).

| Platform | Search query examples | What we want |
|----------|----------------------|--------------|
| Uber Eats — Transactions | `"<Client> UE transactions"`, `"<Client> uber payments"`, `"payments_<YYYY-MM-DD>"` | The transaction/payments CSV for the reporting week |
| Uber Eats — Ads Manager | `"<Client> UE ads"`, `"campaigns_summary_metrics_<YYYY-MM-DD>_<YYYY-MM-DD>"` | Campaign Summary by Location export |
| Uber Eats — Offers | `"<Client> UE offers"` | Offers export (optional) |
| DoorDash — Transactions | `"<Client> DD transactions"`, `"<Client> doordash payments"` | Transaction CSV |
| DoorDash — Sponsored Listing | `"<Client> DD sponsored"`, `"MARKETING_SPONSORED_LISTING"` | SL CSV (optional) |
| DoorDash — Promotions | `"<Client> DD promotion"`, `"MARKETING_PROMOTION"` | Promotion CSV (optional) |
| Grubhub — Settlement | `"<Client> GH settlement"`, `"<Client> grubhub"` | Settlement CSV |

For each match:
1. Call `get_file_metadata` and verify the modified time falls inside or just after the reporting week (Mon-Sun + 3-day grace). Skip stale files.
2. Verify the file extension is `.csv`.
3. Use `read_file_content` to load the file. If the response is too large for a single read or comes back as a binary blob, use `download_file_content` and write to a local path under `OUTPUT/inputs/<platform>/<filename>`.
4. Track the resolved local path — extraction agents in Phase 3 read from these paths.

**Step 4 — Disambiguate / fall back:**
- **Multiple matches:** If `search_files` returns more than one candidate per slot, surface the candidates with their filenames + modified times and ask the user which to use. Do not auto-pick the most recent without confirmation.
- **No matches:** Ask the user to upload manually for that platform. Do NOT halt the run if other platforms loaded cleanly — partial fetch is fine, missing files just go through the existing manual path.
- **Drive MCP unavailable:** Skip the entire auto-fetch flow and run the original manual collection prompt (the `1b` checklist).

**Step 5 — Log what was fetched:**
Write `OUTPUT/drive_fetch.log` listing each file resolved, its source (Drive file ID or "manual upload"), and the modified time. This makes Phase 4.5 validation failures easier to triage.

### What still requires manual action
- First-time client trackers that aren't yet in Drive (e.g., Westville)
- Platforms where the export naming doesn't match the search patterns above (add new patterns when you encounter them and update this section)
- Operations files (DD Quality, UE Accuracy, UE Menu Downtime) — usually ad-hoc; ask the user
- Any platform export the team hasn't dropped into Drive yet for the week — Drive is only authoritative if the team uploads consistently

---

## Phase 2: Context Gathering

Run in parallel with extraction (Phase 3). Write each output to `OUTPUT/`.

### 2a: Agenda Context → `OUTPUT/agenda_context.md`
Search Circleback for the most recent meeting with the client (use `SearchMeetings` with client name).
Read the meeting notes (`ReadMeetings`). Extract:
- Open discussion topics or follow-ups mentioned
- Any strategic decisions pending
- Questions the client raised that need answers this week
- Key themes from the last conversation

Format as 3-5 bullet points that continue the conversation from last meeting. Do NOT list report sections. Write things like:
- "Follow up on Venice ROAS discussion from last week"
- "Review DoorDash expansion test results (client asked about this 2/28)"

If no recent meeting found: `*First meeting or no previous notes available. General performance review.*`

### 2b: Action Items → `OUTPUT/action_items.md`
Pull from three sources:

1. **Circleback**: Search last 2 meetings with client. Extract action items, to-dos, commitments. Use `ReadMeetings` for `action_items` field.
2. **Slack**: Search client name in relevant channels (`slack_search_public` with `"[client name]"` + `"action item" OR "to do" OR "follow up"`). Last 7 days.
3. **Email**: Search Gmail (`gmail_search_messages` with `q="[client name]"`, last 14 days). Look for action items, asks, pending deliverables.

Format:
```
### Carried Over
- [ ] [action item from previous meeting] *(source: meeting 2/28)*
- [ ] [item from Slack] *(source: #channel, 3/5)*

### New This Week
- [ ] [items identified from this week's data or comms]
```

### 2c: Ops Quality Context → `OUTPUT/ops_quality.md`
Process ALL supplementary ops files (if provided). Write a unified section with store operations tables, order accuracy details, and menu downtime events.

If no ops files provided, omit this file entirely.

---

## Phase 3: Platform Extraction (Parallel Agents)

Dispatch one agent per active platform. Each agent:
1. Reads its methodology from `agents/[platform]-extraction.md`
2. Reads the client's data files
3. Outputs standardized JSON to `OUTPUT/[platform]_results.json`

**Launch agents in parallel using the Agent tool:**

For each platform, create an agent with this prompt pattern:
```
Read the extraction methodology at [skill_base]/agents/[ue|dd|gh]-extraction.md.
Then read the client's [platform] data files: [list file paths].
Follow the methodology exactly. Week: [start] to [end].
Client: [name]. Check references/client-registry.md for any client-specific rules.
Write the standardized JSON output to OUTPUT/[platform]_results.json.
```

**Important:**
- UE agent gets: transaction CSV (always) + Offers export (if available) + Ads Manager performance export (only if `UE Ads Manager Access = Yes` AND export provided)
  - Transaction CSV = sales, orders, payout, offer attribution (per-order), ad spend totals (standalone rows)
  - Without Ads Manager: Tier 1 offer-only attribution. Ad spend counted in investment, orders not attributed to ads. Conservative, production-ready.
  - With Ads Manager: Tier 2 enhanced attribution. Ad orders cross-referenced with full-overlap dedup. Multi-store campaigns distributed proportionally by store offer volume.
- DD agent gets: transaction CSV + optional Sponsored Listing + Promotion CSVs
  - Enterprise clients: portal exports are source of truth for marketing attribution + ad spend (invoiced separately)
  - $0.99 flat fee rule: marketing fee of -$0.99 is always an offer redemption fee, not ad spend
- GH agent gets: settlement CSV + client-specific exclusions from registry
  - Ad spend NOT in settlement — leave as $0
  - If merchant_funded_promotion and merchant_funded_loyalty both $0, marketing is inactive (correct, not a gap)
- Each agent outputs JSON following `references/output-schema.json`

Wait for all agents to complete before proceeding.

---

## Phase 3.5: Location Validation

After extraction, before aggregation, validate that all location names map correctly:

```bash
python scripts/validate_locations.py \
    --store-map references/store-maps/[client-slug].json \
    --output-dir OUTPUT
```

This:
1. Reads the client's structured store map JSON (`references/store-maps/`)
2. Checks every location in each platform's JSON output against the map
3. Flags **unmapped locations** with their revenue so you can see what's missing
4. Flags **expected locations** not found in the data (closed/inactive)
5. Applies **merge rules** (e.g., North Hollywood → Studio City in the tracker)
6. Outputs `OUTPUT/location_map.json` — flat lookup consumed by the aggregation script

**If unmapped locations are detected:** Add the missing name to the store map JSON, then re-run validation. Do NOT proceed to aggregation with unmapped locations that have significant revenue.

**Store map JSON format** (`references/store-maps/[client-slug].json`):
```json
{
  "client": "Client Name",
  "locations": {
    "Canonical Name": {
      "uber_eats": ["platform name 1"],
      "doordash": ["platform name"],
      "grubhub": ["Name|City|Address"]
    }
  },
  "merge_rules": {
    "Source Canonical": "Target Canonical"
  }
}
```

Each client needs one store map JSON. Create it from the client registry table when onboarding. The validator auto-extracts short names from "brand (Location)" patterns, so you don't need to list every variant.

---

## Phase 4: Aggregation

Run the aggregation script:

```bash
python scripts/aggregate_platforms.py --output-dir OUTPUT \
    [--tracker-platform-csv PLATFORM_OVERVIEW.csv] \
    [--tracker-location-csv BY_LOCATION.csv] \
    [--current-week 14]
```

**Always pass `--tracker-platform-csv`, `--tracker-location-csv`, and `--current-week` when tracker exports were collected in Phase 1.** These enable WoW and vs-4-week-avg comparisons in the output. Omit only if tracker exports are unavailable.

The aggregation script auto-detects `OUTPUT/location_map.json` (from Phase 3.5) for location name mapping. If no validated map exists, pass `--store-map MAP.json` manually.

This produces:
- `platform_overview.csv` — OVERVIEW + per-platform sections, formatted values
- `by_location.csv` — per-location metrics, sorted by Total Net Sales desc
- `campaign_performance.csv` — all campaign rows from all platforms
- `tracker_update.csv` — paste-ready formatted column for the Weekly Tracker
- `platform_comparisons.csv` — WoW + vs-4wk-avg per metric per platform (if tracker exports provided)
- `location_comparisons.csv` — WoW + vs-4wk-avg per metric per location (if tracker exports provided)

Check stdout for any warnings. Surface to user.

---

## Phase 4.5: Validation Gate (REQUIRED — BLOCKS on failure)

Run the validation script BEFORE generating the Notion update. This catches formula errors in extraction (e.g., net_sales ≠ total_sales - discounts, payout % using wrong denominator) and prevents bad data from reaching clients.

```bash
python scripts/validate_report.py \
    --output-dir OUTPUT \
    --profile-json OUTPUT/client_profile.json
```

Omit `--profile-json` if no Notion profile was fetched in Phase 1.

**Critical checks (script exits 1 if any fail):**
- Net Sales = Total Sales - Discounts (per platform, per location)
- Marketing Driven Sales + Organic Sales = Total Sales
- Orders from Marketing + Organic Orders = Total Orders
- Net Payout = Net Sales - Commissions - Ad Spend - Other Adjustments
- Net Payout % = Net Payout / Total Sales × 100
- Commissions % = Commissions / Total Sales × 100
- Total Marketing Investment = Ad Spend + Discounts
- Location totals sum to platform overview totals
- No negative commissions, ad spend, or discounts (sign errors)

**Soft checks (flagged but don't block):**
- Net Payout % outside 50-85% range
- Payout reconciliation: calculated vs platform payout column > 2% difference
- KPI targets from client profile (if available)
- Extraction agent's own validation flags

**If validation FAILS (exit code 1):**
1. **HALT** — do NOT proceed to Notion generation
2. Show the user the specific failures from `OUTPUT/validation_report.md`
3. Identify which extraction agent produced the bad data
4. Re-run the offending extraction agent with corrected approach
5. Re-run aggregation + validation until exit code = 0

**If validation PASSES (exit code 0):**
- Proceed to Phase 5
- The `OUTPUT/validation_report.md` content will be pasted into the Notion page's QA section

---

## Phase 5: Generate Notion Update

```bash
python scripts/generate_notion_update.py \
    --overview OUTPUT/platform_overview.csv \
    --by-location OUTPUT/by_location.csv \
    --campaign-perf OUTPUT/campaign_performance.csv \
    --prev-overview OUTPUT/prev_platform_overview.csv \
    --prev-by-location OUTPUT/prev_by_location.csv \
    --agenda-context OUTPUT/agenda_context.md \
    --action-items OUTPUT/action_items.md \
    --ops-quality OUTPUT/ops_quality.md \
    --validation-report OUTPUT/validation_report.md \
    --client "CLIENT NAME" --week "Mon DD-DD" \
    --output OUTPUT/notion_weekly_update.md
```

Omit `--prev-overview` and `--prev-by-location` if no prior week data available.
Omit `--ops-quality` if no ops files were provided.
`--validation-report` should always be present (written by Phase 4.5).

### 5b: Optional — Push tracker_update.csv to Drive

After the Notion update is generated and validation has passed, **optionally** push `OUTPUT/tracker_update.csv` to the client's tracker folder in Drive. This is OPTIONAL and additive — the paste-ready columns in Phase 7 remain the primary delivery mechanism so the team can keep eyeballing values before they land in the canonical sheet.

**When to use:**
- Tracker URL was successfully resolved in Phase 1a
- Drive MCP is available and `get_file_metadata` succeeded on the tracker
- The user has confirmed they want auto-write enabled (ask once per session, default to no)

**How to write it:**
1. Use `get_file_metadata` on the tracker file ID to grab its parent folder ID.
2. Use `create_file` to upload `OUTPUT/tracker_update.csv` into that folder, named `<Client> Week <NN> tracker update.csv`. This drops the file next to the tracker so the team can open it side-by-side and paste, or import it as a tab.
3. Print the Drive URL of the uploaded file in chat as confirmation.

**Do NOT:**
- Overwrite the canonical tracker tabs directly. We don't have a "write cells to tab" tool exposed and silently overwriting client trackers is a hard no — paste-ready columns + a sibling CSV is the safe path.
- Skip the Phase 7 paste-ready output. The auto-write is supplementary, not a replacement.

**On failure:** log the error to `OUTPUT/drive_fetch.log` and continue. The paste-ready columns in Phase 7 cover this case.

---

## Phase 6: Rewrite Key Highlights

The script outputs a `KEY_HIGHLIGHTS_DATA` comment block with raw metrics. You MUST rewrite this into 3-5 strategist bullets before presenting to the user.

Read the generated markdown, find the `<!-- KEY_HIGHLIGHTS_DATA ... -->` block, and replace the entire section (comment + placeholder) with bullets.

**Rules for Key Highlights bullets:**
- Each bullet: **bold lead-in with the metric**, then context/interpretation, then recommendation or next step
- Write like an account strategist briefing a client, not a dashboard summary
- Call out what's working, what's not, and what to do about it
- Reference specific locations or platforms when they're driving a trend
- 3-5 bullets max. No sub-bullets, no tables, no "platform breakdown" lists.

**Good examples:**
- `**DoorDash up 30% WoW** ($1,280, 60 orders) with ROAS at 4.6x and spend efficiency improving. Recommend increasing DD ad budget by 20% next week to test the ceiling.`
- `**UE dragging overall ROAS down to 1.2x** with 68% of sales going back to marketing. Venice and Chicago are the worst performers. Recommend pausing Venice UE ads and reallocating to DD where efficiency is 3x better.`
- `**Net payout at 73.1%** is healthy across the portfolio. Two locations below 60% need attention: [location] and [location].`

---

## Phase 7: Final Review & Present

### Automated Validation (already completed in Phase 4.5)
The hard formula checks ran in Phase 4.5 (`validate_report.py`). If you're at this phase, those passed. The remaining checks are presentation-level:

### Presentation Checks
- [ ] **No "Gross Sales" row** in any table. Tax-inclusive numbers removed.
- [ ] Ops quality data matches source files (if provided)
- [ ] Key Highlights have been rewritten (no `KEY_HIGHLIGHTS_DATA` comment remaining)
- [ ] **Every platform table has 20 rows** (7 financial waterfall + 13 marketing attribution) — no rows omitted
- [ ] **Formatting spot-check** — scan all tables for these common errors:
  - ROAS must be `X.X` with NO "x" suffix (wrong: `8.9x`, right: `8.9`)
  - Percentages must be `X%` with NO decimals (wrong: `6.97%`, right: `7%`)
  - AOV must have cents `$XX.XX` (wrong: `$46`, right: `$46.46`)
  - Currency (non-AOV) must have NO cents (wrong: `$599,438.25`, right: `$599,438`)
- [ ] **Performance Flags are 5-7 max**, grouped by theme — not one per location
- [ ] **Commissions and Commissions %** appear in every platform table

### Present to User

**1. Notion Weekly Update** — Create the page directly in the client's Notion workspace using the Notion MCP tools (`notion-create-pages`). Find the correct parent page/database from the client registry. The page contains the full weekly report with these additions:
   - **QA Section**: Paste the contents of `OUTPUT/validation_report.md` at the end of the report as a "Validation" section. This is visible proof that the formulas were verified.
   - All other sections remain the same (agenda, action items, key highlights, platform tables, location table, ops, campaigns).

**2. Tracker Paste Columns** — Print paste-ready value blocks directly in chat. One block per sheet section, formatted so the team can copy the values and paste into the week column. Format:

```
### UBER EATS — paste into Platform Overview tab, UE section
$735,439
$673,510
...
$522,794
```

Each block is a vertical list of values in the exact row order of the sheet. Sections:
- UBER EATS (platform tab)
- DOORDASH (platform tab)
- GRUBHUB (platform tab)
- Each location (location tab) — one block per location

OVERVIEW is formulas in the sheet — do NOT paste values there.

**3. CSV Export** — Also write `tracker_update.csv` to the output directory as a backup/export option. If Phase 5b uploaded the CSV to Drive, include the Drive URL here.

**4. Any Warnings** — missing files, validation flags, anomalies from `OUTPUT/validation_report.md`. Also surface anything from `OUTPUT/drive_fetch.log` if the Drive auto-fetch hit issues (stale files, missing matches, fallbacks to manual).

---

## Output Formatting Rules

| Type | Format | Example |
|------|--------|---------|
| Currency (large) | `$X,XXX` (no cents) | $581,782 |
| Currency (AOV) | `$XX.XX` (with cents) | $42.39 |
| Percentages | `X%` (no decimals) | 10% |
| ROAS | `X.X` (1 decimal, no x) | 6.2 |
| Orders | `X,XXX` (integer) | 1,234 |
| Null ROAS | `--` | -- |
| UE Offers spend | `--*` | --* |

---

## Platform-Level Overview Table (Metric Order)

This is the exact metric order and naming for all platform tables. **Every platform table MUST include ALL rows.** If a value is zero or not applicable, show `$0`, `--`, or `0` — never skip the row.

**Financial Waterfall:**

| # | Metric | Format | Definition |
|---|--------|--------|------------|
| 1 | Total Sales | $X,XXX | Food subtotal excl tax, incl discounts. Was "Net Sales" in old format. |
| 2 | Net Sales | $X,XXX | Total Sales - Discounts (Offers). |
| 3 | Commissions | $X,XXX | Platform commission fees (absolute value). |
| 4 | Commissions % | X% | Commissions / Total Sales. |
| 5 | Other Adjustments | $X,XXX | Refunds, error charges, merchant fees, misc credits/debits. |
| 6 | Net Payout | $X,XXX | Net Sales - Commissions - Ad Spend - Other Adjustments. Tax-normalized across all platforms. |
| 7 | Net Payout % | X% | Net Payout / Total Sales. Comparable across platforms. |

**Marketing Attribution:**

| # | Metric | Format | If N/A |
|---|--------|--------|--------|
| 8 | Marketing Driven Sales | $X,XXX | $0 or -- |
| 9 | Organic Sales | $X,XXX | — |
| 10 | Total Orders | X,XXX | — |
| 11 | Orders from Marketing | XXX | 0 or -- |
| 12 | Organic Orders | X,XXX | — |
| 13 | AOV | $XX.XX | — |
| 14 | Ad Spend | $X,XXX | Net ad spend (transaction CSV or portal). |
| 15 | Discounts (Offers) | $X,XXX | Merchant-funded offers/promos. |
| 16 | Total Marketing Investment | $X,XXX | Ad Spend + Discounts (Offers). $0 if no marketing. |
| 17 | Marketing Credits | $X,XXX | Platform-provided credits/offsets. $0 if none. |
| 18 | Marketing Spend / Sales % | X% | Total Marketing Investment / Total Sales × 100. |
| 19 | Marketing ROAS | X.X | Marketing Driven Sales / Total Marketing Investment. -- if $0 spend. |
| 20 | Marketing CPO | $XX.XX | Total Marketing Investment / Orders from Marketing. |

**REMOVED:** "Total Gross Sales" (tax-inclusive). Tax is a pass-through and was making cross-platform comparisons misleading.

---

## Notion Report Structure

> **CRITICAL FORMATTING REMINDER — apply to ALL tables in the Notion report:**
> - ROAS = `X.X` (one decimal, **NO "x" suffix**). Write `8.9` not `8.9x`.
> - Percentages = `X%` (**NO decimals**). Write `7%` not `6.97%`.
> - AOV = `$XX.XX` (**with cents**). Write `$46.46` not `$46`.
> - Every platform table = **17 rows** (9 financial waterfall + 8 marketing attribution). Never omit rows even if value is `$0` or `--`.
> - Performance Flags = **5-7 max**, grouped by theme. One flag per theme, not one per location.
> - **No "Gross Sales" row.** Tax-inclusive numbers are removed from all tables.

### Section 1: Weekly Snapshot (NEW — always first after the title)
A single callout box with 6 key numbers. This is the "glance and go" — a reader should get the week's story in 5 seconds.

```
📊 Week at a Glance
| Net Sales | Orders | ROAS | Mkt Spend % | Payout % | WoW Trend |
| $1,220,748 | 25,868 | 8.9 | 6% | 75% | ↓4% sales, efficiency ↑ |
```

The WoW Trend column is a 5-7 word plain-English summary of the week (e.g., "↓4% sales, efficiency ↑" or "flat volume, AOV compression" or "strong week across the board").

### Section 2: Agenda
Continues the conversation from the last client meeting.

### Section 3: Action Items
Carried over + new from this week's data. **Max 5-7 items.** Each item is one line — no sub-bullets, no context paragraphs. If it needs explanation, it goes in the flags.

### Section 4: Key Highlights
3-5 bullets. Each bullet follows this exact format:

**Bold metric + direction** — one sentence of context. One sentence of action.

Example: **UE ROAS up 10% to 8.9** — driven by Ads Manager attribution change (new baseline). Do not flag as improvement in client comms.

Rules:
- Two sentences max per bullet. No paragraphs.
- Lead with the number, not the interpretation.
- If you need more than 2 sentences, it's a flag, not a highlight.

### Section 5: Platform Performance
Detailed metric tables by platform. **Every platform table MUST include all 20 metrics in the standard order** (see metric order table above). If a metric is $0 or not applicable, show `$0`, `--`, or `0` — never omit the row.

**When tracker exports were provided (4-week avg available), use 4 columns per platform:**

| Metric | This Week | WoW | vs 4wk Avg |
|--------|-----------|-----|------------|

WoW = change from prior week (e.g., `+5%`, `-$1,200`). vs 4wk Avg = change from trailing 4-week average. Both come from `platform_comparisons.csv`. Use `▲`/`▼` or `+`/`-` prefixes. Show `--` if insufficient history.

**When tracker exports were NOT provided, use 2 columns:**

| Metric | This Week |
|--------|-----------|

### Section 6: Location Performance
Summary table across all locations. **Max 7 columns** to keep it scannable:

| Location | Orders | Net Sales | WoW | ROAS | Payout % | Flag |
|----------|--------|-----------|-----|------|----------|------|

The Flag column is a one-word tag: `⚠️ downtime`, `📉 organic`, `📊 baseline`, or blank. This lets readers instantly see which locations need attention without reading a paragraph.

Do NOT include per-platform breakdowns (UE Net, DD Net, GH Net) in the location table. Those are in the platform tables.

### Section 7: Performance Flags
5-7 consolidated flags grouped by theme. This is the strategist layer.

**Each flag is exactly:**
```
### 🔴 #1 — Bold Title | Scope
One sentence: what happened. One sentence: why. One sentence: what to do.
[Optional: inline table if comparing 3+ locations — keep to one table per flag]
```

**Three sentences max per flag.** No "RCA:" labels, no "Detail:" labels, no multi-paragraph analysis. If you can't say it in 3 sentences, you're over-explaining.

**Grouping rules:**
- One flag per theme, not per location
- One flag per systemic issue
- Methodology notes = one callout in the header, not a flag
- Ops detail belongs in the Ops section, not in flags

**What NOT to flag:**
- Metrics that moved <5% WoW
- Things already covered in Key Highlights
- Individual location ops detail that's in the Ops tables

### Section 8: Operations & Quality
DoorDash ops tables + UE accuracy tables + menu downtime. **Data tables only** — no narrative, no RCA paragraphs. The flags section handles interpretation. This section is reference data.

### Section 9: Campaign Performance
Granular campaign/ad/promo breakdown by platform.

---

## Key Rules

### General
- NEVER print full dataframes or CSV contents to conversation
- Only print warnings and final summary line
- One client per conversation to avoid context bloat
- Settlement files != dashboard data — always note this
- When extracting from tracker: percentages stored as decimals < 2, ROAS has x suffix, currency has $ prefix
- Week = Monday through Sunday. Always verify the start date is a Monday before running extraction.

### Net Payout Definition
**Net Payout = Net Sales - Commissions - Ad Spend - Other Adjustments.** This is calculated from components, NOT pulled from the platform's payout column. By calculating from components, we strip out sales tax (which each platform handles differently) and make all three platforms directly comparable.

The platform payout columns (`Total payout` on UE, `Net total` on DD, `merchant_net_total` on GH) are used as a **validation check** only. The calculated Net Payout should approximate the payout column minus tax. Flag discrepancies > 2%.

- **UE:** Payout column already excludes most tax (MF Tax deducted). Calculated and column should be close.
- **DD:** Payout column includes ~93% of tax as pass-through. Calculated will be lower by the tax amount.
- **GH:** Payout column includes ~95% of tax as pass-through. Calculated will be lower by the tax amount.

**Net Payout %** = Net Payout / **Total Sales** (excl. tax). Comparable across all platforms.

**Why we changed this (April 2026):** The previous approach used the payout column directly, which included tax on DD/GH but not UE. This made DD payout % appear ~10pts higher than UE, leading to misleading cross-platform comparisons. The new approach normalizes by calculating from pre-tax components.

### UE Attribution (Two-Tier System)
- **Offer attribution is per-order** in the transaction CSV: `Offers on items (incl. tax)` < 0 or `Delivery Offer Redemptions (incl. tax)` < 0 on a Completed order row → that order is offer-driven. Available for ALL clients.
- **Ad spend rows** in the transaction CSV have blank Order Status, $0 sales, no Order ID — daily per-store aggregate charges. Ad spend is always counted in Total Marketing Investment regardless of tier.
- **Tier 1 (default):** Offer-only attribution. No Ads Manager needed. Ad spend in investment total, but no ad-attributed orders/sales. ROAS is conservative. This is the standard path for clients without Ads Manager access.
- **Tier 2 (enhanced):** When `UE Ads Manager Access = Yes` AND performance export provided. Ads Manager cross-reference adds ad-attributed orders with full-overlap dedup. Multi-store campaigns distributed by offer order volume. Hard cap at total completed orders.
- **Do NOT block or warn** when Ads Manager is unavailable for a Tier 1 client. It's not missing data — it's a different (valid) attribution tier.
- UE Offers spend is pct only, shows `--*` for dollar amount

### UE $0.99 Marketing Fee
- UE charges some clients a **$0.99 marketing fee per offer redemption**. Look for `Other payments description` containing "marketing" or "promo" with `Other payments` = -0.99.
- This is an **offer cost**, NOT ad spend. Add to Offer/Discount Value.
- **Active for most clients.** Currently inactive for goop Kitchen. Check per-client and note in validation flags.

### DoorDash
- DD store names differ from tracker names — use client registry mappings
- Enterprise clients (e.g., goop): ad spend is invoiced separately, NOT in settlement CSV. Portal exports are source of truth for marketing attribution + ad spend.
- `$0.99` flat marketing fee = always an offer redemption fee, never ad spend
- `Channel = "Marketplace"` filter on all metrics
- Completed = `Transaction type = "Order"` AND `Sales (excl. tax)` > 0

### Grubhub
- Ad Spend is NOT in the settlement CSV — leave as $0 unless separate ad data provided
- If `merchant_funded_promotion` and `merchant_funded_loyalty` are both $0, marketing is inactive (correct, not a data gap)
- Net Payout = calculated (Net Sales - Commissions - Ad Spend - Other Adjustments), NOT from payout column
- Total Sales = sum of `subtotal` (Completed Marketplace orders). No tax-inclusive "Gross Sales" row.
- GH store names use city + address format — store map keys are pipe-delimited: `"Goop Kitchen|Beverly Hills|9254 Alden Dr"`
