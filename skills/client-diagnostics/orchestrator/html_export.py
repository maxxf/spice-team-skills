from __future__ import annotations

"""Phase 5 (export): styled, self-contained HTML from the same orchestrator state.

This is the convergence path: the bespoke per-client report
(Desktop/.../dailys_diagnostic/build_report.py) and the Notion page both come
from one orchestrator pass. `build_html` consumes the identical Phase-5 inputs
as `notion_assembly.build_page_blocks` and reuses its content-derivation
helpers, so the dashboard/toggle structure can never drift between the PDF and
the Notion render.

Output is one HTML string with every chart inlined as base64 — portable,
emailable, and the print source for a headless-Chrome PDF (see SKILL.md).
"""

import base64
from pathlib import Path

from orchestrator import notion_assembly as na

SPICE = {
    "orange": "#FF4A1C", "red": "#B91C1C", "yellow": "#F59E0B",
    "green": "#84CC16", "blue": "#2563EB", "charcoal": "#1F2937",
    "cream": "#FEF3C7", "gray": "#6B7280", "ink200": "#E5E7EB", "bg": "#F9FAFB",
}

_CSS = f"""
*{{box-sizing:border-box}}
body{{margin:0;background:{SPICE['bg']};color:{SPICE['charcoal']};
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
line-height:1.6;font-size:15px}}
.doc{{max-width:880px;margin:32px auto;background:#fff;padding:48px 56px;
box-shadow:0 1px 4px rgba(0,0,0,.06);border-radius:10px}}
.brand{{display:flex;align-items:center;gap:16px;margin-bottom:10px}}
.brand img{{border-radius:9px;display:block;flex:none}}
.meta{{text-transform:uppercase;letter-spacing:.08em;font-size:12px;
color:{SPICE['gray']};font-weight:600}}
h1{{font-size:30px;font-weight:700;letter-spacing:-.02em;margin:.2em 0 .1em}}
h2{{font-size:21px;font-weight:600;margin:34px 0 14px;
border-bottom:1px solid {SPICE['ink200']};padding-bottom:6px}}
h3{{font-size:15px;font-weight:700;margin:18px 0 8px;color:{SPICE['charcoal']}}}
.subhead{{color:{SPICE['gray']};font-size:14px;margin-bottom:20px}}
.alert{{background:#FEF2F2;border-left:4px solid {SPICE['red']};
border-radius:6px;padding:16px 20px;margin:18px 0}}
.hero{{display:flex;flex-wrap:wrap;gap:12px;margin:14px 0 26px}}
.stat{{flex:1 1 200px;min-width:190px;border:1px solid {SPICE['ink200']};
border-radius:8px;padding:16px 18px}}
.stat .lbl{{text-transform:uppercase;font-size:11px;letter-spacing:.06em;
color:{SPICE['gray']};font-weight:600}}
.stat .val{{font-size:24px;font-weight:700;margin:4px 0 2px}}
.cards{{display:flex;flex-wrap:wrap;gap:12px;margin:6px 0 22px}}
.card{{flex:1 1 210px;border:1px solid {SPICE['ink200']};
border-left-width:4px;border-radius:8px;padding:14px 16px;font-size:14px}}
.card b{{display:block;text-transform:uppercase;font-size:11px;
letter-spacing:.06em;margin-bottom:5px}}
.kanban{{display:flex;gap:14px;flex-wrap:wrap;margin:10px 0 8px}}
.col{{flex:1 1 240px;border:1px solid {SPICE['ink200']};border-radius:8px;
padding:14px 16px;background:{SPICE['bg']}}}
.col h3{{margin-top:0}}
.col ul{{margin:0;padding-left:18px}}.col li{{margin:5px 0;font-size:13px}}
img.chart{{width:100%;height:auto;border:1px solid {SPICE['ink200']};
border-radius:8px;margin:8px 0}}
.cap{{font-size:13px;color:{SPICE['gray']};margin:6px 0 2px}}
details{{border:1px solid {SPICE['ink200']};border-radius:8px;
padding:4px 18px;margin:10px 0;background:#fff}}
summary{{font-weight:600;cursor:pointer;padding:10px 0}}
.foot{{margin-top:36px;padding-top:16px;border-top:1px solid {SPICE['ink200']};
color:{SPICE['gray']};font-size:12px;display:flex;align-items:center;gap:10px}}
@media print{{body{{background:#fff}}.doc{{box-shadow:none;margin:0;
max-width:100%;border-radius:0}}
.stat,.card,.col,img,details,.alert{{break-inside:avoid}}
h1,h2,h3{{break-after:avoid}}}}
"""


def _b64_img(path: Path, cls: str = "chart", alt: str = "") -> str:
    if not path or not Path(path).exists():
        return ""
    b = base64.b64encode(Path(path).read_bytes()).decode()
    return f'<img class="{cls}" alt="{alt}" src="data:image/png;base64,{b}">'


def _logo(px: int) -> str:
    """Spice mark — prefer the brand SVG, else skip silently."""
    for p in (
        Path("/Users/maxx/Desktop/Cowork/Brand/Spice-Logos/spice_icon_cream_on_orange.svg"),
        Path(__file__).parent.parent / "assets" / "spice_icon.svg",
    ):
        if p.exists():
            b = base64.b64encode(p.read_bytes()).decode()
            return (f'<img src="data:image/svg+xml;base64,{b}" width="{px}" '
                    f'height="{px}" alt="Spice">')
    return ""


def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def build_html(
    *,
    client: str,
    window: dict,
    payloads: dict,
    radar: dict,
    tier_rollup: dict,
    action_plan: dict,
    foundation_gate: dict,
    charts_dir: Path,
) -> str:
    """Return a self-contained styled HTML string for this diagnostic."""
    charts_dir = Path(charts_dir)
    start, end = window.get("start", "?"), window.get("end", "?")
    H: list[str] = []
    H.append(f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">')
    H.append(f"<title>{_esc(client)} — Diagnostics & Action Plan</title>")
    H.append(f"<style>{_CSS}</style></head><body><div class='doc'>")

    # Masthead
    logo = _logo(50)
    H.append("<div class='brand'>")
    if logo:
        H.append(logo)
    H.append("<div class='meta'>Spice Diagnostic · 90-Day Rolling Report · "
             f"{_esc(client)}</div></div>")
    H.append(f"<h1>{_esc(client)} — Diagnostics &amp; Action Plan</h1>")
    H.append(f"<div class='subhead'><b>Window:</b> {start} – {end}</div>")

    # Executive summary — foundation status folded into one top block
    es = na.build_exec_summary(
        payloads=payloads, radar=radar, tier_rollup=tier_rollup,
        action_plan=action_plan, foundation_gate=foundation_gate)
    H.append("<h2>Executive Summary</h2>")
    accent = SPICE["red"] if es["gated"] else SPICE["green"]
    bg = "#FEF2F2" if es["gated"] else "#F7FCEC"
    H.append(
        f"<div class='card' style='border-left-color:{accent};"
        f"background:{bg};flex:1 1 100%'>"
        f"<div style='font-weight:700;margin-bottom:8px'>{_esc(es['headline'])}</div>"
        "<ul style='margin:0;padding-left:18px'>"
        + "".join(f"<li style='margin:5px 0'>{_esc(b)}</li>"
                  for b in es["bullets"])
        + "</ul></div>"
    )

    # Hero
    hero = na._hero_metrics(payloads)
    H.append("<h2>The 60-second view</h2><div class='hero'>")
    for lbl, val in (("90-Day Gross", hero["gross"]), ("Orders", hero["orders"]),
                     ("Blended AOV", hero["aov"]),
                     (f"Net Payout ({hero['payout_pct']})", hero["payout"])):
        H.append(f"<div class='stat'><div class='lbl'>{_esc(lbl)}</div>"
                 f"<div class='val'>{_esc(val)}</div></div>")
    H.append("</div>")

    # Radar
    avg, d1, d2 = na._radar_summary(radar)
    H.append("<h2>Brand Health Radar</h2>")
    H.append(_b64_img(charts_dir / "radar_7dim.png", alt="radar"))
    H.append(f"<div class='cap'>Overall {avg:.1f}/10. Weakest: {_esc(d1)}, "
             f"{_esc(d2)}.</div>")
    for cand in ("trend_overlay.png", "sparklines_gmv_orders.png"):
        cp = charts_dir / cand
        if cp.exists():
            H.append(_b64_img(cp, alt="trend"))
            break

    # Win / Risk / Opportunity / Decision
    wro = na._derive_wro(action_plan=action_plan, radar=radar,
                         foundation_gate=foundation_gate)
    H.append("<h2>Win / Risk / Opportunity / Decision</h2><div class='cards'>")
    for tag, key, col in (("🏆 Win", "win", SPICE["green"]),
                          ("⚠️ Risk", "risk", SPICE["red"]),
                          ("💡 Opportunity", "opportunity", SPICE["yellow"]),
                          ("🧭 Decision", "decision", SPICE["blue"])):
        H.append(f"<div class='card' style='border-left-color:{col}'>"
                 f"<b>{tag}</b>{_esc(wro[key])}</div>")
    H.append("</div>")

    # Action plan kanban
    H.append("<h2>Action Plan</h2><div class='kanban'>")
    for col_label, items in na._derive_kanban(action_plan=action_plan,
                                              foundation_gate=foundation_gate):
        H.append(f"<div class='col'><h3>{_esc(col_label)}</h3><ul>")
        H.append("".join(f"<li>{_esc(i)}</li>" for i in items)
                 or "<li><i>nothing queued</i></li>")
        H.append("</ul></div>")
    H.append("</div>")

    # Tier health
    H.append("<h2>Tier Health</h2>")
    H.append(_b64_img(charts_dir / "tier_donut.png", alt="tiers"))
    c = na._tier_counts(tier_rollup)
    H.append(f"<div class='cap'>{c['total']} stores: 🟢 {c['green']} · "
             f"🟡 {c['yellow']} · 🔴 {c['red']} · 🆕 {c['new']}.</div>")

    # Half 2 — detail toggles
    for short in na.SUB_SKILL_ORDER:
        label = na.SUB_SKILL_LABELS[short]
        p = payloads.get(short)
        H.append(f"<details><summary>{_esc(label)} Detail</summary>")
        if not p:
            H.append("<p><i>data unavailable — sub-skill did not run</i></p>")
        else:
            prose = (p.get("drafted") or {}).get("toggle_prose", "")
            if prose:
                H.append(f"<p>{_esc(prose)}</p>")
            for ch in (p.get("computed") or {}).get("charts", []) or []:
                cp = ch.get("path", "")
                if cp:
                    rp = na._resolve_chart_path(charts_dir, cp)
                    H.append(_b64_img(Path(rp), alt=ch.get("id", "chart")))
        H.append("</details>")

    # Action plan detail toggle
    H.append("<details><summary>Action Plan Detail (by tier)</summary>")
    tg = action_plan.get("tier_groups", {}) or {}
    for tk, hl in na.TIER_HEADERS:
        g = tg.get(tk, {}) or {}
        H.append(f"<h3>{_esc(hl)} ({len(g.get('stores', []) or [])} stores)</h3>")
        strat = g.get("default_strategy", "")
        if strat:
            H.append(f"<p class='cap'>{_esc(strat)}</p><ul>")
        else:
            H.append("<ul>")
        for a in g.get("auto_actions", []) or []:
            H.append(f"<li>{_esc(a.get('action', '(unnamed)'))}</li>")
        for f in g.get("finding_actions", []) or []:
            H.append(f"<li>{_esc(na._format_finding(f))}</li>")
        H.append("</ul>")
    H.append("</details>")

    H.append("<div class='foot'>")
    if logo:
        H.append(_logo(22))
    H.append(f"<span>Prepared by <b>Spice Digital</b> · {end} · "
             f"Generated from the client-diagnostics orchestrator</span></div>")
    H.append("</div></body></html>")
    return "".join(H)
