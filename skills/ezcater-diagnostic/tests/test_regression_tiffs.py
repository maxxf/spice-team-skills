"""Regression: the core must reproduce the Tiff's Treats audit + live-portal reality.

Ground truth = the human audit (Jun 25 2026) corrected by the live portal exploration
(Jun 26 2026): the badge blocker is delivery tracking, and H4/H14 are PAUSED.
"""
from pathlib import Path

import pandas as pd
import pytest

from ezcater_diagnostic import report, run

FIXTURE = Path(__file__).parent / "fixtures" / "tiffs_treats.csv"

# Portfolio funnel snapshot from the live Sales Performance page (Tiff's, last 30d).
PORTFOLIO = {
    "search_views": 35674, "menu_views": 2471, "orders": 238,
    "conversion_rate_pct": 9.6, "conversion_benchmark_pct": 10.0,
    "new_customers": 163, "existing_customers": 36, "lapsed_customers": 27,
}


@pytest.fixture(scope="module")
def result():
    df = pd.read_csv(FIXTURE)
    return run.run_diagnostic(df, client="tiffs-treats", portfolio=PORTFOLIO)


def _finding(result, pattern_id):
    return next((f for f in result["findings"] if f["pattern_id"] == pattern_id), None)


def test_store_count(result):
    assert result["store_count"] == 175


def test_badge_funnel_tracking_is_the_blocker(result):
    bf = result["badge_funnel"]
    assert bf["total"] == 175
    assert bf["active"] == 106
    assert bf["volume_eligible"] == 31
    assert bf["pass_excl_tracking"] == 16   # pass every goal except delivery tracking
    assert bf["full_pass"] == 0             # self-delivery → 0% tracking everywhere
    assert bf["tracking_blocked_count"] == 16
    assert bf["badged"] == 0


def test_tier_counts(result):
    tc = result["tier_counts"]
    assert tc["new"] == 144   # 69 dark + 75 volume-locked
    assert tc["red"] == 3     # H4 + H14 paused, D19 ops-broken
    assert tc["yellow"] == 28
    assert tc["green"] == 0
    assert sum(tc.values()) == 175


def test_foundation_gate_triggered(result):
    assert result["foundation_gate"]["triggered"] is True


# --- The audit moves + the corrected pause/badge findings ---

def test_pause_is_p0(result):
    f = _finding(result, "store_paused")
    assert f is not None and f["severity"] == "foundation"
    assert set(f["stores"]) == {"H4 Westchase", "H14 Cypress"}


def test_badge_gap_is_tracking(result):
    tracking = _finding(result, "badge_gap_tracking")
    assert tracking is not None and len(tracking["stores"]) == 16
    assert _finding(result, "badge_gap_enrollment") is None  # nothing fully passes


def test_on_time(result):
    f = _finding(result, "on_time_below_badge")
    assert f is not None
    assert len(f["stores"]) == 10  # 8 watch + H14(60) + D19(94); H4 on-time is fine


def test_rejection(result):
    f = _finding(result, "rejection_misconfig")
    assert f is not None and len(f["stores"]) == 4


def test_problem_children(result):
    accuracy = _finding(result, "order_accuracy_low")
    assert accuracy is not None and "D19 Kessler Park" in accuracy["stores"]
    assert accuracy["severity"] == "foundation"


def test_promo_engine(result):
    levers = _finding(result, "levers_all_off")
    dark = _finding(result, "dark_stores")
    locked = _finding(result, "volume_locked")
    assert levers is not None and len(levers["stores"]) == 106
    assert dark is not None and len(dark["stores"]) == 69
    assert locked is not None and len(locked["stores"]) == 75


def test_conversion_vs_peer_fires(result):
    f = _finding(result, "low_conversion_vs_peer")
    assert f is not None  # 9.6% < 10% peer benchmark


def test_radar_has_funnel_dims(result):
    axes = result["radar"]["axes"]
    assert axes.get("Traffic") is not None       # search→menu CTR
    assert axes.get("Conversion") is not None     # vs peer
    assert axes.get("Re-order") is not None        # customer mix


def test_no_false_low_rating(result):
    assert _finding(result, "low_rating") is None


def test_report_renders(result):
    md = report.render_markdown(result)
    assert "Reliability Rockstar Badge Funnel" in md
    assert "Delivery Tracking" in md
