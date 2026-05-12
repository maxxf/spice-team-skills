---
name: context
description: Use when a Spice teammate wants to load Spice org context at the start of a Cowork session or before a complex task. Triggers on "load spice context", "load my spice context", "spice context", "load the team context", "catch me up on spice", "what's going on at spice". Reads the plugin's CLAUDE.md (team, clients, Slack channels, voice rules, workflows) and surfaces a one-page brief. Not the same as Maxx's personal Obsidian-vault context loader.
---

# Spice Org Context Load

Load the shared Spice team operating context for this session. This is the team-facing context loader — it surfaces who Spice is, who's on the team, the client roster, communication conventions, and the skill arsenal.

**Note:** This is different from Maxx's personal `/context` command (which reads his Obsidian vault). That skill is in Maxx's local setup, not in the team plugin. Team members run THIS skill — it pulls from the plugin's shared CLAUDE.md instead.

## Workflow

### 1. Read the plugin's CLAUDE.md

The plugin ships with a `CLAUDE.md` at the repo root that holds the canonical Spice team context. Read it from one of these locations (in order):

1. `<plugin_install_path>/CLAUDE.md` — for Claude Code plugin users (Mode 2). Resolve `<plugin_install_path>` via the plugin manifest or by reading from `~/.claude/plugins/cache/spice-team-skills/spice-team-skills/<version>/CLAUDE.md` if accessible.
2. `~/Desktop/Cowork/Skills/CLAUDE.md` — for Cowork users who placed it manually (Mode 1)
3. `~/Desktop/Cowork/CLAUDE.md` — the original workspace location, if it exists

Use the Read tool to read whichever path is accessible.

### 2. Optionally pull live state from connected MCPs

If the user wants a richer brief (and has the MCPs connected), surface:

- **Active client list** — `notion-search` the Clients DB (`collection://1c8d3ff0-18e7-80e9-8381-000b4448cb87`) for clients with Status = "Active"
- **Recent meetings** — `SearchMeetings` for the last week to surface who Spice has been talking to
- **Recent Slack activity** — `slack_search_public_and_private` with query "spice ops" or similar to get the last day or two of team chatter
- **Calendar** — today + tomorrow's events via the calendar MCP

Skip any of these if the MCP isn't connected. Don't block on missing connectors.

### 3. Synthesize the brief

Output to chat (not a Notion page). Structure:

```
# Spice Context — [today's date]

## Who we are
Spice Digital. Restaurant delivery marketplace agency. Founded by Maxx Freedman.
Core services: Delivery Marketplaces (UE/DD/GH), Retention, Paid Acquisition, Advisory.

## Team
- [pull from CLAUDE.md Team section]

## Active clients
- [pull from CLAUDE.md Active Clients section OR live Notion query]

## Skill arsenal
- [list the team skills in the plugin, grouped by category: reporting, ops, meetings, onboarding, diagnostics, design briefs]

## Slack architecture
- [pull the channel pattern table from CLAUDE.md]

## Today's context (if MCPs available)
- Upcoming meetings: ...
- Recent team activity: ...

## Voice rules (when producing client-facing copy)
- [pull the key voice rules from CLAUDE.md]
```

Target: under 500 words. Don't dump the entire CLAUDE.md verbatim — extract the highlights.

### 4. Confirm what's loaded

End with: "I've loaded Spice org context. Ask me anything about clients, team, skills, or workflows — I have the shared playbook."

## When NOT to use

- If the user is Maxx and they want their personal Obsidian-vault context (use the personal `context` skill in Maxx's local setup)
- If the user is asking about a specific client (use `client-call-prep` or look up the client's Notion page directly)
- If the user wants real-time data (use the relevant MCP directly — Slack, calendar, etc.)

## Common Mistakes

- **Trying to read Maxx's Obsidian vault** — that's a Maxx-only path. Teammates don't have it. If the read fails, that's the bug — fall back to the plugin's CLAUDE.md.
- **Loading too much** — a 2000-word brief is useless. Keep it under 500 words and let the user ask follow-ups.
- **Skipping CLAUDE.md** — the plugin's CLAUDE.md is the source of truth for the team context. Always read it first.
