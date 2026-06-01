---
description: Generate the monthly retention performance report for a client
argument-hint: [client] [month YYYY]
---

Trigger the `retention-monthly-report` skill.

If the user passed arguments after `/retention-report`, parse them as:
1. Client (MBFS | HealthNut | Ahipoki)
2. Reporting month (e.g. "May 2026")

If month not specified, default to last completed month.

If client not specified, ask once before running.

Do not write preamble. Invoke the skill directly.

This skill takes 20-30 minutes including QA. Let the user know when starting.
