# Updating plugins (no reinstall required)

How updates flow from your push to a teammate's Cowork session.

## The flow

1. **You bump + push.** Bump `version` in both the plugin's `plugin.json` AND the matching `plugins[].version` entry in `.claude-plugin/marketplace.json`. Commit + push to `main`.
2. **Teammate runs** `/plugin marketplace update` in Cowork. That command pulls the latest commit from `maxxf/spice-team-skills`.
3. **Cowork compares versions.** Any plugin whose `version` is newer than what they have installed gets updated in place. **No `/plugin install` required.**
4. **Skills + commands refresh on next session start.** Existing sessions may need a Cowork restart to pick up changes.

## Cadence to give the team

Pin this in `#team-spice` and add it to each teammate's onboarding doc:

> **Every Monday morning:** in your Cowork session, run `/plugin marketplace update`.
>
> That's it. You'll get whatever Maxx pushed during the week — new skills, bug fixes, voice updates, all of it. You don't have to reinstall anything.

## Bumping versions — the only thing you have to remember

Two files per plugin, every release:

```
plugins/<plugin-name>/.claude-plugin/plugin.json     # version: "X.Y.Z"
.claude-plugin/marketplace.json                       # plugins[?(@.name=='<plugin-name>')].version: "X.Y.Z"
```

Semver:
- **Patch** (0.2.0 → 0.2.1) — bug fix, typo, voice tweak, single-skill edit
- **Minor** (0.2.0 → 0.3.0) — new skill added, non-breaking refactor, new commands
- **Major** (0.2.0 → 1.0.0) — breaking change (skill removed, trigger phrases changed)

If you forget to bump, Cowork keeps the cached version on the teammate's machine. Bump = the signal.

## Helper: `bump.sh`

To remove the "forgot to bump in both files" footgun, drop this in the repo root:

```bash
#!/usr/bin/env bash
# Usage: bash bump.sh spice-retention patch|minor|major
set -e
PLUGIN="$1"; LEVEL="$2"
PJSON="plugins/$PLUGIN/.claude-plugin/plugin.json"
[ "$PLUGIN" = "spice-team-skills" ] && PJSON=".claude-plugin/plugin.json"
CURRENT=$(python3 -c "import json;print(json.load(open('$PJSON'))['version'])")
IFS=. read -r MAJ MIN PAT <<< "$CURRENT"
case "$LEVEL" in
  patch) PAT=$((PAT+1));;
  minor) MIN=$((MIN+1)); PAT=0;;
  major) MAJ=$((MAJ+1)); MIN=0; PAT=0;;
  *) echo "level must be patch|minor|major"; exit 1;;
esac
NEW="$MAJ.$MIN.$PAT"
python3 -c "
import json
for f in ['$PJSON', '.claude-plugin/marketplace.json']:
    d = json.load(open(f))
    if 'plugins' in d:
        for p in d['plugins']:
            if p['name'] == '$PLUGIN': p['version'] = '$NEW'
    else:
        d['version'] = '$NEW'
    json.dump(d, open(f,'w'), indent=2)
    open(f,'a').write('\n')
print('bumped $PLUGIN $CURRENT → $NEW')
"
```

Run it from the repo root: `bash bump.sh spice-retention patch && git commit -am "spice-retention $NEW" && git push`.

## What if a teammate is still seeing the old version

Most common causes:
- They haven't run `/plugin marketplace update` (most likely)
- They ran update but haven't restarted Cowork (skills/commands sometimes need a fresh session)
- Their git auth for the private repo expired (only relevant if you make the repo private later)

If none of those: `/plugin marketplace remove maxxf/spice-team-skills` then `/plugin marketplace add maxxf/spice-team-skills` to refresh the cache.

## Why the monolith's `update-spice-skills` skill still works

The original `update-spice-skills` skill in the monolith continues to work — it wraps `git pull` against the same repo. After the split, that pull fetches the new plugin folders too. The skill is still useful as a single-command refresh wrapper. No changes needed.

## Versions in the marketplace today (Jun 1, 2026)

| Plugin | Version | Last changed | Next bump expected |
|---|---|---|---|
| `spice-team-skills` (monolith) | 1.11.1 | (last commit before split) | Hard-cut release: 2.0.0 once everyone migrates to new plugins |
| `spice-marketplaces` | 0.1.0 | First release | 0.1.1 when skill content drifts from monolith |
| `spice-retention` | 0.2.0 | Klaviyo + Figma MCP integration | 0.3.0 when retention-paid-attribution + retention-tier-builder land |
| `spice-design` | 0.1.0 | First release | 0.2.0 when more design skills added |
| `spice-operations` | 0.1.0 | First release | 0.1.1 after revenue-reconciliation + contractor-agreement get dropped in from local cache |
