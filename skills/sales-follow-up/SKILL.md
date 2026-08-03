---
name: sales-follow-up
description: >
  Daily pipeline follow-up agent for Spice sales. Scans Circleback meeting notes for unfulfilled commitments (deck, audit, proposal) and Notion Sales Pipeline for stale deals, then drafts Superhuman follow-up emails in Maxx's voice and posts a summary to Slack. Trigger on "sales follow-ups", "check pipeline follow-ups", "what follow-ups do I owe", "draft follow-up emails", "pipeline check", or any request about pending sales actions. Also trigger when Maxx asks "did I send that deck", "who am I following up with", or "what's stale in the pipeline".
---

# Sales Follow-Up

Draft follow-up emails for active sales deals based on two sources: meeting commitments and pipeline staleness. Every email must sound like Maxx wrote it. Every action must be justified by evidence, not arbitrary timers.

## Philosophy

Do not be annoying. A follow-up is only justified when:
1. Maxx committed to sending something and hasn't sent it yet
2. A deal has gone quiet long enough that re-engagement is warranted
3. A next step was agreed on and the date has arrived or passed

If none of these are true, leave the deal alone.

## Data Sources

### Email Source: Superhuman MCP
All email lookups, draft creation, and draft-duplicate checks go through the Superhuman MCP (server prefix `mcp__superhuman__*`). Do not use the Gmail API. Drafts created via Gmail don't sync to Superhuman, where Maxx actually reads and sends, and the Gmail signature handling will double up Maxx's footer.

**Tools you'll use:**
- `query_email_and_calendar` — natural-language search across Maxx's inbox + sent + drafts. Use this for "find emails to/from {email}", "find drafts on this thread", "find the last sent message about {topic}".
- `list_threads` — paginated thread list with filters (e.g., sender, recipient, label, recency). Use when you need to walk a specific contact's history.
- `get_thread` — full message history for a thread_id. Use this once you've located the relevant thread to confirm last sender and content.
- `get_message` — single message by id, for spot-checks.
- `list_splits` — Maxx's drafts pane ("splits" in Superhuman). Use this to check for existing unsent drafts before creating new ones.
- `create_or_update_draft` — the only tool that creates or edits a draft. Always pass `thread_id` for reply drafts. Pass `type: "new"` for fresh outreach.
- `discard_draft` — only use if you created a draft you need to roll back. Never discard a draft you didn't create.

**Duplicate-draft check (run before every `create_or_update_draft`):**
1. Call `list_splits` filtered by the prospect's email or thread_id.
2. If an unsent draft already exists on that thread, do NOT create a new one. Either update the existing draft (pass the same `draft_id` to `create_or_update_draft`) or flag it in the Slack summary as "draft already pending — review existing."

### Source 1: Circleback (commitment detection)
Search this week's meetings for sales/prospect conversations. Read the notes. Identify commitments Maxx made:

**HARD EXCLUSION: hiring candidates.** Never include hiring conversations, co-founder vetting, recruiter intros, or technical assessments in this skill's output, including the "FYI" section of the Slack summary. Signals that mark a meeting as hiring (skip entirely): "co-founder", "founding [role]", "technical lead", "CTO candidate", "hiring", "role", "compensation", "equity", "founding team", "trial project", "assignment", "case study interview", "working session" tied to a candidate name, or any meeting where the other party is being evaluated for employment with Spice rather than as a paying client. If the meeting could plausibly be either, default to excluding it. The sales agent's job is paying-customer pipeline only.

**Commitment signals to scan for:**
- "Maxx is sending" / "will send" / "I'll send" / "sending over"
- "deck" / "services deck" / "services overview"
- "storefront audit" / "audit" / "custom audit" / "UE audit"
- "proposal" / "put together a proposal" / "pilot proposal"
- "follow-up call" / "follow up" / "circle back"
- "I'll have [X] back to you" / "within a couple days"
- Any mention of a deliverable with a deadline

For each commitment found, use Superhuman `query_email_and_calendar` (or `list_threads` + `get_thread`) to check for a sent message in that thread containing the deliverable (deck link, audit link, proposal link). If found, the commitment is fulfilled. Skip it.

### Source 2: Notion Sales Pipeline
Query the Sales Pipeline database (ID: `1c0d3ff0-18e7-80fa-b0b6-cc5887a502c4`).

**Active stages to check:** New Lead, Reached Out, Qualified, Meeting Booked, Pitched, Proposal Shared, Ice Box

**Excluded stages (skip entirely):** Won, Lost, Not a Fit, Agreement Sent

**Staleness rules:**
- `Last contact date` is 14+ days ago → flag as stale
- `Last contact date` is 7-13 days ago AND stage is Proposal Shared or Pitched → flag as cooling
- `Last contact date` is empty → flag as missing data (don't draft, just flag)
- Ice Box deals: only flag if 30+ days, and frame as "worth revisiting?"

For each flagged deal, pull the most recent Superhuman thread with that contact (use the Email field with `query_email_and_calendar` or `list_threads`, then `get_thread` on the top result) to understand context before drafting.

**Critical guard:** Inspect the last message in the thread. If the most recent message is FROM the prospect (i.e., Maxx hasn't replied yet), do NOT draft a follow-up. Flag it in the Slack summary as "{Name} replied {date} and is awaiting your response."

## Email Drafting

### Voice Rules
Read `maxx-freedman-voice-guide.md` before drafting. That file is the source of truth. The rules below are the must-hits, not the full picture.

**The vibe.** Smart friend who works in the industry being straight with the prospect. Direct, specific, a little spicy. Not corporate. Not consultant-speak. Maxx writes like he talks.

**Structural rules (every email):**

- Open with first name + em dash + space. Maxx's signature pattern: `Name — message`. Examples: "Michel — asked about the audit two weeks back." / "Andrea — picking this thread back up." Em dash for the greeting, not commas. (Mid-sentence em dashes inside prose are still fine if they fit the rhythm; the AI tell is using them as filler, not the dash itself.)
- Then immediately the point. No "Hope you're well." No warm-up. No "I wanted to reach out."
- **Each paragraph is a single beat. Separate beats with blank lines.** Paragraphs of 1-3 sentences max. Never run multiple thoughts together as a wall of text. Beat 1: name the silence or state the situation. Beat 2: the offer or the question. Beat 3: the close or kill option.
- Reference something concrete from the last touch. The deal value. A name they mentioned. A date they committed to. The specific thing they said. Generic = delete and rewrite.
- Vary sentence length like a drummer. Short. Then a longer sentence with a real piece of context inside it. Then short again. AI's tell is uniform paragraph length. Don't sound like AI.
- Do the math for the reader when pricing or scope is in play. "$11,380/mo across 26 locations" not "competitive pricing."
- For stale re-engagement specifically, use the **either/or with kill button** pattern Maxx actually writes (see real examples below). Name the silence, state the binary, name one specific tactic, hand them the kill option, end with "Either answer works." or equivalent.
- One moment of personality per email if it fits. Not forced. Not edgy for the sake of it.
- End on a forward push or a clean question. Not a summary of what you just said.
- Read it back in your head as if Maxx were saying it on a call. If it sounds like a press release, rewrite.

**The stale re-engagement template (use this exact shape):**

```
{Name} — {name the silence with specifics}. Either {option A: timing/fit not right} or {option B: priorities shifted/got buried}.

Want {one specific tactical play with location count or detail}, or {kill option: "close this out" / "put this one down" / "put this one on ice"}?

Either answer works.
```

Real examples Maxx sent on 2026-04-28:
- "Jack, three follow-ups, no response. Either the audit's not useful or now's not the time. Want me to put this one on ice, or do you want a quick look at the menu consolidation play across the 50 locations? Either answer works."
- "Manny, sent the audit and pricing back in March, bumped a couple times since. Either the timing's not right or this one's not landing. Want to take a real look at the category consolidation, or close this out? Either answer works."
- "Chuck, two weeks back I asked yes or no on the audit. Silence is fine, just making sure it didn't get lost. Want a quick call to walk through Marlton and Edgewater, or should I put this one down?"

**Hard bans (zero tolerance, every time):**

- AI-style em dashes used as filler inside sentences (e.g., "this is — frankly — overdue"). Em dashes are fine for the `Name — ` greeting and for genuine asides; not as connector tics.
- "Genuinely" / "Straightforward" / "Here's the kicker"
- "It's not about X, it's about Y"
- "At the end of the day" / "In today's [anything]" / "Let's dive in" / "Without further ado"
- "Game-changer" / "Cutting-edge" / "Synergy" / "Holistic" / "Paradigm" / "Best practices" / "Low-hanging fruit"
- "Leverage" (verb) / "Unlock" (metaphor) / "Landscape" / "Navigate" / "Elevate" / "Foster" / "Robust" / "Seamless" / "Ecosystem"
- "I wanted to reach out" / "I hope this finds you well" / "Just circling back" / "Per our conversation" / "As per my last email"
- "Excited to announce" / "Thrilled to share"
- "Moving forward" / "Going forward" (use "from here" or just state the next step)
- Watery qualifiers: "somewhat", "relatively", "fairly", "quite", "rather"
- Filler transitions: "Moreover", "Furthermore", "Additionally", "In addition" — start the next sentence
- Sycophantic openers: "Great question!", "That's a fantastic point!" — delete entirely
- Hedge stacking ("might potentially be somewhat useful") — commit to the position
- More than one exclamation mark per email. Earn it.
- More than 1-2 bolded phrases per section. Bold is for emphasis, not decoration.

**Approved Maxx closers** (pick what fits):

- "Talk soon," (post-discovery, warm follow-up)
- "Sound good?" (after action items or proposals)
- "Let me know how you'd like to proceed" (handing decision back)
- "Happy to jump on a call to talk through any of this" (substantive emails)
- "When ready, feel free to book some time to chat here" (with cal.com link, prospects)
- "Thank you," (escalations, hard messages, payment chases)

**Opener patterns Maxx actually uses (model these — note em dash, not comma):**

- "Simon — deck attached. USD pricing and case studies inside."
- "Andrea — picking this thread back up."
- "Michel — asked about the audit two weeks back, no answer."
- "Matan — appreciate your kind note about the podcast."
- "Tom — asked you three months back if Matt had reviewed."
- "Elena — the latest invoice is a couple weeks past due."
- "James — please contact Michael (copied) to discuss migrating the account."
- "Yo — " (internal team, casual)

**Self-check before saving the draft:**

1. First sentence carries the point (no warm-up lap)
2. At least one specific number, name, date, or detail (no vague claims)
3. Sentence length varies (not three same-shaped sentences in a row)
4. Zero em dashes, zero banned phrases
5. Max one exclamation mark
6. Ends with a push forward or a clean question, not a summary
7. Would Maxx actually say this out loud?

### Email Templates by Situation

#### Post-Discovery Follow-Up (commitment: deck + audit)
**Subject:** Spice <> {restaurant_name}

```
{first_name} — {one-line specific reference to the call or what was promised}.

{Customized 1-2 sentence reference to their specific situation: footprint, gap they flagged, number they shared. This is the body, not the opener.}

[Our services deck]({deck_link})
[Storefront Audit]({audit_link})

{Forward push: "I'll come back on X in the next two weeks." or "Cal.com if you want to dig in sooner."}
```

Note: em dash after first name, not comma. Each beat (opener / body / links / push) is its own paragraph with blank lines between. Customize body to reference something specific. Don't ship the template as-is.

If the audit hasn't been created yet but was promised:
1. Invoke the `storefront-audit` skill for the restaurant (use the restaurant name and any location details from the meeting notes)
2. QA the audit output: verify scores are populated, screenshots/links are valid, and the report is complete
3. Save the audit to Notion
4. Flag in the Slack summary: "Audit created for {restaurant_name} — publish the Notion link before sending the draft." Include the Notion page URL so Maxx can toggle Share to Web quickly.
5. Create the Superhuman draft with the Notion URL as the audit link, but mark the draft in the summary as BLOCKED (needs publish)

If the audit skill fails or produces incomplete output, flag it in the summary: "Audit for {restaurant_name} needs manual review before sending." Do not include a broken link in the draft.

If additional items were discussed (Mailchimp campaigns, data requests, menu info), add them as bullets. Pull from the meeting notes.

#### Post-Discovery Follow-Up (commitment: deck only, no audit)
Same template, remove the audit bullet. Add any other discussed deliverables.

#### Gentle Bump (deal cooling, 7-14 days since proposal/pitch)
Do NOT use a template. Write a short, natural email that:
- Acknowledges they're busy (without being sycophantic about it)
- References one specific thing from your last conversation
- Offers a clear next step
- 3-5 sentences max

**Example patterns from real Maxx emails (em dash openers, paragraph breaks between beats):**
- "Hey guys — I figure you have your hands full with {context}. I'm here in case you have follow up questions or want to discuss next steps."
- "{first_name} — bumping this up so we can plan accordingly."
- "{first_name} — checking in on this. Happy to jump on a quick call if it'd help."
- "{first_name} — picking this thread back up. Last we talked, {specific_thing}. Where did that land?"

For stale 14+ day re-engagements, use the either/or kill-button template above instead of these gentler bumps.

#### Stale Deal Re-engagement (14+ days, needs a decision)
Short and direct. The goal is to get a yes/no, not to re-pitch.
- State where things left off (one sentence)
- Ask directly if they want to move forward
- Offer the booking link as an easy next step
- 2-4 sentences max

#### Meeting Confirmation (24hrs before scheduled call)
Only draft if a follow-up meeting was explicitly scheduled in the notes. Keep it ultra short:
- "Looking forward to connecting {day}. Anything specific you'd like to cover?"

### Hyperlinks
All links in drafts must be hyperlinked, not raw URLs:
- Deck: `[Our services deck](https://www.figma.com/deck/oj07jEcK3FjCzhkQffmYtV)`
- Audit: `[Storefront Audit]({notion_audit_url})`
- Proposal: `[Updated Proposal]({notion_proposal_url})`
- Booking: `[book time here](http://cal.com/spice-digital)`

When creating Superhuman drafts, pass HTML in the `body` field with proper anchor tags:
`<a href="URL">link text</a>`

Superhuman renders the HTML directly. Do not paste raw URLs — they read as lazy and clutter the email.

### Signature
Do NOT add a signature block. Superhuman appends Maxx's signature automatically on send. Adding one in the draft results in a duplicate.

End the body on the last line of copy (e.g., "Talk soon," or the final sentence). No `// maxx freedman | managing partner | Spice`.

## Output

### Superhuman Drafts (the only path)
All drafts go through the Superhuman MCP `create_or_update_draft` tool. Never fall back to Gmail. Gmail-created drafts don't sync into Superhuman where Maxx ships from, and Superhuman auto-appends Maxx's signature, so drafts must NOT include one.

For each follow-up:
- `type: "reply"` for existing threads, with `thread_id` resolved via `query_email_and_calendar` or `list_threads`. Confirm the thread before drafting so you don't reply to the wrong conversation.
- `type: "new"` for fresh outreach (no prior thread).
- Before calling `create_or_update_draft`, call `list_splits` to check for an existing unsent draft on the same thread. If one exists, update it in place by passing its `draft_id` instead of creating a duplicate.
- `body` parameter as HTML, with `<p>` tags wrapping each beat. **Each beat is its own `<p>` paragraph** so they render with vertical spacing in Superhuman, not as one wall of text.
- All hyperlinks as `<a href="URL">text</a>`. No raw URLs.
- No closing signature. Body ends on the last line of copy. Superhuman auto-appends Maxx's signature on send.
- Never call `send_draft`. Drafts only. Maxx reviews and ships from Superhuman.

Example HTML body structure for stale re-engagement:
```html
<p>Name — name the silence with specifics. Either option A or option B.</p>
<p>Want one specific tactical play, or kill option?</p>
<p>Either answer works.</p>
```

### Notion Pipeline Update
For each deal where a draft was created, update the `Last contact date` to today's date. Only do this AFTER confirming the draft was created successfully. Use `notion-update-page` with `command: "update_properties"` and the expanded date format: `{"date:Last contact date:start": "YYYY-MM-DD"}`.

### Slack Summary + Email Copy
Post a summary as a DM to Maxx (user_id `U08DMH0DHS8`). For each draft created, include the full email copy in a thread reply under the summary so Maxx can review and copy-paste into Superhuman if he wants to ship from his phone.

Summary format (top-level message):

```
*Sales Follow-Up Summary — {date}*

*This week's commitments:*
• {Name} / {Restaurant}: {what was promised} → {DRAFT READY / BLOCKED / ALREADY SENT}

*Pipeline watch (stale or cooling):*
• {Name} / {Restaurant}: {stage} for {X days}, last contact {date} → {DRAFT READY / AWAITING YOUR REPLY / STALE - needs decision}

*Flags (no draft):*
• {Name} / {Restaurant}: {reason — missing email, holding until X, owed by Maxx, etc.}

*Drafts created:* {count} — review and ship from Superhuman drafts.
```

Then post each draft as a thread reply (one per draft):

```
*Draft N: {Subject}*
To: {email}
Status: {NEW thread / REPLY to existing}

{full email body, plain text, paragraph breaks preserved with blank lines, URLs written out}
```

Render the Slack body with the same paragraph beats as the email so Maxx can eyeball cadence in chat without opening Superhuman.

## What NOT To Do

- Do not send any email automatically. Drafts only. Maxx reviews and sends from Superhuman. Never call `send_draft`.
- Do not use the Gmail MCP for drafts, sends, or thread reads. Superhuman is the source of truth. Gmail-only is acceptable as a last-resort read fallback, and only if `query_email_and_calendar` errors out.
- Do not draft a follow-up if the last message in the thread is FROM the prospect and unanswered. That's a different problem (Maxx needs to respond, not follow up). Flag it instead: "{Name} replied {date} and is awaiting your response."
- Do not follow up on Ice Box deals unless 30+ days and there's a reason to re-engage.
- Do not create duplicate drafts. Call `list_splits` against the thread or recipient before every `create_or_update_draft`. If an unsent draft exists, update it in place via its `draft_id`, never spawn a second one.
- Do not include a signature block. Superhuman appends Maxx's footer on send.
- Do not use any phrase from the Kill List in the voice guide. Zero tolerance.
- Do not draft generic emails. Every email must reference something specific from the conversation, their business, or the deal context. If you don't have enough context, flag it instead of guessing.
