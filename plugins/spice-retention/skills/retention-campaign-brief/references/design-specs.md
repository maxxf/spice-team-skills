# Design specs (for #design-requests briefs)

## Email hero image

- **Width**: 600px (standard email width)
- **Height**: 300-400px for hero, 200-250px for secondary blocks
- **Format**: PNG or JPG. PNG for anything with text overlay, JPG for photography-only.
- **File size**: under 200KB per image. Large hero images kill mobile load times.
- **Retina considerations**: deliver at 2x (1200px wide) and let email client downscale.

## Subject line + preview text

- Subject: 30-50 characters. Mobile previews truncate at ~30 on iPhone.
- Preview text: 40-90 characters. Appears next to subject in inbox. Never leave this blank — Gmail will pull random body text.

## SMS

- Max 160 characters per message. Carriers split longer.
- Include brand name in first 30 chars. Carriers strip the From field.
- Always include "Reply STOP to opt out" in first message of any series.
- Short links via the platform's URL shortener so clicks are tracked.

## Push notification

- Title: 30-40 characters
- Body: 100 characters max
- Image (Thanx supports): 600x300 PNG

## Logo + brand colors

Pull from each client's Google Drive brand assets folder. Maintained by Dilli.

- **MBFS**: warm Middle Eastern palette. Primary red + cream + black accents.
- **HealthNut**: green + cream. Wellness-adjacent but not yoga-studio.
- **Ahipoki**: teal + coral. Beach / California energy.

If brand colors are not on file, ask Dilli before mocking up.

## Brief format for #design-requests

```
:art: New retention brief — [Campaign name]

*Client*: [Client]
*Send date*: [Date]
*Design deadline*: [Send date minus 5 business days]
*Brief link*: [Notion URL]

*Hero direction*: [one sentence]
*Specs*: Email 600x350, PNG. Mobile-first. Brand colors from [client] folder.
*Body imagery*: [if applicable, what else needs to be designed]

*Assets needed from client*: [if any]

Brief by: Harol
Designer: Dilli
Strategy Lead: [Daniel for Ahipoki | none for HealthNut / MBFS]
```

## Lead time non-negotiables

- Standard campaign: 5 business days from brief to send.
- Rush request: only with Maxx + Dilli double-approval. Adds rework risk.
- Multi-asset campaign (email + SMS + push): 7 business days.
- Klaviyo flow rebuild: 10 business days from brief.
