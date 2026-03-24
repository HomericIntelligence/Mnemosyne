---
name: mojo-ci-failure-systematic-triage
description: "Systematic workflow for triaging and fixing Mojo CI failures at scale — categorize by root cause (compilation, runtime, numerical, infrastructure), fix in priority order, file issues for deep bugs. Use when: (1) CI has 10+ failing test groups, (2) multiple failure categories mixed together, (3) need to distinguish fixable tests from core code bugs."
category: ci-cd
date: 2026-03-24
version: "1.0.0"
user-invocable: false
tags:
  - mojo
  - ci-cd
  - triage
  - testing
  - debugging
---

# Mojo CI Failure Systematic Triage

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-03-24 |
| **Objective** | Fix 20+ CI test failures across 6 test groups after a major Mojo refactoring (AnyTensor move + typed dispatch changes) |
| **Outcome** | Resolved all failures across 7 PRs: compilation fixes, runtime bug fixes, core code enhancements. Reduced from 100+ failing tests to green CI. |

## When to Use

- CI has multiple failing test groups with different root causes mixed together
- Major refactoring broke tests across compilation, runtime, and numerical categories
- Need to prioritize which failures to fix first vs file as issues
- Mojo test failures that mix docstring warnings, type mismatches, use-after-free, and numerical overflow
- Infrastructure flakes (502 errors, container failures) mixed with real code failures

## Verified Workflow

### Quick Reference

```bash
# Step 1: Get all failing tests from CI
gh run view <run-id> --log 2>&1 | grep "❌ FAILED:" | sort -u

# Step 2: Get error details for each failure
gh run view <run-id> --log 2>&1 | grep -E "error:|crashed|Assertion" | head -50

# Step 3: Categorize failures
# Category A: Compilation errors (visible in CI logs, fixable without runtime)
# Category B: Runtime errors (need Podman or CI to reproduce)
# Category C: Infrastructure flakes (502, container failures — re-run)

# Step 4: Fix in order: A (compilation) → B (runtime) → C (re-run)
```

### Detailed Steps

#### 1. Extract All Failures from CI

```bash
# Get the specific failing tests
gh run view <run-id> --log 2>&1 | grep "❌ FAILED:" | sort -u

# Get error context for each
gh run view <run-id> --log 2>&1 | grep -B5 "FAILED:" | grep "error:" | head -30

# Check for infrastructure failures
gh run view <run-id> --log 2>&1 | grep "502\|Cannot connect\|container.*not running"
```

#### 2. Categorize Each Failure

| Category | Error Pattern | Priority | Action |
|----------|--------------|----------|--------|
| **Compilation: docstrings** | `doc string summary should begin with a capital letter` | P1 (batch fix) | Capitalize first letter of all docstring summaries |
| **Compilation: imports** | `package 'X' does not contain 'Y'` | P1 | Fix import paths |
| **Compilation: type mismatch** | `cannot be converted from 'Tensor' to 'AnyTensor'` | P1 | Add `.as_any()` conversion |
| **Compilation: missing args** | `missing N required positional arguments` | P1 | Read function signature, add missing args |
| **Compilation: type inference** | `failed to infer parameter 'dtype'` | P1 | Specify explicit type parameter `Linear[DType.float32]` |
| **Compilation: wrong arg order** | `value passed to 'tolerance' cannot be converted from 'StringLiteral'` | P1 | Fix argument order or use named parameters |
| **Runtime: assertion** | `Assertion failed` | P2 | Investigate test expectations vs implementation |
| **Runtime: values** | `Values are not equal` | P2 | Debug the computation (slice step, __str__ format, etc.) |
| **Runtime: crash** | `execution crashed` | P2 | Investigate use-after-free, numerical overflow, memory bugs |
| **Runtime: NaN/Inf** | `contains NaN or Inf` | P2 | Check numerical stability (float16 range, overflow) |
| **Infrastructure** | `curl: (22) error: 502` | P3 | Re-run CI: `gh run rerun <run-id> --failed` |

#### 3. Fix Compilation Errors First (Batch Processing)

Compilation errors are visible in CI logs and don't need runtime reproduction:

```bash
# Find all files with lowercase docstrings
gh run view <run-id> --log 2>&1 | grep "doc string summary" | \
  sed 's/.*\/workspace\///' | sed 's/:.*//' | sort -u

# Batch fix with parallel agents (one per 5 files)
# Each agent: read file, capitalize docstring first letters, write back
```

#### 4. Fix Runtime Errors (Requires Investigation)

For each runtime failure:
1. Read the test file to understand what it tests
2. Read the CI error output for context (which test passed before the crash)
3. Trace the code path to find the root cause
4. Fix the actual bug, not a workaround

Common Mojo runtime crash root causes:
- **Use-after-free**: Moving AnyTensor ownership into another struct, then using the original
- **Numerical overflow**: `ones()` input through deep conv networks overflows Float32
- **Float16 range**: `Float32(-1e9)` overflows float16 range [-65504, 65504]
- **Precision loss**: `Float32()` casts in backward passes lose gradient precision
- **Slice step bug**: Fast-path memcpy not accounting for step > 1

#### 5. File Issues for Deep Bugs

For failures that require significant code changes:
```bash
gh issue create --title "bug: <description>" \
  --body "<CI evidence, root cause analysis, suggested fix>" \
  --label "bug" --label "testing"
```

#### 6. Verify with CI Re-run

After fixes, push and check CI. If infrastructure flakes occur:
```bash
gh run rerun <run-id> --failed
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Dismissing crashes as JIT | Closed crash issues as "Mojo JIT crash, not fixable" | User confirmed crashes were real bugs (use-after-free, numerical overflow) | ALWAYS investigate crashes — don't assume they're compiler bugs |
| Splitting test files (ADR-009) | Split VGG16 e2e into 3 parts to avoid "heap corruption" | This was a workaround, not a fix. The real cause was numerical overflow from ones() input | Fix root causes, not symptoms. ADR-009 heap corruption workaround is resolved. |
| Single-pass sub-agent fix | Launched agents to fix all docstrings in 15 files | Agents missed 6 docstrings across 3 files | Always do a final `grep '"""[a-z]'` sweep after agent batch fixes |
| Using `counter[0] += 1` in recursion | Mutable List counter passed through recursive __str__ formatting | Mojo error: "expression must be mutable for in-place operator destination" — parameter wasn't `mut` | Use offset-based pure recursion instead of mutable state threading. If you need mutation, add `mut` to parameter. |

## Results & Parameters

### Triage Priority Order

```text
1. Infrastructure flakes → re-run CI (zero code changes)
2. Compilation: docstrings → batch capitalize (mechanical, parallelizable)
3. Compilation: imports/types → fix paths, add .as_any(), explicit type params
4. Compilation: missing args → read function signatures, update call sites
5. Runtime: numerical → fix overflow (use small inputs), precision (use _set_float64)
6. Runtime: memory → fix use-after-free (explicit copy before move)
7. Runtime: __str__ → implement missing formatting (nested brackets, dtype-aware)
8. Deep bugs → file GitHub issues with RCCA
```

### Common Fixes Reference

```mojo
# Docstring capitalization (--Werror)
"""zeros XOR zeros"""  # FAILS
"""Zeros XOR zeros"""  # PASSES

# Tensor to AnyTensor conversion
layer.forward(input)            # FAILS: Tensor not convertible to AnyTensor
layer.forward(input.as_any())   # PASSES

# Parametric type inference
Sequential2[Linear, ReLU](...)                    # FAILS: can't infer dtype
Sequential2[Linear[DType.float32], ReLU](...)     # PASSES

# Use-after-free prevention
var p = Variable(params[i], True, tape)           # MOVES params[i], invalidates it
var copy = params[i]                               # COPY first
var p = Variable(copy, True, tape)                 # Move the copy, original stays valid

# Numerical overflow prevention
var input = ones([4, 3, 32, 32], DType.float32)   # OVERFLOWS through 13 conv layers
var input = full([4, 3, 32, 32], 0.01, ...)       # Stable through deep networks

# Float16-safe initialization
var max_val = Float32(-1e9)       # OVERFLOWS float16 range [-65504, 65504]
var max_val = Float32(-65504.0)   # Safe for all float types

# Gradient precision
grad_input[idx] = Float32(grad_sum)               # LOSES precision
grad_input._set_float64(idx, Float64(grad_sum))   # Preserves precision
```

### Session Stats

| Metric | Value |
|--------|-------|
| PRs created | 7 (#5063-5076) |
| Issues filed | 6 (#5065-5070) |
| Issues closed | 2 (JIT crashes reopened then properly fixed) |
| Files modified | ~50 |
| Lines changed | +1000, -1500 (net -500) |
| Test groups fixed | 6 of 6 |

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectOdyssey | PRs #5063-#5076 | Systematic triage of 20+ CI failures after AnyTensor refactoring |
