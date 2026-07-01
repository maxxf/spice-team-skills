from __future__ import annotations

"""Group findings into a tier-aware action plan.

Foundation-gated → lead with the gated fix, visibility spend HOLD. Otherwise
order by severity (foundation > high > medium > win).
"""

from ezcater_diagnostic.findings import SEVERITY_RANK


def build_action_plan(findings: list[dict], foundation_gate: dict, tier_counts: dict) -> dict:
    ordered = sorted(findings, key=lambda f: SEVERITY_RANK.get(f["severity"], 0), reverse=True)

    lead = []
    if foundation_gate["triggered"]:
        gated_metrics = ", ".join(t["metric"] for t in foundation_gate["triggers"])
        lead.append(
            f"⚠️ Foundation gate triggered ({gated_metrics}). Fix fundamentals before buying "
            f"visibility — PPP/ezRewards/sponsored spend is HOLD until clear."
        )

    this_cycle = [f for f in ordered if f["severity"] in ("foundation", "high")]
    next_cycle = [f for f in ordered if f["severity"] == "medium"]
    watch = [f for f in ordered if f["severity"] == "win"]

    return {
        "lead": lead,
        "this_cycle": this_cycle,
        "next_cycle": next_cycle,
        "watch": watch,
        "tier_counts": tier_counts,
        "foundation_gate": foundation_gate,
    }
