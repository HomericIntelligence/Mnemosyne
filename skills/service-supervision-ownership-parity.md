---
name: service-supervision-ownership-parity
license: BSD-3-Clause
description: "Give every long-running service exactly one owner for start, restart, and liveness evidence. Use when adding or reviewing a deployed component, or after a service stayed down for days because no machinery restarted or watched it."
category: tooling
date: 2026-10-19
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - supervision
  - watchdog
  - liveness
  - outage
  - silent-failure
  - deployment-review
  - restart-scope
  - foreground-daemon
  - incident-reproduction
---
# Give Every Service One Supervision Owner

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-19 |
| **Objective** | Detect and remove the deployment gap in which a long-running service has no component that starts it, restarts it, or alerts on its absence. |
| **Outcome** | Operational. One authorization endpoint ran as an ad-hoc process inside an interactive scheduler allocation. It died with the allocation activity, stayed down for ten days across an unrelated service restart, and was discovered only by user report. A supervision loop plus an operations runbook removed the gap. |
| **Verification** | verified-live: the inventory, the outage reproduction, the restore handoff, and the supervision behavior tests all ran against the live deployment. See [notes](service-supervision-ownership-parity.notes.md). |

## When to Use

- You add a long-running component to a deployment, or you review the launch machinery of an existing one.
- A fleet or stack status report claims a set of "supervisable" components; compare that set against every endpoint clients can call.
- A user-facing operation fails with a connection error against a local service endpoint, and no restart machinery has reacted for days.
- A service runs in a shell, a terminal multiplexer, or an interactive job step that a person started by hand.

## Verified Workflow

### Quick Reference

```text
For each endpoint that accepts client work, answer three questions:
  START:   which machinery brings it up after a host boot or full stop?
  RESTART: which entity observes its exit and starts a replacement?
  LIVENESS: which signal proves up-ness, and who watches that signal?
Any blank answer is a silent-death candidate.
```

### Suggested Approach

1. **Enumerate endpoints, not processes.** List every socket, port, or queue a client can call. The supervision set must cover the enumeration, not the components that were convenient to template.
2. **Name the restart scope of each endpoint.** Traced restart logic must reach the endpoint: a sibling service's restart does not count. A restart of the largest stack component restarted nothing for the endpoint that was down in the incident this entry records.
3. **Treat documentation state as a claim to verify.** A fleet document that labels components supervisable can omit endpoints added later. Reproduce the failing client operation before you trust the inventory.
4. **Give an unsupervised daemon a minimal owner.** A restart-on-unexpected-exit loop with bounded rapid-failure give-up, plus a runbook that states start, stop, and liveness probing, removes the silent-death class. A clean exit code must stay down; a nonzero exit restarts; repeated sub-threshold failures give up with a distinct status instead of hot-looping.
5. **Probe liveness where clients connect.** For a local-transport endpoint, an external status file does not prove reachability. A connect probe on the endpoint itself does.
6. **Record placement constraints explicitly.** When the serving mechanism binds the daemon to a host class, write the constraint in the runbook instead of encoding a choice silently in a template.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Trusting a launch-time setup as deployment | A person started the daemon by hand during initial setup and it worked | The process died with the interactive session and nothing observed the exit for ten days | A manually started foreground process is not deployed |
| Restarting an adjacent stack component | A large stack component was restarted for an unrelated reason during the outage window | The endpoint's absence from every restart scope meant the restart left it dead | Restart coverage ends at the scope boundary; verify membership |
| Accepting a fleet inventory as ground truth | A status document listed only the components its machinery could supervise | The failing endpoint was invisible to that machinery, so the inventory showed no gap | Reproduce the client failure before accepting an inventory |
| Flagging only missing monitoring | The endpoint failure message surfaced as a generic client error | The monitor gap hid a start and restart gap of the same class | Diagnose ownership of all three duties, not only alerting |

## Results & Parameters

### Configuration

```yaml
supervision_inventory:
  per_endpoint:
    start_owner: required
    restart_owner: required
    liveness_signal: required
  watchdog:
    restart_on: nonzero-exit
    stop_on: exit-0
    give_up_after: 5-sub-threshold-failures
    give_up_exit_code: 42
```

### Expected Output

- A table mapping every client-reachable endpoint to a start owner, a restart owner, and a liveness signal.
- For each formerly unsupervised daemon: a supervised start command, a maintenance-stop order (stop the supervisor first), and a connect-level liveness probe.
- A documented placement decision for any daemon whose transport binds it to specific hosts.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Shared-cluster inference deployment | Authorization endpoint for typed administrator operations over a local socket | Ad-hoc interactive process died; ten-day silence across an adjacent restart; restored through a supervised start plus runbook. See [notes](service-supervision-ownership-parity.notes.md). |

## References

- [Prove liveness before you report an outage](prove-long-running-process-liveness.md)
- [Diagnose Unix-socket reachability on shared storage](unix-socket-shared-fs-host-locality.md)
