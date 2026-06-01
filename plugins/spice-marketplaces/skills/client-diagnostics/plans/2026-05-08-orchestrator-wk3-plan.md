# Diagnostics Orchestrator Wk 3 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development. TDD per task. Wk 1 + Wk 2 + Wk 2.5 plans are reference implementations — same structural patterns apply.

**Goal:** Take the diagnostics skill from "synthetic-data PoC" to "produces real client-deliverable artifacts." Closes 4 gaps surfaced during Wk 2 / Wk 2.5: action-plan polish, cross-cutting fail-open, chart generation wiring, Notion page assembly.

**State coming in:** 75 tests passing across 6 skills. Tier-aware action plan working end-to-end against synthetic data. Architecture proven; only the visual + production-hardening layer remains.

**Spec:** `specs/2026-05-08-orchestrator-redesign.md`
**Wk 1 plan:** `plans/2026-05-08-orchestrator-wk1-plan.md`
**Wk 2 plan:** `plans/2026-05-08-orchestrator-wk2-plan.md`
**Source for chart specs:** `references/diagnostic-framework.md` lines 136–209 (Chart Library)
**Existing chart code (preserve, refactor in Chunk 3):** `references/generate_diagnostic_charts.py` (467 lines, 8 chart functions)

**Constraints (same as Wk 1/2):**
- Cowork is NOT in git — no commit steps
- Python 3.9 — `from __future__ import annotations` first line for any new `.py` using modern type hints
- `.venv/bin/pytest` always (no activation)
- Don't modify Wk 1/Wk 2/Wk 2.5 work outside the listed files per chunk
- After tests pass each chunk, deploy via `rsync` to `/Users/maxx/Desktop/spice-team-skills/skills/`

**Wk 3 explicitly does NOT cover (deferred to Wk 4):**
- Real client-data smoke (goop Kitchen exports — Maxx-provided)
- Actually POSTING to Notion via MCP (Wk 3 produces structured page content; publish is a separate concern)
- Time-series sparkline charts (need weekly-bucket data the sub-skills don't currently emit)
- Deliverable trigger firing (Notion property → MCP dispatch loop)
- v0.2 deprecation / migration

---

## File Structure

| Action | Path | Responsibility |
|---|---|---|
| Modify | `Cowork/Skills/diagnostic-action-plan/diagnostic_action_plan/entry.py` | Multi-red-bucket auto-actions + impact_usd ranking within tiers |
| Modify | `Cowork/Skills/diagnostic-action-plan/tests/test_entry.py` | Add tests for the two new behaviors |
| Modify | `Cowork/Skills/client-diagnostics/orchestrator/cross_cutting.py` | Fail-open defensive guards |
| Modify | `Cowork/Skills/client-diagnostics/tests/test_cross_cutting.py` | Tests for fail-open paths |
| Create | `Cowork/Skills/client-diagnostics/orchestrator/chart_helpers.py` | Refactored chart functions (extracted from existing `generate_diagnostic_charts.py`) |
| Create | `Cowork/Skills/client-diagnostics/tests/test_chart_helpers.py` | Tests for chart functions (file-creation + structural assertions) |
| Modify | sub-skills' `compute.py` (menu, ops, campaigns, topline) | Emit real chart paths via `chart_helpers` import |
| Modify | sub-skills' `tests/test_compute.py` | Assert chart files materialized |
| Create | `Cowork/Skills/client-diagnostics/orchestrator/notion_assembly.py` | Phase 5 — assemble dual-half page content from sub-skill outputs + cross-cutting |
| Modify | `Cowork/Skills/client-diagnostics/orchestrator/entry.py` | Wire Phase 5 invocation; produce `notion_page.md` and `notion_blocks.json` |
| Create | `Cowork/Skills/client-diagnostics/tests/test_notion_assembly.py` | Tests for page structure |

---

## Chunk 1: Action-plan polish (multi-red-bucket auto-actions + impact ranking)

Two improvements to `diagnostic-action-plan` v0.2 surfaced during Wk 2.5 smoke:

**Issue A — Multi-red-bucket coverage.** Today's `build_plan` emits ONE "Fix <worst_bucket>" auto-action per red store. If a store is red across menu+ops+campaigns (Venice in the smoke), only one of the three gets surfaced. The framework rule "Red rollup if any bucket = red" implies the GM should fix EVERY red bucket, not just one. Use `per_bucket_flags` from `tier_rollup` to emit one fix-action per red bucket.

**Issue B — Impact ranking within tier groups.** `finding_actions[]` inside each tier group is currently in arbitrary order. Should sort by `estimated_impact_usd` desc (nulls last), then by severity, so the GM scanning a tier sees the highest-impact items first.

### Tasks

**Task 1.1: Multi-red-bucket auto-actions**

- Modify `build_plan` to iterate `per_bucket_flags` for each red store and emit:
  ```python
  for bucket, flag in store_rollup["per_bucket_flags"].items():
      if flag == "red":
          auto_actions.append({
              "kind": "auto",
              "action": f"Fix {bucket} at {store}",
              "stores": [store],
              "rationale": f"Red {bucket} bucket — fix before resuming spend",
              "deliverable_trigger": None,
          })
  ```
- Replace existing single-`worst_bucket` logic with this iteration.
- Add test: `test_red_store_with_multiple_red_buckets_emits_one_action_per_bucket` — Venice with menu=red AND ops=red AND campaigns=red → 3 "Fix X at Venice" auto-actions.
- Adjust existing `test_red_tier_emits_fix_worst_bucket_auto_action` to assert the iteration produces ≥1 fix-action when only one bucket is red (it still passes, just renamed in spirit).

**Task 1.2: Impact ranking within tier groups**

- Add a `_sort_actions_by_impact(actions)` helper:
  ```python
  def _sort_actions_by_impact(actions):
      def key(a):
          val = a.get("estimated_impact_usd")
          has_val = val is not None
          severity_rank = {"foundation": 4, "high": 3, "medium": 2, "low": 1}.get(a.get("severity", "low"), 1)
          return (has_val, val if has_val else 0, severity_rank)
      return sorted(actions, key=key, reverse=True)
  ```
- Apply to each tier group's `finding_actions[]` before output.
- Apply to `portfolio_actions[]`.
- Add test: `test_finding_actions_within_tier_sorted_by_impact_desc` — multiple findings in red with mixed impacts → output has highest impact first, nulls last.

**Checkpoint:** action-plan tests grow from 18 → ~21. Run: `cd diagnostic-action-plan && .venv/bin/pytest tests/ -v`. All passing.

---

## Chunk 2: Cross-cutting fail-open

`orchestrator/cross_cutting.py` currently hard-indexes `payloads["topline"]`, `payloads["menu"]`, etc. If any sub-skill subprocess fails in production (subprocess crash, file-write error), Phase 3 raises `KeyError` instead of fail-opening per the spec.

### Tasks

**Task 2.1: Defensive guards in `assemble_radar`**

- Each radar dim lookup uses `.get()` with a default of `0.0` if the owner sub-skill is missing
- Composite dims (Marketing Efficiency, Operations) check input availability before computing; emit `0.0` with a `"reason": "missing input"` flag in a sibling dict if you want, or just `0.0`

**Task 2.2: Defensive guards in `rollup_tiers`**

- Already partially defensive (Wk 2 tier rollup ignores absent buckets per the post-review fix). Verify behavior holds when a sub-skill payload is missing entirely (not just absent for one store).
- Add test: `test_rollup_tiers_handles_missing_sub_skill_payload` — `per_bucket = {"menu": {...}}` (campaigns + ops missing) → rollup uses only menu, doesn't error.

**Task 2.3: Defensive guards in `compute_foundation_gate`**

- Already partially defensive (Wk 1 fail-conservative rule for ops/menu failures). Verify it handles `payloads.get(owner_short)` returning None.
- Add test: `test_foundation_gate_handles_missing_payload_dict` — `payloads = {}` (all sub-skills failed) → gate triggers with all 5 fail-conservative reasons.

**Task 2.4: Defensive guards in `select_win_risk_opp`**

- Iterate `payloads.values()` defensively; if a payload is malformed (missing `drafted.win_risk_opp_candidates`), skip it.

**Task 2.5: Update orchestrator entry.py to use `_load_payloads` everywhere**

- Currently `_load_payloads` skips failed sub-skills. After Phase 3 calls, the `payloads` dict may not have all 4 keys. Update `assemble_radar` call sites to handle missing topline_metrics / campaigns_metrics:
  ```python
  topline_metrics = payloads.get("topline", {}).get("computed", {}).get("metrics", {})
  campaigns_metrics = payloads.get("campaigns", {}).get("computed", {}).get("metrics", {})
  ```

**Checkpoint:** cross_cutting tests grow from 12 → ~15. client-diagnostics suite all passing. No regression in any sub-skill suite.

---

## Chunk 3: Real chart generation

Wire the existing `generate_diagnostic_charts.py` into the orchestrator/sub-skill pipeline. Each sub-skill becomes capable of producing real PNG charts. Cross-cutting charts (radar, tier donut, top15 green bar) get produced by orchestrator in Phase 3.

### Tasks

**Task 3.1: Refactor `references/generate_diagnostic_charts.py` → `orchestrator/chart_helpers.py`**

- Read the existing file in full. Identify 8 chart functions per the framework Chart Library (lines 136–209): `radar_7dim`, `sparklines_gmv_orders`, `tier_donut`, `funnel_ue`, `top_skus_bar`, `campaign_2x2`, `daypart_heatmap`, `top15_green_bar`.
- Move each function into a new `orchestrator/chart_helpers.py` module. PRESERVE function signatures and matplotlib code byte-for-byte where possible.
- Move `SPICE_PALETTE` constant.
- Each function takes structured data + an `output_path: Path` and writes a PNG.
- Add `from __future__ import annotations` at top.
- Original `references/generate_diagnostic_charts.py` is RENAMED to `references/_legacy_generate_diagnostic_charts.py.bak` (keep as backup; do NOT delete — it's 16.6 KB of validated code).

**Task 3.2: Test chart functions structurally**

Create `tests/test_chart_helpers.py`:
- For each chart function, write a test that calls it with synthetic data and asserts the PNG file is created with non-zero size.
- Don't visually validate the chart contents (out of scope — that's a manual eyeball test). Just file-creation + non-empty + valid PNG header (`b"\x89PNG"`).
- ~8 tests (one per chart).

**Task 3.3: Wire sub-skill chart emission**

Update each sub-skill's `compute.py` to emit charts. Pattern (use this exactly in each):

```python
import sys
from pathlib import Path
sys.path.insert(0, "/Users/maxx/Desktop/Cowork/Skills/client-diagnostics")  # for chart_helpers

from orchestrator import chart_helpers


def run(*, client, window_start, window_end, df, output_dir: Path | None = None) -> dict:
    # ... existing logic ...

    # Charts (only if output_dir provided — keeps tests fast when not needed)
    charts = []
    if output_dir is not None:
        chart_dir = output_dir / "charts"
        chart_dir.mkdir(parents=True, exist_ok=True)
        # emit domain-specific charts
        if "menu" in __name__:
            funnel_path = chart_dir / "funnel_ue.png"
            chart_helpers.funnel_ue(funnel_data, funnel_path)
            charts.append({"id": "funnel_ue", "path": str(funnel_path.relative_to(output_dir.parent.parent))})
            # ... etc
    payload["computed"]["charts"] = charts
    return payload
```

Per sub-skill chart ownership (per spec):
- **topline:** `sparklines_gmv_orders` — DEFERRED (needs weekly-bucket data) — emit empty `charts: []` for Wk 3
- **menu:** `funnel_ue`, `top_skus_bar` — emit if input has the columns; else skip individual chart with `data_quality.gaps` note
- **ops:** `daypart_heatmap` (move to ops since it's operational; framework calls it "blended UE+DD" but ops sub-skill has the closest data) — DEFERRED if input lacks daypart columns
- **campaigns:** `campaign_2x2` — emit if input has the columns

For Wk 3, charts that require data the sub-skill doesn't currently get → skipped (logged in `data_quality.gaps`). Wk 4 enriches inputs.

**Task 3.4: Wire orchestrator cross-cutting chart emission**

In `orchestrator/entry.py` Phase 3, after computing radar / tier_rollup, generate cross-cutting charts to `<run-dir>/cross_cutting/`:
- `radar_7dim.png` from radar dict
- `tier_donut.png` from tier_rollup
- `top15_green_bar.png` from tier_rollup (filter green stores, sort by per-store score, top 15)

Add E2E test: `test_full_run_generates_cross_cutting_charts` — assert files exist after a run.

**Task 3.5: Update sub-skill entries to pass `output_dir`**

Each sub-skill's `entry.py` already takes `--output-path` (the JSON file). Add `--charts-dir` arg, pass to `compute.run(... output_dir=<charts_dir>)`. Orchestrator's `_dispatch_sub_skill` passes the per-sub-skill chart subdir.

**Checkpoint:** chart_helpers + ≥8 tests passing. Each sub-skill emits ≥0 chart paths (depending on data availability). E2E test confirms cross-cutting charts materialize. Note: PNG files are binary; tests should `os.path.exists()` and check file size > 0, not parse contents.

---

## Chunk 4: Notion page assembly (Phase 5)

Build the dual-half client-deliverable Notion page structure. Wk 3 produces a structured representation (markdown + Notion-block JSON); actual MCP publish is Wk 4.

### Tasks

**Task 4.1: `orchestrator/notion_assembly.py`**

Create the module. Two main functions:

```python
def build_page_markdown(*, client, window, payloads, radar, tier_rollup, action_plan, foundation_gate, charts_dir: Path) -> str:
    """Return full dual-half page as markdown (Notion-paste-ready)."""

def build_page_blocks(*, client, window, payloads, radar, tier_rollup, action_plan, foundation_gate, charts_dir: Path) -> list[dict]:
    """Return list of Notion block dicts (for MCP notion-create-pages)."""
```

`build_page_markdown` produces (per spec §"Build the Notion Page" + Wk 1 SKILL.md v0.2 structure):

```markdown
# {Client} | Diagnostics & Action Plan | {window_start} – {window_end}

[FOUNDATION GATE BANNER if triggered]

## Hero Stat Strip

| 90-Day Gross Sales | Orders | Blended AOV | Net Payout |
|---|---|---|---|
| ${gross} | {orders} | ${aov} | {payout} ({payout_pct}%) |

## Brand Health Radar

![Radar]({charts_dir}/radar_7dim.png)
> Overall {score}/10. Weakest: {dim1}, {dim2}.

## Win / Risk / Opportunity

| 🏆 Win | ⚠️ Risk | 💡 Opportunity |
|---|---|---|
| {win.headline} | {risk.headline} | {opp.headline} |
| ${win.value} | ${risk.value} | ${opp.value} |

## Action Plan

### 🔴 Red Stores ({n})
{per-tier auto + finding actions}

### 🟡 Yellow Stores ({n})
...

### 🟢 Green Stores ({n})
...

### 🆕 New Stores ({n})
...

### 🌐 Portfolio
{portfolio_actions}

## Tier Health

![Tier donut]({charts_dir}/tier_donut.png)
{n} stores: 🟢 {g} · 🟡 {y} · 🔴 {r} · 🆕 {nn}.

---

[HALF 2 — collapsed toggles in Notion. In markdown, render as H2 sections]

## Top-line Performance Detail
{topline.drafted.toggle_prose}

## Menu & Storefront Detail
{menu.drafted.toggle_prose}
![Funnel]({charts_dir}/funnel_ue.png) (if exists)
![Top SKUs]({charts_dir}/top_skus_bar.png) (if exists)

## Operations Detail
{ops.drafted.toggle_prose}

## Campaigns Detail
{campaigns.drafted.toggle_prose}
![Campaign 2x2]({charts_dir}/campaign_2x2.png) (if exists)

## Data Quality

✓ Topline ({completeness}%) · ✓ Menu ({completeness}%) · ✓ Ops ({completeness}%) · ✓ Campaigns ({completeness}%)
{any gaps from data_quality.gaps[]}
```

`build_page_blocks` produces the same content as Notion block JSON (heading_2, paragraph, table, image, callout, divider). Reference: `mcp__f34fcb36...__notion-create-pages` API expects a list of block dicts.

**Task 4.2: Update orchestrator `entry.py` Phase 5**

```python
# Phase 5: Notion page assembly
state = run_state.update(layout.run_state_path, phase=5)
from orchestrator import notion_assembly
charts_dir = layout.root / "cross_cutting"  # primary; sub-skill charts also referenced
md = notion_assembly.build_page_markdown(
    client=client,
    window={"start": window_start, "end": window_end},
    payloads=payloads,
    radar=radar,
    tier_rollup=tier_rollup,
    action_plan=action_plan,
    foundation_gate=foundation_gate,
    charts_dir=charts_dir,
)
(layout.root / "notion_page.md").write_text(md)
blocks = notion_assembly.build_page_blocks(... same args ...)
(layout.root / "notion_blocks.json").write_text(json.dumps(blocks, indent=2))
```

**Task 4.3: Tests**

Create `tests/test_notion_assembly.py`:
- `test_markdown_includes_client_and_window` — title line correct
- `test_markdown_includes_foundation_banner_when_triggered` — banner present iff foundation_gate.triggered
- `test_markdown_includes_each_tier_section` — Red/Yellow/Green/New all present (even if 0 stores)
- `test_markdown_includes_each_half2_section` — 4 detail sections present (one per sub-skill)
- `test_markdown_renders_chart_images` — `![...]({path})` for radar + tier_donut + per-sub-skill charts that exist
- `test_blocks_output_is_list_of_valid_block_dicts` — each block has `type` + content matching schema
- `test_data_quality_footer_lists_completeness_per_sub_skill`

Add E2E test: `test_full_run_produces_notion_page_artifact` — after `entry.run(...)`, `notion_page.md` and `notion_blocks.json` exist with non-empty content.

**Checkpoint:** notion_assembly module + ≥7 tests passing. Full pipeline produces a paste-ready markdown artifact + Notion-block JSON.

---

## Chunk 5: Wk 3 verification + deploy

```bash
echo "=== full Wk 3 verification ==="
for skill in client-diagnostics diagnostic-topline diagnostic-menu diagnostic-ops diagnostic-campaigns diagnostic-action-plan; do
  cd /Users/maxx/Desktop/Cowork/Skills/$skill && .venv/bin/pytest tests/ -q
done

echo "=== full pipeline smoke ==="
cd /Users/maxx/Desktop/Cowork/Skills/client-diagnostics && .venv/bin/python -c "
from orchestrator import entry, output_layout
import pandas as pd, tempfile
from pathlib import Path
from datetime import datetime

with tempfile.TemporaryDirectory() as tmp:
    output_layout.RUN_ROOT = Path(tmp)
    inputs = Path(tmp) / 'inputs'; inputs.mkdir()
    # ... synth CSV ...
    result = entry.run(client='wk3-smoke', window_start='2026-02-08', window_end='2026-05-08', inputs_dir=inputs)
    print('notion_page.md size:', (result.layout.root / 'notion_page.md').stat().st_size, 'bytes')
    print('notion_blocks.json size:', (result.layout.root / 'notion_blocks.json').stat().st_size, 'bytes')
    print('cross_cutting charts:', sorted((result.layout.root / 'cross_cutting').glob('*.png')))
"

echo "=== deploy ==="
for skill in client-diagnostics diagnostic-topline diagnostic-menu diagnostic-ops diagnostic-campaigns diagnostic-action-plan; do
  rsync -a --delete \
    --exclude='.venv' --exclude='__pycache__' --exclude='.pytest_cache' --exclude='*.pyc' \
    "/Users/maxx/Desktop/Cowork/Skills/$skill/" \
    "/Users/maxx/Desktop/spice-team-skills/skills/$skill/"
done
```

### Checkpoint

- All ~95+ tests passing (75 entering Wk 3 + ~20 added)
- Wk 3 smoke produces real notion_page.md + cross-cutting PNGs
- Deployed to team-skills

---

## Critical Files

- This plan: `plans/2026-05-08-orchestrator-wk3-plan.md`
- Spec: `specs/2026-05-08-orchestrator-redesign.md`
- Existing chart code: `references/generate_diagnostic_charts.py` (467 lines, becomes `chart_helpers.py` module)
- Framework chart specs: `references/diagnostic-framework.md` lines 136–209
- Action-plan to polish: `Cowork/Skills/diagnostic-action-plan/diagnostic_action_plan/entry.py`
- Cross-cutting to harden: `Cowork/Skills/client-diagnostics/orchestrator/cross_cutting.py`
