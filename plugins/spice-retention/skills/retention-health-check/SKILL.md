---
name: retention-health-check
description: Use this skill to run a daily or weekly proactive scan of every retention client's platform health and surface problems before they hit the bi-weekly meeting. Triggers include "retention pulse", "check retention health", "retention health check", "daily retention scan", "weekly retention check", "is anything on fire in retention", "any retention red flags", or any request to monitor retention KPIs across clients. Schedule this skill via scheduled tasks for daily (morning) or weekly (Monday) runs. Output is a traffic-light Slack post per client + flagged items list. Prevents missed automations, dropped sends, and unsub spikes from going unnoticed for 2 weeks.
---

# Retention Health Check

The retention service had zero automated monitoring as of April 2026. Issues only surfaced at the bi-weekly meeting — 14 days late. This skill closes that gap.

## Inputs

- **Frequency**: daily (default) or weekly
- **Clients to scan**: defaults to all three

## Required tools

- Chrome MCP (light Toast / Thanx / Klaviyo dashboard checks)
- Slack (post results)
- Notion (cross-reference Campaign Planning DB)

## What gets checked, per client

Run these checks against each client's primary platform (Toast for MBFS, Thanx for HealthNut, both + Klaviyo for Ahipoki):

### Automation health
- Are all active automations still sending? Flag any with zero sends in past 7 days.
- Are flow conversion rates within range? Flag if any flow has < 50% of its trailing 30-day average.

### Campaign performance
- Did any send in the past 7 days have an open rate below 15%? (HealthNut threshold: below 50%.)
- Any campaign with unsubscribe rate above 2%?
- Any campaign with revenue per recipient below $0.20?

### Schedule adherence
- Are there campaigns in Campaign Planning DB with send date in the past, still status `Scheduled` or `In Design`? (Missed sends.)
- Are there campaigns scheduled for next 3 days that don't yet have approved creative? (At-risk sends.)

### Platform anomalies
- Has loyalty enrollment dropped > 10% week over week?
- Has EDR risen above 4% (over-discounting)?
- Are there campaigns approaching send date with brief but no design started 4 days out?

### Client-specific watch items
- **MBFS**: Are the automations re-uploaded as of Jun 5? If not, flag red.
- **HealthNut**: Are we on track for 3 campaigns this month? If past mid-month and < 2 sent or scheduled, flag yellow.
- **Ahipoki**: Klaviyo migration progress check. Any flow that should be live but isn't, flag.

## Traffic-light scoring

Per client, assign one of:

- **Green**: nothing flagged
- **Yellow**: 1-2 watch items, none time-critical
- **Red**: any one of: missed send, automation stopped, open rate below 10%, EDR above 5%, client-specific critical flag

## Slack output

Post to `#retention-marketing` (or `#spice-ai-ops` for daily automated runs — Harol decides):

```
:traffic_light: Retention pulse — [date]

*MBFS*: :large_green_circle: | :large_yellow_circle: | :red_circle:
[any flags]

*HealthNut*: [light]
[any flags]

*Ahipoki*: [light]
[any flags]

Trend: [up / flat / down vs last check]
Next check: [next scheduled run]
```

If everything is green: short post. "All three clients green. Next check [date]."

If any red flag: also DM Maxx with the specific issue and a recommended action.

## Schedule it

After first manual run, offer to schedule via `mcp__scheduled-tasks__create_scheduled_task`:

- Daily morning at 8am ET (cronExpression: `0 8 * * *`)
- Or weekly Monday at 8am ET (cronExpression: `0 8 * * 1`)

Harol picks the cadence. Default recommendation: daily for the first month while the system gets calibrated, then weekly.

## What this skill is NOT

- Not a deep audit. That's `retention-platform-audit` (when built).
- Not a meeting prep. That's `retention-meeting-prep`.
- Not a monthly report. That's `retention-monthly-report`.

This is a fast, lightweight, recurring "is anything broken" check. Should run in under 5 minutes.
