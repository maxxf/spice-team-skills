# spice-operations

Back-office operations for Spice Digital. Covers finance, HR, sales support, and admin workflows that don't belong to a specific client service line.

## Skills (2 so far)

- `client-onboarding` — end-to-end new client onboarding (kickoff email, Notion client space, onboarding tasks, Stripe payment link, Slack channel). Built for Cesar (Head of Client Services).
- `onboarding-status-check` — check onboarding task status across all clients, detect form submissions, migrate credentials into Platform Credentials DB + Client Wiki, post status updates.

## Gap — skills to add when you can

These exist in your local Cowork install but weren't accessible from the sandbox during the extraction. Drop them in manually before pushing:

- `revenue-reconciliation` — monthly revenue reconciliation, Stripe vs Mercury
- `contractor-agreement` — branded Spice contractor agreements (PDF for Agree.com)
- `post-sale-proposal` — post-call proposals + follow-up emails for Spice clients
- `sales-follow-up` — daily pipeline follow-up agent (Circleback + Notion + Superhuman)
- `inbox-triage` — Superhuman inbox scan + categorize + flag
- `circleback-to-notion` — Circleback meeting notes → Notion Team Task Tracker
- `client-call-prep` (could go here OR in spice-marketplaces — currently in marketplaces)

Copy them from `~/Library/Application Support/Claude/...` or wherever your local hostloop plugin cache lives, into `plugins/spice-operations/skills/`. Then bump the version in plugin.json and the marketplace manifest.

## Required connections

| Connector | Used by |
|---|---|
| Notion | both shipped skills |
| Slack | onboarding-status-check (posts updates to `#int-` channels and `#new-clients`) |
| Stripe | client-onboarding (Stripe payment link) |
| Gmail | client-onboarding (kickoff email draft) |

## Voice

Follows Maxx's voice rules. Full guide at `references/maxx-freedman-voice-guide.md`.
