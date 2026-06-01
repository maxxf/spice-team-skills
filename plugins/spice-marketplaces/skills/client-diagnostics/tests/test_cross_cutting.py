import pytest
from orchestrator import cross_cutting as xc


def _payload(sub_skill, radar=None, tier=None, findings=None, w_r_o=None, metrics=None):
    return {
        "sub_skill": sub_skill,
        "computed": {
            "metrics": metrics or {},
            "radar_contributions": radar or {},
            "tier_contributions": tier or {},
            "findings": findings or [],
            "charts": [],
        },
        "drafted": {"toggle_title": "", "toggle_prose": "", "win_risk_opp_candidates": w_r_o or []},
        "data_quality": {"completeness": 1.0, "gaps": []},
    }


def test_radar_assembly_uses_owners_per_spec():
    payloads = {
        "topline": _payload("diagnostic-topline", radar={"AOV": 7.2, "Re-order Rate": 6.1}),
        "menu": _payload("diagnostic-menu", radar={"Conversion": 5.5, "Traffic": 6.8}),
        "ops": _payload("diagnostic-ops", tier={
            "Store1": {"score": 9, "flag": "green", "reasons": []},
            "Store2": {"score": 4, "flag": "red", "reasons": []},
            "Store3": {"score": 7, "flag": "green", "reasons": []},
        }),
        "campaigns": _payload("diagnostic-campaigns", radar={"Campaigns / ROAS": 4.2}),
    }
    radar = xc.assemble_radar(payloads, topline_metrics={"gross_sales": 1_000_000}, campaigns_metrics={"total_marketing_investment": 200_000})

    assert radar["AOV"] == 7.2
    assert radar["Re-order Rate"] == 6.1
    assert radar["Conversion"] == 5.5
    assert radar["Traffic"] == 6.8
    assert radar["Campaigns / ROAS"] == 4.2
    # Marketing Efficiency = 1 - (mkt / gross), benchmarked vs 30%, scaled 1-10
    assert 0 <= radar["Marketing Efficiency"] <= 10
    # Operations: 2 of 3 not red = 66.7% → ~6.7
    assert 6.0 <= radar["Operations"] <= 7.5


def test_tier_rollup_red_wins():
    contribs = {
        "menu":  {"Store1": {"score": 8, "flag": "green",  "reasons": []}},
        "ops":   {"Store1": {"score": 4, "flag": "red",    "reasons": []}},
        "campaigns": {"Store1": {"score": 6, "flag": "yellow", "reasons": []}},
    }
    rollup = xc.rollup_tiers(contribs)
    assert rollup["Store1"]["flag"] == "red"
    assert rollup["Store1"]["worst_bucket"] == "ops"


def test_tier_rollup_yellow_when_no_red():
    contribs = {
        "menu":  {"Store1": {"score": 8, "flag": "green",  "reasons": []}},
        "ops":   {"Store1": {"score": 6, "flag": "yellow", "reasons": []}},
        "campaigns": {"Store1": {"score": 7, "flag": "green",  "reasons": []}},
    }
    rollup = xc.rollup_tiers(contribs)
    assert rollup["Store1"]["flag"] == "yellow"


def test_tier_rollup_new_when_any_bucket_new():
    contribs = {
        "menu":  {"Store1": {"score": 8, "flag": "green", "reasons": []}},
        "ops":   {"Store1": {"score": 0, "flag": "new",   "reasons": []}},
        "campaigns": {"Store1": {"score": 7, "flag": "green", "reasons": []}},
    }
    rollup = xc.rollup_tiers(contribs)
    assert rollup["Store1"]["flag"] == "new"


def test_tier_rollup_all_green():
    contribs = {
        "menu":  {"Store1": {"score": 8, "flag": "green", "reasons": []}},
        "ops":   {"Store1": {"score": 9, "flag": "green", "reasons": []}},
        "campaigns": {"Store1": {"score": 7, "flag": "green", "reasons": []}},
    }
    rollup = xc.rollup_tiers(contribs)
    assert rollup["Store1"]["flag"] == "green"


def test_tier_rollup_ignores_buckets_with_no_data_for_a_store():
    """Store present in menu+ops but missing from campaigns should NOT be flagged 'new'."""
    contribs = {
        "menu":  {"BeverlyHills": {"score": 8, "flag": "green", "reasons": []}},
        "ops":   {"BeverlyHills": {"score": 7, "flag": "green", "reasons": []}},
        "campaigns": {},  # campaigns sub-skill has no data for this store (no active campaign)
    }
    rollup = xc.rollup_tiers(contribs)
    assert rollup["BeverlyHills"]["flag"] == "green"
    assert rollup["BeverlyHills"]["worst_bucket"] in ("menu", "ops")
    # only present buckets in the per-bucket dict
    assert "campaigns" not in rollup["BeverlyHills"]["per_bucket_flags"]


def test_wro_dedup_keeps_higher_value():
    payloads = {
        "menu": _payload("diagnostic-menu", w_r_o=[
            {"type": "risk", "headline": "Pricing", "value_usd": 5000, "pattern_id": "pricing"}
        ]),
        "campaigns": _payload("diagnostic-campaigns", w_r_o=[
            {"type": "risk", "headline": "Pricing-camp", "value_usd": 8000, "pattern_id": "pricing"}
        ]),
        "ops": _payload("diagnostic-ops"),
        "topline": _payload("diagnostic-topline"),
    }
    selected = xc.select_win_risk_opp(payloads)
    risks = [c for c in selected if c["type"] == "risk"]
    assert len(risks) == 1
    assert risks[0]["value_usd"] == 8000


def test_wro_top_picks_one_per_type_when_available():
    payloads = {
        "menu": _payload("diagnostic-menu", w_r_o=[
            {"type": "risk", "headline": "A", "value_usd": 1000},
            {"type": "risk", "headline": "B", "value_usd": 9000},
        ]),
        "ops": _payload("diagnostic-ops", w_r_o=[
            {"type": "risk", "headline": "C", "value_usd": 5000},
            {"type": "win", "headline": "W", "value_usd": 3000},
            {"type": "opportunity", "headline": "O", "value_usd": 2000},
        ]),
        "campaigns": _payload("diagnostic-campaigns"),
        "topline": _payload("diagnostic-topline"),
    }
    selected = xc.select_win_risk_opp(payloads)
    types = {c["type"] for c in selected}
    assert types == {"win", "risk", "opportunity"}
    risk = next(c for c in selected if c["type"] == "risk")
    assert risk["headline"] == "B"  # highest value risk


def test_wro_null_value_sorts_last():
    payloads = {
        "menu": _payload("diagnostic-menu", w_r_o=[
            {"type": "risk", "headline": "Has-value", "value_usd": 1000},
            {"type": "risk", "headline": "No-value", "value_usd": None},
        ]),
        "ops": _payload("diagnostic-ops"),
        "campaigns": _payload("diagnostic-campaigns"),
        "topline": _payload("diagnostic-topline"),
    }
    risk = next(c for c in xc.select_win_risk_opp(payloads) if c["type"] == "risk")
    assert risk["headline"] == "Has-value"


def test_foundation_gate_triggers_on_low_rating():
    payloads = {
        "menu": _payload("diagnostic-menu", metrics={"menu_cvr_pct": 18.0, "photo_coverage_pct": 70.0}),
        "ops": _payload("diagnostic-ops", metrics={"rating": 4.0, "error_rate_pct": 3.0, "uptime_pct": 95.0}),
        "campaigns": _payload("diagnostic-campaigns"),
        "topline": _payload("diagnostic-topline"),
    }
    sub_status = {s: "ok" for s in ("diagnostic-ops", "diagnostic-menu", "diagnostic-campaigns", "diagnostic-topline")}
    gate = xc.compute_foundation_gate(payloads, sub_status)
    assert gate["triggered"] is True
    assert any(t.get("metric") == "rating" for t in gate["triggers"])


def test_foundation_gate_no_trigger_when_clean():
    payloads = {
        "menu": _payload("diagnostic-menu", metrics={"menu_cvr_pct": 22.0, "photo_coverage_pct": 80.0}),
        "ops": _payload("diagnostic-ops", metrics={"rating": 4.6, "error_rate_pct": 2.0, "uptime_pct": 96.0}),
        "campaigns": _payload("diagnostic-campaigns"),
        "topline": _payload("diagnostic-topline"),
    }
    sub_status = {s: "ok" for s in ("diagnostic-ops", "diagnostic-menu", "diagnostic-campaigns", "diagnostic-topline")}
    gate = xc.compute_foundation_gate(payloads, sub_status)
    assert gate["triggered"] is False
    assert gate["triggers"] == []


def test_foundation_gate_fail_conservative_when_ops_failed():
    payloads = {
        "menu": _payload("diagnostic-menu", metrics={"menu_cvr_pct": 22.0, "photo_coverage_pct": 80.0}),
        "ops": _payload("diagnostic-ops"),  # no metrics — sub-skill failed
        "campaigns": _payload("diagnostic-campaigns"),
        "topline": _payload("diagnostic-topline"),
    }
    sub_status = {"diagnostic-ops": "failed", "diagnostic-menu": "ok", "diagnostic-campaigns": "ok", "diagnostic-topline": "ok"}
    gate = xc.compute_foundation_gate(payloads, sub_status)
    assert gate["triggered"] is True
    assert any(t.get("reason") == "ops_sub_skill_failed" for t in gate["triggers"])


# --- Wk 3 Chunk 2: defensive fail-open guards ----------------------------------


def test_assemble_radar_returns_zeros_when_owner_payload_missing():
    """When sub-skill payloads are entirely absent, radar still returns all 7 dims with 0.0."""
    radar = xc.assemble_radar({}, topline_metrics={}, campaigns_metrics={})
    expected_dims = {
        "AOV", "Re-order Rate", "Conversion", "Traffic",
        "Campaigns / ROAS", "Marketing Efficiency", "Operations",
    }
    assert set(radar.keys()) == expected_dims
    for dim in expected_dims:
        assert radar[dim] == 0.0


def test_assemble_radar_partial_payloads_uses_present_owners_zero_for_missing():
    """If only menu payload is present, menu-owned dims fill in; others default to 0.0."""
    payloads = {
        "menu": {
            "sub_skill": "diagnostic-menu",
            "computed": {
                "metrics": {},
                "radar_contributions": {"Conversion": 6.5, "Traffic": 7.0},
                "tier_contributions": {},
                "findings": [],
                "charts": [],
            },
            "drafted": {"toggle_title": "", "toggle_prose": "", "win_risk_opp_candidates": []},
            "data_quality": {"completeness": 1.0, "gaps": []},
        }
    }
    radar = xc.assemble_radar(payloads, topline_metrics={}, campaigns_metrics={})
    assert radar["Conversion"] == 6.5
    assert radar["Traffic"] == 7.0
    assert radar["AOV"] == 0.0
    assert radar["Re-order Rate"] == 0.0
    assert radar["Campaigns / ROAS"] == 0.0
    assert radar["Marketing Efficiency"] == 0.0
    assert radar["Operations"] == 0.0


def test_rollup_tiers_handles_missing_sub_skill_payload():
    """per_bucket dict with only menu (no ops/campaigns entries at all) → uses only menu."""
    per_bucket = {
        "menu": {
            "S1": {"score": 8, "flag": "green", "reasons": []},
            "S2": {"score": 4, "flag": "red", "reasons": []},
        }
        # ops + campaigns entirely absent from the dict
    }
    rollup = xc.rollup_tiers(per_bucket)
    assert rollup["S1"]["flag"] == "green"
    assert rollup["S1"]["per_bucket_flags"] == {"menu": "green"}
    assert rollup["S2"]["flag"] == "red"
    assert rollup["S2"]["worst_bucket"] == "menu"


def test_foundation_gate_handles_missing_payload_dict():
    """payloads={} (all sub-skills failed) + all-failed sub_skill_status → triggers, no KeyError."""
    sub_status = {
        "diagnostic-ops": "failed",
        "diagnostic-menu": "failed",
        "diagnostic-campaigns": "failed",
        "diagnostic-topline": "failed",
    }
    gate = xc.compute_foundation_gate({}, sub_status)
    assert gate["triggered"] is True
    reasons = [t.get("reason") for t in gate["triggers"]]
    assert "ops_sub_skill_failed" in reasons
    assert "menu_sub_skill_failed" in reasons


def test_select_win_risk_opp_skips_payloads_missing_drafted_field():
    """Malformed payload (no `drafted` key) is skipped without KeyError."""
    payloads = {
        "menu": {
            "sub_skill": "diagnostic-menu",
            "computed": {
                "metrics": {}, "radar_contributions": {}, "tier_contributions": {},
                "findings": [], "charts": [],
            },
            # no `drafted` key
        },
        "ops": _payload("diagnostic-ops", w_r_o=[
            {"type": "risk", "headline": "OpsRisk", "value_usd": 1234},
        ]),
    }
    selected = xc.select_win_risk_opp(payloads)
    # Only the ops candidate should surface; menu skipped silently.
    risks = [c for c in selected if c["type"] == "risk"]
    assert len(risks) == 1
    assert risks[0]["headline"] == "OpsRisk"


def test_select_win_risk_opp_handles_empty_payloads():
    """payloads={} returns empty list, no error."""
    assert xc.select_win_risk_opp({}) == []
