"""Test the repository boundary between Mnemosyne and Athena."""

from __future__ import annotations

import json
from pathlib import Path

from mnemosyne_skill_utils import find_skill_files, parse_frontmatter

REPO_ROOT = Path(__file__).resolve().parents[1]

# Athena main at 44a22b8dfab986f505a99ce52e8521f645da3e2b.
ATHENA_SKILL_NAMES = {
    "advise",
    "brainstorm",
    "change-review",
    "finalize-plan",
    "git-worktrees",
    "issue-review",
    "learn",
    "myrmidon-swarm",
    "plan-issue",
    "pr-review",
    "repo-review",
    "systematic-debugging",
    "test-driven-development",
    "tidy",
}

OBSOLETE_CLAUDE_PLUGIN_PATHS = (
    ".claude/hooks",
    ".claude/plugins",
    ".claude/shared",
    "plugins",
)


def test_mnemosyne_does_not_vendor_claude_plugins() -> None:
    remaining = [
        path
        for path in OBSOLETE_CLAUDE_PLUGIN_PATHS
        if any(candidate.is_file() for candidate in (REPO_ROOT / path).rglob("*"))
    ]

    assert remaining == []


def test_claude_settings_enable_only_athena() -> None:
    settings = json.loads((REPO_ROOT / ".claude/settings.json").read_text(encoding="utf-8"))

    assert "hooks" not in settings
    assert settings["enabledPlugins"] == {"athena@Athena": True}


def test_flat_corpus_does_not_duplicate_athena_skills() -> None:
    mnemosyne_names: set[str] = set()
    for path in find_skill_files(REPO_ROOT / "skills"):
        frontmatter, _, errors = parse_frontmatter(path.read_text(encoding="utf-8"))
        assert errors == [], path
        mnemosyne_names.add(str(frontmatter["name"]))

    assert mnemosyne_names.isdisjoint(ATHENA_SKILL_NAMES)
