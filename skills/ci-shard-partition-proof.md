---
name: ci-shard-partition-proof
description: "Prove a parallel test-shard gate covers the collected set exactly once, and reject the weaker signature of a shared collection digest plus a selected count. Use when a CI job splits one collected test set across many shards, when a fan-in gate must show that no node is in zero shards or in two shards, when every shard re-collects the full set before it filters, or when a shard-coverage claim rests on per-shard counts."
category: ci-cd
date: 2026-11-07
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - test-sharding
  - partition-proof
  - shard-coverage
  - fail-open-gate
  - fan-in-gate
  - collected-node-ids
  - selection-digest
  - artifact-publisher
  - matrix-context
  - recompute-assignment
---

# Prove That Parallel Test Shards Partition the Collected Set

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-07 |
| **Objective** | Make a fan-in gate prove that each collected test node ID runs in exactly one shard, and that no node runs in zero shards or in two. |
| **Outcome** | Operational. The first gate compared per-shard digests and counts and passed while every shard ran the whole set. The corrected gate recomputes the assignment from an independent collection and matches each shard's selected digest to its own partition. Five deliberate mutations failed closed on a real collection of about nine thousand node IDs. |

Parallel sharding usually works like this: every shard collects the full test
set, then filters it to its own share. Each shard therefore reports the same
collected count and the same collection digest. Those two fields show that the
shards agreed on the input. They do not show that the shards partitioned it.

A gate that checks only a shared collection digest, one agreed shard count, and
the per-shard equation `selected + deselected == collected` passes in these
cases:

- every shard selected the whole set, so each node ran many times;
- every shard selected a subset of the agreed collection, so one node ran in
  no shard;
- shards swapped shares, so the union is still wrong.

All three cases are real defects that a run can report as green.

## When to Use

- A CI job splits one collected test set across parallel shards or workers.
- A fan-in or aggregate gate must decide whether sharded coverage is complete.
- Each shard re-collects the full set before it filters, so the collection
  digest is identical across shards and carries no partition information.
- A coverage claim rests on per-shard case counts, a JUnit total, or a passing
  job summary instead of on the node IDs.
- A review finds that a shard gate can pass when every shard runs everything.

Read the related entries before you choose a design. A tier-partition gate
classifies modules and has the opposite rule for deletions. A non-vacuity rule
covers a gate over an empty derived artifact. A skipped-job rule covers a green
aggregate whose jobs never started. This entry covers the coverage proof for
shards that did run.

## Verified Workflow

### Quick Reference

```bash
# Fail-closed signature of the shard gate:
#   1. read every shard record: collection digest, weight digest, selected digest,
#      and the collected, selected, and deselected counts
#   2. read ONE published collection of node IDs and the weight file
#   3. recompute the assignment from those inputs with the runner's own function
#   4. require, for each shard, both:
#        record.selected_sha256 == digest(assignment[shard])
#        record.selected         == len(assignment[shard])
#   5. fail on a missing record, an empty collection, or a profile mismatch
```

### Suggested Approach

1. Publish an independent collection. Have exactly one shard write the sorted
   collected node IDs to an artifact. Bind the artifact name to the commit and
   to a fixed identity, because the aggregate job has no matrix context. Do not
   publish from every shard under one name: concurrent jobs that overwrite a
   shared artifact name delete each other's copy or fail on a name conflict.
2. Record a selected digest, not only a selected count. Write the digest of the
   node IDs that the shard kept after filtering. A count cannot show which
   nodes a shard ran, and a shared collection digest cannot show what a shard
   did with them.
3. Recompute the assignment in the gate. Load the runner module, call the same
   assignment function with the published collection and the weight file, and
   compare each record to its own partition. Do not trust the record to state
   its own partition.
4. Check identity before content. Fail when a record is missing, when two
   records share a shard index, when indices are not `0..N-1`, when the record
   profiles differ from the run profile, or when the digest of the weight file
   differs from the gate input.
5. Keep the gate fail-closed on its inputs. An empty collection, an absent
   record, a duplicate record under a different directory, and a collection
   digest that no record matches must each fail. Do not fall back to a count
   when the collection is missing.
6. Prove the gate with mutations on real data, not only with unit fixtures.
   Mutate one shard to run the whole set, remove one record, remove one node
   from the collection, change the profile, and change the expected shard
   count. Each mutation must exit non-zero, and each must name its cause.
7. Keep the publishing shard running tests. Do not add `--collect-only` to the
   shard that publishes the collection. A collect-only shard reports an empty
   result and skips its own share. Reject a caller-supplied collect-only flag
   together with a record request.
8. Allow for a container-rendered matrix value. A matrix value can reach a
   step as a string, so compare `matrix.some == '0'`, not `== 0`, and assert
   the condition against the declared matrix in a workflow test.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ----------- | ---------------- | --------------- | --------------- |
| Shared digest and count gate | Compared each shard's collection digest, shard count, and `selected + deselected == collected`, then accepted the run | A reproduction where every shard selected the whole collection returned exit code 0; the gate proved agreement, not partition | Add a selected digest per shard and recompute each shard's expected partition in the gate |
| Aggregate count as coverage evidence | Treated the sum of selected counts across shards and a green job summary as proof of coverage | A shard can select a superset or another shard's share; counts and a green conclusion stay consistent while the union is wrong | Compare node sets, not counts; require each shard's selected digest to equal its own partition |
| Publish from every shard under one name | Had all shards upload the collection to one artifact name with overwrite enabled | Concurrent jobs deleted and recreated the name; a lost delete or a name conflict failed uploads and could leave no artifact | Elect one publisher, or use a unique name per shard and check that all records agree on one collection digest |
| Key the artifact on a version that the matrix never runs | Bound the collection artifact name to a toolchain version and read the same version in the aggregate job | The matrix declared another version, so the upload never ran and the download failed on every run | Derive artifact names from declared matrix values, and assert the condition against the matrix in a workflow test |
| Add collect-only to the publishing shard | Appended a collect-only flag when the record option was set, to make collection cheap | The publishing shard collected everything and ran nothing, so its result artifact was empty and its share went untested | Capture the collection with a plugin in the normal run; the shard that publishes also runs its tests |
| Hard-code one profile in the fan-in gate | Required the pull-request profile in a gate that also serves a promotion profile | Promotion runs wrote another profile and failed the gate for the right record | Derive the profile from the same condition that selects the profile in the shard job |

## Results & Parameters

### Configuration

```yaml
# Shape of the per-shard record the gate reads:
version: 1
profile: <profile-name>
shard: <index>
shard_count: <N>
collected: <count>            # same for every shard
collected_sha256: <digest>    # same for every shard
weights_sha256: <digest>      # same for every shard
selected: <count>             # this shard only
selected_sha256: <digest>     # this shard only
deselected: <count>           # this shard only
```

### Expected Output

- The unmodified records pass with a message that names the shard count, the
  profile, and the number of collected tests.
- A shard that runs the whole set fails with a selected-count mismatch and a
  partition-digest mismatch for that shard.
- A missing record fails on the record count and the index range.
- A collection with one removed node fails on the collection digest and the
  collected count for every record.
- A record from another profile fails and names the shard.
- A wrong expected shard count fails on the record count, the index range, and
  the per-shard `shard_count`.

## Verified On

| Project | Context | Details |
| ----------- | --------- | --------- |
| A Python service monorepo with a 32-shard pull-request test job | A new fan-in gate over per-shard selection records; the first gate passed while every shard ran the whole set, then the corrected gate failed five mutations on a real collection of about nine thousand node IDs | Measured counts and mutation results in [notes](ci-shard-partition-proof.notes.md) |

## References

- [ci-test-partition-new-modules](ci-test-partition-new-modules.md) — the module tier-partition gate, with the opposite deletion rule
- [derived-artifact-gate-non-vacuity](derived-artifact-gate-non-vacuity.md) — a gate that passes over an empty derived artifact
- [required-aggregate-gate-green-because-upstream-skipped](required-aggregate-gate-green-because-upstream-skipped.md) — a green aggregate gate whose jobs never started
- [cli-flag-validation-prevent-silent-noop](cli-flag-validation-prevent-silent-noop.md) — reject incompatible flag combinations at parse time