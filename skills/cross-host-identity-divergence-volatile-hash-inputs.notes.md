# Notes: Cross-Host Identity Divergence from Volatile Hash Inputs

Supporting evidence for `cross-host-identity-divergence-volatile-hash-inputs.md`.
Identifiers of the private deployment (product, model, host, job, repository,
and digest values) are withheld. Only decision-relevant shapes are kept.

## Verified failure shape (before the correction)

- A gateway job rendered on the login node of one shared parallel filesystem
  failed within about 13 seconds on a specific compute node, repeatedly and
  deterministically: three submissions, all on the same variant node, one more
  on a second variant node for comparison.
- The failure message compared a recomputed identity with the identity baked
  into the rendered job environment: expected `ctx-…A`, observed `ctx-…B`
  (two full 64-hex digests), with instructions to restart from the active
  deployment release.
- The same rendered job passed its identity check on a different compute node
  whose shared-filesystem client reported the same device number as the
  login node.
- On-host resolution on the variant node reproduced the in-job digest
  `ctx-…B` exactly, which proved the divergence came from context
  resolution, not from job transport.

## Decisive diagnostic: canonical payload leaf diff

The production canonical hash payload was dumped on both hosts through the
production code path (read-only scheduler probes) and diffed leaf by leaf:

```text
differing leaves:    4
  roots.admin_device              36 -> 37
  roots.admin_deployment_device   36 -> 37
  roots.public_device             36 -> 37
  roots.public_deployment_device  36 -> 37
identical leaves:    every other field
  inode values, root path strings, binding digest, service uid/gid,
  specification body, release and component identities
```

Interpretation: exactly one class of input (client mount-instance device
numbers) diverged; nothing about the logical deployment differed. The equal
inode values across hosts were a property of that mount generation, not a
contract; inode numbers still change at any directory replacement, so the
fix removed the complete volatile class (8 fields) rather than only the
4 fields observed that day.

## Correction and its verification

- The identity payload kept only launch-constant inputs: specification
  content, release and component identities, root path strings, and the
  static binding digest. The 8 mount-instance fields stayed on the resolved
  root identity object, where same-host binding revalidation continues to
  use them.
- Regression coverage: two mount-instance fixtures that differ in all 8
  volatile fields give the same identity, and the production rendered-evidence
  verification accepts the first fixture's environment when evaluated after
  resolution with the second. The test failed before the correction with the
  exact historical digest and passes after it.
- Post-correction live probes on the same host pair (login device 36,
  variant compute node device 37) resolve byte-identical identities.
- A lane service activated at the corrected revision in one attempt on a GPU
  compute node and stayed stable, versus three deterministic 13-second
  failures on the variant node before the correction.

## Bounded replay when the second host cannot execute probes

A separate incident on a comparable deployment confirmed the same divergence
shape without any second-host probe. Scheduler queues were saturated for
days, so no compute-node diagnostic job could start. The decisive evidence
came from one reachable host:

- Resolution through production code on the submit host produced the live
  digest (render-side value) and exposed every payload leaf.
- Re-hashing the production payload with only the four device leaves changed
  from the submit host's value (36) to the hypothesis value (37) reproduced
  the previously observed failing digest exactly, all 64 hexadecimal digits.
  No other leaf was varied.
- Consistency across the fleet removed remaining doubt: 15 job failures in
  one day, each on different node pairs, reported one and the same expected
  digest in the failure message. Only the 2 jobs that landed fully inside
  the matching device cohort started and stayed up.
- Scheduler accounting plus the failure-message digest therefore gives a
  zero-cost census of the cohort split and measures the lost replacement
  capacity while the correction rolls out.

Two accuracy notes for the replay variant:

- Replay on exact construction only. Start from the resolved production
  payload; change the suspect leaf class; keep serialization, sorting, and
  branch handling in production code. A hand-retyped copy is the failed
  attempt in the main entry, not this variant.
- Strength is asymmetric. An exact match identifies the divergent leaf
  class. A mismatch only removes that hypothesis; it does not clear other
  classes, because the replay construction or the hypothesis can still be
  wrong.

## Operational notes

- Probe jobs that import the installed tree must use the tree's own virtual
  environment interpreter. A newer system interpreter elsewhere in the shell
  path (major version mismatch) fails native-extension imports with a
  misleading "unknown location" message and can imitate a product defect.
- Pre-correction identities rotated once relative to post-correction
  identities. Stored records that pinned an old identity failed closed until
  their owner published again; that is the designed migration path.
- No consumer of the identity required the mount-instance fields: every
  consumer compared against a live-computed identity or validated the digest
  format only. Confirm that property in your own codebase before you remove
  identity inputs.
