# ONBOARDING — spice-team-skills

Welcome. This repo is Spice's skill library — markdown SKILL.md files + Python scripts that the team installs as a Claude Code plugin. Maintainer = you.

This doc is canonical. When something here is wrong, update it.

---

## Day 1 — get operational (30 min)

### 1. Accept the GitHub invite

You should have an email from GitHub inviting you to `maxxf/spice-team-skills` with **write** access. Accept it.

### 2. Clone locally

```bash
git clone https://github.com/maxxf/spice-team-skills.git ~/Desktop/spice-team-skills
cd ~/Desktop/spice-team-skills
```

This is your dev tree. Edit, commit, push from here.

### 3. Install the plugin in your Cowork (so you experience what the team sees)

In Cowork (Claude Code), paste this and hit enter:

```
Install the spice-team-skills plugin into my Cowork.

1. Find my Cowork Skills folder (~/Desktop/Cowork/Skills/)
2. Create _archive/<today's date>/ inside it
3. Move ONLY skills matching our team plugin's TEAM_SKILLS list there
4. Get the latest source: git clone https://github.com/maxxf/spice-team-skills.git as fallback if the zip URL is blocked
5. Copy each subdirectory from skills/ into my Cowork Skills folder
6. Report how many skills installed
```

Folder prerequisite: `~/Desktop/Cowork/Skills/` must exist first (`mkdir -p ~/Desktop/Cowork/Skills`). A few teammates skipped this and hit silent failures.

### 4. Verify

In Cowork:
```
@skill context
```

Should load the Spice org context. If it does, you're set.

If anything breaks, post in `#ai-things` — that's the team's feedback channel for skill issues.

---

## Architecture (read this once, refer to it forever)

### What the repo is

- **Public GitHub plugin** for Claude Code
- The team installs it once, gets auto-updates at Cowork session start
- Engineers (you) edit + commit + push; team gets the change in their next session

### Distribution flow

```
You push to maxxf/spice-team-skills (this repo)
        ↓
Cowork users: paste `update spice team skills` OR close + reopen session
Claude Code plugin users: auto-pulls at session start
        ↓
Skills available as `@skill <name>` in their Cowork chat
```

There's no CI/CD. There's no staging. **Pushing to `main` is a release.** That's the deal. Version every push.

### Repo layout

```
.claude-plugin/
  marketplace.json     # marketplace listing (one entry per plugin)
  plugin.json          # this plugin's manifest (name, version, description)
CLAUDE.md              # shared Spice team context — read by every team member
ONBOARDING.md          # this file
skills/
  <skill-name>/
    SKILL.md           # required — frontmatter + workflow
    references/        # optional — supporting docs the skill reads
    scripts/           # optional — Python the skill invokes via Bash
plugins/               # NEW (June 2026) — sibling per-function plugins (see below)
  spice-marketplaces/
  spice-retention/
  spice-design/
  spice-operations/
```

### What a skill is

A skill is a markdown file with YAML frontmatter that Claude loads when a teammate's request matches the description. The frontmatter has `name` and `description`. The body is the workflow Claude follows.

Skills can:
- Call MCP tools (Notion, Slack, Gmail, Calendar, Google Drive, Canva, Figma)
- Shell out to scripts in their own `scripts/` directory
- Read their own `references/` for static reference content
- Hand off to other skills (instruct the user to run `@skill other-skill` next)

Skills can NOT:
- Auto-invoke other skills (no programmatic cross-skill calls — Cowork doesn't support it reliably)
- Reach into other skills' files (each skill is self-contained)
- Modify Cowork settings or installed plugins

When in doubt, the gold-standard reference skill is `ratings-flyer` — small, complete, well-documented. Read it before writing anything new.

### Versioning rules

**Every push that changes user-facing behavior bumps the version.**

- New skill = MINOR bump (e.g. 1.11.0 → 1.12.0)
- Updated skill = PATCH bump (e.g. 1.12.0 → 1.12.1)
- Breaking change to multiple skills or the plugin format = MAJOR bump (e.g. 1.12.0 → 2.0.0)
- Doc-only or comment-only = no bump needed

Bump BOTH:
- `.claude-plugin/plugin.json` → `version`
- `.claude-plugin/marketplace.json` → `plugins[0].version` (the monolith entry)

Each new skill must also be registered in:
- `skills/update-spice-skills/SKILL.md` → the `TEAM_SKILLS` bash array (so the updater knows to archive old copies on next install)

Commit messages: `vX.Y.Z <skill-name>: <what changed>`. See the git log for the pattern.

---

## The per-function plugin migration (decision pending)

In June 2026 someone added four sibling plugins to the marketplace alongside the monolith:

- `spice-marketplaces` (DM operations skills)
- `spice-retention` (retention service skills)
- `spice-design` (design briefs)
- `spice-operations` (back-office: onboarding, status checks)

These are listed in `.claude-plugin/marketplace.json` as siblings to `spice-team-skills`, with `source: "./plugins/<name>"`. The intent: soft migration — teammates start installing only the per-function plugin relevant to their role, instead of the whole monolith.

**Status:** in progress, not committed to. The monolith is still the canonical install. Plugin sources under `plugins/*/` may or may not be in sync with the same skills under `skills/*/`.

**Your call as engineer:** decide whether to (a) commit fully to the migration and deprecate the monolith, (b) keep both indefinitely as parallel install options, or (c) revert to monolith-only and remove the siblings.

Discuss with Maxx before making the call. There's no right answer until you've talked to the team about how they'd prefer to install.

---

## First-week triage backlog

There's a pile of uncommitted work in this repo's working tree from other Claude sessions and ad-hoc edits. Walk through and decide what ships, what gets dropped, what needs more work.

Run this in your local clone after fresh pull:

```bash
git status --short
```

Expect to see:
- Modified files: `CLAUDE.md`, several `skills/*/SKILL.md`, a couple of Python scripts
- Untracked directories: `skills/executive-review/`, additions under `skills/campaign-plan/` (clients/, references/SOP.md, db_to_tracker.py, push_to_sheet.py, refresh.py, new_client.py, playbooks/), maybe more
- Loose files: `deploy_goop_skill.command`

Approach:
1. For each modified file, `git diff` it to see what changed
2. For each untracked dir, read the SKILL.md (if present) and decide: ship as a new skill, fold into an existing skill, or delete
3. Bundle related changes into focused commits with clear messages
4. Bump version once per release batch (not per commit)
5. Push when you're done with each batch
6. Announce in `#ai-things` what shipped

Don't `git add .` blind — that's how WIP from other sessions gets swept into commits that shouldn't include them. Stage files explicitly.

---

## Conventions worth knowing

### The "voice scrub" pattern (org changes)

When a team member's role or name changes throughout the codebase, scrub it everywhere. Recent example: Cesar left, so every "Cesar" reference became "Client Services Lead" (generic role) across SKILL.md files, references, and CLAUDE.md. Search-and-replace pattern + per-file review.

When something like this comes up:
1. `grep -rln "OldName\|oldname" skills/ references/ CLAUDE.md`
2. Replace with the new generic role
3. Update the team's mental model in `CLAUDE.md` if needed
4. Bump PATCH version
5. Announce in `#ai-things` so teammates `update spice team skills`

### Don't ship hardcoded local paths

Some sessions have written `/mnt/.skills/...` or `/var/folders/...` paths into SKILL.md files. Those break for every teammate. Always use:
- Relative paths within the skill: `references/foo.md`
- `$HOME/Desktop/Cowork/Skills/<skill-name>/...` for cross-skill references
- Or have the skill find paths via env vars / discovery logic

### Validation gates beat trust

The weekly-reporting skill (`skills/weekly-reporting/scripts/validate_report.py`) is the model. It runs after extraction agents produce JSON and catches:
- Formula errors (net_sales ≠ total_sales − discounts)
- Silent-zeros (ad_spend = $0 but marketing_driven_sales > 0)
- Tax-inclusion fingerprints (low commissions_pct + high AOV)

When you build a new skill that produces structured output, write a validate.py for it too. Silent failure is the worst failure mode.

### The drafts-not-sends rule for Slack

Skills that post to Slack on a teammate's behalf should ALWAYS use `slack_send_message_draft`, never `slack_send_message`. The user reviews the draft in their Slack and hits send manually. See `post-client-meeting/SKILL.md` Step 5 for the pattern.

### Where things go

- **Per-client config** → Notion (each client has a Wiki page with platform credentials, tracker URL, voice notes, etc.)
- **Org-wide context** → `CLAUDE.md` in this repo
- **Skill-specific reference data** → that skill's `references/` directory
- **Conventions / patterns / how-to** → here in ONBOARDING.md
- **Active discussion / triage** → `#ai-things` Slack channel

---

## Tooling

### MCPs the skills use

Skills assume these MCP servers are connected on every teammate's machine. If you write a new skill that needs an MCP that isn't widely connected, document it in the SKILL.md and ping the team in `#ai-things`:

- Notion (every skill)
- Slack
- Gmail
- Google Calendar
- Google Drive (for tracker fetches)
- Circleback (meeting transcripts)
- Canva (design generation)
- Figma (design upload)

Klaviyo MCP exists in retention skills but isn't reliable yet — manual paste fallback is documented.

### gh CLI

You'll use it to add collaborators, manage releases (if we add them), check workflow runs (if we ever set up CI). Auth with `gh auth login`. The auth token is shared with `git` for HTTPS push.

### The Cowork updater skill

`skills/update-spice-skills/` is the skill teammates run to pull the latest. It's also where you register every new skill in `TEAM_SKILLS`. If you forget to register a new skill there, teammates' old copies of that skill (if any) won't get archived before install — they'll have duplicates.

---

## Where to ask for help

- **Slack: `#ai-things`** — engineering / skill issues, feature requests, bug reports
- **Maxx directly** — strategy, prioritization, what to build next
- **The team plugin's audit trail (`git log`)** — for "why does this skill do X?" questions, check who/when

---

## Things to build (open backlog as of June 2026)

These are the loose ends. None are urgent but all are real.

1. **Triage the WIP backlog** (executive-review/, campaign-plan additions, etc. — see above)
2. **Decide on the per-function plugin migration** (see above)
3. **Klaviyo MCP** — retention skills work in manual-paste mode today; auto-fetch would save hours
4. **CI on push** — currently zero validation; a smoke test that loads every SKILL.md and parses every Python script would catch broken pushes before the team hits them
5. **The "all zeros" defensive fix in `weekly-reporting`** — Dulari hit a silent blank-sheet bug in May 2026; the fix-spec is in the conversation history but never landed. Make aggregate_platforms.py raise loudly when every metric is zero with no error.
6. **A `CONTRIBUTING.md` for future hires** — extract the "Conventions worth knowing" section above into a standalone doc once you've added a few more conventions

---

## Welcome

You own the skill library now. Push fast, version every change, post updates in `#ai-things`, ask Maxx when strategy is unclear. The repo evolves with you.
