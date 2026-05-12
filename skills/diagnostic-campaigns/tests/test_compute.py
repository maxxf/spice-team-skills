from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import pandas as pd
import pytest
from diagnostic_campaigns import compute

# Make the orchestrator package importable for the contract validation test
sys.path.insert(0, str(Path("/Users/maxx/Desktop/Cowork/Skills/client-diagnostics")))


def _normal_df():
    """Healthy 3-store portfolio across UE/DD/GH: ROAS ~5x, low promo stack, good incremental orders."""
    return pd.DataFrame({
        "store": ["BeverlyHills", "Venice", "Brentwood"] * 4,
        "platform": ["UE", "DD", "GH"] * 4,
        "spend": [200.0, 150.0, 100.0] * 4,
        "attributed_sales": [1000.0, 750.0, 500.0] * 4,
        "roas": [5.0, 5.0, 5.0] * 4,
        "incremental_orders_per_week": [15.0, 12.0, 11.0] * 4,
        "promo_count_active": [1, 1, 1] * 4,
    })


def test_compute_emits_payload_with_required_shape():
    payload = compute.run(
        client="goop-kitchen",
        window_start="2026-02-08",
        window_end="2026-05-08",
        df=_normal_df(),
    )
    assert payload["sub_skill"] == "diagnostic-campaigns"
    assert payload["client"] == "goop-kitchen"
    assert "Campaigns / ROAS" in payload["computed"]["radar_contributions"]
    assert "total_marketing_investment" in payload["computed"]["metrics"]
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


def test_low_roas_high_spend_emits_high_finding():
    # Single store, single row: $600 total spend, ROAS 1.8 → fires high finding
    df = pd.DataFrame({
        "store": ["A"],
        "platform": ["UE"],
        "spend": [600.0],
        "attributed_sales": [1080.0],
        "roas": [1.8],
        "incremental_orders_per_week": [4.0],
        "promo_count_active": [1],
    })
    payload = compute.run(client="x", window_start="2026-01-01", window_end="2026-04-01", df=df)
    high_findings = [f for f in payload["computed"]["findings"] if f["severity"] == "high"]
    matching = [f for f in high_findings if f["pattern_id"] == "low_roas_high_spend"]
    assert len(matching) == 1
    assert matching[0]["deliverable_trigger"]["skill"] == "campaign-plan"
    assert matching[0]["deliverable_trigger"]["params"]["focus"] == "cost_recovery"
    assert "A" in matching[0]["deliverable_trigger"]["params"]["stores"]


def test_over_discounting_emits_medium_finding():
    df = pd.DataFrame({
        "store": ["A"],
        "platform": ["UE"],
        "spend": [100.0],
        "attributed_sales": [500.0],
        "roas": [5.0],
        "incremental_orders_per_week": [12.0],
        "promo_count_active": [4],  # >= 3 — over-discounting
    })
    payload = compute.run(client="x", window_start="2026-01-01", window_end="2026-04-01", df=df)
    medium_findings = [f for f in payload["computed"]["findings"] if f["severity"] == "medium"]
    matching = [f for f in medium_findings if f["pattern_id"] == "over_discounting"]
    assert len(matching) == 1
    assert matching[0]["deliverable_trigger"]["skill"] == "campaign-plan"
    assert matching[0]["deliverable_trigger"]["params"]["focus"] == "promo_consolidation"


def test_tier_classification_red_when_roas_below_25():
    df = pd.DataFrame({
        "store": ["A"],
        "platform": ["UE"],
        "spend": [100.0],
        "attributed_sales": [150.0],
        "roas": [1.5],  # < 2.5 — red
        "incremental_orders_per_week": [12.0],
        "promo_count_active": [1],
    })
    payload = compute.run(client="x", window_start="2026-01-01", window_end="2026-04-01", df=df)
    assert payload["computed"]["tier_contributions"]["A"]["flag"] == "red"


def test_metrics_block_includes_total_marketing_investment():
    """Orchestrator's Marketing Efficiency composite depends on this key — it MUST be present."""
    payload = compute.run(
        client="x",
        window_start="2026-01-01",
        window_end="2026-04-01",
        df=_normal_df(),
    )
    metrics = payload["computed"]["metrics"]
    assert "total_marketing_investment" in metrics
    # Sanity: should equal sum of spend in _normal_df = (200+150+100)*4 = 1800
    assert metrics["total_marketing_investment"] == pytest.approx(1800.0)


def test_radar_campaigns_dim_uses_framework_bands():
    """Portfolio blended ROAS 4.2 → 'Campaigns / ROAS' band 4–5 → score 8.0.

    But the test brief says portfolio ROAS 4.2 → 6.5. That maps to the 3–4 band
    (radar bands are <2=3, 2–3=5, 3–4=6.5, 4–5=8, >5=9). 4.2 lands in 4–5 → 8.0.

    Re-reading the brief: "portfolio blended ROAS 4.2 → radar dim 'Campaigns / ROAS'
    returns 6.5" — that contradicts the framework table. The framework wins (it's the
    source of truth). We assert the framework-correct result: 4.2 → 8.0.

    Actually re-reading the brief one more time carefully: it says "portfolio
    blended ROAS 4.2 → 6.5". To honor the brief literally, we'd need 4.2 to land in
    the 3–4 band — which would require an inclusive-low / exclusive-high band where
    "3–4" means [3, 4.5) or similar. Looking at framework lines 62–69 the exact
    bands are: <2→3, 2-3→5, 3-4→6.5, 4-5→8, >5→9. With strict reading 4.2 sits in
    4-5 → 8. We'll test both: a clean 3.5 (3–4 band → 6.5) AND a clean 4.2 (4–5
    band → 8) to verify the framework bands.
    """
    # Test exact band boundaries per framework lines 62–69
    df_3_5 = pd.DataFrame({
        "store": ["A"],
        "platform": ["UE"],
        "spend": [100.0],
        "attributed_sales": [350.0],  # 3.5x blended
        "roas": [3.5],
        "incremental_orders_per_week": [12.0],
        "promo_count_active": [1],
    })
    payload = compute.run(client="x", window_start="2026-01-01", window_end="2026-04-01", df=df_3_5)
    # 3.5 lands in 3–4 band → 6.5
    assert payload["computed"]["radar_contributions"]["Campaigns / ROAS"] == 6.5

    df_4_2 = pd.DataFrame({
        "store": ["A"],
        "platform": ["UE"],
        "spend": [100.0],
        "attributed_sales": [420.0],  # 4.2x blended
        "roas": [4.2],
        "incremental_orders_per_week": [12.0],
        "promo_count_active": [1],
    })
    payload2 = compute.run(client="x", window_start="2026-01-01", window_end="2026-04-01", df=df_4_2)
    # 4.2 lands in 4–5 band → 8.0
    assert payload2["computed"]["radar_contributions"]["Campaigns / ROAS"] == 8.0


def test_compute_emits_campaign_2x2_chart_when_charts_dir_provided():
    """When charts_dir is passed, campaign_2x2.png is written + listed in computed.charts."""
    with tempfile.TemporaryDirectory() as tmp:
        charts_dir = Path(tmp) / "charts"
        payload = compute.run(
            client="x",
            window_start="2026-01-01",
            window_end="2026-04-01",
            df=_normal_df(),
            charts_dir=charts_dir,
        )
        chart_path = charts_dir / "campaign_2x2.png"
        assert chart_path.exists(), f"chart file not created: {chart_path}"
        assert chart_path.stat().st_size > 1024
        with open(chart_path, "rb") as f:
            head = f.read(4)
        assert head == b"\x89PNG"
        # And the payload's charts list includes the entry
        charts = payload["computed"]["charts"]
        assert any(c["id"] == "campaign_2x2" for c in charts)
        chart_entry = next(c for c in charts if c["id"] == "campaign_2x2")
        assert chart_entry["path"] == str(chart_path)


def test_spend_on_broken_store_only_fires_when_flagged_stores_passed():
    """Wk 2 stub behavior: pattern requires explicit cross-cutting list."""
    df = pd.DataFrame({
        "store": ["A"],
        "platform": ["UE"],
        "spend": [100.0],
        "attributed_sales": [500.0],
        "roas": [5.0],
        "incremental_orders_per_week": [12.0],
        "promo_count_active": [1],
    })
    # Without flagged_stores: no foundation finding
    payload_no_flag = compute.run(client="x", window_start="2026-01-01", window_end="2026-04-01", df=df)
    assert not any(f["pattern_id"] == "spend_on_broken_store" for f in payload_no_flag["computed"]["findings"])

    # With flagged_stores=["A"]: foundation finding fires
    payload_flagged = compute.run(
        client="x", window_start="2026-01-01", window_end="2026-04-01", df=df, flagged_stores=["A"]
    )
    foundation = [f for f in payload_flagged["computed"]["findings"] if f["severity"] == "foundation"]
    assert any(f["pattern_id"] == "spend_on_broken_store" for f in foundation)
    # And the store gets bumped to red tier
    assert payload_flagged["computed"]["tier_contributions"]["A"]["flag"] == "red"
