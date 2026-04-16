# Kickoff Email Templates

## Delivery Marketplaces / Multi-Service Email

This email is sent by Maxx (or the salesperson) immediately after SOW signature. It introduces Cesar as Head of Client Services and hands off the relationship for onboarding.

### Variables

| Variable | Source | Example |
|----------|--------|---------|
| `{first_name}` | Client POC first name from Notion client record | Matan |
| `{restaurant_name}` | Client Name from Notion | Westville |
| `{cesar_email}` | Always: cesar@spicedigital.co | cesar@spicedigital.co |
| `{onboarding_form_link}` | Static: https://spice-digital.notion.site/1c8d3ff018e780f5821ff8b52e709724 | — |
| `{stripe_payment_link}` | Generated per-client in Stripe | https://buy.stripe.com/XXXX |
| `{client_portal_link}` | Client space URL in Notion (created during onboarding) | https://www.notion.so/spice-digital/Westville-NYC-326d3ff0... |
| `{kickoff_date}` | Scheduled via Calendly or manual coordination | Date TBD |

### Template

```
Subject: Welcome to Spice! - {restaurant_name} Onboarding

{first_name} — allow me to formally welcome you to Spice. We are excited to be partnering with you and {restaurant_name}!

Over the next week, we will be organizing internally by assigning more Spice members to your team, gathering assets from you, and taking time to understand your business in a more comprehensive way, building on our initial calls together.

In order to streamline this process, I'd like to introduce you to Cesar (copied), Spice's Head of Client Services, to coordinate the following:

- Scheduling Kick-off call: {kickoff_date}
- Setting up shared Slack / WhatsApp for communications
- Gathering your platform login credentials & brand assets: {onboarding_form_link}
- Collecting payment info: {stripe_payment_link}
  - Once payment info is added, save this link for client portal access: {client_portal_link}

Please be sure to set some time aside to prep this info for us.

Thank you!
```

### Notes

- CC cesar@spicedigital.co on the email
- After this email, Cesar takes over all client communication
- Maxx's next touchpoint is the kickoff call itself (handoff moment)
- If the client has special billing (net-15), note that in the email body near the payment link
- For Advisory-only clients, the email is slightly different (Maxx stays as primary, no Cesar intro)

## Advisory-Only Email

For clients purchasing only Advisory services, Maxx remains the primary contact. No Cesar handoff.

```
Subject: Welcome to Spice! - {restaurant_name}

{first_name} — welcome to Spice. Excited to get started with {restaurant_name}.

I'll be your direct point of contact for our advisory engagement. Here's what's next:

- Scheduling our recurring call: {kickoff_date}
- Collecting payment info: {stripe_payment_link}
- I'll be reaching out separately to gather docs and context for our first working session.

Looking forward to it.
```
