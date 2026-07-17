"""HTML exporter — convergence path (PDF + Notion from one orchestrator pass)."""
from __future__ import annotations

from pathlib import Path

from orchestrator import html_export


def _payload(short, *, prose="p", charts=None):
    return {
        "sub_skill": f"diagnostic-{short}", "version": "1.0", "client": "ACME",
        "window": {"start": "2026-02-08", "end": "2026-05-08"},
        "computed": {"metrics": {}, "radar_contributions": {},
                     "tier_contributions": {}, "findings": [],
                     "charts": charts or []},
        "drafted": {"toggle_title": f"{short} Detail", "toggle_prose": prose,
                    "win_risk_opp_candidates": []},
        "data_quality": {"completeness": 1.0, "gaps": []},
    }


def _kwargs():
    return dict(
        client="ACME",
        window={"start": "2026-02-08", "end": "2026-05-08"},
        payloads={
            "topline": _payload("topline", prose="Gross $1.2M.",
                                charts=[]) | {"computed": {
                "metrics": {"gross_sales": 1200000.0, "orders": 25000,
                            "aov": 48.0, "net_payout": 720000.0,
                            "payout_pct": 60.0},
                "radar_contributions": {}, "tier_contributions": {},
                "findings": [], "charts": []}},
            "menu": _payload("menu"), "ops": _payload("ops"),
            "campaigns": _payload("campaigns"),
        },
        radar={"AOV": 6.0, "Re-order Rate": 5.0, "Conversion": 4.0,
               "Traffic": 7.0, "Marketing Efficiency": 5.0, "Operations": 3.0,
               "Campaigns / ROAS": 6.0},
        tier_rollup={"S1": {"flag": "red"}, "S2": {"flag": "yellow"}},
        action_plan={"tier_groups": {
            "red": {"stores": ["S1"], "default_strategy": "Stop.",
                    "auto_actions": [{"action": "Pause S1"}],
                    "finding_actions": []},
            "yellow": {"stores": ["S2"], "default_strategy": "Fix.",
                       "auto_actions": [], "finding_actions": []},
            "green": {"stores": [], "default_strategy": "",
                      "auto_actions": [], "finding_actions": []},
            "new": {"stores": [], "default_strategy": "",
                    "auto_actions": [], "finding_actions": []}},
            "portfolio_actions": []},
        foundation_gate={"triggered": True, "triggers": [
            {"metric": "rating", "value": 4.0, "threshold": 4.2}]},
        charts_dir=Path("/tmp/cd-html-test/cross_cutting"),
    )


def test_build_html_returns_self_contained_document():
    html = html_export.build_html(**_kwargs())
    assert html.startswith("<!DOCTYPE html>")
    assert html.rstrip().endswith("</html>")
    assert "ACME — Diagnostics" in html
    assert "<style>" in html  # CSS inlined


def test_html_has_dashboard_and_toggles():
    html = html_export.build_html(**_kwargs())
    assert "The 60-second view" in html
    assert "Win / Risk / Opportunity / Decision" in html
    assert "Decision" in html
    assert "This Week" in html  # kanban column
    assert "<details>" in html  # half-2 collapsible
    assert "Action Plan Detail" in html
    assert "Foundation gate triggered" in html  # gate banner


def test_html_has_merged_executive_summary_block():
    html = html_export.build_html(**_kwargs())
    assert "Executive Summary" in html
    assert "Foundation gate triggered" in html  # status merged into headline
    assert "Biggest risk" in html and "Do first" in html
    assert "Inside:" in html  # doc roadmap bullet
    assert "<ul" in html  # rendered as bullets, not a paragraph
    assert "class='alert'" not in html  # standalone foundation alert removed


def test_html_renders_hero_numbers_from_topline_payload():
    html = html_export.build_html(**_kwargs())
    assert "$1,200,000" in html
    assert "25,000" in html
