"""Deterministic checks on the skills. No network, no model."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILLS = sorted(p.parent for p in (ROOT / "skills").glob("*/SKILL.md"))
EXAMPLE = ROOT / "skills/review-sweep/profiles/example.md"


def frontmatter(skill_dir):
    m = re.match(r"---\n(.*?)\n---\n", (skill_dir / "SKILL.md").read_text(), re.S)
    assert m, f"{skill_dir.name}: no frontmatter"
    return dict(line.split(": ", 1) for line in m.group(1).splitlines() if ": " in line)


@pytest.mark.parametrize("d", SKILLS, ids=lambda d: d.name)
def test_frontmatter(d):
    fm = frontmatter(d)
    assert fm["name"] == d.name
    assert fm["description"].startswith("Use when"), "description must start with 'Use when'"
    assert len(fm["description"]) <= 1024


@pytest.mark.parametrize("d", SKILLS, ids=lambda d: d.name)
def test_linked_files_exist(d):
    """Every references/ or profiles/ file a SKILL.md names must exist (in it or a sibling skill)."""
    text = (d / "SKILL.md").read_text()
    missing = [
        ref
        for ref in set(re.findall(r"\b((?:references|profiles)/[\w.-]+\.md)\b", text))
        if not any((s / ref).exists() for s in [d, *SKILLS])
    ]
    assert not missing, f"{d.name} links missing files: {missing}"


def test_readme_table_matches_skills():
    readme = (ROOT / "README.md").read_text()
    rows = set(re.findall(r"^\| `([\w-]+)` \|", readme, re.M))
    assert rows == {d.name for d in SKILLS}


def test_setup_covers_every_template_section():
    setup = (ROOT / "skills/setup/SKILL.md").read_text()
    sections = re.findall(r"^## (\w+)", EXAMPLE.read_text(), re.M)
    assert sections, "example.md has no sections?"
    assert [s for s in sections if s not in setup] == []


def test_setup_template_path_is_skill_relative():
    setup = (ROOT / "skills/setup/SKILL.md").read_text()
    assert "skills/review-sweep/profiles/example.md" not in setup
    assert "../review-sweep/profiles/example.md" in setup


def test_setup_cannot_post_or_switch_accounts():
    setup = (ROOT / "skills/setup/SKILL.md").read_text()
    assert not re.search(r"gh (pr|issue) |--approve|--request-changes|-X (POST|PUT|PATCH|DELETE)", setup)
    for line in setup.splitlines():
        if "gh auth switch" in line:
            assert "Never" in line, f"gh auth switch outside a never-rule: {line}"


def test_example_repos_are_owner_repo_lines():
    body = EXAMPLE.read_text().split("## Repos", 1)[1].split("\n## ", 1)[0]
    assert re.findall(r"^- [\w.-]+/[\w.-]+$", body, re.M)


def test_resolution_has_the_safety_rows():
    ref = (ROOT / "skills/review-sweep/references/profiles.md").read_text()
    assert "Two matches: ask which" in ref
    assert "post nothing until the user confirms" in ref


def test_no_stale_plugin_name():
    hits = [
        str(p.relative_to(ROOT))
        for p in ROOT.rglob("*")
        if p.is_file() and ".git" not in p.parts and "tests" not in p.relative_to(ROOT).parts
        and p.suffix in {".md", ".json", ".py"} and "right-model" in p.read_text()
    ]
    assert not hits, hits
