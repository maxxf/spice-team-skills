# Payment Collections Automation

## Overview

Weekly scheduled agent that identifies payment issues across all clients and drafts follow-up emails for Cesar or finance@spicedigital.co to send.

**Schedule:** Every Monday at 9:00 AM
**Posts to:** #spice-actions (summary) + drafts emails for review
**Sender:** finance@spicedigital.co or Cesar (cesar@spicedigital.co)

## Detection Logic

### Step 1: Pull all active clients from Notion

```
Tool: notion-search
data_source_url: collection://1c8d3ff0-18e7-80e9-8381-000b4448cb87
Filter: Status = "Onboarding" OR "Active"
```

### Step 2: Check each client's payment status in Stripe

For each client with a Stripe Customer ID:

```
Tool: list_subscriptions
customer: [cus_XXXX]
status: all
```

Categorize into:

| Scenario | Detection | Priority |
|----------|-----------|----------|
| **A: Never set up payment** | Client in Notion with Status "Onboarding" or "Active" but no Stripe Customer ID, OR Stripe customer exists but no subscription found | High |
| **B: Failed charge** | Subscription status = `past_due` or `unpaid` | High |
| **C: Past-due invoice** | Open invoice with `due_date` in the past and status != `paid` | Medium |
| **D: Expiring card** | Default payment method card expiring within 30 days | Low (preventive) |

### Step 3: Draft follow-up emails

**Scenario A: Never set up payment**

```
Subject: Payment setup for {restaurant_name}

Hi {first_name},

We're getting started on {restaurant_name}'s onboarding and want to make sure billing is squared away.

Here's the link to set up your subscription: {payment_link}

Once that's done, we'll have everything we need on our end. Let us know if you run into any issues.

Thanks,
Cesar Cerda
Head of Client Services
Spice Digital
```

**Scenario B: Failed charge**

```
Subject: Payment update needed - {restaurant_name}

Hi {first_name},

The most recent charge for {restaurant_name}'s account didn't go through. Could you update your payment method here: {customer_portal_link}

If there's an issue on our end, let us know and we'll sort it out.

Thanks,
Cesar Cerda
Head of Client Services
Spice Digital
```

**Scenario C: Past-due invoice (net-15)**

```
Subject: Invoice #{invoice_number} past due - {restaurant_name}

Hi {first_name},

Invoice #{invoice_number} for {restaurant_name} was due on {due_date} and is currently outstanding at {amount}.

Invoice link: {invoice_url}

We'd like to get this resolved this week. Let us know if there's anything we need to discuss.

Thanks,
Cesar Cerda
Head of Client Services
Spice Digital
```

**Scenario D: Expiring card (preventive)**

```
Subject: Card update needed - {restaurant_name}

Hi {first_name},

Quick heads up: the card on file for {restaurant_name} expires {expiry_month}/{expiry_year}. To avoid any interruption, you can update it here: {customer_portal_link}

Takes 30 seconds. Thanks!

Cesar Cerda
Head of Client Services
Spice Digital
```

### Step 4: Escalation logic

- **First notice:** Send Scenario email (Monday after detection)
- **Second notice (1 week later):** Resend with slightly firmer tone, CC Maxx
- **Third notice (2 weeks later):** Escalate to Maxx for direct outreach. Post to #spice-actions.

Track escalation level in the Slack summary so Cesar knows which clients have been contacted before.

### Step 5: Post summary to Slack

Post to #spice-actions:

```
**Weekly Payment Status - [Date]**

**Needs attention (3 clients):**
- Westville: No payment link clicked (onboarding Day 5). Draft email ready.
- Fresh Kitchen: Failed charge on Mar 14. Second notice. Draft email ready.
- Everytable: Invoice #INV-1234 past due by 8 days ($4,225). Draft email ready.

**Healthy (17 clients):**
All subscriptions active, no issues.

**Preventive:**
- Capriotti's: Card expires Apr 2026. Heads-up email drafted.
```

## Email Tone Guidelines

Follow Maxx's communication defaults for late payment/escalation:
- State the problem immediately
- Clear ask
- No softening, no guilt trips, no threats
- Include the link
- "Thank you" or "Thanks" to close
- No "I hope this finds you well" or "Just circling back"

## Stripe Tools Used

| Action | Tool |
|--------|------|
| List all subscriptions | `list_subscriptions` |
| List invoices | `list_invoices` |
| Search customers | `search_stripe_resources` |
| Check payment intents | `list_payment_intents` |
| Get account info | `get_stripe_account_info` |
