---
name: diagnostic-ops
description: >
  Sub-skill of client-diagnostics. Produces operations and quality findings:
  ratings, error rate, cancellation rate, uptime, hours accuracy. Owns the
  per-store "ops" tier sub-bucket. Does NOT emit radar dimensions directly —
  the orchestrator computes the Operations radar dim as a composite from this
  sub-skill's tier_contributions. Dispatched in parallel by the
  client-diagnostics orchestrator. Emits standardized JSON per the sub-skill
  output contract. Should not be invoked directly by users; use
  client-diagnostics.
version: 0.1.0
---

# Diagnostic — Operations & Quality

Produces the operations and quality section of the diagnostic. Owns the **Operations & Quality** Half 2 toggle and the per-store "ops" tier sub-bucket.

The orchestrator's foundation gate reads `computed.metrics.{rating, error_rate_pct, uptime_pct}` from this sub-skill — those keys MUST be present.

## Inputs

The orchestrator passes:
- `--client <slug>` — client slug
- `--window-start YYYY-MM-DD --window-end YYYY-MM-DD` — 90-day window
- `--inputs-dir <path>` — directory containing platform CSVs
- `--output-path <path>` — where to write `diagnostic-ops_results.json`

## Output

A JSON file matching the sub-skill output contract (see `client-diagnostics/orchestrator/contract.py`).

## Pattern Library

See `references/patterns-ops.md`.
