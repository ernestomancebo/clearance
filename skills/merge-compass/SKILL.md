---
name: merge-compass
description: Use when a stacked PR series or a multi-repo work queue was created, finished, merged, retargeted or re-reviewed and contributors or release control need to know what merges next, in what order, and what each PR waits on.
---

# Merge Compass

## Overview
One live table per work queue: every PR, its wave, what it depends on, its review/CI/merge state, and the single next action. Statuses go stale within the hour (others merge, retarget and re-review while you work), so **read GitHub every time; never report remembered status**.

## When to use
- After the work queue changes: PR opened, merged, retargeted, review submitted, conflict appeared.
- Before a release call or when someone asks "what merges next?".
- Not for one PR with no stack or cross-repo contract.

## Steps
1. List the PRs: every `repo#N` of the queue (all repos), plus cross-repo dependencies you know of (generated stubs/protos before consumers, library release before consumer pin bump, infra before deploy).
2. Run it, do not hand-build the table (quote the `repo#N` arguments, `#` breaks some shells; use the repo's gh account for `GH_TOKEN`):
   `GH_TOKEN=... python3 merge_compass.py OWNER 'repo#N' ... --dep 'consumer#M>provider#K' [--wrinkles]`
   (script lives beside this file; stack parents come from base/head branch names; **every cross-repo edge that blocks merging goes in as a `--dep`**, otherwise waves ignore it. Edges that only gate release or deploy (library release then pin bump, infra applied before deploy) are not merge edges: list them under release gates, or waves inflate).
   Add `--wrinkles` to list what blocks a clean merge (conflicts, child behind parent, gone base, red or pending CI).
3. Read the table; fix what it contradicts in your own beliefs (merged by someone else, new CHANGES_REQUESTED, DIRTY after a parent merged, retarget to the default branch needed).
4. Add what the script cannot see: deploy/release gates (infra before consumer deploy, migration before service, library release then consumer pin bump, flag defaults off, nothing applied to live systems without the owner) and holds with their reason (waiting for dataset, owner decision, reviewer). Then write the compass (PR description header "Stack:" or a doc/bead note) as: waves, order, full `owner/repo#N` links, per-PR next action and owner.
5. Say what you did not verify (CI of a just-pushed commit, required checks, branch rules).

## Wave rules
- Wave 0 = merged. Wave 1 = base is the default branch and nothing unmerged below it. Wave n+1 = one more than its deepest unmerged dependency.
- After a parent merges: retarget the child to the default branch (GitHub often does), and expect DIRTY if the parent was squash-merged: needs a merge/rebase fix before it can go.
- Merge order inside a wave is free; across waves it is not.

## Common mistakes
| Mistake | Fix |
|---|---|
| Quoting last session's draft/approved state | Rerun the script |
| Ordering only by PR number | Order by base/head chain and cross-repo deps |
| Forgetting a pin-bump or generated-code dependency | Add `--dep` edges |
| Calling a PR ready because CI is green | Also needs approval, not draft, merge state clean |
