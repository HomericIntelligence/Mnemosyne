---
name: ci-test-partition-new-modules
description: "Classify each new test module in the repository CI partition inventory in the same change, choose its tier by sibling-suite locality, and prove the partition locally with the runner's own loader. Use when: (1) a change adds a test module to a repo whose test runner requires an explicit partition of every discovered module, (2) every CI shard fails fast at configuration with an unclassified-modules partition error while lint, typecheck, and docs stay green, or (3) you must decide which of several inventory lists a new module belongs to."
category: ci-cd
date: 2026-10-26
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: [test-tier, module-partition, inventory-gate, unclassified-modules, fail-closed, shard-config-failure, sibling-locality, new-test-module, ci]
---

# Classify New Test Modules in the CI Partition Inventory

## Overview

| Field | Value |
| --- | --- |
| **Date** | 2026-10-26 |
| **Objective** | Add new test modules without breaking a CI gate that must partition every discovered test module into explicit lists. |
| **Outcome** | Successful; the hosted run went green on all shards after each new module was classified in the same change. |
| **Verification** | verified-ci; the first hosted run failed every shard at configuration, the corrected run passed, and the change merged. |

Some CI profiles do not discover their test set at run time. They read an inventory
of explicit lists, for example a pull-request tier and a nightly tier, and require
the lists together to partition every discovered test module exactly: no module
unclassified, no listed module missing from the tree.

A change that adds a test module without adding its inventory row breaks that
partition. The failure signature is distinctive: every shard of the test job
fails in seconds at configuration, before any test runs, with an error of the
shape `... do not partition ... : unclassified modules: <paths>`; lint,
typecheck, docs, and other gates stay green.

## When to Use

- A change adds a new test module at a root that a CI inventory partitions.
- The test job fails uniformly and fast across every shard with a configuration
  error that names unclassified modules, while every other check passes.
- You must choose which of several inventory lists (for example a pull-request
  tier or a nightly tier) a new module belongs to.
- A local pre-push check must prove the same partition the hosted runner enforces.

For the opposite gate shape, read the related entries: a changed-path gate
classifies the diff and keeps rows for deleted paths, and a frozen-set guard
pins a literal enumeration that a change edits directly. This entry covers the
tree-partition gate.

## Verified Workflow

### Quick Reference

```bash
# In the SAME change that adds the module:
# 1. Add its path to the inventory list of its nearest behavior sibling.
# 2. Prove the partition locally with the repository's own loader, not by eye:
python3 - <<'PY'   # adapt the import to the repository runner module
import the_runner
inv = the_runner.load_inventory(<tier inventory file>)
print(len(inv["pr_modules"]), len(inv["nightly_modules"]))
PY
# 3. Run the tests that cover the tier configuration itself:
<test runner> <ci workflow/tier test module> -k <tier or inventory filter>
```

### Suggested Approach

1. Identify the gate shape before you choose a rule. A tree-partition gate
   requires the classified set to equal the discovered modules: an added module
   needs a row, and a removed module must lose its row. This is the opposite of
   a changed-path (diff) gate, where a deleted path keeps its classification
   row. Do not reuse a diff-gate rule on a partition gate.
2. Classify by sibling-suite locality. Place the new module in the same list as
   the existing module whose runtime cost and dependencies it most resembles,
   for example the suite it extends. Look up that sibling's list instead of
   reasoning from the new module alone. When the local ordering is thematic or
   alphabetical, insert the row next to the sibling so later readers find it
   with its family.
3. Keep the inventory edit in the same change as the new modules. The gate runs
   inside the test job, so a follow-up fix arrives only after every shard of
   the merged-queued change has already failed.
4. Prove the partition locally before push. Run the repository own inventory
   loader or validator, the same code the runner uses, and the tests that cover
   the tier configuration. Reading the lists does not prove the partition; the
   loader checks both directions (unclassified and stale modules) and is cheap.
5. Recognize the blast-radius signature on hosted CI. Uniform sub-minute shard
   failures with all other check families green point at job configuration,
   not at test behavior. Read one shard log first instead of re-running tests.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Fix the inventory after the source change merges | Pushed the new modules and the green local suites, planning to adjust CI data later | Every hosted shard failed at configuration with `unclassified modules`; merge was blocked while lint, typecheck, docs, and policy checks all passed | The partition gate runs inside the test job configuration stage; the inventory rows must land in the same change as the modules |
| Read the lists instead of running the loader | Compared the two inventory sections by eye after adding rows | An eye-level read cannot check the reverse direction (a stale row for a missing module) and cannot confirm the lists still partition the tree | Run the runner's own loader locally; it validates both directions at once and costs seconds |
| Copy a changed-path gate rule onto the partition | Considered keeping rows for removed modules, as a diff-classification gate requires for deletions | A tree-partition gate rejects a row for a missing module as stale (`unknown modules`), the opposite deletion rule | Identify the universe the gate classifies first: tree (additions need rows, removals lose rows) versus diff (deletions keep rows) |

## Results & Parameters

### Configuration

```yaml
# Inventory shape this rule covers (names vary by repository):
version: 1
pr_modules:
  - tests/test_<sibling>.py
  - tests/test_<new>.py        # same change as the module
nightly_modules:
  - tests/test_<heavy sibling>.py
```

### Expected Output

- The local loader validates the file and reports both list counts.
- The tier-covering tests pass.
- The hosted test job starts shard execution instead of failing at
  configuration; the remaining check families keep their earlier results.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| A Python monorepo with a tiered module inventory | Five new test modules; first hosted run failed all shards at configuration, corrected run green and merged | Measured case and classification counts in [notes](ci-test-partition-new-modules.notes.md) |

## Related Entries

- [changed-path-gate-deletion-classification](changed-path-gate-deletion-classification.md) — the diff-classification gate with the opposite deletion rule
- [planning-frozen-registry-guard-co-update](planning-frozen-registry-guard-co-update.md) — co-updating a pinned enumeration that a frozen-set guard asserts
