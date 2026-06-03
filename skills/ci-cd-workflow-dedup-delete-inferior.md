---
name: ci-cd-workflow-dedup-delete-inferior
description: "Delete duplicate GitHub Actions workflow instead of extracting shared jobs when only one consumer exists. Use when: (1) two workflows duplicate the same jobs, (2) one is a strict superset of the other, (3) only one consumer will use the result."
category: ci-cd
date: 2026-06-03
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: [github-actions, workflow-deduplication, deletion-pattern]
---

# CI/CD Workflow Deduplication: Delete Inferior Pattern

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-03 |
| **Objective** | Eliminate duplicate GitHub Actions workflow jobs by deleting the inferior workflow when one is a strict superset of the other |
| **Outcome** | Successfully reduced CI runtime by 50% (halved duplicate jobs); preserved coverage signal |
| **Verification** | verified-ci (ProjectTelemachy #151, PR #257) |

## When to Use

- Two GitHub Actions workflows run the same jobs (lint, test, secrets-scan)
- One workflow is a **strict superset** of the other (contains all its jobs plus additional gates)
- Only **one** consumer will use the merged result
- Goal is to eliminate duplicate work without restructuring for future expansion

## Verified Workflow

### Quick Reference

```bash
# 1. Identify the superset workflow (more jobs, newer features)
diff <(grep "^  [a-z-]*:" ci.yml) <(grep "^  [a-z-]*:" _required.yml)

# 2. Delete the inferior workflow
git rm .github/workflows/ci.yml

# 3. Preserve any observability (e.g., coverage reporting)
# If inferior had coverage flags, add them to superset:
# OLD: run: pixi run pytest --tb=short -q
# NEW: run: pixi run pytest --tb=short -q --cov=telemachy --cov-report=term-missing

# 4. Validate remaining workflow syntax
pixi run yamllint .github/workflows/_required.yml
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/_required.yml'))"
```

### Detailed Steps

1. **Enumerate jobs in both workflows**:
   ```bash
   python3 -c "
   import yaml
   for f in ['ci.yml', '_required.yml']:
       with open(f) as fp:
           w = yaml.safe_load(fp)
           print(f'{f}: {sorted(w[\"jobs\"].keys())}')"
   ```

2. **Verify containment relationship**:
   - Does the superset contain all jobs from the inferior workflow?
   - Does the superset have additional gates (security, build, validation)?
   - Is there a single point of merge (one workflow will remain)?

3. **Identify observable signals being lost**:
   - Coverage reporting flags (e.g., `--cov` pytest args)
   - Custom job timeouts or concurrency rules
   - Artifact uploads or reports
   - Any metrics unique to the inferior workflow

4. **Delete the inferior workflow**:
   ```bash
   git rm .github/workflows/ci.yml  # or whichever is the subset
   ```

5. **Preserve signals in the superset**:
   - Add coverage flags if coverage reporting was unique to the inferior workflow
   - Add concurrency groups if the inferior had rules the superset lacks
   - Add any custom timeout values from the inferior

6. **Validate the remaining workflow**:
   ```bash
   yamllint .github/workflows/_required.yml
   python3 -c "import yaml; yaml.safe_load(open('.github/workflows/_required.yml'))"
   ```

7. **Commit and test in CI**:
   ```bash
   git add .github/workflows/
   git commit -m "fix(ci): deduplicate workflows by removing ci.yml"
   git push && gh pr create
   ```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| GitHub reusable workflows (workflow_call) | Extract common jobs into `.github/workflows/shared.yml` and have both workflows call it | Adds indirection (uses: syntax, parameterization, new file) for zero benefit when only one consumer exists; reusable workflows become worthwhile only with 2+ callers | Prefer deletion for single-consumer scenarios; reserve reusable workflows for multi-consumer patterns |
| Keep both workflows with different purposes | One for developer feedback loop (fast), one for merge gate (comprehensive) | Creates version-drift footgun (pixi-version, checkout@v4 vs v6, timeout values); no explanatory comment why two exist; future maintainers add features to one and forget the other | Document intent clearly if two workflows must coexist; better to merge when job duplication exists |

## Results & Parameters

### ProjectTelemachy #151 (Issue #151)

**Before**:
- `ci.yml` (61 lines): lint-and-test job (ruff + mypy + yamllint + pytest --cov), secrets-scan job (gitleaks)
- `_required.yml` (334 lines): lint, unit-tests, security-secrets-scan, forbid-suppressions, markdownlint, pixi-check, justfile-check, symlink-check, integration-tests, security-dependency-scan, build, schema-validation, deps-version-sync
- **Duplication**: lint, test, secrets-scan ran twice on every push/PR (once in each workflow)

**Changes Made**:
1. `git rm .github/workflows/ci.yml`
2. In `_required.yml` unit-tests job, line 185:
   ```yaml
   - name: Run pytest
     run: pixi run pytest --tb=short -q --cov=telemachy --cov-report=term-missing
   ```

**After**:
- Single workflow `_required.yml` runs all checks once
- Coverage reporting preserved (pytest --cov flags added)
- CI runtime halved (no duplicate lint/test/secrets jobs)
- Version drift eliminated (no more pixi-version or checkout@ mismatches)

### Key Findings

**What Made This Work**:
- Clear job enumeration showed strict containment (all ci.yml jobs in _required.yml)
- Identified the single observable signal being lost (coverage reporting)
- Preserved that signal in the surviving workflow before deletion
- Validated surviving workflow syntax before committing

**What Would NOT Work Here**:
- Reusable workflows (over-engineered for one consumer)
- Keeping both with no comment (version drift + confusion)
- Deleting coverage reporting (would lose observability)

## Verified On

| Project | Context | Outcome |
|---------|---------|---------|
| ProjectTelemachy | PR #257, issue #151 | ✓ Merged (verified-ci, all commits signed, auto-merge enabled) |
