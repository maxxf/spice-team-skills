---
name: spice-prospect-pipeline
description: Daily Spice prospect pipeline. Sources mid-market multi-location restaurants (5-100 locations) in LA / NYC / Austin, runs a storefront audit + generates an AI before/after hero image, drafts a personalized cold email from maxx@spicedigital.co leading with proof (Spice clients) backed by audit findings, posts to #spice-ai-ops for approval, sends via Superhuman MCP on green light, and tracks in the Notion Sales Pipeline. Triggers on "run prospect pipeline", "find prospects", "daily prospects", "audit prospects", or as a scheduled task.
metadata:
  version: "2.0"
  cadence: "5 audits/day"
  cities: ["LA", "NYC", "Austin"]
  filter: "5-100 location restaurants on UE/DD/GH"
  sender: "maxx@spicedigital.co"
  send_via: "Superhuman MCP"
  approval_channel: "#spice-ai-ops"
---

# Spice Prospect Pipeline

You source qualified mid-market restaurant prospects, audit their delivery presence, generate a before/after hero visual to make the audit visceral, draft outreach in Maxx's voice that leads with social proof and evidence, and route to Maxx for approval before sending. The audit + hero mockup is the wedge — it proves Spice's expertise before any pitch.

---

## Confidentiality Boundaries (READ FIRST — DO NOT VIOLATE)

Spice has a confidentiality obligation to every client. Violations break trust and could end relationships.

### You CAN cite in cold outreach:
- **Client names** as social proof: Pret, Capriotti's, goop Kitchen, Fresh Kitchen, Everytable, Counter Service, Brasa Peruvian, Tiff's Treats, Westville
- **Industry benchmarks** from public/platform data: "platform average is 22 menu items"
- **Generalized outcomes** without attribution: "we typically see 15-25% net payout lift when..."
- **The prospect's own public data**: their visible rating, review count, hero image, menu length, promo cadence
- **Spice's service pillars** and methodology framing

### You CANNOT cite:
- ❌ Any client's revenue, sales, AOV, ROAS, or growth rate (e.g., "$230K week", "23% lift")
- ❌ Any client's specific ad spend percentage or marketing spend
- ❌ Any client's specific promo discount levels or campaign details
- ❌ Any client's internal margins, payout %, or financial data
- ❌ Any client-specific tactic that's their competitive advantage
- ❌ Any private data we wouldn't share with that client publicly

### When in doubt
Use the test: **would this make the named client uncomfortable if they read it in a cold email to a competitor?** If yes, don't cite it. Pull the social proof + industry benchmark instead.

---

## The Daily Loop

| Step | What you do |
|------|-------------|
| 1. Source | Pull 5 unworked prospects from Notion Sales Pipeline (or fallback discovery) |
| 2. Verify | Confirm each has UE/DD/GH presence and 5-100 locations |
| 3. Audit | Run storefront-audit skill on the strongest platform per prospect |
| 4. Hero mockup | Generate AI before/after hero image via Replicate (the visual wedge) |
| 5. Find owner | Locate founder/CEO email (website + LinkedIn + Hunter fallback) |
| 6. Draft | Write personalized cold email leading with social proof, backed by audit + benchmark |
| 7. Approval | Post draft + audit + before/after to #spice-ai-ops, @ Maxx |
| 8. Send | On Maxx's ✅, send via Superhuman MCP from maxx@spicedigital.co |
| 9. Track | Update Notion Sales Pipeline status, queue 5-day follow-up |

**Daily cap: 5 audits.** No exceptions. Quality over volume.

---

## Step 1: Source Prospects

### Primary source — Notion Sales Pipeline

The Notion Sales Pipeline DB lives at: `1c8d3ff0-18e7-80e9-8381-000b4448cb87`

Filter:
- `Status` is in `["Targeted", "Cold", "Discovered"]` (unworked)
- `Cities` contains one of: `Los Angeles`, `New York`, `Austin`
- `Locations` between 5 and 100
- `Last Audited` is empty OR > 90 days old
- Not in any active deal stage (`Active`, `Won`, `Lost`, `In Discussion`)

Pull top 5 by `Priority` (manual flag from Maxx) → then by review count + rating. If fewer than 5 unworked match, fill remaining via fallback discovery.

### Fallback source — Google Places discovery

If Notion has fewer than 5 unworked prospects:

```bash
QUERY="restaurants" LOCATION="Los Angeles CA" GOOGLE_PLACES_API_KEY=$GOOGLE_PLACES_API_KEY \
  node tools/discover-restaurants.mjs
```

Discovery script logic:
1. Search Google Places for restaurants in target city
2. For each unique brand name, count results across all 3 cities (chain-size proxy)
3. Filter to 5-100 result count
4. Filter out: corporate giants (McDonald's, Chipotle, Starbucks, etc.), single-unit independents, existing Spice clients
5. Add promising brands to Notion Sales Pipeline as `Status = "Discovered"`
6. Return top 5 by review count + rating

Rotate cities daily — don't pull all 5 from LA every day. Aim for ~2 LA, ~2 NYC, ~1 Austin or rotate.

### Skip these
- Existing Spice clients (`Status = "Active"` in Sales Pipeline)
- Brands with `Status = "Won"` or `Status = "Lost"`
- Brands previously contacted in last 90 days (`Last Outreach` field)
- Single-location independents (< 5 locations)
- National chains (> 100 locations) unless Maxx flags as exception
- Fast food, gas station food, anything below "fast casual"

---

## Step 2: Verify Delivery Presence

For each prospect, verify they exist on at least one major platform:

| Platform | Check |
|----------|-------|
| Uber Eats | Search `uber.com/eats` for brand name in target city |
| DoorDash | Search `doordash.com` for brand name in target city |
| Grubhub | Search `grubhub.com` for brand name in target city |

If on 2+ platforms → great prospect. 1 platform → still good, lower priority. 0 platforms → skip (not in our market).

Pick the **strongest platform** for the audit (highest review count = primary platform = where they care most).

---

## Step 3: Run Storefront Audit

Invoke the existing `storefront-audit` skill:

> Audit [Brand Name] on [Platform] in [City].

Returns scores across 6 dimensions: hero image, menu structure, pricing, promos, operational health, competition.

Output:
1. HTML report saved locally: `~/Desktop/spice-prospect-pipeline/audits/{brand-slug}-{date}.html`
2. Uploaded to Spice's shared Drive folder, public read-only link generated for cold email
3. Score summary saved to Notion Sales Pipeline row (`Audit Score`, `Audit Link`)

**Pick the 1-2 most striking findings** for the email. Examples that hook (rephrased to use prospect's own data + industry benchmarks, never client revenue):
- "Hero image scores 4/10 vs. category leaders at 9+/10"
- "Menu has 67 items vs. platform avg of 22 for fast casual — known conversion drag"
- "Promos section empty — competitors in your category run weekly BOGOs"
- "Operational rating 4.1 — losing visibility to 4.5+ competitors"

---

## Step 4: Generate Before/After Hero Mockup (THE VISUAL WEDGE)

This is the upgrade that makes the audit feel generous instead of critical. The founder doesn't just see what's wrong — they see what their food could look like.

For each prospect, generate one improved hero image via Replicate (Seedream 4.5):

```bash
REPLICATE_API_TOKEN=$REPLICATE_API_TOKEN node tools/gen-hero-mockup.mjs <brand-slug> <cuisine-type>
```

Mockup prompt template:
```
Stunning hero image for a {{cuisine_type}} restaurant on a delivery marketplace. 
Wide cinematic composition (16:9), commercial food photography, dramatic warm lighting,
modern clean aesthetic, hero dish or signature item showcased, no text or logos.
Magazine-quality, $3,000 production value. Critical: zero text, words, letters, watermarks.
```

Save:
- `~/Desktop/spice-prospect-pipeline/hero-mockups/{brand-slug}-mockup.jpg`
- Upload to Drive, public read-only link

The audit HTML report should include a side-by-side: **current hero (downloaded from their UE/DD page)** vs **AI mockup (what we'd ship)**. Label them clearly: "Current: 4/10 score" | "Improved direction: AI rendering for reference".

Cost: ~$0.024/lead (8 images would be $0.024, but we only need 1 hero, so ~$0.003).

**This is the most important enticement upgrade** — visual >> analytical for cold outreach.

---

## Step 5: Find Owner Contact

In order:

### A. Brand website scrape
Scrape homepage + `/contact` + `/about` + `/team` + `/press`. Filter out `noreply@`, `info@`, `support@`. Keep direct names + emails. Capture founder/CEO name from About page.

### B. LinkedIn lookup
Search LinkedIn: `[Brand Name] CEO` or `[Brand Name] founder`. Capture name, title, profile URL, mutual connections (if any).

### C. Hunter.io fallback
If still no email, use Hunter.io domain search. Filter to `confidence > 70` and titles containing CEO/Founder/President/Owner.

### D. Pattern guess (last resort)
Try `firstname@brand.com`, `firstname.lastname@brand.com`, `flastname@brand.com`. Mark `email_confidence: "guessed"` in Notion.

**If no email found after all 4 methods → skip this prospect, return slot to source pool.** Don't waste an audit on an unreachable lead.

---

## Step 6: Draft the Cold Email (LEAD WITH PROOF, NOT PROBLEM)

Voice rules — apply Maxx's voice. Pull from `~/Desktop/Cowork/maxx-freedman-voice-guide.md` and run through `humanizer` skill before posting:
- Concise. Subject line under 50 chars.
- Lead with social proof + relevance. Don't open with their problem.
- One specific number/benchmark in the first 3 lines.
- No corporate boilerplate. No "delve", "landscape", "it's worth noting", emdashes, or AI slurry.
- Max one exclamation mark. Vary sentence tempo: one word. Then five. Then two.
- Sign as "Maxx" (not "Maxx Freedman, Founder" — too corporate for cold).

### Default template — "Storefront Audit + Mockup Cold"

**Subject:** `what we did for goop kitchen would work for {{brand_name}}`

(Subject line uses social proof, not the audit. Hooks curiosity. Industry-aware founders recognize the names.)

**Body:**
```
{{first_name}},

Spice runs delivery marketplace ops for {{relevant_clients}}. Mid-market chains, 
multi-location, mostly in LA/NYC. We typically lift net payout 15-25% in 90 days.

I audited {{brand_name}}'s {{platform}} this morning and built a quick mockup of 
where it could go: {{audit_link}}

Two specific things stood out:
1. {{finding_1_with_industry_benchmark}}
2. {{finding_2_with_industry_benchmark}}

Both are 30-day fixes.

Worth a 20-min call?

Maxx
```

`{{relevant_clients}}` rotates based on prospect's category:
- Fast casual → "Pret, goop Kitchen, Capriotti's"
- Premium / chef-driven → "goop Kitchen, Westville, Brasa Peruvian"
- Bakery / sweets / coffee → "Tiff's Treats, Pret, Counter Service"
- Multi-cuisine / Asian → "Brasa Peruvian, Counter Service, Westville"

Findings should follow the format: `<observation about prospect> vs <public industry benchmark>`. NEVER cite Spice client metrics.

Run the final draft through the `humanizer` skill to strip AI patterns before posting to Slack.

---

## Step 7: Post to Slack for Approval

Channel: **`#spice-ai-ops`** (use `slack_send_message` MCP). Post format:

```
@Maxx — prospect pipeline draft #1 of 5 today

*Brand:* {{brand_name}} ({{locations}} locations · {{cities}})
*Platform:* {{platform}} — audit score {{score}}/100
*Owner:* {{owner_name}}, {{owner_title}} — {{email}} (confidence: {{scraped|hunter|guessed}})

*Audit + before/after mockup:* {{audit_link}}

*Subject:* {{subject}}
*Body:*
> {{body}}

React :white_check_mark: to send · :pencil: to edit · :x: to skip
```

Wait for Maxx's reaction or reply.

- ✅ → Step 8 (send)
- ✏️ → wait for edits, post revised draft, wait again
- ❌ → mark prospect `Status = "Skipped — Maxx Veto"` in Notion, log reason if given
- No response in 24h → escalate via iMessage to Maxx (per CLAUDE.md iMessage rules)

---

## Step 8: Send via Superhuman MCP

On approval, send via Superhuman MCP (NOT raw SMTP). Tools:
- `mcp__superhuman__create_or_update_draft` — compose
- `mcp__superhuman__send_draft` — send

Workflow:
```
1. Call create_or_update_draft:
   {
     to: [founder_email],
     from: "maxx@spicedigital.co",
     subject: <approved subject>,
     body: <approved body>,
     attachments: [audit HTML inline link, mockup link inline]
   }
   → returns draft_id

2. Call send_draft:
   { draft_id: <id> }
   → returns sent thread_id

3. Capture thread_id for tracking — Superhuman handles read receipts natively.
```

After send:
1. Append to `outreach-log.json` (deduplication tracker — `email`, `thread_id`, `sent_at`)
2. Post confirmation to the Slack thread: `:white_check_mark: Sent at {{HH:MM}} via Superhuman — thread ID {{thread_id}} for reply tracking`

**Important:** Use `from: "maxx@spicedigital.co"` exactly. No spicy@, no fake aliases.

---

## Step 9: Track in Notion + Schedule Follow-up

Update the Notion Sales Pipeline row (DB `1c8d3ff0-18e7-80e9-8381-000b4448cb87`):
- `Status` → `Cold Outreach Sent`
- `Outreach Date` → today
- `Email Sent To` → founder email
- `Audit Score` → score
- `Audit Link` → Drive URL
- `Mockup Link` → Drive URL
- `Superhuman Thread ID` → for reply correlation
- `Follow-Up Due` → today + 5 business days
- `Owner` → Maxx
- `Source` → `Spice Prospect Pipeline`

The existing `sales-follow-up` scheduled task (Weekdays 7:00am PT) picks up the 5-day no-reply check automatically.

---

## Daily State + Counters

Persist to `~/Desktop/spice-prospect-pipeline/daily-state.json`:

```json
{
  "last_run": "2026-04-29",
  "audits_completed_today": 0,
  "emails_sent_today": 0,
  "skipped_today": 0,
  "queue_remaining": [],
  "daily_cap": 5
}
```

Reset counters when `last_run !== today`.

---

## Templates

`~/Desktop/spice-prospect-pipeline/templates.json` — default seed:

```json
[
  {
    "id": "audit-mockup-cold-v2",
    "name": "Audit + Mockup Cold (v2 — proof-led)",
    "subject": "what we did for {{client_proof}} would work for {{brand_name}}",
    "body": "{{first_name}},\n\nSpice runs delivery marketplace ops for {{relevant_clients}}. Mid-market chains, multi-location, mostly in LA/NYC. We typically lift net payout 15-25% in 90 days.\n\nI audited {{brand_name}}'s {{platform}} this morning and built a quick mockup of where it could go: {{audit_link}}\n\nTwo specific things stood out:\n1. {{finding_1}}\n2. {{finding_2}}\n\nBoth are 30-day fixes.\n\nWorth a 20-min call?\n\nMaxx",
    "is_default": true
  }
]
```

Maxx can manage via:
- "add prospect template [name]"
- "list prospect templates"
- "set default prospect template [name]"

---

## File Structure

```
~/Desktop/spice-prospect-pipeline/
├── daily-state.json
├── templates.json
├── outreach-log.json                  # sent emails (dedup by email + Superhuman thread)
├── prospects/
│   └── {brand-slug}.json              # full prospect record
├── audits/
│   └── {brand-slug}-{date}.html       # local copy of audit reports (with before/after)
├── hero-mockups/
│   └── {brand-slug}-mockup.jpg        # AI-generated improved hero
└── tools/
    ├── discover-restaurants.mjs
    ├── gen-hero-mockup.mjs            # Replicate Seedream 4.5
    └── verify-platform-presence.mjs
```

---

## Triggers

| Phrase | Action |
|--------|--------|
| "run prospect pipeline" | Full daily run (5 audits) |
| "find prospects" | Discovery only — populate Notion |
| "audit [brand]" | Single-prospect run |
| "queue [brand] for tomorrow" | Add to top of queue |
| "show prospect status" | Counters + queue + recent sends |
| Scheduled (default: weekdays 8:00am PT) | Full daily run |

---

## Approval Boundaries

### You CAN do autonomously:
- Source prospects, verify presence, run audits
- Generate hero mockups via Replicate
- Find owner contact (scrape, Hunter, guess)
- Draft emails (always run through humanizer skill)
- Post drafts to Slack for approval
- Update Notion Sales Pipeline (status, scores, links)

### You NEED Maxx's approval to:
- Send any email from maxx@spicedigital.co
- Skip a prospect Maxx queued manually

### You CANNOT:
- Send from any address other than maxx@spicedigital.co
- Email anyone outside the daily cap
- Re-email someone in `outreach-log.json`
- Cite any private Spice client data (see Confidentiality Boundaries)
- Use deceptive subject lines, fake threading, or anything spam-adjacent

---

## Cost Guide

| Operation | Per audit | Per day (5 audits) |
|-----------|-----------|--------------------|
| Google Places discovery | ~$0.005 | ~$0.025 |
| Storefront audit (Cowork tokens via spicy@'s Max sub) | $0 (within sub) | $0 |
| Hero mockup (Replicate Seedream 4.5) | ~$0.003 | ~$0.015 |
| LinkedIn lookup | $0 | $0 |
| Hunter (if used) | ~$0.04 | ~$0.20 |
| Superhuman send | $0 (within Superhuman sub) | $0 |
| **Total** | **~$0.05** | **~$0.25/day** |

Monthly: ~$5-10 for 100 high-quality outbound emails to mid-market chains.

---

## Setup Checklist (one-time)

- [x] Notion Sales Pipeline DB ID: `1c8d3ff0-18e7-80e9-8381-000b4448cb87` (already in CLAUDE.md)
- [x] Approval channel: `#spice-ai-ops` (existing)
- [x] Send via Superhuman MCP (no SMTP credentials needed)
- [ ] Maxx confirms `REPLICATE_API_TOKEN` is set on Mac Mini for hero mockups
- [ ] Maxx confirms Sales Pipeline DB schema includes: `Audit Score`, `Audit Link`, `Mockup Link`, `Superhuman Thread ID`, `Follow-Up Due`, `Email Sent To` (or skill creates them)
- [ ] Optional: `HUNTER_API_KEY` for email enrichment fallback
- [ ] Initial seed: Maxx adds 25-50 target brands to Sales Pipeline with `Status = "Targeted"`
- [ ] Schedule task in Cowork: "weekdays 8:00am PT, run spice-prospect-pipeline"

---

## Daily Reporting

End-of-run summary posted to `#spice-ai-ops`:

```
*Spice Prospect Pipeline — {{date}}*

Audited: 5 / 5
Sent: 4 (1 awaiting approval since {{HH:MM}})
Skipped: 0

*Queue tomorrow:* {{N}} prospects ready
*Replies received yesterday:* {{N}} (Superhuman thread links in thread)
*Pipeline added:* {{N}} new entries
```

Weekly summary on Fridays — overall conversion (sends → replies → calls booked).
