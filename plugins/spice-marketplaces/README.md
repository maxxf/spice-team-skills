# spice-marketplaces

Delivery marketplace operations for the Spice Digital team. Covers Uber Eats, DoorDash, and Grubhub work for restaurant clients.

Extracted from `spice-team-skills` v1.11.1 as part of the move to per-function plugins. This is one of five: `spice-marketplaces`, `spice-retention`, `spice-paid-media` (forthcoming), `spice-design`, `spice-operations`.

## Skills (19)

**Weekly cadence**
- `weekly-reporting` — process weekly UE/DD/GH reports, paste-ready tracker updates + Notion writeups
- `weekly-scorecard` — Spice Weekly Scorecard live artifact + per-client export
- `ratings-reply` — review reply management + $5 credit incentives across UE and DD

**Campaign ops**
- `campaign-ops` — full campaign ops pipeline (single source of truth)
- `campaign-setup` — fully briefed campaign implementation tickets
- `campaign-plan` — per-client campaign plan + Excel performance tracker

**Client diagnostics (orchestrator + 5 sub-skills)**
- `client-diagnostics` — 90-day diagnostic, publishes to Notion client workspace
- `diagnostic-action-plan` — tier-aware action plan
- `diagnostic-campaigns` — ROAS, ad spend, promo stack
- `diagnostic-menu` — menu CVR, photo coverage, hero status, category sprawl
- `diagnostic-ops` — ratings, error rate, cancellation, uptime, hours accuracy
- `diagnostic-topline` — gross sales, momentum, payout, platform breakdown

**Storefront + menu**
- `storefront-audit` — prospect storefront audits on UE/DD/GH (for sales)
- `menu-conversion-check` — UE conversion funnel diagnosis
- `optimized-menu-sheet` — implementation menu sheet builder
- `hero-image-review` — hero image scoring + creative direction
- `store-ops-leaderboard` — monthly per-store ratings velocity + ops quality

**GM workflow**
- `client-call-prep` — pulls carryover from emails, Slack, prior meeting + QAs the weekly report
- `post-client-meeting` — finalize and share meeting notes

## Required connections

| Connector | Used by |
|---|---|
| Notion | every skill |
| Slack | weekly-reporting, campaign-ops, post-client-meeting, ratings-reply |
| Google Drive | weekly-reporting, weekly-scorecard, menu-conversion-check, store-ops-leaderboard |
| Gmail | client-call-prep |
| Circleback | client-call-prep, post-client-meeting |
| Claude in Chrome / Comet | storefront-audit, menu-conversion-check, hero-image-review (UE/DD/GH dashboards) |

## Voice + non-negotiables

Every client-facing deliverable follows Maxx's voice rules. The full guide ships at `references/maxx-freedman-voice-guide.md`.

Short version:
- No emdashes
- No "it's not about X, it's about Y"
- No "here's the kicker", no "level up", no AI tells
- Direct, specific, numbers over adjectives

## Versioning

Semver in `plugin.json`. Bump on every meaningful change. Marketplace consumers run `/plugin marketplace update` to pull.
