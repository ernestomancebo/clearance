# Profile: example

Copy this file to `~/.claude/state/reviewing-open-prs/profiles/<name>.md` and edit it. Naming the profile in the invoking message (`/merge-compass:reviewing-open-prs <name>`, or the same inside a `/loop` prompt) is the standing authorization to post what the file lists, on every tick, with no per-tick or per-PR approval.

## Account
- Login: `your-login`. Run every `gh` call as `GH_TOKEN=$(gh auth token --user your-login) gh ...`. Never `gh auth switch`.

## Repos (owner `your-org`)
api, web, infrastructure

## Skip
- PRs authored by `your-login`, `dependabot`, `app/dependabot`.
- Drafts (do not record them).

## Verdicts
- GO: approve after human check (attended runs only); comment on unattended ticks.
- GO WITH NITS: same as GO, nits in the body.
- NO GO: request changes.

## Approve
`after human check`: approve only when I have read the draft and said go in an attended run. Delete this section to never approve.

## Disclosure
`disclose`: end each review with `_AI-assisted review, checked by me before posting._` when I checked it, and `_Automated AI-assisted review; not yet checked by me._` on unattended ticks.
(Use `plain` only when your team has agreed that reviews carry no tool notes.)

## Never
Merge, close, push branches, open PRs, dismiss reviews.

## State
`~/.claude/state/reviewing-open-prs/<name>/` (`reviewed_heads.txt`, `posted_log.txt`, `verdicts/`).

## Cadence
Under `/loop`: re-arm 30 minutes out (`delaySeconds` 1800) whether or not anything changed. While reviewers run, wake on their completion and keep 1800 as the fallback.
