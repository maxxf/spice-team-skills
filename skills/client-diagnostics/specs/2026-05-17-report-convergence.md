# Report Convergence — one source for Notion + PDF

**Problem.** Two renderers existed: the per-client bespoke build
(`Desktop/.../dailys_diagnostic/build_report.py`, hand-tuned HTML→PDF) and the
skill's Notion path (`orchestrator/notion_assembly.py`). They drifted — the
Daily's appendix once contradicted its own chart because it was hand-typed.

**Direction.** One orchestrator pass → both outputs. Phase 5 already produces
the canonical state (payloads, radar, tier rollup, action plan, foundation
gate, charts). Notion and HTML/PDF are now both pure renders of that state.

## Status

- ✅ `orchestrator/html_export.py` — styled, self-contained HTML from Phase-5
  state, reusing `notion_assembly` content helpers (hero, radar summary, WRO,
  kanban, tier counts, sub-skill prose, tier detail). Dashboard-first + `<details>`
  toggles mirror the Notion structure exactly; charts inlined as base64.
- ✅ Wired: `entry.run(..., export_html=True)` writes `<run>/report.html`;
  `run_diagnostic.py --html`.
- ✅ PDF: print `report.html` with headless Chrome
  (`--headless --print-to-pdf --no-pdf-header-footer`). Print CSS already
  guards page breaks.

## Remaining (next increments)

1. **Retire the bespoke builder.** Port the few bespoke-only touches worth
   keeping (cover masthead density, narrative captions) into `html_export.py`
   as optional richness; then `dailys_diagnostic/build_report.py` becomes a
   thin `run_diagnostic.py --html` call. Until then it stays as the Daily's
   one-off but is no longer the template.
2. ✅ **Chrome PDF step in-skill.** `orchestrator/pdf_export.py` (Chrome
   discovery + graceful fallback) + `run_diagnostic.py --pdf --out DIR`. One
   Cowork command → stable `<slug>-diagnostic.html` + `.pdf`. No browser →
   HTML still written + actionable message.
3. **Cover page + page numbers** in print CSS (highest cosmetic gap vs bespoke).
5. ✅ **Notion = home, exact format intact.** Native page (skim + search) now
   carries a top `_pdf_link` callout; `--publish` renders the PDF and the
   manifest flags a `kind:"pdf"` entry. Publish flow: upload PDF to Drive,
   swap the placeholder for a Notion bookmark. One page = native dashboard +
   one-click exact-layout PDF.
4. ✅ **Shared chart module.** `chart_helpers.py` is canonical: `trend_overlay`
   added, `top15_green_bar` recoloured by true tier + full-$ labels. Orchestrator
   now feeds it real weekly trend (topline emits `trend_weekly`) and **real
   per-store net payout** (`_build_top15_by_payout` — placeholder removed). The
   bespoke `make_charts.py` is now a candidate for deletion once it's confirmed
   the skill output matches.

## Placeholders — all fixed

- ✅ Top-15 payout: real per-store `net_payout` from the validated input
  (`_build_top15_by_payout`); uniform $1,000 placeholder removed.
- ✅ Re-order Rate: `diagnostic-topline` now scores it from an optional
  `reorder_rate_pct` input via the framework band. When that data is absent the
  radar **suppresses the dim and records a `data_quality` gap** instead of
  emitting a fabricated 6/10 (`cross_cutting.assemble_radar` drops it; fail-open
  zeros only when the topline payload is entirely missing).

No remaining fabricated values in the skill pipeline. `campaigns
spend_on_broken_store` is a wired stub (fires on flagged stores), not fake data.

Single rule going forward: **no hand-typed client numbers in any renderer** —
everything flows from the orchestrator state.
