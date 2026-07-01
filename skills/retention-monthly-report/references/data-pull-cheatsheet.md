# Data pull cheatsheet (Toast + Thanx)

This is the operational equivalent of the [Toast Retention Data Pull Guide](https://www.notion.so/305d3ff018e781909f5dfb9954aa620c) and the [Thanx Retention Data Pull Guide](https://www.notion.so/343d3ff018e780f38220ed7f29b5a188), condensed for in-session reference.

## Toast navigation paths

Login: `toasttab.com/restaurants/admin/home` with the client's credentials.

| Page | Path | What to grab |
|---|---|---|
| Marketing-Driven Sales | Reports > Sales > Marketing-Driven Sales | Total / In-Store / Online / App / Attributed sales + orders |
| Loyalty Insights | Guest Engagement > Loyalty Program > Insights | Sign-ups, redemptions, EDR, retention rate, sales lift |
| Marketing Dashboard | Guest Engagement > Marketing | Subscribers, sends, opens, orders, sales |
| Individual Campaign | Guest Engagement > Marketing > [campaign name] | Audience size, delivered, opened, clicked, unsubs, orders, revenue |
| Automation Flow | Guest Engagement > Marketing > Automations > [flow name] | Same fields per flow |

## Thanx navigation paths

Login: `dashboard.thanx.com` with `success@spicedigital.co`.

| View | Path | What to grab |
|---|---|---|
| Executive Summary | Dashboard home | Total members, active members, revenue from loyalty, AOV growth |
| Campaign Performance | Campaigns > [campaign name] | Opens, clicks, redemptions, revenue, control group lift |
| KPIs | Analytics > KPIs | Capture rate, activation rate, retention rate, EDR |
| Points Redemption Activity Report (new Apr 2026) | Analytics > Reports > Points Redemption | Per-campaign 14-day redemption attribution |
| Activation Funnel | Analytics > Reports > Activation Funnel | Cohort tracking by signup month |
| Customer Insights | Customers > Insights | Visit frequency, spend distribution, item preferences |

## Toast attribution quirk

Toast attribution can double-count when a customer was touched by multiple channels (e.g. email + push). This is a known Toast platform behavior. Do not manually adjust the numbers. Note it in the report's appendix if relevant.

## Thanx A/B testing quirk

Thanx automatically holds out 10% as a control group on every campaign over 5K recipients. The "revenue" number on the campaign page already nets the control lift. Do not subtract twice.

## What's NOT in either dashboard

Some metrics live outside these platforms and need to be pulled separately or noted as unavailable:

- App engagement (Toast). Request from Toast rep.
- Direct delivery platform integration revenue (Thanx). Not connected for any client. Marketplace customers are siloed.
- SMS metrics for Ahipoki. SMS not yet live. Will move into Klaviyo once migration completes.

## Screenshot storage convention

`Google Drive > [Client] > Retention > Reports > [YYYY-MM] > [page-name].png`

Use lowercase + hyphenated filenames. Example: `2026-05-marketing-dashboard.png`.

## If a page errors

- Refresh once. If still erroring, check whether Toast or Thanx is in a known maintenance window.
- If Thanx login fails, the password may have rotated. Check 1Password under "Thanx Success" entry.
- If Toast login fails, the client's account may have a session expiration. Ask the client lead (Alexandra for MBFS, Daniel for Ahipoki) to re-grant Spice access.

Do not retry indefinitely. After 2 failed attempts, surface the issue in the Slack post and proceed with whatever data is available.
