#!/bin/bash
# Deploy goop campaign planning + reporting skill to GitHub
# Double-click this file from Finder OR paste contents into Terminal

set -e
cd "$(dirname "$0")"

echo "=== git status ==="
git status --short

echo ""
echo "=== staging changes ==="
git add skills/goop-campaign-planning-reporting/SKILL.md
git add skills/client-call-prep/SKILL.md
git add CLAUDE.md

echo ""
echo "=== commit ==="
git commit -m "Add goop-campaign-planning-reporting skill; goop QA overrides in client-call-prep

- New skill walks Santi through Monday refresh end-to-end (5 phases, platform data checklist, Sheet v3 + Notion master template flow)
- client-call-prep adds goop-specific Phase 2 QA overrides locking the 4 Highlights pillars (Payout \$ trend / Spend % trend / Struggling locations / Campaigns + launches)
- CLAUDE.md trigger table updated with new skill discovery patterns

Source: gk <> Spice 6/2 meeting decisions"

echo ""
echo "=== push ==="
git push

echo ""
echo "=== DONE. Ro + Santi can now pull the plugin update on their machines. ==="
read -p "Press Enter to close..."
