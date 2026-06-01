# Spice Retention Plugin

Operating system for the Spice Digital retention service. Built for the Retention Lead (currently Harol Alvear) and anyone who later inherits the seat.

## What's inside

**Skills** (loaded on demand by trigger phrase):

| Skill | Trigger examples |
|---|---|
| `retention-help` | "what can retention do for me", "retention workflows", "/retention-help" |
| `retention-campaign-brief` | "draft retention brief for [client]", "brief a retention campaign" |
| `retention-monthly-report` | "pull retention report for [client]", "monthly retention report" |
| `retention-meeting-prep` | "prep retention meeting", "prep for retention sync" |
| `retention-health-check` | "retention pulse", "check retention health" |
| `retention-flow-designer` | "design winback for [client]", "build welcome flow", "loyalty flow", "SMS flow" |
| `retention-segments-subjects` | "segment for [client] campaign", "subject lines for [campaign]" |
| `retention-qa-checklist` | "QA this campaign", "pre-send checklist" |
| `klaviyo-migration` | "ahipoki klaviyo status", "klaviyo migration step" |

**Slash commands** (quick entry points):

- `/retention-help` — list every workflow this plugin ships with
- `/retention-brief` — draft a campaign brief end to end
- `/retention-report` — generate a monthly performance report
- `/retention-check` — run the daily/weekly health check

## Clients covered

- **MBFS** (My Big Fat Shawarma) — Thanx + Toast | Alexandra Sawa | #int-my-big-fat-shawarma
- **HealthNut** — Thanx only | Cindy Bailey | #int-healthnut
- **Ahipoki** — Thanx + Klaviyo (migrating) + SMS (incoming) + Toast | Mike Zimmerman via Daniel Ramirez | #int-ahipoki

## Required connections

This plugin uses real MCP tools wherever they exist and falls back to Chrome navigation when they don't. Connect these in Cowork > Settings > Connectors:

| Connector | Used by | Why |
|---|---|---|
| **Klaviyo** | `klaviyo-migration`, `retention-monthly-report`, `retention-flow-designer`, `retention-campaign-brief` | Native API access for Ahipoki — pull campaigns, metrics, events, create campaigns + flows. Replaces Chrome navigation post-migration. |
| **Figma** | `retention-campaign-brief`, `retention-qa-checklist`, `retention-flow-designer` | Pull design context, screenshots, brand variable defs. Verify Dilli's creative against the brief without leaving the chat. |
| **Notion** | every skill | Campaign Planning DB, Spice Wiki, Retention Weekly template, summary pages |
| **Slack** | every skill | `#retention-marketing`, `#design-requests`, client int channels |
| **Google Drive** | `retention-monthly-report`, `retention-meeting-prep` | Retention Tracker sheets, screenshot storage, brand assets folders |
| **Google Calendar** | `retention-campaign-brief` | Send-date reminders 2 days pre-send |
| **Gmail / Circleback** | `retention-meeting-prep`, `retention-help` | Meeting notes, client comms history |
| **Claude in Chrome / Comet** | `retention-monthly-report`, `retention-health-check`, `retention-meeting-prep` | Toast + Thanx dashboards (no public MCPs available for either) |

If any of these is missing when a skill tries to use it, the skill will tell you specifically what's blocking and how to connect it. It will not silently degrade or fabricate data.

### Connector status check

Day-1 verification: run `/retention-help` and the skill confirms which connectors are live. Anything missing is called out at the top.

## Voice + non-negotiables baked in

- Maxx voice rules: no emdashes, no "it's not about X, it's about Y", no watery openers, no AI tells. Direct, first-principles, useful over polite.
- Every external deliverable cites sources.
- Reports get screenshot proof where applicable.
- Strategy Lead routes client comms (Daniel for Ahipoki). Don't go direct without their sign-off.
- Default model: Sonnet for routine work, Opus only for new strategic problems.

## Source of truth

Built from the April 2026 Retention Service Audit, the Improvement Plan & Skill Roadmap, the Tomas Skill Build Guide, and the Harol Lead Onboarding hub. If those Notion pages change, update the skills.
