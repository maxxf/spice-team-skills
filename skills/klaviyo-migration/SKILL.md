---
name: klaviyo-migration
description: >
  Use this skill for any work related to the Ahipoki Klaviyo migration, which
  started Week 2 of June 2026 and is the biggest active retention workstream.
  Triggers include "ahipoki klaviyo", "klaviyo status", "klaviyo migration",
  "klaviyo flow rebuild", "set up klaviyo for ahipoki", "klaviyo provisioning",
  "anas hoque update", "klaviyo SOP", "klaviyo + thanx integration", "how is
  the klaviyo migration going", or any reference to Klaviyo configuration, flow
  porting, SMS layer setup, or the Klaviyo SOP build that's Harol's first
  written deliverable (due Jun 26). Output depends on the trigger and can be a
  status update, a next step, technical config, or a SOP draft.
---

# Klaviyo Migration (Ahipoki)

Ahipoki is migrating to Klaviyo. This is the biggest active retention workstream and Harol owns it. The migration unlocks SMS (currently blocked on Thanx due to the cumulative-stats wipe issue) and rebuilds flows on a more flexible platform.

## Required tools

- **Klaviyo MCP** (`mcp__plugin_marketing_klaviyo__*` or equivalent — connect via Cowork > Settings > Connectors > Klaviyo). 27+ tools including `get_campaigns`, `get_campaign`, `create_campaign`, `assign_template_to_campaign_message`, `get_catalog_items`, `get_events`, `get_metrics`, `get_account_details`. See `references/klaviyo-mcp-tools.md` for mapping per skill phase.
- Notion (project tracking)
- Slack (`#int-ahipoki`, plus DM Daniel for client comms)
- Email (Anas Hoque is the Klaviyo partner contact)
- Chrome MCP / Comet (only as fallback if the Klaviyo MCP isn't connected yet)

If the Klaviyo MCP is not connected, the first action is to install it. Do not proceed with Chrome navigation for Klaviyo work when the API is available.

## What this skill does, based on the trigger

### "Klaviyo status" / "how's the migration going"

First call `get_account_details` on the Klaviyo MCP to confirm the account is live + Spice has admin. Then call `get_campaigns` to see what's been built. Use that data to populate the status report (don't rely on Notion-only tracking).

Output a status report:

```
## Klaviyo migration status — [date]

**Phase**: [provisioning | integration | flow rebuild | SMS layer | testing | live]

**Completed**
- [list]

**In progress**
- [list with owners + ETAs]

**Blocked**
- [list with blockers + escalation path]

**Next 7 days**
- [planned work]

**Key dates**
- Provisioning kickoff: Jun 2
- Klaviyo SOP due: Jun 26
- Target live for first Klaviyo campaign: [TBD - depends on provisioning]

**Stakeholders**
- Harol — owns execution
- Daniel — owns client comms with Mike
- Anas — Klaviyo partner contact
- Maxx — SMS decision + escalation
```

Pull current state from the Ahipoki Service Upgrade & Transition Plan in Notion.

### "Klaviyo next step"

Look at the phase. Return the single next blocking action.

### "Set up Klaviyo" / "provisioning"

Walk through provisioning checklist:

1. **Account provisioning** (Anas owns)
   - Klaviyo account created under Spice's partner login
   - Billing tied to client (not Spice)
   - Admin access for Harol
   - Read access for Daniel

2. **Thanx integration**
   - Native Klaviyo + Thanx connector enabled
   - Customer sync confirmed (132K customers, 69K loyalty members)
   - Loyalty point balances syncing
   - Visit history syncing
   - Verify customer match rate above 90%

3. **List + segment setup**
   - Master list created from Thanx sync
   - 6 core segments built (engaged, lapsed, VIP, new subscribers, SMS-consented, points-expiring)
   - Suppression lists configured (unsubscribed, complained, bounced)

4. **Sender authentication**
   - DKIM, SPF, DMARC configured for `ahipoki.com`
   - Sender warmup if needed
   - Branded sending domain set up

5. **SMS provisioning**
   - Toll-free number purchased
   - 10DLC registration submitted (3-10 business days)
   - Carrier approval received
   - SMS opt-in mechanism (Klaviyo form on `ahipoki.com`)
   - TCPA compliance audit

### "Flow rebuild" / "port flows from Thanx"

Walk through the flow rebuild plan. The 6 active Thanx automations to rebuild on Klaviyo:

| Flow | Thanx config | Klaviyo build priority |
|---|---|---|
| Welcome | 3-email sequence, immediate / day 3 / day 8 | Day 1 |
| 2nd Purchase Bounceback | Day 7, day 14 | Day 2 |
| 3rd Purchase Activation | Day 14 | Day 3 |
| Win Back | Day 60 lapsed | Day 4 |
| Abandoned Cart | 2h, 24h, 72h | Day 5 |
| Birthday | 7 days before | Day 6 |

Plus a new flow that Thanx couldn't support:

- **Points expiring** — fires when customer has > 100 points expiring in next 30 days, sequence Day -30, Day -14 (SMS), Day -3

For each flow:
1. Build in Klaviyo Flows
2. Test with internal email (use `success@spicedigital.co` + DM Harol)
3. Compare 7-day performance to last 30-day Thanx baseline
4. Activate
5. Sunset Thanx version after 14 days of overlap

### "Klaviyo SOP" / "SOP build"

This is Harol's first written deliverable, due Jun 26.

The SOP should be modeled on the existing [Retention Associate - Thanx Training](https://www.notion.so/28dd3ff018e78071bdd8fdae872bbcf2) doc. Cover:

1. Account setup + Thanx native integration
2. List hygiene + segmentation strategy
3. Flow library (with the 6+1 flows above as templates)
4. Campaign cadence + frequency caps
5. SMS layer + TCPA compliance
6. Deliverability (DKIM / SPF / DMARC, sender warmup, list cleaning)
7. Reporting (KPIs, attribution, integration with the Retention Tracker sheet)
8. Troubleshooting common issues

Output should be a Notion page in the Spice Wiki under "Spice Brain & SOPs", parented under Retention | Playbook.

Style: same voice as the Thanx Training Guide. Operational, step-by-step, with screenshots where helpful.

## Key contacts

- **Anas Hoque** — Klaviyo partner contact. Daniel briefs before first call. Don't engage solo until then.
- **Daniel Ramirez** — Ahipoki Strategy Lead. He runs all Mike comms. Loop him before any client-facing change.
- **Mike Zimmerman** — Ahipoki client side. Smart, demanding. Route through Daniel.
- **Maxx** — SMS decision, billing transition (Thanx → Klaviyo as primary), strategic escalation.

## What this skill is NOT

- Not the Klaviyo configuration itself. The skill walks Harol through it. The dashboards are still manual.
- Not the SMS automation rollout decision. That's a Maxx call (see open decisions).
- Not Thanx sunset planning. Don't kill Thanx flows until Klaviyo equivalents have 14 days of clean overlap data.

## Success criteria

- All 6 existing flows ported and live by end of Month 2
- SMS layer active with at least one flow (winback or points-expiring) by end of Month 2
- Zero flow downtime during the migration
- Klaviyo SOP published Jun 26
- First Klaviyo monthly report integrated into the standard retention tracker template
