# Platform-Specific Guides

## Uber Eats: Auto-Reply Configuration

Uber Eats supports automated review replies through the merchant portal. This means the $5 credit and thank-you message can be configured once and applied automatically to all incoming reviews.

### Setup Steps

1. Navigate to the Uber Eats Merchant Manager for the specific store
   - URL pattern: `https://merchants.ubereats.com/manager/home/{store_uuid}/feedback/reviews`
   - Each location has its own UUID. The GM or account owner provides this.

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
Each store location needs its own auto-reply configured. For multi-location clients, this is a one-time setup task per location. Track completion in the client's onboarding tasks or a dedicated checklist.

### Limitations
- Uber Eats auto-reply sends the same message regardless of star rating
- No conditional logic (can't send different messages for 1-star vs 5-star)
- The $5 promo credit feature availability may vary by market or account tier
- If the client wants personalized replies to negative reviews, those must be done manually on top of the auto-reply (auto-reply fires first, manual reply can follow)

---

## DoorDash: Manual Reply Process

DoorDash does not support auto-reply for reviews. Every reply must be entered manually through the Merchant Portal. The $5 credit is applied by selecting a promo option during the reply flow.

### Access

1. Navigate to the DoorDash Merchant Portal feedback page
   - URL pattern: `https://www.doordash.com/merchant/feedback?business_id={business_id}`
   - Each location has its own business_id. The GM or account owner provides this.

2. You'll see a list of recent reviews with star ratings and any customer comments

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
   d. Paste the personalized reply into the response field
   e. **Apply the $5 credit:**
      - During the reply flow, DoorDash shows an option to include a promo/credit
      - Select the $5 off next order option
      - Confirm the credit is attached before submitting
   f. Submit the reply

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
- For 5-star reviews with no text, use Template 5A verbatim (just swap brand name)
- Batch by star rating: do all 5-stars first (fastest), then work down to 1-stars (need more thought)

### Common DoorDash Portal Quirks
- The reply field sometimes has a character limit (varies). Keep replies under 500 characters to be safe.
- Credits may not be available for all account types. If the promo option isn't showing, escalate to the GM who can check with their DoorDash rep.
- Some older reviews (30+ days) may not allow replies. Focus on the most recent week's reviews.
- The portal can be slow. Give pages a few seconds to load fully before clicking.
