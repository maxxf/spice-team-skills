---
name: storefront-audit
description: Audit prospect delivery platform storefronts on Uber Eats, DoorDash, and Grubhub. Use when asked to grade, audit, analyze, or evaluate a restaurant's 3P marketplace listings. Generates client-ready reports with scores for hero image, menu structure, pricing, promotions, and competitive positioning. Ideal for sales prospecting, lead generation, or pre-engagement discovery.
---

> **Spicy Nugget handoff:** This task can be fully delegated. Post to #spice-ai-ops: "@Spicy Nugget audit [restaurant] on [platform] in [location]"

# 3P Storefront Audit Skill

Produce client-ready storefront audit reports for restaurant prospects across delivery marketplaces.

## When to Use

- "Audit [restaurant] on Uber Eats/DoorDash"
- "Grade this storefront"
- "Analyze their delivery presence"
- "What's wrong with their 3P listings?"
- "Audit all [X] locations" (multi-location mode)
- Pre-sales discovery for prospects

## Workflow

### DEFAULT OUTPUT FORMAT (MANDATORY)

**Always produce the FULL AUDIT REPORT (Section 3 template) as the default output.** This includes all required sections:

1. Executive Summary with overall score and band
2. Platform Scores table (all 6 dimensions)
3. Dimension Breakdown (detailed sub-scores for each dimension)
4. Strategic recommendations (if applicable)
5. Priority Quick Wins (tiered by impact/effort)
6. 90-Day Projected Improvement table
7. Estimated Revenue Opportunity
8. Data Sources

**Alternative formats are ONLY used when explicitly requested:**
- "Prospect Summary Mode" → user says "summary", "one-pager", "follow-up version", or "shareable"
- "CRM Integration Mode" → automatically appended when adding to Notion (in addition to the full report, not instead of)
- "Multi-Location Mode" → user asks to audit multiple locations of the same brand

If the user just says "audit [restaurant]" or "grade their storefront", produce the full report. Every time. No exceptions.

### 1. Discovery & Data Collection

**Find all active listings:**

1. Search each platform (Uber Eats, DoorDash, Grubhub) for the brand name
2. Try variations: full name, abbreviations, common misspellings
3. Set delivery address to target market to unlock local listings
4. Check category pages ("Best Overall", "Top Rated", "Featured") if direct search fails
5. Search Google "[brand] DoorDash/Uber Eats" for deep links as fallback
6. Log all discovery attempts per market

**Collect for each location found:**
- Hero/cover image presence and quality
- Rating, review count, review velocity (30-day)
- 20-30 recent reviews for sentiment analysis
- Menu structure (categories, item count)
- Photo coverage across menu items
- Active promotions and ad placements
- Hours, availability status
- Pricing on 8-12 anchor items

### 2. Scoring (See references/scoring-rubric.md)

Score each location across six dimensions:

| Dimension | Max Score | Key Factors |
|-----------|-----------|-------------|
| Hero Image | 15 | Present, quality, carousel legibility, brand fit |
| Menu Images | 25 | Coverage, quality, consistency |
| Menu Structure | 20 | ≤9 categories, clear naming, modifiers, bundles |
| Customer Sentiment | 15 | Rating, review velocity, actionable themes, delivery issues |
| Promotions | 10 | Active promos, featured placement, offer strategy |
| Competitive Position | 15 | Pricing vs market, differentiation, ratings gap |

**Overall Score Bands:**
- 85-100: Excellent (minor optimizations)
- 70-84: Good (targeted improvements needed)
- 50-69: Fair (significant opportunity)
- <50: Poor (comprehensive overhaul required)

### 3. Report Structure

```markdown
# Storefront Audit: [Brand Name]
**Markets:** [list]  |  **Date:** [date]  |  **Prepared by:** Spice Digital

## Executive Summary
- Overall Score: [X/100]
- Biggest wins (2-3 bullets)
- Biggest gaps (2-3 bullets)
- Top 3 priority fixes with estimated impact

## Platform Analysis

### Uber Eats
[Location comparison table]
[Platform-specific findings]

### DoorDash
[Location comparison table]
[Platform-specific findings]

## Scoring Breakdown
[Detailed scores per dimension with rationale]

## Quick Wins (Implement This Week)
1. [Specific action] → [Expected impact]
2. [Specific action] → [Expected impact]
3. [Specific action] → [Expected impact]

## 90-Day Roadmap
| Timeframe | Focus | Actions |
|-----------|-------|---------|
| Week 1-2 | Stabilize | [fixes] |
| Week 3-4 | Convert | [improvements] |
| Month 2 | Amplify | [optimizations] |
| Month 3 | Scale | [expansion] |

## Competitive Snapshot
[Pricing table vs 2-3 local competitors]
[Positioning assessment]

## Appendix
- Discovery logs
- Full menu analysis
- Customer verbatim samples
```

### 4. Key Benchmarks (Spice Standards)

**Hero Image:**
- Must exist (40% of storefronts missing one)
- Legible at thumbnail size in carousels
- Shows signature item or brand moment
- 5-10% CTR improvement when optimized

**Menu Structure:**
- ≤9 categories maximum (conversion drops 15% above this)
- Top sellers visible in first scroll
- Bundles increase AOV 12-20%
- Photo coverage >80% on top 20% items

**Operations:**
- Prep time below market median by 5 min → better ranking
- Error rate target: <2%
- Rating threshold: 4.5+ with high velocity

**Customer Sentiment:**
- Target: 4.5+ rating with 50+ reviews/month
- Delivery complaints <10% of negative reviews
- Items with recurring delivery issues → remove or repackage
- Positive themes → amplify in photos and copy

**Promotions:**
- New user promos: $X off (kill after 2nd order)
- Threshold promos outperform % off by 2x
- Rotate formats to avoid promo fatigue

### 5. Output

Generate report in Markdown format optimized for:
- Notion embedding
- PDF export
- Client presentation

Include [Image: description] placeholders for screenshots.

## References

- Detailed scoring methodology: `references/scoring-rubric.md`
- Gold standard comparison: `references/gold-standard-comparison.md`
- Lead magnet email sequences: `references/email-sequences.md`

## Scripts

- Browser automation: `scripts/audit_storefront.py`
  - Usage: `python3 audit_storefront.py "Brand Name" "City, State" --platforms uber doordash grubhub`
  - Requires: `pip install playwright && playwright install chromium`
  - Outputs: Screenshots + JSON data to `./audit_output/`

## Workflow Extensions

### Photo Coverage Assessment (REQUIRED)

**Menu images are the #1 disputed finding. Use browser automation for accurate counts.**

⚠️ **CRITICAL:** `web_fetch` returns static HTML that often misses dynamically loaded images. It will show menu items as text-only even when photos exist. **Always use browser automation (Chrome extension) for photo coverage.**

#### Correct Methodology: Browser Automation

1. **Navigate to storefront** via `Claude in Chrome:navigate`
2. **Screenshot the hero section** to confirm hero image
3. **Click each menu category** in the left sidebar (or scroll to section)
4. **Screenshot each category** and count:
   - Items WITH photos (image thumbnail visible)
   - Items WITHOUT photos (text-only: name, price, description)
5. **Track by category** in a table format
6. **Calculate overall coverage:** (items with photos) ÷ (total unique items)

#### Photo Coverage Tracking Template

```markdown
| Category | Items w/ Photo | Items w/o Photo | Coverage |
|----------|----------------|-----------------|----------|
| Pizzas | 16 | 0 | 100% |
| Sides | 2 | 0 | 100% |
| Salads | 2 | 2 | 50% |
| Sauces | 1 | 5 | 17% |
| **TOTAL** | **21** | **7** | **75%** |
```

#### Common Pitfalls to Avoid

1. **Featured Items carousel ≠ full menu coverage**
   - The "Featured items" / "Picked for you" carousels show TOP items (usually with photos)
   - These are duplicates from other categories — don't count twice
   - The real coverage gap is often in secondary categories (sides, sauces, drinks)

2. **Don't confuse image types:**
   - Hero image (banner at top) ≠ menu item photos
   - Category headers ≠ individual item photos
   - "Popular" / "#1 most liked" badge ≠ photo coverage

3. **Check ALL categories:**
   - Pizza/main items often have 100% coverage
   - Sides, sauces, drinks, add-ons often have 0-20% coverage
   - Overall score depends on full menu, not just bestsellers

#### Scoring Photo Coverage (out of 25 points)

| Coverage | Score | Assessment |
|----------|-------|------------|
| >90% | 22-25 | Excellent — minor gaps only |
| 70-89% | 17-21 | Good — main items covered, secondary gaps |
| 50-69% | 12-16 | Fair — significant gaps hurting conversion |
| 30-49% | 6-11 | Poor — major visibility issue |
| <30% | 0-5 | Critical — likely losing 15-25% of orders |

#### Fallback: web_fetch (Limited Use)

If browser automation unavailable, `web_fetch` can confirm:
- Whether hero image exists (look for hero img URL)
- Approximate menu structure from category names
- **Cannot reliably confirm** item-level photo coverage

When using web_fetch fallback, note in report:
> *Photo coverage estimated from HTML structure. Browser verification recommended.*

### Multi-Location Mode

When auditing a brand with multiple locations (chains, franchises, multi-unit groups):

**Discovery:**
1. Search platform for brand name in target market
2. Note all locations returned (address, store ID if visible)
3. For chains with 5+ locations, sample strategically:
   - Highest-rated location
   - Lowest-rated location
   - 2-3 mid-range locations
   - Flag any locations with significantly different menus (franchise variance)

**Scoring approach:**
- Score each location individually using standard rubric
- Calculate **portfolio average** for each dimension
- Identify **outliers** (±15 pts from average) — these need attention
- Note **consistency issues** across locations (different heroes, menus, pricing)

**Report structure for multi-location:**
```markdown
# Portfolio Storefront Audit: [Brand Name]
**Locations Audited:** [X] of [Y] total
**Markets:** [list]
**Date:** [date]

## Portfolio Summary

| Metric | Portfolio Avg | Best | Worst | Gap |
|--------|---------------|------|-------|-----|
| Overall Score | X/100 | [Location] X | [Location] X | X pts |
| Hero Image | X/15 | — | — | — |
| Menu Images | X/25 | — | — | — |
| Menu Structure | X/20 | — | — | — |
| Sentiment | X/15 | — | — | — |
| Promotions | X/10 | — | — | — |
| Competitive | X/15 | — | — | — |

## Location Breakdown

### [Location 1 - Address]
**Score:** X/100
**Platform:** Uber Eats | DoorDash | Grubhub
**Rating:** X.X (XXX reviews)
**Key Issues:** [1-2 bullets]

### [Location 2 - Address]
...

## Consistency Analysis

**Brand Consistency Issues:**
- [ ] Hero images match across locations
- [ ] Menu items/pricing consistent
- [ ] Promotions aligned
- [ ] Naming conventions standardized

**Flagged Variances:**
- [Location X]: [specific issue]
- [Location Y]: [specific issue]

## Portfolio-Wide Recommendations

### Systemwide Fixes (All Locations)
1. [Action] — affects X locations
2. [Action] — affects X locations

### Location-Specific Fixes
| Location | Priority Fix | Impact |
|----------|--------------|--------|
| [Addr 1] | [Action] | [Impact] |
| [Addr 2] | [Action] | [Impact] |

## Revenue Opportunity

**Per-location average:** $X-Xk/month
**Portfolio total:** $X-Xk/month ($X-Xk/year)
```

**Efficiency tips for large portfolios:**
- If 10+ locations: audit 5, extrapolate patterns
- If menus are centrally managed: deep-dive 1-2, spot-check rest
- If franchise model: audit 1 per franchisee cluster
- Always verify at least 1 location per market

### CRM Integration Mode

When completing an audit, **always link to Notion Sales Pipeline:**

1. Search Notion for existing prospect record
2. If found: Add audit summary to the page content
3. If not found: Create new record in Sales Pipeline database
4. Update "Last contact date" property
5. Mark any "send audit" tasks as complete

**Audit summary format for CRM:**
```markdown
## 3P Storefront Audit — [Date]

**Platform:** [Uber Eats / DoorDash / Grubhub]
**Score:** [X/100] ([Band])

### Scoring Breakdown
| Dimension | Score | Notes |
|-----------|-------|-------|
| Hero Image | X/15 | [one-line finding] |
| Menu Images | X/25 | [one-line finding] 🔴 if critical |
| Menu Structure | X/20 | [one-line finding] |
| Sentiment | X/15 | [rating, review count] |
| Promotions | X/10 | [one-line finding] 🔴 if none |
| Competitive | X/15 | [one-line finding] |

### Key Findings
- [Critical gap 1]
- [Critical gap 2]
- [Revenue opportunity: $X-Xk/month]

### Quick Wins Identified
1. [Action] ([effort])
2. [Action] ([effort])
3. [Action] ([effort])
```

### Prospect Summary Mode

When asked to create a "summary", "follow-up", or "shareable" version:

Generate a simple one-pager for the prospect (not the full audit):

```markdown
# [Brand] — Uber Eats Storefront Summary

**Prepared for:** [Contact Name]
**Date:** [Date]

---

## The Bottom Line

**Score: X/100** — [One sentence assessment]

[2-3 sentences on what's happening and why it matters]

---

## What's Working

✅ [Strength 1]
✅ [Strength 2]
✅ [Strength 3]

---

## Three Things Costing You Orders

**1. [Problem headline]**
[1-2 sentences explaining the issue in plain language]

**2. [Problem headline]**
[1-2 sentences explaining the issue in plain language]

**3. [Problem headline]**
[1-2 sentences explaining the issue in plain language]

---

## Quick Wins (This Week)

| Fix | Time | Impact |
|-----|------|--------|
| [Action 1] | [X min/hr] | [+X% metric] |
| [Action 2] | [X min/hr] | [+X% metric] |
| [Action 3] | [X min/hr] | [+X% metric] |

---

## Estimated Opportunity

**Revenue you're likely leaving on the table: $X-Xk/month**

[One sentence on annual impact]

---

## Next Step

[Soft CTA — offer to walk through, no hard sell]

— [Your name]
Spice Digital
[email]
```

**Tone guidelines for prospect summary:**
- Plain language, no jargon
- Direct but not harsh
- Focus on $ opportunity, not criticism
- Keep it under 1 page
- No detailed methodology — that's in the full audit

### Gold Standard Comparison Mode

When asked to "compare to gold standard" or "benchmark":

1. Load `references/gold-standard-comparison.md`
2. Identify prospect's segment (Fast Casual, QSR, etc.)
3. Pull segment benchmark scores
4. Generate gap analysis table with priority scores
5. Add radar chart description to report
6. Include before/after projection table

### Browser Automation Mode (PRIMARY)

**Browser automation via Chrome extension is the preferred method for storefront audits.**

It provides:
- Accurate photo coverage counts (dynamically loaded images render)
- Visual screenshots for reports
- Ability to interact with carousels and category navigation
- Review of actual user experience

**Standard audit flow:**

1. **Connect to browser:**
   ```
   Claude in Chrome:tabs_context_mcp → get tab context
   Claude in Chrome:navigate → go to storefront URL
   ```

2. **Capture hero section:**
   ```
   Claude in Chrome:computer (screenshot) → hero image verification
   ```

3. **Walk each menu category:**
   ```
   Claude in Chrome:computer (left_click) → click category in sidebar
   Claude in Chrome:computer (screenshot) → capture category items
   Repeat for all categories
   ```

4. **Count and document:**
   - Track items with/without photos per category
   - Note any brand consistency issues
   - Capture sample screenshots for report

**If Chrome extension unavailable:**
- Explain limitation to user
- Use web_fetch for basic structure analysis
- Note in report that photo coverage is estimated
- Recommend browser verification before finalizing
