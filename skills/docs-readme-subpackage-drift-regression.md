---
name: docs-readme-subpackage-drift-regression
description: "How to fix and prevent README directory tree drift when a Python subpackage exists on disk but is missing from the README structure block. Use when: (1) audit flags README tree vs disk mismatch, (2) adding a new subpackage to a monorepo."
category: documentation
date: 2026-06-13
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: []
---

# docs-readme-subpackage-drift-regression

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-13 |
| **Objective** | Fix README directory tree omitting `scripts_lib/` subpackage and prevent future drift |
| **Outcome** | Successful — regression test added, CI green, PR #1272 merged |
| **Verification** | verified-ci |

## When to Use

- A strict repo audit flags a subpackage present on disk but absent from `README.md`'s directory tree block
- Prose counts in README (`"19 documented subpackages"`) are stale relative to actual package count
- Adding a new subpackage to a Python monorepo and want a permanent guard
- `tests/unit/validation/` lacks a README structure coverage test

## Verified Workflow

### Quick Reference

```bash
# 1. Find the gap
ls hephaestus/ | grep -v __pycache__ | sort
grep -n "├──\|└──" README.md | head -30

# 2. Insert the missing entry alphabetically (match surrounding indentation)
# e.g. between resilience/ and system/ in the README tree block

# 3. Update stale prose counts
grep -n "documented subpackages\|[0-9]* subpackage" README.md CLAUDE.md

# 4. Add regression test at tests/unit/validation/test_readme_subpackage_tree.py
# (see Results & Parameters for full test)

# 5. Verify
pixi run python -m pytest tests/unit/validation/test_readme_subpackage_tree.py -v
pre-commit run --files README.md CLAUDE.md tests/unit/validation/test_readme_subpackage_tree.py
```

### Detailed Steps

1. **Enumerate real subpackages**: List `hephaestus/` subdirs that have `__init__.py` and don't start with `__`.
2. **Compare vs README tree**: Grep README for `├── <name>/` or `└── <name>/` patterns to find gaps.
3. **Fix README tree**: Insert the missing entry alphabetically, matching column alignment of surrounding comments.
4. **Fix prose counts**: Search README.md and CLAUDE.md for any numeric subpackage count claims and update them.
5. **Add regression test**: Create `tests/unit/validation/test_readme_subpackage_tree.py` (see Results & Parameters). This test will catch all future drift automatically.
6. **Run tests + pre-commit**: Confirm test passes and all hooks (markdownlint, ruff, mypy, unit test structure check) pass.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Manual one-time fix without test | Only updating README.md | Next subpackage addition would drift silently again | Always add a regression test to make the fix permanent |
| Grepping only README for count | Only updating README prose count | CLAUDE.md also had a stale `19 documented subpackages` reference | Search ALL docs for numeric subpackage count claims, not just README |

## Results & Parameters

### Regression Test (copy-paste ready)

Place at `tests/unit/validation/test_readme_subpackage_tree.py`:

```python
"""Guard: README directory tree must list every hephaestus/ subpackage.

Prevents doc-vs-reality drift: a subpackage can exist on disk but be
absent from the README tree while the doc claims a stale count.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_DIR = REPO_ROOT / "hephaestus"
README = REPO_ROOT / "README.md"


def _real_subpackages() -> set[str]:
    """Return the names of every importable hephaestus/ subpackage on disk."""
    return {
        p.name
        for p in PACKAGE_DIR.iterdir()
        if p.is_dir() and (p / "__init__.py").exists() and not p.name.startswith("__")
    }


def test_readme_tree_lists_every_subpackage() -> None:
    """Every real subpackage must appear in the README directory tree block."""
    readme = README.read_text(encoding="utf-8")
    missing = sorted(
        name
        for name in _real_subpackages()
        if f"├── {name}/" not in readme and f"└── {name}/" not in readme
    )
    assert not missing, f"README directory tree omits subpackage(s): {missing}"
```

### Where prose counts can hide

```bash
# Find all numeric subpackage count references across the repo
grep -rn "[0-9]\+ documented subpackage\|[0-9]\+ subpackages" README.md CLAUDE.md docs/
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1188 / PR #1272 — scripts_lib/ missing from README tree | CI green on all Python 3.10–3.13 matrix |
