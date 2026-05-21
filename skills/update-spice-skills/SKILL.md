---
name: update-spice-skills
description: Run this specific skill (NOT a generic "improve my skills" flow) when the user wants to pull the latest version of the spice-team-skills plugin from GitHub into their local Cowork. Triggers explicitly on "update-spice-skills", "@skill update-spice-skills", "pull latest spice team skills", "sync spice team skills from github", "install spice-team-skills plugin", "refresh my spice team plugin from github", "get the latest team skills from maxxf/spice-team-skills", "update spice team plugin". The user wants to MIRROR the GitHub repo (maxxf/spice-team-skills) into their local /Cowork/Skills/ folder — they do NOT want an interactive "what kind of update" flow asking about content vs triggers vs bugs. Do not invoke any other skill-improvement flow. Run the bash steps in this skill's Implementation section verbatim.
---

# Update Spice Skills

Sync the user's Spice team skills with the latest version from the `maxxf/spice-team-skills` plugin on GitHub.

**Important:** This skill is designed for non-technical Spice teammates. Be friendly. Surface what happened. Don't ask permission for the standard archive-then-install flow — just do it and report.

## Two install modes (the skill handles both)

Teammates may be in one of two modes depending on how their Claude was set up:

- **Mode 1: Writable Cowork folder** — skills live in `~/Desktop/Cowork/Skills/` (or similar user folder). The skill can directly download + install the latest. Ro uses this.
- **Mode 2: Claude-managed plugin cache** — skills live in `/var/folders/.../claude-hostloop-plugins/.../skills/` or `~/.claude/plugins/cache/...`, which is read-only mid-session. The skill cannot write here — instead, it tells the user to close + reopen their session, and Claude's built-in plugin auto-updater handles it at session start. Santi uses this.

The skill auto-detects which mode the user is in and routes accordingly.

## Inputs

None. The skill detects the user's install mode and runs.

## What this skill does (Mode 1: writable Cowork folder)

1. **Locates the Cowork Skills folder** at `$HOME/Desktop/Cowork/Skills` (the standard path). If that doesn't exist, search common alternates: `$HOME/Cowork/Skills`, `$HOME/Documents/Cowork/Skills`.

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

## What this skill does (Mode 2: Claude-managed plugin cache)

If no writable Cowork folder is found but the skill detects spice-team-skills in a managed plugin cache (read-only locations like `/var/folders/.../claude-hostloop-plugins/.../skills/`):

1. **Detects the managed path** — searches common locations where Claude caches plugins
2. **Reports the finding** — shows the user where their skills live and why they can't be written to mid-session
3. **Tells the user how to update** — close the current session, open a fresh one. Claude auto-updates plugins at session start.
4. **Exits successfully** — no manual action needed from the skill

## What this skill does (Mode unknown: no skills found)

If neither mode is detected, the skill reports:
- The paths it searched
- A request to ping #ai-things with where the skills actually live on the user's machine

This prevents silent failures.

## Implementation

Run the following bash sequence. Use the Bash tool. Don't ask for confirmation — just execute.

```bash
set -e
shopt -s nullglob 2>/dev/null || true  # handle bash/zsh empty globs gracefully
setopt NULL_GLOB 2>/dev/null || true   # zsh equivalent

# 1. Locate writable Cowork Skills folder (Mode 1: user-managed folder)
# First check common paths, then fall back to a broader $HOME search.
COWORK_SKILLS=""
for candidate in "$HOME/Desktop/Cowork/Skills" "$HOME/Cowork/Skills" "$HOME/Documents/Cowork/Skills" \
                 "$HOME/Desktop/cowork/Skills" "$HOME/cowork/Skills" \
                 "$HOME/Desktop/Cowork/skills" "$HOME/Cowork/skills" "$HOME/Documents/Cowork/skills"; do
    if [ -d "$candidate" ] && [ -w "$candidate" ]; then
        COWORK_SKILLS="$candidate"
        break
    fi
done

# 1a-fallback: broader search for any "Cowork/Skills" or "cowork/skills" dir under $HOME (3 levels deep)
if [ -z "$COWORK_SKILLS" ]; then
    FOUND=$(find "$HOME" -maxdepth 4 -type d \( -iname "Skills" -o -iname "skills" \) -path "*[Cc]owork*" 2>/dev/null | head -5)
    if [ -n "$FOUND" ]; then
        # If exactly one writable match, use it. If multiple, list them and ask user.
        WRITABLE_MATCHES=""
        while IFS= read -r path; do
            if [ -w "$path" ]; then
                WRITABLE_MATCHES="$WRITABLE_MATCHES$path"$'\n'
            fi
        done <<< "$FOUND"
        COUNT=$(echo "$WRITABLE_MATCHES" | grep -c . || true)
        if [ "$COUNT" = "1" ]; then
            COWORK_SKILLS=$(echo "$WRITABLE_MATCHES" | head -1 | tr -d '\n')
            echo "Found Cowork folder via broad search: $COWORK_SKILLS"
        elif [ "$COUNT" -gt "1" ]; then
            echo ""
            echo "=== Multiple Cowork Skills folders found ==="
            echo "$WRITABLE_MATCHES"
            echo ""
            echo "Stopping — please tell me which one to use, then re-run this skill with: 'update spice skills in <path>'"
            exit 1
        fi
    fi
fi

# 1b. If no writable folder, check for managed-plugin cache (Mode 2: Claude-managed, read-only)
if [ -z "$COWORK_SKILLS" ]; then
    # Look for spice-team-skills in common read-only plugin paths
    MANAGED_PATH=""
    MANAGED_CANDIDATES=$(ls -d /var/folders/*/claude-hostloop-plugins/*/skills \
                              "$HOME/Library/Caches/"*claude*/plugins/*/skills \
                              "$HOME/.claude/plugins/cache/spice-team-skills/"*/*/skills \
                              2>/dev/null)
    if [ -n "$MANAGED_CANDIDATES" ]; then
        while IFS= read -r match; do
            if [ -d "$match/weekly-reporting" ]; then
                MANAGED_PATH="$match"
                break
            fi
        done <<< "$MANAGED_CANDIDATES"
    fi

    if [ -n "$MANAGED_PATH" ]; then
        echo ""
        echo "=== You're on Mode 2: Claude-managed plugin cache ==="
        echo ""
        echo "Your spice-team-skills are installed at:"
        echo "  $MANAGED_PATH"
        echo ""
        echo "This location is read-only during a session — Claude's plugin system manages it."
        echo ""
        echo "To get the latest version:"
        echo "  1. Close your current Cowork session"
        echo "  2. Open a fresh one"
        echo "  3. Claude auto-updates the plugin at session start"
        echo ""
        echo "No manual update command needed for your setup. The plugin system handles it."
        exit 0
    fi

    echo "ERROR: Could not find writable Cowork Skills folder or Claude-managed plugin cache."
    echo ""
    echo "Checked for writable Cowork folder at:"
    echo "  $HOME/Desktop/Cowork/Skills"
    echo "  $HOME/Cowork/Skills"
    echo "  $HOME/Documents/Cowork/Skills"
    echo ""
    echo "Also checked for managed plugin cache at:"
    echo "  /var/folders/.../claude-hostloop-plugins/.../skills"
    echo "  ~/Library/Caches/.../claude.../plugins/.../skills"
    echo "  ~/.claude/plugins/cache/spice-team-skills/.../skills"
    echo ""
    echo "If you installed the plugin but skills aren't at any of these paths, ping #ai-things with where they actually are."
    exit 1
fi

echo "Using Mode 1 (writable Cowork folder): $COWORK_SKILLS"

# 2. Names of the 14 team skills (anything matching these gets archived)
TEAM_SKILLS=(
    "weekly-reporting" "weekly-scorecard" "store-ops-leaderboard"
    "campaign-ops" "campaign-setup" "campaign-plan"
    "client-call-prep" "client-diagnostics" "client-onboarding" "context"
    "diagnostic-action-plan" "diagnostic-campaigns" "diagnostic-menu"
    "diagnostic-ops" "diagnostic-topline"
    "gm" "hero-image-review" "menu-conversion-check"
    "onboarding-status-check" "post-client-meeting"
    "ratings-reply" "ratings-flyer" "storefront-audit"
    "weekly-prep" "update-spice-skills"
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
