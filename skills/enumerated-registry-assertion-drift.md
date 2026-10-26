---
name: enumerated-registry-assertion-drift
license: BSD-3-Clause
description: "Treat exact-list test assertions over a registry that several merge lanes extend as a wholesale-red failure class: every lane that appends without syncing the assertions breaks main, and a repair is incomplete unless it syncs to the complete current set and adds a drift guard in the same change. Use when numbered files (migrations, catalogs, fixtures) accumulate from parallel merges, when a PR appends to such a directory without touching the asserting tests, when many test shards fail at once on an exact-list equality, or when a repair commit fixes the drift only up to an older entry."
category: testing
date: 2026-10-25
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [enumerative-tests, migration-list, registry-drift, parallel-merges, merge-waves, exact-list-assertion, drift-guard, main-red, repair-completeness, test-design]
---

# Enumerated Registry Assertion Drift

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-25 |
| **Objective** | Prevent and recognize wholesale test failures caused by exact enumerative assertions over registries that parallel merge waves extend. |
| **Outcome** | Successful as diagnosis: root cause established for a ~26-of-30-shard main-red event, and the repair-completeness rule is evidence-bound. The drift-guard recommendation is proposal-grade in the source engagement. |

An exact-list assertion such as `apply(...) == [full ordered list]` couples
every merge lane to every other lane. The registry grows in one pull
request; the assertion fails in a test those pull requests do not touch.
Many shards or tests then fail at the same time on `main`, and no single
lane owns the red state. The class also survives partial repairs: a fix
that syncs the expectation to the state at analysis time is already
outdated when another lane has merged in between.

## When to Use

Use this skill when one of these conditions applies:

- A test asserts the exact complete list or set of entries in a shared
  registry: numbered SQL migrations, resource catalogs, seed fixtures, or
  manifest directories that several contributors extend.
- Several pull requests or merge lanes land on the same mainline in a
  short window.
- Many test shards fail at the same time, and each failure is an
  exact-list equality mismatch on that registry.
- A pull request appends a file to the registry but does not change the
  asserting tests.
- A repair commit claims to fix "deterministic failures after parallel
  merges". Check that it is complete before you trust it.

## Verified Workflow

### Quick Reference

Diagnosis order for a wholesale-red event:

```bash
# 1. Compare the registry with the assertions at the SAME ref.
git ls-tree <ref> --name-only <registry-dir>/
git show <ref>:<asserting-test-file> | grep -E '0[0-9]{3}_'

# 2. Identify additions per merge (the drift producers).
git log --oneline --diff-filter=A <ref> -- <registry-dir>/

# 3. Confirm the asserting tests changed (or not) in the same commits.
git log --oneline <ref> -- <registry-dir>/ <asserting-test-file>
```

Read the tree at the bound ref with `git ls-tree` and `git show`. Never
read an incumbent working tree: a stale checkout reports the registry as
smaller or larger than the ref under diagnosis.

### Suggested Approach

- **Test authors**: assert invariants, not enumerations, over a shared
  registry. Useful forms: monotonic order, uniqueness, an expected prefix,
  a superset that contains a named baseline, or a catalog fingerprint.
  Reserve exact equality for the segment one change owns, for example "the
  new candidate appends immediately after the previous last entry".
- **Reviewers**: a pull request that appends to such a registry without
  extending the asserting tests in the same merge is a required finding.
  The drift becomes visible only after later merges, so per-PR review is
  the last gate that can contain it.
- **Repair owners**: sync the expectations to the complete current set of
  the tree at merge time, verified against the bound ref. Then add a drift
  guard in the same change: a small check that diffs registry contents
  against the test expectations and fails with an instructive message.
  Without the guard, the class recurs on the next merge wave. Build the
  guard per
  [architecture-executable-convention-guard-pattern](architecture-executable-convention-guard-pattern.md).
- **Diagnosticians**: a same-failure-signature across many shards whose
  assert compares against a full list is drift until disproved. Compare
  registry and tests before suspecting a product defect. Classify
  first-cause versus cascade gates per
  [pr-ci-failure-triage-preexisting-vs-introduced](pr-ci-failure-triage-preexisting-vs-introduced.md).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Enumeration synced to analysis-time state | After a first drift break, a repair commit extended the expected migration list through entry N while entries N+1 and N+2 were already present on the mainline from two other merges | `apply(...) == [...]` returned two extra stems; the same assertion sites failed deterministically again within hours, this time across almost every shard | A repair for this class must sync to the complete set at merge time and add a drift guard in the same change; otherwise the wave-pattern guarantees recurrence |

## Results & Parameters

### Configuration

Record these items with the diagnosis or the repair:

```text
registry_dir: <path of the appended directory, e.g. migrations/>
assert_sites: <test files and lines asserting exact lists>
complete_stem_set_at_ref: <git ls-tree output count or digest at repair ref>
drift_producers: <merge commits that appended without test sync>
drift_guard: <name of the check added by the repair, or NONE>
```

### Expected Output

- The asserting tests and the registry derive the same set at the bound
  ref at repair merge time.
- A later lane that appends without syncing fails the drift guard alone,
  with an actionable message, instead of failing many unrelated tests.
- Review of registry-appending pull requests blocks unsynced additions.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| LLM360/comet | v0.2.4 drive: ~26 of 30 postgres shards red on main during a multi-lane merge wave; diagnosis and repair-class evidence | [notes.md](./enumerated-registry-assertion-drift.notes.md) |

## References

- [architecture-executable-convention-guard-pattern](architecture-executable-convention-guard-pattern.md) — how to build the drift guard as a blocking check.
- [pr-ci-failure-triage-preexisting-vs-introduced](pr-ci-failure-triage-preexisting-vs-introduced.md) — the classify-first discipline that separates this first cause from cascade gates.
