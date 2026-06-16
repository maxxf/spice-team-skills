#!/usr/bin/env python3
"""
Extract intra-year portfolio trajectory from canonical Weekly Platform Overview 2.0 tab.

Inputs:
- Path to "Weekly Platform Overview 2.0" CSV export
- Start week label (default: "5-Jan" = first full week of 2026 = W1 operational baseline)
- End week label (default: most recent week with data)

Output:
- JSON with weekly trajectory for: Total Sales, Net Payout, TMI, Ad Spend, Discounts,
  Mkt/Sales %, ROAS
- W1 vs W_n delta computation
- Annualized projections at W_n run-rate

Usage:
    python compute_intra_year.py \\
        --tab path/to/Weekly_Platform_Overview_2.0.csv \\
        --start-week 5-Jan --end-week 11-May \\
        --output intra_year.json
"""

import argparse
import csv
import json
import re


def money(s: str) -> float | None:
    """Parse a money string. Returns None if empty/invalid."""
    if not s or s.strip() in ('', '-', '$0', '--', '$-'):
        return None
    try:
        cleaned = re.sub(r'[$,%]', '', s.strip())
        return float(cleaned)
    except ValueError:
        return None


def parse_tab(path: str) -> dict:
    """Parse the Weekly Platform Overview 2.0 tab.

    Returns dict with:
        - week_labels: list of date column headers (e.g., ['20-Oct', '27-Oct', ...])
        - overview: {metric_name: {week_label: value, ...}, ...}
        - per_platform: {platform: {metric: {week: value}}, ...}
    """
    with open(path, 'r', encoding='utf-8') as f:
        rows = list(csv.reader(f))

    # Find the date header row (typically row 4 or 5; look for cells like "20-Oct")
    header_idx = None
    for i, row in enumerate(rows):
        if row and any(re.match(r'\d{1,2}-[A-Z][a-z]{2}', c.strip()) for c in row if c):
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("Couldn't find week header row")

    week_labels = [c.strip() for c in rows[header_idx][2:] if c.strip()]

    overview = {}
    per_platform = {}
    current_platform = "Overview"

    for row in rows[header_idx + 1:]:
        if not row or not row[0]:
            continue
        # Platform header rows (e.g., "UBER EATS", "DOORDASH", "GRUBHUB")
        cell0 = row[0].strip()
        if cell0 in ("UBER EATS", "DOORDASH", "GRUBHUB", "Overview") and not any(row[1:]):
            current_platform = cell0
            if current_platform not in per_platform:
                per_platform[current_platform] = {}
            continue
        # Metric rows
        metric = cell0
        values = {}
        for i, label in enumerate(week_labels):
            col_idx = 2 + i  # metric name is col 0, type is col 1, data starts at col 2
            if col_idx < len(row):
                v = money(row[col_idx])
                if v is not None:
                    values[label] = v
        if values:
            if current_platform == "Overview":
                overview[metric] = values
            else:
                per_platform[current_platform][metric] = values

    return {
        'week_labels': week_labels,
        'overview': overview,
        'per_platform': per_platform,
    }


def compute_delta(parsed: dict, start_week: str, end_week: str) -> dict:
    """Compute W1 vs W_n delta + annualized projection."""
    ov = parsed['overview']
    result = {
        'start_week': start_week,
        'end_week': end_week,
        'overview_metrics': {},
    }
    for metric, weekly in ov.items():
        start_val = weekly.get(start_week)
        end_val = weekly.get(end_week)
        if start_val is None or end_val is None:
            continue
        delta = end_val - start_val
        pct = (end_val / start_val - 1) * 100 if start_val != 0 else None
        result['overview_metrics'][metric] = {
            'start_val': start_val,
            'end_val': end_val,
            'delta_absolute': delta,
            'delta_pct': pct,
            'annualized_run_rate_delta': delta * 52 if metric in (
                'Net Payout', 'Total Sales', 'Total Marketing Investment', 'Ad Spend', 'Discounts'
            ) else None,
        }
    return result


def trajectory_for_chart(parsed: dict, metric: str, sample_weeks: list[str]) -> dict:
    """Pull values at specific week labels for chart construction."""
    weekly = parsed['overview'].get(metric, {})
    return {
        'labels': sample_weeks,
        'values': [weekly.get(w) for w in sample_weeks],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tab', required=True, help='Path to Weekly Platform Overview 2.0 CSV')
    ap.add_argument('--start-week', default='5-Jan')
    ap.add_argument('--end-week', required=True)
    ap.add_argument('--chart-weeks', nargs='*', help='Week labels to sample for charts')
    ap.add_argument('--output', required=True)
    args = ap.parse_args()

    parsed = parse_tab(args.tab)
    result = compute_delta(parsed, args.start_week, args.end_week)

    if args.chart_weeks:
        result['charts'] = {
            'tmi_trajectory': trajectory_for_chart(parsed, 'Total Marketing Investment', args.chart_weeks),
            'roas_trajectory': trajectory_for_chart(parsed, 'Marketing ROAS', args.chart_weeks),
            'payout_trajectory': trajectory_for_chart(parsed, 'Net Payout', args.chart_weeks),
        }

    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {args.output}")
    for m in ('Total Sales', 'Net Payout', 'Total Marketing Investment', 'Marketing ROAS'):
        if m in result['overview_metrics']:
            r = result['overview_metrics'][m]
            print(f"  {m}: {r['start_val']:.0f} → {r['end_val']:.0f} ({r['delta_pct']:+.1f}%)")


if __name__ == '__main__':
    main()
