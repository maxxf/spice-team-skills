# Kickoff Email Templates

## Delivery Marketplaces / Multi-Service Email

This email is sent by Maxx or Diline immediately after SOW signature. It introduces the onboarding lead (Diline) and hands off the relationship for onboarding. Real-world subject line pattern: "Onboarding: {restaurant_name} <> Spice".

### Variables

| Variable | Source | Example |
|----------|--------|---------|
| `{first_name}` | Client POC first name from Notion client record | Matan |
| `{restaurant_name}` | Client Name from Notion | Westville |
| `{cs_lead_name}` | Client Services Lead first name (default: Diline) | Diline |
| `{cs_lead_email}` | Client Services Lead email (default: diline@spicedigital.co) | diline@spicedigital.co |
| `{onboarding_form_link}` | Static: https://spice-digital.notion.site/1c8d3ff018e780f5821ff8b52e709724 | — |
| `{stripe_payment_link}` | Generated per-client in Stripe | https://buy.stripe.com/XXXX |
| `{client_portal_link}` | Client space URL in Notion (created during onboarding) | https://www.notion.so/spice-digital/Westville-NYC-326d3ff0... |
| `{kickoff_date}` | Scheduled via Calendly or manual coordination | Date TBD |

### Template

```
Subject: Onboarding: {restaurant_name} <> Spice

{first_name},

Welcome to Spice. To get moving we need your platform logins and payment info by Friday. Everything else follows from those two.

{cs_lead_name} (copied) runs onboarding and is your day to day from here. This week:

- Logins and brand assets: {onboarding_form_link}
- Payment: {stripe_payment_link}
- Kickoff call: {kickoff_date}
- Shared Slack or WhatsApp, whichever your team actually checks

Once payment is in, your client portal lives here: {client_portal_link}

{human_line}

// maxx freedman | managing partner | Spice
```

`{human_line}` is a required merge slot, not decoration. One sentence naming something
specific from the sales conversation: a store that is struggling, a number they quoted,
a problem they said keeps them up. A static template cannot write it, which is exactly
why it is a slot. Do not send this email with the slot unfilled.

### Notes

- These are static templates, so the governor at `references/client-comms-pass.md` runs
  over this file when a template changes rather than on every send. Both templates above
  were checked against it and against `references/client-comms-style.md`.
- CC {cs_lead_email} on the email
- After this email, the Client Services Lead takes over all client communication
- Maxx's next touchpoint is the kickoff call itself (handoff moment)
- If the client has special billing (net-15), note that in the email body near the payment link
- For Advisory-only clients, the email is slightly different (Maxx stays as primary, no Client Services intro)

## Advisory-Only Email

For clients purchasing only Advisory services, Maxx remains the primary contact. No Client Services handoff.

```
Subject: Onboarding: {restaurant_name} <> Spice

{first_name},

Welcome to Spice. One thing to start: payment info at {stripe_payment_link} this week.

I am your direct contact on this engagement, no handoff to anyone else. Our recurring
call is {kickoff_date}, and I will follow up separately for the docs I need before the
first working session.

{human_line}

// maxx freedman | managing partner | Spice
```

Same rule on `{human_line}`: required, and only a person who sat through the sales
conversation can write it.
