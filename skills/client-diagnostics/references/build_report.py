"""Canonical client-diagnostics HTML report builder.

This is the SINGLE source of truth for the client-facing diagnostic report.
It is fully DATA-DRIVEN: every number and every line of narrative is read
from ``findings.json`` + ``metrics.json`` in the run directory. There are
ZERO per-client literals in this file. If you find yourself wanting to
hand-edit the generated HTML or hardcode a client name / dollar figure here,
that is a bug — put the value in findings.json instead and extend the
contract (see ``references/report-data-contract.md``).

Rules that must not regress:
- Deterministic build only — NEVER regex-patch a generated report.
- Single-column layout, max-width 1040px. No multi-column CSS grids.
- Styling comes from the colocated report_style.css (Spice Design System).
- Every <img> obeys max-width:100% so embedded charts never clip in PDF.
- Charts base64-inlined for portability (self-contained HTML).
- Section banners: "Overview" + "Detailed Findings" (client-facing).
- Canonical 6-slot hero, /10 radar, required Half-2 toggle set including
  "Menu & Storefront". See report-data-contract.md.

Usage:
    python build_report.py [RUN_DIR]

RUN_DIR defaults to the directory containing this script. It must contain
findings.json, metrics.json, report_style.css and a charts/ subdir (charts
optional — missing charts render a visible placeholder, never silently).
"""
from __future__ import annotations

import base64
import html
import json
import pathlib
import sys

# --- Canonical structural constants (asserted by tests/test_report_conformance.py)

HERO_SLOTS = [
    "90-Day Gross",
    "Orders",
    "Blended AOV",
    "Net Payout",
    "Order Completion",
    "Customer Sentiment",
]

# Half-2 toggle set. Omission of any of these is a conformance failure.
REQUIRED_TOGGLES = [
    "Portfolio Snapshot",
    "Menu & Storefront",
    "Ops",
    "Brand Operational Health",
    "Campaigns",
    "Location Tiers",
    "Full Action Plan",
    "Appendix",
]

_TIER_EMOJI = {"Red": "🔴", "Yellow": "🟡", "Green": "🟢", "New": "🆕"}
_NA = 'n/a<span class="na-fn">*</span>'


def _esc(v) -> str:
    return html.escape(str(v), quote=False)


# --------------------------------------------------------------------------- #
# Run-dir IO helpers (no module-level path constants so the builder is         #
# importable + testable against an arbitrary fixture directory).               #
# --------------------------------------------------------------------------- #

def _load(run_dir: pathlib.Path):
    fj = json.loads((run_dir / "findings.json").read_text())
    mj = json.loads((run_dir / "metrics.json").read_text())
    return fj, mj


def img(run_dir: pathlib.Path, name: str) -> str:
    p = run_dir / "charts" / name
    if not p.exists():
        return f'<div class="missing">[chart pending: {_esc(name)}]</div>'
    b64 = base64.b64encode(p.read_bytes()).decode()
    return f'<img src="data:image/png;base64,{b64}" alt="{_esc(name)}">'


def spice_logo(run_dir: pathlib.Path, px: int) -> str:
    p = run_dir / "assets" / "spice_icon.svg"
    if not p.exists():
        return ""
    b64 = base64.b64encode(p.read_bytes()).decode()
    return (f'<img src="data:image/svg+xml;base64,{b64}" alt="Spice" '
            f'width="{px}" height="{px}" '
            f'style="border-radius:{max(6, px // 6)}px;display:block;flex:none">')


def stat(lbl: str, val: str, sub: str, alert: bool = False) -> str:
    cls = "stat alert-stat" if alert else "stat"
    return (f'<div class="{cls}"><div class="lbl">{_esc(lbl)}</div>'
            f'<div class="val">{val}</div><div class="sub">{sub}</div></div>')


def ai(title: str, meta: str, pri: str = "") -> str:
    return (f'<div class="ai {pri}"><div class="t">{title}</div>'
            f'<div class="m">{meta}</div></div>')


def _fmt(v, kind: str = "raw") -> str:
    """Render a contract value, with explicit n/a* for None/'n/a'."""
    if v is None or (isinstance(v, str) and v.strip().lower() in ("n/a", "na", "")):
        return _NA
    if kind == "money" and isinstance(v, (int, float)):
        return f"${v:,.0f}"
    if kind == "money2" and isinstance(v, (int, float)):
        return f"${v:,.2f}"
    if kind == "int" and isinstance(v, (int, float)):
        return f"{int(v):,}"
    return _esc(v)


# --------------------------------------------------------------------------- #
# Sections — every one reads from findings.json. No client literals.           #
# --------------------------------------------------------------------------- #

def hero_strip(fj: dict) -> str:
    """The canonical 6-slot hero. Slots are fixed and ordered; a slot whose
    value is missing renders n/a* with a footnote — never dropped, never
    substituted."""
    h = fj.get("hero", {})
    slots = h.get("slots", {})
    cards = []
    for label in HERO_SLOTS:
        s = slots.get(label, {})
        val = s.get("value")
        sub = s.get("sub", "")
        alert = bool(s.get("alert", False))
        cards.append(stat(label, _fmt(val), _esc(sub), alert))
    footnote = h.get("na_footnote")
    fn = (f'<p class="hero-fn">* {_esc(footnote)}</p>' if footnote else "")
    return f'<div class="hero">{"".join(cards)}</div>{fn}'


def exec_summary(fj: dict) -> str:
    """Status headline + bullets, all from findings.json. The gate state and
    every bullet string is supplied by the data contract."""
    es = fj.get("exec_summary", {})
    g = fj.get("foundation_gate", {})
    gated = bool(g.get("triggered", False))
    headline = es.get("headline") or (
        "🛑 Foundation gate triggered." if gated
        else "✅ Foundation clear.")
    if gated:
        accent, bg = "var(--err, #991b1b)", "#fdf0ef"
    else:
        accent, bg = "var(--ok, #14532d)", "#f0f7f1"
    accent = es.get("accent", accent)
    bg = es.get("bg", bg)
    bullets = es.get("bullets", [])
    lis = "".join(f"<li style='margin:6px 0'>{b}</li>" for b in bullets)
    return (
        f'<div class="wro" style="border-left-color:{accent};background:{bg}">'
        f'<div style="font-weight:700;margin-bottom:10px;font-size:15px">'
        f'{headline}</div>'
        f'<ul style="margin:0;padding-left:20px;line-height:1.7">{lis}</ul>'
        f'</div>'
    )


def radar_block(run_dir: pathlib.Path, fj: dict, mj: dict) -> str:
    overall = fj.get("radar_overall", mj.get("radar_overall", 0))
    weakest = fj.get("radar_weakest", [])
    pills = "".join(
        f'<span class="pill">Weakest: {_esc(w[0])} {w[1].get("current")}</span>'
        if i == 0 else f'<span class="pill">{_esc(w[0])} {w[1].get("current")}</span>'
        for i, w in enumerate(weakest[:2])
    )
    notes = fj.get("radar_notes", [])
    note_lis = "".join(f"<li>{n}</li>" for n in notes)
    return (
        f'<h2>Brand Health Radar — Overall {overall} / 10</h2>'
        f'<div class="radar-wrap">{img(run_dir, "radar_7dim.png")}</div>'
        f'<div class="cap"><div style="margin-bottom:8px">{pills}</div>'
        f'<ul style="margin:0;padding-left:20px;line-height:1.7">{note_lis}</ul>'
        f'</div>'
    )


def fro_block(fj: dict) -> str:
    """Foothold · Risk · Opportunity — all cards from findings.json."""
    fro = fj.get("fro", {})
    out = ['<h2>Foothold · Risk · Opportunity</h2>']
    spec = [("foothold", "wro-f", "🟢 Foothold"),
            ("risk", "wro-r", "🔴 Risk"),
            ("opportunity", "wro-o", "🟡 Opportunity")]
    for key, cls, tag in spec:
        c = fro.get(key)
        if not c:
            continue
        fig = f'<div class="fig">{c["fig"]}</div>' if c.get("fig") else ""
        out.append(
            f'<div class="wro {cls}"><div class="tag">{tag}</div>'
            f'{c.get("body", "")}{fig}{c.get("action", "")}</div>'
        )
    return "".join(out)


def levers_block(fj: dict) -> str:
    """The Levers — the client-facing distillation of the opportunity.

    Optional block (rendered only when ``findings.levers.items`` is present).
    Names the top 2–4 levers that move the number, each as
    current → target · mechanism · expected impact. This is the actionable
    counterpart to the Foothold/Risk/Opportunity cards and maps onto the
    weakest actionable radar axes (Traffic/CTR, AOV, Marketing Efficiency).

    Item shape: ``{n?, name, current?, target?, unit?, mechanism?, impact?}``.
    Prose fields are HTML the builder emits verbatim (contract convention);
    the numeric badge and section title are escaped.
    """
    lv = fj.get("levers") or {}
    items = lv.get("items", [])
    if not items:
        return ""
    title = lv.get("title", "The Levers — where the number moves")
    intro = f'<div class="cap">{lv["intro"]}</div>' if lv.get("intro") else ""
    cards = []
    for i, it in enumerate(items):
        n = it.get("n", i + 1)
        cur, tgt = it.get("current"), it.get("target")
        mv = ""
        if cur is not None or tgt is not None:
            cur_h = f'<span class="cur">{cur}</span>' if cur is not None else ""
            arw_h = ('<span class="arw">→</span>'
                     if (cur is not None and tgt is not None) else "")
            tgt_h = f'<span class="tgt">{tgt}</span>' if tgt is not None else ""
            mv = f'<div class="mv">{cur_h}{arw_h}{tgt_h}</div>'
        unit = f'<div class="lever-unit">{it["unit"]}</div>' if it.get("unit") else ""
        mech = f'<div class="mech">{it["mechanism"]}</div>' if it.get("mechanism") else ""
        imp = f'<span class="imp">{it["impact"]}</span>' if it.get("impact") else ""
        cards.append(
            f'<div class="lever"><div class="n">{_esc(str(n))}</div>'
            f'<h4>{it.get("name", "")}</h4>{mv}{unit}{mech}{imp}</div>'
        )
    return (f'<h2>{_esc(title)}</h2>{intro}'
            f'<div class="levers">{"".join(cards)}</div>')


def timeline_block(fj: dict) -> str:
    tl = fj.get("timeline", [])
    if not tl:
        return ""
    nodes = []
    for i, n in enumerate(tl):
        now = " tl-now" if n.get("now") or i == 0 else ""
        nodes.append(
            f'<div class="tl-node{now}"><div class="tl-wk">{_esc(n.get("when",""))}</div>'
            f'<div class="tl-what">{_esc(n.get("what",""))}</div>'
            f'<div class="tl-sub">{_esc(n.get("sub",""))}</div></div>'
        )
    return f'<div class="tl">{"".join(nodes)}</div>'


def this_week_block(fj: dict) -> str:
    ap = fj.get("action_plan", {})
    items = ap.get("this_week", [])
    if not items:
        return ""
    lane = ap.get("this_week_lane", "🚨 This week — the only thing that's urgent")
    out = [f'<div class="lane lane-p1">{_esc(lane)}</div>']
    for it in items:
        out.append(ai(_esc(it.get("title", "")), it.get("meta", ""), "p1"))
    review = ap.get("review_lane")
    if review:
        out.append(f'<div class="lane lane-p2">{_esc(review.get("lane",""))}</div>')
        out.append(
            '<p style="font-size:13px;color:var(--ink-900);'
            'background:var(--spice-tint);border:1px solid #fbd9cc;'
            'border-radius:6px;padding:14px 18px;margin-bottom:24px;'
            f'line-height:1.7">{review.get("body","")}</p>'
        )
    return "".join(out)


def tier_health_block(run_dir: pathlib.Path, fj: dict) -> str:
    th = fj.get("tier_health", {})
    lis = "".join(f"<li>{x}</li>" for x in th.get("lines", []))
    note = (f'<div style="margin-top:8px">{th["note"]}</div>'
            if th.get("note") else "")
    return (
        '<h2>Location Tier Health</h2>'
        f'<div class="radar-wrap">{img(run_dir, "tier_donut.png")}</div>'
        '<div class="cap"><ul style="margin:0;padding-left:20px;'
        f'line-height:1.7">{lis}</ul>{note}</div>'
    )


def what_moved_block(fj: dict) -> str:
    wm = fj.get("what_moved", {})
    if wm.get("first_cycle_note") or fj.get("first_cycle_note"):
        note = wm.get("note") or fj.get("what_moved_note") or (
            "Cycle 0 — baseline established. No prior diagnostic exists; "
            "deltas begin next cycle. No prior numbers are fabricated here.")
        return (f'<h2>What Moved Since Last Cycle</h2>'
                f'<p style="font-size:13px;color:var(--ink-500);'
                f'margin-bottom:10px"><b>{_esc(note)}</b></p>')
    deltas = wm.get("deltas", [])
    rows = "".join(
        f'<tr><td>{_esc(d["name"])}</td><td>{_esc(d["current"])}</td>'
        f'<td>{_esc(d["prior"])}</td>'
        f'<td class="{"up" if d.get("direction")=="up" else "dn"}">'
        f'{_esc(d["delta"])}</td></tr>'
        for d in deltas
    )
    if not rows:
        return ""
    return (
        '<h2>What Moved Since Last Cycle</h2>'
        '<table><tr><th>Metric</th><th>Now</th><th>Prior</th><th>Δ</th></tr>'
        f'{rows}</table>'
    )


def trend_block(run_dir: pathlib.Path, fj: dict, mj: dict) -> str:
    """90-Day Trend. Renders the REAL weekly GMV/orders overlay when
    metrics.trend_weekly is present (derived upstream from per-order DD/GH
    transaction exports); degrades to an honest text note otherwise. The
    chart PNG itself is emitted by make_charts.trend_overlay; img() shows a
    visible placeholder if it is pending — never silently."""
    tw = mj.get("trend_weekly")
    if tw:
        cap = fj.get("trend_caption") or tw.get("caption") or tw.get("source")
        cap_html = (f'<div class="cap" style="margin-top:6px">{_esc(cap)}</div>'
                    if cap else "")
        return (f'<h2>90-Day Trend</h2><div class="panel">'
                f'{img(run_dir, "trend_overlay.png")}</div>{cap_html}')
    msg = fj.get("trend_pending_note") or (
        "No prior-period comparison available this cycle — a weekly GMV/orders "
        "series is not derivable from the parsed exports (no per-order DD/GH "
        "transaction file supplied). Held until a real weekly series is "
        "supplied. No sparkline is fabricated.")
    return (f'<h2>90-Day Trend</h2><div class="panel"><div class="cap" '
            f'style="margin:0">{_esc(msg)}</div></div>')


def daypart_block(run_dir: pathlib.Path, fj: dict, mj: dict) -> str:
    """Daypart heatmap. Renders the REAL day×hour order-count heatmap when
    metrics.daypart is present (derived upstream from per-order DD/GH
    transaction exports) with a peak-window caption sourced from the
    contract; degrades to an honest text note otherwise — never fabricated,
    never falsely labelled 'deferred' when the data is in fact present."""
    dp = mj.get("daypart")
    if dp:
        pk = dp.get("peak") or {}
        cap = fj.get("daypart_caption")
        if not cap and pk:
            cap = (f"Peak demand: {pk.get('day')} "
                   f"{pk.get('hour')}:00 ({pk.get('orders')} orders).")
            if dp.get("weakest_day"):
                cap += f" Weakest day: {dp['weakest_day']}."
        cap_html = (f'<div class="cap" style="margin-top:6px">{_esc(cap)}</div>'
                    if cap else "")
        return (f'<div class="panel">{img(run_dir, "daypart_heatmap.png")}'
                f'</div>{cap_html}')
    msg = fj.get("daypart_pending_note") or (
        "Daypart heatmap deferred — per-order timestamp matrix not in this "
        "cycle's parsed set (no per-order DD/GH transaction file with local "
        "timestamps supplied). No heatmap is fabricated here.")
    return (f'<div class="daypart">📅 <strong>Daypart heatmap deferred</strong>'
            f' — {_esc(msg)}</div>')


def dq_footer(fj: dict) -> str:
    txt = fj.get("data_quality_footer", "")
    return f'<div class="dq"><strong>Data quality:</strong> {txt}</div>'


# --- Half 2 toggles -------------------------------------------------------- #

def _toggle(title: str, body: str, open_: bool = True) -> str:
    o = " open" if open_ else ""
    return (f'<details{o}><summary>{title}</summary>'
            f'<div class="detail-body">{body}</div></details>')


def portfolio_snapshot(fj: dict) -> str:
    ps = fj.get("portfolio_snapshot", {})
    rows = ps.get("rows", [])
    head = ("<tr><th>Platform</th><th>Gross</th><th>Orders</th><th>AOV</th>"
            "<th>Eff. Commission</th><th>Net %</th><th>Est. Monthly</th>"
            "<th>Mktg %</th></tr>")
    trs = []
    for r in rows:
        trs.append(
            f'<tr><td><b>{_esc(r.get("platform",""))}</b></td>'
            f'<td>{_fmt(r.get("gross"), "money")}</td>'
            f'<td>{_fmt(r.get("orders"), "int")}</td>'
            f'<td>{_fmt(r.get("aov"), "money2")}</td>'
            f'<td>{_fmt(r.get("eff_commission"))}</td>'
            f'<td>{_fmt(r.get("net_pct"))}</td>'
            f'<td>{_fmt(r.get("est_monthly"), "money")}</td>'
            f'<td>{_fmt(r.get("mktg_pct"))}</td></tr>'
        )
    narr = ps.get("narrative", "")
    body = (f'<table>{head}{"".join(trs)}</table><p>{narr}</p>')
    return _toggle("📊 Portfolio Snapshot", body)


def _bullet_section(sec: dict) -> str:
    """Render one bullet-structured detail block: optional <h3> heading,
    optional intro paragraph(s), then a tight <ul> of HTML bullets. Every
    string comes from findings.json — no literals here."""
    parts = []
    if sec.get("heading"):
        parts.append(f'<h3>{_esc(sec["heading"])}</h3>')
    for p in sec.get("paras", []):
        parts.append(f'<p>{p}</p>')
    bullets = sec.get("bullets", [])
    if bullets:
        lis = "".join(f"<li>{b}</li>" for b in bullets)
        parts.append('<ul style="margin:6px 0 0;padding-left:20px;'
                     f'line-height:1.7">{lis}</ul>')
    return "".join(parts)


def _data_table(tbl: dict) -> str:
    """Generic table from {headers:[...], rows:[[...]]}. Cells are HTML
    strings supplied by the contract — builder adds no numbers of its own."""
    if not tbl or not tbl.get("headers"):
        return ""
    head = "".join(f"<th>{_esc(h)}</th>" for h in tbl["headers"])
    body = "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
        for row in tbl.get("rows", [])
    )
    return f'<table><tr>{head}</tr>{body}</table>'


def menu_storefront(run_dir: pathlib.Path, fj: dict) -> str:
    """REQUIRED toggle. Renders the storefront-audit + conversion-funnel
    visual section. Fully data-driven:

      * ``menu_storefront.intro``        — HTML intro paragraph(s)
      * ``menu_storefront.storefront_table`` / ``funnel_table``
                                          — {headers, rows} contract tables
      * ``menu_storefront.sections``     — list of bullet-structured blocks
      * ``menu_storefront.html``         — escape hatch / legacy raw HTML
                                            (appended after the structured
                                            parts, before charts)

    Charts ``storefront_audit.png`` and ``funnel_ue.png`` are embedded
    inline when present in charts/ (img() emits a visible placeholder if a
    chart is pending — never silently). If the whole field is omitted the
    toggle still renders an explicit DATA-PENDING block (never dropped).
    Renders gracefully text-only when the chart PNGs are absent."""
    ms = fj.get("menu_storefront")
    if ms is None:
        body = (
            '<p><b>⚠️ Storefront / menu baseline not supplied this cycle.</b> '
            'No prior storefront audit was synthesized into findings.json. '
            'This is a data-pull gap, not an analysis choice.</p>'
            '<h3>⚠️ Data-pending — capture in the next data pull</h3>'
            '<ul style="margin:0;padding-left:20px;line-height:1.7">'
            '<li><b>UE user conversion funnel (per location)</b> — '
            'impressions → storefront → menu → orders.</li>'
            '<li><b>Re-order / repeat-customer rate</b> — UE Repeat Customers '
            '+ DD Frequent Customers (+ GH if exposed), machine-readable.</li>'
            '</ul>')
        return _toggle("🏞️ Menu &amp; Storefront", body)

    parts = []
    if ms.get("intro"):
        parts.append(f'<p>{ms["intro"]}</p>')

    # Storefront-audit visual + table
    sa_img = img(run_dir, "storefront_audit.png")
    if "[chart pending:" not in sa_img:
        parts.append(f'<div class="panel">{sa_img}</div>')
    st = _data_table(ms.get("storefront_table"))
    if st:
        parts.append(st)
    for sec in ms.get("storefront_sections", []):
        parts.append(_bullet_section(sec))

    # Conversion-funnel visual + table
    fn_img = img(run_dir, "funnel_ue.png")
    if "[chart pending:" not in fn_img:
        parts.append(f'<div class="panel">{fn_img}</div>')
    ft = _data_table(ms.get("funnel_table"))
    if ft:
        parts.append(ft)
    for sec in ms.get("funnel_sections", []):
        parts.append(_bullet_section(sec))

    # Generic bullet sections + legacy raw-HTML escape hatch
    for sec in ms.get("sections", []):
        parts.append(_bullet_section(sec))
    if ms.get("html"):
        parts.append(ms["html"])

    body = "".join(parts)
    if not body.strip():
        body = ('<p><b>Storefront / menu baseline supplied but empty.</b> '
                'Populate menu_storefront in findings.json.</p>')
    if "data-pending" not in body.lower() and "data pending" not in body.lower():
        body += (
            '<h3>⚠️ Data-pending — verify each cycle</h3>'
            '<p>Confirm UE user conversion funnel (per location) and '
            're-order / repeat-customer rate are captured and '
            'machine-readable for the next cycle.</p>')
    return _toggle("🏞️ Menu &amp; Storefront", body)


def generic_toggle(fj: dict, key: str, icon_title: str) -> str:
    blk = fj.get(key)
    if not blk:
        return _toggle(icon_title,
                       f'<p>Section not supplied in findings.json '
                       f'(<code>{_esc(key)}</code>).</p>')
    return _toggle(icon_title, blk.get("html", ""))


def appendix(fj: dict) -> str:
    """Full location table, sorted by the contract's sort key. Driven from
    findings.json store_tiers so the appendix can never drift."""
    stores = fj.get("store_tiers", [])
    key = fj.get("appendix_sort_key", "blended_gmv")
    stores = sorted(stores, key=lambda s: -(s.get(key) or 0))
    cols = fj.get("appendix_columns")
    if cols:
        head = "".join(f"<th>{_esc(c['label'])}</th>" for c in cols)
        trs = []
        for s in stores:
            tds = []
            for c in cols:
                v = s.get(c["field"])
                if c.get("tier"):
                    tds.append(f'<td>{_TIER_EMOJI.get(v, "")} {_esc(v)}</td>')
                elif c.get("kind"):
                    tds.append(f'<td>{_fmt(v, c["kind"])}</td>')
                else:
                    tds.append(f'<td>{_esc(v)}</td>')
            trs.append(f'<tr>{"".join(tds)}</tr>')
        table = f'<table><tr>{head}</tr>{"".join(trs)}</table>'
    else:
        # default schema-agnostic shape
        trs = []
        for s in stores:
            trs.append(
                f'<tr><td>{_esc(s.get("store",""))}</td>'
                f'<td>{_TIER_EMOJI.get(s.get("tier",""),"")} '
                f'{_esc(s.get("tier",""))}</td>'
                f'<td>{_fmt(s.get(key), "money")}</td></tr>'
            )
        table = ('<table><tr><th>Store</th><th>Tier</th>'
                 f'<th>{_esc(key)}</th></tr>{"".join(trs)}</table>')
    note = fj.get("appendix_note", "")
    return _toggle("📎 Appendix — Full Location Table",
                   f'{table}<p style="font-size:11px;'
                   f'color:var(--ink-500)">{_esc(note)}</p>', open_=False)


# --------------------------------------------------------------------------- #
# Assembly                                                                     #
# --------------------------------------------------------------------------- #

def build(run_dir: pathlib.Path) -> str:
    fj, mj = _load(run_dir)
    css_path = run_dir / "report_style.css"
    css = css_path.read_text() if css_path.exists() else ""

    client = _esc(fj.get("client", "Client"))
    window = _esc(fj.get("window", ""))
    platforms = _esc(fj.get("platforms", ""))
    n = fj.get("n_locations", "")
    cycle = fj.get("cycle", fj.get("cycle_label", ""))
    locs_line = fj.get("locations_line", f"{n}")
    prepared = _esc(fj.get("prepared_line",
                           "Prepared by Spice Digital · Next cycle in 4 weeks"))

    toggles = "".join([
        portfolio_snapshot(fj),
        menu_storefront(run_dir, fj),
        generic_toggle(fj, "ops_detail", "⚙️ Ops — per-store cross-platform health"),
        generic_toggle(fj, "brand_health_detail",
                        "🛡️ Brand Operational Health Detail"),
        generic_toggle(fj, "campaigns_detail", "📈 Campaigns"),
        generic_toggle(fj, "location_tiers_detail", "🏪 Location Tiers"),
        generic_toggle(fj, "full_action_plan",
                        "✅ Full Action Plan — owners, dates, blockers"),
        appendix(fj),
    ])

    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{client} — Diagnostics &amp; Action Plan — {window}</title>
<style>{css}</style></head><body><div class="doc">

<div style="display:flex;align-items:center;gap:16px;margin-bottom:10px">
{spice_logo(run_dir, 52)}
<div class="meta" style="margin:0">Spice Diagnostic · 90-Day Rolling Report · {client} · {_esc(cycle)}</div>
</div>
<h1>{client} — Diagnostics &amp; Action Plan</h1>
<div class="subhead"><strong>Window:</strong> {window} ·
<strong>Platforms:</strong> {platforms} ·
<strong>Locations:</strong> {_esc(locs_line)}</div>

<div class="half">Overview</div>
<h2>Executive Summary</h2>
{exec_summary(fj)}
<h2>The 60-second view</h2>
{hero_strip(fj)}

{radar_block(run_dir, fj, mj)}

{fro_block(fj)}

{levers_block(fj)}

<h2>Action Plan</h2>
{timeline_block(fj)}
{this_week_block(fj)}

{tier_health_block(run_dir, fj)}

{what_moved_block(fj)}

{trend_block(run_dir, fj, mj)}
{daypart_block(run_dir, fj, mj)}

{dq_footer(fj)}

<div class="half" style="color:var(--ink-900);background:var(--ink-100)">Detailed Findings</div>
<h2>Full analyst depth</h2>

{toggles}

<div class="foot" style="display:flex;align-items:center;justify-content:center;gap:10px">
{spice_logo(run_dir, 24)}
<span>{prepared}</span></div>

</div></body></html>"""


def main(argv) -> int:
    run_dir = pathlib.Path(argv[1]).resolve() if len(argv) > 1 \
        else pathlib.Path(__file__).parent
    out_name = json.loads((run_dir / "findings.json").read_text()).get(
        "output_html", "diagnostic-report.html")
    out = run_dir / out_name
    html_doc = build(run_dir)
    out.write_text(html_doc)
    print(f"{out.name} built clean: {len(html_doc):,} chars, "
          f"{out.stat().st_size:,} bytes (run dir: {run_dir})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
