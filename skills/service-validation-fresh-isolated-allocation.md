---
name: service-validation-fresh-isolated-allocation
license: BSD-3-Clause
description: "Validate service launch and cleanup in an isolated allocation. Use for launch defects, environment-sensitive regressions, or matched A/B experiments."
category: debugging
date: 2026-07-18
version: "1.1.1"
user-invocable: false
tags: [validation, reproduction, isolation, fresh-allocation, teardown, cleanup-evidence, control-plane, artifact-validation, ablation, scheduler, gpu, service-lifecycle]
---

# Service Validation on a Fresh, Isolated Allocation

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-18 |
| **Objective** | Validate, debug, or reproduce a service's behavior on a clean, independently-allocated environment rather than an already-running one, and prove both the allocation and its release as part of the evidence. |
| **Outcome** | Reusable workflow: fresh-allocation-by-default, layered failure isolation (control-plane vs artifact vs probe), single-variable ablation discipline, and cleanup-as-validation. |
| **Verification** | verified-ci (generalized from a scheduler/GPU service validation whose fresh-allocation runbook and single-variable forward-path ablation both passed CI; the concrete scheduler/hardware specifics are intentionally omitted here). |

## When to Use

- You must prove a service or endpoint works end-to-end, but instances are already running and the user has not said reusing them is acceptable.
- You are reproducing a corruption, non-determinism, or regression that a dirty/shared environment could mask or contaminate.
- A manifest-, config-, or checkpoint-driven launch fails and you need to tell apart a control-plane failure, a missing/renamed artifact, and a probe/parameter failure.
- You are running an A/B ablation and must guarantee baseline and treatment differ in exactly one variable.
- Your completion claim needs evidence that the run allocated its own resources and released them, not just that a probe returned 200.

## Verified Workflow

### Quick Reference

```text
Prefer a fresh allocation when testing launch or cleanup behavior. Reuse an
endpoint when existing authority covers the probe and reuse fits the test.
Ask only when resource ownership, disruption, or authority remains unclear.
The allocation and teardown steps below apply when a fresh unit is needed.

1. Read the surface's own contract/docs before acting.
2. Enumerate resources already in use and EXCLUDE them from the new allocation.
3. Allocate a fresh, isolated, labeled unit of compute for this test only.
4. If control-plane bring-up fails, confirm it did not leave a partial
   allocation before falling back to a simpler control path — then release it.
5. Validate every artifact path/digest the launch references BEFORE relaunch.
6. Probe with realistic parameters (e.g. enough output budget); tiny defaults
   can return empty/blank results that look like failures.
7. For ablations, hold everything constant except the one variable and confirm
   from logs that the intended variant actually bound.
8. Tear down: stop the service, release the allocation, stop control, and VERIFY
   the allocation left the scheduler/queue. Cleanup is evidence, not a footnote.
```

### Detailed Steps

1. **Read the contract first.** Read the service's README/AGENTS/product-contract/runbook docs for the exact surface under test before allocating anything — the launch contract (manifest schema, required artifacts, control API) is where most failures originate.
2. **Prefer a fresh allocation for launch and cleanup tests.** A warm allocation cannot prove those behaviors. Reuse an endpoint when existing authorization covers the probe and reuse fits the test; request input only when ownership, disruption, or resource authority is unclear.
3. **Exclude occupied resources.** Enumerate what is already allocated and explicitly exclude it, so the fresh allocation cannot accidentally land on or contend with in-use resources. Label the new allocation with its purpose so it is auditable and reclaimable.
4. **Isolate failure layers.** When a launch fails, classify the failure before retrying:
   - **Control-plane**: bring-up failed before any resource was allocated. Confirm no partial allocation was created; if one was, release it before retrying. Fall back to a simpler/foreground control path only after confirming the clean state.
   - **Artifact**: the config/manifest references a path, checkpoint, image, or digest that is missing or renamed. Verify the referenced facts against the real filesystem/registry, correct the manifest (a scratch copy is fine), and re-validate it through the service's own validation API before relaunch.
   - **Probe/parameter**: the service is up but the probe used unrealistic parameters. Re-probe with realistic values.
5. **Single-variable ablation.** For A/B or forward-path ablations, keep baseline and treatment byte-for-byte identical except the one variable under test, and confirm from server/runtime logs that the intended variant actually bound — do not trust that a flag took effect.
6. **Cleanup is part of validation.** Stop the service, release the allocation, stop the control process, then actively verify the allocation has left the scheduler/queue (poll until the job/reservation is gone, through any transitional "completing" state). A validation that leaks an allocation has not passed.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Probe an already-running endpoint as the validation path | Reused a warm allocation to save setup time | It proves nothing about launch/allocation/cleanup and can be contaminated by prior state | Use a fresh allocation to prove launch and cleanup; use existing task-scoped authorization for suitable reuse probes |
| Relaunch immediately after a manifest launch failed | Retried without checking the referenced artifacts | The manifest pointed at a missing/renamed checkpoint; the retry failed the same way | Verify every referenced artifact path/digest against the real filesystem before relaunch |
| Trust a control-plane failure left nothing behind | Switched to a fallback control path without checking | A partial allocation could leak and contend with the fresh run | After a control-plane failure, confirm no partial allocation exists (and release it) before falling back |
| Probe with the status helper's tiny default output budget | Used a minimal `max_tokens`/output limit | Reasoning-heavy or slow-first-token services returned blank/empty output that looked like a failure | Probe with realistic parameters; distinguish "empty because too small a budget" from a real fault |
| Treat cleanup as an optional follow-up | Declared success when the probe returned OK | The allocation leaked in the scheduler queue | Stop → release → stop control → verify the queue is clear; cleanup is part of the pass criteria |

## Results & Parameters

- **Default posture**: prefer a fresh, isolated allocation for launch tests; use existing authorization for a suitable non-disruptive reuse probe.
- **Failure taxonomy**: control-plane vs artifact vs probe/parameter — classify before retrying.
- **Ablation rule**: exactly one variable differs; confirm the intended variant bound from logs.
- **Cleanup proof**: the allocation is observed leaving the scheduler/queue; a leaked allocation fails the run.

## Attribution

Generalized from a project-specific GPU/scheduler service-validation and corruption-reproduction runbook, with the concrete cluster, hardware, scheduler, engine, and checkpoint details removed. The transferable core — fresh-allocation-by-default, layered failure isolation, single-variable ablation, and cleanup-as-validation — is host- and project-neutral.
