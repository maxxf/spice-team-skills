# Retired — see RUNBOOK.md

This document has been folded into **[RUNBOOK.md](RUNBOOK.md)**, which is now the single source of
truth for running campaign reporting: one-time setup, the weekly run, adding a client, and
troubleshooting.

It was retired on 2026-08-05 because parts of it had gone stale and would have sent you the wrong
way:

- It presented the **Mac Mini** as a zero-setup alternative. The Mini was never validated as a
  runner and its weekly job failed every week from April 12 to July 21. The runbook labels it
  explicitly unsupported.
- It described a **manual Share step** for each client's Sheet and Drive folder. That step doesn't
  exist — client folders live in a shared drive, so the robot already has access. Needing to Share
  means the file was created in the wrong place.
- It pointed at **`new_client.py`** for onboarding. Provisioning is now `provision.py`, which is
  idempotent, supports `--check`, and runs the preflight doctor.
- It predated the **preflight doctor** and the **write-guard snapshot/restore** path, so neither
  appeared in setup or troubleshooting.
