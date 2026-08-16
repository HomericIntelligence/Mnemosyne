---
name: automation-loop-explicit-scope-drain
license: BSD-3-Clause
description: "Keep queue-pipeline loop re-seeding limited to discovery. Use when an automation loop accepts explicit --issues or --prs selections, when a reviewed or merged item reappears after a full drain, or when writing regression tests for loop admission and retry boundaries."
category: tooling
date: 2026-08-05
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - automation-loop
  - queue-pipeline
  - explicit-scope
  - reseeding
  - convergence
  - review-path
  - merge-path
---

# Automation Loop Explicit-Scope Drain

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-05 |
| **Objective** | Prevent a fully drained queue from recreating operator-selected issue or PR cursors on later configured loops. |
| **Outcome** | Successful — explicit issue and PR selections drain once; unscoped repository/organization discovery retains multi-loop re-seeding. |
| **Verification** | verified-ci — ProjectHephaestus issue #2638 / PR #2639 merged with focused tests, static checks, and the full pre-push suite green. |

## When to Use

- A coordinator supports both explicit `--issues`/`--prs` input and unscoped repository or organization discovery.
- A selected issue or PR reappears after its queue pass has fully drained, causing duplicate review or merge-path work.
- The outer loop is being used for discovery, but stage-local retries and fail-backs already own implementation or review retries.
- Adding regression coverage for the distinction between finite operator scope and replenishable discovery scope.

## Verified Workflow

### Quick Reference

```python
def _reseed_if_converged(self) -> bool:
    # Explicit selections are finite operator scope; their queues own retries.
    if self.config.issues or self.config.prs:
        logger.info("explicit issue/PR selection drained; skipping discovery re-seed")
        return False

    if self._loops_run >= self.config.loops:
        return False
    return self._seed_pass() > 0
```

### Detailed Steps

1. Decide whether the run is explicit or discovery-scoped at the coordinator configuration boundary.
2. After a full drain, stop immediately for either non-empty `issues` or non-empty `prs`; do not recreate their cursors.
3. Keep multi-loop re-seeding only for unscoped discovery, subject to the configured loop budget and zero-work convergence behavior.
4. Leave retry and fail-back behavior to the individual stage queues. The outer loop should not turn a completed review or merge-path item into a new admission.
5. Parameterize tests over one explicit issue selection and one explicit PR selection. Patch `_seed_pass` to fail if called, then assert the coordinator stops after one loop with one ledger entry.
6. Verify the merged change with focused tests, architecture tests, type checks, Ruff, formatting, and the repository's full pre-push suite.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | Re-seed every fully drained pass whenever `--loops` remained. | An explicit issue was classified and completed once per configured loop, duplicating work and ledger entries. | `--loops` is a discovery budget, not permission to recreate finite operator selections. |
| 2 | Regression-test only the direct issue path. | The same cursor-recreation bug also applies to explicit PR selections. | Test both explicit selection kinds through one shared guard. |

## Results & Parameters

| Scope | `loops` | Expected result |
|-------|---------|-----------------|
| `issues=[101]`, `prs=[]` | `2` | One pass; `_seed_pass` is not called after drain. |
| `issues=[]`, `prs=[701]` | `2` | One pass; `_seed_pass` is not called after drain. |
| Unscoped `org`/`repos` discovery | `N` | Re-seeding remains available up to the loop budget. |

Focused verification used by ProjectHephaestus PR #2639:

```bash
uv run pytest tests/unit/automation/pipeline/test_backpressure_seeding.py -q --no-cov
uv run pytest tests/unit/automation/test_automation_hotspot_architecture.py -q --no-cov
uv run mypy hephaestus/automation/pipeline/coordinator_sources.py \
  hephaestus/automation/pipeline/coordinator_types.py \
  tests/unit/automation/pipeline/test_backpressure_seeding.py
uv run ruff check hephaestus/automation/pipeline/coordinator_sources.py \
  hephaestus/automation/pipeline/coordinator_types.py \
  tests/unit/automation/pipeline/test_backpressure_seeding.py
uv run ruff format --check hephaestus/automation/pipeline/coordinator_sources.py \
  hephaestus/automation/pipeline/coordinator_types.py \
  tests/unit/automation/pipeline/test_backpressure_seeding.py
```

The full pre-push suite reported 7,156 passed, 11 skipped, and 5 deselected with 83.77% coverage. The fix merged as ProjectHephaestus PR #2639 (commit `446b0fe`; source commit `b46f0b0`).

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #2638 / PR #2639 | Explicit issue and PR selections no longer re-seed after a full drain; discovery loops remain supported. |
