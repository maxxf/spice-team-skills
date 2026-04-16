---
name: gm
description: "Daily morning brief for Maxx. Trigger on 'gm', 'good morning', 'morning brief', 'daily brief', 'what's on today', 'what do I have today', 'daily rundown', 'start my day', 'morning update', or any request for a summary of today's schedule, tasks, and overnight activity. Also trigger when Maxx asks 'what did I miss', 'overnight updates', or 'catch me up'."
---

> **Spicy Nugget handoff:** This runs on Mac Mini as GM Daily Brief (weekdays 6:30am PT). Don't run on laptop unless Spicy is down.

# GM - Daily Morning Brief

Compile Maxx's daily morning brief: today's calendar, open tasks, overnight emails, and Slack activity. Present as a scannable, prioritized rundown he can read in under 2 minutes.

## Data Sources

1. **Google Calendar** — Today's events via `gcal_list_events`
2. **Notion Team Task Tracker** — Maxx's open tasks (data source: `1c8d3ff0-18e7-80f0-a36b-000b6befe5b1`)
3. **Gmail** — Overnight emails via `gmail_search_messages`
4. **Slack** — Overnight messages in key channels

## Reference IDs

- Maxx's Notion user ID: `c249c8bc-e33f-4b35-b4f8-c9b22117cccc`
- Team Task Tracker data source: `1c8d3ff0-18e7-80f0-a36b-000b6befe5b1`
- Clients DB data source: `collection://1c8d3ff0-18e7-80e9-8381-000b4448cb87`
- Key Slack channels to monitor: #team-spice (C08NSJ91N3U), #content-spice-linkedin (C0ABFGE2V9P)

## Workflow

### Step 1: Determine date context

Get today's date. Calculate:
- `today_start`: today at 00:00:00 in PT (America/Los_Angeles)
- `today_end`: today at 23:59:59 in PT
- `overnight_cutoff`: yesterday at 17:00:00 PT (5pm yesterday, when Maxx likely stopped working)

### Step 2: Pull calendar events

Call `gcal_list_events` with:
- `calendarId`: "primary"
- `timeMin`: today_start (RFC3339)
- `timeMax`: today_end (RFC3339)
- `timeZone`: "America/Los_Angeles"

Extract: event title, start time, end time, attendees (names only), location/meeting link. Flag any back-to-back blocks or gaps longer than 1 hour.

### Step 3: Pull Notion tasks

Call `notion-search` to query the Team Task Tracker for Maxx's open tasks:
- Search the data source `collection://1c8d3ff0-18e7-80f0-a36b-000b6befe5b1`
- Filter for tasks assigned to Maxx (user ID `c249c8bc-e33f-4b35-b4f8-c9b22117cccc`)
- Focus on tasks with status NOT "Done" or "Complete"

If the search doesn't return assignee-filtered results, use `notion-fetch` on the data source to get the schema, then use appropriate filtering.

Categorize tasks:
- **Overdue**: due date before today
- **Due today**: due date is today
- **Upcoming this week**: due within the next 5 business days
- **No due date**: open tasks without a deadline

### Step 4: Scan overnight Gmail

Call `gmail_search_messages` with:
- `q`: "after:{yesterday_date} newer_than:1d"
- `maxResults`: 20

Classify each email:
- **Needs response**: emails where Maxx is in TO and the sender is waiting on him
- **FYI**: newsletters, notifications, CC'd threads
- **Client emails**: anything from known client domains

Prioritize client emails and anything requiring a response. Skip obvious newsletters and automated notifications unless they contain actionable info.

### Step 5: Scan overnight Slack

Search Slack for recent activity using `slack_search_public`:
- Query: messages in key channels from overnight
- Check #team-spice (C08NSJ91N3U) for team updates
- Check for any DMs or mentions of Maxx

Also read recent messages from #team-spice using `slack_read_channel` with:
- `channel_id`: "C08NSJ91N3U"
- `oldest`: overnight_cutoff (unix timestamp)
- `limit`: 30

Flag anything that mentions Maxx, contains a question, or looks like it needs his input.

### Step 6: Compile the brief

Present the morning brief in this exact format:

```
# GM — [Day of Week], [Month Day]

## Calendar ([count] events)
[List events chronologically]
- **[Time]** [Event name] — [attendees if <5, or "X attendees"]
- **[Time]** [Event name] — [attendees]
[If back-to-back blocks exist, note: "⚡ Back-to-back from X to Y"]
[If large gap exists, note: "🟢 Open block: X to Y"]

## Tasks ([count] open)
[Group by urgency]
**Overdue ([count]):**
- [Task name] — was due [date]

**Due today ([count]):**
- [Task name]

**This week ([count]):**
- [Task name] — due [day]

## Overnight Inbox
**Needs response ([count]):**
- [Sender] — [subject line, truncated to ~60 chars]

**Client emails ([count]):**
- [Client name / sender] — [subject]

**FYI ([count]):**
- [Brief summary of anything notable, skip the noise]

## Slack Pulse
[2-3 sentence summary of overnight Slack activity]
[Flag any direct questions or mentions]

## Today's Focus
[Based on calendar density, task urgency, and email priority, suggest 1-3 things Maxx should tackle first. Be opinionated.]
```

### Step 7: Tone and formatting rules

- No fluff. Every line should be scannable.
- Use bold for time blocks and sender names only.
- Keep the entire brief under 40 lines if possible.
- "Today's Focus" section should be 2-3 sentences max, written in Maxx's voice (direct, first-principles).
- Don't summarize what's obvious from the data. Add value by surfacing what matters most.
- If nothing notable happened overnight, say so in one line. Don't pad.
- Use PT timezone for all times.

## Error Handling

- If Google Calendar returns no events: show "No meetings today. Deep work day." under Calendar section.
- If Notion search fails or returns empty: note "Could not pull tasks — check Notion directly."
- If Gmail returns nothing: "Clean inbox overnight."
- If Slack returns nothing: "Quiet night on Slack."
- Never skip a section entirely. Always show the header with a one-line status even if empty.

### Step 8: Send via Slack DM

After compiling the brief, send it to Maxx as a Slack direct message using `slack_send_message`:
- `channel_id`: "U08DMH0DHS8" (Maxx's Slack user ID — sending to a user ID opens/uses the DM conversation)
- `text`: The full compiled brief from Step 6

Format the message using Slack mrkdwn (use `*bold*` instead of `**bold**`, use `\n` for line breaks). Keep the structure clean and scannable in Slack's message format.

## Output

Send the compiled brief as a Slack DM to Maxx (U08DMH0DHS8). Also present a short confirmation in the chat: "GM sent to your Slack DMs." Do not create a file.
