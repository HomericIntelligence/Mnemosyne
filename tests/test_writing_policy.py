"""Test writing-policy presence, scope, delegation, and protected content.

These tests do not determine natural-language conformance with ASD-STE100.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import stat
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
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
        r"^### Key Development Principles\n.*?(?=^### Athena Development Principles\n|\Z)",
        "3bd2cdf293366e577fb625fc1cf50f330d78c02e4090a1dbd6f0cda9abf7895c",
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

MIGRATION_FACTUAL_MARKERS = (
    "841/844 nested skills migrated",
    "930 skills successfully indexed",
    "550 valid skills",
    "380 skills with quality issues",
    "git revert 6b6eb31c d1d65f15  # Revert in order",
    "d1d65f15",
    "6b6eb31c",
)


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
        if path not in PROTECTED_PATHS and not path.startswith(".history/") and not _is_skill_companion(path)
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


def test_migration_status_preserves_factual_record() -> None:
    """Keep migration counts, findings, references, and rollback evidence."""
    migration_status = _read("MIGRATION_STATUS.md")

    for marker in MIGRATION_FACTUAL_MARKERS:
        assert marker in migration_status, f"MIGRATION_STATUS.md lost {marker!r}"

    assert "not a plugin marketplace" in migration_status.split("## Summary", 1)[0].lower()


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
    policy_links = _markdown_link_targets(policy)

    assert ASD_SITE_TARGETS & policy_links
    assert ASD_DOWNLOAD_TARGET in policy_links
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
        r"\bplugins/tooling/(?:[^/\s]+/)*mnemosyne/",
        r"(?:mnemosyne|projectmnemosyne)[^\n]{0,100}(?:marketplace\.json|plugin\.json|\.claude-plugin)",
        r"(?:marketplace\.json|plugin\.json|\.claude-plugin)[^\n]{0,100}(?:mnemosyne|projectmnemosyne)",
        r"(?:/advise|/learn).{0,80}projecthephaestus\s+(?:commands?|plugin|skills?)",
        r"projecthephaestus\s+(?:commands?|plugin|skills?).{0,80}(?:/advise|/learn)",
        r"\bprojecthephaestus\s+owns?\s+(?:the\s+)?(?:/advise|/learn)\b",
        r"(?:/advise|/learn)\s+(?:is|are)\s+owned\s+by\s+projecthephaestus\b",
    )


def _has_positive_attribution(text: str) -> bool:
    """Reject positive ASD or STEMG attribution and permit explicit denials."""
    positive_patterns = (
        r"\basd(?:-ste100)?\s+certification\b",
        r"\basd(?:-ste100)?\s+certified\b",
        r"\b(?:asd|stemg)\s+endorsement\b",
        r"\b(?:asd|stemg)\s+approval\b",
        r"\b(?:asd|stemg)\s+approv(?:e|es|ed)\b",
    )
    negative_pattern = re.compile(r"\b(?:not|no|without|never|does not|do not|doesn't|don't|isn't|aren't)\b")
    for sentence in re.split(r"(?<=[.!?])\s+|\n", text.lower()):
        matches = [re.search(pattern, sentence) for pattern in positive_patterns]
        for match in (item for item in matches if item is not None):
            if not negative_pattern.search(sentence[: match.start()]):
                return True
    return False


def _active_claim_scan_paths() -> list[str]:
    """Cover active skills, guidance, schema prose, and other active tracked text."""
    active_non_test = {path for path in _active_review_paths() if not path.startswith("tests/")}
    return sorted(set(_active_skill_paths()) | set(_policy_reference_surfaces()) | active_non_test)


def test_ownership_patterns_cover_reverse_forms_without_broad_matches() -> None:
    """Keep reverse marketplace and ProjectHephaestus ownership forms covered."""
    prohibited_examples = (
        "plugin marketplace (Mnemosyne)",
        "plugins/tooling/mnemosyne/",
        "ProjectHephaestus owns /advise",
        "ProjectHephaestus owns /learn",
        "/advise is owned by ProjectHephaestus",
        "/learn is owned by ProjectHephaestus",
    )
    for example in prohibited_examples:
        assert any(re.search(pattern, example.lower(), flags=re.DOTALL) for pattern in _prohibited_ownership_patterns())

    safe_examples = (
        "A plugin marketplace can provide generic skills.",
        "plugins/tooling/<plugin-name>/",
        "Mnemosyne is not a plugin marketplace.",
        "Mnemosyne is not a marketplace.",
        "Athena owns /advise and /learn; ProjectHephaestus provides shared utilities.",
    )
    for example in safe_examples:
        assert all(
            re.search(pattern, example.lower(), flags=re.DOTALL) is None for pattern in _prohibited_ownership_patterns()
        )


def test_protected_literals_are_unchanged() -> None:
    """Keep high-risk commands, paths, URLs, and configuration values exact."""
    for path, literals in PROTECTED_LITERAL_EXPECTATIONS.items():
        text = _read(path)
        for literal in literals:
            if literal.startswith("https://") and path.endswith(".md"):
                assert literal in _markdown_link_targets(text), f"{path}: missing protected link {literal!r}"
            else:
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
    assert not _has_positive_attribution(text)


def test_attribution_scan_covers_noun_and_past_tense_claims() -> None:
    """Cover certification and endorsement claims while allowing explicit denials."""
    positive_examples = (
        "ASD certification covers Mnemosyne.",
        "ASD certified Mnemosyne.",
        "STEMG endorsement appears in the project record.",
        "ASD approval covers Mnemosyne.",
        "ASD approved Mnemosyne.",
        "ASD approves Mnemosyne.",
        "STEMG approval covers Mnemosyne.",
        "STEMG approved Mnemosyne.",
    )
    for example in positive_examples:
        assert _has_positive_attribution(example)

    negative_examples = (
        "This project makes no ASD certification claim.",
        "ASD did not certify Mnemosyne.",
        "The repository has no STEMG endorsement.",
        "This project makes no ASD approval claim.",
        "ASD did not approve Mnemosyne.",
        "The repository has no STEMG approval.",
        "STEMG did not approve Mnemosyne.",
    )
    for example in negative_examples:
        assert not _has_positive_attribution(example)


def test_repository_does_not_vendor_asd_ste100_assets() -> None:
    """Reject tracked standard PDFs, dictionaries, and logos."""
    paths = _tracked_paths()
    forbidden = [
        path
        for path in paths
        if re.search(r"(?:asd|ste|simplified|technical).*(?:pdf|dict|logo)|(?:pdf|dict|logo).*(?:asd|ste)", path, re.I)
    ]
    assert forbidden == []


AGENT_CONTRACT_TAG = "agent-contract-v1.0.0"
AGENT_CONTRACT_BLOCK_START = f"<!-- BEGIN ATHENA DEVELOPMENT PRINCIPLES: {AGENT_CONTRACT_TAG} -->"
AGENT_CONTRACT_BLOCK_END = "<!-- END ATHENA DEVELOPMENT PRINCIPLES -->"
AGENT_CONTRACT_DETAIL_PREFIX = (
    f"https://github.com/HomericIntelligence/Athena/blob/{AGENT_CONTRACT_TAG}/docs/principles/details/"
)
EXPECTED_AGENT_CONTRACT_IDENTIFIERS = tuple(f"P{number:03d}" for number in range(1, 92))
ROOT_FILE_LIMIT = 256 * 1024
ROOT_CLAUDE_POINTER = b"@AGENTS.md\n"
ATHENA_CONTRACT_RENDERER = REPO_ROOT / "scripts" / "render_athena_agent_contract.py"
EXPECTED_GENERATED_BLOCK_SHA256 = "54705687c9c8d7401127622340c9989ce2579c1f6340caac79ab08d2410ad0be"
AGENT_CONTRACT_ROW_PATTERN = re.compile(
    r"^- \[(P\d{3}) — ([^[]+?)\]"
    r"\((https://github\.com/HomericIntelligence/Athena/blob/"
    rf"{re.escape(AGENT_CONTRACT_TAG)}/docs/principles/details/(p\d{{3}}-[a-z0-9-]+\.md))\)"
    r" — (.+)$"
)


def _read_bounded_regular_file(
    root: Path,
    relative_path: str,
    maximum_bytes: int = ROOT_FILE_LIMIT,
) -> tuple[bytes | None, list[str]]:
    path = root / relative_path

    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return None, [f"{relative_path} is missing"]
    except OSError as error:
        return None, [f"{relative_path} is unreadable: {error}"]

    if stat.S_ISLNK(metadata.st_mode):
        return None, [f"{relative_path} must be a regular file, not a symbolic link"]
    if not stat.S_ISREG(metadata.st_mode):
        return None, [f"{relative_path} must be a regular file"]
    if metadata.st_size > maximum_bytes:
        return None, [f"{relative_path} exceeds {maximum_bytes} bytes"]

    try:
        data = path.read_bytes()
    except OSError as error:
        return None, [f"{relative_path} is unreadable: {error}"]

    if len(data) > maximum_bytes:
        return None, [f"{relative_path} exceeds {maximum_bytes} bytes"]
    return data, []


def _read_bounded_regular_utf8(
    root: Path,
    relative_path: str,
    maximum_bytes: int = ROOT_FILE_LIMIT,
) -> tuple[str | None, list[str]]:
    data, errors = _read_bounded_regular_file(root, relative_path, maximum_bytes)
    if errors:
        return None, errors

    assert data is not None
    try:
        return data.decode("utf-8"), []
    except UnicodeDecodeError as error:
        return None, [f"{relative_path} must be UTF-8: {error}"]


def _extract_generated_block(text: str) -> tuple[str | None, list[str]]:
    start_count = text.count(AGENT_CONTRACT_BLOCK_START)
    end_count = text.count(AGENT_CONTRACT_BLOCK_END)
    errors: list[str] = []

    if start_count != 1:
        errors.append(f"AGENTS.md must contain exactly one generated start marker, found {start_count}")
    if end_count != 1:
        errors.append(f"AGENTS.md must contain exactly one generated end marker, found {end_count}")
    if errors:
        return None, errors

    start_index = text.index(AGENT_CONTRACT_BLOCK_START)
    end_index = text.index(AGENT_CONTRACT_BLOCK_END)
    block_start = start_index + len(AGENT_CONTRACT_BLOCK_START) + 1
    block_end = end_index - 1

    if text[start_index + len(AGENT_CONTRACT_BLOCK_START)] != "\n":
        return None, ["AGENTS.md generated start marker must stand alone on its own line"]
    if text[end_index - 1] != "\n":
        return None, ["AGENTS.md generated end marker must stand alone on its own line"]
    if block_start > block_end:
        return None, ["AGENTS.md generated block markers are out of order"]

    return text[block_start:block_end], []


def _validate_generated_block(root: Path) -> list[str]:
    text, errors = _read_bounded_regular_utf8(root, "AGENTS.md")
    if errors:
        return errors
    assert text is not None

    block, block_errors = _extract_generated_block(text)
    errors.extend(block_errors)
    if block is None:
        return errors

    marked_block = f"{AGENT_CONTRACT_BLOCK_START}\n{block}\n{AGENT_CONTRACT_BLOCK_END}"
    actual_digest = hashlib.sha256(marked_block.encode("utf-8")).hexdigest()
    if actual_digest != EXPECTED_GENERATED_BLOCK_SHA256:
        errors.append("AGENTS.md generated block bytes do not match the pinned Athena release digest")

    rows = block.splitlines()
    if len(rows) != len(EXPECTED_AGENT_CONTRACT_IDENTIFIERS):
        errors.append(f"AGENTS.md must contain exactly {len(EXPECTED_AGENT_CONTRACT_IDENTIFIERS)} generated rows")

    identifiers: list[str] = []
    for index, row in enumerate(rows, start=1):
        match = AGENT_CONTRACT_ROW_PATTERN.fullmatch(row)
        if match is None:
            errors.append(f"AGENTS.md row {index} does not match the released contract format")
            continue

        identifier, name, detail_url, detail_path, description = match.groups()
        expected_identifier = f"P{index:03d}"
        identifiers.append(identifier)

        if identifier != expected_identifier:
            errors.append(f"AGENTS.md row {index} must use identifier {expected_identifier}, not {identifier}")

        if detail_url != f"{AGENT_CONTRACT_DETAIL_PREFIX}{detail_path}":
            errors.append(f"AGENTS.md row {index} must use the tagged Athena detail link for {identifier}")

        expected_detail_path = f"p{index:03d}-"
        if not detail_path.startswith(expected_detail_path):
            errors.append(
                f"AGENTS.md row {index} must use a tagged detail path that starts with {expected_detail_path}"
            )

        if not name or not description:
            errors.append(f"AGENTS.md row {index} must keep the released principle text")

    if identifiers != list(EXPECTED_AGENT_CONTRACT_IDENTIFIERS):
        errors.append("AGENTS.md generated identifiers must be exactly P001 through P091 in order")

    return errors


def _validate_root_claude(root: Path) -> list[str]:
    data, errors = _read_bounded_regular_file(root, "CLAUDE.md", ROOT_FILE_LIMIT)
    if errors:
        return errors

    assert data is not None
    if data != ROOT_CLAUDE_POINTER:
        return ["CLAUDE.md must contain the exact `@AGENTS.md\\n` pointer bytes"]
    return []


def _validate_root_contract(root: Path) -> list[str]:
    errors = _validate_generated_block(root)
    errors.extend(_validate_root_claude(root))
    return errors


def _copy_root_contract_fixture(tmp_path: Path) -> Path:
    for filename in ("AGENTS.md", "CLAUDE.md"):
        shutil.copy2(REPO_ROOT / filename, tmp_path / filename)
    return tmp_path


def _extract_block_text(text: str) -> str:
    start_index = text.index(AGENT_CONTRACT_BLOCK_START) + len(AGENT_CONTRACT_BLOCK_START) + 1
    end_index = text.index(AGENT_CONTRACT_BLOCK_END) - 1
    return text[start_index:end_index]


def _mutate_agents_fixture(tmp_path: Path, mutation: str) -> None:
    agents_path = tmp_path / "AGENTS.md"
    text = agents_path.read_text(encoding="utf-8")

    if mutation == "missing":
        agents_path.unlink()
        return
    if mutation == "duplicate-block":
        block = _extract_block_text(text)
        agents_path.write_text(
            text + "\n" + AGENT_CONTRACT_BLOCK_START + "\n" + block + "\n" + AGENT_CONTRACT_BLOCK_END + "\n",
            encoding="utf-8",
        )
        return
    if mutation == "reordered":
        block_lines = _extract_block_text(text).splitlines()
        block_lines[0], block_lines[1] = block_lines[1], block_lines[0]
        agents_path.write_text(
            text[: text.index(AGENT_CONTRACT_BLOCK_START)]
            + AGENT_CONTRACT_BLOCK_START
            + "\n"
            + "\n".join(block_lines)
            + "\n"
            + AGENT_CONTRACT_BLOCK_END
            + text[text.index(AGENT_CONTRACT_BLOCK_END) + len(AGENT_CONTRACT_BLOCK_END) :],
            encoding="utf-8",
        )
        return
    if mutation == "renamed":
        agents_path.write_text(text.replace("P001 — KISS", "P001 — KISSX", 1), encoding="utf-8")
        return
    if mutation == "reworded":
        original = (
            "Select the design with minimum complexity that obeys all requirements that evidence shows are necessary."
        )
        replacement = "Select the design with minimum complexity that obeys the requirement."
        agents_path.write_text(
            text.replace(original, replacement, 1),
            encoding="utf-8",
        )
        return
    if mutation == "relinked":
        agents_path.write_text(
            text.replace(
                "https://github.com/HomericIntelligence/Athena/blob/agent-contract-v1.0.0/docs/principles/details/p001-kiss.md",
                "https://github.com/HomericIntelligence/Athena/blob/main/docs/principles/details/p001-kiss.md",
                1,
            ),
            encoding="utf-8",
        )
        return
    if mutation == "extra-row":
        block = _extract_block_text(text)
        extra_row = (
            "- [P092 — Extra Principle](https://github.com/HomericIntelligence/Athena/blob/"
            "agent-contract-v1.0.0/docs/principles/details/p092-extra-principle.md) — Extra rule."
        )
        agents_path.write_text(
            text[: text.index(AGENT_CONTRACT_BLOCK_START)]
            + AGENT_CONTRACT_BLOCK_START
            + "\n"
            + block
            + "\n"
            + extra_row
            + "\n"
            + AGENT_CONTRACT_BLOCK_END
            + text[text.index(AGENT_CONTRACT_BLOCK_END) + len(AGENT_CONTRACT_BLOCK_END) :],
            encoding="utf-8",
        )
        return
    if mutation == "symlink":
        agents_path.unlink()
        agents_path.symlink_to(REPO_ROOT / "AGENTS.md")
        return
    if mutation == "oversized":
        agents_path.write_bytes(b"x" * (ROOT_FILE_LIMIT + 1))
        return
    if mutation == "malformed":
        agents_path.write_bytes(b"\xff\xfe\xfd")
        return

    raise AssertionError(f"unknown AGENTS mutation: {mutation}")


def _mutate_claude_fixture(tmp_path: Path, mutation: str) -> None:
    claude_path = tmp_path / "CLAUDE.md"

    if mutation == "missing":
        claude_path.unlink()
        return
    if mutation == "no-lf":
        claude_path.write_bytes(ROOT_CLAUDE_POINTER[:-1])
        return
    if mutation == "crlf":
        claude_path.write_bytes(b"@AGENTS.md\r\n")
        return
    if mutation == "bom":
        claude_path.write_bytes(b"\xef\xbb\xbf" + ROOT_CLAUDE_POINTER)
        return
    if mutation == "leading-data":
        claude_path.write_bytes(b"prefix\n" + ROOT_CLAUDE_POINTER)
        return
    if mutation == "trailing-data":
        claude_path.write_bytes(b"@AGENTS.md\nsuffix\n")
        return
    if mutation == "symlink":
        claude_path.unlink()
        claude_path.symlink_to(REPO_ROOT / "CLAUDE.md")
        return

    raise AssertionError(f"unknown CLAUDE mutation: {mutation}")


def test_root_agents_generated_block_matches_athena_release() -> None:
    errors = _validate_generated_block(REPO_ROOT)

    assert errors == []


def test_root_claude_is_exact_pointer_bytes() -> None:
    data, errors = _read_bounded_regular_file(REPO_ROOT, "CLAUDE.md", len(ROOT_CLAUDE_POINTER))

    assert errors == []
    assert data == ROOT_CLAUDE_POINTER


def test_legacy_claude_guidance_is_preserved() -> None:
    agents = _read("AGENTS.md")

    assert "This file is the sole authoritative agent contract for Mnemosyne." in agents
    assert "Claude Code" in agents
    assert "other agents must follow this contract." in agents


@pytest.mark.parametrize(
    ("mutation", "expected_fragment"),
    [
        pytest.param("missing", "AGENTS.md is missing", id="missing"),
        pytest.param("duplicate-block", "exactly one generated start marker", id="duplicate-block"),
        pytest.param("reordered", "row 1 must use identifier P001", id="reordered"),
        pytest.param("renamed", "generated block bytes do not match", id="renamed"),
        pytest.param("reworded", "generated block bytes do not match", id="reworded"),
        pytest.param("relinked", "generated block bytes do not match", id="relinked"),
        pytest.param("extra-row", "exactly 91 generated rows", id="extra-row"),
        pytest.param("symlink", "must be a regular file, not a symbolic link", id="symlink"),
        pytest.param("oversized", "exceeds 262144 bytes", id="oversized"),
        pytest.param("malformed", "must be UTF-8", id="malformed"),
    ],
)
def test_generated_block_contract_rejects_fixture_mutations(
    mutation: str,
    expected_fragment: str,
    tmp_path: Path,
) -> None:
    _copy_root_contract_fixture(tmp_path)
    _mutate_agents_fixture(tmp_path, mutation)

    errors = _validate_generated_block(tmp_path)

    assert expected_fragment in "\n".join(errors)


@pytest.mark.parametrize(
    ("mutation", "expected_fragment"),
    [
        pytest.param("missing", "CLAUDE.md is missing", id="missing"),
        pytest.param("no-lf", "CLAUDE.md must contain the exact", id="no-lf"),
        pytest.param("crlf", "CLAUDE.md must contain the exact", id="crlf"),
        pytest.param("bom", "CLAUDE.md must contain the exact", id="bom"),
        pytest.param("leading-data", "CLAUDE.md must contain the exact", id="leading-data"),
        pytest.param("trailing-data", "CLAUDE.md must contain the exact", id="trailing-data"),
        pytest.param("symlink", "must be a regular file, not a symbolic link", id="symlink"),
    ],
)
def test_claude_pointer_contract_rejects_fixture_mutations(
    mutation: str,
    expected_fragment: str,
    tmp_path: Path,
) -> None:
    _copy_root_contract_fixture(tmp_path)
    _mutate_claude_fixture(tmp_path, mutation)

    errors = _validate_root_claude(tmp_path)

    assert expected_fragment in "\n".join(errors)


@pytest.fixture
def athena_contract_root() -> Path:
    source = os.environ.get("ATHENA_AGENT_CONTRACT_ROOT")
    if not source:
        pytest.skip("Set ATHENA_AGENT_CONTRACT_ROOT to the Athena agent-contract-v1.0.0 source directory.")
    return Path(source)


def _run_regeneration(root: Path, provider: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts/regenerate_agent_contract.py"),
            "--root",
            str(root),
            "--athena-root",
            str(provider),
            *arguments,
        ],
        capture_output=True,
        check=False,
        timeout=30,
    )


def test_athena_regeneration_produces_no_diff(athena_contract_root: Path, tmp_path: Path) -> None:
    _copy_root_contract_fixture(tmp_path)
    expected = (tmp_path / "AGENTS.md").read_bytes()

    for _ in range(2):
        result = _run_regeneration(tmp_path, athena_contract_root)
        assert result.returncode == 0, result.stderr.decode()
        assert result.stdout == expected
        (tmp_path / "AGENTS.md").write_bytes(result.stdout)

    result = _run_regeneration(tmp_path, athena_contract_root, "--check")
    assert result.returncode == 0, result.stderr.decode()
    assert (tmp_path / "AGENTS.md").read_bytes() == expected
    assert (tmp_path / "CLAUDE.md").read_bytes() == ROOT_CLAUDE_POINTER


def test_athena_regeneration_repairs_drift_without_changing_local_guidance(
    athena_contract_root: Path, tmp_path: Path
) -> None:
    _copy_root_contract_fixture(tmp_path)
    agents = tmp_path / "AGENTS.md"
    expected = b"Local guidance before.\n\n" + agents.read_bytes() + b"\nLocal guidance after.\n"
    agents.write_bytes(expected)
    _mutate_agents_fixture(tmp_path, "renamed")
    changed = agents.read_bytes()

    check = _run_regeneration(tmp_path, athena_contract_root, "--check")
    assert check.returncode == 1
    assert b"differs" in check.stderr
    result = _run_regeneration(tmp_path, athena_contract_root)
    assert result.returncode == 0, result.stderr.decode()
    assert result.stdout == expected
    assert agents.read_bytes() == changed


@pytest.mark.parametrize("relative_path", ["scripts/policies/agent_contract.py", "docs/principles/README.md"])
def test_athena_regeneration_rejects_changed_provider(
    relative_path: str, athena_contract_root: Path, tmp_path: Path
) -> None:
    provider = tmp_path / "provider"
    for filename in ("scripts/policies/agent_contract.py", "docs/principles/README.md"):
        target = provider / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(athena_contract_root / filename, target)
    with (provider / relative_path).open("ab") as stream:
        stream.write(b"\n# Changed release input.\n")

    result = _run_regeneration(REPO_ROOT, provider)
    assert result.returncode == 1
    assert relative_path.encode() in result.stderr
    assert b"SHA-256" in result.stderr
    assert result.stdout == b""


def test_athena_regeneration_requires_provider_files(tmp_path: Path) -> None:
    result = _run_regeneration(REPO_ROOT, tmp_path)
    assert result.returncode == 1
    assert b"agent_contract.py" in result.stderr
    assert result.stdout == b""


def test_athena_renderer_requires_explicit_provider() -> None:
    result = subprocess.run(
        [sys.executable, str(ATHENA_CONTRACT_RENDERER)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
    )
    assert result.returncode == 2
    assert b"--catalog-root" in result.stderr
    assert result.stdout == b""
