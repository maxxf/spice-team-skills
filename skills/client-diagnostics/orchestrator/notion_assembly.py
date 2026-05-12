from __future__ import annotations

"""Phase 5: Notion page assembly.

Two outputs:
  - build_page_markdown(...)  → str   (paste-ready markdown)
  - build_page_blocks(...)    → list[dict]  (Notion block JSON for MCP create-pages)

Both consume the same orchestrator state: sub-skill payloads, radar dict, tier
rollup, action plan (v0.2 tier-aware), and foundation gate.

Design notes:
  - Win/Risk/Opportunity headlines: action plan v0.2 has no top-level wro field.
    Strategy here:
      * Win → top green-tier auto-action (the "scale" instruction) if any green
        stores; else first portfolio_action; else placeholder.
      * Risk → highest-impact finding from the red tier_group; else first red
        auto-action; else first foundation trigger; else placeholder.
      * Opportunity → weakest radar dimension framed as "lift X dim from {score}/10".
    Each cell falls back to "—" if the data is missing.
  - Image URLs use file:// + absolute path. Wk 4 swaps these to Notion uploads.
  - Missing sub-skill payloads degrade gracefully (placeholder section + skipped
    completeness footer entry).
"""

import json
from pathlib import Path

SUB_SKILL_ORDER = ("topline", "menu", "ops", "campaigns")
SUB_SKILL_LABELS = {
    "topline": "Top-line Performance",
    "menu": "Menu & Storefront",
    "ops": "Operations",
    "campaigns": "Campaigns",
}
SUB_SKILL_FOOTER_LABELS = {
    "topline": "Topline",
    "menu": "Menu",
    "ops": "Ops",
    "campaigns": "Campaigns",
}

TIER_HEADERS = [
    ("red", "🔴 Red Stores"),
    ("yellow", "🟡 Yellow Stores"),
    ("green", "🟢 Green Stores"),
    ("new", "🆕 New Stores"),
]

ALLOWED_BLOCK_TYPES = {
    "heading_1",
    "heading_2",
    "heading_3",
    "paragraph",
    "callout",
    "bulleted_list_item",
    "image",
    "table",
    "divider",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_page_markdown(
    *,
    client: str,
    window: dict,
    payloads: dict[str, dict],
    radar: dict[str, float],
    tier_rollup: dict[str, dict],
    action_plan: dict,
    foundation_gate: dict,
    charts_dir: Path,
) -> str:
    """Return full dual-half page as markdown (Notion-paste-ready).

    See module docstring for win/risk/opp derivation strategy.
    """
    parts: list[str] = []

    start = window.get("start", "?")
    end = window.get("end", "?")

    # Title
    parts.append(f"# {client} | Diagnostics & Action Plan | {start} – {end}")
    parts.append("")

    # Foundation banner (only if triggered)
    if foundation_gate.get("triggered"):
        triggers_summary = _summarize_triggers(foundation_gate.get("triggers") or [])
        parts.append(
            f"> ⚠️ **Foundation gate triggered.** {triggers_summary}. "
            "All scaling on hold; foundation actions only."
        )
        parts.append("")

    # ----- HALF 1 -----

    # Hero stat strip
    parts.append("## Hero Stat Strip")
    parts.append("")
    hero = _hero_metrics(payloads)
    parts.append("| 90-Day Gross Sales | Orders | Blended AOV | Net Payout |")
    parts.append("|---|---|---|---|")
    parts.append(
        f"| {hero['gross']} | {hero['orders']} | {hero['aov']} | "
        f"{hero['payout']} ({hero['payout_pct']}) |"
    )
    parts.append("")

    # Brand Health Radar
    parts.append("## Brand Health Radar")
    parts.append("")
    radar_path = _chart_path(charts_dir, "radar_7dim.png")
    parts.append(f"![Radar]({radar_path})")
    avg_score, dim1, dim2 = _radar_summary(radar)
    parts.append(f"> Overall {avg_score:.1f}/10. Weakest: {dim1}, {dim2}.")
    parts.append("")

    # Win / Risk / Opportunity
    parts.append("## Win / Risk / Opportunity")
    parts.append("")
    wro = _derive_wro(action_plan=action_plan, radar=radar, foundation_gate=foundation_gate)
    parts.append("| 🏆 Win | ⚠️ Risk | 💡 Opportunity |")
    parts.append("|---|---|---|")
    parts.append(f"| {wro['win']} | {wro['risk']} | {wro['opportunity']} |")
    parts.append("")

    # Action Plan
    parts.append("## Action Plan")
    parts.append("")
    tier_groups = action_plan.get("tier_groups", {}) or {}
    for tier_key, header_label in TIER_HEADERS:
        group = tier_groups.get(tier_key, {}) or {}
        stores = group.get("stores", []) or []
        parts.append(f"### {header_label} ({len(stores)} stores)")
        if stores:
            parts.append(f"_Stores: {', '.join(stores)}_")
        else:
            parts.append("_(0 stores)_")
        strategy = group.get("default_strategy", "")
        if strategy:
            parts.append(f"*{strategy}*")
        parts.append("")
        for a in group.get("auto_actions", []) or []:
            parts.append(f"- {a.get('action', '(unnamed action)')}")
            rationale = a.get("rationale")
            if rationale:
                parts.append(f"  - _why:_ {rationale}")
        for f in group.get("finding_actions", []) or []:
            line = _format_finding(f)
            parts.append(f"- {line}")
        parts.append("")

    # Portfolio actions
    portfolio = action_plan.get("portfolio_actions", []) or []
    parts.append("### 🌐 Portfolio")
    if portfolio:
        for a in portfolio:
            parts.append(f"- {a.get('action') or a.get('pattern_id') or '(unnamed)'}")
    else:
        parts.append("_(no portfolio-wide actions)_")
    parts.append("")

    # Tier Health
    parts.append("## Tier Health")
    parts.append("")
    donut_path = _chart_path(charts_dir, "tier_donut.png")
    parts.append(f"![Tier donut]({donut_path})")
    counts = _tier_counts(tier_rollup)
    parts.append(
        f"{counts['total']} stores: 🟢 {counts['green']} · 🟡 {counts['yellow']} · "
        f"🔴 {counts['red']} · 🆕 {counts['new']}."
    )
    parts.append("")
    parts.append("---")
    parts.append("")

    # ----- HALF 2: detail sections -----
    for short in SUB_SKILL_ORDER:
        label = SUB_SKILL_LABELS[short]
        parts.append(f"## {label} Detail")
        parts.append("")
        payload = payloads.get(short)
        if not payload:
            parts.append("_(data unavailable — sub-skill did not run)_")
            parts.append("")
            continue
        prose = (payload.get("drafted") or {}).get("toggle_prose", "")
        if prose:
            parts.append(prose)
            parts.append("")
        # Per-sub-skill chart images, if any emitted
        charts = (payload.get("computed") or {}).get("charts", []) or []
        for c in charts:
            cid = c.get("id", "chart")
            cpath = c.get("path", "")
            if cpath:
                resolved = _resolve_chart_path(charts_dir, cpath)
                parts.append(f"![{cid}]({resolved})")
        parts.append("")

    # ----- Data Quality footer -----
    parts.append("## Data Quality")
    parts.append("")
    footer_chunks: list[str] = []
    gap_lines: list[str] = []
    for short in SUB_SKILL_ORDER:
        payload = payloads.get(short)
        if not payload:
            continue
        dq = payload.get("data_quality") or {}
        comp = dq.get("completeness", 0.0) or 0.0
        label = SUB_SKILL_FOOTER_LABELS[short]
        footer_chunks.append(f"✓ {label} ({comp * 100:.0f}%)")
        for gap in dq.get("gaps", []) or []:
            gap_lines.append(f"- {label}: {gap}")
    parts.append(" · ".join(footer_chunks) if footer_chunks else "_(no sub-skill data)_")
    if gap_lines:
        parts.append("")
        parts.append("**Gaps:**")
        parts.extend(gap_lines)

    return "\n".join(parts).rstrip() + "\n"


def build_page_blocks(
    *,
    client: str,
    window: dict,
    payloads: dict[str, dict],
    radar: dict[str, float],
    tier_rollup: dict[str, dict],
    action_plan: dict,
    foundation_gate: dict,
    charts_dir: Path,
) -> list[dict]:
    """Return list of Notion block dicts (for MCP notion-create-pages).

    Wk 3 image blocks use file:// + absolute local path. Wk 4 will swap to
    proper Notion file uploads.
    """
    blocks: list[dict] = []

    start = window.get("start", "?")
    end = window.get("end", "?")

    blocks.append(_h1(f"{client} | Diagnostics & Action Plan | {start} – {end}"))

    if foundation_gate.get("triggered"):
        triggers_summary = _summarize_triggers(foundation_gate.get("triggers") or [])
        blocks.append(_callout(
            f"Foundation gate triggered. {triggers_summary}. All scaling on hold; foundation actions only.",
            emoji="⚠️",
        ))

    # Hero stat strip
    blocks.append(_h2("Hero Stat Strip"))
    hero = _hero_metrics(payloads)
    blocks.append(_paragraph(
        f"90-Day Gross Sales: {hero['gross']} · Orders: {hero['orders']} · "
        f"AOV: {hero['aov']} · Net Payout: {hero['payout']} ({hero['payout_pct']})"
    ))

    # Radar
    blocks.append(_h2("Brand Health Radar"))
    blocks.append(_image(_chart_path(charts_dir, "radar_7dim.png")))
    avg_score, dim1, dim2 = _radar_summary(radar)
    blocks.append(_paragraph(f"Overall {avg_score:.1f}/10. Weakest: {dim1}, {dim2}."))

    # WRO
    blocks.append(_h2("Win / Risk / Opportunity"))
    wro = _derive_wro(action_plan=action_plan, radar=radar, foundation_gate=foundation_gate)
    blocks.append(_paragraph(f"🏆 Win: {wro['win']}"))
    blocks.append(_paragraph(f"⚠️ Risk: {wro['risk']}"))
    blocks.append(_paragraph(f"💡 Opportunity: {wro['opportunity']}"))

    # Action Plan
    blocks.append(_h2("Action Plan"))
    tier_groups = action_plan.get("tier_groups", {}) or {}
    for tier_key, header_label in TIER_HEADERS:
        group = tier_groups.get(tier_key, {}) or {}
        stores = group.get("stores", []) or []
        blocks.append(_h3(f"{header_label} ({len(stores)} stores)"))
        strategy = group.get("default_strategy", "")
        if strategy:
            blocks.append(_paragraph(strategy))
        for a in group.get("auto_actions", []) or []:
            blocks.append(_bullet(a.get("action", "(unnamed action)")))
        for f in group.get("finding_actions", []) or []:
            blocks.append(_bullet(_format_finding(f)))
    portfolio = action_plan.get("portfolio_actions", []) or []
    blocks.append(_h3("🌐 Portfolio"))
    if portfolio:
        for a in portfolio:
            blocks.append(_bullet(a.get("action") or a.get("pattern_id") or "(unnamed)"))
    else:
        blocks.append(_paragraph("(no portfolio-wide actions)"))

    # Tier Health
    blocks.append(_h2("Tier Health"))
    blocks.append(_image(_chart_path(charts_dir, "tier_donut.png")))
    counts = _tier_counts(tier_rollup)
    blocks.append(_paragraph(
        f"{counts['total']} stores: 🟢 {counts['green']} · 🟡 {counts['yellow']} · "
        f"🔴 {counts['red']} · 🆕 {counts['new']}."
    ))

    blocks.append({"type": "divider", "divider": {}})

    # Half 2
    for short in SUB_SKILL_ORDER:
        label = SUB_SKILL_LABELS[short]
        blocks.append(_h2(f"{label} Detail"))
        payload = payloads.get(short)
        if not payload:
            blocks.append(_paragraph("(data unavailable — sub-skill did not run)"))
            continue
        prose = (payload.get("drafted") or {}).get("toggle_prose", "")
        if prose:
            blocks.append(_paragraph(prose))
        charts = (payload.get("computed") or {}).get("charts", []) or []
        for c in charts:
            cpath = c.get("path", "")
            if cpath:
                blocks.append(_image(_resolve_chart_path(charts_dir, cpath)))

    # Data Quality footer
    blocks.append(_h2("Data Quality"))
    footer_chunks: list[str] = []
    gap_lines: list[str] = []
    for short in SUB_SKILL_ORDER:
        payload = payloads.get(short)
        if not payload:
            continue
        dq = payload.get("data_quality") or {}
        comp = dq.get("completeness", 0.0) or 0.0
        label = SUB_SKILL_FOOTER_LABELS[short]
        footer_chunks.append(f"✓ {label} ({comp * 100:.0f}%)")
        for gap in dq.get("gaps", []) or []:
            gap_lines.append(f"{label}: {gap}")
    blocks.append(_paragraph(" · ".join(footer_chunks) if footer_chunks else "(no sub-skill data)"))
    for line in gap_lines:
        blocks.append(_bullet(line))

    return blocks


# ---------------------------------------------------------------------------
# Helpers — content derivation
# ---------------------------------------------------------------------------

def _summarize_triggers(triggers: list[dict]) -> str:
    if not triggers:
        return "Foundation thresholds breached"
    parts = []
    for t in triggers:
        metric = t.get("metric")
        if metric:
            val = t.get("value")
            thr = t.get("threshold")
            parts.append(f"{metric}={val} (threshold {thr})")
        else:
            reason = t.get("reason")
            if reason:
                parts.append(reason)
    return "; ".join(parts) if parts else "Foundation thresholds breached"


def _hero_metrics(payloads: dict[str, dict]) -> dict[str, str]:
    topline = payloads.get("topline") or {}
    metrics = (topline.get("computed") or {}).get("metrics") or {}
    gross = metrics.get("gross_sales")
    orders = metrics.get("orders")
    aov = metrics.get("aov")
    payout = metrics.get("net_payout")
    payout_pct = metrics.get("payout_pct")

    def fmt_dollars(v):
        if v is None:
            return "—"
        try:
            return f"${float(v):,.0f}"
        except (TypeError, ValueError):
            return "—"

    def fmt_int(v):
        if v is None:
            return "—"
        try:
            return f"{int(v):,}"
        except (TypeError, ValueError):
            return "—"

    def fmt_aov(v):
        if v is None:
            return "—"
        try:
            return f"${float(v):,.2f}"
        except (TypeError, ValueError):
            return "—"

    def fmt_pct(v):
        if v is None:
            return "—"
        try:
            return f"{float(v):.1f}%"
        except (TypeError, ValueError):
            return "—"

    return {
        "gross": fmt_dollars(gross),
        "orders": fmt_int(orders),
        "aov": fmt_aov(aov),
        "payout": fmt_dollars(payout),
        "payout_pct": fmt_pct(payout_pct),
    }


def _radar_summary(radar: dict[str, float]) -> tuple:
    if not radar:
        return (0.0, "—", "—")
    items = [(d, float(v)) for d, v in radar.items()]
    avg = sum(v for _, v in items) / len(items)
    items.sort(key=lambda x: x[1])  # ascending → weakest first
    dim1 = items[0][0] if len(items) >= 1 else "—"
    dim2 = items[1][0] if len(items) >= 2 else "—"
    return (avg, dim1, dim2)


def _tier_counts(tier_rollup: dict[str, dict]) -> dict:
    counts = {"green": 0, "yellow": 0, "red": 0, "new": 0}
    for entry in (tier_rollup or {}).values():
        flag = (entry or {}).get("flag")
        if flag in counts:
            counts[flag] += 1
    counts["total"] = sum(counts.values())
    return counts


def _derive_wro(*, action_plan: dict, radar: dict[str, float], foundation_gate: dict) -> dict:
    """Derive 1 win / 1 risk / 1 opportunity headline.

    Win → first green-tier auto-action (the scale instruction).
    Risk → highest-impact red finding_action; else first red auto-action;
           else first foundation trigger.
    Opportunity → weakest radar dim framed as a lift.
    """
    tier_groups = action_plan.get("tier_groups", {}) or {}

    # Win
    green = tier_groups.get("green", {}) or {}
    green_auto = green.get("auto_actions", []) or []
    if green_auto:
        win = green_auto[0].get("action") or "—"
    else:
        portfolio = action_plan.get("portfolio_actions", []) or []
        if portfolio:
            win = portfolio[0].get("action") or "—"
        else:
            win = "—"

    # Risk
    red = tier_groups.get("red", {}) or {}
    red_findings = red.get("finding_actions", []) or []
    risk = "—"
    if red_findings:
        # Already sorted by impact desc inside action plan — take first
        top = red_findings[0]
        impact = top.get("estimated_impact_usd")
        impact_str = f" (${impact:,.0f})" if isinstance(impact, (int, float)) else ""
        risk = f"{top.get('pattern_id', 'risk')} @ {top.get('scope', '')}{impact_str}"
    elif red.get("auto_actions"):
        risk = (red["auto_actions"][0] or {}).get("action") or "—"
    elif foundation_gate.get("triggered"):
        triggers = foundation_gate.get("triggers") or []
        if triggers:
            t = triggers[0]
            metric = t.get("metric")
            if metric:
                risk = f"{metric} below threshold ({t.get('value')} vs {t.get('threshold')})"
            else:
                risk = t.get("reason", "Foundation gate")

    # Opportunity (weakest radar dim)
    if radar:
        weakest = min(radar.items(), key=lambda kv: float(kv[1]))
        opp = f"Lift {weakest[0]} from {float(weakest[1]):.1f}/10"
    else:
        opp = "—"

    return {"win": win, "risk": risk, "opportunity": opp}


def _format_finding(f: dict) -> str:
    pid = f.get("pattern_id", "finding")
    scope = f.get("scope", "")
    impact = f.get("estimated_impact_usd")
    impact_str = f" — ${impact:,.0f}" if isinstance(impact, (int, float)) else ""
    sev = f.get("severity")
    sev_str = f" [{sev}]" if sev else ""
    suffix = " (deferred until foundation clear)" if f.get("deferred_until_foundation_clear") else ""
    return f"{pid} @ {scope}{impact_str}{sev_str}{suffix}"


# ---------------------------------------------------------------------------
# Helpers — chart paths
# ---------------------------------------------------------------------------

def _chart_path(charts_dir: Path, filename: str) -> str:
    """Resolve absolute path for a cross-cutting chart (e.g. radar_7dim.png)."""
    return str((Path(charts_dir) / filename).resolve())


def _resolve_chart_path(charts_dir: Path, raw_path: str) -> str:
    """Resolve a sub-skill chart path.

    Sub-skill payloads may emit either:
      - absolute path
      - relative path rooted at the run-dir (e.g. "menu/charts/funnel_ue.png")

    `charts_dir` is the cross_cutting dir; its parent is the run root.
    """
    p = Path(raw_path)
    if p.is_absolute():
        return str(p)
    run_root = Path(charts_dir).parent
    return str((run_root / p).resolve())


# ---------------------------------------------------------------------------
# Helpers — block constructors
# ---------------------------------------------------------------------------

def _rt(text: str) -> list[dict]:
    return [{"type": "text", "text": {"content": text}}]


def _h1(text: str) -> dict:
    return {"type": "heading_1", "heading_1": {"rich_text": _rt(text)}}


def _h2(text: str) -> dict:
    return {"type": "heading_2", "heading_2": {"rich_text": _rt(text)}}


def _h3(text: str) -> dict:
    return {"type": "heading_3", "heading_3": {"rich_text": _rt(text)}}


def _paragraph(text: str) -> dict:
    return {"type": "paragraph", "paragraph": {"rich_text": _rt(text)}}


def _callout(text: str, *, emoji: str = "⚠️") -> dict:
    return {
        "type": "callout",
        "callout": {
            "rich_text": _rt(text),
            "icon": {"type": "emoji", "emoji": emoji},
        },
    }


def _bullet(text: str) -> dict:
    return {
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": _rt(text)},
    }


def _image(path: str) -> dict:
    # Wk 3: file:// URL pointing at local PNG. Wk 4 swaps to Notion upload.
    url = path if path.startswith("file://") else f"file://{path}"
    return {"type": "image", "image": {"type": "external", "external": {"url": url}}}
