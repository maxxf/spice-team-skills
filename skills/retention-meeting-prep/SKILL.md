---
name: retention-meeting-prep
description: Use this skill before the Spice Retention bi-weekly sync to auto-fill the Retention Weekly template in Notion with live performance data, fulfillment status, and anomaly flags. Triggers include "prep retention meeting", "prep for retention sync", "build the retention weekly", "retention bi-weekly prep", "fill the retention meeting template", or any request to ready the recurring retention review. The default cadence is bi-weekly on Mondays. Output is a pre-filled Notion meeting page + a Slack heads-up to attendees.
---

# Retention Meeting Prep

The bi-weekly retention sync runs Monday with Maxx, Harol, Daniel, Rodrigo, and Dilli rotating in. Pre-filling the template before the meeting cuts the meeting from a status report to a decision forum.

## Inputs

- **Meeting date**: defaults to next Monday if not specified
- **Clients to cover**: defaults to all three (MBFS, HealthNut, Ahipoki). Override only if a client is on pause.

## Required tools

- Notion (read Campaign Planning DB, read Retention Weekly template, write new meeting page)
- Slack (post heads-up)
- Chrome MCP (light Toast / Thanx pulls — same data the `retention-monthly-report` skill uses, but only the last 14 days)

## Process

### Phase 1: Duplicate the template

Find the [Retention Weekly Template](https://www.notion.so/2bfd3ff018e780179ec9c9be0bcb21ad) in Notion. Duplicate it. Title the new page: `Retention Weekly [MM.DD]`. Add to the Retention Meetings database.

### Phase 2: Fill the campaign performance table

For each of MBFS, HealthNut, Ahipoki, pull last 14 days of:

- Email Revenue
- Orders
- Automation Revenue

Source: Toast (MBFS, Ahipoki Toast side) and Thanx (HealthNut, Ahipoki Thanx side). Once Klaviyo is live, pull Ahipoki Klaviyo data too.

Fill the table rows. No empty cells. If a number is unavailable, write "data pending" and surface in the anomaly section.

### Phase 3: Pull fulfillment status

Query the Campaign Planning DB. Filter by status in (`Briefed`, `In Design`, `Scheduled`, `Sent`, `Missed`) and send date in the last 14 days OR next 14 days.

Populate the fulfillment section:

- **Sent**: campaigns that went out, with actual revenue
- **Scheduled**: campaigns built in platform, ready to send
- **In Design**: campaigns with brief out to Dilli but no creative back yet
- **Briefed**: campaigns with brief but design not yet started
- **Missed**: anything past send date still marked Briefed / In Design / Scheduled (this is a red flag — list and tag the owner)

### Phase 4: Anomaly flags

Auto-flag any of the following:

- Open rate on any campaign below 20% (HealthNut threshold is higher — flag below 50% for them)
- Any automation flow with zero sends in past 14 days
- Any campaign past scheduled date but not sent (cross-ref with Campaign Planning DB)
- Loyalty enrollment drop >10% week-over-week
- Unsubscribe rate >2% on any send
- EDR above 4% for any client (over-discounting)
- Capture rate below 13% on Ahipoki (Thanx benchmark)

Put flags in a top-of-page "Watch list" callout block. Make it the first thing the reader sees.

### Phase 5: Pre-meeting Slack heads-up

Post to `#retention-marketing`:

```
:calendar: Retention bi-weekly [MM.DD] is prepped.

Template: [Notion URL]

*Headline numbers*:
- MBFS: $X email revenue (X campaigns sent)
- HealthNut: $X (X campaigns)
- Ahipoki: $X (X campaigns)

*Watch items*: [count]
*Decisions needed at this meeting*: [list any flagged for human input]

Read before we start.
```

Tag attendees: Maxx, Harol, Daniel, Rodrigo, Dilli.

## Definition of done

- Notion meeting page duplicated, titled, filled
- Campaign performance table has real numbers (no blanks)
- Fulfillment section matches Campaign Planning DB
- Watch list callout at top with all anomalies
- Slack heads-up posted at least 2 hours before meeting starts

## What this skill is NOT

- Not the monthly report. That's a separate skill (`retention-monthly-report`) with deeper data + screenshots.
- Not a generic meeting prep. Tied specifically to the Retention Weekly template structure.
- Not for ad-hoc syncs. Use `client-call-prep` for those.

## Recovery if data is missing

If Toast or Thanx is unavailable when this runs, fill what you can and note in the watch list: "Data pull for [client] failed at [time]. Re-run before meeting." Do not block the prep.
