---
name: background-lane-timeout-artifact-reconcile
description: "Reconcile a background planning or review lane that timed out while its artifact state was unknown. Use when a lane may have partially written to a shared delivery surface, when the final result was never reported, or when a replacement worker must avoid duplicating the original work."
category: tooling
date: 2026-11-15
version: "1.0.0"
user-invocable: false
verification: verified-local
license: BSD-3-Clause
tags:
  - background-agent
  - timeout-recovery
  - partial-write
  - artifact-reconciliation
  - bounded-resume
  - agent-orchestration
---

# Background Lane Timeout Artifact Reconcile

## Overview

| Field | Value |
| ----- | ----- |
| **Date** | 2026-11-15 |
| **Objective** | Recover a timed-out planning or review lane without duplicating its artifacts or re-running unrelated discovery. |
| **Outcome** | Operational. The coordinator reconciled unknown write state from live evidence, reused the bounded saved evidence, and resumed the failed work with one item per replacement lane. |

## When to Use

Use this entry when:

- A background planning, review, or other orchestration lane ended in a timeout rather than a final report.
- The lane may already have created, edited, or published one or more coordination artifacts.
- You cannot tell from the worker output alone whether the write reached the delivery surface.
- A replacement lane is about to be dispatched and could duplicate the work.
- A later attempt will use a bounded item scope, not a full re-discovery of the whole program.

## Verified Workflow

### Quick Reference

Treat a timeout as unknown write state, not as zero work:

1. Freeze the saved evidence and name the exact work item.
2. Read the live target state.
3. Compare the live artifact identity with the prepared artifact identity.
4. Classify the state.
5. Resume only the missing work, with one work item per lane.
6. Read back the result before you report it.

### Suggested Approach

1. **Stop before you relaunch.**
   A timeout is an unobserved terminal state. The worker may have failed before the first
   write, or after one or more durable writes. A blind replacement can create a duplicate
   coordination artifact.

2. **Preserve the bounded evidence you already have.**
   Keep the saved snapshot of the target state, prepared artifacts, expected identifiers,
   and the exact resume brief. Do not re-derive a broad context from scratch unless the
   saved evidence cannot be trusted.

3. **Read the live effect surface, not the worker's memory.**
   For each expected artifact, read the live target and compare it with the prepared
   content by identity and digest. Presence, absence, and drift are facts; the lost
   response is not.

4. **Classify before you write.**

   | Observed state | Meaning | Action |
   | -------------- | ------- | ------ |
   | The expected artifact is present and byte-identical to the prepared bytes | Already delivered | Report completion from state evidence; do not write again. |
   | Some expected artifacts are present and the rest are missing | Partial delivery | Resume only the missing artifacts from the saved evidence. |
   | The target has drifted from the saved precondition | Rebind required | Refresh only the affected bindings and prepare the missing delta. |
   | The live state is inconsistent or identity cannot be resolved | Unsafe to write | Stop and report both hypotheses with the readback evidence. |

5. **Resume one work item per replacement lane.**
   When timeouts were caused by parallel load or long context, give the replacement lane
   one item, one bounded evidence set, and one write target. A second multi-item lane can
   reproduce the same timeout and broaden the damage.

6. **Guard the retry.**
   Before each write, re-read the target and compare its identity with the prepared
   operation. After the write, read the result back. If the readback differs from the
   prepared bytes, stop and preserve the evidence; do not create a second artifact.

7. **Report the limit honestly.**
   A lane that completed through reconciliation has no lost completion message. Record that
   the original terminal status was unobserved and that the delivery is proven by live
   state, not by worker prose.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Treat a timeout as a clean failure | Re-dispatched the same broad lane after the worker reported a timeout | The lane may have partially written before the timeout, so the replacement could duplicate a durable artifact | Classify the live state first; resume only the gap |
| Resume the whole program | Rebuilt the original broad context and re-read unrelated material | It repeated expensive discovery and gave the replacement lane a longer, more timeout-prone context | Keep the resume brief to one item and one evidence set |
| Trust the worker's final prose | Interpreted the last message as proof that work did or did not happen | A timeout has no reliable final report; prose cannot reveal a partial write | Use live state and prepared bytes as the evidence |
| Run replacements at the same fan-out | Dispatched several replacement lanes at once after the original fan-out timed out | The same parallel load could reproduce the same failure | Use one item per lane until the failed item reaches a stable boundary |

## Results & Parameters

### Configuration

```yaml
reconciliation:
  unknown_write_state: timeout
  evidence_scope: one work item
  live_probe: exact target identity and digest
  prepared_source: immutable saved artifact bytes
  classification:
    exact-match: already-delivered
    partial-match: resume-missing-artifacts-only
    drifted-target: rebind-affected-artifacts
    inconsistent-or-unresolved: stop-and-report
resume_scope:
  items_per_lane: 1
  context: saved bounded evidence, not full re-discovery
  retry_guard: live target identity before every write
  readback: exact result after every write
fanout:
  first_recovery: one item per lane
  broadened_fanout: only after the failed item reaches a stable boundary
```

### Expected Output

- No duplicate coordination artifact is created for already-delivered work.
- Missing work is resumed from a bounded evidence set, not from a broad re-discovery.
- A partial or unknown result is recorded as a limit, not as a silent success.
- The replacement lane's scope is one item and one write target.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| A multi-item planning and review wave on a shared delivery forge | Several background lanes timed out with unknown write state; live-state reconciliation prevented duplicate artifacts, and one-item replacement lanes completed the failed work | Generalized evidence in [notes](background-lane-timeout-artifact-reconcile.notes.md). |

## References

- [Verify a completion report against the forge](verify-completion-report-against-forge.md) — applies after a lane reports completion with artifact identifiers.
- [Reconcile before retry after mutation status loss](reconcile-before-retry-mutation-status-loss.md) — the general unknown-mutation decision table.
- [Relaunch salvage for an interrupted automation loop](interrupted-automation-loop-relaunch-salvage.md) — salvage of isolated worker worktrees after loop death.
- [Background agent failure detection and recovery](agent-background-task-failure-recovery.md) — dispatch and admission failures that leave no in-flight artifact.
