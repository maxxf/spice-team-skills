"""Action plan builder.

v0.2-tier-aware: groups action items by location tier (red/yellow/green/new),
applies the framework's default tier strategy as automatic action items per
group, layers finding-driven actions inside their target store's tier group.

Backward-compat: when called WITHOUT tier_rollup, falls back to v0.1 stub
behavior (severity-based kanban). Preserves existing test_smoke_e2e.py
expectations.
"""
from __future__ import annotations

TIER_DEFAULT_STRATEGY = {
    "red": "Stop campaigns at this store. Fix the broken bucket(s) before any growth investment.",
    "yellow": "Targeted fix on the weak bucket. Maintain current spend.",
    "green": "Scale: increase ad budget, expand to additional platforms, feature in marketing.",
    "new": "Awareness investment + diagnostic re-run at 60-day mark.",
}

TIER_RANK = {"red": 4, "yellow": 3, "new": 2, "green": 1}  # for "worst tier" arbitration


def build_plan(
    findings: list[dict],
    *,
    foundation_triggered: bool,
    tier_rollup: dict[str, dict] | None = None,
) -> dict:
    """Build a tier-aware action plan.

    Args:
      findings: list of finding dicts from sub-skills (each has scope, severity, deliverable_trigger).
      foundation_triggered: True if orchestrator's foundation gate fired.
      tier_rollup: store→{flag, worst_bucket, per_bucket_flags} from cross_cutting.rollup_tiers.
                   If None, falls back to severity-grouped output for backward compat.
    """
    if tier_rollup is None:
        return _build_v01_stub(findings, foundation_triggered=foundation_triggered)

    return _build_tier_aware(findings, foundation_triggered=foundation_triggered, tier_rollup=tier_rollup)


# ---------------------------------------------------------------------------
# v0.1 fall-back (preserves test_smoke_e2e.py + the 2 backward-compat tests)
# ---------------------------------------------------------------------------

def _build_v01_stub(findings: list[dict], *, foundation_triggered: bool) -> dict:
    p1, p2, p3 = [], [], []
    for f in findings:
        item = {**f}
        if foundation_triggered:
            if f["severity"] == "foundation":
                p1.append(item)
            else:
                p3.append(item)
        else:
            sev = f["severity"]
            if sev in ("foundation", "high"):
                p1.append(item)
            elif sev == "medium":
                p2.append(item)
            else:
                p3.append(item)

    return {
        "version": "0.1-stub",
        "kanban": {"P1_this_week": p1, "P2_next_30d": p2, "P3_watch": p3},
        "deliverable_triggers": [
            f["deliverable_trigger"] for f in findings if f.get("deliverable_trigger")
        ],
    }


# ---------------------------------------------------------------------------
# v0.2 tier-aware path
# ---------------------------------------------------------------------------

def _build_tier_aware(
    findings: list[dict],
    *,
    foundation_triggered: bool,
    tier_rollup: dict[str, dict],
) -> dict:
    # Step 1: bucket stores by tier
    stores_by_tier: dict[str, list[str]] = {"red": [], "yellow": [], "green": [], "new": []}
    for store, info in tier_rollup.items():
        flag = info["flag"]
        if flag in stores_by_tier:
            stores_by_tier[flag].append(store)
    for tier in stores_by_tier:
        stores_by_tier[tier].sort()

    # Step 2: scaffold tier groups (always present, even when empty)
    tier_groups: dict[str, dict] = {}
    for tier in ("red", "yellow", "green", "new"):
        tier_groups[tier] = {
            "stores": stores_by_tier[tier],
            "default_strategy": TIER_DEFAULT_STRATEGY[tier],
            "auto_actions": [],
            "finding_actions": [],
        }

    # Step 3: generate auto-actions per tier per the framework
    portfolio_actions: list[dict] = []

    _emit_red_auto_actions(tier_groups["red"], stores_by_tier["red"], tier_rollup)
    _emit_yellow_auto_actions(tier_groups["yellow"], stores_by_tier["yellow"], tier_rollup, portfolio_actions)
    _emit_green_auto_actions(tier_groups["green"], stores_by_tier["green"], foundation_triggered)
    _emit_new_auto_actions(tier_groups["new"], stores_by_tier["new"], portfolio_actions)

    # Step 4: route findings into tier groups (or portfolio_actions)
    for f in findings:
        scope = f.get("scope", "portfolio")
        if scope == "portfolio":
            portfolio_actions.append({**f})
            continue

        store_names = [s.strip() for s in scope.split(",") if s.strip()]
        unmapped = [s for s in store_names if s not in tier_rollup]

        if unmapped and len(unmapped) == len(store_names):
            # All scoped stores unknown → portfolio with flag
            portfolio_actions.append({**f, "unmapped_store_scope": True})
            continue

        # Worst tier across mapped stores wins
        mapped = [s for s in store_names if s in tier_rollup]
        worst_tier = max(
            (tier_rollup[s]["flag"] for s in mapped),
            key=lambda t: TIER_RANK.get(t, 0),
        )
        item = {**f}
        if foundation_triggered and item.get("severity") != "foundation":
            item["deferred_until_foundation_clear"] = True
        tier_groups[worst_tier]["finding_actions"].append(item)

    # Step 5: sort finding_actions within each tier by impact desc; same for portfolio_actions
    for tier in tier_groups.values():
        tier["finding_actions"] = _sort_actions_by_impact(tier["finding_actions"])
    portfolio_actions = _sort_actions_by_impact(portfolio_actions)

    # Step 6: collect flat deliverable_triggers
    deliverable_triggers: list[dict] = []
    for tier in tier_groups.values():
        for a in tier["auto_actions"]:
            if a.get("deliverable_trigger") is not None:
                deliverable_triggers.append(a["deliverable_trigger"])
        for f in tier["finding_actions"]:
            if f.get("deliverable_trigger") is not None:
                deliverable_triggers.append(f["deliverable_trigger"])
    for f in portfolio_actions:
        if f.get("deliverable_trigger") is not None:
            deliverable_triggers.append(f["deliverable_trigger"])

    return {
        "version": "0.2-tier-aware",
        "foundation_gate_triggered": foundation_triggered,
        "tier_groups": tier_groups,
        "portfolio_actions": portfolio_actions,
        "deliverable_triggers": deliverable_triggers,
    }


def _auto(action: str, *, stores: list[str], rationale: str, deliverable_trigger=None) -> dict:
    return {
        "kind": "auto",
        "action": action,
        "stores": stores,
        "rationale": rationale,
        "deliverable_trigger": deliverable_trigger,
    }


def _sort_actions_by_impact(actions):
    """Sort actions by estimated_impact_usd desc, nulls last, severity as tiebreaker."""
    def key(a):
        val = a.get("estimated_impact_usd")
        has_val = val is not None
        severity_rank = {"foundation": 4, "high": 3, "medium": 2, "low": 1}.get(a.get("severity", "low"), 1)
        return (has_val, val if has_val else 0, severity_rank)
    return sorted(actions, key=key, reverse=True)


def _emit_red_auto_actions(group: dict, red_stores: list[str], rollup: dict[str, dict]) -> None:
    if not red_stores:
        return

    worst_buckets = sorted({rollup[s]["worst_bucket"] for s in red_stores})
    pause_action = (
        f"Pause all campaigns at {', '.join(red_stores)} — until "
        f"{', '.join(worst_buckets)} fixed"
    )
    group["auto_actions"].append(_auto(
        pause_action,
        stores=list(red_stores),
        rationale="Red tier policy: no spend until fundamentals fixed",
    ))

    for store in red_stores:
        per_bucket = rollup[store].get("per_bucket_flags", {})
        for bucket, flag in per_bucket.items():
            if flag == "red":
                group["auto_actions"].append(_auto(
                    f"Fix {bucket} at {store}",
                    stores=[store],
                    rationale=f"Red {bucket} bucket — fix before resuming spend",
                ))


def _emit_yellow_auto_actions(
    group: dict,
    yellow_stores: list[str],
    rollup: dict[str, dict],
    portfolio_actions: list[dict],
) -> None:
    if not yellow_stores:
        return

    for store in yellow_stores:
        worst = rollup[store]["worst_bucket"]
        group["auto_actions"].append(_auto(
            f"Targeted fix at {store} — weak bucket: {worst}",
            stores=[store],
            rationale=f"Yellow tier: address {worst} without pulling spend",
        ))

    portfolio_actions.append(_auto(
        f"Hold spend at {', '.join(yellow_stores)} — no scaling until fixed",
        stores=list(yellow_stores),
        rationale="Yellow tier: maintain current spend, no growth investment yet",
    ))


def _emit_green_auto_actions(group: dict, green_stores: list[str], foundation_triggered: bool) -> None:
    if not green_stores:
        return

    if foundation_triggered:
        group["auto_actions"].append(_auto(
            f"HOLD all scaling at {', '.join(green_stores)} — foundation gate active",
            stores=list(green_stores),
            rationale="Foundation gate active: no growth investment until cleared",
        ))
    else:
        group["auto_actions"].append(_auto(
            f"Increase ad budget +20% at {', '.join(green_stores)}",
            stores=list(green_stores),
            rationale="Green tier ready to scale",
            deliverable_trigger={
                "skill": "campaign-plan",
                "params": {"stores": list(green_stores), "focus": "scale"},
            },
        ))

    group["auto_actions"].append(_auto(
        f"Feature {', '.join(green_stores)} in marketing",
        stores=list(green_stores),
        rationale="Green tier: highlight wins externally",
    ))


def _emit_new_auto_actions(
    group: dict,
    new_stores: list[str],
    portfolio_actions: list[dict],
) -> None:
    if not new_stores:
        return

    for store in new_stores:
        group["auto_actions"].append(_auto(
            f"Continue awareness investment at {store}",
            stores=[store],
            rationale="New tier: build awareness while data accrues",
            deliverable_trigger={
                "skill": "campaign-plan",
                "params": {"stores": [store], "focus": "awareness"},
            },
        ))

    portfolio_actions.append(_auto(
        f"Schedule diagnostic re-run on day-60 for {', '.join(new_stores)}",
        stores=list(new_stores),
        rationale="New tier: re-diagnose at 60-day mark to assign permanent tier",
    ))
