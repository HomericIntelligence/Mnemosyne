"""Test writing-policy presence, scope, delegation, and protected content.

These tests do not determine natural-language conformance with ASD-STE100.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from mnemosyne_skill_utils import find_skill_files

REPO_ROOT = Path(__file__).resolve().parents[1]
ASD_SITE_TARGETS = {
    "https://www.asd-ste100.org",
    "https://www.asd-ste100.org/",
}
ASD_DOWNLOAD_TARGET = "https://www.asd-ste100.org/STE_downloads.html"

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

PROTECTED_LITERAL_EXPECTATIONS = {
    "AGENTS.md": (
        "Read the repository [ASD-STE100 writing policy](docs/asd-ste100.md).",
        "https://www.asd-ste100.org",
        "https://www.asd-ste100.org/STE_downloads.html",
        ".claude/settings.json",
        "`uv sync`",
        "`uv run python scripts/validate_plugins.py`",
        "`uv run python -m pytest tests/`",
        "`uv build`",
        "skills/<name>.md",
        "skills/<name>.notes.md",
        "skills/<name>.history",
    ),
    ".claude/settings.json": (
        '"enabledPlugins": {',
        '"athena@Athena": true',
        '"https://github.com/HomericIntelligence/Athena.git"',
    ),
    "docs/asd-ste100.md": (
        "https://www.asd-ste100.org/",
        "https://www.asd-ste100.org/STE_downloads.html",
        "https://www.asd-ste100.org/STE_faq.html",
        "All retrievable main skill files in `skills/`",
    ),
    "scripts/mnemosyne_skill_utils.py": (
        r'if not re.match(r".*\.notes.*\.md$"',
        r'not re.match(r".*\.history"',
    ),
    "skills/advise-before-planning.md": (
        'skills_path = mnemosyne_root / "skills"',
        "skills_path=str(skills_path)",
        "$HOME/.agent-brain/Mnemosyne",
    ),
}


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _markdown_link_targets(text: str) -> set[str]:
    return set(re.findall(r"\]\((https?://[^)\s]+)\)", text))


def _policy_reference_surfaces() -> list[str]:
    return sorted(path for path in _tracked_paths() if _is_active_guidance_path(path))


def _active_skill_paths() -> set[str]:
    """Return the active main-skill paths from the canonical discovery helper."""
    return {path.relative_to(REPO_ROOT).as_posix() for path in find_skill_files(REPO_ROOT / "skills")}


def _is_skill_companion(path: str) -> bool:
    """Identify notes and history companions in the skills corpus only."""
    if not path.startswith("skills/"):
        return False
    name = Path(path).name
    return re.search(r"\.notes.*\.md$", name) is not None or re.search(r"\.history(?:.*)?$", name) is not None


def _is_active_guidance_path(path: str) -> bool:
    """Classify tracked authoring guidance while excluding legal and history records."""
    return (
        path.endswith(".md")
        and not path.startswith("skills/")
        and not path.startswith(".history/")
        and path not in PROTECTED_PATHS
    ) or (path.startswith("schemas/") and path.endswith(".json"))


def _active_review_paths() -> list[str]:
    """Return active prose paths without notes/history or protected records."""
    return [
        path
        for path in _tracked_paths()
        if path not in PROTECTED_PATHS
        and not path.startswith(".history/")
        and not _is_skill_companion(path)
    ]


def test_agents_contract_requires_asd_ste100() -> None:
    contract = _read("AGENTS.md")

    assert "ASD-STE100 Simplified Technical English" in contract
    assert "Simplified Technical English Maintenance Group (STEMG)" in contract
    assert ASD_SITE_TARGETS & _markdown_link_targets(contract)
    assert "Issue 9" in contract
    assert "all active skill prose" in contract.lower()

    policy = _read("docs/asd-ste100.md")
    assert "ASD-STE100 Simplified Technical English" in policy
    assert ASD_SITE_TARGETS & _markdown_link_targets(policy)
    assert "Issue 9" in policy
    assert "not a statement of ASD approval" in policy


def test_reviewed_direction_surfaces_reference_asd_ste100() -> None:
    missing = [
        path
        for path in _policy_reference_surfaces()
        if "ASD-STE100" not in _read(path) and "AGENTS.md" not in _read(path)
    ]

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
    active_skills = _active_skill_paths()
    assert active_skills
    tracked_active_skills = {
        path for path in paths if path.startswith("skills/") and path.endswith(".md") and not _is_skill_companion(path)
    }
    assert active_skills == tracked_active_skills

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
        if path.startswith("skills/") and path not in active_skills and not _is_skill_companion(path)
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


def test_policy_links_instead_of_copying_asd_rules() -> None:
    """Reject the former local rule-summary markers without claiming full copy detection."""
    policy = _read("docs/asd-ste100.md")

    assert "https://www.asd-ste100.org/" in policy
    assert ASD_DOWNLOAD_TARGET in policy
    assert "## Writing Rules" not in policy
    for former_rule in (
        "1. Use one approved term for each concept.",
        "7. Limit an instruction sentence to 20 words.",
        "10. Do not use contractions, semicolons, or Latin abbreviations.",
    ):
        assert former_rule not in policy


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


def _prohibited_ownership_patterns() -> tuple[str, ...]:
    return (
        r"mnemosyne\s*@\s*mnemosyne",
        r"\bmnemosyne(?:-style)?(?:\s+(?!(?:is|does)\s+not\b|isn't\b)\w+){0,3}\s+marketplaces?\b",
        r"\bplugin\s+marketplace\s*\(\s*mnemosyne\s*\)",
        r"(?:mnemosyne|projectmnemosyne)[^\n]{0,100}(?:marketplace\.json|plugin\.json|\.claude-plugin)",
        r"(?:marketplace\.json|plugin\.json|\.claude-plugin)[^\n]{0,100}(?:mnemosyne|projectmnemosyne)",
        r"(?:/advise|/learn).{0,80}projecthephaestus\s+(?:commands?|plugin|skills?)",
        r"projecthephaestus\s+(?:commands?|plugin|skills?).{0,80}(?:/advise|/learn)",
        r"\bprojecthephaestus\s+owns?\s+(?:the\s+)?(?:/advise|/learn)\b",
        r"(?:/advise|/learn)\s+(?:is|are)\s+owned\s+by\s+projecthephaestus\b",
    )


def _active_claim_scan_paths() -> list[str]:
    """Cover active skills, guidance, schema prose, and other active tracked text."""
    active_non_test = {path for path in _active_review_paths() if not path.startswith("tests/")}
    return sorted(set(_active_skill_paths()) | set(_policy_reference_surfaces()) | active_non_test)


def test_ownership_patterns_cover_reverse_forms_without_broad_matches() -> None:
    """Keep reverse marketplace and ProjectHephaestus ownership forms covered."""
    prohibited_examples = (
        "plugin marketplace (Mnemosyne)",
        "ProjectHephaestus owns /advise",
        "ProjectHephaestus owns /learn",
        "/advise is owned by ProjectHephaestus",
        "/learn is owned by ProjectHephaestus",
    )
    for example in prohibited_examples:
        assert any(re.search(pattern, example.lower(), flags=re.DOTALL) for pattern in _prohibited_ownership_patterns())

    safe_examples = (
        "A plugin marketplace can provide generic skills.",
        "Mnemosyne is not a plugin marketplace.",
        "Mnemosyne is not a marketplace.",
        "Athena owns /advise and /learn; ProjectHephaestus provides shared utilities.",
    )
    for example in safe_examples:
        assert all(
            re.search(pattern, example.lower(), flags=re.DOTALL) is None
            for pattern in _prohibited_ownership_patterns()
        )


def test_protected_literals_are_unchanged() -> None:
    """Keep high-risk commands, paths, URLs, and configuration values exact."""
    for path, literals in PROTECTED_LITERAL_EXPECTATIONS.items():
        text = _read(path)
        for literal in literals:
            assert literal in text, f"{path}: missing protected literal {literal!r}"


def test_active_marketplace_claims_match_athena_boundary() -> None:
    """Reject active guidance that assigns corpus ownership to a plugin."""
    paths = _active_claim_scan_paths()
    assert set(_active_skill_paths()).issubset(paths)
    assert "schemas/skill-frontmatter.schema.json" in paths
    assert "configs/github/merge-queue-policy.json" in paths
    for path in paths:
        text = _read(path).lower()
        for pattern in _prohibited_ownership_patterns():
            assert re.search(pattern, text, flags=re.DOTALL) is None, f"{path}: {pattern}"


def test_active_review_scans_exclude_all_skill_companions() -> None:
    """Keep notes/history evidence outside active prose and approval scans."""
    paths = _active_review_paths()
    assert paths
    assert all(not _is_skill_companion(path) for path in paths)
    assert all(not _is_skill_companion(path) for path in _policy_reference_surfaces())
    assert any(path.endswith(".md") and not path.startswith("skills/") for path in paths)


def test_companion_classifier_handles_arbitrary_suffixes_and_paths() -> None:
    """Keep every skills notes/history companion out of policy and approval scans."""
    for path in (
        "skills/example.notes.md",
        "skills/example.notes-session-one.md",
        "skills/example.notesraw.md",
        "skills/example.history",
        "skills/example.history-v2.md",
    ):
        assert _is_skill_companion(path)

    for path in ("docs/example.notes-review.md", "docs/example.history-review.md"):
        assert not _is_skill_companion(path)


def test_active_mnemosyne_guidance_has_no_plugin_skill_path() -> None:
    """Keep Mnemosyne retrieval on its flat corpus, not a plugin skill path."""
    for path in _active_skill_paths():
        assert ".claude-plugin/skills/" not in _read(path).lower(), path


def test_policy_surface_discovery_uses_tracked_guidance_classifier(monkeypatch) -> None:
    """Include new active Markdown and exclude only explicit legal/history records."""
    tracked = [
        "README.md",
        "docs/example.history-review.md",
        "docs/example.notes-review.md",
        "docs/new-guide.md",
        "skills/example.notes-review.md",
        ".history/old-guide.md",
        "LICENSE",
    ]
    monkeypatch.setattr(sys.modules[__name__], "_tracked_paths", lambda: tracked)

    assert _policy_reference_surfaces() == [
        "README.md",
        "docs/example.history-review.md",
        "docs/example.notes-review.md",
        "docs/new-guide.md",
    ]


def test_repository_makes_no_asd_or_stemg_approval_claims() -> None:
    """Reject positive claims that ASD or STEMG approves this repository."""
    text = "\n".join(_read(path) for path in _active_review_paths() if not path.startswith("tests/"))
    text = text.lower()
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
