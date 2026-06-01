#!/usr/bin/env bash
# Bump a plugin's version in both plugin.json and marketplace.json
# Usage: bash bump.sh <plugin-name> patch|minor|major
# Run from the spice-team-skills repo root (NOT the staging folder).
set -e

PLUGIN="$1"
LEVEL="$2"

if [ -z "$PLUGIN" ] || [ -z "$LEVEL" ]; then
  echo "Usage: bash bump.sh <plugin-name> patch|minor|major"
  echo "  plugin-name: spice-team-skills | spice-marketplaces | spice-retention | spice-design | spice-operations"
  echo "  level: patch (X.Y.+1) | minor (X.+1.0) | major (+1.0.0)"
  exit 1
fi

# Pick the right plugin.json
if [ "$PLUGIN" = "spice-team-skills" ]; then
  PJSON=".claude-plugin/plugin.json"
else
  PJSON="plugins/$PLUGIN/.claude-plugin/plugin.json"
fi

if [ ! -f "$PJSON" ]; then
  echo "ERROR: $PJSON not found. Are you in the repo root?"
  exit 1
fi

CURRENT=$(python3 -c "import json;print(json.load(open('$PJSON'))['version'])")
IFS=. read -r MAJ MIN PAT <<< "$CURRENT"
case "$LEVEL" in
  patch) PAT=$((PAT+1));;
  minor) MIN=$((MIN+1)); PAT=0;;
  major) MAJ=$((MAJ+1)); MIN=0; PAT=0;;
  *) echo "level must be patch|minor|major"; exit 1;;
esac
NEW="$MAJ.$MIN.$PAT"

python3 - "$PLUGIN" "$NEW" "$PJSON" <<'PYEOF'
import json, sys
plugin, new, pjson = sys.argv[1], sys.argv[2], sys.argv[3]

# Update plugin.json
d = json.load(open(pjson))
d['version'] = new
with open(pjson, 'w') as f:
    json.dump(d, f, indent=2)
    f.write('\n')

# Update marketplace.json entry
mfile = '.claude-plugin/marketplace.json'
m = json.load(open(mfile))
for p in m.get('plugins', []):
    if p['name'] == plugin:
        p['version'] = new
        break
with open(mfile, 'w') as f:
    json.dump(m, f, indent=2)
    f.write('\n')
PYEOF

echo "Bumped $PLUGIN: $CURRENT -> $NEW"
echo
echo "Next:"
echo "  git add -A && git commit -m \"$PLUGIN $NEW\" && git push"
echo "Team picks it up with /plugin marketplace update."
