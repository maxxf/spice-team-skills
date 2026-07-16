"""Render analysis.json into a client-facing markdown deliverable.

The markdown is designed to convert cleanly to PDF via the existing Spice `pdf`
skill. Structure matches references/deliverable-template.md.

Usage:
    python render_deliverable.py --client <slug> --analysis <path>/analysis.json --output <path>/deliverable.md
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

PAGE_BREAK = "\n\n\\newpage\n\n"


def fmt_usd(x: float | None, k_threshold: float = 10_000) -> str:
    if x is None:
        return "n/a"
    if abs(x) >= k_threshold:
        return f"${x/1_000:,.0f}K"
    return f"${x:,.0f}"


def fmt_pct(x: float | None, places: int = 1) -> str:
    if x is None:
        return "n/a"
    return f"{x*100:.{places}f}%"


def fmt_roas(x: float | None) -> str:
    if x is None:
        return "n/a"
    return f"{x:.1f}x"


ACTION_ORDER = ["CUT", "PULL_BACK_TO_NC_ONLY", "CONCENTRATE", "FIX_OPS_FIRST", "HOLD"]
ACTION_GLOSS = {
    "CUT": "Spend bought no incremental sales — stop it",
    "PULL_BACK_TO_NC_ONLY": "Reduce to a new-customer-only layer",
    "CONCENTRATE": "Under-invested and paying back — add spend",
    "FIX_OPS_FIRST": "Ops leaking — spend can't fix; pause it",
    "HOLD": "Spend is paying back — no change",
}


def render_exec_summary(data: dict, display_name: str, window_start: str, window_end: str) -> str:
    p = data["portfolio"]
    action_rows = []
    for action in ACTION_ORDER:
        count = p["action_counts"].get(action, 0)
        if count == 0:
            continue
        spend = p["action_spend"].get(action, 0)
        action_rows.append(
            f"| {action.replace('_', ' ')} | {count} | {fmt_usd(spend)} | {ACTION_GLOSS[action]} |"
        )

    top5 = data["locations"][:5]
    top5_rows = []
    for i, loc in enumerate(top5, 1):
        if loc["projected_annual_swing_usd"] <= 0:
            continue
        top5_rows.append(
            f"{i}. **{loc['action'].replace('_', ' ')} — {loc['location_name']}** — "
            f"projected {fmt_usd(loc['projected_annual_swing_usd'])} annualized"
        )

    benchmark = p.get("marketing_pct_benchmark", 0.03)
    bench_pct = f"{benchmark*100:.0f}%"
    cur = p.get("portfolio_marketing_pct") or 0
    if cur > benchmark * 1.6:
        benchmark_read = (
            f"materially above {bench_pct} — a strong cannibalization signal. The portfolio is "
            f"paying for sales it would likely have won anyway."
        )
    elif cur < benchmark * 0.66:
        benchmark_read = (
            f"below {bench_pct} — high-ROAS locations may be under-invested. See the CONCENTRATE "
            f"recommendations."
        )
    elif cur > benchmark:
        benchmark_read = f"slightly above {bench_pct} — review the pull-back candidates."
    else:
        benchmark_read = f"near the {bench_pct} benchmark."

    return f"""# Cannibalization Audit — {display_name}

**Window:** {window_start} to {window_end} · **Locations:** {p['location_count']}

## The Headline

Of {fmt_usd(p['total_spend'])} spent on 3P marketing over the window,
**{fmt_usd(p['cannibalized_spend_annualized_low'])}–{fmt_usd(p['cannibalized_spend_annualized_high'])} (annualized)** bought no incremental sales.

If the recommended reallocation is adopted across the portfolio,
projected net-payout lift: **+{fmt_usd(p['projected_net_payout_lift_annualized'])} annualized**.

## Recommended Actions

| Action | Locations | Total spend | What it means |
|---|---|---|---|
{chr(10).join(action_rows)}

## The Highest-Impact Moves

{chr(10).join(top5_rows) if top5_rows else "_No moves projected with positive dollar swing._"}

## Portfolio Marketing Spend vs. Benchmark

Current marketing-as-percent-of-sales: **{fmt_pct(p.get('portfolio_marketing_pct'))}**
Benchmark: **{bench_pct}**

Read: {benchmark_read}
"""


def render_location_card(loc: dict) -> str:
    events = loc.get("spend_events", [])
    event_rows = []
    for ev in events:
        cf = ev.get("counterfactual", {})
        event_rows.append(
            f"| {ev['event_week']} | {ev['event_type']} | "
            f"${ev['pre_spend_avg']:,.0f} | ${ev['post_spend_avg']:,.0f} | "
            f"${cf.get('observed_sales_post', 0):,.0f} | "
            f"${cf.get('expected_sales_post', 0):,.0f} | "
            f"${cf.get('incremental_sales', 0):,.0f} ({cf.get('confidence', 'n/a')}) |"
        )

    events_section = ""
    if event_rows:
        events_section = f"""
**Spend events the call relied on:**

| Week | Event type | Pre-spend $/wk | Post-spend $/wk | Observed sales (post) | Expected (counterfactual) | Incremental (confidence) |
|---|---|---|---|---|---|---|
{chr(10).join(event_rows)}
"""
    else:
        events_section = (
            "\n_No material spend changes detected in window. The recommendation rests on the "
            "aggregate ratios; no natural-experiment counterfactual was available for this location._\n"
        )

    org_start = loc.get("organic_share_start")
    org_end = loc.get("organic_share_end")
    mix_line = (
        f"{fmt_pct(org_start, 0)} → {fmt_pct(org_end, 0)} ({loc.get('mix_shift_trajectory', 'n/a')})"
        if org_start is not None else "no organic/paid split available"
    )

    return f"""### {loc['location_name']} · {loc.get('market', 'n/a')} · {loc['action'].replace('_', ' ')}

**Recommended action:** {loc['action'].replace('_', ' ')}
**Projected annualized dollar swing:** +{fmt_usd(loc['projected_annual_swing_usd'])}
**Confidence:** {loc.get('confidence', 'low').title()}

**Key metrics over the window:**
- Gross sales: {fmt_usd(loc['gross_sales_total'])} total
- Net payout: {fmt_pct(loc.get('payout_pct'))}
- ROAS: {fmt_roas(loc.get('roas'))} on their own spend{f" · {fmt_roas(loc.get('roas_gross'))} before platform ad credits / co-funding" if loc.get('roas_gross') is not None else ""}
- Marketing % of sales: {fmt_pct(loc.get('marketing_pct'), places=2)}
- Organic share: {mix_line}
- Cancel rate: {fmt_pct(loc.get('cancel_rate'))} · Menu CVR: {fmt_pct(loc.get('menu_cvr'))} · Ratings velocity: {loc.get('ratings_velocity') or 'n/a'}/wk

**Why this action:**

{loc.get('rationale', '_(no rationale provided)_')}

{render_campaign_plan(loc.get('campaign_plan') or {})}
{events_section}
"""


def render_campaign_plan(plan: dict) -> str:
    if not plan or not plan.get("moves"):
        return ""
    moves = "\n".join(f"- {m}" for m in plan["moves"])
    return (
        "**How to run it (campaign moves):**\n\n"
        f"_Audience:_ {plan.get('audience', 'n/a')}  ·  _Offers:_ {plan.get('offers', 'n/a')}\n\n"
        f"{moves}\n"
    )


def render_methodology() -> str:
    return """## How this report was made

**Routing logic.** Each location's recommended action is derived from its ROAS, marketing-as-percent-of-sales, the cannibalization finding, organic/paid mix shift, and operational quality. Full rules: methodology appendix on request.

**Counterfactual baselines** for each spend event use a Bayesian blend of:
- Comp-store locations not running the same spend change (weight 0.6 when ≥5 comps available)
- Prior-year same-week sales for the same location (weight 0.25 when available)
- Brand-wide seasonal trend (weight 0.15)

**Confidence bands.** Each per-location callout is rated High (≥90% confidence), Medium (~70%), or suppressed (below 70%). The headline cannibalization number is reported as a range based on volume-weighted average confidence.

**What this report does not do:**
- Recommend specific creative or campaign-level optimizations (separate Spice deliverable)
- Make claims about 1P (direct-to-consumer) marketing ROI — only 3P / delivery marketplace
- Project beyond the audit window
"""


def render(data: dict, display_name: str, window_start: str, window_end: str) -> str:
    parts = [render_exec_summary(data, display_name, window_start, window_end)]
    parts.append(PAGE_BREAK + "## Portfolio Mix Shift\n\n_Insert organic-vs-paid trajectory chart here_")
    for loc in data["locations"]:
        parts.append(PAGE_BREAK + render_location_card(loc))
    parts.append(PAGE_BREAK + render_methodology())
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", required=True)
    parser.add_argument("--analysis", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--display-name", default=None, help="Client display name for title")
    parser.add_argument("--window-start", default="")
    parser.add_argument("--window-end", default=str(date.today()))
    args = parser.parse_args()

    data = json.loads(args.analysis.read_text())
    display_name = args.display_name or args.client.replace("-", " ").title()
    md = render(data, display_name, args.window_start, args.window_end)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(md)
    print(f"Wrote deliverable to {args.output} ({len(md):,} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
