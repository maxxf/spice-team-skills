---
name: retention-segments-subjects
description: Use this skill to pick the right segment for a retention campaign and generate subject line + preview text options with A/B variants. Triggers include "segment for [client] [campaign]", "who should we send to", "subject lines for [campaign]", "subject line ideas for [client]", "preview text for [campaign]", "A/B subjects", or any request to design the audience or the inbox-side copy of a retention campaign. Output is a recommended segment with reasoning + 5 subject line options (3 styles, 2 controls) + matching preview text + send-time recommendation.
---

# Retention Segments + Subject Lines

The two highest-leverage decisions on any retention campaign are who you send to and what the subject line says. Both happen before the email even opens. This skill makes both deliberate.

## Inputs

1. **Client**: MBFS | HealthNut | Ahipoki
2. **Campaign objective**: promo | winback | seasonal | LTO | review request | loyalty milestone | announcement
3. **Offer or hook**: what the email is actually about
4. **Send date**: defines the urgency framing

## Process

### Phase 1: Segment selection

Pull the canonical segments from `references/segment-rubric.md`. Pick the best fit based on:

- **Reach needed** (how big does the audience need to be)
- **Match between offer and audience** (a winback offer to a regular customer is wasted, a VIP offer to a churned customer signals desperation)
- **Suppression overlap** (don't double-send if a parallel flow is hitting the same segment)

Output the segment recommendation with reasoning. If the campaign needs a custom segment, write the filter logic. Example:

```
Recommended segment: Ahipoki — Lapsed loyalty members (45-89 days)
Filter: last_purchase_date BETWEEN 89 and 45 days ago
        AND loyalty_member = TRUE
        AND email_subscribed = TRUE
Suppression: anyone in active Winback flow, refund last 14 days
Estimated reach: ~8,000-10,000 members
Reasoning: This window is the sweet spot — recent enough to remember the brand, lapsed enough that the offer feels relevant. The Winback flow handles 60+ day lapsers, so we don't double-hit them.
```

### Phase 2: Subject line generation

Generate 5 subject line options across 3 styles. Each under 50 characters. None contain emdashes. None contain hollow openers ("Just so you know", "Quick question").

**Style 1 — Direct value**
The offer or the why, stated plainly.
Example: "$10 off your next bowl"
Example: "Free side this weekend at MBFS"

**Style 2 — Curiosity / question**
A question or unfinished thought.
Example: "Your points are about to expire"
Example: "We saved your seat"

**Style 3 — Personalized / contextual**
Uses first name, last visit, or behavioral context.
Example: "[First name], that bowl you loved is back"
Example: "Been a minute since your last order"

Plus 2 "controls" for A/B testing — variants of the strongest option above with different framing (urgency, length, emoji).

### Phase 3: Preview text

Match each subject with 40-90 character preview text. Preview text is the second-most-read piece of copy after the subject. Never leave it blank.

Bad preview text: "Open this email to find out more"
Good preview text: "We dropped a new bowl. Plus 15% off through Sunday."

### Phase 4: Send time recommendation

Based on:
- Client (each has a sweet spot — see `references/send-times.md`)
- Channel (email vs SMS)
- Day of week
- Offer urgency (a 24h offer needs different timing than a month-long promo)

### Phase 5: A/B test setup

Recommend the A/B variable for any campaign over 5K recipients. Options:
- Subject line (A vs B)
- Preview text
- CTA copy
- Hero image
- Send time

Pick one variable. Never test multiple at once.

## Output format

```
## Segment
[Recommendation + reasoning + filter + reach estimate]

## Subject lines

**Recommended (A)**: "..." (40 char)
Preview: "..." (60 char)

**Variant (B)**: "..."
Preview: "..."

**Style alternatives**:
1. Direct: "..."
2. Question: "..."
3. Personalized: "..."

## Send time
Recommended: [Day] at [time] [client timezone]
Reasoning: [why]

## A/B test
Variable: [subject | preview | CTA | image | time]
Split: 50/50
Decision criterion: open rate primary, click-through secondary, ship the winner to remaining list after 24h
```

## Voice enforcement

Before returning, scan every subject and preview for:

- emdashes → replace
- "Just" / "Quick question" / "Hey there" openers → rewrite or delete
- "Don't miss out" → replace with the actual specific
- AI tells ("amazing", "incredible", "exciting") → rewrite
- All caps beyond 2 words → adjust to sentence case unless intentional emphasis

## What this skill is NOT

- Not a full brief. That's `retention-campaign-brief`.
- Not flow-level work. That's `retention-flow-designer`.
- Not a final QA pass on body copy. That's `retention-qa-checklist`.

References:
- `references/segment-rubric.md` — canonical segments with use cases
- `references/send-times.md` — per-client send time sweet spots
- `references/subject-line-patterns.md` — proven patterns from past Spice campaigns
