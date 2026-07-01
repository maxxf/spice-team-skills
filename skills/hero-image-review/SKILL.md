---
name: hero-image-review
description: >
  Review and score restaurant hero images on Uber Eats, DoorDash, and Grubhub, benchmark against competitors, produce
  creative direction, render a shareable HTML comparison page, and hand off to the design team via a Campaign Planner
  ticket in Notion. Optionally produces a paste-ready brief for Claude Design (claude.ai/design) so the designer starts
  from an AI-generated visual draft. Trigger on "review hero image", "audit hero image", "grade their hero", "hero image
  analysis", "check their cover photo", "compare hero images", "hero refresh for [client]", or any request to evaluate,
  score, or improve a restaurant's delivery platform hero/banner image. Also trigger for hero image planning or A/B tests.
  Goes deeper than storefront-audit. Use this skill whenever hero images are the focus.
---

# Hero Image Review & Design Handoff

Grade a restaurant's hero images, benchmark against competitors, render a shareable HTML comparison page, document creative direction in Notion, and hand off to the design team via a Campaign Planner ticket (which auto-drops into #design-requests).

The default flow is **audit → HTML comparison page → Notion write-up → Campaign Planner ticket**. The designer executes the final assets. Optionally, the skill writes a paste-ready brief for Claude Design (claude.ai/design) so the designer starts from an AI-generated visual draft instead of a blank canvas.

## Inputs

- **Restaurant name** (required)
- **Location / delivery address** (required, for competitive discovery)
- **Platform(s)** (ask the user, see Phase 0)
- **Specific competitors** (optional, otherwise discover top 5 nearby in same cuisine)
- **Photo assets** (optional: Google Drive link, uploaded images, or screenshots from existing platform listings)
- **Brand assets** (optional: logo URL, brand colors, brand kit references — used in the HTML page and Claude Design brief)

## Phase 0: Upfront Questions

Before doing anything else, ask three questions using AskUserQuestion. These shape the entire workflow.

**Question 1:** "Which platforms need hero images for [client]?"
**Options (multiSelect: true):**
- Uber Eats
- DoorDash
- Grubhub
- All three

Each platform has different aspect ratios. A hero designed for one will crop badly on another. The audit, HTML page, and export specs all flow from this answer.

**Question 2:** "Do you have image assets for [client]?"
**Options:**
- Yes, folder of images (Drive link, etc.) — *Most common. Clients typically provide a folder of menu item photos that get composited and edited into heroes.*
- No, pull from their existing platform listings — *Screenshot their best menu item photos from UE/DD/GH and use those as source material.*
- No usable images, brief the designer to shoot fresh — *Production brief only. No source material to reference.*

**Question 3:** "What do you want to do after the review?"
**Options:**
- Review + hand off to design team (Recommended) — *Produces the audit, HTML comparison page, Notion write-up, and Campaign Planner ticket. HTML lands in the client's Cowork folder. New tickets auto-drop into #design-requests, so no separate Slack message needed. The designer gets the full creative direction with variant concepts, platform specs, and source references. This is the workhorse flow.*
- Review + HTML comparison only (share with client for approval first) — *Produces the audit and HTML comparison page as shareable client deliverables. No Notion write-up, no ticket, no Slack post. Use when the client needs to approve direction before any work starts. When they approve, come back and say "hand off [client] hero to design" to trigger the rest.*
- Full pipeline with Claude Design brief — *Same as "hand off to design" but also generates a paste-ready brief for claude.ai/design. The designer pastes the brief into Claude Design to produce AI-generated visual drafts, then exports to PPTX or Canva and finishes in their tool of choice. Brief lands in the Cowork folder and is linked from the Campaign Planner ticket.*
- Just the audit, no handoff — *Grade and competitive analysis only. Good for prospect audits or sales leverage.*

If the user has already specified platforms or shared images in their request, skip the relevant question and use what they provided.

### How the workflow branches

**"Review + hand off to design team"** (DEFAULT) → Run Phases 1-3 and Phase 5. The HTML comparison page drops into the client's Cowork folder. The Notion page captures the structured write-up. The Campaign Planner ticket auto-posts to #design-requests. Skip Phase 4.

**"Review + HTML comparison only"** → Run Phases 1-2, then produce only the HTML comparison page (Phase 3a). No Notion write-up, no ticket. The HTML is the full client-facing deliverable. When the client approves, the user comes back and says "hand off [client] hero to design," which triggers Phases 3b and 5 without re-running the audit.

**"Full pipeline with Claude Design brief"** → Run Phases 1-5. Phase 4 writes the Claude Design brief. The HTML comparison page (Phase 3a) still drops as the visual diagnosis. The Campaign Planner ticket links both.

**"Just the audit"** → Run Phases 1-2 and the HTML comparison page (Phase 3a). No Notion write-up, no ticket. Used for prospect audits or sales leverage.

## Phase 1: Capture

Use Claude in Chrome to scrape hero images. Hero images load dynamically, so web_fetch won't work.

**Target restaurant:**
1. Google "[restaurant] [city] Uber Eats" to find direct storefront link
2. Screenshot the hero/banner area on UE
3. Zoom into the hero for composition detail
4. Repeat on DoorDash and Grubhub (for whichever platforms were selected)
5. Note: composition, color palette, focal point count, text overlays, brand elements, logo placement

**Competitive set (top 5):**
1. Google "site:ubereats.com [cuisine] [city]" to find nearby competitors in same category
2. Pick top 5 by rating + review count + proximity
3. Visit each storefront, screenshot hero image
4. Log: name, rating, review count, hero strategy, storefront URL

**Save all screenshots** to `/Cowork/Clients/[Client]/hero-review-[YYYY-MM-DD]/images/` so the HTML comparison page can reference them via relative paths.

**Efficient routing:** Use Google search to find direct storefront URLs rather than trying to change delivery addresses within the platform. Navigate via Google results, not platform search.

## Phase 2: Score

Score each selected platform independently. Six dimensions, weighted.

| Dimension | 1 (Poor) | 5 (Excellent) | Weight |
|-----------|----------|---------------|--------|
| **Thumbnail Impact** | Unreadable at 150px, no focal point | Instantly clear, single strong focal point | 25% |
| **Differentiation** | Identical to the 40-50% flat lay pattern | Unique visual strategy that breaks from competitors | 20% |
| **Composition** | Cluttered flat lay, 6+ items, no hierarchy | Clean single item OR bold color blocking OR dramatic focus | 20% |
| **Appetite Appeal** | Cold, clinical, poor lighting | Hot, fresh, textured, makes you want to order | 15% |
| **Brand Signal** | No brand elements, could be any restaurant | Instant recognition: color, logo, or signature item | 10% |
| **Technical** | Low resolution, wrong aspect ratio, bad crops | Meets specs exactly, sharp at all sizes | 10% |

**Scoring:** Multiply each score (1-5) by weight, sum for total (max 5.0).
**Grades:** A (4.5-5.0), B (3.5-4.4), C (2.5-3.4), D (1.5-2.4), F (<1.5)

**Platform specs (all three):**

| | Uber Eats | DoorDash | Grubhub |
|---|---|---|---|
| Size | 2880 x 2304px | 1400 x 800px min | 1200 x 800px recommended |
| Ratio | 5:4 | 4:1 (web), 16:9 (app) | 3:2 |
| Format | JPG, PNG, GIF | JPEG, PNG | JPEG, PNG |
| Max | 5MB | 2MB | 5MB |
| Guidelines | [UE Photo Guide](https://help.uber.com/en/merchants-and-restaurants/article/merchant-submitted-menu-catalog-photo-guidelines?nodeId=6985355b-0426-4523-94f2-89bb9b0566e9) | [DD Photo Types](https://help.doordash.com/merchants/s/article/DoorDash-Photos-Types?language=en_US) | [GH Menu Photos](https://learn.grubhub.com/archives/basics/add-menu-photos) |

Grubhub's header image renders wider on desktop and tighter on mobile. The 3:2 ratio is a safe middle ground, but verify current specs in the merchant portal as GH updates these periodically.

DoorDash's 4:1 ratio is dramatically wider than UE's 5:4. An image designed for one will crop badly on the other. Score and recommend separately for each selected platform.

**Strategy classification:**
- **Overhead Flat Lay** (the trap): 6+ items from above. 40-50% of restaurants do this.
- **Single Hero Item + High Contrast**: One plate/item, clean background. Best for fast casual, new brands.
- **Bold Brand Color Blocking**: Brand color as background, product overlaid. Best for multi-location with strong identity.
- **Clean Single Focus**: Single item, dramatic lighting, artisanal feel. Best for premium restaurants.
- **Hybrid/Other**: Text overlays, promo messaging, lifestyle imagery.

## Phase 3: Deliverables

Two artifacts: an HTML comparison page (Phase 3a) that carries the visual weight, and a Notion page (Phase 3b) that captures the structured write-up and lives in the client's workspace.

### Phase 3a: HTML Comparison Page

Save to `/Cowork/Clients/[Client]/hero-review-[YYYY-MM-DD]/hero-comparison.html` as a single self-contained file. Inline CSS, images referenced via relative paths to the `images/` folder from Phase 1 or base64-embedded if portability matters.

**Structure:**

**Header.** Client name, audit date, locations covered, headline grade (weighted average across selected platforms). One-sentence diagnosis below.

**Section 1: The Current State.** Client's hero rendered at each selected platform's actual aspect ratio (UE 5:4, DD 16:9, GH 3:2) using correct aspect-ratio containers. Each tile shows the image, the platform-specific grade as a colored badge (A=green, B=yellow, C=orange, D/F=red), and a one-line diagnosis ("5-6 items competing at 150px. Eye doesn't know where to land.").

**Section 2: The Competitive Landscape.** 2x3 grid of top 5 competitors with the client in the sixth slot for direct comparison. Each tile: hero image cropped to UE 5:4 for consistency, restaurant name as a link to their UE storefront, rating, review count, strategy tag as a pill (Flat Lay / Single Hero / Color Block / Clean Focus / Hybrid), grade badge. Beneath the grid, a one-line pattern observation: "5 of 6 use overhead flat lays. [Competitor X] is the only one breaking the pattern, at grade B."

**Section 3: The Opportunity.** Variant concept cards, one per recommended variant (2-3 cards total). Each card renders:
- Variant name + projected grade as the heading
- Strategy classification as a pill
- Brand color swatch (pull from client brand kit if provided, otherwise from observed brand elements in the current hero)
- Composition wireframe as inline SVG (simple shapes showing focal point placement, negative space, logo zone — not a fake hero mockup)
- Three platform crop previews (small labeled boxes showing UE 5:4, DD 16:9, GH 3:2 and how the composition fits each ratio)
- Two-sentence concept description
- Three "why it wins" bullets referencing specific competitive gaps from Section 2

**Footer.** Link to Notion review page (once created in Phase 3b). Link to Claude Design brief (when Phase 4 runs).

**Styling rules:**
- Clean, lots of whitespace, readable at a glance
- Works when printed to PDF (A4 landscape)
- Humanist sans-serif (system-ui, -apple-system, sans-serif stack)
- Max width 1200px, centered
- No emojis, no gradients, no decorative elements
- Grade badges: A #16a34a, B #ca8a04, C #ea580c, D/F #dc2626 on light backgrounds
- Strategy pills: neutral grey with rounded corners
- Print-safe color palette

**What NOT to include:**
- No rendered hero mockups (Claude Design handles that, CSS fakes look worse than clean wireframes)
- No methodology deep dive (the scoring rubric belongs in the Notion page, not the client-facing HTML)
- No "next steps" section (the variants are the next steps)

### Phase 3b: Notion Page

Create a Notion page under the client's workspace. Search Notion for the client name first to find the right parent page.

**The page has exactly 3 sections.** Grade, Competition, Creative Direction.

At the top of the page, link to the HTML comparison file in the Cowork folder. The HTML carries the visual weight, so the Notion page can stay leaner than the prior version.

#### Section 1: Grade

Per-platform score table with one-line notes per dimension. Then a "bottom line" sentence summarizing the problem.

```
## Uber Eats: C (2.6 / 5.0)

| Dimension | Score | What's happening |
| --- | --- | --- |
| Thumbnail Impact | 2.0 | 5-6 items competing at 150px. Eye doesn't know where to land. |
| Differentiation | 2.0 | Classic flat lay. Same strategy as 60% of competitors. |
| ... | ... | ... |

## DoorDash: D (2.1 / 5.0)

Same image force-cropped to DD's 4:1. Edge dishes cut off. Text overlay adds clutter.

## Grubhub: C- (2.4 / 5.0)

3:2 crop handles the flat lay slightly better than DD, but still no focal point at thumbnail size.

**Bottom line:** The food is good. The strategy is invisible. [Client] blends into a scroll of identical flat lays.
```

Keep platform sections short if they're the same image cropped differently. Don't repeat the full table.

#### Section 2: Competitive Landscape

One table. Every restaurant links to its UE storefront so the reader can click through.

```
| Restaurant | Stars | Reviews | Score | Strategy |
| --- | --- | --- | --- | --- |
| [Restaurant](UE storefront URL) | 4.8 | 6K+ | 2.6 (C) | Overhead Flat Lay |
| ... | ... | ... | ... | ... |
```

Below the table: 2-3 sentences max. Pattern observation. Who broke the pattern. What strategies have zero competitors using them.

#### Section 3: Creative Direction

2-3 variants to test. Each variant gets:

- **Name + projected score** as the heading
- **Strategy type** (one line)
- **The concept** (2-3 sentences describing exactly what's in the frame)
- **Why it wins** (2-3 bullets referencing specific competitive gaps)
- **Platform notes** (one line each for every selected platform, how the composition adapts to that ratio)
- **Production** (one line: angle, lighting, surface, time estimate)

End with a simple 4-row testing plan table (week, variant, platform, KPI).

**What NOT to include in the Notion page:**
- No production checklists (the photographer knows their job)
- No platform specs table (the HTML page already has this, and the designer gets specs via the Campaign Planner ticket)
- No methodology explanations (the scoring rubric doesn't need to be in the deliverable)
- No "next steps" section (the variants ARE the next steps)
- No appendices

## Phase 4: Claude Design Brief (Optional)

**This phase only runs when the user selects "Full pipeline with Claude Design brief."** Skip it for the default "hand off to design" flow.

[Claude Design](https://claude.ai/design) generates AI visual mockups from a structured prompt. It applies brand systems, outputs to PDF, PPTX, Canva, or a shareable URL, and hands the designer a starting file that's closer to production than a text brief alone.

The skill doesn't call Claude Design directly (no MCP yet). It writes a paste-ready brief that Maxx or the designer drops into claude.ai/design in their browser.

### Write the brief

Save to `/Cowork/Clients/[Client]/hero-review-[YYYY-MM-DD]/claude-design-brief.md`.

**Structure:**

**Context block.** Restaurant name, cuisine, locations, brand positioning in one paragraph. Keep it tight so Claude Design gets signal, not noise.

**Brand assets.** Logo URL or file reference. Brand colors as hex codes if known, otherwise descriptive ("brand teal, warm cream accent"). Typography direction if relevant. Pull from the client's brand kit if one lives in the Cowork folder.

**The ask.** A single paragraph telling Claude Design what to produce:
> "Generate [N] hero image variants for delivery platform storefronts. Each variant needs three crops: Uber Eats (5:4, 2880x2304px), DoorDash (16:9, app), Grubhub (3:2, 1200x800px). Photorealistic commercial food photography style. Leave clean negative space for logo placement. No AI-generated text or typography in the image itself."

**Variant specifications.** For each variant from Phase 3:
- Name + strategy classification
- Composition direction (angle, focal point, negative space allocation)
- Color palette (background, accent, food)
- Styling notes (lighting quality, surface material, garnish, steam, props)
- Why this variant wins (one line, competitive gap it fills)

**Source references.** If the client provided a folder of dish photos, include the Drive link. If we screenshotted dishes from their existing listings, include URLs or attach the images to the brief. Claude Design accepts document uploads as source material.

**Output expectations.** "Export final variants as high-res PNG per platform ratio. If the client brand kit is linked, push to Canva for designer handoff. Otherwise export PPTX for the designer to rebuild in their tool of choice."

### Handoff instructions in the ticket

In the Campaign Planner ticket (Phase 5), note:
1. The Claude Design brief lives at the saved file path
2. The designer should open claude.ai/design, upload source images if provided, paste the brief
3. Iterate 2-3 rounds with Claude Design until the variants look right
4. Export and finalize in Canva or Photoshop

**Important:** Claude Design outputs are visual mockups, not final production assets. The designer still owns the final render. The brief closes the gap between "text direction" and "starting file."

## Phase 5: Create Campaign Planner Ticket

After producing the deliverables, create a ticket in the Campaign Planner database in Notion. This automates the handoff to the design team.

**Database:** Campaign Planning (data source: `collection://1c8d3ff0-18e7-8067-abff-000b54568283`)
**Template:** "Hero / Menu Image" (template ID: `24cd3ff0-18e7-8043-8866-e86f7b86953c`)

Create the page using the template, then update with the brief details.

**Properties to set:**

| Property | Value |
|---|---|
| Campaign name | "[Client] Hero Image Refresh \| [Month Year]" |
| Asset Type | "Hero Image" |
| Channels | JSON array of selected platforms, e.g. `["Uber Eats", "DoorDash", "Grubhub"]` |
| Client | Relation to client page (search Notion for the client first to get page URL) |
| Status | "Brief" |
| Service Team | "Marketplace" |
| Start Date | Today's date |

**Page content** should fill in the template fields:
- **Brief Title**: "[Client] Hero Image Refresh"
- **Purpose**: "Hero refresh based on competitive audit. Current grade: [grade]. Target: B+ (3.5+)."
- **Requirements**: Art direction from Phase 3 variants
- **Menu Items**: Link to Google Drive folder or screenshot set
- Below the template, add:
  - Link to the HTML comparison page in Cowork
  - Link to the Notion hero review page from Phase 3b
  - Link to the Claude Design brief (when Phase 4 ran)
  - For each variant: strategy, source image reference, art direction, platform-specific crop notes
  - Export specs table for all selected platforms
  - Testing plan table

Search for the client in Notion first to get the client page URL for the relation field.

## Adapting to the Ask

Not every request needs the full treatment. Match the depth to what was asked.

**Full review** ("review [client]'s hero image", "grade their hero and compare to competition"):
Ask Phase 0 questions. Default to "Review + hand off to design team." Runs Phases 1-3 and 5. The designer gets everything via the Campaign Planner ticket (auto-drops into #design-requests). The client gets the HTML page as the visual deliverable.

**Client approved, now hand off** ("hand off [client] hero to design", "client approved the direction"):
Phases 3b and 5 only. Search Notion for the existing hero review page to pull the creative direction. Don't re-run the audit. Create the Campaign Planner ticket using the already-approved direction.

**Quick direction** ("their hero feels stale, what should we test?"):
Skip the detailed scoring table and HTML page. Quick assessment (1-2 sentences on current state), then creative direction with variants in chat. No deliverables unless asked.

**Generate Claude Design brief** ("write a Claude Design brief for [client]", "generate a design brief for claude.ai/design"):
Only when explicitly asked or when the user picks the full pipeline option in Phase 0. Run Phase 4 to produce the paste-ready brief. Still create the Campaign Planner ticket (Phase 5) so the designer sees the handoff.

**Prospect audit** ("grade Curry Up Now's hero, they're a prospect"):
Phases 1-2 and Phase 3a only, framed as sales leverage. The HTML page becomes the sales artifact. Skip Notion write-up and Campaign Planner ticket (prospect, not active client). Choose "Just the audit" automatically.

**Multi-location** ("check all 13 Curry Up Now locations"):
Check 2-3 locations for hero consistency. Note any variance. The variants should consider franchise scalability. The HTML page handles multi-location by showing a strip of thumbnails per location with the grade variance visible.

## Key Principles

**Ask which platforms first.** Don't assume. Every client's platform mix is different, and the entire workflow cascades from this answer.

**Score what you see.** You're evaluating what a customer sees scrolling through delivery platforms. No guessing at conversion data unless the user provides it.

**Differentiation is the multiplier.** A perfect flat lay still scores low because 40-50% of the market does the same thing. The scoring rewards breaking from the pack.

**Recommend with specificity.** "Get a better hero image" is useless. "Shoot your signature bowl at 45 degrees on matte charcoal, cropped to fill UE's 5:4 frame" is a brief a photographer can execute.

**The HTML is the client-facing artifact.** The Notion page is for the team. The Campaign Planner ticket is for the designer. The HTML comparison page is for the client. Three audiences, three formats, one audit.

**The designer is still the finisher.** Claude Design produces starting files, not final assets. A mockup with correct composition, brand color, and ratio is a better handoff than a text brief, but the designer owns the final render. Never present Claude Design output as production-ready.

**Close the loop.** Every review should end with a Campaign Planner ticket (unless it's a prospect audit or client-approval-first situation). New tickets auto-drop into #design-requests in Slack, so no separate Slack message is needed. A brief sitting in a Notion page that nobody sees is the same as no brief at all.

**Keep the output scannable.** The person reading this should understand the situation and know what to do next within 2 minutes. If a section doesn't move them toward a decision, cut it.

## Reference

Scoring framework based on the Spice Digital 2026 Hero Image Playbook:
https://www.notion.so/2cbd3ff018e780c8b40ddb5cbc14909a

Campaign Planner database: https://www.notion.so/1c8d3ff018e780169ad4f3268648490b
Hero / Menu Image template ID: 24cd3ff0-18e7-8043-8866-e86f7b86953c

Claude Design: https://claude.ai/design
