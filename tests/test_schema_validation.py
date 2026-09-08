#!/usr/bin/env python3
"""Compare runtime frontmatter validation with the published JSON Schema."""

import copy
import datetime
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from mnemosyne_skill_utils import find_skill_files, parse_frontmatter
from validate_plugins import validate_frontmatter

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "schemas" / "skill-frontmatter.schema.json").read_text())
SCHEMA_VALIDATOR = Draft202012Validator(SCHEMA)

VALID_METADATA: dict[str, Any] = {
    "name": "test-skill",
    "description": "Use this skill to test frontmatter.",
    "category": "tooling",
    "date": "2026-01-01",
    "version": "1.0.0",
}


def _schema_metadata(metadata: Any) -> Any:
    """Convert native YAML dates in a copy for JSON Schema validation."""
    normalized = copy.deepcopy(metadata)
    if isinstance(normalized, dict):
        date_value = normalized.get("date")
        if isinstance(date_value, datetime.date) and not isinstance(date_value, datetime.datetime):
            normalized["date"] = date_value.isoformat()
    return normalized


def _is_schema_valid(metadata: Any) -> bool:
    return not list(SCHEMA_VALIDATOR.iter_errors(_schema_metadata(metadata)))


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        ({}, True),
        ({"name": "a"}, True),
        ({"name": "a--b"}, True),
        ({"name": "-"}, False),
        ({"name": "a-"}, False),
        ({"name": 42}, False),
        ({"description": " "}, True),
        ({"description": ""}, False),
        ({"description": None}, False),
        ({"category": "training"}, True),
        ({"category": "banana"}, False),
        ({"category": ["tooling"]}, False),
        ({"date": "2026-01-01"}, True),
        ({"date": datetime.date(2026, 1, 1)}, True),
        ({"date": datetime.datetime(2026, 1, 1)}, False),
        ({"date": "2026-1-01"}, False),
        ({"version": "0.0.0"}, True),
        ({"version": "1.0.0-beta"}, False),
        ({"version": 1.0}, False),
        ({"user-invocable": True}, True),
        ({"user-invocable": "false"}, True),
        ({"user-invocable": "yes"}, False),
        ({"tags": []}, True),
        ({"tags": ["testing", "tooling"]}, True),
        ({"tags": ["testing", 42]}, False),
        ({"unknown-field": {"preserved": True}}, True),
    ],
    ids=lambda value: repr(value),
)
def test_runtime_matches_schema_for_field_values(change: dict[str, Any], expected: bool) -> None:
    """Runtime and schema checks accept the same explicit field values."""
    metadata = {**VALID_METADATA, **change}

    assert _is_schema_valid(metadata) is expected
    assert (validate_frontmatter(metadata, "test-skill.md") == []) is expected


@pytest.mark.parametrize("field", ["name", "description", "category", "date", "version"])
def test_runtime_matches_schema_for_missing_required_fields(field: str) -> None:
    """Runtime and schema checks reject each missing required field."""
    metadata = {key: value for key, value in VALID_METADATA.items() if key != field}

    assert not _is_schema_valid(metadata)
    assert validate_frontmatter(metadata, "test-skill.md")


@pytest.mark.parametrize("field", ["user-invocable", "tags"])
def test_runtime_matches_schema_when_optional_fields_are_omitted(field: str) -> None:
    """Runtime and schema checks permit each optional field to be absent."""
    metadata = {**VALID_METADATA, field: True if field == "user-invocable" else []}
    metadata.pop(field)

    assert _is_schema_valid(metadata)
    assert validate_frontmatter(metadata, "test-skill.md") == []


def test_schema_structure_has_the_frontmatter_contract() -> None:
    """The published schema contains the required fields and categories."""
    assert set(SCHEMA["required"]) == {"name", "description", "category", "date", "version"}
    assert set(SCHEMA["properties"]["category"]["enum"]) == {
        "architecture",
        "ci-cd",
        "debugging",
        "documentation",
        "evaluation",
        "optimization",
        "testing",
        "tooling",
        "training",
    }


def test_current_corpus_metadata_matches_schema_and_runtime() -> None:
    """Each current main skill has metadata that both validators accept."""
    failures: dict[Path, list[str]] = {}
    for path in find_skill_files(ROOT / "skills"):
        metadata, _, parse_errors = parse_frontmatter(path.read_text())
        errors = [*parse_errors, *validate_frontmatter(metadata, path.name)]
        errors.extend(error.message for error in SCHEMA_VALIDATOR.iter_errors(_schema_metadata(metadata)))
        if errors:
            failures[path] = errors

    assert failures == {}
