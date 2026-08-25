"""Test writing-policy presence, scope, delegation, and protected content.

These tests do not determine natural-language conformance with ASD-STE100.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from mnemosyne_skill_utils import find_skill_files

REPO_ROOT = Path(__file__).resolve().parents[1]

POLICY_REFERENCE_SURFACES = (
    "AGENTS.md",
    "CONTRIBUTING.md",
    "README.md",
    "SECURITY.md",
    "docs/ci/merge-queue.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".claude/hooks/learn-trigger.py",
    ".claude/plugins/repo-analyzer/.claude-plugin/plugin.json",
    "plugins/tooling/mnemosyne/.claude-plugin/plugin.json",
    "plugins/ci-cd/mojo-format-non-blocking.json",
    "plugins/tooling/ci-matrix-continue-on-error-pattern.json",
    "schemas/skill-frontmatter.schema.json",
    "plugins/tooling/mnemosyne/references/experiment-log.md",
    "plugins/tooling/mnemosyne/references/troubleshooting.md",
)

POLICY_REFERENCE_PATTERNS = (
    "templates/**/*.md",
    ".github/ISSUE_TEMPLATE/**/*.md",
    ".claude/shared/**/*.md",
    ".claude/plugins/**/commands/*.md",
    "plugins/**/README.md",
    "plugins/**/SKILL.md",
)

DELEGATING_DIRECTION_SURFACES = ("CLAUDE.md",)

PRINCIPLE_BLOCKS = {
    "AGENTS.md": (
        r"^### Key Development Principles\n.*?(?=^### |\Z)",
        "a598f08035644f5642ef27ffde1f879c77b9e4df3b14be96b289535032b13644",
    ),
    "CONTRIBUTING.md": (
        r"^### General Principles\n.*?(?=^## |\Z)",
        "a301685c38836c6f3d22ba07eb78abb9ea1b483bc37effb05b5d89188dd166c0",
    ),
    ".claude/plugins/repo-analyzer/commands/repo-analyze.md": (
        r"<development_principles>.*?</development_principles>",
        "17d93d720772cd7fef0a408f14d509c214d9603bf3f8e71b560d19236ac7414f",
    ),
    ".claude/plugins/repo-analyzer/commands/repo-analyze-strict.md": (
        r"<development_principles>.*?</development_principles>",
        "17d93d720772cd7fef0a408f14d509c214d9603bf3f8e71b560d19236ac7414f",
    ),
    ".claude/plugins/repo-analyzer/commands/repo-analyze-quick.md": (
        r"<development_principles>.*?</development_principles>",
        "e36469013526ab8842a670a68f06a3ae56b27eb7f32379e9f7a76eec0162316f",
    ),
}


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _policy_reference_surfaces() -> list[str]:
    paths = set(POLICY_REFERENCE_SURFACES)
    for pattern in POLICY_REFERENCE_PATTERNS:
        paths.update(path.relative_to(REPO_ROOT).as_posix() for path in REPO_ROOT.glob(pattern))
    return sorted(paths)


def test_agents_contract_requires_asd_ste100() -> None:
    contract = _read("AGENTS.md")

    assert "ASD-STE100 Simplified Technical English" in contract
    assert "https://www.asd-ste100.org" in contract
    assert "Issue 9" in contract
    assert "all active skill prose" in contract.lower()

    policy = _read("docs/asd-ste100.md")
    assert "ASD-STE100 Simplified Technical English" in policy
    assert "https://www.asd-ste100.org" in policy
    assert "Issue 9" in policy
    assert "not a statement of ASD approval" in policy


def test_reviewed_direction_surfaces_reference_asd_ste100() -> None:
    missing = [path for path in _policy_reference_surfaces() if "ASD-STE100" not in _read(path)]

    assert missing == []


def test_policy_declares_scope_for_all_retrievable_skills() -> None:
    retrievable_skills = find_skill_files(REPO_ROOT / "skills")

    assert retrievable_skills
    assert "All retrievable main skill files in `skills/`" in _read("docs/asd-ste100.md")
    assert "All active skill prose" in _read("AGENTS.md")


def test_compatibility_directions_delegate_to_agents_contract() -> None:
    missing = [path for path in DELEGATING_DIRECTION_SURFACES if "AGENTS.md" not in _read(path)]

    assert missing == []


def test_development_principles_are_unchanged() -> None:
    for path, (pattern, expected_digest) in PRINCIPLE_BLOCKS.items():
        match = re.search(pattern, _read(path), flags=re.MULTILINE | re.DOTALL)
        assert match is not None, f"Missing protected principles block in {path}"
        actual_digest = hashlib.sha256(match.group(0).encode()).hexdigest()
        assert actual_digest == expected_digest, f"Protected principles changed in {path}"
