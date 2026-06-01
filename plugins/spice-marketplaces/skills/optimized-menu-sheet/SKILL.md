---
name: optimized-menu-sheet
description: >
  Build an optimized menu sheet (.xlsx) for delivery marketplace clients. The
  sheet is the implementation blueprint that follows a storefront audit: it
  restructures, consolidates, and SKU-rationalizes a restaurant's delivery
  platform menu, with category mapping, price markup logic, photo coverage
  flags, and the recommended hero / featured item ordering. Trigger when the
  user asks to "build menu sheet", "optimized menu for [client]", "menu
  optimization for [client]", "create menu sheet for [client]", "consolidate
  [client]'s menu", "fix [client]'s SKUs", "menu rationalization", "category
  consolidation for [client]", "pricing review for [client]", or any request to
  restructure or optimize a restaurant's delivery platform menu. Use after the
  storefront-audit skill identifies the issues this sheet implements.
---

# Optimized Menu Sheet

The implementation blueprint that follows a storefront audit. Takes a restaurant's current delivery platform menu and produces the restructured version we'll actually ship to Uber Eats, DoorDash, and Grubhub.

## Inputs

1. **Client** — restaurant name
2. **Stores** — list of locations the sheet covers (required)
3. **Focus** — one of `category_consolidation`, `sku_rationalization`, `pricing_review`. Most engagements need all three; the focus selects which gets the deepest treatment in this sheet.
4. **Source menu** — current menu export from the platform (CSV or screenshot tree)

## Output

A single `.xlsx` file with these tabs:

1. **Summary** — what changed and why, with the counts (before / after item counts, category counts, price changes)
2. **Category Map** — current categories → new categories, with a kept / merged / deleted column
3. **Item Detail** — every item with: current name, new name, current price, new price, markup %, category, photo URL, hero candidate flag, modifier group changes, kept / merged / deleted status
4. **Modifiers** — modifier group consolidation (groups with overlap get merged, e.g. "Sauces" + "Dressings" → "Add-ons")
5. **Photo Audit** — items missing photos, items with low-quality photos, items needing reshoots
6. **Hero Recommendation** — top 5 candidates for storefront hero based on AOV contribution, photo quality, brand fit
7. **Implementation Order** — sequence the changes for the operator: Tier 1 (low risk, do first), Tier 2 (medium), Tier 3 (high — needs client approval)

## Process

1. Read the deliverable_contract.json to confirm the schema
2. Pull current menu data (Chrome MCP into UE Manager / DD Merchant Portal / GH for Business, or accept a CSV export)
3. Apply the focus lens (category_consolidation / sku_rationalization / pricing_review)
4. Cross-check against the storefront-audit findings if they exist in Notion
5. Use the xlsx skill to build the workbook
6. Save to the client's Google Drive `/Retention/[Month]/Menu Optimization/` folder
7. Post a Notion doc summarizing changes, link the sheet

## Voice

Follows Maxx's voice rules. See `../../references/maxx-freedman-voice-guide.md` at the plugin root.

## What this skill is NOT

- Not a strategic audit. That's `storefront-audit`.
- Not a campaign brief. That's `campaign-ops` / `campaign-setup`.
- Not the actual platform configuration. The sheet is the spec; an operator implements in the platform.

## Schema (from deliverable_contract.json)

```json
{
  "skill": "optimized-menu-sheet",
  "version": "1.0",
  "params_schema": {
    "type": "object",
    "required": ["stores"],
    "properties": {
      "stores": {"type": "array", "items": {"type": "string"}, "minItems": 1},
      "focus": {"type": "string", "enum": ["category_consolidation", "sku_rationalization", "pricing_review"]}
    }
  }
}
```
