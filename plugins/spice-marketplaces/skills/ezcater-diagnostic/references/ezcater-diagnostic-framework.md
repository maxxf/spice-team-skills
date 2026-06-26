# ezCater Catering Diagnostic Framework & Benchmarks

> Catering analog of the delivery `diagnostic-framework.md`. ~65% of the delivery
> methodology transfers; this file encodes the catering-specific deltas. Built from
> the Tiff's Treats audit (Jun 25 2026) + ezCater partner-portal research.
>
> **Key structural differences vs delivery:**
> - **3 sub-buckets**, not delivery's menu/ops/campaigns: **Ops · Visibility · Packaging**.
>   Catering is request-based (RFQ), not browse-and-order — there is **no menu funnel**
>   (no impressions→menu→order CVR, no storefront CTR), so the delivery "Menu" sub-bucket
>   is replaced by **Packaging completeness**.
> - **Monthly cadence**, not weekly — `month` (1–3) replaces `week` (1–13) for the 90-day window.
> - **Single platform** — `platform = "EZ"`.
> - **Higher rating bar** — ezCater's Reliability Rockstar badge needs **4.8★** (vs delivery 4.5).

## Time Window

All diagnostics run on **trailing 90 days**, expressed as **3 monthly buckets** (`month` 1–3).
Two views:
- **Headline:** 90-day totals — hero stats, radar scoring, action-plan impact.
- **Momentum:** last month vs prior month (and YoY where the payout history reaches back).

If <90 days exist, run on what's available and flag the window in the title. Never silently shorten.

## Brand Health Radar — 6 core + 3 optional funnel dimensions (catering)

Scored 1–10, target defaults to 8. The 6 core dims compute from per-store data. The 3
funnel dims (Traffic/Conversion/Re-order) compute only when portfolio funnel data is
supplied (Sales Performance page) — otherwise they render `(pending)` and drop from the mean.

> **v0.2 correction:** the live portal's Sales Performance page DOES expose a funnel
> (Search Views → Menu Views → Orders), a conversion rate benchmarked vs local peers, and a
> New/Existing/Lapsed customer mix. So Traffic/Conversion/Re-order are recoverable for
> catering after all — supply them via the optional `portfolio` input.

| # | Dimension | Source | Scoring Bands |
|---|---|---|---|
| 1 | **AOV** | gross_sales / orders, 90d | <$100=3 · $100–150=5 · $150–200=6.5 · $200–300=8 · >$300=9–10 *(catering baskets run 15–40× delivery)* |
| 2 | **Operations** | % stores not flagged red across ops bucket | >30% red=3–4 · 15–30%=5 · 5–15%=7 · <5%=8–9 |
| 3 | **Visibility** | lever activation + sponsored ROAS | no levers on=2 · 1 lever=4 · PPP+ezRewards on=7 · +sponsored ROAS≥3.5=9 |
| 4 | **Customer Sentiment** | star rating blend (0–5 → 1–10) | <4.2=3 · 4.2–4.5=5 · 4.5–4.8=7 · ≥4.8 (badge bar)=9–10 |
| 5 | **Momentum** | last-month vs prior (and YoY if available) | <−10%=3 · −10–0%=5 · 0–10%=6.5 · 10–25%=8 · >25%=9–10 |
| 6 | **Packaging** | mean packaging-completeness across stores | <0.6=3 · 0.6–0.8=5 · 0.8–0.9=7 · ≥0.9=9 |
| 7 | **Traffic** *(opt)* | Search Views → Menu Views CTR | <3%=3 · 3–5%=4 · 5–7%=6 · 7–10%=7.5 · >10%=9 |
| 8 | **Conversion** *(opt)* | Menu-View→Order rate vs local peer benchmark (ratio) | <0.7=3 · 0.7–0.9=5 · 0.9–1.1=7 · >1.1=9 |
| 9 | **Re-order** *(opt)* | Existing / (New+Existing+Lapsed) customer share | <15%=3 · 15–25%=5 · 25–40%=7 · >40%=9 |

**Overall radar score:** unweighted mean of the **measured** dims only. Caption:
`Overall {score}/10 (mean of {n} measured axes). Weakest: {axis1}, {axis2}.`
Pending/unmeasurable axes are excluded from the denominator and labeled `(pending)` — never guessed.

## Two threshold systems (the live portal proves this)

The per-store operational detail splits metrics into **two** sets — don't conflate them:

**Accountability / pause standards** — breaching these **PAUSES the store** (zero orders).
These gate revenue and drive the Ops **Broken** flag + the foundation gate.

| Signal | Pause standard |
|---|---|
| Rejected orders | ≤ 5% |
| Canceled orders | ≤ 3% |
| On-time delivery | ≥ 95% |
| Ready for Dispatch | ≥ 95% *(self-delivery → N/A, skipped)* |

**Badge / quality goals** — stricter; missing these costs visibility, not access. Drive the
Ops **Watch** flag.

| Signal | Badge goal |
|---|---|
| Rating | ≥ 4.8 (after ≥8 reviews) |
| On-time delivery | ≥ 98.5% |
| Rejected | ≤ 0.5% |
| Canceled | 0% |
| Order accuracy | ≥ 99% |
| Delivery tracking | ≥ 75% |
| On-time acceptance | 100% |

## Pause status — the #1 lever

`status` ∈ active / at_risk / **paused**. A **paused** store accepts **zero** marketplace
orders until the partner completes ezCater's remediation course (cancellations / rejections /
on-time). This is the highest-priority finding (`store_paused`, P0) and forces the store to
**Red** regardless of every other metric. `at_risk` = heading toward pause → Ops Watch.

## Foundation Health Gate (catering)

Triggers if ANY active store is **paused** or breaches a **pause standard** (rejected >5%,
canceled >3%, on-time <95%, ready-for-dispatch <95%) — or has rating <4.5 / accuracy <97%
(severe quality). When triggered, the action plan leads with the fix and all visibility spend
(PPP/ezRewards/sponsored) is HOLD. Dark/volume-locked stores don't gate the portfolio.

## Reliability Rockstar Badge — Eligibility Funnel

The badge is ezCater's headline visibility lever. It is **not** a diagnostic tier — it's a
platform-imposed gate computed as its own funnel and surfaced as a hero finding.

```
Total stores
  → Active                 (orders ≥ 1 in 90d)
    → Volume-eligible      (orders ≥ 6 in 90d)              ← ezCater's order-count gate
      → Pass goals (excl. tracking)  (rating ≥4.8 after ≥8 reviews, on-time ≥98.5%,
                                      rejected ≤0.5%, canceled 0%, accuracy ≥99%)
        → Full pass        (also delivery tracking ≥ 75%)
          → Badged         (input flag; default 0 if unknown)
```

The gap splits two ways (v0.2 — the live portal proved delivery tracking is the gate):
- **`badge_gap_tracking`** — passes every goal **except delivery tracking ≥75%**. The fix is
  operational: enable driver status updates / ezDispatch. **This is the Tiff's case** — they
  self-deliver, so tracking is 0% and the badge is unreachable until tracking is turned on.
- **`badge_gap_enrollment`** — passes everything incl. tracking but isn't badged → enrollment/config.

(Tiff's: 175 → 106 active → 31 volume-eligible → **16 pass-goals-excl-tracking → 0 full-pass → 0 badged**.
The 16 are tracking-blocked, NOT an enrollment gap — the audit's original "criteria unconfirmed" P0, now resolved.)

## Visibility Levers (catering's "campaigns")

ezCater's paid/visibility surface, replacing delivery ads:

| Lever | Field | What it does | Healthy use |
|---|---|---|---|
| Preferred Partner Program | `ppp_bid_pct` (0–20) | Bid % of food total for ranking | active, tuned to demand |
| ezRewards | `ezrewards_pct` (0–20) | Customer loyalty %, lifts ranking + appeal | active; PPP+ezRewards ≈ +30% orders |
| Sponsored Listings | `sponsored_spend`, `sponsored_attributed_sales` | Pay-per-order premium placement | ROAS ≥ 3.5x |
| Promotions | `promo_count_active` | Promo codes / new-customer offers | segmented, not blanket |

**Sponsored ROAS** = `sponsored_attributed_sales / sponsored_spend` (only when spend > 0).

## Sub-bucket Scoring (per store) — Healthy / Watch / Broken

### Ops performance (two-threshold)
- **Broken** (breaches a **pause standard** or severe quality): status=paused, OR rejected >5%,
  OR canceled >3%, OR on-time <95%, OR ready-for-dispatch <95%, OR rating <4.5, OR accuracy <97%
- **Watch** (misses a **badge goal** but no pause breach): status=at_risk, OR rejected ≥0.5%,
  OR canceled >0%, OR on-time <98.5%, OR accuracy <99%, OR rating <4.8
- **Healthy:** meets all badge goals

> Delivery tracking is deliberately **excluded** from the Ops flag — it's a badge-funnel input
> (`badge_gap_tracking`). For a self-delivery client every store has 0% tracking; folding it
> into Ops would mark the whole portfolio Watch and bury the real signal.

### Visibility performance
- **Healthy:** PPP **and** ezRewards both active, and (no sponsored spend OR sponsored ROAS ≥3.5x)
- **Watch:** no levers active (an **opportunity**, not a fire), OR exactly one lever active, OR sponsored ROAS 2.5–3.5x
- **Broken:** sponsored spend running at ROAS <2.5x (money actively on fire)

> **Catering deviation from delivery.** Delivery treats "no campaigns active when the store
> qualifies" as Broken. In catering that would mark every pristine-ops store in an unmanaged
> account Red just for not advertising — which misreads the opportunity. So **levers-off is a
> Watch**, and the high-severity `levers_all_off` finding (not the tier) carries the
> turn-on-the-promo-engine action. Broken visibility is reserved for spend below 2.5x ROAS.

### Packaging performance
- **Healthy:** completeness ≥0.9 (per-person pricing, headcount tiers, lead-time-gated packages, required fields filled)
- **Watch:** completeness 0.6–0.9
- **Broken:** completeness <0.6

## Tier Rollup (Green / Yellow / Red / New)

Each store rolls its 3 sub-buckets to one tier using **worst-flag-wins**, matching the
deployed delivery `cross_cutting.rollup_tiers` code (the framework's stricter "2+ Watch → Red"
is intentionally NOT applied for catering — see the visibility deviation above):

| Sub-bucket profile | Tier | Default action |
|---|---|---|
| All 3 Healthy | 🟢 **Green** | Scale: raise PPP bid, push ezRewards, feature; pursue badge |
| Any Watch (no Broken) | 🟡 **Yellow** | Targeted fix on the weak bucket; hold spend |
| Any 1 Broken | 🔴 **Red** | Stop buying visibility; fix the broken bucket first |
| Genuinely new / insufficient history **or** orders <6 in 90d | 🆕 **New** | Awareness + reactivation; re-tier once a full cycle exists |

**Edge cases:**
- **Ops Broken always wins** — a Broken-ops store is Red regardless of other buckets.
- **New = volume-locked or genuinely new.** A store with <6 orders/90d can't earn the badge or
  prove performance — it's New (awareness target), not Red. An established store with full
  history is tiered on actual performance (the **pre-Spice baseline** — the bar Spice moves,
  not a Spice scorecard).
- **Dark stores** (0 orders/90d) are New with a reactivation finding.

## Pattern Library (catering findings)

| Pattern ID | Trigger | Severity | Bucket | Deliverable / action |
|---|---|---|---|---|
| `store_paused` | status = paused | foundation (P0) | ops | complete ezCater remediation course to unpause — $0 while paused |
| `pause_risk` | active, breaches a pause standard, not yet paused | high | ops | fix before ezCater pauses the store |
| `low_rating` | rating <4.5 | foundation | ops | ratings push |
| `on_time_below_badge` | on-time <98.5% (active store) | high | ops | on-time fix at flagged stores |
| `rejection_misconfig` | rejection ≥0.5% | medium | ops | rejection/lead-time settings audit (config, not demand) |
| `order_accuracy_low` | accuracy <99% | high (≤97 foundation) | ops | accuracy/QA fix |
| `on_time_acceptance_low` | acceptance <95% | medium | ops | accept orders within 15 min |
| `packaging_incomplete` | completeness <0.6 | foundation | packaging | build catering packages (Feeds-10/25/50, per-person, tiers) |
| `badge_gap_tracking` | pass all goals except delivery tracking ≥75% | high | visibility | enable delivery status updates / ezDispatch — unlock the badge |
| `badge_gap_enrollment` | full pass but not badged | high | visibility | resolve badge enrollment/config |
| `levers_all_off` | active store, no PPP/ezRewards/sponsored | high (opportunity) | visibility | turn on PPP + ezRewards (ezManage); pilot sponsored |
| `low_roas_sponsored` | sponsored spend, ROAS <2.5x | high | visibility | fix or kill sponsored spend |
| `over_discounting` | promo_count_active ≥3 | medium | visibility | consolidate promos |
| `low_conversion_vs_peer` | conversion rate < local peer benchmark | high | packaging | menu photos, packaging, pricing, promos/ezRewards |
| `dark_stores` | 0 orders/90d | medium | topline | reactivation push |
| `volume_locked` | 1–5 orders/90d | medium | topline | awareness to cross the 6-order badge gate |

### Common catering shapes
- **Invisible-but-good** (Tiff's): strong ops + demand, zero levers on → flip the promo engine. The single biggest lift.
- **Volume-locked floor:** large tail of stores under the 6-order gate → awareness, not optimization.
- **Badge left on table:** metrics-pass stores unbadged → enrollment/config fix, near-zero cost.
- **Reliable-but-slow:** good rating, on-time misses → fix the 15-min window, not the food.

## Action Plan Assembly

Group findings by the tier of the store(s) they touch (portfolio-scope findings to a
portfolio lane). Per-tier defaults:
- **Foundation gate triggered** → action plan leads with the gated fix; visibility spend is HOLD.
- **Red** → stop visibility spend at the store; fix worst bucket.
- **Yellow** → targeted fix on the one weak bucket; hold.
- **Green** → scale levers (PPP bid up, ezRewards on, pursue badge), feature.
- **New** → awareness + reactivation; re-diagnose next cycle.

Output is the same two-half Notion page as delivery (dashboard-first hero cards + 6-dim radar +
tier donut + action kanban; analyst-depth toggles below). Reuse the delivery orchestrator's
`notion_assembly.py` / chart helpers when wiring the publish layer (Phase 4).
