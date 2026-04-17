---
name: update-spice-skills
description: Use when the user wants to install or update the Spice Team Skills plugin in their Cowork workspace. Triggers on "update spice skills", "install spice skills", "get the latest skills", "sync skills from maxx", "refresh my spice skills", or any variant. Downloads the latest skills from the public GitHub repo, archives any existing .skill files in the user's Cowork Skills folder, and installs the fresh source directories.
---

# Update Spice Skills

Sync the user's local `/Cowork/Skills/` directory with the latest version of the `maxxf/spice-team-skills` plugin from GitHub.

**Important:** This skill is designed for non-technical Spice teammates. Be friendly. Surface what happened. Don't ask permission for the standard archive-then-install flow — just do it and report.

## Inputs

None. The skill detects the user's Cowork directory and runs.

## What this skill does

1. **Locates the Cowork Skills folder** at `$HOME/Desktop/Cowork/Skills` (the standard path). If that doesn't exist, search common alternates: `$HOME/Cowork/Skills`, `$HOME/Documents/Cowork/Skills`. If still not found, ask the user where their Cowork lives.

2. **Archives existing skills** — moves all current `.skill` files AND any source directories matching the 14 team skill names into `/Cowork/Skills/_archive/<YYYY-MM-DD-HHMMSS>/`. Personal skills (humanizer, post-sale-proposal, content-mining, etc.) are LEFT ALONE.

3. **Downloads the latest plugin** from `https://github.com/maxxf/spice-team-skills/archive/refs/heads/main.zip` to a temp directory.

4. **Extracts and installs** — copies each subdirectory under `skills/` from the downloaded zip directly into `/Cowork/Skills/<skill-name>/`. Also copies `CLAUDE.md` and `references/` to the user's Cowork root if they want shared context refresh (skip if already there and user hasn't asked for it).

5. **Cleans up** — removes the temp download directory.

6. **Reports** — prints a summary:
   ```
   ✓ Archived N old files to /Cowork/Skills/_archive/<timestamp>/
   ✓ Installed 14 fresh skills from spice-team-skills
   ✓ Skills available next time you open a Cowork session

   Skills installed:
     - weekly-reporting
     - campaign-ops
     ... (full list)
   ```

## Implementation

Run the following bash sequence. Use the Bash tool. Don't ask for confirmation — just execute.

```bash
set -e

# 1. Locate Cowork Skills folder
COWORK_SKILLS=""
for candidate in "$HOME/Desktop/Cowork/Skills" "$HOME/Cowork/Skills" "$HOME/Documents/Cowork/Skills"; do
    if [ -d "$candidate" ]; then
        COWORK_SKILLS="$candidate"
        break
    fi
done

if [ -z "$COWORK_SKILLS" ]; then
    echo "ERROR: Could not find Cowork Skills folder. Checked:"
    echo "  $HOME/Desktop/Cowork/Skills"
    echo "  $HOME/Cowork/Skills"
    echo "  $HOME/Documents/Cowork/Skills"
    exit 1
fi

echo "Using: $COWORK_SKILLS"

# 2. Names of the 14 team skills (anything matching these gets archived)
TEAM_SKILLS=(
    "weekly-reporting" "campaign-ops" "campaign-setup" "client-call-prep"
    "client-onboarding" "context" "gm" "hero-image-review"
    "menu-conversion-check" "onboarding-status-check" "post-client-meeting"
    "ratings-reply" "storefront-audit" "weekly-prep" "update-spice-skills"
)

# 3. Create archive folder
TS=$(date +%Y-%m-%d-%H%M%S)
ARCHIVE="$COWORK_SKILLS/_archive/$TS"
mkdir -p "$ARCHIVE"

ARCHIVED_COUNT=0

# 4. Archive matching .skill files
for skill in "${TEAM_SKILLS[@]}"; do
    for variant in "$skill.skill" "$skill-skill.skill" "$skill-update.skill" "$skill-skill-files.zip"; do
        if [ -f "$COWORK_SKILLS/$variant" ]; then
            mv "$COWORK_SKILLS/$variant" "$ARCHIVE/"
            ARCHIVED_COUNT=$((ARCHIVED_COUNT + 1))
        fi
    done
    # Also archive existing source dirs (from a prior install)
    if [ -d "$COWORK_SKILLS/$skill" ]; then
        mv "$COWORK_SKILLS/$skill" "$ARCHIVE/"
        ARCHIVED_COUNT=$((ARCHIVED_COUNT + 1))
    fi
done

# 5. Download latest from GitHub (try zip first, fall back to git clone — some sandboxes block zip URLs)
TMPDIR=$(mktemp -d)
ZIP="$TMPDIR/spice-team-skills.zip"
EXTRACTED="$TMPDIR/spice-team-skills-main"

echo "Downloading latest spice-team-skills..."
if curl -fsSL https://github.com/maxxf/spice-team-skills/archive/refs/heads/main.zip -o "$ZIP" 2>/dev/null && [ -s "$ZIP" ]; then
    unzip -q "$ZIP" -d "$TMPDIR"
elif command -v git >/dev/null 2>&1; then
    echo "  zip download blocked, falling back to git clone..."
    git clone --depth=1 https://github.com/maxxf/spice-team-skills.git "$EXTRACTED" 2>&1 | tail -2
else
    echo "ERROR: Could not download via curl or git. Network restricted?"
    exit 1
fi

if [ ! -d "$EXTRACTED/skills" ]; then
    echo "ERROR: Downloaded source missing skills/ directory at $EXTRACTED"
    exit 1
fi

# 6. Install each skill directory
INSTALLED=()
for skill_path in "$EXTRACTED/skills"/*; do
    if [ -d "$skill_path" ]; then
        skill_name=$(basename "$skill_path")
        # Remove existing directory if present (overwrite cleanly), then copy
        rm -rf "$COWORK_SKILLS/$skill_name"
        cp -r "$skill_path" "$COWORK_SKILLS/$skill_name"
        INSTALLED+=("$skill_name")
    fi
done

# 7. Cleanup
rm -rf "$TMPDIR"

# 8. Report
echo ""
echo "=== Done ==="
echo "✓ Archived $ARCHIVED_COUNT old files/folders to $ARCHIVE/"
echo "✓ Installed ${#INSTALLED[@]} fresh skills:"
for s in "${INSTALLED[@]}"; do
    echo "    - $s"
done
echo ""
echo "Skills are available next time you start a fresh Cowork session."
echo "Old files preserved in $ARCHIVE/ for safety — delete after 30 days if you want."
```

## After running

Tell the user:
1. The skills are now in their Cowork Skills folder
2. They take effect next time they open a Cowork session
3. To update later, just say "update spice skills" again — this skill will fetch the latest

## If something goes wrong

- **"Could not find Cowork Skills folder"** → ask the user where their Cowork directory is, then re-run with that path
- **curl fails** → check the user has internet; the URL is `https://github.com/maxxf/spice-team-skills/archive/refs/heads/main.zip` (public, no auth needed)
- **unzip fails** → the download may have been incomplete; re-run
- **cp fails on a skill** → permissions issue, ask the user to check folder permissions on `/Cowork/Skills/`
