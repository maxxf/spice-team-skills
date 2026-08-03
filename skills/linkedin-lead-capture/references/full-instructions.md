---
name: linkedin-lead-capture
description: >
  Daily LinkedIn lead capture for Spice sales pipeline. Uses browser automation to scan connection requests and DMs, ICP-qualify inbound activity, auto-accept matching connections, create leads in Notion Sales Pipeline + follow-up tasks in Team Task Tracker, draft reply suggestions, and post a summary to #spice-website-leads. Meant to run once each weekday morning (schedule it if your setup supports it); can also be triggered manually from any session. Trigger on "linkedin leads", "check LinkedIn", "who connected on LinkedIn", "LinkedIn inbound", "scan LinkedIn", or any request about LinkedIn connection requests or messages from potential clients. Append "force" (e.g., "check linkedin force") to bypass the dual-run guard on a manual run.
---

> **Requires a browser logged into LinkedIn.** This skill drives LinkedIn through a Chrome session that is already signed in as the account whose inbound you're capturing.

# LinkedIn Lead Capture

Scan LinkedIn for inbound connection requests and DMs, qualify against Spice's ICP, auto-accept matches, create Notion pipeline entries, draft reply suggestions, and post everything to #spice-website-leads.

## Philosophy

LinkedIn inbound is a sales channel, not a social feed. Every connection request and DM from someone who runs restaurants is a potential deal. This skill makes sure none of them fall through the cracks while keeping the pipeline clean of noise.

Do not spam. Do not mass-accept. Do not send anything automatically. The goal is capture + qualify + draft, not outreach automation.

## IMPORTANT: Read the voice guide first

Before drafting ANY reply, locate and read the voice guide `maxx-freedman-voice-guide.md` (ships at the plugin's repo-root `references/`).

If it can't be found, **abort the entire skill** with this Slack post in `#spice-website-leads`: `linkedin-lead-capture aborted: voice guide maxx-freedman-voice-guide.md not found.` Do not proceed with drafting reply suggestions when voice rules are unavailable.

Follow the voice guide exactly. Zero tolerance for banned phrases, em dashes, or AI-sounding copy.

## BRANDING: Always "Spice", never "Spice Digital" in outbound copy. Note: the booking link URL `cal.com/spice-digital` is a legacy slug that must NOT be rewritten — use the URL as-is in hyperlinks, but never echo the words "Spice Digital" in body copy.

---

## Step 0: Dual-Run Guard

Before any LinkedIn navigation, check whether today's run already happened. This prevents a manual on-demand run from double-acting after the scheduled morning run.

### Resolve channel ID

Call `slack_search_channels({query: "spice-website-leads"})`. Take the first result's channel ID. (At spec time this resolved to `C08LZCSRZDX`; resolve at runtime for resilience.) If the search returns zero results, abort with a Slack DM to Maxx: "linkedin-lead-capture aborted: cannot resolve #spice-website-leads channel."

### Check today's posts

Call `slack_read_channel({channel_id: <resolved>, limit: 30, response_format: "concise"})`. Scan the messages for any whose body contains the substring `LinkedIn Lead Capture — {YYYY-MM-DD}` where the date is today in PT, AND whose `ts` falls within today's PT date.

### Decision

- **No matching post found:** proceed to Step 1.
- **Matching post found AND user invocation does NOT contain the literal word "force":** abort. Post a brief reply to `#spice-website-leads`: `Skipped — today's run already posted at {HH:mm PT}. To force a re-run, say "check linkedin force".`
- **Matching post found AND invocation contains "force":** proceed to Step 1, log in summary: "Force-flag override active — bypassing dual-run guard."

### Force flag scope

Only manual on-demand invocations carry the force flag (string match on Maxx's request). A scheduled run **never** honors force — it always respects the guard. This means if Maxx triggers a manual run in the afternoon and a scheduled run already happened that morning, the manual run aborts unless Maxx explicitly says "force."

Match rule: case-insensitive whole-word match for `force` (e.g., regex `\bforce\b/i`). "Force" / "FORCE" / "force it" all qualify; "forces" or "enforced" do not.

---

## Step 1: Dedup Prep

Before touching LinkedIn, build a "known contacts" set so you don't create duplicate leads.

### Notion Pipeline
Query the Sales Pipeline database (ID: `1c0d3ff0-18e7-80fa-b0b6-cc5887a502c4`). Pull all entries: names, LinkedIn URLs (if stored in notes/body), and current stages. This is the primary dedup source.

### Google Calendar
Search Google Calendar for events in the last 14 days matching `"Spice Intro Call"`. These are people who booked directly via Maxx's LinkedIn booking link. Extract attendee names. Format reference: "Spice Intro Call 🌶️ (LinkedIn) between Maxx Freedman and {Name}"

Store both sets for dedup checks in Steps 4-5.

---

## Step 2: Scan Connection Requests

Navigate to `https://www.linkedin.com/mynetwork/invitation-manager/` using Claude in Chrome.

### Login check
After navigating, read the page. If you see a login form, "Sign in", or "Join now", STOP the entire run. Post to #spice-website-leads: "LinkedIn Lead Capture aborted: session expired. Log into LinkedIn in the Chrome browser this skill drives."

### Processing invitations
Read the pending invitations list. For each invitation visible on the first page (do NOT paginate or scroll infinitely):

1. Note the person's name, headline, and any attached note
2. Click their name to visit their full profile
3. Run ICP scoring (see ICP Scoring section below)
4. If ICP score is 60+:
   - Check against known contacts (dedup)
   - If net-new: queue for Notion creation, mark for auto-accept
   - If duplicate: note in summary, skip creation, still accept if not already connected
5. If ICP score is 40-59: flag as "borderline, needs manual review" in summary. Do NOT auto-accept.
6. If ICP score is <40: skip silently. Leave the request pending (never reject).
7. Navigate back to the invitations page before processing the next one

### Auto-accept
For each queued ICP match (score 60+), click the "Accept" button on the invitations page. Maximum 10 auto-accepts per run. If more than 10 qualify, accept the top 10 by score and flag the rest in the summary.

### Rate limiting
- Maximum 20 profile visits per run across all steps
- Wait for each page to fully load before reading
- If LinkedIn shows a CAPTCHA, security check, or "slow down" warning: stop processing invitations immediately, take a screenshot, and report in the Slack summary. Move to Step 3 if possible.

---

## Step 3: Scan DM Inbox

Navigate to `https://www.linkedin.com/messaging/` using Claude in Chrome.

Read the conversation list. Process unread messages and messages from the last 24 hours. For each new DM from someone not already in your known contacts set:

1. Click into the conversation to read the full message
2. Click the sender's name to visit their profile
3. Run ICP scoring
4. If ICP score is 60+:
   - Queue for Notion creation with message context
   - Draft a reply suggestion (see Reply Drafts section)
5. If ICP score is 40-59: flag as borderline in summary
6. If ICP score is <40: skip

Same rate limiting rules as Step 2. Profile visits count against the same 20-visit cap.

---

## ICP Scoring (0-100)

Score each profile across these dimensions. Threshold: 60+ to qualify.

| Signal | Points | What to look for |
|--------|--------|-----------------|
| Decision-maker title | 25 | Owner, Founder, CEO, President, COO, VP Ops, VP Operations, Director of Marketing, Director of Operations, Head of Growth, CMO, General Manager (multi-unit), Franchisee, Partner |
| Restaurant/food industry | 25 | Company or headline mentions: restaurant, food, kitchen, dining, franchise, QSR, fast casual, pizza, burger, sushi, bowl, cafe, bakery, catering, hospitality, food service, bar & grill |
| Multi-location signal | 20 | "X locations", "multi-unit", "franchise", "chain", location count in company description, or company is a recognizable chain |
| Delivery platform signal | 15 | Uber Eats, DoorDash, Grubhub, delivery, third-party delivery, 3P, marketplace, off-premise |
| US major metro | 10 | Los Angeles, New York, Chicago, Miami, San Francisco, Bay Area, Dallas, Houston, Atlanta, Phoenix, Denver, Seattle, Boston, DC, Philadelphia |
| **Negative signals** | **-100** | Recruiter, sales rep, competing delivery agency, "looking for opportunities", MLM, crypto, SaaS vendor selling to restaurants |

### Scoring tiers
- **60+**: ICP match. Auto-accept (if connection request), create Notion lead, draft reply.
- **40-59**: Borderline. Flag in Slack for manual review. No auto-accept, no Notion creation.
- **<40**: Skip silently.

### Qualification note
Write a one-line summary for each scored lead explaining the match: "VP Ops at Torchy's Tacos (50+ locations), based in Dallas, headline mentions delivery growth." This goes into Notion and the Slack summary.

---

## Step 4: Dedup Check

For each queued lead (from Steps 2-3), check against:

1. **Notion Pipeline**: Name match (case-insensitive, first + last) OR LinkedIn URL match in page body/notes
2. **Calendar bookings**: Name match against attendees in "Spice Intro Call" events from last 14 days

If duplicate found:
- Skip Notion creation
- Note in summary: "Already in pipeline as {stage}" or "Booked via calendar on {date}"
- Still auto-accept the connection if applicable (being connected doesn't mean they're a lead)

---

## Step 5: Create Notion Leads

For each net-new ICP lead, create a page in the Sales Pipeline data source (`1c0d3ff0-18e7-805b-ba76-000b04cc35c4`; database ID `1c0d3ff0-18e7-80fa-b0b6-cc5887a502c4`). The property name is `Deal stage`, NOT `Stage` — the existing skill had this wrong and writes silently dropped.

| Sales Pipeline property | Type | Value |
|---|---|---|
| Name | title | `{First} {Last} — {Company}` |
| Deal stage | select | `New Lead` |
| Source | multi-select | `Inbound` |
| Account owner | person | Maxx (resolve user ID once at the start of Step 1 (Dedup Prep) via Notion's user search; cache for the run) |
| Last contact date | date | today (ISO `YYYY-MM-DD`) |
| Service(s) | multi-select | derived (see below) |
| Contact Role | select | derived from title (see below) |
| Decision Maker | text | full job title text |
| Locations | number | parse from profile copy if visible (e.g., "Owner of 12-location chain"), else null |
| Notes | text | structured block — see below |
| Website | url | company website URL from profile if exposed, else null |
| Email | email | leave null (LinkedIn rarely exposes); follow-up will be on LinkedIn first |

### Contact Role derivation (substring match on title, case-insensitive, first match wins)

- "Owner", "Founder", "CEO", "President", "Co-Founder" → `Owner/CEO`
- "GM", "General Manager", "Operating Partner" → `General Manager`
- "Marketing", "CMO", "Director of Marketing", "VP Marketing" → `Marketing Director`
- "Operations", "VP Ops", "COO", "Director of Operations" → `Operations Manager`
- Anything else → `Other`

### Service(s) derivation (multi-select, evaluate signals from DM text + their headline)

- DM/headline mentions "email", "loyalty", "retention", "SMS", "Klaviyo", "Mailchimp" → add `Retention`
- DM/headline mentions "ads", "Meta", "Facebook", "Google ads", "paid media", "performance marketing" → add `Paid Media`
- DM/headline mentions "delivery", "Uber Eats", "DoorDash", "Grubhub", "marketplace", "third-party", "3P" → add `Marketplaces`
- If no signal matched → default to `Marketplaces`
- Multi-select can hold multiple matches simultaneously; if DM mentions both delivery and email, write both.

### Notes property body

```
Source: LinkedIn Inbound ({Connection Request | DM})
ICP Score: {X}/100
LinkedIn: {profile URL}
Title: {their job title}
Company: {company name}
Location: {their location}

Qualification: {one-line ICP qualification note}

{If DM, include: Their message: "{first 500 chars of DM}"}

Email not yet captured. Follow up on LinkedIn first.
```

---

## Step 5b: Create Team Task Tracker Follow-Up

After the Sales Pipeline write succeeds for a net-new ICP lead, create a follow-up task in Team Task Tracker (data source `1c8d3ff0-18e7-80f0-a36b-000b6befe5b1`; database ID `1c8d3ff0-18e7-8054-8b14-cbc13c26bb25`).

### Dedup check first

Before creating, query Team Task Tracker for tasks where:
- `Request Title` starts with `LinkedIn follow-up: {First} {Last}` (no time bound)
- `Status` is NOT `Done`

If any open task exists for that person, skip task creation and note in Slack summary: "Task already exists for {Name}." Append a Notion comment to the existing task containing the new DM text. **Do NOT update the existing task's `Description` property** — the original reply draft stays so the reminder skill keeps surfacing the original guidance. If the new context warrants a different draft, Maxx updates manually.

### Create the task

| Task Tracker property | Type | Value |
|---|---|---|
| Request Title | title | `LinkedIn follow-up: {First} {Last} — {Company}` |
| Status | status | `Not started` |
| Priority | select | `High` if ICP ≥80, `Medium` if 60-79 |
| Source | select | `Agent` |
| Task type | select | `Admin` |
| Urgency Level | select | `Standard - 1 to 2 business days` |
| Due date | date | next business day in PT (Mon if today is Fri/Sat/Sun) |
| (Owner — the unnamed person property literally named `""`; address by Notion API property ID, not by name) | person | Maxx |
| Description | text | structured single-text-blob, format below |
| Additional Notes | text | LinkedIn profile URL only |

### Description property format (CRITICAL — the reminder skill parses on the delimiter)

```
ICP: {score}/100. {one-line qualification}
LinkedIn: {profile URL}
Notion lead: {sales_pipeline_page_url}
{If DM, prepend: Their message: "{first 300 chars of DM}"}

---REPLY DRAFT---
{full draft reply text from Step 6}
```

The `---REPLY DRAFT---` delimiter is read by `linkedin-followup-reminder`. Anything before the delimiter is opaque context; the reminder skill takes only the text after.

**Token scope (CRITICAL):** The literal string `---REPLY DRAFT---` appears ONLY in the Notion Team Task Tracker `Description` property of LinkedIn follow-up tasks. Step 7's Slack thread replies use plain `---` visual fences and never contain the `---REPLY DRAFT---` token. Do not paste the token into Slack output.

### Next-business-day calculation

- Today is Mon-Thu → due = tomorrow
- Today is Fri → due = next Monday
- Today is Sat → due = next Monday
- Today is Sun → due = next Monday
- US federal holidays are not adjusted for (out of scope for v1)

### Failure handling

- Sales Pipeline succeeded but Task Tracker create fails: retry once after 5 seconds. If still failing, post warning in Slack summary: "Notion task creation failed for {Name} — create manually." The lead is still in Sales Pipeline; the Slack reply draft post is unaffected.

---

## Step 6: Draft Reply Suggestions

Draft replies ONLY for DM leads and newly accepted ICP connections. Never send automatically. Drafts appear in the Slack summary for Maxx to copy, edit, and paste into LinkedIn manually.

### Reply framework by message type

**Direct inquiry** ("need help with delivery", "looking for an agency"):
```
{First name}, thanks for reaching out. We work with chains like yours across UE, DD, and GH, currently managing 20+ brands, 400+ locations.

Happy to show you what we're seeing in {their city/market} specifically. Book time here: cal.com/spice-digital

// maxx freedman | managing partner | Spice
```

**Generic connection** (no message, just accepted an ICP connection):
```
{First name}, appreciate the connect. Saw you're running {company} across {detail from profile}.

We manage delivery marketplace ops for restaurant chains, curious if that's something you've been thinking about. Either way, good to be connected.

// maxx freedman | managing partner | Spice
```

**Specific ask** ("can you help with X"):
```
{First name}, {direct answer to their question in 1-2 sentences referencing Spice's experience with similar clients}.

Worth a quick call? cal.com/spice-digital

// maxx freedman | managing partner | Spice
```

### Drafting rules
- Read the voice guide before drafting. Follow it exactly.
- Reference something specific from their profile or message
- Always include `cal.com/spice-digital` booking link
- 3-5 sentences max
- No em dashes, no banned phrases, max one exclamation mark
- Vary sentence length
- Read it mentally. If it sounds like a press release, rewrite it.
- Never write "Spice Digital" in the reply. Just "Spice".

---

## Step 7: Post Slack Summary

Post to `#spice-website-leads` channel.

### Main message format:

```
*LinkedIn Lead Capture — {YYYY-MM-DD}*

*New ICP Leads:* {count}
• {Name} / {Company} / {Title} — Score: {X}/100 — {Connection Request / DM}
  ↳ {qualification note}

*Auto-Accepted:* {count} connection requests
• {Name} — {Company}

*Needs Manual Review:* {count} (borderline, score 40-59)
• {Name} / {Company} — Score: {X}/100

*Skipped (already known):* {count}
• {Name} — already in pipeline as {stage}
• {Name} — booked via calendar on {date}

*Drafted Replies:* {count} — see thread

*Errors/Flags:*
• {any issues: rate limiting, CAPTCHA, failed navigation, etc.}
```

### Thread replies (one per drafted reply):

```
*Reply Draft: {Name} / {Company}*
Their message: "{original DM text, truncated to 200 chars}"

---
{full draft reply text}
---

LinkedIn: {profile_url}
Notion: {notion_page_url or "Created" or "Skipped (duplicate)"}
```

If zero leads were found, still post a summary: "LinkedIn Lead Capture — {YYYY-MM-DD}: No new ICP leads. {X} pending requests checked, {Y} messages scanned." (ISO date format must match the dual-run guard's matching format.)

---

## Error Handling

| Failure | What to do |
|---------|-----------|
| LinkedIn not logged in | Abort entire run. Post to #spice-website-leads: "LinkedIn session expired, log in in the Chrome browser this skill drives." |
| CAPTCHA or security check | Abort current section. Screenshot the page. Report in Slack summary. Try remaining steps if possible. |
| Rate limited | Stop profile visits. Process whatever data was already collected. Note in summary. |
| Notion API failure | Retry once. If still failing, include all lead data in the Slack summary so Maxx can create entries manually. |
| Calendar API failure | Skip calendar dedup layer. Note in summary: "Calendar dedup skipped (API error)." Proceed with Notion-only dedup. |
| No pending invitations | Skip to Step 3. Note: "No pending connection requests." |
| No new DMs | Skip to Step 7. Note: "No new DMs in last 24 hours." |
| LinkedIn UI changed | Abort that section. Report: "LinkedIn UI may have changed, {section} failed. Check manually." |

Each step is independent. A failure in one step should not prevent the others from running. Always post a Slack summary, even if most steps failed.

---

## What NOT To Do

- Never send any LinkedIn message automatically. Drafts only, posted to Slack.
- Never reject or withdraw connection requests. Leave non-ICP requests pending.
- Never send connection requests proactively.
- Never like, comment on, or engage with any LinkedIn content.
- Never scroll feeds or interact with posts.
- Never modify profile settings.
- Never export or download LinkedIn data.
- Never visit more than 20 profiles per run.
- Never accept more than 10 connections per run.
- Never use any phrase from the voice guide Kill List.
- Never write "Spice Digital" in outbound copy. It's just "Spice".
