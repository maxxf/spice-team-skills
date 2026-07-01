import pandas as pd

from ezcater_diagnostic import tiering


def _roll(**kw):
    base = dict(orders=10, status="active", ops_flag="healthy", visibility_flag="healthy", packaging_flag="healthy")
    base.update(kw)
    return tiering.rollup_store(**base)


def test_paused_is_red_regardless_of_buckets():
    r = _roll(status="paused", ops_flag="healthy", visibility_flag="healthy", packaging_flag="healthy")
    assert r["tier"] == "red"
    assert "PAUSED" in r["reason"]


def test_paused_low_volume_still_red_not_new():
    r = _roll(orders=2, status="paused")
    assert r["tier"] == "red"


def test_new_when_volume_locked():
    r = _roll(orders=3, visibility_flag="watch")
    assert r["tier"] == "new"
    assert "volume-locked" in r["reason"]


def test_new_dark_store():
    r = _roll(orders=0, visibility_flag="watch")
    assert r["tier"] == "new"
    assert "dark" in r["reason"]


def test_green_all_healthy():
    assert _roll()["tier"] == "green"


def test_yellow_single_watch():
    r = _roll(visibility_flag="watch")
    assert r["tier"] == "yellow"
    assert r["worst_bucket"] == "visibility"


def test_yellow_two_watch_not_red():
    r = _roll(ops_flag="watch", visibility_flag="watch")
    assert r["tier"] == "yellow"


def test_red_any_broken():
    r = _roll(ops_flag="broken", visibility_flag="watch")
    assert r["tier"] == "red"
    assert r["worst_bucket"] == "ops"


def test_foundation_gate_triggers_on_paused():
    df = pd.DataFrame([
        {"store": "P", "orders": 9, "status": "paused", "rating": 5.0, "on_time_pct": 100.0,
         "rejection_rate_pct": 0.0, "order_accuracy_pct": 100.0, "cancellation_pct": 11.1,
         "ready_for_dispatch_pct": float("nan")},
    ])
    gate = tiering.compute_foundation_gate(df)
    assert gate["triggered"] is True
    metrics = {t["metric"] for t in gate["triggers"]}
    assert "status" in metrics
    assert "cancellation_pct" in metrics


def test_foundation_gate_ignores_dark_stores():
    df = pd.DataFrame([
        {"store": "DARK", "orders": 0, "status": "active", "rating": 0.0, "on_time_pct": 0.0,
         "rejection_rate_pct": 0.0, "order_accuracy_pct": 0.0, "cancellation_pct": 0.0,
         "ready_for_dispatch_pct": float("nan")},
    ])
    gate = tiering.compute_foundation_gate(df)
    assert gate["triggered"] is False
