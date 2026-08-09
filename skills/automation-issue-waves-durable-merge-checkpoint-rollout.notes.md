# ProjectHephaestus Durable Issue-Wave Notes

## Session Status

- Date: 2026-08-06
- Source: reviewed implementation plan supplied to `/learn`
- Verification: unverified
- No Hephaestus code, tests, live GitHub mutation, or CI run was performed in this session.
- The plan already incorporated review corrections for complete configuration transport and the
  final audit-only lifecycle.

These notes retain ProjectHephaestus-specific names and commands. Re-read the live source before
implementation because construction sites and line numbers can drift.

## Intended CLI and Configuration Transport

Add a positive `--issue-limit` and reuse the same positive parser for `--loops` and
`--parallel-repos`. Reject `--issue-limit` whenever `--issues` or `--prs` was explicitly supplied,
while preserving the existing valid combined direct issue/PR recovery scope.

Required transport:

```text
argparse Namespace.issue_limit
-> loop_runner.LoopConfig.issue_limit
-> coordinator_types.PipelineConfig.issue_limit
-> coordinator_types._StageRunConfig.issue_limit
-> coordinator_runtime.StageContext.config.issue_limit
-> pipeline.stages.repo.RepoStage wave admission
```

Append `PipelineConfig.issue_limit` after `force` so the established third positional argument
remains `repo_source_factory`. Add a regression test that constructs the real coordinator and
observes the value in the real repository stage; unit tests that stop at `PipelineConfig` do not
prove the handoff.

## Proposed Checkpoint Owner

New module:

```text
hephaestus/automation/issue_waves.py
```

Proposed frozen types:

- `WaveLease`
- `WaveMergeReceipt`
- `WaveIssueOutcome`
- `WaveRecord`
- `WaveCheckpoint`
- `WaveAdmissionPlan`

Proposed store responsibilities:

- strict load and audit-only read;
- admission planning and phase validation;
- compare-and-swap selection sealing;
- direct recovery-scope binding;
- merge-receipt persistence;
- terminal-outcome persistence;
- prior-wave verification;
- final completion.

Use actionable `IssueWaveError` subclasses. `ArmingStateStore` is not reusable for this authority
because it is per-issue and explicitly best-effort.

## Local State and Security Contract

Checkpoint path:

```text
<repo>/build/.issue_implementer/issue-wave-checkpoint.json
```

Keep a stable sibling lock. Use the existing
`file_lock(..., blocking=False, require_exclusive=True)` and atomic `write_secure()` with mode
`0600`. Before every read, lock, or write, reject:

- a path escaping the repository;
- symlinked state or lock paths;
- non-regular files;
- repository identity mismatch;
- malformed schema, phase, identifier, or full SHA;
- impossible phase transitions.

## Repository-Stage Ordering

`sync_checkout` already returns the validated default-branch SHA from the Git worker. Retain every
successful sync result under a generic repository-stage payload key such as:

```python
SYNCED_MAIN_SHA_KEY = "_synced_default_branch_sha"
```

Move wave admission between synchronization and `ensure_state_labels()`:

```text
CLONE/SYNC -> WAVE_ADMIT -> LABELS -> DISCOVER
```

Direct-scope bootstrap returns after synchronization. The coordinator binds the requested
issue/PR recovery scope against the active wave before it calls `ensure_state_labels()` or
activates direct cursors.

## Selection and Source Transport

Use the oldest-first metadata stream already exposed by
`loop_repo_manager._iter_open_issue_meta()`. For each candidate:

1. Fetch fresh `IssueFacts`.
2. Classify through the canonical seeding/classification helpers.
3. Exclude closed, `stage is None`, and `StageName.FINISHED` results.
4. Append only `facts.number`.
5. Stop at 1/2/4/8 or exhaust all pages for the final phase.

An empty result is sealed as an empty wave. Any read/classification failure leaves the checkpoint
unchanged.

Add an optional `WaveLease` to `RepoIssueSource`, `_DirectIssueSource`, and `_DirectPrSource`.
Store only synthetic metadata needed to replay sealed numbers; fetch fresh facts immediately before
admission. Put the lease in each `WorkItem` payload under one canonical key.

Set a coordinator-wide wave-mode latch when a checkpoint-backed source becomes active. In
`_reseed_if_converged()`, return `False` for the rest of the process so `--loops` cannot rediscover
additional work.

## Direct Recovery Gate

After synchronization and before label setup:

1. Start with direct `--issues` as repository-local issue identifiers.
2. Resolve every direct `--prs` value through the target repository accessor.
3. Reject a PR with no linked issue.
4. Bind the combined issue set to the active wave.
5. Carry the returned lease on both direct cursors.

A binding error fails bootstrap before GitHub workflow mutation. Outside an active rollout,
existing identifier-based behavior remains unchanged.

## Git Ancestry Worker Operation

Register read-only Git operation:

```text
verify_issue_wave_ancestry
```

It accepts an expected repository root, current synchronized main SHA, and one or more ancestor
SHAs. Under the existing Git lock, validate paths and full SHAs, then run:

```bash
git merge-base --is-ancestor <ancestor> <main>
```

Return failure for a missing/non-ancestor commit, malformed SHA, unexpected checkout path, timeout,
or subprocess error. Test multiple merge receipts in one request.

## Merge Receipt Contract

Extend immutable `MergeWaitCycleCompleted` with optional `merge_sha`. Validate it as a full commit
SHA in `__post_init__`.

Populate the field only when the conditional merge response:

- returns success;
- states `merged: true`;
- contains a valid full `sha`;
- reconciles to a terminal merged PR state.

In `MergeWaitStage`, persist issue, PR, reviewed head, and merge SHA before calling the existing
merged route. For a wave item, a missing issue, PR, or merge SHA is terminal failure. Existing
non-wave already-merged behavior remains unchanged, but already/external/ambiguous merges receive no
wave receipt.

## Finished-Stage Ordering

In `FinishedStage.RECORD`, synthesize any missing result, then record the checkpoint terminal
outcome before appending to the in-memory ledger. On `IssueWaveError`, replace the result with a
failed checkpoint-write result. Mark the item as recorded only after the durable call and preserve
the worktree on failure.

A recovery run may replace an earlier failed outcome only after the same selected issue finishes
with a valid receipt.

## Documentation Targets

- `docs/adr/0021-durable-issue-wave-checkpoints.md`: authority, repository/main binding, merge
  receipts, audit-only completion, security, recovery, and rollback consequences.
- `docs/adr/README.md`: register contiguous ADR 0021.
- `docs/architecture.md`: durable-state exception, intake ordering, one-pass sources, restart
  reconstruction, merge receipts, terminal ordering, CLI lifecycle.
- `docs/runbooks/automation-loop-crash.md`: staged commands, same-selector resume, direct recovery,
  completed audits, and backup-based restoration instead of hand editing.

Do not add the checkpoint to the automation coverage omit list merely because it participates in
orchestration. Keep pure state-machine and persistence logic directly unit-testable.

## Test Inventory

Create:

```text
tests/unit/automation/test_issue_waves.py
tests/unit/automation/test_issue_wave_cli.py
tests/unit/automation/pipeline/test_issue_wave_pipeline.py
tests/unit/automation/pipeline/test_issue_wave_git.py
```

High-value regressions:

- positive parsing for all three numeric flags and direct-scope mutual exclusion;
- legacy third-positional `PipelineConfig` binding;
- complete CLI/config/coordinator/real-repository-stage handoff;
- first-N filtering, immutable selection replay, empty/all modes, and post-seal drift;
- admission and recovery binding before label setup;
- same-process reseed suppression;
- cross-store reopen and compare-and-swap conflicts;
- merge receipt authority and terminal persistence ordering;
- prior-wave override, PR mismatch, missing receipt, and ancestry failures;
- final completion and repeat audit-only runs with no mutation;
- malformed state restored via the supported backup process rather than manual edits.

## Proposed Verification Commands

```bash
uv run pytest \
  tests/unit/automation/test_issue_wave_cli.py \
  tests/unit/automation/test_issue_waves.py \
  tests/unit/automation/pipeline/test_issue_wave_pipeline.py \
  tests/unit/automation/pipeline/test_issue_wave_git.py -q

uv run ruff check hephaestus/automation tests/unit/automation
uv run mypy hephaestus/automation tests/unit/automation

uv run pytest \
  tests/unit/docs/test_adr_records.py \
  tests/unit/docs/test_automation_loop_architecture.py \
  tests/unit/validation \
  tests/unit/automation/pipeline/test_pipeline_architecture.py \
  tests/unit/automation/test_atomic_write_guard.py -q

uv run pytest tests/unit -q
```

Run the operational sequence only after implementation and CI pass:

```bash
hephaestus-automation-loop --repos <REPO> --issue-limit 1
hephaestus-automation-loop --repos <REPO> --issue-limit 2
hephaestus-automation-loop --repos <REPO> --issue-limit 4
hephaestus-automation-loop --repos <REPO> --issue-limit 8
hephaestus-automation-loop --repos <REPO>
hephaestus-automation-loop --repos <REPO>  # repeat audit-only check
```
