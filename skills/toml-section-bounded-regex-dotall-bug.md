---
name: toml-section-bounded-regex-dotall-bug
description: "Fix for re.DOTALL cross-section matching bug when extracting values from TOML [tool.X] sections via regex. Use when: (1) writing a regex to extract a key from a specific TOML section, (2) a TOML parser regex returns wrong values for keys that appear in multiple sections, (3) refactoring TOML extraction code that uses re.DOTALL."
category: debugging
date: 2026-06-13
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [toml, regex, python, dotall, section-boundary]
---

# TOML Section-Bounded Regex — re.DOTALL Cross-Section Bug

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-13 |
| **Objective** | Extract a key from a specific TOML `[tool.X]` section without matching across section boundaries |
| **Outcome** | Latent bug found and fixed; section-bounded negative-lookahead pattern is the canonical fix |
| **Verification** | verified-local |

## When to Use

- Writing a regex to extract a value from a TOML `[tool.mypy]`, `[tool.pytest]`, or any `[tool.*]` section
- A TOML extraction function returns an unexpected value when the key appears in more than one section
- Refactoring Python code that uses `re.DOTALL` to parse structured TOML content
- Reviewing any regex that spans multiple lines in a TOML/INI-style config file

## Verified Workflow

### Quick Reference

```python
# BAD — re.DOTALL crosses [section] boundaries
pattern = re.compile(
    r"\[tool\.mypy\].*?python_version\s*=\s*\"([^\"]+)\"",
    re.DOTALL
)

# GOOD — section-bounded: stops at next [section] header
pattern = re.compile(
    r"\[tool\.mypy\]\n(?:(?!\[).+\n)*?python_version\s*=\s*\"([^\"]+)\""
)
```

### Detailed Steps

1. Identify every regex in the codebase that uses `re.DOTALL` (or `re.S`) AND targets a `[section]` header in a TOML/INI file.
2. For each such regex, replace `.*?` (DOTALL wildcard) with `(?:(?!\[).+\n)*?` — the negative-lookahead `(?!\[)` ensures the match stops when a new `[` section header is encountered.
3. Remove the `re.DOTALL` flag from `re.compile(...)`.
4. Add a regression test that places the target key in a *different* section after the intended section and asserts the extraction returns `None` (or the correct value from the intended section).

### Why `(?:(?!\[).+\n)*?` Works

- `(?!\[)` — negative lookahead: the current line must NOT start with `[`
- `.+\n` — match one full line (non-empty)
- `*?` — non-greedy: stop as soon as the target key is found
- Together: consume lines one at a time, stopping at the first `[section]` header

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| `re.DOTALL` with `.*?` | Used `re.compile(r"\[tool\.mypy\].*?python_version...", re.DOTALL)` | `.*?` with DOTALL crosses `[` boundaries — matches `python_version` in a later `[tool.X]` section | Never use `re.DOTALL` for intra-section TOML extraction |
| `[^\[]*?` character class | Used `[^\[]*?` to stop at `[` | Fails on multi-line values: `[^\[]` rejects `[` anywhere in the content, including valid inline arrays | Negative lookahead is more precise than character exclusion |

## Results & Parameters

```python
import re

# Generalized pattern — replace tool\.mypy with your target section
def make_section_regex(section: str, key: str) -> re.Pattern:
    section_escaped = re.escape(section)
    key_escaped = re.escape(key)
    return re.compile(
        rf"\[{section_escaped}\]\n(?:(?!\[).+\n)*?{key_escaped}\s*=\s*\"([^\"]+)\""
    )

# Example: extract python_version from [tool.mypy]
_MYPY_PYTHON_VERSION_RE = re.compile(
    r"\[tool\.mypy\]\n(?:(?!\[).+\n)*?python_version\s*=\s*\"([^\"]+)\""
)

# Regression test pattern
def test_does_not_cross_section_boundary():
    content = '[tool.other]\npython_version = "3.9"\n\n[tool.mypy]\npython_version = "3.11"\n'
    m = _MYPY_PYTHON_VERSION_RE.search(content)
    assert m and m.group(1) == "3.11"  # must not return 3.9

def test_stops_at_next_section():
    content = '[tool.mypy]\nstrict = true\n\n[tool.ruff]\npython_version = "3.12"\n'
    m = _MYPY_PYTHON_VERSION_RE.search(content)
    assert m is None  # [tool.mypy] has no python_version; must not match ruff's
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1189 — python-version-consistency DRY refactor | `hephaestus/validation/python_version.py` `_extract_versions_from_text()` |
