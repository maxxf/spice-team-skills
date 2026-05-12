from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import pytest
from diagnostic_topline import compute

# Make the orchestrator package importable for the contract validation test
sys.path.insert(0, str(Path("/Users/maxx/Desktop/Cowork/Skills/client-diagnostics")))


def _normal_df():
    return pd.DataFrame({
        "store": ["BeverlyHills", "Venice"] * 10,
        "week": list(range(1, 11)) * 2,
        "gross_sales": [10000, 8000] * 10,
        "orders": [200, 150] * 10,
        "net_payout": [7000, 5500] * 10,
    })


def test_compute_emits_payload_with_required_shape():
    payload = compute.run(client="goop-kitchen", window_start="2026-02-08", window_end="2026-05-08", df=_normal_df())
    assert payload["sub_skill"] == "diagnostic-topline"
    assert payload["client"] == "goop-kitchen"
    assert "AOV" in payload["computed"]["radar_contributions"]
    assert "Re-order Rate" in payload["computed"]["radar_contributions"]
    assert payload["computed"]["metrics"]["gross_sales"] > 0
    assert isinstance(payload["computed"]["findings"], list)


def test_compute_payload_passes_contract_validator():
    from orchestrator import contract
    payload = compute.run(client="x", window_start="2026-01-01", window_end="2026-04-01", df=_normal_df())
    contract.validate(payload)  # no exception


def test_low_payout_emits_foundation_finding():
    df = pd.DataFrame({
        "store": ["A"] * 4, "week": [1, 2, 3, 4],
        "gross_sales": [10000] * 4, "orders": [200] * 4,
        "net_payout": [3000] * 4,  # 30% payout — below 50% triggers foundation finding
    })
    payload = compute.run(client="x", window_start="2026-01-01", window_end="2026-04-01", df=df)
    foundation_findings = [f for f in payload["computed"]["findings"] if f["severity"] == "foundation"]
    assert len(foundation_findings) == 1
    assert foundation_findings[0]["pattern_id"] == "payout_collapse"
