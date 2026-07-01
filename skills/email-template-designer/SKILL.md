---
name: email-template-designer
description: Design high-fidelity email marketing templates for Spice restaurant clients, pulling brand context from Notion and outputting Figma-importable HTML. Trigger on "design email for [client]", "email template for [client]", "create email for [client]", "promo email for [client]", "retention email for [client]", "win-back email for [client]", "BOGO email", "seasonal email", "loyalty email", "grand opening email", "new menu item email", "LTO email", or any request to design, create, or draft a visual email template for a restaurant client. Also trigger when the user says "email campaign creative for [client]", "design the email for this campaign", or references building email visuals/designs for any client.
---

# Email Template Designer

Design production-quality email marketing templates for Spice Digital restaurant clients. Pulls brand context from Notion, generates A/B variant HTML emails with platform-specific CTAs, and outputs files importable into Figma.

## HARD RULE: No Design Without Brand Context

**DO NOT generate any HTML, copy, or design output until you have completed the brand context pull from Notion.** This is not optional. A template without real brand data is useless — it produces generic output that the designer has to rebuild from scratch, which defeats the entire purpose of this skill.

The sequence is always: **Brand first. Campaign details second. Design third.** If brand data is missing or incomplete in Notion, say so and ask the operator what to do — do not fill in defaults or guess colors/fonts.

## Who Uses This

Retention Specialist + Designer, running 5-10 email designs per week across the client roster.

## What This Skill Produces

For every campaign, the skill outputs:

1. **Variant A HTML** (600px desktop) — primary visual hierarchy
2. **Variant B HTML** (600px desktop) — alternative visual hierarchy
3. **Mobile Preview HTML** (320px stacked) — for mobile QA
4. **Subject line options** (3) + preview text options (2)
5. **Hero + secondary image direction** with suggested assets from client library
6. **Platform-specific CTAs** with UTM tracking structure

## How It Works

1. **REQUIRED: Pull client brand context + asset library + past performance from Notion**
2. Clarify campaign details with the operator
3. Select layout architecture (A/B/C/D) and generate two HTML variants
4. Save HTML files (Figma-importable via html.to.design plugin)
5. Log the work to Campaign Planning DB with performance tracking fields

---

## Step 1: Pull Client Brand Context from Notion (MANDATORY)

Before designing anything, search Notion for the client's brand assets, existing photography, and past email performance. **You must complete this step and confirm the brand brief with the operator before writing a single line of HTML.**

### Where to Look

Every client has a **Client Portal** page in the "Clients" database. Inside each portal:

| Section | What's There | How to Find |
|---------|-------------|-------------|
| **Client Wiki** | Brand colors, fonts, tone of voice, logos, platform credentials | Inline database inside the portal page |
| **Creative Assets / Asset Library** | Logos, hero images, food photography, brand kit files | Inline database labeled "Asset Library" or "Creative Assets" |
| **Documents** | Brand books (PDF), style guides, audit decks | Inline database labeled "Document Hub" |
| **Campaign Planner** | Active/past campaigns + performance data | Inline database with Campaign Planning data |

### Search Sequence (12 steps)

```
BRAND CONTEXT:
1.  notion-search: query="[CLIENT NAME]" → find the Client Portal page
2.  notion-fetch: id=[portal page ID] → get portal structure + Service Details
3.  From portal content, find the Client Wiki data-source-url (collection://...)
4.  notion-fetch: id=[Client Wiki data-source-url] → get brand info entries
5.  notion-search: query="[CLIENT NAME] brand" OR "style guide" OR "brand book" → find brand docs
6.  notion-search: query="[CLIENT NAME] hero image review" → find photography direction
7.  notion-fetch: any brand book, style guide, or hero image review pages found

ASSET LIBRARY (see references/asset-suggestions.md):
8.  notion-fetch: Creative Assets / Asset Library database from portal
    → Extract all entries, note filenames, tags, URLs
9.  For each Campaign Planner entry from past 90 days:
    → Check for attached files/media (note recently used images to avoid reuse)
10. If hero image review exists: extract specific photo references (filenames, folders)

PAST PERFORMANCE (see references/performance-tracking.md):
11. notion-search: query="[CLIENT NAME] campaign" in Campaign Planning DB
    → Pull top 3 most recent campaigns, check Winner + Notes fields
12. Detect patterns: layout preference, price sensitivity, subject line style, CTA language
```

### What to Extract

Build a brand brief from what you find. Every field below must be filled before you proceed to design. If you can't find a value, explicitly note it as "NOT FOUND" in the brief.

- **Colors**: Primary, secondary, accent (hex codes). Look in brand books, hero image reviews, Client Wiki.
- **Typography**: Brand fonts + fallbacks. Check brand books and Figma links.
- **Tone / Voice**: How the brand speaks. Check Client Wiki, brand books, review reply templates.
- **Logo treatment**: Wordmark style (lowercase? uppercase? icon?), placement pattern, color variants.
- **Food photography style**: Pull from hero image reviews (compositions, color analysis, direction).
- **Brand personality**: Mission, positioning, differentiators. Service Details field has strategic context.
- **Platform context**: Which platforms (UE, DD, GH), location count, audience, priority goals.
- **Price positioning**: Some brands lead with price (Everytable's $8-10). Others never mention it.
- **Competitive context**: Hero image reviews include competitive analysis for visual differentiation.

### Present the Brand Brief Before Designing

After pulling all the data, present a combined brand + assets + performance brief:

```
BRAND BRIEF: [Client Name]
Colors: [primary hex] / [secondary hex] / [accent hex]
Fonts: [brand font] (fallback: [fallback])
Voice: [2-3 word description]
Photo style: [description from hero reviews]
Logo: [treatment description]
Price positioning: [visible/hidden/contextual]
Platforms: [UE/DD/GH] | [X locations]

AVAILABLE ASSETS:
Hero candidates: [X images found] — top match: [filename, source]
Secondary candidates: [X images found] — top match: [filename, source]
Recently used (avoid): [list]
Missing: [what's needed but not in library]

PAST PERFORMANCE (last 3 emails):
1. [Date] - [Type] - Layout [X] - Open: [Y%] - Click: [Z%] - Winner: [A/B]
2. [Date] - [Type] - Layout [X] - Open: [Y%] - Click: [Z%]
3. [Date] - [Type] - Layout [X] - Open: [Y%] - Click: [Z%]
Patterns: [detected patterns or "No past data — this is the baseline"]

Anything I'm missing or getting wrong?
```

Only proceed to Step 2 after the operator confirms or corrects this brief.

### If Brand Data Is Sparse

For new clients or those without a brand library:
1. Tell the operator what's missing. Don't silently fill gaps.
2. Ask if they have a website, Instagram, or any existing email to reference.
3. Use the Chrome MCP to pull visual style from their website if available.
4. Check if they've gone through the Brand Library Review process (SOP page ID: 295d3ff0-18e7-80d3-9189-fe38e60680d5).
5. As a last resort, reference Spice Brand Guidelines for AI Asset Generation (page ID: 306d3ff0-18e7-8103-86ec-f69a373553b8) — but note these are Spice's guidelines, not the client's.

---

## Step 2: Clarify Campaign Details

Use AskUserQuestion to confirm:

**Question 1 — Email Type:**
- New Menu Item / LTO Launch
- BOGO / Promotional Offer
- Win-Back / Re-Engagement
- Seasonal / Holiday Campaign
- Loyalty / Rewards Nudge
- Grand Opening / New Location

**Question 2 — Key Details:**
- What specifically is being promoted? (dish name, offer details, occasion)
- Platform(s): Uber Eats, DoorDash, Grubhub, direct ordering?
- Target audience: all customers, lapsed, new, specific segment?
- Any deadline or expiration date?
- Promo code? (if yes, include in CTA section)

**Question 3 — Layout Override (optional):**
- Default layout is auto-selected based on email type (see matrix below)
- Operator can override: "Use Layout D for this one" or "Try the editorial approach"
- If past performance shows a layout preference for this client, note it

### Layout Selection Matrix

| Email Type | Default Layout | When to Override |
|-----------|---------------|-----------------|
| LTO Launch (single item) | A: Hero Impact | D: Narrative if there's a chef/ingredient story |
| LTO Launch (multi-item) | C: Multi-Product Grid | A: Hero Impact if one item is clearly the star |
| BOGO / Promo | C: Multi-Product Grid | A: Hero Impact for simple single-item deals |
| Win-Back | B: Editorial | A: Hero Impact if pairing with new item reveal |
| Seasonal | A: Hero Impact | C: Multi-Product Grid for full seasonal menu |
| Loyalty Nudge | B: Editorial | C: Multi-Product Grid if showing redeemable items |
| Grand Opening | A: Hero Impact | D: Narrative for community/neighborhood story |

Read `references/prompt-templates.md` for the full prompt formula per email type.
Read `references/layout-architectures.md` for the full structural specs per layout.

---

## Step 3: Generate the HTML Email Templates

Build **three HTML files** per campaign:

### 3a: Select Layout Architecture

Based on the email type and layout matrix (or operator override), select the primary layout from `references/layout-architectures.md`:
- **Layout A: Hero Impact** — image-dominant, single hero, bold headline
- **Layout B: Editorial** — text-forward, feels like a letter, minimal imagery
- **Layout C: Multi-Product Grid** — distributed, 2-column product layout
- **Layout D: Narrative** — sequential storytelling with alternating blocks

### 3b: Generate Variant A (Primary Hierarchy)

Build the first HTML file using the selected layout's primary visual strategy.

### 3c: Generate Variant B (Alternative Hierarchy)

Build the second HTML file using the same layout but with the alternative hierarchy:
- Layout A: Variant B hides price until body; hero is pure food aspiration
- Layout B: Variant B adds a small centered image above the headline
- Layout C: Variant B removes per-item prices, uses single "starting at $X"
- Layout D: Variant B leads with product, then tells the story

**What changes**: Layout structure, headline approach, CTA copy
**What stays the same**: Brand colors, fonts, voice, core offer details, image direction, footer

### 3d: Generate Mobile Preview

Build a 320px stacked version that applies mobile adaptation rules:
- Two-column blocks stack to single column
- Headlines drop ~6px in font size
- CTA buttons go full-width (48px min tap target)
- Side padding reduces from 40px to 20px
- Product grids stack to one item per row

### Design Principles (from Spice Brand Guidelines)

- **Type-led, not image-led**: Bold headlines carry the design
- **Restrained palette**: Client's brand colors + one accent, never busy
- **Let data breathe**: Generous whitespace, no decoration for decoration's sake
- **Editorial over corporate**: Sharp, confident, opinionated
- **Bold claims, simple proof**: Short headlines, one line of evidence

### HTML Requirements

- **Self-contained**: All styles inline (no external CSS). `@media` only in mobile file.
- **Email-safe**: Table-based layout for email client compatibility
- **600px wide** (desktop) / **320px wide** (mobile preview)
- **Web fonts with fallbacks**: Brand font + system font stack
- **Image placeholders with asset suggestions**: Colored divs with direction + suggested files from the client's asset library (see `references/asset-suggestions.md`)
- **Platform-specific CTAs with UTM tracking**: Individual buttons per platform with tracking parameters (see `references/platform-ctas.md`)

### CTA Generation

Pull platform info from the brand context (Step 1) and generate:
- Platform-specific buttons (not generic "Order Now")
- UTM structure: `utm_source=email&utm_medium=retention&utm_campaign=[client]-[type]-[monthyear]&utm_content=[variant]-[platform]`
- Promo code callout block above CTAs (if applicable)
- Platform availability line below CTAs

See `references/platform-ctas.md` for full HTML snippets and priority ordering.

### Output Files

Save to the workspace output folder:
- `[ClientName] - [EmailType] - [Date] - Variant A.html`
- `[ClientName] - [EmailType] - [Date] - Variant B.html`
- `[ClientName] - [EmailType] - [Date] - Mobile.html`

Also provide in the response:
- 3 subject line options
- 2 preview text options
- Hero image direction + suggested asset from library
- Secondary image direction + suggested asset from library
- Platform CTAs generated (which platforms, UTM structure)

---

## Step 4: Figma Import

The HTML files are designed to import cleanly into Figma via the html.to.design plugin.

### Recommended Workflow: html.to.design Plugin

1. Open the Variant A HTML in Chrome (double-click the file)
2. In Figma, create a new frame (600px wide)
3. Run html.to.design plugin (Right-click > Plugins > html.to.design)
4. Choose "Import from URL" or "Import from Code"
5. The plugin converts HTML to editable Figma layers
6. Repeat for Variant B

### After Figma Import
- Replace `[IMAGE]` placeholder divs with actual food photography (use the suggested assets)
- Apply exact brand fonts (Figma has font access the HTML may not)
- Adjust spacing/sizing to pixel-perfect
- Review mobile preview HTML for stacking behavior
- Add to the client's Brand Library Figma file if one exists
- Export final version for ESP upload

### Alternative: Figma MCP Direct Push (Experimental)
If the Figma MCP is connected, offer to push the design structure directly using `generate-design-structured`. This produces wireframe-quality output — useful for rapid layout exploration but not production-ready. HTML import is recommended for final templates.

See `references/figma-import-guide.md` for detailed import instructions and post-import checklist.

---

## Step 5: Log the Work

After the email is designed and approved, log to the **Campaign Planning DB** in Notion:

### Required Fields
- Client name
- Email type (LTO Launch / BOGO / Win-Back / Seasonal / Loyalty / Grand Opening)
- Layout used (A: Hero Impact / B: Editorial / C: Multi-Product Grid / D: Narrative)
- Variant sent (A or B)
- Subject line sent
- Platforms targeted
- Date sent
- HTML source file (attached)
- Screenshot (embedded)

### Performance Fields (filled 48-72 hours after send)
- Open rate (%)
- Click rate (%)
- Conversion rate (if trackable)
- Revenue attributed (if trackable)
- Variant winner (A / B / Tie / N/A)
- Performance notes (specialist's judgment on what worked)

If this is a new client's first email, save the color/font/style choices to their Client Wiki for next time.

See `references/performance-tracking.md` for full field specs and quarterly review process.

---

## Iteration Guidance

The first output is a strong draft, not a final. Expect 2-4 rounds:

- **Round 1**: Structure and copy review. Does the hierarchy work? Is the CTA right?
- **Round 2**: Visual refinement. Colors, spacing, image direction adjustments.
- **Round 3**: Brand alignment. Does it feel like this specific client, not generic?
- **Round 4**: Final QA. Proofread, verify offer details, check dates, confirm UTMs.

When the operator asks to iterate, make targeted edits to the HTML. Don't regenerate from scratch unless the direction is fundamentally wrong.

---

## Weekly Production Cadence

For the Retention Specialist + Designer doing 5-10 emails/week:

- **Monday**: Pull briefs from Campaign Planning DB, pre-fill brand context + past performance for each client. Batch the Notion searches.
- **Tue-Wed**: Run through this skill per email. Batch by client (easier to stay in brand voice). Target 2-3 emails per sitting. Each produces 2 variants + mobile preview.
- **Thursday**: QA + client approval. Share HTML previews or Figma links. Designer swaps placeholders with real photos.
- **Friday**: Export approved emails, log to Campaign Planning DB with screenshots. Tag variant winners when ESP data comes in from previous week's sends.

---

## Reference Files

| File | What It Contains |
|------|-----------------|
| `references/prompt-templates.md` | 6 prompt formulas (LTO, BOGO, Win-Back, Seasonal, Loyalty, Grand Opening) + generation rules |
| `references/layout-architectures.md` | 4 layout structures (Hero Impact, Editorial, Multi-Product Grid, Narrative) + A/B variant strategies + mobile adaptation rules |
| `references/platform-ctas.md` | Platform-specific CTA HTML, UTM structure, promo code handling, button priority order |
| `references/performance-tracking.md` | What to log, what to pull, pattern detection, quarterly review process |
| `references/asset-suggestions.md` | How to search for and surface existing client photography, placeholder enhancement format |
| `references/figma-import-guide.md` | html.to.design workflow, post-import checklist, file naming conventions |
