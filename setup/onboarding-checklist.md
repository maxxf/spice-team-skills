# Spice Team Skills — Onboarding Checklist

Welcome to the Spice team plugin. This is your one-time setup. Plan ~30 minutes total.

## Prerequisites

- [ ] Claude Code installed and running on your machine
- [ ] GitHub account created (free) — Maxx will add you as a collaborator on `maxxf/spice-team-skills`
- [ ] Notion workspace access (you should already have this)
- [ ] Google Drive access to Spice client folders (request from Maxx if missing)

## Step 0: Authenticate git to GitHub (REQUIRED — do this first)

The plugin lives in a private GitHub repo. Without auth, the install command will fail silently or with a vague error.

**One-time setup (~2 minutes):**

1. Install the GitHub CLI if you don't have it:
   - **Mac:** `brew install gh` (or download from https://cli.github.com/)
   - **Linux:** see https://github.com/cli/cli/blob/trunk/docs/install_linux.md
   - **Windows:** `winget install --id GitHub.cli`

2. In your terminal, run:
   ```
   gh auth login
   ```
   - Choose: **github.com** → **HTTPS** → **Login with a web browser**
   - Copy the device code shown, paste into the GitHub page that opens, click Authorize
   - Confirm `gh auth status` shows you logged in

3. Verify git can access the repo:
   ```
   git ls-remote https://github.com/maxxf/spice-team-skills.git
   ```
   If you see commit SHAs, you're good. If you see "authentication failed" or "not found," the auth didn't take — re-run `gh auth login`.

**Skip this step ONLY if** you already use `gh` regularly and `gh auth status` shows you authenticated to github.com.

## Step 1: Install the plugin

In Claude Code, run these slash commands (type them literally in the chat input):

```
/plugin marketplace add maxxf/spice-team-skills
/plugin install spice-team-skills
```

> **Note:** You do NOT need to add GitHub as an MCP connector. The plugin grabs itself from GitHub via git directly using your `gh auth` from Step 0.

Verify: run `/plugin list` and confirm `spice-team-skills` appears in the installed list.

If install fails with auth error → Step 0 didn't complete. Re-run `gh auth login` and retry.

## Step 2: Connect MCP servers

You need the following MCP servers configured. Most are connector-based — the Spice workspace likely has them already connected if you've used Cowork before.

| MCP Server | Purpose | Verify command |
|------------|---------|----------------|
| Notion | Client context, profiles, Wiki, task creation | Try fetching any client page |
| Google Drive | Read tracker Sheets, write reports | Try `search_files` for "Spice" |
| Slack | Action items, notifications, posting | Try searching `#spice-ops` |
| Gmail | Client email context | Try searching your inbox |
| Circleback | Meeting notes, agenda context | Try searching meetings for any client |

**If any MCP fails to connect:** ping Maxx in #team-spice. The skill will fall back to manual paths but will be slower.

## Step 3: Update your Cowork CLAUDE.md (Option 2 setup)

Your local Cowork directory's CLAUDE.md should import the plugin's CLAUDE.md so org context updates flow automatically.

Replace your local `/Cowork/CLAUDE.md` (or wherever you have one) with:

```markdown
# My Cowork Workspace

@~/.claude/plugins/cache/maxxf/spice-team-skills/CLAUDE.md

## My personal context

[Add anything specific to YOU here — your role, your client list, your weekly cadence, your preferences. Everything above this line is the shared Spice context, auto-updated.]

- Name: [your name]
- Role: [your role]
- Clients I work on: [list]
```

This means: shared org context comes from the plugin (auto-updated), your personal context stays local.

## Step 4: Verify everything works

Run these to confirm:

```
@skill context
```

Should load the full Spice context (clients, team, channels). If it doesn't, the plugin install or import didn't work.

```
@skill weekly-reporting
```
(For analysts only — Manish, Dulari, Santiago)

Should prompt for client name and try to fetch a Notion profile. Even without running a full report, this confirms the skill is wired.

```
@skill campaign-ops
```
(For ops — Rodrigo, Rui, Ana, Santiago)

Should load the campaign ops workflow.

## Done

You're set up. Skills auto-update at the start of each new Claude Code session — no action required from you. Mid-session updates: run `/reload-plugins`.

If anything breaks or feels off, post in #team-spice with:
- Which skill you ran
- What you expected
- What happened instead

---

## What changed for you

| Before | After |
|--------|-------|
| Maxx sends you `.skill` file via Slack | Plugin auto-updates from GitHub |
| You re-import each update manually | Updates flow at session start |
| Org context lives in your local CLAUDE.md | Org context lives in the plugin (auto-updated); your CLAUDE.md just imports it |
| Client config scattered across context files + chat | Each client has a "Weekly Reporting Profile" page in their Notion Wiki |
