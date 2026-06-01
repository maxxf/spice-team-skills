"""Tests for orchestrator/input_schema.py — Wk 4 Chunk 1."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from orchestrator import entry, input_schema, output_layout
from orchestrator.input_schema import InputSchemaError


def _full_df() -> pd.DataFrame:
    """Synthetic full-shape df mirroring test_smoke_e2e_full._synth_csv."""
    return pd.DataFrame({
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


def test_valid_df_passes():
    """Synthetic full-shape df → no exception."""
    df = _full_df()
    # Should not raise
    input_schema.validate(df)


def test_missing_column_fails_with_named_columns():
    """Drop `rating` → InputSchemaError with 'rating' in the message."""
    df = _full_df().drop(columns=["rating"])
    with pytest.raises(InputSchemaError) as excinfo:
        input_schema.validate(df)
    assert "rating" in str(excinfo.value)


def test_empty_df_fails():
    """Empty DataFrame → InputSchemaError."""
    df = pd.DataFrame(columns=list(_full_df().columns))
    with pytest.raises(InputSchemaError):
        input_schema.validate(df)


def test_invalid_week_range_fails():
    """week=14 → InputSchemaError mentioning '1–13'."""
    df = _full_df()
    df.loc[0, "week"] = 14
    with pytest.raises(InputSchemaError) as excinfo:
        input_schema.validate(df)
    assert "1" in str(excinfo.value) and "13" in str(excinfo.value)


def test_invalid_rating_range_fails():
    """rating=6.5 → InputSchemaError mentioning rating range."""
    df = _full_df()
    df.loc[0, "rating"] = 6.5
    with pytest.raises(InputSchemaError) as excinfo:
        input_schema.validate(df)
    assert "rating" in str(excinfo.value)


def test_invalid_platform_fails():
    """platform='FB' → InputSchemaError mentioning UE/DD/GH."""
    df = _full_df()
    df.loc[0, "platform"] = "FB"
    with pytest.raises(InputSchemaError) as excinfo:
        input_schema.validate(df)
    msg = str(excinfo.value)
    assert "UE" in msg and "DD" in msg and "GH" in msg


def test_orchestrator_short_circuits_on_invalid_input(monkeypatch):
    """entry.run(...) with a CSV missing required columns must raise InputSchemaError
    BEFORE any sub-skill subprocess fires.
    """
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(output_layout, "RUN_ROOT", Path(tmp) / "runs")
        inputs = Path(tmp) / "inputs"
        inputs.mkdir()
        # Write a CSV missing the `rating` column
        bad_df = _full_df().drop(columns=["rating"])
        bad_df.to_csv(inputs / "bad.csv", index=False)

        # Track sub-skill dispatch calls — they MUST NOT fire
        calls: list[str] = []

        def _fake_dispatch(*args, **kwargs):
            calls.append("dispatched")
            raise AssertionError("Sub-skill dispatch fired before validator short-circuit")

        # Monkey-patch all dispatch helpers + action plan
        monkeypatch.setattr(entry, "_dispatch_topline", _fake_dispatch)
        monkeypatch.setattr(entry, "_dispatch_menu", _fake_dispatch)
        monkeypatch.setattr(entry, "_dispatch_ops", _fake_dispatch)
        monkeypatch.setattr(entry, "_dispatch_campaigns", _fake_dispatch)
        monkeypatch.setattr(entry, "_dispatch_action_plan", _fake_dispatch)

        with pytest.raises(InputSchemaError):
            entry.run(
                client="smoke-test",
                window_start="2026-02-09",
                window_end="2026-05-09",
                inputs_dir=inputs,
            )
        assert calls == [], "Sub-skill dispatch fired despite invalid input"
