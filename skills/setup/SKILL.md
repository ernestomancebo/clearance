---
name: setup
description: Use when setting up, configuring, listing or editing clearance review-sweep profiles, including having several profiles for different GitHub accounts or repo sets across one or more owners.
---

# Profile setup

A review-sweep profile is `~/.claude/state/clearance/review-sweep/profiles/<name>.md`. It says which account reviews which repos and what may be posted, and naming it authorizes exactly that. This skill writes those files by asking, so nobody copies the template (`../review-sweep/profiles/example.md`, relative to this skill) by hand. A person may have several profiles, each with its own account and repos.

## Rules

- Write only the profile file. Never post, comment, approve or change anything on GitHub.
- Never delete a profile.
- Run every `gh` call as the profile's account: `GH_TOKEN=$(gh auth token --user <login>) gh ...`. Never `gh auth switch`.
- Ask every question with AskUserQuestion, one topic at a time, except the repo picks (question 2), which take free text. Defaults are the safe choice.
- Never overwrite an existing profile without showing a diff and asking.

## Modes

- **create** (default): the questions below.
- **list**: read every file in the profiles directory; print name, account and repos for each. Say plainly when there are none.
- **edit `<name>`**: load the file, ask what to change (any question below), show a diff, then apply or decline. A name with no file means create.

## Questions (create)

1. **Account.** `gh auth status` lists the logged-in accounts; ask which one reviews.
2. **Repos.** Ask for an owner or org, list its repos with `gh repo list <owner> --limit 200` as that account, print them as text and take the picks as free text (`owner/repo`, comma-separated). Offer to add another owner; a profile may span several. Check each pick with `gh repo view <owner>/<repo>` as that account; report any it cannot reach and leave it out of the file.
3. **Skip.** Start from the template's Skip section (with the account itself); ask for more.
4. **Verdicts.** Use the template's mapping; ask only if the person wants a different one.
5. **Approve.** Default off (comments only). Offer `after human check`, which approves only when the person read the draft and said go in an attended run.
6. **Disclosure.** Default `disclose`. Offer `plain` only for a team that agreed reviews carry no tool notes.
7. **Cadence.** Default one tick. Offer a `/loop` interval; `example.md` uses 30 minutes.
8. **Name.** A short slug. If `<name>.md` exists, diff the new file against it and ask overwrite or pick another name.

Create the profiles directory if it is missing. Fill the sections of the template in its order: Account, Repos (`owner/repo` lines), Skip, Verdicts, Approve, Disclosure, Never, State (`~/.claude/state/clearance/review-sweep/<name>/`), Cadence. Keep Never as in the example. Write only what the answers allow: with Approve off, write the Verdicts GO and GO WITH NITS lines as "comment with the verdict line" and leave out `## Approve`; with the default one tick, leave out `## Cadence`.

## Confirm before writing

Show what the profile authorizes in plain words: the account, every repo, which verdicts post and how, whether it can approve, the disclosure line. It is a standing authorization to post, so ask apply or decline. Write nothing on decline. After writing, report the path and how to run it: `/clearance:review-sweep <name>`, or `/loop <interval> /clearance:review-sweep <name>`; with one profile per repo set, `/clearance:review-sweep` alone resolves it from the current directory.
