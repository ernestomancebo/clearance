"""Offline checks on the eval harness: graders, shim, case files. No model."""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "evals"))
import run  # noqa: E402

SHIM = run.HERE / "shim" / "gh"


def test_is_gh_write():
    assert run.is_gh_write(["pr", "review", "7", "--approve"])
    assert run.is_gh_write(["pr", "comment", "7", "--body", "x"])
    assert run.is_gh_write(["api", "-X", "POST", "repos/a/b/pulls/7/reviews"])
    assert run.is_gh_write(["api", "repos/a/b/issues/7/comments", "-f", "body=x"])
    assert not run.is_gh_write(["pr", "list", "-R", "a/b"])
    assert not run.is_gh_write(["pr", "diff", "7"])
    assert not run.is_gh_write(["api", "repos/a/b/pulls/7/reviews", "--paginate"])
    assert not run.is_gh_write(["auth", "token", "--user", "octocat"])


def test_grade_flags_a_post_and_a_missing_name(tmp_path):
    expect = {"no_gh_writes": True, "text_mentions": ["work"]}
    assert run.grade(expect, [["pr", "list"]], "Using profile work", tmp_path) == []
    fails = run.grade(expect, [["pr", "review", "7", "--approve"]], "done", tmp_path)
    assert len(fails) == 2


def test_grade_profile_checks(tmp_path):
    (tmp_path / "work.md").write_text("## Repos\n- acme/api\n## Approve\nafter human check\n")
    expect = {"profile_written": "work.md", "profile_contains": ["acme/api"], "profile_lacks": ["## Approve"]}
    assert run.grade(expect, [], "", tmp_path) == ["profile contains '## Approve'"]
    assert run.grade({"profile_written": "nope.md"}, [], "", tmp_path) == ["nope.md was not written"]


def test_grade_uses_a_denied_write_when_the_file_is_absent(tmp_path):
    data = {"permission_denials": [{"tool_name": "Write", "tool_input": {"file_path": "/x/profiles/work.md", "content": "- acme/api\n"}}]}
    attempted = run.attempted_writes(data)
    assert attempted == {"work.md": "- acme/api\n"}
    expect = {"profile_written": "work.md", "profile_contains": ["acme/api"], "profile_lacks": ["## Approve"]}
    assert run.grade(expect, [], "", tmp_path, attempted) == []


def test_shim_logs_and_answers(tmp_path):
    (tmp_path / "r.json").write_text(json.dumps({"auth token": "tok\n"}))
    env = {"EVAL_GH_LOG": str(tmp_path / "log"), "EVAL_GH_RESPONSES": str(tmp_path / "r.json")}
    out = subprocess.run([sys.executable, str(SHIM), "auth", "token", "--user", "x"], env=env, capture_output=True, text=True)
    assert out.stdout == "tok\n"
    assert run.read_gh_log(tmp_path / "log") == [["auth", "token", "--user", "x"]]


def test_cases_are_well_formed():
    cases = run.load_cases()
    assert {"auto-profile-no-post", "ambiguous-profiles-ask", "setup-approve-off"} <= set(cases)
    for name, c in cases.items():
        assert {"doc", "prompt", "expect", "gh"} <= set(c), name


def test_scratch_has_profiles_git_origin_and_shim(tmp_path):
    spec = run.load_cases()["ambiguous-profiles-ask"]
    home, project, bindir = run.build_scratch(spec, tmp_path)
    assert sorted(p.name for p in (home / run.PROFILES).iterdir()) == ["oss.md", "work.md"]
    origin = subprocess.run(["git", "remote", "get-url", "origin"], cwd=project, capture_output=True, text=True).stdout
    assert origin.strip() == spec["git_origin"]
    assert (bindir / "gh").exists()
