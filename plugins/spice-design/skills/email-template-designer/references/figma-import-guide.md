# Figma Import Guide for Email Templates

## How to Get HTML Email Templates into Figma

### Option A: html.to.design Plugin (Recommended)

**Setup (one-time):**
1. Open Figma
2. Go to Community > Plugins > search "html.to.design"
3. Install the plugin (free tier works fine)

**Per-email workflow:**
1. Open the HTML file in Chrome (double-click or drag to browser)
2. In Figma, create a new frame (600px wide)
3. Run html.to.design plugin (Right-click > Plugins > html.to.design)
4. Choose "Import from URL" and paste the local file URL, or "Import from Code" and paste the HTML
5. The plugin converts the email to editable Figma layers

**After import:**
- Swap `[IMAGE]` placeholder divs with actual food photography
- Replace system fonts with exact brand fonts
- Fine-tune spacing, colors, and sizing
- Group and organize layers into components

### Option B: Direct Figma MCP

If the Figma MCP connector is active, Claude can push designs directly using `generate-design-structured`. This skips the HTML step entirely but requires the MCP connection.

### Option C: Screenshot + Rebuild

For quick turnarounds:
1. Open HTML in Chrome at 2x zoom
2. Screenshot (Cmd+Shift+4 on Mac)
3. Place in Figma as a reference layer at 50% opacity
4. Rebuild on top using Figma's native tools
5. Delete the reference layer when done

This is fastest for simple layouts where you just need the structure as a starting point.

---

## Post-Import Checklist

After getting the template into Figma:

- [ ] All placeholder images replaced with actual food photography
- [ ] Brand fonts applied (not just system fallbacks)
- [ ] Colors match client brand kit exactly
- [ ] CTA button size/padding feels right on mobile preview
- [ ] Footer legal text is accurate for the client
- [ ] Unsubscribe link text is present
- [ ] Social links point to correct client profiles
- [ ] Template saved to the client's Figma project folder
- [ ] If Brand Library exists, template added to the library file

---

## File Naming Convention

HTML files: `[ClientName] - [EmailType] - [MonthYear].html`
Figma frames: `[ClientName] / Email / [EmailType] - [MonthYear]`

Email types: LTO Launch, BOGO, Seasonal, Win-Back, Loyalty, Grand Opening

---

## Tips for Clean Figma Import

1. **Table-based HTML imports better** than flexbox/grid. The templates are built with tables specifically for this reason (and email client compatibility).

2. **Inline styles import cleanly**. No external CSS means the plugin captures everything.

3. **600px width is standard**. Don't resize the HTML before import. Scale in Figma after.

4. **Image placeholders convert to rectangles** in Figma. Just swap the fill from color to image.

5. **Text layers are editable** after import. Copy changes happen in Figma, not back in the HTML.
