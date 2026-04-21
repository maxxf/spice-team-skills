---
name: client-call-prep
description: Comprehensive client meeting preparation workflow. Use when the user wants to prepare for an upcoming client call or sync. Triggers on "prep for [client] call", "prepare for [client] meeting", "get ready for [client] sync", "review [client] context", or when user mentions preparing for any client meeting. Searches emails, Slack, Circleback transcripts, pulls performance data, tracks action items, and creates strategic meeting doc with agenda.
---

# Client Call Prep

Prepare comprehensively for client meetings by gathering context from all sources, tracking action items, and creating a strategic meeting doc with current performance data.

## Workflow

Follow these steps in sequence to prepare for a client meeting:

### 1. Identify the Client and Meeting

**Ask the user if not clear from context:**
- Which client is the meeting with?
- Is there a specific meeting today, or should I find the next scheduled one?

**Auto-find meeting details:**
- Use Google Calendar to find today's (or next) meeting with the client
- Extract meeting time, attendees, and any existing agenda items
- If multiple meetings found, ask user to clarify which one

### 1.5. Check for Existing Meeting Doc (REQUIRED — do before creating anything)

Before gathering context or creating new docs, search the client's Meeting Notes database in Notion to see if a doc already exists for this meeting. This prevents duplicate docs piling up.

1. Navigate to the client's Notion project page → Meeting Notes database (usually labeled `👥 Meeting Notes` or similar)
2. Use `mcp__f34fcb36-bc14-4569-bc45-beaff552d0f7__notion-search` with:
   - `query_type: "internal"`
   - `data_source_url`: the Meeting Notes database's data source URL (from `<data-source>` tag in the project page)
   - Query: today's date, meeting name, or attendee + date combo
3. Filter to results from the last 7 days
4. **If an existing doc is found:**
   - Read it via `notion-fetch`
   - Classify it: is it a placeholder (auto-created from calendar), a partial prep, or a complete prep?
   - Set the plan to **UPDATE** that doc in Step 6 rather than creating new
   - Note the page ID for use in Step 6
5. **If no existing doc is found:**
   - Proceed to create new in Step 6
6. **If multiple docs match** (e.g., duplicates): flag to user with URLs — ask which to use. Do NOT silently pick one.

**Never create a duplicate meeting doc.** If in doubt, ask.

### 2. Gather Context from Recent Communications

**Search the last 7 days:**

**Emails (Gmail):**
Search for emails to/from the client. Focus on: decisions made, questions raised, issues flagged, upcoming initiatives.

**Slack:**
Search for messages in client channels and DMs. Focus on: real-time updates, quick decisions, operational issues, informal context.

**Circleback Transcripts:**
Pull the most recent 3 meetings with this client. Extract: key decisions, action items, open questions, strategic direction.

### 3. Track Action Items from Previous Meetings

**For each action item from previous meetings:**
- Check status (completed, in progress, blocked, not started)
- Note who owns it
- Flag any overdue items
- Prepare to discuss progress

**Sources for action items:**
- Circleback meeting notes
- Previous meeting docs in Notion
- Slack threads where work was discussed
- Email confirmations or updates

### 4. Pull Current Performance Data

**Primary source: Google Sheets**
- Find the client's weekly tracker spreadsheet
- Pull week-over-week metrics
- Calculate key changes (ROAS, CPO, sales, orders)

**Fallback sources if no Google Sheet:**
1. Delivery platform dashboards (DoorDash, Uber Eats, Grubhub)
2. Loop or other tracking tools
3. Notion databases with performance data

**Key metrics to gather:**
- Total sales (week-over-week)
- Marketing-driven sales vs organic
- ROAS and CPO by platform
- Order volume and AOV
- Net payout % and dollar amount

### 5. Review Campaign Performance

**For each active platform:**
- Current campaigns with spend and performance
- Campaign calendar (upcoming promotions)
- Platform-specific offers/promos
- Co-funding opportunities or platform support

### 6. Create OR Update Strategic Meeting Doc in Notion

**Decision from Step 1.5:**
- **If an existing doc was found** — UPDATE that doc rather than creating a new one. Use `mcp__f34fcb36-bc14-4569-bc45-beaff552d0f7__notion-update-page` with `content_updates` to merge the prep content into the existing structure. Preserve any content the client may have already added (agenda items, questions). Fill in placeholders and append new sections.
- **If no existing doc was found** — create new via `notion-create-pages` in the Meeting Notes database.

**Location:** Client's workspace → Meeting Notes database

**Structure:**

```markdown
# Agenda
- [List key topics to discuss based on context gathered]
- [Action item status review]
- [Performance overview]
- [Strategic priorities or decisions needed]
- [Next steps]

## Action Items
> Carried over from last meeting -- check off completed items
- [ ] **[Owner]:** [Task] -- Status?
- [ ] **[Owner]:** [Task] -- Status?

> New this meeting
[To be filled during/after the meeting]

---

## Executive Summary
**UP:**
- [3-5 bullets on positive trends, wins, improvements]

**DOWN:**
- [3-5 bullets on challenges, declines, issues]

**NEXT:**
- [3-5 bullets on priorities, upcoming initiatives, decisions needed]

---

## Sales & Marketing KPIs
### Week [Date] vs Week [Date]

[Table with key metrics and week-over-week changes]

---

## Platform Performance

**DoorDash** (X% of revenue):
- Sales: $X -> $Y (+/-Z%)
- ROAS: X.X, CPO: $X
- [Key insight about performance]

**Campaign Performance:**
- [Active campaigns with spend/performance]
- [Upcoming promotions]
- [Platform-specific offers]

**Uber Eats** (X% of revenue):
- Sales: $X -> $Y (+/-Z%)
- ROAS: X.X, CPO: $X
- [Key insight about performance]

**Campaign Performance:**
- [Active campaigns with spend/performance]
- [Upcoming promotions]
- [Platform-specific offers]

**Grubhub** (X% of revenue):
- Sales: $X -> $Y (+/-Z%)
- ROAS: X.X, CPO: $X
- [Key insight about performance]

**Campaign Performance:**
- [Active campaigns with spend/performance]
- [Upcoming promotions]
- [Platform-specific offers]

---

## Strategic Recommendations
### Immediate (This Week)
[Numbered list with owners and due dates]

### Short-Term (2-4 Weeks)
[Numbered list with owners and due dates]

### 30-Day Targets
[Bulleted list of measurable goals]

---

## Updates from Each Platform
[Detail any platform-specific news, changes, support offered]

---

## Open Questions for Discussion
[Numbered list of questions to address in the meeting]
```

### 7. Synthesize Meeting Brief

**Create a concise summary for your own reference:**
- Top 3 things to discuss
- Key decisions needed
- Critical action items to follow up on
- Any sensitive topics or concerns

## Data Source Priority

When gathering performance data, follow this order:

1. **Google Sheets** - Most common, usually has complete week-over-week data
2. **Delivery Platform Dashboards** - For real-time or missing metrics
3. **Loop** - If client uses Loop for tracking
4. **Notion Databases** - For custom metrics or supplementary data
5. **Circleback/Email** - For context on why metrics changed

## Common Client Types & Adaptations

**Delivery Platform Clients (Restaurants):**
- Focus on platform performance (DoorDash, Uber, Grubhub)
- Include menu optimization notes
- Track tier strategy for locations
- Note operational issues affecting performance

**Retention/Growth Clients:**
- Focus on retention metrics (churn, LTV, engagement)
- Highlight campaign performance
- Track A/B tests and experiments

**Paid Acquisition Clients:**
- Focus on CAC, ROAS, conversion rates
- Platform-by-platform performance (Meta, Google, TikTok)
- Creative performance and testing

## Tips

**Efficient context gathering:**
- Run email, Slack, and Circleback searches in parallel
- Start with most recent data and work backwards
- Focus on actionable insights, not just data dumps

**Action item tracking:**
- Always check status before the meeting
- Flag blockers or delays proactively
- Note what's been completed to celebrate wins

**Performance data:**
- Lead with the "so what" -- why metrics changed
- Compare to targets, not just previous week
- Prepare explanations for anomalies

**Meeting doc best practices:**
- Create the doc before the meeting starts
- Share link with the client at the start of the call
- Use it as a live document during discussion
- Update action items in real-time

**When to skip certain sections:**
- No campaign performance section if client has no active campaigns
- Simplify KPI table if limited data available
- Skip platform sections for non-platform clients

## Example Usage

**User says:** "prep for Everytable call"

**Skill does:**
1. Searches Gmail for Everytable emails (last 7 days)
2. Searches Slack in #everytable channel (last 7 days)
3. Pulls 3 most recent Circleback meetings
4. Finds Everytable Google Sheet tracker
5. Pulls week-over-week metrics
6. Identifies action items from previous meetings
7. Creates new meeting doc in Everytable -> Meeting Notes
8. Populates doc with agenda, action items, performance data, campaign details
9. Summarizes key topics for the call
