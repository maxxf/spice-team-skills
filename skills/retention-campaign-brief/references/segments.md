# Canonical segments

## Thanx (MBFS, HealthNut, Ahipoki)

Pre-built segments in the Thanx dashboard:

- **VIP customers** — top 20% by revenue. Use for early access, premium offers.
- **Regular customers** — 3+ visits per month. Use for loyalty milestone messaging.
- **At-risk** — no visit in 30 days. Use for soft re-engagement.
- **Churned** — no visit in 60+ days. Use for winback with offer.
- **First-time visitors** — 1 visit only. Use for bounceback (drive 2nd visit).
- **Birthday month** — pulled from profile. Use for birthday automation only.
- **Location preference** — for location-specific promos.

Custom segments worth building (Ahipoki examples):

- **Expiring points (next 30 days)** — high-value, time-sensitive segment. 103K points expired in March 2026 alone. Build this campaign.
- **2-visit + lapsed 45 days** — close to becoming loyal, slipping. High-leverage winback.
- **First-time online orderer (not yet enrolled in loyalty)** — convert to member.

## Toast (MBFS)

Toast segments are coarser than Thanx. The useful ones:

- **All subscribers**
- **Subscribers who clicked last 30 days**
- **Subscribers with no opens last 60 days** (sunset candidates)
- **Loyalty members** (if Toast Loyalty is on)
- **Subscribers by location**

Toast does not have native lapsed / VIP / behavioral segments the way Thanx does. Build custom in the campaign builder before sending.

## Klaviyo (Ahipoki, incoming)

When the Klaviyo migration completes, available segments include:

- **Engaged 30 / 60 / 90** — opened or clicked in window
- **VIP (lifetime value > $X)** — set X based on Ahipoki AOV
- **Browsed not purchased** — site behavior, needs Klaviyo tracking pixel
- **Cart abandoners** — 1h, 24h, 72h triggers
- **Post-purchase day 7 / 14 / 30** — bounceback
- **Subscriber inactive 60 / 90 / 180** — winback ladder
- **SMS-consented** — separate from email list, treat as own segment

Build the SMS-consented segment as soon as Klaviyo provisioning completes. SMS opens at 3-5x email rates. Do not let it sit unused.

## Suppression rules (apply to every campaign)

Always exclude:

- Unsubscribed
- Email marked as spam
- Bounced last 30 days
- Refund issued last 14 days
- Active complaint (flag in Toast / Thanx)
- For winback campaigns: exclude anyone with a purchase in the last 14 days
- For new-customer campaigns: exclude anyone who has ever purchased
- For VIP campaigns: exclude anyone below the tier threshold

If suppression is not applied, the campaign will hit unintended customers. This is the most-missed step.
