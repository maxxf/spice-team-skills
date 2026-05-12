# Campaigns & Promos Pattern Library (v0.1)

Subset of `client-diagnostics/references/diagnostic-framework.md` scoped to the campaigns sub-skill (tier sub-bucket: "campaigns"; owns radar dim "Campaigns / ROAS").

## Patterns

| pattern_id | Trigger | Severity | Default deliverable |
|---|---|---|---|
| low_roas_high_spend | total spend > $500/wk AND blended ROAS < 2.5 | high | campaign-plan (params: stores, focus="cost_recovery") |
| over_discounting | promo_count_active >= 3 | medium | campaign-plan (params: stores, focus="promo_consolidation") |
| spend_on_broken_store | spend > 0 AND store appears in cross-cutting flagged-store list | foundation | (action-plan applies foundation override) |

The "Ad Dependent" pattern in the framework maps to the combination of `low_roas_high_spend` + a Red ops/menu sub-bucket — money on fire while fundamentals are broken.

## Cross-cutting note: spend_on_broken_store (Wk 2 stub)

The `spend_on_broken_store` pattern requires Phase-3 cross-cutting state (which stores are red-flagged in ops or menu) that the orchestrator only knows after all sub-skills have run. Wk 2 implementation: the entry CLI accepts `--cross-cutting-flagged-stores <comma,separated>` (default empty). When the orchestrator dispatches this sub-skill, Wk 2 always passes empty (synthetic data tests never fire it). In Wk 2.5/Wk 3, the orchestrator will run the campaigns sub-skill twice, or read run_state.json to pass the real flagged list on a second pass.

The compute function takes `flagged_stores: list[str]` (default `[]`) — keep the synthetic test surface clean.

## Tier sub-bucket — Campaigns (per framework lines 89–92)

Each store gets a `campaigns` flag of green / yellow / red:

- **Healthy (green):** blended ROAS >= 3.5 AND incremental_orders_per_week >= 10 AND promo_count_active < 2
- **Watch (yellow):** ROAS 2.5–3.5 OR promo_count_active >= 2 OR (spend > 0 AND incremental_orders_per_week < 10)
- **Broken (red):** ROAS < 2.5 OR (store appears in `flagged_stores` per `spend_on_broken_store`)

`new` is reserved for stores with insufficient history; Wk 2 synthetic data never produces it.

## Radar contribution — Campaigns / ROAS (per framework table)

Portfolio-blended ROAS = `sum(attributed_sales) / sum(spend)`:

| Blended ROAS | Score |
|---|---|
| <2 | 3 |
| 2–3 | 5 |
| 3–4 | 6.5 |
| 4–5 | 8 |
| >5 | 9 |

## Marketing Efficiency composite input (CRITICAL)

The orchestrator's `assemble_radar` reads `total_marketing_investment` (sum of all spend across portfolio) from `computed.metrics`. This key MUST be present in every payload — the Marketing Efficiency radar dim depends on it. Missing it silently breaks orchestrator radar assembly.
