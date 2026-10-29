---
name: pr-review-deployed-composition-error-contract
description: "Verify that a composition running in a deployed host process delivers its contracted error behavior. Use when: (1) a review covers a caller that composes a shared discovery, loader, or resolver whose default wiring production uses, (2) a supervisor, identity renderer, or multi-worker launcher populates the host process environment at spawn time, (3) an interface contract promises a specific transport status for a failure class such as destination-unavailable, (4) failure-outcome tests patch internal attributes or run with a clean environment, or (5) an earlier review round verified the feature with injected substitutes only."
category: tooling
date: 2026-10-28
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - pr-review
  - source-review
  - error-contract
  - deployed-environment
  - exception-mapping
  - mock-seam-audit
  - discovery-resolver
  - behavior-testing
---

# Verify a Deployed Composition Delivers Its Contracted Error Behavior

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-28 |
| **Objective** | During a review, prove that a caller which composes a shared discovery or resolution module delivers the transport status the interface contract promises for each failure class, in the process environment the host actually runs with — before the review ships a GO. |
| **Outcome** | Successful during one corrective review round: the three checks below found a major contract defect that an earlier round and a green unit-test suite had both missed. Verification level is verified-local (one applied case). |

## When to Use

- A review covers a caller that composes a shared discovery, loader, or resolver module, and the caller offers an injectable seam but no production call site injects a substitute, so the default wiring is the production wiring.
- The host process receives its environment at spawn time: a supervisor writes variables into the child environment, an identity renderer produces management or deployment variables, or a multi-worker launcher writes variables into the process environment before workers start.
- The composed module has environment preconditions: for example it refuses to run when a management variable is set, or conflicts when an ambient identifier differs from a resolved one.
- An interface contract promises a specific transport status for a failure class, for example `503` plus a retry header for a destination that is unavailable.
- Failure-outcome tests patch internal attributes or functions, substitute the composed dependency, or run with a clean environment.
- An earlier review round verified the surface with injected fixtures, and the corrective round must decide whether the default composition delivers the contract.

## Verified Workflow

### Quick Reference

Run four source greps, then read two hops deep from the call site:

```bash
# Check 1: sites that populate the production host process environment
grep -nE 'os\.environ\[|environ\.update|environment\.update' src/
# Check 2: every exception the composed chain can raise
grep -nE '^\s*raise\s' src/<composed-module>.py
# Check 3: the caller's catch set and the status each caught class maps to
grep -nE '^\s*except[ (]' src/<caller>.py
# Check 4: patch targets in the tests that pin the contracted failure outcome
grep -nE 'monkeypatch\.setattr|unittest\.mock\.patch' tests/
```

### Suggested Approach

Do three checks. Each maps one evidence class to one decision.

1. **Environment-contract trace.** Enumerate the sites that build the host process environment (supervisor spawn update, multi-worker launcher writes, rendered identity fields), including every default-mode call path. List the variables the deployed host always carries. Then read the composed module's preconditions. Trace what the caller does on each call path: a caller that composes the module with the process environment puts the host-carried variables in scope. When a variable the host always carries violates a precondition of the composed module, every request that reaches the composition fails in production before any routing decision, while clean-environment tests pass. Also verify the claim that some seam replaces production behavior: find each production call site; when none injects a substitute, the default composition is what the review must grade.
2. **Raise-inventory mapping.** For each function the caller composes, two levels deep, enumerate every condition that raises: environment refusal, identifier conflict, record file missing, record malformed, record mismatched against its registration. List the caller's catch set and the status each caught class maps to. Every unmapped class escapes to the framework default, usually `500`. When the contract requires a specific status for a failure class, each unmapped class that normal operation can trigger is a reachable contract defect. Code shape is not coverage: fallback branches that would return the domain-correct error are evidence only when execution can reach them without a same-instant race; pre-empting raises make intent not delivery.
3. **Mock-seam audit.** Locate the tests that pin the contracted failure outcome and record each patch target. A genuine external boundary is a registry or record file, a process environment value, a socket, or a clock. An internal attribute or function is not a boundary; a patch there replaces real code whose real implementation raises under exactly the conditions the test states. Such a test pins a status mapping the real composition does not deliver, and it cannot be behavior coverage for the contract. Require per contracted outcome: one end-to-end test that drives the real composition with fakes only at genuine boundaries (record files under a temporary path, an in-memory server transport), and one test that supplies the host-carried identity variables from check 1; both pin the status, the headers, and the absence of the downstream side effect (no backend call).

Report severity from contract effect: a contracted status that is unreachable for a cause normal operation produces means the promised behavior is not delivered; that is at least major, not minor. An environment class that fails the whole feature path on entry carries the weight of a hard feature failure.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | An earlier review round verified the routing surface with substitutes injected at the caller seam and reported no defect | The production wiring composes the default resolver; the substitutes skipped exactly the code that raises in deployment | Verify the default composition production uses; an injected seam verifies intent, not delivery |
| 2 | A green unit-test suite under a clean environment was accepted as coverage of the availability contract | The deployed host always carries identity variables that the composed module refuses, so the refusal class was invisible to the suite | Reproduce the deployed environment contract in at least one test; clean environments certify only the API shape |
| 3 | The catch set was assumed complete because domain-error fallback branches existed in the source | Earlier raises pre-empted the fallbacks; the branches were reachable only through a same-instant race, so the mapping existed as intent, not behavior | Enumerate raises from source and diff them against the catch set; do not infer coverage from the shape of the code |

## Results & Parameters

### Quick Reference

- **Environment class.** A host-carried variable that violates a composed-module precondition kills the whole contracted path in production, before routing; one found instance fails the review dimension and usually the round.
- **Exception class.** Treat environment-independent causes (record missing, malformed, mismatched) the same: these are the common dependency-down states, and each must reach the mapped domain error.
- **Reachability rule.** A converted-cause branch reachable only by race shows the intent to convert and the gap of the composition; cite it as evidence, not as coverage.
- **Test requirement.** Per contracted failure outcome: one real-composition end-to-end test at genuine boundaries plus one deployed-environment test; pin status, required headers, and no downstream side effect.
- **Review output.** For each raise class that escapes the catch set, report location of the raise, the catch-set evidence, the contract citation, and the reachability argument; when nothing escapes, record the raise inventory you enumerated as the basis of the claim.

### Expected Output

- A list of the variables the deployed host carries and where each is written.
- A raise inventory of the composed chain and the caller's catch-set mapping, with each unmapped class marked as a defect or waived with evidence.
- A patch-target table for the contracted-outcome tests: genuine boundary versus internal seam.
- Zero or more findings; a finding that makes the contracted status unreachable blocks the verdict.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A public open-source multi-deployment inference gateway | Report-only exact-head source review, corrective round, of a target-routing feature | The checks found one major defect: the default resolver composition raised unmapped exceptions in the deployed environment and for record-missing causes, making the contracted `503` unreachable. See [notes](../skills/pr-review-deployed-composition-error-contract.notes.md). |

## References

- [Related: translate a dependency exceptions at the boundary (author side)](resilience-circuit-breaker-error-translation.md)
- [Related: verify test premises and mock targets when authoring tests](planning-test-coverage-verify-premise-and-mock-targets.md)
- [Related: behavior-first test design and correct mock seams](tdd-workflow-and-test-coverage-expansion.md)
