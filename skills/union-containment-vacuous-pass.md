---
name: union-containment-vacuous-pass
description: "Make a set-containment or set-equality regression assertion non-vacuous when the test fixtures coincide with the pre-fix state of both compared sets: mint one probe row that belongs to exactly one compared set so the defect under repair must change the asserted result. Use when: (1) you write or review a regression test that asserts X is a subset of Y, set equality, or an empty difference between two data sources, (2) every fixture row satisfies both sides of the comparison on a fresh or seeded environment, for example seed rows that a UNION view reproduces from its static side, (3) a test you expected to fail before the fix passes instead, or (4) you must prove that a RED result came from the defect and not from an unrelated difference."
category: testing
date: 2026-10-26
version: "1.0.0"
user-invocable: false
tags:
  - vacuous-pass
  - set-containment
  - union-view
  - probe-fixture
  - red-green-proof
  - regression-test-design
  - seed-fixtures
  - subset-assertion
---

# Union Containment Vacuous Pass

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-26 |
| **Objective** | Give a regression assertion real signal when the fixtures satisfy both sides of the comparison with and without the defect. |
| **Outcome** | Operational rule from one live regression test. A subset assertion over only the shipped seed rows passed before the fix, because the seeds equaled the static side of a UNION view and the asserted difference was empty in both revisions. One probe row exclusive to the dynamic side turned the same assertion into a RED-then-GREEN proof. |

A containment assertion `X ⊆ Y` (or an empty-difference / equality assertion)
has signal only when the data makes `X ∖ Y` different in the broken and
repaired revisions. If every fixture row belongs to both compared sets, the
difference is empty in both revisions and the assertion passes forever. The
test then records the defect as covered while the defect is invisible to it.

## When to Use

Use this skill when these conditions apply:

- You write or review a regression test over a UNION, JOIN, difference, or
  subset relation between two data sources: a SQL view, an aggregation, or
  an in-memory merge.
- The test fixtures on a fresh or seeded environment satisfy both sides of
  the comparison. Common case: migration seeds that insert the same rows the
  UNION's static branch already produces.
- A test that must fail before the fix passes instead, or you cannot tell
  which revision a passing test would fail on.
- You review a regression test whose asserted set is empty on the pre-fix
  revision: approve only with a probe or with a proof that the assertion is
  non-vacuous.

This rule does not cover exact-list assertions that drift across parallel
merge lanes. That failure class has a different trigger and repair. See
References.

## Verified Workflow

### Quick Reference

```text
1. Compute the asserted difference on the pristine fixture data BEFORE the
   fix. If it is empty, the containment assertion is vacuous: it passes with
   and without the defect and is not evidence.
2. Mint one fixture row that belongs to exactly one compared set and to no
   shipped seed set, for example a history row absent from configuration.
3. Assert that the probe is visible in the combined result. Keep an overlap
   or counterpart assertion for the rows both sets share.
4. Run the test at the pre-fix revision: it must fail (RED). Run it with the
   fix: it must pass (GREEN). Record both results.
```

### Suggested Approach

1. Evaluate the assertion on the pre-fix revision first. Write the exact
   query or expression the assertion computes, for example a difference
   between the dynamic source and the combined result. If the result is the
   empty set before and after the fix, the test cannot see the defect.
2. Design the probe around the defect shape, not around convenience data.
   The probe must change membership of the asserted set when the defect is
   present: a row the broken code drops, duplicates, or fails to combine.
   Give it a key that no seed, migration, or fixture creates elsewhere.
3. Assert the two branches separately. Membership of the probe proves the
   defect branch is included. A count or flag on one row both sets share
   proves the overlap branch combines that row exactly once.
4. Prove RED, then prove GREEN. A RED without a probe check can come from an
   unrelated change; run the same test at the pre-fix revision and require
   failure, then at the fixed revision and require success.
5. When no fresh environment is available, build one from the migration
   chain or the factory fixtures at the bound revision. Do not substitute an
   incumbent database that already carries production rows: it makes the
   vacuity check unrepeatable.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Seed-only containment assertion | Asserted every dynamic-source row visible in a UNION view, using only the shipped seed rows | The test passed at the pre-fix revision: the seeds equaled the UNION's static side, so the asserted difference was empty in both revisions and the defect (the view dropped the dynamic side) was invisible | Compute the asserted difference at the pre-fix revision; when it is empty in both revisions, mint a probe row exclusive to the defect-affected side |

## Results & Parameters

### Configuration

```text
probe row   = unique key; absent from every shipped seed set;
              present in exactly one compared source
membership  = assert probe is an element of the combined result
overlap     = assert rows present in both sources combine to the expected
              count (for example exactly one row per shared key)
proof       = same test at pre-fix revision -> RED; with fix -> GREEN;
              record both results
```

### Expected Output

- At the pre-fix revision the test fails and the failure message names the
  probe.
- At the fixed revision the test passes, and the full owning suite passes.
- The vacuity check is reproducible: the difference query on pristine
  fixtures returns the probe before the fix and the empty set after.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A proprietary database-backed reporting service (unnamed per the privacy policy) | Regression test for a view rebuilt as the UNION of a current-configuration source and an audit-history source; seed rows equaled the configuration side on a fresh database | Measurement detail in [the notes](union-containment-vacuous-pass.notes.md). |

## References

- [enumerated-registry-assertion-drift](enumerated-registry-assertion-drift.md) — the adjacent failure class: exact-list assertions over registers that parallel merges extend. Distinct trigger and repair.
- [error-message-consistency-optional-dependency-pola](error-message-consistency-optional-dependency-pola.md) — a cousin rule that makes absence assertions non-vacuous by breaking the correct input.
