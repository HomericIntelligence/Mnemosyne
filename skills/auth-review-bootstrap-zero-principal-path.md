---
name: auth-review-bootstrap-zero-principal-path
license: BSD-3-Clause
description: "Trace the zero-principal authorization path before a GO when you review a bootstrap authentication or authorization change: first administrator, first enrollment, machine-authority bridge, or initial-key issuance."
category: tooling
date: 2026-10-15
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [code-review, authentication, authorization, bootstrap, first-principal, deadlock, machine-authority, enrollment, verified-local]
---

# Authentication Review: Trace the Zero-Principal Path

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-15 |
| **Objective** | Find bootstrap authorization deadlocks during review: a system state in which no enrolled principal exists and no authority can grant the first one. |
| **Outcome** | Operational — the trace missed once in a full checklist review and was caught only by live exercise; the rule is now part of review of bootstrap-boundary changes. |

## When to Use

Use this skill when a plan review or implementation review touches a bootstrap boundary of
an authentication or authorization system:

- creation or enrollment of the first administrator or first privileged member;
- a claim or enrollment flow that converts an unenrolled identity into a recognized one;
- a machine-authority or service-identity bridge that authorizes an action without an
  already-enrolled human approver;
- issuance or rotation of the initial credential (first key, bootstrap token, root secret);
- any change to the gate that decides who can authorize the first grant.

Do not apply this trace to steady-state authorization changes where an enrolled privileged
principal is guaranteed to exist.

## Verified Workflow

### Quick Reference

Assume a clean state: zero enrolled identities, factory configuration only. Walk the path
from that state to the first enrolled privileged principal, step by step. At each step,
name the authority that permits the step. If any step needs an already-enrolled
principal, you found a deadlock.

### Suggested Approach

1. **Classify the boundary.** Decide whether the change touches a bootstrap boundary
   (triggers above). Put the classification in the review record.
2. **Enumerate the zero-principal path.** Start from zero enrolled identities. For each
   step toward the first enrolled principal, identify the gate that authorizes it and
   the input that gate evaluates.
3. **Require one proven unblocked mechanism.** Acceptable mechanisms include:
   - a machine-bound identity gate (for example, a service-account check on a local
     socket) that authorizes the first issuance;
   - a one-time bootstrap credential with a limited scope;
   - an operator-authenticated channel outside the system's own authority model.

   A mechanism whose authorization input presupposes an enrolled actor (an approver, an
   administrator, a member) is not unblocked — it moves the deadlock one step away.
4. **Check the evidence class.** Fixture-based unit tests that pre-enroll actors cannot
   expose a zero-principal deadlock, and green CI on such tests is not contrary evidence.
   Require a live walkthrough from a clean state, or an integration test that starts with
   an empty enrollment store and performs the first grant end to end. When the review
   scope touches the boundary, put this exercise in the plan conditions.
5. **Review a deadlock fix against the same trace.** The fix must open exactly the
   intended first step without widening authority beyond it: bind the mechanism to the
   deployment's declared identity (for example, the configured service principal), keep
   denial rules intact for every non-bootstrap request, and keep the path offline from
   production trust material where the design requires it.

Report the trace as an explicit review finding: the enumerated path, the unblocked
mechanism, and the live-exercise evidence or the admitted gap.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Condition-checklist review with full local tests and green CI | Reviewed a deployment-lane credential-authority change: verified every acceptance condition, ran the full affected test suite (all passing), observed green CI, and gave GO | The first live claim by an enrolled member deadlocked: credential issuance required an authority that presupposed an enrolled actor, so no first principal could ever be authorized; none of the static checks modeled the zero-principal state | Trace the zero-principal path explicitly at bootstrap boundaries; unit fixtures that pre-enroll actors cannot expose a first-grant deadlock |
| Deadlock fix without re-tracing | Initial review of the fix focused on the new machine-authority gate alone | Narrow review cannot show that the new mechanism closes the whole path and opens nothing else | Re-trace the full zero-principal path on the fix and verify the boundary conditions hold for every non-bootstrap request |

## Results & Parameters

### Review-record output

- Boundary classification: bootstrap-boundary change or steady-state change.
- The zero-principal path, step by step, with the authorizing gate at each step.
- The unblocked first-grant mechanism and its binding (declared identity, one-time
  scope, or operator channel).
- Evidence class: live clean-state exercise, empty-store integration test, or an
  admitted gap.

### Expected Output

- A GO verdict names the trace result and cites the live or integration evidence.
- A NO-GO verdict names the deadlocked step and the missing authority.
- Plan conditions for bootstrap-boundary work include the clean-state exercise.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Multi-agent credential-authority review | Plan and implementation review of a deployment-lane authority change and its machine-authority deadlock fix | Deadlock caught by live lane exercise after a checklist GO; fix merged after re-trace; evidence generalized for privacy |
