# Notes: Classify New Test Modules in the CI Partition Inventory

Supporting evidence for [ci-test-partition-new-modules](ci-test-partition-new-modules.md).
Measured cases from two Python monorepo deliveries on 2026-10-26 and
2026-10-28, and a third on 2026-11-02; all identifiers generalized.

## Measured case

- Change: one pull request added five new test root modules to a repository
  whose ordinary pull-request profile partitions test modules into an explicit
  pull-request list and a nightly list. Every other family of checks is
  separate.
- First hosted run: all 32 test shards failed in about 13 to 35 seconds each
  with the configuration error `The test-tier lists do not partition root
  modules: unclassified modules: <the five new paths>`. Lint, typecheck, docs,
  secrets, policy, and artifact checks all passed. The summary job failed with
  `required job did not succeed: test`.
- The shard log, not re-testing, gave the diagnosis: the runner validates the
  inventory before it selects any test case, so no test executed.
- Fix: one inventory file edit in the same branch. Classification by
  sibling-suite locality put three modules with their fast in-process siblings
  in the pull-request list and two modules with their heavy lifecycle siblings
  in the nightly list. After the fix the local loader reported 211 and 102
  classified modules, the full count of discovered modules.
- Local proof before push: the runner own inventory loader returned a
  validated partition, and the tier-covering tests (59 tests selected by a
  `-k tier` filter over the CI workflow test module) passed.
- Second hosted run: green; the branch merged and the default-branch run on
  the merge commit also passed.

## Diagnostic cues

- Uniform sub-minute failure of every shard with all other check families
  green means job configuration, not test behavior.
- The aggregate summary lists the test family as `failure` while its own
  per-check table shows the neighbors as `success`; read one shard log for the
  configuration line.
- The loader error names both directions: `unclassified modules` for tree
  modules missing from the lists, and `unknown modules` for list rows whose
  module no longer exists. A removal must therefore drop the row in the same
  change, the opposite of a changed-path diff gate.
- A union-invariant failure that only one shard or one suite job shows, while
  the other shards pass, marks a nontier-family gap in module discovery, not
  a list row.
- When neighboring checks fail from a different first cause, attribute each
  check family on its own error text. A latent lane-caused gap can surface
  only after the foreign failures that masked it are repaired.

## Measured case 2: nontier suite family (2026-10-28)

- Change: one pull request added a six-module real-identity conformance suite
  in a new test directory beside the tiered root modules and the integration
  directory. The suites run through a separate real-identity script and a
  release workflow, never through the tiered profiles.
- The invariant had the shape `promotion tier ∪ nontier families == all
  discovered modules`, and module discovery enumerated only the tiered root
  and the integration directory. The new directory belonged to neither side.
- First full hosted run: only the shard that contained the inventory invariant
  test failed with the union assertion, and the release suite job failed on
  the same test. The other 31 shards passed. Earlier partial runs had masked
  the gap: foreign typecheck breakage and a changed-path classifier failure
  had reddened the same checks first, and the invariant surfaced only after
  both causes were repaired in the tree.
- Diagnosis: per-family attribution on each check's own error text separated
  the lane-caused union failure from the foreign typecheck failure.
- Fix: extended the runner's discovery function to enumerate the suite
  directory as a nontier family, with the nontier semantics documented in the
  discovery contract. No tier list row, no pinned root count change (only
  root modules feed it), no inventory file edit at all.
- Local proof before push: the inventory invariant test and its neighbors
  passed (58 tests selected by a `-k tier` filter over the CI workflow test
  module).
- Second hosted run: all gates green, including the 32 shards and the release
  suite job; the change merged.

## Measured case 3: classified but never executed (2026-11-02)

- Context: a repository with a pull-request tier and a heavier tier, 32 shards
  each, and a JUnit artifact per shard.
- The module of interest was correctly classified in the heavier tier. The
  partition gate never fired, because the inventory was valid and complete.
- A change-covering run of the pull-request profile reported green: 52 checks,
  0 failures, and 9082 testcases across the 32 shard artifacts.
- No case from the module of interest appeared in any of those 32 artifacts.
  The module failed on the default branch: 1 failed, 12 passed locally.
- The heavier tier did select the module. Its shard listed the module in the
  shard's `modules` field, but the JUnit held 245 cases against roughly 506
  expected, with 26 failures, so the shard stopped before the module's later
  cases.
- Result: the failure was reported by no CI path. Three separate failures in
  that module had reached the default branch while every pull-request report
  was green.
- Recovery used: run the module directly, locally, at the default-branch
  commit. That reproduced the red in under a second and established it as
  pre-existing and not lane-caused.
- Two further reds in the same module were found by other sessions with the
  same local method, which is why per-family attribution matters here.
- Fixes went out as small separate changes; one competing fix for the same red
  was withdrawn in favour of the one that removed the stale citations instead
  of widening the guard. Both were verified against the same module.
- Retrieval boundary: byte counts, case counts and shard counts above are
  measurements from one repository. Treat the ordering and the abort signal as
  general; treat the exact numbers as case-specific.
