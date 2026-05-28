---
name: documentation-drift-detection-hatch-vcs
description: "Detect and fix stale documentation in guidance files (CLAUDE.md) that contradict actual implementation. Use when: (1) guidance docs claim outdated workflows, (2) multiple docs contradict each other, (3) auditing guidance files before major releases."
category: documentation
date: 2026-05-28
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: [documentation-drift, guidance-audit, hatch-vcs, version-management]
---

# Documentation Drift Detection — Hatch-VCS Verification

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-28 |
| **Objective** | Detect and fix stale documentation in guidance files (CLAUDE.md) that contradict actual codebase implementation; prevent misdirection of human and AI contributors. |
| **Outcome** | Successfully identified four factually incorrect lines in CLAUDE.md "Version Management" section; corrected to reflect actual hatch-vcs dynamic versioning pattern. PR #637 merged with all checks passing. |
| **Verification** | verified-ci |
| **Issue** | ProjectHephaestus #618 |

## When to Use

- Guidance files (CLAUDE.md, CONTRIBUTING.md, docs/RELEASING.md) contain claims that contradict source code, pyproject.toml, or build hooks
- Multiple guidance docs give conflicting instructions (e.g., one says "edit VERSION file", another says version comes from git tags)
- Preparing for a major release and need to audit all documentation for consistency
- Post-code-review: code implements pattern X, but guidance still documents pattern Y
- Discovering that a utility (e.g., VersionManager) is documented but no longer used in the codebase

## Verified Workflow

### Quick Reference

**Step 1: Identify the claim being audited**

```bash
# In ProjectHephaestus, search CLAUDE.md for version-related claims
grep -n "version\|VERSION\|Version" /path/to/CLAUDE.md | head -20
```

**Step 2: Verify the claim against pyproject.toml**

```bash
# Check if [project].version is static or dynamic
grep -A 2 "^\[project\]" pyproject.toml | grep -E "version|dynamic"

# Should show: dynamic = ["version"]
# With: [tool.hatch.version] source = "vcs"
```

**Step 3: Verify against source code**

```bash
# Check if VersionManager utility exists and is used
find hephaestus -name "*version*" -type f | grep -v __pycache__

# Check how version is read at runtime
grep -r "importlib.metadata\|__version__" hephaestus/__init__.py
```

**Step 4: Check build-time hooks**

```bash
# Verify hatch-vcs generates _version.py at build time
grep -A 3 "tool.hatch.build.hooks.vcs" pyproject.toml

# Should show: version-file = "hephaestus/_version.py"
```

**Step 5: Cross-check all guidance docs for consistency**

```bash
# Ensure CLAUDE.md, CONTRIBUTING.md, RELEASING.md agree
for file in CLAUDE.md CONTRIBUTING.md docs/RELEASING.md; do
  echo "=== $file ==="
  grep -i "hatch-vcs\|dynamic.*version\|git.*tag" "$file" || echo "No hatch-vcs mention"
done
```

**Step 6: Correct the false documentation**

Edit CLAUDE.md "Version Management" section to state:

```markdown
## Version Management

This project uses **hatch-vcs dynamic versioning** — the package version is derived
from git tags, not stored in any file.

- **Single source of truth**: the latest `vX.Y.Z` git tag. `pyproject.toml` declares
  `dynamic = ["version"]` with `[tool.hatch.version]` `source = "vcs"`; there is **no**
  static `[project].version` field.
- **`hephaestus/_version.py`** is generated at build time by the hatch-vcs build hook
  and is not committed.
- **`pixi.toml`** intentionally has no version field — do not add one.
- The `check-version-single-source` pre-commit hook enforces this invariant.
- To cut a release: create a signed `vX.Y.Z` git tag. See `docs/RELEASING.md`.
```

### Detailed Steps

1. **Search for the false claim** in guidance files using grep patterns for version-related language
2. **Cross-reference against pyproject.toml** to determine actual versioning approach (static vs. hatch-vcs)
3. **Check source code** (hephaestus/__init__.py, _version.py generation) to see how version is actually read
4. **Verify build hooks** in pyproject.toml to confirm version generation mechanism
5. **Audit all guidance docs** for consistency — CLAUDE.md, CONTRIBUTING.md, docs/RELEASING.md must agree
6. **Correct the documentation** in-place with the verified workflow
7. **Run pre-commit hooks** to validate documentation format
8. **Commit with detailed message** explaining the false claim and verified correction
9. **Cross-reference related docs** to ensure no other files contain the same false claim

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Trusting guidance doc as source of truth | Assumed CLAUDE.md accurately reflected implementation | CLAUDE.md had stale instructions describing static [project].version field + VersionManager utility (neither exist in actual code) | Guidance files drift from implementation; must systematically verify every claim against source code + config |
| Single-doc audit | Only checked CLAUDE.md for version management | Found inconsistency with docs/RELEASING.md which correctly described hatch-vcs; CONTRIBUTING.md partially correct | Multi-doc consistency required; DRY principle: version strategy must be documented identically in all guidance files |
| grep-only validation | Used grep to check for "version" mentions | Missed the logical consistency problem: docs claimed a VersionManager that doesn't exist, and pyproject.toml contradicted the static [project].version claim | Must cross-reference multiple files; grep finds mentions but not logical inconsistencies |
| Assuming documentation is read before changes | Did not validate docs before starting implementation | Misdirected contributors following stale documentation | Guidance files are high-leverage (read by all humans + AI agents); drift has outsized impact; audit before major releases |

## Results & Parameters

### Exact Verification Commands Used

```bash
# Command 1: Extract version-related claims from CLAUDE.md
grep -n "version\|Version\|VERSION" /home/mvillmow/Projects/ProjectHephaestus/CLAUDE.md

# Command 2: Verify pyproject.toml has dynamic versioning
grep -E "dynamic|hatch.version" /home/mvillmow/Projects/ProjectHephaestus/pyproject.toml

# Command 3: Check if VersionManager exists
find /home/mvillmow/Projects/ProjectHephaestus/hephaestus -name "*version*" | grep -v __pycache__

# Command 4: Verify version is read via importlib.metadata
grep -n "importlib.metadata\|__version__" /home/mvillmow/Projects/ProjectHephaestus/hephaestus/__init__.py

# Command 5: Cross-check CONTRIBUTING.md
grep -i "hatch-vcs\|dynamic" /home/mvillmow/Projects/ProjectHephaestus/CONTRIBUTING.md

# Command 6: Cross-check docs/RELEASING.md
grep -i "hatch-vcs\|dynamic\|git.*tag" /home/mvillmow/Projects/ProjectHephaestus/docs/RELEASING.md
```

### Expected Outputs

**False claims found in old CLAUDE.md:**
```
Line N: "...maintains a VERSION file..."
Line N+1: "...VersionManager utility updates VERSION..."
Line N+2: "[project].version = "X.Y.Z"..."
Line N+3: "...pixi.toml [workspace] version field..."
```

**Verified in pyproject.toml:**
```
dynamic = ["version"]

[tool.hatch.version]
source = "vcs"

[tool.hatch.build.hooks.vcs]
version-file = "hephaestus/_version.py"
```

**Verified in hephaestus/__init__.py:**
```python
from importlib.metadata import version as get_version
__version__ = get_version("hephaestus")
```

**Verified in docs/RELEASING.md and CONTRIBUTING.md:**
Both correctly describe hatch-vcs dynamic versioning from git tags.

### Categories of Documentation Drift Found

| Claim | Status | Fix |
|-------|--------|-----|
| "maintains a VERSION file" | FALSE | Removed; version comes from git tags via hatch-vcs |
| "VersionManager utility updates VERSION" | FALSE | Removed; no such utility exists; version is build-time generated |
| "[project].version = "X.Y.Z" static field" | FALSE | Corrected to: dynamic = ["version"] with source = "vcs" |
| "pixi.toml [workspace] version field exists" | FALSE | Removed; pixi.toml has no version field intentionally |
| "hephaestus/_version.py is committed" | FALSE | Corrected to: generated at build time, not committed |
| "To release: edit VERSION file / git tag" | PARTIAL | Clarified: git tag only (no VERSION file edit) |

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #618 — Fix CLAUDE.md Version Management section | PR #637 merged with all CI checks passing; cross-referenced with CONTRIBUTING.md and docs/RELEASING.md for consistency |
| ProjectHephaestus | Pre-release audit | Version management pattern audited and verified before 1.0 release |

---

## Key Learnings

1. **Guidance files are high-leverage** — CLAUDE.md is canonical for all contributors (human and AI). Drift misdirects everyone.

2. **Documentation drift is invisible** — Without systematic verification against source code, stale docs are trusted until they cause failures.

3. **Multi-doc consistency is essential** — Version management must be described identically in CLAUDE.md, CONTRIBUTING.md, and docs/RELEASING.md. One file contradicting another creates confusion.

4. **Systematic verification pattern**:
   - Extract claims from guidance (grep)
   - Cross-check against implementation (source code, config files, build hooks)
   - Verify against related docs (DRY principle)
   - Correct in-place with detailed justification
   - Commit with explanation of false claim + verified correction

5. **The hatch-vcs pattern** is the source of truth:
   - Git tag (e.g., `v1.0.0`) → single source of truth
   - `pyproject.toml`: `dynamic = ["version"]` with `source = "vcs"`
   - Build time: hatch-vcs hook generates `_version.py` (not committed)
   - Runtime: `importlib.metadata.version()` reads installed package version
   - No static version field anywhere in the codebase
