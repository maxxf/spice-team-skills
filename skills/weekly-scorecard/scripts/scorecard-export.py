#!/usr/bin/env python3
"""
Spice Weekly Scorecard — Static Client Export Generator

Generates a self-contained, client-ready HTML scorecard from the canonical
long-format CSV. Used to share weekly scorecards with clients via email or
Notion portal upload.

Usage:
    python3 scorecard-export.py \\
        --csv /path/to/scorecard-metrics.csv \\
        --client fresh_kitchen \\
        --week-end 2026-04-26 \\
        --output /path/to/output.html

The CSV must have the canonical schema:
    client_slug, week_start, week_end, platform, location, metric,
    value, prior_value, status, source_file, pulled_at, pulled_by, notes

Brand colors and client display name can be overridden via flags.

Last updated: 2026-04-30
"""

from __future__ import annotations
import argparse
import csv
import html
import json
from pathlib import Path
from datetime import date, timedelta
from typing import Optional

# ---------------------------------------------------------------------------
# Metric metadata (canonical schema)
# ---------------------------------------------------------------------------

METRIC_META = {
    'total_sales':           {'label': 'Total Sales',          'section': 'money',           'unit': 'currency', 'format': 'currency0'},
    'net_payout':            {'label': 'Net Payout',           'section': 'money',           'unit': 'currency', 'format': 'currency0'},
    'net_payout_pct':        {'label': 'Net Payout %',         'section': 'money',           'unit': 'percent',  'format': 'percent1'},
    'organic_sales_pct':     {'label': 'Organic Sales %',      'section': 'money',           'unit': 'percent',  'format': 'percent1'},
    'aov':                   {'label': 'AOV',                  'section': 'money',           'unit': 'currency', 'format': 'currency2'},
    'marketing_spend_pct':   {'label': 'Marketing Spend %',    'section': 'efficiency',      'unit': 'percent',  'format': 'percent1'},
    'marketing_spend':       {'label': 'Marketing Spend',      'section': 'efficiency',      'unit': 'currency', 'format': 'currency0'},
    'roas':                  {'label': 'ROAS',                 'section': 'efficiency',      'unit': 'ratio',    'format': 'roas'},
    'order_count':           {'label': 'Orders',               'section': 'efficiency',      'unit': 'integer',  'format': 'integer'},
    'order_completion_rate': {'label': 'Order Completion %',   'section': 'operations',      'unit': 'percent',  'format': 'percent1'},
    'error_rate':            {'label': 'Error Rate',           'section': 'operations',      'unit': 'percent',  'format': 'percent2'},
    'cancel_rate':           {'label': 'Cancel Rate',          'section': 'operations',      'unit': 'percent',  'format': 'percent2'},
    'downtime_hours':        {'label': 'Downtime (hrs)',       'section': 'operations',      'unit': 'decimal',  'format': 'decimal1'},
    'avg_rating':            {'label': 'Avg Rating',           'section': 'reputation',      'unit': 'decimal',  'format': 'decimal2'},
    'ratings_velocity':      {'label': 'Ratings Velocity',     'section': 'reputation',      'unit': 'integer',  'format': 'integer_per_week'},
    'storefront_views':      {'label': 'Storefront Views',     'section': 'discoverability', 'unit': 'integer',  'format': 'integer'},
    'menu_conversion':       {'label': 'Menu Conversion',      'section': 'discoverability', 'unit': 'percent',  'format': 'percent1'},
}

SECTIONS = [
    {'id': 'money',           'label': 'Money',           'question': 'Did we make money?'},
    {'id': 'efficiency',      'label': 'Efficiency',      'question': 'Was the spend efficient?'},
    {'id': 'operations',      'label': 'Operations',      'question': 'Did operations stay clean?'},
    {'id': 'reputation',      'label': 'Reputation',      'question': 'Are customers happy?'},
    {'id': 'discoverability', 'label': 'Discoverability', 'question': 'Will next week be better?'},
]

# Brand presets — extend as more clients onboard.
BRAND_PRESETS = {
    'fresh_kitchen': {
        'display_name': 'Fresh Kitchen',
        'primary': '#E884A7',
        'accent':  '#35673B',
        'cream':   '#F7EDE3',
        'brown':   '#9A6A4F',
        'tagline': 'Good Food Forever',
    },
    'goop_kitchen': {
        'display_name': 'goop Kitchen',
        'primary': '#1a1a1a',
        'accent':  '#888780',
        'cream':   '#f7f7f5',
        'brown':   '#5f5e5a',
        'tagline': '',
    },
    'default': {
        'display_name': '',
        'primary': '#1a1a1a',
        'accent':  '#5f5e5a',
        'cream':   '#f7f7f5',
        'brown':   '#888780',
        'tagline': '',
    },
}

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def fmt(v, format_):
    if v is None or v == '':
        return '—'
    try:
        n = float(v)
    except (TypeError, ValueError):
        return '—'
    if format_ == 'currency0':       return '$' + f"{round(n):,}"
    if format_ == 'currency2':       return '$' + f"{n:,.2f}"
    if format_ == 'percent1':        return f"{n:.1f}%"
    if format_ == 'percent2':        return f"{n:.2f}%"
    if format_ == 'decimal1':        return f"{n:.1f}"
    if format_ == 'decimal2':        return f"{n:.2f}"
    if format_ == 'roas':            return f"{n:.1f}x"
    if format_ == 'integer':         return f"{round(n):,}"
    if format_ == 'integer_per_week':return f"{round(n):,}/wk"
    return str(n)


def fmt_delta(curr, prior, unit):
    if prior is None or prior == '' or curr is None or curr == '':
        return {'text': '—', 'color': '#888780', 'arrow': ''}
    try:
        c = float(curr); p = float(prior)
    except (TypeError, ValueError):
        return {'text': '—', 'color': '#888780', 'arrow': ''}
    if p == 0:
        return {'text': '—', 'color': '#888780', 'arrow': ''}
    if unit in ('percent', 'ratio'):
        diff = c - p
        sign = '+' if diff > 0 else ''
        if diff > 0.05:
            arrow, color = '▲', '#3b6d11'
        elif diff < -0.05:
            arrow, color = '▼', '#a32d2d'
        else:
            arrow, color = '–', '#5f5e5a'
        suffix = 'x' if unit == 'ratio' else 'pp'
        return {'text': f"{sign}{diff:.1f}{suffix}", 'color': color, 'arrow': arrow}
    pct = ((c - p) / p) * 100
    sign = '+' if pct > 0 else ''
    if pct > 0.5:
        arrow, color = '▲', '#3b6d11'
    elif pct < -0.5:
        arrow, color = '▼', '#a32d2d'
    else:
        arrow, color = '–', '#5f5e5a'
    return {'text': f"{sign}{pct:.1f}%", 'color': color, 'arrow': arrow}


def build_sparkline(values, color, w=100, h=20):
    if not values or len(values) < 2:
        return ''
    pad = 2
    mn, mx = min(values), max(values)
    rng = (mx - mn) or 1
    pts = []
    for i, v in enumerate(values):
        x = pad + (i * (w - 2 * pad)) / (len(values) - 1)
        y = h - pad - ((v - mn) / rng) * (h - 2 * pad)
        pts.append(f"{round(x)},{round(y)}")
    return f'<svg width="{w}" height="{h}"><polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="1.2"/></svg>'


# ---------------------------------------------------------------------------
# Data loading and filtering
# ---------------------------------------------------------------------------

def load_csv(path: Path) -> list[dict]:
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def get_current_row(rows, client_slug, week_end, metric, platform, location):
    for r in rows:
        if (r['client_slug'] == client_slug and
            r['week_end'] == week_end and
            r['metric'] == metric and
            r['platform'] == platform and
            r['location'] == location):
            return r
    return None


def get_sparkline_series(rows, client_slug, metric, platform, location):
    matches = [r for r in rows
               if r['client_slug'] == client_slug
               and r['metric'] == metric
               and r['platform'] == platform
               and r['location'] == location]
    matches.sort(key=lambda r: r['week_end'])
    out = []
    for r in matches:
        try:
            out.append(float(r['value']))
        except (TypeError, ValueError):
            pass
    return out


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

STATUS_COLORS = {
    'green':  {'dot': '#3b6d11', 'text': '#3b6d11'},
    'yellow': {'dot': '#854f0b', 'text': '#854f0b'},
    'red':    {'dot': '#a32d2d', 'text': '#a32d2d'},
    'gray':   {'dot': '#b4b2a9', 'text': '#888780'},
}


def render_metric_row(rows, client, week_end, metric, platform, location, is_child=False, force_platform_label=False):
    meta = METRIC_META.get(metric)
    if not meta:
        return ''
    row = get_current_row(rows, client, week_end, metric, platform, location)
    if not row:
        return ''
    try:
        value = float(row['value'])
    except (TypeError, ValueError):
        value = None
    prior = row.get('prior_value', '')
    status = (row.get('status') or 'gray').lower()
    sc = STATUS_COLORS.get(status, STATUS_COLORS['gray'])
    delta = fmt_delta(value, prior, meta['unit'])
    series = get_sparkline_series(rows, client, metric, platform, location)
    spark_color = sc['text'] if status in ('red', 'yellow', 'green') else '#5f5e5a'
    notes = (row.get('notes') or '').strip()

    if is_child:
        label_html = f'<span class="platform-tag">{html.escape(platform)}</span>'
    elif force_platform_label and platform != 'ALL':
        label_html = f'{html.escape(meta["label"])} <span class="platform-tag">{html.escape(platform)}</span>'
    else:
        label_html = html.escape(meta['label'])

    notes_html = ''
    if notes and not is_child:
        notes_html = f'<div class="metric-note">{html.escape(notes)}</div>'

    row_class = 'platform-row' if is_child else ''
    return (
        f'<tr class="{row_class}">'
        f'<td class="metric-label">{label_html}{notes_html}</td>'
        f'<td class="metric-value">{fmt(value, meta["format"])}</td>'
        f'<td class="metric-delta" style="color: {delta["color"]};">{delta["arrow"]} {delta["text"]}</td>'
        f'<td class="metric-spark">{build_sparkline(series, spark_color)}</td>'
        f'<td class="metric-status"><span class="status-dot" title="{status}" style="background: {sc["dot"]};"></span></td>'
        f'</tr>'
    )


def render_metric_group(rows, client, week_end, metric):
    all_row = get_current_row(rows, client, week_end, metric, 'ALL', 'ALL')
    ue_row = get_current_row(rows, client, week_end, metric, 'Uber Eats', 'ALL')
    dd_row = get_current_row(rows, client, week_end, metric, 'DoorDash', 'ALL')
    gh_row = get_current_row(rows, client, week_end, metric, 'Grubhub', 'ALL')

    children = []
    if ue_row: children.append(('Uber Eats', 'ALL'))
    if dd_row: children.append(('DoorDash', 'ALL'))
    if gh_row: children.append(('Grubhub', 'ALL'))

    if all_row:
        parent_html = render_metric_row(rows, client, week_end, metric, 'ALL', 'ALL', False)
        child_list = children
    elif len(children) == 1:
        # Single-platform metric — show only that row, no platform tag needed
        p, l = children[0]
        return render_metric_row(rows, client, week_end, metric, p, l, False)
    elif len(children) > 1:
        # Multi-platform but no aggregate row — render each labeled by platform
        out = ''
        for p, l in children:
            out += render_metric_row(rows, client, week_end, metric, p, l, False, force_platform_label=True)
        return out
    else:
        return ''

    # Render parent + always-expanded children (static export, no toggle)
    out = parent_html
    if len(child_list) > 1:
        for p, l in child_list:
            out += render_metric_row(rows, client, week_end, metric, p, l, True)
    return out


def render_location_grid(rows, client, week_end):
    locs = [r for r in rows
            if r['client_slug'] == client
            and r['week_end'] == week_end
            and r['metric'] == 'total_sales'
            and r['location'] != 'ALL']
    if not locs:
        return ''
    locs.sort(key=lambda r: float(r['value']) if r.get('value') else 0, reverse=True)
    out = '<div class="grid-section">Per-location performance</div><div class="loc-grid">'
    for r in locs:
        status = (r.get('status') or 'gray').lower()
        sc = STATUS_COLORS.get(status, STATUS_COLORS['gray'])
        roas_row = next((x for x in rows
                         if x['client_slug'] == client
                         and x['week_end'] == week_end
                         and x['metric'] == 'roas'
                         and x['location'] == r['location']), None)
        roas_text = f"{roas_row['value']}x ROAS" if roas_row else ''
        out += (
            f'<div class="loc-card">'
            f'<div class="loc-name">{html.escape(r["location"])}</div>'
            f'<div class="loc-value">{fmt(float(r["value"]), "currency0")}</div>'
            f'<div class="loc-roas">{html.escape(roas_text)}</div>'
            f'<span class="loc-dot" style="background: {sc["dot"]};"></span>'
            f'</div>'
        )
    out += '</div>'
    return out


def render_headline(rows, client, week_end, brand):
    row = get_current_row(rows, client, week_end, 'total_sales', 'ALL', 'ALL')
    if not row:
        return ''
    try:
        value = float(row['value']); prior = float(row.get('prior_value') or 0)
    except (TypeError, ValueError):
        return ''
    delta = fmt_delta(value, prior, 'currency')
    series = get_sparkline_series(rows, client, 'total_sales', 'ALL', 'ALL')
    status = (row.get('status') or 'gray').lower()
    sc = STATUS_COLORS.get(status, STATUS_COLORS['gray'])
    return (
        f'<div class="headline">'
        f'<div class="headline-value">{fmt(value, "currency0")}</div>'
        f'<div class="headline-delta" style="color: {delta["color"]};">{delta["arrow"]} {delta["text"]}</div>'
        f'<div class="headline-spark">{build_sparkline(series, sc["text"], 180, 36)}</div>'
        f'</div>'
        f'<div class="headline-sub">Total sales week-over-week</div>'
    )


def render_html(rows: list[dict], client: str, week_end: str, signal_text: str, brand: dict, generated_at: str) -> str:
    # Filter rows to the client and recent weeks for sparklines
    week_end_d = date.fromisoformat(week_end)
    cutoff = (week_end_d - timedelta(weeks=12)).isoformat()
    rows = [r for r in rows
            if r['client_slug'] == client
            and r['week_end'] >= cutoff]

    start_row = next((r for r in rows
                      if r['client_slug'] == client and r['week_end'] == week_end), None)
    week_start = start_row['week_start'] if start_row else ''
    date_range = f"{week_start} to {week_end}"

    # Build sections
    sections_html = ''
    for sec in SECTIONS:
        metrics_in_section = [m for m, meta in METRIC_META.items() if meta['section'] == sec['id']]
        rendered = ''
        for m in metrics_in_section:
            rendered += render_metric_group(rows, client, week_end, m)
        if rendered:
            sections_html += (
                f'<div class="section-header">'
                f'<div class="section-label">{sec["label"]}</div>'
                f'<div class="section-question">{sec["question"]}</div>'
                f'</div>'
                f'<table>{rendered}</table>'
            )

    headline_html = render_headline(rows, client, week_end, brand)
    location_html = render_location_grid(rows, client, week_end)

    signal_html = (
        f'<div class="signal-box">'
        f'<div class="signal-label">This week\'s signal</div>'
        f'<div class="signal-text">{html.escape(signal_text)}</div>'
        f'</div>'
    ) if signal_text else ''

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(brand['display_name'])} — Weekly Scorecard ({week_end})</title>
<style>
:root {{
  color-scheme: light;
  --primary: {brand['primary']};
  --accent: {brand['accent']};
  --cream: {brand['cream']};
  --bg: #ffffff;
  --bg-secondary: #f7f7f5;
  --bg-warning: #faeeda;
  --text-primary: #1a1a1a;
  --text-secondary: #5f5e5a;
  --text-tertiary: #888780;
  --text-success: #3b6d11;
  --text-warning: #854f0b;
  --text-danger: #a32d2d;
  --border-tertiary: rgba(0,0,0,0.10);
  --border-secondary: rgba(0,0,0,0.20);
  --radius-md: 8px;
  --radius-lg: 12px;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--bg);
  color: var(--text-primary);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 14px;
  line-height: 1.5;
}}
.container {{ max-width: 760px; margin: 0 auto; padding: 0 1.5rem 2rem; }}
.brand-banner {{
  background: var(--primary);
  color: white;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.5rem;
}}
.brand-banner-inner {{
  max-width: 760px; margin: 0 auto;
  display: flex; align-items: baseline; justify-content: space-between;
  flex-wrap: wrap; gap: 8px;
}}
.brand-name {{ font-size: 18px; font-weight: 500; }}
.brand-meta {{ font-size: 12px; opacity: 0.9; }}
.title-row {{
  display: flex; justify-content: space-between; align-items: baseline;
  gap: 12px; flex-wrap: wrap; margin-bottom: 1rem;
}}
.title {{ font-size: 22px; font-weight: 500; margin: 0; }}
.subtitle {{ font-size: 13px; color: var(--text-secondary); }}
.headline {{
  display: flex; align-items: baseline; gap: 16px; margin-bottom: 0.5rem;
  flex-wrap: wrap;
}}
.headline-value {{ font-size: 36px; font-weight: 500; }}
.headline-delta {{ font-size: 15px; font-weight: 500; }}
.headline-spark {{ margin-left: auto; }}
.headline-sub {{ font-size: 13px; color: var(--text-secondary); margin-bottom: 1.5rem; }}
.section-header {{ display: flex; align-items: baseline; gap: 8px; margin: 1.75rem 0 0.5rem; }}
.section-label {{
  font-size: 13px; font-weight: 500; color: var(--text-secondary);
  text-transform: uppercase; letter-spacing: 0.04em;
}}
.section-question {{ font-size: 12px; color: var(--text-tertiary); font-style: italic; }}
table {{ width: 100%; border-collapse: collapse; }}
td {{ padding: 10px 0; vertical-align: middle; }}
tr {{ border-bottom: 0.5px solid var(--border-tertiary); }}
tr:last-child {{ border-bottom: none; }}
.metric-label {{ width: 38%; }}
.metric-value {{ font-weight: 500; width: 18%; }}
.metric-delta {{ width: 14%; }}
.metric-spark {{ width: 22%; }}
.metric-status {{ width: 8%; text-align: right; }}
.metric-note {{
  font-size: 12px; color: var(--text-tertiary);
  font-style: italic; margin-top: 2px;
}}
.platform-tag {{
  color: var(--text-tertiary); font-size: 12px;
  background: var(--bg-secondary); padding: 1px 6px; border-radius: 4px;
}}
.status-dot {{
  display: inline-block; width: 10px; height: 10px; border-radius: 50%;
}}
.platform-row td {{
  padding: 6px 0 6px 24px;
  background: var(--bg-secondary);
  font-size: 13px;
}}
.platform-row td:first-child {{ padding-left: 32px; }}
.platform-row .metric-label {{ color: var(--text-secondary); }}
.grid-section {{
  font-size: 13px; font-weight: 500; color: var(--text-secondary);
  text-transform: uppercase; letter-spacing: 0.04em; margin: 2rem 0 0.75rem;
}}
.loc-grid {{
  display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 8px;
}}
.loc-card {{
  background: var(--bg-secondary); border-radius: var(--radius-md);
  padding: 10px 12px; position: relative;
}}
.loc-name {{ font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; padding-right: 14px; }}
.loc-value {{ font-size: 16px; font-weight: 500; }}
.loc-roas {{ font-size: 11px; color: var(--text-tertiary); margin-top: 2px; }}
.loc-dot {{
  position: absolute; top: 10px; right: 10px;
  display: inline-block; width: 8px; height: 8px; border-radius: 50%;
}}
.signal-box {{
  margin-top: 2rem; padding: 14px 16px;
  background: var(--bg-warning); border-radius: var(--radius-md);
  border-left: 3px solid var(--text-warning);
}}
.signal-label {{
  font-size: 12px; font-weight: 500; color: var(--text-warning);
  text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 6px;
}}
.signal-text {{
  font-size: 14px; color: var(--text-warning); line-height: 1.6;
  white-space: pre-wrap;
}}
.footer {{
  margin-top: 3rem; padding-top: 1rem;
  border-top: 0.5px solid var(--border-tertiary);
  font-size: 11px; color: var(--text-tertiary);
  display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px;
}}
.legend {{
  display: flex; gap: 16px; align-items: center;
  margin-bottom: 1.5rem; padding: 8px 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  font-size: 12px; color: var(--text-secondary);
}}
.legend-item {{ display: flex; align-items: center; gap: 6px; }}
@media (max-width: 600px) {{
  .container {{ padding: 0 1rem 2rem; }}
  .headline-value {{ font-size: 28px; }}
  .metric-label {{ width: 50%; }}
  .metric-spark {{ display: none; }}
}}
</style>
</head>
<body>
<div class="brand-banner">
  <div class="brand-banner-inner">
    <div class="brand-name">{html.escape(brand['display_name'])}</div>
    <div class="brand-meta">Weekly Scorecard · {date_range}</div>
  </div>
</div>
<div class="container">
  <div class="legend">
    <div class="legend-item"><span class="status-dot" style="background: #3b6d11;"></span>On track</div>
    <div class="legend-item"><span class="status-dot" style="background: #854f0b;"></span>Watch</div>
    <div class="legend-item"><span class="status-dot" style="background: #a32d2d;"></span>Acting on it</div>
  </div>
  {headline_html}
  {sections_html}
  {location_html}
  {signal_html}
  <div class="footer">
    <div>Generated by Spice Digital · {generated_at}</div>
    <div>Questions? Reply to your weekly recap email.</div>
  </div>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Generate static client-facing weekly scorecard HTML.')
    parser.add_argument('--csv', required=True, type=Path, help='Path to canonical scorecard metrics CSV.')
    parser.add_argument('--client', required=True, help='Client slug (e.g. fresh_kitchen).')
    parser.add_argument('--week-end', required=True, help='Week end date in YYYY-MM-DD.')
    parser.add_argument('--output', required=True, type=Path, help='Output HTML file path.')
    parser.add_argument('--signal', default='', help='Signal text (the GM-authored narrative). Optional.')
    parser.add_argument('--signal-file', type=Path, help='Path to a file containing the signal text. Overrides --signal.')
    parser.add_argument('--display-name', help='Override client display name from brand preset.')
    parser.add_argument('--generated-at', help='Override the "generated at" date string. Defaults to today.')
    args = parser.parse_args()

    rows = load_csv(args.csv)
    if not rows:
        raise SystemExit(f"No rows loaded from {args.csv}")

    signal_text = args.signal
    if args.signal_file and args.signal_file.exists():
        signal_text = args.signal_file.read_text(encoding='utf-8').strip()

    brand = dict(BRAND_PRESETS.get(args.client, BRAND_PRESETS['default']))
    if args.display_name:
        brand['display_name'] = args.display_name
    if not brand['display_name']:
        brand['display_name'] = args.client.replace('_', ' ').title()

    generated_at = args.generated_at or date.today().isoformat()

    html_doc = render_html(rows, args.client, args.week_end, signal_text, brand, generated_at)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html_doc, encoding='utf-8')
    print(f"Generated {args.output} ({args.output.stat().st_size:,} bytes)")


if __name__ == '__main__':
    main()
