from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import pytest
from diagnostic_ops import compute

# Make the orchestrator package importable for the contract validation test
sys.path.insert(0, str(Path("/Users/maxx/Desktop/Cowork/Skills/client-diagnostics")))


def _normal_df():
    """Healthy 3-store portfolio: rating ~4.6, error <2%, cancel <2%, uptime >97%, hours accurate."""
    return pd.DataFrame({
        "store": ["BeverlyHills", "Venice", "Brentwood"] * 4,
        "rating": [4.7, 4.6, 4.5] * 4,
        "error_rate_pct": [1.2, 1.5, 1.8] * 4,
        "cancellation_pct": [1.0, 1.5, 1.2] * 4,
        "uptime_pct": [98.5, 98.0, 97.5] * 4,
        "hours_accurate": [True, True, True] * 4,
    })


def test_compute_emits_payload_with_required_shape():
    payload = compute.run(
        client="goop-kitchen",
        window_start="2026-02-08",
        window_end="2026-05-08",
        df=_normal_df(),
    )
    assert payload["sub_skill"] == "diagnostic-ops"
    assert payload["client"] == "goop-kitchen"
    # Ops emits NO direct radar dims — orchestrator composes Operations from tier_contributions
    assert payload["computed"]["radar_contributions"] == {}
    assert "rating" in payload["computed"]["metrics"]
    assert "error_rate_pct" in payload["computed"]["metrics"]
    assert "uptime_pct" in payload["computed"]["metrics"]
    assert isinstance(payload["computed"]["findings"], list)
    assert isinstance(payload["computed"]["tier_contributions"], dict)
    # tier_contributions populated for every store in the input
    assert set(payload["computed"]["tier_contributions"].keys()) == {"BeverlyHills", "Venice", "Brentwood"}


def test_compute_payload_passes_contract_validator():
    from orchestrator import contract
    payload = compute.run(
        client="x",
        window_start="2026-01-01",
        window_end="2026-04-01",
        df=_normal_df(),
    )
    contract.validate(payload)  # no exception


def test_low_rating_emits_foundation_finding():
    df = pd.DataFrame({
        "store": ["A"] * 4,
        "rating": [4.0] * 4,  # < 4.2 — Stop Everything
        "error_rate_pct": [1.0] * 4,
        "cancellation_pct": [1.0] * 4,
        "uptime_pct": [98.0] * 4,
        "hours_accurate": [True] * 4,
    })
    payload = compute.run(client="x", window_start="2026-01-01", window_end="2026-04-01", df=df)
    foundation_findings = [f for f in payload["computed"]["findings"] if f["severity"] == "foundation"]
    rating_findings = [f for f in foundation_findings if f["pattern_id"] == "low_rating_below_42"]
    assert len(rating_findings) == 1
    assert rating_findings[0]["deliverable_trigger"]["skill"] == "ratings-flyer"
    assert "A" in rating_findings[0]["deliverable_trigger"]["params"]["stores"]


def test_error_spike_emits_foundation_finding():
    df = pd.DataFrame({
        "store": ["A"] * 4,
        "rating": [4.6] * 4,
        "error_rate_pct": [7.0] * 4,  # > 5% — Stop Everything
        "cancellation_pct": [1.0] * 4,
        "uptime_pct": [98.0] * 4,
        "hours_accurate": [True] * 4,
    })
    payload = compute.run(client="x", window_start="2026-01-01", window_end="2026-04-01", df=df)
    foundation_findings = [f for f in payload["computed"]["findings"] if f["severity"] == "foundation"]
    error_findings = [f for f in foundation_findings if f["pattern_id"] == "error_spike"]
    assert len(error_findings) == 1


def test_tier_classification_red_when_uptime_below_90():
    df = pd.DataFrame({
        "store": ["A"] * 4,
        "rating": [4.6] * 4,
        "error_rate_pct": [1.0] * 4,
        "cancellation_pct": [1.0] * 4,
        "uptime_pct": [85.0] * 4,  # < 90% — red trigger via uptime
        "hours_accurate": [True] * 4,
    })
    payload = compute.run(client="x", window_start="2026-01-01", window_end="2026-04-01", df=df)
    assert payload["computed"]["tier_contributions"]["A"]["flag"] == "red"


def test_metrics_block_includes_foundation_gate_inputs():
    """Orchestrator's foundation gate depends on these keys — they MUST be present."""
    payload = compute.run(
        client="x",
        window_start="2026-01-01",
        window_end="2026-04-01",
        df=_normal_df(),
    )
    metrics = payload["computed"]["metrics"]
    assert "rating" in metrics
    assert "error_rate_pct" in metrics
    assert "uptime_pct" in metrics


def test_customer_sentiment_star_derived_when_no_explicit_column():
    """No customer_sentiment_pct column → derive from normalized star rating."""
    payload = compute.run(
        client="x", window_start="2026-01-01", window_end="2026-04-01",
        df=_normal_df(),  # rating mean = 4.6 → (4.6-1)/4 = 90.0%
    )
    m = payload["computed"]["metrics"]
    assert m["rating_basis"] == "star-derived"
    assert m["customer_sentiment_pct"] == 90.0


def test_customer_sentiment_uses_explicit_volume_weighted_column():
    """customer_sentiment_pct + rating_count present → volume-weighted blend."""
    df = pd.DataFrame({
        "store": ["A", "B"] * 2,
        "rating": [4.6, 4.6] * 2,
        "error_rate_pct": [1.0, 1.0] * 2,
        "cancellation_pct": [1.0, 1.0] * 2,
        "uptime_pct": [98.0, 98.0] * 2,
        "hours_accurate": [True, True] * 2,
        "customer_sentiment_pct": [60.0, 90.0] * 2,
        "rating_count": [100, 300] * 2,  # weighted → (60*100+90*300)/400 = 82.5
    })
    payload = compute.run(client="x", window_start="2026-01-01", window_end="2026-04-01", df=df)
    m = payload["computed"]["metrics"]
    assert m["rating_basis"] == "unified-positive-rate"
    assert m["customer_sentiment_pct"] == 82.5


def test_cancellation_surge_emits_high_finding():
    df = pd.DataFrame({
        "store": ["A"] * 4,
        "rating": [4.6] * 4,
        "error_rate_pct": [1.0] * 4,
        "cancellation_pct": [7.0] * 4,  # > 5%
        "uptime_pct": [98.0] * 4,
        "hours_accurate": [True] * 4,
    })
    payload = compute.run(client="x", window_start="2026-01-01", window_end="2026-04-01", df=df)
    high_findings = [f for f in payload["computed"]["findings"] if f["severity"] == "high"]
    matching = [f for f in high_findings if f["pattern_id"] == "cancellation_surge"]
    assert len(matching) == 1
