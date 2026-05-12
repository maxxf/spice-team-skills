# Operations & Quality Pattern Library (v0.1)

Subset of `client-diagnostics/references/diagnostic-framework.md` scoped to the ops sub-skill (tier sub-bucket: "ops"; no direct radar dims — Operations is an orchestrator-composite from tier_contributions).

## Patterns

| pattern_id | Trigger | Severity | Default deliverable |
|---|---|---|---|
| low_rating_below_42 | rating < 4.2 | foundation | ratings-flyer (params: stores affected) |
| error_spike | error_rate_pct > 5 | foundation | (foundation gate routing — orchestrator handles) |
| cancellation_surge | cancellation_pct > 5 | high | (action-plan handles internally — no specific downstream skill yet) |

The "Leaky Bucket" pattern in the framework maps to the combination of `error_spike` + `cancellation_surge` — operational issues bleeding revenue from an otherwise-healthy storefront.

## Tier sub-bucket — Ops (per framework lines 84–87)

Each store gets an `ops` flag of green / yellow / red:

- **Healthy (green):** error_rate_pct < 2% AND cancellation_pct < 2% AND uptime_pct > 97% AND rating ≥ 4.5 AND hours_accurate
- **Watch (yellow):** error_rate_pct 2–5%, OR cancellation_pct 2–5%, OR uptime_pct 90–97%, OR rating 4.2–4.5
- **Broken (red):** error_rate_pct > 5%, OR cancellation_pct > 5%, OR uptime_pct < 90%, OR rating < 4.2, OR repeated hours-mismatch (Wk 2 synthetic: any single `hours_accurate=False`)

`new` is reserved for stores with insufficient history; Wk 2 synthetic data never produces it.

## Foundation gate inputs (CRITICAL)

The orchestrator's `compute_foundation_gate` reads these keys from `computed.metrics`:

- `rating` — portfolio min (gate fires on any store rating < 4.2)
- `error_rate_pct` — portfolio max (gate fires on any store error_rate > 5%)
- `uptime_pct` — portfolio min (gate fires on any store uptime < 90%)

These keys MUST be present in every payload. Missing them silently breaks the orchestrator's foundation routing.

## Radar contributions

This sub-skill emits `radar_contributions = {}`. The Operations radar dim is computed by the orchestrator as a composite from this sub-skill's `tier_contributions` (see `cross_cutting.assemble_radar`).
