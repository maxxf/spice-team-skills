---
name: retention-monthly-report
description: Use this skill to generate the monthly retention report for MBFS, HealthNut, or Ahipoki. Triggers include "pull retention report for [client]", "monthly retention report for [client]", "generate [client] retention numbers", "monthly KPIs for [client]", "[client] retention summary", or any combo of client + month + reporting / numbers / KPIs. The skill walks the Chrome MCP through Toast and Thanx dashboards, populates the client's Retention Tracker Google Sheet, generates a Notion summary page, and posts highlights to #retention-marketing. Replaces 3-4 hours of manual data entry per month per client. This is the highest-leverage retention skill.
---

# Retention Monthly Report

The monthly retention report is the single most time-consuming recurring task in the service. Tomas burned 3-4 hours per month on it. This skill cuts it to under 30 minutes including QA.

## Inputs

1. **Client**: MBFS | HealthNut | Ahipoki
2. **Reporting month**: e.g. "May 2026"
3. **Platforms** (auto-detected from client, but ask if ambiguous):
   - MBFS → Toast + Thanx
   - HealthNut → Thanx only
   - Ahipoki → Thanx + Klaviyo (once migration completes) + Toast (reporting only)

## Required tools

- Notion MCP (read Campaign Planning DB, write summary page)
- Slack MCP (post to `#retention-marketing`)
- Google Drive MCP (write to client's Retention Tracker sheet, store screenshots)
- **Klaviyo MCP** (for Ahipoki post-migration — replaces Chrome navigation for the Klaviyo side entirely). Tools: `get_campaigns`, `get_campaign`, `get_metrics`, `get_events`.
- Chrome MCP / Comet (navigate Toast + Thanx dashboards — no public MCPs exist for either)

If Chrome MCP is not connected, stop and tell the user. Do not attempt to fabricate numbers.

For Ahipoki: if the Klaviyo MCP is connected, use it instead of Chrome for the Klaviyo data. ~30 min faster per report.

## Process

### Phase 1: Toast pull (MBFS and Ahipoki only)

Navigate the Chrome MCP through these 5 Toast admin pages. Each page has exact fields to capture. Pull every number listed.

**Page 1: Reports > Sales > Marketing-Driven Sales**
- Total Sales
- In-Store Sales
- Toast Online Ordering Sales
- Branded Mobile App Sales
- Attributed Sales
- Attributed Orders
- Loyalty-Attributed Sales
- Email-Attributed Sales

**Page 2: Guest Engagement > Loyalty Program > Insights**
- Loyalty Orders Share %
- Avg Loyalty Spend
- Loyalty Sign-ups
- Loyalty Redemptions
- Total Discount Amount
- Loyalty Sales Lift
- Loyalty Retention Rate
- Non-Loyalty Retention Rate

**Page 3: Guest Engagement > Marketing (dashboard)**
- Total Subscribers
- Emails Sent
- Emails Delivered
- Emails Opened
- Orders Driven
- Sales Driven

**Page 4: Guest Engagement > Marketing > each individual campaign sent this month**
Per campaign:
- Campaign Name
- Send Date
- Type
- Audience Size
- Delivered
- Opened
- Clicked
- Unsubscribed
- Orders
- Revenue

**Page 5: Guest Engagement > Marketing > Automations tab > each active flow**
Per automation:
- Sends
- Delivered
- Opens
- Clicks
- Unsubscribed
- Orders
- Revenue

Take screenshots of each page as proof. Store them in the client's Google Drive `Reports/[Month]/` folder.

### Phase 2: Thanx pull (all three clients)

Navigate to `dashboard.thanx.com` using `success@spicedigital.co`. Pull:

**Top-line KPIs:**
- Capture Rate
- Activation Rate
- Retention Rate
- EDR (Effective Discount Rate)
- Total Members
- Monthly Active Members
- Member Growth (month over month)

**Per-campaign performance:**
- Opens
- Clicks
- Redemptions
- Revenue
- A/B test winners (if applicable)
- Control group lift

**Use the new Thanx reports (released April 2026):**
- Points Redemption Activity Report (14-day attribution window per campaign)
- Activation Funnel Report (cohort tracking, account creation → 1st, 2nd, 3rd purchase)

Take screenshots. Store with the Toast screenshots.

### Phase 3: Klaviyo pull (Ahipoki only, once live) — via Klaviyo MCP

When the Klaviyo MCP is connected, use the API directly. No Chrome navigation needed.

Steps:

1. `get_campaigns` with date filter for the reporting month. Returns the list of every campaign sent.
2. For each campaign, `get_campaign(campaign_id)` to pull: recipients, opens, clicks, unsubscribes, conversions, revenue, control-group lift.
3. `get_metrics` for top-line: list growth, total revenue, revenue per recipient, average order value.
4. `get_events` filtered by `unsubscribed`, `flagged`, `complained` to spot any spike worth flagging in the anomalies section.
5. For each active flow (welcome, winback, abandoned cart, etc.), pull flow-level metrics.
6. If SMS is live, the same calls return SMS-channel data: delivered, clicked, opted out.

Until the Klaviyo MCP is connected OR Klaviyo provisioning is not yet complete: fall back to Chrome navigation through `klaviyo.com` using the same field list, OR skip and note in the summary "Klaviyo migration in progress, data pending."

### Phase 4: Populate the Google Sheet

Open the client's Retention Tracker workbook. Template links:
- MBFS: ask Harol for current sheet URL or pull from `clients/MBFS` Cowork project
- HealthNut: ask Harol or pull from project
- Ahipoki: ask Harol or pull from project

Fill three tabs:
- **Tab 1**: Monthly KPIs by source
- **Tab 2**: Campaign-level stats (one row per send)
- **Tab 3**: Automation / flow stats (one row per flow)

Use the existing formulas (delivery rate, open rate, click rate, unsub rate, revenue per recipient). Do not overwrite formulas. Fill values only.

### Phase 5: Notion summary page

Create a new Notion page in the client's Documents Hub with this structure:

```
# [Client] Retention Report — [Month YYYY]

## Headline
Three bullets. Specific. Numbers. Example:
- $14,212 in attributed email revenue (up 18% MoM)
- Winback automation drove $3,841 from 6,200 sends (62¢/recipient)
- Open rates held at 41% across 3 campaigns

## What worked
2-3 specific campaigns or automations that overperformed. Why we think they worked.

## What didn't
1-2 things below benchmark. Diagnosis. What we'll do differently next month.

## Anomalies + flags
- Any open rate below benchmark
- Any automation that stopped sending
- Any unsub spike (>2%)
- Any campaign with revenue per recipient below $0.20

## Next month plan
3-5 campaigns scheduled. Pull from Campaign Planning DB.

## Appendix
- Link to Google Sheet
- Link to screenshots folder
- Per-campaign table
- Per-automation table
```

### Phase 6: Slack post

Post to `#retention-marketing` with this template:

```
:bar_chart: [Client] retention report — [Month]

*Headline*: [one-line top number]
*Best campaign*: [campaign name] — [revenue / open rate]
*Watch item*: [anything below benchmark or anomalous]

Full report: [Notion link]
Sheet: [Google Sheet link]
```

Tag Maxx if anything flagged as "watch item" needs his attention.

## QA before returning

- Every number in the Notion summary appears in the Google Sheet too. No orphan numbers.
- Every campaign in the month is accounted for (cross-check against Campaign Planning DB).
- Screenshots are linkable.
- Voice rules applied (no emdashes, no AI tells).

## If a number is missing

Do not fabricate. Mark the field "data pending" and surface in the summary's anomalies section. Tag Maxx in the Slack post.

## Time saved

Manual process: 3-4 hours per client per month.
This skill: 20-30 minutes including QA.
Annual time saved per client: ~36-42 hours.
