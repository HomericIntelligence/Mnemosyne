"""Test the skill frontmatter contract through real files and the CLI."""

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml
from mnemosyne_skill_utils import find_skill_files
from validate_plugins import validate_plugin

pytestmark = pytest.mark.nightly

ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = ROOT / "scripts" / "validate_plugins.py"

VALID_METADATA: dict[str, Any] = {
    "name": "test-skill",
    "description": "Use this skill to test valid frontmatter.",
    "category": "tooling",
    "date": "2026-01-01",
    "version": "1.0.0",
}

VALID_BODY = """\
# Test Skill

## Overview

| Field | Value |
| --- | --- |
| Objective | Test the validator. |

## When to Use

Use this skill for validator tests.

## Verified Workflow

### Quick Reference

Run the validator.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Invalid data | Used invalid data. | Validation failed. | Use valid data. |

## Results & Parameters

The validator accepts the file.
"""


def _write_skill(skills_dir: Path, filename: str, metadata: Any, body: str = VALID_BODY) -> Path:
    """Write one test skill and return its path."""
    skills_dir.mkdir(exist_ok=True)
    frontmatter = yaml.safe_dump(metadata, sort_keys=False).rstrip()
    path = skills_dir / filename
    path.write_text(f"---\n{frontmatter}\n---\n{body}")
    return path


def _run_validator(tmp_path: Path) -> subprocess.CompletedProcess[str]:
    """Run the validator against the test directory."""
    return subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )


def test_control_cli_passes(tmp_path: Path) -> None:
    """A valid file passes through the real CLI boundary."""
    _write_skill(tmp_path / "skills", "test-skill.md", VALID_METADATA)

    result = _run_validator(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Errors" not in result.stdout


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", "-"),
        ("name", "ends-"),
        ("name", 42),
        ("description", 42),
        ("description", None),
        ("category", ["tooling"]),
        ("category", None),
        ("date", "2026-1-01"),
        ("date", "2026-01-01T00:00:00"),
        ("date", 42),
        ("version", "banana"),
        ("version", "1.0"),
        ("version", 1.0),
        ("user-invocable", "yes"),
        ("user-invocable", 1),
        ("user-invocable", []),
        ("user-invocable", {}),
        ("tags", "testing"),
        ("tags", ["testing", 42]),
    ],
)
def test_invalid_field_fails_cli(tmp_path: Path, field: str, value: Any) -> None:
    """Each invalid field produces one field-specific CLI failure."""
    metadata = {**VALID_METADATA, field: value}
    filename = f"invalid-{field}.md"
    _write_skill(tmp_path / "skills", filename, metadata)

    result = _run_validator(tmp_path)
    output = result.stdout + result.stderr

    assert result.returncode == 1
    assert filename in output
    assert field in output.lower()
    assert "Traceback" not in output
    assert "Missing required section" not in output
    assert "Failed Attempts table" not in output


@pytest.mark.parametrize("field", ["name", "description", "category", "date", "version"])
def test_missing_required_field_fails_cli(tmp_path: Path, field: str) -> None:
    """The CLI rejects each missing required field."""
    metadata = {key: value for key, value in VALID_METADATA.items() if key != field}
    _write_skill(tmp_path / "skills", f"missing-{field}.md", metadata)

    result = _run_validator(tmp_path)
    output = result.stdout + result.stderr

    assert result.returncode == 1
    assert f"Missing required field: {field}" in output
    assert "Missing required section" not in output


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", "a"),
        ("name", "a--b"),
        ("description", " "),
        ("date", "2026-01-01"),
        ("user-invocable", True),
        ("user-invocable", "false"),
        ("tags", []),
        ("extra-field", {"preserved": True}),
    ],
)
def test_schema_boundary_values_pass_cli(tmp_path: Path, field: str, value: Any) -> None:
    """The CLI accepts values that are valid at schema boundaries."""
    _write_skill(tmp_path / "skills", "boundary.md", {**VALID_METADATA, field: value})

    result = _run_validator(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr


def test_bare_yaml_date_passes_cli(tmp_path: Path) -> None:
    """A native YAML date value passes the string-based schema contract."""
    skills = tmp_path / "skills"
    skills.mkdir()
    metadata = "\n".join(
        [
            "name: test-skill",
            "description: Use this skill to test a YAML date.",
            "category: tooling",
            "date: 2026-01-01",
            'version: "1.0.0"',
        ]
    )
    (skills / "bare-date.md").write_text(f"---\n{metadata}\n---\n{VALID_BODY}")

    result = _run_validator(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("metadata_text", ["", "{}"])
def test_empty_metadata_reports_required_fields(tmp_path: Path, metadata_text: str) -> None:
    """A parsed empty mapping reaches metadata validation."""
    skills = tmp_path / "skills"
    skills.mkdir()
    (skills / "empty.md").write_text(f"---\n{metadata_text}\n---\n{VALID_BODY}")

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    for field in VALID_METADATA:
        assert f"Missing required field: {field}" in result.stdout


@pytest.mark.parametrize("metadata", [["name"], "name", 42])
def test_non_mapping_metadata_fails_without_traceback(tmp_path: Path, metadata: Any) -> None:
    """A YAML sequence or scalar produces a diagnostic, not an exception."""
    _write_skill(tmp_path / "skills", "non-mapping.md", metadata)

    result = _run_validator(tmp_path)
    output = result.stdout + result.stderr

    assert result.returncode == 1
    assert "frontmatter" in output.lower()
    assert "mapping" in output.lower()
    assert "Traceback" not in output


def test_empty_metadata_reports_missing_fields_and_sections(tmp_path: Path) -> None:
    """An empty mapping does not bypass section validation."""
    skills = tmp_path / "skills"
    skills.mkdir()
    (skills / "empty.md").write_text("---\n{}\n---\n# Incomplete\n")

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "Missing required field: name" in result.stdout
    assert "Missing required section: ## Overview" in result.stdout


def test_cli_aggregates_valid_and_invalid_files(tmp_path: Path) -> None:
    """One invalid file makes a mixed directory fail."""
    skills = tmp_path / "skills"
    _write_skill(skills, "valid.md", VALID_METADATA)
    _write_skill(skills, "invalid.md", {**VALID_METADATA, "version": "banana"})

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert "valid.md" in result.stdout
    assert "invalid.md" in result.stdout
    assert "Invalid version" in result.stdout


def test_current_corpus_passes_runtime_validation() -> None:
    """All current main skill files pass the runtime validator."""
    failures = {
        path: errors
        for path in find_skill_files(ROOT / "skills")
        if (errors := validate_plugin(path.name))
    }

    assert failures == {}
