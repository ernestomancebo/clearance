---
name: reviewing-open-prs
description: Use when asked to review, sweep, babysit or loop over the open pull requests of one or more GitHub repos and post verdicts (approve, request changes, comment) under the user's account, including recurring runs that must only re-review what changed.
---

# Reviewing Open PRs

## Overview

A tick is a pipeline with state: scan, delta, brief, review, verdict, post, record. State is two files the parent keeps in the profile's state directory, outside any repo: `reviewed_heads.txt` (one `owner/repo#n sha` per line) and `posted_log.txt`. A PR is work only when its head is missing from the state file. The parent owns the scope, the posting and the state; subagents only review. Each review is the two-axis pass from `mattpocock-skills:code-review`.

**Every PR needs a brief. A brief missing the repo's language, the parent branch of a stacked PR, or the existing threads produces a wrong review.**

Not for a single PR already open in the conversation; run the code-review skill directly.

## Profiles

A profile is `~/.claude/state/reviewing-open-prs/profiles/<name>.md` (kept outside the plugin, so updates never overwrite it; `profiles/example.md` beside this skill is the template). It names the account, repos, skipped authors, verdict mapping, disclosure, state directory and cadence. `/merge-compass:reviewing-open-prs <name>` loads it, and the same name inside a `/loop` prompt does too (`/loop 30m /merge-compass:reviewing-open-prs <name>`).

- **Naming a profile that exists is the standing authorization** for exactly what the file lists, on every tick. Nothing it omits is authorized.
- **State lives in the profile's state directory** (create it if missing), so a new session resumes from the recorded heads. Never use a session scratchpad for state.
- **No profile named, or no such file:** use Scope below and dry-run.
- **A profile that names no cadence** runs one tick.
- **A profile that names no disclosure** uses `disclose` (see `references/posting.md`).
- **A profile that names no approval rule** never approves: GO and GO WITH NITS post as comments.

## Scope: which account, which repos

Never assume either; several accounts can be logged in, each with its own repos and permissions.

- **Discover.** `gh auth status` lists the accounts. `gh repo list <owner> --limit 200` lists repos per owner or org; `gh search prs --review-requested=<login>` finds requests elsewhere.
- **Ask once**, before the first tick, unless a profile or the invoking message names them: the account, the repos, the excluded authors. In a loop ask on tick one only and reuse `scope.txt` until the loop prompt changes. If nobody answers, post nothing and dry-run.
- **Verify access** per repo with `gh repo view` as the chosen account. Report a repo it cannot reach; never fall back to another account.
- **Run every `gh` call as that account**: `GH_TOKEN=$(gh auth token --user <login>) gh ...`, and pass the account to subagents. Never `gh auth switch`: it changes the active account for every terminal and agent on the machine.

## Authorization

Posting is outward-facing. Permission is given once, ahead of the run, never per tick or per PR.

- **Standing.** A named profile, or an invoking message or `/loop` prompt (which repeats verbatim each tick) that names a posting action, authorizes every tick. It covers only what it names: repos, excluded authors, and the verdict mapping.
- **Absent.** Dry run: write each body to the scratch directory, list the commands once, ask the user once. Never queue per-PR approvals or wait between ticks.
- **Never in scope:** merging, closing, pushing branches, opening PRs, dismissing reviews, editing titles or labels.
- **Revocation.** "Stop" or a narrower scope applies from the next action, mid-tick included.

## The tick

1. **Scan** each repo: `gh pr list --state open --json number,author,headRefOid,isDraft,title`; drop bots and excluded authors. A failed or timed-out `gh` call, or an empty `gh auth token`, is not an empty result: retry once, then mark that repo unscanned in the tick summary and retry next tick.
2. **Delta.** Head unchanged: skip. New head on a reviewed PR: delta review against the recorded sha. Skip when the account's latest review on this head is APPROVED, CHANGES_REQUESTED or starts with a verdict line; an empty-body COMMENTED review is a thread reply and does not count. Record that head.
3. **Brief** per PR from `references/review-brief.md`. Read `go.mod`, `*.tf` or `pyproject.toml` first so the language is right.
4. **Review** small PRs yourself and larger ones in a read-only subagent. When more than five PRs are new in one tick (a stack going ready), write one shared brief file with the rules and the stack order, give each subagent only its PR-specific part, and review the bottom of a stack first. Confirm in code any blocker a subagent reports before it goes into a post. A subagent: fetch and diff origin refs, never check out a shared tree, run both axes itself, spawn nothing. It returns a verdict and a draft body. It does not post or touch state.
5. **Verdict.** NO GO requests changes. GO and GO WITH NITS (nits in the body) **approve only after a human check**: the profile must set `Approve: after human check`, and in an attended run the owner reads the draft and the verdict and says go before you approve. On an unattended tick (a `/loop` run nobody is watching) post GO and GO WITH NITS as a comment with the verdict line, never as an approval: an approval counts toward branch protection, and an agent's review must not stand in for the human one. A PR authored by the posting account cannot be approved or rejected by it: comment, or skip if excluded.
6. **Post** (parent only): re-read the head sha right before posting and skip if it moved; one review inside the authorization, under 250 words, first line `**<VERDICT>** (reviewed at <sha9>)`, first person. Checks and commands: `references/posting.md`.
7. **Record** the head and action only after the post lands, then schedule the next tick.

## Quick reference

| Situation | Do |
|---|---|
| Stacked on another PR | diff `origin/<parent>...origin/<head>`; say so in the body |
| Verdict is CLOSE or superseded | request changes with the evidence |
| Tracker call hangs | PR body is the spec; say so |
| Delta found nothing new | skip the post, record the head |

## Red flags

- A body that breaks the profile's disclosure setting: under `disclose`, a missing disclosure line; under `plain`, any mention of AI, automation, agents, sessions or a temp path (CI check names such as `ai-review` count).
- A body reading as a bare filename (`-f` instead of `-F`).
- A review with no `reviewed at` line.
- An approval posted on an unattended tick, or without the owner's go in an attended run.
- A diff larger than the PR's own commits (stacked PR diffed against main).
- A repo in scope with no scan result this tick.

## Common mistakes

- Counting your thread replies on your own PR as a review.
- Firing many tracker calls at once; one hung call blocks the tick.
- Letting a subagent post, or write the state file.
