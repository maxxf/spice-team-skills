# Diagnostics Orchestrator Wk 2 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development. Follow TDD per task. The Wk 1 plan (`2026-05-08-orchestrator-wk1-plan.md`) is the reference implementation pattern — Wk 2 sub-skills mirror Wk 1's `diagnostic-topline` structure exactly.

**Goal:** Build the 3 remaining domain sub-skills (`diagnostic-menu`, `diagnostic-ops`, `diagnostic-campaigns`) and update the orchestrator to dispatch all 4 sub-skills in parallel with cross-cutting integration. Closes the contract loop end-to-end against synthetic data for ALL domains.

**Architecture:** Each sub-skill follows the topline pattern: hyphen-named skill folder + underscore-named Python package + `pyproject.toml` + per-skill venv + tests/. Each emits contract-shaped JSON. Orchestrator's Phase 2 fans out via parallel subprocess; Phase 3 assembles cross-cutting; Phase 4 dispatches action-plan with all 4 sub-skill outputs.

**Spec:** `specs/2026-05-08-orchestrator-redesign.md`
**Wk 1 plan (reference):** `plans/2026-05-08-orchestrator-wk1-plan.md`
**Pattern source for sub-skill compute logic:** `references/diagnostic-framework.md` (radar scoring bands, foundation thresholds, location tier sub-bucket rules, pattern library, cuisine CVR benchmarks)

**Constraints (same as Wk 1):**
- Cowork is NOT in git — no commit steps
- Python 3.9 — `from __future__ import annotations` as first line of every new `.py` using modern type hints
- `.venv/bin/pytest` always (no activation)
- Don't modify Wk 1 work in `client-diagnostics/orchestrator/` except `entry.py` in Chunk 4
- Don't touch `references/diagnostic-framework.md` content (it's the source of truth for sub-skill compute logic)
- After tests pass, deploy via `rsync` to `/Users/maxx/Desktop/spice-team-skills/skills/`

**Wk 2 explicitly does NOT cover:**
- Real chart generation (sub-skills emit chart placeholder paths only; real chart wiring = Wk 3 with `generate_diagnostic_charts.py` refactor)
- Real Notion page assembly (Phase 5 stays a stub; Wk 3)
- Real client-data inputs (synthetic CSV only Wk 2; goop Kitchen exports = Wk 3)
- Promoting `diagnostic-action-plan` from stub → full prioritization (Wk 2-3 transition; tracked separately)
- Deliverable trigger firing (Wk 3-4)

---

## File Structure

| Action | Path | Responsibility |
|---|---|---|
| Create | `Cowork/Skills/diagnostic-menu/` skill folder | Menu/storefront sub-skill |
| Create | `Cowork/Skills/diagnostic-ops/` skill folder | Operations sub-skill |
| Create | `Cowork/Skills/diagnostic-campaigns/` skill folder | Campaigns sub-skill |
| Modify | `Cowork/Skills/client-diagnostics/orchestrator/entry.py` | Add parallel dispatch of all 4 sub-skills + cross-cutting integration |
| Create | `Cowork/Skills/client-diagnostics/tests/test_smoke_e2e_full.py` | Full 4-sub-skill E2E test |

Each new sub-skill folder shape (mirrors `diagnostic-topline/`):
```
diagnostic-{menu,ops,campaigns}/
├── SKILL.md
├── pyproject.toml                    # pythonpath = ["."]
├── diagnostic_{menu,ops,campaigns}/  # underscore-named Python package
│   ├── __init__.py
│   ├── compute.py                    # main computation
│   └── entry.py                      # CLI wrapper, orchestrator dispatches via subprocess
├── references/
│   └── patterns-{menu,ops,campaigns}.md  # subset of diagnostic-framework.md
└── tests/
    ├── __init__.py
    └── test_compute.py
```

---

## Chunk 1: `diagnostic-menu` sub-skill

**Domain:** menu structure, storefront visual, conversion funnel, photo coverage, SKU performance.
**Owns radar dims:** Conversion (UE menu CVR), Traffic (storefront → menu CTR).
**Owns tier bucket:** "menu" (per `diagnostic-framework.md` lines 79–82: Healthy/Watch/Broken rules for CVR + photos + categories + hero).

### Inputs (Wk 2 = synthetic DataFrame)

Synthetic input columns: `store`, `menu_cvr_pct`, `photo_coverage_pct`, `hero_set` (bool), `categories_count`, `categories_populated`, `storefront_to_menu_ctr_pct`, `top_sku_revenue` (per row optional). Plan's compute can simulate this via `pandas.DataFrame`.

### Findings to implement (3, from framework's pattern library)

| pattern_id | Trigger | Severity | Deliverable trigger |
|---|---|---|---|
| `low_cvr_high_traffic` | menu_cvr_pct < cuisine benchmark AND storefront_to_menu_ctr_pct > 9% | high | `optimized-menu-sheet` (params: stores affected, focus="category_consolidation") |
| `low_photo_coverage` | photo_coverage_pct < 50% | foundation | (foundation gate routing — orchestrator handles) |
| `sku_sprawl` | categories_count > 8 AND any category empty | medium | `optimized-menu-sheet` (params: stores, focus="sku_rationalization") |

### Tier scoring (per framework lines 79–82, encoded in compute)

For each store in the input, classify per-store menu bucket:
- **Healthy:** CVR ≥ 18% (Spice fast-casual benchmark default — could be cuisine-aware later) AND photo_coverage ≥ 80% AND hero_set AND categories_populated == categories_count
- **Watch:** CVR within 20% below benchmark, OR photo_coverage 50–80%, OR 1 category empty
- **Broken:** CVR < 80% of benchmark, OR photo_coverage < 50%, OR 2+ categories empty, OR hero not set

### Radar contribution scoring (per framework table)

- **Conversion** (UE menu CVR): <15%=3 · 15–18%=4.5 · 18–20%=5 · 20–25%=7 · >25%=8 (use portfolio-level avg CVR)
- **Traffic** (storefront → menu CTR): <5%=3 · 5–7%=4 · 7–9%=6 · 9–12%=7.5 · >12%=9 (portfolio avg)

### Tests required (≥ 6)

Mirror Wk 1's topline tests:
- `test_compute_emits_payload_with_required_shape` — basic shape check
- `test_compute_payload_passes_contract_validator` — `from orchestrator import contract; contract.validate(payload)` (must add `sys.path.insert` for client-diagnostics)
- `test_low_photo_coverage_emits_foundation_finding` — store with 30% photo coverage produces a `low_photo_coverage` foundation finding
- `test_low_cvr_high_traffic_emits_high_finding` — store with 12% CVR + 11% CTR produces a `low_cvr_high_traffic` high-severity finding
- `test_tier_classification_red_when_photos_below_50` — store at 30% photos lands in tier_contributions with `flag="red"`
- `test_radar_conversion_dim_uses_framework_bands` — input avg CVR 22% → radar dim "Conversion" returns score 7

### Process

Same TDD pattern as Wk 1 Task 3.1 (`diagnostic-topline`):
1. Create folder + per-skill venv (`python3 -m venv .venv`, install pytest + pandas + jsonschema)
2. Write `pyproject.toml` (pythonpath=["."])
3. Write `SKILL.md` (mirror topline's frontmatter; description references this sub-skill's domain)
4. Write `references/patterns-menu.md` (the 3 patterns table above + cuisine CVR benchmarks copied from `diagnostic-framework.md` lines 47–60)
5. Write failing tests (the 6 listed above)
6. Implement `compute.py` (and `__init__.py` empty marker)
7. Verify tests pass
8. Write `entry.py` CLI wrapper (mirrors topline's entry.py — argparse, load CSVs from inputs-dir, write payload JSON to output-path)

### Checkpoint
- 6+ tests passing in `diagnostic-menu/tests/`
- Contract validator passes payload from `compute.run(...)` (round-trip)
- Foundation findings + high-severity findings emit deliverable_trigger blocks

---

## Chunk 2: `diagnostic-ops` sub-skill

**Domain:** uptime, errors, cancellations, ratings, downtime, hours accuracy.
**Owns radar dims:** none directly (Operations is orchestrator-composite, computed from this sub-skill's tier_contributions).
**Owns tier bucket:** "ops" (per `diagnostic-framework.md` lines 84–87).

### Inputs (synthetic DataFrame)

Synthetic columns: `store`, `rating`, `error_rate_pct`, `cancellation_pct`, `uptime_pct`, `hours_accurate` (bool).

### Findings to implement (3)

| pattern_id | Trigger | Severity | Deliverable trigger |
|---|---|---|---|
| `low_rating_below_42` | rating < 4.2 | foundation | `ratings-flyer` (params: stores affected) |
| `error_spike` | error_rate_pct > 5 | foundation | (foundation gate routing) |
| `cancellation_surge` | cancellation_pct > 5 | high | (action-plan handles — internal ops fix) |

### Tier scoring (per framework lines 84–87)

- **Healthy:** error_rate < 2% AND cancellation < 2% AND uptime > 97% AND rating ≥ 4.5 AND hours_accurate
- **Watch:** error_rate 2–5% OR cancellation 2–5% OR uptime 90–97% OR rating 4.2–4.5
- **Broken:** error_rate > 5% OR cancellation > 5% OR uptime < 90% OR rating < 4.2 OR repeated hours-mismatch

### Radar contribution

This sub-skill emits NO direct radar dims (Operations is composite at orchestrator). However it MUST emit tier_contributions populated for every store, since orchestrator's `assemble_radar` reads `payloads["ops"]["computed"]["tier_contributions"]` to compute the Operations composite.

It MUST also emit metrics for the foundation gate to read: `rating`, `error_rate_pct`, `uptime_pct` (portfolio-level — min/max/avg across stores; orchestrator's `compute_foundation_gate` reads `payloads["ops"]["computed"]["metrics"]`).

### Tests required (≥ 6)

- Same shape + validator tests as menu
- `test_low_rating_emits_foundation_finding` — store at 4.0 rating emits `low_rating_below_42` foundation finding with `ratings-flyer` deliverable_trigger
- `test_error_spike_emits_foundation_finding` — error_rate 7% emits `error_spike` foundation finding
- `test_tier_classification_red_when_uptime_below_90` — store with 85% uptime → tier flag="red"
- `test_metrics_block_includes_foundation_gate_inputs` — payload `computed.metrics` contains `rating`, `error_rate_pct`, `uptime_pct` keys (orchestrator depends on this)

### Process: same as Chunk 1 substituted for "ops".

### Checkpoint
- 6+ tests passing in `diagnostic-ops/tests/`
- Contract validator passes
- Foundation gate inputs (rating, error_rate_pct, uptime_pct) present in metrics block

---

## Chunk 3: `diagnostic-campaigns` sub-skill

**Domain:** promos, ads, ROAS, daypart, spend efficiency.
**Owns radar dims:** Campaigns / ROAS (blended).
**Owns tier bucket:** "campaigns" (per `diagnostic-framework.md` lines 89–92).

### Inputs (synthetic DataFrame)

Synthetic columns: `store`, `platform` (UE/DD/GH), `spend`, `attributed_sales`, `roas`, `incremental_orders_per_week`, `promo_count_active`.

### Findings to implement (3)

| pattern_id | Trigger | Severity | Deliverable trigger |
|---|---|---|---|
| `low_roas_high_spend` | spend > $500/wk AND roas < 2.5 | high | `campaign-plan` (params: stores, focus="cost_recovery") |
| `over_discounting` | promo_count_active >= 3 | medium | `campaign-plan` (params: stores, focus="promo_consolidation") |
| `spend_on_broken_store` | spend > 0 AND store appears in cross-cutting state's red-flagged stores | foundation | (action-plan applies foundation override) |

Note: `spend_on_broken_store` requires cross-cutting state from Phase 3 — Wk 2 detects via a shared run_state.json read in the sub-skill (orchestrator writes to run_state, sub-skill reads). Document but DEFER actual implementation to Wk 2.5/Wk 3 if read-after-write timing is hairy. Wk 2 stub: emit only when an explicit `--cross-cutting-flagged-stores` CLI arg is passed.

### Tier scoring (per framework lines 89–92)

- **Healthy:** blended ROAS ≥ 3.5 AND spend efficient AND no over-discounting
- **Watch:** ROAS 2.5–3.5 OR promo_count_active ≥ 2 OR spend running but < 10 incremental orders/week
- **Broken:** ROAS < 2.5 OR spend on broken store (deferred per above)

### Radar contribution

- **Campaigns / ROAS** (blended across UE+DD+GH): <2x=3 · 2–3x=5 · 3–4x=6.5 · 4–5x=8 · >5x=9 (portfolio-level blended ROAS)

Also MUST emit metrics: `total_marketing_investment` (sum of spend) — orchestrator's `assemble_radar` reads this for Marketing Efficiency composite.

### Tests required (≥ 6)

- Shape + validator tests
- `test_low_roas_high_spend_emits_high_finding`
- `test_over_discounting_emits_medium_finding`
- `test_tier_classification_red_when_roas_below_25` — store with ROAS=1.5 → tier flag="red"
- `test_metrics_block_includes_total_marketing_investment` — payload `computed.metrics` has `total_marketing_investment`
- `test_radar_campaigns_dim_uses_framework_bands` — portfolio ROAS 4.2 → radar dim "Campaigns / ROAS" = 6.5

### Process: same TDD pattern.

### Checkpoint
- 6+ tests passing in `diagnostic-campaigns/tests/`
- Contract validator passes
- Marketing Efficiency composite input (`total_marketing_investment`) present in metrics

---

## Chunk 4: Orchestrator update — parallel dispatch + cross-cutting integration

Update `client-diagnostics/orchestrator/entry.py` to dispatch all 4 sub-skills (parallel where possible), assemble cross-cutting outputs, and run the action-plan with the full integrated context.

### Files
- Modify: `Cowork/Skills/client-diagnostics/orchestrator/entry.py`
- Create: `Cowork/Skills/client-diagnostics/tests/test_smoke_e2e_full.py`

### entry.py changes

Replace the current `_dispatch_topline`-only Phase 2 with a function that dispatches all 4 sub-skills via `concurrent.futures.ThreadPoolExecutor` (subprocess calls are I/O bound — threads work; processes overkill for Wk 2). Each dispatch is independent; parallel safe.

```python
from concurrent.futures import ThreadPoolExecutor

def run(*, client, window_start, window_end, inputs_dir, when=None) -> RunResult:
    when = when or datetime.now()
    layout = output_layout.create_run_dirs(client, when)
    run_id = f"{client}-{when.strftime('%Y-%m-%dT%H:%M:%S')}"
    state = run_state.init(run_id, layout.run_state_path)

    # Phase 2: parallel dispatch
    state = run_state.update(layout.run_state_path, phase=2)
    sub_skills = [
        ("topline", _dispatch_topline),
        ("menu", _dispatch_menu),
        ("ops", _dispatch_ops),
        ("campaigns", _dispatch_campaigns),
    ]
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {
            ex.submit(fn, client=client, window_start=window_start, window_end=window_end,
                      inputs_dir=inputs_dir, output_path=layout.sub_skill_results_path(short))
            : short for short, fn in sub_skills
        }
        statuses = {}
        for fut in futures:
            short = futures[fut]
            try:
                fut.result()
                statuses[f"diagnostic-{short}"] = "ok"
            except Exception:
                statuses[f"diagnostic-{short}"] = "failed"
    state = run_state.update(layout.run_state_path, sub_skill_status=statuses)

    # Phase 3: cross-cutting
    state = run_state.update(layout.run_state_path, phase=3)
    payloads = _load_payloads(layout, statuses)
    for p in payloads.values():
        contract.validate(p)
    radar = cross_cutting.assemble_radar(
        payloads,
        topline_metrics=payloads["topline"]["computed"]["metrics"],
        campaigns_metrics=payloads["campaigns"]["computed"]["metrics"],
    )
    tier_rollup = cross_cutting.rollup_tiers({
        "menu": payloads["menu"]["computed"]["tier_contributions"],
        "ops": payloads["ops"]["computed"]["tier_contributions"],
        "campaigns": payloads["campaigns"]["computed"]["tier_contributions"],
    })
    foundation_gate = cross_cutting.compute_foundation_gate(payloads, statuses)
    wro = cross_cutting.select_win_risk_opp(payloads)
    state = run_state.update(layout.run_state_path, foundation_gate=foundation_gate)

    # Persist cross-cutting outputs
    (layout.root / "cross_cutting" / "radar.json").write_text(json.dumps(radar, indent=2, sort_keys=True))
    (layout.root / "cross_cutting" / "tier_rollup.json").write_text(json.dumps(tier_rollup, indent=2, sort_keys=True))
    (layout.root / "cross_cutting" / "win_risk_opp.json").write_text(json.dumps(wro, indent=2, sort_keys=True))

    # Phase 4: action plan with all findings
    state = run_state.update(layout.run_state_path, phase=4)
    findings = []
    for p in payloads.values():
        findings.extend(p["computed"]["findings"])
    ap_output_path = layout.root / "action-plan" / "diagnostic-action-plan_results.json"
    _dispatch_action_plan(findings, foundation_triggered=foundation_gate["triggered"], output_path=ap_output_path)

    state = run_state.update(layout.run_state_path, phase=5)
    return RunResult(layout=layout, state=state)


def _load_payloads(layout, statuses) -> dict[str, dict]:
    """Load each successful sub-skill's results JSON. Skip failed sub-skills (fail-open per spec)."""
    payloads = {}
    for short in ("topline", "menu", "ops", "campaigns"):
        if statuses.get(f"diagnostic-{short}") == "ok":
            payloads[short] = json.loads(layout.sub_skill_results_path(short).read_text())
    return payloads


def _dispatch_menu(*, client, window_start, window_end, inputs_dir, output_path):
    _dispatch_sub_skill("menu", client=client, window_start=window_start, window_end=window_end,
                        inputs_dir=inputs_dir, output_path=output_path)

def _dispatch_ops(*, client, window_start, window_end, inputs_dir, output_path):
    _dispatch_sub_skill("ops", client=client, window_start=window_start, window_end=window_end,
                        inputs_dir=inputs_dir, output_path=output_path)

def _dispatch_campaigns(*, client, window_start, window_end, inputs_dir, output_path):
    _dispatch_sub_skill("campaigns", client=client, window_start=window_start, window_end=window_end,
                        inputs_dir=inputs_dir, output_path=output_path)

def _dispatch_sub_skill(short: str, *, client, window_start, window_end, inputs_dir, output_path):
    skill_dir = SKILLS_ROOT / f"diagnostic-{short}"
    cmd = [
        str(skill_dir / ".venv" / "bin" / "python"),
        "-m", f"diagnostic_{short}.entry",
        "--client", client,
        "--window-start", window_start,
        "--window-end", window_end,
        "--inputs-dir", str(inputs_dir),
        "--output-path", str(output_path),
    ]
    env = {**os.environ, "PYTHONPATH": str(skill_dir)}
    subprocess.run(cmd, check=True, env=env)
```

(Refactor `_dispatch_topline` to call `_dispatch_sub_skill("topline", ...)` for consistency.)

### test_smoke_e2e_full.py

```python
"""Wk 2 full E2E: 4 parallel sub-skills + cross-cutting + action plan."""
import json
import tempfile
from pathlib import Path
import pandas as pd
from datetime import datetime

from orchestrator import contract, output_layout, entry


def _synth_csv(path: Path):
    """Synthetic CSV with columns each sub-skill needs. Real inputs Wk 3."""
    df = pd.DataFrame({
        "store": ["BeverlyHills", "Venice", "Brentwood"] * 5,
        "week": list(range(1, 6)) * 3,
        # topline cols
        "gross_sales": [12000, 9000, 7000] * 5,
        "orders": [240, 180, 140] * 5,
        "net_payout": [8000, 6000, 4500] * 5,
        # menu cols
        "menu_cvr_pct": [22.0, 14.0, 19.0] * 5,
        "photo_coverage_pct": [85, 35, 70] * 5,
        "hero_set": [True, True, True] * 5,
        "categories_count": [6, 6, 6] * 5,
        "categories_populated": [6, 5, 6] * 5,
        "storefront_to_menu_ctr_pct": [10.0, 11.0, 8.0] * 5,
        # ops cols
        "rating": [4.6, 4.0, 4.3] * 5,
        "error_rate_pct": [1.5, 6.0, 3.0] * 5,
        "cancellation_pct": [1.0, 4.0, 2.5] * 5,
        "uptime_pct": [98.0, 88.0, 95.0] * 5,
        "hours_accurate": [True, False, True] * 5,
        # campaigns cols
        "platform": ["UE", "DD", "GH"] * 5,
        "spend": [600, 400, 200] * 5,
        "attributed_sales": [3000, 800, 1000] * 5,
        "roas": [5.0, 2.0, 5.0] * 5,
        "incremental_orders_per_week": [15, 5, 8] * 5,
        "promo_count_active": [2, 4, 1] * 5,
    })
    df.to_csv(path, index=False)


def test_full_run_dispatches_all_4_sub_skills(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(output_layout, "RUN_ROOT", Path(tmp) / "runs")
        inputs = Path(tmp) / "inputs"
        inputs.mkdir()
        _synth_csv(inputs / "synth.csv")

        result = entry.run(
            client="test-client",
            window_start="2026-02-08", window_end="2026-05-08",
            inputs_dir=inputs, when=datetime(2026, 5, 8, 14, 30, 0),
        )

        for short in ("topline", "menu", "ops", "campaigns"):
            payload = json.loads(result.layout.sub_skill_results_path(short).read_text())
            contract.validate(payload)
            assert payload["sub_skill"] == f"diagnostic-{short}"

        state = json.loads(result.layout.run_state_path.read_text())
        for sub in ("diagnostic-topline", "diagnostic-menu", "diagnostic-ops", "diagnostic-campaigns"):
            assert state["sub_skill_status"][sub] == "ok"


def test_full_run_assembles_cross_cutting(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(output_layout, "RUN_ROOT", Path(tmp) / "runs")
        inputs = Path(tmp) / "inputs"
        inputs.mkdir()
        _synth_csv(inputs / "synth.csv")

        result = entry.run(client="t", window_start="2026-02-08", window_end="2026-05-08",
                           inputs_dir=inputs, when=datetime(2026, 5, 8, 14, 30, 0))

        radar = json.loads((result.layout.root / "cross_cutting" / "radar.json").read_text())
        for dim in ("AOV", "Re-order Rate", "Conversion", "Traffic", "Marketing Efficiency", "Operations", "Campaigns / ROAS"):
            assert dim in radar
            assert isinstance(radar[dim], (int, float))

        tier = json.loads((result.layout.root / "cross_cutting" / "tier_rollup.json").read_text())
        assert "Venice" in tier
        # Venice has 35% photo coverage → menu="red", and ops 88% uptime → ops="red"; rollup should be red
        assert tier["Venice"]["flag"] == "red"


def test_full_run_foundation_gate_triggered_by_low_rating_and_low_photos(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(output_layout, "RUN_ROOT", Path(tmp) / "runs")
        inputs = Path(tmp) / "inputs"
        inputs.mkdir()
        _synth_csv(inputs / "synth.csv")

        result = entry.run(client="t", window_start="2026-02-08", window_end="2026-05-08",
                           inputs_dir=inputs, when=datetime(2026, 5, 8, 14, 30, 0))

        state = json.loads(result.layout.run_state_path.read_text())
        # rating min in synth = 4.0 (Venice) → triggers low_rating_below_42 (ops sub-skill)
        # photo_coverage 35% (Venice) → triggers low_photo_coverage (menu sub-skill)
        # Either triggers foundation gate via thresholds (rating < 4.2, photo_coverage < 50)
        assert state["foundation_gate"]["triggered"] is True

        # Action plan should be foundation-only
        ap = json.loads((result.layout.root / "action-plan" / "diagnostic-action-plan_results.json").read_text())
        # All P1 items are foundation severity
        assert all(it["severity"] == "foundation" for it in ap["kanban"]["P1_this_week"])
```

### TDD discipline

1. Write the 3 tests in `test_smoke_e2e_full.py`
2. Run, expect failure (`_dispatch_menu` etc. not defined)
3. Implement entry.py changes
4. Run, expect pass

### Checkpoint

- 3 new tests in `test_smoke_e2e_full.py` all pass
- Existing 29 tests in `client-diagnostics/tests/` all still pass
- Existing 3 + 4 + 6 + 6 + 6 = 25 tests in sub-skill test suites all pass
- **Grand total expected: 60 passing tests** (29 client-diagnostics + 3 topline + 6 menu + 6 ops + 6 campaigns + 4 action-plan + 6 from new sub-skill tests already counted... let me recount: 29 + 3 + 4 + 6 + 6 + 6 + 3 = 57)

Total: **57 passing tests across 6 skill folders** (or 5 if optimized-menu-sheet is just a contract file).

---

## Chunk 5: Wk 2 verification + deploy

### Verification

```bash
echo "=== client-diagnostics (29 + 3 new = 32 expected) ==="
cd /Users/maxx/Desktop/Cowork/Skills/client-diagnostics && .venv/bin/pytest tests/ -q 2>&1 | tail -2
echo "=== diagnostic-topline (3) ==="
cd /Users/maxx/Desktop/Cowork/Skills/diagnostic-topline && .venv/bin/pytest tests/ -q 2>&1 | tail -2
echo "=== diagnostic-menu (6+) ==="
cd /Users/maxx/Desktop/Cowork/Skills/diagnostic-menu && .venv/bin/pytest tests/ -q 2>&1 | tail -2
echo "=== diagnostic-ops (6+) ==="
cd /Users/maxx/Desktop/Cowork/Skills/diagnostic-ops && .venv/bin/pytest tests/ -q 2>&1 | tail -2
echo "=== diagnostic-campaigns (6+) ==="
cd /Users/maxx/Desktop/Cowork/Skills/diagnostic-campaigns && .venv/bin/pytest tests/ -q 2>&1 | tail -2
echo "=== diagnostic-action-plan (4) ==="
cd /Users/maxx/Desktop/Cowork/Skills/diagnostic-action-plan && .venv/bin/pytest tests/ -q 2>&1 | tail -2
```

### Deploy

```bash
for skill in client-diagnostics diagnostic-topline diagnostic-menu diagnostic-ops diagnostic-campaigns diagnostic-action-plan optimized-menu-sheet; do
  rsync -a --delete \
    --exclude='.venv' --exclude='__pycache__' --exclude='.pytest_cache' --exclude='*.pyc' \
    "/Users/maxx/Desktop/Cowork/Skills/$skill/" \
    "/Users/maxx/Desktop/spice-team-skills/skills/$skill/"
done
```

### Checkpoint

- All 57+ tests pass
- 6 skill folders deployed to team-skills
- spice-team-skills/skills/ should now have 24 skill folders (17 prior + 7 from this build)

---

## Critical Files

- This plan: `plans/2026-05-08-orchestrator-wk2-plan.md`
- Spec: `specs/2026-05-08-orchestrator-redesign.md`
- Wk 1 plan (reference for sub-skill structure): `plans/2026-05-08-orchestrator-wk1-plan.md`
- Source of truth for sub-skill compute logic: `references/diagnostic-framework.md`
- Reference implementation: `Cowork/Skills/diagnostic-topline/` (mirror for new sub-skills)
