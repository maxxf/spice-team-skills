# Diagnostics — Orchestrator Redesign Spec

**Date:** 2026-05-08
**Status:** Design approved (Maxx + Ro), pending Santi sanity check
**Supersedes:** `client-diagnostics` v0.2 monolithic
**Authors:** Maxx (domain), Ro (architecture), Claude (eng)

---

## Context

The `client-diagnostics` skill v0.2 produces a strong dual-half Notion artifact, but the team is hitting **interpretation drift**: two GMs running the same client/data produce different conclusions, prioritize different stores, and write different action plans. (Ranked failure modes from Maxx, most → least painful: a > c > d > b — interpretation, structure, voice, then inputs.)

Root cause: the SKILL.md is robust as a guide, but it asks the GM to make too many judgment calls (Win/Risk/Opp selection, action-plan prioritization, prose authoring, cross-section synthesis). Standardization-by-prose is fragile. With ~17 active clients and growing GM/ops headcount, drift compounds.

This redesign:

1. **Decomposes** the monolith into an *orchestrator* + 5 domain *sub-skills* (Ro's call). Enables parallel dispatch, reusability (a sub-skill can be invoked standalone), and per-domain ownership.
2. **Introduces a two-layer pattern** within each sub-skill: *computed* (deterministic, GM cannot edit) vs *drafted* (prose, GM polishes inline like the scorecard's Signal callout). Standardization is enforced by the contract between layers, not by humans following text.
3. **Reframes action items as deliverable triggers** — every finding routes to a downstream productized skill (menu sheet, leaderboard, campaign plan, hero image, ratings flyer). The diagnostic becomes the ignition for the broader service graph.

---

## Architecture

```
client-diagnostics (orchestrator)
├── Phase 1: Pre-flight + data validation
├── Phase 2: PARALLEL sub-skill dispatch
│   ├── diagnostic-topline      → financials, momentum, platform breakdown
│   ├── diagnostic-menu         → storefront visual, conversion funnel, SKUs, photo coverage
│   ├── diagnostic-ops          → uptime, errors, cancellations, ratings, downtime
│   └── diagnostic-campaigns    → promos, ads, ROAS, daypart
├── Phase 3: Cross-cutting computation (orchestrator-level)
│   ├── 7-dim radar (assembled from sub-skill radar_contributions)
│   ├── Location tier rollup (assembled from sub-skill tier_contributions)
│   ├── Foundation gate decision (rating, error, uptime, CVR, photos)
│   └── Win/Risk/Opp top-3 selection (ranked across all sub-skill candidates by impact_usd)
├── Phase 4: SEQUENTIAL action plan
│   └── diagnostic-action-plan → consumes all 4 sub-skill outputs + cross-cutting,
│                                produces kanban + deliverable triggers
└── Phase 5: Notion page assembly
    ├── Half 1 dashboard (hero strip, radar, kanban, win/risk/opp, tier donut, trend, daypart)
    ├── Half 2 toggles (one per sub-skill, populated from `drafted.toggle_prose`)
    └── Client-facing email draft
```

---

## Decisions

### Decision 1 — Sub-skill output contract

Every sub-skill writes a single JSON file `OUTPUT/<sub-skill>_results.json` matching this schema. The contract is the standardization mechanism — orchestrator stitches deterministically, sub-skills are independently testable.

```json
{
  "sub_skill": "diagnostic-menu",
  "version": "1.0",
  "client": "<client-slug>",
  "window": { "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" },
  "computed": {
    "metrics": { /* domain-specific block */ },
    "radar_contributions": { "<dim_name>": <1-10 float>, ... },
    "tier_contributions": {
      "<store_name>": {
        "score": <1-10 float>,
        "flag": "green|yellow|red|new",
        "reasons": ["<why this score>"]
      }
    },
    "findings": [
      {
        "pattern_id": "<id from this sub-skill's pattern library>",
        "severity": "low|medium|high|foundation",
        "scope": "portfolio|<comma_separated_store_names>",
        "evidence": { /* data citations */ },
        "estimated_impact_usd": <number|null>,
        "deliverable_trigger": {
          "skill": "<spice-skill-slug>",
          "params": { /* skill-specific input params */ }
        }
      }
    ],
    "charts": [ { "id": "<chart_id>", "path": "OUTPUT/<file>.png" } ]
  },
  "drafted": {
    "toggle_title": "<Half 2 toggle name>",
    "toggle_prose": "<LLM-drafted markdown for the toggle body>",
    "win_risk_opp_candidates": [
      { "type": "win|risk|opportunity", "headline": "<text>", "value_usd": <number|null> }
    ]
  },
  "data_quality": {
    "completeness": <0.0-1.0>,
    "gaps": [ "<gap description>" ]
  }
}
```

**Why this shape:** orchestrator stitching is deterministic; sub-skill is callable standalone (it can ship just its toggle if invoked alone); action-plan sub-skill consumes structured `findings[]` (not prose); the `deliverable_trigger` block is what makes action-as-router work.

### Decision 2 — Pattern library ownership

Each sub-skill owns its slice. The current `references/diagnostic-framework.md` splits:

| Sub-skill | Pattern library file |
|---|---|
| `diagnostic-topline` | `references/patterns-topline.md` |
| `diagnostic-menu` | `references/patterns-menu.md` |
| `diagnostic-ops` | `references/patterns-ops.md` |
| `diagnostic-campaigns` | `references/patterns-campaigns.md` |
| `client-diagnostics` (orchestrator) | `references/cross-cutting-patterns.md` (only patterns spanning 2+ domains, e.g. *"high traffic + low conversion + ratings strong = pricing problem, not menu problem"*) |

**Why:** per-domain ownership maps to per-domain expertise. Cross-cutting patterns are rare; they belong with the orchestrator.

When the split happens, every cross-domain reference in the original framework gets preserved as an explicit "See also: `<sub-skill>/patterns-X.md#<anchor>`" link — prose chains across domains today and we don't lose that by mechanical split.

The radar dimension scoring rubric, cuisine CVR benchmarks, and chart spec library also redistribute:
- Radar rubric per dim → owned by the sub-skill that produces that dim's contribution (see Contracts §"Radar dim ownership")
- Cuisine CVR benchmarks → `diagnostic-menu/references/`
- **Domain charts** (per-sub-skill: `funnel_ue.png`, `top_skus_bar.png`, `campaign_2x2.png`, etc.) — owned by the relevant sub-skill
- **Cross-cutting charts** (`radar_7dim.png`, `tier_donut.png`, `sparklines_gmv_orders.png`, `daypart_heatmap.png`, `top15_green_bar.png`) — owned by orchestrator, generated in Phase 3 from sub-skill outputs
- A shared `chart_helpers.py` module lives at orchestrator level providing matplotlib primitives; both orchestrator and sub-skills import from it

### Decision 3 — Foundation gate location

**Lives at the orchestrator. Runs in Phase 3** (after parallel sub-skill dispatch, before action-plan sub-skill).

Inputs come from multiple sub-skills (rating from ops, CVR from menu, photo coverage from menu, error rate from ops, uptime from ops). Only the orchestrator has them all.

If gate triggers:
- Orchestrator records `foundation_gate.triggered = true` in shared run state
- `diagnostic-action-plan` consumes the triggered state and produces a foundation-only action plan (no campaigns, no promos, no spend until fixed) — the existing v0.2 logic, just relocated
- Half 1 dashboard renders a banner above the hero strip flagging the gate

```json
{
  "triggered": true,
  "triggers": [
    { "metric": "rating", "value": 4.0, "threshold": 4.2, "scope": "store_3,store_7" }
  ],
  "override_action_plan": true
}
```

**Fail-conservative rule:** If any sub-skill that owns a foundation-gate input (`diagnostic-ops` for rating/error/uptime, `diagnostic-menu` for CVR/photos) failed in Phase 2, the orchestrator must treat the gate as *triggered* and surface a banner explaining the gate fired due to missing data. Better to over-trigger and have the GM clear it manually than miss a foundation issue silently.

---

## Contracts

Implementation-level contracts that the Decisions assume. The implementer should treat these as binding.

### Run-state + output layout

A single canonical layout per run:

```
/tmp/diagnostic-runs/<client-slug>/<run-timestamp-ISO>/
├── run_state.json                   # orchestrator-owned, source of truth for cross-phase state
├── inputs/                          # raw exports collected in Phase 1
├── topline/
│   ├── diagnostic-topline_results.json
│   └── charts/                      # sub-skill writes only inside its own dir
├── menu/
│   ├── diagnostic-menu_results.json
│   └── charts/
├── ops/
│   ├── diagnostic-ops_results.json
│   └── charts/
├── campaigns/
│   ├── diagnostic-campaigns_results.json
│   └── charts/
├── cross_cutting/                   # orchestrator-owned: radar, tier_donut, sparklines, daypart, top15
│   └── *.png
└── action-plan/
    └── diagnostic-action-plan_results.json
```

**Each sub-skill writes only inside its own subdirectory.** Eliminates `funnel_*.png` collisions. Orchestrator owns `run_state.json` and `cross_cutting/`. Atomic-write all JSON via temp-file + rename.

`run_state.json` schema (orchestrator-only writer; sub-skills read via Phase-3 handoff, not concurrently):

```json
{
  "run_id": "<client-slug>-<ISO-timestamp>",
  "phase": "1|2|3|4|5",
  "sub_skill_status": {
    "diagnostic-topline": "pending|running|ok|failed",
    "diagnostic-menu":    "pending|running|ok|failed",
    "diagnostic-ops":     "pending|running|ok|failed",
    "diagnostic-campaigns": "pending|running|ok|failed"
  },
  "foundation_gate": { /* see Decision 3 */ },
  "prior_run_id": "<run_id of last successful run for this client>|null"
}
```

### Radar dim → sub-skill ownership

The 7 radar dims map to a single primary owner each. Composite dims (Marketing Efficiency, Operations) require multi-input math the orchestrator performs in Phase 3.

| Radar dim | Owner | Notes |
|---|---|---|
| 1. AOV | topline | direct |
| 2. Re-order Rate | topline | direct (it's a portfolio-level financial measure) |
| 3. Conversion (UE menu CVR) | menu | direct |
| 4. Marketing Efficiency | **orchestrator (composite)** | inputs: `topline.metrics.gross_sales` + `campaigns.metrics.total_marketing_investment` |
| 5. Operations | **orchestrator (composite)** | inputs: `ops.tier_contributions[*].flag` (pct of stores not flagged) |
| 6. Traffic | menu | storefront → menu CTR |
| 7. Campaigns / ROAS | campaigns | direct (blended) |

Sub-skills emit only their primary-owned dims in `radar_contributions`. Orchestrator computes composite dims in Phase 3.

### Location tier rollup

Each store appears in `tier_contributions` of menu, ops, and campaigns sub-skills (one score per bucket). Orchestrator merges in Phase 3 using the existing v0.2 rollup rule (relocated from `references/diagnostic-framework.md` §"Location Tier Strategy" → `references/cross-cutting-patterns.md`):

- 🔴 Red rollup if any bucket = red
- 🟡 Yellow rollup if any bucket = yellow and none = red
- 🟢 Green rollup if all buckets = green
- 🆕 New rollup if store has < 30d data in any bucket

Orchestrator writes the rollup into `run_state.json` and the kanban consumes it.

### "What Moved Since Last Cycle" persistence

Each completed run writes `run_state.json` to a per-client archive: `/tmp/diagnostic-runs/<client-slug>/_archive/<run_id>.json` (and same to a Notion property block on the diagnostic page for durable storage beyond `/tmp` cleanup).

Phase 5 reads the most recent archive predating this run, computes deltas (Re-order Rate Δ, Error Rate Δ, Blended ROAS Δ), and renders the panel. If no prior archive exists, panel reads "first cycle — baseline established."

### Win/Risk/Opp dedup + tiebreak

Phase 3 collects `win_risk_opp_candidates` from all sub-skills. Selection rules:
- **Dedup:** if two candidates share the same `pattern_id` (cross-domain finding surfaced by two sub-skills), keep the one with higher `value_usd`; if both null, keep the one with higher `severity`; if both equal, prefer the sub-skill in this priority order: ops > menu > campaigns > topline (operations issues outrank revenue framings).
- **Top-3 rank:** sort by `value_usd` desc; nulls sort last; tiebreak by `severity` (foundation > high > medium > low) then by sub-skill priority above.
- Always include at least one of each type if candidates exist (one win, one risk, one opp). If a type has zero candidates, render the slot empty with a "no signal this cycle" hint.

### Deliverable trigger versioning

Each downstream deliverable skill the orchestrator wires up declares its expected input params in a `deliverable_contract.json` at its skill root (e.g., `/Users/maxx/Desktop/Cowork/Skills/optimized-menu-sheet/deliverable_contract.json`). The action-plan sub-skill validates `deliverable_trigger.params` against the contract before emitting; mismatch → emit a Notion task instead of a trigger and flag in `data_quality.gaps`.

Contracts get committed alongside their owning skill, so a deliverable skill version-bumping its inputs is detected at validation time, not runtime.

---

## Build Sequence

| Phase | Build | Why |
|---|---|---|
| **Wk 1 (this week)** | Orchestrator skeleton + `diagnostic-topline` sub-skill + **stub `diagnostic-action-plan`** that consumes one finding | Real end-to-end requires at least one consumer of the contract. Stub action-plan validates the producer→consumer round-trip. Recommend dry-run against goop Kitchen — full data exists. |
| **Wk 2** | `diagnostic-menu`, `diagnostic-ops`, `diagnostic-campaigns` (parallel build, one per session) | Independent — can be built in any order or concurrently |
| **Wk 2–3** | Promote `diagnostic-action-plan` from stub to full skill | Consumes findings from all 4 sub-skills + cross-cutting state |
| **Wk 3** | End-to-end smoke test on a 2nd client; tune | Catches integration gaps |
| **Wk 3–4** | Wire `deliverable_trigger` invocations | **v1 mechanism:** kanban card carries the `deliverable_trigger` JSON in a Notion property block; GM copy-pastes it into a Claude session that fires the named skill. **v2 (later):** polling worker watches Notion for "Trigger" property changes and dispatches via the Spice MCP server. Not free — real work, not wire-up. Contract-test against each downstream skill's `deliverable_contract.json` before declaring done. |

---

## Out of Scope

- Building or modifying the 5 deliverable skills (`optimized-menu-sheet`, `leaderboard-update`, campaign-plan, `hero-image-review`, `ratings-flyer`). Wire-up only.
- Changing the visual structure of the Notion page (Half 1/Half 2). Same look, new pipeline underneath.
- Migrating active clients off v0.2 onto the new pipeline — phased rollout, separate plan after build complete.
- Cowork live artifact for diagnostic exploration — future work, not v1.

---

## Open Questions (with proposed defaults)

1. **Sub-skill failure handling** — **Default: fail-open** for any sub-skill OTHER than ops/menu (whose outputs feed the foundation gate). Failed section renders as *"section unavailable due to data gap — see data quality footer"* toggle. Ops or menu failure → fail-conservative on the foundation gate (assume triggered). Hard fail only if Phase 1 pre-flight fails.
2. **Backwards compatibility with v0.2 outputs?** Default: not required. Once v1 ships, v0.2 is deprecated. Phased migration per client (active engagements stay on v0.2 mid-cycle; new diagnostics use v1; cutover at next 90-day reset).
3. **Idempotency / re-runs** — Same client run twice in a day: orchestrator versions by `<run-timestamp>` (never overwrites). "What Moved" panel uses the most recent prior-day archive, not prior-hour, to avoid noise.
4. **Sub-skill schema version skew** — Schema version is at the top of the contract (`"version": "1.0"`). Orchestrator pins compatible major version; minor bumps are additive-only. If a sub-skill emits a major version the orchestrator doesn't support, fail-open with explicit "schema mismatch" gap.
5. **Cost / token budget of parallel dispatch** — 4 sub-skills × LLM-drafted prose ≈ 4× single-pass cost. Per-run budget cap stored in orchestrator config; default $1.50/run; alert if exceeded. Sub-skill prose can be opted out via `--no-prose` flag for dev runs (computed-only output).
6. **PII / client-data on shared `/tmp`** — Single-machine assumption (Mac Mini or per-GM laptop). If multi-tenant deployment becomes real, `/tmp/diagnostic-runs/` gets a per-user prefix and `_archive` moves to encrypted client-storage. Documented as a deployment-time concern, not a v1 build concern.
7. **In-flight v0.2 migration risk** — Active engagements mid-90-day cycle should NOT switch pipelines. Risk: GMs ship a half-v0.2/half-v1 diagnostic and outputs diverge by section. Mitigation: cutover gate in `client-onboarding` skill — only NEW engagements use v1 until v0.2 is fully retired.

---

## Verification

- End-to-end run on goop Kitchen produces a Notion page that visually matches today's v0.2 output (same Half 1 / Half 2 structure, same charts, same kanban shape).
- Same data, two different sessions/machines, produces a **stable computed-layer hash**. Hash scope: `computed.metrics`, `computed.radar_contributions`, `computed.tier_contributions`, and `computed.findings[].pattern_id|severity|scope|estimated_impact_usd`. **Excluded from hash:** `charts[].path` (contains run-timestamp), `findings[].evidence` (may contain run IDs), `drafted.*` (prose is non-deterministic by design), `data_quality` (run-state dependent).
- Action items in the kanban each carry a `deliverable_trigger`; manual trigger of one fires the downstream skill correctly with the right params and passes the `deliverable_contract.json` validation.
- Foundation-gate triggered on a deliberately-low-rating test client overrides the action plan to foundation-only and renders the banner.
- Foundation-gate triggered on a *missing* ops sub-skill output (simulate ops failure) triggers the conservative-fail rule and renders the gate banner with "due to data gap" reason.

---

## Critical Files

- `/Users/maxx/Desktop/Cowork/Skills/client-diagnostics/SKILL.md` — current v0.2 (becomes orchestrator)
- `/Users/maxx/Desktop/Cowork/Skills/client-diagnostics/references/diagnostic-framework.md` — current pattern library (gets split)
- `/Users/maxx/Desktop/Cowork/Skills/client-diagnostics/references/generate_diagnostic_charts.py` — chart helpers (refactored as shared module)
- New sub-skill folders to be created at `Cowork/Skills/diagnostic-{topline,menu,ops,campaigns,action-plan}/`
