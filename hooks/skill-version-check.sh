#!/bin/sh
# Spice skill-version beacon — answers "is this machine actually on the latest skills?"
#
# Runs at SessionStart on each team member's machine (pushed org-wide via Managed
# Settings). Compares the INSTALLED spice-team-skills plugin version against the
# latest on GitHub. If the machine is behind it (a) tells the user how to fix it,
# and (b) — if SLACK_WEBHOOK is set — pings #skill-versions so the team lead sees
# the stale machine without asking anyone. Silent when current. Never fails the
# session (always exits 0).
#
# The Slack ping is rate-limited per machine: SessionStart fires for every
# background/scheduled session too, so without a cooldown a stale machine posts
# once per session — dozens per hour on machines running sync loops. We post at
# most once per COOLDOWN_SECS for a given installed→latest pair; a new pair
# (fresh release) posts immediately. The in-terminal WARN is not throttled.
PJ="$HOME/.claude/plugins/marketplaces/spice-team-skills/.claude-plugin/plugin.json"
RAW="https://raw.githubusercontent.com/maxxf/spice-team-skills/main/.claude-plugin/plugin.json"
SLACK_WEBHOOK="${SKILL_VERSIONS_WEBHOOK:-}"   # set SKILL_VERSIONS_WEBHOOK via managed-settings env to enable the #skill-versions roster ping (keeps the secret out of the public repo)
STATE="$HOME/.claude/plugins/.spice-skill-beacon-state"   # line 1: last pinged version pair, line 2: epoch of that ping
COOLDOWN_SECS=86400

have=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['version'])" "$PJ" 2>/dev/null) || have=""
latest=$(curl -s --max-time 4 "$RAW" | python3 -c "import json,sys;print(json.load(sys.stdin)['version'])" 2>/dev/null) || latest=""

if [ -n "$have" ] && [ -n "$latest" ] && [ "$have" != "$latest" ]; then
  echo "WARN: Spice team skills are OUT OF DATE on this machine — installed v$have, latest v$latest."
  echo "Fix: restart Claude Code (autoUpdate pulls it) or run  /plugin marketplace update spice-team-skills"
  if [ -n "$SLACK_WEBHOOK" ]; then
    pair="v$have->v$latest"
    now=$(date +%s)
    last_pair=""; last_ts=0
    if [ -f "$STATE" ]; then
      last_pair=$(sed -n '1p' "$STATE" 2>/dev/null)
      last_ts=$(sed -n '2p' "$STATE" 2>/dev/null)
    fi
    case "$last_ts" in ''|*[!0-9]*) last_ts=0;; esac
    if [ "$pair" != "$last_pair" ] || [ $((now - last_ts)) -ge "$COOLDOWN_SECS" ]; then
      curl -s --max-time 4 -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\":warning: stale skills — $(whoami)@$(hostname -s 2>/dev/null): v$have (latest v$latest)\"}" \
        "$SLACK_WEBHOOK" >/dev/null 2>&1
      printf '%s\n%s\n' "$pair" "$now" > "$STATE" 2>/dev/null
    fi
  fi
fi
exit 0
