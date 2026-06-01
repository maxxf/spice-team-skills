---
name: post-client-meeting
description: Finalize and share client meeting notes. Use when the user wants to wrap up a client meeting by cleaning up meeting docs, publishing them, and sending a recap email. Trigger on "finalize meeting notes", "wrap up meeting", "send meeting recap", "post-meeting follow-up", or "share meeting notes with client".
---

# Post Client Meeting

Finalize client meeting documentation and send a professional recap email with action items and meeting link.

## Workflow

Follow these steps in sequence to wrap up a client meeting:

### 1. Locate the Meeting Doc (do NOT create a new one)

Search the client's Notion Meeting Notes database for the doc tied to this meeting. Find it by date + meeting name combination.

1. Navigate to the client's project page → Meeting Notes database
2. Use `mcp__f34fcb36-bc14-4569-bc45-beaff552d0f7__notion-search` filtered to that database, searching for today's date or the meeting name
3. Read the matching doc via `notion-fetch`

**If no doc exists** — flag to the user and ask whether to create one from the transcript + weekly data before proceeding. Do NOT silently create one.

**If multiple docs match** (e.g., a prep doc and a separate recap doc) — ask the user which to update. Don't merge or pick silently.

Work with the existing prep/call doc throughout the rest of this workflow.

### 2. Cross-reference the client's tracker Sheet (REQUIRED — accuracy check)

Before finalizing the recap, verify the performance numbers in the meeting doc against the client's Google Sheet tracker. This catches stale data (e.g., a prep doc written Monday with Week 14 numbers, but the meeting discussed Week 15).

1. Get the tracker URL from the client's Notion Weekly Reporting Profile → Report Writer Notes (or from `references/client-registry.md` as fallback)
2. Use `mcp__3cfdef12-aed5-469f-904c-ae7eaeff04dd__read_file_content` to fetch the tracker's current "Weekly Platform Overview" and "By Location" tabs
3. Compare the numbers in the meeting doc against the tracker — if there's drift, update the doc with the correct (tracker) values before sharing with the client

**Example tracker URL for goop Kitchen:** `https://docs.google.com/spreadsheets/d/18we-M-qVdug4LRZiolfScL3emVPE0AuL4Zb9Zqn_A3A/edit`

If Drive MCP is unavailable, skip this check but flag to the user that the doc hasn't been tracker-verified.

### 3. Prep the Doc for Client Sharing

The prep doc contains internal sections that must be stripped before sharing with the client. Walk through the doc and remove:

**Strip entirely:**
- **Agenda** section — internal pre-meeting talking points, not useful to the client after the meeting
- **Action Items (carried-over / open from prep)** — internal tracking of prior commitments; the recap should only include action items from THIS meeting
- **Strategic Recommendations** when marked internal, or any team-only analysis
- **Open Questions for Discussion** — internal prep notes
- Anything explicitly marked **"INTERNAL"** or **"DO NOT SHARE"**
- Team-only commentary, sensitive competitive notes, pricing strategy

**Keep and polish:**
- **30-Second Brief / Executive Summary** (top of doc)
- **Performance Snapshot** tables (Platform + Location) — tracker-verified in Step 2
- **Meeting Recap** with decisions, context, next steps (this is the client-facing substance)
- **NEW Action Items from this meeting** — clean, owner-tagged, due-dated
- **Links** to the week's full weekly report

**Finalize:**
- Verify tables match the tracker (from Step 2)
- Fix any `[TBD]` or `[date]` placeholders
- Confirm professional tone throughout
- Update the page title: drop any "Call Prep" prefix. Use "Meeting Recap — [Date]" or similar client-appropriate label.

### 4. Draft the Client Email — PASTE IN CHAT (do NOT create a Gmail draft)

Create a concise, friendly recap email. The email goes directly in the chat for the user to copy and send — **do NOT use Gmail MCP to create a draft**, because Gmail drafts can't be cleanly updated/deleted via MCP and they pile up in the user's drafts folder.

**Subject line:** `[Client Name] Meeting Recap — [Date]`

**Email body:**

```
Hi [Client Contact],

Great connecting today. Here's a quick recap:

[3-5 TLDR bullet points summarizing key takeaways, decisions, or highlights from the meeting]

**Action Items:**
- [ ] **[Owner Name]:** [Task description] — Due: [Date]
- [ ] **[Owner Name]:** [Task description] — Due: [Date]
- [ ] **[Owner Name]:** [Task description] — Due: [Date]

Full meeting notes: [Link to Notion doc]

[Brief next step or closing — 1 sentence]

Best,
[Your Name]
```

**Tone guidelines:**
- Direct and friendly, not overly formal
- Conversational but professional
- Action-oriented and clear
- Use first names when appropriate
- Keep it concise — aim for under 150 words total

**Delivery format (paste this directly in chat as a copy-paste-ready block):**

```
To: [recipients]
CC: [cc list, if any]
Subject: [subject]

[body]
```

The user copies this into their Gmail/client themselves. No Gmail drafts. No external sends.

### 5. Post Spice-internal action items to `#int-[client]` Slack channel

After the client recap is squared away, post the **Spice-team-owned action items** to the client's internal Slack channel so the team sees what landed on them and can self-track. This is internal — not for the client.

**Step 5a: Identify Spice-internal owners (NEW from this meeting)**

From the meeting doc's "NEW Action Items" section, classify each item by owner. Spice team members (always post these to `#int-[client]`):

- Maxx, Tomas, Manish, Dulari, Rodrigo, Ana, Santiago, Dilli, David, Rui (and any future Spice hires)
- "Spice", "Team", "Ops", "Design", or any Spice-role label
- Anything tagged "internal" or where the owner is unspecified but the task is clearly Spice's

Skip client-side owners (the client's contacts) — they got those items in the recap email.

**Step 5a-bis: Pull CARRY-OVER action items from previous meetings (still relevant)**

Don't just post today's items in isolation — pull the open Spice-owned action items from the **last 3 meetings with this client** so the team sees the full active queue.

1. `SearchMeetings` with the client name, sorted by date desc, limit 3 (the meeting we just processed + 2 prior)
2. For each prior meeting (skip the current one), `ReadMeetings` and pull `actionItems`
3. Filter to:
   - Spice-owned (same classification logic as Step 5a)
   - `status` is NOT "COMPLETED" / "DONE" (Circleback uses "PENDING" for open items)
4. Tag each carry-over item with its source meeting date for context
5. **Deduplicate against today's items** — if the same task is in this meeting AND a previous one (same wording, same owner), only show it once under "carried over" with a note that it was raised in [date] and again today
6. **Filter out stale ones** — if an item is older than 4 weeks AND has no recent mention in transcripts/Slack/email, flag it as "stale, may already be done — verify before posting" rather than blindly including

If both NEW + CARRY-OVER lists are empty, **skip Step 5 entirely**.

**Step 5b: Look up the client's internal channel**

Use `mcp__dab362fb-680c-4394-8a3c-857a73b5017d__slack_search_channels` with query `int-[client-slug]` (e.g., `int-goop-kitchen`, `int-mbfs`). The Slack channel pattern is documented in the team CLAUDE.md.

If the channel can't be found, flag to the user with the slug you tried — don't post to the wrong channel.

**Step 5c: Look up Slack user IDs for each Spice owner**

For proper @mentions, fetch each owner's Slack user ID via `mcp__dab362fb-680c-4394-8a3c-857a73b5017d__slack_search_users` (by first name + email domain `@spicedigital.co` if needed for disambiguation). Cache these IDs in conversation if you do multiple lookups.

If a user can't be resolved, fall back to writing their name in plain text — don't fabricate a user ID.

**Step 5d: Compose the Slack draft**

Format (omit sections that are empty — don't show empty headers):

```
:memo: action items from today's [Client Name] meeting

new from today:
• <@SLACK_USER_ID> — [task description] — due [date]
• <@SLACK_USER_ID> — [task description] — due [date]

carried over (still open from prior meetings):
• <@SLACK_USER_ID> — [task description] — due [date] *(raised [meeting date], age: [Nw])*
• <@SLACK_USER_ID> — [task description] — due [date] *(raised [meeting date], age: [Nw])*

waiting on [client] side (FYI — not action items for us):
• [client contact name] — [task]
• [client contact name] — [task]

full notes: [Notion meeting doc URL]
```

**Section rules:**
- `new from today` — only items from THIS meeting where the Spice owner just got tagged
- `carried over` — Spice-owned items from prior meetings still PENDING. Include the source meeting date + age in weeks so the team sees what's been lingering. Items aged >2 meetings should escalate visually (e.g., `*(raised 4/14, age: 4w — escalating)*`).
- `waiting on [client] side` — client-owned items so the team has full context on what's blocking us. Mark FYI, not action.
- Drop any section that's empty. Don't show `new from today:` with no bullets underneath.

**Tone rules** (match Spice internal voice):
- Lowercase OK
- Direct, fragments OK
- No corporate fluff
- One CTA per item (the task itself)
- Always include the due date — if missing, write `due TBD` and call it out as a gap

**Step 5e: Create as a Slack DRAFT (not sent)**

Use `mcp__dab362fb-680c-4394-8a3c-857a73b5017d__slack_send_message_draft` with the channel ID from 5b. This creates the message as a draft in the user's Slack — they review it in the channel and hit send manually. Per safety rules, do NOT use `slack_send_message` to auto-send team comms.

**Step 5f: Confirm to user**

After the draft is created, tell the user:
- Channel name + Slack URL of the draft
- Number of action items posted
- Owners tagged (so they can spot-check before sending)
- Any items that fell back to plain text (because user IDs didn't resolve)

### 6. Confirm Doc is Share-Ready (final checklist)

Before handing off to the user, verify the following:

- [ ] Agenda section removed
- [ ] Carried-over / pre-meeting Action Items section removed
- [ ] Internal strategic / pricing / competitive notes removed
- [ ] Performance data verified against current tracker (Step 2)
- [ ] New action items listed with owners + due dates
- [ ] Link to the week's full weekly report embedded in the doc
- [ ] Page title dropped "Call Prep" prefix (now "Meeting Recap — [Date]" or similar)
- [ ] Email draft pasted in chat (NOT created as Gmail draft)
- [ ] Spice-internal action items posted as draft to `#int-[client]` Slack channel (Step 5) — OR confirmed there were none
- [ ] Notion doc URL provided to the user

Report to the user:
- Finalized Notion meeting doc URL
- The pasted email block (for them to copy into Gmail)
- Slack draft URL for the `#int-[client]` action-items post (for them to review + send)
- Any gaps (missing owner, missing due date, unresolved Slack user, etc.)

The user sends both the email and the Slack post at their discretion.

## Email Examples

**Example 1 -- Weekly sync:**
```
Hi Sarah,

Great sync today. Quick recap:

- DoorDash ROAS holding steady at 6.3 despite slight CPO improvement
- Organic sales surged 32% week-over-week -- investigating drivers
- Tier 3 locations getting Uber co-funding while we fix ops issues

**Action Items:**
- [ ] **Ro:** Finalize tier-based budget structure -- Due: Feb 7
- [ ] **Yuriy:** Schedule bi-weekly ops meeting -- Due: Feb 7
- [ ] **Team:** Plan March Madness BOGO campaign -- Due: Feb 28

Full meeting notes: [link]

Let's touch base next week on the organic surge findings.

Best,
Maxx
```

**Example 2 -- Strategy session:**
```
Hi David,

Productive session on Q2 planning. Key decisions:

- Moving forward with the 3-tier location strategy
- Pausing spend on underperforming locations until ops improve
- Testing keyword campaigns on Uber once baseline is established

**Action Items:**
- [ ] **Jason:** Implement menu optimization via Deliverect -- Due: Feb 21
- [ ] **Maxx:** Coordinate menu photo shoot with fiber bowl rebrand -- TBD

Full meeting notes: [link]

Excited to see these improvements roll out.

Best,
Maxx
```

## Tips

- Always get user approval before sending the email
- Confirm which action items should be client-facing vs internal-only
- Use the client's preferred communication style (formal vs casual)
- Double-check that internal strategy or pricing info is removed
