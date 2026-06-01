# Performance Tracking & Feedback Loop

## Why This Matters

At 5-10 emails per week, the team generates enough data to learn what works per client. Without a feedback loop, every email is designed from scratch intuition. With one, each email builds on the last.

---

## What to Log (Step 5 of the Skill)

After every email is designed and approved, log these fields to the **Campaign Planning DB** in Notion:

| Field | Value | Example |
|-------|-------|---------|
| Client | Client name | Everytable |
| Email Type | From the 6 types | LTO Launch |
| Layout | A/B/C/D from layout architectures | A: Hero Impact |
| Variant | A or B | Variant A (price-led) |
| Subject Line | The one that was chosen/sent | "New summer bowls. $8.99. Real food." |
| Headline | The main headline used | "Summer bowls just dropped." |
| CTA Copy | Button text | "Order on Uber Eats" |
| Platforms | Which platform CTAs were included | UE, DD, GH |
| Date Sent | When the email was deployed | 2026-04-22 |
| HTML File | Link to the HTML source | Attached to the Notion page |
| Screenshot | Visual reference | Embedded in the Notion page |

### Performance Fields (filled after send)

These are added by the retention specialist 48-72 hours after send, once ESP data is available:

| Field | Value | Source |
|-------|-------|--------|
| Open Rate | Percentage | ESP (Mailchimp, Klaviyo, etc.) |
| Click Rate | Percentage | ESP |
| Conversion Rate | Orders attributed | Platform analytics + UTM |
| Revenue | Dollar amount if trackable | Platform analytics |
| Winner | Which variant won (if A/B) | Comparison of above metrics |
| Notes | What worked, what didn't | Specialist's judgment |

---

## What to Pull (Step 1 Enhancement: Past Winners)

During the brand context pull, add this search after the standard 8-step sequence:

```
9. notion-search: query="[CLIENT NAME] campaign" in Campaign Planning DB
10. Filter for: same email type OR same layout, sorted by date descending
11. Pull the top 3 most recent campaigns for this client
12. Check for "Winner" and "Notes" fields
```

### How to Use Past Performance

Present a "Past Performance" section in the brand brief:

```
PAST PERFORMANCE: [Client Name]
Last 3 emails:
1. [Date] - [Type] - Layout [X] Variant [Y] - Open: [Z%] - Click: [W%] - Winner: [A/B]
   Notes: [specialist notes]
2. [Date] - [Type] - Layout [X] Variant [Y] - Open: [Z%] - Click: [W%]
   Notes: [specialist notes]  
3. [Date] - [Type] - Layout [X] Variant [Y] - Open: [Z%] - Click: [W%]
   Notes: [specialist notes]

Patterns: [auto-detected patterns, e.g., "Layout A consistently outperforms B for this client" or "Price-led variants win 3/3 times"]
```

### Pattern Detection Rules

When reviewing past campaigns, flag these patterns:

- **Layout preference**: If one layout type has 2+ wins, default to it
- **Price sensitivity**: If price-led variants consistently win, always lead with price
- **Subject line style**: Note which subject line approach won (urgency vs. curiosity vs. direct)
- **CTA language**: Track if "Order Now" vs. specific platform names vs. casual language performs better
- **Optimal length**: If shorter emails (Layout B) outperform longer ones, note it

If no past data exists (new client or first email), skip this section and note "No past performance data. This is the baseline."

---

## Quarterly Review Prompt

Every 90 days, the retention specialist should run a review across all clients:

```
Pull all Campaign Planning entries from the last 90 days.
Group by client.
For each client, identify:
- Best-performing email type
- Best-performing layout
- Average open rate trend (improving/declining/flat)
- Most effective subject line patterns
- Any client showing declining engagement (needs strategy shift)
```

This review feeds into campaign planning for the next quarter and may trigger changes to the default layout assignments in `layout-architectures.md`.

---

## Notion Campaign Planning DB Fields

Ensure these properties exist in the Campaign Planning database. If they don't, create them:

- **Email Type** (Select): LTO Launch, BOGO/Promo, Win-Back, Seasonal, Loyalty, Grand Opening
- **Layout Used** (Select): A: Hero Impact, B: Editorial, C: Multi-Product Grid, D: Narrative
- **Variant** (Select): Variant A, Variant B
- **Subject Line Sent** (Text)
- **Open Rate** (Number, percent)
- **Click Rate** (Number, percent)
- **Variant Winner** (Select): A, B, Tie, N/A
- **Performance Notes** (Text)
- **HTML Source** (Files & Media)
- **Email Screenshot** (Files & Media)
