# Onboarding Task Templates by Service

## Shared Tasks (Create Once Only)

These tasks are common across all services. Create only ONE instance per client, regardless of how many services selected.

| Task | Phase | Days | Default Owner | Notes |
|------|-------|------|---------------|-------|
| Create internal Slack channel (#int-[client]) | Kickoff | 0 | Client Services Lead | Invite relevant Spice team members (Service Lead, supporting team). |
| Set up client comms channel: Slack Connect or WhatsApp | Kickoff | 0 | Client Services Lead | Client chooses. Preferred: Slack Connect channel (#ext-[client]-spice). If client prefers WhatsApp (or lacks paid Slack), create a WhatsApp group and bridge it into Slack via 2Chat. Invite client POC. |
| Confirm Payment On File in Stripe | Kickoff | 1 | Client Services Lead | Payment link created automatically during onboarding and sent by Maxx/Diline in the kickoff email. The Lead verifies client completed payment by asking "did [client] pay?" or checking Stripe. |
| Update Figma kickoff deck (present on kickoff call) | Kickoff | 0 | Dilli Dias (design) | Assigned to Dilli to update as soon as the deal is Closed Won: duplicate the Kick-Off Figma Slides template, update client name/logo and service scope. Onboarding lead schedules the call and presents; Maxx attends DM/multi-service kickoffs for the formal handoff. |

Tag shared tasks with the **first** selected service.

## Delivery Marketplaces

| Task | Phase | Days | Default Owner | Notes |
|------|-------|------|---------------|-------|
| Client completes onboarding form w/ login credentials | Access & Setup | 5 | Client Services Lead | Form link: https://spice-digital.notion.site/1c8d3ff018e780f5821ff8b52e709724. Once submitted, transfer platform logins to client credential DB. |
| Get intros to platform reps + request Advanced Ads enablement | Access & Setup | 5 | Assigned by Client Services Lead | Request AM intros for UE, DD, GH per location. **In the same request, ask each rep to enable the advanced ads platform** for all locations: Uber Eats Ads Manager (Advanced Ads), DoorDash Ads Manager (self-serve sponsored listings), Grubhub sponsored listings / loyalty tools. Rep enablement lags the request — track per location. |
| Confirm Access to 3P, Menu Manager & Advanced Ads | Access & Setup | 7 | Assigned by Client Services Lead | Verify login access to all platforms + menu management tools. Grant access as **individual seats** per person under the `ops@spicedigital.co` alias with 2FA (never shared logins; use platform-native roles). Gate check: confirm the advanced ads platform is actually live on all 3 (not just base portal access) before campaign build — flag any store where the upgrade didn't flip on. |
| Connect Spicy analytics data sync | Access & Setup | 10 | Assigned by Client Services Lead | Connect all 3P merchant portals + ad platforms to the Spicy data pipeline (persistent browser sessions on the Mac Mini; 2FA routes to success@spicedigital.co). Powers dashboards, CSV exports, and order-level financials. Request the client's COGs sheet for margin analysis. |
| Run Diagnostics on 3P & Build Action Plan | Audit | 7 | Assigned by Client Services Lead | Kick off as soon as platform access is confirmed (target Day 7, latest). Use storefront-audit skill. Score hero images, menu structure, pricing, promos, competitive positioning. Output to client Document Hub. |
| Draft Optimized Menu Sheet | Audit | 14 | Assigned by Client Services Lead | Use optimized-menu-sheet skill. Informed by storefront audit findings. Include keyword optimization, category consolidation, pricing strategy. |
| Ratings Boost Flyer Design | Build & Launch | 14 | Assigned by Client Services Lead | Brief the design team (Dilli) on a ratings boost flyer for in-store display. Target: Top Eats (UE) and Most Loved (DD) badges. |
| Draft Campaign Plan & Share w/ Client | Build & Launch | 14 | Assigned by Client Services Lead | Plan promo/ads strategy for Month 1. Include BOGO, Spend X Save Y, and ads budget. Test for 1 full month before iterating. |
| Implement Menu Optimizations & New Images | Build & Launch | 17 | Assigned by Client Services Lead | Execute menu sheet changes across all platforms. Coordinate hero image and menu photo updates. |
| Implement Campaign Plan | Build & Launch | 21 | Assigned by Client Services Lead | Launch promotions and ads per the approved campaign plan. Set up Uber Advanced Ads if applicable. |
| Create Master Tracking Sheet | Build & Launch | 21 | Assigned by Client Services Lead | Set up weekly tracking sheet for campaign performance, experiments log, and KPIs. Link in client space. The Spicy dashboard is the primary source of truth for performance data; this manual sheet runs alongside it as the client-facing / backup view. |

**Total: 11 unique + 4 shared = 15 tasks**

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

**Total: 9 unique + 4 shared = 13 tasks**

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

**Total: 8 unique + 4 shared = 12 tasks**

## Advisory

| Task | Phase | Days | Default Owner | Notes |
|------|-------|------|---------------|-------|
| Schedule recurring weekly/bi-weekly call | Kickoff | 3 | Maxx | Advisory calls are Maxx-led. Set recurring calendar event. |
| Gather key docs & context | Access & Setup | 7 | Maxx | Collect P&Ls, platform data, org chart, growth goals. |
| Draft 90-Day Growth Roadmap | Audit | 14 | Maxx | Build strategic roadmap based on diagnostics and client goals. |
| Present Roadmap to Leadership | Build & Launch | 21 | Maxx | Deliver roadmap presentation to client leadership team. |

**Total: 4 unique + 4 shared = 8 tasks**

---

## Task Owner Logic

- **Advisory tasks**: Always owned by Maxx. Advisory is Maxx-led, not delegated.
- **Shared tasks**: Slack channels + comms owned by the Client Services Lead. Stripe payment confirmation owned by Maxx. The Figma kickoff deck is owned by Dilli (design), who updates it post-Closed Won; the onboarding lead presents it on the kickoff call.
- **All other tasks**: Default to the Client Services Lead. Lead reassigns to the pod (e.g. Santiago/Rodrigo GM, Manish ops analyst, Dilli design) based on workload and client needs.

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
| Connect Spicy analytics data sync | — | Connect via the Spicy pipeline on the Mac Mini. No Cowork skill trigger yet. |
| Audit existing flows and list health (Retention) | — | Manual audit. No skill yet. |
| Audit existing campaigns (Paid) | — | Manual audit. No skill yet. |

Replace `[client]` with the actual client name when creating tasks.

---

## Onboarding Form — Expanded Fields (proposed, pending Notion update)

The current Notion onboarding form collects logins + a few asset links. The expanded set
below gathers everything the team otherwise chases down manually in the first two weeks.
**Proposed — the live Notion form has not been changed yet; awaiting approval.**

**Contacts & access**
- Main POC (name, email, phone) + role
- Billing contact (name, email)
- Escalation / decision-maker contact
- Known platform account-manager names + emails (UE / DD / GH), if any

**Platform logins** (existing — keep)
- Delivery platforms: UE / DD / GH (per location)
- POS / integrator (Toast, Square, Deliverect, OLO, etc.)
- Direct-ordering platform
- Email marketing / ESP + loyalty (Retention)
- Ad accounts + pixel (Paid)

**Financials & goals** (new)
- COGs by item or category (or link to a sheet)
- Target margins / net-payout goal
- Current monthly 3P sales + marketing spend, by platform
- Primary growth goal for the engagement

**Menu & brand** (new)
- Brand assets folder (logo, brand colors, fonts)
- Menu photos folder
- Top-selling items
- Items to push / de-emphasize

**Operations** (new)
- Hours + holiday closures per location
- Locations list with addresses + which platforms are live on each
- Tax / service-fee settings, if the client manages them
- Current promos / ads running
- Known competitor set (for the storefront audit)

Once approved, this becomes the field spec for updating the Notion form at
`https://spice-digital.notion.site/1c8d3ff018e780f5821ff8b52e709724`.
