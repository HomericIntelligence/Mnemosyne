---
name: unix-socket-shared-fs-host-locality
license: BSD-3-Clause
description: "Diagnose connection-refused on a Unix-domain socket whose path exists on shared cluster storage. Use when the socket file is visible to every host but only the host that bound it can serve clients."
category: debugging
date: 2026-10-19
version: "1.0.0"
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
---
# Unix Sockets on Shared Storage Serve Only the Binding Host

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-19 |
| **Objective** | Explain and diagnose a connection-refused failure against a Unix-domain socket path that exists and is readable on shared storage. |
| **Outcome** | Operational. Clients on two host classes received refused connections against a socket path that existed on shared storage. The listener had run on a third host and had been dead for days; the path was a stale artifact. A connect probe per host class plus sibling-artifact freshness settled the diagnosis. |
| **Verification** | verified-live: probes ran from a login-class host and a compute-class host against the production socket path; freshness evidence came from the adjacent audit file. See [notes](unix-socket-shared-fs-host-locality.notes.md). |

## When to Use

- A client reports connection refused on a Unix socket whose path clearly exists on a shared filesystem.
- A service binds a socket under a cluster-wide mount, and administrators run clients from more than one host.
- A socket file persists after its listener died, and the path looks healthy in directory listings.
- You choose where a socket-binding daemon must run when clients live on several hosts.

## Verified Workflow

### Quick Reference

```bash
# Path existence is not liveness. Probe the endpoint from the host that should serve it.
test -S "$SOCK" && echo "path exists" || echo "path missing"
python3 -c 'import socket,sys; s=socket.socket(socket.AF_UNIX); s.connect(sys.argv[1]); s.close()' "$SOCK" \
  && echo "listener answers on THIS host" || echo "no listener on THIS host"
# Freshness hint from adjacent artifacts the service rewrites on activity:
stat -c '%y %n' "$SOCK" "${SOCK%/*}/audit.log" 2>/dev/null
```

### Suggested Approach

1. **Apply the kernel boundary.** A Unix socket is a kernel object of the host that bound it. A shared filesystem exports the path to every host, but the object belongs to one kernel. Clients on any other host see the path and get refused connections.
2. **Read a present-but-refused socket as staleness evidence, not as a permission fault.** A dead listener leaves its socket file behind; permissions on the file then misdirect the investigation. Check whether any process hosts the path before changing modes or ownership.
3. **Find the serving host from evidence, not from the path.** Inspect the process table on candidate hosts for the service account, and compare modification times of the socket and its sibling activity artifacts (audit or log files the service rewrites). Stale artifacts plus no process prove absence; the host that must hold the daemon is the host where clients run.
4. **Probe from each client host class.** A login-class host and a compute-class host are different kernels. Run the connect probe where the client runs; a refusal there is authoritative even when the path mounted cleanly.
5. **Place one daemon per serving host.** When several host classes need the service, run one instance per host and give clients an explicit per-host selection (a per-host socket directory or a documented host flag). Do not expect one instance to answer through the shared mount.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Retrying the client command | Re-ran the administrative command after diagnosing the cause | The listener was still dead; retries against a host-local endpoint cannot cross kernels | Fix the serving side before asking users to retry |
| Checking the socket path on shared storage | Listed the directory and confirmed the socket file existed | The file was a stale artifact of a dead listener; existence proved nothing about liveness | Presence on shared storage is a hint, never a proof |
| Assuming a same-filesystem client can connect | Ran the client from a host that mounts the same filesystem | The filesystem exports the path, not the kernel object; the connection was refused | Treat any unix-socket client on another host as unreachable |
| Blaming permissions first | Considered ownership and mode faults because the socket was group-restricted | The refusal came from absence, not authorization; the file survived the process | Rule out a dead listener before a permission change |

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
```

### Expected Output

- A verdict that names the serving host (or its absence), the staleness of the path, and the last activity time from sibling artifacts.
- For multi-host service: a per-host instance layout and the client-side host selection flag.
- A liveness signal that is a connect probe, not directory metadata.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Shared-cluster inference deployment | Administrator authorization service on a shared parallel filesystem | Dead-listener staleness reproduced from two host classes; restore placed the supervised daemon on the administrator host. See [notes](unix-socket-shared-fs-host-locality.notes.md). |

## References

- [Give every service one supervision owner](service-supervision-ownership-parity.md)
- [Prove liveness before you report an outage](prove-long-running-process-liveness.md)
