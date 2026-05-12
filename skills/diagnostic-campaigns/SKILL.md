---
name: diagnostic-campaigns
description: >
  Sub-skill of client-diagnostics. Produces campaign and promo findings:
  ROAS, ad spend efficiency, promo stack count, incremental orders per week.
  Owns the per-store "campaigns" tier sub-bucket and the "Campaigns / ROAS"
  radar dim. Dispatched in parallel by the client-diagnostics orchestrator.
  Emits standardized JSON per the sub-skill output contract. Should not be
  invoked directly by users; use client-diagnostics.
version: 0.1.0
---

# Diagnostic — Campaigns & Promos

Produces the campaigns and promos section of the diagnostic. Owns the **Campaigns & Promos** Half 2 toggle, the per-store "campaigns" tier sub-bucket, and the **Campaigns / ROAS** radar dim.

The orchestrator's Marketing Efficiency composite reads `computed.metrics.total_marketing_investment` from this sub-skill — that key MUST be present.

## Inputs

The orchestrator passes:
- `--client <slug>` — client slug
- `--window-start YYYY-MM-DD --window-end YYYY-MM-DD` — 90-day window
- `--inputs-dir <path>` — directory containing platform CSVs
- `--output-path <path>` — where to write `diagnostic-campaigns_results.json`
- `--cross-cutting-flagged-stores <store1,store2>` — optional Wk 2 stub for the `spend_on_broken_store` pattern (defaults to empty)

## Output

A JSON file matching the sub-skill output contract (see `client-diagnostics/orchestrator/contract.py`).

## Pattern Library

See `references/patterns-campaigns.md`.
