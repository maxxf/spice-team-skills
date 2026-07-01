---
name: retention-campaign-brief
description: Use this skill to draft a complete retention campaign brief for MBFS, HealthNut, or Ahipoki. Triggers include "draft retention brief for [client]", "brief a retention campaign", "create campaign for [client] [date]", "rough in a brief for [client]", "build [campaign type] for [client]", "winback brief for [client]", "promo brief for [client]", "loyalty brief for [client]", or any combo of client + campaign topic + send date. Output is copy draft + Campaign Planning DB entry in Notion + design brief posted to #design-requests + reminder set 2 days before send. Replaces the existing campaign-brief-creator for retention work because it adds segment selection, channel mix, suppression rules, and per-client voice handling.
---

# Retention Campaign Brief

A retention campaign brief is the single source document a designer, a strategist, and a platform operator can all execute from without asking questions. If anyone needs to DM you to clarify after reading it, the brief failed.

## Inputs you need

If the user did not provide them, ask once for whatever is missing. Do not ask one at a time.

1. **Client**: MBFS | HealthNut | Ahipoki
2. **Campaign objective**: promo | seasonal | LTO | re-engagement | winback | loyalty milestone | review request | welcome refresh
3. **Target segment**: see `references/segments.md` for the canonical options per platform
4. **Offer**: dollar off, % off, free item, BOGO, or no offer (announcement only)
5. **Send date**: ISO date. Determines the design deadline (send date minus 5 business days)
6. **Channels**: email, SMS, push. Default to email + push for Thanx clients, email + SMS for Toast / Klaviyo if SMS is live.
7. **Anything client-specific the operator should know**: e.g. "Mike asked for this on Monday's call", "use the new hero image from Dilli's June batch"

## Required tools

- Notion MCP (create brief page, register in Campaign Planning DB)
- Slack MCP (post to `#design-requests`)
- Google Calendar MCP (set reminder 2 days before send)
- **Figma MCP** (`get_design_context`, `get_variable_defs`, `get_screenshot` on the client's brand library file — pull actual brand colors, fonts, and approved hero shots instead of describing them in prose)
- **Klaviyo MCP** (for Ahipoki — validate the segment exists, optionally pre-create the campaign shell with `create_campaign`)

## Process

Run these phases in order. Do not skip the suppression rules step. Suppression rules are the most-missed item across the retention service.

### Phase 1: Load client context

Read `references/client-voice.md` and pull the section for the requested client. Read `references/platform-rules.md` and pull the section for the platform the client is on.

If Figma MCP is connected, also call `get_variable_defs` on the client's Figma brand library to pull current brand colors and typography. This catches drift between the brief's stated brand colors and what Dilli is actually shipping.

### Phase 2: Draft the brief

Output the brief as a Notion-ready document with these blocks:

1. **Campaign name** — Format: `[Client] | [Campaign type] | [Send month YYYY]`. Example: `Ahipoki | Winback | June 2026`.
2. **Objective** — One sentence. Specific. "Reactivate Ahipoki loyalty members who have not visited in 60+ days using a points-expiring offer."
3. **Target segment** — Exact segment definition (filters, count if known, platform name)
4. **Offer + promo code** — Code format: `[Client prefix][Type][##]`. Ahipoki uses `SP |` prefix. MBFS uses descriptive codes like `COMEBACK15`. Include validity window and minimums.
5. **Send timing** — Date, time of day (default 10am client timezone), and channel sequence (e.g. email first, SMS 24h later if no click).
6. **Suppression rules** — List of segments to exclude. Always exclude: unsubscribed, recent complaints, refund recipients in last 14 days. Plus campaign-specific (e.g. winback excludes recent purchasers).
7. **Subject line + preview** — Provide 3 options for A/B. Use voice rules in `references/client-voice.md`. Do not use emdashes.
8. **Body copy** — Full email copy, 100-200 words, with placeholders for personalization tokens. Sentence case headings. No "here's the thing". No "level up".
9. **Hero / visual direction** — One sentence describing what the designer should produce. Example: "Hero image: signature ahi bowl, top-down, on white surface, with overlaid 'Your points expire soon' text in Ahipoki teal."
10. **Primary + secondary CTA** — Exact button text and URL pattern.
11. **Success metrics** — Per-campaign-type benchmarks from `references/benchmarks.md`. Always include open rate, CTR, revenue per recipient, redemption rate.
12. **QA checklist link** — Link to the `retention-qa-checklist` skill output that must run before send.

### Phase 3: Register in Campaign Planning DB

Create a new entry in the [Campaign Planning database](https://www.notion.so/Campaign-Planning) in Notion with:

- Client (relation)
- Campaign name
- Platform
- Channels
- Status: "Briefed"
- Send date
- Designer (default Dilli)
- Strategy Lead (Daniel for Ahipoki, leave blank for others)
- Brief URL (link to the Notion brief just created)
- Revenue (leave blank, populated post-send by `retention-monthly-report`)

### Phase 4: Design brief to #design-requests

Post to Slack `#design-requests` using this template:

```
:art: New retention brief — [Campaign name]

*Client*: [Client]
*Send date*: [Date]
*Design deadline*: [Send date minus 5 business days]
*Brief*: [Notion URL]
*Hero direction*: [One-line from the brief]
*Specs*: [pull from references/design-specs.md based on platform]

Brief by: Harol | Designer: Dilli
```

Tag Dilli in the post.

### Phase 5: Set the reminder

Create a calendar reminder (Google Calendar MCP) for 2 business days before the send date with title `QA + schedule: [Campaign name]`. The reminder fires the `retention-qa-checklist` skill.

### Phase 6 (Ahipoki only, Klaviyo MCP connected)

Pre-create the campaign shell in Klaviyo via `create_campaign` so it appears in Harol's Klaviyo dashboard ready for template assignment once Dilli ships the design. Pass the Klaviyo campaign ID back into the Campaign Planning DB row so it's traceable end-to-end.

## Definition of done

- Notion brief exists and is linkable
- Campaign Planning DB entry exists
- `#design-requests` post is live and Dilli is tagged
- Reminder is scheduled
- Strategy Lead (Daniel for Ahipoki) is tagged in the Notion brief if applicable

## Style enforcement

Before returning, scan the brief for:

- Any emdash → replace with a period or parens
- Any phrase matching "it's not about X, it's about Y" → rewrite
- Any sentence starting with "Here's the thing" or "Here's the kicker" → delete
- Any "level up" or "supercharge" → rewrite to something specific
- Any AI giveaways ("delve", "in today's fast-paced world", "leveraging", "robust") → rewrite

If you find any of the above, fix before returning. Do not return draft copy that needs the user to scrub it.

## References

- `references/client-voice.md` — per-client voice + brand voice rules
- `references/segments.md` — canonical segment definitions per platform
- `references/platform-rules.md` — Thanx, Toast, Klaviyo specifics
- `references/benchmarks.md` — open / click / revenue benchmarks by campaign type
- `references/design-specs.md` — image dimensions + asset requirements per platform
