"""Regression tests for sub-skill dispatch resolution and fail-loud behavior.

Guards the INDAY-2026-07-23 failure mode: the orchestrator dispatched each
diagnostic-* sub-skill via a hardcoded `<sub-skill>/.venv/bin/python`. On a box
without those venvs the subprocess raised FileNotFoundError, which Phase 2
swallowed and marked "failed" — and the affected report section was then
silently populated with zeros, so a blank diagnostic shipped looking complete.

Two guarantees:
  1. Portable interpreter resolution — a missing per-sub-skill venv is NOT fatal;
     the orchestrator falls back to an interpreter that actually exists.
  2. A genuinely un-dispatchable sub-skill FAILS LOUD (raises, naming the
     degraded section) instead of emitting a zero-filled section.
"""
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest
from datetime import datetime

from orchestrator import entry, output_layout


def _synth_csv(path: Path):
    df = pd.DataFrame({
        "store": ["BeverlyHills", "Venice", "Brentwood"] * 5,
        "week": list(range(1, 6)) * 3,
        "gross_sales": [12000, 9000, 7000] * 5,
        "orders": [240, 180, 140] * 5,
        "net_payout": [8000, 6000, 4500] * 5,
        "menu_cvr_pct": [22.0, 14.0, 19.0] * 5,
        "photo_coverage_pct": [85, 35, 70] * 5,
        "hero_set": [True, True, True] * 5,
        "categories_count": [6, 6, 6] * 5,
        "categories_populated": [6, 5, 6] * 5,
        "storefront_to_menu_ctr_pct": [10.0, 11.0, 8.0] * 5,
        "rating": [4.6, 4.0, 4.3] * 5,
        "error_rate_pct": [1.5, 6.0, 3.0] * 5,
        "cancellation_pct": [1.0, 4.0, 2.5] * 5,
        "uptime_pct": [98.0, 88.0, 95.0] * 5,
        "hours_accurate": [True, False, True] * 5,
        "platform": ["UE", "DD", "GH"] * 5,
        "spend": [600, 400, 200] * 5,
        "attributed_sales": [3000, 800, 1000] * 5,
        "roas": [5.0, 2.0, 5.0] * 5,
        "incremental_orders_per_week": [15, 5, 8] * 5,
        "promo_count_active": [2, 4, 1] * 5,
    })
    df.to_csv(path, index=False)


def test_resolve_sub_skill_python_falls_back_when_venv_missing():
    """Fix 1: with no `diagnostic-topline/.venv`, resolution must still return an
    existing python executable (the orchestrator's own interpreter), never a
    non-existent hardcoded path."""
    py = entry._resolve_sub_skill_python("topline")
    assert py.exists(), f"resolver returned a non-existent interpreter: {py}"
    assert os.access(py, os.X_OK), f"resolver returned a non-executable path: {py}"


def test_failed_sub_skill_dispatch_raises_loud_error_naming_section(monkeypatch):
    """Fix 2: an un-dispatchable sub-skill must FAIL LOUD (raise, naming the
    degraded section) rather than completing the run with a zero-filled section."""
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(output_layout, "RUN_ROOT", Path(tmp) / "runs")
        inputs = Path(tmp) / "inputs"
        inputs.mkdir()
        _synth_csv(inputs / "synth.csv")

        # Simulate what a missing venv / crashing subprocess does to one sub-skill.
        def _boom(**kwargs):
            raise FileNotFoundError("no such file: .venv/bin/python")

        monkeypatch.setattr(entry, "_dispatch_ops", _boom)

        with pytest.raises(entry.SubSkillDispatchError) as excinfo:
            entry.run(
                client="test-client",
                window_start="2026-02-08", window_end="2026-05-08",
                inputs_dir=inputs, when=datetime(2026, 5, 8, 14, 30, 0),
            )
        # The error must name which section is degraded so it is not mistaken
        # for a data gap.
        assert "ops" in str(excinfo.value)
