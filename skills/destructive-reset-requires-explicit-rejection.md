---
name: destructive-reset-requires-explicit-rejection
license: BSD-3-Clause
description: "Gate destructive local-state resets in self-healing scripts on an explicit server rejection class (HTTP 401/403 or an equivalent deny verdict); treat timeouts, transport errors, and 5xx as service-unavailable and keep the state. Use when writing or debugging recovery, onboarding, or credential-repair automation that deletes local state before re-creating it, especially behind a server-side uniqueness policy."
category: debugging
date: 2026-10-23
version: "1.0.0"
user-invocable: false
tags:
- error-classification
- destructive-recovery
- credential-reset
- entitlement-uniqueness-policy
- transient-errors
---

# Skill: destructive-reset-requires-explicit-rejection

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-23 |
| **Objective** | Stop self-healing automation from converting recoverable remote-service failures into orphaned server-side entitlements |
| **Outcome** | Two production incidents root-caused to a missing error classification; after gating the reset on explicit rejection only, no recurrence during continued endpoint flakiness |

## When to Use

Use this skill when:

- You are writing or reviewing a script that deletes or resets local state (credentials, key material, config, journals, caches) when a remote validation check fails.
- A server-side uniqueness policy exists (one active key, seat, claim, or entitlement per principal) whose conflicts block re-creation of the same resource.
- You are debugging an incident of the shape "user re-registers but the server answers `conflict` forever after a local reset".
- A retry/recover path treats every failure class identically (rejection, timeout, 5xx, transport) and one of its branches is irreversible.

**Trigger symptoms**:

```text
identity check: HTTP 502 / ReadTimeout          (endpoint degraded, key never evaluated)
script:        "stale state; resetting"          (wrong: resets a valid or pending key)
server after:  entitlement still active, material lost  (orphan)
re-register:   conflict, conflict, conflict ...  (one-active policy blocks recovery)
```

## Verified Workflow

### Quick Reference

Classify the failure before any irreversible step. Destruction requires the strongest evidence: an authoritative rejection of the state itself.

```bash
# destructive reset ONLY on explicit rejection
if remote_check_fails; then
  if error_is_explicit_rejection; then   # e.g. HTTP 401/403, "rejected", "unauthorized", "denied"
    backup_local_state                   # always backup before a state change you cannot reverse
    reset_local_state
  else                                   # timeout, 5xx, transport, TLS/DNS, parse failure, unknown
    fail_soft_keep_state_and_report      # service is unhealthy; the local state may be valid
  fi
fi
```

### Suggested Approach

Distinguish *rejection* from *unavailability*. A rejection (401/403, explicit deny) means the server evaluated the presented state and refused it — destruction of that state is justified because the goal is to re-create state the server will accept. Unavailability (timeout, connection error, 5xx, TLS/DNS failure, unparseable response, or an unknown error) means the server never evaluated the state — the state may be perfectly valid, so keep it, report the service problem, and retry.

Remember that local deletion never revokes remote entitlements. The server keeps its record under its own authority. Behind a uniqueness policy, deleting the only client copy of an otherwise-active entitlement creates an *orphan*: the server counts the entitlement as held, every re-creation attempt conflicts, and no client holds the material to use or revoke it. Recovery then needs privileged backend access (an audited administrative revoke or a direct row update reconciled to the audit trail), not more retries.

Make fail-soft the default branch. Classify unknown, ambiguous, or mixed evidence as transient. Destruction without backup is irreversible, so it belongs on the branch with the strongest evidence, never on `else` by accident. When the remote check itself is intermittent, treat a single failure as transient evidence, and consider requiring consecutive observations of the rejection class before destroying.

Do not re-verify redundantly. If a check already validated the state moments earlier in the same run, do not add a second remote call with the same purpose — each extra call is one more exposure to endpoint flakiness, and (per this rule) one more chance for a misclassification. Reuse the earlier positive result and proceed to behavioural validation (an end-to-end operation that exercises the state) as the final gate instead of repeating the identity check.

If self-serve flows queue requests for a worker to fulfill, note a second-order mechanism: a published result can short-circuit re-evaluation of the same request, so after the blocking condition is fixed, clear the stale result (or submit a fresh request) before re-fulfilling. See [notes](destructive-reset-requires-explicit-rejection.notes.md) for the generalized incident mechanics and the exact gate implementation used in production.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Reset on any failure | A self-serve onboarding script reset local credential state whenever the remote identity check failed, with no error classification | An HTTP 502 from a degraded identity endpoint (capacity churn on the serving layer) triggered the branch; the script discarded valid pending state and re-registered | During transient endpoint degradation, "any failure" is mostly not a rejection; every reset on a transient blip destroys state the user needs |
| Reset on read-timeout | The same script later saw a `ReadTimeout` on the same endpoint and reset a fresh, confirmed-working key | The server still held the key as active (timeout ≠ rejection), the one-active-key policy returned permanent `conflict` on re-registration, and the user stayed wedged until an operator revoked the orphaned row with an audited administrative action | Timeout is unavailability, not rejection; local deletion does not revoke remote entitlements; conflict loops after an orphan is created require operator rescue, not retries |

## Results & Parameters

### Configuration

```text
rejection_classes:      HTTP 401, HTTP 403, explicit "rejected"/"denied"/"revoked" verdicts
unavailable_classes:    timeout, connection error, HTTP 5xx, TLS/DNS failure, unparseable or empty response
default_classification: unavailable   # unknown or ambiguous evidence never authorizes destruction
preconditions:          backup the state before reset; confirm the server can re-issue before deleting
```

### Expected Output

- Destructive resets fire only when the server authoritatively refused well-formed presented state.
- Transient incidents end with local state intact and a "service degraded, retry shortly" outcome.
- Zero orphaned entitlements from recovery automation; no operator-rescue conflict loops.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Internal model-serving platform | Production rollout: self-serve credential onboarding across multiple users during endpoint capacity churn | [notes.md](destructive-reset-requires-explicit-rejection.notes.md) |

## References

- Related error-classification sibling (retry-side taxonomy for transient families): [automation-529-overload-not-retried-classifier-gap.md](automation-529-overload-not-retried-classifier-gap.md)
