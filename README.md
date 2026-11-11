# merge-compass

A Claude Code plugin for the part of the development lifecycle that starts
once code is in a pull request: reviewing it, acting on review feedback, and
getting a stacked or multi-repo series merged in the right order.

## Install

```bash
claude plugin marketplace add ernestomancebo/merge-compass
claude plugin install merge-compass@merge-compass-marketplace
```

Requires the [GitHub CLI](https://cli.github.com/) (`gh`), authenticated for
the accounts you review with. `reviewing-open-prs` runs its two-axis review
from `mattpocock-skills:code-review`; install that plugin too.

## Skills

| Skill | Use it when | What it does |
|---|---|---|
| `reviewing-open-prs` | You want open PRs across one or more repos reviewed, once or on a `/loop` | Scans, reviews only heads it has not seen, posts one verdict per head (GO / GO WITH NITS / NO GO) and records state, so a new session resumes where the last stopped |
| `merge-compass` | A stacked or cross-repo PR set changed and someone asks "what merges next?" | Reads live GitHub state and prints waves, dependencies, review/CI state and the next action per PR (`merge_compass.py`) |
| `merge-compass-sonar` | Review feedback arrived on a stacked series, or the series conflicts or trails its parents | Checks each review claim against the code, routes it to the PR that introduced it, propagates fixes up the stack and clears merge blockers |
| `stacked-pr-finisher` | A series is built and about to go to review or release | Audits bases, waves, labels, cross-repo links and PR descriptions, and lists what fails |

## Safety rules the skills follow

- **Nothing outward-facing without standing authorization.** A review profile
  lists exactly what may be posted; without one, `reviewing-open-prs` dry-runs.
  None of the skills merge, close or force-push.
- **Approvals need a human check.** `reviewing-open-prs` approves only when the
  profile sets `Approve: after human check` and you said go on that verdict in an
  attended run. Unattended `/loop` ticks post GO verdicts as comments.
- **Agent approvals should not count toward required reviews.** Keep branch
  protection requiring a human approval; the agent's review informs it, it does
  not replace it.
- **Disclosure is a profile setting.** By default each posted review and reply
  ends with a one-line AI-assisted note that says whether you checked it before
  posting. A profile can choose `plain` when a team has agreed on reviews
  without tool notes.
- **Live state only.** Statuses are read from GitHub on every run, never from
  memory.

## Profiles

Copy `skills/reviewing-open-prs/profiles/example.md` to
`~/.claude/state/reviewing-open-prs/profiles/<name>.md`, edit the account, repos
and rules, then run `/merge-compass:reviewing-open-prs <name>` or
`/loop 30m /merge-compass:reviewing-open-prs <name>`.

## Pairs with

[right-model](https://github.com/ernestomancebo/right-model): pin each
subagent role to the model tier its task needs. The review subagents here are
a natural fit for its `verifier` role.

## License

MIT
