---
name: client-call-prep
description: >
  GM-owned skill that runs before every client meeting. Pulls carryover context from
  three required sources (client emails, Slack channel, last meeting notes + transcript),
  QAs the ops-generated weekly report against the locked structure, finalizes a
  locked-format agenda, publishes the client-facing meeting doc, and outputs a brief
  for the meeting lead. Triggers on "prep for [client] call", "prepare for [client]
  meeting", "get ready for [client] sync", "meeting prep for [client]", or any request
  to prepare for an upcoming client touchpoint. Replaces the prior weekly-report-gm-qa
  step — QA is now Phase 2 inside this skill.
---

# Client Call Prep

This skill is the GM's contract before every client meeting. It runs AFTER the ops team has finished `weekly-reporting`. It does five things in strict order:

0. **Auto-locates the ops weekly report** in Notion (the GM doesn't paste a link)
1. Pulls carryover context from the three required sources
2. QAs the ops-generated report against the locked structure
3. Finalizes the agenda using the locked format
4. Publishes the meeting doc and outputs the meeting lead's brief

If the ops weekly report does not yet exist in Notion, stop and surface to the user. Do not run this skill on stale data.

---

## Required Inputs

Before running, confirm:
- Client name
- Meeting date/time (use Google Calendar to verify if not given)
- The ops-generated weekly report page in Notion — **auto-located in Phase 0** if the GM doesn't paste a link

---

## Phase 0: Locate the Ops Weekly Report (auto-find — don't make the GM hunt for it)

The GM shouldn't have to paste the report link. Find it.

1. **If the GM provided a link**, use it. Skip to Phase 1.
2. **Otherwise, search for it:**
   - Find the client's Notion project page (`notion-search` with client name → their project page)
   - Search the client's **Documents/Document Hub** and **Meeting Notes** databases for the current week's report. Query patterns: `"[Client] Weekly Update"`, `"[Client] Weekly Report"`, `"Week [N]"`, `"W[N]"`, or the meeting's week date range (e.g., "May 6-12").
   - Filter to pages created in the last 7 days. The ops team runs `weekly-reporting` before the GM preps, so the report should be recent.
3. **Confirm the match with the GM before proceeding:**
   - Show: page title, created date, URL
   - Ask: "Found this week's ops report: [title] ([date]). Use this? (y/n)"
   - Only proceed once confirmed. If the GM says it's the wrong one, ask for the correct link.
4. **If multiple candidate reports match** (e.g., a draft + a final, or two weeks), list them with dates and ask which to use. Don't guess.
5. **If NO report is found:**
   - The ops team hasn't run `weekly-reporting` yet for this week. STOP and surface to the GM: "No ops weekly report found for [client] this week. Ops needs to run weekly-reporting first — this skill QAs their output, it doesn't generate the report. Want me to ping ops, or do you have the link?"
   - Do NOT proceed on stale data or fabricate a report.

Once the report page is located + confirmed, carry its page ID through Phases 2–4 (Phase 2 reads it, Phase 4 updates it in place).

---

## Phase 1: Pull Carryover Context (REQUIRED — DO NOT SKIP)

You MUST pull from all three sources below. Do not summarize from memory. Each source has a specific retrieval contract.

### 1a. Last meeting — full notes + transcript

- `SearchMeetings` with client name, sorted by date desc. Take most recent.
- `ReadMeetings` for full notes (the entire `notes` field, not just action items).
- `GetTranscriptsForMeetings` for the full transcript. Read it.
- Extract into the carryover pack:
  - Open commitments (who promised what, due when)
  - Unresolved threads — topics raised but not closed
  - Direct quotes that signal client priorities or concerns
  - Anything the client asked us to follow up on

### 1b. Client emails — last 14 days

- `SearchEmails` with `participant:` filter for every email in the client contact list, joined with OR. Time bound `after:[today minus 14 days]`.
- Read full thread content for any thread that:
  - Was sent by the client (not us)
  - Contains an action item, question, or concern
  - References a meeting, deliverable, or escalation
- Skip auto-generated platform notifications.

### 1c. Slack — last 14 days

- Look up the client's internal Slack channel ID from the client registry.
- `slack_read_channel` with limit=100. Page back with cursor until you cover 14 days.
- Also `slack_search_public_and_private` for client-name mentions outside the dedicated channel (DMs, ops channels, support threads).
- Extract:
  - Decisions made internally that affect the client
  - Issues flagged by the team
  - Operational concerns the client may raise on the call

### 1d. Output the Carryover Context Pack

Write a structured artifact (in-conversation, used by Phases 2–4):

```yaml
open_action_items:
  - item: "..."
    owner: "..."
    age_in_meetings: 3
    source: "meeting 4/14"
unresolved_threads:
  - topic: "..."
    raised_on: "..."
    quote: "..."
    source: "transcript 4/14 @ 12:30"
client_concerns_from_comms:
  - concern: "..."
    source: "email 4/21 from JP"
biggest_perf_change_this_week:
  metric: "..."
  delta: "..."
  source: "ops report W17"
```

If any of the three sources returns nothing, flag it explicitly. Do not fill the gap with assumptions.

---

## Phase 2: QA the Ops Report

Read the ops-generated weekly report. Diff against the locked structure. Each item is a hard check.

- [ ] Section block order: Agenda → Action Items → Key Highlights → Performance Flags → Platform Performance → Location Performance → Ops & Quality → Campaign Performance → QA
- [ ] Agenda has 3–5 bullets, each formatted exactly as: `**[Topic]** — [the question or decision needed]`. Single sentence per bullet. No prose. No "highlights" disguised as agenda.
- [ ] Every open action item from the Carryover Context Pack is either in the agenda or in "Carried Over"
- [ ] Action items aged >2 meetings show escalation count: `*(escalated W14 → W15 → W16 → W17)*`
- [ ] Performance flags ≤5, numbered #1–#5, every flag has Cause + Action
- [ ] No prose analysis sections outside the locked structure. Delete "Why X hasn't improved" essays — that content belongs in the meeting lead's brief, not the client doc.
- [ ] Voice is client-facing. No internal jargon, no "TBD," no internal questions.
- [ ] All numbers passed the QA validation table at the bottom of the ops report

For each failed check, log the specific edit needed. Do not edit yet. Surface the full QA result to the user before applying changes.

---

## Phase 3: Finalize the Agenda

Rebuild the agenda from the Carryover Context Pack. Source priority:

1. Open action items aged >1 meeting (these get top billing — escalating means we keep raising them)
2. Unresolved threads from prior meeting transcript
3. The single biggest WoW performance change this week
4. Any client concern surfaced in emails or Slack in the last 14 days

Format every bullet exactly as: `**[Topic]** — [the question or decision needed]`

Gold-standard examples (match this voice):
- `**AWAN conversion** — menu conversion has been 5%; we reduced prices and tested campaigns. Has this improved? Why or why not?`
- `**Ratings flyers** — supposed to be running. How is distribution going? Have ratings counts moved?`
- `**Venice ops** — week 4 of daily AM pauses. What's the corrective plan?`

Maximum 5 bullets. No section can be a "highlights" dump. No prose.

---

## Phase 4: Apply Edits and Publish

- Use `notion-update-page` to apply the QA edits and the finalized agenda to the existing ops report page. Do not create a new page — the ops page is canonical.
- Confirm the page is published and shareable.

---

## Phase 5: Synthesize the Meeting Lead's Brief

Output to chat (not Notion). Format:

- **Top 3 things that matter today** — the three discussion points worth the meeting lead's prep time. Each one explains what the lead needs to know going in, the current data, and the decision on the table.
- **Action item status** — table of every carried-over item: owner, age in meetings, current status, source.
- **Decisions needed today** — concrete go/no-gos.
- **Watch-outs / sensitive** — relationship dynamics, who's likely to push back, what's politically loaded, who tends to no-show.
- **Open questions to put to the room** — direct asks for the meeting.
- **Sources** — every link cited (Notion docs, Circleback transcript, email thread, Slack channel).

---

## Key Rules

- Never write the agenda from memory. Always derive from the Carryover Context Pack.
- Never invent sections. Stick to the locked structure.
- If a required source (email, Slack, last meeting) returns nothing, flag it explicitly.
- The client doc is for the client. The brief is for the meeting lead. Don't mix them.
- This skill replaces any standalone weekly-report-gm-qa skill. QA is Phase 2 here.

---

## When to Run

- Before every scheduled client meeting (weekly, biweekly, ad-hoc)
- After ops finishes `weekly-reporting` for that week
- Run early enough that QA edits can land before the meeting starts (target: 2+ hours before)

---

## When NOT to Run

- If the ops weekly report doesn't exist yet — wait for it
- If there's no client meeting and no client-facing communication scheduled — the report sits in internal Notion as data; lighter QA can run inside `weekly-reporting` itself
