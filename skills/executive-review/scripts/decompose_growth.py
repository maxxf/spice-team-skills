#!/usr/bin/env python3
"""
Decompose same-store YoY growth into attributable buckets.

Reads the output of compute_yoy.py and produces an attribution breakdown:
- Spice-attributable: cannibalization fix + DD channel reallocation
- Joint: menu CVR + ratings work (when applicable)
- Brand momentum: residual organic growth on goop / client side

Approach:
1. Identify the dominant cannibalization signal (platform with negative ad spend % AND positive sales %)
2. Estimate cannibalization-attributable growth as the full delta on that platform
3. For the other platform (where spend grew), estimate marginal ROAS and attribute spend-driven growth
4. Residual = brand momentum

This is a defensible heuristic but not the only valid attribution. Outputs include all the
intermediate math so the reader can challenge the bucketing.

Usage:
    python decompose_growth.py --yoy-input yoy_output.json --output attribution.json
"""

import argparse
import json


def decompose(yoy: dict, marginal_roas_assumption: float = 6.0) -> dict:
    """Decompose YoY same-store growth into attribution buckets.

    Args:
        yoy: output dict from compute_yoy.py
        marginal_roas_assumption: assumed marginal ROAS on incremental ad spend.
            Default 6.0x is conservative. Adjust if client's true marginal is known.
    """
    t = yoy['totals']
    total_sales_delta = t['sales_current'] - t['sales_prior']

    ue_delta = t['ue_sales_current'] - t['ue_sales_prior']
    dd_delta = t['dd_sales_current'] - t['dd_sales_prior']
    ue_ad_delta = t['ue_ad_spend_current'] - t['ue_ad_spend_prior']
    dd_ad_delta = t['dd_ad_spend_current'] - t['dd_ad_spend_prior']

    # Identify cannibalization platform: sales up, ad spend down
    cannibal_platform = None
    cannibal_growth = 0
    if ue_delta > 0 and ue_ad_delta < 0:
        cannibal_platform = 'UE'
        cannibal_growth = ue_delta
    elif dd_delta > 0 and dd_ad_delta < 0:
        cannibal_platform = 'DD'
        cannibal_growth = dd_delta

    # The other platform: if ad spend grew, attribute marginal spend ROAS
    spend_driven_growth = 0
    other_platform = None
    if cannibal_platform == 'UE':
        other_platform = 'DD'
        if dd_ad_delta > 0:
            spend_driven_growth = min(dd_ad_delta * marginal_roas_assumption, dd_delta)
    elif cannibal_platform == 'DD':
        other_platform = 'UE'
        if ue_ad_delta > 0:
            spend_driven_growth = min(ue_ad_delta * marginal_roas_assumption, ue_delta)
    else:
        # No clean cannibalization signal: split spend-driven across both platforms
        total_ad_delta = max(0, ue_ad_delta + dd_ad_delta)
        spend_driven_growth = total_ad_delta * marginal_roas_assumption

    # Spice-attributable = cannibalization + spend reallocation
    spice_attributable = cannibal_growth + spend_driven_growth

    # Brand / momentum = residual
    brand_residual = total_sales_delta - spice_attributable
    # Cap at zero if math went weird
    if brand_residual < 0:
        brand_residual = 0

    return {
        'total_sales_delta': total_sales_delta,
        'ue_delta': ue_delta,
        'dd_delta': dd_delta,
        'ue_ad_spend_delta': ue_ad_delta,
        'dd_ad_spend_delta': dd_ad_delta,
        'cannibal_platform': cannibal_platform,
        'cannibal_growth': cannibal_growth,
        'other_platform': other_platform,
        'spend_driven_growth': spend_driven_growth,
        'marginal_roas_assumption': marginal_roas_assumption,
        'attribution': {
            'spice_marketing_strategy': spice_attributable,
            'spice_pct': spice_attributable / total_sales_delta * 100 if total_sales_delta else 0,
            'brand_momentum_residual': brand_residual,
            'brand_pct': brand_residual / total_sales_delta * 100 if total_sales_delta else 0,
        },
        'narrative_hint': _build_narrative(
            cannibal_platform, cannibal_growth, spend_driven_growth, brand_residual,
            ue_ad_delta, ue_delta, dd_ad_delta, dd_delta
        ),
    }


def _build_narrative(cp, cg, sdg, br, ue_ad, ue_s, dd_ad, dd_s) -> str:
    """Produce a one-paragraph narrative hint suitable for the §1 doc text."""
    parts = []
    if cp:
        pct_ad_cut = abs(ue_ad if cp == 'UE' else dd_ad)
        pct_sales_growth = (ue_s if cp == 'UE' else dd_s)
        parts.append(
            f"{cp} ad spend went down by ${pct_ad_cut:,.0f} but {cp} sales grew "
            f"by ${pct_sales_growth:,.0f}. That's the cannibalization fix signature."
        )
    if sdg > 0:
        parts.append(
            f"Other-platform spend reallocation likely drove "
            f"~${sdg:,.0f} of incremental sales."
        )
    if br > 0:
        parts.append(
            f"Residual ~${br:,.0f} attributable to brand momentum + organic flywheel."
        )
    return " ".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--yoy-input', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--marginal-roas', type=float, default=6.0,
                    help='Assumed marginal ROAS on incremental ad spend (default 6.0)')
    args = ap.parse_args()

    with open(args.yoy_input) as f:
        yoy = json.load(f)
    result = decompose(yoy, args.marginal_roas)
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"Attribution: {result['attribution']['spice_pct']:.0f}% Spice / "
          f"{result['attribution']['brand_pct']:.0f}% brand")
    print(result['narrative_hint'])


if __name__ == '__main__':
    main()
