---
name: optimized-menu-sheet
description: Build an optimized menu sheet (.xlsx) for delivery marketplace clients. Trigger when asked to "build menu sheet", "optimized menu", "menu optimization for [client]", "create menu sheet for [client]", or any request to restructure, consolidate, or optimize a restaurant's delivery platform menu. This is the implementation blueprint that follows a storefront audit.
---

# Optimized Menu Sheet Skill

Generate a comprehensive, client-ready menu optimization workbook (.xlsx) for delivery marketplace clients. This is the actionable implementation document that tells the client exactly what to change, item by item, category by category.

This deliverable typically follows a storefront audit. The audit diagnoses problems; this sheet prescribes the fix.

## When to Use

- "Build a menu sheet for [client]"
- "Optimize [client]'s menu"
- "Create the menu optimization for [client]"
- "Restructure their DoorDash/Uber Eats menu"
- "Consolidate [client]'s categories"
- After any storefront audit where menu structure scored below 16/20

## Inputs Needed

Before building, gather this information (ask the GM if not provided):

1. **Client name** (required)
2. **Platform(s)** to optimize (Uber Eats, DoorDash, Grubhub, or all)
3. **Current menu data** via one of:
   - Browser automation: browse the storefront and scrape the full menu
   - Client-provided menu export (CSV, Excel, or PDF)
   - Storefront audit data (if recently completed)
4. **Known issues** from storefront audit or GM observations (optional but helpful)
5. **Client POC name and role** (for the ownership table)
6. **Spice Growth Manager name** (for the ownership table)

## Workflow

### Step 1: Collect Current Menu Data

**Preferred method: Browser automation via Claude in Chrome**

1. Navigate to the client's primary delivery platform storefront
2. Walk every menu category and capture:
   - Category name
   - Every item: name, description, price, photo (yes/no), modifiers
3. Count total SKUs, total categories
4. Note any items with high error rates (visible in reviews)
5. Check ratings and recent reviews for delivery/quality complaints

If browser unavailable, work from whatever data the GM provides.

### Step 2: Analyze and Strategize

Before building the sheet, determine:

**Category Strategy:**
- Target: 8 categories maximum (conversion drops 15%+ above 9)
- Category names should match search terms customers actually type
- Identify categories to KEEP, MERGE, or KILL
- Every merge needs a rationale tied to search behavior

**SKU Rationalization:**
- Target: reduce active SKUs by 30-40% from current count
- Identify dead SKUs (zero or near-zero sales, ask GM for data)
- Identify high-error-rate items to HIDE until ops fixes them
- Keep top sellers and high-margin items

**Title & Description Optimization:**
- Titles should include searchable keywords
- Descriptions should be 1-2 sentences with inline health/dietary tags
- Health tags: Gluten-Free, Vegan, High Protein, Dairy-Free, Low Calorie, Plant-Based, etc.

**Bundle Opportunities:**
- Bundles increase AOV by 12-20%
- Design 3-5 bundles targeting different customer segments
- Each bundle should save the customer $2-10 vs buying separately

### Step 3: Build the Workbook

Generate the Excel file using openpyxl (`python3 -m pip install openpyxl` if missing). The workbook has exactly 7 tabs in this order:

1. **Cover** — client name, date, Spice GM owner, scope (which platform[s]), 90-day target outcome, one-paragraph executive summary
2. **Full Menu** — every item: Category | Original Name | Optimized Title | Description | Price | Photo Y/N | Health Tags | Action (KEEP / EDIT / HIDE / KILL) | Notes
3. **Categories** — Current Category | Current SKU Count | Target Category | Target SKU Count | Rationale (search-behavior tied) | Action (KEEP / MERGE / KILL)
4. **Items to Remove** — two sections:
   - *Dead SKUs* (zero/near-zero sales): Name | Last 30d Orders | Recommendation
   - *High-Error Items* (flagged by reviews/ops): Name | Error Rate or Review Quote | Recommendation (HIDE until ops fix)
5. **Bundles** — Bundle Name | Component Items | Bundle Price | Standalone Total | Customer Savings | Target Audience | Platform | Rollout Week
6. **Image Guidelines** — DO/DON'T table (composition, lighting, plating, props) + per-meal-type guidance (breakfast / entrée / dessert / drink). Reference internal Notion design hub if available.
7. **Timeline + Success Metrics** — Week-by-week task list with owners (Spice / Client / Both) AND a Success Metrics section: Metric | Current Baseline | 30-Day Target | 60-Day Target | Actual (blank for client to fill).

**Important formatting rules:**
- Use Arial font throughout
- Header rows: dark background (#1B1B3A), white bold text, size 11
- Sub-header rows (section dividers): yellow/gold background (#FFF2CC), black bold text
- Data rows: alternating white / light gray (#F5F5F5) for readability
- Column widths: auto-fit to content, minimum 15 characters
- Freeze top rows (headers) on every tab
- No merged cells except title row on each tab

### Step 4: Save and Deliver

1. Save the workbook as `[Client Name] | Optimized Menu Sheet.xlsx`
2. Place in the user's workspace folder
3. Provide a link to the file
4. Summarize key changes: how many categories reduced to, SKUs removed, bundles added, and estimated impact

## Output Quality Checks

Before delivering, verify:
- [ ] All 7 tabs present and populated
- [ ] Category count is 8 or fewer in the optimized structure
- [ ] Every item in Full Menu tab has: category, original name, optimized title, description, price, health tags
- [ ] Items to Remove has both "dead SKUs" and "high error rate" sections
- [ ] Bundles have components, pricing, savings, and target audience
- [ ] Timeline has realistic week-by-week tasks with owners
- [ ] Success Metrics has current baselines and 30/60 day targets with blank "Actual" columns
- [ ] Image Guidelines has both DO/DON'T table and visual style guidance per meal type

## References

- Tab structure + column definitions are inlined in Step 3 above (no external file dependency).
- Voice / brand rules for the Cover tab summary: `references/maxx-freedman-voice-guide.md` in this repo.
