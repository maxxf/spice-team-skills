---
name: linkedin-followup-reminder
description: >
  Daily 9:00 AM PT reminder DM listing active LinkedIn follow-up tasks from Notion Team Task Tracker with reply drafts. Companion to linkedin-lead-capture. Trigger on "linkedin reminders", "what linkedin follow-ups", "show today's linkedin tasks", or any request to surface pending LinkedIn follow-ups.
---

> This is meant to run once each weekday morning (schedule it if your setup supports it), but it can also be triggered manually from any session.

# LinkedIn Follow-Up Reminder

Query Notion Team Task Tracker for active LinkedIn follow-up tasks due today or earlier, then DM Maxx in Slack with the reply drafts so he can act in 1-2 clicks during his 9:15 admin block.

## Philosophy

Tasks created by `linkedin-lead-capture` are easy to forget if they only live in Notion. This skill surfaces them where Maxx already lives (Slack), with the reply draft already at his fingertips. Read-only on Notion; only side effect is a Slack DM.

## Step 1: Query Team Task Tracker

Query data source `1c8d3ff0-18e7-80f0-a36b-000b6befe5b1` (Team Task Tracker) using filters:

- `Source` equals `Agent` (select equals)
- `Status` equals `Not started` (status equals)
- `Request Title` starts with `LinkedIn follow-up:` (title starts_with)
- `Due date` is on or before today PT (date on_or_before)

Sort by `Due date` ascending. Limit to **25 results**.

## Step 2: Decision

- **Zero matches:** silent exit. Log to console: "No active LinkedIn follow-ups today." No Slack post, no DM.
- **1-25 matches:** proceed to Step 3.
- **25 hit (potential overflow):** still send the DM with the 25 you have, but prepend a warning header `WARNING: 25+ active LinkedIn follow-up tasks. Top 25 shown. Investigate backlog.` This is a runaway-condition signal — Maxx should triage.

## Step 3: Extract reply drafts from Description

For each task, read its `Description` text property. Split on the literal string `---REPLY DRAFT---`. Take the second half (everything after the delimiter), trim whitespace. This is the reply draft.

If a task has no `---REPLY DRAFT---` delimiter (legacy task created before this format was established): skip the reply draft block in the DM, include only the structured context. Note in the DM: `(no draft — created before reply-draft format)`.

Truncate each draft to **500 characters**. If truncated, append `… (full draft in Notion)`.

## Step 4: DM Maxx

Resolve Maxx's Slack user ID via `slack_search_users({query: "maxx freedman"})` if not already cached. Send a single DM (not a thread) with this format:

````
*LinkedIn follow-ups for {Day, Mon DD}* — {count} active

*{Name} — {Company}*
ICP: {X}/100. {qualification one-liner from Description first half}
LinkedIn: {profile_url from Description}
Notion: {task_url}  (mark Done when replied)

Reply draft:
```
{draft text, truncated to 500 chars}
```

---

(repeat per task)
````

The triple-backtick code block around the draft is intentional — it preserves whitespace and lets Maxx copy the draft cleanly into LinkedIn.

## Step 5: Done

Log: "Sent reminder DM to Maxx with {count} follow-ups." Exit.

## Failure handling

- Notion query fails: retry once with 30-second delay. If still fails, DM Maxx: `linkedin-followup-reminder failed: {error message}. Check Notion MCP.`
- Slack DM fails: log to console + console-visible error. (No fallback channel — DM is the surface; if Slack is down, the cron will retry tomorrow.)
- User ID resolution fails: DM cannot be sent. Log error. (Initial deployment must verify the user ID resolves correctly.)

## What NOT To Do

- Never modify Notion tasks. Read-only.
- Never resolve / mark done / change status. That's Maxx's call after he replies on LinkedIn.
- Never DM anyone other than Maxx.
- Never include non-LinkedIn-followup tasks in the DM (filter must be strict).
