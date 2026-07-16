"""Real-data proof run on Goop Kitchen using the figures from the 6-month
review's Data Appendix (Notion page 36bd3ff018e7819ea13ec3888ecafdfa).

These numbers are real, sourced from the goop weekly metrics sheet via the
Notion appendix. The point of this script is to verify the analytical engine
reproduces the directional story of the Goop engagement:

  - Spend cut ~30% (Jan→Feb), sales held → the cut was free (cannibalization)
  - SoMa, Venice, Costa Mesa → CONCENTRATE (UNICORN thesis)
  - SJ, Pasadena → high marketing %, moderate ROAS (RED tier)

Run from the skill root:
    .venv/bin/python -m tests.goop_proof
"""
from __future__ import annotations

import csv
import json
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))
from analyze import analyze  # noqa: E402


# Group-level weekly series Jan 5 - May 11 (19 weeks). Source: Data Appendix.
# (week, sales, net_payout, ad_spend, roas, orders)
GROUP = [
    ("2026-01-05", 1317548,  966697, 53646, 6.0, 27606),
    ("2026-01-12", 1314990,  980363, 47566, 6.9, 27949),
    ("2026-01-19", 1297740,  968271, 47372, 7.6, 27026),
    ("2026-01-26", 1346151, 1013802, 48097, 7.7, 28152),
    ("2026-02-02", 1280132,  990970, 29671, 9.4, 26846),
    ("2026-02-09", 1256275,  974665, 30412, 9.4, 26395),
    ("2026-02-16", 1258309,  971493, 30036, 9.1, 26520),
    ("2026-02-23", 1365715, 1056882, 34384, 9.2, 28975),
    ("2026-03-02", 1361154, 1045938, 35134, 8.6, 28796),
    ("2026-03-09", 1388805, 1069480, 37154, 8.7, 29448),
    ("2026-03-16", 1377194, 1058208, 36070, 9.3, 28916),
    ("2026-03-23", 1276742,  979720, 35810, 9.0, 26933),
    ("2026-03-30", 1220748,  931512, 36921, 8.9, 25868),
    ("2026-04-06", 1281657,  978452, 36450, 8.6, 27016),
    ("2026-04-13", 1330042, 1016045, 37973, 8.6, 27592),
    ("2026-04-20", 1447636, 1122183, 40667, 9.0, 30317),
    ("2026-04-27", 1449059, 1114556, 38694, 8.9, 30320),
    ("2026-05-04", 1428211, 1111156, 35208, 9.1, 29526),
    ("2026-05-11", 1421486, 1104584, 37312, 8.8, 29817),
]

# W20 per-location snapshots — tests routing on real ratios.
# (loc, name, comp, market, sales, mkt_pct, payout_pct, roas)
SNAPSHOTS = [
    ("soma",       "SoMa",       "la",  "SF",       157195, 0.007, 0.82, 10.3),
    ("venice",     "Venice",     "la",  "LA",       123039, 0.018, 0.81, 12.2),
    ("costa-mesa", "Costa Mesa", "la",  "Costa Mesa", 100880, 0.027, 0.80,  8.0),
    ("san-jose",   "San Jose",   "red", "SJ",        50843, 0.157, 0.68,  5.7),
    ("pasadena",   "Pasadena",   "red", "Pasadena",  56280, 0.147, 0.69,  5.6),
]

COLS = [
    "location_id", "location_name", "comp_set", "market", "week_starting",
    "week_index", "platform", "gross_sales", "net_payout", "orders",
    "organic_sales", "paid_sales", "spend", "attributed_sales",
    "cancel_rate", "menu_cvr", "menu_views", "new_reviews", "avg_rating",
]


def build_unified(path: Path) -> None:
    n = len(GROUP)
    rows = []
    for i, (wk, sales, payout, spend, roas, orders) in enumerate(GROUP):
        # Real mix shift over the window: organic 42% → 56% (Notion appendix).
        org_share = 0.42 + (0.56 - 0.42) * (i / (n - 1))
        rows.append({
            "location_id": "portfolio", "location_name": "Portfolio (group)",
            "comp_set": "grp", "market": "ALL", "week_starting": wk,
            "week_index": i + 1, "platform": "all",
            "gross_sales": sales, "net_payout": payout, "orders": orders,
            "organic_sales": round(sales * org_share, 2),
            "paid_sales": round(sales * (1 - org_share), 2),
            "spend": spend, "attributed_sales": round(spend * roas, 2),
            "cancel_rate": "", "menu_cvr": "", "menu_views": "",
            "new_reviews": "", "avg_rating": "",
        })
    for loc, name, comp, mkt, sales, mp, pp, roas in SNAPSHOTS:
        spend = sales * mp
        rows.append({
            "location_id": loc, "location_name": name, "comp_set": comp,
            "market": mkt, "week_starting": "2026-05-11", "week_index": 20,
            "platform": "all", "gross_sales": sales,
            "net_payout": round(sales * pp, 2), "orders": round(sales / 47),
            "organic_sales": "", "paid_sales": "",
            "spend": round(spend, 2), "attributed_sales": round(spend * roas, 2),
            "cancel_rate": "", "menu_cvr": "", "menu_views": "",
            "new_reviews": "", "avg_rating": "",
        })
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "unified.csv"
        build_unified(p)
        cfg = SKILL / "clients" / "_goop_proof.json"
        cfg.write_text(json.dumps({"client_slug": "_goop_proof"}))
        try:
            result = analyze(p, "_goop_proof", SKILL)
        finally:
            cfg.unlink()

    pf = result["portfolio"]
    cannib_lo = pf["cannibalized_spend_annualized_low"]
    cannib_hi = pf["cannibalized_spend_annualized_high"]
    print(f"PORTFOLIO")
    print(f"  total spend (window): ${pf['total_spend']:,.0f}")
    print(f"  cannibalized (window): ${pf['cannibalized_spend_window']:,.0f}")
    print(f"  cannibalized annualized range: ${cannib_lo:,.0f} – ${cannib_hi:,.0f}")
    print(f"  action distribution: {pf['action_counts']}")
    print()
    print(f"PER-LOCATION ACTIONS")
    for l in result["locations"]:
        print(f"  {l['location_name']:<18} → {l['action']:<22} "
              f"roas={l.get('roas') or 0:.1f}x · mkt={l.get('marketing_pct') or 0:.2%}")
    print()
    print(f"SPEND EVENTS (Portfolio)")
    for l in result["locations"]:
        if l["location_id"] != "portfolio":
            continue
        for e in l["spend_events"]:
            cf = e["counterfactual"]
            print(f"  {e['event_week']} {e['event_type']:<10} "
                  f"pre=${e['pre_spend_avg']:>7,.0f}/wk → post=${e['post_spend_avg']:>7,.0f}/wk "
                  f"sustained={e.get('sustained_weeks', '?')}w · conf={cf.get('confidence')}")
            if cf.get("finding"):
                print(f"      └─ {cf['finding']}")

    # Sanity checks against the known Goop story
    actions = {l["location_id"]: l["action"] for l in result["locations"]}
    checks = [
        ("SoMa → CONCENTRATE", actions.get("soma") == "CONCENTRATE"),
        ("Venice → CONCENTRATE", actions.get("venice") == "CONCENTRATE"),
        ("Cannibalization detected on portfolio", any(
            l["cannibalization_detected"] for l in result["locations"] if l["location_id"] == "portfolio"
        )),
        ("Cannibalized > $0", pf["cannibalized_spend_window"] > 0),
    ]
    print()
    print("STORY CHECKS")
    all_pass = True
    for label, ok in checks:
        flag = "✓" if ok else "✗"
        if not ok:
            all_pass = False
        print(f"  {flag} {label}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
