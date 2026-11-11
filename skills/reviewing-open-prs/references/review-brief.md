# Per-PR review brief (give this to the reviewing subagent)

Fill every field. A blank field is a wrong review waiting to happen.

```
Repo: <owner/repo>   PR: #<n>   Author: <login>   Draft: <y/n>
Account: <login chosen in scope.txt>; run every gh call as GH_TOKEN=$(gh auth token --user <login>) gh ...; never gh auth switch
Language / stack: <e.g. Django+gRPC, Go sqlc+buf, Terraform>   Standards: <CLAUDE.md, CONTRIBUTING.md, docs/architecture/…>
Base: <branch>   Parent if stacked: <branch or "none">   Head: <sha9>
Diff command: git diff origin/<parent-or-base>...origin/<head>
Local checkout: <path> (dirty: never checkout; fetch + origin refs only)
Spec: <PR body path | ticket text path | "PR body only">
Prior review (delta only): <path to report> reviewed at <sha9>; items to re-check: …
Existing threads: run `gh api repos/<o>/<r>/pulls/<n>/comments --paginate` and `gh pr view <n> --json reviews`; report only new findings, plus an "Unaddressed asks" list.
Do not spawn subagents. Run Standards first, then Spec, keep the sections separate, then a Bugs pass with file:line evidence.
Report: verdict first (GO / GO WITH NITS / NO GO), under 500 words, then Standards, Spec, Bugs, Unaddressed asks.
```

Standards axis carries the Fowler smell baseline from `mattpocock-skills:code-review`; a documented repo rule overrides a smell.

Stacked PRs: confirm with `git merge-base --is-ancestor origin/<parent> origin/<head>`. If the PR's listed base is another PR's head branch, that head is the parent. Review bottom of the stack first.

Delta reviews: if `<old-sha>` is an ancestor of `<new-sha>`, `git log <old-sha>..<new-sha> --not origin/main` lists the author's new commits; an empty list means the head moved by merging main, so no new review. If it is not an ancestor the branch was rebased: compare with `git range-diff <old-sha>...<new-sha>` and review only commits that differ.
