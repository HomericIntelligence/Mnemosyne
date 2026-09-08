#!/usr/bin/env python3
"""
Validate flat-format skill files (skills/*.md).

Checks:
- Maximum retrievable skill size (30,000 bytes)
- Required YAML frontmatter fields (name, description, category, date, version)
- Section presence (Overview, When to Use, Verified Workflow, Failed Attempts, Results & Parameters)
- Failed Attempts table structure
- Category validity
- Date format (YYYY-MM-DD)
- Quick Reference demotion check (should be ### not ##)
"""

import argparse
import datetime
import re
import sys
import textwrap
from pathlib import Path
from typing import Any, List, Optional

from mnemosyne_skill_utils import find_skill_files, parse_frontmatter  # noqa: F401  (re-exported for tests)

SKILLS_DIR = Path("skills")
MAX_SKILL_FILE_SIZE_BYTES = 30_000
VALID_CATEGORIES = {
    "training",
    "evaluation",
    "optimization",
    "debugging",
    "architecture",
    "tooling",
    "ci-cd",
    "testing",
    "documentation",
}

# Color codes for terminal output
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"


def find_plugins() -> List[Path]:
    """Find all flat skill files (skills/*.md, exclude *.notes*.md and *.history)."""
    return find_skill_files(SKILLS_DIR)


def validate_frontmatter(frontmatter: Any, filename: str) -> List[str]:
    """Validate required frontmatter fields."""
    errors: List[str] = []

    if not isinstance(frontmatter, dict):
        return ["Invalid frontmatter: expected a YAML mapping"]

    required = ["name", "description", "category", "date", "version"]
    for field in required:
        if field not in frontmatter:
            errors.append(f"Missing required field: {field}")
        elif not frontmatter[field]:
            errors.append(f"Empty required field: {field}")

    if "name" in frontmatter and frontmatter["name"]:
        name = frontmatter["name"]
        if not isinstance(name, str):
            errors.append("Invalid name: expected a string")
        elif not re.fullmatch(r"(?:[a-z0-9][a-z0-9-]*[a-z0-9]|[a-z0-9])", name):
            errors.append(f"Invalid name format: '{name}' must be kebab-case (lowercase, hyphens, no spaces)")

    if "description" in frontmatter and frontmatter["description"]:
        if not isinstance(frontmatter["description"], str):
            errors.append("Invalid description: expected a string")

    if "category" in frontmatter and frontmatter["category"]:
        category = frontmatter["category"]
        if not isinstance(category, str):
            errors.append("Invalid category: expected a string")
        elif category not in VALID_CATEGORIES:
            errors.append(f"Invalid category: {category}. Valid: {', '.join(sorted(VALID_CATEGORIES))}")

    if "date" in frontmatter and frontmatter["date"]:
        date_value = frontmatter["date"]
        if isinstance(date_value, datetime.date) and not isinstance(date_value, datetime.datetime):
            date_text = date_value.isoformat()
        elif isinstance(date_value, str):
            date_text = date_value
        else:
            date_text = None
        if date_text is None or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_text):
            errors.append(f"Invalid date format: {date_value} (expected YYYY-MM-DD)")

    if "version" in frontmatter and frontmatter["version"]:
        version = frontmatter["version"]
        if not isinstance(version, str):
            errors.append("Invalid version: expected a string")
        elif not re.fullmatch(r"\d+\.\d+\.\d+", version):
            errors.append(f"Invalid version format: {version} (expected X.Y.Z)")

    if "user-invocable" in frontmatter:
        user_invocable = frontmatter["user-invocable"]
        if not isinstance(user_invocable, bool) and (
            not isinstance(user_invocable, str) or user_invocable not in {"true", "false"}
        ):
            errors.append("Invalid user-invocable: expected a Boolean or 'true'/'false'")

    if "tags" in frontmatter:
        tags = frontmatter["tags"]
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            errors.append("Invalid tags: expected an array of strings")

    return errors


def validate_sections(body: str) -> List[str]:
    """Validate required markdown sections."""
    errors = []

    required_sections = [
        "## Overview",
        "## When to Use",
        "## Verified Workflow",
        "## Failed Attempts",
        "## Results & Parameters",
    ]

    for section in required_sections:
        if section not in body:
            errors.append(f"Missing required section: {section}")

    return errors


def validate_failed_attempts_table(body: str) -> List[str]:
    """Validate Failed Attempts table structure."""
    errors: List[str] = []
    required_columns = ["Attempt", "What Was Tried", "Why It Failed", "Lesson Learned"]

    # Find Failed Attempts section
    if "## Failed Attempts" not in body:
        return errors  # Already checked in validate_sections

    # Extract Failed Attempts content
    match = re.search(r"## Failed Attempts\s*\n(.*?)(?:\n## |\Z)", body, re.DOTALL)

    if not match:
        return errors

    section_content = match.group(1).strip()
    lines: List[str] = []
    fence_marker: Optional[str] = None
    for line in section_content.splitlines():
        stripped = line.lstrip()
        marker = stripped[:3]
        if marker in {"```", "~~~"}:
            if fence_marker is None:
                fence_marker = marker
            elif marker == fence_marker:
                fence_marker = None
            continue
        if fence_marker is None:
            lines.append(line)

    def split_row(line: str) -> List[str]:
        """Split a Markdown table row without splitting escaped pipes."""
        stripped = line.strip()
        cells: List[str] = []
        cell: List[str] = []
        slash_count = 0
        for character in stripped:
            if character == "|" and slash_count % 2 == 0:
                cells.append("".join(cell).strip())
                cell = []
            else:
                cell.append(character)
            slash_count = slash_count + 1 if character == "\\" else 0
        cells.append("".join(cell).strip())
        if stripped.startswith("|"):
            cells = cells[1:]
        if stripped.endswith("|"):
            cells = cells[:-1]
        return cells

    table_rows = [(index, split_row(line)) for index, line in enumerate(lines) if "|" in line]
    if not table_rows:
        return ["Failed Attempts section must contain a table"]

    header_index: Optional[int] = None
    header_cells: List[str] = []
    for index, cells in table_rows:
        if all(column in cells for column in required_columns):
            header_index = index
            header_cells = cells
            break

    if header_index is None:
        return ["Failed Attempts table missing required columns"]

    if header_index + 1 >= len(lines):
        return ["Failed Attempts table is incomplete (needs a separator and at least one data row)"]

    separator_cells = split_row(lines[header_index + 1])
    separator_pattern = re.compile(r"^:?-{3,}:?$")
    if len(separator_cells) != len(header_cells) or not all(
        separator_pattern.fullmatch(cell) for cell in separator_cells
    ):
        return ["Failed Attempts table has an invalid separator row"]

    if header_index + 2 >= len(lines):
        return ["Failed Attempts table is incomplete (needs at least one data row)"]

    data_cells = split_row(lines[header_index + 2])
    if len(data_cells) < len(header_cells) or not any(data_cells):
        return ["Failed Attempts table needs at least one nonempty data row"]

    return errors


def validate_quick_reference_heading(body: str) -> List[str]:
    """
    Validate that Quick Reference uses ### not ##.
    This was a common issue in old format.
    """
    errors = []

    # Look for ## Quick Reference (should be ### Quick Reference)
    if re.search(r"^## Quick Reference", body, re.MULTILINE):
        errors.append("Quick Reference should use ### (h3) not ## (h2)")

    return errors


def validate_plugin(filename: str) -> List[str]:
    """Validate a single skill file. Returns list of errors."""
    errors = []

    file_path = SKILLS_DIR / filename

    try:
        with open(file_path, "r") as f:
            content = f.read()
    except IOError as e:
        return [f"Cannot read file: {e}"]

    size_bytes = file_path.stat().st_size
    if size_bytes > MAX_SKILL_FILE_SIZE_BYTES:
        errors.append(
            f"Skill file {file_path} is {size_bytes:,} bytes; allowed maximum is {MAX_SKILL_FILE_SIZE_BYTES:,} bytes"
        )

    # Parse frontmatter
    frontmatter, body, parse_errors = parse_frontmatter(content)
    errors.extend(parse_errors)

    if parse_errors:
        return errors

    # Validate frontmatter fields
    errors.extend(validate_frontmatter(frontmatter, filename))

    # Validate sections
    errors.extend(validate_sections(body))

    # Validate Failed Attempts table
    errors.extend(validate_failed_attempts_table(body))

    # Validate Quick Reference heading
    errors.extend(validate_quick_reference_heading(body))

    return errors


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="validate_plugins.py",
        description="Validate flat-format skill files (skills/*.md).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            examples:
              # Validate all skill files in skills/
              python3 scripts/validate_plugins.py

              # Run from any directory (skills/ resolved relative to cwd)
              cd /path/to/Mnemosyne && python3 scripts/validate_plugins.py

              # Pipe through grep to show only failing files
              python3 scripts/validate_plugins.py 2>&1 | grep '^✗'

              # Use in CI — exits 1 if any errors are found
              python3 scripts/validate_plugins.py || exit 1
            """
        ),
    )
    return parser


def main():
    """Main validation entry point."""
    build_parser().parse_args()

    plugins = find_plugins()

    if not plugins:
        print(f"{RED}No skill files found in {SKILLS_DIR}{RESET}")
        sys.exit(1)

    print(f"Validating {len(plugins)} skill files...\n")

    total_errors = 0
    valid_files = 0

    for plugin_file in plugins:
        filename = plugin_file.name
        errors = validate_plugin(filename)

        if errors:
            total_errors += len(errors)
            print(f"{RED}✗{RESET} {filename}")
            for error in errors:
                print(f"    {RED}•{RESET} {error}")
        else:
            valid_files += 1
            print(f"{GREEN}✓{RESET} {filename}")

    # Summary
    print(f"\n{'=' * 60}")
    print("Validation Summary:")
    print(f"  {GREEN}Valid{RESET}: {valid_files}/{len(plugins)}")
    if total_errors > 0:
        print(f"  {RED}Errors{RESET}: {total_errors}")
    print(f"{'=' * 60}")

    if total_errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
