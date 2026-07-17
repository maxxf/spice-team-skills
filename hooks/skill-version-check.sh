#!/bin/sh
# Spice skill-version beacon — answers "is this machine actually on the latest skills?"
#
# Runs at SessionStart on each team member's machine (pushed org-wide via Managed
# Settings). Compares the INSTALLED spice-team-skills plugin version against the
# latest on GitHub. If the machine is behind it (a) tells the user how to fix it,
# and (b) — if SLACK_WEBHOOK is set — pings #skill-versions so the team lead sees
# the stale machine without asking anyone. Silent when current. Never fails the
# session (always exits 0).
PJ="$HOME/.claude/plugins/marketplaces/spice-team-skills/.claude-plugin/plugin.json"
RAW="https://raw.githubusercontent.com/maxxf/spice-team-skills/main/.claude-plugin/plugin.json"
SLACK_WEBHOOK="${SKILL_VERSIONS_WEBHOOK:-}"   # set SKILL_VERSIONS_WEBHOOK via managed-settings env to enable the #skill-versions roster ping (keeps the secret out of the public repo)

have=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['version'])" "$PJ" 2>/dev/null) || have=""
latest=$(curl -s --max-time 4 "$RAW" | python3 -c "import json,sys;print(json.load(sys.stdin)['version'])" 2>/dev/null) || latest=""

# Race guard: this hook fires before Claude Code's marketplace autoUpdate
# finishes its pull, so a just-shipped release reads as "stale" even though
# the update lands seconds later. On mismatch, try the pull ourselves and
# re-read — only warn if the machine is STILL behind (i.e. the pull failed).
if [ -n "$have" ] && [ -n "$latest" ] && [ "$have" != "$latest" ]; then
  git -C "$HOME/.claude/plugins/marketplaces/spice-team-skills" pull --ff-only --quiet >/dev/null 2>&1 || true
  have=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['version'])" "$PJ" 2>/dev/null) || have=""
fi

if [ -n "$have" ] && [ -n "$latest" ] && [ "$have" != "$latest" ]; then
  echo "WARN: Spice team skills are OUT OF DATE on this machine — installed v$have, latest v$latest."
  echo "Fix: restart Claude Code (autoUpdate pulls it) or run  /plugin marketplace update spice-team-skills"
  if [ -n "$SLACK_WEBHOOK" ]; then
    curl -s --max-time 4 -X POST -H 'Content-type: application/json' \
      --data "{\"text\":\":warning: stale skills — $(whoami)@$(hostname -s 2>/dev/null): v$have (latest v$latest)\"}" \
      "$SLACK_WEBHOOK" >/dev/null 2>&1
  fi
fi
exit 0
