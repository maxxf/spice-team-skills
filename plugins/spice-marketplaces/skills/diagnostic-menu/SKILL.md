---
name: diagnostic-menu
description: >
  Sub-skill of client-diagnostics. Produces menu and storefront findings:
  menu CVR, photo coverage, hero status, category sprawl, and storefront
  → menu click-through. Owns the Conversion and Traffic radar dimensions
  and the per-store "menu" tier sub-bucket. Dispatched in parallel by the
  client-diagnostics orchestrator. Emits standardized JSON per the
  sub-skill output contract. Should not be invoked directly by users; use
  client-diagnostics.
version: 0.1.0
---

# Diagnostic — Menu & Storefront

Produces the menu and storefront section of the diagnostic. Owns the **Menu & Storefront** Half 2 toggle, the Conversion and Traffic radar dimensions, the per-store "menu" tier sub-bucket, and menu/photo/SKU findings.

## Inputs

The orchestrator passes:
- `--client <slug>` — client slug
- `--window-start YYYY-MM-DD --window-end YYYY-MM-DD` — 90-day window
- `--inputs-dir <path>` — directory containing platform CSVs
- `--output-path <path>` — where to write `diagnostic-menu_results.json`

## Output

A JSON file matching the sub-skill output contract (see `client-diagnostics/orchestrator/contract.py`).

## Pattern Library

See `references/patterns-menu.md`.
