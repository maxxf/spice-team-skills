# Cannibalization Analysis Framework

The codified playbook. This document is the authoritative source for the analysis rules — `scripts/analyze.py` reads from here.

The tool answers one question per location: **how much of the 3P marketing spend bought sales the restaurant would have gotten anyway, and what should they do about it?** The output is a cannibalization finding plus a routing action. There is no tier taxonomy — the action falls directly out of the signals.

## The analytical passes

### Pass 1 — Per-location metrics

For each location, compute aggregate metrics over the audit window (default 26 weeks):

- `roas` = attributed_sales / spend (where spend > 0; else N/A)
- `payout_pct` = net_payout / gross_sales
- `marketing_pct` = spend / gross_sales
- `cancel_rate` = canceled_orders / total_orders
- `menu_cvr` = orders / menu_views
- `ratings_velocity` = new_reviews_per_week (trailing 8 weeks)

These are inputs to the routing decision — not a classification. No labels are assigned.

### Pass 2 — Spend event detection

For each location, scan the weekly spend series. Flag a **spend event** when:

- **Material step change:** weekly spend changes by ≥30% from a 4-week trailing average, sustained for ≥3 consecutive weeks
- **Start event:** spend goes from $0 to >$0 for ≥3 consecutive weeks
- **Stop event:** spend goes from >$0 to $0 for ≥3 consecutive weeks

Each event is a natural experiment for the counterfactual. Tag each with event type, week, pre/post spend average, and magnitude.

### Pass 3 — Counterfactual baseline (the core of the tool)

For each spend event, build an expected-sales baseline using three signals (weighted by data availability):

1. **Comp-store baseline (primary, weight 0.6 when comp set ≥ 5)** — locations in the same comp set that did NOT run the same spend change in the same window. Their sales trajectory pre→post is the comp signal.
2. **Prior-year same-week (weight 0.25 when available)** — same location, same calendar week, one year earlier. Adjusted for known structural events.
3. **Seasonal trend (weight 0.15)** — the brand-wide week-over-week sales pattern, applied to the location.

Combine via Bayesian average:

```
expected_sales_post = (0.6 × comp_baseline) + (0.25 × prior_year) + (0.15 × seasonal_trend)
incremental_sales = observed_sales_post − expected_sales_post
effective_CAC = spend_post / incremental_sales   (negative or N/A if incremental ≤ 0)
```

**Confidence band:**
- **High** (90%): comp set ≥ 5 AND prior-year data present
- **Medium** (70%): one of those holds
- **Low** (<70%): suppress this event's contribution to per-location callouts; surface in methodology only

If `incremental_sales ≤ 0` with confidence ≥ medium: that spend bought nothing. Add to cannibalized_spend total.

### Pass 4 — Mix shift detection

For each location, compute trailing 4-week organic share over the window:

```
organic_share_t = organic_sales_t / (organic_sales_t + paid_sales_t)
```

Classify the trajectory:

| Trajectory | Δ organic share over window | Sales trajectory | Implication |
|---|---|---|---|
| **organic_ascending** | +5pp or more | Flat or up | Spend pullback candidate — earned audience is carrying it |
| **organic_eroding_sales_holding** | −5pp or more | Flat or up | Paid is offsetting natural decay — pulling back risks exposing the decline |
| **organic_eroding_sales_falling** | −5pp or more | Down | Funnel is leaking — more spend won't fix |
| **stable** | Within ±5pp | Any | No mix-shift signal |

### Pass 5 — Routing recommendation

Emit ONE action per location, derived directly from the signals. Decision tree, evaluated in order — first match wins:

1. **Ops broken** (`cancel_rate > 0.10` OR `menu_cvr < 0.25`) → `FIX_OPS_FIRST`. Spend cannot fix a leaking funnel. Recommend pausing incremental spend until cancel ≤ 0.08 and CVR ≥ 0.30. **This refusal is the credibility move — the tool will not recommend "spend more" into broken operations.**
2. **Cannibalization detected AND organic ascending** → `CUT`. The location is generating sales organically; the paid spend is taxing customers it would have won anyway. Annualized savings = current spend.
3. **Cannibalization detected** (incremental ≤ 0, conf ≥ medium) → `PULL_BACK_TO_NC_ONLY`. Cut repeat-customer targeting; retain a minimal new-customer-acquisition layer. Annualized savings ≈ 50% of current spend.
4. **High ROAS, under-invested** (`roas ≥ 8` AND `marketing_pct < benchmark`) → `CONCENTRATE`. The location pays back well and is starved. Recommend lifting spend toward the benchmark. Projected incremental = spend_lift × roas × payout_pct.
5. **Organic eroding, sales holding** → `HOLD`. Paid is doing its job — defending the location from decay. Pulling back risks exposing the underlying decline.
6. **Saturated** (`marketing_pct ≥ 1.5× benchmark` AND `roas < 6` AND organic stable/ascending) → `PULL_BACK_TO_NC_ONLY`. Overspending at only mediocre returns — marginal dollars buying repeats. A strong-ROAS location above benchmark is left alone; the returns earn the spend.
7. **Otherwise** → `HOLD`. Spend is paying back, no signal to change.

For each non-HOLD action, project the annualized dollar swing (savings for CUT/PULL_BACK; incremental net payout for CONCENTRATE; $0 for FIX_OPS_FIRST, with the ops opportunity cited separately).

### Pass 6 — Campaign moves (execution layer)

The routing action is the spend *envelope*; this pass fills in *how to run it*. Each action maps to concrete campaign tactics, grounded in Spice's canonical practice (do not invent — these come from the segmentation playbook):

- **CUT** → pause Sponsored Listings across platforms; kill broad (All) + repeat-customer offers; hold organic. Watch organic share for 2–3 weeks.
- **PULL_BACK_TO_NC_ONLY** → re-target Sponsored Listings to **new-to-brand only**, drop All/Existing; keep a capped Lapsed win-back; swap broad offers for a first-order acquisition offer + a $5/$25 → Lapsed line; reduce total budget.
- **CONCENTRATE** → raise Sponsored Listings budget; segment Ads **New ~70 / Lapsed ~30** on separate capped lines (never a single 'Ads · All'); add/raise a new-customer acquisition offer + optional Spend×Save; hold/grow while ROAS ≥ ~4x (performance-gated — don't mechanically cap a delivering store to 3%).
- **HOLD** → maintain mix; if a non-new store is still on a single 'Ads · All' line, split it New + Lapsed.
- **FIX_OPS_FIRST** → pause ALL paid until cancel ≤ 8% and CVR ≥ 30%.

Platform rules baked in: UE separates new-to-brand (true acquisition) from new-to-location (cross-store) and is the only platform that supports creative A/B tests; DD runs offers/SL straight with no creative tests (lapsed = "Low-Frequency Customers"); GH has coarser targeting. Source memories: `ad_segmentation_practice`, `uber_ads_targeting`, `dd_no_creative_tests`, `growth_store_spend_gating`. Keep this pass in sync with those.

## The marketing-spend benchmark

A common healthy benchmark for a multi-unit delivery portfolio is **marketing-as-percent-of-sales near 3%**. Materially above is a cannibalization signal; materially below on a high-ROAS location signals under-investment. The benchmark is configurable per run via `clients/<slug>.json` → `marketing_pct_benchmark` (default 0.03). It anchors the CONCENTRATE and saturation rules — it is a heuristic, not a hard rule.

## Confidence in the headline number

The headline — "cannibalized spend (annualized)" — must carry its uncertainty.

```
cannibalized_spend = sum over (locations × spend_events) of:
  spend during event window  IF  incremental_sales ≤ 0 with confidence ≥ medium
```

Report as a range based on the volume-weighted average confidence across events.

## What the framework refuses to do

- **Run with <4 months continuous data.** Seasonal trend dominates below this; the counterfactual is unreliable.
- **Recommend "spend more" when ops are broken.** The credibility move is the refusal.
- **Fabricate a counterfactual when comp set < 3 AND no prior-year data.** Surface the gap; exclude the location from per-location callouts.
- **Roll up a "waste %" without a confidence interval.** Externally cited numbers must carry their uncertainty.

## A note on routing without classification

Earlier drafts bucketed locations into named tiers before routing. That was removed: a tier label is an intermediate abstraction that adds nothing the raw signals don't already carry, and it bakes in a proprietary taxonomy that doesn't generalize. The decision tree above keys off the measured signals directly — ROAS, the cannibalization finding, mix-shift trajectory, and ops health. Same decision, fewer moving parts, works for any restaurant.
