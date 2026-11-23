# Choosing a profile

Applies when `/clearance:review-sweep` is run without a name. First hit wins:

1. **A name in the invocation** (`/clearance:review-sweep <name>`).
2. **Exactly one profile lists this directory's repo.** Parse `git remote get-url origin` to `owner/repo` (ssh or https, with or without `.git`, case-insensitive) and compare it with each profile's Repos. Two matches: ask which. Not a git repo, no `origin`, or a fork origin that no profile lists: skip this step.
3. **Exactly one profile exists.**
4. **Otherwise** list the profiles (name, account, repos) and ask once per session. With no profiles at all, say so, point to `/clearance:setup`, and dry-run.

A profile's Repos are ``owner/repo`` lines. The older single-owner form, ``## Repos (owner `x`)`` followed by a comma list, is still accepted: expand it to `owner/repo` before comparing.

## Does it authorize posting?

| How the profile was chosen | Posts without a further confirmation? |
|---|---|
| Named in the invocation | Yes |
| Chosen by the user when asked (step 2 tie, step 4) | Yes |
| Picked automatically (step 2 or 3 alone) | No: announce it with its reason ("it lists this repo", "it is your only profile"), review, post nothing until the user confirms that name once. The confirmation counts as naming it. |

## Under `/loop`

Once a profile is confirmed, the loop prompt must name it so every tick repeats it. Self-paced loops re-arm with their own prompt: write the name into it. A fixed-interval prompt belongs to the user: tell them to restart the loop as `/loop <interval> /clearance:review-sweep <name>`. Until then each tick re-resolves and posts nothing.
