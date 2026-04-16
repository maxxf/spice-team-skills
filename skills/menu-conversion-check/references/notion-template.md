# Notion Page Template for Menu Conversion Analysis

This is the exact Notion-flavored markdown to use when creating the client-facing page. Replace all `[bracketed]` values with actual data.

## Template

```notion
## Bottom Line

[Client]'s Uber Eats menu conversion rate ranges from **[lowest]% ([location]) to [highest]% ([location])** across [N] locations. Below 20% is considered bad. 20% is good. 30% is excellent. 40%+ puts you in the top 1%. [One sentence on trajectory and the single biggest finding.]

This analysis covers [start date] to [end date] vs. [comparison date range].

[If 10+ location client and only a subset was pulled, add: "This analysis covers [X] of [Y] total locations, focused on [selection criteria]."]

---

## Location Performance Rankings

<table header-row="true">
<tr>
<td>**Location**</td>
<td>**Sales**</td>
<td>**vs Prior**</td>
<td>**Orders**</td>
<td>**vs Prior**</td>
<td>**Menu Conv.**</td>
<td>**vs Prior**</td>
</tr>
[Rows sorted by sales descending, one per location]
</table>

---

## Per-Location Breakdown

### [Location Name] ([Address or Identifier])

<callout icon="[emoji]" color="[color]_bg">
**Diagnosis: [Type] Problem.** [One sentence explaining the signal in the data that points to this diagnosis.]
</callout>

<table header-row="true">
<tr>
<td>**Metric**</td>
<td>**Current**</td>
<td>**vs. Prior**</td>
</tr>
<tr>
<td>Sales</td>
<td>[amount]</td>
<td>[+/-X%]</td>
</tr>
<tr>
<td>Orders</td>
<td>[count]</td>
<td>[+/-X%]</td>
</tr>
<tr>
<td>Avg Order Value</td>
<td>[amount]</td>
<td>[+/-X%]</td>
</tr>
<tr>
<td>Menu Conversion</td>
<td>[X%]</td>
<td>[+/-X%]</td>
</tr>
</table>

**Funnel:**

<table header-row="true">
<tr>
<td>**Stage**</td>
<td>**Count**</td>
<td>**vs. Prior**</td>
</tr>
<tr>
<td>Viewed Store</td>
<td>[count]</td>
<td>[+/-X%]</td>
</tr>
<tr>
<td>Viewed Menu</td>
<td>[count]</td>
<td>[+/-X%]</td>
</tr>
<tr>
<td>Added to Cart</td>
<td>[count]</td>
<td>[+/-X%]</td>
</tr>
<tr>
<td>Placed Order</td>
<td>[count]</td>
<td>[+/-X%]</td>
</tr>
</table>

[1-2 sentences in plain language explaining what the data means. Do the math for the reader. Show the delivered price if pricing is the issue. Show the traffic collapse if distribution is the issue.]

---

[Repeat for each location with appropriate diagnosis callout colors:]
- Pricing Problem: icon="🔴" color="red_bg"
- Traffic Problem: icon="🟡" color="yellow_bg"
- Menu Problem: icon="🟠" color="orange_bg"
- Offer/Promo Problem: icon="🟣" color="purple_bg"
- Seasonal/External: icon="⚪" color="gray_bg"

---

## Action Plan

### Step 1: [Verb phrase describing the action]

**What:** [Specific action with numbers]

**Why:** [Data point that justifies this action]

**The math:** [Show the expected impact calculation]

### Step 2: [Second action]

[Same structure]

### Step 3: [Third action - fix fundamentals]

[Bullet points for each location-specific fix, if applicable]

---

## Expected Impact

<table header-row="true">
<tr>
<td>**Metric**</td>
<td>**Current**</td>
<td>**Target (30 days)**</td>
<td>**Target (60 days)**</td>
</tr>
<tr>
<td>Menu Conversion Rate</td>
<td>[X%]</td>
<td>[X-Y%]</td>
<td>[X-Y%]</td>
</tr>
<tr>
<td>Monthly Orders</td>
<td>[~X]</td>
<td>[~X]</td>
<td>[~X+]</td>
</tr>
<tr>
<td>Monthly Sales</td>
<td>[$X]</td>
<td>[$X+]</td>
<td>[$X+]</td>
</tr>
</table>

---

## Timeline

<table header-row="true">
<tr>
<td>**Week**</td>
<td>**Action**</td>
<td>**Owner**</td>
</tr>
<tr>
<td>Week 1 ([dates])</td>
<td>[Specific actions]</td>
<td>[Owner]</td>
</tr>
<tr>
<td>Week 2 ([dates])</td>
<td>[Specific actions]</td>
<td>[Owner]</td>
</tr>
<tr>
<td>Week 3 ([dates])</td>
<td>[Specific actions]</td>
<td>[Owner]</td>
</tr>
<tr>
<td>Week 4 ([dates])</td>
<td>[Specific actions]</td>
<td>[Owner]</td>
</tr>
</table>

---

*Data pulled [date] from Uber Eats Manager. Prepared by Spice Digital.*
```

## Notion Page Properties

When creating the page in the Document Hub:

```json
{
  "Doc name": "[Client] Menu Conversion Analysis - [Month Year]",
  "Category": "[\"Strategy doc\"]",
  "Client": "[\"https://www.notion.so/[client-page-id]\"]"
}
```

Icon: "📊"

## Finding the Right Notion Location

1. Search Notion for the client name in the Clients database (`collection://1c8d3ff0-18e7-80e9-8381-000b4448cb87`)
2. Fetch the client page to find the Document Hub database
3. Look for a data source URL like `collection://[uuid]` under the "Documents (Reports, Audits & Decks)" section
4. Create the page under that data source with the properties above
