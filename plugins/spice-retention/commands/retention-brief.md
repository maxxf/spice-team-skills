---
description: Draft a complete retention campaign brief (Notion + #design-requests + reminder)
argument-hint: [client] [campaign type] [send date]
---

Trigger the `retention-campaign-brief` skill.

If the user passed arguments after `/retention-brief`, parse them as:
1. Client (MBFS | HealthNut | Ahipoki)
2. Campaign type
3. Send date

Pass whatever was provided into the skill. If anything is missing, the skill will ask.

Do not write preamble. Invoke the skill directly.
