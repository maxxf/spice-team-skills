# Email Prompt Templates for Restaurant Clients

These are the internal prompt formulas Claude uses when generating email templates. Each template maps to an email type. The operator fills in the bracketed variables; Claude uses them to generate the HTML.

---

## Universal Variables (fill these for every email)

| Variable | Description |
|----------|-------------|
| RESTAURANT NAME | Client brand name as it appears on delivery platforms |
| BRAND COLORS | Primary hex, secondary hex, accent hex (from Notion Client Wiki) |
| BRAND FONTS | Primary font + fallback (from Notion Client Wiki or brand book) |
| BRAND PERSONALITY | 2-3 adjectives: playful, premium, community-driven, irreverent, minimal, bold, etc. |
| PLATFORM | Uber Eats, DoorDash, Grubhub, or direct ordering |
| AUDIENCE | Who specifically: regulars, lapsed, new, families, late-night, health-conscious, etc. |
| CTA | The action: Order Now, Use Code X, Find a Location, Claim Offer |

---

## Template 1: New Menu Item / LTO Launch

**When**: Client launches a new dish, limited-time offer, or seasonal menu addition.

### Prompt Formula

```
Design a promotional email template for [RESTAURANT NAME] launching [MENU ITEM / LTO NAME].

Brand context:
- Colors: [PRIMARY HEX], [SECONDARY HEX], accent [ACCENT HEX]
- Fonts: [BRAND FONT] (fallback: [FALLBACK FONT])
- Personality: [BRAND PERSONALITY]

Tone: [craveable, bold, seasonal / vibrant, playful, indulgent / etc.]

Include:
- 3 subject line options (under 50 chars, food-forward, urgency-driven)
- 2 preview text options (complement subject, hint at the offer)
- Hero image direction
- 1 strong headline
- Concise body copy (under 80 words)
- Secondary image direction
- 1 clear CTA

Structure:
- Open with a bold statement introducing [MENU ITEM]
- Describe it as [POSITIONING: e.g., "our most indulgent burger yet" / "plant-powered comfort food" / "a chef-crafted seasonal exclusive"]
- Highlight these benefits: [BENEFIT 1: e.g., made with X ingredient], [BENEFIT 2: e.g., available for delivery], [BENEFIT 3: e.g., pairs with Y]
- Emphasize the visual/food appeal: [STYLE: e.g., dripping cheese pull, vibrant bowl colors, rustic plating on wood board]
- Make it feel ideal for [AUDIENCE]
- Hero image direction: [SUBJECT: the dish / COMPOSITION: overhead flat lay or 45-degree hero angle / MOOD: warm, appetizing / BACKGROUND: branded or neutral]
- Secondary image direction: [ACTION: someone taking first bite / DETAIL: close-up of key ingredient / STYLING: in branded packaging / SETTING: delivery at doorstep]
- End with a strong CTA that drives the reader to [CTA ACTION]

Direction:
- Keep it punchy, craveable, and visually driven
- Avoid generic restaurant copy or corporate food language
- Make it feel like a campaign launch, not a menu update email
- Match the brand voice of [BRAND PERSONALITY]
```

---

## Template 2: BOGO / Promotional Offer

**When**: Running BOGO, BOGA, percentage-off, free delivery, or any discount/incentive campaign.

### Prompt Formula

```
Design a promotional email template for [RESTAURANT NAME] running [OFFER: e.g., Buy One Get One Free on all bowls / 25% off first orders / Free delivery this weekend].

Brand context:
- Colors: [PRIMARY HEX], [SECONDARY HEX], accent [ACCENT HEX]
- Fonts: [BRAND FONT] (fallback: [FALLBACK FONT])
- Personality: [BRAND PERSONALITY]

Tone: [urgent, exciting, value-packed / casual, fun, deal-savvy / etc.]

Include:
- 3 subject line options (lead with the deal, create urgency)
- 2 preview text options (reinforce the value, add deadline if applicable)
- Hero image direction
- 1 strong headline
- Concise body copy (under 60 words — let the offer speak)
- Secondary image direction
- 1 clear CTA

Structure:
- Open with the offer front and center — no buildup needed
- Position it as [POSITIONING: e.g., "our way of saying thanks" / "your excuse to try everything" / "weekend sorted"]
- Highlight: [WHAT they get], [WHERE it's available: platform + locations], [WHEN it expires]
- Emphasize the visual appeal: [STYLE: e.g., two bowls side by side, stacked burgers, colorful spread]
- Hero image: [SUBJECT: the offer items together / COMPOSITION: symmetrical, abundant / MOOD: vibrant, generous / BACKGROUND: clean with brand color pop]
- Secondary image: [the platform order screen / someone unboxing delivery / lifestyle shot of sharing the meal]
- End with CTA to [ORDER NOW / USE CODE / TAP TO CLAIM]

Direction:
- Lead with value, not brand story
- Deadline urgency is your friend — use it
- Avoid walls of terms and conditions in the body (put T&C in fine print footer)
- Make the reader feel like they'd be foolish to miss this
```

---

## Template 3: Win-Back / Re-Engagement

**When**: Targeting customers who haven't ordered in 30-60+ days. Tone shifts from promotional to personal.

### Prompt Formula

```
Design a re-engagement email template for [RESTAURANT NAME] targeting customers who haven't ordered in [TIMEFRAME: 30/60/90 days].

Brand context:
- Colors: [PRIMARY HEX], [SECONDARY HEX], accent [ACCENT HEX]
- Fonts: [BRAND FONT] (fallback: [FALLBACK FONT])
- Personality: [BRAND PERSONALITY]

Tone: [warm, personal, inviting / playful, no-pressure / nostalgic, tempting]

Include:
- 3 subject line options (personal, curiosity-driven, avoid "we miss you" cliches)
- 2 preview text options (hint at what's new or what they're missing)
- Hero image direction
- 1 strong headline
- Concise body copy (under 70 words)
- Secondary image direction
- 1 clear CTA
- Optional: incentive line (e.g., "Here's $5 on us")

Structure:
- Open with acknowledgment, not guilt ("It's been a minute" not "Where'd you go?")
- Show what's new since they last ordered: [NEW ITEMS / MENU CHANGES / NEW LOCATIONS / SEASONAL ADDITIONS]
- Offer a reason to come back: [INCENTIVE: discount code / free item / free delivery] or [EMOTIONAL HOOK: "your favorite bowl is still here"]
- Make it feel like a friend checking in, not a brand chasing a sale
- Hero image: [SUBJECT: their most-ordered category or signature dish / COMPOSITION: intimate, close-up / MOOD: warm, nostalgic / BACKGROUND: soft, muted]
- Secondary image: [new menu additions / fresh seasonal items / the kitchen team]
- End with CTA to [ORDER YOUR FAVORITE / COME BACK FOR $X OFF / SEE WHAT'S NEW]

Direction:
- This is a conversation, not a billboard
- Skip the "we miss you" subject lines — everyone does those
- If using an incentive, don't bury it — put it in the subject or headline
- Shorter is better here — respect that they've been away for a reason
```

---

## Template 4: Seasonal / Holiday Campaign

**When**: Holidays, seasonal menu drops, cultural moments (Super Bowl, Valentine's, Cinco de Mayo, etc.)

### Prompt Formula

```
Design a seasonal campaign email template for [RESTAURANT NAME] for [OCCASION: e.g., Super Bowl Sunday / Valentine's Day / Summer Menu Launch / Cinco de Mayo].

Brand context:
- Colors: [PRIMARY HEX], [SECONDARY HEX], accent [ACCENT HEX]
- Fonts: [BRAND FONT] (fallback: [FALLBACK FONT])
- Personality: [BRAND PERSONALITY]

Tone: [festive, bold, communal / romantic, indulgent / celebratory, playful]

Include:
- 3 subject line options (tie to the occasion, not generic holiday greetings)
- 2 preview text options
- Hero image direction
- 1 strong headline
- Concise body copy (under 80 words)
- Secondary image direction
- 1 clear CTA

Structure:
- Open by connecting the food to the moment ("Game day needs a lineup" not "Happy Super Bowl!")
- Position the offering as [POSITIONING: e.g., "the catering order that wins the party" / "date night, delivered" / "summer on a plate"]
- Highlight: [FEATURED ITEMS], [SPECIAL PRICING if any], [ORDERING DEADLINE for catering/advance orders]
- Emphasize the occasion visually: [STYLE: e.g., party spread, candlelit dinner for two, bright summer colors]
- Hero image: [SUBJECT: occasion-appropriate food spread / COMPOSITION: abundant, lifestyle / MOOD: matches the holiday energy / BACKGROUND: contextual setting]
- Secondary image: [detail shot of hero dish / group enjoying the food / packaging ready for the occasion]
- End with CTA to [ORDER FOR GAME DAY / BOOK YOUR TABLE / ORDER BY FRIDAY]

Direction:
- The occasion is the hook, the food is the hero
- Don't over-decorate with holiday clip art vibes — keep it brand-aligned
- If there's a deadline (catering cutoff, pre-order window), make it prominent
- Think about what the customer is actually doing that day and meet them there
```

---

## Template 5: Loyalty / Rewards Nudge

**When**: Driving repeat orders through loyalty programs, points reminders, milestone rewards.

### Prompt Formula

```
Design a loyalty/rewards email template for [RESTAURANT NAME] nudging customers to [ACTION: redeem points / hit their next reward / join the loyalty program / use their birthday reward].

Brand context:
- Colors: [PRIMARY HEX], [SECONDARY HEX], accent [ACCENT HEX]
- Fonts: [BRAND FONT] (fallback: [FALLBACK FONT])
- Personality: [BRAND PERSONALITY]

Tone: [appreciative, motivating, exclusive / playful, rewarding / warm, VIP]

Include:
- 3 subject line options (make them feel special, hint at the reward)
- 2 preview text options
- Hero image direction
- 1 strong headline
- Concise body copy (under 60 words)
- Secondary image direction
- 1 clear CTA

Structure:
- Open with recognition ("You've earned it" / "X points away from something good")
- Show them exactly where they stand: [POINTS BALANCE / REWARD TIER / MILESTONE]
- Make the reward tangible: [WHAT THEY GET: free entree, $10 off, exclusive item]
- Create gentle urgency if applicable: [EXPIRATION DATE / LIMITED REDEMPTION WINDOW]
- Hero image: [SUBJECT: the reward item / COMPOSITION: centered, aspirational / MOOD: premium, earned / BACKGROUND: minimal with brand accent]
- Secondary image: [progress bar graphic / the menu they can redeem on / VIP-style branding element]
- End with CTA to [REDEEM NOW / SEE YOUR REWARDS / CLAIM YOUR FREE ITEM]

Direction:
- Make them feel like insiders, not targets
- Specificity wins — "You're 2 orders from a free burrito" beats "Earn rewards!"
- Keep it short — loyalty emails should feel like a quick, welcome ping
```

---

## Template 6: Grand Opening / New Location

**When**: Client opens a new location or launches on a new delivery platform in a market.

### Prompt Formula

```
Design a grand opening email template for [RESTAURANT NAME] launching [NEW LOCATION / now available on PLATFORM in MARKET].

Brand context:
- Colors: [PRIMARY HEX], [SECONDARY HEX], accent [ACCENT HEX]
- Fonts: [BRAND FONT] (fallback: [FALLBACK FONT])
- Personality: [BRAND PERSONALITY]

Tone: [exciting, community-driven, celebratory / premium, arrival-event / neighborhood-friendly, accessible]

Include:
- 3 subject line options (location-specific, excitement-driven)
- 2 preview text options
- Hero image direction
- 1 strong headline
- Concise body copy (under 80 words)
- Secondary image direction
- 1 clear CTA

Structure:
- Open with the arrival announcement ("Now in [NEIGHBORHOOD]" / "[CITY], we're here")
- Position it as [POSITIONING: e.g., "your new go-to for X" / "finally, Y in your zip code"]
- Highlight: [WHAT makes this location/launch special], [OPENING OFFER if any], [DELIVERY RADIUS or neighborhoods served]
- Emphasize local connection: [LOCAL DETAIL: neighborhood name, nearby landmark, community angle]
- Hero image: [SUBJECT: storefront or signature dish / COMPOSITION: wide, inviting / MOOD: fresh, new / BACKGROUND: the actual location or neighborhood context]
- Secondary image: [interior shot / the team / delivery arriving in the neighborhood]
- End with CTA to [ORDER NOW / EXPLORE THE MENU / GET OPENING-DAY DEAL]

Direction:
- Local specificity is everything — "Now in Silver Lake" beats "Now open"
- If there's an opening promo, lead with it in the subject line
- Make it feel like an event, not an announcement
```

---

## Layout Assignment by Template

Each prompt template has a default layout architecture. See `references/layout-architectures.md` for full structural specs.

| Template | Default Layout | Alt Layout |
|----------|---------------|------------|
| 1: LTO Launch (single item) | A: Hero Impact | D: Narrative (if chef/ingredient story) |
| 1: LTO Launch (multi-item) | C: Multi-Product Grid | A: Hero Impact (if one item is the star) |
| 2: BOGO / Promo | C: Multi-Product Grid | A: Hero Impact (simple single-item deal) |
| 3: Win-Back | B: Editorial | A: Hero Impact (if pairing with new item reveal) |
| 4: Seasonal | A: Hero Impact | C: Multi-Product Grid (full seasonal menu) |
| 5: Loyalty Nudge | B: Editorial | C: Multi-Product Grid (showing redeemable items) |
| 6: Grand Opening | A: Hero Impact | D: Narrative (community/neighborhood story) |

## A/B Variant Generation

For every email, generate **two HTML files** using the same brand system but different visual strategies. See `references/layout-architectures.md` for variant strategy by layout.

File naming:
- `[ClientName] - [EmailType] - [Date] - Variant A.html`
- `[ClientName] - [EmailType] - [Date] - Variant B.html`
- `[ClientName] - [EmailType] - [Date] - Mobile.html` (320px stacked preview)

## Platform-Specific CTAs

Every email must include platform-specific CTA buttons with UTM tracking. See `references/platform-ctas.md` for full specs.

- Pull platform info from Notion Service Details during brand context step
- Generate individual buttons per platform (not generic "Order Now")
- Include UTM structure: `utm_source=email&utm_medium=retention&utm_campaign=[slug]&utm_content=[variant]-[platform]`
- If promo code exists, place code callout block above CTA buttons

## Image Placeholders with Asset Suggestions

When generating placeholders, include suggested assets from the client's library. See `references/asset-suggestions.md` for the full search sequence.

```html
<td style="background-color: [BRAND_LIGHT_COLOR]; padding: 40px; text-align: center;">
  <div style="color: [BRAND_TEXT_COLOR]; font-size: 14px; font-style: italic;">
    [IMAGE: Overhead shot of the new summer bowl with avocado, grilled chicken, 
    and cilantro-lime rice. Warm natural lighting. White marble surface.
    SUGGESTED: "Summer Bowl Hero-3.jpg" from Asset Library (uploaded Mar 2026).
    Crop to center bowl, maintain warm tones.]
  </div>
</td>
```

## HTML Generation Rules

When Claude generates the actual HTML template from these prompts:

1. **Width**: 600px (desktop), 320px (mobile preview)
2. **Layout**: Table-based (email client compatibility). Structure from `layout-architectures.md`
3. **Styles**: All inline (no external CSS). `@media` queries only in the mobile preview file
4. **Images**: Colored placeholder divs with descriptive text + asset suggestions from the client's library
5. **Fonts**: Web font reference + system fallback stack
6. **Colors**: Pull from client brand context, never guess
7. **CTAs**: Platform-specific buttons with UTM tracking (see `platform-ctas.md`)
8. **Footer**: Include unsubscribe placeholder, brand address, social icon placeholders
9. **Preheader**: Hidden text for inbox preview
10. **Mobile**: Separate 320px preview file. Desktop file uses simple single-column structure that degrades gracefully
11. **Variants**: Always generate two HTML files (Variant A + Variant B) per campaign
