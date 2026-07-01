---
name: retention-qa-checklist
description: Use this skill to run a pre-send QA on any retention campaign before it goes live on Toast, Thanx, or Klaviyo. Triggers include "QA this campaign", "pre-send checklist", "ready to send [campaign]", "verify [campaign] before send", "run QA on [client] campaign", "check this email before it goes", or any request to validate a campaign just before scheduling or activating it. Output is a pass / fail / fix list against 12 checkpoints. If any check fails, the campaign does not go live until fixed. This is the last gate before a send.
---

# Retention QA Checklist

A QA pass takes 10-15 minutes. A bad send takes hours of cleanup, unsubs, and an awkward client call. Always run this.

## Required tools

- Notion MCP (read the brief)
- Slack MCP (escalate if a fail is found)
- **Figma MCP** (`get_screenshot`, `get_design_context` on the final approved design — verify brand consistency, image dimensions, color palette without manual inspection)
- **Klaviyo MCP** (Ahipoki — `get_campaign` to inspect the actual scheduled campaign, confirm segment + send time + template are wired correctly)
- Chrome MCP / Comet (Thanx + Toast platform inspection)

## Inputs

1. **Campaign name** or link to the brief
2. **Platform**: Toast | Thanx | Klaviyo
3. **Send timing**: when the campaign is scheduled
4. **Screenshots or platform access** for visual + functional checks (Figma MCP handles design inspection; Klaviyo MCP handles platform config inspection for Ahipoki)

## Process

Run all 12 checkpoints. Mark each `pass`, `fail`, or `n/a`. If anything is `fail`, fix or escalate before the scheduled send.

### Content checks

**1. Subject + preview text**
- Subject under 50 characters
- Preview text 40-90 characters, not blank
- No emdashes anywhere
- No "Just" / "Quick question" / "Hey there" openers
- Sentence case (unless intentional emphasis)

**2. Body copy**
- Voice rules applied (no AI tells, no watery language)
- Names match the segment ([First Name] tag tested in preview)
- Offer details match the brief (% off, code, validity, minimums)
- No placeholder text left in ("[client]", "[offer]", "TBD")
- Mobile preview readable

**3. Personalization tokens**
- First name token populates correctly
- Loyalty points token populates correctly (if used)
- Last visit token populates correctly (if used)
- Fallback values set for all tokens (e.g. "friend" if first name missing)

### Link checks

**4. Primary CTA link**
- Goes to the right URL
- Includes UTM tags (`utm_source=[platform]&utm_medium=email&utm_campaign=[campaign-name]`)
- Promo code prefilled in URL if applicable

**5. All other links**
- Every link in the email clicks to the right page
- No 404s
- Unsubscribe link present and works
- Privacy policy / terms link present where required

### Visual checks

**6. Hero image**
- Image displays at correct dimensions
- Alt text set (for accessibility + when images blocked)
- Mobile preview not cropped weird
- File size under 200KB

**7. Brand consistency** (Figma MCP if connected)
- Colors match client brand palette (call `get_variable_defs` on the client's Figma brand library, compare to the campaign's hex codes)
- Logo placement standard
- Footer matches latest approved version
- Pull `get_screenshot` of the final design for visual diff against brand library

### Audience + suppression

**8. Segment**
- Segment is the one in the brief
- Size matches expected (within 10%)
- Test send received (send to yourself + Maxx + Daniel for Ahipoki)

**9. Suppression rules applied**
- Unsubscribed excluded
- Recent purchasers excluded (for winback)
- Refund recipients last 14 days excluded
- Parallel flow conflicts checked (no double-hits)

### Send mechanics

**10. Send time**
- Scheduled time matches the brief
- Client timezone correct
- Not during a quiet hour
- Not within 24 hours of another send to the same segment

**11. A/B test setup** (if applicable)
- Test variable defined (subject / preview / CTA / image / time)
- Split is 50/50
- Statistical threshold for winner-pick is set
- Auto-send-winner is enabled OR Harol will manually pick after 24h

**12. Compliance**
- For SMS: STOP / HELP keywords included, brand name in first 30 chars, opt-in confirmed
- For email: CAN-SPAM footer with physical address, unsubscribe link works
- For loyalty offers: terms link works, redemption rules visible

## Output format

```
QA pass for [Campaign name] — [Send date/time]

✅ 1. Subject + preview
✅ 2. Body copy
✅ 3. Personalization tokens
✅ 4. Primary CTA link
✅ 5. All other links
✅ 6. Hero image
✅ 7. Brand consistency
✅ 8. Segment
✅ 9. Suppression rules
✅ 10. Send time
✅ 11. A/B setup (or n/a)
✅ 12. Compliance

Result: ready to send
```

If any check fails:

```
QA pass for [Campaign name] — [Send date/time]

✅ 1-3
❌ 4. Primary CTA link — UTM tag missing
✅ 5-9
⚠️ 10. Send time — scheduled for Sunday 8am, our rule is no Sunday before noon. Push to 12pm?
✅ 11-12

Result: HOLD. Fix item 4. Confirm item 10 with Harol before activation.
```

## Escalation

If a `fail` is found and the send is within 2 hours, DM Harol immediately. If within 24 hours, post in `#retention-marketing` tagging Harol.

If a `fail` involves a suppression issue and the campaign already partially sent, escalate to Maxx immediately. This is the worst-case scenario and needs same-day cleanup.

## What this skill is NOT

- Not a strategic review. The brief was already approved.
- Not a copy edit. The brief is what it is.
- Not a creative review. Dilli already approved the design.

This is a functional check that the campaign will go out correctly. Pure execution gate.
