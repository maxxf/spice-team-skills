# Notion Sales Pipeline — Schema Additions

> Database ID: `1c8d3ff0-18e7-80e9-8381-000b4448cb87`
> One-time setup: add the fields below to your existing Sales Pipeline DB.

The skill writes to the Sales Pipeline DB. Some fields likely already exist (Name, Status, Owner). Others need to be added so the skill can store audits, mockups, and reply tracking.

---

## Status options

Make sure the `Status` select field includes these options. Add any that are missing.

| Status | When |
|--------|------|
| `Targeted` | Maxx flagged manually as a top prospect |
| `Discovered` | Auto-added by `discover-restaurants.mjs` |
| `Cold` | Generic unworked prospect |
| `Cold Outreach Sent` | Email sent, awaiting reply |
| `Replied` | Founder responded |
| `In Discussion` | Active sales conversation |
| `Won` | Closed deal |
| `Lost` | Passed or rejected |
| `Skipped — Maxx Veto` | Maxx ❌'d the draft |
| `Active` | Existing Spice client (don't pitch) |

---

## Required field additions

Add these properties to the Sales Pipeline DB. Type and purpose noted for each.

| Field | Type | Purpose |
|-------|------|---------|
| `Cities` | Multi-select | LA / NYC / Austin / Other — which target cities they operate in |
| `Locations` | Number | Total location count (used for 5-100 filter) |
| `Priority` | Select | High / Medium / Low — Maxx flags top targets |
| `Last Audited` | Date | When most recent audit ran (skill checks > 90 days for re-audit) |
| `Audit Score` | Number | 0-100 from storefront-audit skill |
| `Audit Link` | URL | Drive link to audit HTML report (with before/after) |
| `Mockup Link` | URL | Drive link to AI hero mockup |
| `Email Sent To` | Email | Founder/CEO email used for outreach |
| `Email Confidence` | Select | scraped / linkedin / hunter / guessed |
| `Outreach Date` | Date | When cold email was sent |
| `Superhuman Thread ID` | Text | For correlating replies back to this prospect |
| `Follow-Up Due` | Date | Outreach Date + 5 business days; sales-follow-up skill uses this |
| `Source` | Select | Maxx / Spice Prospect Pipeline / Referral / LinkedIn / Other |
| `Owner` | Person | Defaults to Maxx for outbound |
| `Last Touch` | Date | Most recent activity (any direction) |

---

## Optional but useful

| Field | Type | Purpose |
|-------|------|---------|
| `Founder Name` | Text | Captured during enrichment |
| `Founder Title` | Text | CEO / Founder / President / Owner |
| `Founder LinkedIn` | URL | For mutual-connection lookup |
| `Brand Website` | URL | Their main marketing site |
| `Strongest Platform` | Select | UE / DD / GH / Multiple — what they audit on |
| `Audit Findings` | Text (long) | The 1-2 audit findings cited in outreach |
| `Reply Snippet` | Text | First few lines of any reply, for quick context |
| `Notes` | Text | Manual scratchpad |

---

## How to add fields fast

1. Open the Sales Pipeline DB in Notion
2. Click `+` next to the rightmost column header
3. Pick the type from the table above
4. Name it exactly as shown (the skill matches by name)
5. For `Status` and `Priority` selects, add the listed options

Takes ~3 minutes total.

---

## Verification query

After adding the fields, the skill should be able to filter:

```
WHERE Status IN ["Targeted", "Cold", "Discovered"]
  AND Cities CONTAINS one of [LA, NYC, Austin]
  AND Locations BETWEEN 5 AND 100
  AND (Last Audited IS EMPTY OR Last Audited < TODAY - 90 days)
```

If the skill errors with "property not found", a field is missing or named differently. Check the field names against this doc.
