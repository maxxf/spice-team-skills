"""Wk 2 full E2E: 4 parallel sub-skills + cross-cutting + action plan."""
import json
import tempfile
from pathlib import Path
import pandas as pd
from datetime import datetime

from orchestrator import contract, output_layout, entry


def _synth_csv(path: Path):
    """Synthetic CSV with columns each sub-skill needs. Real inputs Wk 3."""
    df = pd.DataFrame({
        "store": ["BeverlyHills", "Venice", "Brentwood"] * 5,
        "week": list(range(1, 6)) * 3,
        # topline cols
        "gross_sales": [12000, 9000, 7000] * 5,
        "orders": [240, 180, 140] * 5,
        "net_payout": [8000, 6000, 4500] * 5,
        # menu cols
        "menu_cvr_pct": [22.0, 14.0, 19.0] * 5,
        "photo_coverage_pct": [85, 35, 70] * 5,
        "hero_set": [True, True, True] * 5,
        "categories_count": [6, 6, 6] * 5,
        "categories_populated": [6, 5, 6] * 5,
        "storefront_to_menu_ctr_pct": [10.0, 11.0, 8.0] * 5,
        # ops cols
        "rating": [4.6, 4.0, 4.3] * 5,
        "error_rate_pct": [1.5, 6.0, 3.0] * 5,
        "cancellation_pct": [1.0, 4.0, 2.5] * 5,
        "uptime_pct": [98.0, 88.0, 95.0] * 5,
        "hours_accurate": [True, False, True] * 5,
        # campaigns cols
        "platform": ["UE", "DD", "GH"] * 5,
        "spend": [600, 400, 200] * 5,
        "attributed_sales": [3000, 800, 1000] * 5,
        "roas": [5.0, 2.0, 5.0] * 5,
        "incremental_orders_per_week": [15, 5, 8] * 5,
        "promo_count_active": [2, 4, 1] * 5,
    })
    df.to_csv(path, index=False)


def test_full_run_dispatches_all_4_sub_skills(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(output_layout, "RUN_ROOT", Path(tmp) / "runs")
        inputs = Path(tmp) / "inputs"
        inputs.mkdir()
        _synth_csv(inputs / "synth.csv")

        result = entry.run(
            client="test-client",
            window_start="2026-02-08", window_end="2026-05-08",
            inputs_dir=inputs, when=datetime(2026, 5, 8, 14, 30, 0),
        )

        for short in ("topline", "menu", "ops", "campaigns"):
            payload = json.loads(result.layout.sub_skill_results_path(short).read_text())
            contract.validate(payload)
            assert payload["sub_skill"] == f"diagnostic-{short}"

        state = json.loads(result.layout.run_state_path.read_text())
        for sub in ("diagnostic-topline", "diagnostic-menu", "diagnostic-ops", "diagnostic-campaigns"):
            assert state["sub_skill_status"][sub] == "ok"


def test_full_run_assembles_cross_cutting(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(output_layout, "RUN_ROOT", Path(tmp) / "runs")
        inputs = Path(tmp) / "inputs"
        inputs.mkdir()
        _synth_csv(inputs / "synth.csv")

        result = entry.run(client="t", window_start="2026-02-08", window_end="2026-05-08",
                           inputs_dir=inputs, when=datetime(2026, 5, 8, 14, 30, 0))

        radar = json.loads((result.layout.root / "cross_cutting" / "radar.json").read_text())
        for dim in ("AOV", "Re-order Rate", "Conversion", "Traffic", "Marketing Efficiency", "Operations", "Campaigns / ROAS"):
            assert dim in radar
            assert isinstance(radar[dim], (int, float))

        tier = json.loads((result.layout.root / "cross_cutting" / "tier_rollup.json").read_text())
        assert "Venice" in tier
        # Venice has 35% photo coverage → menu="red", and ops 88% uptime → ops="red"; rollup should be red
        assert tier["Venice"]["flag"] == "red"


def test_full_run_foundation_gate_triggered_by_low_rating_and_low_photos(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(output_layout, "RUN_ROOT", Path(tmp) / "runs")
        inputs = Path(tmp) / "inputs"
        inputs.mkdir()
        _synth_csv(inputs / "synth.csv")

        result = entry.run(client="t", window_start="2026-02-08", window_end="2026-05-08",
                           inputs_dir=inputs, when=datetime(2026, 5, 8, 14, 30, 0))

        state = json.loads(result.layout.run_state_path.read_text())
        # rating min in synth = 4.0 (Venice) → triggers low_rating_below_42 (ops sub-skill)
        # photo_coverage 35% (Venice) → triggers low_photo_coverage (menu sub-skill)
        # Either triggers foundation gate via thresholds (rating < 4.2, photo_coverage < 50)
        assert state["foundation_gate"]["triggered"] is True

        # Action plan now uses tier-aware schema; foundation_gate flag is propagated.
        ap = json.loads((result.layout.root / "action-plan" / "diagnostic-action-plan_results.json").read_text())
        assert ap["foundation_gate_triggered"] is True
        # Red tier exists (Venice has 35% photo coverage and 88% uptime)
        assert "red" in ap["tier_groups"]
        assert "Venice" in ap["tier_groups"]["red"]["stores"]
        assert ap["tier_groups"]["red"]["default_strategy"].startswith("Stop campaigns")
        # Pause-campaigns auto-action exists for red tier
        pause_actions = [a for a in ap["tier_groups"]["red"]["auto_actions"] if "Pause" in a["action"]]
        assert len(pause_actions) == 1


def _synth_csv_with_green(path: Path):
    """Variant with a fully-green store so top15_green_bar fires."""
    df = pd.DataFrame({
        "store": ["BeverlyHills", "Venice", "Brentwood"] * 5,
        "week": list(range(1, 6)) * 3,
        "gross_sales": [12000, 9000, 7000] * 5,
        "orders": [240, 180, 140] * 5,
        "net_payout": [8000, 6000, 4500] * 5,
        # menu cols — BeverlyHills clean-green
        "menu_cvr_pct": [22.0, 14.0, 19.0] * 5,
        "photo_coverage_pct": [85, 35, 70] * 5,
        "hero_set": [True, True, True] * 5,
        "categories_count": [6, 6, 6] * 5,
        "categories_populated": [6, 5, 6] * 5,
        "storefront_to_menu_ctr_pct": [10.0, 11.0, 8.0] * 5,
        # ops cols — BeverlyHills clean-green
        "rating": [4.7, 4.0, 4.3] * 5,
        "error_rate_pct": [1.0, 6.0, 3.0] * 5,
        "cancellation_pct": [0.5, 4.0, 2.5] * 5,
        "uptime_pct": [99.0, 88.0, 95.0] * 5,
        "hours_accurate": [True, False, True] * 5,
        # campaigns — BeverlyHills high ROAS, low promos, lots of incremental orders
        "platform": ["UE", "DD", "GH"] * 5,
        "spend": [600, 400, 200] * 5,
        "attributed_sales": [4500, 800, 1000] * 5,
        "roas": [7.5, 2.0, 5.0] * 5,
        "incremental_orders_per_week": [25, 5, 8] * 5,
        "promo_count_active": [1, 4, 1] * 5,
    })
    df.to_csv(path, index=False)


def test_full_run_generates_cross_cutting_charts(monkeypatch):
    """Wk 3: orchestrator Phase 3 emits radar + tier_donut + top15_green_bar PNGs;
    campaigns sub-skill emits campaign_2x2 PNG into its own charts subdir."""
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(output_layout, "RUN_ROOT", Path(tmp) / "runs")
        inputs = Path(tmp) / "inputs"
        inputs.mkdir()
        _synth_csv_with_green(inputs / "synth.csv")

        result = entry.run(
            client="t", window_start="2026-02-08", window_end="2026-05-08",
            inputs_dir=inputs, when=datetime(2026, 5, 8, 14, 30, 0),
        )

        cc_dir = result.layout.root / "cross_cutting"
        assert (cc_dir / "radar_7dim.png").exists()
        assert (cc_dir / "tier_donut.png").exists()
        # top15_green_bar requires ≥1 green store; this variant has BeverlyHills as green.
        assert (cc_dir / "top15_green_bar.png").exists()
        # campaign_2x2 lives in the campaigns sub-skill's chart subdir
        camp_chart = result.layout.root / "campaigns" / "charts" / "campaign_2x2.png"
        assert camp_chart.exists()


def test_full_run_produces_notion_page_artifact(monkeypatch):
    """After full pipeline run, notion_page.md and notion_blocks.json exist with non-empty content."""
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(output_layout, "RUN_ROOT", Path(tmp) / "runs")
        inputs = Path(tmp) / "inputs"
        inputs.mkdir()
        _synth_csv(inputs / "synth.csv")

        result = entry.run(
            client="t", window_start="2026-02-08", window_end="2026-05-08",
            inputs_dir=inputs, when=datetime(2026, 5, 8, 14, 30, 0),
        )

        page_md = result.layout.root / "notion_page.md"
        blocks_json = result.layout.root / "notion_blocks.json"
        assert page_md.exists() and page_md.stat().st_size > 200
        assert blocks_json.exists()
        blocks = json.loads(blocks_json.read_text())
        assert isinstance(blocks, list) and len(blocks) > 5
        # Title appears in markdown
        assert "Diagnostics & Action Plan" in page_md.read_text()


def test_full_run_with_publish_flag_writes_publish_payload(monkeypatch):
    """Wk 4 Chunk 3: publish_to_notion=True writes publish_blocks.json + charts_manifest.json."""
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(output_layout, "RUN_ROOT", Path(tmp) / "runs")
        inputs = Path(tmp) / "inputs"
        inputs.mkdir()
        _synth_csv(inputs / "synth.csv")

        result = entry.run(
            client="t", window_start="2026-02-08", window_end="2026-05-08",
            inputs_dir=inputs, when=datetime(2026, 5, 8, 14, 30, 0),
            publish_to_notion=True,
        )

        assert (result.layout.root / "publish_blocks.json").exists()
        assert (result.layout.root / "charts_manifest.json").exists()
        # Filtered payload has no image blocks
        filtered = json.loads((result.layout.root / "publish_blocks.json").read_text())
        assert all(b.get("type") != "image" for b in filtered)
        # Manifest is a list (may be empty if no charts emitted; here at least the cross-cutting charts exist)
        manifest = json.loads((result.layout.root / "charts_manifest.json").read_text())
        assert isinstance(manifest, list)


def test_full_run_action_plan_groups_findings_by_tier(monkeypatch):
    """Action plan organizes by location tier; all four tier groups always exist."""
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(output_layout, "RUN_ROOT", Path(tmp) / "runs")
        inputs = Path(tmp) / "inputs"
        inputs.mkdir()
        _synth_csv(inputs / "synth.csv")

        result = entry.run(
            client="t", window_start="2026-02-08", window_end="2026-05-08",
            inputs_dir=inputs, when=datetime(2026, 5, 8, 14, 30, 0),
        )

        ap = json.loads((result.layout.root / "action-plan" / "diagnostic-action-plan_results.json").read_text())
        for tier in ("red", "yellow", "green", "new"):
            assert tier in ap["tier_groups"]
            assert "stores" in ap["tier_groups"][tier]
            assert "default_strategy" in ap["tier_groups"][tier]
            assert "auto_actions" in ap["tier_groups"][tier]
            assert "finding_actions" in ap["tier_groups"][tier]
        assert "portfolio_actions" in ap
        assert "deliverable_triggers" in ap
