---
name: onboarding-status-check
description: Check onboarding task status across all clients, detect form submissions, migrate credentials into Platform Credentials DB + Client Wiki + Client page, and post updates to client #int- channels and #new-client-onboarding. Use this skill whenever the user mentions "onboarding status check", "who's behind on onboarding", "check onboarding tasks", "onboarding health check", "any overdue onboarding tasks", "check if [client] filled out their form", "migrate onboarding credentials", "process onboarding forms", or any request to review client onboarding progress, detect form submissions, or migrate credentials from onboarding forms into Notion.
---

> **Spicy Nugget handoff:** This runs on Mac Mini as Onboarding Status Check (Tue/Thu 9:00am PT). Don't run on laptop unless Spicy is down.

Run an onboarding status check for all Spice clients. Here is exactly what to do:

1. Get today's date in PT timezone.

2. Query the Notion Client Onboarding database for all incomplete tasks:
   - Use notion-search with query "onboarding" and data_source_url: collection://239d3ff0-18e7-8041-84d2-000b393bcc69
   - Filter for: Status != "Done", Status != "N/A", has a Client assigned
   - Fetch full task details to get Due Date values
   - For each task, also fetch the linked Client page to get: Client Name, Client Email, SOW Start Date, and the client page URL (needed for relations later)

3. **Onboarding Form Detection & Data Migration:**
   For each client that has an incomplete "Client completes onboarding form w/ login credentials" task:

   a. **Check for form submission:** Search the Onboarding Form DB (data_source_url: collection://1c8d3ff0-18e7-80df-a6ac-000bdaba588c) for the client's business name. Fetch any matching response.

   b. **If a form response exists, run the full migration:**

      **i. Create entries in DB: Platform Credentials** (collection://f99b8707-392b-4862-95cd-e29863276fb0):
      - Parse the "Delivery Platform - Logins" field. Clients write credentials in various formats:
        - Labeled block: "Uber Eats\nUN: email@domain.com\nPW: password123"
        - Inline: "Uber Eats: email@domain.com / password123"
        - Shorthand: "UE: email / pass, DD: email / pass, GH: email / pass"
        - Free text with platform names mixed in
      - For each platform credential found, create a page in Platform Credentials DB with:
        - Name: "[Client Name] - [Platform]" (e.g., "Westville - Uber Eats")
        - Platform: Match to one of [DoorDash, Grubhub, Uber Eats, Toast, OLO, Punchh, Attentive, Loop AI]
        - Email: extracted login email
        - Password: extracted password
        - Client: relation to the client page URL (format: JSON array, e.g., ["https://www.notion.so/abc123..."])
        - Notes: any extra context from the form field that didn't fit cleanly into email/password
      - Also parse "Point of Sale / Integrator - Logins" and "Direct Ordering Platform - Login" the same way. Use the best-matching Platform option, or put the platform name in the Name field if no match (e.g., "Westville - Square").
      - Parse "Email Marketing Platform - Login" and "Website Platform - Login" similarly.
      - If a credential can't be cleanly parsed (e.g., "ask Morgan for DD login"), create the entry anyway with whatever info is available and add a Note flagging it needs manual review.
      - **Platform matching notes:** Platforms like Thanx, Square, Deliverect, Shopify don't have a dropdown match. Use the closest option (e.g., Attentive for Thanx) and note the actual platform name in the Name field and Notes.
      - **Deduplication:** If a client has multiple locations, form submissions may share the same credentials. Check for existing entries before creating duplicates.

      **ii. Update the Clients DB** (collection://1c8d3ff0-18e7-80e9-8381-000b4448cb87):
      - Set "Client Email" to the form's "Main Point of Contact - Email" value (if currently empty)
      - Do NOT overwrite existing Client Email if already populated

      **iii. Add entries to the Client Wiki** (the inline database inside each client's page, found under the "Client Wiki" toggle):
      - Fetch the client page to find the Client Wiki data source URL (look for `<database>` tags with "Client Wiki" or "New database" title inside the client page content)
      - Create entries for:
        - Name: "Brand Assets Folder", URL: value from form's "Brand Assets Folder" field
        - Name: "Menu Images Folder", URL: value from form's "Menu Images Folder" field
        - Name: "Platform Contacts", URL: (leave blank, put the "Delivery Platforms - Contacts" text in the page body as content)
        - Name: "Main POC: [Name]", URL: "mailto:[email]" using form's POC name and email
      - Skip any entry where the form field was left blank

      **iv. Mark the onboarding task as Done:**
      - Use notion-update-page to set the Status of the "Client completes onboarding form" task to "Done"
      - Add a note to the task's "Notes / Links" field: "Auto-processed [today's date]. Credentials migrated to Platform Credentials DB. Client page and Wiki updated."

      **v. Add a migration summary line to the Slack post for that client:**
      "✅ Onboarding form submitted -- credentials migrated to Platform Credentials DB, client page updated, task marked Done."

   c. **If NO form response exists:**
      - Leave the task status as-is
      - If the task is 3+ days overdue and still marked "Not Started", recommend changing status to "Waiting on Client" in the Slack post:
        "📝 Onboarding form not yet submitted. Consider updating status to 'Waiting on Client' and nudging [POC name]."

4. Categorize each task by how overdue it is:
   - 🚨 Blocker: Due Date < today by 5+ days. Tag @maxx in the message. Something is stuck.
   - 🔴 Overdue: Due Date < today by 3-4 days. Action needed.
   - ⚠️ At Risk: Due Date = today, tomorrow, or 1-2 days ago (recently past due but not yet 3 days).
   - ✅ On Track: Due Date > tomorrow.
   - If a task has no explicit Due Date (date:Date:start is empty), calculate it from SOW Start Date + Days After Start.
   - If both are missing, categorize as "No due date" and note it.

5. Stale task detection: If a task is 3+ days overdue and still marked "Not Started", flag it with: "⚠️ Still marked Not Started -- may need a status update in Notion." The team sometimes finishes tasks without updating the status.

6. Client nudge drafts: For any task that is 3+ days overdue and has status "Waiting on Client" (e.g., onboarding form, credentials, platform access), draft a short follow-up message using slack_send_message_draft in the client's external channel (#ext-[client]-spice). Search for the channel using slack_search_channels with channel_types "public_channel,private_channel". Format:
   "Hey [Client POC first name], quick follow-up on [specific item needed]. We're ready to move forward on [next step] as soon as we have [the thing]. Can you send that over this week?"
   These are DRAFTS only -- team lead reviews and sends.

7. Post client-specific updates to each client's internal Slack channel (#int-[client-name]). IMPORTANT: Search for channels using slack_search_channels with channel_types "public_channel,private_channel" since #int- channels may be private. Format:

*📋 [Client Name] Onboarding Update -- [Date]*

🚨 Blockers: [X] | 🔴 Overdue: [X] | ⚠️ At Risk: [X] | ✅ On Track: [X]

*🚨 Blockers (5+ days overdue):*
• [Task Name] -- *<@[owner-slack-id]>* -- due [Date] ([X] days late) *<@maxx>*
  ↳ [Note: may need status update, or is genuinely stuck]

*🔴 Overdue (3+ days):*
• [Task Name] -- *<@[owner-slack-id]>* -- due [Date] ([X] days late)

*⚠️ At Risk (due today/tomorrow or 1-2 days past):*
• [Task Name] -- *<@[owner-slack-id]>* -- due [Date]

If any credentials were migrated during this run, add:
✅ Onboarding form processed -- credentials migrated to Platform Credentials DB, client page updated.

If any client nudge drafts were created, add at the bottom:
📨 Client nudge drafted in #ext-[client]-spice -- review and send.

8. Post a rolled-up summary to #new-client-onboarding (channel ID: C08D4EM5UCX) with all clients combined:

*📋 Onboarding Status Check -- [Date]*

*Overview:*
🚨 Blockers: [X] tasks
🔴 Overdue: [X] tasks
⚠️ At Risk: [X] tasks
✅ On Track: [X] tasks

If any form migrations happened during this run, add a section:
*📥 Form Submissions Processed:*
• [Client Name] -- credentials migrated, task auto-closed

Then list each client with a one-line summary of their status. Link to details in their #int- channel.

If there are zero overdue or at-risk tasks across all clients, still post a short confirmation to #new-client-onboarding: "✅ All onboarding tasks on track as of [Date]."

**IMPORTANT: Slack formatting rules.** Never use em dashes in Slack messages. Use double hyphens (--) instead. Em dashes cause "invalid_blocks" errors in the Slack API.

---

## Reference Data

### Database IDs
- Client Onboarding Tasks: collection://239d3ff0-18e7-8041-84d2-000b393bcc69
- Onboarding Form Responses: collection://1c8d3ff0-18e7-80df-a6ac-000bdaba588c
- Platform Credentials: collection://f99b8707-392b-4862-95cd-e29863276fb0
- Clients: collection://1c8d3ff0-18e7-80e9-8381-000b4448cb87

### Platform Credentials DB Schema
- Name (title): "[Client] - [Platform]"
- Platform (select): DoorDash, Grubhub, Uber Eats, Toast, OLO, Punchh, Attentive, Loop AI
- Email (rich_text)
- Password (rich_text)
- Client (relation to Clients DB)
- Notes (rich_text)

### Onboarding Form Fields -> Migration Targets
| Form Field | Target 1 (Platform Credentials DB) | Target 2 (Client Wiki) | Target 3 (Clients DB) |
|---|---|---|---|
| Client - Business Name | Used for matching | -- | -- |
| Client - Main Point of Contact | -- | Wiki entry: "Main POC: [Name]" | -- |
| Main Point of Contact - Email | -- | Wiki entry URL: mailto:[email] | Client Email (if empty) |
| Delivery Platform - Logins | Parse into per-platform entries | -- | -- |
| Delivery Platforms - Contacts | -- | Wiki entry: "Platform Contacts" | -- |
| Point of Sale / Integrator - Logins | Parse into credential entries | -- | -- |
| Direct Ordering Platform - Login | Parse into credential entry | -- | -- |
| Email Marketing Platform - Login | Parse into credential entry | -- | -- |
| Website Platform - Login | Parse into credential entry | -- | -- |
| Brand Assets Folder | -- | Wiki entry: "Brand Assets Folder" + URL | -- |
| Menu Images Folder | -- | Wiki entry: "Menu Images Folder" + URL | -- |

### Team Slack Handle Reference
- Maxx Freedman (Notion ID: c249c8bc-e33f-4b35-b4f8-c9b22117cccc) -> @maxx (Slack: U08DMH0DHS8)
- Rodrigo Gutierrez (Notion ID: babf0663-1fa3-49dd-8605-5b777bab2c13) -> @rodrigo (Slack: U08E7SBQQCQ)
- David Pliego (Notion ID: 1c0d872b-594c-8190-90bc-00025e02e3b6) -> @david (Slack: U08LFKULX6H)
- Rui Moreira (Notion ID: 1b7d872b-594c-813a-9ec9-00026a26bf6a) -> @rui (Slack: U08G4JH12ET)
- Manish Kumar (Notion ID: 2afd872b-594c-8133-b913-00024826113c) -> @manish (Slack: U09TR52DVMY)
- Dulari Fernando (Notion ID: 1cad872b-594c-81a0-a0db-000282941e87) -> @dulari (Slack: U08LFKT3APP)
- Diri Thadhani (Notion ID: 270d872b-594c-81f7-b95e-0002309a801d) -> @diri

### Slack Channel Reference
- #new-client-onboarding: C08D4EM5UCX
- Client internal channels: search for #int-[client-name] with channel_types "public_channel,private_channel"
- Client external channels: search for #ext-[client]-spice with channel_types "public_channel,private_channel"
