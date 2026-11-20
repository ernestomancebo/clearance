---
name: setup
description: Use when creating, listing or editing clearance review-sweep profiles: which GitHub account reviews which repos, across one or more owners.
---

# Profile setup

A review-sweep profile is `~/.claude/state/clearance/review-sweep/profiles/<name>.md`. It says which account reviews which repos and what may be posted, and naming it authorizes exactly that. This skill writes those files by asking, so nobody copies `skills/review-sweep/profiles/example.md` by hand. A person may have several profiles, each with its own account and repos.

## Rules

- Write only the profile file. Never post, comment, approve or change anything on GitHub.
- Never delete a profile.
- Run every `gh` call as the profile's account: `GH_TOKEN=$(gh auth token --user <login>) gh ...`. Never `gh auth switch`.
- Ask every question with AskUserQuestion, one topic at a time. Defaults are the safe choice.
- Never overwrite an existing profile without showing a diff and asking.

## Modes

- **create** (default): the questions below.
- **list**: read every file in the profiles directory; print name, account and repos for each. Say plainly when there are none.
- **edit `<name>`**: load the file, ask what to change (any question below), show a diff, then apply or decline. A name with no file means create.

## Questions (create)

1. **Account.** `gh auth status` lists the logged-in accounts; ask which one reviews.
2. **Repos.** Ask for an owner or org, list its repos with `gh repo list <owner> --limit 200` as that account, and let the person pick. Offer to add another owner; a profile may span several. Check each pick with `gh repo view <owner>/<repo>` as that account; report any it cannot reach and leave it out of the file.
3. **Skip.** Default: the account itself, `dependabot`, `app/dependabot`, and drafts. Ask for more.
4. **Verdicts.** Default mapping as in `example.md`: GO approves only if Approve allows it, GO WITH NITS the same with nits in the body, NO GO requests changes.
5. **Approve.** Default off (comments only). Offer `after human check`, which approves only when the person read the draft and said go in an attended run.
6. **Disclosure.** Default `disclose`. Offer `plain` only for a team that agreed reviews carry no tool notes.
7. **Cadence.** Default one tick. Offer a `/loop` interval; `example.md` uses 30 minutes.
8. **Name.** A short slug. If `<name>.md` exists, treat the run as an edit.

Fill the sections of `skills/review-sweep/profiles/example.md` in its order: Account, Repos (`owner/repo` lines), Skip, Verdicts, Approve, Disclosure, Never, State (`~/.claude/state/clearance/review-sweep/<name>/`), Cadence. Keep Never as in the example.

## Confirm before writing

Show what the profile authorizes in plain words: the account, every repo, which verdicts post and how, whether it can approve, the disclosure line. It is a standing authorization to post, so ask apply or decline. Write nothing on decline. After writing, report the path and how to run it: `/clearance:review-sweep <name>`, or `/loop <interval> /clearance:review-sweep <name>`; with one profile per repo set, `/clearance:review-sweep` alone resolves it from the current directory.
