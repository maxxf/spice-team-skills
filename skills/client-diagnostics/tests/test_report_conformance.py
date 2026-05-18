"""Conformance test for the canonical report pipeline.

Builds a report from a tiny in-memory fixture (findings.json + metrics.json)
and asserts the structural invariants that kept drifting on live clients:

- both `.half` banners ("Overview" + "Detailed Findings") present
- exactly the 6 canonical hero `.stat` slots, with the canonical labels
- radar section title contains "/ 10"
- the full required Half-2 toggle set is present, incl. "Menu & Storefront"
- no per-client literal bleed in the builder SOURCE (no Daily's / Virgil's
  numbers or names hardcoded)

Mirrors the repo's existing structural-test style (test_chart_helpers.py,
test_output_layout.py): construct minimum fixture, call, assert on output.
"""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

REF = Path(__file__).resolve().parents[1] / "references"
_spec = importlib.util.spec_from_file_location(
    "build_report", REF / "build_report.py")
build_report = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_report)

_mc_spec = importlib.util.spec_from_file_location(
    "make_charts", REF / "make_charts.py")
make_charts = importlib.util.module_from_spec(_mc_spec)
_mc_spec.loader.exec_module(make_charts)

CANONICAL_HERO = [
    "90-Day Gross", "Orders", "Blended AOV",
    "Net Payout", "Order Completion", "Customer Sentiment",
]
REQUIRED_TOGGLES = [
    "Portfolio Snapshot", "Menu &amp; Storefront", "Ops",
    "Brand Operational Health", "Campaigns", "Location Tiers",
    "Full Action Plan", "Appendix",
]


def _fixture(tmp: Path) -> Path:
    findings = {
        "client": "Fixture Co",
        "window": "Jan 1 – Mar 31, 2026 (90 days)",
        "platforms": "DoorDash only",
        "n_locations": 2,
        "locations_line": "2 (Alpha, Beta)",
        "cycle": "Cycle 0",
        "prepared_line": "Prepared by Spice Digital",
        "output_html": "fixture-report.html",
        "hero": {
            "slots": {
                "90-Day Gross": {"value": 50000, "sub": "baseline"},
                "Orders": {"value": 1200, "sub": "DD only"},
                "Blended AOV": {"value": 41.67, "sub": "per order"},
                "Net Payout": {"value": None, "sub": "not in export"},
                "Order Completion": {"value": "96.0%", "sub": "DD cancel+err"},
                "Customer Sentiment": {"value": "4.4 / 5", "sub": "n=80"},
            },
            "na_footnote": "Net payout column absent this cycle.",
        },
        "exec_summary": {"headline": "✅ Foundation clear.",
                         "bullets": ["one", "two"]},
        "foundation_gate": {"triggered": False},
        "radar_overall": 5.5,
        "radar_weakest": [["Operations", {"current": 3.0, "target": 9}]],
        "radar_notes": ["Re-order Rate not scored — data-pending."],
        "fro": {"foothold": {"body": "<b>Alpha solid.</b>", "fig": "$30K"}},
        "timeline": [{"when": "Week 1", "what": "Triage", "sub": "x"}],
        "action_plan": {"this_week": [{"title": "Do thing", "meta": "Owner"}]},
        "tier_health": {"lines": ["<b>Alpha — Green.</b>"],
                        "note": "Pre-Spice baseline, not a Spice scorecard."},
        "what_moved": {"first_cycle_note": True},
        "data_quality_footer": "DD 90d ok",
        "portfolio_snapshot": {
            "rows": [{"platform": "DoorDash", "gross": 50000, "orders": 1200,
                      "aov": 41.67, "eff_commission": None, "net_pct": None,
                      "est_monthly": 16667, "mktg_pct": "5.9%"}],
            "narrative": "Single platform.",
        },
        "menu_storefront": {"html": "<p>Storefront baseline carried.</p>"},
        "ops_detail": {"html": "<p>ops</p>"},
        "brand_health_detail": {"html": "<p>radar detail</p>"},
        "campaigns_detail": {"html": "<p>campaign-lifetime caveat.</p>"},
        "location_tiers_detail": {"html": "<p>tiers</p>"},
        "full_action_plan": {"html": "<p>plan</p>"},
        "store_tiers": [
            {"store": "Alpha", "tier": "Green", "blended_gmv": 30000},
            {"store": "Beta", "tier": "Red", "blended_gmv": 20000},
        ],
        "appendix_note": "Sorted by GMV.",
    }
    metrics = {
        "radar": {
            "AOV": {"current": 7, "target": 8},
            "Re-order Rate": {"current": None, "target": 8, "pending": True},
            "Operations": {"current": 3, "target": 9},
        },
        "radar_overall": 5.5,
        "tiers": {"Green": 1, "Red": 1,
                  "by_store": {"Alpha": "Green", "Beta": "Red"}},
        "top15_green": [{"name": "Alpha", "gmv": 30000, "tier": "Green"}],
        "trend_weekly": None,
        "daypart": None,
    }
    (tmp / "findings.json").write_text(json.dumps(findings))
    (tmp / "metrics.json").write_text(json.dumps(metrics))
    (tmp / "report_style.css").write_text(".stat{}")
    return tmp


def test_both_half_banners_present():
    with tempfile.TemporaryDirectory() as t:
        doc = build_report.build(_fixture(Path(t)))
    assert '<div class="half">Overview</div>' in doc
    assert "Detailed Findings</div>" in doc
    assert 'class="half"' in doc


def test_exactly_six_canonical_hero_slots():
    with tempfile.TemporaryDirectory() as t:
        doc = build_report.build(_fixture(Path(t)))
    hero = doc.split('<div class="hero">')[1].split("</div></div>")[0]
    stats = re.findall(r'<div class="stat[^"]*">', hero)
    # 6 hero cards in the strip
    assert doc.count('<div class="stat') == 6, doc.count('<div class="stat')
    for lbl in CANONICAL_HERO:
        assert f'<div class="lbl">{lbl}</div>' in doc, f"missing slot {lbl}"
    # missing metric -> n/a*, never dropped or substituted
    assert 'n/a<span class="na-fn">*</span>' in doc


def test_radar_title_is_out_of_ten():
    with tempfile.TemporaryDirectory() as t:
        doc = build_report.build(_fixture(Path(t)))
    assert re.search(r"Brand Health Radar — Overall .+ / 10", doc)


def test_required_toggle_set_present_including_menu_storefront():
    with tempfile.TemporaryDirectory() as t:
        doc = build_report.build(_fixture(Path(t)))
    for tog in REQUIRED_TOGGLES:
        assert tog in doc, f"required toggle missing: {tog}"
    assert "Menu &amp; Storefront" in doc


def test_menu_storefront_renders_when_field_absent():
    """Even if the data team omits the storefront audit, the toggle must
    still render with an explicit DATA-PENDING block — never dropped."""
    with tempfile.TemporaryDirectory() as t:
        tmp = _fixture(Path(t))
        fj = json.loads((tmp / "findings.json").read_text())
        del fj["menu_storefront"]
        (tmp / "findings.json").write_text(json.dumps(fj))
        doc = build_report.build(tmp)
    assert "Menu &amp; Storefront" in doc
    assert "data-pending" in doc.lower() or "data pending" in doc.lower()


# Per-client tokens that must never appear in EITHER generalized source —
# includes the funnel/storefront values proven on the live Virgil's run, so
# the new code paths can't smuggle literals back in.
_FORBIDDEN = [
    "$22,239", "22,239", "$102,432", "102,432", "$44,549",
    "Daily's", "Virgil", "Alicart",
    "Las Vegas", "Times Square", "Upper West Side",
    "122,096", "122096", "8,544", "8544", "5.98", "0.69%",
    "March 11", "Mar 11", "62/100", "Dancu",
    # trend / daypart VALUE literals proven on the live Virgil's run
    # (NOT schema key names like trend_weekly/daypart/peak/weakest_day,
    # which the data-driven builder must reference to read the contract)
    "61895", "61,895", "27719", "12818",
    "DD+GH per-order", "1.727", "0.928", "2.142",
    "W07", "W19", "Thu 18", "55453",
    "4150.65", "4925.7", "Times Sq", "59,156",
]


def test_no_per_client_literal_bleed_in_builder_source():
    src = (REF / "build_report.py").read_text()
    for token in _FORBIDDEN:
        assert token not in src, f"per-client literal in builder: {token!r}"


def test_no_per_client_literal_bleed_in_chart_source():
    src = (REF / "make_charts.py").read_text()
    for token in _FORBIDDEN:
        assert token not in src, f"per-client literal in charts: {token!r}"


# --------------------------------------------------------------------------- #
# Funnel + storefront-audit data path (the back-ported Virgil's improvements). #
# --------------------------------------------------------------------------- #

def _fixture_with_visuals(tmp: Path) -> Path:
    tmp = _fixture(tmp)
    fj = json.loads((tmp / "findings.json").read_text())
    mj = json.loads((tmp / "metrics.json").read_text())
    mj["funnel"] = {
        "stages": ["Store views", "Menu views", "Added to cart", "Orders"],
        "values": [40000, 3000, 900, 500],
        "title": "Conversion Funnel — fixture",
        "caption": "fixture funnel callout (data-supplied)",
    }
    mj["storefront_audit"] = {
        "listings": [["UE Alpha", 71, "Good"], ["DD Beta", 49, "Poor"]],
        "portfolio_avg": 60,
        "title": "Storefront Audit — fixture",
        "subtitle": "fixture subtitle (data-supplied)",
    }
    mj["top15_green_meta"] = {"title": "Fixture GMV by Store",
                              "subtitle": "fixture tier subtitle"}
    fj["menu_storefront"] = {
        "intro": "<b>Fixture storefront baseline.</b>",
        "storefront_table": {"headers": ["Listing", "Total /100"],
                             "rows": [["UE Alpha", "<b>71</b>"]]},
        "storefront_sections": [{"heading": "What the baseline says",
                                 "bullets": ["<b>Strong:</b> hero on-brand."]}],
        "funnel_table": {"headers": ["Store", "Store views"],
                         "rows": [["Alpha", "40,000"]]},
        "funnel_sections": [{"heading": "Funnel read",
                             "bullets": ["Menu friction is the lever."]}],
    }
    (tmp / "findings.json").write_text(json.dumps(fj))
    (tmp / "metrics.json").write_text(json.dumps(mj))
    return tmp


def test_funnel_and_storefront_charts_render_and_embed():
    """make_charts emits the two new PNGs from metrics, and the builder
    base64-embeds them inside the Menu & Storefront toggle (no placeholder)."""
    with tempfile.TemporaryDirectory() as t:
        tmp = _fixture_with_visuals(Path(t))
        made = make_charts.generate(tmp)
        names = {p.name for p in made}
        assert "funnel_ue.png" in names
        assert "storefront_audit.png" in names
        assert (tmp / "charts" / "funnel_ue.png").exists()
        assert (tmp / "charts" / "storefront_audit.png").exists()
        doc = build_report.build(tmp)
    # toggle present, structured content + both charts embedded inline
    assert "Menu &amp; Storefront" in doc
    assert "Fixture storefront baseline." in doc
    assert "What the baseline says" in doc
    assert "Funnel read" in doc
    assert "data:image/png;base64," in doc
    assert "[chart pending: funnel_ue.png]" not in doc
    assert "[chart pending: storefront_audit.png]" not in doc


def test_menu_storefront_text_only_when_charts_absent():
    """Structured menu_storefront supplied but chart PNGs not generated —
    section must still render (text-only) with visible chart placeholders,
    never crash, never drop the toggle."""
    with tempfile.TemporaryDirectory() as t:
        tmp = _fixture_with_visuals(Path(t))
        # deliberately do NOT run make_charts
        doc = build_report.build(tmp)
    assert "Menu &amp; Storefront" in doc
    assert "Fixture storefront baseline." in doc
    assert "What the baseline says" in doc


def test_charts_noop_when_funnel_storefront_absent():
    """Base fixture has no funnel/storefront keys — those charts must be
    skipped cleanly (not raised, not fabricated), like trend/daypart."""
    with tempfile.TemporaryDirectory() as t:
        tmp = _fixture(Path(t))
        made = make_charts.generate(tmp)
        names = {p.name for p in made}
    assert "funnel_ue.png" not in names
    assert "storefront_audit.png" not in names
    assert "radar_7dim.png" in names


# --------------------------------------------------------------------------- #
# Weekly-trend + daypart data path (the back-ported per-order DD/GH chart      #
# derivations). REAL charts when data present; honest text when absent.        #
# --------------------------------------------------------------------------- #

def _fixture_with_trend_daypart(tmp: Path) -> Path:
    tmp = _fixture(tmp)
    mj = json.loads((tmp / "metrics.json").read_text())
    mj["trend_weekly"] = {
        "weeks": ["Wk1", "Wk2", "Wk3", "Wk4"],
        "gmv": [1000.0, 1500.0, 1200.0, 1800.0],
        "orders": [20, 30, 24, 36],
        "title": "Fixture Weekly Trend",
        "caption": "fixture trend caption (data-supplied)",
        "source": "fixture per-order",
    }
    mj["daypart"] = {
        "days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "hours": list(range(24)),
        "matrix": [[i % 5 for i in range(24)] for _ in range(7)],
        "peak": {"day": "Sat", "hour": 19, "orders": 12},
        "weakest_day": "Mon",
        "title": "Fixture Daypart",
        "source": "fixture per-order",
    }
    (tmp / "metrics.json").write_text(json.dumps(mj))
    return tmp


def test_trend_and_daypart_charts_render_and_embed():
    """make_charts emits the two REAL PNGs from the per-order-derived
    series, and the builder base64-embeds them in the 90-Day Trend +
    Daypart sections — no placeholder, no false 'deferred' label, peak
    caption auto-built from contract data."""
    with tempfile.TemporaryDirectory() as t:
        tmp = _fixture_with_trend_daypart(Path(t))
        made = make_charts.generate(tmp)
        names = {p.name for p in made}
        assert "trend_overlay.png" in names
        assert "daypart_heatmap.png" in names
        assert (tmp / "charts" / "trend_overlay.png").exists()
        assert (tmp / "charts" / "daypart_heatmap.png").exists()
        doc = build_report.build(tmp)
    assert "90-Day Trend" in doc
    assert "data:image/png;base64," in doc
    assert "[chart pending: trend_overlay.png]" not in doc
    assert "[chart pending: daypart_heatmap.png]" not in doc
    # daypart present => NOT labelled deferred, peak caption auto-built
    assert "Daypart heatmap deferred" not in doc
    assert "Peak demand: Sat 19:00 (12 orders)" in doc
    assert "Weakest day: Mon" in doc


def test_trend_and_daypart_degrade_gracefully_when_absent():
    """Base fixture has trend_weekly/daypart = None — charts skipped, and
    both report sections render an HONEST text note (never a fabricated
    chart, never crash)."""
    with tempfile.TemporaryDirectory() as t:
        tmp = _fixture(Path(t))
        made = make_charts.generate(tmp)
        names = {p.name for p in made}
        doc = build_report.build(tmp)
    assert "trend_overlay.png" not in names
    assert "daypart_heatmap.png" not in names
    assert "90-Day Trend" in doc
    assert "Daypart heatmap deferred" in doc
    assert "not derivable" in doc or "not in this" in doc.lower() \
        or "not derivable from the parsed exports" in doc


# --------------------------------------------------------------------------- #
# Client DECK conformance (references/build_deck.js).                          #
# The deck is the client-shared deliverable; the HTML report is the creator's #
# working artifact. Same zero-literal discipline as the report builder.       #
# --------------------------------------------------------------------------- #

DECK_JS = REF / "build_deck.js"

# Literals proven on the live Virgil's / Daily's runs that must never be
# baked into the generalized deck source (extends _FORBIDDEN with the
# reference deck's hardcoded prose/people the generalized port must NOT carry).
_DECK_FORBIDDEN = _FORBIDDEN + [
    "Virgil's BBQ", "virgils-bbq", "Alicart",
    "Rodrigo", "Ana", "Manish", "Dancu",
    "Feb 9 to May 10", "Thursday 6 PM", "13-week",
    "$46,978", "$24,398", "$31,055", "16.4%", "28.1%", "19.7%",
    "5.61%", "7.69%", "Times Square · Upper West Side",
]


def test_no_per_client_literal_bleed_in_deck_source():
    """ALWAYS runs (no pptxgenjs needed) — the deck builder source must be
    100% data-driven, exactly like build_report.py / make_charts.py."""
    src = DECK_JS.read_text()
    for token in _DECK_FORBIDDEN:
        assert token not in src, f"per-client literal in deck builder: {token!r}"


def _node_and_pptx(run_dir: Path) -> bool:
    """True iff `node` is on PATH and pptxgenjs is installable/resolvable for
    a build in run_dir. We install into references/node_modules once (the
    SKILL workflow installs into the run dir; either location resolves)."""
    if shutil.which("node") is None:
        return None  # node unavailable -> skip build-exec tests
    if (REF / "node_modules" / "pptxgenjs").exists():
        return True
    try:
        subprocess.run(["npm", "install", "pptxgenjs"], cwd=REF,
                        check=True, capture_output=True, timeout=180)
        return (REF / "node_modules" / "pptxgenjs").exists()
    except Exception:
        return None


def _deck_fixture(tmp: Path, with_charts: bool) -> Path:
    """Reuse the report fixture, add the deck-only narrative + (optionally)
    stub chart PNGs so we exercise both the present and absent paths."""
    tmp = _fixture(tmp)
    fj = json.loads((tmp / "findings.json").read_text())
    fj["client_slug"] = "fixture-co"
    fj["foundation_gate"] = {"triggered": True, "rule": "No spend until cleared.",
                             "rows": [{"label": "DoorDash", "detail": "Cancel high"}]}
    fj["portfolio_snapshot"] = {
        "rows": [{"platform": "DoorDash", "gross": 30000, "eff_commission": "16%"}],
        "narrative": "Single platform.",
    }
    fj["deck"] = {
        "title_kicker": "Spice Digital · Delivery Marketplace Diagnostic",
        "headline_finding": {"title": "Headline", "stat": "0.7%",
                             "stat_sub": "conversion", "bullets": ["a", "b"]},
        "action_lanes": [{"lane": "This week", "items": ["x"]},
                         {"lane": "Week 2", "items": ["y"]}],
        "closing": {"kicker": "What we need", "title": "To move fast",
                    "bullets": ["sign off"]},
    }
    (tmp / "findings.json").write_text(json.dumps(fj))
    shutil.copy(REF / "report_style.css", tmp / "report_style.css")
    if with_charts:
        (tmp / "charts").mkdir(exist_ok=True)
        for n in ("radar_7dim.png", "top15_green_bar.png",
                  "trend_overlay.png", "daypart_heatmap.png"):
            (tmp / "charts" / n).write_bytes(b"\x89PNG\r\n\x1a\n")
    return tmp


def _slide_count(pptx: Path) -> int:
    with zipfile.ZipFile(pptx) as z:
        return len([n for n in z.namelist()
                    if re.match(r"ppt/slides/slide\d+\.xml$", n)])


def test_deck_builds_valid_pptx_and_embeds_charts():
    """Build a deck from a fixture WITH chart PNGs: must produce a valid
    .pptx (zip with the expected slide count) and embed the chart media."""
    with tempfile.TemporaryDirectory() as t:
        ok = _node_and_pptx(Path(t))
        if not ok:
            import pytest
            pytest.skip("node/pptxgenjs unavailable in this venv")
        tmp = _deck_fixture(Path(t), with_charts=True)
        r = subprocess.run(["node", str(DECK_JS), str(tmp)],
                            capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, r.stderr
        out = tmp / "fixture-co-deck.pptx"
        assert out.exists(), "deck .pptx not written"
        assert zipfile.is_zipfile(out), "deck is not a valid pptx zip"
        # 10 slides when all charts present (title, 60s, radar, gate,
        # headline, FRO, economics, trend/daypart, action, closing)
        assert _slide_count(out) == 10, _slide_count(out)
        with zipfile.ZipFile(out) as z:
            media = [n for n in z.namelist() if n.startswith("ppt/media/")]
        assert media, "no chart/logo media embedded"


def test_deck_degrades_when_charts_absent():
    """Same fixture but NO chart PNGs: deck must still build a valid pptx
    with fewer slides (the chart-only trend/daypart slide is dropped) and
    must NOT crash on the missing images."""
    with tempfile.TemporaryDirectory() as t:
        ok = _node_and_pptx(Path(t))
        if not ok:
            import pytest
            pytest.skip("node/pptxgenjs unavailable in this venv")
        tmp = _deck_fixture(Path(t), with_charts=False)
        r = subprocess.run(["node", str(DECK_JS), str(tmp)],
                            capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, r.stderr
        out = tmp / "fixture-co-deck.pptx"
        assert zipfile.is_zipfile(out)
        # trend/daypart slide requires >=1 chart -> dropped when none present
        assert _slide_count(out) == 9, _slide_count(out)
