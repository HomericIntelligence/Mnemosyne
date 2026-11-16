---
name: release-activation-with-live-old-release-outage
license: BSD-3-Clause
description: "Avoid and recover from the outage that follows activating a new release while the old release still runs. Use when: (1) you plan to activate a release while the previous gateway and replicas are live, (2) supervisors or registrars log a release or deployment-context identity check failure right after an activation, (3) replicas die and the model list is empty after an activation, (4) the control service rejects the new release's administrator after the activation, or (5) a hot-swap candidate was rejected and new replicas then fail on a release or source mismatch."
category: debugging
date: 2026-10-29
version: "1.1.0"
user-invocable: false
verification: verified-local
tags: [rejected-candidate, lane-pointer, release-activation, blue-green, outage, identity-check, operator-binding, rollback, cold-restart]
---

# Release Activation While the Old Release Is Live

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-29 |
| **Objective** | Switch the active release without killing the pools that the old release serves, and recover when it does kill them. |
| **Outcome** | Operational. An activation with live old components made the old supervisor and the replica registrars fail their identity checks and stop the pools. A rollback of the activation did not bring back the dead replicas. A cold stop, a fresh activation and a cold start restored service. |

Components that compare a release identifier, a release checksum or a control
revision treat the activation as a foreign change. The old supervisor refuses to
manage. The replica registrars see that the active deployment context differs
and end their replicas. The cost is an outage, not a drain.

## When to Use

- You are about to activate a release with a live gateway or live replicas.
- Logs show `release identity check failed` or `active deployment-context
  check failed` right after the activation.
- The control service rejects requests from the new release's administrator
  after an activation or a rollback.
- A hot-swap candidate was rejected, the old generation still serves, and every
  new replica ends within a minute with a source or release mismatch.

## Verified Workflow

### Quick Reference

```text
Before: stop or drain the old release unless the components compare a stable
        deployment identity (deployment, cluster, namespace, endpoint).
After:  restart the control service so it binds the active release.
Rollback of an activation restores the pointer, not the dead replicas.
Rejected hot-swap candidate: the lane can stay ahead of the serving generation.
  Restore the saved prior manifest in one documented activation. Do not flip
  the pointer by hand and do not restart the serving generation.
```

### Suggested Approach

1. Check the compare keys of every long-lived component: supervisor, registrar,
   monitor. If a key is a release identifier, checksum or source revision, a
   live activation is unsafe.
2. If a live activation is required, first run the version of each component that
   compares the stable deployment identity. Otherwise choose a cold path: cancel
   the jobs, retire the runtime evidence records, activate, start the gateway,
   and set the pool counts again.
3. After every activation or rollback, restart the control service. It binds the
   registered context and the active release when it starts, so it rejects the
   next request from a different release.
4. When the activation outage has already happened, do not hand-signal the
   supervisor. A signal can mean a different action in the new template (a
   drain). Use the supported stop and start verbs, and read the supervisor log
   for the exact check that failed.
5. Rejected-candidate branch: a hot-swap candidate that fails its readiness
   check leaves the old generation serving. The lane pointer and the registered
   context can still name the candidate release. A supervisor that keeps the old
   context then logs a "context stale" line for the pools whose contract differs
   between the releases. Every replica rendered while the pointer is ahead ends
   at start with a source or release mismatch, so many replicas can fail in one
   second. Compare the pointer, the stack record, and the serving generation's
   release before you scale. Restore the saved prior manifest through the
   documented activation, which also restores the registered context file. Keep
   the old generation and its jobs untouched. When a release coordinator owns the
   lane, give it the log lines and wait for its restore. Do not flip the pointer
   yourself. Scaling a pool while the lane is ahead only adds failing jobs.
6. Prove the restore from new replica logs that pass the start check. A job
   state of PENDING or RUNNING is not proof: low-priority replicas can be
   preempted before they reach the check.
7. Record each local patch and each restart in the issue that owns the main fix.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Activate with live old components | Used local patches to skip the activation gates | The old supervisor and the replica registrars failed their identity checks and stopped the pools | The gates protect a real coupling; skip them only when the components compare the stable identity |
| Roll back the activation | Restored the previous active release pointer | The dead replicas stayed dead and the pools were empty | A rollback of the pointer is not a restart; plan the cold path first |
| Scale a pool while the lane was ahead | Raised the desired count after a rejected candidate. | The new jobs were rendered against the candidate release and failed the start check. | Restore the lane first. Scale only after new replicas pass the check. |
| Reuse the running control service | Activated and then called the new release's administrator | The service rejected the request because it still bound the old release | Restart the control service after each activation or rollback |

## Results & Parameters

### Configuration

```yaml
cold_path:
  1: cancel every job of the deployment and wait for zero live jobs
  2: retire the stale runtime evidence records (keep them as audit files)
  3: activate the release
  4: restart the control service
  5: start the gateway, then set the pool counts
verify: "public discovery record names the new release; the model list is not empty"
rejected_candidate:
  signature: [candidate readiness timeout, pointer ahead of serving generation, supervisor context stale line, replicas end within a minute]
  recovery: documented activation of the saved prior manifest; no job cancelled; no serving-generation restart
  proof: new replica logs pass the start check
```

### Expected Output

After the cold path the public discovery record names the new release and the
gateway lists a model once a replica is ready.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A scheduler-managed model-serving deployment | Production release cut, 2026-10 | An activation with live old components caused an outage of about one hour. |
| A scheduler-managed model-serving deployment | A rejected hot-swap candidate left the lane ahead of the serving generation, 2026-11 | About two dozen replicas of one pool failed together and new replicas failed within a minute. The release coordinator restored the prior manifest. At capture, the new replicas had not yet passed the start check, so recovery of serving was not confirmed. |

## References

- [serving-pool-replica-outage-diagnosis](serving-pool-replica-outage-diagnosis.md) — classify a pool loss before you respond
- [live-hotfix-content-addressed-identity-rotation](live-hotfix-content-addressed-identity-rotation.md) — identity rotation during a live hotfix
