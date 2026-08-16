---
name: warden-hot-upgrade-listener-isolation
license: BSD-3-Clause
description: "Use when: (1) designing or reviewing a same-host hot upgrade with a standby control plane and HAProxy handoff, (2) validating that a temporary management listener cannot collide with a public gateway listener, (3) separating scheduler-selected active placement from source-node-pinned standby placement."
category: architecture
date: 2026-07-29
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - warden
  - hot-upgrade
  - haproxy
  - listener-isolation
  - slurm
  - standby
---

# Warden Hot-Upgrade Listener Isolation

## Overview

| Field | Value |
| --- | --- |
| **Date** | 2026-07-29 |
| **Objective** | Preserve a stable public gateway route during a same-host Warden hot upgrade. |
| **Outcome** | Verified that an active control plane is scheduler-placed, only its standby is source-node pinned, and the standby management listener is isolated from both the active management and public gateway listeners. |

## When to Use

- Reviewing a control-plane hot upgrade that starts a standby process on the active host.
- Adding a configurable standby API port beside a long-lived public HAProxy listener.
- Retiring a manifest field that previously pinned ordinary control-plane placement.

## Verified Workflow

### Quick Reference

1. Let the scheduler choose the ordinary active control-plane node.
2. Pin only the hot-upgrade standby to the active node and run it on a distinct management port.
3. Before submitting the standby, reject a port equal to either the active control-plane API port or the public gateway listener port.
4. Start the target HAProxy with graceful replacement so the public host, port, and route remain unchanged while existing streams drain.

### Detailed Steps

1. Keep node targeting out of the active control-plane manifest contract. The active process discovers its actual scheduler-assigned node after submission.
2. At the shared Slurm command boundary, reject a target node unless the role is `standby`; this prevents a future active caller from silently restoring node pinning.
3. During upgrade preflight, validate the selected standby port is a valid TCP port and differs from both the source management port and `gateway.bind_port`.
4. Keep the standby fenced while it validates the registry and routes. Its management listener is temporary and is not a gateway listener.
5. At cutover, use HAProxy graceful replacement (`-sf`) on the already configured gateway listener. New requests use the replacement while the source drains in-flight streams.
6. Test the public manifest loader rejects retired placement fields, the active command rejects explicit targeting, the standby command preserves source-node targeting, and both explicit and default-derived management-port collisions fail preflight.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Manifest-only retirement | Removing the active node-pin field from the checked-in profile | A private command parameter could still pin an active process. | Enforce the role invariant at the shared command boundary. |
| API-port-only validation | Ensuring standby port differs only from the source management API port | A custom source port or explicit standby port can collide with HAProxy on the same host. | Reserve the public gateway listener as part of hot-upgrade preflight. |
| Builder-only regression | Injecting a retired field into an already loaded mapping | It bypassed the public schema/loader contract. | Exercise the on-disk manifest loader for retired-field behavior. |

## Results & Parameters

### Configuration

```text
active role: scheduler-selected node, no target node
standby role: target node = active control-plane node
standby management port: valid TCP port != active management port != gateway.bind_port
gateway handoff: retain public host, port, and route; gracefully replace HAProxy
```

### Expected Output

- An active submission with a target node fails before scheduler submission.
- A standby submission uses the active node and a distinct temporary management listener.
- A standby management port colliding with the public gateway listener fails preflight.
- Clients continue using the same public gateway URL through HAProxy cutover.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| Inference360 | PR #479 hot-upgrade placement and listener-isolation fix | Focused lifecycle and upgrade tests passed locally; the PR tracks its required CI. |

## References

- [Inference360 PR #479](https://github.com/LLM360/Inference360/pull/479)
