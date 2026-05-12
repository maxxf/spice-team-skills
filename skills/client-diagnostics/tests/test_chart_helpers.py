"""Structural tests for the 4 chart functions wired in Wk 3.

Each test constructs the minimum valid `metrics` dict for a chart, calls the
function with a tempdir, and asserts the resulting PNG file exists, has
non-trivial size, and starts with the PNG magic bytes.

Visual correctness is out of scope (manual eyeball test).
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from orchestrator import chart_helpers

PNG_MAGIC = b"\x89PNG"
MIN_PNG_SIZE = 1024  # any real chart should easily exceed 1KB


def _assert_valid_png(path: Path) -> None:
    assert path.exists(), f"chart file not created: {path}"
    assert path.stat().st_size > MIN_PNG_SIZE, (
        f"chart file too small ({path.stat().st_size} bytes): {path}"
    )
    with open(path, "rb") as f:
        head = f.read(4)
    assert head == PNG_MAGIC, f"file does not start with PNG magic bytes: {path}"


def test_radar_7dim_writes_png():
    metrics = {
        "radar": {
            "AOV": {"current": 6, "target": 8},
            "Re-order Rate": {"current": 5, "target": 8},
            "Conversion": {"current": 6, "target": 8},
            "Marketing Efficiency": {"current": 3, "target": 8},
            "Operations": {"current": 5, "target": 9},
            "Traffic": {"current": 4, "target": 8},
            "Campaigns / ROAS": {"current": 6, "target": 8},
        }
    }
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        result = chart_helpers.radar_7dim(metrics, out)
        assert result == out / "radar_7dim.png"
        _assert_valid_png(result)


def test_tier_donut_writes_png():
    metrics = {
        "tiers": {
            "Green": 46,
            "Yellow": 55,
            "Red": 54,
            "New": 25,
            "payout_share": {"Green": 0.62, "Yellow": 0.24, "Red": 0.10, "New": 0.04},
        }
    }
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        result = chart_helpers.tier_donut(metrics, out)
        assert result == out / "tier_donut.png"
        _assert_valid_png(result)


def test_top15_green_bar_writes_png():
    metrics = {
        "top15_green": [
            {"name": f"Store {i}", "payout": 30000 - i * 1500, "tier": "Green"}
            for i in range(10)
        ]
    }
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        result = chart_helpers.top15_green_bar(metrics, out)
        assert result == out / "top15_green_bar.png"
        _assert_valid_png(result)


def test_campaign_2x2_writes_png():
    metrics = {
        "campaigns": [
            {"name": "DD DashPass", "spend": 12000, "roas": 9.8, "orders": 3200, "platform": "DD"},
            {"name": "UE Sponsored", "spend": 4000, "roas": 3.1, "orders": 800, "platform": "UE"},
            {"name": "GH Loyalty", "spend": 1500, "roas": 1.8, "orders": 240, "platform": "GH"},
            {"name": "DD Promos", "spend": 7000, "roas": 4.4, "orders": 1600, "platform": "DD"},
        ]
    }
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        result = chart_helpers.campaign_2x2(metrics, out)
        assert result == out / "campaign_2x2.png"
        _assert_valid_png(result)
