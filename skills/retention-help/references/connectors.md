# MCP connector inventory

What each skill in this plugin uses, and what blocks if missing.

| Connector | Skills that depend on it | Falls back to | Critical? |
|---|---|---|---|
| **Klaviyo** | klaviyo-migration, retention-monthly-report (Ahipoki), retention-flow-designer (Ahipoki), retention-campaign-brief (Ahipoki), retention-qa-checklist (Ahipoki) | Chrome navigation of Klaviyo dashboard | Critical post-Klaviyo-migration |
| **Figma** | retention-campaign-brief, retention-qa-checklist, retention-flow-designer | Manual inspection or asking Dilli | Important, not critical |
| **Notion** | every skill | Nothing — Notion is mandatory | Critical |
| **Slack** | every skill | Nothing — Slack is mandatory | Critical |
| **Google Drive** | retention-monthly-report, retention-meeting-prep | Manual sheet editing in browser | Critical |
| **Google Calendar** | retention-campaign-brief (reminders) | Manual calendar entry | Nice-to-have |
| **Gmail / Circleback** | retention-meeting-prep, retention-help | Manual transcript review | Important |
| **Claude in Chrome / Comet** | retention-monthly-report (Toast + Thanx), retention-health-check (Toast + Thanx), retention-meeting-prep | Nothing — no MCP exists for Toast or Thanx | Critical for Toast + Thanx clients |

## Install paths

If a connector is missing, route to Cowork > Settings > Connectors. Klaviyo + Figma are OAuth — they pop a browser auth window. Notion, Slack, Google services use the standard Cowork auth flow.

## Day-1 verification (Harol)

When Harol asks "what skills do I have", or runs `/retention-help` for the first time, this skill should:

1. Enumerate the 9 skills + 4 commands in this plugin
2. Cross-check the connector status above
3. Surface any missing connector with the specific skill that needs it
4. Suggest installation order: Notion + Slack first (universally required), then Klaviyo + Figma + Google Drive, then Calendar + Gmail, then Chrome last

## What still has no MCP

- **Thanx** — no public API or MCP exists. Stuck on Chrome navigation.
- **Toast** — same. Toast Marketing module is a closed dashboard. Chrome only.
- **MBFS-specific tooling** — Toast covers it.

If a Thanx or Toast MCP appears in the registry later, update the relevant skills to prefer it over Chrome.
