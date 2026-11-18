---
name: unbounded-request-diagnostic-timeouts
license: BSD-3-Clause
description: "Scope an intentionally unbounded primary request to named operations while diagnostic and revalidation requests retain independent finite deadlines. Use when removing a timeout from one external request, threading a nullable timeout through helper and error paths, or reviewing probes that can inherit the primary wait policy."
category: architecture
date: 2026-11-17
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - timeout
  - unbounded-request
  - diagnostic-probe
  - revalidation
  - remaining-budget
  - error-path
  - regression-test
---

# Unbounded Primary Request, Bounded Diagnostic Requests

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-17 |
| **Objective** | Let a slow primary operation answer without a fixed timeout while every auxiliary request keeps its intended deadline policy. |
| **Outcome** | Operational. A transport-level review found an unbounded timeout on an inventory diagnostic after the primary control became unbounded. A per-operation timeout boundary and an error-path regression corrected the defect. Focused tests, full repository checks, and independent review passed. Live non-strict generation passed for every dynamically discovered model, and strict runs retained their documented failure contract. |
| **Verification** | verified-live for the source implementation and its regression evidence. |

## When to Use

- A requirement removes the fixed timeout from a readiness, capability, or other primary external request so a slow endpoint can answer.
- A nullable timeout or remaining-budget value flows through shared helpers, fallback requests, error classification, or reconciliation probes.
- Discovery, inventory, route, or state revalidation must stay bounded even when the primary operation can wait indefinitely.
- A test covers the primary success path but does not record the timeout used by requests on an error path.

Do not use this entry to size guardians around one finite total request arbiter. Use [Timeout Hierarchy: One Arbiter Plus Margin Steps](timeout-hierarchy-arbiter-margin-ladder.md) for that decision. Use [Preserve Primary Failure Diagnostics](preserve-primary-failure-diagnostics.md) when the main problem is failure evidence and unknown remote state.

## Verified Workflow

### Quick Reference

Treat an unbounded timeout as a property of a named operation, not as a property of every request that the operation can reach.

```python
def diagnostic_timeout(primary_timeout, remaining_budget):
    if primary_timeout is None:
        return DEFAULT_DIAGNOSTIC_TIMEOUT
    return remaining_budget
```

- Pass the unbounded sentinel only to operations whose contracts explicitly permit it.
- Map that sentinel to the existing finite default at each bounded diagnostic boundary.
- Preserve an explicit caller's remaining budget, including an expired budget. Do not give that caller a new full timeout.
- Record the real transport timeout for primary and diagnostic requests in one error-path regression.

### Suggested Approach

1. **Confirm that an unbounded wait is intentional.** A slow valid response can justify removing a cap only when the operation's contract permits indefinite waiting. Keep a finite deadline when no such requirement exists. Do not extend the exception to runtime requests, discovery, or diagnostics by default.

2. **Inventory the complete request graph.** Start at the changed API and follow its timeout through success, fallback, error-classification, reconciliation, and cleanup paths. Classify each outbound request as an allowed unbounded primary operation, an independently allowed unbounded operation, or a bounded auxiliary operation. Direct transport call sites alone do not show values inherited through helpers.

3. **Rebind the policy at each auxiliary boundary.** When the primary timeout is `None`, supply the auxiliary operation's established finite default. When the caller supplied a finite timeout, pass the unspent remainder instead. This distinction preserves both the new unbounded-primary contract and the old explicit-deadline contract. Make remaining-budget helpers and expiry guards `None`-safe before arithmetic or comparison. Document any auxiliary operation that is intentionally unbounded as a separate exception.

4. **Verify the transport's sentinel semantics.** For the actual HTTP or process transport, prove that `None` means no fixed timeout rather than an error or a hidden library default. A delayed local test server can establish this behavior without a live service. Do not generalize one library's semantics to another transport.

5. **Force the diagnostic path in a regression.** Use a transport fake that records `(operation, timeout)` for every call. Make the primary requests fail with the response that triggers diagnostic revalidation. Assert that the primary observations are nonempty and unbounded, the diagnostic observations are nonempty and finite, and explicit-budget tests retain their prior deadline behavior. A signature-only assertion cannot prove this propagation contract. Removing the sentinel-to-default mapping must make the regression fail.

6. **Align documentation and live evidence.** State the timeout policy by operation class. Exercise a slow primary request and the diagnostic error path, then run the focused and repository-level checks. Keep credentials and endpoint identities out of published evidence.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | --------------- | --------------- | ---------------- |
| Remove the cap through a shared default | Changed the primary helper's default timeout to `None` and let existing helpers forward it | Error handling also forwarded `None` to an inventory diagnostic, so an unresponsive diagnostic could wait indefinitely | Trace the value through error paths and rebind it at each operation boundary |
| Test only the primary control | Asserted that the primary request received `None` and that discovery signatures retained a finite default | The test did not execute the diagnostic path that inherited the primary value | Record every transport call in a forced error-path regression and require nonempty observations for each request class |
| Compare a nullable budget with zero directly | Widened the timeout type to include `None` but left `timeout <= 0` in a route-confirmation guard | Existing route tests failed on the new default path before the auxiliary-timeout repair was complete | Make expiry guards `None`-safe while preserving explicit expired-deadline behavior |

## Results & Parameters

### Configuration

| Operation class | Required timeout policy |
| --------------- | ----------------------- |
| Named primary operation whose contract permits an unbounded wait | `None` or the transport's verified unbounded sentinel |
| Discovery, inventory, and other bounded diagnostics | Their established finite default when the primary value is unbounded |
| Auxiliary operation with an independent unbounded contract | Unbounded only when that exception is explicit and tested |
| Explicit finite caller budget | The unspent remainder, including the existing expired-deadline behavior |
| Runtime attempts and total deadlines | Unchanged unless their own requirements change |

### Expected Output

- The transport trace shows the unbounded sentinel only on the operations named by the contract.
- The same trace shows a finite timeout on every bounded diagnostic call.
- Explicit-timeout callers retain their remaining-budget behavior.
- A regression that removes the diagnostic mapping fails on the diagnostic timeout observation.
- Documentation names the bounded and unbounded operation classes without claiming that the whole workflow is unbounded.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| A provider-neutral model-evaluation client | Slow primary capability requests and bounded inventory revalidation after primary failure | Generalized source evidence and verification limits are in [notes](unbounded-request-diagnostic-timeouts.notes.md). |

## References

- [Timeout Hierarchy: One Arbiter Plus Margin Steps](timeout-hierarchy-arbiter-margin-ladder.md) — use for finite nested request budgets and guardian margins.
- [External Request Boundary Invariants](external-request-boundary-invariants.md) — use for provider accounting, per-attempt deadlines, and response commit boundaries.
- [Preserve Primary Failure Diagnostics](preserve-primary-failure-diagnostics.md) — use for bounded reconciliation probes and preserved failure causality.
- [Non-Vacuous Regression Guards](testing-non-vacuous-regression-guards-behavior-unchanged.md) — use mutation checks to prove that a regression can fail.
