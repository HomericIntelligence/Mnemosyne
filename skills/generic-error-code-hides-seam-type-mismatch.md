---
name: generic-error-code-hides-seam-type-mismatch
license: BSD-3-Clause
description: "Recover the real exception behind one generic domain error code from an adapter that wraps a callee with 'except Exception'. Use when every internal failure reports as the same code, an isolated child-process reproduction of the far side succeeds, and the broken part is the type of the object passed across the seam, not the child."
category: debugging
date: 2026-10-30
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - adapter-seam
  - generic-error
  - fail-closed
  - exception-cause
  - type-mismatch
  - subprocess-worker
  - isolation-reproduction
  - trust-boundary
  - bytes-vs-str
  - debugging
---

# A Generic Error Code Can Hide a Type Mismatch at an Adapter Seam

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-10-30 |
| **Objective** | Find the root cause when a whole test group fails with one generic domain error code and no exception text. |
| **Outcome** | The adapter that calls the restricted worker wrapped every internal failure with `except Exception: raise DomainError(GENERIC)`. The real defect was on the caller side of the seam: the verifier returned a raw verified object (byte fields), while the worker entry expected a sealed object (decoded text fields). A child-process reproduction of the worker with the exact frame succeeded, which proved the child innocent and pointed at the seam. An in-harness probe of the seam call surfaced `AttributeError` on the missing method, and the fix was to seal the verified inputs once at the boundary. |

## When to Use

- One error code reports every internal failure of a wrapped callee, and tests or logs show no exception text.
- A reproduction of the far side (child process, worker, external tool) with the exact serialized input succeeds.
- The code between the wrapper and the callee changed recently, or the wrapper's parameter type is a different class from the object the caller actually holds.
- You are about to patch the far side (the child) because it is the part you can see, while the failures do not change.

## Verified Workflow

1. Read the wrapper first. Find the `except Exception` (or equivalent) that folds internal failures into the generic code. Note what it destroys: the exception class, message, and cause.

2. Check the cause chain in a probe before patching anything:

```python
try:
    wrapper_call()
except DomainError as error:
    print(repr(error.__cause__))   # the folded original exception
```

3. Reproduce the far side in isolation with the exact serialized input. If the child or worker answers correctly, the far side is innocent; stop patching it.

4. Probe the seam call directly. Print `repr()` of each argument at the call site and compare each with the callee's declared parameter type. A mismatch here (raw object passed where the sealed or decoded form is required) raises inside the wrapper and reappears as the generic code.

5. Fix at the seam. Convert once, where the types meet: add a seal or decode step that accepts the verified form, or type the wrapper's parameter as the verified form. Do not convert in both the caller and the callee.

6. Restore operator reachability. A restricted child that discards its stderr makes every future failure undebuggable. Capture the child's stderr in the parent (or log the cause server-side behind the security boundary) so the next mismatch is one lookup, not one investigation.

### Quick Reference

```python
# Innocent far side? Reproduce it exactly, in isolation.
run_child(payload)                       # succeeds -> child is not the defect
# Broken near side? Probe the seam.
print(repr(arg), type(arg))              # VerifiedInputs, not SealedInputs
# Fix once, where the types meet.
decision = worker(request=request, sealed=Sealed.from_verified(verified))
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| 1 | Patch the child for a suspected serialization change before any reproduction | The failures did not change; the child was never reached, because the wrapper raised before the child spawned | Prove which side of the seam raises before patching either side |
| 2 | Reproduce the child body with the exact frame and stderr visible | The child succeeded and returned a valid reply, so the reproduction excluded the defect | A green isolated reproduction is evidence about the far side only; the seam remains untested |
| 3 | Trust the generic error surface and re-read the wrapper's logic for the defect | The wrapper's own code was correct; the defect was the argument type two frames away | Fold the cause into the probe, not the patch: `__cause__` names the true defect |

## Results & Parameters

- Symptom signature: every test in one group fails with the same generic code; the isolated child reproduction is green; the wrapper's `except Exception` is the only place the real exception touches.
- Probe sequence that found it: cause-chain print, far-side reproduction, seam-call probe with `repr()` of the arguments.
- Root cause shape: a verifier that returns raw bytes fed to an entry point typed for decoded text; the sealed form exists but nothing produced it at the boundary.
- Fix shape: one seal step at the boundary, accepted by both the in-process and worker paths; no change to the child.
- Verification: verified-local; the failing group went green after the seam fix, with lint and type checks clean.
