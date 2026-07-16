# Deliverable Template — Cannibalization Audit Report

Output structure for the client-facing PDF. `scripts/render_deliverable.py` produces a markdown file matching this layout; the existing Spice `pdf` skill converts to PDF.

The deliverable is **action-first**. Page 1 is what the buyer (VP Marketing / COO) needs to walk into a budget meeting with. Pages 2+ are the receipts.

## Page 1 — Executive Summary

```
# Cannibalization Audit — <Client Display Name>
**Window:** <YYYY-MM-DD> to <YYYY-MM-DD> · **Locations:** <N> · **Platforms:** UE / DD / GH

## The Headline

Of $<total_spend> spent on 3P marketing over the window,
**$<cannibalized_low>–$<cannibalized_high> bought no incremental sales.**

If the recommended reallocation is adopted across the portfolio,
projected net-payout lift: **+$<lift_annualized> annualized**.

## Recommended Actions

| Action | Locations | Total spend | What it means |
|---|---|---|---|
| CUT | N | $X | Spend bought no incremental sales — stop it |
| PULL BACK TO NC ONLY | N | $X | Reduce to a new-customer-only layer |
| CONCENTRATE | N | $X | Under-invested and paying back — add spend |
| FIX OPS FIRST | N | $X | Ops leaking — spend can't fix; pause it |
| HOLD | N | $X | Spend is paying back — no change |

(Only rows with locations are shown.)

## The Five Highest-Impact Moves

1. **<Action> — <Location>** — projected $X annualized
2. ...
3. ...
4. ...
5. ...

## Portfolio Marketing Spend vs. Benchmark

Current marketing-as-percent-of-sales: **X%**
Benchmark: **3%** (configurable per restaurant)
Read: <one sentence explanation — over, under, or on>
```

## Page 2 — Portfolio Mix Shift

```
## Organic vs. Paid Share, Trajectory

[Chart: organic share % over the 26-week window, portfolio rollup]

- Start of window: organic = X%, paid = Y%
- End of window: organic = X%, paid = Y%
- Net shift: <±Z pp>

<one-paragraph read: what the trajectory means for the portfolio. The classic
cannibalization signature is organic share rising while paid spend is cut and
total sales hold flat — that pattern is the proof the spend was buying customers
who would have ordered anyway.>
```

## Pages 3..N — Per-Location Cards

One card per location, sorted by projected dollar swing descending.

```
### <Location Name> · <Market> · <Recommended Action>

**Recommended action:** <ACTION>
**Projected annualized dollar swing:** +$<X>
**Confidence:** <High / Medium>

**Key metrics over the window:**
- Gross sales: $<X>/wk avg
- Net payout %: <X>%
- ROAS: <X>x
- Marketing % of sales: <X>%
- Organic share trajectory: <start>% → <end>%
- Cancel rate: <X>% · Menu CVR: <X>% · Ratings velocity: <X>/wk

**Why this action:**
<2–3 sentence narrative grounded in the spend events the analysis used.>

**Spend events the call relied on:**
| Week | Event type | Pre-spend $/wk | Post-spend $/wk | Observed sales Δ | Expected (counterfactual) | Incremental |
|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... |
```

If a location has no qualifying spend events (e.g., consistent spend throughout window), the card omits the spend-events table and notes:
> No material spend changes detected in window. The recommendation rests on the aggregate ratios; no natural-experiment counterfactual was available for this location.

## Final Page — Methodology & Caveats

```
## How this report was made

**Window:** <dates>. <N> weeks of continuous data across <N> locations on <platforms>.

**Routing logic:** each location's recommended action is derived from its ROAS, marketing-as-percent-of-sales, the cannibalization finding (below), organic/paid mix shift, and operational quality. Full rules in the methodology appendix (available on request).

**Counterfactual baselines** for each spend event use a Bayesian blend of:
- Comp-store locations not running the same spend change (weight 0.6 when ≥5 comps available)
- Prior-year same-week sales for the same location (weight 0.25 when available)
- Brand-wide seasonal trend (weight 0.15)

**Confidence bands.** Each per-location callout is rated High (≥90% confidence), Medium (~70%), or suppressed (below 70%). The headline cannibalization number is reported as a range based on volume-weighted average confidence.

**Caveats:**
- <Any data gaps surfaced during validation, e.g., "GH operations data unavailable for the full window — GH-only ops thresholds are limited">
- <Structural events in window, e.g., "NYC launch is treated as a new-store period with no prior-year baseline">
- <Locations excluded from per-location callouts due to comp-set or data gaps>

**What this report does not do:**
- Recommend specific creative or campaign-level optimizations (separate Spice deliverable)
- Make claims about 1P (direct-to-consumer) marketing ROI — only 3P / delivery marketplace
- Project beyond the audit window
```

## Formatting notes for `render_deliverable.py`

- All dollar figures rounded to nearest $1K above $10K; below that, nearest $100
- All percentages to one decimal place
- ROAS to one decimal place
- Per-location cards: hard page break before each (use `\\newpage` in markdown for the PDF step)
- Table widths: prefer 5-column max for the spend-events table; if more columns needed, restructure
