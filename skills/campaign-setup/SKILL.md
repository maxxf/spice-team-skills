---
name: campaign-setup
description: >
  Create a fully briefed campaign implementation ticket in the Team Task Tracker,
  register it in the Campaign Planning DB (the campaign registry), assign to the
  ops analyst on the client's Supporting Team, and notify #support-ops in Slack.
  Every campaign MUST be logged in the Campaign Planning DB for visibility.
  Use this skill whenever the user says "set up campaign for [client]", "schedule
  [campaign type] for [client]", "create campaign ticket", "BOGA for [client]",
  "BOGO for [client]", "set up promo for [client]", "launch offer on Uber Eats/
  DoorDash for [client]", "campaign ticket for [client]", or any request to
  operationally set up (not strategically plan) a delivery marketplace campaign.
  Also trigger when the user says "set up ads for [client]", "schedule featured
  listing", "create DashPass offer", "Grubhub loyalty for [client]", "sponsored
  placement on Grubhub", or references any specific platform campaign type for a
  client. This skill covers Uber Eats, DoorDash, AND Grubhub campaign types.
  This skill is for EXECUTION handoff, not strategic planning (use campaign-planner
  for strategy).
---

# Campaign Setup

Create a campaign implementation ticket, log it in the Campaign Registry (Campaign
Planning DB), assign to the right ops analyst, and notify via Slack. Every campaign
MUST be registered in the Campaign Planning DB for full visibility.

> **Strategy filter — apply the playbooks before registering.** Every campaign passes through the Spice marketplace playbooks at `Cowork/Skills/campaign-plan/references/playbooks/` (`what-works.md` + `marketplace-playbook.md`). Hard gates: (1) **Foundations** — block if rating <4.5, error rate >2%, uptime <95%, or menu conversion <20% at the target locations; route to ops/menu work first. (2) **Segment required** — every campaign sets `Customer Segment` on the DB row (New / Existing / Lapsed / DashPass / All). No blanket promos without explicit "All" justification. (3) **Marketplace only** — UE / DD / GH; Meta is a separate service. (4) **Decay plan** — multi-week campaigns include a refresh + spend-down plan. If a proposal violates a playbook rule with intent, document the "why" in the campaign Notes.

## Why This Skill Exists

Every campaign Spice runs needs to be briefed, logged, and trackable. The Campaign
Planning DB is the single source of truth for what's running, when, and for which
client. This skill automates the full pipeline: brief the details, create the
Task Tracker ticket, register the campaign in the DB (so it appears in all views
and client portals), assign to ops, and notify. One command turns "run a BOGA at
these 3 locations" into a fully tracked, visible, assigned campaign.

## Prerequisites

- **Notion MCP** (create/update pages in Team Task Tracker + Campaign Planning)
- **Slack MCP** (send notification to #support-ops)
- Client must exist in the Clients database with a `Supporting Team` field populated

## Inputs Needed

Collect from the user (ask for anything missing):

1. **Client name** (must match a client in the Clients DB)
2. **Platform(s)**: Uber Eats, DoorDash, Grubhub, or combination
3. **Campaign type** (see Campaign Type Reference below)
4. **Offer details** (e.g., "Buy 1 entree, get 1 add-on free", "20% off orders $20+")
5. **Locations** (specific subset or "all")
6. **Start date** ⚠️ REQUIRED — do not proceed without this
7. **End date** (or duration to calculate end date) ⚠️ REQUIRED — do not proceed without this
8. **Customer segment**: All, New only, Existing only, Lapsed, DashPass (DD only)
9. **Day part**: All day, Lunch, Dinner, Late Night
10. **Budget** (if ad-type campaign) or "merchant-funded" (if offer-only)
11. **Priority**: High / Medium / Low (default: Medium)
12. **Urgency**: Urgent / Standard / Low Priority (default: Standard)
13. **Client approved?**: Yes / Not yet (default: Not yet)
14. **Needs design/creative?**: Yes / No — ALWAYS ASK THIS. If yes, collect:
    - **Asset type**: Ad - Static, Ad - Video, Hero Image, Menu Image, Flyer, Email
    - **Creative brief** (what should the design convey, any specific assets/photos to use)
    - Dilli Dias is auto-assigned as Designer (Notion ID: `33bd872b-594c-81e0-937a-0002fe81f779`)

**Hard requirements:** Start date and end date (or duration) are non-negotiable. If
the user doesn't provide them, ask. If they say "not sure yet," push back: campaigns
without dates can't be tracked on the timeline or auto-completed. They can give a
rough estimate and update later, but they must give *something*.

If the user provides a Notion task page URL, update that page instead of creating new.

## Task Title Format (Notion Entry)

**MANDATORY.** Every Notion task/registry title MUST follow this pattern:

```
[Client Short Name] — [Platform Abbrev] [Campaign Type] ([Location List]) [Start MM/DD]
```

**Platform abbreviations:** UE = Uber Eats, DD = DoorDash, GH = Grubhub, UE+DD = both, ALL = all three

**Examples:**
- `Fresh Kitchen — UE BOGA (Boca, Miami, Lutz) 4/13`
- `Greenleaf — DD DashPass 20% Off (All Locations) 5/01`
- `Awan — UE+DD Featured Listing (Doral, Brickell) 4/20`
- `Pokeworks — UE Free Delivery (Tampa, Orlando) 6/15`
- `Everytable — GH Loyalty (All Locations) 5/01`
- `Ahipoki — ALL BOGO (6 Locations) 7/01`

## In-Platform Campaign Naming Convention

**SEPARATE FROM the Notion title.** This is what the ops analyst types into the
platform dashboard when creating the campaign in Uber Eats, DoorDash, or Grubhub.

Best practice: create separate campaigns per location in Uber Eats (and generally
across platforms). Each campaign in-platform follows this naming format:

```
[Location] | [Offer / Ad Type] | [Customer Segment]
```

**Examples:**
- `Boca Raton | BOGA | All Customers`
- `Miami | BOGA | All Customers`
- `Lutz | BOGA | New Customers`
- `Doral | Featured Listing | All Customers`
- `Brickell | 20% Off $20+ | DashPass`
- `Winter Garden | Free Delivery | New Customers`
- `Gainesville | Sponsored Placement | All Customers`

**Rules:**
- Use pipe `|` as separator (easy to scan in platform dashboards)
- Location = the city or neighborhood name, matching the store name in the platform
- Offer / Ad Type = the specific campaign type or offer details
- Customer Segment = who the offer targets
- Keep it concise. The platform dashboard truncates long names.

Include the full list of in-platform campaign names in the brief body so the ops
analyst can copy/paste directly when setting up each location.

**Rules:**
- Use the client's common short name, not the full legal name
- If more than 4 locations, use "(X Locations)" instead of listing them
- Date is always the START date in M/DD format
- Campaign type uses the short name from the reference table below

## Campaign Type Reference

### Uber Eats

| Short Name | Full Name | Type | Description |
|---|---|---|---|
| Featured Listing | Featured Listing | Ad | CPM-based placement higher in search. Set daily budget. |
| Sponsored Item | Sponsored Items | Ad | Individual items promoted in browse/search. |
| % Off | Percentage Discount | Offer | % off order total or specific items. Specify min order + max discount. |
| $ Off | Dollar Discount | Offer | Flat dollar off. Specify min order threshold. |
| BOGO | Buy One Get One | Offer | Buy one item, get same/different item free. Specify qualifying + free items. |
| BOGA | Buy One Get One Add-on | Offer | Buy entree, get add-on free. Specify entree category + add-on category. |
| Free Delivery | Free Delivery | Offer | Restaurant absorbs delivery fee. Specify min order if any. |
| Bundle | Bundle Deal | Offer | Multi-item combo at set price. Specify items + bundle price. |

### DoorDash

| Short Name | Full Name | Type | Description |
|---|---|---|---|
| Promoted Listing | Promoted Listing | Ad | CPC bid-based search placement. Set daily budget + bid. |
| DashPass % Off | DashPass Offer | Offer | Exclusive discount for DashPass subscribers. |
| Tiered Discount | Tiered Discount | Offer | Spend threshold triggers discount (e.g., $5 off $25+). |
| First Order | First Order Discount | Offer | New customer discount. Specify % or $ off. |
| Free Delivery | Free Delivery | Offer | Absorb delivery fee for orders over threshold. |
| BOGO | Buy One Get One | Offer | Same as UE. Specify qualifying + free items. |

### Grubhub

| Short Name | Full Name | Type | Description |
|---|---|---|---|
| Sponsored Placement | Sponsored Results | Ad | Daily-budget bid-based search ranking boost. Smaller pool than UE/DD but less competition in some markets. |
| Loyalty | Loyalty Program | Offer | Customers earn points, get rewards after X orders. Restaurant funds reward (typically $5-10 off). |
| % Off | Percentage Discount | Offer | Percentage off order total. Simpler targeting than UE/DD. |
| $ Off | Dollar Discount | Offer | Flat dollar off order. Specify min order threshold. |
| Free Delivery | Free Delivery | Offer | Restaurant absorbs delivery fee. |
| BOGO | Buy One Get One | Offer | Buy one item, get another free. |

## Workflow

### Step 1: Resolve Client

1. Search the Clients DB (`collection://1c8d3ff0-18e7-80e9-8381-000b4448cb87`) for the client by name
2. From the client page, extract:
   - Client page URL (for the `Client` relation field)
   - `Supporting Team` user IDs
   - Client short name (for the task title)
3. Cross-reference Supporting Team against the ops analyst roster:

**Ops Analyst Roster:**

| Name | Notion User ID | Slack User ID |
|---|---|---|
| Santiago Beltran | 336d872b-594c-81f7-887a-0002fa54184e | U0AQJFT8LP8 |
| Dulari Fernando | 1cad872b-594c-81a0-a0db-000282941e87 | U08LFKT3APP |
| Manish Kumar | 2afd872b-594c-8133-b913-00024826113c | U09TR52DVMY |

4. If one ops analyst is on the Supporting Team, assign to them
5. If multiple ops analysts are on the Supporting Team, assign to all of them
6. If NO ops analyst is on the Supporting Team, assign to all three and note this in the Slack message ("no assigned ops analyst for this client, please self-assign")

### Step 2: Build the Task Title

Follow the MANDATORY title format above. Construct from the inputs:
- Client short name
- Platform abbreviation(s)
- Campaign type short name (from the reference table)
- Location list or "X Locations"
- Start date in M/DD

### Step 3: Create or Update the Team Task Tracker Entry

**Data source:** `collection://1c8d3ff0-18e7-80f0-a36b-000b6befe5b1`

Set these properties:
```
Request Title: [formatted title from Step 2]
Client: [client page URL from Step 1]
Status: "Not started"
Task type: "Campaign Implementation"
Source: "Agent"
Platforms: [selected platform(s)]
Locations: [comma-separated location names]
Priority: [from input, default "Medium"]
Urgency Level: [from input, default "Standard - 1 to 2 business days"]
Description: [one-line summary: duration, offer, locations, segment]
Approval Contact: [client's approval contact if known]
"": [ops analyst Notion user ID(s) from Step 1]  ← this is the Assignee field
date:Due date:start: [start date minus 2 days, or start date if <2 days away]
date:Go-Live Date:start: [campaign start date]
```

Then populate the page CONTENT with the campaign brief:

```markdown
# Campaign Brief

**Campaign Objective**
[User-provided objective, or auto-generate: "Drive [goal] at [N] locations
([location list]) by running a [duration] [campaign type] [offer type] on
[platform]. [Rationale for the offer mechanic]."]

**Locations**
- [Location 1] [RED emoji if priority location]
- [Location 2]
...

**Offer Mechanic**
[Detailed offer description from user input]

**Customer Segment:** [segment]
**Day Part:** [day part]
**Budget:** [budget details or "Merchant-funded offer"]

---

[Campaign details table - fill in only the relevant platform columns]

| Details | Uber Eats | DoorDash | Grubhub |
|---|---|---|---|
| Campaign Type | [Ad / Offer] | [Ad / Offer] | [Ad / Offer] |
| Campaign Offer | [offer details] | [offer details] | [offer details] |
| Customer Segment | [segment] | [segment] | [segment] |
| Campaign Day Part | [day part] | [day part] | [day part] |
| Start Date | [date] | [date] | [date] |
| End Date | [date] | [date] | [date] |

---

## Implementation Checklist
- [ ] Client approved campaign details
- [ ] Budget confirmed
- [ ] [Platform] campaign scheduled
- [ ] Campaign Roadmap (sheet) updated
- [ ] Manager verified campaign is live
- [ ] Client notified campaign is live
```

**IMPORTANT:** Only include checklist items for the platforms being used.
Do NOT include DoorDash checklist items for a UE-only campaign, and vice versa.

### Step 4: Register Campaign in Campaign Planning DB

**Data source:** `collection://1c8d3ff0-18e7-8067-abff-000b54568283`

This is the campaign registry, the single source of truth. Create ONE entry per
campaign (not per-location). One campaign = one row. Location details are captured
in the Locations text field; per-location breakdown lives in the Task Tracker brief.

Properties:
```
Campaign name: "[formatted title from Step 2]"
Entry Type: "Campaign"
Campaign Type: [matching short name from Campaign Type Reference]
Channels: [JSON array of platforms, e.g., ["Uber Eats"] or ["Uber Eats", "DoorDash"]]
Client: [client page URL from Step 1]
Status: "Brief" (or "Client Approved" if user confirmed approval)
Service Team: "Marketplace"
Offer Details: [full offer description, e.g., "Buy 1 entree, get 1 add-on free (side, drink, or snack)"]
Customer Segment: [from input: "All", "New Only", "Existing Only", "Lapsed", "DashPass"]
Day Part: [from input: "All Day", "Lunch", "Dinner", "Late Night"]
Budget: [budget text, e.g., "Merchant-funded", "$10/day/location", "$500 total"]
Locations: [comma-separated location names]
Location Count: [number of locations as integer]
ROAS Target: [if ad campaign, target ROAS as number; null for merchant-funded offers]
Task Tracker Link: [URL of the Team Task Tracker page created in Step 3]
date:Start Date:start: [campaign start date]
date:End Date:start: [campaign end date]
```

**If design/creative is needed**, also set:
```
Designer: ["33bd872b-594c-81e0-937a-0002fe81f779"]  ← Dilli Dias
Asset Type: [from input: "Ad - Static", "Ad - Video", "Hero Image", "Menu Image", "Flyer", "Email"]
```

When design is flagged, the campaign entry serves double duty: it's both the campaign
record AND the design brief. Dilli can filter Campaign Planning by Designer = Dilli
to see all campaigns that need creative work from her.

Also populate the page CONTENT with the campaign brief body. This makes every
registry entry self-contained (clickable from client portals without following links):

```markdown
# Campaign Brief

**Objective**
[User-provided objective, or auto-generate: "Drive [goal] at [N] locations
([location list]) by running a [duration] [campaign type] [offer type] on
[platform]. [Rationale for the offer mechanic]."]

**Offer Mechanic**
[Detailed offer description from user input]

**Locations**
- [Location 1] [🔴 if priority location]
- [Location 2]
...

---

## Campaign Details

[Campaign details table - only include columns for platforms being used]

| Details | Uber Eats | DoorDash | Grubhub |
|---|---|---|---|
| Campaign Type | [Ad / Offer] | | |
| Offer | [details] | | |
| Segment | [segment] | | |
| Day Part | [day part] | | |
| Start | [date] | | |
| End | [date] | | |
| Budget | [budget] | | |

---

## In-Platform Campaign Names

Copy/paste these when setting up each campaign in the platform dashboard.
Format: `Location | Offer/Ad Type | Segment`

[Generate one row per location. If multi-platform, note which platform each is for.]

| Location | Platform | Campaign Name (copy/paste into platform) |
|---|---|---|
| [Location 1] | [UE/DD/GH] | [Location 1] | [Offer Type] | [Segment] |
| [Location 2] | [UE/DD/GH] | [Location 2] | [Offer Type] | [Segment] |
...

---

## Implementation Checklist

- [ ] Client approved campaign details
- [ ] Budget confirmed
- [ ] [Platform] campaign(s) created (1 per location)
- [ ] Campaign names match naming convention above
- [ ] 📸 Screenshot of each platform setup uploaded below
- [ ] Campaign Roadmap (sheet) updated
- [ ] Manager verified campaign is live
- [ ] Client notified campaign is live

[IF DESIGN NEEDED, add these items:]
- [ ] 🎨 Creative brief shared with Dilli
- [ ] Design V.1 delivered
- [ ] Design approved by client
- [ ] Creative assets uploaded to platform

---

## Platform Setup Screenshots

⚠️ **Required.** After setting up campaigns in each platform, screenshot the
confirmation screen and upload here. One screenshot per platform per location.
This is proof of setup and the team's reference for verifying the campaign is
configured correctly.

[Ops analyst: drag and drop screenshots here]

---

[IF DESIGN NEEDED, include this section:]

## Creative Brief

**Asset Type:** [Ad - Static / Ad - Video / Hero Image / etc.]
**Designer:** Dilli Dias
**Dimensions/Specs:** [platform-specific specs, e.g., UE hero = 1200x400px]

**Direction:**
[What should the design convey? Key message, product focus, any specific
photos or brand assets to use. Include links to photo drive if available.]

**Deliverables:**
- [ ] [Asset 1 description + dimensions]
- [ ] [Asset 2 description + dimensions]

**Design Files:**
[Dilli: upload final assets here]

---

## Performance Log
*Fill in after campaign ends.*

**Actual ROAS:** —
**Incremental Orders:** —
**Notes:** —
```

This entry automatically appears in:
- **Active Campaigns** view (table filtered to active campaign statuses)
- **Campaign Timeline** (horizontal bars from start to end date, best for 1-2 month planning)
- **Campaign Calendar** (calendar by start date)
- **Campaign Board** (kanban by status)
- **Client portal** (via the existing linked view of Campaign Planning in each client's space)
- **All Campaigns** view (full history, sorted by date descending)

### Step 5: Soft Approval Check

Before sending the Slack notification, determine approval status:

- If the user explicitly said "client approved" or "approved", the Campaign Planning
  entry Status should already be "Client Approved" from Step 4. No warning needed.
- If NOT approved, Status stays "Brief" and the Slack message includes:
  `:warning: Campaign not yet client-approved. Status is "Brief" in Campaign Registry. Move to "Client Approved" once confirmed.`

This is a soft gate. The campaign is created and assigned regardless, but the warning
ensures the team knows approval is pending and the registry reflects reality.

### Step 6: Notify via Slack

Send a message to `#support-ops` (channel ID: C08DJUDFVHR):

```
:mega: *New Campaign Ticket*

*[Task Title]*
:link: [Notion task page URL]
:bar_chart: [Campaign Planning registry entry URL]

*Client:* [client name]
*Platform:* [platform(s)]
*Campaign:* [campaign type] — [offer summary]
*Locations:* [location list]
*Go-live:* [start date]
*Due:* [due date]

Assigned to: @[ops analyst name]
```

If approval is pending, append:
```
:warning: Campaign not yet client-approved. Status is "Brief" in Campaign Registry. Move to "Client Approved" once confirmed.
```

If design is needed, append:
```
:art: *Design needed.* Dilli assigned. Asset type: [asset type]. See creative brief in the registry entry.
```

If no ops analyst was matched, replace the assigned line with:
```
:warning: No assigned ops analyst for this client. @Santiago @Dulari @Manish please self-assign.
```

Use the Slack user IDs for @mentions:
- Santiago: <@U0AQJFT8LP8>
- Dulari: <@U08LFKT3APP>
- Manish: <@U09TR52DVMY>

### Step 7: Confirm to User

Report back:
1. Link to the Team Task Tracker page (the brief)
2. Link to the Campaign Planning registry entry
3. Who it was assigned to
4. Confirmation that Slack notification was sent
5. Approval status (approved or pending)
6. Design status (if applicable: Dilli assigned, asset type)

## Campaign Status Flow

Campaigns in the Campaign Planning DB follow this lifecycle:

```
Brief → Client Approved → Scheduled → Complete
                                    → Canceled
                       → On Hold
```

- **Brief**: Campaign is briefed but not yet approved by the client
- **Client Approved**: Client has signed off on the campaign details
- **Scheduled**: Campaign has been set up in the platform dashboard(s)
- **Complete**: Campaign has ended and (ideally) performance data is logged
- **Canceled**: Campaign was canceled before or during execution
- **On Hold**: Campaign is paused

The ops analyst managing the campaign should update the status in Campaign Planning
as the campaign progresses. After completion, they should fill in Actual ROAS and
Performance Notes for the post-campaign record.

## Edge Cases

- **User provides a Notion task page URL**: Update that existing page instead of creating a new one. Still create the Campaign Planning registry entry and send the Slack notification.
- **"All locations"**: Fetch location list from the client's `Service Details` field or ask the user.
- **Multi-platform campaign**: Create one Task Tracker entry AND one Campaign Planning registry entry covering all platforms. The Channels multi-select field captures multiple platforms on a single entry.
- **Campaign on Grubhub**: Check the client's service details. If the client is flagged as "NO Grubhub" (e.g., Fresh Kitchen), reject gracefully and suggest UE/DD alternatives. Otherwise, include Grubhub in the brief. Note: Grubhub's promo tools have less targeting granularity than UE/DD.
- **Missing client in DB**: Ask the user to confirm the client name or create the client first.
- **Ad campaigns (budget-based)**: Include budget fields in the brief. Add "Budget cap set in platform" to the checklist. Set ROAS Target if the user provides one.
- **Duplicate campaign check**: Before creating, search Campaign Planning for existing entries with the same client + overlapping dates + same campaign type. If found, warn the user and ask if this is intentional (e.g., a second wave) or a duplicate.
