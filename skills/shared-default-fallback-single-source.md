---
name: shared-default-fallback-single-source
description: "Use when: (1) a selector or pipeline helper hardcodes a fallback value that duplicates a shared default constant, (2) blank or missing configuration must follow the canonical runtime default, (3) tests should prove explicit configuration still wins while default changes propagate automatically."
category: architecture
date: 2026-08-07
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: [defaults, fallback, single-source-of-truth, configuration, regression-testing]
---

# Shared Default Fallback as a Single Source of Truth

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-07 |
| **Objective** | Prevent helper-level fallback literals from drifting away from a canonical runtime default. |
| **Outcome** | A selector delegated blank and missing configuration to the shared default while preserving explicit configuration precedence; focused tests and CI passed. |
| **Verification** | verified-ci |

## When to Use

- A helper contains `configured_value or "current-default"` while another module owns the canonical default.
- Changing the shared default updates one code path but leaves a pipeline, CLI, or adapter on the old value.
- Empty strings and missing attributes should behave like unspecified configuration.
- A regression test currently asserts a literal fallback instead of proving delegation to the shared constant.

## Verified Workflow

### Quick Reference

```python
from package.runtime_defaults import DEFAULT_BACKEND


def select_backend(config: object) -> str:
    configured = getattr(config, "backend", "")
    return str(configured or DEFAULT_BACKEND)
```

```python
def test_blank_value_uses_shared_default(monkeypatch):
    monkeypatch.setattr(selector_module, "DEFAULT_BACKEND", "alternate")
    assert selector_module.select_backend(config_with(backend="")) == "alternate"


def test_explicit_value_wins():
    assert selector_module.select_backend(config_with(backend="explicit")) == "explicit"
```

### Detailed Steps

1. Locate every definition and use of the fallback value. Identify which module already owns the runtime default rather than introducing another constant.
2. Import the canonical constant at the selector boundary and replace only the duplicated literal. Preserve the existing precedence rule: a non-empty explicit value wins.
3. Decide deliberately which values mean "unspecified." If the established contract treats both a missing attribute and `""` as absent, keep that behavior with `getattr(..., "") or DEFAULT_BACKEND`.
4. Add a mutation-sensitive regression test. Patch the constant to a value different from today's default and assert that blank configuration returns the patched value.
5. Add separate tests for explicit and, when supported, missing configuration. These protect precedence and absence semantics independently.
6. Search the affected selector surface for the old inline fallback, then run focused tests and the repository's complete validation.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Keep the inline literal because it matches today | Left `or "current-default"` beside a shared constant with the same value | The two sources can diverge during the next default change | Reuse the existing authority instead of copying its current value. |
| Update only the expected test value | Changed assertions without changing the selector | Tests documented the new expectation while production still used the stale fallback | Change the selector and its regression tests together. |
| Assert equality with today's literal | Tested that blank configuration returned a fixed string | The test still passed when the selector bypassed the shared constant | Patch the shared constant to a distinct value so the test proves delegation. |
| Test only the fallback path | Covered blank configuration but not explicit precedence | A later refactor could make the default override operator input | Pin fallback and explicit-value behavior with separate tests. |

## Results & Parameters

### Decision Table

| Configuration state | Expected result |
| ------------------- | --------------- |
| Explicit non-empty value | Return the explicit value. |
| Empty value | Return the shared default. |
| Missing attribute, when supported | Return the shared default. |
| Shared default changes | All delegating selectors change without local edits. |

### Verification Commands

```bash
rg -n 'DEFAULT_BACKEND|select_backend|current-default' <source-root> <test-root>
<package-manager> run pytest <focused-test-path> -k 'default or explicit'
<package-manager> run <validation-task>
```

Successful verification shows no duplicated fallback literal in the selector, mutation-sensitive tests passing, and the complete validation task green.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private Python automation repository | Pipeline selector default alignment | Focused fallback and precedence regressions passed together with repository CI; identifying implementation details were intentionally generalized. |

## References

- [Dependency manifest single source of truth](dependency-manifest-single-source-of-truth.md)
