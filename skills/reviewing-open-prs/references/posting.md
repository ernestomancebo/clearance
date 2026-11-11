# Posting the verdict

Every `gh` command below runs as the account recorded in `scope.txt`: prefix with `GH_TOKEN=$(gh auth token --user <login>)`. Never `gh auth switch`.

One review per PR per head. Body under 250 words, written to a file, first line:

```
**GO** (reviewed at a1b2c3d4e)          → after the owner's go: gh pr review <n> -R <o>/<r> --approve --body-file body.md
                                          unattended tick: --comment (verdict line first)
**GO WITH NITS** (reviewed at …)         → same as GO, nits in the body
**NO GO** (reviewed at …)               → --request-changes
```

Approving needs the profile's `Approve: after human check` and the owner's go on this verdict in an attended run. Without both, GO and GO WITH NITS are comments.

Own PRs (author == the posting account): GitHub refuses approve and request-changes; use `--comment` with the verdict word first, or skip when the user excluded their own PRs.

Before posting, check the latest review by the posting account on that PR:

```
gh api repos/<o>/<r>/pulls/<n>/reviews --paginate --slurp | jq 'add // [] | [.[] | select(.user.login=="<user>")] | last | "\(.state) \(.commit_id) \(.body[0:40])"'
```

Use `--slurp`, not `--jq`: with `--paginate` a `--jq` filter runs once per page, so `last` returns one line per page and can read the wrong review on PRs with more than 30.

Skip when `commit_id` equals the current head and the state is APPROVED or CHANGES_REQUESTED, or the body starts with a verdict line. An empty-body COMMENTED review is a thread reply and does not count.

Body wording: first person, as the account owner. Never include session ids or links, scratchpad or temp paths. Then apply the profile's **Disclosure** setting:

- **`disclose`** (the default): end the body with one line that says truthfully whether a human checked it (a profile may give its own wording). Check it is there: `tail -1 body.md`.
  - Attended run, owner read it before posting: `_AI-assisted review, checked by me before posting._`
  - Unattended tick: `_Automated AI-assisted review; not yet checked by me._`
- **`plain`**: only when the profile says so, for a team that has agreed reviews carry no tool notes. No mention of AI, automation, agents or sessions; domain words that contain "session" (chat sessions) are fine. Grep the file before posting:

```
grep -iE 'claude|assisted|automat|session|/private/tmp' body.md
```

Under either setting, grep for temp paths: `grep -E '/private/tmp|/tmp/' body.md`.

Fixing a posted body: use **capital `-F`**. Lowercase `-f` sends the literal string `@file` as the body.

```
id=$(gh api repos/<o>/<r>/pulls/<n>/reviews --paginate --slurp | jq 'add // [] | [.[] | select(.user.login=="<user>")] | last | .id')
gh api -X PUT repos/<o>/<r>/pulls/<n>/reviews/$id -F body=@body.md
```

GET it back and grep again. Log every action as `repo#n  <approve|request-changes|comment|skipped:reason>  <sha9>  review_id=<id>`.

Dry run (no authorization): write the body to `<scratch>/<repo>-<n>.body.md` and append the exact `gh pr review ...` command to `<scratch>/would_run.txt`. Post nothing and record the head as `dry-run`, not as reviewed, so the next tick can post once authorization exists.
