# Campaign-Plan Strategy & Roadmap Mode — Design Spec

**Date:** 2026-06-11 · **Owner:** Maxx · **Status:** Approved design, pending implementation plan
**Skill:** `campaign-plan` (dev: `/Users/maxx/Desktop/Cowork/Skills/campaign-plan/`, deployed: `spice-team-skills/skills/campaign-plan/`)

## Problem

The campaign-plan Sheet has Q2/Q3/Q4 Plan tabs (tabs 5–7) that are protected and human-authored — in practice they sit empty. There is no productized way to (a) tier locations correctly, (b) decide per-tier spend + campaign strategy, or (c) plot a forward roadmap. Tiering today is whatever the diagnostic last said, with no performance overlay, no goal lens, and no approval step. The strategy that does exist lives in GMs' heads.

## Goal

An interactive strategy session inside the campaign-plan skill that:
1. Walks the user through location tier groupings based on performance + diagnostics and **gets explicit approval**.
2. Recommends per-tier strategy: spend %, campaign types, segmentation — each citing the playbook rule it applies.
3. Captures upcoming events (launches, holidays, LTOs) by asking the right questions.
4. Drafts a rolling ~90-day roadmap, requests feedback, revises until approved.
5. On approval, produces a **client-shareable Notion strategy page (by tier)** and **fills the Sheet's Q-plan roadmap tabs**.

## Entry point: the 3-way router

When the skill triggers, resolve to one of three modes. Route directly when the trigger is explicit; otherwise ask the user to pick.

| Mode | What it does | Writes | Example triggers |
|---|---|---|---|
| **Update reporting sheet** | Existing automated weekly refresh (exports → Dashboard/Ads/Offers/History) | Sheet (reporting tabs) | "refresh campaign plan", "update campaign tracker" |
| **Plan campaigns** | This spec — interactive tier → strategy → events → roadmap session | Notion strategy page · Q-plan tabs · Notion DB rows (`Not started`) · client config | "plan strategy for goop", "build the roadmap", "tier strategy" |
| **Run analysis** | Read-only Q&A over the live sheet + History (declines, incrementality, what's working). Answers in chat, writes nothing. | none | "analyze goop", "why did X drop" |

**Run analysis scope (complete definition — no new machinery):** the mode is purely conversational. It calls `strategy_read.py` (the same merged per-location read the strategy session uses) plus existing History reads, then Claude answers the question in chat, citing playbook rules where relevant. No dedicated script, no writes, no artifacts. If the user asks for something that requires writing (a findings doc, a tier change), Claude offers to switch modes. That is the entire mode; nothing about it is deferred.

## The tier framework (canonical rubric — decided 2026-06-11)

Tier is **not** a ROAS ranking. It's an overlay of axes, and spend runs *inverse* to capacity/efficiency. The organizing lens is the per-location **goal**.

### Per-location inputs (the overlay)

| Axis | Source | Mode |
|---|---|---|
| **Goal** — top-line sales growth vs incremental payout | Proposed from capacity + tier signals; GM/client confirms | Confirm at gate, persisted |
| Ops health (ratings, fulfillment, errors, uptime) | Latest diagnostic / leaderboard | Auto |
| Menu strength (conversion) | Diagnostic | Auto |
| Campaign efficiency (ROAS, spend % of sales) | Live campaign Sheet (Dashboard By Location) | Auto |
| Capacity (at capacity / room to grow / needs base) | Diagnostic + GM confirm | Auto-propose, confirm |
| Re-order rate | **GM captures manually from platforms** | Prompted, persisted with capture date, re-confirmed each session |

### The 5 tiers

| Tier | Profile | Default goal | Spend (% of location sales) | Strategy posture |
|---|---|---|---|---|
| **Top** | Great ops, at capacity, >6x ROAS | Incremental payout | **0–3%** | Protect efficiency: retention/loyalty lean; stepped-pullback tests to prove incrementality; new-cust only if re-order high |
| **Mid** | OK ops, room to grow, 4–6x | **Either — explicit call required** | **4–8%** | Growth-goal: acquisition toward top of band. Payout-goal: hold spend, shift mix to efficiency |
| **Low** | Weak-but-fixable ops, <4x, needs to grow | Top-line growth | **8–15%** | Acquisition-led base building paired with ops/menu fix workstream; lower ROAS accepted knowingly |
| **New** | Brand new | Top-line growth | **15–20% for 4–8 wks, then taper** | Awareness + acquisition-heavy; re-diagnose at 60d |
| **Red** | Ops/menu broken | Fix first | **0% — hold** | No spend until Cardinal Rule gate passes (rating ≥4.5, error <2%, uptime >95%, menu conv ≥20%, photos) |

### Re-order rate logic

- **High re-order** → new customers stick → justify acquisition at the top of the tier's band; tilt New/Existing/Lapsed split toward **New**.
- **Low re-order** → acquisition leaks → tilt toward retention/reactivation; fix retention before scaling acquisition.

### Goal logic

The same metrics read differently per goal: 5x ROAS at 7% spend is fine for a growth store, a problem for a payout store. Mid tier is where the growth-vs-harvest call is a genuine client conversation — the gate forces it explicit.

## Plan-campaigns flow (gated, conversational)

Claude drives the conversation. Python does only deterministic I/O: `strategy_read.py` (read) and `strategy_write.py` (write).

### 1. Read

Assemble per-location data:
1. **Saved tier recs** — `tier_strategy` block in `clients/<slug>.json` from the last session (tiers, goals, re-order rates + capture dates, per-tier strategy params). Seeds the session so the user isn't re-litigating groupings each quarter.
2. **Original diagnostic tiers** — existing `net_sales_pull.pull_tier_map` (By Tier tab) + diagnostic ops/menu/capacity signals where available.
3. **Performance overlay** — per-location ROAS, spend %, mktg-driven %, sales from the live Sheet.

Merge rule: saved recs if present, else diagnostic; overlay performance; **flag any location whose current performance disagrees with its tier**, with the reason (e.g. "diagnostic had it Yellow, but 8.3x ROAS at 4% spend for 3 wks → propose Top").

**Tier vocabulary mapping.** The diagnostic speaks Green/Yellow/Red; this rubric speaks Top/Mid/Low/New/Red. Color tiers only *inform the proposal* — the scorecard always proposes in the 5-tier vocabulary, seeded as:

| Diagnostic | Seeds to | Disambiguator |
|---|---|---|
| Green | Top or Mid | >6x ROAS **and** at capacity → Top; else Mid |
| Yellow | Mid or Low | ≥4x ROAS → Mid; <4x → Low |
| Red | Red | — |
| (any) location open <8 weeks | New | age wins over color |

Location age comes from an `opened` date in the config's `tier_strategy.locations` entry when present; otherwise Claude asks the GM at the gate for any location that looks new (in performance data but not the diagnostic, or flagged by the GM) and saves the date.

Saved `tier_strategy` recs are already 5-tier and need no mapping. If the user adjusts in color terms at the gate ("keep Pico Yellow"), Claude maps it via the table and confirms the interpretation ("Yellow at 5.1x → keeping Pico **Mid**").

### 2. Tier gate (approval #1)

Present a per-location scorecard:

`Location · Goal (proposed → confirm) · ROAS · Spend% · Menu conv · Ops · Capacity · Re-order (saved → confirm) → Proposed tier · Why`

- Movers flagged with reasons.
- Prompt for missing/stale re-order rates (GM enters; saved with date).
- User approves or adjusts ("keep Pico Yellow"). Nothing downstream runs before sign-off.
- On approval: write tiers + goals + re-order rates back to `clients/<slug>.json`.

### 3. Per-tier strategy (approval #2)

For each approved tier, recommend a strategy block, every line citing its playbook rule:
- **Spend** — default % of tier sales per the rubric bands; 55/45 acquisition/retention baseline adjusted by re-order logic; suggested $ computed from current sales. If user supplies a budget envelope, allocate that instead and show both.
- **Campaign types** — location-based only (never keyword); matched to tier + goal (Top: loyalty/retention + pullback tests · Mid: per goal · Low: acquisition offers + fix workstream · New: awareness + flyer play · Red: none).
- **Segmentation** — New/Existing/Lapsed mix per tier, re-order-adjusted.
- **Cadence/exit** — decay rule: creative refresh by wk 4–5, spend-down schedule planned at entry.

User approves/edits per tier. Approved params persist to config.

### 4. Events

Claude asks targeted questions: NROs/launches + dates, LTOs/menu drops, client moments, blackout weeks. US holidays in the window are pre-filled for confirm/add.

### 5. Roadmap (approval #3)

Rolling **~90 days** (≈13 weeks from today; spans quarter boundaries). Draft a per-location weekly grid grouped by tier — rows = locations under tier headers; columns = weeks; cells = planned mechanic (e.g. "S$30-S$5 New"); events band across the top. Iterate in chat until approved.

### 6. Write (on final approval)

1. **Notion strategy page** (client-shareable, in client's Notion space): "why this quarter" summary → one section per tier (posture, goal, locations, spend %/$, campaign types, segmentation, key plays) → roadmap-at-a-glance. Idempotent: update existing page if present (page id cached in config). **First-run parent resolution:** client configs carry no Notion parent today; on first run Claude resolves the client's Documents Hub via Notion search, confirms the destination with the user, then caches both `notion_parent_page_id` and the created `notion_strategy_page_id` in config.
2. **Sheet Q-plan tabs**: write the grid into whichever Q-plan tab(s) the 90-day window spans. This mode is the **authorized writer** for Q-plan tabs; the weekly refresh continues to never touch them.

   **How write authority is granted (the guard stays):** `sheets_writer.assert_safe_to_write` currently blocks every primitive on tabs matching `PROTECTED_TAB_SUBSTRINGS` (which includes "plan") — a deliberate invariant so the refresh can never clobber forward calendars. We do NOT narrow the protected list. Instead, the write primitives gain an explicit `allow_protected: bool = False` opt-in parameter that `strategy_write.py` alone passes; `refresh.py` and every existing call site remain default-False, so the refresh physically cannot write these tabs even by future accident. Tab creation for a missing Q-plan tab uses the same opt-in.

   **Existing human content:** GMs may have hand-authored content in these tabs. Before writing, `strategy_write.py` reads the target range; if it's non-empty, the conversation shows what's there vs what will replace it and requires an explicit confirm before the write — same philosophy as the other gates. An empty tab writes without ceremony.

   **Grid format (canonical, pinned — v2 platform lanes, 2026-06-12):** Row 1 title (`Q3 2026 Plan — <Client>`); row 2 events band; row 3 column headers: `Tier · Location · Platform · W<ISO> <Mon date>` × the weeks in this tab's quarter; then **one lane per location × platform** (DD/UE/GH, only platforms the location runs), grouped under emoji-coded tier section rows (🟢 Top → 🔵 Mid → 🟠 Low → 🟣 New → 🔴 Red), cells = that platform's mechanic shorthand. Visual coding by the writer: per-tier soft row tints (TIER_META) + brand-colored bold platform labels (DD red / UE green / GH orange). Weeks outside this tab's quarter belong to the adjacent Q-plan tab.
3. **Notion Campaign Planning DB**: each planned campaign row lands via the existing `add_campaign.py` (verified compatible: it writes name/type/channels/locations/segment/status/dates/ROAS-target). The DB has no "Proposed" status — rows enter as **`Not started`** with a `Roadmap <window>` tag via `--notes` (which maps to the Notion property **"Performance Notes"** — dual-used here alongside its playbook-precedent purpose) so campaign-ops picks them up with no double-entry.
4. **Config**: `tier_strategy` block updated (tiers, goals, re-order + dates, per-tier params, roadmap version + date).

## Persistence schema (`clients/<slug>.json`)

```json
"tier_strategy": {
  "updated": "2026-06-11",
  "locations": {
    "Venice": {"tier": "Top", "goal": "payout", "reorder_rate": 0.42, "reorder_captured": "2026-06-11", "opened": "2024-11-03", "overrides": "kept Top despite spend% spike — NRO halo"}
  },
  "tiers": {
    "Top": {"spend_pct": [0, 3], "acq_retention": "30/70", "notes": "..."}
  },
  "notion_parent_page_id": "...",
  "notion_strategy_page_id": "...",
  "roadmap": {"window_start": "2026-06-15", "window_end": "2026-09-13"}
}
```

## Edge cases

- **No diagnostic** → derive proposal from performance only; say so; lean harder on GM confirmation.
- **New client / no history** → diagnostic + playbook defaults; more questions, no flagged movers.
- **Location mismatch** (in diagnostic, not in perf data, or vice versa) → surface unmatched list, ask, don't guess.
- **Envelope vs %-of-sales conflict** → reconcile, show both, user picks.
- **Q-plan tab missing** (e.g. window reaches next year's Q1) → create the tab with the canonical grid format.
- **Re-order rate stale (>1 quarter)** → flag at gate, request refresh, proceed with stale value only on explicit OK.

## Brand-agnostic requirement (binding)

This mode must work for **any client** with zero code changes — goop is only the first verification instance. Concretely:

- **No client names, location names, or brand assumptions in code or SKILL.md logic.** Client examples in docs are illustrative only.
- **All client identity flows from `clients/<slug>.json`**: sheet ids, location aliases, tier_strategy block, Notion page ids, reporting day. A new client = a new config file, nothing else.
- **The tier rubric's spend bands are canonical defaults, per-client overridable**: the bands (0–3 / 4–8 / 8–15 / 15–20 / hold) seed every client; an approved session may persist adjusted bands in `tier_strategy.tiers` for that client only. The rubric doc states the defaults; config states the client's reality.
- **Events machinery is generic**: US holidays computed from the window; everything brand-specific (NROs, LTOs, client moments) enters via the session Q&A, never from code.
- **Degrade gracefully on missing surfaces**: no diagnostic, no By-Tier tab, no saved config block — the session still runs (per Edge cases), so brand-new clients on day one are first-class.

## Non-goals

- No auto-send of anything client-facing; the Notion page is shared by the GM.
- No campaign execution (stays with campaign-ops).
- No profitability/payout reporting (stays with weekly reporting).
- The weekly refresh remains fully non-interactive and never touches Q-plan tabs.

## Components

| Unit | Purpose | Depends on |
|---|---|---|
| SKILL.md router section | 3-way mode routing + Plan-campaigns conversational script (gates, rubric, questions) | — |
| `references/strategy_read.py` | Pull + merge config/diagnostic/performance into one per-location JSON for the session | `net_sales_pull`, Sheets API, client config |
| `references/strategy_write.py` | Write Q-plan tab grid(s); update config; (Notion writes go through Notion MCP from the conversation, not Python) | `sheets_writer` primitives, client config |
| `references/tier-framework.md` | The canonical rubric as a reference doc (the table above) | — |

Claude (the conversation) owns: proposing tiers/goals, strategy authorship, events Q&A, roadmap drafting, Notion page creation via MCP. Python owns: reads and sheet/config writes. Notion DB rows go through the existing `add_campaign.py` (compatibility verified above).

### Interfaces (so each unit is testable without reading internals)

`strategy_read.py --client <slug>` → one JSON to stdout:

```json
{
  "client": "goop-kitchen",
  "asof": "2026-06-11",
  "locations": [
    {"location": "Venice",
     "saved": {"tier": "Top", "goal": "payout", "reorder_rate": 0.42, "reorder_captured": "2026-03-02"},
     "diagnostic": {"color": "Green", "menu_conv": 0.27, "ops": {"rating": 4.7, "fulfillment": 0.99}, "capacity": "at"},
     "performance": {"roas": 7.2, "spend_pct": 2.1, "mkt_driven_pct": 0.31, "sales": 48210},
     "flags": ["reorder_stale"]}
  ],
  "unmatched": {"diagnostic_only": [], "performance_only": ["Berkeley"]}
}
```

`strategy_write.py --client <slug> --grid <json>` ← grid JSON:

```json
{
  "window": {"start": "2026-06-15", "end": "2026-09-13"},
  "events": [{"week": "2026-06-29", "label": "July 4"}, {"week": "2026-07-13", "label": "Berkeley NRO"}],
  "rows": [
    {"tier": "Mid", "location": "Pasadena",
     "cells": {"2026-06-15": "S$45-S$10 All", "2026-06-22": "—"}}
  ]
}
```

It splits the window across Q-plan tabs by quarter, writes each (with the `allow_protected` opt-in), and updates `tier_strategy` in config from a `--config <json>` payload.

**Non-empty-tab confirm flow (two-call protocol):** `strategy_write.py --check` is a dry run — it returns each target tab's existing content (or `empty`) and writes nothing. Claude shows any non-empty content vs the replacement and gets the user's confirm in chat, then calls again with `--overwrite` to execute. Without `--overwrite`, the script refuses to write a non-empty Q-plan tab. Empty tabs write on the first (non-check) call.

## Verification

- Run "plan strategy for goop": session seeds from diagnostic tiers, flags at least the known movers, gates hold until approval.
- Approved tiers/goals/re-order persist; a second run seeds from them and only asks "still current?".
- Q-plan tabs contain the approved grid; weekly refresh run afterward leaves them untouched.
- Notion strategy page exists, reads client-clean, sections per tier with spend bands + goals.
- Planning DB shows the roadmap's campaigns as `Not started` with a `Roadmap <window>` Notes tag.
