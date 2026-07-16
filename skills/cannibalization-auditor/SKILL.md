---
name: cannibalization-auditor
description: >
  Runs a 6-month cannibalization + spend reallocation audit for a multi-unit
  restaurant client on UE/DD/GH. Use this skill whenever the user says "run a
  cannibalization audit for [client]", "audit [client]'s ad spend", "find the
  waste in [client]'s 3P marketing", "where is [client] cannibalizing",
  "route [client]'s spend by location", "build a spend reallocation report for
  [client]", "is [client] overspending on 3P", "[client] portfolio audit",
  "[client] paid vs organic mix audit", or asks to assess whether a brand's
  delivery marketplace marketing dollars are buying incremental sales.
  Different from client-diagnostics (90-day point-in-time health check) — this
  is a 6-month decision tool that returns per-location routing recommendations
  (concentrate / hold / pull-back-to-NC-only / cut / fix-ops-first) and the
  projected dollar swing of each move. Use this even if the user doesn't say
  "cannibalization" explicitly — any question about whether ad spend is
  earning its keep across multiple locations triggers it. Works for any
  multi-unit restaurant; nothing about it is specific to a particular client.
version: 0.1.0
---

# Cannibalization Auditor

**Goal:** the user types one sentence at the start, drops 6 months of platform exports into one Drive folder, and gets back a deliverable that tells them — per location — what to do with their 3P marketing spend.

The output is a cannibalization finding plus a routing decision per location — CONCENTRATE / HOLD / PULL_BACK_TO_NC_ONLY / CUT / FIX_OPS_FIRST — derived directly from observed spend events, ROAS, payout %, mix shift, and operational quality. No tier taxonomy; the action falls out of the signals.

## When to use this vs. client-diagnostics

- **client-diagnostics** = 90-day point-in-time health check. Storefront audit, foundation gate, tier sub-buckets across many dimensions. Output: action plan.
- **cannibalization-auditor** = 6-month decision tool. Spend vs. sales counterfactual. Output: per-location routing decision + dollar projection.

A client can run both. They answer different questions.

## Triggers

- "run a cannibalization audit for [client]"
- "audit [client]'s ad spend"
- "find the waste in [client]'s 3P marketing"
- "where is [client] cannibalizing"
- "route [client]'s spend by location"
- "build a spend reallocation report for [client]"
- "is [client] overspending on 3P"
- "[client] paid vs organic mix audit"

## Before you start: know the method

Read `references/methodology-plain-english.md` once. It's the five-step explanation of how the audit works, the honesty rules, and a paste-ready version for the client. An operator who can't explain the method in their own words shouldn't ship the deliverable.

## Where the spend + attribution numbers come from (canonical first)

**The auditor consumes Spice's canonical attribution, it does not invent its own.** Marketing spend and marketing-driven sales must follow the weekly-reporting methodology (`weekly-reporting/references/output-schema.json` and `spice-agent/WEEKLY-REPORTING-METHODOLOGY.md`). Two sourcing paths:

1. **Existing Spice clients (preferred) — source from weekly reporting.** The client is already reported weekly with canonical per-order attribution. The auditor's `unified.csv` is built directly from those per-location-per-week metrics:

   | auditor field | canonical source (weekly-reporting `metrics`) |
   |---|---|
   | `gross_sales` | `total_sales` (food subtotal excl tax — NOT platform gross; avoids DD/GH tax distortion) |
   | `spend` | `total_marketing_investment` (= Ad Spend + Discounts, credits netted, co-funded excluded) |
   | `attributed_sales` / `paid_sales` | `marketing_driven_sales` (per-order, **deduped** — ad+offer on one order counted once) |
   | `organic_sales` | `organic_sales` |
   | `net_payout` | `net_payout` (calculated from components, tax-normalized) |
   | `roas` | `marketing_roas` (= MDS / Total Marketing Investment) |

   When sourced this way, the double-dip is already solved at the order level, the numbers **reconcile with the weekly scorecard the client already sees**, and the audit inherits the reporting **completeness gate** (`weekly-reporting/scripts/validate_report.py`) — which refuses to run on missing offer exports. (Goop W24 proof: a $139K headline-vs-tier gap came purely from missing offer exports on 9 of 15 stores. That same gap would silently break a cannibalization audit. Don't let it.)

2. **Cold prospects (fallback) — parse raw exports.** A prospect isn't on weekly reporting, so the auditor parses raw platform exports per the data-collection checklist and applies a crude order-can't-exceed-sales cap to approximate the canonical dedupe. This is good enough for a sales-grade finding but is explicitly the fallback, not the standard. Flag in the manifest that attribution is approximate.

**For Goop specifically:** Goop is reported weekly, so the audit should be built from the canonical weekly metrics for the 26-week window — not a fresh raw pull. If the per-week canonical outputs are archived and cleanly consumable, that reduces or removes the need for Santi's raw export tasks. Verify the archive before assuming the raw pull is required.

## The flow

### Step 1: Resolve the client

Extract the client name. Check `clients/<slug>.json` for an existing config. If missing, copy `clients/_template.json` to `clients/<slug>.json`, set `client_slug` and `client_display_name`, continue.

If a `client-diagnostics/clients/<slug>.json` already exists, mirror its `notion.parent_page_id`, `platforms_in_scope`, and `data_quirks` fields. The cannibalization auditor and the diagnostic share the same client identity.

### Step 2: Confirm the audit window

Default window: **trailing 6 months** (26 weeks) from today. Confirm with the user before pulling — they may want to anchor to a specific event (e.g., "since Spice took over in November"). Use exact dates, not relative phrases.

If the window crosses a major structural event (new market launch, store closure, platform commission change), surface it. The counterfactual is honest only when the comp set is stable.

**Ask which channels carry paid spend.** Default scope is UE / DD / GH. Ask the operator: "Does this brand run paid spend anywhere besides Uber Eats, DoorDash, and Grubhub — SkipTheDishes, ezCater, a catering platform?" If yes and the spend is material, add that platform to `platforms_in_scope` in the client config and include it in the pull — the cannibalization number is only complete if it sees every paid channel on a location. The engine is platform-agnostic; a new platform just needs a `column_mappings` entry, no code change. If the extra channel is a rounding error, note it in the manifest and stay on the big three.

### Step 3: Create the Drive drop folder and hand over the data-collection checklist

Folder convention (mirror of client-diagnostics, separate path):

```
1. Active /
  └── <Client Display Name> /
       └── 4. Audits /
            └── <YYYY-MM-DD>-cannibalization /
                 └── inputs /
                      ├── ue /
                      ├── dd /
                      └── gh /
```

**3P-only.** No 1P / POS data is pulled — the audit's question is "did 3P spend produce incremental 3P sales?" and the comp set is other 3P locations.

Use the Drive `create_file` MCP. Create the folder chain, then post `references/data-collection-checklist.md` to the user — adapted to the client's platforms in scope (`data_quirks` in the config).

Lead the message with the Drive folder link. End with: "Once everything's in the folder, just say 'ready' and I'll validate and run."

### Step 4: Wait for the user's "ready" signal

Don't proceed until they confirm. Window pulls can take a GM 30–60 minutes.

### Step 5: Validate the inputs

When the user signals ready, list the Drive folder contents and run:

```bash
.venv/bin/python scripts/validate_inputs.py --inputs-dir <local-path-to-downloaded-inputs>
```

The validator checks: every required file present per platform in scope; every file has expected columns; the window covers ≥4 months continuous data (the floor — below this the counterfactual is unreliable and the tool refuses to run).

If validation fails, surface the exact missing files / columns. Offer to proceed degraded only when the missing data is non-foundational (e.g., no GH at all is fine; missing UE spend is not).

### Step 6: Build the unified per-location-per-week dataset

```bash
.venv/bin/python scripts/build_unified.py --client <slug> --inputs-dir <path> --output <path>/unified.csv
```

Produces a single CSV at `unified.csv`: one row per (location × week), with columns for spend, sales, orders, organic_sales, paid_sales, ROAS, net_payout, cancel_rate, menu_cvr, ratings_velocity, and platform breakdowns. See `references/input-csv-schema.md` for the full schema.

Drop the unified.csv into the Drive cycle folder next to `inputs/` so the source-data audit trail lives with the analysis.

### Step 7: Run the cannibalization analysis

```bash
.venv/bin/python scripts/analyze.py --client <slug> --unified <path>/unified.csv --output <path>/analysis.json
```

Five analytical passes, in order. Full logic in `references/analysis-framework.md`:

1. **Per-location metrics** — compute ROAS, payout %, marketing %, and ops health (cancel rate, menu CVR, ratings velocity) per location. Inputs to the routing decision, not labels.
2. **Spend event detection** — flag (location × week) pairs where spend changed materially (≥30% step change sustained ≥3 weeks, or start/stop events). Each = a natural experiment.
3. **Counterfactual baseline** — for each spend event, build expected sales using comp-store locations not running the same change + prior-year same-week + seasonal trend. Bayesian fit. Output: observed delta − expected delta = incremental sales. Spend / incremental = effective CAC.
4. **Mix shift detection** — track organic-vs-paid share of sales by location across the window. Rising organic → spend pullback candidate. Collapsing organic + holding sales → spend concentration candidate. Collapsing organic + collapsing sales → ops investigation candidate.
5. **Routing recommendation** — emit ONE action per location: CONCENTRATE / HOLD / PULL_BACK_TO_NC_ONLY / CUT / FIX_OPS_FIRST. Project the annualized dollar swing if the action is taken.
6. **Campaign moves (execution layer)** — map each action to concrete campaign tactics (audience targeting, ad products, offer structures), grounded in Spice's canonical segmentation playbook: New-led ~70/30 segmentation, new-to-brand vs new-to-location targeting, DD-runs-offers-straight (no creative tests), performance-gated growth spend. Turns "cut this location" into "here's exactly what to run there."

#### ⚠ Read `completeness_flags` BEFORE you render or share

The analysis output carries a `portfolio.completeness_flags` list. **Read it every run — do not ship the number if a flag is unresolved.** The one that will burn you:

- **SPEND SANITY (any location > 60% marketing)** — almost always means the spend is GROSS, i.e. platform ad credits / co-funded promos weren't netted out. Uber/DD/GH credit back a large share of ad spend; a gross figure roughly *doubles* spend and *halves* ROAS, which fabricates cannibalization that isn't there. If you see this flag, go back to the exports: use `Net Ad Spend` (not `Gross Ad Spend`), subtract `Ad Credits`, and exclude co-funded offer portions. Re-run. (This is exactly what went wrong on the first Sweetfin pass — 33% marketing and stores >100% collapsed to 22% and zero once credits were netted.) A location can legitimately exceed 60% — but you must *confirm* it's net before it ships, never assume.

Other flags (missing organic/paid split, no spend events, unreliable ROAS) qualify confidence rather than block — the deliverable should state them, not hide them.

#### Optional: `new_customer_spend_share` (new-led acquisition signal)

If you have a platform acquisition/audience signal showing what share of ad spend targets *new* customers (e.g. the UE Ads audience-segment export), set `new_customer_spend_share` in the client config (0–1). When it's ≥ 0.60, a location the saturation rule would pull back is HELD instead *if its ROAS clears ~2.5×* — because the spend is acquisition, not repeat-customer cannibalization, and first-window ROAS understates a customer who reorders. It only softens the soft saturation rule; it never overrides a measured counterfactual or the ≥50%-of-sales safety net. Leave it unset when you don't have the signal.

### Step 8: Render the deliverable

```bash
.venv/bin/python scripts/render_deliverable.py --client <slug> --analysis <path>/analysis.json --output <path>/deliverable.md
```

Produces a markdown file with the structure defined in `references/deliverable-template.md`:
- Page 1: exec summary — total $ cannibalized, projected net-payout lift annualized, recommended-action distribution
- Page 2: portfolio mix-shift chart (organic vs paid over the window)
- Pages 3–N: per-location card (recommended action, spend events used, projected dollar swing)
- Final page: methodology + caveats

Convert markdown to PDF using the existing Spice `pdf` skill. Upload to the cycle folder as `deliverable.pdf`.

### Step 9: Publish to Notion (optional)

If the user wants a Notion deliverable, mirror the client-diagnostics publish pattern: convert the markdown to Notion blocks, create the page under the client's wiki, embed the PDF as a bookmark.

For v0, the PDF in Drive is the canonical deliverable. Notion publish is a stretch.

### Step 10: Return the result

> ✅ Audit complete: `<drive pdf link>`
>
> **Recommended actions:** N CUT · N PULL BACK · N CONCENTRATE · N HOLD · N FIX OPS FIRST
> **Cannibalized spend (annualized):** $X
> **Projected net-payout lift if all recommendations adopted:** $Y annualized
> **Top move:** [the single biggest dollar swing recommendation]
>
> Source data + unified CSV: `<drive cycle folder>`

That's the entire flow.

## What to do when something goes wrong

| Situation | What you do |
|---|---|
| Client config missing | Create from template, mirror client-diagnostics config if present |
| Window crosses major structural event | Surface it. Offer to split the window or proceed with disclosure |
| Validator fails on missing columns | Show exact missing columns. Offer to proceed degraded only if non-foundational |
| <4 months of data | Refuse to run. Tell the user why — the counterfactual is unreliable below the floor |
| Spend events detected but counterfactual is wide (low confidence) | Suppress the per-location callout, surface in methodology page |
| Ops broken across most of the portfolio | Output the audit but lead the exec summary with "spend cannot fix this portfolio — fix ops first" |

## Anti-patterns

- **Don't recommend "spend more" when ops are broken.** The credibility move is the refusal. Cancel rate or menu CVR below threshold means spend funds the leak faster, not growth.
- **Don't conflate cannibalization with under-performance.** A low-ROAS location with broken ops is a fix-ops-first, not a cut — spending less won't fix a leaking funnel either, but cutting it loses the acquisition layer. Route to ops.
- **Don't fabricate a counterfactual when comp set is too small.** If the brand has 10 locations and 8 ran the same spend change, the natural-experiment math has no comp. Surface the gap; suppress those locations from the per-location callouts.
- **Don't roll up to "total waste %" without confidence intervals.** The number that ships externally must carry its uncertainty.
- **Don't run on <4 months of data.** The floor exists because seasonal trend dominates below it.

## Files in this skill

- `references/data-collection-checklist.md` — operator-facing pull list, per platform
- `references/analysis-framework.md` — routing rules + counterfactual methodology (canonical)
- `references/input-csv-schema.md` — unified per-location-per-week schema
- `references/deliverable-template.md` — output structure
- `scripts/validate_inputs.py` — folder + column validator
- `scripts/build_unified.py` — CSV normalizer
- `scripts/analyze.py` — five-pass analytical engine
- `scripts/render_deliverable.py` — markdown deliverable
- `clients/_template.json` — per-restaurant config template
- `clients/<slug>.json` — per-restaurant config (locations, column mappings, benchmark)

## Per-restaurant configuration

Each restaurant gets a `clients/<slug>.json` capturing its locations (with comp sets and markets), the platform column mappings for its exports, an optional `marketing_pct_benchmark` (defaults to 0.03), and an optional `new_customer_spend_share` (0–1; the share of ad spend aimed at new customers, from a platform acquisition/audience export — see Step 7). Nothing about the analysis is hardcoded to any particular restaurant — the config is the only restaurant-specific surface, and a new one is created from `_template.json` on first run.

**Note on the benchmark.** `marketing_pct_benchmark` (default 3%) is a heuristic that only anchors two soft rules (concentrate / saturation). It is deliberately *not* cited in client-facing rationales, and the hard calls — the ≥50%-of-sales safety net and the ROAS gate — don't depend on it. Treat 3% as a reference, not a verdict; set it per client when you have a defensible number.
