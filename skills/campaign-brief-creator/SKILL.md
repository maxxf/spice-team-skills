---
name: campaign-brief-creator
description: >
  Use this skill whenever the user asks to draft, create, or push a retention email campaign brief
  for HealthNut, Ahipoki, or My Big Fat Shawarma. Triggers include: "draft a campaign brief",
  "create a campaign for [client]", "push this to Notion", "add this to the campaign planner",
  "rough in a brief for [date]", "write a brief for [client] [topic]", or any combo of client +
  topic + send date. Always use this skill when a retention brief needs to land in Notion — even
  if the user just says "add it to the planner" without explicitly invoking the skill name.
---

# Campaign Brief Creator (v2)

Drafts retention email briefs and pushes them to the Notion Campaign Planning database in the
exact format the production team uses — no template reinvention, no manual cleanup downstream.

This skill mirrors the production `Email Campaign` template verbatim. Do NOT modify the table
structure, color tags, or syntax shown below. The retention team renders these briefs daily;
even small drift creates downstream rework.

---

## Hardcoded references

### Campaign Planning data source
```
1c8d3ff0-18e7-8067-abff-000b54568283
```
Use as `data_source_id` parent for every campaign page.

### Production page template (for reference, not direct use)
```
1c8d3ff018e780f1a616dd5e6cdfe214
```
This is the live `Email Campaign` template in Notion. The verbatim content below was extracted
from it on 2026-04-27. If you suspect the template has changed, fetch this page first and
update the skill before proceeding.

### Client page IDs (verified 2026-04-27)
| Client (display name in Notion) | Notion Client Page ID |
|---|---|
| Health Nut | `265d3ff018e7805ba337fc9f092c4125` |
| Ahipoki | `1c8d3ff018e7808880a4c5915dab0e4b` |
| My Big Fat Shawarma | `29bd3ff018e7800b99a3f0351d1f97e2` |

> Note: Notion stores it as "Health Nut" with a space, not "HealthNut". When users say HealthNut,
> we still match — but the Client property on the page uses the page URL above, not the name.

### Per-client voice notes
Always read the relevant voice file before drafting copy:
- `clients/healthnut.md` — leafy, casual, loyalty-driven, LA-fast-casual
- `clients/ahipoki.md` — warm, instructive, surf-meets-Hawaii
- `clients/mbfs.md` — bold, cheeky, "Big Fat" macro-flexed swagger

### Default page properties
| Property | Default | Notes |
|---|---|---|
| `Asset Type` | `Email` | select |
| `Service Team` | `Retention` | select |
| `Channels` | `Email` | multi_select — pass as comma-separated string. For SMS adds: `"Email, SMS"` |
| `Status` | `Brief` | status type, value `Brief` |
| `icon` | `icons/mail_gray` | matches production |
| `Entry Type` | `Campaign` | select — production briefs are `Campaign` not `Design Asset` |

### Valid Status options
`Drafting` · `Not started` · `Brief` · `Design V.1` · `Design V.2` · `Internal Review` ·
`Client Review V.1` · `Client Review V.2` · `Final Client Review` · `Client Approved` ·
`On Hold` · `Canceled` · `Scheduled` · `Complete`

---

## Title naming convention

Production team uses `MM/DD | [Email |] Topic` — slashes, not periods. The "Email |" middle
segment is sometimes included, sometimes not. Recent pattern by client:
- HealthNut: `MM/DD | Email | Topic` (e.g. `04/20 | Email | Double Leaves Week`)
- Ahipoki: `MM/DD | Email | Topic` (e.g. `11/20 | Email | Thanksgiving, The Ahipoki Way`)
- MBFS: `MM/DD | Topic` (e.g. `01/08 | High-Protein Bowls!`, `02/03 | Superbowl Campaign`)

Match the per-client convention. Pipes in the title are stored as `\\|` in the property value
(Notion escapes them automatically when you pass `|` directly).

---

## The brief template — VERBATIM from production

This is the EXACT template structure used in production. Do not substitute markdown tables.
The HTML tags and color attributes drive the color-coding and toggles.

The full template has three sections. **Default behavior: include all three.** Users typically
ask to drop sections — if they do, follow the rules below.

### Section 1 — Sending Details (toggle, optional)

Include unless user says "skip sending details" or "no audience test." Production briefs keep
this empty for the client/strategist to fill at send time.

```
### Sending Details {toggle="true"}
	<table header-row="true" header-column="true">
	<colgroup>
	<col color="purple_bg" width="219.984375">
	<col width="237.953125">
	<col width="224.984375">
	</colgroup>
<tr color="purple_bg">
<td></td>
<td>**A Test**</td>
<td>B Test</td>
</tr>
<tr>
<td>**Send Time**</td>
<td></td>
<td></td>
</tr>
<tr>
<td>**Timezone**</td>
<td></td>
<td></td>
</tr>
<tr>
<td><span color="gray">Determine at Send Time? Y/N</span></td>
<td></td>
<td></td>
</tr>
<tr>
<td>**Included Segments**</td>
<td></td>
<td></td>
</tr>
<tr>
<td>**Excluded Segments**</td>
<td></td>
<td></td>
</tr>
<tr>
<td><span color="gray">Smart Sending On/Off</span></td>
<td></td>
<td></td>
</tr>
	</table>
```

### Section 2 — Main email brief (required)

This is the always-present section. Fill in `{{placeholder}}` values. Add a third C Spot row
when the brief has 3 spots (HealthNut Double Leaves and MBFS High-Protein both used C Spots —
this is normal for offer + value-stack + evergreen layouts).

For SMS-enabled clients (HealthNut, MBFS), append the `**SMS**` gray_bg row at the bottom of the
table when the brief includes SMS. Skip the SMS row entirely for Ahipoki (no SMS in scope).

```
### Campaign, Promo, Educate Email
<table header-row="true">
<colgroup>
<col width="697.998291015625">
</colgroup>
<tr color="red_bg">
<td>**Creative References**</td>
</tr>
<tr>
<td>{{visual_direction}}</td>
</tr>
<tr color="gray_bg">
<td>**SUBJECT**<span color="brown_bg">** LINE**</span></td>
</tr>
<tr>
<td>{{subject_line}}</td>
</tr>
<tr color="gray_bg">
<td>**PREHEADER**</td>
</tr>
<tr>
<td>{{preheader}}</td>
</tr>
<tr color="purple_bg">
<td>**A Spot**</td>
</tr>
<tr>
<td>**H1**: {{a_h1}}<br>**Image:** {{a_image}}<br>**Copy:** {{a_copy}}<br>**CTA:** {{a_cta}}<br>**CTA Link:** </td>
</tr>
<tr color="purple_bg">
<td>**B Spot**</td>
</tr>
<tr>
<td>**H1**: {{b_h1}}<br>**Image:** {{b_image}}<br>**Copy:** {{b_copy}}<br>**CTA:** {{b_cta}}<br>**CTA Link:** </td>
</tr>
</table>
```

**Optional 3rd spot — insert before `</table>` when needed:**
```
<tr color="purple_bg">
<td>**C Spot**</td>
</tr>
<tr>
<td>**H1**: {{c_h1}}<br>**Image:** {{c_image}}<br>**Copy:** {{c_copy}}<br>**CTA:** {{c_cta}}<br>**CTA Link:** </td>
</tr>
```

**Optional SMS row — insert before `</table>` when client has SMS in scope:**
```
<tr color="gray_bg">
<td>**SMS**</td>
</tr>
<tr>
<td>{{sms_copy}} → \[link\]</td>
</tr>
```

**Optional PUSH callout — render AFTER the table closes, as a colored callout (Ahipoki and HealthNut use Thanx push):**
```
**PUSH:** {{push_copy}} {color="gray_bg"}
```

### Section 3 — Creative A/B (toggle, default: drop unless A/B test requested)

Default: do NOT include this section. Production briefs only keep it when running a Creative A/B
test (subject line variant, copy variant, etc.). If user says "set up an A/B test" or "creative
A/B," include this section verbatim:

```
### Creative A/B {toggle="true"}
	<table header-column="true">
	<colgroup>
	<col color="purple_bg" width="348.9991455078125">
	<col width="348.9991455078125">
	</colgroup>
<tr>
<td>**Learning Question ***What are we trying to learn and how will we accomplish it?*</td>
<td>{{learning_question}}</td>
</tr>
<tr>
<td>**Test Type**<br>*Example: CTA Color, Copy, Offer, etc. *</td>
<td>{{test_type}}</td>
</tr>
	</table>
	<table header-row="true">
	<colgroup>
	<col width="347.9687805175781">
	<col width="346.97222900390625">
	</colgroup>
<tr color="red_bg">
<td>**Creative References**</td>
<td></td>
</tr>
<tr>
<td>{{ab_visual_direction}}</td>
<td></td>
</tr>
<tr color="purple_bg">
<td>**SUBJECT**<span color="brown_bg">** LINE A**</span></td>
<td>**SUBJECT**<span color="brown_bg">** LINE B**</span></td>
</tr>
<tr>
<td>{{subject_a}}</td>
<td>{{subject_b}}</td>
</tr>
<tr color="purple_bg">
<td>**PREHEADER**<br>*Reminder: If running a subject line test, do NOT modify the pre-header as it skews results*</td>
<td></td>
</tr>
<tr>
<td>{{preheader_ab}}</td>
<td></td>
</tr>
<tr color="yellow_bg">
<td>**(A)A Spot**</td>
<td>**(B)A Spot**</td>
</tr>
<tr>
<td>**H1**: {{aa_h1}}<br>**Image:** {{aa_image}}<br>**Copy:** {{aa_copy}}<br>**CTA:** {{aa_cta}}<br>**CTA Link:**</td>
<td>**H1**: {{ba_h1}}<br>**Image:** {{ba_image}}<br>**Copy:** {{ba_copy}}<br>**CTA:** {{ba_cta}}<br>**CTA Link:**</td>
</tr>
<tr color="yellow_bg">
<td>**(A)B Spot**</td>
<td>**(B)B Spot**</td>
</tr>
<tr>
<td>**H1**: {{ab_h1}}<br>**Image:** {{ab_image}}<br>**Copy:** {{ab_copy}}<br>**CTA:** {{ab_cta}}<br>**CTA Link:**</td>
<td>**H1**: {{bb_h1}}<br>**Image:** {{bb_image}}<br>**Copy:** {{bb_copy}}<br>**CTA:** {{bb_cta}}<br>**CTA Link:**</td>
</tr>
	</table>
```

---

## Page opening — required for every brief

Every page must open with this exact block:

```
# Campaign Strategy
**General Idea or Concept for Campaign**
- {{one_sentence_concept_summary}}
<empty-block/>
```

If including A/B Test row in Sending Details, also add this red note BEFORE Section 1:
```
*Note: Delete A/B Test row and extra column if not doing an Audience A/B Test for this send. Then delete this note. * {color="red"}
```

---

## Step-by-step workflow

### Step 1 — Confirm inputs
Before drafting, verify you have:
- Client (HealthNut / Ahipoki / MBFS)
- Send date (MM/DD)
- Campaign concept / offer / topic
- Target audience (default: All subscribers)
- Channels (default: Email only; for HealthNut/MBFS ask if SMS too)
- Number of spots (default: 2 spots A + B; ask if 3 needed)
- A/B test? (default: no Creative A/B section; ask only if user implies testing)

If missing, ask before proceeding. Be terse.

### Step 2 — Read voice notes
Read `clients/{client}.md` to load voice/style/menu signals before drafting copy. Do not skip.

### Step 3 — Draft
Fill in placeholders following the brand voice. Apply retention copywriting fundamentals:
- **Subject lines:** create curiosity, ownership, or urgency. Avoid description-only.
- **Preheader:** complement the subject, never restate it. Add value/clarity.
- **A Spot:** main hook + offer, short and punchy. The single thing they should remember.
- **B Spot:** stack supporting value (perks, options, secondary use case). Reinforces, doesn't compete.
- **C Spot (when used):** evergreen anchor — sign-up CTA, app download, rewards loop entry.
- **SMS:** 1-2 sentences max, casual, ends with `→ \[link\]` (literal text — user swaps later).
- **CTA Link:** ALWAYS leave blank. User fills it in.

### Step 4 — Assemble the page content
Concatenate in this order:
1. Page opening block (`# Campaign Strategy`...)
2. Optional A/B note (red) — only if Section 1 includes A/B Test row
3. Section 1 — Sending Details (default: include, empty)
4. Section 2 — Main Email Brief (always include, filled)
5. Optional PUSH callout (after Section 2 close)
6. Section 3 — Creative A/B (default: skip)

### Step 5 — Push to Notion
Single tool call: `notion-create-pages` with:
```json
{
  "parent": {"type": "data_source_id", "data_source_id": "1c8d3ff0-18e7-8067-abff-000b54568283"},
  "pages": [{
    "icon": "icons/mail_gray",
    "properties": {
      "Campaign name": "{{title following per-client convention}}",
      "Asset Type": "Email",
      "Service Team": "Retention",
      "Channels": "Email",
      "Entry Type": "Campaign",
      "Status": "Brief",
      "Client": "{{client_page_url}}",
      "date:Start Date:start": "YYYY-MM-DD",
      "date:Start Date:is_datetime": 0
    },
    "content": "{{full assembled brief content}}"
  }]
}
```

For SMS-included briefs, set `"Channels": "Email, SMS"` (multi_select accepts comma-separated string).

### Step 6 — Confirm + share + educate
Reply with:
- The Notion URL
- The full brief pasted in chat (so user has it without opening Notion)
- A short "Why this works" section: subject line angle, A/B/C split rationale, brand-voice notes
- Suggest the next step: `email-template-designer` skill to create the visual draft from this brief

---

## Guardrails

- **NEVER reinvent the template.** Use the exact HTML/markdown above. Multi-column markdown breaks the format.
- **NEVER guess CTA links** — always blank. The user fills in.
- **Always check the client name spelling** — Notion has "Health Nut" (space), not "HealthNut".
- **Channels is multi_select** — pass as comma-separated string: `"Email"` or `"Email, SMS"`. Not an array, not a single-item array. The Notion MCP tool handles the conversion.
- **Status default is `Brief`**, not `Drafting`, not `Not started`. Briefs that are ready for design pickup move from `Brief` → `Design V.1`.
- **If the client isn't in the table**, fetch their page from Notion before guessing the ID. Use search.
- **Title convention is per-client.** Don't force `MM.DD` (period) — production uses `MM/DD` (slash) and the "Email |" middle segment varies by client.
- **Default to no Creative A/B section.** Only include if user explicitly asks for an A/B test.
- **SMS is HealthNut + MBFS only.** Do not propose SMS for Ahipoki — they don't have it in scope.
- **C Spot is optional, common.** Don't force it; don't avoid it. Match what the brief actually needs.
- **If the brief is for a flow (welcome / win-back / abandoned cart) rather than a single send,** flag this — flows need different page structure (multi-email) and may warrant a different page type.

---

## Common deviations from the template (tracked, accepted)

These are real patterns from recent production briefs. Match them when relevant.

- **Drop Sending Details + Creative A/B for already-scoped sends** (HealthNut Double Leaves did this — the brief was small and direct).
- **Add C Spot for offer + value + evergreen layouts** (HealthNut Double Leaves, MBFS High-Protein).
- **Add PUSH callout** after Main Email when push notification copy is in scope (Ahipoki First Timer Bowl).
- **Add SMS row inside Main Email table** for HealthNut and MBFS sends.
- **Inline image references** with Drive/Instagram URLs are common — quote them in the Image: field directly.

---

## Why this skill exists

The retention team renders 8-12 briefs per month across HealthNut, Ahipoki, and MBFS. Drafting
in the right format — with the right voice — is the difference between a brief that ships clean
to design and one that bounces back with formatting fixes. This skill removes both failure modes
in a single tool call, then teaches the user the "why" so the strategy compounds across briefs.
