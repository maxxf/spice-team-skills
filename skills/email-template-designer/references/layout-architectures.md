# Email Layout Architectures

Four distinct visual structures mapped to email types. Each architecture has a different visual hierarchy, pacing, and emotional register. The operator can override, but these are the defaults.

---

## Layout A: Hero Impact

**Default for**: LTO Launch, Grand Opening, Seasonal Campaign

**Visual hierarchy**: Image-dominant. Big hero, bold headline, short body, CTA.

**When to use**: When there's a single hero item or moment to sell. The visual does the heavy lifting.

```
[PREHEADER]
[BRAND STRIPE - 6px colored bar]
[HEADER - logo left, context label right]
[HERO IMAGE - full-width, 280-320px tall, brand-colored background]
[PRICE/OFFER BADGE - pill-shaped, accent color, overlaps hero bottom]
[HEADLINE - 28-32px, bold, 1-2 lines max]
[BODY - 15-16px, 2-3 sentences max]
[PRODUCT CARDS - if multiple items, card layout with thumbnails + price]
[CTA BUTTON - brand primary, generous padding]
[PLATFORM LINE - "Available on UE, DD & GH"]
[SECONDARY IMAGE - full-width, complementary shot]
[MISSION STRIP - accent-colored bar with brand proof points]
[FOOTER - dark background, logo, socials, legal]
```

**Design notes**:
- Hero section uses brand primary as background, image placeholder centered
- Product cards only appear when 2+ items; skip for single-item promos
- Mission strip reinforces brand positioning (locations, price, values)
- Total height target: 1400-1600px (scrollable but not endless)

---

## Layout B: Editorial / Text-Forward

**Default for**: Win-Back, Loyalty Nudge

**Visual hierarchy**: Copy-dominant. Headline carries the design. Images support, not lead.

**When to use**: When the message is personal, the tone is conversational, or the "product" is a feeling/relationship, not a dish.

```
[PREHEADER]
[HEADER - centered logo, minimal, no stripe]
[SPACER - 40px breathing room]
[HEADLINE - 32-40px, centered, 1 line, brand color or near-black]
[SUBHEAD - 16px, muted color, 1 line beneath headline]
[BODY - 16px, centered, 3-5 short paragraphs with generous line-height]
[INLINE ACCENT - colored divider or small brand element between body and CTA]
[CTA BUTTON - centered, secondary color or outlined style]
[SPACER - 32px]
[SINGLE IMAGE - optional, small (200px wide), centered, rounded corners]
[CAPTION - 12px, muted, image context]
[FOOTER - light background, softer treatment than Layout A]
```

**Design notes**:
- No hero image section. The headline IS the hero.
- Body copy is the star. Give it room. Line-height 1.7+.
- Max 2 colors (brand primary + near-black text). Restrained.
- Image is optional and small. Think editorial magazine, not billboard.
- Feels like a letter, not an ad.
- Total height target: 900-1100px (deliberately short)

---

## Layout C: Multi-Product Grid

**Default for**: BOGO/Promotional (multi-item), Seasonal (menu showcase)

**Visual hierarchy**: Distributed. No single hero. Multiple items compete equally.

**When to use**: When the campaign features 3+ items, a collection, or a menu category. The variety IS the message.

```
[PREHEADER]
[BRAND STRIPE]
[HEADER - logo left, context label right]
[HEADLINE - 26-30px, left-aligned, above the grid]
[INTRO LINE - 15px, 1 sentence setting up the grid]
[PRODUCT GRID - 2-column table layout]
  [ITEM 1: image placeholder (240x180) + name + price + 1-line description]
  [ITEM 2: image placeholder (240x180) + name + price + 1-line description]
  [ITEM 3: image placeholder (240x180) + name + price + 1-line description]
  [ITEM 4: image placeholder (240x180) + name + price + 1-line description]
[OFFER BANNER - full-width, accent background, deal callout if applicable]
[CTA BUTTON - centered, brand primary]
[PLATFORM BUTTONS - individual platform CTAs if multi-platform]
[FOOTER - standard]
```

**Design notes**:
- 2-column grid on desktop, stacks to 1-column on mobile
- Each grid cell is self-contained: image, name, price, one line
- Offer banner only appears if there's a deal (BOGO, %-off). Skip for pure menu showcases.
- Works well for "here's what's new this season" or "pick your BOGO pair"
- Total height target: 1200-1500px depending on item count

---

## Layout D: Narrative / Storytelling

**Default for**: Grand Opening (story angle), Brand campaigns, Special collaborations

**Visual hierarchy**: Sequential. Guides the reader through a story with alternating content blocks.

**When to use**: When there's a story to tell. A new location's neighborhood connection. A chef collaboration. A mission-driven campaign. Not for quick promos.

```
[PREHEADER]
[HEADER - minimal, logo only]
[FULL-WIDTH IMAGE - cinematic, wide-ratio (600x250), sets the scene]
[HEADLINE - 28-34px, overlapping or just below image, bold]
[STORY BLOCK 1 - text left (60%), image right (40%)]
  [Paragraph: the setup / why this matters]
  [Small image: supporting visual]
[DIVIDER - thin line or brand accent]
[STORY BLOCK 2 - image left (40%), text right (60%)]
  [Small image: the product/place/person]
  [Paragraph: the payoff / what they get]
[QUOTE OR CALLOUT - centered, larger font, brand color, from chef/founder/team]
[CTA BUTTON - centered]
[CLOSING IMAGE - wide, warm, community/lifestyle feel]
[FOOTER - standard]
```

**Design notes**:
- Alternating image/text blocks create visual rhythm and prevent scroll fatigue
- Two-column blocks use 60/40 split (not 50/50 — asymmetry is more dynamic)
- The quote/callout block is optional but powerful for brand storytelling
- This layout is longer by design. It earns the scroll with content, not just images.
- Total height target: 1600-2000px
- Use sparingly. 1-2 per month per client max. Not for routine promos.

---

## Layout Selection Matrix

| Email Type | Default Layout | Alt Layout | When to Override |
|-----------|---------------|------------|-----------------|
| LTO Launch (single item) | A: Hero Impact | D: Narrative | If there's a chef story or ingredient story worth telling |
| LTO Launch (multiple items) | C: Multi-Product Grid | A: Hero Impact | If one item is clearly the star and others are supporting |
| BOGO / Promo | C: Multi-Product Grid | A: Hero Impact | If the deal is simple (one item BOGO, not a spread) |
| Win-Back | B: Editorial | A: Hero Impact | If pairing win-back with a new menu item reveal |
| Loyalty Nudge | B: Editorial | C: Multi-Product Grid | If showing multiple items they can redeem on |
| Seasonal Campaign | A: Hero Impact | C: Multi-Product Grid | If showcasing a full seasonal menu vs. one hero dish |
| Grand Opening | A: Hero Impact | D: Narrative | If the location has a community story worth telling |

---

## A/B Variant Generation

For every email, generate **two variants** using the same brand system but different visual strategies:

### Variant Strategy by Layout

| Primary Layout | Variant A | Variant B |
|---------------|-----------|-----------|
| A: Hero Impact | Price/offer badge prominent in hero | Price hidden until body copy; hero is pure food aspiration |
| B: Editorial | Headline-led (big text, no image) | Image-led (small centered image above headline) |
| C: Multi-Product Grid | Grid with prices visible | Grid without prices, single "starting at $X" below grid |
| D: Narrative | Story-first (image → text → image → text) | Product-first (hero item → then the story context) |

### What Changes Between Variants
- **Layout structure** (the arrangement of blocks)
- **Headline approach** (benefit-led vs. product-led vs. urgency-led)
- **CTA copy** (direct action vs. curiosity-driven)

### What Stays the Same Between Variants
- Brand colors, fonts, voice
- Core offer details (price, items, dates)
- Image direction (same photos, different placement)
- Footer, legal, preheader

### File Naming
- `[ClientName] - [EmailType] - [Date] - Variant A.html`
- `[ClientName] - [EmailType] - [Date] - Variant B.html`

---

## Mobile Adaptation Rules

Every layout must degrade cleanly to 320px width. These rules apply universally:

1. **Two-column blocks** stack to single column (image on top, text below)
2. **Product grids** stack to single column (one item per row)
3. **Hero images** scale to 100% width, maintain aspect ratio
4. **Headlines** drop ~6px in font size (32px desktop → 26px mobile)
5. **Body text** stays at 16px (already mobile-optimal)
6. **CTA buttons** go full-width with minimum 48px tap target height
7. **Side padding** reduces from 40px to 20px
8. **Product card thumbnails** scale from 64px to 48px

### Mobile Preview Generation

Generate a separate `[ClientName] - [EmailType] - [Date] - Mobile.html` file that:
- Wraps the email in a 320px container
- Applies the stacking rules above
- Uses `@media` query with `max-width: 480px` breakpoint
- Adds `mso-hide: all` for Outlook-safe responsive blocks

The designer reviews both desktop (600px) and mobile (320px) before approving.
