# Spice - Shared Team Context

> **Canonical Spice org context, distributed via the `spice-team-skills` plugin.**
> Import this file rather than duplicating it. Bulk tables (Slack channels, Notion IDs,
> weekly cadence, skill-trigger routing, Spicy delegation, workspace layout, full comms
> and pricing detail) live in `references/team-ops-reference.md` — read that when you need a
> specific channel, ID, trigger, or delegation detail. This file carries only always-on essentials.

## About Maxx (Spice founder)
Maxx Freedman. Founder/CEO of Spice Digital. Email: maxx@spicedigital.co
Restaurant delivery marketplace management company. Core services: Delivery Marketplaces
(Uber Eats, DoorDash, Grubhub), Retention Marketing, Paid Acquisition, Advisory.
US-based; team distributed internationally (Colombia, Portugal, Pakistan, India).

## How I Think
First principles. Direct. Context-adaptive. Skip "great question" fluff. Verifiable facts
over platitudes. Useful over polite. When wrong, say so and show better. Quick, clever humor
when it fits. Forward-thinking. Concise, no fluff. Play devil's advocate when necessary.
Self-critique every response internally (rate 1-10, fix, iterate); I only see the final version.

## How I Write (READ BEFORE ANY BRANDED OUTPUT)
Full voice guide: `references/maxx-freedman-voice-guide.md` — read it before writing anything
under my name or the Spice brand. It carries the complete banned-pattern list (em dashes,
"leverage", "game-changer", "I wanted to reach out", watery qualifiers, filler transitions,
sycophantic openers) and the structural rules. Do not write branded copy from memory.

Short version: I write like I talk. Direct, specific, a little spicy. Point in the first
sentence. Numbers to back it up. Clear next step to close. Vary sentence length. Do the math
for the reader (never "affordable" — show the per-location cost). One moment of personality
per piece. Max one exclamation mark. Cut any sentence that doesn't advance the message.

## Active Clients
Source of truth is the Notion Clients DB; this snapshot is quick context. Grouped by service.

- **Delivery Marketplaces**: Abby's Bagels, Ahipoki, AWAN, BDS (Brooklyn Dumpling Shop), Brasa Peruvian, Capriotti's, Counter Service, Dayglow Coffee, Everytable, Fresh Kitchen, goop Kitchen, Menya Ultra, My Big Fat Shawarma (MBFS), PRET, The Chicken Shop, Tiff's Treats, Virgil's BBQ (Alicart), Westville
- **Retention**: Ahipoki, Health Nut, My Big Fat Shawarma
- **Advisory**: Everytable, Fresh Kitchen, goop Kitchen, Westville
- **Paid Media**: Counter Service
- **Past (inactive — do NOT treat as active)**: Teleferic Barcelona, Cal's Corner, Bowld Kitchen, Ambiyan Kitchen, Temaki To Go, Gertie, Moltn
- **Pipeline**: live in the Notion Sales Pipeline CRM — don't hardcode prospect names; check the CRM.

## Team
- **Maxx Freedman**: Founder/CEO. Sales, strategy, product (Spicy). Owns client relationships and closes.
- **Rodrigo Gutierrez**: GM, 3P (marketplace) lead. Client-facing execution.
- **Ana Pernett**: GM. **Daniel Ramirez**: GM.
- **Santiago López**: Senior Ops Analyst. Client-facing.
- **Manish Kumar**: Analytics/ops. Weekly trackers, campaign performance data.
- **Dulari Fernando**: Ops/data (part-time). **David Pliego**: Paid Media Specialist (part-time).
- **Dilli Dias**: Designer. Hero images, flyers, email templates, landing pages (via design-brief flow).
- **Diline G**: EA. Onboarding chase, CRM upkeep, content coordination.
- **Harol**: Retention Specialist (took over from Tomas).
- **Spicy Nugget**: the AI employee/agent — runs skills and scheduled ops. Not a task owner.

## Deliverable Formats (org standard — every skill)
Client-facing deliverables render through the **Spice Design System V.1** (Geist + Geist Mono,
Chili `#FF3B00`, Cream `#FCF3ED`, Espresso `#201916`, 12px card radius). Tokens: HQ
`companies/spice/knowledge/brand/tokens.json`. Never flat documents. (Chili is `#FF3B00`, not
`#fa4803` or `#FF4A1C`; logo SVGs still carry `#FF4A1C` pending reissue — drive the mark from
the accent token.)

Two client shapes, not interchangeable:
- **Diagnostics/audits/reports → hosted on HQ via `/deploy`.** Styled HTML off the tokens.
  Use a random token in the app name, never a guessable `{client}-{service}`. No password —
  the unguessable URL is the control, and these carry client revenue.
- **Proposals → a Notion page**, copied from *TEMPLATE — Client Proposal*, created as a **child
  of the deal record** in the Sales Pipeline, then published to web. Never send the deal record
  URL itself; it holds pricing exceptions and fallback offers.

Full rule: HQ policy `spice-proposals-in-notion-diagnostics-on-hq`.
- **Never produce `.docx`/Word docs** — off-brand and flat. Use hosted HTML, a Notion page, or a design brief.
- The deal record and internal diagnostic are **internal**. Client gets the hosted diagnostic and the published proposal, nothing else.
- **Spreadsheets** (`.xlsx`/Sheets) only where a grid is right: optimized menu sheets, trackers, scorecards.
- **Design work for Dilli** (photos, flyers, hero images, email templates, landing pages) routes through the design-brief flow — a Campaign Planning DB entry + Slack ping to #design-campaigns. Not a Word brief.

## How everyone works clients (org standard)
Client knowledge lives in **HQ** (shared brain) and each client's **Notion Client Wiki**. Do
**not** open or build a per-client Cowork project — just work in Cowork and **name the client**;
it pulls that client's context (creds, tracker URLs, voice, history) automatically. This is how
the team shares context, stays consistent, and stops burning usage re-explaining clients.

- **Source of truth = the client's Notion Client Wiki.** HQ and Cowork *read* from it — they do not duplicate it. One record, no drift.
- **One client = one config = one live sheet.** Per-client skills key off the slug: `campaign-plan` / `weekly-reporting` read `clients/<slug>.json` and update that client's live Sheet in place.

Working a client (everyone, every time): 1) In Cowork, name the client — pulls context from HQ +
the Notion Client Wiki. 2) Drop the week's exports in the client's Drive `Campaign Plan Inputs/<Monday>/`,
then run the skill. **Don't** paste raw client data into a throwaway thread, or keep client context
in your head/local notes instead of the Notion Client Wiki.

## Communication Defaults (summary — full detail in `references/team-ops-reference.md`)
- **Client emails**: canon `references/client-comms-style.md`; governor `references/client-comms-pass.md`
  runs on every client email and client Slack message (never sends). Name opener → why they're reading;
  ask in first three lines; link the analysis; 150 words max (replies under 40 exempt, over 200 a fail);
  one line of human attention; one real closing question. "Happy to jump on a call..." is banned padding.
- **Cold outreach**: three sentences, link the deck, link to book. No essay.
- **Late payment**: state the problem, clear ask, invoice link, "Thank you." No guilt trips.
- **Slack**: direct, tag owners, fragments/lowercase OK in casual channels.
- **Proposals**: modular pricing, always a pilot option, do the math for the reader.
- **Newsletter (Spicy Nuggets)**: lowercase except proper nouns, attitude, punchy, bold key numbers, Beehiiv.
- **Internal**: coach mode — direct feedback, named owners, clear deadlines.

## Standard Pricing (summary — full bands in `references/team-ops-reference.md`)
Source of truth is the **Notion Scope & Pricing Hub**. Read it before quoting; **do not quote
from memory or from a skill file.** Delivery Marketplaces: Track A $2,750 base + $175/location
beyond 5; Track B $1,750 + $100 (5-location minimum, base covers first 5). Loop discontinued
(Jul 2026). ezCater priced on trailing revenue bands, $2,500 floor. Quoting outside these rules
is a founder exception — log it in the deal record's internal notes so it never becomes silent precedent.

## Skill Routing, Slack, Notion, Cadence, Spicy Delegation
The trigger→skill routing table, Slack channel architecture, Notion DB IDs, Maxx's weekly
cadence, Spicy Nugget delegation rules, and the Cowork workspace layout all live in
`references/team-ops-reference.md`. Read it when you need one of those specifics.

## Key References
- `references/team-ops-reference.md`: Slack/Notion/cadence/skill-routing/Spicy-delegation/workspace + full comms & pricing detail
- `references/client-comms-style.md`: client email standard (read before writing to any client)
- `references/client-comms-pass.md`: governor on client comms — drafts and checks every client email and Slack message; never sends
- `references/maxx-freedman-voice-guide.md`: complete writing voice guide (read before any branded output)
- `spice-cowork-audit.md`: full operational audit of skills, agents, plugins, and gaps

---
*Last updated Aug 6, 2026. Team from HQ directory; clients live from the Notion Clients DB.*
