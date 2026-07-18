---
name: ci-cd-stage-shared-backoff-cap-constant
description: "Use when: (1) legacy poll backoff caps are duplicated across CI pipeline stages, (2) stage-local literals drift from a shared base constant, (3) you need a base-level invariant test tying consumer modules back to the shared export."
category: ci-cd
date: 2026-07-07
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - ci
  - pipeline
  - backoff
  - constant
  - base
  - invariant
  - regression
  - tests
---

# CI/CD Stage Shared Backoff Cap Constant

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-07 |
| **Objective** | Pin the shared backoff-cap invariant by centralizing the legacy poll cap in `stages/base.py` and proving every consumer re-exports the same value |
| **Outcome** | Successful — `BACKOFF_CAP_S = 60` moved to `base.py`, `ci.py` and `merge_wait.py` import/re-export it, and a base-level regression test now locks the shared constant relationship |
| **Verification** | verified-ci |

## When to Use

- A pipeline stage copies a legacy poll/backoff cap literal into more than one module
- `ci.py`, `merge_wait.py`, or similar stage modules are drifting from a shared base value
- You need a test that proves the base module is the single source of truth for a stage constant
- A review flags duplicated timer/backoff constants that should be hoisted into a common stage base

## Verified Workflow

### Quick Reference

```bash
# Centralize the literal in the stage base and import it from each consumer.
# Then verify the invariant across base + consumers.
python3 -m pytest \
  tests/unit/automation/pipeline/stages/test_stage_base.py \
  tests/unit/automation/pipeline/stages/test_stage_ci.py \
  tests/unit/automation/pipeline/stages/test_stage_merge_wait.py \
  --no-cov -q
# expected: 86 passed
```

### Detailed Steps

1. **Hoist the shared literal into `stages/base.py`.** Keep the legacy cap in one place:

   ```python
   BACKOFF_CAP_S = 60
   ```

2. **Re-export or import the shared constant from each consumer.** `ci.py` and `merge_wait.py`
   should no longer own their own copy of the value.

3. **Add a base-level invariant test.** Assert that the base module and both consumers all expose
   the same constant:

   ```python
   assert base.BACKOFF_CAP_S == ci.BACKOFF_CAP_S == merge_wait.BACKOFF_CAP_S
   ```

4. **Keep the delay formula anchored to the shared cap.** The poll delay should continue to clamp
   against the shared constant:

   ```python
   delay = min(2 ** polls, BACKOFF_CAP_S)
   ```

5. **Run the targeted stage tests.** The source repo verification passed with the three stage test
   files below and no coverage collection:

   ```bash
   python3 -m pytest \
     tests/unit/automation/pipeline/stages/test_stage_base.py \
     tests/unit/automation/pipeline/stages/test_stage_ci.py \
     tests/unit/automation/pipeline/stages/test_stage_merge_wait.py \
     --no-cov -q
   ```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Leave `BACKOFF_CAP_S = 60` duplicated in `ci.py` and `merge_wait.py` | Kept the legacy literal in both stage modules | The cap could drift silently across stages, so CI risk stayed distributed instead of centralized | Hoist the value into `stages/base.py` and make the consumers import it |
| Rely only on stage-specific tests | Verified `ci.py` and `merge_wait.py` behavior without a base-level equality assertion | The modules could still diverge while their local tests stayed green | Add a base test that ties `base.BACKOFF_CAP_S`, `ci.BACKOFF_CAP_S`, and `merge_wait.BACKOFF_CAP_S` together |

## Results & Parameters

**Central source of truth**

```python
# hephaestus/automation/pipeline/stages/base.py
BACKOFF_CAP_S = 60
```

**Consumer pattern**

```python
# hephaestus/automation/pipeline/stages/ci.py
from .base import BACKOFF_CAP_S

# hephaestus/automation/pipeline/stages/merge_wait.py
from .base import BACKOFF_CAP_S
```

**Invariant test**

```python
assert base.BACKOFF_CAP_S == ci.BACKOFF_CAP_S == merge_wait.BACKOFF_CAP_S
```

**Behavioral parameter**

- `delay = min(2 ** polls, BACKOFF_CAP_S)`
- `BACKOFF_CAP_S = 60`
- The shared constant is the single source of truth for the legacy poll backoff cap

**Verified result**

- Targeted verification passed in the source repo:

  ```bash
  python3 -m pytest \
    tests/unit/automation/pipeline/stages/test_stage_base.py \
    tests/unit/automation/pipeline/stages/test_stage_ci.py \
    tests/unit/automation/pipeline/stages/test_stage_merge_wait.py \
    --no-cov -q
  ```

- Result: `86 passed`

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1918 / PR #1996 | Shared legacy poll backoff cap centralized from `ci.py` and `merge_wait.py` into `stages/base.py`; regression test asserts `base.BACKOFF_CAP_S == ci.BACKOFF_CAP_S == merge_wait.BACKOFF_CAP_S` |
