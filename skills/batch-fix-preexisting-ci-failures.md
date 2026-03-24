---
name: batch-fix-preexisting-ci-failures
description: "Systematic workflow for fixing multiple pre-existing CI failures on a PR by comparing against main, triaging by root cause, and applying targeted fixes. Use when: (1) PR CI shows failures unrelated to PR changes, (2) main branch has same failures, (3) need to fix multiple heterogeneous test failures in one PR."
category: ci-cd
date: 2026-03-24
version: "1.0.0"
user-invocable: false
tags:
  - ci
  - pre-existing
  - batch-fix
  - triage
  - mojo
---

# Batch Fix Pre-Existing CI Failures

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-03-24 |
| **Objective** | Fix 5 pre-existing CI failures across 4 CI job groups on PR #5076 |
| **Outcome** | ✅ SUCCESS - All 5 failures diagnosed and fixed in single commit |

## When to Use

- PR CI shows failures in test groups unrelated to PR changes
- Same failures appear on recent main branch CI runs
- Multiple heterogeneous failure types (compile errors, runtime crashes, assertion failures)
- Need to batch-fix pre-existing issues to get a PR green

## Verified Workflow

### Quick Reference

```bash
# 1. Get PR failure details
gh pr checks <PR> --repo <owner>/<repo> | grep fail

# 2. Get failed job logs
gh api repos/<owner>/<repo>/actions/jobs/<job-id>/logs | grep -E "❌ FAILED|Failed tests:" -A 5

# 3. Compare against main
gh run list --branch main --workflow "Comprehensive Tests" --limit 3 --json conclusion,databaseId
gh run view <main-run-id> --json jobs | python3 -c "import json,sys; [print(f'{j[\"conclusion\"]}: {j[\"name\"]}') for j in json.load(sys.stdin)['jobs'] if j['conclusion']=='failure']"

# 4. Get main branch failure details for comparison
gh api repos/<owner>/<repo>/actions/jobs/<main-job-id>/logs | grep -E "❌ FAILED" -A 3
```

### Detailed Steps

1. **Identify all failing CI jobs** on the PR using `gh pr checks`
2. **Get detailed error messages** from each failed job's logs
3. **Compare against main branch** — find which failures are pre-existing vs new regressions
4. **Triage by root cause category**:
   - Compile errors (type mismatches, parse errors)
   - Runtime assertion failures (logic bugs)
   - JIT crashes (ADR-009 heap corruption)
   - Numerical issues (overflow, NaN)
5. **Fix in priority order**: compile errors first (blocking), then runtime bugs, then crashes
6. **Batch into single commit** when all fixes are independent

### Common Mojo CI Failure Categories

| Category | Error Pattern | Fix |
|----------|--------------|-----|
| Type mismatch | `cannot be converted from 'Tensor' to 'AnyTensor'` | Add `.as_any()` conversion |
| Parse error | `expected ')' in call argument list` | Check positional vs keyword args, f-string compatibility |
| Assertion fail | `Values are not equal` | Debug the actual computation, check fast-path optimizations |
| JIT crash | `libKGENCompilerRTShared.so` / `execution crashed` | Split file per ADR-009 (max 10 test functions per file) |
| Numerical overflow | `inf >= X` | Use proper weight initialization (He/Xavier) |
| ADR-009 violation | Too many test functions per file | Count `fn test_*` functions, split if > 10 |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| N/A | Direct diagnosis approach worked | N/A | Compare against main FIRST to avoid investigating issues that aren't your PR's fault |

## Results & Parameters

**5 fixes applied in one commit**:

1. **Fast-path step bug** (`any_tensor.mojo`): Add `step != 1` check to memcpy guard
2. **Arg order bug** (`test_setitem_view_part1.mojo`): Use `message=` keyword arg
3. **Type conversion** (`test_typed_conv2d.mojo`): Add `.as_any()` to 5 call sites
4. **ADR-009 split** (`test_training_loop.mojo`): Trim 19→7 tests, move rest to part files
5. **He initialization** (`test_vgg16_e2e.mojo`): `sqrt(2/fan_in)` for conv/FC weights

**Parallelization strategy**: Launch 3 implementation agents in background for independent fixes while working on remaining 2 fixes directly.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectOdyssey | PR #5076 fix-remaining-crashes-round2 | [notes](./skills/batch-fix-preexisting-ci-failures.notes.md) |
