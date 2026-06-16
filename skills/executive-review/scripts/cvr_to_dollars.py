#!/usr/bin/env python3
"""
Quantify menu CVR lift as annualized $ at current menu view volume.

Use case: client asks "what do those extra conversion rate points actually translate to in sales?"
This script answers it per location, per platform.

Inputs:
- Pre-change CVR baseline (decimal, e.g., 0.25 for 25%)
- Post-change CVR (decimal)
- Recent avg weekly menu views
- AOV

Output:
- Weekly $ lift
- Annualized $ lift (assumes 52 weeks of steady-state)

Usage:
    python cvr_to_dollars.py \\
        --location "Pasadena" --platform "UE" \\
        --pre 0.25 --post 0.34 \\
        --menu-views 1430 --aov 50

Or as a library:
    from cvr_to_dollars import compute_lift
    result = compute_lift(pre=0.25, post=0.34, menu_views=1430, aov=50)
"""

import argparse
import json


def compute_lift(pre: float, post: float, menu_views: float, aov: float) -> dict:
    """Compute weekly + annualized $ lift from CVR improvement.

    Args:
        pre: baseline CVR (decimal, e.g., 0.25)
        post: post-change CVR (decimal)
        menu_views: avg weekly menu views (last 4-6 weeks recommended)
        aov: avg order value ($)

    Returns dict with:
        - pre_pct, post_pct, lift_pts (in % terms for display)
        - orders_pre_per_wk, orders_post_per_wk, orders_lift_per_wk
        - sales_pre_per_wk, sales_post_per_wk, sales_lift_per_wk
        - sales_lift_annualized
    """
    lift_pts = (post - pre) * 100
    orders_pre = pre * menu_views
    orders_post = post * menu_views
    orders_lift = orders_post - orders_pre
    sales_pre = orders_pre * aov
    sales_post = orders_post * aov
    sales_lift = orders_lift * aov
    return {
        'pre_pct': pre * 100,
        'post_pct': post * 100,
        'lift_pts': lift_pts,
        'lift_relative_pct': (post/pre - 1) * 100 if pre else None,
        'orders_pre_per_wk': round(orders_pre, 1),
        'orders_post_per_wk': round(orders_post, 1),
        'orders_lift_per_wk': round(orders_lift, 1),
        'sales_pre_per_wk': round(sales_pre, 0),
        'sales_post_per_wk': round(sales_post, 0),
        'sales_lift_per_wk': round(sales_lift, 0),
        'sales_lift_annualized': round(sales_lift * 52, 0),
    }


def aggregate_lifts(lifts: list[dict]) -> dict:
    """Sum a list of compute_lift results into a portfolio total."""
    total_weekly = sum(l['sales_lift_per_wk'] for l in lifts)
    return {
        'count': len(lifts),
        'total_weekly_lift': total_weekly,
        'total_annualized_lift': total_weekly * 52,
        'details': lifts,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--location', required=True)
    ap.add_argument('--platform', required=True, choices=['UE', 'DD', 'GH'])
    ap.add_argument('--pre', type=float, required=True, help='Baseline CVR (decimal, e.g., 0.25)')
    ap.add_argument('--post', type=float, required=True, help='Post-change CVR (decimal)')
    ap.add_argument('--menu-views', type=float, required=True)
    ap.add_argument('--aov', type=float, required=True)
    ap.add_argument('--json', action='store_true', help='Output JSON only')
    args = ap.parse_args()

    result = compute_lift(args.pre, args.post, args.menu_views, args.aov)
    result['location'] = args.location
    result['platform'] = args.platform

    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(f"\n{args.location} {args.platform} CVR Lift:")
    print(f"  {result['pre_pct']:.0f}% → {result['post_pct']:.0f}% "
          f"(+{result['lift_pts']:.0f} pts, +{result['lift_relative_pct']:.0f}% relative)")
    print(f"  Menu views/wk: {args.menu_views:,.0f}")
    print(f"  AOV: ${args.aov:.2f}")
    print(f"  Order lift: +{result['orders_lift_per_wk']:.0f} orders/wk")
    print(f"  Sales lift: +${result['sales_lift_per_wk']:,.0f}/wk")
    print(f"  Annualized: ~${result['sales_lift_annualized']:,.0f}/yr")


if __name__ == '__main__':
    main()
