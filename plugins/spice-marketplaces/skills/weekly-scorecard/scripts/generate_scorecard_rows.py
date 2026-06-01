#!/usr/bin/env python3
"""
Generate scorecard_rows.csv — the canonical long-format weekly metric rows
ready to paste into the Spice Weekly Scorecard Master Sheet's `data` tab.

This is the bridge between the existing weekly-reporting skill (which outputs
wide-format CSVs for the per-client tracker Sheets) and the new long-format
master Sheet that powers the live scorecard artifact and client-facing exports.

Inputs (already produced by the weekly-reporting skill):
  --platform-csv  path/to/platform_overview.csv
  --location-csv  path/to/by_location.csv
  --client        client_slug (e.g. fresh_kitchen)
  --week-start    YYYY-MM-DD (Monday)
  --week-end      YYYY-MM-DD (Sunday)
  --pulled-by     Reporter name (e.g. Manish)

Optional:
  --thresholds-csv  Path to a per-client thresholds CSV (overrides defaults)
                    Schema: metric,type,green,yellow,red
  --output          Output path. Defaults to ./scorecard_rows.csv

Output:
  scorecard_rows.csv with the canonical schema:
    client_slug, week_start, week_end, platform, location, metric,
    value, prior_value, status, source_file, pulled_at, pulled_by, notes

Status is computed at write time using the absolute thresholds in this file
(or per-client overrides via --thresholds-csv). Manish/Dulari paste the
output into the master Sheet data tab.

Last updated: 2026-04-30
"""

from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Mapping: weekly-reporting skill column names → canonical metric names
# ---------------------------------------------------------------------------
# The skill outputs platform_overview.csv with rows like:
#   Metric, Uber Eats, DoorDash, Grubhub, Blended, WoW (Blended), vs 4wk Avg
# We pivot these into one row per metric per platform.
#
# Skill row names that map directly to canonical metrics:
SKILL_TO_CANONICAL = {
    'Total Sales':           'total_sales',
    'Net Sales':             'net_sales',         # informational, not surfaced
    'Net Payout':            'net_payout',
    'Net Payout %':          'net_payout_pct',
    'Total Orders':          'order_count',
    'AOV':                   'aov',
    'Ad Spend':              'marketing_spend',   # rolled into context_only
    'Total Marketing Inv.':  'marketing_spend',   # alt naming
    'Mkt Spend %':           'marketing_spend_pct',
    'Marketing Spend / Sales %': 'marketing_spend_pct',
    'Marketing ROAS':        'roas',
    'ROAS':                  'roas',
    'Marketing Driven Sales':'marketing_driven_sales',  # used to compute organic_sales_pct
    'Organic Sales':         'organic_sales',            # used to compute organic_sales_pct
    'Marketing CPO':         'marketing_cpo',            # not surfaced in scorecard
    'Commissions %':         'commissions_pct',          # not surfaced
}

# Metrics we surface in the scorecard (must match metrics_meta in the master Sheet)
SCORECARD_METRICS = {
    'total_sales', 'net_payout', 'net_payout_pct', 'organic_sales_pct', 'aov',
    'marketing_spend', 'marketing_spend_pct', 'roas', 'order_count',
    'order_completion_rate', 'error_rate', 'cancel_rate', 'refund_rate',
    'downtime_hours', 'avg_rating', 'ratings_velocity', 'storefront_views',
    'menu_conversion', 'repeat_customer_pct'
}

# ---------------------------------------------------------------------------
# Default thresholds (mirror of master Sheet's thresholds_default tab).
# Override per-client via --thresholds-csv flag.
# ---------------------------------------------------------------------------
DEFAULT_THRESHOLDS = {
    # metric: (type, green, yellow, red, direction)
    'total_sales':           ('relative', 0,    -5,    -5,    'higher_better'),
    'net_payout':            ('relative', 0,    -5,    -5,    'higher_better'),
    'net_payout_pct':        ('absolute', 70,   60,    60,    'higher_better'),
    'organic_sales_pct':     ('absolute', 70,   50,    50,    'higher_better'),
    'aov':                   ('relative', -2,   -5,    -5,    'higher_better'),
    'marketing_spend':       ('context_only', None, None, None, 'context_only'),
    'marketing_spend_pct':   ('absolute', 15,   25,    25,    'lower_better'),
    'roas':                  ('absolute', 5.0,  3.0,   3.0,   'higher_better'),
    'order_count':           ('context_only', None, None, None, 'context_only'),
    'order_completion_rate': ('absolute', 97,   95,    95,    'higher_better'),
    'error_rate':            ('absolute', 1.5,  3.0,   3.0,   'lower_better'),
    'cancel_rate':           ('absolute', 1.5,  3.0,   3.0,   'lower_better'),
    'refund_rate':           ('absolute', 2.0,  4.0,   4.0,   'lower_better'),
    'downtime_hours':        ('absolute', 1.0,  4.0,   4.0,   'lower_better'),
    'avg_rating':            ('absolute', 4.7,  4.5,   4.5,   'higher_better'),
    'ratings_velocity':      ('relative', 0,    -20,   -20,   'higher_better'),
    'storefront_views':      ('relative', -5,   -15,   -15,   'higher_better'),
    'menu_conversion':       ('absolute', 12,   8,     8,     'higher_better'),
    'repeat_customer_pct':   ('context_only', None, None, None, 'context_only'),
}

PLATFORM_COLUMN_NAMES = {
    'Uber Eats': 'Uber Eats',
    'DoorDash':  'DoorDash',
    'Grubhub':   'Grubhub',
    'ALL':       'Blended',  # The skill uses "Blended" for the cross-platform roll-up
}


def parse_number(s):
    if s is None or s == '' or s == '--' or s.strip() == '':
        return None
    s = s.strip().replace('$', '').replace(',', '').replace('%', '').replace('x', '')
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def load_thresholds(path: Path | None):
    if not path or not path.exists():
        return DEFAULT_THRESHOLDS
    out = dict(DEFAULT_THRESHOLDS)
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            metric = r['metric'].strip()
            ttype = r['type'].strip()
            g = parse_number(r.get('green'))
            y = parse_number(r.get('yellow'))
            red = parse_number(r.get('red'))
            direction = DEFAULT_THRESHOLDS.get(metric, (None, None, None, None, 'higher_better'))[4]
            out[metric] = (ttype, g, y, red, direction)
    return out


def compute_status(metric, value, prior_value, thresholds):
    if value is None:
        return 'gray'
    if metric not in thresholds:
        return 'gray'
    ttype, g, y, red, direction = thresholds[metric]
    if ttype == 'context_only':
        return 'gray'
    if ttype == 'relative':
        if prior_value is None or prior_value == 0:
            return 'gray'
        target = (value - prior_value) / prior_value * 100
    else:  # absolute
        target = value
    if direction == 'higher_better':
        if target >= g:   return 'green'
        if target >= y:   return 'yellow'
        return 'red'
    else:  # lower_better
        if target <= g:   return 'green'
        if target <= y:   return 'yellow'
        return 'red'


def load_platform_overview(path: Path):
    """
    Returns a dict: { (metric, platform): {'value': float, 'prior': float} }
    The platform_overview.csv from the skill has rows like:
      Metric, Uber Eats, DoorDash, Grubhub, Blended, WoW (Blended), vs 4wk Avg
    """
    out = {}
    if not path.exists():
        return out
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Find prior-week column if present (some exports include "Last Week" column)
        for row in reader:
            metric_name = (row.get('Metric') or '').strip()
            if not metric_name or metric_name not in SKILL_TO_CANONICAL:
                continue
            canonical = SKILL_TO_CANONICAL[metric_name]
            for platform, col in PLATFORM_COLUMN_NAMES.items():
                value = parse_number(row.get(col))
                # Try common prior-week column naming conventions
                prior = (parse_number(row.get(f'{col} (Last Week)'))
                         or parse_number(row.get(f'{col} Prior'))
                         or parse_number(row.get(f'Last Week {col}')))
                # If skill uses WoW% only, derive prior from value × (1 - wow/100)
                if prior is None and value is not None:
                    wow = parse_number(row.get(f'WoW ({col})')) or parse_number(row.get('WoW (Blended)'))
                    if wow is not None:
                        try:
                            prior = value / (1 + wow / 100)
                        except ZeroDivisionError:
                            prior = None
                key = (canonical, platform)
                if value is not None or prior is not None:
                    out[key] = {'value': value, 'prior': prior}
    return out


def load_location_csv(path: Path):
    """
    Returns a list of dicts:
      [{'location': 'Miami', 'metric': 'total_sales', 'value': 31680, 'prior': 31200, 'platform': 'ALL'}, ...]
    The by_location.csv from the skill has one row per location with metric columns.
    """
    out = []
    if not path.exists():
        return out
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            location = (row.get('Location') or '').strip()
            if not location or location.upper() in ('PORTFOLIO', 'TOTAL', 'BLENDED'):
                continue
            for skill_name, canonical in SKILL_TO_CANONICAL.items():
                if canonical not in SCORECARD_METRICS:
                    continue
                value = parse_number(row.get(skill_name))
                # Prior columns may not exist at location level
                prior = (parse_number(row.get(f'{skill_name} (Last Week)'))
                         or parse_number(row.get(f'{skill_name} Prior')))
                if value is None and prior is None:
                    continue
                out.append({
                    'location': location,
                    'metric': canonical,
                    'value': value,
                    'prior': prior,
                    'platform': 'ALL',
                })
    return out


def derive_organic_sales_pct(platform_data):
    """Compute organic_sales_pct from marketing_driven_sales and total_sales."""
    out = {}
    for platform in PLATFORM_COLUMN_NAMES:
        ts = platform_data.get(('total_sales', platform))
        mds = platform_data.get(('marketing_driven_sales', platform))
        if ts and mds and ts.get('value') and mds.get('value') is not None and ts['value'] > 0:
            value = (1 - mds['value'] / ts['value']) * 100
            prior = None
            if ts.get('prior') and mds.get('prior') is not None and ts['prior'] > 0:
                prior = (1 - mds['prior'] / ts['prior']) * 100
            out[('organic_sales_pct', platform)] = {'value': value, 'prior': prior}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--platform-csv', required=True, type=Path, help='platform_overview.csv from weekly-reporting skill')
    ap.add_argument('--location-csv', type=Path, help='by_location.csv from weekly-reporting skill (optional)')
    ap.add_argument('--client',       required=True, help='client_slug (e.g. fresh_kitchen)')
    ap.add_argument('--week-start',   required=True, help='YYYY-MM-DD (Monday of the reporting week)')
    ap.add_argument('--week-end',     required=True, help='YYYY-MM-DD (Sunday of the reporting week)')
    ap.add_argument('--pulled-by',    required=True, help='Reporter name (Manish, Dulari, etc.)')
    ap.add_argument('--thresholds-csv', type=Path, help='Per-client thresholds override CSV')
    ap.add_argument('--source-file',  default='', help='Reference to the raw export file (audit trail)')
    ap.add_argument('--output',       type=Path, default=Path('scorecard_rows.csv'))
    ap.add_argument('--active-platforms', default='', help='Comma-separated active platforms (e.g. UE,DD). If set, suppresses rows for inactive platforms. Use canonical names: Uber Eats, DoorDash, Grubhub, ALL.')
    args = ap.parse_args()

    # Normalize platform aliases
    PLATFORM_ALIASES = {'UE': 'Uber Eats', 'DD': 'DoorDash', 'GH': 'Grubhub', 'ALL': 'ALL'}
    active = None
    if args.active_platforms:
        active = set()
        for p in args.active_platforms.split(','):
            p = p.strip()
            active.add(PLATFORM_ALIASES.get(p, p))
        active.add('ALL')  # ALL is always active

    thresholds = load_thresholds(args.thresholds_csv)
    pulled_at = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')

    # 1. Load platform-level data
    platform_data = load_platform_overview(args.platform_csv)
    platform_data.update(derive_organic_sales_pct(platform_data))

    # 2. Load per-location data
    location_data = load_location_csv(args.location_csv) if args.location_csv else []

    # 3. Write output
    rows = []
    for (metric, platform), values in platform_data.items():
        if metric not in SCORECARD_METRICS:
            continue
        if active is not None and platform not in active:
            continue
        v = values.get('value')
        p = values.get('prior')
        # Skip rows that are clearly inactive (zero with zero prior)
        if (v in (None, 0, 0.0)) and (p in (None, 0, 0.0)):
            continue
        status = compute_status(metric, values.get('value'), values.get('prior'), thresholds)
        rows.append({
            'client_slug': args.client,
            'week_start': args.week_start,
            'week_end': args.week_end,
            'platform': platform,
            'location': 'ALL',
            'metric': metric,
            'value': format_value(values.get('value')),
            'prior_value': format_value(values.get('prior')),
            'status': status,
            'source_file': args.source_file,
            'pulled_at': pulled_at,
            'pulled_by': args.pulled_by,
            'notes': '',
        })

    for entry in location_data:
        if entry['metric'] not in SCORECARD_METRICS:
            continue
        status = compute_status(entry['metric'], entry.get('value'), entry.get('prior'), thresholds)
        rows.append({
            'client_slug': args.client,
            'week_start': args.week_start,
            'week_end': args.week_end,
            'platform': entry['platform'],
            'location': entry['location'],
            'metric': entry['metric'],
            'value': format_value(entry.get('value')),
            'prior_value': format_value(entry.get('prior')),
            'status': status,
            'source_file': args.source_file,
            'pulled_at': pulled_at,
            'pulled_by': args.pulled_by,
            'notes': '',
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        'client_slug', 'week_start', 'week_end', 'platform', 'location', 'metric',
        'value', 'prior_value', 'status', 'source_file', 'pulled_at', 'pulled_by', 'notes'
    ]
    with open(args.output, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"Wrote {len(rows)} rows to {args.output}")
    print(f"Paste these into: Spice Weekly Scorecard Master → data tab → bottom of sheet")


def format_value(v):
    if v is None:
        return ''
    if isinstance(v, float):
        # Round to 2 decimals if not integer-like
        if v == int(v):
            return str(int(v))
        return f"{v:.2f}"
    return str(v)


if __name__ == '__main__':
    main()
