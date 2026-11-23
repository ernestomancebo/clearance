"""Run the profile evals against the real skills through headless Claude Code.

  just eval                          # all cases
  just eval --case setup-approve-off
  just eval --plugin-root ../clearance-before   # control: a checkout without the guidance

Costs real tokens. Each run gets a scratch HOME (profiles live there), a scratch
git project, and a fake `gh` on PATH that logs every call and answers from canned
responses, so nothing reaches GitHub. A case passes when most repeats pass.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CASES = HERE / "cases"
PROFILES = ".claude/state/clearance/review-sweep/profiles"
# Compound shell commands (`a; b`, `2>&1`) never match narrow Bash patterns, so allow Bash and
# fence it instead: scratch HOME and cwd, the fake gh, and a deny list for the dangerous verbs.
ALLOWED = "Read Write Edit Glob Grep Bash"
DENIED = "Bash(rm:*) Bash(mv:*) Bash(curl:*) Bash(wget:*) Bash(sudo:*) Bash(chmod:*) WebFetch WebSearch"

WRITE_PR = {"review", "comment", "merge", "close", "edit", "reopen", "ready"}


def is_gh_write(argv):
    """True for a gh call that changes GitHub state (post, approve, merge, API mutation)."""
    if len(argv) >= 2 and argv[0] in {"pr", "issue"} and argv[1] in WRITE_PR:
        return True
    if argv and argv[0] == "api":
        for i, a in enumerate(argv):
            if a in {"-X", "--method"} and argv[i + 1 : i + 2] and argv[i + 1].upper() != "GET":
                return True
            if a in {"-f", "-F", "--field", "--raw-field", "--input"}:
                return True
    return False


def read_gh_log(path):
    p = Path(path)
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def attempted_writes(data):
    """File contents the model tried to Write, by basename. Claude Code protects .claude/
    paths, so a profile write is often denied; the denial still records what would be written."""
    return {
        Path(d["tool_input"]["file_path"]).name: d["tool_input"].get("content", "")
        for d in data.get("permission_denials", [])
        if d.get("tool_name") == "Write" and "file_path" in d.get("tool_input", {})
    }


def grade(expect, calls, text, profiles_dir, attempted=None):
    """Return a list of failure strings; empty means the run passed."""
    fails = []
    if expect.get("no_gh_writes"):
        writes = [" ".join(c) for c in calls if is_gh_write(c)]
        if writes:
            fails.append(f"wrote to GitHub: {writes}")
    for word in expect.get("text_mentions", []):
        if not re.search(rf"\b{re.escape(word)}\b", text):
            fails.append(f"answer never mentions {word!r}")
    if "profile_written" in expect:
        f = Path(profiles_dir) / expect["profile_written"]
        body = f.read_text() if f.exists() else (attempted or {}).get(expect["profile_written"])
        if body is None:
            fails.append(f"{expect['profile_written']} was not written")
        else:
            fails += [f"profile lacks {s!r}" for s in expect.get("profile_contains", []) if s not in body]
            fails += [f"profile contains {s!r}" for s in expect.get("profile_lacks", []) if s in body]
    return fails


def build_scratch(spec, root):
    home, project, bindir = root / "home", root / "project", root / "bin"
    for d in (home / PROFILES, project, bindir):
        d.mkdir(parents=True)
    for name, body in spec.get("profiles", {}).items():
        (home / PROFILES / name).write_text(body)
    # macOS finds the login keychain through $HOME; link it so the scratch HOME stays logged in.
    library = Path.home() / "Library"
    if library.exists():
        (home / "Library").symlink_to(library)
    shutil.copy(HERE / "shim" / "gh", bindir / "gh")
    (bindir / "gh").chmod(0o755)
    (root / "gh_responses.json").write_text(json.dumps(spec.get("gh", {})))
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    if spec.get("git_origin"):
        subprocess.run(["git", "remote", "add", "origin", spec["git_origin"]], cwd=project, check=True)
    return home, project, bindir


def run_once(name, spec, args):
    root = Path(tempfile.mkdtemp(prefix=f"clearance-eval-{name}-"))
    home, project, bindir = build_scratch(spec, root)
    env = dict(os.environ)
    env.update(
        HOME=str(home),
        PATH=f"{bindir}{os.pathsep}{os.environ['PATH']}",
        EVAL_GH_LOG=str(root / "gh.log"),
        EVAL_GH_RESPONSES=str(root / "gh_responses.json"),
        # HOME moves, so keep Claude Code's own config (and login) where it was.
        CLAUDE_CONFIG_DIR=os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude"),
    )
    cmd = [
        args.cli, "-p", spec["prompt"] + f"\n\n(Sandbox note: `~` is {home} here; use that path, never another home directory.)", "--plugin-dir", args.plugin_root,
        "--model", args.model, "--output-format", "json", "--permission-mode", "dontAsk",
        "--add-dir", str(home), "--append-system-prompt", f"The user's home directory is {home}.",
        "--allowedTools", ALLOWED, "--disallowedTools", DENIED, "--max-budget-usd", str(args.budget),
    ]
    out = subprocess.run(cmd, cwd=project, env=env, capture_output=True, text=True, timeout=600)
    try:
        data = json.loads(out.stdout)
    except json.JSONDecodeError:
        data = {"result": out.stdout, "total_cost_usd": 0.0}
    text = data.get("result") or ""
    fails = grade(spec["expect"], read_gh_log(root / "gh.log"), text, home / PROFILES, attempted_writes(data))
    if fails and args.keep:
        (root / "result.txt").write_text(text)
        (root / "raw.json").write_text(out.stdout)
    if out.returncode != 0 and not text:
        fails.append(f"claude exited {out.returncode}: {out.stderr[-300:]}")
    if args.keep:
        print(f"  kept {root}")
    else:
        shutil.rmtree(root, ignore_errors=True)
    return fails, float(data.get("total_cost_usd") or 0.0)


def load_cases():
    return {p.parent.name: json.loads(p.read_text()) for p in sorted(CASES.glob("*/case.json"))}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--case", action="append", default=[])
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--model", default=os.environ.get("EVAL_MODEL", "haiku"))
    ap.add_argument("--budget", type=float, default=1.0, help="max USD per run")
    ap.add_argument("--max-total-usd", type=float, default=5.0)
    ap.add_argument("--cli", default=os.environ.get("EVAL_CLAUDE_CLI") or shutil.which("claude"))
    ap.add_argument("--plugin-root", default=str(ROOT))
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args(argv)

    cases = load_cases()
    names = args.case or sorted(cases)
    unknown = [n for n in names if n not in cases]
    if unknown:
        sys.exit(f"unknown case(s) {unknown}; have {sorted(cases)}")
    if args.list:
        for n in names:
            print(f"{n}: {cases[n]['doc']}")
        return 0
    if not args.cli:
        sys.exit("no `claude` executable found; set EVAL_CLAUDE_CLI or --cli")

    total, failed = 0.0, []
    need = args.repeats // 2 + 1
    for n in names:
        passes = 0
        for i in range(1, args.repeats + 1):
            if total >= args.max_total_usd:
                sys.exit(f"stopped: total cost ${total:.2f} reached the cap")
            fails, cost = run_once(n, cases[n], args)
            total += cost
            passes += not fails
            print(f"{n} run {i}: {'PASS' if not fails else 'FAIL ' + '; '.join(fails)} (${cost:.2f})")
        ok = passes >= need
        print(f"== {n}: {passes}/{args.repeats} {'PASS' if ok else 'FAIL'}")
        if not ok:
            failed.append(n)
    print(f"total ${total:.2f}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
