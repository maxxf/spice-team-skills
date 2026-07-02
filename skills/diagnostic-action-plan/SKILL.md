---
name: diagnostic-action-plan
description: >
  Sub-skill of client-diagnostics. Builds a tier-aware action plan grouped by
  location tier (Red/Yellow/Green/New) using the cross-cutting tier rollup as
  the primary axis. Each tier group ships with default-strategy auto-actions
  per the diagnostic framework, plus finding-driven actions routed to their
  target store's tier group. Foundation gate downgrades scaling actions to HOLD.
  Backward-compat: if called without tier_rollup, falls back to v0.1 severity
  kanban (P1/P2/P3).
version: 0.2.1
---

# Diagnostic — Action Plan

v0.2 promotes the v0.1 stub to a tier-aware action plan. Tier groups are the
primary organizing axis; severity within a tier is captured by the finding
itself.

## Inputs

- `findings`: list of finding dicts (orchestrator collates from sub-skills).
  Each has at minimum `pattern_id`, `severity`, `scope`, `deliverable_trigger`.
- `foundation_triggered`: bool from orchestrator's foundation gate.
- `tier_rollup` (optional): `{store: {flag, worst_bucket, per_bucket_flags}}`
  from `cross_cutting.rollup_tiers`. When None, falls back to v0.1 stub.

## Output (tier-aware mode)

```json
{
  "version": "0.2-tier-aware",
  "foundation_gate_triggered": false,
  "tier_groups": {
    "red":    { "stores": [...], "default_strategy": "...", "auto_actions": [...], "finding_actions": [...] },
    "yellow": { "stores": [...], "default_strategy": "...", "auto_actions": [...], "finding_actions": [...] },
    "green":  { "stores": [...], "default_strategy": "...", "auto_actions": [...], "finding_actions": [...] },
    "new":    { "stores": [...], "default_strategy": "...", "auto_actions": [...], "finding_actions": [...] }
  },
  "portfolio_actions": [...],
  "deliverable_triggers": [...]
}
```

All four tier groups are always present, even when their `stores` list is
empty. Findings with `scope="portfolio"` route to top-level
`portfolio_actions`. Findings spanning multiple stores in different tiers
land in the worst tier (Red > Yellow > New > Green). Findings whose scope
references a store missing from `tier_rollup` are placed in
`portfolio_actions` with `unmapped_store_scope: true`.

## Auto-action rules (per framework)

| Tier   | Auto-actions emitted |
|--------|----------------------|
| Red    | (1) Pause all campaigns at <red stores> until <worst buckets> fixed; (2) per store, "Fix <worst_bucket> at <store>" |
| Yellow | (1) Per store, "Targeted fix at <store> — weak bucket: <worst_bucket>"; (2) portfolio "Hold spend at <yellow stores>" |
| Green  | (1) "Increase ad budget +20% at <green stores>" with `campaign-plan` trigger (focus=scale); (2) "Feature <green stores> in marketing" |
| New    | (1) Per store, "Continue awareness investment at <store>" with `campaign-plan` trigger (focus=awareness); (2) portfolio "Schedule diagnostic re-run on day-60" |

## Foundation-gate behavior

When `foundation_triggered=True`:
- `foundation_gate_triggered: true` at top level.
- Green's "+20% budget" auto-action is replaced with "HOLD all scaling — foundation gate active".
- Yellow / Red / New auto-actions are unchanged (already conservative).
- Non-foundation findings in green/yellow/new are tagged `deferred_until_foundation_clear: true` (still visible to GM).

## Portfolio-consolidation + presentation rules (canonical)

The raw sub-skill findings over-fragment. Before emitting, consolidate:

- **One review effort, not two.** Merge any "rating push" and "review-velocity
  push" into a **single** program. Pick the locations that matter (rating-gated
  stores + low-review-volume stores) and run one flyer/$5-credit push across
  them. Never ship two overlapping review actions. Flyer mechanics: **we design
  → client prints & bags them → we automate the Uber Eats replies; DoorDash
  replies are manual on the client.**
- **Hero image is portfolio-wide by default.** A storefront-CTR fix is a
  hero/photo problem across *all* locations, not one store. Emit a single
  "hero refresh — all locations" action (routed to Dilli via design brief),
  unless there's a specific reason to isolate one store.
- **Separate "what we need from the client" from "what Spice does."** Stage the
  client-asks explicitly (approve menu restructure, upload/portal access, print
  flyers) — these gate time-to-value. Surface them as their own block.
- **Sequence menu + ops before aggressive campaign scaling.** Campaigns convert
  better after menu/ops fixes. But **carve out quick wins** — obvious spend
  trims, a hero swap, a higher-threshold AOV campaign — and ship them
  immediately. Time-to-value is the invisible metric every client is watching:
  how fast do they get something usable or a result.
- **Cadence.** Present in **week 2**, start implementing by **week 3**. Every
  deliverable must have a clear "what it is + when we share it."

## v0.1 fall-back

When `tier_rollup` is None, output reverts to:

```json
{
  "version": "0.1-stub",
  "kanban": { "P1_this_week": [...], "P2_next_30d": [...], "P3_watch": [...] },
  "deliverable_triggers": [...]
}
```

Preserves the original `test_smoke_e2e.py::test_full_run_produces_valid_outputs`
contract.
