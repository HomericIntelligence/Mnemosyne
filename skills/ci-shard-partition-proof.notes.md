# Notes: CI Shard Partition Proof

Supporting evidence for [ci-shard-partition-proof.md](ci-shard-partition-proof.md).
This file is not part of normal retrieval.

## Measured evidence

The triggering change added a fan-in gate to a pull-request test job that splits
one collected set across 32 shards. The repository is a Python monorepo. The
collection used for verification held about 9,085 node IDs, and the run profile
selected 252 root test modules.

### Weak gate that passed

The first gate checked the record count, the unique shard indices, the index
range, and equality across shards of the collection digest, the weight digest,
and the shard count. It also checked `selected + deselected == collected`.

A reproduction that wrote `selected = collected` and `deselected = 0` for every
shard returned exit code 0. The gate proved that the shards agreed on an input.
It did not prove that the shards partitioned it.

### Corrected gate

The record gained a `selected_sha256` field. The gate loads the runner module,
calls the assignment function with the published collection and the weight
file, and then requires, for each shard, that `selected_sha256` equals the
digest of that shard's partition and that `selected` equals the partition size.

Mutation results on the real collection:

| Mutation | Exit code | Reasons reported |
| ----------- | --------- | ------------------ |
| No mutation | 0 | Complete partition of about nine thousand tests |
| One shard replaced with a whole-run record | 1 | Selected-count mismatch and partition-digest mismatch for that shard |
| One record removed | 1 | Record count and index range |
| One node removed from the collection | 1 | Collection digest and collected count for each record |
| Record from another profile | 1 | Profile mismatch naming the shard |
| Wrong expected shard count | 1 | Record count, index range, and per-shard `shard_count` |

### Capture ordering

The collection plugin registers its hook with the highest ordering priority and
the shard filter plugin registers with the lowest. The collection hook
therefore records the full set before the shard plugin removes other shares.

### Publishing shard

An early version appended a collect-only flag when the record option was set.
The publishing shard then collected everything and ran nothing, and its result
artifact was empty. The corrected version captures the collection through the
plugin in the normal run, so the publishing shard runs its own share.

### Artifact identity

The first publisher election was keyed on a toolchain version that the matrix
did not declare. The upload step never ran, and the download step failed on
every run. A second version had every shard upload the collection to one name
with overwrite enabled; concurrent jobs then deleted and recreated that name.
The final version elects a single shard by its index and uses a name without a
toolchain version.

A matrix value can arrive as a string in a step condition. Compare it to a
quoted value and assert the condition against the declared matrix in a
workflow test.

### Profile binding

The fan-in gate serves both a pull-request profile and a promotion profile. An
early version hard-coded the pull-request profile, so promotion records failed
the gate. The gate now derives the profile from the same condition that selects
the profile in the shard job, and a workflow test ties the two conditions
together.

## Comparison tool

A separate offline tool compares two published collections at the node level.
It reports lost and added node IDs and the nodes whose shard would change. It
labels a shard change as provisional, because the shard numbers come from the
weight file of the comparing tree and not from the two original runs.

A comparison of the base revision against the change reported no lost node IDs
and a small number of added node IDs, which showed that the change removed no
test from the collected set.

## Limits

- The verification is local and against real collection data. The hosted run
  had not yet executed the gate at the time of writing.
- One unrelated test in the same shard failed on both the base revision and the
  change, which showed that the failure was not caused by this change.