---
name: testing-authority-subtraction-surrogate-repoint
license: BSD-3-Clause
description: "Repoint tests that pin a removed registry entry to a surviving entry that stays registered in every authority the test touches and that satisfies every gate on the exercised render path. Use when a change removes a model, recipe, or catalog member from one of several policy authorities (for example production deployment contexts) while the entry remains in development or evaluation authorities, when pinned tests then fail through a fail-closed membership check instead of an assertion, when a surrogate that passes the policy intersection still fails later gates such as a missing immutable image digest or an unset fast-start contract, or when a cluster-scoped recipe override is silently inert because resolution reads the removed field from the recipe top level."
category: testing
date: 2026-10-28
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - policy-subtraction
  - authority-membership
  - fail-closed-guard
  - test-surrogate
  - render-path-gates
  - registration-intersection
  - recipe-override-resolution
  - lane-disable
---

# Testing Authority Subtraction Surrogate Repoint

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-28 |
| **Objective** | Repair the test coupling that a policy subtraction breaks by repointing each pinned test to a correctly selected surviving entry. |
| **Outcome** | Verified in CI: the targeted suites pass on the merge commit, and a companion suite now pins the removed entry as failed-closed. |

A test that renders or validates with one pinned entry against an
authority (a deployment context, a policy mapping, a registry) couples the
test to that membership set. Removing the entry from one authority breaks
the test downstream through a fail-closed membership check, not through a
readable assertion. The entry can remain registered in other authorities,
which hides the coupling during RED checks that run only against the
remaining registrations. The repair selects a surrogate: an entry that
stays registered in every authority the test touches and that passes every
gate on each code path the test exercises.

## When to Use

Use this skill when one of these conditions applies:

- A change removes an entry from some authorities while the entry remains
  in development or evaluation authorities.
- After that removal, tests that pin the entry against several authorities
  fail with a fail-closed guard message, for example a membership check
  that names the allowed list and reports the removed entry as observed.
- Other tests that pin the same entry keep passing because they build
  tree-independent fixtures, so the breakage reaches CI instead of local
  validation.
- A repointed surrogate passes the membership intersection but fails a
  later render gate, for example a fast-start code path that requires a
  healthy standby node or an immutable image digest.
- A recipe-level override injected into a cluster section is silently
  inert because resolution reads that field from the recipe top level.

## Verified Workflow

### Quick Reference

Select the surrogate in three filters:

```text
1. membership:   surrogate ∈ ⋂ authorities the test touches
2. path gates:   each render path's requirements all satisfied
3. override level: inject removed fields at the resolution top level
```

Enumerate the shipped authority files and compute the model intersection
before you pick a surrogate name. Do not guess from familiarity.

### Suggested Approach

- **Compute the membership intersection first.** List the registered
  entries of every authority each failing test touches and intersect the
  sets. An entry removed from one authority is not a legal surrogate for a
  test that renders against that authority.
- **Map each render gate the test walks.** A replica render can require an
  image with an immutable digest. A fast-start render without a launch
  image instead requires a healthy standby node, reserved ports, attempt
  identity, and a matching standby deployment identity. A standby-node
  render additionally requires a fast-start contract and a matching engine
  adapter. Read the gate code; do not infer the gates from one green case.
- **Pick the surrogate that passes every gate with the fewest test
  changes.** Prefer an entry without a fast-start contract for replica
  renders: it avoids the standby-node dependency entirely.
- **Inject removed contracts at the level resolution reads them.** When a
  survivor lacks a contract the test requires (for example a standby-node
  render that needs a fast-start recipe), build a fixture copy of the
  survivor and inject the missing field at the recipe top level. A field
  set inside a cluster section can be legal schema and still never reach
  the resolved recipe, which produces a second, less obvious failure.
- **Pin the subtraction itself fail-closed.** Deliver a suite that proves
  the removed entry is absent from the authorities and that downstream
  consumers reject records that reference it. Build one positive record
  and assert the membership predicate rejects it, so the check cannot pass
  vacuously. See
  [testing-retired-lever-inertness-guard](testing-retired-lever-inertness-guard.md)
  for the inertness-proof shape.
- **Expect helper coupling when an authority empties legitimately.** Test
  helpers that derive fixtures from an authority's entry list (for example
  taking the first registered recipe) raise an empty-iteration error when
  that list becomes legitimately empty. Route such helpers to an authority
  that keeps entries, and make the coupling explicit in the helper.
- **Classify the remaining breakage before rerunning.** If a push shows
  failures the change cannot explain, compare the failing paths with the
  change's file list per
  [pr-ci-failure-triage-preexisting-vs-introduced](pr-ci-failure-triage-preexisting-vs-introduced.md);
  a co-merged lane can break the same window. For the addition-drift
  counterpart of this failure class, see
  [enumerated-registry-assertion-drift](enumerated-registry-assertion-drift.md).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| First available survivor | Repointed the render pin to a survivor from the membership intersection whose recipe carried a top-level fast-start contract but no immutable image digest | The replica render entered the fast-start path, had no launch image, and raised "fast-start replica rendering requires a healthy donor"; the test supplies no standby node | The membership intersection is the first filter, not the last; a fast-start recipe without an immutable image changes which dependencies a render needs |
| Cluster-section override | Injected the missing fast-start contract into the survivor's cluster section of the donor fixture recipe | Resolution read fast-start only from the recipe top level; the cluster-scoped field was schema-legal, set, and inert, and the standby-node render raised "donor rendering requires an SGLang fast_start cookbook" | Verify override fields against the resolver before writing the fixture; a schema-legal field can be resolution-inert |
| Cluster-section override after rename confusion | Switched the donor fixture to the fast-start injection only after a first edit round | One exploratory edit was recoverable because the test run isolated the two failing tests before a full suite rerun (~50 s per pair versus ~13 min for the file) | Iterate surrogate repairs on the smallest failing subset first; keep the full-file pass for the final confirmation |

## Results & Parameters

### Configuration

Record these items with the repair:

```text
removed_entry: <the entry removed from the authority>
authorities_removed_from: <context files that no longer register it>
authorities_remaining: <context files that still register it>
surrogate: <selected surviving entry>
selection_filters: <membership intersection, image digest, fast-start absence>
companion_subtraction_guard: <suite that pins the absence and rejection>
```

### Expected Output

- Every repointed test passes against the authorities it touches.
- The removed entry fails closed for downstream consumers; the pinning
  suite is non-vacuous and passes.
- CI shards that previously failed on the membership guard pass on the
  repaired branch.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| LLM360/comet | Issue #3178 drive, PR #3409: removed the kimi-k3 lane from the four tenant-serving deployment contexts; repointed two coexistence renders to k2-horizon-32b with a top-level fast-start injection on the donor fixture | [notes.md](./testing-authority-subtraction-surrogate-repoint.notes.md) |

## References

- [enumerated-registry-assertion-drift](enumerated-registry-assertion-drift.md) — the addition-drift counterpart: exact-list assertions over growing registries.
- [pr-ci-failure-triage-preexisting-vs-introduced](pr-ci-failure-triage-preexisting-vs-introduced.md) — classify window breakage before rerunning.
- [testing-retired-lever-inertness-guard](testing-retired-lever-inertness-guard.md) — proof shape that a retired lever stays inert.
