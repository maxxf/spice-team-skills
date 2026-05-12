# Diagnostic Framework & Benchmarks

> **Note (2026-05-08, orchestrator redesign Wk 1):** This file is the canonical pattern library for v0.2 (monolithic) and remains operational. Wk 2 redistributes per sub-skill:
> - 7-dim radar bands → split per radar dim owner (see spec §Contracts §"Radar dim ownership")
> - Foundation Health Gate → encoded in `orchestrator/cross_cutting.py::compute_foundation_gate`
> - Cuisine CVR benchmarks → `Cowork/Skills/diagnostic-menu/references/`
> - Location Tier Strategy → already extracted to `cross-cutting-patterns.md` (Wk 1)
> - Common Diagnostic Patterns → split per sub-skill in `patterns-<sub>.md`
> - Chart Library → split per sub-skill (charts owned by domain) + cross-cutting at orchestrator
>
> Until Wk 2 redistribution completes, all references in v0.2 SKILL.md continue to work against this file.

## Time Window

All diagnostics run on **trailing 90 days**. Two views are computed:
- **Headline:** 90-day totals — used in hero stat strip, radar scoring, action-plan impact estimates.
- **Momentum:** last 4 weeks vs. prior 4 weeks delta — used in callouts and the "what's changing" narrative.

If <90 days of data exists, run on what's available and flag the window in the title. Never silently shorten.

## Brand Health Radar — 7 Dimensions

The radar in Half 1 of the Notion output uses these 7 axes. Each scored 1–10. Targets default to 8 unless the client's tier or category warrants a different bar.

| # | Dimension | Source | Scoring Bands |
|---|---|---|---|
| 1 | **AOV** | Blended across platforms | <$20=2 · $20–25=4 · $25–30=6 · $30–35=7 · $35–40=8 · >$40=9–10 |
| 2 | **Re-order Rate** | UE Repeat Customer Rate + DD Frequent Customers % (volume-weighted blend) | <15%=2 · 15–25%=4 · 25–35%=6 · 35–45%=7.5 · 45–55%=9 · >55%=10 |
| 3 | **Conversion** | UE menu CVR (primary) | <15%=3 · 15–18%=4.5 · 18–20%=5 · 20–25%=7 · >25%=8–9 |
| 4 | **Marketing Efficiency** | 1 − (marketing spend % of gross). Spice benchmark: 30% spend = healthy | >40% spend=3 · 35–40%=4.5 · 30–35%=6.5 · 25–30%=8 · <25%=9–10 |
| 5 | **Operations** | % stores flagged across all platforms (errors, cancels, downtime) | >30%=3–4 · 15–30%=5 · 5–15%=7 · <5%=8–9 |
| 6 | **Traffic** | UE storefront → menu CTR (impression-to-store-view as fallback) | <5%=3 · 5–7%=4 · 7–9%=6 · 9–12%=7.5 · >12%=9 |
| 7 | **Campaigns / ROAS** | Blended ROAS across UE Ads + DD SL + GH Sponsored | <2x=3 · 2–3x=5 · 3–4x=6.5 · 4–5x=8 · >5x=9–10 |

**Re-order Rate definition (detail):**
- UE: % of orders in the period from customers with ≥2 orders in trailing 90 days. Source: UE Manager → Customers tab → Repeat Customer Rate.
- DD: % share of orders from customers DD classifies as "frequent" (≥4 orders in 90 days). Source: DD Merchant Portal → Customer Insights.
- GH: repeat order rate if exposed in the GH ops report; otherwise mark as data gap.
- **Blend:** volume-weighted average across platforms with data. Volume = orders in period. If only one platform has data, report that platform's rate and note the gap.

**Overall radar score:** unweighted mean of the 7 dimensions (use weighted average if the GM specifies). Caption format: `Overall {score}/10. Weakest: {axis1}, {axis2}.`

## Foundation Health Gate

Before recommending any spend, check the foundation. If anything is in "Stop Everything," that's the entire action plan until fixed.

| Signal | Healthy | Fix First | Stop Everything |
|---|---|---|---|
| Rating | >4.5 | 4.2–4.5 | <4.2 |
| Error rate | <2% | 2–5% | >5% |
| Uptime | >95% | 90–95% | <90% |
| Menu conversion | >20% | 15–20% | <15% |
| Photo coverage | >90% | 50–90% | <50% |
| Hours accuracy | Matches actual | Minor gaps | Closed when listed open |
| Re-order rate | >35% | 25–35% | <25% (no organic moat) |

## Cuisine-Specific CVR Benchmarks

| Cuisine Type | Good CVR | Average CVR | Poor CVR |
|---|---|---|---|
| Fast Casual / QSR | 15–18% | 12–15% | <12% |
| Pizza / Italian | 16–20% | 13–16% | <13% |
| Asian (Chinese, Thai, Japanese) | 14–18% | 11–14% | <11% |
| Poke / Bowl / Health | 12–16% | 10–12% | <10% |
| Mexican / Latin | 14–18% | 11–14% | <11% |
| Indian / South Asian | 12–16% | 9–12% | <9% |
| Burger / American | 15–20% | 12–15% | <12% |
| Upscale Casual | 10–14% | 8–10% | <8% |
| Juice / Smoothie | 8–12% | 6–8% | <6% |
| Bakery / Dessert | 14–18% | 10–14% | <10% |

## Campaign Verdict Thresholds

| Verdict | ROAS Range | Action |
|---|---|---|
| SCALE | >5.0x | Increase budget immediately |
| KEEP | 3.5x–5.0x | Maintain current budget |
| HOLD | 2.5x–3.5x with fixable ops issue | Hold until resolved |
| KILL | <2.5x OR ops-critical store | Pause immediately |

## Location Tier Strategy (Green / Yellow / Red / New)

Replaces the old A/B/C-by-payout tiering. Every store is classified across three sub-buckets, then rolled up to a single tier. The tier dictates the default action.

### Sub-bucket scoring (per store)

Each sub-bucket scored Healthy / Watch / Broken:

**Menu performance**
- **Healthy**: UE menu CVR ≥ cuisine "Average" benchmark, photo coverage ≥ 80%, hero set, all categories populated
- **Watch**: CVR within 20% below benchmark, OR photo coverage 50–80%, OR 1 category empty
- **Broken**: CVR <20% below benchmark, OR photo coverage <50%, OR 2+ categories empty, OR no hero

**Ops performance**
- **Healthy**: error rate <2%, cancellation <2%, uptime >97%, rating ≥4.5, hours accurate
- **Watch**: error rate 2–5%, OR cancellation 2–5%, OR uptime 90–97%, OR rating 4.2–4.5
- **Broken**: error rate >5%, OR cancellation >5%, OR uptime <90%, OR rating <4.2, OR repeated hours-mismatch incidents

**Campaign performance**
- **Healthy**: blended ROAS ≥3.5x, spend efficient relative to incremental orders, no over-discounting
- **Watch**: ROAS 2.5–3.5x, OR promo stack ≥2 active, OR spend running but <10 incremental orders/week
- **Broken**: ROAS <2.5x, OR ad spend running while ops Broken (money on fire), OR no campaigns active and store qualifies for them

### Rollup rule

| Sub-bucket profile | Tier | Default action |
|---|---|---|
| All 3 Healthy | 🟢 **Green** | Scale: increase ad budget, expand to additional platforms, feature in marketing |
| Any 1 Watch, rest Healthy | 🟡 **Yellow** | Targeted fix on the weak bucket. Maintain current spend. |
| Any 1 Broken **or** 2+ Watch | 🔴 **Red** | **Stop campaigns at this store.** Fix the broken bucket(s) before any growth investment. |
| Launched <60 days, insufficient data | 🆕 **New** | Awareness investment + diagnostic re-run at 60-day mark to assign permanent tier |

**Edge cases:**
- **Ops Broken always wins.** A store with Broken ops is Red, regardless of Menu/Campaign scores. Money burning at a broken store is the fastest revenue leak.
- **New trumps the others.** If launched <60 days, the store is New, even if data already looks good. Don't stamp Green on a store that hasn't seen a normal cycle.
- **Single-platform stores.** If a store only has data on 1 of UE/DD/GH, score the available platform and note the limitation. Don't blend zeros.

### What this replaces

Prior A/B/C/Critical system tiered stores by net payout within geo segment, then forced Critical on ops-flagged stores. The new system flips the logic: **performance health drives tier, not revenue size.** A high-revenue store with Broken ops is Red, not "Tier A with a Critical flag." This makes the action plan unambiguous: Red stores stop spending, full stop.

For revenue-size analysis (e.g., "where is most of the money"), use the Top-15 by Net Payout view in the Location Tiers toggle. That stays as a separate cut, not a tier.

## Common Diagnostic Patterns

### Invisible Restaurant
Low impressions, low traffic, decent conversion when found. → Hero refresh + sponsored placement + SEO menu titles.

### Window Shopper
High traffic, low conversion. → Menu consolidation + photo sprint + strategic pricing + bundles.

### Leaky Bucket
Good orders + high cancellations / accuracy issues. → Ops audit, menu availability sync, hours fix.

### Ad Dependent
Revenue collapses when ads pause. → Fix fundamentals (menu, photos, ratings, **re-order rate**) before rebuilding ad strategy.

### Price Shock
High menu views, drop-off at checkout. → Pricing review, absorb delivery fee, value bundles, free-delivery threshold.

### No Moat (NEW)
Re-order rate <25% despite decent overall volume. → Customer is acquired by promo, never returns. Fix product/experience first; loyalty mechanics second; ad scaling last.

---

## Chart Library

All charts produced by `references/generate_diagnostic_charts.py` from a single `metrics.json` input. All use the Spice palette:

```python
SPICE_PALETTE = {
    "red":     "#B91C1C",  # primary, "current" overlay, P1 risks
    "charcoal":"#1F2937",  # text, axes
    "sage":    "#84CC16",  # "target" overlay, wins
    "cream":   "#FEF3C7",  # background fills
    "amber":   "#F59E0B",  # P2, opportunities
    "blue":    "#2563EB",  # P3, decisions needed, neutral data
    "gray":    "#9CA3AF",  # secondary axis, prior-period comparisons
}
```

### radar_7dim.png

- matplotlib polar axes, 7 spokes (one per dimension above, in the order listed)
- Two filled polygons: **Current** (red, alpha 0.4) over **Target** (sage, alpha 0.2 with dashed outline)
- Y-axis 0–10, light gridlines at 2/4/6/8
- Spoke labels: dimension name + current score (e.g., "AOV\n6/10")
- Title: "Brand Health"; subtitle hidden (caption added in Notion underneath)
- Size: 6.5 × 6.5 inches @ 200dpi

### sparklines_gmv_orders.png

- Two small line subplots in a row, no axes, no gridlines (AOV is shown in the hero stat strip — not duplicated here)
- Each: weekly buckets across 90 days; last 4 weeks shaded with `cream` background
- Title above each: metric name + current 4w total (e.g., "GMV — $X" with delta % colored red/sage)
- Size: 7.5 × 2.2 inches @ 200dpi

### tier_donut.png

- matplotlib pie + center hole (donut). Slices: 🟢 Green (sage `#84CC16`), 🟡 Yellow (amber `#F59E0B`), 🔴 Red (`#B91C1C`), 🆕 New (blue `#2563EB`)
- Center label: total store count
- Legend: each tier with `{label}: {n} stores · {pct}% of payout`
- Size: 5 × 5 inches @ 200dpi

### funnel_ue.png

- Horizontal funnel: Impressions → Storefront Views → Menu Views → Orders
- Each stage labeled with absolute number + drop-off % to next stage
- Bars filled `red`, drop-off arrows `gray`
- Size: 8 × 4 inches @ 200dpi

### top_skus_bar.png

- Horizontal bar chart, top 10 SKUs by combined revenue (UE+DD)
- Bars colored by % of revenue (gradient: charcoal → red)
- Each bar labeled with `$X (n%)`
- Size: 7 × 5 inches @ 200dpi

### campaign_2x2.png

- Scatter plot: x = Spend, y = ROAS. Marker size = orders. Marker color = platform (UE/DD/GH)
- Quadrant lines at ROAS=3.5 (KEEP threshold) and median spend
- Quadrant labels in corners: "SCALE" (top-right) · "INVEST MORE" (top-left) · "FIX OR KILL" (bottom-left) · "OVER-SPEND" (bottom-right)
- Each marker labeled with campaign name (small font)
- Size: 8 × 6 inches @ 200dpi

### daypart_heatmap.png

- imshow heatmap: 7 rows (Mon–Sun) × 24 columns (hours)
- Cell value = order count or order share. Colormap: cream → red
- Annotations on each cell with order count
- Title: "Order Density by Daypart (UE + DD blended)"
- Size: 12 × 4 inches @ 200dpi

### top15_green_bar.png

- Horizontal bar, top 15 Green-tier stores by 90-day net payout
- Bars colored sage; payout amount labeled at end
- If <15 Green stores exist, fill remainder with top Yellow stores using amber bars (visually distinct)
- Size: 8 × 7 inches @ 200dpi
