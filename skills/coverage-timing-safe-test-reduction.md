---
name: coverage-timing-safe-test-reduction
description: Diagnose coverage instrumentation that perturbs wall-clock-sensitive tests, define minimal disclosed measurement exclusions, and prove that test deletions or relocations lose no executed lines or branch arcs under symmetric baseline and candidate measurement.
category: testing
date: 2026-11-18
version: 1.0.0
user-invocable: false
tags:
  - coverage
  - test-reduction
  - timing-sensitive-tests
  - baseline-parity
  - branch-coverage
---

# Coverage-Timing-Safe Test Reduction

## Overview

| Field | Value |
| --- | --- |
| Date | 2026-11-18 |
| Objective | Reduce test execution without losing behavior evidence when coverage tracing changes real-time behavior. |
| Outcome | A minimal disclosed measurement boundary, symmetric executed-line and branch-arc comparison, and a final uninstrumented behavior gate. |

## When to Use

Use this skill when:

- line or branch tracing makes a test exceed a real-time deadline, lease, timeout, or assertion window;
- more than one test fails or approaches a limit on the same instrumented path;
- a test deletion, relocation, or consolidation needs coverage-no-loss evidence rather than test-count parity;
- a relocated test leaves the instrumented suite inventory and needs separate candidate coverage;
- a measurement exclusion must leave collection, execution, assertions, and cleanup intact.

Do not use this skill to:

- calculate only an aggregate coverage threshold;
- profile runtime when instrumentation does not change behavior;
- weaken a production timing contract or a test assertion to make measurement pass; or
- replace the final uninstrumented qualification run.

## Verified Workflow

### 1. Bind the behavior and measurement scopes

Record the baseline and candidate revisions, exact test-node inventory, test placements, coverage source scope, tracer, branch mode, context mode, report format, and run identities.

Use executed source lines and executed branch arcs as set-valued evidence. Do not substitute test counts, aggregate percentages, or missing-line unions for these sets.

Keep a disposition ledger for each removed node: retain, delete with justification, or relocate to an exact replacement node. Require every retained node exactly once in the final behavior gate.

### 2. Diagnose the timing interaction before excluding calls

Reproduce the slowdown with the intended instrumentation. Inspect the failing assertion, the real-time contract, and the shared execution path. Compare durations across the complete behavior family, not only the first failure.

Group nodes by evidence that they reach the same timing-sensitive operation. A duration threshold alone is not a behavior boundary. Keep related lower-risk cases traced when they do not share that operation or remain comfortably within their deadline.

If another node needs an exclusion after the first correction, stop and diagnose the family again. Do not add exclusions one failure at a time.

### 3. Select the smallest symmetric measurement boundary

Use the same tracer and branch configuration for baseline and candidate. Do not replace branch tracing with a faster core that cannot produce equivalent branch arcs.

When call tracing itself breaks the behavior, pause tracing only for the exact evidenced test calls. Apply the exclusion to call-phase subprocess tracing as well when the tracer inherits it. Continue to measure setup and teardown. Collection, execution, assertions, phase accounting, and cleanup must still occur.

Publish an exclusion manifest for every measurement shard or worker. Bind each manifest to the source revision, run, instrumentation identity, phase, and subprocess setting. Require every excluded node exactly once across the complete run and no unlisted exclusion.

Stop the design if an excluded test still fails or a node outside the evidenced boundary needs exclusion. Do not widen the boundary automatically.

### 4. Collect a fresh baseline

Run the complete baseline with the selected instrumentation and exclusions. Require the exact inventory, all behavior checks green, cleanup complete, aggregate acceptance, phase records, and coverage artifacts.

Do not stitch shards, durations, or coverage from failed diagnostic runs into an accepted baseline. Derive comparison evidence and planning durations only from the accepted run.

### 5. Measure the candidate under the same contract

Apply the approved test changes without changing production behavior or test assertions. Keep the baseline instrumentation and exclusion set unchanged.

Keep a deleted test fully measured in the baseline. Measure each relocated test in its original baseline location and its replacement candidate location. If the replacement is outside the instrumented gate inventory, run separate candidate auxiliary coverage with its own data file, report, success receipt, and failure propagation. Do not add the auxiliary nodes to the gate's execution inventory.

### 6. Compare executed evidence for loss

For each side, union executed lines and executed branch arcs over the agreed application coverage scope. Require compatible report schemas and the same instrumentation identity and exclusion set.

Let `L_base` and `L_candidate` be the executed-line sets. Let `B_base` and `B_candidate` be the executed branch-arc sets. Require both:

```text
L_base - L_candidate = empty
B_base - B_candidate = empty
```

Report candidate additions separately. A candidate addition does not offset a baseline loss. Do not infer per-test branch attribution from a union that lacks per-test contexts.

Validate the analyzer with negative probes for a failed run, substituted inventory, misplaced exclusion, instrumentation mismatch, invalid phase evidence, line loss, and branch loss.

### 7. Qualify behavior without measurement exclusions

Run the final behavior gate without coverage tracing or call exclusions. Require every retained test, each relocated test exactly once in its intended suite, cleanup, aggregation, and the applicable wall-time bound.

An instrumented measurement run can have a different wall time. It cannot replace this final uninstrumented acceptance gate.

### 8. Disclose the measurement limit

State the exact number of excluded calls and whether subprocess tracing was excluded. State that setup and teardown remained measured. Do not claim per-call line or branch coverage for the excluded calls.

Record the accepted revisions, run identities, manifests, executed-line and branch-arc deltas, final gate result, and wall-time evidence with the change.

### Quick Reference

| Decision or artifact | Required rule |
| --- | --- |
| Timing diagnosis | Identify the shared real-time operation; do not react to one failed node at a time. |
| Exclusion boundary | Smallest evidenced call set, identical on both sides, with setup and teardown still measured. |
| Execution inventory | Every approved test executes; an exclusion is not a skip or deletion. |
| Baseline | One fresh, complete, green measurement run; no diagnostic stitching. |
| Relocation | Measure old and new locations; use isolated auxiliary coverage when needed. |
| Coverage acceptance | No baseline-to-candidate executed-line or executed-branch-arc loss. |
| Final behavior gate | Uninstrumented, complete, green, and inside the required wall-time bound. |
| Disclosure | Name unmeasured calls and subprocesses; never imply per-call coverage for them. |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Add one exclusion after each failure | Excluded only the latest timing-sensitive failure. | Tracing overhead moved the failure to another node on the same path. | Diagnose the complete behavior family and define one evidence-based boundary. |
| Use a faster tracer | Selected a monitoring core that did not support the required branch events. | The run could not produce equivalent branch arcs. | Keep equivalent instrumentation on both sides; reduce scope only with disclosure. |
| Compare coverage percentages | Compared aggregate line or branch percentages after test removal. | Percentages and file totals hid local executed-evidence loss. | Compare executed-line and branch-arc sets directly and reject every baseline loss. |
| Reuse diagnostic shards | Combined green artifacts from different failed runs. | The result was not one fresh behavior-valid baseline with a consistent scope. | Accept only a complete fresh run under the final measurement contract. |
| Treat paused coverage as a skipped test | Removed the excluded node from execution or result accounting. | Behavior, cleanup, and inventory evidence disappeared. | Pause only tracing; retain every execution and phase record. |
| Change the timing contract | Increased a lease or relaxed an assertion to accommodate tracing. | The measurement changed the behavior under test. | Fix the measurement design, not the production or test behavior. |
| Use the instrumented run as final qualification | Accepted the slower measurement run as the behavior gate. | It did not prove uninstrumented behavior or the required wall time. | Run a separate final gate without coverage exclusions. |

## Results & Parameters

| Input or result | Rule |
| --- | --- |
| `inventory` | Exact node identities, dispositions, suite placement, and exactly-once execution evidence. |
| `exclusions` | Exact nodes, call phase, subprocess setting, source, run, and instrumentation binding. |
| `instrumentation` | Equivalent tracer, branch mode, context mode, source scope, and report format on both sides. |
| `baseline` | Fresh green run with complete behavior, cleanup, phase, and coverage evidence. |
| `candidate` | Same measurement scope plus fully measured replacement nodes outside the gate when applicable. |
| `line_loss` | `L_base - L_candidate`; must be empty. |
| `branch_loss` | `B_base - B_candidate`; must be empty. |
| `additions` | Candidate-only lines and arcs; report separately from loss. |
| `final_gate` | No coverage exclusions; complete behavior and wall-time acceptance required. |

Use this disclosure only after the evidence passes:

> All inventory tests executed. The disclosed call-phase exclusions also excluded subprocess tracing; setup and teardown remained measured. Baseline and candidate used identical instrumentation and exclusions. Executed-line and branch-arc comparisons showed no baseline-to-candidate loss. No per-call coverage is claimed for the excluded calls. The final uninstrumented behavior gate met its required bound.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| Application repository | Hosted sharded integration tests with real-time lease assertions and branch tracing. | A family-wide timing diagnosis replaced failure-by-failure exclusions. Fresh baseline and candidate runs preserved the approved execution inventory and had no executed-line or branch-arc loss under identical disclosed exclusions. |
| Application repository | Analyzer mutation probes and a final uninstrumented gate. | Invalid runs, inventory substitutions, exclusion drift, instrumentation drift, and line or branch loss were rejected. The final behavior gate passed within its wall-time bound. |
