"""Tests for Wk 3 Chunk 4: Notion page assembly (Phase 5)."""
from __future__ import annotations

from pathlib import Path

import pytest

from orchestrator import notion_assembly


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ALLOWED_BLOCK_TYPES = {
    "heading_1",
    "heading_2",
    "heading_3",
    "paragraph",
    "callout",
    "bulleted_list_item",
    "image",
    "table",
    "divider",
}


def _payload(short: str, *, completeness: float = 1.0, gaps=None, charts=None, prose=None,
             findings=None, metrics=None, tier_contributions=None) -> dict:
    return {
        "sub_skill": f"diagnostic-{short}",
        "version": "1.0",
        "client": "ACME",
        "window": {"start": "2026-02-08", "end": "2026-05-08"},
        "computed": {
            "metrics": metrics or {},
            "radar_contributions": {},
            "tier_contributions": tier_contributions or {},
            "findings": findings or [],
            "charts": charts or [],
        },
        "drafted": {
            "toggle_title": f"{short.capitalize()} Detail",
            "toggle_prose": prose or f"Synthetic prose for {short}.",
            "win_risk_opp_candidates": [],
        },
        "data_quality": {"completeness": completeness, "gaps": gaps or []},
    }


def _topline_payload() -> dict:
    return _payload(
        "topline",
        metrics={
            "gross_sales": 1234567.0,
            "orders": 25000,
            "aov": 49.38,
            "net_payout": 740000.0,
            "payout_pct": 60.0,
        },
        prose="Top-line: gross sales $1.2M across 25K orders.",
    )


def _menu_payload() -> dict:
    return _payload(
        "menu",
        prose="Menu: 14% conversion at Venice — funnel leak.",
        charts=[{"id": "funnel_ue", "path": "menu/charts/funnel_ue.png"}],
        gaps=["missing photo coverage for Brentwood"],
        completeness=0.85,
    )


def _ops_payload() -> dict:
    return _payload(
        "ops",
        prose="Ops: 88% uptime at Venice; rating 4.0.",
        completeness=0.90,
    )


def _campaigns_payload() -> dict:
    return _payload(
        "campaigns",
        prose="Campaigns: ROAS varies 2.0–7.5 across stores.",
        charts=[{"id": "campaign_2x2", "path": "campaigns/charts/campaign_2x2.png"}],
        completeness=0.95,
    )


def _all_payloads() -> dict:
    return {
        "topline": _topline_payload(),
        "menu": _menu_payload(),
        "ops": _ops_payload(),
        "campaigns": _campaigns_payload(),
    }


def _radar() -> dict:
    return {
        "AOV": 9.0,
        "Re-order Rate": 6.0,
        "Conversion": 4.0,  # weakest
        "Traffic": 7.0,
        "Marketing Efficiency": 5.5,
        "Operations": 3.5,  # 2nd weakest
        "Campaigns / ROAS": 6.5,
    }


def _tier_rollup() -> dict:
    return {
        "BeverlyHills": {
            "flag": "green",
            "worst_bucket": "menu",
            "per_bucket_flags": {"menu": "green", "ops": "green", "campaigns": "green"},
        },
        "Venice": {
            "flag": "red",
            "worst_bucket": "menu",
            "per_bucket_flags": {"menu": "red", "ops": "red", "campaigns": "yellow"},
        },
        "Brentwood": {
            "flag": "yellow",
            "worst_bucket": "campaigns",
            "per_bucket_flags": {"menu": "green", "ops": "yellow", "campaigns": "yellow"},
        },
    }


def _action_plan(*, foundation_triggered: bool = False) -> dict:
    return {
        "version": "0.2-tier-aware",
        "foundation_gate_triggered": foundation_triggered,
        "tier_groups": {
            "red": {
                "stores": ["Venice"],
                "default_strategy": "Stop campaigns at this store. Fix the broken bucket(s) before any growth investment.",
                "auto_actions": [
                    {
                        "kind": "auto",
                        "action": "Pause all campaigns at Venice — until menu, ops fixed",
                        "stores": ["Venice"],
                        "rationale": "Red tier policy",
                        "deliverable_trigger": None,
                    },
                    {
                        "kind": "auto",
                        "action": "Fix menu at Venice",
                        "stores": ["Venice"],
                        "rationale": "Red menu bucket",
                        "deliverable_trigger": None,
                    },
                ],
                "finding_actions": [
                    {
                        "pattern_id": "low_photo_coverage",
                        "severity": "high",
                        "scope": "Venice",
                        "estimated_impact_usd": 1500.0,
                        "evidence": {},
                        "deliverable_trigger": None,
                    }
                ],
            },
            "yellow": {
                "stores": ["Brentwood"],
                "default_strategy": "Targeted fix on the weak bucket. Maintain current spend.",
                "auto_actions": [],
                "finding_actions": [],
            },
            "green": {
                "stores": ["BeverlyHills"],
                "default_strategy": "Scale: increase ad budget, expand to additional platforms, feature in marketing.",
                "auto_actions": [
                    {
                        "kind": "auto",
                        "action": "Increase ad budget +20% at BeverlyHills",
                        "stores": ["BeverlyHills"],
                        "rationale": "Green tier ready to scale",
                        "deliverable_trigger": None,
                    }
                ],
                "finding_actions": [],
            },
            "new": {
                "stores": [],
                "default_strategy": "Awareness investment + diagnostic re-run at 60-day mark.",
                "auto_actions": [],
                "finding_actions": [],
            },
        },
        "portfolio_actions": [
            {
                "kind": "auto",
                "action": "Hold spend at Brentwood — no scaling until fixed",
                "stores": ["Brentwood"],
                "rationale": "Yellow tier portfolio rule",
                "deliverable_trigger": None,
            }
        ],
        "deliverable_triggers": [],
    }


def _foundation_gate(triggered: bool = False) -> dict:
    if triggered:
        return {
            "triggered": True,
            "triggers": [
                {"metric": "rating", "value": 4.0, "threshold": 4.2, "scope": "portfolio"},
                {"metric": "photo_coverage_pct", "value": 35.0, "threshold": 50.0, "scope": "portfolio"},
            ],
            "override_action_plan": True,
        }
    return {"triggered": False, "triggers": [], "override_action_plan": False}


def _common_kwargs(*, foundation: bool = False, payloads_override=None, charts_dir: Path = Path("/tmp/cd-test/cross_cutting")):
    return dict(
        client="ACME",
        window={"start": "2026-02-08", "end": "2026-05-08"},
        payloads=payloads_override if payloads_override is not None else _all_payloads(),
        radar=_radar(),
        tier_rollup=_tier_rollup(),
        action_plan=_action_plan(foundation_triggered=foundation),
        foundation_gate=_foundation_gate(foundation),
        charts_dir=charts_dir,
    )


# ---------------------------------------------------------------------------
# Markdown tests
# ---------------------------------------------------------------------------

def test_markdown_includes_client_and_window():
    md = notion_assembly.build_page_markdown(**_common_kwargs())
    assert md.splitlines()[0].startswith("# ACME | Diagnostics & Action Plan |")
    assert "2026-02-08" in md
    assert "2026-05-08" in md


def test_markdown_includes_foundation_banner_when_triggered():
    md_on = notion_assembly.build_page_markdown(**_common_kwargs(foundation=True))
    md_off = notion_assembly.build_page_markdown(**_common_kwargs(foundation=False))
    assert "Foundation gate triggered" in md_on
    assert "Foundation gate triggered" not in md_off


def test_markdown_includes_each_tier_section():
    md = notion_assembly.build_page_markdown(**_common_kwargs())
    # All four tier groups must appear (even when 0 stores)
    assert "Red Stores" in md
    assert "Yellow Stores" in md
    assert "Green Stores" in md
    assert "New Stores" in md
    # New tier has 0 stores — section still rendered
    assert "(0 stores)" in md


def test_markdown_includes_each_half2_section():
    md = notion_assembly.build_page_markdown(**_common_kwargs())
    assert "Top-line Performance Detail" in md
    assert "Menu & Storefront Detail" in md
    assert "Operations Detail" in md
    assert "Campaigns Detail" in md
    # Each prose appears in the rendered output
    assert "Top-line: gross sales $1.2M" in md
    assert "Menu: 14% conversion" in md
    assert "Ops: 88% uptime" in md
    assert "Campaigns: ROAS varies" in md


def test_markdown_renders_chart_image_for_radar_and_tier_donut():
    md = notion_assembly.build_page_markdown(**_common_kwargs())
    assert "radar_7dim.png" in md
    assert "tier_donut.png" in md
    assert "![Radar]" in md
    assert "![Tier donut]" in md


def test_blocks_output_is_list_of_valid_block_dicts():
    blocks = notion_assembly.build_page_blocks(**_common_kwargs())
    assert isinstance(blocks, list) and len(blocks) > 5
    for b in blocks:
        assert isinstance(b, dict)
        assert "type" in b
        assert b["type"] in ALLOWED_BLOCK_TYPES, f"unexpected block type: {b['type']}"
        # The sub-key matching the type must exist
        assert b["type"] in b, f"block missing matching sub-key for type={b['type']}"


def test_data_quality_footer_lists_completeness_per_sub_skill():
    md = notion_assembly.build_page_markdown(**_common_kwargs())
    # Each sub-skill's completeness pct appears in the footer line
    assert "Topline (100%)" in md
    assert "Menu (85%)" in md
    assert "Ops (90%)" in md
    assert "Campaigns (95%)" in md


def test_markdown_handles_missing_sub_skill_payload_gracefully():
    payloads = _all_payloads()
    payloads.pop("ops")  # simulate ops sub-skill failure
    md = notion_assembly.build_page_markdown(
        **_common_kwargs(payloads_override=payloads)
    )
    # Should NOT raise; ops section either skipped or replaced with placeholder
    assert "Top-line Performance Detail" in md
    assert "Menu & Storefront Detail" in md
    assert "Campaigns Detail" in md
    # And footer line must not crash on missing ops
    assert "Topline (100%)" in md
