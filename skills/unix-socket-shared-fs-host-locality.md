---
name: unix-socket-shared-fs-host-locality
license: BSD-3-Clause
description: "Diagnose connection-refused on a Unix-domain socket whose path exists on shared cluster storage, and plan where the client must run. Use when the socket file is visible to every host but only the host that bound it can serve clients, when an operator step or runbook schedules an operator-bound command on a scheduler node, or when a readiness gate passes on one host but another host must act. Covers the remote-host refusal guard, pre-failure evidence as the wrong-host proof for a cold start, and reply readiness versus fleet health."
category: debugging
date: 2026-10-19
version: "1.1.0"
user-invocable: false
verification: verified-live
tags:
  - unix-socket
  - shared-filesystem
  - cluster
  - econnrefused
  - stale-socket
  - host-placement
  - debugging
  - multi-login
  - operator-socket
  - scheduler-allocation
  - host-locality-guard
  - readiness-vs-health
---
# Unix Sockets on Shared Storage Serve Only the Binding Host

## Overview

| Field | Value |
| ------- | ----- |
| **Date** | 2026-10-19 |
| **Objective** | Explain and diagnose a connection-refused failure against a Unix-domain socket path that exists and is readable on shared storage, and keep operator-bound steps on the binding host. |
| **Outcome** | Operational. Clients on two host classes received refused connections against a socket path that existed on shared storage. The listener had run on a third host and had been dead for days; the path was a stale artifact. A connect probe per host class plus sibling-artifact freshness settled the diagnosis. A later cutover review added the planning and step-design branches. |
| **Verification** | verified-live for the diagnosis: probes ran from a login-class host and a compute-class host against the production socket path; freshness evidence came from the adjacent audit file. The step-design branch comes from read-only review of a documented cutover and has no live run. See [notes](unix-socket-shared-fs-host-locality.notes.md). |

## When to Use

- A client reports connection refused on a Unix socket whose path clearly exists on a shared filesystem.
- A service binds a socket under a cluster-wide mount, and administrators run clients from more than one host.
- A socket file persists after its listener died, and the path looks healthy in directory listings.
- You choose where a socket-binding daemon must run when clients live on several hosts.
- You plan or review an operator step, a runbook, or a migration that calls a local-socket control verb from a scheduler allocation or any host other than the binding host.

## Verified Workflow

### Quick Reference

```bash
# Path existence is not liveness. Probe the endpoint from the host that must serve it.
test -S "$SOCK" && echo "path exists" || echo "path missing"
python3 -c 'import socket,sys; s=socket.socket(socket.AF_UNIX); s.connect(sys.argv[1]); s.close()' "$SOCK" \
  && echo "listener answers on THIS host" || echo "no listener on THIS host"
# Freshness hint from adjacent artifacts the service rewrites on activity:
stat -c '%y %n' "$SOCK" "${SOCK%/*}/audit.log" 2>/dev/null
```

### Suggested Approach

1. **Apply the kernel boundary.** A Unix socket is a kernel object of the host that bound it. A shared filesystem exports the path to every host, but the object belongs to one kernel. Clients on any other host see the path and get refused connections.
2. **Read a present-but-refused socket as staleness evidence, not as a permission fault.** A dead listener leaves its socket file behind; permissions on the file then misdirect the investigation. Check whether any process hosts the path before you change modes or ownership.
3. **Find the serving host from evidence, not from the path.** Inspect the process table on candidate hosts for the service account. Compare the modification times of the socket and its sibling activity artifacts. Stale artifacts and no process prove absence. The host that must hold the daemon is the host where the clients run.
4. **Probe from each client host class.** A login-class host and a compute-class host are different kernels. Run the connect probe where the client runs. A refusal there is authoritative, even when the path mounted cleanly.
5. **Place one daemon per serving host.** When several host classes need the service, run one instance per host. Give clients an explicit per-host selection, such as a per-host socket directory or a documented host flag. Do not expect one instance to answer through the shared mount.
6. **Keep operator-bound commands on the binding host.** The local-socket verbs, the operator start and stop, and the migrations that the operator gates all need that kernel. State this rule in the header of each step that uses them. A scheduler allocation is not the binding host.
7. **Refuse a remote host before any effect.** At step start, test the scheduler allocation variable and exit nonzero before any filesystem, database, or service change. A rule that only the header states is not a guard. On a cold start, the database reachability proof also fails from a remote host, because the local forward exists only on the binding host. Use that failure as a second proof, not as the guard.
8. **Gate on a reply, not on fleet health.** A readiness gate that exits nonzero for a degraded pool reports a serving operator as absent. Gate on a request that the registered context admits. Then read the reply fields. A dead listener gives a no-reply error. A wrong host or context gives a context-mismatch error. Both are the failure that the gate must report.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | --------------- | ------------- | -------------- |
| Retrying the client command | Re-ran the administrative command after diagnosing the cause | The listener was still dead. Retries against a host-local endpoint cannot cross kernels | Fix the serving side before you ask users to retry |
| Checking the socket path on shared storage | Listed the directory and confirmed that the socket file existed | The file was a stale artifact of a dead listener. Existence proved nothing about liveness | Presence on shared storage is a hint, never a proof |
| Assuming a same-filesystem client can connect | Ran the client from a host that mounts the same filesystem | The filesystem exports the path, not the kernel object. The connection was refused | Treat any unix-socket client on another host as unreachable |
| Blaming permissions first | Considered ownership and mode faults because the socket was group-restricted | The refusal came from absence, not authorization. The file survived the process | Rule out a dead listener before a permission change |
| Readiness gate on a fleet report verb | Ran the status verb that reports pool health and required exit 0 | That verb exits 1 when a pool is degraded. A serving operator with one bad pool looked absent | Gate on the reply that proves the context, not on fleet health |
| Heartbeat gate alone | Waited for a fresh heartbeat of the launched pid | The heartbeat proves that the process writes state. It does not prove that a client reaches the socket with the registered context | Add one reply probe after the heartbeat gate |

## Results & Parameters

### Configuration

```yaml
diagnosis:
  probes:
    - path-stat
    - connect-probe-from-client-host
    - sibling-artifact-freshness
    - serving-host-process-table
placement:
  single_admin_host: one unscoped instance on that host
  multiple_admin_hosts: one instance per host with per-host socket paths
step_guard:
  refuse_when: scheduler allocation variable is set
  refuse_point: before any effect
  evidence: process argv, executing binary, and the pre-failure log lines
readiness:
  admit: a request that the operator admits only for its registered context
  require: exit 0 plus the identity fields of the reply
  never: a fleet-health verb as the readiness gate
```

### Expected Output

- A verdict that names the serving host or its absence, the staleness of the path, and the last activity time from the sibling artifacts.
- For a multi-host service: a per-host instance layout and the client-side host selection flag.
- A liveness signal that is a connect probe, not directory metadata.
- A step header and a code guard that keep every operator-bound command on the binding host.
- A readiness result that separates "not reachable" from "wrong context", and that ignores pool health.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Shared-cluster inference deployment | Administrator authorization service on a shared parallel filesystem | Dead-listener staleness reproduced from two host classes. The restore placed the supervised daemon on the administrator host. See [notes](unix-socket-shared-fs-host-locality.notes.md). |
| Shared-cluster inference deployment | Cutover step that starts or replaces the same operator | Step-design branch added from read-only review of the committed step and the product client paths. No live run. See [notes](unix-socket-shared-fs-host-locality.notes.md). |

## References

- [Give every service one supervision owner](service-supervision-ownership-parity.md)
- [Prove liveness before you report an outage](prove-long-running-process-liveness.md)
- [Stop the previous release's daemon through a supported stop](cutover-stop-previous-release-daemon.md)
- [Validate a deploy step chain as one ordered chain](runbook-step-chain-contract-validation.md)