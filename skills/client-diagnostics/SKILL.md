---
name: client-diagnostics
description: >
  Runs a 90-day diagnostic for a delivery marketplace client and publishes
  the result to their Notion workspace. Use when the user says "diagnose
  [client]", "run a diagnostic for [client]", "build an action plan for
  [client]", "what's wrong with [client]'s performance", "diagnose
  [client]'s storefront", or asks to assess a client's delivery marketplace
  health. Handles the full flow: gives the user an explicit data-collection
  checklist, creates the Drive folder for them to drop files into, waits for
  confirmation, runs the multi-skill orchestrator, uploads charts, creates
  the Notion page, returns one URL.
version: 1.9.0
---

# Client Diagnostics

**Goal: the user types one sentence at the start, drops files into one Drive folder, and gets one Notion URL back.**

When invoked, run this entire flow yourself. Do not make the user write code, edit JSON, or copy MCP payloads. Use Drive as the canonical data store. Tell them exactly what to fetch.

## Triggers

- "diagnose [client]"
- "run a diagnostic for [client]"
- "build an action plan for [client]"
- "what's wrong with [client]'s performance"
- "[client]'s storefront audit" (when 90-day scope, not point-in-time)
- User pastes platform data and asks for analysis

## The flow

### Step 1: Resolve the client

Extract the client name from the user's message. Check `clients/` for an existing config (e.g., user said "Daily's" → look for `clients/dailys.json`).

If no config exists:
1. Ask once for the display name if you can't infer it confidently
2. Generate a slug: lowercase, strip apostrophes, dashes for spaces ("Daily's" → "dailys", "Goop Kitchen" → "goop-kitchen")
3. Copy `clients/_template.json` to `clients/<slug>.json`. Fill in `client_slug` and `client_display_name`.
4. Continue.

### Step 2: Resolve the Notion target

Read the client config. If `notion.parent_page_id` is set, use it. If null, find it via `notion-search`. Try in this order, stop at first clear hit:
1. `<display name> Wiki`
2. `<display name> Client Portal`
3. `<display name>` (filter visually for the right page in Spice / Clients)

Confirm with the user in one line. Once confirmed, write the page ID back to `clients/<slug>.json`. If notion-search returns nothing usable, ask the user for the URL.

### Step 3: Create the Drive drop folder and hand the user the data checklist

Canonical root: **`Spice Digital LLC / 1. Clients / 1. Active`** (Drive folder ID `1kIwq7HSW2v427c0XZVynrO8XnAuxvkMO`).

Each active client already has a folder there with numbered subfolders (`1. Client Portal`, `2. Creative`). Your job is to create the diagnostics path:

```
1. Active /
  └── <Client Display Name> /
       ├── 1. Client Portal /            (already exists)
       ├── 2. Creative /                 (already exists)
       └── 3. Diagnostics /              (create if missing)
            └── <YYYY-MM-DD> /           (this cycle, dated today)
                 └── inputs /
                      ├── ue /
                      ├── dd /
                      ├── gh /
                      ├── screenshots /
                      └── notes /
```

Use the Drive `create_file` MCP. Steps:
1. Search for `<Client Display Name>` folder under parent `1kIwq7HSW2v427c0XZVynrO8XnAuxvkMO`. If not found, the client doesn't exist in `1. Active` yet, so create the client folder first as a child of `1kIwq7HSW2v427c0XZVynrO8XnAuxvkMO`.
2. Search for `3. Diagnostics` under the client folder. Create if missing.
3. Create the dated cycle folder under `3. Diagnostics`.
4. Create the `inputs/` subfolder structure inside.
5. Return the cycle folder URL.

Sharing should inherit from the parent (Spice team edit access). Don't override unless explicitly asked.

Then post the data-collection checklist to the user. Pull the full list from `references/data-collection-checklist.md`. Format it as actual checkboxes the user can mentally tick off, broken into platform sections. Lead with the Drive folder link so they know where to drop.

Call out the **REQUIRED per-location captures explicitly** in the checklist
you post: UE Repeat Customers, DD Frequent Customers %, GH repeat (if
exposed), and UE conversion funnel — each per location, legible and
machine-readable, saved under `inputs/screenshots/{reorder,funnel}/`. Tell
the user that Re-order Rate going unscored is a data-pull failure, not an
analysis choice, and that you'll do a legibility pre-flight on these when
they say "done". Also remind them the source-export date stamps are
authoritative — if a platform's picker snapped to a different range, the
export's own dates win.

Adapt the list to the client's actual platforms. If you know the client doesn't run on Grubhub (check `data_quirks` in the config), drop the GH section with a note. If unsure, ask: "Does this client run on UE / DD / GH? I'll skip whatever they don't use."

End the message with: "Once everything's in the folder, just say 'done' or 'ready' and I'll take it from there. The full checklist also lives at `references/data-collection-checklist.md` if you want to print it."

### Step 4: Wait for the user's "done" signal

Don't proceed until the user confirms. They may need a few hours.

When they confirm, list the Drive folder contents. Validate:
- At least the financial CSV is present per platform that's in scope
- At least 1 screenshot is present
- The window matches what you expect. **Window-trust rule:** the date stamps inside the source exports are authoritative over the manifest/Slack header. If they disagree, use the export dates and note the discrepancy (it goes in the report's `data_quality_footer`).
- The REQUIRED per-location captures (UE Repeat Customers, DD Frequent Customers %, UE conversion funnel; GH repeat if exposed) are present AND legible. Open them. Blurry / cropped / truncated = a data-pull failure — ask for a re-pull, don't proceed with Re-order silently data-pending unless the user explicitly accepts it.

If something critical is missing, tell them what and offer to proceed with degraded analysis (e.g., "no UE Repeat Customer Rate, so the radar's Re-order dim will use DD-only blend; ok to proceed?"). If they say proceed, continue. If they want to fetch the missing piece, wait again.

### Step 5: Build the unified input CSV from the dropped files

Download files from the Drive folder to `/tmp/diagnostic-inputs-<slug>-<timestamp>/`. Read each. Transform per-store metrics into the unified 22-column schema (see `references/input-csv-schema.md`).

Mapping notes:
- **UE financial CSV** → topline (gross_sales, orders, net_payout) per store per week. Skip header row (`skiprows=1`).
- **UE conversion funnel screenshot/CSV** → menu CVR (impressions → orders) and storefront → menu CTR per store
- **UE menu items export** → photo coverage % (count items with photo URL / total items) per store, categories_count, categories_populated
- **UE repeat customer screenshot** → portfolio Re-order Rate (no per-store breakdown; emit at portfolio level)
- **DD financial CSV (per-order)** → topline supplement, blend with UE. **Also bucket every order row by ISO week → `metrics.trend_weekly` (weekly GMV + orders) AND by day×hour → `metrics.daypart` (7×24 order-count matrix + peak).** This is REQUIRED whenever the per-order export exists — see the trend/daypart rule below.
- **GH finance CSV (per-order)** → topline supplement; blend its per-order rows into the SAME `metrics.trend_weekly` + `metrics.daypart` derivation as DD (use `order_date` + `order_hour_of_day`).
- **DD ops quality export** → rating, error_rate_pct, cancellation_pct, uptime_pct, hours_accurate per store
- **DD sponsored listings + promos** → spend, attributed_sales, roas, promo_count_active per store
- **GH performance export** → topline supplement, blend
- **Screenshots** → fill in `hero_set` (true if hero image visible, false if missing/default), categories from category structure screenshot
- **Anything genuinely missing** → use the framework's documented defaults (`references/diagnostic-framework.md`) and add a `data_quality.gaps` note in the resulting diagnostic

Save the unified CSV to the Drive folder as `inputs/unified-input.csv` so it lives next to the source data for audit. Also keep a local copy at `/tmp/diagnostic-runs/<slug>/<timestamp>/inputs/` for the orchestrator.

### Step 6: Run the orchestrator

```bash
# Run from the client-diagnostics skill directory (wherever the plugin is installed)
cd "$(dirname "$(find ~ -name SKILL.md -path '*client-diagnostics*' 2>/dev/null | head -1)")"
.venv/bin/python scripts/run_diagnostic.py --client <slug> --inputs-dir /tmp/diagnostic-runs/<slug>/<timestamp>/inputs
```

If the schema validator complains, surface the exact error to the user. If a column is missing because you couldn't derive it from the source files, offer the framework default and re-run.

The script writes results to `/tmp/diagnostic-runs/<slug>/<timestamp>/`. Capture the path.

### Step 7: Upload charts to Drive

Charts:
- `<result_dir>/cross_cutting/radar_7dim.png`
- `<result_dir>/cross_cutting/tier_donut.png`
- `<result_dir>/cross_cutting/top15_green_bar.png`
- `<result_dir>/campaigns/charts/campaign_2x2.png`

Upload each to a new subfolder in the same Drive cycle folder: `output-charts/`. Use the Drive `create_file` MCP. After upload, set the file's permission so anyone with the link can view (Notion external image URLs need this). Capture each file's shareable URL.

If Drive upload fails for any chart, fall back: tell the user, give the local paths, they drag them in manually after the page is created.

### Step 7.5: Build the client HTML + PDF report (canonical, parameterized)

The client-facing report is built by `references/build_report.py` — the
**single** canonical builder. It is fully data-driven: it reads
`findings.json` + `metrics.json` from the run dir. **Never hand-edit
generated HTML. Never use per-client literals. Never regex-patch a report.**
If a value is wrong, fix `findings.json`, not the HTML or the Python.

```bash
# run dir must contain findings.json, metrics.json, report_style.css,
# assets/spice_icon.svg (copy from references/), charts/ (from Step 7-charts)
cp references/report_style.css <run_dir>/
mkdir -p <run_dir>/assets && cp references/assets/spice_icon.svg <run_dir>/assets/
.venv/bin/python references/make_charts.py <run_dir>      # radar, tier donut, GMV bar, funnel, storefront audit, trend overlay, daypart heatmap (each renders iff its metrics key is present)
.venv/bin/python references/build_report.py <run_dir>     # → HTML
.venv/bin/python references/export_pdf.py <run_dir>/<report>.html <run_dir>/<report>.pdf
```

The `findings.json`/`metrics.json` schema is documented in
`references/report-data-contract.md`. Build `findings.json` from the
sub-skill outputs; populate every required narrative field there.

### Step 7.6: Build the Spice-branded client deck (.pptx)

The **client-shared deliverable** is a Spice-branded PowerPoint deck built by
`references/build_deck.js` — the **single** canonical deck builder. It is
fully data-driven: it reads the SAME `findings.json` + `metrics.json` the
report consumes, embeds whichever `charts/*.png` exist in the run dir, and
sources its colour palette by **parsing the Spice Design System tokens out of
`report_style.css`** (so the deck and HTML report can never drift). **Zero
per-client literals — never hand-edit the generated .pptx, never hardcode a
client name/number in build_deck.js.** Deck-only narrative (title kicker,
headline-finding slide, action lanes, closing asks) lives under the optional
`deck` object in findings.json — see `references/report-data-contract.md`.

Node dependency: `pptxgenjs`. Install it once in the run dir (same pattern as
other per-run deps):

```bash
# run dir already has findings.json, metrics.json, report_style.css, charts/
cd <run_dir> && npm install pptxgenjs
node "$(dirname "$(find ~ -name SKILL.md -path '*client-diagnostics*' 2>/dev/null | head -1)")/references/build_deck.js" <run_dir>
# → <run_dir>/<client-slug>-deck.pptx
```

Charts degrade gracefully: any chart PNG that is absent is skipped (no broken
image, no crash) and its slide element is omitted. The deck builder is
self-contained — the Spice wordmarks live in `references/assets/` (no Cowork
path dependency).

**Locked report rules — these regressed on a live client; do not break them:**

1. **Canonical 6-slot hero (fixed order):** `90-Day Gross` · `Orders` ·
   `Blended AOV` · `Net Payout` · `Order Completion` · `Customer Sentiment`.
   If a metric is unavailable on a platform, render `n/a*` with a footnote
   (`hero.na_footnote`) — **never silently drop a slot or substitute a
   different metric.**
2. **Required Half-2 toggle set (all present, omission is a bug):** Portfolio
   Snapshot · **Menu & Storefront** · Ops · Brand Operational Health ·
   Campaigns · Location Tiers · Full Action Plan · Appendix. **Menu &
   Storefront is required**: synthesize any prior storefront audit; if
   absent, the toggle still renders with an explicit DATA-PENDING block
   flagging conversion funnel + re-order rate.
3. **Window-trust rule:** source-export date stamps are authoritative over
   manifest/Slack headers. If they disagree, use the export dates and note
   the discrepancy in `data_quality_footer`.
4. **Attribution rule:** ROAS / attributed-sales must be labeled
   campaign-lifetime vs 90d-matched. Never headline attributed sales that
   exceed window GMV without the caveat inline at point of use (radar_notes
   + campaigns_detail).
5. **Radar honesty:** Re-order Rate is first-class but if the data isn't
   machine-readable it is DATA-PENDING — excluded from the overall, never
   guessed or carried silently. Proxy-derived axes (Conversion/Traffic from
   ad data when true funnel absent) carry an `(ad proxy)` label. Overall =
   mean of measured axes only.
6. **Trend + daypart are derivable, not deferrable:** the 90-Day Trend chart
   (`metrics.trend_weekly`) and Daypart heatmap (`metrics.daypart`) are
   **derived deterministically from the per-order DoorDash + Grubhub
   transaction exports** (DD `Timestamp local time`; GH
   `order_date`/`order_hour_of_day`) — one row per order, bucketed to ISO
   week and to day×hour. **Whenever those per-order exports exist, you MUST
   derive and populate `trend_weekly` + `daypart` — do NOT mark them
   "deferred".** Only leave them null if the per-order exports are genuinely
   absent (platform won't expose per-order data for this account vintage),
   and say so explicitly in `data_quality_footer`. A store-aggregated
   summary CSV does not substitute (no per-order timestamp to bucket). The
   builder renders the real charts when present and an honest text note when
   genuinely absent — it never fabricates a sparkline or heatmap.
7. **Deliverable model — three artifacts, explicit roles:**
   - **HTML report = the creator's working / presentation artifact.** The
     GM / Strategy Lead drives the internal review and the live client
     walkthrough *from the HTML report* (it is self-contained, all charts
     base64-inlined, opens in any browser). It is NOT sent to the client as
     the deliverable — it is the analyst's cockpit.
   - **Spice-branded PPTX deck = the client-shared deliverable.** Built by
     `references/build_deck.js` (Step 7.6), filed in the client's Drive
     `…/3. Diagnostics/<cycle>/` folder. It opens and is editable in Google
     Slides on the web, so the client can review/annotate it. This is the
     artifact you put in the client's hands.
   - **Full PDF = the analyst detail / permanent record.** The deterministic
     visual PDF (all charts, from `export_pdf.py`) is the complete-depth
     archival copy; it also lands in the same Drive Diagnostics folder
     alongside the deck for anyone who wants the full report without a
     browser.
   - **Notion page = the thin, searchable index.** Exec summary + the key
     tables + **prominent links to the deck and the PDF** in Drive. **Do NOT
     prescribe manually rebuilding charts into Notion** — the integration
     can't embed local PNGs and per-cycle manual chart-dropping is exactly
     the drift this skill exists to prevent. Notion links the artifacts; it
     is not itself the deliverable.

   Final hand-off: drop both the **deck (.pptx)** and the **PDF** into the
   client's Drive `…/3. Diagnostics/<cycle>/` folder (a ~10-second file move
   each; automated upload is not reliable — the Drive tool can't take a
   multi-MB inline upload), then paste those Drive links into the Notion
   record and the `#int-[client]` Slack thread, calling out the deck as the
   client-facing deliverable and the PDF as the full record. Share Notion
   links via the **workspace-slug Notion URL or the client-portal navigation
   path**, never the integration's bare `notion.so/<id>` deep link (it 404s
   for human viewers).

Conformance is enforced by `tests/test_report_conformance.py` (both `.half`
banners, exactly 6 canonical hero slots, `/ 10` radar title, full required
toggle set, zero per-client literal bleed in the report builder source AND in
`references/build_deck.js`, and — when pptxgenjs is installable — a valid
.pptx with the expected slide count that embeds charts when present and
degrades when absent).

### Step 8: Create the Notion page with embedded charts

Run the publish payload generator:

```bash
.venv/bin/python scripts/run_diagnostic.py --client <slug> --inputs-dir <inputs-dir> --publish
```

Read `<result_dir>/publish_blocks.json` and `<result_dir>/charts_manifest.json`. For each manifest entry, find the placeholder paragraph in the blocks (its content references the chart filename) and replace with a real Notion image block:

```json
{"type": "image", "image": {"type": "external", "external": {"url": "<drive_url>"}}}
```

Read the page title from `<result_dir>/notion_page.md`'s H1 line.

Call `notion-create-pages` MCP:
- parent: `{"page_id": "<from client config>"}`
- properties: `{"title": [{"text": {"content": "<page title>"}}]}`
- children: the substituted blocks list

Capture the returned page URL.

### Step 9: Return the URL plus a short summary

Post back:

> ✅ Diagnostic published: `<notion url>`
>
> **Foundation gate:** [triggered with reasons | clear]
> **Tier breakdown:** N Red, N Yellow, N Green, N New (list red store names if 1 to 3)
> **Top action:** [first P1 auto-action from the action plan]
>
> Source data lives at: `<drive cycle folder url>`

That's the entire flow. The user typed one sentence at the start, dropped files in one folder, said "done" once, got one URL back at the end.

## What to do when something goes wrong

| Situation | What you do |
|---|---|
| Client config missing | Create from template (Step 1), continue silently |
| Notion target unset | Search via notion-search, confirm with user once, write back to config |
| Drive folder creation fails | Surface error. Common cause: missing parent folder. Create chain of parents. |
| User says "done" but folder is empty / partial | List what's missing, ask if they want to proceed degraded or fetch more |
| Schema validator fails on missing columns | Show the exact missing columns. Offer framework defaults. Don't silently fudge. |
| Sub-skill subprocess fails mid-run | Orchestrator fail-opens. Tell the user the affected section is incomplete. Foundation gate auto-triggers if ops or menu fails. |
| Drive chart upload fails | Fall back: surface failure, give local paths, user drags into Notion manually |
| Notion publish fails | Save substituted blocks to a file, give user the path so they can retry from another session |

## Anti-patterns

- Don't ask the user to fill 22 CSV columns by hand. Pull from their data sources.
- Don't ask the user to edit JSON. Do it for them.
- Don't ask the user to copy-paste MCP payloads. Call MCPs yourself.
- Don't dump the full schema in chat. Give them the data-collection checklist instead (it maps to the schema implicitly).
- Don't proceed without the foundation gate inputs (rating, error_rate, uptime, CVR, photos). If any are missing and you have to default, surface it loudly so the user knows the gate may be wrong.
- Don't skip the source-data audit trail. Always keep the unified CSV in Drive next to the raw inputs.

## Files in this skill

- `scripts/run_diagnostic.py` (Python runner, called from Step 6 onward)
- `orchestrator/entry.py` (Phase 1 to 5 controller)
- `orchestrator/notion_publisher.py` (block filtering for publish)
- `orchestrator/input_schema.py` (validator)
- `clients/<slug>.json` (per-client config: Notion target, brand, thresholds)
- `clients/_template.json` (template for new clients)
- `references/data-collection-checklist.md` (GM-facing data shopping list)
- `references/input-csv-schema.md` (the 22-column schema)
- `references/diagnostic-input-template.csv` (empty header-only template for manual builds)
- `references/diagnostic-framework.md` (radar bands, foundation thresholds, tier rules, pattern library, defaults for missing data)
- `references/build_report.py` (canonical, fully parameterized client HTML report builder — reads findings.json+metrics.json, zero per-client literals)
- `references/build_deck.js` (canonical, fully data-driven Spice-branded client deck builder — reads the SAME findings.json+metrics.json+charts, parses palette tokens from report_style.css, zero per-client literals; needs `npm install pptxgenjs` in the run dir)
- `references/make_charts.py` (canonical chart module — /10 radar, performance-tier donut, GMV bar, conversion funnel, storefront audit, weekly trend overlay, daypart heatmap; all data-driven, standardized suptitle-in-margin title/subtitle pattern, honestly no-ops any chart whose metrics key is genuinely absent)
- `references/export_pdf.py` (HTML→PDF via Chrome headless)
- `references/report_style.css` (Spice Design System stylesheet — restyle here, regenerate; never hand-edit per client)
- `references/report-data-contract.md` (the findings.json/metrics.json schema the builder consumes)
- `references/assets/spice_icon.svg` (inline brand mark for the HTML report)
- `references/assets/spice_wordmark_cream_on_orange_square.png` + `spice_wordmark_red.png` (deck logos — self-contained, no Cowork dependency)
- `specs/2026-05-08-orchestrator-redesign.md` (architecture spec)

## Sub-skills this orchestrates

Dispatched in parallel from Phase 2. You don't usually need to think about these unless something breaks:
- `diagnostic-topline` (financials, momentum, AOV / Re-order radar)
- `diagnostic-menu` (CVR, photo coverage, SKU sprawl, Conversion / Traffic radar)
- `diagnostic-ops` (uptime, errors, rating, foundation gate inputs)
- `diagnostic-campaigns` (ROAS, promo mix, Campaigns radar, Marketing Efficiency input)
- `diagnostic-action-plan` (tier-grouped kanban from all findings)
