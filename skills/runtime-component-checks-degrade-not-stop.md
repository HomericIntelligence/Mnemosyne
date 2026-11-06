---
name: runtime-component-checks-degrade-not-stop
license: BSD-3-Clause
description: "Keep post-launch checks from stopping, evicting, or marking unhealthy a running component. Use when: (1) a review or design adds a check on identity records, digests, manifests, mode bits, release or context drift, or a peer's state to a running component; (2) a running service exits, ends its allocation, or reports unhealthy because a verification did not agree with its records; (3) a component cannot start because a peer component is not up yet; (4) a startup guard and the request path both apply the same trust rule and one of them stops the process; (5) an author defends a launch-time refusal with the words 'fail closed' for a check that runs after the component has started."
category: architecture
date: 2026-11-06
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - architecture
  - availability
  - fail-closed
  - degraded-mode
  - supervision
  - startup-checks
  - identity-verification
  - trust-boundary
  - service-ownership
---

# Runtime Component Checks Degrade, They Do Not Stop

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-06 |
| **Objective** | Decide where a verification check may stop a running component, and where it must only log, retry, and report degraded, so one disagreement or one absent peer does not take a lane down |
| **Outcome** | Operational. The rule was adopted as a repository-wide contract after an outage family in which post-launch record checks stopped healthy components |

## When to Use

Apply this skill when any condition holds:

- A check is added, or reviewed, for a component that **has already started**: an identity record, a
  digest, a manifest, a mode bit, release or context drift, or the state of a peer component.
- A running service exits, ends its allocation, or reports unhealthy because a verification did not
  agree with a record or with another component.
- A component cannot start because a peer is not up, and the two form a startup order.
- The same trust rule is applied twice: once before launch and once at request time, and one of the
  applications stops the process.
- An author defends a refusal that happens after start with "fail closed" without naming what the
  check protects.

Do not apply this skill to **request-time** authentication, authorization, or input rejection, and
do not use it to weaken a **pre-launch** trust-boundary check. These stay fail-closed; see the
decision table.

## Verified Workflow

### Quick Reference

Decide by **when the check runs** and **what it protects**:

| Check | Runs | Refusal is allowed when |
| --- | --- | --- |
| Authentication, authorization, input rejection | request time | Always. A refused request is not a stopped component. |
| Secrets, and paths that can write outside the lane | before launch | Always. A component that cannot reach its secret or would write outside its lane must not launch. |
| Identity records, digests, manifests, mode bits, release or context drift, a peer's state | **after** launch | Only where an owner-approved issue or the repository contract names that exact refusal. |
| A peer that is not up | after launch | Never. Wait, retry on a bounded schedule, and report degraded. |
| Recovery of a component that already failed | recovery | Only where an owner-approved issue names the refusal to restore what cannot be verified. |

One-line rule: **a running component degrades; it does not stop.**

### Suggested Approach

1. Classify the check by the table above before you change any code. The deciding fact is the
   moment the check runs, not the strength of the verification.
2. For a post-launch check with no owner-approved refusal, split it into three parts:
   - the **record** stays: log identity, digest, manifest, and drift findings for traceability;
   - the **reaction** becomes degrade: set a bounded degraded state, report it, retry on a schedule;
   - the **stop** is removed. Do not replace a stop with a silent pass.
3. Make each component start on its own. A peer that is not up is a normal state, not a failure
   condition: retry with backoff, expose the degraded state where health is read, and recover when
   the peer arrives. Do not create a startup order between independent components.
4. Keep the request path as the enforcement point. A record mismatch that matters becomes a
   request-time refusal with a caused, bounded error, not a process exit.
5. When you review such a change, look for the three shapes in the review checklist below. Treat a
   pass that returns "unhealthy" to an orchestrator as a stop.
6. Record in the change why any remaining refusal is authorized, and name the owner-approved issue
   or contract clause. An unrecorded refusal is a defect even when it is correct in spirit.

### Review checklist

- [ ] Does any post-launch check call `exit`, abort the allocation, mark the component unhealthy, or
      refuse to continue?
- [ ] Is a peer treated as required at start?
- [ ] Does a record check (digest, manifest, mode, drift) stop the process instead of logging?
- [ ] Is the same trust rule both a start gate and a request gate? Only the request gate may refuse.
- [ ] Does a remaining refusal cite its authorization?

### Degraded Conditions

- If the component cannot report degraded health yet, log the finding at a stable rate and keep
  serving. Add the health field before you add the check.
- If a post-launch check protects something whose failure is unacceptable (for example a wrong
  lane's credentials), route the refusal to request time. Do not restore the exit.
- If an owner-approved issue already names a refusal, leave it. Cite the issue in the code comment.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | ---------------- | --------------- | -------------- |
| Kept a post-launch record check as a process exit and called it "fail closed" | The check compared a record with the running state and exited on a mismatch | The component was already serving; the exit converted one bad record into a full outage, and a restart loop repeated it | Attach "fail closed" to a check by its **timing**, not its intent. A post-launch check fails a request, not the component. |
| Made each component wait for its peer before starting | A startup order was added so a peer would always be present | The order made an independent component's availability depend on another component, and a single absent peer stopped everything downstream | A peer that is not up is a normal state. Retry and degrade instead of ordering the starts. |
| Applied the same trust check at launch and at request time | The launch check stopped the component, the request check refused the request | The launch check had no way to refuse a single request, so it stopped all of them | Keep one enforcement point, and put it where the refusal can be scoped: request time. |

## Results & Parameters

### Configuration

```yaml
component_check_policy:
  request_time: fail_closed          # authentication, authorization, input
  pre_launch: fail_closed            # secrets, out-of-lane write paths
  post_launch_record: log_and_degrade # identity, digest, manifest, mode, drift
  peer_state: retry_and_degrade       # never a start gate
  allowed_stop: only_where_owner_approved
  degraded_reporting:
    log_rate: bounded
    health_field: required
```

### Expected Output

- A component starts with no peer up and reports degraded until the peer is available.
- A record, digest, manifest, mode, or drift mismatch is logged with its identity, and the component
  keeps serving; a request that depends on the mismatch is refused with a bounded error.
- Every remaining post-launch refusal cites its authorization.
- A checkpoint: grep the component for exits and health transitions on the post-launch check path;
  the result is empty, or each hit names its owner-approved issue.

## Verified On

| Project | Context | Details |
| --------- | --------- | ------- |
| Comet | Repository contract adoption, 2026-11 | The rule entered the repository agent contract as a named section for all components. See [notes](runtime-component-checks-degrade-not-stop.notes.md). |

## References

- [ASD-STE100 technical English](../docs/asd-ste100.md)
- [Service startup precondition bootstrap deadlock](service-startup-precondition-bootstrap-deadlock.md)
- [Supervised restart with stale worker state](supervised-restart-stale-worker-state-guard.md)
- [Readiness, closed status, and local alert recovery](observability-readiness-closed-status-local-alert-recovery.md)