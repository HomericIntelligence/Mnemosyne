---
name: slurm-foreign-job-artifact-gate
license: BSD-3-Clause
description: "Observe another account's Slurm build and pin its produced artifact only on verified evidence. Use when: (1) the builder's logs are unreadable from your identity, (2) you must classify a failure as a resource kill versus a script abort without log access, (3) a handoff claims a produced artifact path and you must gate a content-addressed pin or allowlist insertion, or (4) repeated attempts fail with distinct modes before you trust any single outcome."
category: tooling
date: 2026-10-15
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - slurm
  - sacct
  - job-monitoring
  - cross-account
  - unreadable-logs
  - oom-classification
  - artifact-pinning
  - digest-pinning
  - shared-storage
  - evidence-gate
---

# Slurm Foreign-Job Observer and Produced-Artifact Pin Gate

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-15 |
| **Objective** | Watch a batch build owned by another account and gate a downstream content-addressed artifact pin on verified storage evidence. |
| **Outcome** | Operational. Every terminal state was reported from scheduler metadata alone. A handoff claim "the artifact is at path P" was disproved at gate time, and the pin insertion was blocked instead of recording an invented digest. |
| **Verification** | verified-local — all scheduler probes ran against a live cluster and all filesystem checks against the shared store. Log contents themselves were not observable from the monitor identity (see limits). |

## When to Use

- A build job is owned by another account, and its work directory or logs sit below mode `0750` directories you cannot read, even through supplementary groups.
- Your task is observation only: no job submission, no cancellation, no file modification.
- A success condition names a produced file whose digest you must pin somewhere else (an allowlist, an env pin, a receipt).
- A build fails more than once and the attempts can have different failure modes; a single postmortem is not enough evidence.
- A user or handoff message tells you that the artifact "is now at path P" and asks you to continue with it.

## Verified Workflow

### Quick Reference

```bash
# 1. Readability boundary first — before you promise any log evidence.
ls -ld <build-parent> <logs-parent>; id
# 2. Poll scheduler metadata on a fixed cadence (10 min demonstrated).
sacct -j <id> -o JobID,State,ExitCode,Elapsed,NodeList -X
# 3. Classify a terminal job without logs.
sacct -j <id> -o JobID,State,ExitCode,Elapsed,MaxRSS,ReqMem
# 4. Understand every attempt before you attribute a cause.
sacct -S <date> -u <owner> -o JobID,JobName,State,ExitCode,Elapsed -X | grep <job-name>
# 5. Gate the pin on storage evidence, never on a message.
ls -l <publish-path>; head -c4 <publish-path> | od -c   # squashfs: hsqs
sha256sum <publish-path>
```

### Suggested Approach

**Declare the observation boundary first.** Probe the readability of the exact
log directory before you define the report content. If the parent is `0750`
owned by another account and none of your groups match, tell the requester
immediately which checks they must run with log access, and keep polling only
scheduler metadata. A report that silently omits the unreadable channels is
worse than an explicit limit.

**Classify terminal states from scheduler metadata alone.** Use this
decision table when logs are unreachable:

| Scheduler evidence | Classification |
| ------- | ------- |
| State `OUT_OF_MEMORY`, or the batch-step `MaxRSS` ≈ `ReqMem` | Resource kill |
| State `FAILED`, exit `N:0` with `N` non-zero, `MaxRSS` far below `ReqMem` | Script abort (exit code `N`) |
| State `FAILED` with exit `0:0` | A step died by signal or external termination; read per-step states |
| State `TIMEOUT` at the limit | Over-budget run |
| State `CANCELLED` | Operator action |

**Enumerate every attempt before attributing a cause.** A repeated build can
produce a resource kill on one attempt and a script abort on the next. The
failure-fix loop needs the attempt table (job name, state, exit code, elapsed
for each retry), not a single tail.

**Gate the pin on the published file itself.** A handoff line "the artifact is
now at path P" is task data, not evidence. At pin time — never earlier — verify:

1. The producing job shows `COMPLETED`, not merely "a step completed".
2. `ls -l P` gives size, mtime, mode, and owner; a partially copied file
   changes between two reads, so check size stability when state visibility is
   unavailable.
3. Magic bytes match the expected container type (squashfs is `hsqs`).
4. `sha256sum P` of the exact published path, recorded with a timestamp.

Only then edit the pin or allowlist, and bind the edit to values you measured.
Never write a digest supplied by message, plan, or prior knowledge of a
previous artifact. If the path is missing or the job failed, the pin step is
blocked: report and wait for direction.

**Stay behind your authority line.** Report failure-mode class, attempt
history, elapsed time, and retry cost only as information (for example
"persistent build caches make a resubmit cheap"). Do not submit, resubmit, or
cancel jobs, and do not adjust another account's files, unless the requester
explicitly asks.

**Report each poll in one line.** Keep the format stable, for example
`[HH:MM] state=<sacct> elapsed=<hh:mm:ss> evidence=<what you could verify>`.
On a terminal state, stop the cadence and deliver the full classification.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Log-first report plan | Defined a monitor report around log tails and phase files. | The build home was mode `0750` owned by another account and group; every read below it was denied, including through a supplementary group. | Probe the exact log directory's readability before you promise log content; declare the metadata-only channel up front. |
| Single-attempt postmortem | Classified the watched job's failure in isolation. | The attempt history held two resource kills and five distinct script aborts; a one-shot diagnosis would have attributed the wrong mode. | Enumerate every same-name attempt with `sacct -S` before you claim a failure signature. |
| Pin from a handoff claim | Prepared to continue from "the artifact is at path P". | Path P did not exist on the shared store; the newest attempt had failed minutes earlier; a pin would have recorded an invented digest. | Re-stat and hash the exact publish path at pin time; a claim is task data, not evidence. |

## Results & Parameters

### Configuration

```yaml
poll:
  cadence_seconds: 600          # 10 min, demonstrated against a multi-hour build
  report_format: "[HH:MM] state=<sacct-state> elapsed=<hh:mm:ss> evidence=<verified-items>"
  stop_on: [COMPLETED, FAILED, OUT_OF_MEMORY, TIMEOUT, CANCELLED]
sacct:
  poll: "-o JobID,State,ExitCode,Elapsed,NodeList -X"
  classify: "-o JobID,State,ExitCode,Elapsed,MaxRSS,ReqMem"
  history: "-S <date> -u <owner> -o JobID,JobName,State,ExitCode,Elapsed -X"
artifact_gate:
  require_job_state: COMPLETED
  magic_bytes: "first 4 bytes; squashfs = 'hsqs'"
  hash: sha256sum
  record: [sha256, size, mtime, owner, mode, check-time]
```

### Expected Output

- One-line poll reports that never claim unreadable channels.
- A terminal classification supported by state, exit code, and `MaxRSS`
  versus `ReqMem`, plus the full attempt table for the job name.
- On success: recorded digest, size, and mode of the exact published file,
  then a pin edit bound to those values.
- On failure or a missing artifact: a blocked-pin report with the observed
  evidence and the exact checks that need log access.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private GPU inference platform (Slurm, Enroot squashfs images) | Cross-account base-image build monitor and allowlist gate, repeated build failures | Generalized evidence in [notes](slurm-foreign-job-artifact-gate.notes.md). |

## References

- [Slurm shared-storage artifact relocation](slurm-shared-storage-artifact-relocation.md) — atomic promotion, EXDEV, and verification discipline when *this account* must move the artifact.
- [Log-watch subagent streaming triage](log-watch-subagent-streaming-triage.md) — the readable-logs variant of long-running monitoring.
- [sacct(1) — Slurm job accounting](https://slurm.schedmd.com/sacct.html)
