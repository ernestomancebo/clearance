---
name: preflight
description: Use when a stacked PR series or cross-repo set is built and about to go to review or release, and you must verify release waves, branch bases, labels, PR descriptions and cross-repo links are all consistent.
---

# Preflight

## Overview
A series is finished only when a reader can open any one PR and see where it sits, what it waits on, and what it unblocks, in every repo it touches. This is an audit with fixes, run once the work is built and again before release.

## Checklist (report pass/fail per item with the PR)
1. **Waves exist and are written down**: REQUIRED SUB-SKILL: clearance:merge-plan. Run its script now (do not derive waves by hand); the result is linked from the top PR and a tracking issue/bead/milestone.
2. **Bases are right**: each child's base is its parent's head; no child targets a merged or deleted branch; siblings that should be linear are.
3. **In sync**: no DIRTY/behind branch; parents merged into children after any parent change; CI green on the latest pushed commit (not an older one); lint/type/baseline unchanged or growth labelled.
4. **Contracts in sync**: generated code, snapshots/goldens, pinned copies of contract blocks, docs/plans describing what is built (statuses, names, paths), release notes and moved-paths lists.
5. **Cross-repo links**: each PR description names its counterparts (generated stubs, client, consumer pin, infra) in both directions with full `owner/repo#N` links (a bare `#N` resolves to the wrong repo) and the merge-order constraint ("do not merge until X"); mode/flag gates stated.
6. **Labels and titles**: one shared label for the project across repos; a "Stack N/M" prefix or header; draft state matches readiness; title style and ticket id follow each repo's own convention (they differ per repo: check, do not unify).
7. **Descriptions are true**: every claim (tests counts, "done in #N", "stacked on #N", gaps) re-checked against the branch; known gaps listed; if the owner forbids attribution, grep every PR body for `Generated with` and `Co-Authored-By` (a clean first read is not a check) and list hits.
8. **Follow-ups are tracked**: each deferred item has a bead/issue with an owner and the PR that surfaced it.
9. **Version and consumers**: the library release/version bump, release notes and moved-paths list exist, and each consumer pin-bump PR is planned.
10. **Release control**: deploy-order constraints (migration before service, bucket before consumer), flags default off, rollback noted, nothing applied to live systems without the owner.

## Fixing
Apply label/body/base edits only to PRs you own, after listing them; ask before editing others' PRs or applying anything outward-facing in bulk. Re-run merge-plan at the end.

## Common mistakes
| Mistake | Fix |
|---|---|
| "Green" from a stale CI run | Check the check-runs of the head sha |
| Body says "amended in #N" but it was not | Verify with git/gh before keeping the claim |
| Labels added in one repo only | Same label name in every repo, create if missing |
| Counterpart link missing on the generated-code PR | Add both directions |
