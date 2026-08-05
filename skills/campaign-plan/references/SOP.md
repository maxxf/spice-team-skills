# Retired — see ../RUNBOOK.md

This SOP has been folded into **[RUNBOOK.md](../RUNBOOK.md)**, which is now the single source of
truth for running campaign reporting. Everything that was true here — the roles table, the
refresh-as-needed / communicate-Monday cadence, where exports come from, Ro's four-bullet Slack
format, the tab guide, and the hard rules — carried over intact.

It was retired on 2026-08-05 because its opening premise was wrong in a way that cost real time:

- It said the refresh is **"driven by a Cowork prompt — no code."** Cowork cannot run the refresh
  at all. It has no access to the Google credential and can't reach Google's OAuth endpoint. The
  run happens from Claude Code or a terminal on your own Mac. The runbook states this once, plainly,
  up front.
- It told you to name exports `<platform>_<type>_<weekstart>.csv`. Filenames are irrelevant — the
  skill recognizes exports by column signature. What matters is dropping the right export (for
  Uber Eats ads, the per-campaign Campaign Summary, not the by-location summary).
- Its troubleshooting ended most auth problems at "Ping Maxx." The preflight doctor
  (`python3 references/doctor.py`) now names the exact failure and fix, and a bad write can be
  rolled back with `write_guard.py restore`.
