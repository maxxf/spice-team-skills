# Platform-Specific CTAs & Deep Links

## Why This Matters

A generic "Order Now" button pointing to `#` ships to production if nobody catches it. The skill must generate platform-specific CTAs with trackable links so the retention specialist can drop in the real URLs and the analytics team can attribute conversions.

---

## CTA Generation Rules

### Step 1: Pull Platform Info from Notion

During the brand context pull (Step 1 of the skill), extract from Service Details:
- Which platforms the client is on (Uber Eats, DoorDash, Grubhub, direct ordering)
- Store/merchant IDs if available in Platform Credentials (Client Wiki)
- Whether the client has a direct ordering URL

### Step 2: Generate Platform-Specific Buttons

**If client is on 1 platform**: Single CTA button with platform name.
**If client is on 2-3 platforms**: Individual buttons for each platform, stacked vertically with 8px gap.
**If client is on 3+ platforms + direct**: Lead with direct ordering CTA (highest margin), then platform buttons at smaller size below.

### Platform Button Styles

Each platform button uses the client's brand colors (not the platform's brand colors — we're not advertising for Uber Eats). But the button text names the platform for clarity.

```html
<!-- Single platform -->
<td style="background-color: [BRAND_PRIMARY]; border-radius: 8px; padding: 16px 48px; text-align: center;">
  <a href="[TRACKING_URL]" style="color: [BRAND_LIGHT]; font-size: 16px; font-weight: 700; text-decoration: none;">
    Order on Uber Eats
  </a>
</td>

<!-- Multi-platform stack -->
<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto;">
  <!-- Primary CTA -->
  <tr>
    <td style="background-color: [BRAND_PRIMARY]; border-radius: 8px; padding: 14px 40px; text-align: center;">
      <a href="[UE_TRACKING_URL]" style="color: [BRAND_LIGHT]; font-size: 15px; font-weight: 700; text-decoration: none;">
        Order on Uber Eats
      </a>
    </td>
  </tr>
  <tr><td style="height: 8px;"></td></tr>
  <!-- Secondary CTA -->
  <tr>
    <td style="background-color: [BRAND_SECONDARY]; border-radius: 8px; padding: 14px 40px; text-align: center;">
      <a href="[DD_TRACKING_URL]" style="color: [BRAND_LIGHT]; font-size: 15px; font-weight: 700; text-decoration: none;">
        Order on DoorDash
      </a>
    </td>
  </tr>
  <tr><td style="height: 8px;"></td></tr>
  <!-- Tertiary CTA -->
  <tr>
    <td style="border: 2px solid [BRAND_PRIMARY]; border-radius: 8px; padding: 12px 40px; text-align: center;">
      <a href="[GH_TRACKING_URL]" style="color: [BRAND_PRIMARY]; font-size: 15px; font-weight: 700; text-decoration: none;">
        Order on Grubhub
      </a>
    </td>
  </tr>
</table>
```

### Platform Priority Order

When stacking buttons, order by client's platform priority (from Service Details goals). Default order if not specified:
1. Direct ordering (highest margin for client)
2. Uber Eats (typically largest volume)
3. DoorDash
4. Grubhub

---

## UTM Structure

Every CTA link must include UTM parameters for attribution. Use this structure:

```
[BASE_URL]?utm_source=email&utm_medium=retention&utm_campaign=[CAMPAIGN_SLUG]&utm_content=[VARIANT]
```

### Parameter Definitions

| Parameter | Value | Example |
|-----------|-------|---------|
| `utm_source` | Always `email` | `email` |
| `utm_medium` | Always `retention` | `retention` |
| `utm_campaign` | `[client]-[type]-[month][year]` lowercase, hyphenated | `everytable-summer-lto-apr2026` |
| `utm_content` | `variant-a` or `variant-b` + platform | `variant-a-ubereats` |

### Example Full URLs

```
# Uber Eats
https://www.ubereats.com/store/everytable-xxx?utm_source=email&utm_medium=retention&utm_campaign=everytable-summer-lto-apr2026&utm_content=variant-a-ubereats

# DoorDash
https://www.doordash.com/store/everytable-xxx?utm_source=email&utm_medium=retention&utm_campaign=everytable-summer-lto-apr2026&utm_content=variant-a-doordash

# Grubhub
https://www.grubhub.com/restaurant/everytable-xxx?utm_source=email&utm_medium=retention&utm_campaign=everytable-summer-lto-apr2026&utm_content=variant-a-grubhub
```

### Placeholder Format

Since the exact store URLs vary by location, generate UTM-ready placeholders:

```html
href="[UE_STORE_URL]?utm_source=email&utm_medium=retention&utm_campaign=everytable-summer-lto-apr2026&utm_content=variant-a-ubereats"
```

The retention specialist fills in `[UE_STORE_URL]` from the client's Platform Credentials in Notion. The UTM parameters are already built.

---

## Platform Availability Line

Below the CTA buttons, always include a text line confirming where the food is available:

```html
<p style="margin: 12px 0 0 0; font-size: 13px; color: [BRAND_MUTED_TEXT];">
  Available on [PLATFORM 1], [PLATFORM 2] & [PLATFORM 3] at all [X] locations
</p>
```

This line pulls from the brand context (platforms + location count).

---

## Promo Code Handling

If the campaign includes a promo code:

```html
<!-- Code callout above CTA -->
<td style="padding: 0 40px 12px 40px; text-align: center;">
  <div style="background-color: [BRAND_LIGHT_BG]; border: 1px dashed [BRAND_PRIMARY]; border-radius: 8px; padding: 12px 24px; display: inline-block;">
    <span style="font-size: 12px; color: [BRAND_MUTED]; text-transform: uppercase; letter-spacing: 1px;">Use code</span><br>
    <span style="font-size: 20px; font-weight: 800; color: [BRAND_PRIMARY]; letter-spacing: 2px;">[PROMO_CODE]</span>
  </div>
</td>
```

Place the code block directly above the platform CTAs. The code is visually distinct (dashed border, larger font) so it's easy to spot and copy.
