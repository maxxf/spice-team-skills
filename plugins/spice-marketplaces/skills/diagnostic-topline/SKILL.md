---
name: diagnostic-topline
description: >
  Sub-skill of client-diagnostics. Produces top-line financial findings:
  gross sales, momentum, payout, platform breakdown. Dispatched in parallel
  by the client-diagnostics orchestrator. Emits standardized JSON per the
  sub-skill output contract. Should not be invoked directly by users; use
  client-diagnostics.
version: 0.1.0
---

# Diagnostic — Top-line Performance

Produces the top-line section of the diagnostic. Owns the **Top-line Performance** Half 2 toggle, the AOV and Re-order Rate radar dimensions, and revenue/momentum findings.

## Inputs

The orchestrator passes:
- `--client <slug>` — client slug
- `--window-start YYYY-MM-DD --window-end YYYY-MM-DD` — 90-day window
- `--inputs-dir <path>` — directory containing platform CSVs
- `--output-path <path>` — where to write `diagnostic-topline_results.json`

## Output

A JSON file matching the sub-skill output contract (see `client-diagnostics/orchestrator/contract.py`).

## Pattern Library

See `references/patterns-topline.md`.
