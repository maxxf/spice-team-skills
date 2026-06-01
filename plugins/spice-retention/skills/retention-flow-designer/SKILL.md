---
name: retention-flow-designer
description: Use this skill to design or rebuild an automated flow on Thanx or Klaviyo. Covers winback, welcome, post-purchase bounceback, abandoned cart, birthday, loyalty milestone, and SMS sequences. Triggers include "design winback for [client]", "build welcome flow for [client]", "create cart abandon for [client]", "loyalty milestone flow", "birthday automation", "post-purchase bounceback", "SMS sequence for [client]", "[client] flow rebuild", or any request to design or rebuild a marketing automation. Output is a flow spec (triggers, sequence, copy, channels, suppression) + Notion brief + handoff to design via #design-requests. Does not actually configure the platform — that's still manual on Thanx and Klaviyo.
---

# Retention Flow Designer

A flow is a sequence of triggered messages that fires automatically based on customer behavior or attributes. Done well, flows are the highest-ROI retention work. Done poorly, they spam the list and drive unsubs.

## Required tools

- Notion (write flow spec)
- Slack (post design brief to `#design-requests`)
- **Klaviyo MCP** (for Ahipoki — `get_campaigns` to confirm flow doesn't already exist, `create_campaign` + `assign_template_to_campaign_message` to spin up the first send, `get_catalog_items` for menu-item references)
- **Figma MCP** (`get_design_context`, `get_screenshot`, `get_variable_defs` on the client's brand library — pull real brand colors and approved hero images instead of guessing)

## Inputs

1. **Client**: MBFS | HealthNut | Ahipoki
2. **Flow type**: see catalog below
3. **Platform**: Thanx | Klaviyo | Toast (for MBFS automations)
4. **Channels**: email | SMS | push (which to include in this flow)
5. **Trigger**: behavior or attribute that fires the flow
6. **Goal**: specific outcome (e.g. "drive 2nd visit within 14 days")

## Flow catalog

Each flow type has a standard skeleton. Adapt to the client.

### Welcome (3-email sequence)

- **Trigger**: new email subscriber (loyalty signup or online order email capture)
- **Goal**: drive first or next purchase within 7 days
- **Sequence**:
  - Email 1 — Immediate. Welcome + brand intro + first offer (5-10% off OR free side OR loyalty points bonus).
  - Email 2 — Day 3 if offer unused. Reminder + social proof.
  - Email 3 — Day 8 if still unused. Final reminder + urgency.
- **Suppression**: anyone who placed an order after the trigger
- **Benchmark**: Open 50%+, CTR 15%+, conversion 25% within 7 days

### Winback (60-day lapsed)

- **Trigger**: customer with no order in 60 days
- **Goal**: reactivate within 14 days
- **Sequence**:
  - Email 1 — Day 60. Soft re-engagement + offer (15% off, 1 month validity).
  - SMS — Day 67. If no email click. Short, punchy: "$10 off, this week only, link in profile."
  - Email 2 — Day 75. Final attempt + emotional appeal.
- **Suppression**: any purchase since trigger, unsubscribed, refund last 14 days
- **Benchmark**: Open 35-40%, redemption 5-8%, return rate 10% within 14 days. Thanx reports 6x ROI average.

### Post-purchase bounceback (1st → 2nd visit)

- **Trigger**: first-ever order completed
- **Goal**: drive 2nd visit within 14 days
- **Sequence**:
  - Email 1 — Day 3 post-order. Thanks + suggestion (other menu items).
  - Email 2 — Day 7. Bounceback offer (free side or 10% off next order).
  - Email 3 — Day 12. Last call on bounceback offer.
- **Suppression**: any purchase since trigger
- **Benchmark**: 25-30% conversion within 14 days

### Abandoned cart

- **Trigger**: items added to cart, no purchase
- **Goal**: recover the order
- **Sequence**:
  - Email 1 — 2 hours. Friendly nudge, cart contents shown.
  - Email 2 — 24 hours. Reminder + small incentive (free delivery or 5% off).
  - Email 3 — 72 hours. Last chance + bigger nudge (only if 0% recovery from email 1+2 historically).
- **Suppression**: cart completed
- **Benchmark**: 10-15% recovery rate

### Birthday

- **Trigger**: 7 days before birthday (auto-send)
- **Goal**: drive a birthday visit
- **Sequence**: Single email. Birthday treat (free item, double points, or % off).
- **Benchmark**: Open 50-60%, redemption 45-60%, AOV +31% vs baseline

### Loyalty milestone (tier upgrade)

- **Trigger**: customer reaches new tier threshold
- **Goal**: reinforce loyalty + drive next visit
- **Sequence**: Single email. Congrats + new tier benefits + CTA.
- **Benchmark**: Open 55-65%, CTR 20-25%, order within 7 days 30%+

### Points expiring (Ahipoki-specific, high-value)

- **Trigger**: customer has > 100 points expiring within next 30 days
- **Goal**: drive redemption visit
- **Sequence**:
  - Email 1 — 30 days before expiry. "Your points are about to expire."
  - SMS — 14 days before expiry. "[X] free bowls expiring. Redeem now."
  - Email 2 — 3 days before expiry. Final warning.
- **Why this matters**: 103K points expired at Ahipoki in March 2026 with no recovery campaign. This is sitting revenue.
- **Benchmark**: 15-25% redemption rate, > 50% open rate (high urgency)

### SMS-only (Ahipoki, post-Klaviyo)

- **Use cases**: order confirmation, ready-for-pickup, time-limited offer (under 24h)
- **Compliance**: TCPA, double opt-in, STOP/HELP keywords, never before 9am or after 9pm local
- **Frequency cap**: max 4 SMS per subscriber per month across all flows
- **Always include**: brand name in first 30 chars + STOP keyword on every series-opener

## Process

### Phase 1: Confirm the flow type + platform

Ask if not specified. Pull the skeleton from above.

### Phase 2: Draft the spec

Output a Notion-ready document with:

1. **Flow name**: `[Client] | [Flow type] | [vN]`
2. **Trigger definition**: precise filter (e.g. `last_purchase_date <= NOW - 60 days AND total_orders >= 1`)
3. **Goal + benchmark**: pulled from the skeleton above
4. **Sequence**: every step, with timing, channel, subject/SMS body, CTA, exit conditions
5. **Suppression rules**: explicit list
6. **Copy for each message**: full draft, voice rules applied, in `retention-campaign-brief` format
7. **A/B test plan** (if list is over 5K): control vs variant
8. **Setup checklist**: platform-specific steps (Thanx vs Klaviyo) to configure
9. **QA criteria**: how to validate before activation

### Phase 3: Brief design (if creative is needed)

If the flow needs visuals (welcome, milestone, birthday), post to `#design-requests` with the design brief format from `retention-campaign-brief/references/design-specs.md`.

### Phase 4: Register in Campaign Planning DB

Create an entry with status `Flow Design`. Tag the flow as a recurring asset, not a one-off campaign.

## Output to user

End with a single-line summary:
```
[Flow name] designed. Notion: [link]. Design: [Slack URL or "no creative needed"]. Setup: [Thanx | Klaviyo] manual, ~[X] hours.
```

## Platform implementation notes

### Thanx (HealthNut, Ahipoki existing)
- Configure in: Dashboard > Automated Campaigns
- Native A/B with 10% control group auto-applied
- SMS not yet live for Ahipoki, design for email + push only until enabled

### Klaviyo (Ahipoki, post-migration)
- Configure in: Flows > Create New
- Trigger types: List, Segment, Metric, Date-Based
- SMS layer requires phone collection + double opt-in
- Use the native Thanx integration as the data source
- **For the first campaign in a new flow**: use the Klaviyo MCP `create_campaign` tool to spin it up directly. Then `assign_template_to_campaign_message` once Dilli's Figma design is exported. Flow configuration itself (triggers, branches, timing) still needs to happen in the Klaviyo dashboard — the MCP doesn't expose flow builder yet.

### Toast (MBFS)
- Configure in: Guest Engagement > Marketing > Automations
- Limited trigger options compared to Thanx / Klaviyo. Welcome, Winback, Bounceback, Birthday available natively.

## What this skill is NOT

- Not platform configuration. The skill designs the flow. A human (Harol or platform vendor) builds it in the dashboard.
- Not a one-off campaign brief. That's `retention-campaign-brief`.
- Not Klaviyo migration. That's `klaviyo-migration`.
