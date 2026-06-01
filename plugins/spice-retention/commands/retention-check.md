---
description: Run the daily/weekly retention health check across all clients
---

Trigger the `retention-health-check` skill.

Default behavior:
- Scan all three clients (MBFS, HealthNut, Ahipoki)
- Post traffic-light summary to `#retention-marketing`
- DM Maxx if any red flags

If the user passed arguments specifying frequency (daily / weekly) or a specific client, pass those into the skill.

Do not write preamble. Invoke the skill directly. Output should be done in under 5 minutes.

After the skill returns, offer to schedule it as a recurring task if it isn't already scheduled.
