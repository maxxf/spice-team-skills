#!/usr/bin/env python3
"""
Compute YoY same-store comp using canonical Weekly Reporting Skill methodology.

Inputs:
- UE raw CSVs for current year + prior year (Mon-Sun windows)
- DD raw CSVs for current year + prior year (Mon-Sun windows)
- Optional GH raw CSVs

Methodology (per Weekly Reporting Skill):
- Total Sales = food subtotal EXCLUDING tax
- Net Sales = Total Sales − Discounts
- Net Payout = Net Sales − Commissions − Ad Spend − Other Adjustments

Same-store ex-closing handling:
- Identify stores active in BOTH prior-year window AND current-year window
- Exclude any store flagged as closing/winding-down via --exclude-stores flag

Output:
- JSON with per-store sales, payout, ad spend, discounts for both years
- Aggregate same-store ex-closing totals
- YoY % per store + aggregate

Usage:
    python compute_yoy.py \\
        --ue-prior path/to/ue-2025.csv \\
        --ue-current path/to/ue-2026.csv \\
        --dd-prior path/to/dd-2025.csv \\
        --dd-current path/to/dd-2026.csv \\
        --start-prior 2024-12-30 --end-prior 2025-05-18 \\
        --start-current 2025-12-29 --end-current 2026-05-17 \\
        --exclude-stores "beverly hills" \\
        --output yoy_output.json
"""

import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import datetime


def norm_store(s: str, store_map: dict | None = None) -> str:
    """Normalize store name. Pass a store_map for client-specific rules."""
    s = s.lower().strip()
    s = re.sub(r'^[a-z\s]+kitchen\s*\(', '', s)  # strip "goop kitchen ("
    s = s.rstrip(')').strip()
    if store_map:
        return store_map.get(s, s)
    # Common normalizations (override per client via --store-map JSON)
    if "north hollywood" in s or "studio city" in s:
        return "studio city / north hollywood"
    if "silver lake" in s:
        return "silver lake"
    if "beverly hills" in s:
        return "beverly hills"
    if "santa monica" in s:
        return "santa monica"
    if s == "robertson":
        return "pico-robertson"
    return s


def parse_ue(path: str, start: datetime, end: datetime, store_map: dict | None = None) -> dict:
    """Parse UE raw CSV. Returns per-store: sales_excl_tax, discounts, commission, ad_spend, other_adj."""
    sd = defaultdict(lambda: {
        'sales_excl_tax': 0.0, 'discounts': 0.0, 'commission': 0.0,
        'ad_spend': 0.0, 'mkt_fac_tax': 0.0, 'delivery_fee': 0.0,
        'processing_fee': 0.0, 'container_deposit': 0.0,
        'orders': 0,
    })
    with open(path, 'r', encoding='utf-8') as f:
        f.readline()  # skip descriptive header row
        for row in csv.DictReader(f):
            store = norm_store(row.get('Store Name', ''), store_map)
            od = row.get('Order Date', '').strip()
            try:
                m, d, y = od.split('/')
                y = int(y)
                if y < 100: y += 2000
                dt = datetime(y, int(m), int(d))
            except (ValueError, AttributeError):
                continue
            if not (start <= dt <= end):
                continue
            s = sd[store]
            try:
                if row.get('Order Status') == 'Completed':
                    s['sales_excl_tax'] += float(row.get('Sales (excl. tax)') or 0)
                    s['orders'] += 1
                    # Discounts (offers): strip tax portion to keep excl-tax basis
                    offers_incl = abs(float(row.get('Offers on items (incl. tax)') or 0))
                    tax_offers = abs(float(row.get('Tax On Offers on items') or 0))
                    s['discounts'] += max(0, offers_incl - tax_offers)
                s['commission'] += abs(float(row.get('Marketplace Fee') or 0))
                s['mkt_fac_tax'] += abs(float(row.get('Marketplace Facilitator Tax') or 0))
                s['delivery_fee'] += abs(float(row.get('Delivery Network Fee') or 0))
                s['processing_fee'] += abs(float(row.get('Order Processing Fee') or 0))
                s['container_deposit'] += abs(float(row.get('Container Deposit Fee') or 0))
                desc = (row.get('Other payments description', '') or '').strip()
                op = float(row.get('Other payments') or 0)
                if desc == 'Ad Spend':
                    s['ad_spend'] += abs(op)
            except (ValueError, KeyError):
                pass
    # Compute Other Adjustments per canonical (excl MFT: treated as pass-through)
    for store, s in sd.items():
        s['other_adj'] = s['delivery_fee'] + s['processing_fee'] + s['container_deposit']
        s['net_payout'] = (s['sales_excl_tax'] - s['discounts']
                          - s['commission'] - s['ad_spend'] - s['other_adj'])
    return dict(sd)


def parse_dd(path: str, store_map: dict | None = None) -> dict:
    """Parse DD raw CSV (already date-filtered by the export window)."""
    sd = defaultdict(lambda: {
        'sales_excl_tax': 0.0, 'discounts': 0.0, 'commission': 0.0,
        'ad_spend': 0.0, 'merchant_fees': 0.0, 'error_charges': 0.0,
        'adjustments': 0.0, 'orders': 0,
    })
    with open(path, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            store = norm_store(row.get('Store name', ''), store_map)
            s = sd[store]
            try:
                if row.get('Transaction type') == 'Order':
                    s['sales_excl_tax'] += float(row['Subtotal'])
                    s['orders'] += 1
                s['commission'] += abs(float(row.get('Commission') or 0))
                s['ad_spend'] += abs(float(row.get('Marketing fees') or 0))
                s['discounts'] += abs(float(row.get('Customer discounts') or 0))
                s['merchant_fees'] += abs(float(row.get('Merchant fees') or 0))
                s['error_charges'] += abs(float(row.get('Error charges') or 0))
                s['adjustments'] += float(row.get('Adjustments') or 0)
            except (ValueError, KeyError):
                pass
    for store, s in sd.items():
        s['other_adj'] = s['merchant_fees'] + s['error_charges'] - s['adjustments']
        s['net_payout'] = (s['sales_excl_tax'] - s['discounts']
                          - s['commission'] - s['ad_spend'] - s['other_adj'])
    return dict(sd)


def combine_platforms(ue: dict, dd: dict) -> dict:
    """Combine UE + DD per-store (and optionally GH later)."""
    stores = set(ue.keys()) | set(dd.keys())
    out = {}
    for s in stores:
        u = ue.get(s, {})
        d = dd.get(s, {})
        out[s] = {
            'sales': u.get('sales_excl_tax', 0) + d.get('sales_excl_tax', 0),
            'discounts': u.get('discounts', 0) + d.get('discounts', 0),
            'ad_spend': u.get('ad_spend', 0) + d.get('ad_spend', 0),
            'tmi': (u.get('discounts', 0) + d.get('discounts', 0)
                   + u.get('ad_spend', 0) + d.get('ad_spend', 0)),
            'payout': u.get('net_payout', 0) + d.get('net_payout', 0),
            'orders': u.get('orders', 0) + d.get('orders', 0),
            # Platform splits (useful for cannibalization story)
            'ue_sales': u.get('sales_excl_tax', 0),
            'ue_ad_spend': u.get('ad_spend', 0),
            'ue_payout': u.get('net_payout', 0),
            'dd_sales': d.get('sales_excl_tax', 0),
            'dd_ad_spend': d.get('ad_spend', 0),
            'dd_payout': d.get('net_payout', 0),
        }
    return out


def compute_yoy(prior: dict, current: dict, exclude: set[str]) -> dict:
    """Compute YoY same-store ex-excluded-stores."""
    same_stores = (set(prior.keys()) & set(current.keys())) - exclude
    rows = []
    totals = defaultdict(float)
    for s in same_stores:
        p, c = prior[s], current[s]
        delta = {
            'store': s,
            'sales_prior': p['sales'], 'sales_current': c['sales'],
            'sales_yoy_pct': (c['sales']/p['sales']-1)*100 if p['sales'] else None,
            'payout_prior': p['payout'], 'payout_current': c['payout'],
            'payout_yoy_pct': (c['payout']/p['payout']-1)*100 if p['payout'] else None,
            'ad_spend_prior': p['ad_spend'], 'ad_spend_current': c['ad_spend'],
            'ad_spend_yoy_pct': (c['ad_spend']/p['ad_spend']-1)*100 if p['ad_spend'] else None,
            'tmi_prior': p['tmi'], 'tmi_current': c['tmi'],
            'tmi_yoy_pct': (c['tmi']/p['tmi']-1)*100 if p['tmi'] else None,
        }
        rows.append(delta)
        for k in ['sales', 'payout', 'ad_spend', 'tmi', 'discounts',
                  'ue_sales', 'ue_ad_spend', 'ue_payout',
                  'dd_sales', 'dd_ad_spend', 'dd_payout']:
            totals[f'{k}_prior'] += p.get(k, 0)
            totals[f'{k}_current'] += c.get(k, 0)
    totals_pct = {}
    for k in ['sales', 'payout', 'ad_spend', 'tmi',
              'ue_sales', 'ue_ad_spend', 'ue_payout',
              'dd_sales', 'dd_ad_spend', 'dd_payout']:
        prior_v = totals[f'{k}_prior']
        cur_v = totals[f'{k}_current']
        totals_pct[f'{k}_yoy_pct'] = (cur_v/prior_v-1)*100 if prior_v else None
    return {
        'same_stores': sorted(same_stores),
        'excluded_stores': sorted(exclude),
        'per_store': rows,
        'totals': dict(totals),
        'totals_yoy_pct': totals_pct,
        'tmi_pct_prior': totals['tmi_prior']/totals['sales_prior']*100 if totals['sales_prior'] else None,
        'tmi_pct_current': totals['tmi_current']/totals['sales_current']*100 if totals['sales_current'] else None,
        'payout_pct_prior': totals['payout_prior']/totals['sales_prior']*100 if totals['sales_prior'] else None,
        'payout_pct_current': totals['payout_current']/totals['sales_current']*100 if totals['sales_current'] else None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ue-prior', required=True)
    ap.add_argument('--ue-current', required=True)
    ap.add_argument('--dd-prior', required=True)
    ap.add_argument('--dd-current', required=True)
    ap.add_argument('--start-prior', required=True, help='YYYY-MM-DD')
    ap.add_argument('--end-prior', required=True)
    ap.add_argument('--start-current', required=True)
    ap.add_argument('--end-current', required=True)
    ap.add_argument('--exclude-stores', nargs='*', default=[])
    ap.add_argument('--store-map', help='Optional JSON file with store name normalizations')
    ap.add_argument('--output', required=True)
    args = ap.parse_args()

    store_map = None
    if args.store_map:
        with open(args.store_map) as f:
            store_map = json.load(f)

    sp = datetime.fromisoformat(args.start_prior)
    ep = datetime.fromisoformat(args.end_prior)
    sc = datetime.fromisoformat(args.start_current)
    ec = datetime.fromisoformat(args.end_current)

    ue_p = parse_ue(args.ue_prior, sp, ep, store_map)
    ue_c = parse_ue(args.ue_current, sc, ec, store_map)
    dd_p = parse_dd(args.dd_prior, store_map)
    dd_c = parse_dd(args.dd_current, store_map)

    prior = combine_platforms(ue_p, dd_p)
    current = combine_platforms(ue_c, dd_c)

    exclude = {s.lower() for s in args.exclude_stores}
    result = compute_yoy(prior, current, exclude)
    result['period_prior'] = f"{args.start_prior} → {args.end_prior}"
    result['period_current'] = f"{args.start_current} → {args.end_current}"

    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {args.output}")
    print(f"Same-stores ex-excluded: {len(result['same_stores'])}")
    print(f"YoY Sales: {result['totals_yoy_pct']['sales_yoy_pct']:+.1f}%")
    print(f"YoY Payout: {result['totals_yoy_pct']['payout_yoy_pct']:+.1f}%")
    print(f"YoY Ad Spend: {result['totals_yoy_pct']['ad_spend_yoy_pct']:+.1f}%")


if __name__ == '__main__':
    main()
