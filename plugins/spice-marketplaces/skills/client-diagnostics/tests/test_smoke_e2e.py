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
    """Synthetic CSV with columns each of the 4 sub-skills needs.

    Wk 2 refactor: orchestrator now dispatches all 4 sub-skills in parallel,
    so this CSV must include menu/ops/campaigns columns even for the topline-
    focused smoke test. Mirrors `test_smoke_e2e_full.py::_synth_csv`. Real
    inputs arrive Wk 3.
    """
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

        # Action plan output exists. With tier_rollup wired in (Wk 2.5), the
        # orchestrator-driven plan uses the v0.2 tier-aware schema.
        ap_path = result.layout.root / "action-plan" / "diagnostic-action-plan_results.json"
        ap = json.loads(ap_path.read_text())
        assert "tier_groups" in ap
        for tier in ("red", "yellow", "green", "new"):
            assert tier in ap["tier_groups"]

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
