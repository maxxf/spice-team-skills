"""Regression tests for discrete DoorDash downtime EVENT detection in the ops
bucket, and for demoting promo-count from a campaigns tier trigger to a note.

Root cause these lock down:
  1. A store whose 90-day AVERAGES look Healthy (uptime 99%, error 1%, rating
     4.8) but that had an involuntary DoorDash auto-pause during the window was
     scored "green" because the run averaged the event away. Discrete
     involuntary events (auto-pause on high avoidable/POS cancel rate, or a
     dasher-reported store closure) MUST drive ops -> Broken -> tier Red,
     overriding the smoothed averages.
  2. Promo stack >= 2 concurrent promos used to force a campaigns "Watch"
     (yellow). Promo count is now a NOTED observation only, never a tier
     determinant. ROAS + incremental-order criteria still drive the tier.

These import the sibling sub-skill packages directly (they have no venv of
their own; the client-diagnostics venv carries pandas).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_SKILLS_ROOT = Path(__file__).resolve().parents[2]
for _short in ("ops", "campaigns"):
    _p = str(_SKILLS_ROOT / f"diagnostic-{_short}")
    if _p not in sys.path:
        sys.path.insert(0, _p)
# client-diagnostics itself (orchestrator package) for the tier rollup
_p = str(_SKILLS_ROOT / "client-diagnostics")
if _p not in sys.path:
    sys.path.insert(0, _p)

from diagnostic_ops import compute as ops_compute  # noqa: E402
from diagnostic_campaigns import compute as campaigns_compute  # noqa: E402
from orchestrator import cross_cutting  # noqa: E402


def _healthy_ops_rows(store: str, **event_overrides) -> pd.DataFrame:
    """A store with textbook-healthy smoothed averages across a few rows.

    uptime 99%, error 1%, rating 4.8, cancel 1% — nothing in the averages would
    ever flag this store. Event columns default to 0; override per test.
    """
    base = {
        "store": [store] * 3,
        "rating": [4.8, 4.8, 4.8],
        "error_rate_pct": [1.0, 1.0, 1.0],
        "cancellation_pct": [1.0, 1.0, 1.0],
        "uptime_pct": [99.0, 99.0, 99.0],
        "hours_accurate": [True, True, True],
        # ops-event columns — additive across rows, so put the whole window
        # total on the first row and 0 on the rest.
        "auto_pause_involuntary_min": [0, 0, 0],
        "dasher_closure_min": [0, 0, 0],
        "merchant_closure_min": [0, 0, 0],
        "dasher_wait_pause_min": [0, 0, 0],
        "avoidable_ops_cancels": [0, 0, 0],
    }
    for col, total in event_overrides.items():
        base[col] = [total, 0, 0]
    return pd.DataFrame(base)


def _run_ops(df: pd.DataFrame) -> dict:
    return ops_compute.run(
        client="t", window_start="2026-04-13", window_end="2026-07-12", df=df
    )


# --- 1. involuntary event overrides healthy averages -----------------------

def test_involuntary_auto_pause_forces_ops_broken_red_despite_healthy_averages():
    df = _healthy_ops_rows("NoMad", auto_pause_involuntary_min=594)
    payload = _run_ops(df)
    tc = payload["computed"]["tier_contributions"]["NoMad"]
    assert tc["flag"] == "red", tc
    # tier rollup must carry the red through to the store-level verdict
    rollup = cross_cutting.rollup_tiers({"ops": payload["computed"]["tier_contributions"]})
    assert rollup["NoMad"]["flag"] == "red"


def test_dasher_reported_closure_forces_ops_broken_red():
    df = _healthy_ops_rows("Midtown East", dasher_closure_min=297)
    tc = _run_ops(df)["computed"]["tier_contributions"]["Midtown East"]
    assert tc["flag"] == "red", tc


# --- 2. intentional / capacity events are Watch, not Red -------------------

def test_merchant_triggered_closure_is_watch_not_red():
    df = _healthy_ops_rows("Soho", merchant_closure_min=409)
    tc = _run_ops(df)["computed"]["tier_contributions"]["Soho"]
    assert tc["flag"] == "yellow", tc


def test_dasher_wait_pause_is_watch_not_red():
    df = _healthy_ops_rows("Flatiron", dasher_wait_pause_min=150)
    tc = _run_ops(df)["computed"]["tier_contributions"]["Flatiron"]
    assert tc["flag"] == "yellow", tc


def test_involuntary_event_wins_over_intentional_closure():
    # Rock Center: both an involuntary auto-pause AND a merchant closure -> Red.
    df = _healthy_ops_rows(
        "Rock Center", auto_pause_involuntary_min=23, merchant_closure_min=90
    )
    tc = _run_ops(df)["computed"]["tier_contributions"]["Rock Center"]
    assert tc["flag"] == "red", tc


def test_clean_store_with_no_events_stays_green():
    df = _healthy_ops_rows("NYP")
    tc = _run_ops(df)["computed"]["tier_contributions"]["NYP"]
    assert tc["flag"] == "green", tc


# --- 3. backward compatibility: no event columns at all --------------------

def test_ops_backward_compatible_when_event_columns_absent():
    df = pd.DataFrame({
        "store": ["A", "A"],
        "rating": [4.8, 4.8],
        "error_rate_pct": [1.0, 1.0],
        "cancellation_pct": [1.0, 1.0],
        "uptime_pct": [99.0, 99.0],
        "hours_accurate": [True, True],
    })
    tc = _run_ops(df)["computed"]["tier_contributions"]["A"]
    assert tc["flag"] == "green", tc


# --- 4. promo count is NOT a tier determinant ------------------------------

def _campaigns_df(store: str, promo_count: int) -> pd.DataFrame:
    """Healthy campaigns store: ROAS 4.0x (>= 3.5 healthy), 15 incremental
    orders/wk (>= 10 healthy), modest spend. Only the promo stack differs."""
    return pd.DataFrame({
        "store": [store],
        "spend": [100.0],
        "attributed_sales": [400.0],
        "roas": [4.0],
        "incremental_orders_per_week": [15.0],
        "promo_count_active": [promo_count],
    })


def test_promo_stack_does_not_downgrade_a_healthy_store():
    payload = campaigns_compute.run(
        client="t", window_start="2026-04-13", window_end="2026-07-12",
        df=_campaigns_df("Discounter", promo_count=5),
    )
    tc = payload["computed"]["tier_contributions"]["Discounter"]
    assert tc["flag"] == "green", tc
    # and no reason string should cite promo stacking as a watch trigger
    joined = " ".join(tc["reasons"]).lower()
    assert "promos stacked (watch)" not in joined


def test_promo_stack_still_surfaces_as_a_note_finding():
    """Demoted, not deleted: over-discounting stays a low-severity observation
    with no internal skill name leaked into the deliverable trigger."""
    payload = campaigns_compute.run(
        client="t", window_start="2026-04-13", window_end="2026-07-12",
        df=_campaigns_df("Discounter", promo_count=5),
    )
    notes = [f for f in payload["computed"]["findings"] if f["pattern_id"] == "over_discounting"]
    assert notes, "over_discounting note should still be emitted"
    assert notes[0]["severity"] == "low"
    assert notes[0]["deliverable_trigger"]["skill"] == ""
