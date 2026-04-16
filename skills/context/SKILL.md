---
name: context
description: Load Maxx's full life + work state. Trigger on "/context", "load my context", "what am I working on", "catch me up", or at the start of any deep work session. Reads the Obsidian vault index, top-of-mind, active projects, and recent daily notes to build a complete picture.
---

# Context Load

Load the full operating context for this session by reading from the Obsidian vault and connected systems.

## Workflow

### 1. Read Vault Core (Obsidian MCP)

Read these files from the Obsidian vault in parallel:

- `00-home/index.md` — master briefing, who Maxx is, system overview
- `00-home/top-of-mind.md` — what's active this week
- Latest 3 daily notes from `00-home/daily/` (most recent first)

### 2. Read Domain MOCs

Read all MOC files to understand current state of each domain:

- `spice/_spice-moc.md`
- `brand/_brand-moc.md`
- `people/_people-moc.md`
- `ideas/_ideas-moc.md`
- `beliefs/_beliefs-moc.md`

### 3. Pull Live State from Connected Systems

In parallel:
- **Calendar**: Pull today's and tomorrow's events via Google Calendar MCP
- **Slack**: Check for unread messages or mentions in key channels
- **Gmail**: Check for flagged/important emails from last 24 hours

### 4. Synthesize Context Brief

Present a structured brief:

```
## Context Brief — [date]

### Who You Are
(One-liner from vault index)

### This Week
(From top-of-mind.md)

### Today
- Calendar: [meetings today]
- Pending: [action items from recent daily notes]
- Attention needed: [flagged emails, Slack mentions]

### Active Across Domains
- Spice: [active client work]
- Brand: [content in progress]
- Ideas: [concepts being explored]

### Carry-Forward
(Unfinished items from last 3 daily notes)
```

### 5. Ask

"What do you want to focus on today?"
