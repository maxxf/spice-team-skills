import pytest
from orchestrator import contract


def _valid_payload(sub_skill: str = "diagnostic-topline") -> dict:
    return {
        "sub_skill": sub_skill,
        "version": "1.0",
        "client": "goop-kitchen",
        "window": {"start": "2026-02-08", "end": "2026-05-08"},
        "computed": {
            "metrics": {"gross_sales": 1500000},
            "radar_contributions": {"AOV": 7.2, "Re-order Rate": 6.1},
            "tier_contributions": {
                "BeverlyHills": {"score": 8.0, "flag": "green", "reasons": ["high CVR"]}
            },
            "findings": [
                {
                    "pattern_id": "revenue_down_traffic_stable",
                    "severity": "high",
                    "scope": "BeverlyHills",
                    "evidence": {"weeks": 4, "delta_pct": -12.5},
                    "estimated_impact_usd": 12000,
                    "deliverable_trigger": {"skill": "optimized-menu-sheet", "params": {"stores": ["BeverlyHills"]}},
                }
            ],
            "charts": [{"id": "sparklines", "path": "topline/charts/sparklines.png"}],
        },
        "drafted": {
            "toggle_title": "Top-line Performance",
            "toggle_prose": "...",
            "win_risk_opp_candidates": [
                {"type": "risk", "headline": "BH revenue down 12%", "value_usd": 12000, "pattern_id": "revenue_down_traffic_stable"}
            ],
        },
        "data_quality": {"completeness": 0.95, "gaps": []},
    }


def test_valid_payload_passes_validator():
    contract.validate(_valid_payload())


def test_missing_required_field_fails():
    p = _valid_payload()
    del p["computed"]["radar_contributions"]
    with pytest.raises(contract.ContractError):
        contract.validate(p)


def test_invalid_severity_fails():
    p = _valid_payload()
    p["computed"]["findings"][0]["severity"] = "critical"  # not in enum
    with pytest.raises(contract.ContractError):
        contract.validate(p)


def test_invalid_wro_type_fails():
    p = _valid_payload()
    p["drafted"]["win_risk_opp_candidates"][0]["type"] = "celebration"  # not in enum
    with pytest.raises(contract.ContractError):
        contract.validate(p)


def test_computed_hash_is_stable_across_drafted_changes():
    p1 = _valid_payload()
    p2 = _valid_payload()
    p2["drafted"]["toggle_prose"] = "totally different prose"
    p2["data_quality"]["completeness"] = 0.7
    assert contract.computed_hash(p1) == contract.computed_hash(p2)


def test_computed_hash_excludes_chart_paths():
    p1 = _valid_payload()
    p2 = _valid_payload()
    p2["computed"]["charts"][0]["path"] = "topline/charts/sparklines-DIFFERENT.png"
    assert contract.computed_hash(p1) == contract.computed_hash(p2)


def test_computed_hash_excludes_evidence():
    p1 = _valid_payload()
    p2 = _valid_payload()
    p2["computed"]["findings"][0]["evidence"] = {"foo": "bar", "ts": "2026-05-08T14:30:00"}
    assert contract.computed_hash(p1) == contract.computed_hash(p2)


def test_computed_hash_changes_when_metric_changes():
    p1 = _valid_payload()
    p2 = _valid_payload()
    p2["computed"]["metrics"]["gross_sales"] = 1600000
    assert contract.computed_hash(p1) != contract.computed_hash(p2)
