from __future__ import annotations

"""Cross-cutting Phase 3 computation: radar composite, tier rollup, W/R/O dedup, foundation gate."""

PRIMARY_OWNED_DIMS = {
    "AOV": "topline",
    "Re-order Rate": "topline",
    "Conversion": "menu",
    "Traffic": "menu",
    "Campaigns / ROAS": "campaigns",
}
SUB_SKILL_PRIORITY = ("ops", "menu", "campaigns", "topline")
FLAG_RANK = {"new": 4, "red": 3, "yellow": 2, "green": 1}


def assemble_radar(payloads: dict[str, dict], *, topline_metrics: dict, campaigns_metrics: dict) -> dict[str, float]:
    """Assemble 7-dim radar. Fail-open: missing owner payloads → 0.0 for that dim."""
    radar: dict[str, float] = {}
    for dim, owner in PRIMARY_OWNED_DIMS.items():
        owner_payload = payloads.get(owner) or {}
        owner_radar = (owner_payload.get("computed") or {}).get("radar_contributions") or {}
        radar[dim] = owner_radar.get(dim, 0.0)

    # Composite: Marketing Efficiency = 1 - (mkt / gross), benchmarked vs 30%, scaled 1-10
    topline_metrics = topline_metrics or {}
    campaigns_metrics = campaigns_metrics or {}
    gross = float(topline_metrics.get("gross_sales", 0) or 0)
    mkt = float(campaigns_metrics.get("total_marketing_investment", 0) or 0)
    if gross > 0:
        mkt_ratio = mkt / gross
        # 0% mkt = 10; 30% mkt = 5 (benchmark); 60%+ mkt = 1
        radar["Marketing Efficiency"] = max(1.0, min(10.0, 10.0 - (mkt_ratio / 0.06)))
    else:
        radar["Marketing Efficiency"] = 0.0

    # Composite: Operations = pct stores not flagged red, scaled 1-10
    ops_payload = payloads.get("ops") or {}
    ops_tiers = (ops_payload.get("computed") or {}).get("tier_contributions") or {}
    if ops_tiers:
        non_red = sum(1 for t in ops_tiers.values() if t.get("flag") != "red")
        pct = non_red / len(ops_tiers)
        radar["Operations"] = max(1.0, min(10.0, pct * 10.0))
    else:
        radar["Operations"] = 0.0

    return radar


def rollup_tiers(per_bucket: dict[str, dict[str, dict]]) -> dict[str, dict]:
    """per_bucket = {'menu': {store: {...}}, 'ops': {...}, 'campaigns': {...}}

    A store's rollup uses ONLY the buckets that emitted data for it.
    Absent-from-bucket means "no signal" — does not become 'new'.
    """
    all_stores = set()
    for bucket in per_bucket.values():
        all_stores.update(bucket.keys())

    rollup: dict[str, dict] = {}
    for store in all_stores:
        present = {b: per_bucket[b][store] for b in per_bucket if store in per_bucket[b]}
        flags_by_bucket = {b: present[b]["flag"] for b in present}
        worst_flag = max(flags_by_bucket.values(), key=lambda f: FLAG_RANK[f])
        worst_bucket = next(b for b, f in flags_by_bucket.items() if f == worst_flag)
        rollup[store] = {
            "flag": worst_flag,
            "worst_bucket": worst_bucket,
            "per_bucket_flags": flags_by_bucket,  # only present buckets
        }
    return rollup


def select_win_risk_opp(payloads: dict[str, dict]) -> list[dict]:
    """Top 3, one per type if possible. Dedup by pattern_id; tiebreak by value, severity, sub_skill priority.

    Fail-open: malformed payloads (missing `drafted` or `win_risk_opp_candidates`) are skipped silently.
    """
    candidates: list[dict] = []
    for sub_skill, payload in (payloads or {}).items():
        if not isinstance(payload, dict):
            continue
        drafted = payload.get("drafted")
        if not isinstance(drafted, dict):
            continue
        wro_list = drafted.get("win_risk_opp_candidates")
        if not isinstance(wro_list, list):
            continue
        ss_short = sub_skill.replace("diagnostic-", "")
        for c in wro_list:
            if not isinstance(c, dict) or "type" not in c:
                continue
            candidates.append({**c, "_sub_skill": ss_short})

    # Dedup by pattern_id; tiebreak via _wro_rank
    by_pattern: dict[str, dict] = {}
    no_pattern: list[dict] = []
    for c in candidates:
        pid = c.get("pattern_id")
        if pid is None:
            no_pattern.append(c)
            continue
        existing = by_pattern.get(pid)
        if existing is None or _wro_rank(c) > _wro_rank(existing):
            by_pattern[pid] = c
    deduped = list(by_pattern.values()) + no_pattern

    # Pick top 1 of each type if available
    selected: list[dict] = []
    for kind in ("win", "risk", "opportunity"):
        of_kind = sorted([c for c in deduped if c["type"] == kind], key=_wro_rank, reverse=True)
        if of_kind:
            selected.append(of_kind[0])
    return selected


def _wro_rank(c: dict) -> tuple:
    val = c.get("value_usd")
    has_val = val is not None
    severity_rank = {"foundation": 4, "high": 3, "medium": 2, "low": 1}.get(c.get("severity", "low"), 1)
    sub_skill_priority = {"ops": 4, "menu": 3, "campaigns": 2, "topline": 1}.get(c.get("_sub_skill", "topline"), 0)
    return (has_val, val if has_val else 0, severity_rank, sub_skill_priority)


FOUNDATION_THRESHOLDS = {
    "rating": ("ops", "<", 4.2),
    "error_rate_pct": ("ops", ">", 5.0),
    "uptime_pct": ("ops", "<", 90.0),
    "menu_cvr_pct": ("menu", "<", 15.0),
    "photo_coverage_pct": ("menu", "<", 50.0),
}


def compute_foundation_gate(payloads: dict[str, dict], sub_skill_status: dict[str, str]) -> dict:
    """Per spec §Decision 3 with fail-conservative rule."""
    triggers: list[dict] = []

    # Fail-conservative: ops or menu failure → trigger
    for required in ("diagnostic-ops", "diagnostic-menu"):
        if sub_skill_status.get(required) == "failed":
            triggers.append({"metric": None, "reason": f"{required.replace('diagnostic-', '')}_sub_skill_failed"})

    # Threshold checks (only if owner sub-skill ran)
    for metric, (owner_short, op, threshold) in FOUNDATION_THRESHOLDS.items():
        owner_full = f"diagnostic-{owner_short}"
        if sub_skill_status.get(owner_full) != "ok":
            continue
        owner_payload = (payloads or {}).get(owner_short) or {}
        owner_metrics = (owner_payload.get("computed") or {}).get("metrics") or {}
        value = owner_metrics.get(metric)
        if value is None:
            continue
        tripped = (op == "<" and value < threshold) or (op == ">" and value > threshold)
        if tripped:
            triggers.append({"metric": metric, "value": value, "threshold": threshold, "scope": "portfolio"})

    return {
        "triggered": bool(triggers),
        "triggers": triggers,
        "override_action_plan": bool(triggers),
    }
