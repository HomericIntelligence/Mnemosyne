---
name: mypy-incremental-cache-scope
description: "Keep explicit mypy incremental-mode configuration separate from cache-format optimization. Use when: (1) an audit asks to make incremental mode explicit, (2) a change also proposes `sqlite_cache`, or (3) CI cache behavior needs a narrowly scoped, testable contract."
category: tooling
date: 2026-08-07
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: [mypy, incremental, cache, sqlite, pyproject, yagni]
---

# Mypy Incremental Cache Scope

## Overview

| Field | Value |
|-------|-------|
| Date | 2026-08-07 |
| Objective | Make mypy incremental behavior explicit without bundling an unrelated cache-format change. |
| Outcome | Configure `incremental` and `cache_dir` in the audit fix; require separate measured evidence before enabling `sqlite_cache`. |

## When to Use

- A configuration audit flags implicit mypy incremental behavior.
- A reviewer sees `sqlite_cache = true` added beside the incremental setting.
- A guard test asserts configuration knobs beyond the stated requirement.
- CI cache restoration is being optimized independently of type-check behavior.

## Verified Workflow

### Quick Reference

```toml
[tool.mypy]
incremental = true
cache_dir = ".mypy_cache"
# sqlite_cache is a separate cache-format decision.
```

1. Translate the requirement literally: explicit incremental mode requires `incremental = true`; an explicit location may add `cache_dir`.
2. Do not add `sqlite_cache` unless the task includes cache-format optimization and has measured restore or filesystem evidence.
3. Test only the scoped contract. Parse the configuration and assert `incremental` and `cache_dir`; do not freeze unrelated defaults.
4. If CI persists `.mypy_cache`, include the type-checker version and relevant configuration or lockfiles in the cache key.
5. Run mypy twice when validating incremental reuse, then invalidate a source or configuration input and prove the expected recheck occurs.

This distinction matters because incremental mode controls reuse of prior type-check state, while `sqlite_cache` changes how that state is stored. They can be evaluated independently.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Bundle the SQLite cache | Added `sqlite_cache = true` to an explicit-incremental audit fix | It changed cache format without evidence that format was the bottleneck | Split performance optimization from behavior clarification |
| Guard every proposed key | Added a test requiring `sqlite_cache` | The test cemented an out-of-scope choice and failed when the option was removed | Assert only the stated configuration contract |
| Cache without invalidation inputs | Reused one CI cache key across tool and config changes | Stale metadata could survive incompatible changes | Key cache reuse to tool and configuration inputs |

## Results & Parameters

| Parameter | Scoped value | Notes |
|-----------|--------------|-------|
| `incremental` | `true` | Makes reuse explicit |
| `cache_dir` | `.mypy_cache` | Stable directory for local or CI persistence |
| `sqlite_cache` | omitted | Evaluate separately with measurements |

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| Python automation package | Static-analysis configuration audit | CI accepted the minimal explicit incremental configuration after the unrelated cache-format option and its guard were removed. |
