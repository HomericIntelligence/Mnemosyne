---
name: scheduler-service-replacement-identity-continuity
license: BSD-3-Clause
description: "Preserve a scheduler-managed service's execution identity across walltime renewal and replacement. Use when: (1) a long-running service can outlive one allocation, (2) restart may be invoked by a different operator, or (3) private state and credentials are owned by the original service identity."
category: architecture
date: 2026-08-21
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [scheduler, service-lifecycle, walltime, restart, identity, ownership, credentials, fail-closed]
---

# Scheduler Service Replacement Identity Continuity

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-21 |
| **Objective** | Keep a persistent service available across scheduler allocation expiry without changing its authoritative execution identity. |
| **Outcome** | A reusable lifecycle contract that separates operator identity from service identity, treats walltime as an explicit terminal event, and fails closed before a replacement can run as the wrong owner. |
| **Verification** | verified-local from scheduler accounting and service logs, with sensitive incident coordinates removed. |

## When to Use

- A gateway, controller, or other persistent service runs inside a scheduler allocation with a finite walltime.
- A restart or replacement command may be issued by someone other than the identity that owns the service state.
- Credentials, sockets, or state files are intentionally private to the service owner.
- A launch uses a requeue option and operators assume it automatically renews a job after walltime expiry.
- A replacement allocation is accepted by the scheduler but the service fails before startup because its effective identity changed.

Do not use mutable job names, the current CLI caller, or filesystem accessibility as proof of service ownership. Use an explicit durable service identity or a fixed service account authorized by the deployment contract.

## Verified Workflow

### Quick Reference

```text
Persist: service_id + authoritative_execution_identity + active_allocation_id
Observe: scheduler terminal reason and remaining walltime
Renew: before expiry, or explicitly replace after a terminal event
Replace: submit through the authoritative identity boundary
Verify: scheduler owner == recorded identity before publishing the service
Fail closed: missing, stale, conflicting, or unauthorized identity
```

### Detailed Steps

1. **Model walltime as a lifecycle boundary.** Record the allocation time limit and monitor remaining time. A scheduler's requeue flag commonly expresses eligibility for selected requeue events; it is not proof that walltime expiry creates a fresh allocation or renews the limit. Handle `TIMEOUT` or the scheduler's equivalent as an explicit terminal reason.
2. **Persist service authority separately from the caller.** Durable service state must bind a stable service identifier to its authoritative execution identity. The user invoking `restart` is an operator principal, not an implicit replacement owner.
3. **Choose one supported identity model.** Either run every generation under a fixed service account, or retain the original authorized scheduler/filesystem owner for the service lifetime. If cross-user operation is supported, route it through a narrowly scoped owner-run service or delegated control API; do not impersonate by copying ambient user context.
4. **Renew before expiry or replace deliberately.** Start controlled replacement early enough to launch, restore state, pass readiness checks, and transfer traffic before the old allocation expires. If the old allocation has already terminated, classify the reason and explicitly submit a replacement; do not wait for an assumed automatic renewal.
5. **Validate identity before launch and publication.** Compare the scheduler-reported owner of the replacement with the durable authoritative identity. Confirm private state and credentials remain readable by that identity without changing their protection. Reject the replacement before traffic publication on any mismatch.
6. **Update allocation state atomically.** Persist the new allocation identifier only after scheduler ownership is verified. Publish the service only after readiness succeeds. Preserve the prior terminal allocation and reason as audit evidence rather than overwriting it.
7. **Test behavior, not just submission.** Exercise walltime expiry, pre-expiry replacement, a different invoking operator, missing identity state, stale allocation state, scheduler-owner mismatch, and readiness failure. A successful scheduler submission is not sufficient evidence; tests must assert the effective owner and service availability transition.

### Minimal state and transition contract

```yaml
service:
  id: <stable-service-id>
  execution_identity: <authoritative-principal>
  active_allocation_id: <scheduler-allocation-id>
  generation: <monotonic-generation>

replacement:
  allowed_when:
    - execution_identity_is_present
    - caller_is_authorized_to_request_restart
    - scheduler_submission_uses_execution_identity
    - reported_scheduler_owner_matches_execution_identity
  publish_after:
    - replacement_is_ready
    - durable_allocation_state_is_committed
  deny_when:
    - identity_is_missing_stale_or_conflicting
    - scheduler_owner_differs
    - private_state_requires_permission_weakening
```

The exact delegation mechanism is deployment-specific, but its contract is not: an authorized operator may request a restart without becoming the service's execution identity.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Treat requeue eligibility as walltime renewal | Enabled scheduler requeue support and expected a time-limited persistent service to continue automatically | The allocation reached its terminal walltime without creating a replacement generation | Monitor walltime and implement explicit controlled renewal or terminal-event replacement |
| Derive replacement owner from the invoking caller | Submitted the new allocation as whichever operator ran the restart command | The new process could not read owner-restricted service credentials and state | Separate operator authorization from durable execution identity |
| Loosen private-file permissions | Considered making credentials broadly readable so a different replacement owner could start | This converts an identity bug into a credential exposure and still leaves ownership ambiguous | Preserve least-privilege permissions and fix the execution-identity boundary |
| Trust scheduler acceptance | Treated a returned allocation identifier as proof that replacement was valid | Submission can succeed under the wrong owner and fail before service readiness | Re-query and compare scheduler ownership before committing or publishing the replacement |
| Use a mutable job name as authority | Inferred ownership from a shared display label | Names can collide, be reused, and carry no authorization proof | Persist a stable service identity and authoritative principal explicitly |

## Results & Parameters

### Required invariants

| Invariant | Required behavior |
| --------- | ----------------- |
| Service identity | Stable across allocation generations |
| Operator identity | Authorizes the request but never silently replaces service ownership |
| Execution identity | Explicit, durable, and verified against scheduler state |
| Walltime | Monitored as a terminal boundary with renewal lead time |
| Requeue | Treated as scheduler-specific eligibility, not assumed periodic renewal |
| Private state | Remains least-privilege; no permission broadening as recovery |
| State update | New allocation committed only after owner verification |
| Publication | Occurs only after readiness and durable state commit |
| Unknown identity | Fails closed with an actionable ownership error |

### Behavior-first acceptance matrix

| Scenario | Expected result |
| -------- | --------------- |
| Same authorized operator requests replacement | New allocation runs as the durable execution identity |
| Different authorized operator requests replacement | Request succeeds through delegation; execution identity remains unchanged |
| Unauthorized operator requests replacement | Request is denied before scheduler submission |
| Allocation reaches walltime | Terminal reason is observed and explicit recovery begins; no silent availability assumption |
| Scheduler reports a different owner | Replacement is rejected and not published |
| Durable identity is missing or stale | Replacement fails closed with remediation guidance |
| Private credentials are owner-only | Replacement reads them as the same authoritative identity; permissions remain unchanged |
| Replacement fails readiness | Old generation remains authoritative when still live; failed generation is not published |

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Project-neutral scheduler-backed service | Incident diagnosis of a walltime terminal event followed by a cross-identity replacement failure | Scheduler accounting established the terminal reason; service logs established that the replacement identity could not access owner-private startup state. Sensitive coordinates were intentionally omitted. |

## References

- [Slurm wrap shell contract](slurm-wrap-shell-contract.md)
- [Service validation on a fresh isolated allocation](service-validation-fresh-isolated-allocation.md)
- [Autoscaling template promotion evidence](autoscaling-template-promotion-evidence.md)
