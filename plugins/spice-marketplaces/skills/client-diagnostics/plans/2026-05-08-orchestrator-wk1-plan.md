# Diagnostics Orchestrator Wk 1 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the orchestrator skeleton + `diagnostic-topline` sub-skill + `diagnostic-action-plan` stub. Validates the producer→consumer contract end-to-end against synthetic data.

**Architecture:** Orchestrator-as-skill at `Cowork/Skills/client-diagnostics/` re-architected from monolithic to dispatcher. Two new sub-skill folders. Shared Python module `orchestrator/` for run-state, contract, cross-cutting computation, and Notion assembly. TDD throughout for Python; verification steps for SKILL.md.

**Tech Stack:** Python 3.11+, pytest, jsonschema, pandas, matplotlib. Skills are Markdown + Python. Pre-existing convention: skill folders are hyphen-named (`diagnostic-topline`). New conventions introduced here:
- Each skill carries an underscore-named Python *package* inside (e.g. `Cowork/Skills/diagnostic-topline/diagnostic_topline/`) — Python can't import hyphens.
- Each skill has a `pyproject.toml` at its root configuring pytest's `pythonpath` so test imports just work.
- Each skill has a `tests/` directory.

**Spec:** `/Users/maxx/Desktop/Cowork/Skills/client-diagnostics/specs/2026-05-08-orchestrator-redesign.md`

**Note on git:** `/Users/maxx/Desktop/Cowork/` is not under git and there's no parent repo. This plan does NOT include git operations. Maxx wraps Wk 1 work via the existing Spice deployment process (copy-to-plugin) at the end. Each task ends with a **Checkpoint** instead of a commit — verify state, then continue.

---

## CRITICAL: Existing Assets to Honor

**Do not delete, overwrite, or rewrite these files. They contain real institutional knowledge.**

| Existing asset | Wk 1 treatment |
|---|---|
| `Cowork/Skills/client-diagnostics/references/diagnostic-framework.md` (210 lines: 7-dim radar scoring bands, foundation gate thresholds, cuisine CVR benchmarks, location tier strategy + rollup rules + edge cases, 6 diagnostic patterns, 8-chart library spec w/ Spice palette) | **Preserve in place.** Task 4.3 extracts ONLY the Location Tier Strategy section (lines ~71–112) into the new `cross-cutting-patterns.md`. Adds a deprecation banner to the framework but does NOT remove content. Wk 2 redistributes the rest per sub-skill. |
| `Cowork/Skills/client-diagnostics/references/generate_diagnostic_charts.py` (16.6 KB, 8 chart functions for the v0.2 Notion output, with the SPICE_PALETTE constant) | **Preserve in place.** Wk 2 refactors as orchestrator's `chart_helpers.py`; Wk 1 leaves it alone. The orchestrator package's `chart_helpers.py` is NOT created in Wk 1 (deferred to Wk 2). |
| `Cowork/Skills/client-diagnostics/SKILL.md` (v0.2 monolith) | Task 4.2 replaces with the orchestrator dispatcher version. Original v0.2 content is captured in spec + framework references — safe to replace. |

**Existing downstream skills the action plan will eventually trigger (Wk 3-4 wire-up):**

| Skill | Location | Wk 1 treatment |
|---|---|---|
| `optimized-menu-sheet` | **Not on this machine.** Listed in session-start skill list but no SKILL.md found in any plugin marketplace, source repo, or Cowork. | Wk 1 creates a *placeholder* `deliverable_contract.json` at `Cowork/Skills/optimized-menu-sheet/`. The contract is reconciled in Wk 3-4 when the real skill becomes available. |
| `hero-image-review` | `/Users/maxx/Desktop/spice-team-skills/skills/hero-image-review/` AND `Cowork/Skills/hero-image-review/` | No Wk 1 work. Noted for Wk 3-4 wire-up. |
| `ratings-flyer` | `/Users/maxx/Desktop/spice-team-skills/skills/ratings-flyer/` | No Wk 1 work. Noted for Wk 3-4 wire-up. |
| `leaderboard-update` | `/Users/maxx/Documents/Claude/Projects/Everytable/leaderboard-update-skill/` (Everytable-only today) | No Wk 1 work; productized in slot-3 plan separately. |
| `campaign-plan` | Does not exist. Slot 4 of umbrella plan. | No Wk 1 work. |

**Spice deployment topology discovered during audit:** the canonical deployable source for spice-team-skills lives at `/Users/maxx/Desktop/spice-team-skills/skills/`. After Wk 1 tests pass, copy the new skill folders (`client-diagnostics/`, `diagnostic-topline/`, `diagnostic-action-plan/`) into that source repo for plugin redeployment. **NOT a Wk 1 build task** — Maxx triggers manually post-verification.

---

## File Structure

| Action | Path | Responsibility |
|---|---|---|
| Modify | `Cowork/Skills/client-diagnostics/SKILL.md` | Becomes orchestrator (dispatcher, not monolith) |
| Create | `Cowork/Skills/client-diagnostics/pyproject.toml` | pytest pythonpath config |
| Create | `Cowork/Skills/client-diagnostics/orchestrator/__init__.py` | Package marker |
| Create | `Cowork/Skills/client-diagnostics/orchestrator/run_state.py` | Atomic JSON I/O for `run_state.json` |
| Create | `Cowork/Skills/client-diagnostics/orchestrator/output_layout.py` | Path resolution + dir creation per Contracts §"Run-state + output layout" |
| Create | `Cowork/Skills/client-diagnostics/orchestrator/contract.py` | JSON schema for sub-skill output + validator + computed-layer hash |
| Create | `Cowork/Skills/client-diagnostics/orchestrator/cross_cutting.py` | Radar composite, tier rollup, W/R/O dedup, foundation gate |
| Create | `Cowork/Skills/client-diagnostics/orchestrator/entry.py` | Orchestrator main entry point |
| Create | `Cowork/Skills/client-diagnostics/tests/test_run_state.py` | |
| Create | `Cowork/Skills/client-diagnostics/tests/test_output_layout.py` | |
| Create | `Cowork/Skills/client-diagnostics/tests/test_contract.py` | |
| Create | `Cowork/Skills/client-diagnostics/tests/test_cross_cutting.py` | |
| Create | `Cowork/Skills/client-diagnostics/tests/test_smoke_e2e.py` | End-to-end with synthetic data |
| Create | `Cowork/Skills/client-diagnostics/references/cross-cutting-patterns.md` | Patterns moved out of monolithic framework |
| Modify | `Cowork/Skills/client-diagnostics/references/diagnostic-framework.md` | Trim cross-cutting content (moved to above) |
| Create | `Cowork/Skills/client-diagnostics/requirements-dev.txt` | pytest, jsonschema, pandas, matplotlib (dev-only deps) |
| Create | `Cowork/Skills/diagnostic-topline/SKILL.md` | Sub-skill SKILL.md |
| Create | `Cowork/Skills/diagnostic-topline/pyproject.toml` | pytest pythonpath config |
| Create | `Cowork/Skills/diagnostic-topline/diagnostic_topline/__init__.py` | Python package marker (underscore name) |
| Create | `Cowork/Skills/diagnostic-topline/diagnostic_topline/compute.py` | Computes metrics, radar dims, tier contributions, findings |
| Create | `Cowork/Skills/diagnostic-topline/diagnostic_topline/entry.py` | Sub-skill main entry — orchestrator dispatches this |
| Create | `Cowork/Skills/diagnostic-topline/references/patterns-topline.md` | Topline pattern library |
| Create | `Cowork/Skills/diagnostic-topline/tests/test_compute.py` | |
| Create | `Cowork/Skills/diagnostic-action-plan/SKILL.md` | Stub sub-skill SKILL.md |
| Create | `Cowork/Skills/diagnostic-action-plan/pyproject.toml` | pytest pythonpath config |
| Create | `Cowork/Skills/diagnostic-action-plan/diagnostic_action_plan/__init__.py` | Python package marker |
| Create | `Cowork/Skills/diagnostic-action-plan/diagnostic_action_plan/entry.py` | Stub: consumes 1 finding, emits kanban card |
| Create | `Cowork/Skills/diagnostic-action-plan/tests/test_entry.py` | |
| Create | `Cowork/Skills/optimized-menu-sheet/deliverable_contract.json` | One example downstream contract (folder is being newly created) |

**Skill ↔ Python package naming convention:** the skill folder is hyphenated (Spice convention); the Python package inside is the same name with underscores. Tests at `<skill>/tests/` import the package; `pyproject.toml` puts the skill root on `pythonpath`.

---

## Chunk 1: Foundation Python module (run-state, output layout, contract)

This chunk builds the Python infrastructure every other chunk depends on. Pure functions where possible. Self-contained, fast tests.

### Task 1.1: Set up venv + dev deps + pyproject.toml

**Files:**
- Create: `Cowork/Skills/client-diagnostics/requirements-dev.txt`
- Create: `Cowork/Skills/client-diagnostics/pyproject.toml`

- [ ] **Step 1: Write `requirements-dev.txt`:**

```
pytest>=8.0
jsonschema>=4.20
pandas>=2.1
matplotlib>=3.8
```

- [ ] **Step 2: Write `pyproject.toml`** so pytest finds the orchestrator package without sys.path hacks:

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

- [ ] **Step 3: Create venv + install:**

```bash
cd /Users/maxx/Desktop/Cowork/Skills/client-diagnostics
python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest --version
```

Expected: `pytest 8.x.x` printed.

- [ ] **Checkpoint:** confirm `.venv/bin/pytest` runs and prints version.

---

### Task 1.2: `output_layout.py` — path resolution + dir creation

Implements Contracts §"Run-state + output layout". Pure functions; only side effect is `mkdir -p`.

**Files:**
- Create: `Cowork/Skills/client-diagnostics/orchestrator/__init__.py` (empty)
- Create: `Cowork/Skills/client-diagnostics/orchestrator/output_layout.py`
- Create: `Cowork/Skills/client-diagnostics/tests/__init__.py` (empty)
- Create: `Cowork/Skills/client-diagnostics/tests/test_output_layout.py`

- [ ] **Step 1: Write the failing test** (`tests/test_output_layout.py`):

```python
from datetime import datetime
from pathlib import Path
import tempfile
from orchestrator import output_layout


def test_run_dir_layout(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(output_layout, "RUN_ROOT", Path(tmp))
        ts = datetime(2026, 5, 8, 14, 30, 0)
        layout = output_layout.create_run_dirs("goop-kitchen", ts)

        assert layout.root == Path(tmp) / "goop-kitchen" / "2026-05-08T14:30:00"
        assert (layout.root / "inputs").is_dir()
        assert (layout.root / "topline" / "charts").is_dir()
        assert (layout.root / "menu" / "charts").is_dir()
        assert (layout.root / "ops" / "charts").is_dir()
        assert (layout.root / "campaigns" / "charts").is_dir()
        assert (layout.root / "cross_cutting").is_dir()
        assert (layout.root / "action-plan").is_dir()
        assert layout.run_state_path == layout.root / "run_state.json"
        assert layout.sub_skill_results_path("topline") == layout.root / "topline" / "diagnostic-topline_results.json"


def test_archive_dir_per_client(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(output_layout, "RUN_ROOT", Path(tmp))
        archive = output_layout.archive_dir("goop-kitchen")
        assert archive == Path(tmp) / "goop-kitchen" / "_archive"
        assert archive.is_dir()


def test_create_run_dirs_idempotent(monkeypatch):
    """Calling twice with same timestamp doesn't error."""
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(output_layout, "RUN_ROOT", Path(tmp))
        ts = datetime(2026, 5, 8, 14, 30, 0)
        layout1 = output_layout.create_run_dirs("c", ts)
        layout2 = output_layout.create_run_dirs("c", ts)
        assert layout1.root == layout2.root


def test_sub_skill_results_path_for_each_known_sub_skill(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(output_layout, "RUN_ROOT", Path(tmp))
        layout = output_layout.create_run_dirs("c", datetime(2026, 5, 8))
        for sub in ("topline", "menu", "ops", "campaigns"):
            p = layout.sub_skill_results_path(sub)
            assert p.parent == layout.root / sub
            assert p.name == f"diagnostic-{sub}_results.json"
```

- [ ] **Step 2: Run, verify failure:**

```bash
cd /Users/maxx/Desktop/Cowork/Skills/client-diagnostics
.venv/bin/pytest tests/test_output_layout.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'orchestrator'`.

- [ ] **Step 3: Write minimal implementation** (`orchestrator/__init__.py` empty + `orchestrator/output_layout.py`):

```python
"""Resolve and create run-time output paths per spec §Contracts."""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

RUN_ROOT = Path("/tmp/diagnostic-runs")
SUB_SKILLS = ("topline", "menu", "ops", "campaigns")


@dataclass(frozen=True)
class RunLayout:
    root: Path
    run_state_path: Path

    def sub_skill_results_path(self, sub_skill: str) -> Path:
        return self.root / sub_skill / f"diagnostic-{sub_skill}_results.json"


def create_run_dirs(client_slug: str, when: datetime) -> RunLayout:
    ts = when.strftime("%Y-%m-%dT%H:%M:%S")
    root = RUN_ROOT / client_slug / ts
    for sub in SUB_SKILLS:
        (root / sub / "charts").mkdir(parents=True, exist_ok=True)
    (root / "inputs").mkdir(parents=True, exist_ok=True)
    (root / "cross_cutting").mkdir(parents=True, exist_ok=True)
    (root / "action-plan").mkdir(parents=True, exist_ok=True)
    return RunLayout(root=root, run_state_path=root / "run_state.json")


def archive_dir(client_slug: str) -> Path:
    d = RUN_ROOT / client_slug / "_archive"
    d.mkdir(parents=True, exist_ok=True)
    return d
```

- [ ] **Step 4: Run, verify pass:**

```bash
.venv/bin/pytest tests/test_output_layout.py -v
```

Expected: 4 passed.

- [ ] **Checkpoint:** all 4 output_layout tests pass.

---

### Task 1.3: `run_state.py` — atomic JSON I/O for shared run state

Implements `run_state.json` schema from Contracts. Atomic writes via temp-file + rename.

**Files:**
- Create: `Cowork/Skills/client-diagnostics/orchestrator/run_state.py`
- Create: `Cowork/Skills/client-diagnostics/tests/test_run_state.py`

- [ ] **Step 1: Write the failing test:**

```python
import json
import tempfile
from pathlib import Path
from orchestrator import run_state


def test_initial_state_shape():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "run_state.json"
        state = run_state.init("goop-kitchen-2026-05-08T14:30:00", path)
        assert state["run_id"] == "goop-kitchen-2026-05-08T14:30:00"
        assert state["phase"] == 1
        assert state["sub_skill_status"] == {
            "diagnostic-topline": "pending",
            "diagnostic-menu": "pending",
            "diagnostic-ops": "pending",
            "diagnostic-campaigns": "pending",
        }
        assert state["foundation_gate"] is None
        assert state["prior_run_id"] is None
        assert path.exists()
        assert json.loads(path.read_text())["run_id"] == state["run_id"]


def test_update_is_atomic_no_partial_writes():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "run_state.json"
        run_state.init("rid", path)
        run_state.update(path, sub_skill_status={"diagnostic-topline": "ok"})
        loaded = json.loads(path.read_text())
        assert loaded["sub_skill_status"]["diagnostic-topline"] == "ok"
        assert loaded["sub_skill_status"]["diagnostic-menu"] == "pending"  # not clobbered
        assert not list(path.parent.glob("*.tmp")), "temp file leaked"


def test_set_foundation_gate_and_phase():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "run_state.json"
        run_state.init("rid", path)
        run_state.update(path, phase=3, foundation_gate={"triggered": True, "triggers": [], "override_action_plan": True})
        loaded = json.loads(path.read_text())
        assert loaded["phase"] == 3
        assert loaded["foundation_gate"]["triggered"] is True
```

- [ ] **Step 2: Run, verify failure:**

```bash
.venv/bin/pytest tests/test_run_state.py -v
```

Expected: FAIL with `ModuleNotFoundError: orchestrator.run_state`.

- [ ] **Step 3: Write minimal implementation:**

```python
"""Atomic shared run-state I/O. Orchestrator-only writer."""
import json
import os
from pathlib import Path
from typing import Any

SUB_SKILLS = ("diagnostic-topline", "diagnostic-menu", "diagnostic-ops", "diagnostic-campaigns")


def init(run_id: str, path: Path, prior_run_id: str | None = None) -> dict[str, Any]:
    state = {
        "run_id": run_id,
        "phase": 1,
        "sub_skill_status": {s: "pending" for s in SUB_SKILLS},
        "foundation_gate": None,
        "prior_run_id": prior_run_id,
    }
    _atomic_write(path, state)
    return state


def update(path: Path, **fields) -> dict[str, Any]:
    state = json.loads(path.read_text())
    if "sub_skill_status" in fields:
        state["sub_skill_status"].update(fields.pop("sub_skill_status"))
    state.update(fields)
    _atomic_write(path, state)
    return state


def _atomic_write(path: Path, state: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True))
    os.replace(tmp, path)
```

- [ ] **Step 4: Run, verify pass:**

```bash
.venv/bin/pytest tests/test_run_state.py -v
```

Expected: 3 passed.

- [ ] **Checkpoint:** all 3 run_state tests pass.

---

### Task 1.4: `contract.py` — sub-skill output schema, validator, computed-layer hash

Single source of truth for the sub-skill output contract. Used by sub-skill emit, orchestrator consume, and verification.

**Files:**
- Create: `Cowork/Skills/client-diagnostics/orchestrator/contract.py`
- Create: `Cowork/Skills/client-diagnostics/tests/test_contract.py`

- [ ] **Step 1: Write the failing test:**

```python
import pytest
from orchestrator import contract


def _valid_payload(sub_skill: str = "diagnostic-topline") -> dict:
    return {
        "sub_skill": sub_skill,
        "version": "1.0",
        "client": "goop-kitchen",
        "window": {"start": "2026-02-08", "end": "2026-05-08"},
        "computed": {
            "metrics": {"gross_sales": 1500000},
            "radar_contributions": {"AOV": 7.2, "Re-order Rate": 6.1},
            "tier_contributions": {
                "BeverlyHills": {"score": 8.0, "flag": "green", "reasons": ["high CVR"]}
            },
            "findings": [
                {
                    "pattern_id": "revenue_down_traffic_stable",
                    "severity": "high",
                    "scope": "BeverlyHills",
                    "evidence": {"weeks": 4, "delta_pct": -12.5},
                    "estimated_impact_usd": 12000,
                    "deliverable_trigger": {"skill": "optimized-menu-sheet", "params": {"stores": ["BeverlyHills"]}},
                }
            ],
            "charts": [{"id": "sparklines", "path": "topline/charts/sparklines.png"}],
        },
        "drafted": {
            "toggle_title": "Top-line Performance",
            "toggle_prose": "...",
            "win_risk_opp_candidates": [
                {"type": "risk", "headline": "BH revenue down 12%", "value_usd": 12000, "pattern_id": "revenue_down_traffic_stable"}
            ],
        },
        "data_quality": {"completeness": 0.95, "gaps": []},
    }


def test_valid_payload_passes_validator():
    contract.validate(_valid_payload())


def test_missing_required_field_fails():
    p = _valid_payload()
    del p["computed"]["radar_contributions"]
    with pytest.raises(contract.ContractError):
        contract.validate(p)


def test_invalid_severity_fails():
    p = _valid_payload()
    p["computed"]["findings"][0]["severity"] = "critical"  # not in enum
    with pytest.raises(contract.ContractError):
        contract.validate(p)


def test_invalid_wro_type_fails():
    p = _valid_payload()
    p["drafted"]["win_risk_opp_candidates"][0]["type"] = "celebration"  # not in enum
    with pytest.raises(contract.ContractError):
        contract.validate(p)


def test_computed_hash_is_stable_across_drafted_changes():
    p1 = _valid_payload()
    p2 = _valid_payload()
    p2["drafted"]["toggle_prose"] = "totally different prose"
    p2["data_quality"]["completeness"] = 0.7
    assert contract.computed_hash(p1) == contract.computed_hash(p2)


def test_computed_hash_excludes_chart_paths():
    p1 = _valid_payload()
    p2 = _valid_payload()
    p2["computed"]["charts"][0]["path"] = "topline/charts/sparklines-DIFFERENT.png"
    assert contract.computed_hash(p1) == contract.computed_hash(p2)


def test_computed_hash_excludes_evidence():
    p1 = _valid_payload()
    p2 = _valid_payload()
    p2["computed"]["findings"][0]["evidence"] = {"foo": "bar", "ts": "2026-05-08T14:30:00"}
    assert contract.computed_hash(p1) == contract.computed_hash(p2)


def test_computed_hash_changes_when_metric_changes():
    p1 = _valid_payload()
    p2 = _valid_payload()
    p2["computed"]["metrics"]["gross_sales"] = 1600000
    assert contract.computed_hash(p1) != contract.computed_hash(p2)
```

- [ ] **Step 2: Run, verify failure:**

```bash
.venv/bin/pytest tests/test_contract.py -v
```

- [ ] **Step 3: Write minimal implementation:**

```python
"""Sub-skill output contract — JSON schema + validator + computed-layer hash."""
import hashlib
import json
import jsonschema

SCHEMA = {
    "type": "object",
    "required": ["sub_skill", "version", "client", "window", "computed", "drafted", "data_quality"],
    "properties": {
        "sub_skill": {"type": "string"},
        "version": {"type": "string"},
        "client": {"type": "string"},
        "window": {
            "type": "object",
            "required": ["start", "end"],
            "properties": {"start": {"type": "string"}, "end": {"type": "string"}},
        },
        "computed": {
            "type": "object",
            "required": ["metrics", "radar_contributions", "tier_contributions", "findings", "charts"],
            "properties": {
                "metrics": {"type": "object"},
                "radar_contributions": {"type": "object", "additionalProperties": {"type": "number"}},
                "tier_contributions": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "required": ["score", "flag", "reasons"],
                        "properties": {
                            "score": {"type": "number"},
                            "flag": {"enum": ["green", "yellow", "red", "new"]},
                            "reasons": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
                "findings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["pattern_id", "severity", "scope", "evidence", "estimated_impact_usd", "deliverable_trigger"],
                        "properties": {
                            "pattern_id": {"type": "string"},
                            "severity": {"enum": ["low", "medium", "high", "foundation"]},
                            "scope": {"type": "string"},
                            "evidence": {"type": "object"},
                            "estimated_impact_usd": {"type": ["number", "null"]},
                            "deliverable_trigger": {
                                "type": "object",
                                "required": ["skill", "params"],
                                "properties": {"skill": {"type": "string"}, "params": {"type": "object"}},
                            },
                        },
                    },
                },
                "charts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id", "path"],
                        "properties": {"id": {"type": "string"}, "path": {"type": "string"}},
                    },
                },
            },
        },
        "drafted": {
            "type": "object",
            "required": ["toggle_title", "toggle_prose", "win_risk_opp_candidates"],
            "properties": {
                "toggle_title": {"type": "string"},
                "toggle_prose": {"type": "string"},
                "win_risk_opp_candidates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["type", "headline"],
                        "properties": {
                            "type": {"enum": ["win", "risk", "opportunity"]},
                            "headline": {"type": "string"},
                            "value_usd": {"type": ["number", "null"]},
                            "pattern_id": {"type": "string"},  # optional, used for cross-sub-skill dedup
                            "severity": {"enum": ["low", "medium", "high", "foundation"]},
                        },
                    },
                },
            },
        },
        "data_quality": {
            "type": "object",
            "required": ["completeness", "gaps"],
            "properties": {
                "completeness": {"type": "number"},
                "gaps": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
}


class ContractError(Exception):
    pass


def validate(payload: dict) -> None:
    try:
        jsonschema.validate(payload, SCHEMA)
    except jsonschema.ValidationError as e:
        raise ContractError(str(e)) from e


def computed_hash(payload: dict) -> str:
    """Hash only the deterministic subset per spec §Verification.

    Excludes: charts[].path, findings[].evidence, drafted, data_quality.
    Includes: metrics, radar_contributions, tier_contributions,
              findings[].{pattern_id, severity, scope, estimated_impact_usd}.
    """
    c = payload["computed"]
    deterministic = {
        "metrics": c["metrics"],
        "radar_contributions": c["radar_contributions"],
        "tier_contributions": c["tier_contributions"],
        "findings": [
            {
                "pattern_id": f["pattern_id"],
                "severity": f["severity"],
                "scope": f["scope"],
                "estimated_impact_usd": f["estimated_impact_usd"],
            }
            for f in c["findings"]
        ],
    }
    serialized = json.dumps(deterministic, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode()).hexdigest()
```

- [ ] **Step 4: Run, verify pass:**

```bash
.venv/bin/pytest tests/test_contract.py -v
```

Expected: 8 passed.

- [ ] **Checkpoint:** all 8 contract tests pass.

---

## Chunk 2: Cross-cutting computation (radar, tier, W/R/O, foundation gate)

Pure functions consuming validated sub-skill payloads. No I/O. Most logic-dense module — keep tests thorough.

### Task 2.1: Radar composite + tier rollup

**Files:**
- Create: `Cowork/Skills/client-diagnostics/orchestrator/cross_cutting.py`
- Create: `Cowork/Skills/client-diagnostics/tests/test_cross_cutting.py`

- [ ] **Step 1: Write failing tests for radar + tier:**

```python
import pytest
from orchestrator import cross_cutting as xc


def _payload(sub_skill, radar=None, tier=None, findings=None, w_r_o=None, metrics=None):
    return {
        "sub_skill": sub_skill,
        "computed": {
            "metrics": metrics or {},
            "radar_contributions": radar or {},
            "tier_contributions": tier or {},
            "findings": findings or [],
            "charts": [],
        },
        "drafted": {"toggle_title": "", "toggle_prose": "", "win_risk_opp_candidates": w_r_o or []},
        "data_quality": {"completeness": 1.0, "gaps": []},
    }


def test_radar_assembly_uses_owners_per_spec():
    payloads = {
        "topline": _payload("diagnostic-topline", radar={"AOV": 7.2, "Re-order Rate": 6.1}),
        "menu": _payload("diagnostic-menu", radar={"Conversion": 5.5, "Traffic": 6.8}),
        "ops": _payload("diagnostic-ops", tier={
            "Store1": {"score": 9, "flag": "green", "reasons": []},
            "Store2": {"score": 4, "flag": "red", "reasons": []},
            "Store3": {"score": 7, "flag": "green", "reasons": []},
        }),
        "campaigns": _payload("diagnostic-campaigns", radar={"Campaigns / ROAS": 4.2}),
    }
    radar = xc.assemble_radar(payloads, topline_metrics={"gross_sales": 1_000_000}, campaigns_metrics={"total_marketing_investment": 200_000})

    assert radar["AOV"] == 7.2
    assert radar["Re-order Rate"] == 6.1
    assert radar["Conversion"] == 5.5
    assert radar["Traffic"] == 6.8
    assert radar["Campaigns / ROAS"] == 4.2
    # Marketing Efficiency = 1 - (mkt / gross), benchmarked vs 30%, scaled 1-10
    assert 0 <= radar["Marketing Efficiency"] <= 10
    # Operations: 2 of 3 not red = 66.7% → ~6.7
    assert 6.0 <= radar["Operations"] <= 7.5


def test_tier_rollup_red_wins():
    contribs = {
        "menu":  {"Store1": {"score": 8, "flag": "green",  "reasons": []}},
        "ops":   {"Store1": {"score": 4, "flag": "red",    "reasons": []}},
        "campaigns": {"Store1": {"score": 6, "flag": "yellow", "reasons": []}},
    }
    rollup = xc.rollup_tiers(contribs)
    assert rollup["Store1"]["flag"] == "red"
    assert rollup["Store1"]["worst_bucket"] == "ops"


def test_tier_rollup_yellow_when_no_red():
    contribs = {
        "menu":  {"Store1": {"score": 8, "flag": "green",  "reasons": []}},
        "ops":   {"Store1": {"score": 6, "flag": "yellow", "reasons": []}},
        "campaigns": {"Store1": {"score": 7, "flag": "green",  "reasons": []}},
    }
    rollup = xc.rollup_tiers(contribs)
    assert rollup["Store1"]["flag"] == "yellow"


def test_tier_rollup_new_when_any_bucket_new():
    contribs = {
        "menu":  {"Store1": {"score": 8, "flag": "green", "reasons": []}},
        "ops":   {"Store1": {"score": 0, "flag": "new",   "reasons": []}},
        "campaigns": {"Store1": {"score": 7, "flag": "green", "reasons": []}},
    }
    rollup = xc.rollup_tiers(contribs)
    assert rollup["Store1"]["flag"] == "new"


def test_tier_rollup_all_green():
    contribs = {
        "menu":  {"Store1": {"score": 8, "flag": "green", "reasons": []}},
        "ops":   {"Store1": {"score": 9, "flag": "green", "reasons": []}},
        "campaigns": {"Store1": {"score": 7, "flag": "green", "reasons": []}},
    }
    rollup = xc.rollup_tiers(contribs)
    assert rollup["Store1"]["flag"] == "green"
```

- [ ] **Step 2: Run, verify failure.**

```bash
.venv/bin/pytest tests/test_cross_cutting.py -v
```

- [ ] **Step 3: Implement:**

```python
"""Cross-cutting Phase 3 computation: radar composite, tier rollup, W/R/O dedup, foundation gate."""

PRIMARY_OWNED_DIMS = {
    "AOV": "topline",
    "Re-order Rate": "topline",
    "Conversion": "menu",
    "Traffic": "menu",
    "Campaigns / ROAS": "campaigns",
}
SUB_SKILL_PRIORITY = ("ops", "menu", "campaigns", "topline")
FLAG_RANK = {"red": 3, "yellow": 2, "green": 1, "new": 0}


def assemble_radar(payloads: dict[str, dict], *, topline_metrics: dict, campaigns_metrics: dict) -> dict[str, float]:
    radar: dict[str, float] = {}
    for dim, owner in PRIMARY_OWNED_DIMS.items():
        radar[dim] = payloads[owner]["computed"]["radar_contributions"].get(dim, 0.0)

    # Composite: Marketing Efficiency = 1 - (mkt / gross), benchmarked vs 30%, scaled 1-10
    gross = float(topline_metrics.get("gross_sales", 0))
    mkt = float(campaigns_metrics.get("total_marketing_investment", 0))
    if gross > 0:
        mkt_ratio = mkt / gross
        # 0% mkt = 10; 30% mkt = 5 (benchmark); 60%+ mkt = 1
        radar["Marketing Efficiency"] = max(1.0, min(10.0, 10.0 - (mkt_ratio / 0.06)))
    else:
        radar["Marketing Efficiency"] = 0.0

    # Composite: Operations = pct stores not flagged red, scaled 1-10
    ops_tiers = payloads["ops"]["computed"]["tier_contributions"]
    if ops_tiers:
        non_red = sum(1 for t in ops_tiers.values() if t["flag"] != "red")
        pct = non_red / len(ops_tiers)
        radar["Operations"] = max(1.0, min(10.0, pct * 10.0))
    else:
        radar["Operations"] = 0.0

    return radar


def rollup_tiers(per_bucket: dict[str, dict[str, dict]]) -> dict[str, dict]:
    """per_bucket = {'menu': {store: {...}}, 'ops': {...}, 'campaigns': {...}}"""
    all_stores = set()
    for bucket in per_bucket.values():
        all_stores.update(bucket.keys())

    rollup: dict[str, dict] = {}
    for store in all_stores:
        flags_by_bucket = {b: per_bucket[b].get(store, {}).get("flag", "new") for b in per_bucket}
        worst_flag = max(flags_by_bucket.values(), key=lambda f: FLAG_RANK[f])
        worst_bucket = next(b for b, f in flags_by_bucket.items() if f == worst_flag)
        rollup[store] = {
            "flag": worst_flag,
            "worst_bucket": worst_bucket,
            "per_bucket_flags": flags_by_bucket,
        }
    return rollup
```

- [ ] **Step 4: Run, verify pass.**

```bash
.venv/bin/pytest tests/test_cross_cutting.py -v
```

Expected: 5 passed.

- [ ] **Checkpoint:** all 5 cross_cutting tests pass.

---

### Task 2.2: W/R/O dedup + tiebreak

- [ ] **Step 1: Append failing tests** to `tests/test_cross_cutting.py`:

```python
def test_wro_dedup_keeps_higher_value():
    payloads = {
        "menu": _payload("diagnostic-menu", w_r_o=[
            {"type": "risk", "headline": "Pricing", "value_usd": 5000, "pattern_id": "pricing"}
        ]),
        "campaigns": _payload("diagnostic-campaigns", w_r_o=[
            {"type": "risk", "headline": "Pricing-camp", "value_usd": 8000, "pattern_id": "pricing"}
        ]),
        "ops": _payload("diagnostic-ops"),
        "topline": _payload("diagnostic-topline"),
    }
    selected = xc.select_win_risk_opp(payloads)
    risks = [c for c in selected if c["type"] == "risk"]
    assert len(risks) == 1
    assert risks[0]["value_usd"] == 8000


def test_wro_top_picks_one_per_type_when_available():
    payloads = {
        "menu": _payload("diagnostic-menu", w_r_o=[
            {"type": "risk", "headline": "A", "value_usd": 1000},
            {"type": "risk", "headline": "B", "value_usd": 9000},
        ]),
        "ops": _payload("diagnostic-ops", w_r_o=[
            {"type": "risk", "headline": "C", "value_usd": 5000},
            {"type": "win", "headline": "W", "value_usd": 3000},
            {"type": "opportunity", "headline": "O", "value_usd": 2000},
        ]),
        "campaigns": _payload("diagnostic-campaigns"),
        "topline": _payload("diagnostic-topline"),
    }
    selected = xc.select_win_risk_opp(payloads)
    types = {c["type"] for c in selected}
    assert types == {"win", "risk", "opportunity"}
    risk = next(c for c in selected if c["type"] == "risk")
    assert risk["headline"] == "B"  # highest value risk


def test_wro_null_value_sorts_last():
    payloads = {
        "menu": _payload("diagnostic-menu", w_r_o=[
            {"type": "risk", "headline": "Has-value", "value_usd": 1000},
            {"type": "risk", "headline": "No-value", "value_usd": None},
        ]),
        "ops": _payload("diagnostic-ops"),
        "campaigns": _payload("diagnostic-campaigns"),
        "topline": _payload("diagnostic-topline"),
    }
    risk = next(c for c in xc.select_win_risk_opp(payloads) if c["type"] == "risk")
    assert risk["headline"] == "Has-value"
```

- [ ] **Step 2: Run, verify failure** (`select_win_risk_opp` undefined).

- [ ] **Step 3: Append implementation** to `cross_cutting.py`:

```python
def select_win_risk_opp(payloads: dict[str, dict]) -> list[dict]:
    """Top 3, one per type if possible. Dedup by pattern_id; tiebreak by value, severity, sub_skill priority."""
    candidates: list[dict] = []
    for sub_skill, payload in payloads.items():
        ss_short = sub_skill.replace("diagnostic-", "")
        for c in payload["drafted"]["win_risk_opp_candidates"]:
            candidates.append({**c, "_sub_skill": ss_short})

    # Dedup by pattern_id; tiebreak via _wro_rank
    by_pattern: dict[str, dict] = {}
    no_pattern: list[dict] = []
    for c in candidates:
        pid = c.get("pattern_id")
        if pid is None:
            no_pattern.append(c)
            continue
        existing = by_pattern.get(pid)
        if existing is None or _wro_rank(c) > _wro_rank(existing):
            by_pattern[pid] = c
    deduped = list(by_pattern.values()) + no_pattern

    # Pick top 1 of each type if available
    selected: list[dict] = []
    for kind in ("win", "risk", "opportunity"):
        of_kind = sorted([c for c in deduped if c["type"] == kind], key=_wro_rank, reverse=True)
        if of_kind:
            selected.append(of_kind[0])
    return selected


def _wro_rank(c: dict) -> tuple:
    val = c.get("value_usd")
    has_val = val is not None
    severity_rank = {"foundation": 4, "high": 3, "medium": 2, "low": 1}.get(c.get("severity", "low"), 1)
    sub_skill_priority = {"ops": 4, "menu": 3, "campaigns": 2, "topline": 1}.get(c.get("_sub_skill", "topline"), 0)
    return (has_val, val if has_val else 0, severity_rank, sub_skill_priority)
```

- [ ] **Step 4: Run, verify pass** (8 total in `test_cross_cutting.py`).

- [ ] **Checkpoint:** all 8 cross_cutting tests pass.

---

### Task 2.3: Foundation gate (with fail-conservative rule)

- [ ] **Step 1: Append failing tests:**

```python
def test_foundation_gate_triggers_on_low_rating():
    payloads = {
        "menu": _payload("diagnostic-menu", metrics={"menu_cvr_pct": 18.0, "photo_coverage_pct": 70.0}),
        "ops": _payload("diagnostic-ops", metrics={"rating": 4.0, "error_rate_pct": 3.0, "uptime_pct": 95.0}),
        "campaigns": _payload("diagnostic-campaigns"),
        "topline": _payload("diagnostic-topline"),
    }
    sub_status = {s: "ok" for s in ("diagnostic-ops", "diagnostic-menu", "diagnostic-campaigns", "diagnostic-topline")}
    gate = xc.compute_foundation_gate(payloads, sub_status)
    assert gate["triggered"] is True
    assert any(t.get("metric") == "rating" for t in gate["triggers"])


def test_foundation_gate_no_trigger_when_clean():
    payloads = {
        "menu": _payload("diagnostic-menu", metrics={"menu_cvr_pct": 22.0, "photo_coverage_pct": 80.0}),
        "ops": _payload("diagnostic-ops", metrics={"rating": 4.6, "error_rate_pct": 2.0, "uptime_pct": 96.0}),
        "campaigns": _payload("diagnostic-campaigns"),
        "topline": _payload("diagnostic-topline"),
    }
    sub_status = {s: "ok" for s in ("diagnostic-ops", "diagnostic-menu", "diagnostic-campaigns", "diagnostic-topline")}
    gate = xc.compute_foundation_gate(payloads, sub_status)
    assert gate["triggered"] is False
    assert gate["triggers"] == []


def test_foundation_gate_fail_conservative_when_ops_failed():
    payloads = {
        "menu": _payload("diagnostic-menu", metrics={"menu_cvr_pct": 22.0, "photo_coverage_pct": 80.0}),
        "ops": _payload("diagnostic-ops"),  # no metrics — sub-skill failed
        "campaigns": _payload("diagnostic-campaigns"),
        "topline": _payload("diagnostic-topline"),
    }
    sub_status = {"diagnostic-ops": "failed", "diagnostic-menu": "ok", "diagnostic-campaigns": "ok", "diagnostic-topline": "ok"}
    gate = xc.compute_foundation_gate(payloads, sub_status)
    assert gate["triggered"] is True
    assert any(t.get("reason") == "ops_sub_skill_failed" for t in gate["triggers"])
```

- [ ] **Step 2: Run, verify failure.**

- [ ] **Step 3: Append implementation:**

```python
FOUNDATION_THRESHOLDS = {
    "rating": ("ops", "<", 4.2),
    "error_rate_pct": ("ops", ">", 5.0),
    "uptime_pct": ("ops", "<", 90.0),
    "menu_cvr_pct": ("menu", "<", 15.0),
    "photo_coverage_pct": ("menu", "<", 50.0),
}


def compute_foundation_gate(payloads: dict[str, dict], sub_skill_status: dict[str, str]) -> dict:
    """Per spec §Decision 3 with fail-conservative rule."""
    triggers: list[dict] = []

    # Fail-conservative: ops or menu failure → trigger
    for required in ("diagnostic-ops", "diagnostic-menu"):
        if sub_skill_status.get(required) == "failed":
            triggers.append({"metric": None, "reason": f"{required.replace('diagnostic-', '')}_sub_skill_failed"})

    # Threshold checks (only if owner sub-skill ran)
    for metric, (owner_short, op, threshold) in FOUNDATION_THRESHOLDS.items():
        owner_full = f"diagnostic-{owner_short}"
        if sub_skill_status.get(owner_full) != "ok":
            continue
        value = payloads[owner_short]["computed"]["metrics"].get(metric)
        if value is None:
            continue
        tripped = (op == "<" and value < threshold) or (op == ">" and value > threshold)
        if tripped:
            triggers.append({"metric": metric, "value": value, "threshold": threshold, "scope": "portfolio"})

    return {
        "triggered": bool(triggers),
        "triggers": triggers,
        "override_action_plan": bool(triggers),
    }
```

- [ ] **Step 4: Run, verify pass** (11 total in `test_cross_cutting.py`).

- [ ] **Checkpoint:** all 11 cross_cutting tests pass.

---

## Chunk 3: `diagnostic-topline` sub-skill + `diagnostic-action-plan` stub

Two sub-skill packages built in parallel. Each emits contract-shaped JSON. Each gets its own `pyproject.toml` so pytest finds the package without sys.path hacks.

### Task 3.1: `diagnostic-topline` — minimal computing emitter

Goal: produces a valid contract payload from a tiny synthetic dataset. Real metric/finding logic comes Wk 2; this proves the contract round-trip.

**Files:**
- Create: `Cowork/Skills/diagnostic-topline/SKILL.md`
- Create: `Cowork/Skills/diagnostic-topline/pyproject.toml`
- Create: `Cowork/Skills/diagnostic-topline/diagnostic_topline/__init__.py`
- Create: `Cowork/Skills/diagnostic-topline/diagnostic_topline/compute.py`
- Create: `Cowork/Skills/diagnostic-topline/diagnostic_topline/entry.py`
- Create: `Cowork/Skills/diagnostic-topline/references/patterns-topline.md`
- Create: `Cowork/Skills/diagnostic-topline/tests/__init__.py`
- Create: `Cowork/Skills/diagnostic-topline/tests/test_compute.py`

- [ ] **Step 1: Create the skill folder + venv:**

```bash
mkdir -p /Users/maxx/Desktop/Cowork/Skills/diagnostic-topline/diagnostic_topline \
          /Users/maxx/Desktop/Cowork/Skills/diagnostic-topline/tests \
          /Users/maxx/Desktop/Cowork/Skills/diagnostic-topline/references
cd /Users/maxx/Desktop/Cowork/Skills/diagnostic-topline
python3 -m venv .venv
.venv/bin/pip install -U pip pytest pandas jsonschema
```

- [ ] **Step 2: Write `pyproject.toml`** (puts skill root on pythonpath so `from diagnostic_topline import ...` works):

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

- [ ] **Step 3: Write `SKILL.md`:**

```markdown
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
```

- [ ] **Step 4: Write `references/patterns-topline.md`:**

```markdown
# Top-line Pattern Library (v0.1)

| pattern_id | Trigger | Severity | Default deliverable |
|---|---|---|---|
| revenue_down_traffic_stable | gross_sales WoW Δ < -10% AND impressions WoW Δ within ±5% | high | optimized-menu-sheet |
| momentum_decay | last-4-wks gross < prior-4-wks gross by >5% AND payout_pct stable | medium | campaign-plan |
| payout_collapse | net_payout_pct < 50% | foundation | (foundation gate routing) |

Full pattern library backfilled in Wk 2.
```

- [ ] **Step 5: Write `__init__.py` (empty file)** at `diagnostic_topline/__init__.py` and `tests/__init__.py`.

- [ ] **Step 6: Write the failing test** at `tests/test_compute.py`:

```python
import sys
from pathlib import Path
import pandas as pd
import pytest
from diagnostic_topline import compute

# Make the orchestrator package importable for the contract validation test
sys.path.insert(0, str(Path("/Users/maxx/Desktop/Cowork/Skills/client-diagnostics")))


def _normal_df():
    return pd.DataFrame({
        "store": ["BeverlyHills", "Venice"] * 10,
        "week": list(range(1, 11)) * 2,
        "gross_sales": [10000, 8000] * 10,
        "orders": [200, 150] * 10,
        "net_payout": [7000, 5500] * 10,
    })


def test_compute_emits_payload_with_required_shape():
    payload = compute.run(client="goop-kitchen", window_start="2026-02-08", window_end="2026-05-08", df=_normal_df())
    assert payload["sub_skill"] == "diagnostic-topline"
    assert payload["client"] == "goop-kitchen"
    assert "AOV" in payload["computed"]["radar_contributions"]
    assert "Re-order Rate" in payload["computed"]["radar_contributions"]
    assert payload["computed"]["metrics"]["gross_sales"] > 0
    assert isinstance(payload["computed"]["findings"], list)


def test_compute_payload_passes_contract_validator():
    from orchestrator import contract
    payload = compute.run(client="x", window_start="2026-01-01", window_end="2026-04-01", df=_normal_df())
    contract.validate(payload)  # no exception


def test_low_payout_emits_foundation_finding():
    df = pd.DataFrame({
        "store": ["A"] * 4, "week": [1,2,3,4],
        "gross_sales": [10000]*4, "orders": [200]*4,
        "net_payout": [3000]*4,  # 30% payout — below 50% triggers foundation finding
    })
    payload = compute.run(client="x", window_start="2026-01-01", window_end="2026-04-01", df=df)
    foundation_findings = [f for f in payload["computed"]["findings"] if f["severity"] == "foundation"]
    assert len(foundation_findings) == 1
    assert foundation_findings[0]["pattern_id"] == "payout_collapse"
```

- [ ] **Step 7: Run, verify failure** (`ModuleNotFoundError: diagnostic_topline.compute`).

```bash
cd /Users/maxx/Desktop/Cowork/Skills/diagnostic-topline
.venv/bin/pytest tests/ -v
```

- [ ] **Step 8: Write minimal `compute.py`:**

```python
"""Top-line metric computation. Emits sub-skill contract payload."""
import pandas as pd


def run(*, client: str, window_start: str, window_end: str, df: pd.DataFrame) -> dict:
    gross_sales = float(df["gross_sales"].sum())
    orders = int(df["orders"].sum())
    aov = gross_sales / orders if orders else 0.0
    net_payout = float(df["net_payout"].sum())
    payout_pct = (net_payout / gross_sales * 100) if gross_sales else 0.0

    # Naive radar scoring — Wk 2 will replace with real benchmarking
    aov_score = max(1.0, min(10.0, aov / 5))  # $50 AOV = 10
    reorder_score = 6.0  # placeholder; real metric needs customer-level data

    findings: list[dict] = []
    if payout_pct < 50:
        findings.append({
            "pattern_id": "payout_collapse",
            "severity": "foundation",
            "scope": "portfolio",
            "evidence": {"payout_pct": payout_pct},
            "estimated_impact_usd": (50 - payout_pct) / 100 * gross_sales,
            "deliverable_trigger": {"skill": "campaign-plan", "params": {"focus": "cost_recovery"}},
        })

    return {
        "sub_skill": "diagnostic-topline",
        "version": "1.0",
        "client": client,
        "window": {"start": window_start, "end": window_end},
        "computed": {
            "metrics": {"gross_sales": gross_sales, "orders": orders, "aov": aov, "net_payout": net_payout, "payout_pct": payout_pct},
            "radar_contributions": {"AOV": aov_score, "Re-order Rate": reorder_score},
            "tier_contributions": {},  # topline does not contribute to tier — leave empty
            "findings": findings,
            "charts": [],
        },
        "drafted": {
            "toggle_title": "Top-line Performance",
            "toggle_prose": f"Gross sales: ${gross_sales:,.0f} across {orders:,} orders. AOV: ${aov:.2f}. Net payout: {payout_pct:.1f}%.",
            "win_risk_opp_candidates": [],
        },
        "data_quality": {"completeness": 1.0, "gaps": []},
    }
```

- [ ] **Step 9: Install jsonschema in topline venv** (needed for the contract-validation test) and re-run:

```bash
cd /Users/maxx/Desktop/Cowork/Skills/diagnostic-topline
.venv/bin/pip install jsonschema
.venv/bin/pytest tests/ -v
```

Expected: 3 passed.

- [ ] **Step 10: Write `entry.py`** as the orchestrator-callable CLI entry:

```python
"""CLI entry. Orchestrator dispatches via subprocess."""
import argparse
import json
import pandas as pd
from pathlib import Path
from diagnostic_topline import compute


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--window-start", required=True)
    ap.add_argument("--window-end", required=True)
    ap.add_argument("--inputs-dir", required=True, type=Path)
    ap.add_argument("--output-path", required=True, type=Path)
    args = ap.parse_args()

    csvs = sorted(args.inputs_dir.glob("*.csv"))
    if not csvs:
        raise SystemExit(f"no input CSVs found in {args.inputs_dir}")
    df = pd.concat([pd.read_csv(c) for c in csvs], ignore_index=True)

    payload = compute.run(client=args.client, window_start=args.window_start, window_end=args.window_end, df=df)
    args.output_path.write_text(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
```

- [ ] **Checkpoint:** all 3 topline tests pass; `entry.py` script importable.

---

### Task 3.2: `diagnostic-action-plan` stub

**Files:**
- Create: `Cowork/Skills/diagnostic-action-plan/SKILL.md`
- Create: `Cowork/Skills/diagnostic-action-plan/pyproject.toml`
- Create: `Cowork/Skills/diagnostic-action-plan/diagnostic_action_plan/__init__.py`
- Create: `Cowork/Skills/diagnostic-action-plan/diagnostic_action_plan/entry.py`
- Create: `Cowork/Skills/diagnostic-action-plan/tests/__init__.py`
- Create: `Cowork/Skills/diagnostic-action-plan/tests/test_entry.py`

- [ ] **Step 1: Create folder + venv:**

```bash
mkdir -p /Users/maxx/Desktop/Cowork/Skills/diagnostic-action-plan/diagnostic_action_plan \
          /Users/maxx/Desktop/Cowork/Skills/diagnostic-action-plan/tests
cd /Users/maxx/Desktop/Cowork/Skills/diagnostic-action-plan
python3 -m venv .venv
.venv/bin/pip install -U pip pytest jsonschema
```

- [ ] **Step 2: Write `pyproject.toml`:**

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

- [ ] **Step 3: Write SKILL.md:**

```markdown
---
name: diagnostic-action-plan
description: >
  Sub-skill of client-diagnostics. Synthesizes the action plan kanban
  (P1/P2/P3) from all 4 domain sub-skills' findings + cross-cutting state.
  v0.1 STUB: consumes findings, emits kanban with deliverable triggers,
  no prioritization yet. Full prioritization in v1.0 (Wk 2-3).
version: 0.1.0
---

# Diagnostic — Action Plan (Stub)

v0.1 stub for contract round-trip validation. Reads findings, emits a kanban-shaped action plan.

## Inputs

- `findings`: list of finding dicts (orchestrator collates from sub-skills)
- `foundation_triggered`: bool from orchestrator's foundation gate

## Output

```json
{
  "version": "0.1-stub",
  "kanban": {
    "P1_this_week": [...],
    "P2_next_30d": [...],
    "P3_watch": [...]
  },
  "deliverable_triggers": [...]
}
```
```

- [ ] **Step 4: Write the failing test** at `tests/test_entry.py`:

```python
import json
from pathlib import Path
import jsonschema
import pytest
from diagnostic_action_plan import entry

CONTRACT_PATH = Path("/Users/maxx/Desktop/Cowork/Skills/optimized-menu-sheet/deliverable_contract.json")


def test_stub_routes_foundation_finding_to_p1():
    findings = [
        {"pattern_id": "payout_collapse", "severity": "foundation", "scope": "portfolio",
         "estimated_impact_usd": 50000, "deliverable_trigger": {"skill": "campaign-plan", "params": {}}},
        {"pattern_id": "low_cvr", "severity": "medium", "scope": "Venice",
         "estimated_impact_usd": 5000, "deliverable_trigger": {"skill": "optimized-menu-sheet", "params": {"stores": ["Venice"]}}},
    ]
    plan = entry.build_plan(findings, foundation_triggered=True)
    p1 = plan["kanban"]["P1_this_week"]
    assert any(it["pattern_id"] == "payout_collapse" for it in p1)
    # foundation triggered → all non-foundation findings get pushed to watch list (no spend until fixed)
    assert all(it["severity"] == "foundation" for it in p1)


def test_stub_emits_deliverable_triggers():
    findings = [
        {"pattern_id": "low_cvr", "severity": "medium", "scope": "Venice",
         "estimated_impact_usd": 5000, "deliverable_trigger": {"skill": "optimized-menu-sheet", "params": {"stores": ["Venice"]}}}
    ]
    plan = entry.build_plan(findings, foundation_triggered=False)
    assert len(plan["deliverable_triggers"]) == 1
    assert plan["deliverable_triggers"][0]["skill"] == "optimized-menu-sheet"


def test_emitted_trigger_validates_against_downstream_contract():
    contract = json.loads(CONTRACT_PATH.read_text())
    findings = [
        {"pattern_id": "low_cvr", "severity": "medium", "scope": "Venice",
         "estimated_impact_usd": 5000,
         "deliverable_trigger": {"skill": "optimized-menu-sheet", "params": {"stores": ["Venice"], "focus": "category_consolidation"}}}
    ]
    plan = entry.build_plan(findings, foundation_triggered=False)
    trigger = plan["deliverable_triggers"][0]
    assert trigger["skill"] == contract["skill"]
    jsonschema.validate(trigger["params"], contract["params_schema"])  # no exception


def test_invalid_params_fail_contract():
    contract = json.loads(CONTRACT_PATH.read_text())
    bad_params = {"focus": "category_consolidation"}  # missing required `stores`
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad_params, contract["params_schema"])
```

- [ ] **Step 5: Run, verify failure.**

```bash
cd /Users/maxx/Desktop/Cowork/Skills/diagnostic-action-plan
.venv/bin/pytest tests/ -v
```

Expected failures: `ModuleNotFoundError` for `diagnostic_action_plan` AND/OR `FileNotFoundError` for `optimized-menu-sheet/deliverable_contract.json` (the contract file gets created in Task 3.3).

- [ ] **Step 6: Write `entry.py`:**

```python
"""Action plan stub. Build a v0.1 kanban from findings."""

def build_plan(findings: list[dict], *, foundation_triggered: bool) -> dict:
    p1, p2, p3 = [], [], []
    for f in findings:
        item = {**f}
        if foundation_triggered:
            # Foundation gate active: only foundation findings ship; rest deferred to watch list
            if f["severity"] == "foundation":
                p1.append(item)
            else:
                p3.append(item)
        else:
            sev = f["severity"]
            if sev in ("foundation", "high"):
                p1.append(item)
            elif sev == "medium":
                p2.append(item)
            else:
                p3.append(item)

    return {
        "version": "0.1-stub",
        "kanban": {"P1_this_week": p1, "P2_next_30d": p2, "P3_watch": p3},
        "deliverable_triggers": [
            f["deliverable_trigger"] for f in findings if f.get("deliverable_trigger")
        ],
    }
```

- [ ] **Step 7: Run.** First two tests pass; tests 3 + 4 still fail because contract file doesn't exist — that's Task 3.3.

- [ ] **Checkpoint:** tests 1+2 pass; tests 3+4 wait on Task 3.3.

---

### Task 3.3: One example `deliverable_contract.json` for action-plan validation

**Files:**
- Create: `Cowork/Skills/optimized-menu-sheet/` (directory — newly created)
- Create: `Cowork/Skills/optimized-menu-sheet/deliverable_contract.json`

- [ ] **Step 1: Create the skill folder:**

```bash
mkdir -p /Users/maxx/Desktop/Cowork/Skills/optimized-menu-sheet
```

- [ ] **Step 2: Write the contract:**

```json
{
  "skill": "optimized-menu-sheet",
  "version": "1.0",
  "params_schema": {
    "type": "object",
    "required": ["stores"],
    "properties": {
      "stores": {"type": "array", "items": {"type": "string"}, "minItems": 1},
      "focus": {"type": "string", "enum": ["category_consolidation", "sku_rationalization", "pricing_review"]}
    }
  }
}
```

- [ ] **Step 3: Re-run action-plan tests:**

```bash
cd /Users/maxx/Desktop/Cowork/Skills/diagnostic-action-plan
.venv/bin/pytest tests/ -v
```

Expected: 4 passed.

- [ ] **Checkpoint:** all 4 action-plan tests pass.

---

## Chunk 4: Orchestrator + end-to-end smoke test

Ties everything together. The orchestrator SKILL.md becomes a dispatcher, and the orchestrator's `entry.py` runs the full pipeline against synthetic input data.

### Task 4.1: Orchestrator `entry.py` — Phase 1-5 controller

**Files:**
- Create: `Cowork/Skills/client-diagnostics/orchestrator/entry.py`
- Create: `Cowork/Skills/client-diagnostics/tests/test_smoke_e2e.py`

- [ ] **Step 1: Write the failing E2E test** at `tests/test_smoke_e2e.py`:

```python
"""End-to-end smoke: synthetic input → orchestrator → topline + action-plan-stub.

Note: hash-stability test verifies the compute layer is deterministic when given
identical inputs. It does NOT verify stability across data variation — Wk 2 covers that.
"""
import json
import tempfile
from pathlib import Path
import pandas as pd
from datetime import datetime

from orchestrator import contract, output_layout, entry


def _synth_csv(path: Path):
    df = pd.DataFrame({
        "store": ["BeverlyHills", "Venice", "Brentwood"] * 5,
        "week": list(range(1, 6)) * 3,
        "gross_sales": [12000, 9000, 7000] * 5,
        "orders": [240, 180, 140] * 5,
        "net_payout": [8000, 6000, 4500] * 5,
    })
    df.to_csv(path, index=False)


def test_full_run_produces_valid_outputs(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(output_layout, "RUN_ROOT", Path(tmp) / "runs")
        inputs = Path(tmp) / "inputs"
        inputs.mkdir()
        _synth_csv(inputs / "synth.csv")

        result = entry.run(
            client="test-client",
            window_start="2026-02-08",
            window_end="2026-05-08",
            inputs_dir=inputs,
            when=datetime(2026, 5, 8, 14, 30, 0),
        )

        # Topline payload exists and validates
        topline_path = result.layout.sub_skill_results_path("topline")
        topline_payload = json.loads(topline_path.read_text())
        contract.validate(topline_payload)

        # Action plan output exists
        ap_path = result.layout.root / "action-plan" / "diagnostic-action-plan_results.json"
        ap = json.loads(ap_path.read_text())
        assert "kanban" in ap

        # run_state.json reflects topline as ok
        state = json.loads(result.layout.run_state_path.read_text())
        assert state["sub_skill_status"]["diagnostic-topline"] == "ok"


def test_topline_compute_is_deterministic_for_identical_inputs(monkeypatch):
    """Same synthetic input twice → identical computed-layer hash. Proves compute determinism, not pipeline stability across real-world variation."""
    hashes = []
    for _ in range(2):
        with tempfile.TemporaryDirectory() as tmp:
            monkeypatch.setattr(output_layout, "RUN_ROOT", Path(tmp) / "runs")
            inputs = Path(tmp) / "inputs"
            inputs.mkdir()
            _synth_csv(inputs / "synth.csv")
            result = entry.run(client="t", window_start="2026-02-08", window_end="2026-05-08", inputs_dir=inputs, when=datetime(2026, 5, 8, 14, 30, 0))
            payload = json.loads(result.layout.sub_skill_results_path("topline").read_text())
            hashes.append(contract.computed_hash(payload))
    assert hashes[0] == hashes[1]
```

- [ ] **Step 2: Run, verify failure.**

```bash
cd /Users/maxx/Desktop/Cowork/Skills/client-diagnostics
.venv/bin/pytest tests/test_smoke_e2e.py -v
```

- [ ] **Step 3: Implement orchestrator `entry.py`:**

```python
"""Orchestrator main entry. Phase 1-5 controller. Wk 1: dispatches topline + action-plan stub only."""
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from orchestrator import contract, output_layout, run_state

SKILLS_ROOT = Path("/Users/maxx/Desktop/Cowork/Skills")


@dataclass(frozen=True)
class RunResult:
    layout: output_layout.RunLayout
    state: dict


def run(*, client: str, window_start: str, window_end: str, inputs_dir: Path, when: datetime | None = None) -> RunResult:
    when = when or datetime.now()
    layout = output_layout.create_run_dirs(client, when)
    run_id = f"{client}-{when.strftime('%Y-%m-%dT%H:%M:%S')}"
    state = run_state.init(run_id, layout.run_state_path)

    # Phase 2: dispatch topline (Wk 1 only — others come Wk 2)
    state = run_state.update(layout.run_state_path, phase=2, sub_skill_status={"diagnostic-topline": "running"})
    topline_path = layout.sub_skill_results_path("topline")
    _dispatch_topline(client=client, window_start=window_start, window_end=window_end, inputs_dir=inputs_dir, output_path=topline_path)
    state = run_state.update(layout.run_state_path, sub_skill_status={"diagnostic-topline": "ok"})

    # Phase 3: cross-cutting (limited Wk 1 — only validation; full radar/tier needs all sub-skills)
    state = run_state.update(layout.run_state_path, phase=3)
    topline_payload = json.loads(topline_path.read_text())
    contract.validate(topline_payload)

    # Phase 4: dispatch action-plan stub (in-process Wk 1 — subprocess in Wk 2 once fully promoted)
    state = run_state.update(layout.run_state_path, phase=4)
    ap_output_path = layout.root / "action-plan" / "diagnostic-action-plan_results.json"
    findings = topline_payload["computed"]["findings"]
    _dispatch_action_plan(findings, foundation_triggered=False, output_path=ap_output_path)

    # Phase 5: deferred to Wk 2 (Notion assembly)
    state = run_state.update(layout.run_state_path, phase=5)

    return RunResult(layout=layout, state=state)


def _dispatch_topline(*, client, window_start, window_end, inputs_dir, output_path):
    skill_dir = SKILLS_ROOT / "diagnostic-topline"
    cmd = [
        str(skill_dir / ".venv" / "bin" / "python"),
        "-m", "diagnostic_topline.entry",
        "--client", client,
        "--window-start", window_start,
        "--window-end", window_end,
        "--inputs-dir", str(inputs_dir),
        "--output-path", str(output_path),
    ]
    env = {**os.environ, "PYTHONPATH": str(skill_dir)}
    subprocess.run(cmd, check=True, env=env)


def _dispatch_action_plan(findings, *, foundation_triggered: bool, output_path: Path):
    # Wk 1: in-process. Wk 2-3 swaps to subprocess once fully promoted.
    skill_dir = SKILLS_ROOT / "diagnostic-action-plan"
    if str(skill_dir) not in sys.path:
        sys.path.insert(0, str(skill_dir))
    from diagnostic_action_plan.entry import build_plan
    plan = build_plan(findings, foundation_triggered=foundation_triggered)
    output_path.write_text(json.dumps(plan, indent=2, sort_keys=True))
```

- [ ] **Step 4: Run E2E tests:**

```bash
cd /Users/maxx/Desktop/Cowork/Skills/client-diagnostics
.venv/bin/pytest tests/test_smoke_e2e.py -v
```

Expected: 2 passed.

- [ ] **Checkpoint:** all 2 E2E tests pass.

---

### Task 4.2: Rewrite orchestrator `SKILL.md` as dispatcher

**Files:**
- Modify: `Cowork/Skills/client-diagnostics/SKILL.md`

- [ ] **Step 1:** Read current SKILL.md to identify what stays vs what relocates:

```bash
wc -l /Users/maxx/Desktop/Cowork/Skills/client-diagnostics/SKILL.md
```

- [ ] **Step 2: Replace SKILL.md** with the orchestrator version:

```markdown
---
name: client-diagnostics
description: >
  Orchestrator skill. Produces a 90-day client diagnostic by dispatching
  domain sub-skills in parallel (topline, menu, ops, campaigns), assembling
  cross-cutting outputs (radar, tier rollup, foundation gate), then routing
  findings to deliverable skills via the action-plan sub-skill. Output is
  a dual-half Notion page (dashboard + collapsed toggles).
version: 1.0.0
supersedes: 0.2.0 (monolithic)
---

# Client Diagnostics — Orchestrator

This skill is a **dispatcher**, not a monolithic generator. It coordinates 5 sub-skills:

- `diagnostic-topline` — financials, momentum, platform breakdown
- `diagnostic-menu` — storefront visual, conversion, SKUs, photo coverage *(Wk 2)*
- `diagnostic-ops` — uptime, errors, cancellations, ratings, downtime *(Wk 2)*
- `diagnostic-campaigns` — promos, ads, ROAS, daypart *(Wk 2)*
- `diagnostic-action-plan` — synthesizes kanban + deliverable triggers

## Wk 1 status (this build)

- ✅ Orchestrator skeleton (`orchestrator/entry.py`)
- ✅ Run-state + output layout (`orchestrator/run_state.py`, `orchestrator/output_layout.py`)
- ✅ Sub-skill output contract (`orchestrator/contract.py`)
- ✅ Cross-cutting computation (`orchestrator/cross_cutting.py`)
- ✅ `diagnostic-topline` v0.1 (synthetic-data validated)
- ✅ `diagnostic-action-plan` v0.1 stub
- 🚧 menu/ops/campaigns sub-skills — Wk 2
- 🚧 Notion page assembly — Wk 2 (currently outputs JSON only)
- 🚧 Real goop Kitchen end-to-end — Wk 2

## How to invoke (programmatic)

```bash
cd /Users/maxx/Desktop/Cowork/Skills/client-diagnostics
.venv/bin/python -c "
from datetime import datetime
from pathlib import Path
from orchestrator import entry
result = entry.run(
    client='goop-kitchen',
    window_start='2026-02-08',
    window_end='2026-05-08',
    inputs_dir=Path('/path/to/exports'),
)
print('Run wrote to:', result.layout.root)
"
```

Reads platform CSVs from `inputs_dir`, writes to `/tmp/diagnostic-runs/<client>/<timestamp>/`.

## Reference architecture

- **Spec:** `specs/2026-05-08-orchestrator-redesign.md`
- **Wk 1 plan:** `plans/2026-05-08-orchestrator-wk1-plan.md`
- **Cross-cutting patterns:** `references/cross-cutting-patterns.md`
- **Per sub-skill patterns:** `Cowork/Skills/diagnostic-<sub>/references/patterns-<sub>.md`

## Migration from v0.2

v0.2 monolithic logic stays operational until Wk 4 cutover. New diagnostics use v1; in-flight engagements stay on v0.2 mid-cycle. See spec §Open Questions #2 + #7 for migration policy.
```

- [ ] **Step 3: Verify the SKILL.md frontmatter parses:**

```bash
.venv/bin/python -c "
import yaml, re
text = open('/Users/maxx/Desktop/Cowork/Skills/client-diagnostics/SKILL.md').read()
m = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
fm = yaml.safe_load(m.group(1))
assert fm['name'] == 'client-diagnostics'
assert fm['version'] == '1.0.0'
print('SKILL.md frontmatter OK:', fm)
"
```

If `yaml` not installed: `.venv/bin/pip install pyyaml`.

Expected: prints frontmatter dict.

- [ ] **Checkpoint:** SKILL.md frontmatter loads cleanly.

---

### Task 4.3: Pattern library split — relocate cross-cutting content

**Files:**
- Create: `Cowork/Skills/client-diagnostics/references/cross-cutting-patterns.md`
- Modify: `Cowork/Skills/client-diagnostics/references/diagnostic-framework.md` (banner only — content split happens Wk 2)

- [ ] **Step 1: Read the existing framework** to locate the Location Tier Strategy section:

```bash
sed -n '71,112p' /Users/maxx/Desktop/Cowork/Skills/client-diagnostics/references/diagnostic-framework.md
```

This section (lines 71–112) contains the canonical Location Tier Strategy: sub-bucket scoring rules (Menu/Ops/Campaign × Healthy/Watch/Broken), the rollup table, edge cases (Ops Broken always wins, New trumps the others, single-platform stores), and the historical context for what it replaces.

- [ ] **Step 2: Create `cross-cutting-patterns.md`** by COPYING the Location Tier Strategy section verbatim from the framework, then add a header explaining the file's role:

```markdown
# Cross-Cutting Patterns (Orchestrator-owned)

Patterns spanning 2+ sub-skill domains live here. Per-domain patterns live in `Cowork/Skills/diagnostic-<sub>/references/patterns-<sub>.md` (Wk 2 work).

The Location Tier Strategy is the canonical cross-cutting pattern: each store gets per-bucket scores from menu/ops/campaigns sub-skills, then the orchestrator merges into a single rollup.

---

[paste lines 71–112 of diagnostic-framework.md verbatim — the entire "Location Tier Strategy" section through "What this replaces"]

---

## Code synchronization

The rollup rule above is encoded in `orchestrator/cross_cutting.py::rollup_tiers`. **Update both the docs and the code together** when the rule changes.
```

- [ ] **Step 3: Add a non-destructive banner** to the TOP of `diagnostic-framework.md` (do NOT remove or modify the existing 210 lines of content):

```bash
# Insert at line 1, preserving everything else:
```

Resulting structure:
```markdown
# Diagnostic Framework & Benchmarks

> **Note (2026-05-08, orchestrator redesign Wk 1):** This file is the canonical pattern library for v0.2 (monolithic) and remains operational. Wk 2 redistributes per sub-skill:
> - 7-dim radar bands → split per radar dim owner (see spec §Contracts §"Radar dim ownership")
> - Foundation Health Gate → encoded in `orchestrator/cross_cutting.py::compute_foundation_gate`
> - Cuisine CVR benchmarks → `Cowork/Skills/diagnostic-menu/references/`
> - Location Tier Strategy → already extracted to `cross-cutting-patterns.md` (Wk 1)
> - Common Diagnostic Patterns → split per sub-skill in `patterns-<sub>.md`
> - Chart Library → split per sub-skill (charts owned by domain) + cross-cutting at orchestrator
>
> Until Wk 2 redistribution completes, all references in v0.2 SKILL.md continue to work against this file.

[existing 210 lines below, untouched]
```

- [ ] **Checkpoint:** `cross-cutting-patterns.md` exists with verbatim-copied Location Tier Strategy. `diagnostic-framework.md` has the banner at top; rest of file unchanged. `wc -l diagnostic-framework.md` should be 220 (210 original + 10-line banner).

---

## Wk 1 completion verification

Run the full test suite and confirm:

- [ ] **All Python tests pass across all three skills:**

```bash
cd /Users/maxx/Desktop/Cowork/Skills/client-diagnostics && .venv/bin/pytest tests/ -v
cd /Users/maxx/Desktop/Cowork/Skills/diagnostic-topline && .venv/bin/pytest tests/ -v
cd /Users/maxx/Desktop/Cowork/Skills/diagnostic-action-plan && .venv/bin/pytest tests/ -v
```

Expected counts:
- `client-diagnostics/tests/`: **4** (output_layout) + **3** (run_state) + **8** (contract) + **11** (cross_cutting) + **2** (smoke E2E) = **28**
- `diagnostic-topline/tests/`: **3**
- `diagnostic-action-plan/tests/`: **4**
- **Grand total: 35 passing tests**

- [ ] **Computed-layer hash stable across runs** (proven by `test_topline_compute_is_deterministic_for_identical_inputs`).

- [ ] **Orchestrator skill loads** (frontmatter parses).

- [ ] **One downstream contract validates** (`optimized-menu-sheet/deliverable_contract.json` proves the loop).

- [ ] **Snapshot the work** for the Spice deployment process — Maxx wraps Wk 1 by copying the new skill folders into the `spice-team-skills` plugin marketplace via the existing publish mechanism. (No git operations required because Cowork is not under git.)

---

## What Wk 1 explicitly does NOT cover

- `diagnostic-menu`, `diagnostic-ops`, `diagnostic-campaigns` sub-skills — Wk 2
- Notion page assembly (`notion_assembly.py` is implicit; Wk 2 builds it)
- Chart generation in sub-skills (chart helpers stub only; Wk 2 wires real charts)
- Full pattern libraries per sub-skill (Wk 2 backfills from existing framework)
- Real goop Kitchen end-to-end (synthetic data only Wk 1; Wk 2 with real exports)
- Deliverable trigger wire-up to actually fire downstream skills (Wk 3-4)
- v0.2 deprecation / migration (Wk 4)

These are tracked in the spec build sequence and get their own plans.

---

## Critical Files (recap)

- Spec: `specs/2026-05-08-orchestrator-redesign.md`
- This plan: `plans/2026-05-08-orchestrator-wk1-plan.md`
- Orchestrator entry: `orchestrator/entry.py`
- Contract: `orchestrator/contract.py`
- Cross-cutting: `orchestrator/cross_cutting.py`
- Topline sub-skill: `Cowork/Skills/diagnostic-topline/`
- Action-plan stub: `Cowork/Skills/diagnostic-action-plan/`
- One example downstream contract: `Cowork/Skills/optimized-menu-sheet/deliverable_contract.json`
