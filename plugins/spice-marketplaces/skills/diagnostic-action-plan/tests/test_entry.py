from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
from diagnostic_action_plan import entry

CONTRACT_PATH = Path("/Users/maxx/Desktop/Cowork/Skills/optimized-menu-sheet/deliverable_contract.json")


# ---------------------------------------------------------------------------
# Adapted v0.1 tests — backward-compat path (no tier_rollup) still preserved.
# ---------------------------------------------------------------------------

def test_stub_routes_foundation_finding_to_p1():
    """When called WITHOUT tier_rollup, falls back to v0.1 kanban behavior."""
    findings = [
        {"pattern_id": "payout_collapse", "severity": "foundation", "scope": "portfolio",
         "estimated_impact_usd": 50000, "deliverable_trigger": {"skill": "campaign-plan", "params": {}}},
        {"pattern_id": "low_cvr", "severity": "medium", "scope": "Venice",
         "estimated_impact_usd": 5000, "deliverable_trigger": {"skill": "optimized-menu-sheet", "params": {"stores": ["Venice"]}}},
    ]
    plan = entry.build_plan(findings, foundation_triggered=True)
    p1 = plan["kanban"]["P1_this_week"]
    assert any(it["pattern_id"] == "payout_collapse" for it in p1)
    assert all(it["severity"] == "foundation" for it in p1)


def test_stub_emits_deliverable_triggers():
    """v0.1 fall-back still emits deliverable_triggers list."""
    findings = [
        {"pattern_id": "low_cvr", "severity": "medium", "scope": "Venice",
         "estimated_impact_usd": 5000, "deliverable_trigger": {"skill": "optimized-menu-sheet", "params": {"stores": ["Venice"]}}}
    ]
    plan = entry.build_plan(findings, foundation_triggered=False)
    assert len(plan["deliverable_triggers"]) == 1
    assert plan["deliverable_triggers"][0]["skill"] == "optimized-menu-sheet"


def test_emitted_trigger_validates_against_downstream_contract():
    """Finding-driven trigger validates against the optimized-menu-sheet contract (works in both modes)."""
    contract = json.loads(CONTRACT_PATH.read_text())
    findings = [
        {"pattern_id": "low_cvr", "severity": "medium", "scope": "Venice",
         "estimated_impact_usd": 5000,
         "deliverable_trigger": {"skill": "optimized-menu-sheet", "params": {"stores": ["Venice"], "focus": "category_consolidation"}}}
    ]
    tier_rollup = {"Venice": {"flag": "red", "worst_bucket": "menu", "per_bucket_flags": {"menu": "red"}}}
    plan = entry.build_plan(findings, foundation_triggered=False, tier_rollup=tier_rollup)
    # Find the menu-sheet trigger in the flat list
    menu_sheet_triggers = [t for t in plan["deliverable_triggers"] if t["skill"] == "optimized-menu-sheet"]
    assert len(menu_sheet_triggers) == 1
    trigger = menu_sheet_triggers[0]
    assert trigger["skill"] == contract["skill"]
    jsonschema.validate(trigger["params"], contract["params_schema"])  # no exception


def test_invalid_params_fail_contract():
    contract = json.loads(CONTRACT_PATH.read_text())
    bad_params = {"focus": "category_consolidation"}  # missing required `stores`
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad_params, contract["params_schema"])


# ---------------------------------------------------------------------------
# Tier-aware mode (v0.2): structural assertions + auto-action generation rules.
# ---------------------------------------------------------------------------

def _r(flag, worst_bucket, **per):
    """Compact rollup-entry helper."""
    if not per:
        per = {worst_bucket: flag}
    return {"flag": flag, "worst_bucket": worst_bucket, "per_bucket_flags": dict(per)}


def test_red_tier_emits_pause_campaigns_auto_action():
    rollup = {
        "Venice": _r("red", "ops"),
        "Brentwood": _r("red", "menu"),
    }
    plan = entry.build_plan([], foundation_triggered=False, tier_rollup=rollup)
    pause = [a for a in plan["tier_groups"]["red"]["auto_actions"] if "Pause" in a["action"]]
    assert len(pause) == 1
    # Both stores named in the action
    assert "Venice" in pause[0]["action"]
    assert "Brentwood" in pause[0]["action"]
    assert set(pause[0]["stores"]) == {"Venice", "Brentwood"}
    assert pause[0]["deliverable_trigger"] is None
    assert pause[0]["kind"] == "auto"


def test_red_tier_emits_fix_worst_bucket_auto_action():
    rollup = {"Venice": _r("red", "ops")}
    plan = entry.build_plan([], foundation_triggered=False, tier_rollup=rollup)
    fix_actions = [a for a in plan["tier_groups"]["red"]["auto_actions"] if a["action"].startswith("Fix")]
    assert any(a["action"] == "Fix ops at Venice" for a in fix_actions)


def test_yellow_tier_emits_targeted_fix_per_store():
    rollup = {"Venice": _r("yellow", "menu")}
    plan = entry.build_plan([], foundation_triggered=False, tier_rollup=rollup)
    targeted = [a for a in plan["tier_groups"]["yellow"]["auto_actions"] if "Targeted fix" in a["action"]]
    assert any("Venice" in a["action"] and "menu" in a["action"] for a in targeted)


def test_green_tier_emits_scale_auto_action_with_campaign_plan_trigger():
    rollup = {"BeverlyHills": _r("green", "ops", ops="green", menu="green", campaigns="green")}
    plan = entry.build_plan([], foundation_triggered=False, tier_rollup=rollup)
    scale = [a for a in plan["tier_groups"]["green"]["auto_actions"] if "+20%" in a["action"]]
    assert len(scale) == 1
    assert scale[0]["deliverable_trigger"] is not None
    assert scale[0]["deliverable_trigger"]["skill"] == "campaign-plan"
    assert scale[0]["deliverable_trigger"]["params"]["focus"] == "scale"
    assert "BeverlyHills" in scale[0]["deliverable_trigger"]["params"]["stores"]


def test_new_tier_emits_re_diagnostic_schedule():
    rollup = {"PalmSprings": _r("new", "menu")}
    plan = entry.build_plan([], foundation_triggered=False, tier_rollup=rollup)
    # Per spec: per-store "Continue awareness" lives in the tier group;
    # the day-60 re-diagnostic is a portfolio-level action.
    awareness = [a for a in plan["tier_groups"]["new"]["auto_actions"] if "awareness" in a["action"].lower()]
    assert any("PalmSprings" in a["action"] for a in awareness)
    schedule = [a for a in plan["portfolio_actions"] if "day-60" in a.get("action", "")]
    assert len(schedule) == 1
    assert "PalmSprings" in schedule[0]["action"]


def test_finding_with_store_scope_lands_in_that_stores_tier_group():
    rollup = {"Venice": _r("red", "ops")}
    findings = [{
        "pattern_id": "high_error_rate",
        "severity": "high",
        "scope": "Venice",
        "estimated_impact_usd": 3000,
        "deliverable_trigger": None,
    }]
    plan = entry.build_plan(findings, foundation_triggered=False, tier_rollup=rollup)
    venice_findings = plan["tier_groups"]["red"]["finding_actions"]
    assert any(f["pattern_id"] == "high_error_rate" for f in venice_findings)


def test_finding_with_portfolio_scope_lands_in_portfolio_actions():
    rollup = {"Venice": _r("red", "ops")}
    findings = [{
        "pattern_id": "payout_collapse",
        "severity": "foundation",
        "scope": "portfolio",
        "estimated_impact_usd": 50000,
        "deliverable_trigger": None,
    }]
    plan = entry.build_plan(findings, foundation_triggered=False, tier_rollup=rollup)
    assert any(f["pattern_id"] == "payout_collapse" for f in plan["portfolio_actions"])


def test_foundation_triggered_downgrades_green_auto_actions():
    rollup = {"BeverlyHills": _r("green", "ops", ops="green", menu="green", campaigns="green")}
    plan = entry.build_plan([], foundation_triggered=True, tier_rollup=rollup)
    assert plan["foundation_gate_triggered"] is True
    green_auto = plan["tier_groups"]["green"]["auto_actions"]
    # Scale action should be downgraded to a HOLD instruction; +20% should NOT appear
    assert not any("+20%" in a["action"] for a in green_auto)
    assert any("HOLD" in a["action"] for a in green_auto)


def test_no_tier_rollup_falls_back_to_v01_stub_format():
    findings = [
        {"pattern_id": "low_cvr", "severity": "medium", "scope": "Venice",
         "estimated_impact_usd": 5000, "deliverable_trigger": None}
    ]
    plan = entry.build_plan(findings, foundation_triggered=False)
    assert plan["version"] == "0.1-stub"
    assert "kanban" in plan
    assert "tier_groups" not in plan


def test_multi_store_finding_lands_in_worst_tier():
    rollup = {
        "Venice": _r("red", "ops"),
        "BeverlyHills": _r("green", "ops", ops="green", menu="green", campaigns="green"),
    }
    findings = [{
        "pattern_id": "promo_stack",
        "severity": "high",
        "scope": "Venice,BeverlyHills",
        "estimated_impact_usd": 4000,
        "deliverable_trigger": None,
    }]
    plan = entry.build_plan(findings, foundation_triggered=False, tier_rollup=rollup)
    red_findings = plan["tier_groups"]["red"]["finding_actions"]
    green_findings = plan["tier_groups"]["green"]["finding_actions"]
    assert any(f["pattern_id"] == "promo_stack" for f in red_findings)
    assert not any(f["pattern_id"] == "promo_stack" for f in green_findings)


def test_all_tier_groups_always_present_even_when_empty():
    """Even if rollup has only red stores, yellow/green/new groups must still exist as empty placeholders."""
    rollup = {"Venice": _r("red", "ops")}
    plan = entry.build_plan([], foundation_triggered=False, tier_rollup=rollup)
    for tier in ("red", "yellow", "green", "new"):
        assert tier in plan["tier_groups"]
        assert "stores" in plan["tier_groups"][tier]
        assert "default_strategy" in plan["tier_groups"][tier]
        assert "auto_actions" in plan["tier_groups"][tier]
        assert "finding_actions" in plan["tier_groups"][tier]
    assert plan["tier_groups"]["yellow"]["stores"] == []
    assert plan["tier_groups"]["yellow"]["auto_actions"] == []
    assert plan["tier_groups"]["yellow"]["finding_actions"] == []


def test_unmapped_store_scope_lands_in_portfolio_with_flag():
    rollup = {"Venice": _r("red", "ops")}
    findings = [{
        "pattern_id": "ghost_store",
        "severity": "medium",
        "scope": "Malibu",  # not in rollup
        "estimated_impact_usd": 1000,
        "deliverable_trigger": None,
    }]
    plan = entry.build_plan(findings, foundation_triggered=False, tier_rollup=rollup)
    ghost = [f for f in plan["portfolio_actions"] if f["pattern_id"] == "ghost_store"]
    assert len(ghost) == 1
    assert ghost[0].get("unmapped_store_scope") is True


def test_deliverable_triggers_flat_list_includes_auto_action_triggers():
    """The flat deliverable_triggers should pull from BOTH auto_actions and finding_actions."""
    rollup = {
        "BeverlyHills": _r("green", "ops", ops="green", menu="green", campaigns="green"),
    }
    findings = [{
        "pattern_id": "low_cvr",
        "severity": "medium",
        "scope": "BeverlyHills",
        "estimated_impact_usd": 5000,
        "deliverable_trigger": {"skill": "optimized-menu-sheet", "params": {"stores": ["BeverlyHills"]}},
    }]
    plan = entry.build_plan(findings, foundation_triggered=False, tier_rollup=rollup)
    skills_in_triggers = {t["skill"] for t in plan["deliverable_triggers"]}
    assert "campaign-plan" in skills_in_triggers  # from green auto-action
    assert "optimized-menu-sheet" in skills_in_triggers  # from finding


def test_foundation_triggered_marks_non_foundation_findings_deferred():
    rollup = {"BeverlyHills": _r("green", "ops", ops="green", menu="green", campaigns="green")}
    findings = [{
        "pattern_id": "low_cvr",
        "severity": "medium",
        "scope": "BeverlyHills",
        "estimated_impact_usd": 5000,
        "deliverable_trigger": None,
    }]
    plan = entry.build_plan(findings, foundation_triggered=True, tier_rollup=rollup)
    green_findings = plan["tier_groups"]["green"]["finding_actions"]
    assert len(green_findings) == 1
    assert green_findings[0].get("deferred_until_foundation_clear") is True


# ---------------------------------------------------------------------------
# Wk 3 Chunk 1: multi-red-bucket auto-actions + impact ranking within tiers.
# ---------------------------------------------------------------------------

def test_red_store_with_multiple_red_buckets_emits_one_action_per_bucket():
    """Venice red across menu+ops+campaigns → 3 'Fix X at Venice' auto-actions."""
    rollup = {
        "Venice": _r("red", "ops", menu="red", ops="red", campaigns="red"),
    }
    plan = entry.build_plan([], foundation_triggered=False, tier_rollup=rollup)
    fix_actions = [
        a for a in plan["tier_groups"]["red"]["auto_actions"]
        if a["action"].startswith("Fix") and "Venice" in a["action"]
    ]
    assert len(fix_actions) == 3
    action_strings = {a["action"] for a in fix_actions}
    assert "Fix menu at Venice" in action_strings
    assert "Fix ops at Venice" in action_strings
    assert "Fix campaigns at Venice" in action_strings


def test_finding_actions_within_tier_sorted_by_impact_desc():
    """Multiple red-tier findings with mixed impacts → output ordered highest-first, nulls last."""
    rollup = {"Venice": _r("red", "ops")}
    findings = [
        {"pattern_id": "low_impact", "severity": "medium", "scope": "Venice",
         "estimated_impact_usd": 1000, "deliverable_trigger": None},
        {"pattern_id": "no_impact", "severity": "high", "scope": "Venice",
         "estimated_impact_usd": None, "deliverable_trigger": None},
        {"pattern_id": "high_impact", "severity": "medium", "scope": "Venice",
         "estimated_impact_usd": 9000, "deliverable_trigger": None},
        {"pattern_id": "mid_impact", "severity": "medium", "scope": "Venice",
         "estimated_impact_usd": 4000, "deliverable_trigger": None},
    ]
    plan = entry.build_plan(findings, foundation_triggered=False, tier_rollup=rollup)
    venice_findings = plan["tier_groups"]["red"]["finding_actions"]
    pattern_order = [f["pattern_id"] for f in venice_findings]
    assert pattern_order == ["high_impact", "mid_impact", "low_impact", "no_impact"]


def test_portfolio_actions_sorted_by_impact_desc():
    """Portfolio actions (findings + auto-actions) sorted by impact desc, nulls last."""
    rollup = {"Venice": _r("red", "ops")}
    findings = [
        {"pattern_id": "small_portfolio", "severity": "medium", "scope": "portfolio",
         "estimated_impact_usd": 2000, "deliverable_trigger": None},
        {"pattern_id": "no_impact_portfolio", "severity": "high", "scope": "portfolio",
         "estimated_impact_usd": None, "deliverable_trigger": None},
        {"pattern_id": "huge_portfolio", "severity": "foundation", "scope": "portfolio",
         "estimated_impact_usd": 75000, "deliverable_trigger": None},
        {"pattern_id": "mid_portfolio", "severity": "medium", "scope": "portfolio",
         "estimated_impact_usd": 10000, "deliverable_trigger": None},
    ]
    plan = entry.build_plan(findings, foundation_triggered=False, tier_rollup=rollup)
    portfolio = plan["portfolio_actions"]

    # Filter to just the findings we care about (portfolio also gets auto-actions);
    # they should appear in impact-desc order relative to each other.
    finding_pids = ["huge_portfolio", "mid_portfolio", "small_portfolio", "no_impact_portfolio"]
    seen = [a.get("pattern_id") for a in portfolio if a.get("pattern_id") in finding_pids]
    assert seen == finding_pids
