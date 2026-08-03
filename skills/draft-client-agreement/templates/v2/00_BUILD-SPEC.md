# Multi-Service Agreement — Build Spec (v2)

**Status:** Draft for Maxx review. Nothing in the live Agree.com template has been
changed. This spec plus the SOW drafts in `sows/` are the source material the v2
skill and the certified Agree.com templates will compile from.

**Goal:** Move the `draft-client-agreement` skill from a single hardcoded
DM-only template to a modular system that assembles an agreement from any
combination of Spice's five service models, with current (July 2026) pricing and
the Two-Track Standard baked in.

---

## 1. The five service models

Each model is a self-contained SOW that plugs into one governing MSA. Full drafts
live in `sows/`. Pricing below is the canonical July 2026 state, reconciled
against the Scope & Pricing Hub.

| # | Service | Billing shape | Standalone? | Two-track? |
|---|---------|---------------|-------------|------------|
| 1 | Delivery Marketplaces | Recurring monthly | Yes | Yes (A/B) |
| 2 | Retention Marketing | Recurring monthly (+ one-time setup) | Yes | No (flat) |
| 3 | ezCater Catering | Recurring monthly | Yes | Yes (A/B) |
| 4 | Advisory | Recurring monthly | **No — add-on only** | No (flat) |
| 5 | Marketplace Launch | One-time milestone (40/30/30) + recurring at go-live | Yes | Track A only at signing |

### 1.1 Delivery Marketplaces (recurring)
- **Track A (Flat):** $2,750/mo base (covers first 5 locations) + $175/location beyond 5.
- **Track B (Performance):** $1,750/mo base (covers first 5) + $100/location beyond 5, plus **10% of net-payout dollars above (baseline + 5%)**, summed across UE/DD/GH, same-store basis. New stores join the baseline set at their 12-month mark.
- **Track B discovery gate:** ≥ $125K/mo top-line delivery (~$1.5M/yr) across managed platforms, OR ≥ $75K/mo net payout if the client shares payout figures. Below the floor → Track A only.
- Menu updates $50/hr; design work $75/hr (project-based, not billed monthly).
- **Loop is discontinued** — no analytics pass-through on any track. Remove all Loop language from the SOW.

### 1.2 Retention Marketing (recurring, flat only)
- **Basic $1,000/mo** — 2 campaigns/mo, client-led planning, 1 revision/campaign.
- **Standard $1,750/mo** — 4 campaigns/mo, collaborative (1 monthly planning session), 2 revisions.
- **Pro $2,500/mo** — 4 campaigns/mo + A/B testing, advanced segmentation, multivariate; 2 monthly planning sessions; 2 revisions.
- **Setup $3,500 one-time** — 4 automations (welcome, winback, 1st-to-2nd, loyalty) + brand library + 5 templates. **Waived on 6-month commitment.**
- Additional email campaign $375 each.
- **SMS add-on $500/mo** + $500 one-time activation (10DLC, opt-in, automation cloning; waived on 6-month add-on commit). Up to 4 SMS flows, 2 SMS campaigns/mo, +$200 per extra SMS campaign. Compliance owned by Spice. Platforms: Toast, Thanx, Klaviyo (must already run email there).

### 1.3 ezCater Catering (recurring)
- **Track A (Flat):** $1,250/mo base (covers first 5) + $150/location 6–10 + $75/location 11+. 50+ locations = custom enterprise quote.
- **Track B (Performance):** $750/mo base (covers first 5) + $100/location 6–10 + $50/location 11+, plus **10% of net-payout dollars above (baseline + 5%)**.
- **Track B discovery gate:** ≥ $65K/mo ezCater sales (~$780K/yr), OR ≥ $50K/mo payout if shared.
- v1 scope is the **marketing/visibility layer**: reliability & pause management, Reliability Rockstar badge pursuit, Preferred Partner bidding / ezRewards / sponsored listings / promotions, menu-packaging-photo conversion, monthly reporting. **Not** corporate-account sales outreach. Monthly cadence.

### 1.4 Advisory (recurring, flat, **add-on only**)
- **Advisory-Lite $2,500/mo** — 1-hr strategy call every 2 weeks with Maxx, async Slack/email, quarterly review, cross-service coordination.
- **Fractional Head of Growth $5,000/mo** — weekly strategy meetings, full growth roadmap (quarterly OKRs / monthly priorities / weekly actions), ops-team coordination, P&L/margin review, new-market planning.
- **Hard rule: Advisory is never sold standalone.** It must attach to at least one operational SOW (Delivery, Retention, Catering, or Launch). The skill must refuse an Advisory-only envelope.

### 1.5 Marketplace Launch Package (one-time milestone + recurring at go-live)
- **$12,000 one-time** (covers first 5 locations) + $500/location beyond 5.
- **Milestone billing (deliverables, not retainer):** 40% ($4,800) at signing · 30% ($3,600) at build-complete · 30% ($3,600) at go-live.
- **Ongoing management starts at go-live** at Delivery Marketplaces rates (Track A $2,750/mo base default; Track B only at first renewal once history exists).
- **Not waivable** — it is the product, not a fee.
- 6-month ongoing minimum clock starts **at go-live**, not signing (~9-month typical total engagement).
- Optional lever: client commits to a 12-month ongoing minimum at signing → credit $2,000 against the launch package.
- 5-location minimum. Applies only to brands not live (or dark) on the managed marketplaces; existing clients adding one platform stay in ongoing scope (no launch package).

### 1.6 Cross-cutting standards (apply to every SOW)
- **5-location minimum**, every service model, no exceptions. The base fee covers the first 5 locations.
- **6-month initial term**, then month-to-month, 60-day notice after the initial term.
- Upfront payment, auto-pay ACH or credit card, on/about the 1st of each billing cycle. Fees prorated for partial months.
- Adding a service module mid-term does **not** reset the 6-month clock; new module prorated for the current month.
- Removing a service requires 30-day notice; cannot drop below minimum viable package during the initial term.
- Standard exclusions: platform commission fees, ad spend (pass-through, billed separately), third-party software, photography/videography production, physical collateral.
- Two-track (A/B) applies to **Delivery + Catering only** in v1. Retention and Advisory are flat-only.

---

## 2. Assembly architecture (Option A — modular library + dynamic fields)

### 2.1 Document model
One envelope = **MSA (governing) + N service SOWs + Schedule A (consolidated fees) + one master signature block.**

- **MSA** — unchanged governing terms. Client fills company name + address + effective date **once** in the MSA header (already deduped in v2 of the current template).
- **Service SOWs** — one per selected service, page-break separated, each incorporated into the MSA by reference. Each SOW carries only its service-specific Scope / Deliverables / Pricing Matrix / Monthly Rate Summary. The full Term / Termination / Payment boilerplate lives in the MSA and shared boilerplate, not repeated per SOW (extends the v2 dedup that already removed the SOW party tables).
- **Schedule A — Fees Summary** — a single rollup table of every active SOW's recurring monthly fees + any one-time fees (Retention setup, SMS activation, Launch milestones), with the combined monthly total. One place the client sees the whole number.
- **Master signature block** — signs the entire package once. Spice: signature + date (Maxx). Client: signature + printed name + title + date.

### 2.2 Field model — must go dynamic
The current skill hardcodes 15 field positions (`122`, `349`, …). **That map breaks the instant the SOW count changes**, because every added SOW shifts ProseMirror positions. For a modular system the skill must:
1. Assemble the blocks (MSA + selected SOW blocks + Schedule A + signature).
2. **Scan** `tiptap.view.state.doc.descendants()` for `field` nodes at assembly time.
3. Assign `recipient_id` by field role/order (effective_date + company + address + master signature set), not by hardcoded absolute position.
4. `saveRevision()` and verify partyNone = 0.

Target field set (fixed regardless of SOW count, because term/payment/signature are centralized):
- MSA header: `effective_date` (Spice/Maxx), `company_name` (client), `address` (client).
- Master signature: `spice_signature` + `spice_date` (Maxx); `client_signature` + `client_name` + `client_title` + `client_date` (client).
- **7 fields total, position-independent.** Everything else (fees) is pre-filled text, not a signer field.

### 2.3 Skill inputs (per deal)
- Services selected (1+ of the five; Advisory requires ≥1 operational service).
- Per Delivery/Catering: Track A or B (skill applies the discovery gate — Track B requires the trailing sales floor be captured and cleared, else Track A only).
- Retention: tier (Basic/Standard/Pro) + SMS add-on yes/no.
- Advisory: tier (Lite / Head of Growth).
- Launch: location count + optional 12-month-commit credit.
- Location count (enforce 5-location minimum).

### 2.4 Block library (mirrors current injection method)
Store certified block sets per service (same `localStorage` + `replaceBlocks` + `saveRevision` mechanism the skill already documents). Assemble = MSA blocks + selected SOW block sets (page-break separated) + Schedule A + signature block.

---

## 3. Structural decisions — LOCKED (Maxx, Jul 22 2026)

1. **One master signature block** for the whole package. A single execution covers the MSA and every attached SOW. 7 signer fields total, position-independent.
2. **Schedule A consolidated fee summary page** — single rollup of all recurring + one-time fees (Retention setup, SMS activation, Launch milestones) into one combined monthly total.
3. **Term centralized in the MSA.** Term / termination / payment live once in the MSA and govern all SOWs. Each SOW references it and states only service-specific nuance (e.g., Launch's go-live clock start).
4. **Track baked in per deal.** The skill selects the track (applying the Track B discovery gate); the signed DM/Catering SOW shows only the chosen track's numbers.
5. **Launch = one envelope, both line types.** The Launch SOW carries the one-time 40/30/30 milestones and the recurring-at-go-live management in a single agreement, one signing event. **Build dependency:** verify Agree.com's billing widget handles one-time + recurring line items together before this ships (its one-time/autorenew toggle suggests yes — confirm with a test envelope).

---

## 4. Build sequence (after content approval)

1. **Legal review** of the five SOW drafts in `sows/` (long pole — these are new contract surfaces).
2. Rebuild the certified Agree.com **source templates**: updated MSA (if term centralizes), one certified SOW template per service, Schedule A, master signature block.
3. Extract certified block sets into the skill's block library (localStorage injection method).
4. Rewrite the skill's field logic from hardcoded positions to **dynamic scan** (Section 2.2).
5. Add service-selection + track-gate + pricing-rollup logic to the skill.
6. End-to-end test envelope for each combination class: single service, stacked recurring (DM + Retention + Advisory), and Launch (milestone + recurring).

Do **not** edit the live canonical template (`1abce0bb…`) until steps 1–2 are approved — every future client agreement inherits it.

---

## 5. Integration path — Agree.com REST API (RECOMMENDED; supersedes browser automation)

**Finding (Jul 23 2026):** Agree.com has a full REST API — `agree.com/developers`.
The skill's "browser-only, no public API" premise is outdated. There is **no
Agree.com MCP** (registry empty), but the REST API makes one unnecessary.

**What the API covers (confirmed from the developer docs):**
- Generate agreements from templates; assign signature fields; manage contacts; send for signature.
- **Webhooks on every event — signatures, payments, invoice-status changes.**
- Native **payments: ACH / card / wire, one-time OR recurring on any schedule.**
- Auth: OAuth / Bearer API key.

**Why rebuild on the API.** It retires the most brittle part of the skill — the
React-fiber walk, `saveRevision` hunt, Cloudflare 403 lockouts, title
sanitization, and the classifier-blocked send all exist only because the flow was
browser-only. On the API: envelope create, field assignment, and send become clean
authenticated calls (send still gated behind an explicit Maxx confirmation, but as
a proper API call, not injected JS).

**Two unlocks the browser path can't do:**
1. **Webhook on `signed` → auto-advance the Notion deal to "Signed"/onboarding and trigger client-onboarding-v2.** Kills the manual status-update and "did they sign yet" roadmap items.
2. **Native recurring + one-time payments** — resolves the Launch one-time-plus-recurring dependency (Section 3, item 5) directly.

**Open decision — billing consolidation.** Spice already runs **Stripe** (subscriptions, via client-onboarding-v2) and **Mercury** (banking). Agree.com payments overlap with Stripe. Options:
- **(1, recommended) Agree.com for signature only; Stripe stays the biller.** Smallest change, billing stack intact.
- **(2) Agree.com carries billing too** (recurring + Launch milestones) — one sign→pay system, but migrates billing off Stripe.
- **(3) Hybrid** — Agree.com for Launch one-time milestones (awkward in Stripe), Stripe for recurring.

**Operational prerequisite:** an Agree.com **API key stored in your team's secret store (Bitwarden or equivalent) — never pasted**. Then map the API's template + field model to the block library in Section 2.4 and wire the `signed` webhook.

**Revised build sequence (replaces Section 4 steps 2–4 once the API is adopted):**
1. Legal review of the five SOW drafts (unchanged — still the long pole).
2. Store Agree.com API key in your team's secret store (Bitwarden or equivalent); confirm template + field endpoints against the drafts.
3. Certify one template per service in Agree.com; record template IDs + field IDs.
4. Rebuild the skill's Step 4 on API calls (create-from-template, assign fields, add recipient, send) — retire the browser-automation JS (keep it documented as fallback only).
5. Wire the `signed` webhook → Notion stage advance + onboarding trigger.
6. E2E test: single service, stacked recurring (DM + Retention + Advisory), Launch (milestone + recurring).

Sources: agree.com/developers, agree.com/about.
