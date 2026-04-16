---
name: weekly-prep
description: Sunday evening weekly prep for Maxx. Trigger when asked to "prep for the week", "weekly prep", "Sunday prep", or "get ready for Monday". Pulls calendar events, recent meeting notes from ALL clients, pipeline database, and sales emails/calls to generate a structured weekly overview with top wins, client updates, pipeline movement, and copy/paste content for the standup doc.
---

# Weekly Prep

Generate Maxx's Sunday evening weekly prep by pulling data from Circleback (meetings/calendar), Notion (pipeline database, client pages), Gmail, and synthesizing it into actionable output.

## Workflow

### 1. Pull Calendar Events (Coming Week)
```
SearchCalendarEvents:
- startDate: [tomorrow, Monday]
- endDate: [+7 days]
- pageIndex: 0
```

Used to populate Top Priorities and identify sales calls, client meetings, and conflicts. No separate calendar table in output.

### 2. Pull Recent Meeting Notes (Last 7 Days)
```
SearchMeetings:
- startDate: [7 days ago]
- endDate: [today]
- pageIndex: 0
```

Then `ReadMeetings` for ALL client meetings to extract:
- Wins (metrics, milestones) — attribute to team member who owns account
- Open action items (what's due, who owns it)
- Churn signals or lost clients
- Onboarding progress updates

**Include ALL clients, not just ones Maxx attends:**
- Goop Kitchen (Rodrigo, Diri)
- Capriotti's (Rodrigo)
- Dayglow/AWAN (David)
- Everytable (Maxx lead, Ro + Manish supporting)
- Teleferic (David)
- My Big Fat Shawarma (Rodrigo, Manish)
- Counter Service (Ro, Daniela)
- Menya Ultra
- Temaki
- Gertie (David)
- Retention clients: MBF, HealthNut, AhiPoki (Tomas, Rui)
- Any new clients in onboarding

Also pull Retention Biweekly for retention-specific updates.

**CRITICAL: Exclude the Spice Team Weekly Standup meeting from all data sourcing.** The weekly prep feeds INTO the standup doc, so pulling data FROM it creates circular duplication. Only source wins, metrics, and updates from client-specific meetings, sales calls, 1:1s, and platform biweeklies. If a data point only appears in the standup and not in any client meeting, it cannot be included in the weekly prep.

### 3. Pull Client Pages from Notion (Onboarding + Context)

Search Notion for client pages, especially clients in onboarding:
```
notion-search:
- query: "[Client Name]" — fetch client workspace pages
```

For onboarding clients, fetch the full page to get:
- Onboarding checklist status (completed vs. pending tasks)
- Blockers, overdue items, at-risk items
- Service details, MRR, key contacts

For active clients, look for:
- Recent meeting notes pages (last 7 days)
- Key updates, decisions, blockers documented by the team
- Action items assigned in Notion

### 4. Pull Sales Pipeline from Notion
```
notion-search:
- query: "Pipeline" or fetch pipeline database directly (ID: 1c0d3ff0-18e7-80fa-b0b6-cc5887a502c4)
```

Check for movement since last week:
- New prospects added
- Status changes (cold → warm, warm → proposal sent, etc.)
- Deals closed (won or lost)

Cross-reference with sales calls/emails from the past week to capture context on next steps.

### 4b. Scan Gmail for Pipeline Signals (Last 7 Days)
```
search_gmail_messages:
- q: "newer_than:7d (from:*@goopkitchen.com OR from:*@capriottis.com OR from:*@brooklyndumpling.com OR from:*@everytable.com OR from:*@enjoyawan.com OR from:*@dayglow.coffee OR from:*@telefericbarcelona.com OR from:*@menya-ultra.com)"
```

Also search for active prospect threads:
```
search_gmail_messages:
- q: "newer_than:7d (proposal OR agreement OR onboarding OR invoice)"
```

And hiring/team threads:
```
search_gmail_messages:
- q: "newer_than:7d (hiring OR contractor OR interview OR offer OR onboard)"
```

This catches:
- Client replies between meetings (async decisions, blockers, asks)
- Proposal follow-ups and contract status updates
- Scheduling signals that never reach Circleback
- Prospect engagement that indicates deal movement
- Hiring updates, interview scheduling, contractor follow-ups

Cross-reference with Circleback notes to fill gaps. If an email thread contradicts or updates meeting notes, the email is more recent and takes precedence.

### 5. Build Churn Risk Scores

Score every active client on 5 dimensions (0 = healthy, 1 = yellow, 2 = red):

| Dimension | What it measures |
|-----------|-----------------|
| **Pay** | Late payments, billing disputes, Stripe issues |
| **Eng** | Responsiveness, meeting attendance, POC changes |
| **Perf** | Sales trends, conversion rates, rating drops |
| **Ops** | Platform issues, menu problems, campaign blockers |
| **Rel** | Account lead changes, relationship tension, difficult-to-work-with signals |

**Total /10. Tiers:** High (6+), Monitor (3-5), Healthy (0-2).

Compare against previous week's scores (fetch prior weekly prep page). Note any score changes and why.

Only surface clients scoring 3+ in the output. All others are noted as Healthy.

### 6. Generate Output

Structure the output in this exact section order:

---

## Output Format

### TL;DR (3 lines max)

Three sentences, max. The single most important win, the single biggest risk, and the single most urgent action item. This is what Maxx reads on his phone before coffee.

Format:
```
**Win:** [one line]
**Risk:** [one line]
**Do Monday:** [one line]
```

---

### 🏆 Big Wins (Top 3-5)

**Select the 3-5 most impactful wins from last week.** Rank by significance (revenue impact, efficiency gains, client milestones). Call out the team member responsible.

Format:
1. **[Win headline]** — [Team Member], [Client]: [specific metrics/details]. *(Source: [meeting name], [date])*
2. ...

Prioritize wins with concrete numbers over qualitative updates. Always include source attribution.

---

### 🔄 Sales Pipeline Update

**Grouped by deal stage. No tables.** Headers for each stage, bullets for each prospect with context.

Format:
```
### Won ✅
- **[Prospect]** ([size], $MRR) — [one-line context]. Next: [action].

### Proposal Shared
- **[Prospect]** ([size]) — [context]. Next: [action]. [status emoji]

### Meeting Booked
- **[Prospect]** ([contact name], [size], [location]) — [source]. **[Day] [Date].**

### Pitched
- **[Prospect]** ([type]) — [context]. Next: [action]. [status emoji if overdue]

### Evaluating
- **[Prospect]** ([type]) — [context]. Next: [action].

### Gone Cold
- [Prospect list] — no email or meeting activity in last 7 days.

### Status Unknown
- [Prospect list] — no signals this week. Check status.
```

Only include stages that have prospects. Skip empty stages.

Do NOT include hiring updates here — this is sales pipeline only.

---

### Onboarding Status Check by Client

**Only include clients currently in onboarding.** For each:

```
### [Client Name] ([Status], [location count], $[MRR]/mo)
Blockers: [N] | Overdue: [N] | At Risk: [N] | On Track: [N]
- [x] **[Completed task]**: [status detail]
- [ ] **[Pending task]**: [status + due date]. [On track / ⚠️ At risk / 🚨 Overdue].
Next milestone: [what's next and when].
```

Pull checklist status from Notion client pages. Cross-reference with meeting notes for real-world progress that may not be reflected in Notion yet.

---

### Churn Risk & Churn Cases

**Active Churn Cases:** [list any clients actively churning].

Only clients scoring 3+ shown. All other accounts noted as Healthy (0-2/10).

Scoring table (only 3+ clients):
| Client | Score | Tier | Pay | Eng | Perf | Ops | Rel | Key Issue |
|--------|-------|------|-----|-----|------|-----|-----|-----------|

Then action items for each at-risk/churning client:
- [ ] **[Client]**: [specific actions this week]. [Note any score changes from prior week].

---

### 📊 Client Updates + Open Action Items

**Include ALL active clients**, alphabetically. Keep each entry tight.

Format:
```
### [Client Name] *([Owner(s)])*
- **Wins:** [one line, metrics preferred. "None" if none.]
- **Open:** [2-4 sentences max. What's due, what's blocked, who owns. Bold the most urgent item.]
```

Rules:
- No repeating info already covered in Big Wins, Onboarding, or Churn sections. Reference those sections instead ("see Churn section above").
- Bold the single most important open item per client.
- If nothing changed for a client, say "No movement this week" and move on.

---

### 🧑‍💼 Team & Hiring Updates

Bullet list covering:
- New hires (start dates, onboarding status, who's ramping them)
- Departures and account transitions
- Role changes (full-time to part-time, etc.)
- Open roles and candidate pipeline (interviews scheduled, follow-ups overdue)
- Contractor/partner status changes (Notice Media, design contractors, etc.)

Flag overdue follow-ups with ⚠️.

---

### 🎯 Your Top Priorities This Week

- [ ] **[Priority]** — [1 sentence context, why it matters, deadline if applicable]

Synthesize from: client action items, pipeline follow-ups, calendar, hiring, strategic initiatives. Order by urgency/impact. 8-12 items max.

---

### 📝 Ready-to-Paste Content for Standup Doc

**Executive Summary (Churn & Risk):**
```
Churn: [clients lost or actively churning, with key metric]
At Risk: [clients 3+ score with one-line reason]
```

**Accomplishments & Shout Outs:**
```
1/ [win] — [team member]
2/ [win] — [team member]
3/ [win] — [team member]
```

**Top Priorities:**
```
- [priority]
- [priority]
...
```

**Pipeline Update:**
```
Closed Won: [if any]
Likely to Close: [prospect] ([size])
Active Convos: [prospects with recent movement]
Gone Cold: [prospects with no response]
Status Unknown: [prospects needing status check]
```

---

## Notes
- **NEVER source data from the Spice Team Weekly Standup meeting.** This avoids duplication since the weekly prep output feeds into the standup doc. Only use client meetings, sales calls, 1:1s, platform biweeklies, Notion, and Gmail as sources.
- Big Wins: Select TOP 3-5 only, ranked by impact, with team member callout and source attribution (meeting name + date).
- Churn Risk: Compare against previous week's prep. Note score changes and reasons.
- Sales Pipeline: Grouped by stage, bullets not tables. NO hiring updates.
- Client Updates: Cover ALL accounts. Keep tight (wins one line, open 2-4 sentences). Don't repeat info from other sections.
- Team & Hiring: Separate section. Flag overdue follow-ups.
- Maxx fills in his own "Something Fun" from the weekend.
- The standup doc template auto-duplicates Monday at 9am.

### 7. Output to Notion

After generating the markdown output, create or update a Notion page with the weekly prep content.

**Location:** Create under "Maxx - Scratchpad" page in Notion (ID: 1d0d3ff0-18e7-805d-8802-fd9baee89737).
**Title format:** "📋 Weekly Prep | [Mon date] - [Fri date], [Year]"

```
notion-search:
- query: "Weekly Prep [date]"
```

If a page already exists for this week, update it with the latest data. If not, create a new page.

**Use `notion-create-pages` or `notion-update-page`** to push the full prep content. This is the primary output.

**CRITICAL formatting rule:** When using `replace_content` or `new_str`, always use actual newline characters in the string. Never use escaped `\n` sequences, which render as literal text in Notion.

Provide a link to the Notion page in the final response.
