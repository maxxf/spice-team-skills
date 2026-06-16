#!/usr/bin/env python3
"""
Extract struggling locations progress from canonical "By Location 2.0" and "Ops - Focus Locations" tabs.

Pulls per-location:
- Sales trajectory (W1 / W_n / peak in between)
- Net Payout trajectory
- Mkt Spend % trajectory
- ROAS trajectory
- Menu CVR (from Ops - Focus Locations if tracked)
- Ratings velocity (from Ops - Focus Locations if tracked)

Usage:
    python compute_struggling.py \\
        --by-location path/to/By_Location_2.0.csv \\
        --ops-focus path/to/Ops_Focus_Locations.csv \\
        --locations "San Jose" "Pasadena" \\
        --start-week 5-Jan --end-week 11-May \\
        --output struggling.json
"""

import argparse
import csv
import json
import re


def money(s: str) -> float | None:
    if not s or s.strip() in ('', '-', '$0', '--'):
        return None
    try:
        return float(re.sub(r'[$,%]', '', s.strip()))
    except ValueError:
        return None


def parse_by_location(path: str) -> dict:
    """Parse By Location 2.0 tab. Returns {store_name: {metric: {week: value}}}."""
    with open(path, 'r', encoding='utf-8') as f:
        rows = list(csv.reader(f))

    # Find header row
    header_idx = None
    for i, row in enumerate(rows):
        if row and any(re.match(r'\d{1,2}-[A-Z][a-z]{2}', c.strip()) for c in row if c):
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("Couldn't find week header row")
    week_labels = [c.strip() for c in rows[header_idx][2:] if c.strip()]

    locations = {}
    current_loc = None
    for row in rows[header_idx + 1:]:
        if not row or not row[0]:
            continue
        cell0 = row[0].strip()
        # Location header rows (just name, rest empty)
        if cell0 and not any(c.strip() for c in row[1:]):
            current_loc = cell0
            locations[current_loc] = {}
            continue
        # Metric rows
        if current_loc:
            metric = cell0
            values = {}
            for i, label in enumerate(week_labels):
                col_idx = 2 + i
                if col_idx < len(row):
                    v = money(row[col_idx])
                    if v is not None:
                        values[label] = v
            if values:
                locations[current_loc][metric] = values
    return {'week_labels': week_labels, 'locations': locations}


def parse_ops_focus(path: str) -> dict:
    """Parse Ops - Focus Locations tab. CVR + ratings + menu views per location per platform."""
    with open(path, 'r', encoding='utf-8') as f:
        rows = list(csv.reader(f))

    header_idx = None
    for i, row in enumerate(rows):
        if row and any(re.match(r'\d{1,2}-[A-Z][a-z]{2}', c.strip()) for c in row if c):
            header_idx = i
            break
    week_labels = [c.strip() for c in rows[header_idx][2:] if c.strip()]

    locations = {}
    current_loc = None
    for row in rows[header_idx + 1:]:
        if not row or not row[0]: continue
        cell0 = row[0].strip()
        if cell0.startswith(('LA - ', 'Bay - ', 'NYC - ', 'SoCal - ')) or (cell0 and not any(c.strip() for c in row[1:])):
            current_loc = cell0
            locations[current_loc] = {}
            continue
        if current_loc and row[1]:
            metric = row[1].strip()
            values = {}
            for i, label in enumerate(week_labels):
                col_idx = 2 + i
                if col_idx < len(row):
                    v = money(row[col_idx])
                    if v is not None:
                        values[label] = v
            if values:
                locations[current_loc][metric] = values
    return {'week_labels': week_labels, 'locations': locations}


def extract_struggling_progress(by_loc: dict, ops: dict, locations: list[str],
                                start_week: str, end_week: str) -> dict:
    """Build per-location progress summary."""
    result = {}
    for loc in locations:
        # Match loose: e.g., "San Jose" should match "San Jose" or "Bay - San Jose"
        loc_data = None
        for stored_name, data in by_loc['locations'].items():
            if loc.lower() in stored_name.lower():
                loc_data = data
                break

        ops_data = None
        for stored_name, data in ops['locations'].items():
            if loc.lower() in stored_name.lower():
                ops_data = data
                break

        if not loc_data:
            result[loc] = {'error': f'No By Location data found for {loc}'}
            continue

        # Pull trajectory for key metrics
        progress = {}
        for metric in ('Total Sales', 'Net Payout', 'Marketing Spend / Sales %', 'Marketing ROAS'):
            weekly = loc_data.get(metric, {})
            start_v = weekly.get(start_week)
            end_v = weekly.get(end_week)
            if start_v is not None and end_v is not None:
                peak = max(weekly.values()) if weekly else None
                peak_week = max(weekly, key=weekly.get) if weekly else None
                progress[metric] = {
                    'start': start_v,
                    'end': end_v,
                    'peak': peak,
                    'peak_week': peak_week,
                    'delta_pct': (end_v / start_v - 1) * 100 if start_v else None,
                }

        # CVR + ratings from ops tab if available
        if ops_data:
            for cvr_key in ('Uber - Conversion Rate %', 'Uber - Conversion Rate',
                           'DoorDash - Conversion Rate %'):
                if cvr_key in ops_data:
                    weekly = ops_data[cvr_key]
                    progress[cvr_key] = {
                        'start': weekly.get(start_week),
                        'end': weekly.get(end_week),
                        'recent_4wk_avg': sum(list(weekly.values())[-4:]) / 4 if len(weekly) >= 4 else None,
                    }
            for menu_key in ('Uber - Menu Views', 'DoorDash - Menu Views'):
                if menu_key in ops_data:
                    weekly = ops_data[menu_key]
                    progress[menu_key] = {
                        'recent_4wk_avg': sum(list(weekly.values())[-4:]) / 4 if len(weekly) >= 4 else None,
                    }
            for rating_key in ('Uber - Ratings count', 'DoorDash - Ratings count'):
                if rating_key in ops_data:
                    weekly = ops_data[rating_key]
                    early = list(weekly.values())[:4]
                    late = list(weekly.values())[-4:]
                    progress[rating_key] = {
                        'early_4wk_avg': sum(early) / len(early) if early else None,
                        'recent_4wk_avg': sum(late) / len(late) if late else None,
                    }

        result[loc] = progress
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--by-location', required=True)
    ap.add_argument('--ops-focus', help='Optional; skip if not tracking CVR/ratings')
    ap.add_argument('--locations', nargs='+', required=True)
    ap.add_argument('--start-week', default='5-Jan')
    ap.add_argument('--end-week', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()

    by_loc = parse_by_location(args.by_location)
    ops = parse_ops_focus(args.ops_focus) if args.ops_focus else {'locations': {}}

    result = extract_struggling_progress(by_loc, ops, args.locations,
                                         args.start_week, args.end_week)
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)

    for loc, data in result.items():
        print(f"\n{loc}:")
        for metric, info in data.items():
            if isinstance(info, dict) and 'start' in info:
                d = info.get('delta_pct')
                d_str = f"{d:+.1f}%" if d is not None else "n/a"
                print(f"  {metric}: {info['start']:.2f} → {info['end']:.2f} ({d_str})")


if __name__ == '__main__':
    main()
