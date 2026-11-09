---
name: live-lane-consistency-scan-tolerates-writers
license: BSD-3-Clause
description: "Keep a whole-tree consistency scan (inventory, attestation, pre-migration check) completable while the serving lane keeps writing state. Use when: (1) a scan or receipt aborts with a vanished file or a file-identity mismatch on a system that is serving; (2) one failed long scan makes every other request to a single-dispatch control service answer 'busy'; (3) a release sequence step requires a consistency record that no earlier step produces; or (4) a control daemon must start on a node that has no user service manager."
category: architecture
date: 2026-11-09
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - consistency-scan
  - inventory
  - attestation
  - live-writers
  - atomic-rename
  - single-dispatch
  - operator-daemon
  - release-sequence
  - precondition-gap
  - host-locality
  - scheduler-step
---

# Live-Lane Consistency Scan Tolerates Writers

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-09 |
| **Objective** | Make a whole-tree consistency scan complete on a serving system, and make the release sequence that depends on it fail before its first write instead of after. |
| **Outcome** | Operational as diagnosis and design rule. Three failures were proven live in one production promotion: the scan aborted on a file that a live writer had replaced mid-scan; the failed scan wedged the control daemon's single dispatch lane; and the step that required the scan's record ran long after it should have. The start model and the sequence order are proven by the run; the scan's tolerance rule is the required correction. |
| **Verification** | verified-live: three distinct scan failures diagnosed from operation records and process evidence in one production run. The corrected scans are not yet deployed. |

## When to Use

Use this skill when one of these conditions applies:

- A consistency scan walks a whole deployment tree (permissions, ownership, identity of declared paths) and must produce a receipt or attestation on a system that is serving requests.
- The scan aborts with a vanished temporary file, a file-identity mismatch, or a "changed during scan" error, and **a different path fails on each attempt**.
- One control service handles one request at a time, and a long failing request makes every other request answer "busy" until it ends.
- A release, or any ordered procedure, has a step that requires a record that no earlier step produces.
- A control daemon must start on a node where the user service manager is absent.

Do not use this skill for a same-object check on a single directory; that race has its own entry, `directory-identity-check-stable-stat-fields`. Do not use it for stopping the previous release's daemon before a repair; that is `cutover-stop-previous-release-daemon`.

## Verified Workflow

### Quick Reference

```text
1. A DIFFERENT FILE FAILS EACH RUN => concurrent-writer race, not a
   corrupt path. Stop retrying a full scan. Confirm: compare the failing
   names across attempts and the writers' file mtimes.
2. TOLERATE: report a path that changes identity during the scan as
   "changing" and complete the receipt. Or exclude declared-runtime paths
   from enumeration. Or retry a vanished entry a bounded number of times.
   Never fail the whole scan on a replaced file.
3. FREE THE SINGLE LANE: a scan that fails must not hold the dispatch
   critical section. Chunk it, or run it outside the queue, and return
   immediately on failure.
4. ORDER: every step's required record is produced by an earlier step,
   and the guard runs BEFORE the step's first write.
5. START THE DAEMON WHERE IT CAN RUN: use a scheduler step when the node
   has no user service manager; re-exec the step onto that node.
```

### Suggested Approach

1. **Classify the failure before the next attempt.** A scan that fails on a different path each time is a concurrency race: legitimate writers replace files within the scan window with write-to-temporary-then-rename. A scan that fails on the same path is a corrupt or divergent path. The two need different corrections, and a retry loop only confirms which one you have.

2. **Separate declared state from live runtime state.** A scan of permissions and ownership should enumerate the structure the operators establish, not the records the service rewrites every cycle (status, retry markers, per-job metric files, restart markers). Either exclude those path families by policy or report them as changing. This is the same boundary as "mutable runtime state is not structure."

3. **Make a changed entry a finding, not a failure.** When a path's identity changes between the directory scan and the identity check, record it as changing with its policy and continue. Repairs skip it; the next run picks it up. The receipt then states exactly which paths moved, which is more useful than one error naming the first victim.

4. **Release the control lane on failure.** If one request holds the dispatch queue, a 90-second failing scan denies every other verb. Bound the scan's critical section: scan outside the queue and commit the receipt inside it, or chunk the walk and yield. A busy answer on an unrelated verb during a failed scan is the symptom that the lane was not released.

5. **Check sequence order against produced records.** Walk the ordered steps and ask for each: which step writes the record this step consumes? A step that requires a record nothing produces fails late, after writes, and is not resumable without redoing them. Move the producing step earlier and add the same guard before the first write of the consuming step.

6. **Choose the start mechanism by what the node provides.** A user service manager is not guaranteed on a compute node. Where it is absent, start the daemon as a scheduler step inside the allocation that the daemon manages: it survives the calling shell and ends only with that allocation. Re-exec the step onto the node that owns the socket, because a unix socket is host-local.

7. **Keep the daemon-start choreography.** Changing the start mechanism does not change the safe sequence: skip when an operator already accepts the target context, validate the configuration without a socket, stop the prior daemon through its own tree, wait for readiness and prove context registration, then check liveness at two intervals.

8. **Bind cross-release helper state to the release that owns it.** A supervision helper left from a previous release will restart the previous daemon. Take its claim for the window between stop and start, and release it on failure so the prior daemon returns. Do not leave a shipped step depending on a previous run's directory.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | --------------- |
| Retry the full scan | Rerun the scan after a vanished-temp-file error | A different declared file failed on the second run (a per-job metric file), and the failed scan held the control lane for the whole window | A different victim each run proves a writer race; a retry re-enters it and extends the outage |
| Restart the control daemon to clear the lane | Restart the daemon so the dispatch queue starts empty | The next verb still answered "busy" for the first seconds after restart, and the underlying race was untouched | The lane is not the defect; bound the scan's critical section instead |
| Run the verb from the wrong host | Run the path verb from a login host while the daemon served from a compute host | Connection refused: the socket is host-local, and nothing listens on the other host | Resolve the daemon's host and re-exec there; do not treat a transport refusal as a service defect |
| Trust the step order in the README | Follow the documented order and expect each step's inputs to exist | The promotion-validation step required a recorded attestation that no step produced, and failed after authoring records and building manifests | Audit each step's consumed records against the producing steps, and guard before the first write |

## Results & Parameters

### Configuration

```yaml
scan_tolerance:
  declared_structure: [permissions, ownership, identity of established paths]
  runtime_records_excluded: [status files, retry markers, per-job metrics, restart markers]
  changed_during_scan: report as "changing", keep the receipt, repair later
  bounded_retry: only for a vanished entry; never a full-scan loop
single_dispatch_lane:
  scan_outside_the_queue: true
  on_failure: release the lane, return the evidence, do not block the queue
sequence_guard:
  rule: the producing step precedes the consuming step
  placement: before the consuming step's first write
daemon_start:
  subscriptions: no user service manager on the node
  model: scheduler step inside the managed allocation
  host_resolution: re-exec onto the node that owns the socket
liveness_checks: [30 s after start, 5 min after start]
```

### Expected Output

- A scan returns a receipt digest on a serving system, repeatedly and with no failing path.
- Any path that moved is named in the receipt as changing, not raised as a single error.
- Unrelated control verbs answer normally during and after a scan.
- A step that lacks its required record stops before it writes.
- The control daemon starts on a node without a user service manager and passes its liveness checks.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Shared-cluster multi-model inference deployment (scheduler-managed lane, per-release control daemon, host-local socket, live supervisor rewriting state) | A production promotion hit all three failures in one run; scan, lane, and sequence evidence recorded from operation records and the process table | Generalized evidence in [notes](live-lane-consistency-scan-tolerates-writers.notes.md); host, product, and path identifiers omitted |

## References

- [directory-identity-check-stable-stat-fields](directory-identity-check-stable-stat-fields.md) — the single-directory same-object check and its stable stat fields
- [cutover-stop-previous-release-daemon](cutover-stop-previous-release-daemon.md) — stopping the previous release's daemon before a consistency-checked repair
- [unix-socket-shared-fs-host-locality](unix-socket-shared-fs-host-locality.md) — why the socket, and the step that uses it, are host-local
- [systemd-user-linger-without-root](systemd-user-linger-without-root.md) — the user-manager path when the node has a bus