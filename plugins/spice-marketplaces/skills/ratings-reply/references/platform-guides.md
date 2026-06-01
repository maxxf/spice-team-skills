# Platform-Specific Guides

## Uber Eats: Auto-Reply Configuration

Uber Eats supports automated review replies through the merchant portal. This means the $5 credit and thank-you message can be configured once and applied automatically to all incoming reviews.

### Setup Steps

1. Log into the Uber Eats Merchant Manager using credentials from the Platform Credentials DB in Notion
   - URL: `https://merchants.ubereats.com/manager/`
   - For multi-location accounts, select the specific store from the location switcher on the dashboard

2. Go to **Feedback > Reviews** in the left sidebar

3. Look for **Auto-Reply Settings** or **Review Response Settings**
   - This may be under a gear icon or "Settings" within the reviews section

4. Configure the auto-reply:
   - Enable auto-reply for all star ratings (1 through 5)
   - Set the reply message. Use one universal template since UE auto-reply doesn't support conditional logic by star rating:

   **Recommended Universal Auto-Reply:**
   > Thank you for taking the time to leave a review! Your feedback helps us improve. As a thank you, we've added a $5 credit to your next Uber Eats order with us. We appreciate your support and hope to serve you again soon!

5. Enable the **$5 Promo Credit** attachment
   - Uber Eats allows you to attach a promotion to the auto-reply
   - Set: $5 off next order, no minimum, single use
   - Expiration: 30 days from issue (recommended)

6. Save and confirm the auto-reply is active

### Verification
- After setup, check back in 24-48 hours to confirm replies are going out
- Spot-check a few recent reviews to make sure the credit is being applied
- Add a note in the client's Notion page that auto-reply is live with the date

### Per-Client Configuration
Each store location needs its own auto-reply configured. For multi-location clients, use the location switcher in the dashboard to cycle through each location. This is a one-time setup task per location. Track completion in the client's onboarding tasks or a dedicated checklist.

### Limitations
- Uber Eats auto-reply sends the same message regardless of star rating
- No conditional logic (can't send different messages for 1-star vs 5-star)
- The $5 promo credit feature availability may vary by market or account tier
- If the client wants personalized replies to negative reviews, those must be done manually on top of the auto-reply (auto-reply fires first, manual reply can follow)

---

## DoorDash: Manual Reply Process

DoorDash does not support auto-reply for reviews. Every reply must be entered manually through the Merchant Portal. The $5 credit is applied by selecting a promo option during the reply flow.

**Browser automation note:** DoorDash's Merchant Portal blocks Claude in Chrome (no screenshots or page reads allowed). All DoorDash work is fully manual by the Ops Analyst. Claude assists by providing templates and logging completion, not by navigating the portal.

### Access

1. Log into the DoorDash Merchant Portal using credentials from the Platform Credentials DB in Notion
   - URL: `https://merchant.doordash.com/` (or `https://www.doordash.com/merchant/`)
   - For multi-location accounts, use the store switcher at the top left (e.g., "All stores (241)")

2. In the left sidebar, go to **Customers > Ratings & reviews**. You'll see a list of recent reviews with star ratings, customer tags, and comments. Each review shows a red **"Respond"** button.

### Weekly Reply Process (Ops Analyst)

**When:** Every Monday (or the designated weekly reply day)
**Who:** Ops Analyst assigned to the client
**Time estimate:** 15-30 minutes per client depending on review volume

#### Step-by-Step

1. **Open the feedback page** for each assigned client location

2. **Filter to unreplied reviews** (if filter is available) or scroll through and identify reviews without a response

3. **For each unreplied review:**
   a. Read the review text and note the star rating
   b. Select the appropriate template from the reply-templates reference (match by star rating and context)
   c. Personalize the template:
      - Insert the customer's first name if visible
      - Reference any specific dish or issue they mentioned
      - Swap in the brand name and "DoorDash" as the platform
   d. Paste the personalized reply into the Message field (300 character limit)
   e. **Apply the $5 credit:**
      - Below the message field, find the **Discount** section
      - Select the **$5** radio button (other options: $10, $15, Other)
      - Confirm $5 is selected before clicking Send
   f. Click the red **Send** button

4. **Log completion:**
   - Post in the client's internal Slack channel (#int-{client}): "Reviews replied, {X} total, {Y} with credits applied. Week of {date}."
   - If any reviews were flagged (abusive, suspected fraud, escalation-worthy), tag the GM in the same message

5. **Escalation triggers** (tag GM before replying):
   - Review mentions health/safety issue (food poisoning, allergens, foreign objects)
   - Review contains threats or harassment
   - Review mentions legal action
   - Suspected fake/competitor review
   - Review calls out a specific employee by name

### Tips for Speed
- Keep the reply-templates doc open in a second tab
- Copy the base template, then customize the bracketed fields
- For reviews with no text (just a "Liked" or "Loved" tag), use the template verbatim (just swap brand name)
- Batch by star rating: do all 5-stars first (fastest), then work down to 1-stars (need more thought)
- The **Template** dropdown at the top of the reply modal has DoorDash's pre-built templates. Ignore these and paste from our custom templates instead.

### Reply Modal Layout
When you click the red **Respond** button on a review, a modal opens with:
1. **Template** dropdown (top) - select "None" or a saved template
2. **Message** field - 300 character limit, required
3. **Discount** section - radio buttons: $5 / $10 / $15 / Other
4. **Send** button (bottom right, red)

Note: Responses are private, visible only to you and the customer. The customer cannot reply back.

### Common DoorDash Portal Quirks
- The reply field has a **300 character limit**. All templates must fit within this.
- You have **7 days** to respond to a review. After that, the Respond button disappears.
- Credits may not be available for all account types. If the Discount section isn't showing, escalate to the GM who can check with their DoorDash rep.
- The portal can be slow. Give pages a few seconds to load fully before clicking.
- Reviews show customer order history (e.g., "New customer", "3 orders") which can help personalize replies.
