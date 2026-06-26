import math

import pandas as pd

from ezcater_diagnostic import scorers


def _store(**kw):
    base = dict(
        store="S", status="active", orders=10, gross_sales=2000.0,
        on_time_pct=99.0, on_time_acceptance_pct=99.0, rejection_rate_pct=0.0,
        order_accuracy_pct=99.5, cancellation_pct=0.0, delivery_tracking_pct=0.0,
        ready_for_dispatch_pct=float("nan"), rating=4.9, review_count=12,
        ppp_bid_pct=0.0, ezrewards_pct=0.0, sponsored_spend=0.0,
        sponsored_attributed_sales=0.0, promo_count_active=0, packaging_complete=1.0,
    )
    base.update(kw)
    return pd.Series(base)


def test_ops_healthy_meets_badge_goals():
    flag, _ = scorers.classify_ops(_store())
    assert flag == "healthy"


def test_ops_paused_is_broken():
    flag, reasons = scorers.classify_ops(_store(status="paused"))
    assert flag == "broken"
    assert any("PAUSED" in r for r in reasons)


def test_ops_watch_badge_miss_on_time():
    # 97% on-time misses the 98.5 badge goal but clears the 95 pause standard → watch.
    flag, _ = scorers.classify_ops(_store(on_time_pct=97.0))
    assert flag == "watch"


def test_ops_broken_on_time_pause_standard():
    flag, _ = scorers.classify_ops(_store(on_time_pct=60.0))
    assert flag == "broken"


def test_ops_broken_cancellation_pause_standard():
    flag, _ = scorers.classify_ops(_store(cancellation_pct=11.1))
    assert flag == "broken"


def test_ops_watch_small_cancellation_badge_miss():
    # 0.5% cancellation > 0% badge goal but < 3% pause standard → watch, not broken.
    flag, _ = scorers.classify_ops(_store(cancellation_pct=0.5))
    assert flag == "watch"


def test_ops_broken_accuracy_severe():
    flag, _ = scorers.classify_ops(_store(order_accuracy_pct=96.3))
    assert flag == "broken"


def test_ops_at_risk_status_is_watch():
    flag, _ = scorers.classify_ops(_store(status="at_risk"))
    assert flag == "watch"


def test_ops_ready_for_dispatch_pause_standard():
    flag, _ = scorers.classify_ops(_store(ready_for_dispatch_pct=80.0))
    assert flag == "broken"


def test_ops_nan_ready_for_dispatch_ignored():
    # Self-delivery → NaN ready-for-dispatch must not trip the pause standard.
    flag, _ = scorers.classify_ops(_store(ready_for_dispatch_pct=float("nan")))
    assert flag == "healthy"


def test_visibility_levers_off_is_watch():
    flag, _ = scorers.classify_visibility(_store())
    assert flag == "watch"


def test_visibility_healthy_both_levers():
    flag, _ = scorers.classify_visibility(_store(ppp_bid_pct=5.0, ezrewards_pct=5.0))
    assert flag == "healthy"


def test_visibility_broken_low_roas():
    flag, _ = scorers.classify_visibility(_store(sponsored_spend=100.0, sponsored_attributed_sales=200.0))
    assert flag == "broken"


def test_packaging_bands():
    assert scorers.classify_packaging(_store(packaging_complete=1.0))[0] == "healthy"
    assert scorers.classify_packaging(_store(packaging_complete=0.7))[0] == "watch"
    assert scorers.classify_packaging(_store(packaging_complete=0.4))[0] == "broken"


def test_aggregate_sums_sales_keeps_status_and_tracking():
    df = pd.DataFrame([
        _store(store="A", month=1, orders=5, gross_sales=1000.0, rating=4.8, delivery_tracking_pct=0.0),
        _store(store="A", month=2, orders=5, gross_sales=1000.0, rating=5.0, delivery_tracking_pct=0.0, status="paused"),
    ])
    agg = scorers.aggregate_by_store(df)
    assert len(agg) == 1
    assert agg.iloc[0]["orders"] == 10
    assert agg.iloc[0]["gross_sales"] == 2000.0
    assert abs(agg.iloc[0]["rating"] - 4.9) < 1e-9
    assert agg.iloc[0]["status"] == "paused"  # last
    assert math.isnan(agg.iloc[0]["ready_for_dispatch_pct"])
