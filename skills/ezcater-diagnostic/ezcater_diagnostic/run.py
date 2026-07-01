from __future__ import annotations

"""Top-level catering diagnostic orchestrator.

Load CSV(s) → validate → aggregate → score sub-buckets → roll up tiers →
badge funnel → foundation gate → findings → radar → action plan → result dict.
Deterministic and credit-free (pure pandas), mirroring `client-diagnostics`.
"""

from pathlib import Path

import pandas as pd

from ezcater_diagnostic import action_plan, badge, findings, input_schema, radar, scorers, tiering


def _momentum_pct(df: pd.DataFrame) -> float | None:
    """Portfolio month-over-month sales delta (last vs prior bucket), %."""
    by_month = df.groupby("month")["gross_sales"].sum().sort_index()
    if len(by_month) < 2:
        return None
    prior, last = float(by_month.iloc[-2]), float(by_month.iloc[-1])
    if prior <= 0:
        return None
    return round((last - prior) / prior * 100.0, 1)


def run_diagnostic(df: pd.DataFrame, *, client: str = "client", portfolio: dict | None = None) -> dict:
    input_schema.validate(df)
    by_store = scorers.aggregate_by_store(df)

    per_store_tiers: dict[str, dict] = {}
    tier_counts = {"green": 0, "yellow": 0, "red": 0, "new": 0}
    for _, row in by_store.iterrows():
        store = str(row["store"])
        ops_flag, ops_reasons = scorers.classify_ops(row)
        vis_flag, vis_reasons = scorers.classify_visibility(row)
        pkg_flag, pkg_reasons = scorers.classify_packaging(row)
        rollup = tiering.rollup_store(
            orders=int(row["orders"]),
            status=row["status"],
            ops_flag=ops_flag,
            visibility_flag=vis_flag,
            packaging_flag=pkg_flag,
        )
        rollup["reasons"] = {"ops": ops_reasons, "visibility": vis_reasons, "packaging": pkg_reasons}
        per_store_tiers[store] = rollup
        tier_counts[rollup["tier"]] += 1

    badge_funnel = badge.compute_badge_funnel(by_store)
    foundation_gate = tiering.compute_foundation_gate(by_store)
    found = findings.detect_findings(by_store, badge_funnel, portfolio)
    momentum = _momentum_pct(df)
    radar_result = radar.compute_radar(by_store, per_store_tiers, momentum, portfolio)
    plan = action_plan.build_action_plan(found, foundation_gate, tier_counts)

    return {
        "client": client,
        "window_days": 90,
        "store_count": len(by_store),
        "portfolio": portfolio,
        "totals": {
            "gross_sales": round(float(by_store["gross_sales"].sum()), 2),
            "orders": int(by_store["orders"].sum()),
            "aov": round(float(by_store["gross_sales"].sum() / by_store["orders"].sum()), 2)
            if by_store["orders"].sum() else 0.0,
            "momentum_pct": momentum,
        },
        "tier_counts": tier_counts,
        "per_store_tiers": per_store_tiers,
        "badge_funnel": badge_funnel,
        "foundation_gate": foundation_gate,
        "findings": found,
        "radar": radar_result,
        "action_plan": plan,
    }


def run_from_inputs_dir(inputs_dir: Path, *, client: str = "client") -> dict:
    inputs_dir = Path(inputs_dir)
    csvs = sorted(inputs_dir.glob("*.csv"))
    if not csvs:
        raise SystemExit(f"no input CSVs found in {inputs_dir}")
    df = pd.concat([pd.read_csv(c) for c in csvs], ignore_index=True)
    # Optional portfolio-level funnel data (Search/Menu views, conversion vs peer, customer mix).
    portfolio = None
    pf = inputs_dir / "portfolio.json"
    if pf.exists():
        import json
        portfolio = json.loads(pf.read_text())
    return run_diagnostic(df, client=client, portfolio=portfolio)
