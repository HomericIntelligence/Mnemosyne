---
name: mypy-incremental-config-scope-sqlite-cache-separately
description: "When adding explicit mypy incremental mode to pyproject.toml, scope to incremental=true + cache_dir only — sqlite_cache is a separate format-change optimization and must not be bundled with an incremental-mode audit fix. Use when: (1) fixing an audit finding about unconfigured mypy incremental mode, (2) reviewing a PR that adds sqlite_cache alongside incremental, (3) planning mypy config improvements in a Python project."
category: tooling
date: 2026-06-26
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: [mypy, incremental, sqlite_cache, pyproject, type-checking, yagni, scope]
---

# mypy Incremental Config: Scope sqlite_cache Separately

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-26 |
| **Objective** | Fix audit finding: mypy pre-commit hook runs full codebase with no explicitly configured incremental mode |
| **Outcome** | Success — `incremental = true` + `cache_dir = ".mypy_cache"` added; `sqlite_cache` removed after reviewer YAGNI flag |
| **Verification** | verified-ci |

## When to Use

- Fixing an audit finding that says mypy incremental mode "is not explicitly configured"
- Reviewing a PR that adds `sqlite_cache = true` alongside `incremental = true` to `[tool.mypy]`
- Planning mypy config improvements where the goal is just "make the default explicit"
- Any "configure `--incremental` explicitly" remedy in `pyproject.toml`

## Verified Workflow

### Quick Reference

```toml
# pyproject.toml — [tool.mypy] section
# Correct: only these two for an "explicit incremental" audit fix
incremental = true
cache_dir = ".mypy_cache"

# DO NOT add sqlite_cache = true unless you are specifically optimizing
# CI cache restore time and that is the stated goal of the change.
```

```python
# tests/unit/validation/test_mypy_incremental_config.py
# Guard test — assert only the two in-scope keys
import tomllib
from pathlib import Path
import pytest

PYPROJECT = Path(__file__).resolve().parents[3] / "pyproject.toml"

@pytest.fixture(scope="module")
def mypy_config() -> dict[str, object]:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return data["tool"]["mypy"]

def test_incremental_enabled(mypy_config: dict[str, object]) -> None:
    assert mypy_config.get("incremental") is True

def test_cache_dir_pinned(mypy_config: dict[str, object]) -> None:
    assert mypy_config.get("cache_dir") == ".mypy_cache"
```

```yaml
# .github/workflows/_required.yml — lint job, after pre-commit cache step
- name: Cache mypy incremental cache
  uses: actions/cache@<pinned-sha>  # v5
  with:
    path: .mypy_cache
    key: mypy-${{ runner.os }}-${{ hashFiles('pixi.lock', 'pyproject.toml') }}
    restore-keys: |
      mypy-${{ runner.os }}-
```

### Detailed Steps

1. **Add only `incremental` and `cache_dir` to `[tool.mypy]`** — these two keys make the existing default explicit. Salt the CI cache key with `pixi.lock` (mypy version pin) + `pyproject.toml` (mypy config hash) so a version or config bump invalidates the cache.

2. **Do NOT add `sqlite_cache = true` in the same PR** — this changes mypy's on-disk cache *format* (many JSON fragment files → one SQLite file). It is justified as a CI-restore speed optimization but is independent of the "configure incremental mode" remedy. Bundling it violates YAGNI and will draw a reviewer flag.

3. **Write a `tomllib`-based guard test** — parse `pyproject.toml` and assert each key. Assert only `incremental` and `cache_dir`; do NOT assert `sqlite_cache` (it is not part of the fix).

4. **Verify `.mypy_cache` is gitignored** before adding the CI cache step — it must not be committed. Standard location: `.gitignore` with `.mypy_cache/`.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Bundle `sqlite_cache = true` with incremental fix | Added all three keys (`incremental`, `cache_dir`, `sqlite_cache`) in one PR | Reviewer flagged `sqlite_cache` as YAGNI — it changes cache *format*, an independent CI-restore optimization not required by the "explicit incremental" audit finding | Scope `sqlite_cache` to its own issue/PR with a measured CI-restore bottleneck as justification |
| Assert `sqlite_cache` in the guard test | Test file included `test_sqlite_cache_enabled` asserting `sqlite_cache is True` | Once `sqlite_cache` was removed from `pyproject.toml`, the test failed; also cements an out-of-scope knob | Guard tests should only assert the keys that are in scope for the fix |

## Results & Parameters

```toml
# Minimal correct [tool.mypy] incremental config (audit-fix scope only)
incremental = true
cache_dir = ".mypy_cache"
# sqlite_cache omitted — belongs to a separate "optimize CI cache restore" change
```

Expected CI cache key format:
```
mypy-<runner.os>-<sha256(pixi.lock + pyproject.toml)>
```

Cache invalidation triggers: mypy version bump (via `pixi.lock`), any `[tool.mypy]` config change (via `pyproject.toml`).

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1503 audit fix (2026-06-26) | PR #1649; `sqlite_cache` removed after review; guard test uses `tomllib` (stdlib 3.11+) |
