"""The cannibalization analytical engine. Five passes:

1. Per-location metrics (ROAS, payout %, marketing %, ops health) — inputs, not labels
2. Spend event detection (start / stop / step ≥30% sustained ≥3w)
3. Counterfactual baseline (comp-store + prior-year + seasonal, Bayesian blend)
4. Mix shift detection (organic share trajectory)
5. Routing recommendation (CONCENTRATE / HOLD / PULL_BACK_TO_NC_ONLY / CUT / FIX_OPS_FIRST)

The output per location is a cannibalization finding plus one routing action,
derived directly from the signals. There is no tier classification.

Reads unified.csv, emits analysis.json.

Full logic specified in references/analysis-framework.md. When in doubt about
a threshold or rule, that file is canonical.

Usage:
    python analyze.py --client <slug> --unified <path>/unified.csv --output <path>/analysis.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path

import numpy as np
import pandas as pd

# Thresholds — keep in sync with references/analysis-framework.md
OPS_MAX_CANCEL = 0.10
OPS_MIN_CVR = 0.25

# A location pays back well enough to be worth concentrating into when ROAS
# clears this and it's spending below the benchmark.
CONCENTRATE_MIN_ROAS = 8.0
# Saturation / pullback fires when a location is overspending (marketing % is
# this multiple of the benchmark or more) AND its ROAS is only mediocre. A
# location with strong ROAS is left alone even if it's above benchmark — strong
# returns earn the spend.
SATURATION_MARKETING_MULTIPLE = 1.5
SATURATION_MAX_ROAS = 4.0  # Spice's own hold gate (growth_store_spend_gating): a store
                           # clearing ROAS >= 4x is performing — don't pull it on saturation
                           # alone. Was 6.0, which contradicted the codified 4x gate.
# Gross over-spend safety net: spending this share of sales on marketing is
# unsustainable at ANY plausible ROAS (attributed sales can't exceed real sales,
# so 50%+ marketing can't pay back). Pull back regardless of mix data or ROAS
# reliability — catches the egregious store that would otherwise fall to a silent
# HOLD. Deliberately absolute (not a benchmark multiple) so it fires only on
# unambiguous waste, not on every above-benchmark store when ROAS is unreliable.
UNSUSTAINABLE_MARKETING_PCT = 0.50

# New-led spend override for the SOFT saturation rule only. The saturation rule
# assumes marginal marketing dollars are buying repeat customers who'd have
# ordered anyway. When a platform acquisition/audience signal shows most ad spend
# is targeting NEW customers, that premise is false — the spend is acquisition,
# not cannibalization, and first-window ROAS understates its value (a new customer
# reorders). So a store the saturation rule would pull back is HELD instead when:
#   ad-spend share to new customers >= NEW_LED_SPEND_THRESHOLD  AND  ROAS >= NEW_LED_HEALTHY_ROAS
# The ROAS floor stops it from excusing a genuinely bad store (sub-floor ROAS is
# too expensive even as pure acquisition). This ONLY touches the soft saturation
# heuristic — it never overrides a measured counterfactual (CUT / PULL_BACK from a
# detected cannibalization event) or the >=50% unsustainable-spend safety net.
# `new_customer_spend_share` is a per-run input (client config); the signal is
# typically portfolio-level intent, so it applies uniformly across locations —
# noted as directional in the output.
NEW_LED_SPEND_THRESHOLD = 0.60
NEW_LED_HEALTHY_ROAS = 2.5

# Spend-sanity ceiling. A real store rarely spends more than this share of sales
# on marketing — when it appears to, the first suspect is a GROSS spend figure
# that hasn't netted platform ad credits / co-funded promos (Uber, DoorDash and
# Grubhub all credit back ad spend and co-fund offers). Grabbing a gross "total ad
# spend" column instead of the net-of-credits column roughly doubles spend and
# halves ROAS. This flag forces a human to confirm the spend is net before the
# number ships. Data-source-agnostic: it keys off the resulting ratio, so it fires
# no matter which column mapping produced it. See references/data-collection-checklist.md.
SPEND_SANITY_CEILING = 0.60

EVENT_MIN_STEP_PCT = 0.30
EVENT_MIN_SUSTAIN_WEEKS = 3

COMP_WEIGHT = 0.60
PRIOR_YEAR_WEIGHT = 0.25
SEASONAL_WEIGHT = 0.15

CONFIDENCE_HIGH_MIN_COMPS = 5

# Marketing-as-percent-of-sales benchmark. A heuristic anchor for the
# concentrate / saturation rules, configurable per run via the client config.
DEFAULT_MKTG_BENCHMARK = 0.03


@dataclass
class LocationAnalysis:
    location_id: str
    location_name: str
    comp_set: str
    market: str
    roas: float | None
    roas_gross: float | None
    payout_pct: float | None
    marketing_pct: float | None
    cancel_rate: float | None
    menu_cvr: float | None
    ratings_velocity: float | None
    gross_sales_total: float
    spend_total: float
    spend_gross_total: float | None
    organic_share_start: float | None
    organic_share_end: float | None
    mix_shift_trajectory: str
    cannibalization_detected: bool = False
    spend_events: list[dict] = field(default_factory=list)
    cannibalized_spend: float = 0.0
    confidence: str = "low"
    action: str = "HOLD"
    projected_annual_swing_usd: float = 0.0
    rationale: str = ""
    campaign_plan: dict = field(default_factory=dict)
    data_flags: list = field(default_factory=list)


def load_unified(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["week_starting"])
    df["week_starting"] = pd.to_datetime(df["week_starting"]).dt.date

    # Double-dip guard (FALLBACK only). When the unified.csv is sourced from
    # canonical weekly-reporting metrics, attributed_sales = Marketing-Driven
    # Sales, which is already deduped at the order level (ad+offer on one order
    # counted once) — this cap is then a harmless no-op. The cap exists for the
    # cold-prospect fallback path where we parse raw platform exports: there, a
    # single order can be claimed by BOTH the ads console and the offers report,
    # so summed attributed_sales can exceed actual sales. Attribution is a subset
    # of real sales by definition, so cap it at gross. Keeps ROAS (and the
    # routing thresholds that read it) honest. The cannibalization finding itself
    # is built on the gross-sales counterfactual — ground truth, never
    # double-counted. Spend is correctly summed (ad + offer = two real costs).
    # See SKILL.md "Where the spend + attribution numbers come from".
    if "attributed_sales" in df.columns and "gross_sales" in df.columns:
        attr = pd.to_numeric(df["attributed_sales"], errors="coerce")
        gross = pd.to_numeric(df["gross_sales"], errors="coerce")
        df["attributed_sales"] = attr.where(attr <= gross, gross)

    return df


def aggregate_location(df_loc: pd.DataFrame) -> dict:
    gross = float(df_loc["gross_sales"].sum())
    payout = float(df_loc["net_payout"].sum())
    spend = float(df_loc["spend"].sum())
    attr = float(df_loc["attributed_sales"].sum())
    orders = float(df_loc["orders"].sum())

    # Optional gross marketing cost (BEFORE platform ad credits + co-funded offers).
    # When present, we report ROAS two ways: net (what the brand actually pays) and
    # gross (what it would be if the platform funded nothing). The gap makes the
    # brand's dependence on platform funding explicit. `spend` (net) stays the
    # routing input — routing decisions are about the brand's real dollars.
    spend_gross = (
        float(df_loc["spend_gross"].sum())
        if "spend_gross" in df_loc.columns and df_loc["spend_gross"].notna().any()
        else None
    )

    return {
        "gross_sales_total": gross,
        "net_payout_total": payout,
        "spend_total": spend,
        "spend_gross_total": spend_gross,
        "attributed_sales_total": attr,
        "orders_total": orders,
        "roas": (attr / spend) if spend > 0 else None,
        "roas_gross": (attr / spend_gross) if spend_gross and spend_gross > 0 else None,
        "payout_pct": (payout / gross) if gross > 0 else None,
        "marketing_pct": (spend / gross) if gross > 0 else None,
        "cancel_rate": float(df_loc["cancel_rate"].mean()) if df_loc["cancel_rate"].notna().any() else None,
        "menu_cvr": float(df_loc["menu_cvr"].mean()) if df_loc["menu_cvr"].notna().any() else None,
        "ratings_velocity": float(df_loc["new_reviews"].rolling(4, min_periods=1).mean().iloc[-1])
            if df_loc["new_reviews"].notna().any() else None,
    }


def detect_spend_events(df_loc: pd.DataFrame) -> list[dict]:
    """Find weeks where weekly spend changed materially and sustained for ≥3 weeks."""
    series = df_loc.set_index("week_starting")["spend"].fillna(0).sort_index()
    events = []
    if len(series) < EVENT_MIN_SUSTAIN_WEEKS * 2:
        return events

    rolling4 = series.rolling(4, min_periods=2).mean()

    for i in range(4, len(series) - EVENT_MIN_SUSTAIN_WEEKS):
        pre_avg = rolling4.iloc[i - 1]
        post_avg = series.iloc[i:i + EVENT_MIN_SUSTAIN_WEEKS].mean()

        if pre_avg == 0 and post_avg > 0:
            etype = "start"
        elif pre_avg > 0 and post_avg == 0:
            etype = "stop"
        elif pre_avg > 0 and abs(post_avg - pre_avg) / pre_avg >= EVENT_MIN_STEP_PCT:
            etype = "step_up" if post_avg > pre_avg else "step_down"
        else:
            continue

        magnitude = (post_avg - pre_avg) / pre_avg if pre_avg > 0 else float("inf")
        events.append({
            "event_type": etype,
            "event_week": str(series.index[i]),
            "pre_spend_avg": round(float(pre_avg), 2),
            "post_spend_avg": round(float(post_avg), 2),
            "magnitude_pct": round(float(magnitude * 100), 1) if math.isfinite(magnitude) else None,
        })

    # Deduplicate adjacent events of the same type (a sustained change shouldn't generate weekly events)
    deduped = []
    for e in events:
        if deduped and deduped[-1]["event_type"] == e["event_type"]:
            continue
        deduped.append(e)
    return deduped


def counterfactual_for_event(
    df_all: pd.DataFrame,
    loc_id: str,
    event: dict,
    comp_set: str,
    post_window_weeks: int = EVENT_MIN_SUSTAIN_WEEKS,
) -> dict:
    """Build expected post-sales using comp-store, prior-year, seasonal blend.

    post_window_weeks: how many weeks of post-event data to average. Short (3w)
    for step_up/start where incremental sales should appear fast. Longer (up to
    ~8w) for sustained step_down/stop events — short windows get fooled by
    seasonal noise on the immediate post-event weeks.
    """
    week = pd.to_datetime(event["event_week"]).date()
    df_loc = df_all[(df_all["location_id"] == loc_id) & (df_all["platform"] == "all")].copy()
    df_loc["week_starting"] = pd.to_datetime(df_loc["week_starting"]).dt.date
    df_loc = df_loc.sort_values("week_starting")

    pre = df_loc[df_loc["week_starting"] < week].tail(4)["gross_sales"].mean()
    post = df_loc[df_loc["week_starting"] >= week].head(post_window_weeks)["gross_sales"].mean()
    if pd.isna(pre) or pd.isna(post):
        return {"confidence": "low", "incremental_sales": None}

    # Comp-store baseline. A valid control is a same-comp-set location that did
    # NOT change its own spend in this window — otherwise it's in the treatment
    # too and can't tell us what "no change" would have looked like. When spend
    # is pulled across the whole portfolio at once, almost no clean comps exist,
    # so confidence should fall. We split comps into clean vs concurrent and
    # build the baseline from clean comps only.
    comps = df_all[
        (df_all["platform"] == "all")
        & (df_all["comp_set"] == comp_set)
        & (df_all["location_id"] != loc_id)
    ].copy()
    comps["week_starting"] = pd.to_datetime(comps["week_starting"]).dt.date

    total_comps = 0
    concurrent_comps = 0
    clean_growths: list[float] = []
    for _cloc, g in comps.groupby("location_id"):
        g = g.sort_values("week_starting")
        c_pre_sales = g[g["week_starting"] < week].tail(4)["gross_sales"].mean()
        c_post_sales = g[g["week_starting"] >= week].head(post_window_weeks)["gross_sales"].mean()
        if pd.isna(c_pre_sales) or c_pre_sales <= 0 or pd.isna(c_post_sales):
            continue
        total_comps += 1
        c_pre_spend = g[g["week_starting"] < week].tail(4)["spend"].mean()
        c_post_spend = g[g["week_starting"] >= week].head(post_window_weeks)["spend"].mean()
        # Did this comp also change its spend materially (a concurrent event)?
        if pd.isna(c_pre_spend) or c_pre_spend == 0:
            changed = (not pd.isna(c_post_spend)) and c_post_spend > 0
        else:
            changed = abs((c_post_spend - c_pre_spend) / c_pre_spend) >= EVENT_MIN_STEP_PCT
        if changed:
            concurrent_comps += 1
        else:
            clean_growths.append((c_post_sales - c_pre_sales) / c_pre_sales)

    clean_comp_count = len(clean_growths)
    if clean_comp_count >= 1:
        comp_growth_pct = sum(clean_growths) / clean_comp_count
        comp_baseline = pre * (1 + comp_growth_pct)
    else:
        comp_baseline = pre  # no clean control — assume flat (and confidence drops below)

    # v0: prior-year and seasonal are stubs equal to pre-period. Improve when real data is available.
    prior_year_baseline = pre
    seasonal_baseline = pre

    expected_post = (
        COMP_WEIGHT * comp_baseline
        + PRIOR_YEAR_WEIGHT * prior_year_baseline
        + SEASONAL_WEIGHT * seasonal_baseline
    )
    incremental = post - expected_post

    # Confidence is earned by CLEAN controls, not raw comp count. A portfolio-wide
    # simultaneous pull leaves few clean comps → confidence correctly falls.
    if clean_comp_count >= CONFIDENCE_HIGH_MIN_COMPS:
        confidence = "high"
    elif clean_comp_count >= 2:
        confidence = "medium"
    else:
        confidence = "low"

    concurrent_fraction = (concurrent_comps / total_comps) if total_comps else 0.0

    return {
        "expected_sales_post": round(float(expected_post), 2),
        "observed_sales_post": round(float(post), 2),
        "incremental_sales": round(float(incremental), 2),
        "confidence": confidence,
        "comp_count": int(total_comps),
        "clean_comp_count": int(clean_comp_count),
        "concurrent_comp_count": int(concurrent_comps),
        "concurrent_comp_fraction": round(float(concurrent_fraction), 2),
    }


def mix_shift(df_loc: pd.DataFrame) -> dict:
    df = df_loc.copy().sort_values("week_starting")
    df["org"] = df["organic_sales"].fillna(0)
    df["pd"] = df["paid_sales"].fillna(0)
    df["total"] = df["org"] + df["pd"]

    if df["total"].sum() == 0:
        return {"start": None, "end": None, "trajectory": "no_data"}

    start_window = df.head(4)
    end_window = df.tail(4)
    start_share = start_window["org"].sum() / start_window["total"].sum() if start_window["total"].sum() else None
    end_share = end_window["org"].sum() / end_window["total"].sum() if end_window["total"].sum() else None

    if start_share is None or end_share is None:
        return {"start": start_share, "end": end_share, "trajectory": "no_data"}

    delta = end_share - start_share
    sales_delta_pct = (
        (end_window["total"].sum() - start_window["total"].sum())
        / start_window["total"].sum()
        if start_window["total"].sum() > 0 else 0
    )

    if delta >= 0.05:
        traj = "organic_ascending"
    elif delta <= -0.05 and sales_delta_pct >= -0.05:
        traj = "organic_eroding_sales_holding"
    elif delta <= -0.05 and sales_delta_pct < -0.05:
        traj = "organic_eroding_sales_falling"
    else:
        traj = "stable"

    return {
        "start": round(float(start_share), 3),
        "end": round(float(end_share), 3),
        "trajectory": traj,
    }


def route(la: LocationAnalysis, mktg_benchmark: float,
          new_customer_spend_share: float | None = None) -> tuple[str, float, str]:
    """Return (action, projected_annual_swing_usd, rationale).

    Keys off the measured signals directly — ROAS, the cannibalization finding,
    mix-shift trajectory, and ops health. No tier label. Decision tree order
    matches references/analysis-framework.md Pass 5.
    """
    annualize = 52 / 26
    roas = la.roas
    mktg = la.marketing_pct or 0.0

    # 1. Ops broken — spend cannot fix a leaking funnel. The refusal is the point.
    ops_broken = (
        (la.cancel_rate is not None and la.cancel_rate > OPS_MAX_CANCEL)
        or (la.menu_cvr is not None and la.menu_cvr < OPS_MIN_CVR)
    )
    if ops_broken:
        return (
            "FIX_OPS_FIRST",
            0.0,
            "Operations are leaking — cancel rate or menu conversion is below the "
            "threshold where spend earns back. Pause incremental spend until cancel "
            "rate ≤ 8% and menu CVR ≥ 30%. More spend here just funds the leak faster.",
        )

    # 2. Cannibalization detected AND organic carrying the location — cut entirely.
    if la.cannibalization_detected and la.mix_shift_trajectory == "organic_ascending":
        annualized_savings = la.spend_total * annualize if la.spend_total > 0 else 0.0
        return (
            "CUT",
            annualized_savings,
            f"Organic share rose from {(la.organic_share_start or 0)*100:.0f}% → "
            f"{(la.organic_share_end or 0)*100:.0f}% while paid spend showed no incremental "
            f"sales in the counterfactual. The spend is taxing customers that arrived organically.",
        )

    # 3. Cannibalization detected — pull back to a minimal new-customer layer.
    if la.cannibalization_detected:
        annualized_pullback = la.spend_total * annualize * 0.5
        return (
            "PULL_BACK_TO_NC_ONLY",
            annualized_pullback,
            "Spend showed no incremental sales in the counterfactual. Cut repeat-customer "
            "targeting; keep a minimal new-customer-acquisition layer to defend the top of funnel.",
        )

    # 3.5 Gross over-spend safety net. Spending ≥50% of sales on marketing can't
    #     pay back at any plausible ROAS — pull back regardless of mix data, ROAS
    #     reliability, or a detected spend event. Sits above the mix-based rules so
    #     an over-marketed store can never fall to a HOLD. Absolute threshold:
    #     fires only on unambiguous waste.
    if mktg >= UNSUSTAINABLE_MARKETING_PCT:
        annualized_pullback = la.spend_total * annualize * 0.5
        return (
            "PULL_BACK_TO_NC_ONLY",
            annualized_pullback,
            f"Marketing is {mktg*100:.0f}% of sales — no ROAS justifies spending half your "
            f"top line on marketing. Pull back hard to a new-customer core and re-test.",
        )

    # 4. High ROAS and under-invested — concentrate toward the benchmark.
    if roas is not None and roas >= CONCENTRATE_MIN_ROAS and mktg < mktg_benchmark:
        spend_lift = (mktg_benchmark - mktg) * la.gross_sales_total
        projected_incremental = spend_lift * roas * (la.payout_pct or 0.75)
        annualized = projected_incremental * annualize
        return (
            "CONCENTRATE",
            annualized,
            f"{roas:.1f}x ROAS at only {mktg*100:.2f}% of sales — this location pays back well "
            f"and is starved. Lifting marketing toward {mktg_benchmark*100:.0f}% projects "
            f"+${annualized:,.0f} annualized in net payout.",
        )

    # 5. Organic eroding but sales holding — paid is defending. Hold.
    if la.mix_shift_trajectory == "organic_eroding_sales_holding":
        return (
            "HOLD",
            0.0,
            "Organic share is eroding but sales are holding — paid is offsetting the natural "
            "decay. Pulling back risks exposing the underlying decline. Hold and investigate "
            "the organic side.",
        )

    # 6. Saturated — overspending well above benchmark at only mediocre ROAS,
    #    with organic not falling. Strong-ROAS locations are left alone here.
    if (
        mktg >= mktg_benchmark * SATURATION_MARKETING_MULTIPLE
        and roas is not None and roas < SATURATION_MAX_ROAS
        and la.mix_shift_trajectory in ("stable", "organic_ascending")
    ):
        # New-led override: if the acquisition signal shows spend is going to new
        # customers (not recycling to repeats), the saturation premise is wrong —
        # this is acquisition, and first-window ROAS understates it. Hold instead,
        # provided ROAS clears the acquisition floor (below it, too expensive even
        # for pure acquisition). Only softens THIS rule; measured cannibalization
        # (rules 2/3) and the >=50% safety net (3.5) already fired above.
        if (
            new_customer_spend_share is not None
            and new_customer_spend_share >= NEW_LED_SPEND_THRESHOLD
            and roas >= NEW_LED_HEALTHY_ROAS
        ):
            return (
                "HOLD",
                0.0,
                f"Spending {mktg*100:.1f}% of sales at {roas:.1f}x ROAS looks saturated, but "
                f"{new_customer_spend_share*100:.0f}% of ad spend targets new customers — this is "
                f"acquisition, not repeat-customer cannibalization, and first-window ROAS understates "
                f"the value of a customer who reorders. Hold and watch retention. "
                f"(New-led signal is portfolio-level intent — directional.)",
            )
        annualized_pullback = la.spend_total * annualize * 0.3
        return (
            "PULL_BACK_TO_NC_ONLY",
            annualized_pullback,
            f"Spending {mktg*100:.1f}% of sales at only {roas:.1f}x ROAS with organic share holding "
            f"— a high rate of spend at a return this thin means marginal dollars are buying repeat "
            f"customers you'd likely have kept anyway. Shift to new-customer-only targeting.",
        )

    # 7. Otherwise — spend is paying back, no clear signal to change. Downgrade to a
    #    PROVISIONAL hold only when a flag actually limits routing (mix missing or
    #    ROAS unreliable). "No spend events" is NOT limiting — signal-based routing
    #    still works without a counterfactual — so a store with a clean mix signal
    #    and healthy ROAS stays a confident hold even though it had no spend event.
    routing_limited = any(
        ("organic/paid split missing" in fl) or ("ROAS implausibly low" in fl)
        for fl in la.data_flags
    )
    if routing_limited:
        return (
            "HOLD",
            0.0,
            "Provisional hold — spend looks like it's paying back, but a key input is missing "
            "(organic/paid split or reliable attribution), so healthy acquisition can't be fully "
            "separated from cannibalization here. See data flags.",
        )
    return ("HOLD", 0.0, "Spend is paying back and no mix-shift or cannibalization signal fired. No change recommended.")


# Platform reminders attached to every location's plan. Grounded in the canonical
# segmentation playbook (ad_segmentation_practice, uber_ads_targeting,
# dd_no_creative_tests). Keep these in sync with those references.
_PLATFORM_NOTES = [
    "UE: full audience targeting — separate new-to-brand (true acquisition) from "
    "new-to-location (cross-store capture); creative A/B tests are UE-only.",
    "DD: run offers / Sponsored Listings straight — no creative tests; the lapsed "
    "audience is labeled 'Low-Frequency Customers'.",
    "GH: Sponsored Listings + promotions; audience targeting is coarser than UE.",
]


def campaign_moves(la: LocationAnalysis) -> dict:
    """Pass 6 — map a routing action to concrete campaign moves.

    Grounded in Spice's canonical practice, not invented per run:
    - Non-new stores segment Ads by audience (New + Lapsed), per-segment caps,
      default New-led ~70/30 — never a single 'Ads · All' line.
    - New-to-brand = true acquisition; Lapsed = capped win-back harvest.
    - DoorDash runs offers/SL straight — no creative tests (UE only).
    - Growth stores are performance-gated: hold spend while ROAS ≥ ~4x; don't
      mechanically cap a delivering store to the 3% ratio.
    """
    action = la.action
    if action == "FIX_OPS_FIRST":
        return {
            "audience": "none — paid paused",
            "offers": "paused",
            "moves": [
                "Pause ALL paid (Sponsored Listings + offers) on every platform.",
                "Do not resume until cancel rate ≤ 8% and menu CVR ≥ 30%.",
                "Spend into a leaking funnel just funds the leak — fix ops first, then "
                "re-enter with a new-customer-only acquisition layer.",
            ],
            "platform_notes": _PLATFORM_NOTES,
        }
    if action == "CUT":
        return {
            "audience": "none — stop the cannibalized spend",
            "offers": "kill broad (All) + repeat-customer offers",
            "moves": [
                "Pause Sponsored Listings across UE / DD / GH — the counterfactual shows "
                "this spend produced no incremental sales.",
                "Kill broad (All-audience) and repeat-customer offers; keep the storefront "
                "running organically.",
                "Watch organic share for 2–3 weeks. If it dips, the spend was doing more "
                "than the data showed — re-enter at new-to-brand-only, not All.",
            ],
            "platform_notes": _PLATFORM_NOTES,
        }
    if action == "PULL_BACK_TO_NC_ONLY":
        return {
            "audience": "new-to-brand only (+ optional capped Lapsed win-back)",
            "offers": "first-order acquisition + capped lapsed win-back",
            "moves": [
                "Re-target Sponsored Listings to new-to-brand customers only — drop the "
                "All / Existing lines (that's the cannibalized layer buying repeats).",
                "Keep a small Lapsed win-back line if the pool supports it (DD: "
                "'Low-Frequency Customers').",
                "Swap any broad offer for a first-order acquisition offer; add a capped "
                "$5/$25 → Lapsed win-back.",
                "Reduce total paid budget — you're defending acquisition, not buying repeats.",
            ],
            "platform_notes": _PLATFORM_NOTES,
        }
    if action == "CONCENTRATE":
        return {
            "audience": "New-led ~70/30 (New + Lapsed), per-segment caps",
            "offers": "new-customer acquisition + optional Spend×Save",
            "moves": [
                "Raise Sponsored Listings budget — this location pays back and is starved.",
                "Segment Ads New ~70 / Lapsed ~30 on separate lines with their own caps — "
                "never a single 'Ads · All' line.",
                "Add or raise a new-customer acquisition offer; consider a Spend×Save "
                "threshold to lift AOV.",
                "Hold/grow spend while ROAS ≥ ~4x — performance-gated. Don't mechanically "
                "cap a delivering store to the 3% ratio.",
            ],
            "platform_notes": _PLATFORM_NOTES,
        }
    # HOLD
    return {
        "audience": "maintain — ensure Ads are segmented New + Lapsed",
        "offers": "maintain",
        "moves": [
            "Maintain the current mix; no spend change.",
            "If this non-new store is still on a single 'Ads · All' line, split it New + "
            "Lapsed with per-segment caps (standing practice — lets you read and cap each).",
        ],
        "platform_notes": _PLATFORM_NOTES,
    }


def analyze(unified_path: Path, client_slug: str, skill_dir: Path) -> dict:
    df = load_unified(unified_path)
    df_all = df[df["platform"] == "all"].copy()

    config_path = skill_dir / "clients" / f"{client_slug}.json"
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    mktg_benchmark = float(config.get("marketing_pct_benchmark", DEFAULT_MKTG_BENCHMARK))
    new_customer_spend_share = config.get("new_customer_spend_share")
    if new_customer_spend_share is not None:
        new_customer_spend_share = float(new_customer_spend_share)

    results: list[LocationAnalysis] = []
    for loc_id, df_loc in df_all.groupby("location_id"):
        df_loc = df_loc.sort_values("week_starting").reset_index(drop=True)
        agg = aggregate_location(df_loc)
        events = detect_spend_events(df_loc)

        # How long each event sustained: from its week to the next event's week,
        # or to the end of the data window if it's the last event. This matters
        # for two things: (1) for step_down/stop events the counterfactual needs
        # a long enough post-window to look past seasonal noise, and (2) the
        # cannibalization sum should reflect the actual sustained period.
        event_weeks = [pd.to_datetime(e["event_week"]).date() for e in events]
        last_data_week = df_loc["week_starting"].max()
        if isinstance(last_data_week, pd.Timestamp):
            last_data_week = last_data_week.date()

        counterfactuals = []
        cannibalized = 0.0
        cannibalization_detected = False
        for i, ev in enumerate(events):
            ev_week = event_weeks[i]
            next_week = event_weeks[i + 1] if i + 1 < len(events) else last_data_week
            duration_weeks = max(1, (next_week - ev_week).days // 7)

            etype = ev["event_type"]
            # Step_up / start: 3-week look — incremental should appear fast.
            # Step_down / stop: up to 8 weeks — short windows get fooled by
            # immediate seasonal noise on the post-cut weeks.
            post_window = EVENT_MIN_SUSTAIN_WEEKS if etype in ("step_up", "start") else min(8, duration_weeks)

            cf = counterfactual_for_event(
                df_all, loc_id, ev, df_loc["comp_set"].iloc[0],
                post_window_weeks=post_window,
            )
            ev["counterfactual"] = cf
            ev["sustained_weeks"] = duration_weeks
            incr = cf.get("incremental_sales")
            if incr is None:
                counterfactuals.append(ev)
                continue

            if etype in ("step_up", "start"):
                # Spend went UP. If it bought no incremental sales, that added
                # spend was cannibalized.
                if incr <= 0 and cf["confidence"] in ("high", "medium"):
                    cannibalization_detected = True
                    event_spend = df_loc[df_loc["week_starting"] >= ev_week].head(EVENT_MIN_SUSTAIN_WEEKS)["spend"].sum()
                    cannibalized += float(event_spend)
                    cf["finding"] = "added spend produced no incremental sales"
            else:
                # Spend went DOWN (step_down / stop). If sales HELD (observed is
                # at or above the counterfactual within a small tolerance), the
                # removed spend was cannibalized — the cut was free. This is the
                # Goop / Ahipoki shape: cut spend, sales didn't move.
                expected = cf.get("expected_sales_post")
                observed = cf.get("observed_sales_post")
                held = (
                    expected is not None and observed is not None
                    and expected > 0 and observed >= expected * 0.97
                )
                # A sustained cut where you watched sales hold IS the natural
                # experiment — strong evidence even without a large comp set.
                # Promote a clear hold to at least medium confidence.
                cut_conf = cf["confidence"]
                if held and cut_conf == "low":
                    cut_conf = "medium"
                    cf["confidence"] = cut_conf
                if held and cut_conf in ("high", "medium"):
                    cannibalization_detected = True
                    removed_per_wk = max(0.0, ev["pre_spend_avg"] - ev["post_spend_avg"])
                    # Real savings = removed/wk × the weeks the cut actually sustained.
                    cannibalized += removed_per_wk * duration_weeks
                    cf["finding"] = (
                        f"spend was cut and sales held for {duration_weeks}w — the removed "
                        f"spend was cannibalized"
                    )
            counterfactuals.append(ev)

        mix = mix_shift(df_loc)

        la = LocationAnalysis(
            location_id=loc_id,
            location_name=df_loc["location_name"].iloc[0] if "location_name" in df_loc.columns else loc_id,
            comp_set=df_loc["comp_set"].iloc[0] if "comp_set" in df_loc.columns else "default",
            market=df_loc["market"].iloc[0] if "market" in df_loc.columns else "unknown",
            roas=agg.get("roas"),
            roas_gross=agg.get("roas_gross"),
            payout_pct=agg.get("payout_pct"),
            marketing_pct=agg.get("marketing_pct"),
            cancel_rate=agg.get("cancel_rate"),
            menu_cvr=agg.get("menu_cvr"),
            ratings_velocity=agg.get("ratings_velocity"),
            gross_sales_total=agg["gross_sales_total"],
            spend_total=agg["spend_total"],
            spend_gross_total=agg.get("spend_gross_total"),
            organic_share_start=mix["start"],
            organic_share_end=mix["end"],
            mix_shift_trajectory=mix["trajectory"],
            cannibalization_detected=cannibalization_detected,
            spend_events=counterfactuals,
            cannibalized_spend=round(cannibalized, 2),
        )

        # Completeness gate — surface what's missing so a call is never made on
        # silent gaps. These don't block routing, but they qualify the confidence.
        flags: list[str] = []
        if mix["trajectory"] == "no_data":
            flags.append("organic/paid split missing — mix-shift signals unavailable")
        if not counterfactuals:
            flags.append("no material spend-change events in window — no natural experiment to measure")
        roas_v = agg.get("roas")
        # Attribution looks partial when ROAS is implausibly low against real spend
        # (e.g. attributed_sales only carries one ad product). Flag it so ROAS-based
        # routing isn't trusted blindly.
        if roas_v is not None and roas_v < 1.0 and (agg.get("marketing_pct") or 0) > 0.05:
            flags.append("ROAS implausibly low — attributed_sales likely partial; treat ROAS as unreliable")
        # Spend-sanity: marketing % above the ceiling almost always means spend is
        # GROSS (platform ad credits / co-funded promos not netted out). Flag loudly
        # for human verification — this is the guard that catches the gross-not-net
        # error before the number ships.
        mktg_pct_v = agg.get("marketing_pct") or 0
        if mktg_pct_v > SPEND_SANITY_CEILING:
            flags.append(
                f"marketing is {mktg_pct_v*100:.0f}% of sales — VERIFY spend is NET of platform "
                f"ad credits and co-funded promos (Uber/DD/GH all credit ad spend). A gross figure "
                f"roughly doubles spend and halves ROAS. Confirm before sharing."
            )
        la.data_flags = flags

        action, swing, rationale = route(la, mktg_benchmark, new_customer_spend_share)
        la.action = action
        la.projected_annual_swing_usd = round(swing, 2)
        la.rationale = rationale
        la.campaign_plan = campaign_moves(la)  # Pass 6 — concrete campaign moves

        # Confidence: high if at least one high-conf event OR comp set ≥ 5
        conf = "low"
        for ev in counterfactuals:
            c = ev["counterfactual"].get("confidence", "low")
            if c == "high":
                conf = "high"
                break
            if c == "medium" and conf == "low":
                conf = "medium"
        la.confidence = conf

        results.append(la)

    # Portfolio aggregates
    total_spend = sum(r.spend_total for r in results)
    total_attr = sum((r.roas * r.spend_total) for r in results if r.roas)  # ≈ attributed sales
    _gross_costs = [r.spend_gross_total for r in results if r.spend_gross_total is not None]
    total_spend_gross = sum(_gross_costs) if _gross_costs else None
    total_gross = sum(r.gross_sales_total for r in results)
    total_cannibalized = sum(r.cannibalized_spend for r in results)
    total_projected_swing = sum(r.projected_annual_swing_usd for r in results)

    annualize = 52 / 26
    cannibalized_annual = total_cannibalized * annualize
    cannibalized_low = cannibalized_annual * 0.80
    cannibalized_high = cannibalized_annual * 1.20

    # Action distribution (replaces the tier distribution)
    action_counts: dict = {}
    action_spend: dict = {}
    for r in results:
        action_counts[r.action] = action_counts.get(r.action, 0) + 1
        action_spend[r.action] = action_spend.get(r.action, 0) + r.spend_total

    # Portfolio-level completeness — what's missing across the whole run, so the
    # deliverable leads with data caveats instead of hiding them.
    n = len(results) or 1
    completeness: list[str] = []
    n_no_mix = sum(1 for r in results if "organic/paid split missing" in " ".join(r.data_flags))
    n_no_events = sum(1 for r in results if "no material spend-change events" in " ".join(r.data_flags))
    n_bad_roas = sum(1 for r in results if "ROAS implausibly low" in " ".join(r.data_flags))
    n_spend_sanity = sum(1 for r in results if "VERIFY spend is NET" in " ".join(r.data_flags))
    if n_no_mix >= n * 0.5:
        completeness.append(f"Organic/paid split missing for {n_no_mix}/{n} locations — mix-shift analysis unavailable; routing leaned on spend ratio + counterfactual only.")
    if n_no_events >= n * 0.5:
        completeness.append(f"No material spend-change events for {n_no_events}/{n} locations — spend was steady, so the natural-experiment counterfactual had little to measure. A cannibalization read needs spend movement.")
    if n_bad_roas >= 1:
        completeness.append(f"ROAS unreliable for {n_bad_roas} location(s) — attributed_sales looks partial (e.g. advanced-ads only). Treat ROAS as directional, not a routing input.")
    if n_spend_sanity >= 1:
        completeness.append(f"⚠ SPEND SANITY: {n_spend_sanity} location(s) above 60% marketing — VERIFY ad spend is NET of platform ad credits and co-funded promos before sharing. A gross figure roughly doubles spend and halves ROAS. This is the most common data error in this audit.")

    output = {
        "client": client_slug,
        "portfolio": {
            "location_count": len(results),
            "total_gross_sales": round(total_gross, 2),
            "total_spend": round(total_spend, 2),
            "total_spend_gross": round(total_spend_gross, 2) if total_spend_gross is not None else None,
            "portfolio_marketing_pct": round(total_spend / total_gross, 4) if total_gross > 0 else None,
            "portfolio_marketing_pct_gross": round(total_spend_gross / total_gross, 4) if (total_spend_gross and total_gross > 0) else None,
            "portfolio_roas_net": round(total_attr / total_spend, 2) if total_spend > 0 else None,
            "portfolio_roas_gross": round(total_attr / total_spend_gross, 2) if (total_spend_gross and total_spend_gross > 0) else None,
            "marketing_pct_benchmark": mktg_benchmark,
            "cannibalized_spend_window": round(total_cannibalized, 2),
            "cannibalized_spend_annualized_low": round(cannibalized_low, 2),
            "cannibalized_spend_annualized_high": round(cannibalized_high, 2),
            "projected_net_payout_lift_annualized": round(total_projected_swing, 2),
            "action_counts": action_counts,
            "action_spend": {k: round(v, 2) for k, v in action_spend.items()},
            "completeness_flags": completeness,
        },
        "locations": [asdict(r) for r in sorted(
            results, key=lambda r: -r.projected_annual_swing_usd
        )],
    }
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", required=True)
    parser.add_argument("--unified", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parent.parent
    result = analyze(args.unified, args.client, skill_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str))

    p = result["portfolio"]
    print(f"Audit complete: {args.output}")
    print(f"  Locations: {p['location_count']}")
    print(f"  Action distribution: {p['action_counts']}")
    print(f"  Cannibalized (annualized, range): "
          f"${p['cannibalized_spend_annualized_low']:,.0f} – ${p['cannibalized_spend_annualized_high']:,.0f}")
    print(f"  Projected net payout lift if all recommendations adopted: "
          f"${p['projected_net_payout_lift_annualized']:,.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
