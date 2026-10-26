---
name: supervised-restart-stale-worker-state-guard
description: "Keep a startup state-cleanliness guard from poisoning supervised restarts. Use when a child whose workers write per-instance artifacts into a shared state directory is restarted in place, when an absence assertion rejects pre-existing artifacts at launch, or when a restart budget expires into an outage that only a fresh allocation repairs."
category: architecture
date: 2026-10-26
version: "1.0.0"
user-invocable: false
tags:
  - supervision
  - restart
  - startup-guard
  - state-cleanup
  - outage
  - worker-pool
  - pid-lived-artifacts
---

# Supervised Restart Stale Worker-State Guard

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-26 |
| **Objective** | Keep one supervised in-place restart from becoming a guaranteed crash-loop when per-worker artifacts of the previous child remain in a shared state directory |
| **Outcome** | Successful. The same mechanism caused a multi-minute production outage: one health-triggered restart crash-looped on leftover per-worker state until the restart budget expired, and service returned only when a fresh allocation arrived with an empty state directory. The generalized rule and its repair pattern are recorded here; the owning tracker holds the product defect. |

## When to Use

Apply this skill when:

- A supervisor restarts a child process in place, and the child's workers each write artifacts named by PID or instance identity into a state directory that survives the restart.
- A startup guard asserts that the state directory contains no worker artifacts before it launches a new worker pool.
- A supervisor log shows repeated launch crashes that name a stale worker artifact, followed by a restart-budget exhaustion message, and the service returns only after a fresh allocation or a fresh state directory.
- You design or review a freshness or contamination guard over shared runtime state.

## Verified Workflow

### Quick Reference

```text
During a startup absence-check over a shared state directory, classify each
pre-existing entry before you reject it:

  same-owner artifact whose recorded PID or instance is dead
      -> clean it (or ignore it), then start
  live entry, foreign name, foreign type, foreign owner
      -> refuse to start

A guard that rejects dead same-owner leftovers converts every routine
restart into a crash-loop: attempt one fails, attempt one leaves new
leftovers, and every later attempt collides until the budget expires.
```

### Suggested Approach

1. **Name a deleter for every artifact class.** Trace the full lifecycle of each per-worker artifact: the creator, each reader or aggregator, and the component that removes it. A graceful shutdown that writes a final record but keeps the artifact is finalization, not cleanup. If no deleter exists for the dead-owner case, the artifacts accumulate forever.
2. **Scope the guard to its actual domain.** A strict absence assertion protects one thing: first allocation against foreign contamination. Apply strict absence to the first launch of an allocation and to entries that are foreign by name, type, or owner. Do not apply it to dead same-owner leftovers from the same component generation.
3. **Clean at the safest boundary.** Prefer cleanup at stop time by the owner. At start time, remove or skip artifacts whose recorded PID is dead before the absence check runs. A group kill of the old child tree removes processes, not files.
4. **Keep the guard fail-closed for foreign entries.** Repair by narrowing the check, not by loosening it. An absence guard that accepts everything converts loud contamination into silent cross-generation state mix.
5. **Test the three restart shapes.** Clean-stop restart must start. Hard-kill restart must start. Foreign injection must still refuse. Verify the first two through the actual supervisor restart path, including its budget, not only through direct launch.
6. **For diagnosis, match the signature before you repair.** Repeated launch crashes that name a stale worker artifact, a restart-budget exhaustion line, and recovery only through a fresh allocation or an empty state directory identify this defect class. A restart that succeeds in place after the repair is the completion evidence.

If a runtime seal forbids start-time deletion, keep the absence check but make it ignore entries whose PID is dead instead of rejecting them. That preserves the contamination signal with weaker hygiene. Record the cap: dead-PID entries then persist until allocation teardown.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Startup absence assertion over all worker artifacts | Treated dead same-owner per-PID files as contamination | Attempt one left new files, so every retry collided; five restarts expired the budget and the endpoint went down | Scope absence assertions to live or foreign entries. Dead same-owner leftovers need a deleter, not a refusal |
| Worker final record on shutdown as the hygiene story | Each worker wrote a terminal snapshot at shutdown and kept its file | A final write is not a delete; nothing removed the files | Assign an explicit deleter to every artifact class. Do not count finalization as cleanup |
| Recovery through a fresh allocation | A new scheduled job with an empty state directory restored the service | Each occurrence still cost minutes of full outage, and the defect remained for the next restart | Fresh-allocation recovery proves the poisoning mechanism. It is not the repair |

## Results & Parameters

### Configuration

```yaml
startup_guard:
  reject: [foreign-name, foreign-type, foreign-owner, live-owner-conflict]
  clean_before_check: [same-owner artifact with dead recorded pid]
  strict_absence_scope: first-allocation-only
supervisor:
  restart_safety: restart-succeeds-with-dead-leftovers-cleaned
  stop_hygiene: owner-removes-per-instance-artifacts-on-graceful-stop
```

### Expected Output

- An in-place supervisor restart succeeds after a clean stop and after a hard kill of the previous child.
- A foreign, live, or type-mismatched entry in the state directory still fails the launch.
- Supervisor logs show at most a bounded restart sequence; the budget is not consumed by artifact collisions.
- No per-worker artifact survives its owner's death across a restart.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A supervised HTTP service whose workers publish per-PID state files into a shared runtime directory | Production restart after health-probe failures of the running child | One triggered restart crash-looped on stale worker state until the restart budget expired; multi-minute outage; a fresh allocation recovered service; defect recorded in the owning tracker. See [notes](supervised-restart-stale-worker-state-guard.notes.md). |

## References

- [Service startup precondition bootstrap deadlock](service-startup-precondition-bootstrap-deadlock.md) — the first-start variant: a guard that blocks first start when only the service itself can satisfy it
- [Service supervision ownership parity](service-supervision-ownership-parity.md) — missing restart ownership; this entry is its complement: ownership exists, and the restart path itself is poisoned
- [systemd restart-storm fix](systemd-docker-compose-restart-storm-fix.md) — restart storms from double supervision, a different mechanism with the same surface symptom
- [ASD-STE100 technical English](../docs/asd-ste100.md)
