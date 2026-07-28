from __future__ import annotations

"""Orchestrator main entry. Phase 1-5 controller.

Wk 2: dispatches all 4 domain sub-skills in parallel (topline + menu + ops +
campaigns), assembles cross-cutting outputs (radar, tier rollup, win/risk/opp,
foundation gate), and runs the action-plan stub with the full integrated
findings list.
"""
import json
import os
import pathlib
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from orchestrator import chart_helpers, contract, cross_cutting, output_layout, run_state

# The diagnostic-* sub-skills live beside client-diagnostics in the same skills
# directory. Resolve relative to this file so the orchestrator works from any
# install location (plugin cache, Cowork mirror, canonical repo) rather than a
# single hard-coded path. entry.py -> orchestrator/ -> client-diagnostics/ ->
# skills/ (parents[2]).
SKILLS_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RunResult:
    layout: output_layout.RunLayout
    state: dict


def run(
    *,
    client: str,
    window_start: str,
    window_end: str,
    inputs_dir: Path,
    when: datetime | None = None,
    publish_to_notion: bool = False,
) -> RunResult:
    when = when or datetime.now()

    # Phase 1 pre-flight: validate diagnostic input CSV(s) before doing any work
    import pandas as pd
    from orchestrator import input_schema

    csvs = sorted(inputs_dir.glob("*.csv"))
    if not csvs:
        raise SystemExit(f"No CSV files found in {inputs_dir}. Drop the diagnostic input CSV here.")
    df = pd.concat([pd.read_csv(c) for c in csvs], ignore_index=True)
    input_schema.validate(df)  # raises InputSchemaError with actionable message

    layout = output_layout.create_run_dirs(client, when)
    run_id = f"{client}-{when.strftime('%Y-%m-%dT%H:%M:%S')}"
    state = run_state.init(run_id, layout.run_state_path)

    # Phase 2: parallel dispatch of all 4 domain sub-skills
    state = run_state.update(layout.run_state_path, phase=2)
    sub_skills = [
        ("topline", _dispatch_topline),
        ("menu", _dispatch_menu),
        ("ops", _dispatch_ops),
        ("campaigns", _dispatch_campaigns),
    ]
    statuses: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {
            ex.submit(
                fn,
                client=client,
                window_start=window_start,
                window_end=window_end,
                inputs_dir=inputs_dir,
                output_path=layout.sub_skill_results_path(short),
                charts_dir=layout.root / short / "charts",
            ): short
            for short, fn in sub_skills
        }
        for fut in futures:
            short = futures[fut]
            try:
                fut.result()
                statuses[f"diagnostic-{short}"] = "ok"
            except Exception as exc:
                # Do NOT swallow. A section we cannot produce must not be
                # zero-filled and shipped as if complete.
                statuses[f"diagnostic-{short}"] = "failed"
                raise SubSkillDispatchError(
                    f"diagnostic-{short} could not be dispatched, so the "
                    f"{short} section would be incomplete: {exc}"
                ) from exc
    state = run_state.update(layout.run_state_path, sub_skill_status=statuses)

    # Phase 3: cross-cutting assembly
    state = run_state.update(layout.run_state_path, phase=3)
    payloads = _load_payloads(layout, statuses)
    for p in payloads.values():
        contract.validate(p)
    radar = cross_cutting.assemble_radar(
        payloads,
        topline_metrics=payloads.get("topline", {}).get("computed", {}).get("metrics", {}),
        campaigns_metrics=payloads.get("campaigns", {}).get("computed", {}).get("metrics", {}),
    )
    tier_rollup = cross_cutting.rollup_tiers({
        "menu": payloads.get("menu", {}).get("computed", {}).get("tier_contributions", {}),
        "ops": payloads.get("ops", {}).get("computed", {}).get("tier_contributions", {}),
        "campaigns": payloads.get("campaigns", {}).get("computed", {}).get("tier_contributions", {}),
    })
    foundation_gate = cross_cutting.compute_foundation_gate(payloads, statuses)
    wro = cross_cutting.select_win_risk_opp(payloads)
    state = run_state.update(layout.run_state_path, foundation_gate=foundation_gate)

    # Persist cross-cutting outputs
    (layout.root / "cross_cutting" / "radar.json").write_text(json.dumps(radar, indent=2, sort_keys=True))
    (layout.root / "cross_cutting" / "tier_rollup.json").write_text(json.dumps(tier_rollup, indent=2, sort_keys=True))
    (layout.root / "cross_cutting" / "win_risk_opp.json").write_text(json.dumps(wro, indent=2, sort_keys=True))

    # Cross-cutting charts (Wk 3): radar_7dim, tier_donut, top15_green_bar
    cc_dir = layout.root / "cross_cutting"
    try:
        chart_helpers.radar_7dim(
            {"radar": {dim: {"current": v, "target": 8} for dim, v in radar.items()}},
            cc_dir,
        )
    except Exception:
        pass
    try:
        chart_helpers.tier_donut({"tiers": _tier_counts(tier_rollup)}, cc_dir)
    except Exception:
        pass
    try:
        top_green = _build_top_green(tier_rollup)
        if top_green:
            chart_helpers.top15_green_bar({"top_green": top_green, "top15_green": top_green}, cc_dir)
    except Exception:
        pass

    # Phase 4: action plan with all findings from all sub-skills
    state = run_state.update(layout.run_state_path, phase=4)
    findings: list[dict] = []
    for p in payloads.values():
        findings.extend(p["computed"]["findings"])
    ap_output_path = layout.root / "action-plan" / "diagnostic-action-plan_results.json"
    _dispatch_action_plan(
        findings,
        foundation_triggered=foundation_gate["triggered"],
        tier_rollup=tier_rollup,
        output_path=ap_output_path,
    )

    # Phase 5: Notion page assembly
    state = run_state.update(layout.run_state_path, phase=5)
    from orchestrator import notion_assembly

    # Read action_plan back from disk (it was written in Phase 4)
    action_plan = json.loads(ap_output_path.read_text())

    charts_dir = layout.root / "cross_cutting"

    md = notion_assembly.build_page_markdown(
        client=client,
        window={"start": window_start, "end": window_end},
        payloads=payloads,
        radar=radar,
        tier_rollup=tier_rollup,
        action_plan=action_plan,
        foundation_gate=foundation_gate,
        charts_dir=charts_dir,
    )
    (layout.root / "notion_page.md").write_text(md)

    blocks = notion_assembly.build_page_blocks(
        client=client,
        window={"start": window_start, "end": window_end},
        payloads=payloads,
        radar=radar,
        tier_rollup=tier_rollup,
        action_plan=action_plan,
        foundation_gate=foundation_gate,
        charts_dir=charts_dir,
    )
    (layout.root / "notion_blocks.json").write_text(json.dumps(blocks, indent=2, sort_keys=True))

    # Optional: Wk 4 Chunk 3 publish helper artifacts.
    # Writes filtered (text-only) blocks + charts manifest so the calling Claude
    # session can invoke notion-create-pages with the payload. Actual MCP call
    # happens in scripts/run_diagnostic.py (Chunk 4); orchestrator stays MCP-free.
    if publish_to_notion:
        from orchestrator import notion_publisher

        filtered, manifest = notion_publisher.filter_image_blocks(blocks)
        (layout.root / "publish_blocks.json").write_text(json.dumps(filtered, indent=2))
        (layout.root / "charts_manifest.json").write_text(json.dumps(manifest, indent=2))

    return RunResult(layout=layout, state=state)


def _load_payloads(layout: output_layout.RunLayout, statuses: dict[str, str]) -> dict[str, dict]:
    """Load each successful sub-skill's results JSON. Skip failed sub-skills (fail-open per spec)."""
    payloads: dict[str, dict] = {}
    for short in ("topline", "menu", "ops", "campaigns"):
        if statuses.get(f"diagnostic-{short}") == "ok":
            payloads[short] = json.loads(layout.sub_skill_results_path(short).read_text())
    return payloads


def _dispatch_topline(*, client, window_start, window_end, inputs_dir, output_path, charts_dir=None):
    # Wk 3: topline does not yet accept --charts-dir (defers sparklines to Wk 4).
    _dispatch_sub_skill("topline", client=client, window_start=window_start, window_end=window_end,
                        inputs_dir=inputs_dir, output_path=output_path, charts_dir=None)


def _dispatch_menu(*, client, window_start, window_end, inputs_dir, output_path, charts_dir=None):
    # Wk 3: menu does not yet accept --charts-dir (defers funnel/SKU charts to Wk 4).
    _dispatch_sub_skill("menu", client=client, window_start=window_start, window_end=window_end,
                        inputs_dir=inputs_dir, output_path=output_path, charts_dir=None)


def _dispatch_ops(*, client, window_start, window_end, inputs_dir, output_path, charts_dir=None):
    # Wk 3: ops does not yet accept --charts-dir (defers daypart heatmap to Wk 4).
    _dispatch_sub_skill("ops", client=client, window_start=window_start, window_end=window_end,
                        inputs_dir=inputs_dir, output_path=output_path, charts_dir=None)


def _dispatch_campaigns(*, client, window_start, window_end, inputs_dir, output_path, charts_dir=None):
    _dispatch_sub_skill("campaigns", client=client, window_start=window_start, window_end=window_end,
                        inputs_dir=inputs_dir, output_path=output_path, charts_dir=charts_dir)


class SubSkillDispatchError(RuntimeError):
    """A diagnostic sub-skill could not be dispatched at all.

    Raised instead of marking the sub-skill "failed" and continuing. Guards the
    INDAY-2026-07-23 failure mode: a dispatch that could not even start (missing
    interpreter, crashed subprocess) was swallowed, the affected section was then
    zero-filled by the assembler, and a blank diagnostic shipped looking complete.
    A run that cannot produce a section must fail loudly and name that section.
    """


def _resolve_sub_skill_python(short: str) -> pathlib.Path:
    """Return an interpreter that actually exists for ``diagnostic-<short>``.

    Prefers the sub-skill's own venv; falls back to the interpreter running the
    orchestrator (the client-diagnostics venv carries pandas/matplotlib and the
    sub-skill packages import cleanly on the shared PYTHONPATH). Never returns a
    non-existent hardcoded path.
    """
    sub_venv_python = SKILLS_ROOT / f"diagnostic-{short}" / ".venv" / "bin" / "python"
    if sub_venv_python.exists() and os.access(sub_venv_python, os.X_OK):
        return sub_venv_python
    return pathlib.Path(sys.executable)


def _dispatch_sub_skill(short: str, *, client, window_start, window_end, inputs_dir, output_path, charts_dir=None):
    skill_dir = SKILLS_ROOT / f"diagnostic-{short}"
    # Prefer the sub-skill's own venv if it has one; otherwise fall back to the
    # interpreter currently running the orchestrator (the client-diagnostics
    # venv carries pandas/matplotlib, and the sub-skill packages import cleanly
    # on the shared PYTHONPATH). This keeps the orchestrator runnable whether or
    # not each sub-skill was independently bootstrapped with its own venv.
    python_exe = str(_resolve_sub_skill_python(short))
    cmd = [
        python_exe,
        "-m", f"diagnostic_{short}.entry",
        "--client", client,
        "--window-start", window_start,
        "--window-end", window_end,
        "--inputs-dir", str(inputs_dir),
        "--output-path", str(output_path),
    ]
    if charts_dir is not None:
        cmd += ["--charts-dir", str(charts_dir)]
    # Put the sub-skill dir first so `diagnostic_{short}` resolves, and keep the
    # client-diagnostics root on the path so sub-skills can import chart_helpers.
    pythonpath = os.pathsep.join([str(skill_dir), str(SKILLS_ROOT / "client-diagnostics")])
    env = {**os.environ, "PYTHONPATH": pythonpath}
    subprocess.run(cmd, check=True, env=env)


def _tier_counts(tier_rollup: dict) -> dict:
    """Count stores per tier flag for the donut chart."""
    counts = {"Green": 0, "Yellow": 0, "Red": 0, "New": 0}
    flag_to_label = {"green": "Green", "yellow": "Yellow", "red": "Red", "new": "New"}
    for entry in (tier_rollup or {}).values():
        flag = (entry or {}).get("flag")
        label = flag_to_label.get(flag)
        if label:
            counts[label] += 1
    return counts


def _build_top_green(tier_rollup: dict) -> list[dict]:
    """Build top_green list for the green-bar chart.

    Wk 3 uses a uniform placeholder payout — Wk 4 plumbs real per-store payout
    from topline tier_contributions or sub-skill metrics.
    """
    green_stores = sorted(
        store for store, entry in (tier_rollup or {}).items()
        if (entry or {}).get("flag") == "green"
    )
    placeholder_payout = 1000.0
    return [{"name": s, "payout": placeholder_payout, "tier": "Green"} for s in green_stores]


def _dispatch_action_plan(
    findings,
    *,
    foundation_triggered: bool,
    tier_rollup: dict | None = None,
    output_path: Path,
):
    # Wk 1: in-process. Wk 2-3 swaps to subprocess once fully promoted.
    skill_dir = SKILLS_ROOT / "diagnostic-action-plan"
    if str(skill_dir) not in sys.path:
        sys.path.insert(0, str(skill_dir))
    from diagnostic_action_plan.entry import build_plan
    plan = build_plan(findings, foundation_triggered=foundation_triggered, tier_rollup=tier_rollup)
    output_path.write_text(json.dumps(plan, indent=2, sort_keys=True))
