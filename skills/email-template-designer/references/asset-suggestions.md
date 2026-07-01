# Asset Library Image Suggestions

## The Problem with Placeholders

Image placeholders with descriptive text (e.g., `[IMAGE: Overhead shot of mango bowl...]`) are useful for communicating intent. But they leave the designer hunting through folders, Figma files, and Notion databases to find actual photos that match. At 5-10 emails per week, that's 10-20 image searches per week wasted.

## The Fix

During the brand context pull, also search the client's Creative Assets / Asset Library and surface specific images that match the campaign's needs. The designer gets a shortlist, not a scavenger hunt.

---

## Where Client Images Live

### In Notion

1. **Creative Assets / Asset Library** (inline database in Client Portal)
   - Tagged by type: hero image, food photography, lifestyle, packaging, team
   - May include Figma file links, Google Drive links, or direct uploads
   - Search: Look for the "Asset Library" or "Creative Assets" data-source-url in the portal

2. **Campaign Planner entries** (past campaigns)
   - Each campaign entry may have attached screenshots, design files, or photo references
   - Search: Filter Campaign Planner by client name, look for "Files & Media" property

3. **Hero Image Review pages**
   - Contain detailed photography analysis, compositions, and reference images
   - Often link to specific photo shoot assets (e.g., "Plated" folder references)
   - Search: Already in the standard search sequence (step 6)

4. **Document Hub**
   - Brand books sometimes embed example photography or link to asset folders
   - Style guides may reference specific hero images by filename

### In Figma

If the client has a Brand Library Figma file:
- Check via Figma MCP: `search-designs` for "[Client Name] Brand" or "[Client Name] Assets"
- Pull asset thumbnails from the library file

### External

- Google Drive links referenced in Notion entries
- Client's website (hero images, menu photos) via Chrome MCP
- Instagram feed (if linked in Client Wiki)

---

## Search Sequence for Assets

Add these steps after the standard brand context search:

```
# After step 8 of the standard sequence:

9.  notion-fetch: Creative Assets / Asset Library database from portal
    → Extract all entries, note filenames, tags, and any URLs
    
10. For each Campaign Planner entry from the past 90 days:
    → Check for attached files/media
    → Note which images were used (prevents accidental reuse)

11. If hero image review exists:
    → Extract specific photo references (filenames, folder names)
    → Note photography direction (angles, compositions, backgrounds)
    → These are the highest-quality image direction available

12. If Figma Brand Library exists for client:
    → Search Figma for "[Client Name]" designs
    → Pull asset names from the library file
```

---

## How to Present Image Suggestions

After the brand brief, present an image suggestion section:

```
AVAILABLE ASSETS: [Client Name]

Hero image candidates:
1. [filename/description] — from [source: Asset Library / Campaign X / Hero Review]
   Match quality: HIGH / MEDIUM / LOW for this campaign
   
2. [filename/description] — from [source]
   Match quality: HIGH / MEDIUM / LOW

Secondary image candidates:
1. [filename/description] — from [source]
   Match quality: HIGH / MEDIUM / LOW

Recently used (avoid reuse):
- [filename] — used in [Campaign Name, Date]
- [filename] — used in [Campaign Name, Date]

Missing: [describe what's needed but not in the library]
→ Recommend: [new photo shoot / stock source / AI generation via Pixa]
```

### Match Quality Criteria

- **HIGH**: Image matches the campaign's subject, composition style, and brand aesthetic. Can be used as-is or with minor cropping.
- **MEDIUM**: Right subject but wrong angle, wrong background, or different style than the campaign needs. Usable with editing.
- **LOW**: Same food category but doesn't match the specific campaign vision. Fallback only.

---

## Placeholder Enhancement

When generating HTML, enhance placeholders with asset references:

```html
<!-- Before (generic placeholder) -->
<div style="color: #4db8ab; font-size: 13px; font-style: italic;">
  [IMAGE: Overhead shot of mango chicken bowl. Teal background.]
</div>

<!-- After (placeholder with asset reference) -->
<div style="color: #4db8ab; font-size: 13px; font-style: italic;">
  [IMAGE: Overhead shot of mango chicken bowl. Teal background.
   SUGGESTED: "Chili Crisp Noodles Sesame Chicken-1.jpg" from Plated folder
   (referenced in Hero Image Review Apr 2026). Crop to center bowl.]
</div>
```

This gives the designer a starting point. They can use the suggested image or find a better one, but they're not starting from zero.

---

## When Assets Are Missing

If the client's asset library is empty or sparse:

1. **Flag it in the brand brief**: "Asset Library: SPARSE — [X] images available, none match this campaign."
2. **Recommend action**:
   - If the client has a photo shoot scheduled: "Wait for new assets from [date]"
   - If no shoot planned: "Recommend lightweight photo shoot or Pixa AI generation"
   - For AI generation: Reference Spice Brand Guidelines for AI Asset Generation (page ID: 306d3ff0-18e7-8103-86ec-f69a373553b8)
3. **Generate the template anyway** with strong placeholder direction. The template is still useful for copy approval and layout approval even without final photography.
