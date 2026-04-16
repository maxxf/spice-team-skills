---
name: hero-image-review
description: >
  Review and score restaurant hero images on Uber Eats, DoorDash, and Grubhub, benchmark against competitors, produce creative direction,
  and hand off to the design team via a Campaign Planner ticket in Notion. Optionally generate AI reference drafts with Pixa.
  Trigger on "review hero image", "audit hero image", "grade their hero", "hero image analysis", "check their cover photo",
  "compare hero images", "hero refresh for [client]", or any request to evaluate, score, or improve a restaurant's delivery
  platform hero/banner image. Also trigger for hero image planning or A/B tests.
  Goes deeper than storefront-audit. Use this skill whenever hero images are the focus.
---

# Hero Image Review & Design Handoff

Grade a restaurant's hero images, benchmark against competitors, produce creative direction with specific variant concepts, and hand off to the design team via a Campaign Planner ticket in Notion (which auto-drops into #design-requests).

The default flow is **audit → creative direction → Campaign Planner ticket**. The designer executes the final assets. AI generation via Pixa is available as an optional add-on to produce reference drafts for the designer, but the quality isn't production-ready yet, so it supplements the brief rather than replacing the designer.

## Inputs

- **Restaurant name** (required)
- **Location / delivery address** (required, for competitive discovery)
- **Platform(s)** (ask the user, see Phase 0)
- **Specific competitors** (optional, otherwise discover top 5 nearby in same cuisine)
- **Photo assets** (optional: Google Drive link, uploaded images, or Pixa collection)

## Phase 0: Upfront Questions

Before doing anything else, ask three questions using AskUserQuestion. These shape the entire workflow.

**Question 1:** "Which platforms need hero images for [client]?"
**Options (multiSelect: true):**
- Uber Eats
- DoorDash
- Grubhub
- All three

Each platform has different aspect ratios. A hero designed for one will crop badly on another. The audit, generation, and export specs all flow from this answer.

**Question 2:** "Do you have image assets for [client]?"
**Options:**
- Yes, folder of images (Drive link, etc.) — *Most common. Clients typically provide a folder of menu item photos that we composite and edit into heroes.*
- No, pull from their existing platform listings — *We'll screenshot their best menu item photos from UE/DD/GH and use those as source material.*
- No usable images, generate concepts from scratch — *Text-to-image only. AI concept drafts for designer direction, not production assets.*

**Question 3:** "What do you want to do after the review?"
**Options:**
- Review + hand off to design team (Recommended) — *Produces the audit and creative direction, then creates a Campaign Planner ticket and posts the brief to #design-requests. The designer executes the final assets. This is the standard flow.*
- Review + concepts only (share with client for approval first) — *Produces the audit and creative direction as a shareable deliverable. No ticket, no Slack post. Use when the client needs to approve direction before any work starts.*
- Full pipeline with AI drafts (experimental) — *Same as "hand off to design" but also generates AI reference drafts via Pixa. These are directional only, not production assets. Useful for giving the designer a visual starting point.*
- Just the audit, no handoff — *Grade and competitive analysis only. Good for prospect audits or sales leverage.*

If the user has already specified platforms or shared images in their request, skip the relevant question and use what they provided.

### How the workflow branches

**"Review + hand off to design team"** (DEFAULT) → Run Phases 1-3, then Phase 5 (Campaign Planner ticket). New tickets automatically appear in #design-requests, so no separate Slack message needed. The designer gets the full creative direction with variant concepts, platform specs, and source image references. This is the workhorse flow.

**"Review + concepts only"** → Run Phases 1-3 only. The Notion page with grades, competition, and creative direction is the deliverable. Share it with the client. When the client approves, the user comes back and says "hand off [client] hero to design," which triggers Phase 5 without re-running the audit.

**"Full pipeline with AI drafts"** → Run Phases 1-5. Phases 1-3 produce the review, Phase 4 generates AI reference drafts via Pixa (experimental, not production quality), Phase 5 hands off to design. The AI drafts are labeled as directional reference material in the ticket.

**"Just the audit"** → Run Phases 1-3 only. No ticket. Used for prospect audits or sales leverage.

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
4. Log: name, rating, review count, hero strategy

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

## Phase 3: Build the Notion Page

Create a Notion page under the client's workspace. Search Notion for the client name first to find the right parent page.

**The page has exactly 3 sections.** No production checklists, no appendices, no methodology explanations. Grade, Competition, Creative Direction. That's it.

### Section 1: Grade

Per-platform score table with one-line notes per dimension. Then a "bottom line" sentence summarizing the problem.

Example format:
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

### Section 2: Competitive Landscape

One table. Every restaurant links to its UE storefront so the reader can click through.

```
| Restaurant | Stars | Reviews | Score | Strategy |
| --- | --- | --- | --- | --- |
| [Restaurant](UE storefront URL) | 4.8 | 6K+ | 2.6 (C) | Overhead Flat Lay |
| ... | ... | ... | ... | ... |
```

Below the table: 2-3 sentences max. What percentage uses flat lays? Who broke the pattern? What strategies have zero competitors using them?

### Section 3: Creative Direction

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
- No platform specs table (put it at the very bottom if you must, collapsed/minimal)
- No methodology explanations (the scoring rubric doesn't need to be in the deliverable)
- No "next steps" section (the variants ARE the next steps)
- No appendices
- No "questions for the team" section

## Phase 4: Generate AI Reference Drafts with Pixa (Optional)

**This phase only runs when the user selects "Full pipeline with AI drafts."** Skip it for the default "hand off to design" flow.

Pixa can generate reference compositions that give the designer a visual starting point. These are directional drafts, not production assets. The AI-generated text overlays (brand names, taglines) should always be replaced with the actual logo and brand assets by the designer. The pipeline is the same regardless of where the source images come from.

### Step 1: Get source images into Pixa

**Path A (client provided a folder):** This is the most common scenario. Clients hand over a Google Drive folder of menu item photos. Browse the folder, identify the 2-3 strongest dishes visually (look for: color contrast, height/dimension, texture, hero-worthy presentation). Get shareable URLs for each image, then use the `upload` tool (method: `url`) to bring them into Pixa.

**Path B (pull from platform listings):** Use Claude in Chrome to visit the client's UE/DD/GH storefronts. Screenshot the best-looking menu item photos (not the current hero, the individual item images). Look for dishes with vibrant color, clean plating, and good lighting. Save screenshots, then use `upload` (method: `upload_url`) to get a curl-able upload URL and push them to Pixa via shell.

**Path C (no usable images):** Skip to the text-to-image fallback at the end of this section.

**Important about inline chat images:** If the user shares images directly in the conversation (drag-and-drop or paste), these exist only in conversation context and can't be uploaded to Pixa. Ask the user for shareable URLs (Drive "Get link" or any public URL). If they can't provide URLs, fall back to Path C.

### Step 2: Select hero candidates

From the uploaded images, pick the dishes that will read best at thumbnail size. Prioritize:
- **Color contrast** against the intended background (e.g., warm food on cool teal)
- **Height and dimension** (bowls with ingredients piled high > flat plates)
- **Signature dishes** (the item the restaurant is known for, or the top seller)
- **Photographic quality** (sharp focus, good lighting, appetizing presentation)

You're picking 2-3 images to build hero variants from.

### Step 3: The production pipeline

Run this sequence for each hero variant, for each selected platform:

```
1. remove_background
   → edit_image(action: "remove_background", image: [asset_id])
   → Returns: clean cutout of the dish, no background

2. generate composite
   → generate_media(
       prompt: "Commercial food photography. [Dish description] on [branded background color] surface.
                [Composition direction from Phase 3]. [Angle, lighting, styling notes].
                Photorealistic, appetizing, restaurant delivery platform hero image.
                No text, no words, no logos, no overlays. Clean background with space for logo placement.",
       model: [use models tool to find best food photography model],
       attachments: [cutout asset_id],
       aspect_ratio: [platform ratio],
       num_variations: 2,
       output_format: "png"
     )
   → Returns: the dish composited into the hero scene at the correct platform ratio
   → IMPORTANT: Always specify "no text" in the prompt. AI-generated typography is unreliable. Leave clean space for the designer to place the actual brand logo.

3. upscale to platform specs
   → edit_image(action: "upscale", image: [composite asset_id], scale: "2")
   → Returns: high-res version ready for upload to the platform
```

**Platform aspect ratios:**
- Uber Eats: `5:4`
- DoorDash: `16:9` (app) or `21:9` (web, closest to 4:1)
- Grubhub: `3:2`

**For multi-item compositions** (e.g., the "Community Table" variant with 2-3 dishes):
- Remove background on each dish separately
- Use `generate_media` with all cutouts as attachments and a prompt describing the arrangement
- Or: remove background on the best group shot and expand it to the target ratio using `edit_image(action: "expand", aspect_ratio: "[ratio]")` which fills the extended canvas with AI-generated content

### Step 4: Organize outputs

For each generated asset, use `get_download_url` to get a downloadable link. Organize by variant and platform:

```
[Client] Hero Refresh/
├── Variant A - [Name]/
│   ├── UE-5x4-v1.png
│   ├── UE-5x4-v2.png
│   ├── DD-16x9-v1.png
│   ├── DD-16x9-v2.png
│   ├── GH-3x2-v1.png
│   └── GH-3x2-v2.png
├── Variant B - [Name]/
│   └── [same structure]
└── Source Cutouts/
    ├── [dish1]-cutout.png
    └── [dish2]-cutout.png
```

Save download URLs for inclusion in the Campaign Planner ticket and Slack brief.

### Text-to-image fallback (Path C, no usable photos):

When there are no source images at all, generate concept drafts from prompts only. These are directional, not production assets.

1. Use `models` tool (action: `recommend`, query: "commercial food photography, restaurant hero image, product shot") to find the best model
2. Generate 2 variations per variant per platform using `generate_media` with detailed prompts from Phase 3
3. **Label everything clearly as "AI concept draft (directional)"** in the Notion ticket and Slack brief
4. Note that designers should execute the final version using real food photography

### Model selection:

Use `models` tool with action `recommend` and query describing the use case. As of early 2026, Nano Banana 2 is the top pick for product photography (supports image attachments for compositing). Flux 2 Max is the runner-up at lower credit cost. Flux Kontext Pro is good for context-aware edits on existing images.

## Phase 5: Create Campaign Planner Ticket

After generating assets, create a ticket in the Campaign Planner database in Notion. This automates the handoff to the design team.

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
- **Menu Items**: Link to Google Drive folder or Pixa collection
- Below the template, add:
  - Link to the hero review Notion page from Phase 3
  - For each variant: strategy, source image reference, art direction, platform-specific crop notes
  - Export specs table for all selected platforms
  - Testing plan table
  - Note about AI-generated drafts with instruction that these are directional, not final

Search for the client in Notion first to get the client page URL for the relation field.

## Adapting to the Ask

Not every request needs the full treatment. Match the depth to what was asked.

**Full review** ("review [client]'s hero image", "grade their hero and compare to competition"):
Ask Phase 0 questions. Default to "Review + hand off to design team." Runs Phases 1-3 → 5. The designer gets everything they need via the Campaign Planner ticket (auto-drops into #design-requests).

**Client approved, now hand off** ("hand off [client] hero to design", "client approved the direction"):
Phase 5 only. Search Notion for the existing hero review page to pull the creative direction. Don't re-run the audit. Create the Campaign Planner ticket using the already-approved direction.

**Quick direction** ("their hero feels stale, what should we test?"):
Skip the detailed scoring table. Quick assessment (1-2 sentences on current state), then creative direction with variants. No ticket unless asked.

**Generate AI drafts** ("generate a hero for [client] using these photos", "create Pixa drafts for [client]"):
Only when explicitly asked. Run Phase 4 (Pixa generation) to produce reference drafts. Still create the Campaign Planner ticket (Phase 5). Label all AI outputs as directional reference, not production assets.

**Prospect audit** ("grade Curry Up Now's hero, they're a prospect"):
Phases 1-3 only, framed as sales leverage. Skip Campaign Planner ticket and Slack post (prospect, not active client). Choose "Just the audit" automatically.

**Multi-location** ("check all 13 Curry Up Now locations"):
Check 2-3 locations for hero consistency. Note any variance. The variants should consider franchise scalability.

## Key Principles

**Ask which platforms first.** Don't assume. Every client's platform mix is different, and the entire workflow cascades from this answer.

**Score what you see.** You're evaluating what a customer sees scrolling through delivery platforms. No guessing at conversion data unless the user provides it.

**Differentiation is the multiplier.** A perfect flat lay still scores low because 40-50% of the market does the same thing. The scoring rewards breaking from the pack.

**Recommend with specificity.** "Get a better hero image" is useless. "Shoot your signature bowl at 45 degrees on matte charcoal, cropped to fill UE's 5:4 frame" is a brief a photographer can execute.

**The designer is the finisher.** AI-generated drafts are reference material, not deliverables. The default flow hands off creative direction to the design team. Pixa can produce reference compositions when available, but the designer makes the final asset. Never present AI drafts as production-ready.

**Close the loop.** Every review should end with a Campaign Planner ticket (unless it's a prospect audit or client-approval-first situation). New tickets auto-drop into #design-requests in Slack, so no separate Slack message is needed. The brief sitting in a Notion page that nobody sees is the same as no brief at all.

**Keep the output scannable.** The person reading this should understand the situation and know what to do next within 2 minutes. If a section doesn't move them toward a decision, cut it.

## Reference

Scoring framework based on the Spice Digital 2026 Hero Image Playbook:
https://www.notion.so/2cbd3ff018e780c8b40ddb5cbc14909a

Campaign Planner database: https://www.notion.so/1c8d3ff018e780169ad4f3268648490b
Hero / Menu Image template ID: 24cd3ff0-18e7-8043-8866-e86f7b86953c
