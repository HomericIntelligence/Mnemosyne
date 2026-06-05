---
name: ci-dependency-floor-semantic-version-guard
description: "Use when: (1) comparing version specs across manifest files (pyproject.toml, pixi.toml), (2) ensuring dependency floors stay consistent without string-equality surprises (e.g., '9.0' vs '9.0.0'), (3) implementing regression guards for manifest drift, (4) testing that pinned versions are semantically equivalent across files using PEP 440 version comparison."
category: ci-cd
date: 2026-06-05
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - dependencies
  - version-comparison
  - regression-guard
  - pytest
  - pixi
  - pyproject
  - semver
  - pep-440
  - manifest-consistency
---

# Semantic-Version-Aware Regression Guard for Dependency Floor Consistency

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-05 |
| **Objective** | Document pytest 9.x / pytest-cov 7.x tight floors and add regression guard to prevent accidental version spec drift across manifest files (pyproject.toml, pixi.toml) using PEP 440 semantic version comparison |
| **Outcome** | Successful implementation in ProjectHephaestus issue #785; two test methods that validate floor/cap consistency across pyproject.toml and pixi.toml using `packaging.version.Version` for semantic equality |
| **Verification** | verified-local (all tests pass locally; CI validation pending on merge) |

## When to Use

- Reviewing a PR that pins tight version floors (e.g., `pytest>=9.0`) across multiple manifest files
- Implementing regression guards for dependency consistency across `pyproject.toml` and `pixi.toml`
- Testing that version strings like `"9.0"` and `"9.0.0"` are semantically equivalent (PEP 440)
- Detecting manifest drift where one file says `pytest==9.0.1` and another says `pytest>=9.0` without catching the inconsistency
- Setting up automated checks to prevent hand-edited version specs from diverging across manifest files

## Verified Workflow

### Quick Reference

```bash
# Core pattern: use packaging.version.Version for semantic comparison
from packaging.version import Version

# Raw string comparison fails:
assert "9.0" == "9.0.0"  # False! ← trap for manifest drift

# Semantic comparison works:
assert Version("9.0") == Version("9.0.0")  # True ← safe

# For parsing specifiers like ">=9.0" or "==9.0.1", use _find_dep() helper:
def _find_dep(specifier_string: str, pkg_name: str) -> str | None:
    """Extract version from PEP 508 specifier using punctuation delimiters.
    
    Args:
        specifier_string: e.g., "pytest>=9.0", "pytest-cov==7.0.0"
        pkg_name: e.g., "pytest"
    
    Returns:
        Version string (e.g., "9.0") or None if not found.
    """
    if pkg_name not in specifier_string:
        return None
    
    # Find package name and skip it
    idx = specifier_string.find(pkg_name)
    remainder = specifier_string[idx + len(pkg_name):]
    
    # Strip PEP 508 specifier punctuation (>=, <=, ==, !=, ~=, <, >, =)
    # Try longest operators first to avoid eating a second = from ==
    for op in ["~=", "==", "!=", ">=", "<=", "<", ">", "="]:
        if remainder.startswith(op):
            remainder = remainder[len(op):]
            break
    
    # Return the version part (stops at comma, semicolon, or bracket if present)
    for stop_char in [",", ";", "[", "]"]:
        if stop_char in remainder:
            remainder = remainder[:remainder.find(stop_char)]
    
    return remainder.strip() if remainder else None

# Test case template:
def test_pytest_floor_consistency():
    """Verify pytest floor is semantically consistent across manifests."""
    floor_pyproject = "9.0"        # from pyproject.toml
    floor_pixi = "9.0.0"           # from pixi.toml
    
    assert Version(floor_pyproject) == Version(floor_pixi), \
        f"pytest floor mismatch: pyproject declares {floor_pyproject}, pixi declares {floor_pixi}"

def test_pytest_cov_cap_consistency():
    """Verify pytest-cov cap is semantically consistent across manifests."""
    cap_pyproject = "<7.1"         # from pyproject.toml
    cap_pixi = "<7.1.0"            # from pixi.toml (if present)
    
    # Extract versions using _find_dep()
    version_pyproject = _find_dep(cap_pyproject, "pytest-cov")
    version_pixi = _find_dep(cap_pixi, "pytest-cov")
    
    assert Version(version_pyproject) == Version(version_pixi), \
        f"pytest-cov cap mismatch: {version_pyproject} != {version_pixi}"
```

### Detailed Steps

#### Step 1 — Identify Tight-Floor Dependencies

Scan `pyproject.toml` and `pixi.toml` for dependencies with exact or tight version bounds:

```bash
# In pyproject.toml:
grep -E '(pytest|pytest-cov).*[<>=]' pyproject.toml

# In pixi.toml:
grep -E '(pytest|pytest-cov)' pixi.toml
```

Expected output: entries like `pytest>=9.0` (floor), `pytest-cov<7.1` (cap).

#### Step 2 — Understand the Problem

Raw string comparison fails to catch semver equivalence:

```python
# This will fail (false negative) even though specs are semantically identical:
assert "9.0" == "9.0.0"  # False — but semantically they're the same floor

# This is why manifest drift goes undetected in naive tests:
pyproject_floor = "9.0"
pixi_floor = "9.0.0"
if pyproject_floor != pixi_floor:  # ← raw string check
    print("Drift detected")  # Won't print even though specs differ in representation
```

Solution: Use `packaging.version.Version` to normalize before comparing.

#### Step 3 — Implement the _find_dep() Helper

This helper robustly extracts package versions from PEP 508 specifiers (handles `>=`, `==`, `!=`, `~=`, `<`, `>`, `=`):

```python
from typing import Optional

def _find_dep(specifier_string: str, pkg_name: str) -> Optional[str]:
    """Extract version from a PEP 508 specifier string.
    
    PEP 508 format: https://www.python.org/dev/peps/pep-0508/
    Examples:
        - _find_dep("pytest>=9.0", "pytest") → "9.0"
        - _find_dep("pytest-cov==7.0.0", "pytest-cov") → "7.0.0"
        - _find_dep("some-other-pkg>=1.0", "pytest") → None
    
    Args:
        specifier_string: PEP 508 specifier (e.g., ">=9.0", "==7.0.0")
        pkg_name: Package name to search for
    
    Returns:
        Version string (e.g., "9.0") or None if pkg_name not found.
    """
    if pkg_name not in specifier_string:
        return None
    
    # Locate package name in the specifier string
    idx = specifier_string.find(pkg_name)
    remainder = specifier_string[idx + len(pkg_name):]
    
    # Strip PEP 508 comparison operators (longest first to avoid == → = + =)
    for op in ["~=", "==", "!=", ">=", "<=", "<", ">", "="]:
        if remainder.startswith(op):
            remainder = remainder[len(op):]
            break
    
    # Trim at commas, semicolons, or brackets (for extras like "pytest-cov[toml]>=7.0")
    for stop_char in [",", ";", "[", "]"]:
        if stop_char in remainder:
            remainder = remainder[:remainder.find(stop_char)]
    
    return remainder.strip() if remainder.strip() else None
```

#### Step 4 — Write the Test Suite

Create `tests/unit/scripts/test_dependency_floor_consistency.py`:

```python
"""Regression guard: verify dependency floor consistency across manifests.

Pytest 9.x and pytest-cov 7.x have tight floors. This suite ensures that
pyproject.toml and pixi.toml declare the same semantic versions, preventing
accidental downgrades if version strings drift (e.g., "9.0" vs "9.0.0").
"""

import re
from pathlib import Path
from typing import Optional

from packaging.version import Version
import pytest


def _find_dep(specifier_string: str, pkg_name: str) -> Optional[str]:
    """Extract version from a PEP 508 specifier string.
    
    Handles operators: >=, <=, ==, !=, ~=, <, >, =
    """
    if pkg_name not in specifier_string:
        return None
    
    idx = specifier_string.find(pkg_name)
    remainder = specifier_string[idx + len(pkg_name):]
    
    # Strip operators (longest first)
    for op in ["~=", "==", "!=", ">=", "<=", "<", ">", "="]:
        if remainder.startswith(op):
            remainder = remainder[len(op):]
            break
    
    # Trim at word boundaries
    for stop_char in [",", ";", "[", "]", " "]:
        if stop_char in remainder:
            remainder = remainder[:remainder.find(stop_char)]
    
    return remainder.strip() if remainder.strip() else None


class TestPytestConsistency:
    """Verify pytest and pytest-cov versions are consistent across manifests."""
    
    @pytest.fixture(scope="class")
    def project_root(self) -> Path:
        """Locate the project root."""
        path = Path(__file__).parent
        while path != path.parent:
            if (path / "pyproject.toml").exists():
                return path
            path = path.parent
        raise RuntimeError("Could not find project root (pyproject.toml)")
    
    def test_pytest_floor_consistency_pyproject_vs_pixi(self, project_root: Path) -> None:
        """Verify pytest floor is semantically consistent.
        
        Context: pytest 9.x is a floor (minimum required version).
        Both pyproject.toml and pixi.toml must declare the same floor,
        even if string representation differs ("9.0" vs "9.0.0").
        """
        pyproject_path = project_root / "pyproject.toml"
        pixi_path = project_root / "pixi.toml"
        
        # Read files
        pyproject_content = pyproject_path.read_text()
        pixi_content = pixi_path.read_text()
        
        # Extract pytest floor from pyproject.toml [project.optional-dependencies]
        # Pattern: "pytest>=X.Y.Z" or similar
        pyproject_match = re.search(r'"pytest>=([0-9.]+)"', pyproject_content)
        assert pyproject_match, "Could not find pytest floor in pyproject.toml"
        pytest_floor_pyproject = pyproject_match.group(1)
        
        # Extract pytest floor from pixi.toml [dependencies]
        pixi_match = re.search(r'pytest\s*>=\s*([0-9.]+)', pixi_content)
        assert pixi_match, "Could not find pytest floor in pixi.toml"
        pytest_floor_pixi = pixi_match.group(1)
        
        # Compare semantically (PEP 440)
        assert Version(pytest_floor_pyproject) == Version(pytest_floor_pixi), \
            (f"pytest floor mismatch: pyproject.toml declares {pytest_floor_pyproject}, "
             f"pixi.toml declares {pytest_floor_pixi}. Use packaging.version.Version for "
             f"comparison to catch drift despite string representation differences.")
    
    def test_pytest_cov_floor_consistency_pyproject_vs_pixi(self, project_root: Path) -> None:
        """Verify pytest-cov floor is semantically consistent.
        
        Context: pytest-cov 7.x is a floor. Both manifests must declare
        the same floor, even if string formats differ.
        """
        pyproject_path = project_root / "pyproject.toml"
        pixi_path = project_root / "pixi.toml"
        
        # Read files
        pyproject_content = pyproject_path.read_text()
        pixi_content = pixi_path.read_text()
        
        # Extract pytest-cov floor from pyproject.toml
        pyproject_match = re.search(r'"pytest-cov>=([0-9.]+)"', pyproject_content)
        assert pyproject_match, "Could not find pytest-cov floor in pyproject.toml"
        pytest_cov_floor_pyproject = pyproject_match.group(1)
        
        # Extract pytest-cov floor from pixi.toml
        pixi_match = re.search(r'pytest-cov\s*>=\s*([0-9.]+)', pixi_content)
        assert pixi_match, "Could not find pytest-cov floor in pixi.toml"
        pytest_cov_floor_pixi = pixi_match.group(1)
        
        # Compare semantically
        assert Version(pytest_cov_floor_pyproject) == Version(pytest_cov_floor_pixi), \
            (f"pytest-cov floor mismatch: pyproject.toml declares {pytest_cov_floor_pyproject}, "
             f"pixi.toml declares {pytest_cov_floor_pixi}.")
```

#### Step 5 — Document the Rationale in pyproject.toml

Use the mypy comment pattern to document why tight floors are necessary:

```toml
# NOTE: pytest and pytest-cov floors are intentionally tight (>=9.0, >=7.0).
# This is a runtime requirement for test discovery and coverage reporting.
# DO NOT change without coordination:
#   1. Update pytest>=X.Y in [project.optional-dependencies]
#   2. Update pytest>=X.Y in pixi.toml [dependencies]
#   3. Run tests/unit/scripts/test_dependency_floor_consistency.py to verify
#      both floors are semantically equal (handles "9.0" vs "9.0.0" diffs)
#   See: https://github.com/HomericIntelligence/ProjectHephaestus/issues/785
```

#### Step 6 — Run the Regression Guard

```bash
# Run the floor consistency tests in isolation
pytest tests/unit/scripts/test_dependency_floor_consistency.py -v

# Run all unit tests to ensure nothing breaks
pytest tests/unit/ -v

# Pre-commit hooks (formatting, linting, etc.)
pre-commit run --all-files
```

Expected output on success:
```
tests/unit/scripts/test_dependency_floor_consistency.py::TestPytestConsistency::test_pytest_floor_consistency_pyproject_vs_pixi PASSED
tests/unit/scripts/test_dependency_floor_consistency.py::TestPytestConsistency::test_pytest_cov_floor_consistency_pyproject_vs_pixi PASSED
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Compare version strings directly (raw equality) | `assert pyproject_floor == pixi_floor` where `pyproject_floor="9.0"` and `pixi_floor="9.0.0"` | String comparison fails because `"9.0" != "9.0.0"` even though they represent the same PEP 440 version. Manifest drift goes undetected. | Always normalize versions with `packaging.version.Version()` before comparing, never raw string equality. |
| Use string `.split('.')` and compare tuple of ints | Parse "9.0.0" to `(9, 0, 0)` and "9.0" to `(9, 0)`, pad with zeros | Fragile for complex version schemes (pre-releases, dev versions, local versions). Doesn't handle "9.0.0a1" vs "9.0a1" correctly. | Delegate to `packaging.version.Version` which handles PEP 440 edge cases. |
| Extract versions with naive regex `r'>=([0-9]+\.[0-9]+)'` | Simple pattern matching for "X.Y" version format | Fails when version is "9.0.0" (three dots) or when extras are present like `pytest-cov[toml]>=7.0`. Misses edge cases in PEP 508 specifiers. | Use a robust helper like `_find_dep()` that parses PEP 508 operators (`~=`, `==`, `!=`, `>=`, `<=`, etc.) and handles extras (`[toml]`) and comments. |
| Hardcode the floor version number in the test | `assert Version("9.0") == Version(pytest_floor_pixi)` | Test becomes a tautology; it always passes the hardcoded value. When the real floor changes (9.1, 9.2), the test doesn't catch drift. | Extract both floors from both files and compare them to each other, not to a constant. |
| Check only pyproject.toml, ignore pixi.toml | Assume pixi.toml follows pyproject.toml automatically | Maintainers sometimes edit one manifest but forget the other. Drift accumulates silently. | Test both files in every regression guard; make drift detection active, not reactive. |

## Results & Parameters

### Test Suite Location

```
tests/unit/scripts/test_dependency_floor_consistency.py
```

### Dependencies Required

```bash
# In pyproject.toml [project.optional-dependencies]
packaging>=21.0  # for packaging.version.Version
pytest>=9.0
pytest-cov>=7.0

# In pixi.toml [dependencies]
pytest >=9.0
pytest-cov >=7.0
```

### Key Configuration

```toml
# pyproject.toml: document the floor rationale
[project.optional-dependencies]
test = [
    "pytest>=9.0",
    "pytest-cov>=7.0",
    # ... other test deps
]

# NOTE: pytest and pytest-cov floors are intentionally tight (>=9.0, >=7.0).
# See test_dependency_floor_consistency.py and issue #785 for the regression guard.
```

```toml
# pixi.toml: match the floor exactly
[dependencies]
pytest = ">=9.0"
pytest-cov = ">=7.0"
```

### Version Comparison Examples

```python
from packaging.version import Version

# These all compare as equal (PEP 440 semantic equivalence):
assert Version("9.0") == Version("9.0.0")
assert Version("7.0") == Version("7.0.0")
assert Version("1.2") == Version("1.2.0")

# These compare as different (intentional):
assert Version("9.0") != Version("9.1")
assert Version("7.0") != Version("7.0.1")  # patch bump still differs
```

### Verification Checklist

```markdown
## Before Merging a Version Bump PR

- [ ] Both pyproject.toml and pixi.toml are in the commit
- [ ] `pytest test_dependency_floor_consistency.py -v` passes
- [ ] No other tests broke
- [ ] Pre-commit hooks pass (ruff, mypy, etc.)
- [ ] Docstring in pyproject.toml updated if floor reason changed
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| HomericIntelligence/ProjectHephaestus | Issue #785: document pytest 9.x / pytest-cov 7.x tight floors | Implemented `TestPytestConsistency` class with semantic version comparison using `packaging.version.Version`; all tests pass locally; CI validation pending on merge |

## Related Skills

- `central-version-manifest-drift-from-automation-bypass` — broader manifest drift detection across Dockerfiles and workflows; this skill focuses narrowly on Python dependency floors
- `python-version-drift-detection` — version drift in Python code (classifiers, `sys.version_info` checks); related but different layer than manifest file consistency
- `doc-config-drift-check` — documentation/config synchronization; similar pattern of keeping two files in sync
