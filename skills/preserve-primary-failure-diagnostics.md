---
name: preserve-primary-failure-diagnostics
description: "Use when an operation fails and its reconciliation probe also fails or times out. Keep the primary failure evidence, add the probe failure as causal context, and keep the result blocked while the remote state is unknown."
category: debugging
date: 2026-09-15
version: "1.0.0"
user-invocable: false
tags: [diagnostics, subprocess, reconciliation, probe, timeout, causality, fail-closed]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/preserve-primary-failure-diagnostics.history"
history-cleanup-date: "2026-09-20"
---

# Preserve Primary Failure Diagnostics

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-09-15 |
| **Objective** | Keep the initial operation evidence when a follow-up state probe also fails. |
| **Outcome** | The caller receives one bounded and redacted causal diagnostic. Unknown state stays blocked. |

## When to Use

- A write, push, publish, or remote operation fails and starts a reconciliation probe.
- The probe can fail because of a timeout, command error, authentication error, runtime error, or operating-system error.
- The probe output can be empty and must not replace useful output from the initial failure.
- A durable result must show both the initial failure and the failed attempt to determine final state.

## Verified Workflow

### Quick Reference

```python
try:
    perform_operation()
except OperationError as operation_error:
    primary = bounded_redacted_diagnostic(operation_error)
    try:
        state = reconcile_state()
    except ProbeError as probe_error:
        raise UnknownOperationState(primary=primary) from probe_error
    handle_reconciled_state(state, primary)
```

### Detailed Steps

1. Capture the initial failure before you start the probe.
2. Redact sensitive data before you apply a size limit or store the diagnostic.
3. Give the probe a bounded deadline.
4. Classify the probe result as confirmed success, confirmed failure, or unknown state.
5. If the probe fails, translate its supported failure types at the probe boundary.
6. Keep the initial output, status, and failure classification in the translated result.
7. Attach the probe exception as the cause. Do not use its empty streams as replacement evidence.
8. Keep publication or the next state-changing action blocked while the final state is unknown.
9. Test timeout, command, authentication, runtime, and operating-system probe failures.
10. Test the complete durable route. Confirm operation order, redaction, and stored diagnostics.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Let the probe exception escape | The reconciliation call ran outside the translation boundary. | The caller saw only the probe failure and lost the initial operation evidence. | Translate probe failures where both failures are available. |
| Catch only probe timeouts | The code handled the exhausted-deadline case only. | Command, authentication, runtime, and operating-system failures still bypassed the diagnostic contract. | Handle the supported probe failure family with one stable policy. |
| Replace the initial streams | The result used stdout and stderr from the last exception. | A probe frequently has empty output, so useful initial evidence disappeared. | Keep the initial diagnostic and add the probe as causal context. |
| Test only the helper | A unit test called the diagnostic constructor directly. | The test did not prove that orchestration and durable storage kept the evidence. | Test the complete failure route through its durable boundary. |

## Results & Parameters

### Required Result Fields

```yaml
operation_state: unknown
action_allowed: false
primary_failure:
  classification: <stable-kind>
  diagnostic: <bounded-redacted-text>
probe_failure:
  classification: <stable-kind>
causal_chain_preserved: true
```

### Expected Output

- The initial failure remains the principal diagnostic.
- The probe failure explains why final state is unknown.
- The system does not retry or publish until a new state check succeeds.
- Durable output contains no sensitive data.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| General automation | A failed publication and failed remote-state probe | Focused failure-route tests and exact-source continuous integration passed. |

## References

- [Python exception chaining](https://docs.python.org/3/reference/simple_stmts.html#the-raise-statement)
- [Subprocess exceptions](https://docs.python.org/3/library/subprocess.html#exceptions)
- [Fail-Closed JSON Result Validation](tooling-subprocess-json-fail-closed-result-validation.md)
