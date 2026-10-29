---
name: release-activation-with-live-old-release-outage
license: BSD-3-Clause
description: "Avoid and recover from the outage that follows activating a new release while the old release still runs. Use when: (1) you plan to activate a release while the previous gateway and replicas are live, (2) supervisors or registrars log a release or deployment-context identity check failure right after an activation, (3) replicas die and the model list is empty after an activation, (4) the control service rejects the new release's administrator after the activation."
category: debugging
date: 2026-10-29
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [release-activation, blue-green, outage, identity-check, operator-binding, rollback, cold-restart]
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

## Verified Workflow

### Quick Reference

```text
Before: stop or drain the old release unless the components compare a stable
        deployment identity (deployment, cluster, namespace, endpoint).
After:  restart the control service so it binds the active release.
Rollback of an activation restores the pointer, not the dead replicas.
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
5. Record each local patch and each restart in the issue that owns the main fix.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Activate with live old components | Used local patches to skip the activation gates | The old supervisor and the replica registrars failed their identity checks and stopped the pools | The gates protect a real coupling; skip them only when the components compare the stable identity |
| Roll back the activation | Restored the previous active release pointer | The dead replicas stayed dead and the pools were empty | A rollback of the pointer is not a restart; plan the cold path first |
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
```

### Expected Output

After the cold path the public discovery record names the new release and the
gateway lists a model once a replica is ready.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A scheduler-managed model-serving deployment | Production release cut, 2026-10 | An activation with live old components caused an outage of about one hour. |

## References

- [serving-pool-replica-outage-diagnosis](serving-pool-replica-outage-diagnosis.md) — classify a pool loss before you respond
- [live-hotfix-content-addressed-identity-rotation](live-hotfix-content-addressed-identity-rotation.md) — identity rotation during a live hotfix
