#!/usr/bin/env python3
"""Merge compass: one table for a set of PRs (stacked and cross-repo).

usage: GH_TOKEN=... python3 merge_compass.py OWNER repo#N [repo#N ...] [--dep a#1>b#2 ...] [--wrinkles] [--share]
  --share prints the series as a pasteable list in merge order (full links, state, next action) and which
  reviewers who requested changes can be asked to re-review (their review predates the latest push).
  --wrinkles also lists what keeps a PR from merging cleanly: conflicts, a child behind its parent's head,
  a base branch that is gone (parent merged: retarget), a branch behind its base only when branch rules require it up to date (otherwise listed as info), red or pending CI.
  --dep "client#53>api#761" means client#53 cannot merge before api#761 (cross-repo).
Waves: 0 = already merged; 1 = base is the repo default branch and no unmerged dependency;
n+1 = one more than the deepest unmerged dependency (stack parent = open PR whose head is this PR's base).
Reads live state from the GitHub API every run; never trust a remembered status.
"""
import json
import subprocess
import sys


def gh(args):
    out = subprocess.run(["gh", *args], capture_output=True, text=True)
    if out.returncode:
        raise SystemExit(f"gh {' '.join(args)} failed: {out.stderr.strip()}")
    return json.loads(out.stdout)


def review_states(owner_repo, num):
    """Last APPROVED / CHANGES_REQUESTED / DISMISSED per reviewer from the REST reviews list.
    `gh pr view --json latestReviews` can come back empty while changes are still requested."""
    out = subprocess.run(["gh", "api", "--paginate", f"repos/{owner_repo}/pulls/{num}/reviews"],
                         capture_output=True, text=True)
    last = {}
    for r in json.loads(out.stdout or "[]"):
        if r["state"] in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            last[r["user"]["login"]] = (r["state"], r["submitted_at"])
    return {u: v for u, v in last.items() if v[0] != "DISMISSED"}


def main(argv):
    owner, refs, deps, show_wrinkles, show_share = argv[0], [], [], False, False
    it = iter(argv[1:])
    for a in it:
        if a == "--dep":
            deps.append(next(it))
        elif a == "--wrinkles":
            show_wrinkles = True
        elif a == "--share":
            show_share = True
        else:
            refs.append(a)
    prs = {}
    for ref in refs:
        repo, num = ref.split("#")
        d = gh(["pr", "view", num, "-R", f"{owner}/{repo}", "--json",
                "number,state,isDraft,title,url,commits,baseRefName,headRefName,headRefOid,reviewDecision,mergeStateStatus,"
                "latestReviews,statusCheckRollup,labels"])
        rs = review_states(f"{owner}/{repo}", num)
        head_time = d["commits"][-1]["committedDate"] if d["commits"] else ""
        checks = [(c.get("conclusion") or c.get("status") or "?") for c in d["statusCheckRollup"]]
        prs[ref] = {
            "state": d["state"], "draft": d["isDraft"], "base": d["baseRefName"], "head": d["headRefName"],
            "decision": d["reviewDecision"] or "-", "merge": d["mergeStateStatus"],
            "reviews": ",".join(f"{u}:{s[:4]}" for u, (s, _) in rs.items()) or "-",
            "ci": "FAIL" if "FAILURE" in checks else ("pending" if {"IN_PROGRESS", "QUEUED", "PENDING"} & set(checks) else "ok"),
            "labels": ",".join(l["name"] for l in d["labels"]) or "-", "title": d["title"][:48],
            "oid": d["headRefOid"], "owner_repo": f"{owner}/{repo}", "url": d["url"],
            "head_time": head_time,
            "stale_changes": [u for u, (s, at) in rs.items() if s == "CHANGES_REQUESTED" and at < head_time],
        }
    needs = {r: [] for r in prs}
    for r, p in prs.items():
        parent = next((q for q, o in prs.items() if q.split("#")[0] == r.split("#")[0]
                       and o["head"] == p["base"] and o["state"] == "OPEN"), None)
        if parent and p["state"] == "OPEN":
            needs[r].append(parent)
    for d in deps:
        a, b = d.split(">")
        if a in needs:
            needs[a].append(b)
    wave = {}

    def w(r, seen=()):
        if r in wave:
            return wave[r]
        if r in seen:
            raise SystemExit(f"dependency cycle at {r}")
        p = prs.get(r)
        if p is None or p["state"] == "MERGED":
            wave[r] = 0
            return 0
        wave[r] = 1 + max([w(x, seen + (r,)) for x in needs[r]] or [0])
        return wave[r]

    for r in prs:
        w(r)

    def action(r, p):
        if p["state"] == "MERGED":
            return "merged"
        if p["state"] == "CLOSED":
            return "closed: decide"
        if any(prs[x]["state"] != "MERGED" for x in needs[r] if x in prs):
            return "waits: " + ", ".join(x for x in needs[r] if x in prs and prs[x]["state"] != "MERGED")
        if p["merge"] == "DIRTY":
            return "fix conflicts / rebase"
        if p["ci"] == "FAIL":
            return "fix CI"
        if p["decision"] == "CHANGES_REQUESTED":
            return "answer review, ask re-review"
        if p["decision"] != "APPROVED":
            return "needs review"
        if p["draft"]:
            return "approved but draft: mark ready"
        if p["ci"] == "pending":
            return "wait for CI"
        return "READY to merge" if p["merge"] in ("CLEAN", "UNSTABLE", "HAS_HOOKS") else f"blocked ({p['merge']})"

    snapshot = (prs, needs)
    print("| wave | PR | base | draft | review | CI | merge state | depends on | next action |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in sorted(prs, key=lambda x: (wave[x], x)):
        p = prs[r]
        print(f"| {wave[r]} | {r} {p['title']} | {p['base']} | {'draft' if p['draft'] else 'ready'} | "
              f"{p['decision']} ({p['reviews']}) | {p['ci']} | {p['merge']} | {', '.join(needs[r]) or '-'} | {action(r, p)} |")
    if show_wrinkles:
        wrinkles(prs, needs)
    if show_share:
        share(prs, needs, wave, action)


def share(prs, needs, wave, action):
    """Pasteable series list in merge order, then who can be asked to re-review. No @-mentions: names are plain."""
    print("\n### Series status (merge order, live)")
    for i, r in enumerate(sorted(prs, key=lambda x: (wave[x], x)), 1):
        p = prs[r]
        state = "merged" if p["state"] == "MERGED" else ("draft" if p["draft"] else "ready")
        print(f"{i}. [{r}]({p['url']}) {p['title']}: {state}, review {p['decision']}, CI {p['ci']}, "
              f"{p['merge']}; {action(r, p)}")
    asks = [(r, p["stale_changes"]) for r, p in sorted(prs.items()) if p["state"] == "OPEN" and p["stale_changes"]]
    print("\n### Ready for re-review (changes were requested before the latest push)")
    if not asks:
        print("none")
    for r, who in asks:
        print(f"- [{r}]({prs[r]['url']}): {', '.join(who)}")


def behind_by(owner_repo, base, head):
    """Commits `base` has that `head` lacks (0 when head contains base)."""
    out = subprocess.run(["gh", "api", f"repos/{owner_repo}/compare/{base}...{head}", "-q", ".behind_by"],
                         capture_output=True, text=True)
    return int(out.stdout.strip()) if out.returncode == 0 and out.stdout.strip().isdigit() else None


def wrinkles(prs, needs):
    print("\n| PR | wrinkle | fix |")
    print("|---|---|---|")
    n = 0
    info = []
    for r, p in sorted(prs.items()):
        if p["state"] != "OPEN":
            continue
        found = []
        if p["merge"] == "DIRTY":
            found.append(("conflicts with its base", "merge the base into the branch, resolve, push"))
        parent = next((q for q in needs[r] if q in prs and q.split("#")[0] == r.split("#")[0]
                       and prs[q]["head"] == p["base"]), None)
        if parent and prs[parent]["state"] == "OPEN":
            b = behind_by(p["owner_repo"], prs[parent]["oid"], p["oid"])
            if b:
                found.append((f"behind parent {parent} by {b} commit(s)", "merge the parent into this branch, rerun checks"))
        elif not parent and p["base"] not in ("main", "master", "development"):
            found.append((f"base branch {p['base']} has no open PR (parent merged or deleted)", "retarget to the default branch, merge it in"))
        elif not parent:
            b = behind_by(p["owner_repo"], p["base"], p["oid"])
            if b and p["merge"] == "BEHIND":
                found.append((f"behind {p['base']} by {b} commit(s) and the branch rules require it up to date", "merge the base in"))
            elif b and p["merge"] != "DIRTY":
                info.append(f"{r}: {b} commit(s) behind {p['base']}, merges clean")
        if p["ci"] == "FAIL":
            found.append(("CI failing", "read the failed step: this PR's code, a flake, or CI infrastructure"))
        elif p["ci"] == "pending":
            found.append(("CI pending", "wait; do not report green"))
        for what, fix in found:
            n += 1
            print(f"| {r} | {what} | {fix} |")
    if not n:
        print("| - | none | - |")
    if info:
        print("\ninfo, not wrinkles (a clean merge into a moved base needs no action; merging it in anyway "
              "invalidates approvals and CI and cascades up the stack): " + "; ".join(info))


if __name__ == "__main__":
    main(sys.argv[1:])
