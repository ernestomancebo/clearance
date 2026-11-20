# Profile Setup and Resolution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `/clearance:setup` to create, list and edit review-sweep profiles, and let `review-sweep` pick a profile without being told.

**Architecture:** Clearance is prose skills (markdown), so every deliverable is a markdown edit verified by grep and a read-through; there is no test suite. The setup skill is new; resolution rules go into `review-sweep`'s existing Profiles section. Paths do not move.

**Tech Stack:** Markdown skills, `gh` CLI, AskUserQuestion.

**Spec:** `docs/superpowers/specs/2026-11-20-profile-setup-design.md`

## Global Constraints

- Profile path stays `~/.claude/state/clearance/review-sweep/profiles/<name>.md`; state dir `~/.claude/state/clearance/review-sweep/<name>/`.
- Every `gh` call runs as `GH_TOKEN=$(gh auth token --user <login>) gh ...`; never `gh auth switch`.
- `## Repos` accepts `owner/repo` lines; the legacy `## Repos (owner \`x\`)` comma list stays valid.
- Setup writes only the profile file; it never posts or changes anything on GitHub, and never deletes a profile.
- Safe defaults: approve off, disclosure `disclose`, cadence one tick, skip = the account itself, `dependabot`, `app/dependabot`, drafts.
- Skill frontmatter is `name` and a "Use when..." `description`, as in the existing skills.

## Review Focus

- Two profiles list the current repo: ask, never pick one.
- Current directory is not a git repo, or has no `origin`: skip the directory match, fall through to steps 3-4.
- Zero profiles exist: `/clearance:review-sweep` points to `/clearance:setup` instead of only dry-running.
- A profile name that already exists in setup: show a diff and ask; never overwrite silently.
- A listed repo the chosen account cannot reach: reported and left out of the file.

## Task 1: Profile format and resolution in review-sweep

**Files:**
- Modify: `skills/review-sweep/profiles/example.md` (the `## Repos` section)
- Modify: `skills/review-sweep/SKILL.md` (Profiles section, lines ~16-25)

**Interfaces:**
- Produces: the resolution order and the `owner/repo` Repos format that Task 2's skill writes and Task 3 documents.

- [ ] **Step 1: Update `example.md`.** Replace the `## Repos (owner ...)` section with a `## Repos` section listing `your-org/api`, `your-org/web` and `other-org/infrastructure`, plus one line saying the older `## Repos (owner \`x\`)` comma list still works.
- [ ] **Step 2: Add a resolution subsection to `SKILL.md` Profiles.** Put it after the opening paragraph. Content, first hit wins: (1) a name in the invocation; (2) exactly one profile lists this directory's `origin` remote parsed to `owner/repo`; (3) exactly one profile exists; (4) list the profiles and ask once per session. Two matches at step 2 means ask. Zero profiles means say so and point to `/clearance:setup`, then dry-run.
- [ ] **Step 3: Add the authorization rule for auto-resolved profiles.** Steps 2-3 select and announce the profile ("Using profile `<name>`: it lists this repo"); review runs, but nothing is posted until the user confirms that name once, and the confirmation counts as naming it. Under `/loop`, the confirmed name is written into the loop prompt so every tick repeats it.
- [ ] **Step 4: Note the repo format in `SKILL.md`.** Add one sentence that a profile's Repos are `owner/repo` lines (legacy form accepted).
- [ ] **Step 5: Verify.** Run `grep -n "owner/repo\|exactly one profile\|clearance:setup" skills/review-sweep/SKILL.md skills/review-sweep/profiles/example.md`. Expected: a hit in each file for the format, and hits for the resolution order and the setup pointer in `SKILL.md`. Re-read the Profiles section once for contradictions with "Naming a profile that exists is the standing authorization".
- [ ] **Step 6: Commit** `feat: resolve a review-sweep profile without being told`.

## Task 2: The setup skill

**Files:**
- Create: `skills/setup/SKILL.md`

**Interfaces:**
- Consumes: the profile format and resolution from Task 1 (the file it writes must follow `example.md`).
- Produces: `/clearance:setup` with modes create (default), list, edit `<name>`.

- [ ] **Step 1: Write the frontmatter.** `name: setup`; description: "Use when creating, listing or editing clearance review-sweep profiles: which GitHub account reviews which repos, across one or more owners."
- [ ] **Step 2: Write the body.** Cover, in order: the three modes; the question sequence from the spec (account from `gh auth status`; repos via `gh repo list <owner> --limit 200` as that account, owners added one at a time; skip; verdicts/approve/disclosure/cadence with the Global Constraints defaults; name as a slug), all asked through AskUserQuestion; per-repo access check with `gh repo view` as that account, unreachable repos reported and left out; the authorization summary and apply/decline before any write; edit mode loads the file, asks what to change, shows a diff; list mode prints name, account, repos for each profile. State the Global Constraints as rules (writes only the profile file, never posts, never deletes, never `gh auth switch`).
- [ ] **Step 3: Verify.** Read `example.md` beside the setup skill's output spec and check that every `example.md` section has a question or default in the skill. Run `grep -c "AskUserQuestion" skills/setup/SKILL.md` (expected: at least 1) and `grep -n "gh auth switch" skills/setup/SKILL.md` (expected: only in a "never" rule).
- [ ] **Step 4: Commit** `feat: add setup skill for review-sweep profiles`.

## Task 3: README

**Files:**
- Modify: `README.md` (Skills table, Profiles section)

**Interfaces:**
- Consumes: skill name `setup` and the resolution order.

- [ ] **Step 1: Add a `setup` row** to the Skills table: use it when creating or editing profiles; what it does in one sentence.
- [ ] **Step 2: Rewrite the Profiles section** to lead with `/clearance:setup`, keep the manual copy path as a fallback, and state the resolution order in two lines.
- [ ] **Step 3: Verify.** `grep -n "clearance:setup" README.md` shows both places; the Safety rules section is untouched except for any line the new resolution rule contradicts.
- [ ] **Step 4: Commit** `docs: document the setup skill and profile resolution`.
