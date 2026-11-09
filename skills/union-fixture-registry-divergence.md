---
name: union-fixture-registry-divergence
license: BSD-3-Clause
description: "Diagnose a shared test fixture or shared factory that permits a shape production forbids. Use when many tests in one module fail at once immediately after you add a registry equality check, a completeness check, or any rule that compares a container against its owner; when the tests build a union or superset of per-scope entries; or when a test that should reject a hostile input passes instead."
category: testing
date: 2026-11-09
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - shared-fixture
  - union-release
  - registry-invariant
  - per-scope-projection
  - identity-rebind
  - fail-for-the-wrong-reason
  - acceptance-contrast
  - regression-attribution
  - test-double
  - authority-at-resolution
---

# Union Test Fixtures Against a Per-Scope Registry Invariant

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-09 |
| **Objective** | Add or diagnose a rule that compares one scope's declared set with one shared artifact's contents, without weakening the rule to suit a test double, and without letting a new rejection test pass for an unintended reason. |
| **Outcome** | Successful. The rule stayed exact in production, the shared fixture projected per scope, and two rejection tests gained an assertion that attributes the rejection to the intended branch. Verified by focused local runs and a green full CI on the merged head. |

A shared test fixture can accept a shape that production refuses. The usual
case is a helper that builds one artifact for every scope at once, so each
caller receives a superset. A new equality rule then fails across most of a
module. The first instinct is to relax the rule, because the strike count
looks like a rule defect. The evidence usually says the opposite: the fixture
models a state that production never reaches.

Two distinct failures follow, and each has its own repair:

1. **The double is unrealistic.** Many tests fail at once on a rule, and the
   fixture supplies entries that no single caller owns.
2. **A new test passes for the wrong reason.** A rejection test asserts only
   that an error occurred. After the fixture changes, another branch raises
   first, and the test keeps passing without exercising its subject.

## When to Use

- Many tests in one module fail at once right after you add a rule that
  compares a scope's declared set with a shared artifact's contents.
- The failures name extra entries that the fixture builder adds for
  cross-scope use, not entries that the scope itself declares.
- A helper builds one shared artifact from the union of several scopes, and
  each scope resolves against the shared artifact.
- The shared artifact carries content-derived identities, and subsetting it
  invalidates those identities.
- You are about to weaken, soften, or add an exemption to a production rule
  because test doubles violate it.
- A rejection test asserts only that *some* error occurs, and a change to the
  fixture can change which branch raises.

Do not use this entry as permission to weaken the rule. Weakening the rule is
the failed branch below.

## Verified Workflow

### Quick Reference

Decide who owns the shape before you touch the rule:

```bash
# 1. Read one failure and the shared builder in the same pass.
#    Ask: does the failing scope itself declare the extra entries?  If not,
#    the double is the unrealistic party, not the rule.
# 2. Find every caller of the shared builder, not only the failing module.
grep -rn "<builder_name>(" tests/
# 3. Before you subset a content-addressed artifact, find its identity fields
#    and whether they are derived or carried.
grep -rn "identity\|_id\b\|digest\|fingerprint" <artifact_model_module>
```

Rule: keep the production invariant exact. Make each scope resolve against
only the entries that scope owns.

### Suggested Approach

1. **Classify the rule against the double before you classify the double
   against the rule.** Read one failing test and the shared builder in the
   same pass. If the failing scope does not declare the extra entries, the
   double supplies a shape that production cannot reach. Record that
   conclusion, because it decides every later step.
2. **State the production shape explicitly.** Write the rule as an
   invariant over one scope's own artifact, not over a shared artifact. The
   fixture is a test convenience; it is not a requirement source.
3. **Project the shared artifact per scope.** Add one helper that returns the
   artifact restricted to a named scope's entries, and route every builder in
   the module through it. Keep the projection total and deterministic, so two
   calls with the same inputs produce equal results.
4. **Re-derive carried identities after you subset.** A content-addressed
   artifact usually both derives identities and carries them. Drop the
   derived identity fields before you re-validate the restricted artifact, and
   let the model recompute them. If you keep the old values, validation
   refuses the artifact with an identity mismatch that names the stale value.
   Do this at every place that re-validates, including helpers that only read.
5. **Project before you compare, not after.** A comparison helper that takes
   the shared artifact and a scope must project first. Otherwise the
   comparison raises an identity mismatch rather than the rule you are
   testing.
6. **Give each rejection test an attribution assertion.** After a
   fixture change, assert the *specific* diagnostic (message fragment, error
   field, or exception subtype) that only the intended branch produces. A
   rejection that satisfied the test before the change is now a second
   signal: confirm the test still reaches its subject.
7. **Re-run the neighbours, not only the fixed module.** A projection helper
   changes what every caller resolves. Run the modules that consume the same
   builders, so a newly unrealistic double elsewhere is visible in the same
   pass.
8. **Record the count delta.** Report how many failures existed before and
   after. A drop from a large number to a small, named family is the
   evidence that the classification was right; an unchanged count says the
   first cause is still unidentified.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Soften the production rule for the tests | The new equality rule broke most tests in one module, so the rule looked too strict and an exemption for the shared fixture looked cheap | The shared fixture supplied entries that no single scope declared. The strikes came from the double, and an exemption would have kept the production divergence silent, which is the defect the rule removes | Classify the failure against the double before you touch the rule. A large simultaneous strike count is evidence about the fixture at least as often as about the rule |
| Subset a content-addressed artifact and re-validate it unchanged | Restricted the shared artifact to one scope's entries, then validated the result | The derived identity fields still described the full artifact, so validation refused the restricted artifact with an identity mismatch that named the stale derived value | Drop the derived identity fields and let the model recompute them; do this at every re-validation site |
| Project inside the comparison only | Passed the shared artifact and the scope to the comparison helper and let the helper subset | The comparison raised the identity mismatch first, so the test no longer exercised the rule it named | Project before you compare, at the artifact's own construction site |
| Assert only that an error occurred | The rejection test caught any error | After the fixture changed, another branch raised first. The test still passed, so its subject was never exercised | Assert the specific diagnostic of the intended branch, and re-check each rejection test after a fixture change |
| Lower the expectation to a subset assertion | Asserted that the scope's set is a subset of the shared artifact's set | The subset assertion is true for the union double by construction, so it cannot detect the divergence, and it passes for a scope that supplies nothing | Assert equality in production and give the double the production shape, instead of weakening the assertion |

## Results & Parameters

### Configuration

```yaml
classification:
  question: does the failing scope declare the extra entries itself?
  answer_no: the double supplies an unreachable shape; project, do not relax
  answer_yes: the rule may be wrong; stop and re-read the requirement
projection:
  shape: shared_artifact restricted to scope_owned_entries
  where: at artifact construction, before every comparison
  property: total and deterministic (same inputs give equal artifacts)
identity_rebind:
  derived_fields: drop before re-validation; the model recomputes them
  carried_fields: keep
  sites: every place that re-validates, including read-only helpers
attribution:
  assertion: the specific diagnostic of the intended branch
  recheck: after any fixture change, confirm the test still reaches its subject
evidence:
  report: failure count before and after, with the remaining family named
```

### Expected Output

- The production rule keeps its exact comparison, with no test-shaped exemption.
- One projection helper serves every builder in the module that uses the shared artifact.
- Re-validation of a restricted artifact succeeds, with recomputed identities.
- Each rejection test fails if its intended branch stops raising, even when
  another branch still raises.
- The neighbour modules that consume the same builders pass.
- The failure count drops to a named, explained family, or the first cause is
  still unidentified.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Python multi-scope deployment registry (privacy-screened) | A registry equality rule added at a resolution boundary; a shared test fixture built one artifact for several scopes; focused reruns plus green CI on the merged head | Generalised evidence and the count record in [notes](union-fixture-registry-divergence.notes.md) |

## References

- [planning-frozen-registry-guard-co-update](planning-frozen-registry-guard-co-update.md) — the co-update homes of a pinned enumeration; this entry covers a shared double that admits an unreachable shape
- [testing-retired-lever-inertness-guard](testing-retired-lever-inertness-guard.md) — pairing every rejection with an acceptance contrast so the rejection is attributable
- [live-hotfix-content-addressed-identity-rotation](live-hotfix-content-addressed-identity-rotation.md) — the production identity chain whose derived layers the test double must recompute
- [stale-plan-already-resolved](stale-plan-already-resolved.md) — the first step of a resume: confirm the premise still holds on the current default branch
- [pytest-fixture-patterns-and-deduplication](pytest-fixture-patterns-and-deduplication.md) — shared-fixture organisation patterns