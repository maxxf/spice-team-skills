# Platform-specific rules

## Thanx

- Login: dashboard.thanx.com using success@spicedigital.co
- Native A/B testing with automatic 10% control group holdout (use it on every campaign over 5K recipients)
- SMS not yet enabled for Ahipoki. Klaviyo or Attentive being investigated. For now, email + push only.
- Effective Discount Rate (EDR) target: 2.5-3.5% of revenue. If a campaign would push EDR above 4%, reduce reward value or add restrictions.
- Sync schedule: menu changes hourly, 86'd items every 5 minutes. Push manually if reward menu changed in Toast and is not appearing in Thanx.
- New Thanx features (April 2026 release):
  - Points Redemption Activity Report (14-day attribution per campaign)
  - Activation Funnel Report (cohort: account creation → 1st, 2nd, 3rd purchase)
  - Tiers Program (bronze / silver / gold by annual spend) — Patrick has the spec sheet, ask if not on file

## Toast

- Admin: toasttab.com/restaurants/admin/home
- Email module + SMS module (separate sign-ups)
- SMS registration: 3-10 business days through Toast carrier verification. $185/month for Marketing Essentials Suite.
- Attribution can double-count across channels (known Toast behavior, do not adjust manually).
- 5 reporting pages for monthly report (used by `retention-monthly-report` skill):
  1. Reports > Sales > Marketing-Driven Sales
  2. Guest Engagement > Loyalty Program > Insights
  3. Guest Engagement > Marketing (dashboard)
  4. Guest Engagement > Marketing > each individual campaign
  5. Guest Engagement > Marketing > Automations tab > each active flow
- Toast does not surface app engagement metrics in one dashboard. Request from Toast rep if needed.

## Klaviyo (Ahipoki, migrating)

- Klaviyo partner contact: Anas Hoque
- Native Thanx integration available (use it instead of building custom segments from scratch)
- Account provisioning starts Week 2 of Harol's tenure
- Flow library to rebuild from Thanx → Klaviyo:
  - Welcome (3-email sequence)
  - 2nd Purchase bounceback
  - 3rd Purchase activation
  - Winback (60-day lapsed)
  - Abandoned Cart (2h, 24h, 72h)
  - Birthday
  - Loyalty milestone
- SMS layer activates with Klaviyo SMS. Compliance: TCPA, double opt-in, STOP / HELP keywords, unsubscribe in every message.

## Send time conventions

- Email: 10am client local time on weekdays. 11am Saturday. No sends Sunday before noon.
- SMS: 11am-7pm local only. Never before 9am or after 9pm. TCPA quiet hours are 8pm-8am but Spice rule is tighter.
- Push: any time, but coordinate with email so customer doesn't get email + push within 15 minutes.

## Per-platform send limits

Do not over-send. Inbox fatigue kills opens.

- MBFS: 4-5 sends per subscriber per month max
- HealthNut: 4-5 per month max. Even though opens are high, list fatigue is real.
- Ahipoki: 6-8 per month max across email + SMS + push combined. Mike has flagged "too many emails" twice in 2025.
