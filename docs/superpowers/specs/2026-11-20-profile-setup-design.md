# Profile setup and resolution

## Intent
Profiles are hand-copied markdown files, and every session the user has to name the profile or repos again. Two fixes: a skill that creates and manages profiles, and a rule that picks the right profile without being told.

## Goals
- `/clearance:setup` creates, lists and edits profiles by asking questions, then writes the file.
- A profile may target repos under several owners.
- `review-sweep` run with no name resolves a profile on its own, and says which one it chose.

## Non-goals
- Deleting profiles; moving profile or state paths; any index file; changing what other skills do.

## Anti-goals
- Setup widening what may be posted beyond what the user confirmed.
- Resolution silently choosing between ambiguous profiles.
- Breaking existing profiles or their state directories.

## Approaches
- **A. New `setup` skill; resolution lives in `review-sweep` (chosen).** No path changes, no migration. `feedback-router` already follows the active review-sweep profile, so it inherits the behavior.
- B. Shared `~/.claude/state/clearance/profiles/` plus a shared reference. Tidier, but breaks existing paths and needs a migration.
- C. A `profiles.json` repo-to-profile index. Can drift from hand-edited files.

## Design
**Setup skill** (`skills/setup/SKILL.md`, `/clearance:setup`). Modes: create (default), list, edit `<name>`. Questions go through AskUserQuestion, one topic at a time:
1. Account: from `gh auth status`; every later `gh` call runs as `GH_TOKEN=$(gh auth token --user <login>)`, never `gh auth switch`.
2. Repos: discovered with `gh repo list <owner>` as that account, owners added one at a time; access verified per repo; unreachable repos reported, not written.
3. Skip: defaults to the account itself, `dependabot`, `app/dependabot`, drafts.
4. Verdicts, approve, disclosure, cadence: defaults are the safe ones. Approve is off unless the user opts into `after human check`. Disclosure is `disclose`. Cadence is one tick unless the user asks for a loop interval.
5. Name: a short slug; an existing name is edited, never overwritten without showing the diff.

Before writing, show exactly what the profile authorizes (repos, verdicts, approval, disclosure) and ask apply or decline: the file is a standing authorization to post. Setup only writes the profile file under `~/.claude/state/clearance/review-sweep/profiles/`; it never posts or changes anything on GitHub.

**Repos format.** `## Repos` accepts `owner/repo` lines. The old single-owner form (`## Repos (owner \`x\`)` with a comma list) stays valid. This was my call.

**Resolution** (added to `review-sweep`'s Profiles section), first hit wins:
1. A name passed in the invocation.
2. Exactly one profile lists the current directory's git remote (`origin`, parsed to `owner/repo`).
3. Exactly one profile exists.
4. Otherwise list the profiles and ask once per session.
If two profiles match the directory, ask. Steps 2 and 3 only select a profile and announce it; they never loosen its permissions. Under `/loop`, the resolved name is written into the loop prompt so every tick repeats it.

**Docs.** Update `profiles/example.md`, the review-sweep Profiles and Scope sections, and the README (skills table and Profiles section).

## Left to the builder
Question wording, the list output format, and how the skill parses the legacy repo form.
