# Spice Team Skills

Private plugin for the Spice Digital team. Contains reporting, ops, campaign, meeting, and onboarding skills used across delivery marketplace client work.

## Install

```
/plugin marketplace add maxxf/spice-team-skills
/plugin install spice-team-skills
```

After install, update your local Cowork CLAUDE.md to import this plugin's CLAUDE.md (see `setup/onboarding-checklist.md`).

## Required MCP Servers

| Server | Used by | Setup |
|--------|---------|-------|
| Notion | All skills | Notion connector |
| Google Drive | weekly-reporting, menu-conversion-check | Google Drive connector |
| Slack | weekly-reporting, campaign-ops, post-client-meeting | Slack connector |
| Gmail | weekly-prep, client-call-prep | Gmail connector |
| Circleback | weekly-reporting, client-call-prep, post-client-meeting | Circleback connector |

## Skills

See `skills/` for all available skills. Run `@skill <name>` to invoke.

## Onboarding

See `setup/onboarding-checklist.md` for the full setup process.

## Updates

Skills auto-update at the start of each Claude Code session. No action required.

## Maintained by

Maxx Freedman (maxx@spicedigital.co)
