---
name: cutover-stop-previous-release-daemon
license: BSD-3-Clause
description: "Stop the previous release's foreground host daemon through a supported, release-pinned stop before a consistency-checked repair and before the new release's daemon start at a cutover. Use when: (1) a rollout stops the old release's scheduler allocations but leaves its foreground host daemons running, (2) a fail-closed consistency proof rolls back because a live daemon keeps writing its liveness file, (3) a new daemon start can collide with a still-live old daemon's singleton socket or lock, or (4) a deployed stop must verify exact release identity in /proc before it sends any signal."
category: tooling
date: 2026-10-26
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - cutover
  - release-migration
  - foreground-daemon
  - stop-ordering
  - fail-closed
  - consistency-proof
  - release-identity
  - proc-identity
  - pid-reuse
  - pidfd
  - watchdog-supervision
  - singleton-lock
  - liveness-heartbeat
  - idempotent-stop
---

# Stop the Previous Release's Daemon Before the Repair and the New Start

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-26 |
| **Objective** | Give a release cutover one supported, idempotent stop for the previous release's foreground host daemon, placed before any consistency-checked repair and before the new release's daemon start. |
| **Outcome** | Designed, implemented, and tested. The cutover had stopped the old release's scheduler allocations (gateway, replicas, donors) but never its foreground host daemon. The live daemon kept writing its heartbeat, a fail-closed service-path repair rolled back with an inventory-changed error, and the new daemon start could collide with the old daemon's singleton socket and lock. A pid-stamped, release-pinned stop command with a runbook placement now stops the old daemon and proves the stop before the repair and the new start. |
| **Verification** | The cause and the manual workaround were verified live in one production cutover. The supported stop is verified by behavior tests for every decision branch (release identity acceptance and refusal, idempotence, watchdog selection, exit and freeze proofs, host-scoped paths) and by the implementation review; the live cutover run of the new command is a documented, gated, separate evidence step. See [notes](cutover-stop-previous-release-daemon.notes.md). |

## When to Use

- A release cutover or migration stops the old release's scheduler allocations, and the old release also runs one or more foreground host daemons (operator, registrar, supervisor-helper) that no scheduler step stops.
- A fail-closed path repair, migration, or transition proof rolls back with an inventory-changed or inventory-diverged error while a live daemon keeps writing its liveness file. This failure is a rollback, not a mode change: nothing was repaired.
- The new release's daemon start holds a singleton through a socket, lock file, or pidfile that a still-live old daemon also owns.
- You design or review the stop itself, and the process to stop always belongs to the previous release.

Do not use this skill for a routine single-service restart that changes no release and runs no consistency-checked repair. Do not assume an allocation stop, a drain verb, or a resilience teardown stops a foreground host daemon; verify supervision ownership per service.

## Verified Workflow

### Quick Reference

```text
1. ORDER: stop the old release's foreground daemons after the allocation
   stop, before every consistency-checked repair, and before each new
   daemon start.
2. IDENTITY: verify the exact release in /proc from literal paths (argv[0],
   argv[1], exe); never resolve a "current" link; an unknown layout fails
   closed and sends no signal.
3. SIGNAL: the supervision owner (the watchdog when one is verified), else
   the daemon; never SIGKILL from the stop tool.
4. PROOF: process exit through a pidfd, a liveness file that stays
   unchanged over a fixed window, and a singleton lock that is free.
5. IDEMPOTENCE: no heartbeat, a pid that does not run, or a reused pid
   with a free lock is already_stopped; repeat calls are safe.
```

### Suggested Approach

1. **Inventory the foreground daemons of the old release.** Allocation stops and drain verbs do not stop daemons that run on administrator hosts. Enumerate them through their heartbeat or socket and the process table, not through the scheduler. See [service-supervision-ownership-parity](service-supervision-ownership-parity.md): every service needs exactly one owner for start, restart, and liveness.

2. **Use a pid-stamped stop through a supported command, not a socket action.** The old daemon speaks the previous release's request protocol and rejects requests from a different release context. Every release that publishes a heartbeat with `pid`, `service_host`, and `heartbeat_at` can be stopped by a signal, older releases included. Put the stop on a release-independent path: it must not pass the attestation or consistency gates that the repair step exists to re-seal, because the stop runs while those records can still diverge.

3. **Place the stop by evidence, not by age rules.** A heartbeat-age gate on start-up blocks a legal stop → repair → start on a different host and blocks a crash failover. Prevent the start collision with the stop's own proof (process gone, singleton lock free, liveness frozen) and with the documented runbook order. Do not add age-based refusals to serve.

4. **Verify the exact release identity in `/proc` before any signal.** Collect three literal candidates: argv[0], argv[1], and `realpath`-free `/proc/<pid>/exe` (the kernel already resolves the executed image). Release publication typically rewrites console-script shebangs to a literal release interpreter path, so argv[0] names the release even when the interpreter binary links out to a base Python; for release venvs that put the interpreter home in the release tree, `exe` names the release too. The stop passes only when all of these hold:
   - at least one candidate lies in the expected release tree;
   - no candidate lies in a different release tree; and
   - no candidate is resolved through a `current` symlink. A literal `current` path counts as neutral, never as a match.

   Fail closed on an unknown layout: print the three candidates and send no signal. The operator then uses the documented manual procedure after examining the evidence.

5. **Apply the remaining identity checks before the signal.** The cmdline names the daemon's serve verb for the target root, not a wait or status command. The process UID equals the service principal. The heartbeat cluster equals the target cluster. The heartbeat host equals the local host; when it does not, refuse and name the remote host (for example, for `srun -w <host>`). Liveness and identity checks are host-local, so the command never signals a process on a different host.

6. **Signal the supervision owner when one is verified.** A supervised daemon restarts after a nonzero exit, so signaling the child only defeats the stop. Detect the supervisor from the parent pid: its cmdline contains the watchdog script name followed by a separator, its post-separator arguments equal the daemon's arguments after its interpreter and script, and its UID equals the daemon UID. Signal the watchdog and wait for the exit of both. A parent that does not match receives no signal. Never send SIGKILL: a watchdog escalates by its own stop grace, and a tool-side kill hides the mismatch that a frozen-heartbeat proof would have shown.

7. **Prevent pid reuse.** Open a pidfd for the process before the identity checks, re-read the identity after the open, signal through the pidfd, and poll the pidfd for the exit. A pid read from a heartbeat and signaled directly can reach an unrelated process that reused the number.

8. **Make the stop idempotent with a lock-based decision.**
   - No heartbeat → lock proof → `already_stopped`.
   - Heartbeat pid does not run on this host → lock proof → `already_stopped`.
   - Heartbeat pid runs but is not a serve of the target (an unrelated process reused the pid) → lock proof: a free lock yields `already_stopped` with a reused-pid marker and no signal; a held lock is a refusal.
   - Heartbeat pid runs and is a serve of the target but of a different release (for example, the new release) → refusal and no signal.
   - A repeated call after a successful stop returns `already_stopped`.

9. **Prove the stop with the liveness record that the next steps trust.** After the exit, read `heartbeat_at` and the file modification time, wait a short fixed window, and read them again: both must stay unchanged. Then prove that the singleton lock takes. Do not delete the heartbeat: the repair's consistency proof then sees one stable object. Only after the frozen liveness record and the free lock is it safe to run the consistency-checked repair and the new start.

10. **Record the runbook placement and any external owner.** Put the stop in the documented release order before the repair steps and before the new start. When the rollout automation lives outside the repository, state the gap in the deliverable and name each call point: after the allocation stop, before every consistency-checked repair, and before the new daemon start.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Allocation-only cutover | The cutover stopped the old release's scheduler allocations and retired gateway evidence, but never the old release's operator daemon | The live daemon kept writing its heartbeat; the service-path apply re-inventory diverged from the receipt within seconds and rolled back fail-closed; the new daemon start could collide with the old daemon's socket and lock | An allocation stop is not a daemon stop; the supported stop belongs before the repair and before the new start |
| Socket shutdown action through the new release's protocol | Considered adding an operator shutdown action for the stop | The process to stop always belongs to the previous release: it has no such action and rejects requests from a different release context | A pid-stamped stop works on every release that publishes pid and host in its heartbeat |
| Heartbeat-age start refusal | The first design made start-up refuse a stale heartbeat to prevent the new/old collision | A correct stop leaves a frozen heartbeat, so the age rule blocked the legal stop → repair → start sequence on a different host and blocked a crash failover during the refusal window | Use the stop's own evidence (process gone, lock free, liveness frozen) plus runbook order; never an age gate |
| Resolving the `current` interpreter path as identity | Considered resolving `venv/current` (or an equivalent link) to classify the process release | The link can have been re-pointed before the stop, so the resolved path can name the wrong release | Classify from literal argv paths and the kernel-resolved executed image only; a literal `current` path counts as neutral |

## Results & Parameters

### Configuration

```yaml
stop_decision:
  identity_candidates: [argv0, argv1, proc_pid_exe]
  rule: at least one candidate in the expected release tree; none in another
    release tree; no candidate resolved through a current link; unknown
    layout fails closed and sends no signal
  pre_signal_checks: [serve verb for the target root, process uid, heartbeat
    cluster, heartbeat host is local; a different host is a refusal that
    names the host]
signal:
  target: verified watchdog parent when present, else the daemon pid
  rule: never SIGKILL from the stop tool; the watchdog escalates by its own
    stop grace
pid_reuse: open a pidfd and re-read the identity before signaling; wait by
  polling the pidfd
proof:
  exit_grace: watchdog stop grace plus a margin (30 s verified)
  freeze_window: 2 s; heartbeat_at and modification time stay unchanged
  singleton_lock: exclusive lock takes after the exit
  heartbeat_file: never deleted; the repair sees one stable object
idempotence:
  already_stopped: [no heartbeat, pid not running, reused pid with free lock]
  refusal: [reused pid with held lock, serve of a different release, failed
    identity check; refusal sends no signal and prints the evidence]
```

### Expected Output

- The old daemon is stopped with the evidence trail: `outcome: stopped` or
  `outcome: already_stopped`, both with `lock_free: true`.
- The heartbeat stays frozen and the singleton lock is free, so the
  consistency-checked repair no longer rolls back on an inventory change,
  and the new release's daemon start holds the socket and lock alone.
- A refusal names the failing check and the process evidence, and sends no
  signal.
- The runbook places the stop before the repair and the new start; any
  external rollout owner and its call points are documented.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Shared-cluster multi-model inference deployment (Slurm, per-release interpreter trees, foreground operator daemon with a liveness heartbeat) | A production cutover hit the allocation-only gap; the manual pid-stamped workaround stopped the old daemon; the supported stop command and runbook placement were implemented with behavior tests for every decision branch | Generalized evidence in [notes](cutover-stop-previous-release-daemon.notes.md); product, host, and schedulers identifiers intentionally omitted |

## References

- [service-supervision-ownership-parity](service-supervision-ownership-parity.md) — one owner for start, restart, and liveness; the inventory rule behind step 1
- [live-hotfix-content-addressed-identity-rotation](live-hotfix-content-addressed-identity-rotation.md) — the incident-side carrier purge; this entry covers the designed cutover stop, which the live-hotfix skill does the bypass for
- [unix-socket-shared-fs-host-locality](unix-socket-shared-fs-host-locality.md) — why the stop and its identity checks are host-local and a cross-host heartbeat is a refusal, not a signal
