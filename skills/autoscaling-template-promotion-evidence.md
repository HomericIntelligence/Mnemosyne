---
name: autoscaling-template-promotion-evidence
description: "Use when: (1) designing production admission for a route-eligible autoscaling pool, (2) deciding whether exact scale-out clones must repeat a soak, (3) defining durable evidence that separates template promotion from allocation-specific admission, (4) reviewing restart and relaunch invalidation rules for autoscaling safety."
category: architecture
date: 2026-07-29
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - autoscaling
  - production-promotion
  - soak-testing
  - durable-evidence
  - launch-identity
  - replica-admission
  - fail-closed
---

# Autoscaling Template Promotion Evidence

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-29 |
| **Objective** | Separate one-time production promotion of an exact frozen autoscaling pool template from the fresh safety checks required for each allocated clone. |
| **Outcome** | Architecture rule: the first reference instance completes the full production gate, including soak; same-launch exact clones inherit a protected durable template-promotion receipt instead of repeating soak, while still passing allocation-specific admission. |
| **Verification** | unverified — architecture and issue-plan review only; runtime implementation, executable validation, and production evidence are pending. |

## When to Use

- Designing a route-eligible autoscaling pool whose instances are exact
  realizations of a frozen launch-time template.
- Reviewing whether scale-out latency is being inflated by unnecessarily
  repeating a soak that already proved the exact template.
- Separating reusable template evidence from node-, allocation-, endpoint-, and
  route-specific evidence that cannot safely be inherited.
- Defining fail-closed behavior for missing, stale, or mismatched promotion
  evidence.
- Specifying whether controller restarts may reuse prior evidence and when a new
  launch or changed identity requires a fresh soak.

Do not use this pattern when replicas may drift from the promoted template, when
launch identity is not durable, or when the system cannot prove that a new
replica is an exact clone. In those cases, inherited soak evidence is unsafe.

## Verified Workflow

> **Planning-only status:** The repository requires this heading, but the
> workflow below is a proposed architecture-review contract, not a verified
> runtime implementation. Its verification level is `unverified`; implementation
> and executable evidence remain pending.

### Quick Reference

1. Freeze the route-eligible pool template and compute its identity digest at
   launch.
2. Start one reference instance for that exact template.
3. Run the complete production-promotion gate on the reference instance,
   including soak.
4. Persist a protected, durable template-promotion receipt before allowing
   clones to inherit the result.
5. For every same-launch exact clone, validate the receipt match and run fresh
   allocation-specific admission checks. Do not repeat soak.
6. Publish the clone only after both the inherited receipt and every fresh check
   pass.
7. Fail closed when the receipt is missing, unverifiable, invalidated, or does
   not match the clone's frozen identity.
8. Require a new reference promotion and soak for a new launch, a changed frozen
   identity, or changed promotion evidence. Reuse after a controller restart is
   allowed only when the same durable launch identity is restored and a
   separate durable ownership handoff authorizes the new controller.

### Detailed Steps

#### 1. Freeze and identify the promotable template

Define the smallest immutable identity that proves two instances are exact
realizations of the same route-eligible pool template. The identity should bind
at least:

- durable launch identity and target/pool identity;
- route and workload artifact or model/checkpoint digest;
- runtime image, serving engine, and execution profile;
- job class and node/CPU/GPU allocation shape;
- promotion policy and required software/fabric policy;
- the canonical template digest derived from those frozen inputs.

Do not use mutable display names or a subset of these facts as the receipt key.
Runtime policy edits must create a new identity or be rejected; otherwise an
old soak could authorize materially different replicas.

#### 2. Promote exactly one reference instance

The first reference instance for the frozen template must complete the full
production-promotion gate. That gate includes soak plus every product-required
fabric, API, benchmark, observability, isolation, and workload-specific safety
gate. No clone may inherit promotion before this reference gate succeeds.

The reference instance is not special after promotion because of its allocation
identifier. It is useful because it produced evidence for the exact frozen
template identity.

#### 3. Persist a protected template-promotion receipt

Write the receipt to durable state before permitting route publication based on
inherited evidence. The receipt should contain:

| Receipt field | Required meaning |
| ------------- | ---------------- |
| Receipt schema version | Enables explicit compatibility handling |
| Frozen template identity and digest | Exact inputs whose behavior was soaked |
| Durable launch identity | Restricts inheritance to the same launch |
| Reference allocation identity | Provides audit provenance |
| Gate policy version | Identifies the required production gate |
| Evidence digests and timestamps | Binds the decision to immutable evidence |
| Promotion result | Records a complete successful gate, not a partial pass |
| Issuer identity and epoch | Immutable provenance for the decision that created the receipt |
| Invalidation status and reason | Makes revocation explicit and auditable |

The receipt must be protected from ordinary replica lifecycle mutations,
atomically visible to admission decisions, and recoverable after an authorized
controller restart. Apply durable-write-before-state-advance discipline so a
clone cannot become publishable before its authorizing receipt is committed.
Do not rewrite the receipt merely because controller ownership changes. Keep
the historical issuer identity and epoch as immutable provenance, and store the
current controller lease or handoff epoch in a separate durable,
single-writer ownership record.

#### 4. Admit each clone with fresh allocation-specific evidence

An exact same-launch clone inherits only the template-level evidence, including
the completed soak. Every clone must independently pass fresh checks for:

- controller and scheduler ownership of the allocation;
- node, CPU, GPU, and accelerator health;
- allocation-local fabric preflight;
- direct readiness and canary API behavior;
- listener and route isolation;
- observability labels and identity;
- applicable mixture-of-experts communication admission.

These checks protect against facts that can differ even when the image and
template are identical. A successful template receipt must never bypass them.

#### 5. Publish through a two-part fail-closed decision

A clone is route-eligible only when both conditions are true:

1. A valid, durable template-promotion receipt exactly matches the clone's
   launch and frozen template identity.
2. The clone's fresh allocation-specific admission report is complete and
   successful.

Missing data, partial evidence, digest mismatches, unknown receipt schema
versions, or a missing, stale, or conflicting controller ownership record are
denials, not warnings. Keep the clone unpublished and expose the blocking
reason through status and alerts. A receipt's historical issuer epoch is not
stale merely because a compatible controller has taken ownership through a
valid durable handoff.

#### 6. Invalidate conservatively

Require a new reference promotion and soak when any frozen identity input
changes, when required promotion evidence changes or becomes invalid, or when a
new launch is created. A controller process restart may reuse the receipt only
if it restores the same durable launch identity, proves compatible state, and
acquires ownership through a durable single-writer lease or handoff record.
That record must fence the prior controller without mutating the receipt's
historical issuer provenance. A process restart is not permission to synthesize
a launch identity from mutable runtime state or infer ownership from the
receipt alone.

#### 7. Review the boundary with scenario-based acceptance criteria

Before implementation, require scenarios that prove:

- no clone publishes before the reference soak and durable receipt exist;
- an exact same-launch clone publishes after fresh admission without repeating
  soak;
- a clone with unhealthy allocation-local resources remains unpublished;
- a missing or mismatched receipt blocks publication;
- a changed template, policy, artifact, or launch identity requires re-soak;
- a compatible controller with a valid old-issuer-to-new-controller handoff
  reuses the receipt for the same durable launch;
- an incompatible restart, downgrade, conflicting controller, or untransferred
  ownership record is fenced;
- evidence and status make inherited versus fresh gates distinguishable.

Translate these scenarios into behavior-level tests and operational validation
during implementation. Do not substitute tests that merely search
documentation strings for executable admission behavior.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Soak every scale-out replica | Applied the entire initial production gate to each exact clone | Repeated a template-level proof, delaying capacity recovery without addressing allocation-specific failures more precisely | Soak the frozen template once; validate every allocation freshly |
| Trust the template receipt alone | Published clones solely because their template matched the reference | Exact software can still land on an unhealthy node, broken fabric, conflicting listener, or mislabeled telemetry | Inherited evidence and fresh allocation admission are both mandatory |
| Reuse promotion across launches | Treated an artifact or image digest as sufficient identity | Launch policy, execution shape, route ownership, and promotion requirements can change while the artifact stays constant | Bind the receipt to the complete frozen identity and durable launch |
| Keep promotion only in controller memory | Lost the receipt on restart or reconstructed it from partial runtime observations | Restart behavior became either unsafe or forced an unnecessary new soak with no auditable distinction | Persist a protected receipt before state advances, retain immutable issuer provenance, and restore only through a durable ownership handoff |
| Treat a mismatch as degraded-but-allowed | Warned on stale or incomplete receipt fields while continuing publication | Unknown evidence provenance became authorization for production traffic | Missing, stale, partial, or mismatched evidence must fail closed |

## Results & Parameters

### Evidence split

| Evidence scope | Run frequency | Examples | Inheritance |
| -------------- | ------------- | -------- | ----------- |
| Frozen template promotion | Once per exact template in a durable launch | Full production gates, benchmark, observability qualification, soak, workload-specific policy | Same-launch exact clones only |
| Allocation-specific admission | Every instance allocation | Ownership, node/CPU/GPU health, fabric preflight, direct/canary API, listener/route isolation, observability identity, applicable mixture-of-experts admission | Never inherited |

### Required parameters

| Parameter | Rule |
| --------- | ---- |
| Launch identity | Durable, immutable for the launch, and included in every receipt lookup |
| Template digest | Derived from all frozen route-eligible pool inputs |
| Receipt storage | Durable, protected, atomically readable, and auditable |
| Receipt match | Exact; partial or best-effort matches are forbidden |
| Clone soak | Not repeated after a valid same-launch template receipt |
| Clone admission | Fresh and complete for every allocation |
| Restart reuse | Same durable launch identity plus compatible state and a separate durable single-writer handoff; retain the receipt's historical issuer provenance |
| Invalidation | New launch, changed frozen identity, changed evidence, or explicit revocation |
| Failure posture | Keep the clone unpublished and report the blocking reason |

### Expected implementation outcome

- Initial production promotion remains conservative and includes a complete
  soak.
- Routine scale-out avoids soak latency only for exact, provable clones.
- Allocation-local defects cannot inherit a pass from the reference instance.
- Restart and relaunch semantics are deterministic and auditable.
- Operators can distinguish inherited template evidence from fresh
  replica-admission evidence.

These are proposed acceptance outcomes. Runtime implementation and validation
must be completed before changing this entry's verification level.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Project-neutral architecture review | Autoscaling epic and staged issue-plan review | Architecture contract only; `unverified`. No runtime implementation, executable test, or production validation has been completed. |

## References

- [Fresh isolated allocation validation](service-validation-fresh-isolated-allocation.md)
- [Manifest-derived identity and digest hardening](manifests-config-derived-limits-digest-hardening.md)
- [Durable state before pipeline advancement](architecture-pipeline-durable-state-ac3.md)
