---
disabled: true
disabled_reason: Runs on Mac Mini (Spicy Nugget). Do not schedule on laptop.
name: review
description: Friday scorecard with letter grade, client metrics, and team assessment
---

---
name: review
description: Friday end-of-week scorecard and review for Spice Digital. Trigger on "review", "Friday review", "weekly review", "week in review", "scorecard", "how'd we do this week", "weekly scorecard", "end of week review", "Friday wrapup", "weekly metrics", or any request to evaluate the week's performance. Also trigger on "grade the week", "rate this week", or "what did we accomplish this week". Pulls meeting outcomes, client metrics, pipeline movement, and team output to generate an honest assessment with a letter grade.
---

# Friday Scorecard (/review)

Generate an honest end-of-week assessment of how Spice performed. This isn't a feel-good summary. It's a scorecard with teeth — what went well, what didn't, and a letter grade for the week.

The Friday review is the accountability mechanism. It forces a backward look before /weekly-prep does the forward look on Sunday.

## Workflow

### 1. Gather This Week's Meeting Data

```
SearchMeetings:
- startDate: Monday of this week
- endDate: today (Friday)
```

ReadMeetings for all client meetings. Extract:
- Decisions made
- Action items created vs completed
- Client sentiment (positive, neutral, negative signals)
- Any client escalations or complaints

### 2. Pull Client Performance Metrics

For each active client with a Google Sheet tracker, pull this week's numbers:

```
Google Drive search:
- Find weekly tracker sheets for active clients
```

Key metrics per client:
- Total sales (this week vs last week, % change)
- Marketing-driven sales and ROAS (if running campaigns)
- Order volume and AOV trends
- Net payout %

If no Google Sheet exists, check Notion databases or skip that client's quantitative section.

### 3. Pipeline Movement

```
notion-search:
- query: "Pipeline" database
```

Compare current pipeline state to last week:
- New prospects added
- Prospects that advanced stages
- Deals closed (won or lost)
- Prospects gone cold (no activity in 7+ days)

### 4. Action Item Completion Rate

Pull all action items created this week (from Circleback meetings) and check how many are marked complete vs still open. Calculate a completion rate.

This is the most honest metric in the scorecard. If the team created 20 action items and completed 6, that's a 30% completion rate and it needs to be called out.

### 5. Team Output Assessment

Review what each team member shipped or accomplished this week:
- **Rodrigo:** [Key outputs for his clients]
- **David:** [Key outputs for his clients]
- **Manish:** [Key outputs]
- **Daniela:** [Key outputs]
- **Tomas/Rui:** [Retention work]

Source from: Circleback meetings, Slack activity, Notion task completions.

### 6. Score the Week

Assign a letter grade (A through F) based on:

| Factor | Weight | What "A" Looks Like |
|--------|--------|-------------------|
| Client results | 30% | Metrics trending up across majority of clients |
| Action item completion | 25% | 80%+ of items completed on time |
| Pipeline movement | 20% | Net positive pipeline movement (new > lost) |
| Client satisfaction | 15% | No escalations, positive signals in meetings |
| Team execution | 10% | Everyone delivered their key outputs |

The grade should be defensible. Show the reasoning, not just the letter.

## Output Format

---

### 📊 Week in Review — [Month Day] to [Month Day], [Year]

**Grade: [Letter]** — [One-sentence justification]

#### 🏆 Wins
1. [Biggest win of the week — specific metrics]
2. [Second win]
3. [Third win]

#### 📉 Misses
1. [What fell short — be specific about impact]
2. [What fell short]

#### 📈 Client Scorecard
| Client | Sales Trend | Key Metric | Sentiment | Notes |
|--------|-------------|------------|-----------|-------|
| Goop Kitchen | ↑ 12% | ROAS 4.2x | 😊 | Menu audit landed well |
| Capriotti's | ↓ 5% | CPO up $0.80 | 😐 | Investigating DD algo change |
| Everytable | → flat | Orders +3% | 😊 | New locations onboarding |
| ... | ... | ... | ... | ... |

#### ⚡ Action Item Scorecard
- **Created this week:** [X]
- **Completed:** [Y] ([Z]%)
- **Overdue (carried from prior weeks):** [N]
- **Biggest miss:** [Specific item that should have been done but wasn't]

#### 🔮 Pipeline Snapshot
| Prospect | Stage | Movement | Next Step |
|----------|-------|----------|-----------|
| Main Squeeze | Proposal Sent | ↑ from Discovery | Follow up Monday |
| Brooklyn Dumpling | Cold | ↓ No reply 10d | One more touch then shelf |

#### 👥 Team Performance
- **Ro:** [Assessment — what shipped, what's pending]
- **David:** [Assessment]
- **Manish:** [Assessment]
- **Daniela:** [Assessment]
- **Tomas/Rui:** [Assessment]

#### 🎯 Next Week's Must-Wins
1. [The thing that matters most next week]
2. [Second priority]
3. [Third priority]

---

### Formatting Principles

- **The grade is honest.** B- weeks happen. C weeks happen. Calling it an A when it wasn't helps no one.
- **Wins and Misses are balanced.** Don't bury the misses or pad the wins.
- **Sentiment emojis are quick visual cues.** 😊 = happy, 😐 = neutral, 😟 = concerning. Don't overthink them.
- **Action item completion rate is the accountability metric.** If it's consistently low, the team is overcommitting.
- **Next Week's Must-Wins set up Sunday's /weekly-prep.** This is the handoff.

## Output Destination

Push to Notion under "Maxx - Scratchpad" with title format:
**Review | Week of [Mon Mar 2, 2026]**

Display inline first.

## Relationship to Other Skills

- **/gn** daily syncs feed data into the Friday review
- **/weekly-prep** on Sunday plans the next week; /review on Friday grades the current one
- **/kickoff** on Monday broadcasts the plan; /review on Friday checks if it happened
- The weekly rhythm: Review (Fri) → Prep (Sun) → Kickoff (Mon) → Daily GM/GN → Review (Fri)

## Edge Cases

**Short week (holiday, PTO):** Adjust expectations. A 3-day week with 60% action item completion might still be an A if the right things got done.

**No metrics available:** Some clients don't have tracker sheets yet. Score those clients on qualitative signals only (meeting sentiment, Slack activity, action item progress).

**First week with a new client:** Don't grade them yet. Note "onboarding in progress" and track baseline setup tasks instead of performance metrics.