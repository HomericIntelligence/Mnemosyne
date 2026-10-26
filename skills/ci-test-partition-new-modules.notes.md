# Notes: Classify New Test Modules in the CI Partition Inventory

Supporting evidence for [ci-test-partition-new-modules](ci-test-partition-new-modules.md).
Measured case from one Python monorepo delivery on 2026-10-26; all
identifiers generalized.

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
