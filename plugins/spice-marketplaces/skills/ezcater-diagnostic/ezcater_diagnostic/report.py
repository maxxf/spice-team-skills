from __future__ import annotations

"""Render a diagnostic result dict to a skimmable markdown report.

This is the text deliverable. The richer Notion/PDF/chart layer (Phase 4) reuses
the delivery orchestrator's notion_assembly + chart helpers against this result.
"""

TIER_EMOJI = {"green": "🟢", "yellow": "🟡", "red": "🔴", "new": "🆕"}
SEV_EMOJI = {"foundation": "🛑", "high": "🔴", "medium": "🟠", "win": "✅"}


def _fmt_stores(stores: list[str], limit: int = 8) -> str:
    if len(stores) <= limit:
        return ", ".join(stores)
    return ", ".join(stores[:limit]) + f" … (+{len(stores) - limit} more)"


def _count(stores: list[str]) -> str:
    n = len(stores)
    return f"{n} store" if n == 1 else f"{n} stores"


def render_markdown(result: dict) -> str:
    t = result["totals"]
    bf = result["badge_funnel"]
    tc = result["tier_counts"]
    radar = result["radar"]
    gate = result["foundation_gate"]
    lines: list[str] = []

    lines.append(f"# ezCater Diagnostic — {result['client']} (trailing {result['window_days']}d)")
    lines.append("")

    if gate["triggered"]:
        metrics = ", ".join(tr["metric"] for tr in gate["triggers"])
        lines.append(f"> 🛑 **Foundation gate triggered:** {metrics}. Visibility spend is HOLD until fixed.")
        lines.append("")

    # Hero stats
    mom = t["momentum_pct"]
    mom_str = f"{mom:+.1f}% MoM" if mom is not None else "n/a"
    lines.append("## Headline")
    lines.append(f"- **Stores:** {result['store_count']}")
    lines.append(f"- **90-day sales:** ${t['gross_sales']:,.0f} · **Orders:** {t['orders']:,} · **AOV:** ${t['aov']:,.0f}")
    lines.append(f"- **Momentum:** {mom_str}")
    overall = radar["overall"]
    lines.append(f"- **Brand Health:** {overall}/10 (mean of {radar['measured_count']} measured axes)" if overall is not None else "- **Brand Health:** n/a")
    lines.append("")

    # Radar
    lines.append("## Brand Health Radar")
    for axis, score in radar["axes"].items():
        lines.append(f"- {axis}: {'(pending)' if score is None else f'{score}/10'}")
    lines.append("")

    # Tiers
    lines.append("## Location Tiers")
    lines.append(
        f"{TIER_EMOJI['green']} {tc['green']} Green · "
        f"{TIER_EMOJI['yellow']} {tc['yellow']} Yellow · "
        f"{TIER_EMOJI['red']} {tc['red']} Red · "
        f"{TIER_EMOJI['new']} {tc['new']} New"
    )
    lines.append("")

    # Badge funnel
    lines.append("## Reliability Rockstar Badge Funnel")
    lines.append(
        f"- Total: {bf['total']} → Active: {bf['active']} → Volume-eligible: {bf['volume_eligible']} → "
        f"Pass goals (excl. tracking): {bf['pass_excl_tracking']} → Full pass: {bf['full_pass']} → Badged: {bf['badged']}"
    )
    if bf["tracking_blocked_count"]:
        lines.append(f"- 🛑 **{bf['tracking_blocked_count']} stores pass every goal except Delivery Tracking ≥75%** — enable delivery status updates to unlock the badge.")
    if bf["enrollment_gap_count"]:
        lines.append(f"- 🛑 **{bf['enrollment_gap_count']} stores meet all goals but aren't badged** — enrollment/config gap.")
    lines.append("")

    # Action plan
    plan = result["action_plan"]
    lines.append("## Action Plan")
    for note in plan["lead"]:
        lines.append(f"- {note}")
    if plan["this_cycle"]:
        lines.append("")
        lines.append("**This cycle (foundation + high):**")
        for f in plan["this_cycle"]:
            scope = "portfolio" if not f["stores"] else f"{_count(f['stores'])}: {_fmt_stores(f['stores'])}"
            lines.append(f"- {SEV_EMOJI.get(f['severity'], '•')} `{f['pattern_id']}` — {f['action']} ({scope})")
    if plan["next_cycle"]:
        lines.append("")
        lines.append("**Next cycle (medium):**")
        for f in plan["next_cycle"]:
            scope = "portfolio" if not f["stores"] else _count(f["stores"])
            lines.append(f"- {SEV_EMOJI.get(f['severity'], '•')} `{f['pattern_id']}` — {f['action']} ({scope})")
    lines.append("")

    return "\n".join(lines)
