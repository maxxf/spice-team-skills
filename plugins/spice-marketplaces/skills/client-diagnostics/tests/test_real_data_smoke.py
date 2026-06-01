"""Real-data smoke tests for Wk 4. Skipped by default; run with REAL_DATA_DIR env var.

Usage:
    REAL_DATA_DIR=/path/to/dailys-q1-exports .venv/bin/pytest tests/test_real_data_smoke.py -v
"""
import os
import pytest
from pathlib import Path

REAL_DATA_DIR = os.environ.get("REAL_DATA_DIR")
SKIP_REASON = "set REAL_DATA_DIR env var to run real-data smoke"


@pytest.mark.skipif(not REAL_DATA_DIR, reason=SKIP_REASON)
def test_real_data_runs_full_pipeline():
    """Drop a directory of real diagnostic_input.csv files; verify pipeline produces all expected artifacts."""
    from orchestrator import entry, output_layout
    from datetime import datetime

    inputs = Path(REAL_DATA_DIR)
    assert inputs.is_dir(), f"REAL_DATA_DIR={inputs} doesn't exist"
    assert any(inputs.glob("*.csv")), f"No CSVs in {inputs}"

    result = entry.run(
        client=os.environ.get("REAL_DATA_CLIENT", "smoke-test"),
        window_start="2026-02-09",
        window_end="2026-05-09",
        inputs_dir=inputs,
        when=datetime.now(),
    )

    # All expected artifacts exist
    assert (result.layout.root / "notion_page.md").exists()
    assert (result.layout.root / "notion_blocks.json").exists()
    assert (result.layout.root / "cross_cutting" / "radar_7dim.png").exists()
    assert (result.layout.root / "cross_cutting" / "tier_donut.png").exists()
    assert (result.layout.root / "cross_cutting" / "top15_green_bar.png").exists()

    # Print path so user can inspect
    print(f"\n✅ Real-data smoke complete. Artifacts: {result.layout.root}")
