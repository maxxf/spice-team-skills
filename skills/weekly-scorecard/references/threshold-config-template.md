# Threshold Config — Copy-Paste Template for New Clients

When onboarding a client onto the scorecard, copy this section into their Notion Weekly Reporting Profile, replace `[CLIENT NAME]` and the notes per their tier/lifecycle, and you're done.

The defaults below match the master Sheet's `thresholds_default` tab. Override only the rows that need to differ for this client.

---

## Threshold Config (Weekly Scorecard)

*Last updated [DATE].* Status logic: green/yellow/red dots are computed by the parser at write time using the rules below. Override industry defaults here as [CLIENT NAME]'s baseline shifts. Live data layer: [Spice Weekly Scorecard Master](https://docs.google.com/spreadsheets/d/1kL39_lOQYsYkUN4h1iZGqdgnkjOu1OfD1SdjI0g2Ajo).

### Money

| metric | type | green | yellow | red | notes |
| --- | --- | --- | --- | --- | --- |
| total_sales | relative | WoW ≥ 0% | WoW ≥ -5% | WoW < -5% | Default. Tighten for growth-stage clients. |
| net_payout | relative | WoW ≥ 0% | WoW ≥ -5% | WoW < -5% | Mirrors sales unless fees/refunds spike. |
| net_payout_pct | absolute | ≥ 70% | ≥ 60% | < 60% | Tighten for premium pricing models (75%/65%). |
| organic_sales_pct | absolute | ≥ 70% | ≥ 50% | < 50% | Loosen for paid-acquisition-heavy clients. |
| aov | relative | WoW ≥ -2% | WoW ≥ -5% | WoW < -5% | Protect against AOV erosion from promo mix. |

### Efficiency

| metric | type | green | yellow | red | notes |
| --- | --- | --- | --- | --- | --- |
| marketing_spend_pct | absolute | ≤ 15% | ≤ 25% | > 25% | Tighten for mature clients (10%/18%). |
| roas | absolute | ≥ 5.0x | ≥ 3.0x | < 3.0x | Sub-3x is unprofitable on most categories. |

### Operations

| metric | type | green | yellow | red | notes |
| --- | --- | --- | --- | --- | --- |
| order_completion_rate | absolute | ≥ 97% | ≥ 95% | < 95% | Below 95% triggers algorithmic deprioritization. |
| error_rate | absolute | ≤ 1.5% | ≤ 3.0% | > 3.0% | UE hard cap for storefront good standing. |
| cancel_rate | absolute | ≤ 1.5% | ≤ 3.0% | > 3.0% | Cancels also impact rating eligibility. |
| refund_rate | absolute | ≤ 2.0% | ≤ 4.0% | > 4.0% | Money-out signal; correlates with quality. |
| downtime_hours | absolute | ≤ 1.0 | ≤ 4.0 | > 4.0 | More than 4 hours offline = staffing failure. |

### Reputation

| metric | type | green | yellow | red | notes |
| --- | --- | --- | --- | --- | --- |
| avg_rating | absolute | ≥ 4.7 | ≥ 4.5 | < 4.5 | Tighten for premium brands (4.8/4.6). |
| ratings_velocity | relative | WoW ≥ 0 | WoW ≥ -20% | WoW < -20% | Velocity drop = credit/flyer pipeline broken. |

### Discoverability

| metric | type | green | yellow | red | notes |
| --- | --- | --- | --- | --- | --- |
| storefront_views | relative | WoW ≥ -5% | WoW ≥ -15% | WoW < -15% | Top-of-funnel collapse = search rank issue. |
| menu_conversion | absolute | ≥ 12% | ≥ 8% | < 8% | UE only. 8% floor where pricing/menu needs work. |

### Per-Location Tier Overrides (optional, for multi-unit clients with tiers)

Apply on top of absolute thresholds for `total_sales` only. Delete this section if the client doesn't have a tier system.

| Tier | Locations | total_sales rule |
| --- | --- | --- |
| RED priority | [list] | green ≥ +5% WoW, yellow ≥ 0%, red < 0% |
| Standard | [list] | default rules |
| GREEN | [list] | default rules |
| YELLOW | [list] | default rules |
| UNICORN | [list] | green ≥ -3% WoW (testing spend pullback) |

### Notes

- [Add client-specific quirks here. Examples: "BOGO-on-bowl is OFF-LIMITS", "DD ad spend invoiced separately", "Pre-rebrand weeks not comparable", etc.]
- Threshold tuning happens here. No script restart needed — next weekly run picks up new rules automatically.

---

## Tuning cheat sheet by client lifecycle

| Lifecycle | Tighten | Loosen |
|---|---|---|
| New (first 8 weeks) | nothing | total_sales (allow growth ramp), marketing_spend_pct (allow paid push) |
| Growth-stage (months 2-6) | nothing | nothing |
| Mature (6+ months) | total_sales (require WoW ≥ +2%), marketing_spend_pct (≤10%/≤18%) | nothing |
| Premium brand | avg_rating (≥4.8/≥4.6), error_rate (≤1.0%), order_completion (≥98%/≥96%) | nothing |
| Multi-tier (RED/UNICORN) | RED tier total_sales (require growth), UNICORN tier marketing_spend_pct | UNICORN tier total_sales (allow -3% WoW) |
| Paid-acquisition heavy | nothing | organic_sales_pct (≥50%/≥30%), marketing_spend_pct (≤25%/≤40%) |
