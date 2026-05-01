---
name: client-onboarding
description: End-to-end new client onboarding for Spice. Handles post-signature setup including kickoff email draft, Notion client space creation, onboarding task generation, Stripe payment link setup, and Slack channel coordination. Designed for the Client Services Lead to run autonomously after Maxx closes the deal. Supports Delivery Marketplaces, Retention, Paid Acquisition, and Advisory services.
---

> **Spicy Nugget handoff:** After the kickoff call, delegate ongoing onboarding task tracking to Spicy. Post to #spice-ai-ops: "@Spicy Nugget check onboarding status for [client]"

# Client Onboarding Skill

End-to-end post-signature onboarding automation. Takes a new client from Closed Won to fully set up in Notion with tasks, email drafted, and manual steps checklist.

**Primary user:** Client Services Lead
**Handoff point:** Maxx closes deal, sends kickoff email with the Client Services Lead CC'd. From that point, the Client Services Lead owns everything except the kickoff call (where Maxx makes the formal introduction).

## Trigger Phrases

- "Onboard [client name]"
- "Set up new client"
- "Create client workspace for [name]"
- "Add [client] to Notion"
- "New client [name]"
- "Start onboarding for [name]"

## Required Information

Collect before starting. If the client already exists in Notion (Closed Won status), pull as much as possible from the existing record.

| Field | Required | Notes |
|-------|----------|-------|
| Client Name | Yes | Official business name |
| Services | Yes | Select from list below |
| SOW Start Date | Yes | YYYY-MM-DD format |
| Location Count | Yes (DM) | Number of locations for DM pricing. Not needed for Advisory-only. |
| Main POC | Yes | Client's primary contact name + email |
| Key Context | Optional | Notes from sales calls, special requirements, billing terms |

**If client record exists in Notion:** Search first (Step 1), pull existing data, and confirm with user before proceeding. Don't duplicate records.

## Service Selection

Ask user to confirm which services this client is onboarding for:

| Service | Code | Task Count (incl. shared) |
|---------|------|---------------------------|
| Delivery Marketplaces | `DM` | 14 tasks |
| Retention (Email/SMS/Loyalty) | `RET` | 12 tasks |
| Paid Acquisition (Meta/Google/TikTok) | `PAID` | 11 tasks |
| Advisory | `ADV` | 7 tasks |

Only generate tasks for selected services. See `references/onboarding-tasks.md` for full task details.

## Workflow

### Step 1: Check for Existing Client

Search Clients database before creating:
```
Tool: notion-search
Query: [client name]
data_source_url: collection://1c8d3ff0-18e7-80e9-8381-000b4448cb87
```

- If found with Status "Onboarding" or "Active" → confirm with user, likely updating existing client
- If found with Status "Closed Won" → proceed with onboarding setup using existing record
- If not found → will create new record in Step 3

### Step 2: Pricing Calculation & Stripe Handoff

**Who runs Stripe:** Only Maxx has Stripe access. This step calculates pricing and outputs a Stripe action checklist for Maxx. If Maxx is running the skill, Stripe tools are used directly. If the Client Services Lead is running it, Stripe steps are output as manual tasks for Maxx.

**Step 2a: Calculate pricing**

| Service | Stripe Product | Price ID | Amount |
|---------|----------------|----------|--------|
| DM Base Fee | Per-client product | Created per client | $1,000/mo |
| DM First 5 Locations | DM First 5 Locations | `price_1Sn0k7FSznekd2wYk5POzUaX` | $350/loc/mo |
| DM Locations 6+ | DM Locations 6+ | `price_1Sn0kgFSznekd2wYjOTMUtih` | $175/loc/mo |
| Loop Analytics (DM included) | *Manual line item* | — | $60/loc/mo |
| Retention | Retention Lite | `price_1SfDC3FSznekd2wY5FY2QUUf` | $1,400/mo |
| Advisory | Fractional Head of Growth | `price_1SpYumFSznekd2wYC6stONcN` | $4,000/mo |
| Advisory Lite | Advisory Lite | `price_1TCCHbFSznekd2wY1mrKsAmC` | $2,500/mo |
| Paid Acquisition | *Custom quote* | — | Varies |

**Delivery Marketplaces Pricing Formula:**
```
DM Monthly = $1,000 base
           + ($350 x first 5 locations)
           + ($175 x locations 6+)
           + ($60 x all locations)  <- Loop Analytics
```

**CONFIRM pricing with user before proceeding.** Clients may have negotiated custom pricing.

**Step 2b: Stripe action checklist (for Maxx)**

Always output this in the summary, regardless of who runs the skill:

```
STRIPE SETUP (Maxx only):
1. Create Stripe customer: [Client Name], [Client Email]
2. Create payment link for [first service] at $[amount]/mo (recurring)
3. Configure payment link to collect: name, email, phone, business name + address, billing contact
4. For multi-service clients: add additional services to subscription when they start
5. Share payment link with the Client Services Lead to include in kickoff email
6. Update Notion client record with Stripe Customer ID and payment link URL
```

If Maxx is running the skill with Stripe access:
- Search Stripe for existing customer first
- Create customer if not found
- Create product + recurring price if custom pricing
- Create payment link
- Update Notion record with Stripe Customer ID and billing notes

**Step 2c: Payment status check**

Anyone can ask: "did [client] pay?" or "check payment for [client]"

If Stripe tools are available, this triggers a lookup. If not, output: "Check with Maxx or review in Stripe dashboard."

### Step 3: Client Space Setup

**If client page already exists (e.g., created from CRM):** Skip duplication, use existing page. Verify properties are populated.

**If no client page exists:** Duplicate the client portal template:

```json
{
  "page_id": "1c8d3ff0-18e7-80d2-8ff3-dc0d0ad881c5"
}
```

**Template ID:** `1c8d3ff0-18e7-80d2-8ff3-dc0d0ad881c5` (Client Portal [Template])

This creates a full workspace with:
- Onboarding Checklist (linked view)
- Client Wiki (inline DB)
- Documents / Document Hub (inline DB)
- Meeting Notes (inline DB)
- Team Tasks (linked view)
- Campaign Planner (linked view)
- Menu Requests (linked view)
- Creative Assets (inline DB)

**Important:** Duplication is async. Wait 5 seconds before updating properties.

### Step 4: Update Client Properties

After page exists (created or found), update properties:

```json
{
  "page_id": "[client-page-id]",
  "command": "update_properties",
  "properties": {
    "Client Name": "[name]",
    "Service(s)": "[service1], [service2]",
    "Status": "Onboarding",
    "Service Lead": "[relevant user IDs]",
    "Supporting Team": "[relevant user IDs]",
    "date:SOW Start Date:start": "YYYY-MM-DD",
    "date:SOW Start Date:is_datetime": 0,
    "Service Details - ": "[formatted details]",
    "Client Email": "[POC email]",
    "Billing Contact Email": "[billing email]",
    "Billing Notes": "[pricing breakdown, payment terms]"
  }
}
```

**Service Details Format:**
```
**[SERVICE NAME]**
- Platforms: [list]
- Locations: [count] across [regions]
- Priority: [goals/focus areas]

[Additional context from sales calls]
```

### Step 5: Generate Onboarding Tasks

Create tasks in the Client Onboarding database using `notion-create-pages`.

**Data source:** `239d3ff0-18e7-8041-84d2-000b393bcc69`

**Step 5a: Create shared tasks (once only)**

| Task | Phase | Days | Owner ID |
|------|-------|------|----------|
| Create internal Slack channel (#int-[client]) | Kickoff | 0 | Client Services Lead (assign at runtime) |
| Create external Slack channel (#ext-[client]-spice) or WhatsApp group | Kickoff | 0 | Client Services Lead (assign at runtime) |
| Confirm Payment On File in Stripe | Kickoff | 1 | Client Services Lead (assign at runtime) |

**Step 5b: Create service-specific tasks**

See `references/onboarding-tasks.md` for the full task list per service.

**Owner logic:**
- Advisory tasks → Maxx (`c249c8bc-e33f-4b35-b4f8-c9b22117cccc`)
- All other tasks → Client Services Lead (assign at runtime). Lead reassigns to team members.

**Task creation format:**
```json
{
  "Task": "[task name]",
  "Service": "[Delivery Marketplaces|Retention|Paid Acquisition|Advisory]",
  "Phase": "[Kickoff|Access & Setup|Audit|Build & Launch|Optimize]",
  "Status": "Not Started",
  "Owner": "[\"[user-id]\"]",
  "Client": "[\"https://www.notion.so/[client-page-id]\"]",
  "Notes / Links": "[context from task reference]"
}
```

**Link tasks to the client page URL**, not the template.

### Step 5c: Storefront Audit Integration (DM Only)

When DM service is selected, the "Run Diagnostics on 3P" task should reference the `storefront-audit` skill. Add a note to that task:

> Once platform access is confirmed (~Day 7), run: "audit [client name] storefronts" using the storefront-audit skill. Save output to client's Document Hub. Findings inform Menu Sheet and Campaign Plan tasks.

### Step 6: Draft Kickoff Email

See `references/kickoff-email-template.md` for the full template.

**For multi-service or DM clients:** Draft email introducing the Client Services Lead. Include onboarding form link, payment link (if available), and client portal link.

**For Advisory-only clients:** Draft email from Maxx directly (no Client Services handoff).

**Present the draft to the user for review before sending.** The user (Maxx or the Client Services Lead) sends the email manually.

### Step 7: Output Summary & Manual Steps

After all automation completes, output:

```markdown
## Onboarding Setup Complete

**Client:** [name]
**Client Page:** [Notion URL]
**Services:** [list]
**Tasks Created:** [count] across [services]
**SOW Start Date:** [date]

## Kickoff Email

[Draft email content here, ready to copy/paste or send via Gmail]

**To:** [client POC email]
**CC:** [client services lead email]
**Subject:** Welcome to Spice! - [restaurant name] Onboarding

## Stripe Setup (Maxx Action Required)

Pricing: [breakdown with per-service totals]
Terms: [upfront / net-15]

- [ ] Create Stripe customer for [Client Name] ([Client Email])
- [ ] Create payment link for [first service] at $[amount]/mo (recurring)
- [ ] Configure link to collect: name, email, phone, business name + address, billing contact
- [ ] Share payment link with the Client Services Lead for kickoff email
- [ ] Update Notion record with Stripe Customer ID + payment link URL
- [ ] For multi-service: add [next service] ($[amount]/mo) to subscription when it starts on [date]

## Manual Steps for the Client Services Lead

### Database Filters (Required)
The following linked views in the client page need filters applied:

- [ ] Onboarding Checklist: Add filter → Client → is → [Client Name]
- [ ] Team Tasks: Add filter → Client → is → [Client Name]
- [ ] Campaign Planner: Add filter → Client → is → [Client Name]
- [ ] Menu Requests: Add filter → Client → is → [Client Name]

### Slack / WhatsApp (tracked as onboarding tasks)
- [ ] Add channel URLs to client record Slack Channel(s) field after creation

### Kickoff Deck
- [ ] Open Figma Slides: https://www.figma.com/slides/eu0b0OLglaRTd2n3bPw7tc/Kick-Off
- [ ] Duplicate template slides for new client
- [ ] Update client name and logo
- [ ] Schedule kickoff call (Maxx attends for handoff, Client Services Lead runs from there)

### Post-Kickoff
- [ ] After kickoff call, Maxx exits day-to-day. The Client Services Lead owns the relationship.
- [ ] Once platform access confirmed (~Day 7), run storefront audit (DM clients only)
- [ ] Verify onboarding task due dates are calculating correctly
```

## Team User IDs

| Name | Role | Email | Notion ID |
|------|------|-------|-----------|
| Maxx Freedman | CEO / Sales | maxx@spicedigital.co | c249c8bc-e33f-4b35-b4f8-c9b22117cccc |
| Rodrigo Gutierrez | Growth & Marketplace Ops | rodrigo@spicedigital.co | babf0663-1fa3-49dd-8605-5b777bab2c13 |
| David Pliego | Operations / Systems | david@spicedigital.co | 1c0d872b-594c-8190-90bc-00025e02e3b6 |
| Rui Moreira | Marketplace Operations | rui@spicedigital.co | 1b7d872b-594c-813a-9ec9-00026a26bf6a |
| Manish Kumar | Data / Analytics | manish@spicedigital.co | 2afd872b-594c-8133-b913-00024826113c |
| Tomas Wayne | Operations (transitioning) | tomas@spicedigital.co | 2bad872b-594c-81ce-9d48-00022fecb006 |
| Ana | Growth Manager (starting Mar 18, 2026) | — | — |
| Dulari Fernando | — | dulari@spicedigital.co | 1cad872b-594c-81a0-a0db-000282941e87 |
| Diri Thadhani | — | diri@spicedigital.co | 270d872b-594c-81f7-b95e-0002309a801d |

## Notion Database References

| Database | Data Source ID | Use |
|----------|----------------|-----|
| Clients | `1c8d3ff0-18e7-80e9-8381-000b4448cb87` | Client records |
| Client Onboarding | `239d3ff0-18e7-8041-84d2-000b393bcc69` | Onboarding tasks |
| Team Task Tracker | `1c8d3ff0-18e7-80f0-a36b-000b6befe5b1` | Ongoing tasks |
| Campaign Planning | `1c8d3ff0-18e7-8067-abff-000b54568283` | Campaign calendar |
| Storefront Change Requests | `1c8d3ff0-18e7-80a4-8411-000b1588c553` | Menu updates |

## Key Page References

| Page | ID | Use |
|------|-----|-----|
| Client Portal [Template] | `1c8d3ff0-18e7-80d2-8ff3-dc0d0ad881c5` | Duplicate for new clients |
| Onboarding Form | `1c8d3ff018e780f5821ff8b52e709724` | Client-facing credential collection form |
| Onboarding SOP | `1e0d3ff018e7801aaa3ae93307b5d22c` | Master SOP page in Spice Wiki |
| Kickoff Deck (Figma) | `eu0b0OLglaRTd2n3bPw7tc` | Figma Slides template for kickoff presentations |

## References

- Task templates by service: `references/onboarding-tasks.md`
- Kickoff email templates: `references/kickoff-email-template.md`
- Storefront audit skill: `/mnt/.skills/skills/storefront-audit/SKILL.md`
- Optimized menu sheet skill: `/mnt/.skills/skills/optimized-menu-sheet/SKILL.md`

## Related Skills

- **storefront-audit**: Run after platform access confirmed to generate diagnostics report (DM clients)
- **optimized-menu-sheet**: Build menu optimization blueprint from storefront audit findings (DM clients)
- **onboarding-status-check**: Monitor task completion and flag overdue items across all clients
- **client-call-prep**: Prep for kickoff call with full client context
