"""Test writing-policy presence, scope, delegation, and protected content.

These tests do not determine natural-language conformance with ASD-STE100.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from collections import Counter
from pathlib import Path

from mnemosyne_skill_utils import find_skill_files

REPO_ROOT = Path(__file__).resolve().parents[1]
ASD_SITE_TARGETS = {
    "https://www.asd-ste100.org",
    "https://www.asd-ste100.org/",
}
ASD_DOWNLOAD_TARGET = "https://www.asd-ste100.org/STE_downloads.html"

POLICY_REFERENCE_SURFACES = (
    "AGENTS.md",
    "CONTRIBUTING.md",
    "README.md",
    "SECURITY.md",
    "docs/ci/merge-queue.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    "schemas/skill-frontmatter.schema.json",
)

POLICY_REFERENCE_PATTERNS = (
    "templates/**/*.md",
    ".github/ISSUE_TEMPLATE/**/*.md",
)

DELEGATING_DIRECTION_SURFACES = ("CLAUDE.md",)
PROTECTED_PATHS = {
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "LICENSE",
    "THIRD_PARTY_LICENSES.md",
    "uv.lock",
}

PRINCIPLE_BLOCKS = {
    "AGENTS.md": (
        r"^### Key Development Principles\n.*?(?=^### |\Z)",
        "a598f08035644f5642ef27ffde1f879c77b9e4df3b14be96b289535032b13644",
    ),
    "CONTRIBUTING.md": (
        r"^### General Principles\n.*?(?=^## |\Z)",
        "a301685c38836c6f3d22ba07eb78abb9ea1b483bc37effb05b5d89188dd166c0",
    ),
}


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _markdown_link_targets(text: str) -> set[str]:
    return set(re.findall(r"\]\((https?://[^)\s]+)\)", text))


def _policy_reference_surfaces() -> list[str]:
    paths = set(POLICY_REFERENCE_SURFACES)
    for pattern in POLICY_REFERENCE_PATTERNS:
        paths.update(path.relative_to(REPO_ROOT).as_posix() for path in REPO_ROOT.glob(pattern))
    return sorted(paths)


def test_agents_contract_requires_asd_ste100() -> None:
    contract = _read("AGENTS.md")

    assert "ASD-STE100 Simplified Technical English" in contract
    assert ASD_SITE_TARGETS & _markdown_link_targets(contract)
    assert "Issue 9" in contract
    assert "all active skill prose" in contract.lower()

    policy = _read("docs/asd-ste100.md")
    assert "ASD-STE100 Simplified Technical English" in policy
    assert ASD_SITE_TARGETS & _markdown_link_targets(policy)
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


def _tracked_paths() -> list[str]:
    output = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=False,
    ).stdout
    return sorted(path for path in output.decode().split("\0") if path)


def test_active_guidance_inventory_is_closed() -> None:
    """Require tracked active surfaces to match an explicit review class."""
    paths = _tracked_paths()
    active_skills = {
        path for path in paths if path.startswith("skills/") and path.endswith(".md") and not path.endswith(".notes.md")
    }
    discovered_skills = {path.relative_to(REPO_ROOT).as_posix() for path in find_skill_files(REPO_ROOT / "skills")}
    assert discovered_skills == active_skills

    def classify(path: str) -> str:
        if path in active_skills:
            return "active-main-skill"
        if path.startswith("skills/"):
            return "protected-skill-companion"
        if path.startswith(".history/") or path in PROTECTED_PATHS:
            return "protected-record"
        if path.endswith(".md"):
            return "active-guidance-markdown"
        return "mixed-tracked-file"

    unknown = [
        path
        for path in paths
        if path.startswith("skills/")
        and path not in active_skills
        and not path.endswith(".history")
        and not path.endswith(".notes.md")
    ]
    assert unknown == []
    classes = Counter(classify(path) for path in paths)
    assert classes["active-main-skill"] == len(active_skills)
    assert classes["active-guidance-markdown"] > 0
    assert classes["mixed-tracked-file"] > 0


def test_official_source_issue_and_download_contract() -> None:
    """Require links to the official site and download page without copied rules."""
    policy = _read("docs/asd-ste100.md")

    assert "Issue 9" in policy
    assert "15 January 2025" in policy
    policy_links = _markdown_link_targets(policy)
    assert ASD_SITE_TARGETS & policy_links
    assert ASD_DOWNLOAD_TARGET in policy_links
    assert "## Writing Rules" not in policy
    assert "controlled dictionary" not in policy.lower()


def test_all_active_guidance_surfaces_reference_or_delegate_to_policy() -> None:
    """Require active authoring surfaces to name the policy or delegate to AGENTS.md."""
    paths = _policy_reference_surfaces()
    missing = [path for path in paths if "ASD-STE100" not in _read(path) and "AGENTS.md" not in _read(path)]
    assert missing == []


def test_pull_request_template_requires_complete_writing_review() -> None:
    """Require the pull-request checklist to cover scope, literals, and attribution."""
    template = _read(".github/PULL_REQUEST_TEMPLATE.md")
    for phrase in (
        "complete `git ls-files` inventory",
        "inventory digest",
        "Protected literals",
        "software-development principles",
        "copied standard",
        "approval, certification, or endorsement",
        "Athena boundary",
    ):
        assert phrase.lower() in template.lower()


def test_active_marketplace_claims_match_athena_boundary() -> None:
    """Reject current prose that describes Mnemosyne as a plugin marketplace."""
    paths = [
        path
        for path in _tracked_paths()
        if path.startswith("skills/") and path.endswith(".md") and not path.endswith(".notes.md")
    ]
    for path in paths:
        text = _read(path).lower()
        assert "mnemosyne marketplace" not in text
        assert "skills marketplace" not in text


def test_repository_makes_no_asd_or_stemg_approval_claims() -> None:
    """Reject positive claims that ASD or STEMG approves this repository."""
    text = "\n".join(
        _read(path)
        for path in _tracked_paths()
        if path not in PROTECTED_PATHS
        and not path.startswith(".history/")
        and not path.startswith("tests/")
        and (not path.startswith("skills/") or path.endswith(".md"))
    ).lower()
    for pattern in (
        r"asd.{0,40}(approves|certifies|endorses)",
        r"stemg.{0,40}(approves|certifies|endorses)",
    ):
        assert re.search(pattern, text) is None


def test_repository_does_not_vendor_asd_ste100_assets() -> None:
    """Reject tracked standard PDFs, dictionaries, and logos."""
    paths = _tracked_paths()
    forbidden = [
        path
        for path in paths
        if re.search(r"(?:asd|ste|simplified|technical).*(?:pdf|dict|logo)|(?:pdf|dict|logo).*(?:asd|ste)", path, re.I)
    ]
    assert forbidden == []
