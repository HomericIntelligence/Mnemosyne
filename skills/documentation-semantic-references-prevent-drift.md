---
name: documentation-semantic-references-prevent-drift
description: "Prevent documentation drift by using semantic references (links to source files) instead of hardcoding version numbers or config values. Use when: (1) documenting version requirements that come from pyproject.toml, (2) referencing config fields that might change, (3) creating cross-file documentation links."
category: documentation
date: 2026-06-05
version: "1.0.0"
verification: verified-local
tags: [drift-prevention, documentation-maintenance]
---

# Semantic References Prevent Documentation Drift

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-05 |
| **Objective** | Prevent documentation from silently drifting when upstream config (requires-python, versions, config values) changes |
| **Outcome** | Successful — applied in PR #943 and verified by review feedback |
| **Verification** | verified-local |

## When to Use

- Documenting Python version requirements (reference `requires-python` in `pyproject.toml`, not hardcoded "3.10+")
- Documenting version constraints (link to source file, not hardcoded ">=1.0,<2")
- Documenting config field values that come from source files
- Creating cross-file documentation references (link with anchor, not copy-paste text)

## Verified Workflow

### Quick Reference

**Don't hardcode:**
```markdown
This package requires Python 3.10+.
```

**Do use semantic reference:**
```markdown
This package requires Python 3.10+ (see `requires-python` in [`pyproject.toml`](pyproject.toml)).
```

### Detailed Steps

1. Identify version/config fields that are sourced from config files (pyproject.toml, pixi.toml, etc.)
2. Replace inline hardcoded values with references to the source file
3. Use markdown links to point readers to the authoritative source: `[file](path/to/file)`
4. For specific anchors: `[CONTRIBUTING.md#platform-support](CONTRIBUTING.md#platform-support)`
5. Test: Verify the link is accessible and anchor exists

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Hardcode version inline | "Python 3.10+" in README | Drifts when `requires-python` is bumped by Dependabot; creates silent documentation-code divergence | Use semantic references instead |
| Duplicate table in README and CONTRIBUTING | Copy platform comparison table to both files | Creates two sources of truth; table drifts independently in each file | DRY principle: link to canonical table, don't duplicate |

## Results & Parameters

**Applied in:** PR #943 (issue #767)

**Before (PR #943 initial commit):**
```markdown
The wheel is pure-Python and installs on Linux, macOS, and Windows (Python 3.10+; ...)
```

**After (PR #943 review feedback fix):**
```markdown
The wheel is pure-Python and installs on Linux, macOS, and Windows (see `requires-python` in [`pyproject.toml`](pyproject.toml)).
```

**Benefit:** Documentation now auto-updates when upstream config changes; no Dependabot-related drift.
