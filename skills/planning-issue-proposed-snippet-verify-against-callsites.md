---
name: planning-issue-proposed-snippet-verify-against-callsites
description: "An issue's PROPOSED solution code (a 'Proposed Solution' snippet, a suggested signature, a sketch of the new API) is a HYPOTHESIS to verify, NOT a spec to transcribe — before adopting it, grep the issue's own premise tokens to enumerate EVERY real call site and READ each one to recover the contract the snippet must satisfy. The proposed snippet is frequently subtly wrong because the issue author sketched it without auditing all consumers. The sharpest failure mode: a proposed CONTEXT MANAGER (or decorator/wrapper) that cannot express a CALLER-SPECIFIC control-flow obligation the real sites require — e.g. `acquire_slot()` returns `int | None` and every worker does `if slot_id is None: return WorkerResult(success=False, ...)` BEFORE its try-block, but a context manager cannot `return` a domain object on the caller's behalf, so a CM that `yield`s an unconditionally-acquired id either raises on the None branch or silently drops the early-return semantics. The fix pattern: have the CM yield the nullable value (`int | None`) and KEEP each caller's `if x is None: return <DomainResult>` guard INSIDE the `with`, so the CM owns only resource release (idempotent on None). Also: preserve per-site `finally` side effects that are NOT part of the resource lifecycle (e.g. a `time.sleep(1)` throttle) by leaving them in the caller, not folding them into the wrapper. Use when: (1) planning from an issue that ships a 'Proposed Solution' / 'Proposed API' code block, (2) the proposal is a context manager, decorator, base-class method, or helper that wraps an existing acquire/release or try/finally pattern, (3) the wrapped primitive can fail/return None/raise and callers branch on that, (4) callers return DIFFERENT domain types (WorkerResult vs PlanResult) on the failure path, (5) the issue claims 'low risk — wraps existing API' (that phrasing is a smell to audit, not a reason to skip auditing), (6) some call sites carry extra `finally` work beyond the resource release."
category: architecture
date: 2026-06-30
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - planning-methodology
  - issue-proposed-snippet
  - verify-against-callsites
  - context-manager
  - caller-early-return
  - nullable-acquire
  - resource-lifecycle
  - dry-refactor
  - python
---

# Planning: Verify an Issue's Proposed Snippet Against Every Call Site

> **Warning:** This skill is planning-only and **unverified** — it was captured from producing an implementation plan (ProjectHephaestus #1437) that was NOT implemented at capture time. Treat the "Workflow" as a hypothesis until an implementation + CI confirm it.

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-30 |
| **Objective** | When an issue includes a proposed code snippet, decide whether to adopt it by reconciling it against the real call sites rather than transcribing it |
| **Outcome** | Plan correctly identified that the issue's proposed `slot()` context manager was wrong for the codebase and specified a corrected design |
| **Verification** | unverified (planning-only; no code/tests/CI executed) |

## When to Use

- Planning from an issue whose body contains a **"Proposed Solution"** / **"Proposed API"** code block.
- The proposal is a **context manager, decorator, base-class method, or helper** that wraps an existing acquire/release or `try/finally` lifecycle.
- The wrapped primitive can **return `None` / raise / fail**, and callers branch on that result.
- Different callers return **different domain types** on the failure path (e.g. `WorkerResult` vs `PlanResult`).
- The issue says **"low risk — wraps existing API"** (treat as a prompt to audit, not a license to skip auditing).
- Some call sites carry **extra `finally` work** beyond the resource release (throttles, logging, cleanup).

## Verified Workflow

> (Planning-only; titled "Workflow" because the plan was produced but not implemented. Confidence: unverified.)

### Quick Reference

```bash
# 1. Enumerate EVERY call site using the issue's OWN premise tokens (not incidental ones).
grep -rn "acquire_slot\|release_slot" hephaestus/ --include="*.py"

# 2. READ each acquire site fully — recover the contract the wrapper must satisfy.
#    Look specifically for control flow the wrapper cannot express:
grep -n "if slot_id is None\|if .* is None: *$" hephaestus/automation/*.py

# 3. Confirm the wrapped primitive's nullability/raise behavior at the source.
sed -n '31,67p' hephaestus/automation/status_tracker.py   # acquire_slot -> int | None; release_slot guards range
```

### Detailed Steps

1. **Treat the proposed snippet as a hypothesis.** Quote it, then ask: "What must every real caller do that this snippet does not let it do?"
2. **Grep the issue's own premise tokens** (the function names the issue names — `acquire_slot`/`release_slot`), not incidental tokens, to enumerate ALL call sites. Under-enumeration is the classic NOGO.
3. **Read each call site** and extract the *shared contract*. In #1437 the contract was: on acquisition failure (`acquire_slot()` returns `None`), the caller returns a **caller-specific domain object** (`WorkerResult` / `PlanResult`) *before* doing any work.
4. **Test the proposal against the contract.** A context manager runs `__enter__` → `yield` → `__exit__`; it cannot make the caller `return`. So a CM that `yield`s an unconditionally-acquired id breaks the `None`-early-return that every caller needs.
5. **Specify the corrected design.** Have the CM yield the nullable value (`int | None`); keep each caller's `if x is None: return <DomainResult>` guard *inside* the `with`; the CM owns only release, guarded to be a no-op on `None` (`if slot_id is not None: self.release_slot(slot_id)`).
6. **Preserve non-lifecycle `finally` side effects in the caller.** Two sites had `time.sleep(1)` in `finally` before the release — that throttle is not part of the slot lifecycle, so it stays in the caller (as an inner `try/finally` that no longer releases), not folded into the wrapper.
7. **Write the plan stating the decision, not the options** — "the proposed snippet is wrong because X; the corrected design is Y," with `file:line` evidence for each real call site.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Adopt the issue's `slot()` body verbatim | The issue proposed `slot_id = self.acquire_slot(); ... yield slot_id` then `finally: self.release_slot(slot_id)` | `acquire_slot()` returns `int | None`; on `None` every caller must `return` a domain object first — a CM cannot return on the caller's behalf, and `release_slot(None)` would hit a `None < int` `TypeError` without a guard | A proposed wrapper that hides a fallible acquire silently drops the callers' early-return semantics; yield the nullable and keep the guard in the caller |
| Fold every `finally` into the wrapper | Assume all 5 sites only release in `finally` | 2 sites also `time.sleep(1)` in `finally` (a rate-limit throttle), unrelated to the slot lifecycle | Audit each `finally` body; keep non-lifecycle side effects in the caller, move only the resource release into the wrapper |
| Trust "low risk — wraps existing API" | Take the issue's risk self-assessment at face value | The "wraps existing API" framing concealed a control-flow mismatch across 5 callers | The issue author's risk label is a claim; the audit is the evidence |

## Results & Parameters

Corrected design that satisfies all 5 call sites (ProjectHephaestus #1437):

```python
from collections.abc import Iterator
from contextlib import contextmanager

@contextmanager
def slot(self, initial_msg: str = "", timeout: float | None = None) -> Iterator[int | None]:
    """Acquire a slot for the with-block, then release it. Yields None on timeout.

    The caller MUST handle the None case (e.g. return a failure result);
    the slot is released automatically on block exit, including on exception.
    """
    slot_id = self.acquire_slot(timeout=timeout)
    try:
        if slot_id is not None and initial_msg:
            self.update_slot(slot_id, initial_msg)
        yield slot_id
    finally:
        if slot_id is not None:        # release is a no-op / guarded on None
            self.release_slot(slot_id)
```

Caller pattern (every one of the 5 sites keeps its own early-return type):

```python
with self.status_tracker.slot() as slot_id:
    if slot_id is None:
        return WorkerResult(issue_number=issue_number, success=False,
                            error="Failed to acquire worker slot")
    try:
        ...  # work
    finally:
        time.sleep(1)   # non-lifecycle throttle stays in caller; release owned by slot()
```

Call-site inventory (the audit output that drove the design):

| Site | Failure-path return type |
| ----- | -------------------------- |
| `pr_reviewer.py:649` | `WorkerResult` (+ `time.sleep(1)` in `finally`) |
| `address_review.py:654` | `WorkerResult` (+ `time.sleep(1)` in `finally`) |
| `planner.py:233` | `PlanResult` |
| `plan_reviewer.py:173` | `WorkerResult` |
| `ci_driver.py:733` | `WorkerResult` |

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectHephaestus | Issue #1437 — `slot()` context manager for `StatusTracker` | Planning-only; plan specified the corrected yield-nullable design after auditing all 5 acquire sites |
