"""Regression test for the spend-sanity guard.

The most common data error in this audit is feeding GROSS ad spend (platform ad
credits / co-funded promos not netted out), which roughly doubles spend and halves
ROAS. The guard flags any location above 60% marketing so a human verifies the
spend is net before the number ships. This test locks that guard.

    python -m tests.spend_sanity_test
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from analyze import analyze  # noqa: E402

SANITY_MARKER = "SPEND SANITY"


def build(spend_per_wk: float) -> pd.DataFrame:
    """One location, 26 weeks, constant $50k/wk gross. spend_per_wk sets marketing %."""
    weeks = [date(2025, 11, 25) + timedelta(weeks=i) for i in range(26)]
    rows = []
    for i, wk in enumerate(weeks):
        gross = 50_000.0
        rows.append({
            "location_id": "loc", "location_name": "Loc", "comp_set": "c", "market": "M",
            "week_starting": wk, "week_index": i + 1, "platform": "all",
            "gross_sales": gross, "net_payout": gross * 0.7, "orders": gross / 50,
            "organic_sales": gross * 0.5, "paid_sales": gross * 0.5,
            "spend": spend_per_wk, "attributed_sales": spend_per_wk * 2.0,
            "cancel_rate": 0.04, "menu_cvr": 0.30, "menu_views": (gross / 50) / 0.30,
            "new_reviews": 10, "avg_rating": 4.4,
        })
    return pd.DataFrame(rows)


def run(spend_per_wk: float) -> list[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        unified = tmp / "unified.csv"
        build(spend_per_wk).to_csv(unified, index=False)
        cfg = SKILL_DIR / "clients" / "_spend_sanity_test.json"
        cfg.write_text(json.dumps({"client_slug": "_spend_sanity_test"}))
        try:
            res = analyze(unified, "_spend_sanity_test", SKILL_DIR)
        finally:
            cfg.unlink()
    return res["portfolio"]["completeness_flags"]


def main() -> int:
    # 70% marketing (gross-looking) → guard MUST fire.
    hot = " ".join(run(35_000))   # 35k / 50k = 70%
    # 20% marketing (plausible net) → guard MUST NOT fire.
    ok = " ".join(run(10_000))    # 10k / 50k = 20%

    passed = True
    if SANITY_MARKER not in hot:
        print("✗ guard did NOT fire at 70% marketing (should have)")
        passed = False
    else:
        print("✓ guard fires at 70% marketing")
    if SANITY_MARKER in ok:
        print("✗ guard fired at 20% marketing (false positive)")
        passed = False
    else:
        print("✓ guard silent at 20% marketing")

    print("SPEND SANITY TEST PASSED ✓" if passed else "SPEND SANITY TEST FAILED")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
