# Storefront Audit Scoring Rubric

Detailed methodology for scoring 3P delivery storefronts.

## 1. Hero Image Score (0-15 points)

The hero/cover image is the large banner at the top of the storefront, above the restaurant name.

### Presence (0-6 points)
- Present and renders correctly: 6
- Present but low resolution/cropped poorly: 3
- Missing entirely: 0

### Quality Assessment (0-6 points)
Evaluate:
- **Sharpness/Focus**: Clear, not blurry
- **Lighting**: Well-lit, appetizing
- **Composition**: Centered, intentional framing
- **Brand Fit**: Matches restaurant identity

Score:
- Excellent (all criteria): 6
- Good (3 of 4): 4
- Fair (2 of 4): 2
- Poor (<2): 1

### Carousel Legibility (0-3 points)
- Readable at thumbnail size in search results: 3
- Partially legible: 1
- Text/detail lost at thumbnail: 0

---

## 2. Menu Image Score (0-25 points)

**⚠️ VERIFICATION REQUIRED:** Use browser automation (Chrome extension) to count photos per category. Do NOT rely on web_fetch — it misses dynamically loaded images and will produce inaccurate scores.

### Coverage Score (0-10 points)

**How to count:**
1. Click each menu category in the sidebar
2. Count items WITH photo thumbnail vs WITHOUT (text-only)
3. Track in a category table
4. Calculate overall: `images_present / total_items`

**Exclude from count:**
- "Featured items" / "Picked for you" (duplicates from other categories)
- Category header images (not item-level)

Apply 1.5x weight to:
- Top 3 revenue categories (Mains, Combos, Best Sellers)
- Featured/Popular items on platform rails

| Coverage | Score |
|----------|-------|
| ≥90% | 10 |
| 75-89% | 8 |
| 60-74% | 6 |
| 40-59% | 4 |
| 20-39% | 2 |
| <20% | 0 |

### Quality Score (0-10 points)

Evaluate 8 sub-criteria (0-1.25 each, average × 8):
1. Sharpness/Focus
2. Exposure/Lighting
3. Color Accuracy/White Balance
4. Crop/Framing (item centered, no awkward cuts)
5. Resolution/Clarity (no pixelation)
6. Background Cleanliness
7. Styling/Plating (appetizing, no mess/condensation)
8. Platform Fit (renders well in tiles)

Sample: top sellers + 1-2 items per category.

### Consistency Score (0-5 points)

Evaluate 4 sub-criteria (0-1.25 each):
1. **Lighting Consistency**: Similar exposure/temperature
2. **Angle Consistency**: Coherent camera angles
3. **Background Consistency**: Cohesive surfaces/props
4. **Brand Alignment**: Style matches identity

Penalize:
- Title/photo mismatch (wrong protein/portion)
- Description/photo mismatch
- Mixed sources without harmonization

---

## 3. Menu Structure Score (0-20 points)

### Category Count (0-8 points)
| Categories | Score |
|------------|-------|
| ≤9 | 8 |
| 10-12 | 6 |
| 13-15 | 4 |
| 16-20 | 2 |
| >20 | 0 |

### Organization (0-6 points)
- Top sellers/signatures prominently placed: +2
- Logical category order (appetizers → mains → desserts): +2
- Clear, descriptive category names: +2

### Conversion Optimizations (0-6 points)
- Modifiers present (sizes, add-ons): +2
- Bundle/combo offerings: +2
- Clear pricing (no "priced by add-ons" friction): +2

---

## 4. Customer Sentiment Score (0-15 points)

Analyze reviews to surface ops issues, menu problems, and delivery-specific complaints.

### Rating & Velocity (0-5 points)

| Rating | Review Count (30 days) | Score |
|--------|------------------------|-------|
| ≥4.5 | ≥50 | 5 |
| ≥4.5 | 20-49 | 4 |
| 4.2-4.4 | ≥50 | 4 |
| 4.2-4.4 | 20-49 | 3 |
| 4.0-4.1 | Any | 2 |
| <4.0 | Any | 0 |

### Sentiment Theme Analysis (0-6 points)

Sample 20-30 recent reviews. Categorize mentions:

**Positive Themes (amplify via photos/copy):**
- Food quality praise
- Portion size appreciation
- Packaging compliments
- Speed/freshness mentions

**Negative Themes (ops fixes needed):**
- Missing items
- Wrong orders
- Cold/soggy food
- Long wait times
- Packaging failures

Score:
- Predominantly positive, few actionable negatives: 6
- Mixed, clear patterns to address: 4
- Significant negative patterns: 2
- Severe recurring issues: 0

### Delivery-Specific Issues (0-4 points)

Flag and penalize delivery problems that require menu/ops changes:

| Issue Type | Examples | Fix Category |
|------------|----------|--------------|
| Temperature | "Food arrived cold", "Ice melted" | Packaging/batching |
| Structural | "Burger was smashed", "Tacos fell apart" | Packaging/menu design |
| Spillage | "Sauce leaked everywhere" | Container selection |
| Freshness | "Fries were soggy", "Foam collapsed" | Timing/menu removal |

Score:
- No delivery-specific complaints: 4
- Occasional mentions (<10%): 3
- Frequent patterns (10-25%): 1
- Systemic issues (>25%): 0

### Actionable Outputs

For each negative theme, generate:
1. **Root cause** (ops, packaging, menu design, or item)
2. **Recommended fix** (specific action)
3. **Items to consider removing** (if delivery-incompatible)

Example:
> "Poke bowl arrives with everything mixed together" 
> → **Fix:** Compartmentalized container, sauce on side
> → **Menu note:** Add "sauce on side" as default modifier

---

## 5. Promotions Score (0-10 points)

### Active Promotions (0-4 points)
- Multiple strategic promos active: 4
- One promo active: 2
- No promos: 0

### Featured Placement (0-3 points)
- Appears in "Deals", "Offers", or featured rails: 3
- Has promo badge but not featured: 2
- No visibility boost: 0

### Offer Strategy (0-3 points)
Evaluate against best practices:
- Uses threshold ($X off $Y+) vs flat %: +1
- Daypart or category targeting: +1
- New user vs all-user segmentation: +1

---

## 6. Competitive Position Score (0-15 points)

### Pricing Position (0-6 points)
Compare 8-12 anchor items to 2-3 local competitors:
- Strategic positioning (premium justified or value leader): 6
- At parity with no differentiation: 4
- Misaligned (premium price, commodity perception): 2
- Significantly overpriced with no justification: 0

### Ratings Gap (0-5 points)
| Rating vs Competitors | Score |
|-----------------------|-------|
| Higher by 0.3+ | 5 |
| At parity (±0.2) | 3 |
| Lower by 0.3-0.5 | 1 |
| Lower by >0.5 | 0 |

### Differentiation (0-4 points)
- Clear unique value proposition visible: +2
- Signature items highlighted: +2

---

## Score Interpretation

| Total Score | Rating | Recommended Action |
|-------------|--------|-------------------|
| 85-100 | Excellent | Minor optimizations, scale what's working |
| 70-84 | Good | Target 2-3 specific gaps for quick wins |
| 50-69 | Fair | Comprehensive audit and 60-day improvement plan |
| <50 | Poor | Full storefront rebuild recommended |

---

## Platform-Specific Notes

### Uber Eats
- Hero image is the banner directly above restaurant title
- Check "Savings and more" for promo visibility
- Category tiles should be scannable

### DoorDash
- Search "Best Overall", "Top Rated", "Featured" for visibility
- Check if appearing in category pages (Pizza, Asian, etc.)
- Note DashPass eligibility

### Grubhub
- Check "Perks" badge presence
- Note loyalty program integration
- Assess search ranking in category
