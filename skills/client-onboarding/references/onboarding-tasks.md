# Onboarding Task Templates by Service

## Shared Tasks (Create Once Only)

These tasks are common across all services. Create only ONE instance per client, regardless of how many services selected.

| Task | Phase | Days | Default Owner | Notes |
|------|-------|------|---------------|-------|
| Create internal Slack channel (#int-[client]) | Kickoff | 0 | Client Services Lead | Invite relevant Spice team members (Service Lead, supporting team). |
| Create external Slack channel (#ext-[client]-spice) or WhatsApp group | Kickoff | 0 | Client Services Lead | If client lacks paid Slack, create WhatsApp group and integrate via 2Chat. Invite client POC. |
| Confirm Payment On File in Stripe | Kickoff | 1 | Client Services Lead | Payment link created automatically during onboarding. The Lead verifies client completed payment by asking "did [client] pay?" or checking Stripe. |

Tag shared tasks with the **first** selected service.

## Delivery Marketplaces

| Task | Phase | Days | Default Owner | Notes |
|------|-------|------|---------------|-------|
| Client completes onboarding form w/ login credentials | Access & Setup | 5 | Client Services Lead | Form link: https://spice-digital.notion.site/1c8d3ff018e780f5821ff8b52e709724. Once submitted, transfer platform logins to client credential DB. |
| Get intros to platform account managers | Access & Setup | 5 | Assigned by Client Services Lead | Request introductions to UE, DD, GH account reps for each location. |
| Confirm Access to 3P & Menu Manager (Deliverect, etc.) | Access & Setup | 7 | Assigned by Client Services Lead | Verify login access to all platforms and menu management tools. |
| Connect Loop AI - Analytics Platform | Access & Setup | 10 | Assigned by Client Services Lead | Connect all 3P platforms to Loop. Upsell Loop chargeback manager (30% of won disputes). Request COGs sheet from client. |
| Run Diagnostics on 3P & Build Action Plan | Audit | 10 | Assigned by Client Services Lead | Use storefront-audit skill once access is confirmed. Score hero images, menu structure, pricing, promos, competitive positioning. Output to client Document Hub. |
| Draft Optimized Menu Sheet | Audit | 14 | Assigned by Client Services Lead | Use optimized-menu-sheet skill. Informed by storefront audit findings. Include keyword optimization, category consolidation, pricing strategy. |
| Ratings Boost Flyer Design | Build & Launch | 14 | Assigned by Client Services Lead | Brief design team (Fabio/Michelle/Morena) on ratings boost flyer for in-store display. Target: Top Eats (UE) and Most Loved (DD) badges. |
| Draft Campaign Plan & Share w/ Client | Build & Launch | 14 | Assigned by Client Services Lead | Plan promo/ads strategy for Month 1. Include BOGO, Spend X Save Y, and ads budget. Test for 1 full month before iterating. |
| Implement Menu Optimizations & New Images | Build & Launch | 17 | Assigned by Client Services Lead | Execute menu sheet changes across all platforms. Coordinate hero image and menu photo updates. |
| Implement Campaign Plan | Build & Launch | 21 | Assigned by Client Services Lead | Launch promotions and ads per the approved campaign plan. Set up Uber Advanced Ads if applicable. |
| Create Master Tracking Sheet | Build & Launch | 21 | Assigned by Client Services Lead | Set up weekly tracking sheet for campaign performance, experiments log, and KPIs. Link in client space. |

**Total: 11 unique + 3 shared = 14 tasks**

## Retention

| Task | Phase | Days | Default Owner | Notes |
|------|-------|------|---------------|-------|
| Client completes onboarding form w/ ESP credentials | Access & Setup | 5 | Client Services Lead | Collect ESP (Klaviyo, Mailchimp, etc.) and loyalty platform credentials. |
| Confirm Access to ESP & Loyalty Platform | Access & Setup | 7 | Assigned by Client Services Lead | Verify login access and permissions to all retention platforms. |
| Audit existing flows and list health | Audit | 10 | Assigned by Client Services Lead | Review existing automations, list size, engagement rates, deliverability. |
| Draft Lifecycle Flow Plan | Audit | 14 | Assigned by Client Services Lead | Map welcome, abandoned cart, post-purchase, win-back, and VIP flows. |
| Build Core Flows in ESP | Build & Launch | 21 | Assigned by Client Services Lead | Implement the lifecycle flow plan in the ESP. |
| Draft Campaign Calendar (First 30 Days) | Build & Launch | 14 | Assigned by Client Services Lead | Plan first month of email/SMS campaigns. |
| Implement First Campaign | Build & Launch | 17 | Assigned by Client Services Lead | Launch first scheduled campaign per calendar. |
| Set Up List Growth Tracking | Build & Launch | 21 | Assigned by Client Services Lead | Configure tracking for subscriber growth, opt-in rates, list health. |
| Build Lapsed Customer Flows | Optimize | 30 | Assigned by Client Services Lead | Target lapsed customers with re-engagement sequences. |

**Total: 9 unique + 3 shared = 12 tasks**

## Paid Acquisition

| Task | Phase | Days | Default Owner | Notes |
|------|-------|------|---------------|-------|
| Client completes onboarding form w/ ad account access | Access & Setup | 5 | Client Services Lead | Collect Meta, Google, TikTok ad account access and pixel info. |
| Confirm Access to Ad Accounts & Pixel | Access & Setup | 7 | Assigned by Client Services Lead | Verify login access, pixel installation, and conversion tracking. |
| Audit existing campaigns and performance | Audit | 10 | Assigned by Client Services Lead | Review current campaigns, spend, ROAS, creative performance. |
| Draft Creative Brief | Audit | 12 | Assigned by Client Services Lead | Brief for initial ad creative. Coordinate with design team. |
| Draft Media Plan & Budget Allocation | Build & Launch | 14 | Assigned by Client Services Lead | Allocate budget across platforms, audiences, and campaign types. |
| Build Campaign Structure | Build & Launch | 17 | Assigned by Client Services Lead | Set up campaigns, ad sets, audiences in platform. |
| Launch First Campaigns | Build & Launch | 21 | Assigned by Client Services Lead | Go live with first campaign set. |
| Set Up Reporting Dashboard | Build & Launch | 21 | Assigned by Client Services Lead | Configure weekly/monthly performance reporting. |

**Total: 8 unique + 3 shared = 11 tasks**

## Advisory

| Task | Phase | Days | Default Owner | Notes |
|------|-------|------|---------------|-------|
| Schedule recurring weekly/bi-weekly call | Kickoff | 3 | Maxx | Advisory calls are Maxx-led. Set recurring calendar event. |
| Gather key docs & context | Access & Setup | 7 | Maxx | Collect P&Ls, platform data, org chart, growth goals. |
| Draft 90-Day Growth Roadmap | Audit | 14 | Maxx | Build strategic roadmap based on diagnostics and client goals. |
| Present Roadmap to Leadership | Build & Launch | 21 | Maxx | Deliver roadmap presentation to client leadership team. |

**Total: 4 unique + 3 shared = 7 tasks**

---

## Task Owner Logic

- **Advisory tasks**: Always owned by Maxx. Advisory is Maxx-led, not delegated.
- **Shared tasks**: "Slack/WhatsApp" owned by the Client Services Lead. "Stripe" owned by Maxx.
- **All other tasks**: Default to the Client Services Lead. Lead reassigns to Rui, Rodrigo, or other team members based on workload and client needs.

## Status Defaults

- New tasks: `Not Started`
- First task (Slack/WhatsApp setup): Mark `Done` immediately if already completed at kickoff
- Tasks waiting on client info: `Waiting on Client`

## Skill Integration Map

When creating tasks, include the relevant SKILL trigger in the "Notes / Links" field so the Client Services Lead or any team member using Cowork knows exactly what to say.

| Task | Skill | Trigger Phrase (in Notes) |
|------|-------|---------------------------|
| Confirm Payment On File in Stripe | Stripe lookup | `SKILL: Say "did [client] pay?" to check payment status in Stripe.` |
| Gather key docs & context (Advisory) | client-call-prep | `SKILL: Say "prep for [client] call" to pull all available context.` |
| Run Diagnostics on 3P & Build Action Plan | storefront-audit | `SKILL: Say "audit [client] storefronts" to run full 3P audit.` |
| Draft Optimized Menu Sheet | optimized-menu-sheet | `SKILL: Say "build menu sheet for [client]" to generate .xlsx blueprint.` |
| Draft 90-Day Growth Roadmap (Advisory) | client-call-prep + pptx | `SKILL: Say "prep for [client] call" for context, then use pptx skill for deck.` |
| Present Roadmap to Leadership (Advisory) | pptx | `SKILL: Say "create presentation for [client] roadmap" to build the deck.` |
| Draft Campaign Plan & Share w/ Client | client-call-prep | `SKILL: Say "prep for [client] call" to pull context before drafting.` |
| Ratings Boost Flyer Design | response-drafting | `SKILL: Say "draft response to design team" for the creative brief.` |
| Create Master Tracking Sheet | xlsx + weekly-reporting | `SKILL: Say "create spreadsheet for [client] tracking" to build the sheet.` |
| Audit existing flows and list health (Retention) | — | Manual audit. No skill yet. |
| Audit existing campaigns (Paid) | — | Manual audit. No skill yet. |

Replace `[client]` with the actual client name when creating tasks.
