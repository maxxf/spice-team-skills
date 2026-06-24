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
version: 1.2.0
---

# Client Diagnostics

**Goal: the user types one sentence at the start, drops files into one Drive folder, and gets one Notion URL back.**

When invoked, run this entire flow yourself. Do not make the user write code, edit JSON, or copy MCP payloads. Use Drive as the canonical data store. Tell them exactly what to fetch.

> **Strategy filter — route the action plan through the playbooks.** When generating recommendations, consult `Cowork/Skills/campaign-plan/references/playbooks/what-works.md` + `marketplace-playbook.md`. Apply these specifically: (1) **Foundations gate first** — if rating <4.5, error >2%, uptime <95%, or menu conversion <20%, the action plan leads with foundations work, NOT ad spend. (2) **Cite proven precedent** — when proposing a tactic, name the playbook play it applies (e.g., "Sunnyvale flyer at low-ratings location", "Spend X Save Y aggressive at sub-20% conversion", "Friday-depth tweak at high-weekend-competition location"). (3) **DoorDash priority** for new clients (89% payout vs 78% UE). (4) **Location-based, not keyword** for any paid recommendation. (5) **Segment offers** by New/Existing/Lapsed/All; never recommend a blanket promo for established locations. The diagnostic's job isn't to invent strategy each time — it's to apply the proven playbook to this client's specific shape.

**Output shape.** The Notion page is dashboard-first: Half 1 is skim-in-60s and
flat — foundation banner (if gated), 4 hero metric cards, 7-dim Brand Health
radar, Win/Risk/Opportunity/Decision cards, a This Week / Next 30 / Watch
action kanban, and the tier-health donut. Half 2 holds all analyst depth, each
section collapsed under a Notion `toggle`. The block builder is
`orchestrator/notion_assembly.py`.

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

Adapt the list to the client's actual platforms. If you know the client doesn't run on Grubhub (check `data_quirks` in the config), drop the GH section with a note. If unsure, ask: "Does this client run on UE / DD / GH? I'll skip whatever they don't use."

End the message with: "Once everything's in the folder, just say 'done' or 'ready' and I'll take it from there. The full checklist also lives at `references/data-collection-checklist.md` if you want to print it."

### Step 4: Wait for the user's "done" signal

Don't proceed until the user confirms. They may need a few hours.

When they confirm, list the Drive folder contents. Validate:
- At least the financial CSV is present per platform that's in scope
- At least 1 screenshot is present
- The window matches what you expect (look at file modification dates and ranges in the data; flag if exports look like they're from different windows)

If something critical is missing, tell them what and offer to proceed with degraded analysis (e.g., "no UE Repeat Customer Rate, so the radar's Re-order dim will use DD-only blend; ok to proceed?"). If they say proceed, continue. If they want to fetch the missing piece, wait again.

### Step 5: Build the unified input CSV from the dropped files

Download files from the Drive folder to `/tmp/diagnostic-inputs-<slug>-<timestamp>/`. Read each. Transform per-store metrics into the unified 22-column schema (see `references/input-csv-schema.md`).

Mapping notes:
- **UE financial CSV** → topline (gross_sales, orders, net_payout) per store per week. Skip header row (`skiprows=1`).
- **UE conversion funnel screenshot/CSV** → menu CVR (impressions → orders) and storefront → menu CTR per store
- **UE menu items export** → photo coverage % (count items with photo URL / total items) per store, categories_count, categories_populated
- **UE repeat customer screenshot + DD Frequent Customers** → optional `reorder_rate_pct` column (volume-weighted unified rate, framework *Re-order Rate*). If you genuinely can't pull it, omit the column — the radar suppresses the Re-order dim and flags a data-quality gap rather than showing a fabricated score. Never type a guessed number here.
- **DD financial CSV** → topline supplement, blend with UE
- **DD ops quality export** → error_rate_pct, cancellation_pct, uptime_pct, hours_accurate per store
- **Customer sentiment (cross-platform)** → build the unified `rating` per the framework's *Customer Sentiment* spec: per-platform positive rate (DD loved/(loved+disliked); UE/GH 4–5★/total), volume-weight by rating count, then `rating = round(1 + 4 × positive_rate, 2)`. Optionally also emit `customer_sentiment_pct` (the 0–100 blend) and `rating_count` columns — the ops sub-skill passes these through. DD-only client → `rating` is the loved-rate on the 0–5 scale; note the single-platform gap in `data_quality.gaps`.
- **DD sponsored listings + promos** → spend, attributed_sales, roas, promo_count_active per store
- **GH performance export** → topline supplement, blend
- **Screenshots** → fill in `hero_set` (true if hero image visible, false if missing/default), categories from category structure screenshot
- **Anything genuinely missing** → use the framework's documented defaults (`references/diagnostic-framework.md`) and add a `data_quality.gaps` note in the resulting diagnostic

Save the unified CSV to the Drive folder as `inputs/unified-input.csv` so it lives next to the source data for audit. Also keep a local copy at `/tmp/diagnostic-runs/<slug>/<timestamp>/inputs/` for the orchestrator.

### Step 6: Run the orchestrator

```bash
cd /Users/maxx/Desktop/Cowork/Skills/client-diagnostics
.venv/bin/python scripts/run_diagnostic.py --client <slug> --inputs-dir /tmp/diagnostic-runs/<slug>/<timestamp>/inputs
```

If the schema validator complains, surface the exact error to the user. If a column is missing because you couldn't derive it from the source files, offer the framework default and re-run.

**Completeness preflight (do not skip).** The runner prints a `=== Completeness preflight ===` block with a `DEPTH:` line (FULL / STANDARD / PARTIAL / TOPLINE-ONLY) and the missing input categories. **Surface this to the user verbatim before producing the page.** If DEPTH is not FULL/STANDARD, tell the user exactly which inputs are missing and what each gap costs (e.g. "no conversion funnel → no menu-CVR analysis"), and ask whether to pull them first or proceed. If they proceed, **stamp a banner at the very top of the Notion page**: `⚠️ <DEPTH> diagnostic — missing: <categories>. Pull these for full depth.` A thin run must never ship looking complete. Always run with `--pdf` (or `--publish`) so the chart/PDF layer is produced — a text-only diagnostic is half the deliverable. For marquee clients, add `--require-full` to hard-abort on a partial input set.

The script writes results to `/tmp/diagnostic-runs/<slug>/<timestamp>/`. Capture the path.

### Step 7: Upload charts to Drive

Run the publish step first (Step 8 command) so `charts_manifest.json` exists, then
upload **every** PNG listed in that manifest — do not hardcode a chart list, it
varies per client (radar + tier donut always; plus sparklines, top-15-green,
UE funnel, campaign 2x2, and any sub-skill charts when their data is present).
Each manifest entry has `{chart_id, filename, local_path}`.

Upload each `local_path` to a new subfolder in the same Drive cycle folder:
`output-charts/`. Use the Drive `create_file` MCP. After upload, set the file's
permission so anyone with the link can view (Notion external image URLs need
this). Capture each file's shareable URL keyed by `chart_id`.

If Drive upload fails for any chart, fall back: tell the user, give the local paths, they drag them in manually after the page is created.

### Step 8: Create the Notion page with embedded charts

Run the publish payload generator:

```bash
.venv/bin/python scripts/run_diagnostic.py --client <slug> --inputs-dir <inputs-dir> --publish
```

Read `<result_dir>/publish_blocks.json` and `<result_dir>/charts_manifest.json`.

`publish_blocks.json` is the full page with every image block already swapped
for a clearly-labelled placeholder paragraph of the form
`📊 Chart: <chart_id> — replace this paragraph with the uploaded image block (<filename>; local: <path>)`.
Half-2 detail sections are `toggle` blocks (collapsed by default) — leave their
structure intact; placeholders may live inside a toggle's `children`.

For each manifest entry, locate the placeholder paragraph whose text contains
that entry's `chart_id`, and replace the whole paragraph with a Notion image
block pointing at the Drive URL you captured for that `chart_id`:

```json
{"type": "image", "image": {"type": "external", "external": {"url": "<drive_url>"}}}
```

**PDF attachment (keeps the exact format in Notion).** `--publish` also
renders `<slug>-diagnostic.pdf` and the manifest includes a `{"kind":"pdf"}`
entry. Upload that PDF to the Drive cycle folder (link-viewable, same as
charts), then find the placeholder paragraph that reads `📄 PDF placeholder …`
and replace it with a Notion bookmark to the Drive PDF URL:

```json
{"type": "bookmark", "bookmark": {"url": "<drive_pdf_url>"}}
```

This is why Notion is the preferred home: the page is native + searchable for
skimming, and the exact-layout PDF lives one click away on the same page.

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
- `specs/2026-05-08-orchestrator-redesign.md` (architecture spec)

## Sub-skills this orchestrates

Dispatched in parallel from Phase 2. You don't usually need to think about these unless something breaks:
- `diagnostic-topline` (financials, momentum, AOV / Re-order radar)
- `diagnostic-menu` (CVR, photo coverage, SKU sprawl, Conversion / Traffic radar)
- `diagnostic-ops` (uptime, errors, rating, foundation gate inputs)
- `diagnostic-campaigns` (ROAS, promo mix, Campaigns radar, Marketing Efficiency input)
- `diagnostic-action-plan` (tier-grouped kanban from all findings)
