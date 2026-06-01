---
name: ratings-reply
description: Manage customer review replies and $5 credit incentives across Uber Eats and DoorDash for Spice clients. Use this skill when the user mentions "review replies", "ratings replies", "reply to reviews", "review management", "$5 credit", "review credits", "feedback replies", "customer reviews on DoorDash", "customer reviews on Uber Eats", "set up auto-reply", "configure review responses", "weekly review replies", or any request to respond to customer reviews on delivery platforms. Also trigger when the user asks about review response templates, review reply cadence, setting up review incentives, or managing the flyer-to-credit pipeline. This covers both the Uber Eats auto-reply configuration (with browser automation) and the DoorDash manual weekly reply process.
---

# Ratings & Review Reply Management

This skill handles the end-to-end process of replying to customer reviews on Uber Eats and DoorDash, including applying $5 promotional credits as part of Spice's review incentive program (the flyer program).

## Context

Spice runs a review solicitation program for clients: printed flyers in delivery bags offer customers $5 off their next order in exchange for leaving a rating/review on Uber Eats or DoorDash. The two platforms handle reply workflows differently:

- **Uber Eats**: Supports auto-reply with attached promo credits. One-time setup per store location. Can be automated via browser.
- **DoorDash**: No auto-reply. Requires manual replies through the Merchant Portal with credits applied during the reply flow.

## Step 1: Ask Who Handles DoorDash Manual Replies

Before doing anything else, ask the user:

**"Will our team (Spice Ops) handle the weekly DoorDash review replies for this client, or will the client's team manage replies themselves?"**

Use the AskUserQuestion tool with these options:

- **Spice team handles it** (Ops Analyst does weekly replies, logs in Slack, handles escalations)
- **Client manages their own** (We provide them a Notion guide with templates and process, they reply directly)

This answer determines which path the rest of the skill follows. Store the answer and branch accordingly.

---

## Uber Eats Auto-Reply Setup (Browser Automation)

This section applies to BOTH paths. UE auto-reply is always configured by Spice because it's a one-time setup with no ongoing manual work.

The Ops Analyst will already be logged into UE Manager in Chrome. Use Claude in Chrome tools to automate the configuration.

### Prerequisites

- Ops Analyst is logged into Uber Eats Manager in their browser (using credentials from Platform Credentials DB in Notion)
- Claude in Chrome (browser tools) is enabled

### Automated Setup Flow

For each store location, execute this sequence:

#### Step 1: Navigate to the Reviews Page

```
Use: mcp__Claude_in_Chrome__tabs_context_mcp to get the active tab ID
Use: mcp__Claude_in_Chrome__navigate to go to:
  https://merchants.ubereats.com/manager/
Use: mcp__Claude_in_Chrome__computer action: "wait" duration: 3
  (UE Manager is React-heavy and needs time to render)
```

The Ops Analyst should already be logged in. From the main dashboard, navigate to the specific store location (if multi-location) and then to Feedback > Reviews. Use screenshots and `read_page` to find the correct navigation path since the portal layout changes periodically.

#### Step 2: Take a Screenshot and Read the Page

```
Use: mcp__Claude_in_Chrome__computer action: "screenshot"
  (Verify we're on the right page and logged in)
Use: mcp__Claude_in_Chrome__read_page filter: "interactive"
  (Find the auto-reply settings, review response config, or gear/settings icon)
```

Look for elements like:
- "Auto-reply" toggle or settings
- "Review response" or "Feedback settings"
- A gear icon or "Settings" link near the reviews section
- "Reply settings" or "Automated responses"

The UE Manager UI changes periodically. If the expected elements aren't found, take a screenshot and ask the user to point out where the auto-reply settings are.

#### Step 3: Enable Auto-Reply

Once you've located the auto-reply settings:

1. **Screenshot the current state** before making changes
2. **Tell the user what you're about to do:**
   "I'm going to enable auto-reply for this location with the following message and a $5 promo credit. Confirm before I proceed?"
3. **Wait for explicit user confirmation** before clicking or typing anything
4. After confirmation:
   - Toggle auto-reply ON if it's currently off
   - Find the reply message text field
   - Use `form_input` to set the message:

   ```
   Thank you for taking the time to leave a review! Your feedback helps us improve. As a thank you, we've added a $5 credit to your next Uber Eats order with us. We appreciate your support and hope to serve you again soon!
   ```

5. **Configure the $5 promo credit:**
   - Look for a "Promotion" or "Credit" or "Offer" option attached to the auto-reply
   - Set: $5 off next order, no minimum, single use
   - Set expiration to 30 days if the option exists

6. **Screenshot the configured state** before saving
7. **Tell the user:** "Here's the configuration. Ready to save?"
8. **Wait for confirmation**, then click Save/Submit

#### Step 4: Verify

```
Use: mcp__Claude_in_Chrome__computer action: "wait" duration: 2
Use: mcp__Claude_in_Chrome__computer action: "screenshot"
  (Confirm the settings saved successfully)
```

Report to the user: "Auto-reply configured for {location_name}. Moving to the next location." or "All locations configured."

#### Step 5: Log Completion

After all locations for a client are configured, post in the client's #int-{client} Slack channel:
"UE auto-reply configured for {X} locations. $5 credit active. Date: {date}."

### Multi-Location Clients

For clients with multiple locations:

1. Once logged in, use the store/location switcher in the UE Manager dashboard to cycle through each location
2. Process each location sequentially using the flow above
3. Track completion: after each location, tell the user "{N} of {total} locations configured"
4. If any location fails (page won't load, settings not found, error on save), skip it and flag it at the end

### Fallback: Manual Guidance

If Claude in Chrome is not available, or the UE portal layout has changed significantly and automation can't find the right elements:

1. Read `references/platform-guides.md` for the manual setup walkthrough
2. Walk the user through the steps verbally
3. The user handles the clicking, you handle the instructions and template text

---

## Path A: Spice Team Handles DoorDash Replies

Use this path when our Ops Analysts are managing review replies on behalf of the client.

**Important:** DoorDash's Merchant Portal blocks browser automation tools (Claude in Chrome cannot screenshot or read the page). All DoorDash review replies are fully manual. The Ops Analyst handles everything directly in the portal. Claude's role is to provide templates, track progress, and log completion.

### Ownership

- **Growth Managers** assign this task to Ops Analysts per client
- **Ops Analysts** execute the weekly DoorDash replies and initial Uber Eats auto-reply setup
- **GMs** handle escalations (health/safety, threats, suspected fraud, legal mentions)

### A1: Execute Weekly DoorDash Review Replies

When asked to do weekly review replies for a client on DoorDash:

1. Read `references/reply-templates.md` for the full template library
2. Read `references/platform-guides.md` for the DoorDash step-by-step process
3. The Ops Analyst should already be logged into the DoorDash Merchant Portal using credentials from the Platform Credentials DB in Notion. Navigate to **Customer Feedback** from the left sidebar.
4. Guide the Ops Analyst through:
   - Opening each client location's feedback page
   - Identifying unreplied reviews
   - Selecting the right template based on star rating
   - Personalizing with customer name, dish mentions, specific issues
   - Applying the $5 credit during the reply flow
   - Logging completion in #int-{client} Slack channel with format:
     "DD reviews replied. {X} total, {Y} credits applied. Week of {date}."
5. Flag any reviews that need GM escalation before replying

### A2: Generate Client-Specific Reply Templates

When asked to draft or customize review reply templates for internal use:

1. Read `references/reply-templates.md` for the base templates
2. Customize the templates with the client's brand name, tone preferences, and any special offers beyond the standard $5
3. Output a client-specific template doc that Ops can reference during weekly replies

### A3: Audit Review Reply Coverage

When asked to check if reviews are being replied to:

1. For Uber Eats: Verify auto-reply is active by checking recent reviews for responses
2. For DoorDash: Check the feedback page for unreplied reviews and note how many are pending
3. Report back with: total reviews, replied count, unreplied count, average rating, and any escalation flags

### Weekly Cadence (Path A)

**DoorDash replies happen every Monday.** Ops Analyst processes all unreplied reviews from the prior week across all assigned client locations. Completion is logged in each client's internal Slack channel.

**Uber Eats auto-reply runs continuously** once configured. Spot-check monthly to confirm it's still active and credits are being applied.

---

## Path B: Client Manages Their Own Replies

Use this path when the client's team will handle DoorDash review replies directly. The Ops Analyst prepares, publishes, and shares the guide. The client executes weekly.

### B1: Prepare & Publish the Client Guide

The canonical client guide template lives at:
`https://www.notion.so/33ad3ff018e781c783cfcf4909e6f55e`

This guide includes portal navigation directions, how to set up DoorDash Saved Reply templates, and copy/paste templates for every star tier.

**Ops Analyst workflow:**

1. **Duplicate the template page** into the client's Notion portal under Documents
   - Use the Notion tools: `mcp__notion__notion-duplicate-page` with page ID `33ad3ff0-18e7-81c7-83cf-cf4909e6f55e`
   - Then `mcp__notion__notion-move-pages` to place it under the client's Documents section

2. **Customize the duplicate:**
   - Replace every `[brand]` with the client's actual restaurant name
   - Adjust credit amount if different from $5
   - Note: The client navigates to Customer Feedback from the left sidebar after logging into merchant.doordash.com

3. **Publish to web:**
   - On the duplicated page, click Share (top right)
   - Toggle "Publish to web" on
   - Copy the published URL

4. **Share with the client** via email or #ext-{client}-spice:

   > "Here's the review reply guide we put together for your team. It walks through where to find reviews in DoorDash, how to set up saved reply templates so it takes 30 seconds per review, and the template text for every star rating. The key thing: every review gets a reply with a $5 credit, regardless of the rating. Let us know if you have questions!"
   >
   > [published Notion link]

5. **Log in #int-{client}:** "DD review reply guide published and shared with client. Date: {date}."

### B2: Periodic Check-In

Even when the client handles their own replies, Spice should spot-check quarterly:

1. Pull up the client's DoorDash feedback page
2. Check if reviews from the past 2-4 weeks have replies
3. If reply coverage is dropping off, flag it to the GM who can follow up with the client
4. This is a 5-minute task, not a deep audit. Just confirm the client is actually doing it.

---

## Escalation Rules (Both Paths)

Do NOT reply to a review (or advise the client to reply) if any of these apply. Tag the GM first:

- Review mentions food poisoning, allergens, or foreign objects
- Review contains threats or harassment
- Review mentions legal action or lawsuits
- Review appears to be fake or from a competitor
- Review names a specific employee

For Path B clients, these escalation rules are already included in the shared Notion guide.

## Credit Rules (Both Paths)

- $5 credit applies to ALL reviews regardless of star rating
- Credit is single-use, no minimum order, 30-day expiration (recommended)
- Every review gets a reply with credit attached. No exceptions by rating.

## Reply Tone Guidelines

Read the voice guide at `maxx-freedman-voice-guide.md` for Spice's overall communication style. For review replies specifically:

- Professional but warm. Not robotic, not overly casual.
- Short. Most replies should be 2-3 sentences plus the credit line.
- Empathetic on negative reviews without being defensive or making excuses.
- Never blame the customer. Never blame the platform in a customer-facing reply (even if it's the platform's fault, be diplomatic).
- One personality moment per reply if the review gives you something to work with (they loved a specific dish, they're clearly a regular, etc.).

## Reference: Client Guide Notion Page

The client-facing DoorDash review reply guide (for Path B) is maintained as a Notion page:
- **Page ID:** `33ad3ff0-18e7-81c7-83cf-cf4909e6f55e`
- **URL:** `https://www.notion.so/33ad3ff018e781c783cfcf4909e6f55e`

This page contains simplified instructions and all reply templates organized by star rating. It's designed to be duplicated per client and customized with their brand name.
