# Spice Team Ops Reference (load on demand)

Detailed org tables and routing that don't need to ride every turn's context.
The always-on essentials live in `CLAUDE.md`; read this file when you need the
specific channel, database ID, cadence, skill trigger, or delegation detail.

## Slack Architecture

| Channel Pattern | Purpose |
|---|---|
| #spice-ops | Daily kickoffs, operational updates (Spicy Bot posts here) |
| #spice-reports | Automated reporting outputs |
| #spice-actions | Action items and escalations |
| #spice-digest | Digest/summary posts |
| #spice-website-leads | Inbound lead notifications |
| #team-spice | General team channel |
| #content-spice-linkedin | Content pipeline coordination |
| #int-[client] | Internal channel per client (e.g., #int-goop-kitchen) |
| #ext-[client]-spice | External shared channel with client |
| #design-campaigns | Design briefs to Dilli |
| #spice-ai-ops | Delegation channel for @Spicy Nugget |

## Notion Structure

| Database | ID | Purpose |
|---|---|---|
| Sales Pipeline | `1c0d3ff0-18e7-80fa-b0b6-cc5887a502c4` | CRM for prospects and deals |
| Team Task Tracker | `1c8d3ff0-18e7-8054-8b14-cbc13c26bb25` | Action items assigned from meetings |
| Content Pipeline | `2d1d3ff0-18e7-813c-8e5f-c95a5e33d4fe` | Editorial calendar and content ideas |
| Content Calendar | `2d1d3ff0-18e7-81be-bf3a-ece205560b99` | Publishing schedule |
| Spice Agent Product Spec | `313d3ff0-18e7-81d8-9841-c57d4939da6e` | AI product development |
| Client Dashboard | Per-client workspaces with onboarding tasks | |
| Bi-Weekly Company Review | Internal KPI review doc | |

## Maxx's Weekly Cadence

### Daily Blocks
- 8:30-10:15: Workout/walk
- 9:15-9:45: Email/Admin
- 10:00-12:30: Deep Work
- 12:30-1:30: Block

### Weekly Pattern
- **Monday**: Team Standup (12pm), client calls afternoon (BDS, gK, PRET, Caps, Fresh Kitchen), product/app work (3:30-5:30)
- **Tuesday**: Biweekly syncs (goop x DoorDash marketing)
- **Wednesday**: Everytable sync
- **Thursday**: Open client calls, sales calls
- **Friday**: lighter schedule
- **Sunday evening**: Weekly prep

## When Maxx Says... (skill routing)

| Trigger | Skill |
|---|---|
| "prep for [client]" / "prepare for [client] meeting" | client-call-prep |
| "wrap up [client] meeting" / "send meeting recap" | post-client-meeting |
| "draft proposal for [client]" | post-sale-proposal |
| "weekly prep" / "prep for the week" / "Sunday prep" | weekly-prep |
| "onboarding status" / "who's behind on onboarding" | onboarding-status-check |
| "revenue reconciliation" / "how much should I pay myself" | revenue-reconciliation |
| "audit [restaurant]" / "grade their storefront" | storefront-audit |
| "menu sheet for [client]" / "optimize menu" | optimized-menu-sheet |
| "newsletter" / "spicy nuggets" / "what's happening in delivery" | spicy-nuggets-newsletter |
| "mine content" / "what can we post" / "pull content" | content-mining |
| "onboard [client]" / "set up [client] workspace" | client-onboarding |
| "contractor agreement for [name]" | contractor-agreement |
| "humanize" / "make this sound human" / "de-AI this" | humanizer |
| "process weekly reports for [client]" | weekly-reporting |
| "assign tasks from meetings" / "sync Circleback" | circleback-to-notion |
| "load my context" / "catch me up" / "what am I working on" | context |
| "trace [topic]" / "how did I get here" / "show me the evolution" | trace |
| "connect [A] and [B]" / "bridge these ideas" | connect |
| "ingest this" / "add to vault" / "capture this" / "process meeting" | ingest |
| "what patterns" / "generate ideas" / "what am I missing" | ideas-from-vault |
| "linkedin leads" / "check LinkedIn" / "who connected on LinkedIn" / "LinkedIn inbound" | linkedin-lead-capture |

## Delegating to Spicy Nugget

Spicy Nugget is the AI employee running 24/7 on the Mac Mini. When a task is
operational (data pull, audit, meeting prep, analysis, onboarding, campaign
work), delegate to Spicy via Slack.

**How to delegate:**
1. Post in #spice-ai-ops: "@Spicy Nugget [task description]"
2. Or tell me: "Have Spicy do X" and I'll post to Slack on your behalf
3. Maxx can also DM @Spicy Nugget directly in Slack from his phone

**Spicy handles:**
- All scheduled ops (16 jobs fire automatically)
- Storefront audits, menu sheets, call prep, meeting wrap-up
- Campaign planning, ROAS analysis, campaign management (with approval)
- Menu updates (with approval)
- Data sync, ratings scrape, analysis
- CSV imports from platform report emails
- Onboarding task tracking and status checks
- Content mining and newsletter drafts
- Proactive monitoring (Slack context, email, calendar, business risks)

**Maxx keeps personally (NOT for Spicy):**
- Proposals and sales emails (voice-specific)
- Revenue reconciliation (financial)
- Contractor agreements (legal)
- Vault operations (context, trace, connect, ingest, ideas)
- Humanizer (personal voice)
- Board letters
- Won deal billing sync

## Workspace File Structure

```
/Cowork/
├── Clients/
│   ├── GK/          (goop Kitchen working files)
│   ├── Pret/        (PRET working files)
│   ├── Westville/   (Westville working files)
│   └── _Internal/Weekly-Prep/
├── Content/         (LinkedIn posts, content plans)
├── Finance/         (Revenue reconciliation spreadsheets)
├── Skills/          (.skill files for deployment)
└── [working files: reports, proposals, audits]
```

## Communication Defaults — full per-channel detail

### Client Emails
**Canon: `references/client-comms-style.md`.** Skeleton, 150-word ceiling,
banned-pattern table, before/after pairs. **Governor: `references/client-comms-pass.md`**
runs on every client email and client Slack message (drafts + checks length,
ask position, link, banned patterns, dashes, voice, human-attention line). It
never sends. Short version: name opener, then immediately why they're reading;
ask in the first three lines; specific metrics but link the analysis; 150 words
max (replies under 40 exempt, over 200 is a fail); one line of specific human
attention per email; close with one real question, not three soft exits. Note:
"Happy to jump on a call..." is now banned padding — use "Want to talk it
through?" or cut.

### Cold Outreach
Three sentences. Link to the deck. Link to book a call. Done. No essay.

### Late Payment / Escalation
State the problem immediately. Clear ask. No softening, no guilt trips, no
threats. "I want us to get current on payments this week." Then the invoice
link. Then "Thank you."

### Slack Posts
Direct, action-oriented. Tag owners explicitly. Fragments OK. Lowercase fine in
casual channels.

### Proposals
Modular pricing. Always include pilot option. Reference storefront audit
findings when available. Do the math for the reader (per-location cost with
reframe).

### Newsletter (Spicy Nuggets)
All lowercase except proper nouns. Attitude. Short punchy paragraphs. Bold key
numbers. Published on Beehiiv.

### Internal Team
Coach mode. Direct feedback, named owners, clear deadlines. First-principles
thinking, no fluff, verifiable data.

## Standard Pricing Reference (detail)

Source of truth is the **Notion Scope & Pricing Hub**. Read it before quoting;
do not quote from memory or from a skill file.

- *Two-Track Pricing Standard (July 2026)* — 5-location minimum, base covers first 5, Track A flat vs Track B performance, and the Track B eligibility gates
- *Delivery Marketplaces Pricing* — Track A $2,750 base + $175/location beyond 5; Track B $1,750 + $100. **Loop is discontinued (Jul 2026)**, no pass-through on any quote
- *ezCater Catering Pricing v2 (Aug 2026)* — prices on trailing ezCater revenue bands, not location count. $2,500 price floor, $35K/mo qualification floor, 8% of channel ceiling
- *Retention Marketing Pricing*, *Advisory Pricing*, *Standard Contract Terms*

Quoting outside these rules is a founder exception. Log it in the deal record's
internal notes so it does not become silent precedent.

## Active Projects Beyond Client Work
- **Spicy**: Spice's software product, in active development. Daily calendar block.
- **Newsletter**: "Spicy Nuggets" weekly on Beehiiv.
- **Hiring**: open roles tracked internally — ask Maxx for the current list.
