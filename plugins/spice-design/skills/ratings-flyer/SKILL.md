---
name: ratings-flyer
description: Submit a design brief for a 2-sided printed ratings flyer that drops in a restaurant client's delivery bags and drives review velocity on Uber Eats and DoorDash. Trigger on "ratings flyer for [client]", "review flyer for [client]", "flyer brief for [client]", "design a $5 flyer", "design a $10 flyer", "delivery bag flyer", "review incentive flyer", "rate and review flyer", "credit flyer", "insert flyer for [client]", or any request to create, brief, or hand off a printed flyer that offers customers a credit in exchange for leaving a review. Also trigger when the user says "we need a new ratings flyer", "refresh [client]'s flyer", "Dilli needs a flyer brief", or references designing a print asset tied to the review incentive program.
---

# Ratings Flyer Brief

Creates a new entry in the Campaign Planning DB using the "Ratings Flyer" template, then pings Dilli in #design-campaigns. Template auto-fills the brief structure. You fill the variables.

## What You Produce

1. A new Campaign Planning entry (type: Design Asset, asset type: Flyer) applied from the `Ratings Flyer` template
2. A Slack post in #design-campaigns tagging Dilli with the entry link
3. A heads-up in #int-[client]

## Hard Rule: Pull Brand Context First

Before creating the entry, fetch brand context from the client's Notion portal. Same pattern as `email-template-designer`: Client Wiki (colors, fonts, voice), Asset Library (logo files, photography), Hero Image reviews (photo direction). If any of this is missing, flag it. Do not guess.

Present a 5-line brand snapshot back to the operator before continuing:

```
[Client] | Primary: [hex] | Font: [name] | Platforms live: [UE/DD] | Photo: [best candidate filename]
```

## Step 1: Confirm Variables

Ask the operator (use `AskUserQuestion`):

1. **Credit amount + platforms** ($5 UE+DD like Ffresh, $10 UE-only like Everytable, other)
2. **Deadlines** (artwork due, client in-hand date)
3. **Print quantity** (typical: 500 to 5,000)
4. **Front headline direction** (Value-forward / Unlock / Gratitude / Custom) see `references/copy-and-layout.md`
5. **Front photo treatment** (single hero, multi-item collage, type-led, or specific Asset Library filename)

## Step 2: Create the Campaign Planning Entry from Template

Use `notion-create-pages` with:

- **Parent:** `data_source_id: 1c8d3ff0-18e7-8067-abff-000b54568283` (Campaign Planning DB)
- **Template ID:** `34cd3ff0-18e7-8010-92d4-fce622d452ab` (Ratings Flyer template)
- **Properties to set:**
  - `Campaign name`: `Ratings Flyer: [Client]: $[X]: [MMM YYYY]`
  - `Client`: relation to client's page in Clients DB (`collection://1c8d3ff0-18e7-80e9-8381-000b4448cb87`)
  - `Asset Type`: `Flyer` (prefilled by template)
  - `Entry Type`: `Design Asset` (prefilled)
  - `Service Team`: `Marketplace` (prefilled)
  - `Status`: `Brief` (prefilled)
  - `Channels`: multi-select based on operator's Q1 answer
  - `Designer`: Dilli Dias (user ID: `33bd872b-594c-81e0-937a-0002fe81f779`)
  - `Start Date`: operator's Q2 artwork-due date
  - `End Date`: operator's Q2 in-hand date
  - `Offer Details`: `$[X] credit for review on [platforms]`
  - `Locations`: from brand snapshot

The template body auto-fills with brief structure. After creating, edit the page body to swap placeholders with actual client values using `notion-update-page`.

## Step 3: Slack Handoff

Search for `#design-campaigns` via `slack_search_channels`. Post:

```
:art: *Ratings Flyer Brief: [Client]*

Credit: $[X] on [platforms]
Front: [headline direction], [photo treatment]
Artwork due: [date] | In-hand: [date] | Qty: [print run]

<@Dilli>: full brief in Campaign Planner: [page URL]
```

Then post a heads-up in `#int-[client]`:

```
Ratings flyer brief submitted. $[X] credit, 4x6 print, 2-sided. Dilli on it. Artwork target: [date]. Campaign Planner: [page URL]
```

## Step 4: Confirm Back

Return to the operator:
- Campaign Planner link
- Slack posts confirmed (#design-campaigns + #int-[client])
- Next checkpoint: Dilli's V.1 by [date]

## Iteration

Status progression follows the Campaign Planning DB defaults: `Brief` → `Design V.1` → `Internal Review` → `Client Review V.1` → `Final Client Review` → `Client Approved` → `Scheduled` → `Complete`. Route revisions by commenting on the Planner entry, not re-pinging Slack.

## Escalation

- Credit outside $5-$15: confirm with Growth Manager before creating
- First flyer for a new client: flag "needs client approval" and hold Dilli ping
- Deadline under 48 hours: flag Maxx in Slack before registering

## Reference Files

| File | Use |
|------|-----|
| `references/copy-and-layout.md` | Headline options, supporting line variants, front/back layout directions, Ffresh and Everytable annotated examples |

## Template Page

Template lives at: `https://www.notion.so/34cd3ff018e7801092d4fce622d452ab`
Template ID: `34cd3ff0-18e7-8010-92d4-fce622d452ab`

If the template is ever edited in Notion, no skill changes are needed. The skill points at the template ID and Notion auto-fills the body + prefilled properties (Asset Type: Flyer, Entry Type: Design Asset, Service Team: Marketplace, Status: Brief).
