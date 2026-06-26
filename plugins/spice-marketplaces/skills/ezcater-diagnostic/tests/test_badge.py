import pandas as pd

from ezcater_diagnostic import badge, scorers


def _agg(rows):
    return scorers.aggregate_by_store(pd.DataFrame(rows))


def _row(store, **kw):
    base = dict(
        store=store, month=1, platform="EZ", status="active", orders=10, gross_sales=2000.0,
        on_time_pct=99.0, on_time_acceptance_pct=99.0, rejection_rate_pct=0.0,
        order_accuracy_pct=99.5, cancellation_pct=0.0, delivery_tracking_pct=80.0,
        ready_for_dispatch_pct=float("nan"), rating=4.9, review_count=12,
        ppp_bid_pct=0.0, ezrewards_pct=0.0, sponsored_spend=0.0,
        sponsored_attributed_sales=0.0, promo_count_active=0, packaging_complete=1.0,
    )
    base.update(kw)
    return base


def test_full_pass_when_tracking_ok():
    bf = badge.compute_badge_funnel(_agg([_row("a"), _row("b")]))
    assert bf["pass_excl_tracking"] == 2
    assert bf["full_pass"] == 2
    assert bf["tracking_blocked_count"] == 0
    assert bf["enrollment_gap_count"] == 2  # full pass, not badged


def test_tracking_blocked_self_delivery():
    # 0% tracking → pass everything except tracking → tracking-blocked, not full pass.
    bf = badge.compute_badge_funnel(_agg([_row("a", delivery_tracking_pct=0.0), _row("b", delivery_tracking_pct=0.0)]))
    assert bf["pass_excl_tracking"] == 2
    assert bf["full_pass"] == 0
    assert bf["tracking_blocked_count"] == 2
    assert bf["enrollment_gap_count"] == 0


def test_funnel_counts_mixed():
    rows = [
        _row("dark", orders=0, gross_sales=0.0, review_count=0),
        _row("locked", orders=3, review_count=4),
        _row("pass", delivery_tracking_pct=0.0),
        _row("fail_reviews", review_count=5, delivery_tracking_pct=0.0),
        _row("fail_ontime", on_time_pct=96.0, delivery_tracking_pct=0.0),
    ]
    bf = badge.compute_badge_funnel(_agg(rows))
    assert bf["total"] == 5
    assert bf["active"] == 4
    assert bf["volume_eligible"] == 3  # pass, fail_reviews, fail_ontime
    assert bf["pass_excl_tracking"] == 1  # only "pass"
    assert bf["tracking_blocked_count"] == 1


def test_badged_store_excluded_from_gaps():
    bf = badge.compute_badge_funnel(_agg([_row("a"), _row("b", badged=True)]))
    assert bf["badged"] == 1
    assert bf["enrollment_gap_count"] == 1
    assert bf["enrollment_gap_stores"] == ["a"]
