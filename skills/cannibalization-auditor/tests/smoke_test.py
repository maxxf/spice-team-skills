"""End-to-end smoke test: generate synthetic unified.csv, run analyze.py + render.

Produces 5 locations with known patterns; checks that each lands on the
expected routing action. Run from the skill root:

    python -m tests.smoke_test
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


def build_synthetic_unified() -> pd.DataFrame:
    """Five locations, 26 weeks each, with deliberate patterns.

    - soma: 11x ROAS, <1% spend, 82% payout → under-invested → CONCENTRATE
    - venice: 7.5x ROAS, 78% payout, modestly over benchmark → HOLD
    - silver-lake: 3.5x ROAS, 8% spend, organic stable → PULL_BACK_TO_NC_ONLY
      (below the 4x hold gate — locks the saturation boundary; a store CLEARING
      4x must HOLD, which `venice` at 7.5x covers)
    - san-jose-broken: 18% cancel rate → ops broken → FIX_OPS_FIRST
    - waste-loc: 1.5x ROAS, 16% spend, organic rising → PULL_BACK_TO_NC_ONLY
    """
    weeks = [date(2025, 11, 25) + timedelta(weeks=i) for i in range(26)]
    rows = []

    specs = [
        # (loc_id, name, comp_set, market, gross_per_wk, payout_pct, spend_per_wk, attr_roas, org_share_start, org_share_end, cancel, cvr)
        ("soma", "SoMa", "sf-bay", "SF", 150_000, 0.82, 1000, 11.0, 0.55, 0.58, 0.03, 0.32),
        ("venice", "Venice", "la-westside", "LA", 90_000, 0.78, 4500, 7.5, 0.45, 0.48, 0.04, 0.30),
        ("silver-lake", "Silver Lake", "la-eastside", "LA", 75_000, 0.74, 6000, 3.5, 0.42, 0.43, 0.05, 0.28),
        ("san-jose-broken", "San Jose", "sf-bay", "SF", 40_000, 0.65, 3500, 3.0, 0.40, 0.35, 0.18, 0.22),
        ("waste-loc", "WasteLoc", "la-central", "LA", 50_000, 0.70, 8000, 1.5, 0.40, 0.52, 0.05, 0.31),
    ]

    for spec in specs:
        loc_id, name, comp_set, market, gross_per_wk, payout_pct, spend_per_wk, roas, org_start, org_end, cancel, cvr = spec
        for i, wk in enumerate(weeks):
            # Linear interpolation of organic share over the window
            org_share = org_start + (org_end - org_start) * (i / max(len(weeks) - 1, 1))
            gross = gross_per_wk
            organic_sales = gross * org_share
            paid_sales = gross * (1 - org_share)
            payout = gross * payout_pct
            spend = spend_per_wk
            attr = spend * roas

            rows.append({
                "location_id": loc_id, "location_name": name, "comp_set": comp_set, "market": market,
                "week_starting": wk, "week_index": i + 1, "platform": "all",
                "gross_sales": gross, "net_payout": payout, "orders": gross / 50,
                "organic_sales": organic_sales, "paid_sales": paid_sales,
                "spend": spend, "attributed_sales": attr,
                "cancel_rate": cancel, "menu_cvr": cvr, "menu_views": (gross / 50) / cvr,
                "new_reviews": 15, "avg_rating": 4.3,
            })

    return pd.DataFrame(rows)


def main() -> int:
    print("[1/4] Building synthetic unified dataset...")
    df = build_synthetic_unified()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        unified_path = tmp / "unified.csv"
        df.to_csv(unified_path, index=False)
        print(f"      Wrote {len(df)} rows to {unified_path}")

        # Need a minimal client config for the analyze script to find
        client_dir = SKILL_DIR / "clients"
        client_dir.mkdir(parents=True, exist_ok=True)
        smoke_config = client_dir / "_smoke_test.json"
        smoke_config.write_text(json.dumps({"client_slug": "_smoke_test"}))

        print("[2/4] Running analyze.py...")
        result = analyze(unified_path, "_smoke_test", SKILL_DIR)

        smoke_config.unlink()

    print("[3/4] Checking routing actions...")
    # The synthetic data has constant spend per location (no spend events), so
    # cannibalization detection won't fire — actions come from the signal-based
    # rules: ops health, ROAS, marketing %, and mix-shift trajectory.
    expected = {
        "soma": "CONCENTRATE",            # 11x ROAS, 0.67% spend → under-invested
        "venice": "HOLD",                 # 7.5x ROAS, paying back, near benchmark
        "silver-lake": "PULL_BACK_TO_NC_ONLY",  # 3.5x ROAS (below 4x gate), above benchmark, organic stable
        "san-jose-broken": "FIX_OPS_FIRST",     # 18% cancel rate → ops broken
        "waste-loc": "PULL_BACK_TO_NC_ONLY",    # 1.5x ROAS, above benchmark, organic rising
    }
    actual = {loc["location_id"]: loc["action"] for loc in result["locations"]}

    all_pass = True
    for loc_id, exp in expected.items():
        got = actual.get(loc_id)
        flag = "✓" if got == exp else "✗"
        if got != exp:
            all_pass = False
        print(f"      {flag} {loc_id:<20} expected={exp:<22} got={got}")

    print("[4/4] Portfolio summary:")
    p = result["portfolio"]
    print(f"      Locations: {p['location_count']}")
    print(f"      Action counts: {p['action_counts']}")
    print(f"      Portfolio marketing %: {p.get('portfolio_marketing_pct', 0)*100:.2f}% "
          f"(benchmark: {p.get('marketing_pct_benchmark', 0.03)*100:.0f}%)")
    print(f"      Projected net payout lift if all recommendations adopted: ${p['projected_net_payout_lift_annualized']:,.0f}")

    print()
    print("Per-location actions:")
    for loc in result["locations"]:
        print(f"  {loc['location_name']:<15} → {loc['action']:<25} "
              f"swing=${loc['projected_annual_swing_usd']:,.0f}")

    if all_pass:
        print("\nSMOKE TEST PASSED ✓")
        return 0
    print("\nSMOKE TEST FAILED — routing actions do not match expectations")
    return 1


if __name__ == "__main__":
    sys.exit(main())
