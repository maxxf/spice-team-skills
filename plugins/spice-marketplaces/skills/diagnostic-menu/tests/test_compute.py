from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import pytest
from diagnostic_menu import compute

# Make the orchestrator package importable for the contract validation test
sys.path.insert(0, str(Path("/Users/maxx/Desktop/Cowork/Skills/client-diagnostics")))


def _normal_df():
    """Healthy 3-store portfolio: CVR ~20%, photos ~85%, hero set, all categories populated."""
    return pd.DataFrame({
        "store": ["BeverlyHills", "Venice", "Brentwood"] * 4,
        "menu_cvr_pct": [22.0, 19.0, 20.0] * 4,
        "photo_coverage_pct": [88.0, 82.0, 90.0] * 4,
        "hero_set": [True, True, True] * 4,
        "categories_count": [6, 6, 6] * 4,
        "categories_populated": [6, 6, 6] * 4,
        "storefront_to_menu_ctr_pct": [10.0, 9.5, 11.0] * 4,
    })


def test_compute_emits_payload_with_required_shape():
    payload = compute.run(
        client="goop-kitchen",
        window_start="2026-02-08",
        window_end="2026-05-08",
        df=_normal_df(),
    )
    assert payload["sub_skill"] == "diagnostic-menu"
    assert payload["client"] == "goop-kitchen"
    assert "Conversion" in payload["computed"]["radar_contributions"]
    assert "Traffic" in payload["computed"]["radar_contributions"]
    assert "menu_cvr_pct" in payload["computed"]["metrics"]
    assert "photo_coverage_pct" in payload["computed"]["metrics"]
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


def test_low_photo_coverage_emits_foundation_finding():
    df = pd.DataFrame({
        "store": ["A"] * 4,
        "menu_cvr_pct": [20.0] * 4,
        "photo_coverage_pct": [30.0] * 4,  # < 50% — Stop Everything
        "hero_set": [True] * 4,
        "categories_count": [5] * 4,
        "categories_populated": [5] * 4,
        "storefront_to_menu_ctr_pct": [8.0] * 4,
    })
    payload = compute.run(client="x", window_start="2026-01-01", window_end="2026-04-01", df=df)
    foundation_findings = [f for f in payload["computed"]["findings"] if f["severity"] == "foundation"]
    photo_findings = [f for f in foundation_findings if f["pattern_id"] == "low_photo_coverage"]
    assert len(photo_findings) == 1


def test_low_cvr_high_traffic_emits_high_finding():
    df = pd.DataFrame({
        "store": ["A"] * 4,
        "menu_cvr_pct": [12.0] * 4,
        "photo_coverage_pct": [85.0] * 4,
        "hero_set": [True] * 4,
        "categories_count": [5] * 4,
        "categories_populated": [5] * 4,
        "storefront_to_menu_ctr_pct": [11.0] * 4,
    })
    payload = compute.run(client="x", window_start="2026-01-01", window_end="2026-04-01", df=df)
    high_findings = [f for f in payload["computed"]["findings"] if f["severity"] == "high"]
    matching = [f for f in high_findings if f["pattern_id"] == "low_cvr_high_traffic"]
    assert len(matching) == 1
    assert matching[0]["deliverable_trigger"]["skill"] == "optimized-menu-sheet"
    assert matching[0]["deliverable_trigger"]["params"]["focus"] == "category_consolidation"


def test_tier_classification_red_when_photos_below_50():
    df = pd.DataFrame({
        "store": ["A"] * 4,
        "menu_cvr_pct": [20.0] * 4,
        "photo_coverage_pct": [30.0] * 4,  # red trigger via photos
        "hero_set": [True] * 4,
        "categories_count": [5] * 4,
        "categories_populated": [5] * 4,
        "storefront_to_menu_ctr_pct": [8.0] * 4,
    })
    payload = compute.run(client="x", window_start="2026-01-01", window_end="2026-04-01", df=df)
    assert payload["computed"]["tier_contributions"]["A"]["flag"] == "red"


def test_radar_conversion_dim_uses_framework_bands():
    # Portfolio mean CVR = 22% → Conversion band 20–25 → score 7
    df = pd.DataFrame({
        "store": ["A", "B"] * 2,
        "menu_cvr_pct": [22.0, 22.0] * 2,
        "photo_coverage_pct": [85.0, 85.0] * 2,
        "hero_set": [True, True] * 2,
        "categories_count": [5, 5] * 2,
        "categories_populated": [5, 5] * 2,
        "storefront_to_menu_ctr_pct": [10.0, 10.0] * 2,
    })
    payload = compute.run(client="x", window_start="2026-01-01", window_end="2026-04-01", df=df)
    assert payload["computed"]["radar_contributions"]["Conversion"] == 7
