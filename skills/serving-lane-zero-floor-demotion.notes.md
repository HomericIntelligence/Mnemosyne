# serving-lane-zero-floor-demotion — Evidence Notes

Privacy-safe supporting evidence for the main skill. Repository, organization,
issue, and pull-request identifiers are generalized per the privacy rules.

## Source Context

A production model-serving control plane operated two lanes for one model: a
full-precision KV-cache lane (BF16-class) and a newer lower-precision lane
(FP8-class). A merged pull request demoted the BF16-class lane to a zero
replica floor with a 50-replica ceiling on every cluster while the FP8-class
lane kept a 2-replica production floor.

## Evidence Chain Behind the Decision

- Lane-parity measurement: two matched replicas that differed only in the
  KV-cache data type produced identical pass or fail results on 96 of 96
  qualification cases, latency and throughput parity, and no significant
  evaluation-harness regression.
- Demand measurement: the superseded pool was overprovisioned 40–100x at
  current demand (about 1 average running request against a 38-request
  maximum per replica). Steady demand fits on one replica.
- Ceiling selection: the 50-replica ceiling per cluster still exceeds the
  64-slot burst headroom that an earlier capacity issue asked to keep. This
  is why the ceiling needs an explicit bound after the floor drops to zero:
  demand-driven scale-up becomes the only reason the pool grows.

## Configuration Layers Touched

The change edited exactly four files:

1. The serving cookbook YAML: global floor dropped, one cluster override
   floor dropped, and both cluster ceilings lowered to the shared bound.
2. The production deployment-context policy YAML: the model policy bounds
   mirrored the cookbook values, so the steady-state desired count is 0 and
   demand-driven autoscale can still start up to 50 replicas.
3. Two bound-pinning tests that assert the production policy matrix values.

## Base-Drift Detail

The directing issue recorded an older global floor (5). The checked-out base
commit already carried a lower value (1) plus a cluster override. The
effective target state was unchanged; the pull request body recorded the
actual base values and the observation that the issue body was stale. Compute
diffs against the checked-out base, never against issue-recorded numbers.

## Baseline Timeline

1. First baseline attempt failed on the environment: the fresh worktree had
   no virtual environment and a no-sync runner prevented building one. The
   repository bootstrap script remedied it.
2. Second attempt failed at collection: one requested test node identifier
   came from a stale test cache and no longer existed.
3. Third attempt was superseded by an explicit operator waiver: the
   replacement lane was already validated, so post-change evidence replaced
   the pre-change baseline. The waiver and its authority were recorded in the
   pull request.

A separate uncommitted change in a parallel worktree touched the same bound
lines with different values. The pull request declared it as a future
conflict risk, not part of the change.

## Validation Record

- Repository setup script: format check, lint, and type check passed in the
  worktree.
- Pre-commit hooks on the change commit: format, lint, YAML/TOML checks, and
  type check passed.
- Pull-request CI: all test shards, lint, typecheck, documentation-strict,
  deployment-policy, promotion-policy, supply-chain scans, and artifact jobs
  passed on two runs; the change was then merged.

## Provenance

Lesson extracted at a DONE ceremony on 2026-10-24 from the merged demotion
pull request described above. The repository-specific identifiers are
withheld; the decision rule and the measured parameters are the durable
content.
