# Segment selection rubric

Use this to map campaign objective → segment.

| Objective | Best segment | Reach | Why |
|---|---|---|---|
| Welcome new subscribers | Subscribers from last 7 days, no purchase | Small (~50-500/wk) | Hot list, single-purpose flow |
| Drive first purchase | New members, signup last 30 days, 0 orders | Small-medium | Conversion-focused |
| 1st → 2nd visit bounceback | First-time purchasers, last 14 days | Small | High-leverage cohort |
| Soft re-engagement (30-day) | At-risk: no visit 30-45 days | Medium | Recapture before they fully churn |
| Winback (60-day) | Churned: no visit 60-89 days, 1+ prior orders | Medium-large | Highest-ROI segment per Thanx data |
| Deep winback (90+) | Long-lapsed: no visit 90+ days | Large | Lower hit rate, big lift if it works |
| VIP exclusive offer | Top 20% by revenue | Small | Premium signal, drives advocacy |
| Loyalty milestone | New tier-reached members | Small | Reinforces program value |
| Points expiring (Ahipoki) | Points > 100 expiring next 30 days | Small-medium | Pure recovery — would otherwise be wasted |
| Birthday | Birthday month + 7 days before | Small (daily trickle) | 31% higher AOV per industry data |
| Cart abandon | Items in cart, no purchase 2h+ | Daily trickle | 10-15% recovery |
| Review request | Order completed last 3-5 days, no complaint flag | Daily trickle | Drives ratings velocity |
| Broad promo / LTO | All engaged subscribers (opened/clicked last 90d) | Largest | Reach-driven |
| Major announcement | All subscribers | Largest | Full list, low frequency |
| Location-specific promo | Subscribers with location preference = X | Per location | Geo-targeting |

## When to combine segments

For a campaign where the offer logic differs by audience (e.g. winback + birthday in same week), build two separate campaigns rather than one with conditional content. Conditional logic in email is error-prone and breaks Thanx A/B testing.

## When to NOT send

If the segment is under 100 people, skip the email and DM the segment manually (or wait for the segment to grow). Email infrastructure costs and deliverability hit don't pay off below 100.

If the segment overlaps > 60% with another campaign you sent in the last 7 days, hold this one. List fatigue is the silent killer.

## Per-client overlay

- **MBFS**: list is smaller (~5-10K subscribers). Pick high-precision segments. Mass sends fall flat.
- **HealthNut**: list is engaged (66-72% opens). Treat with care — over-mailing burns the trust.
- **Ahipoki**: 132K customers, 69K loyalty members. Can support larger sends but Mike has flagged "too many emails" twice. Keep frequency cap to 6-8/month total.
