---
name: automation-issue-waves-durable-merge-checkpoint-rollout
description: "Design and verify durable repository-scoped issue waves that admit exact selections in 1, 2, 4, 8, then all phases. Use when: (1) an automation rollout must advance only after the prior exact issues merged normally, (2) restarts must replay immutable identifiers without rediscovery, (3) external or ambiguous merges must not authorize the next wave, (4) completed rollouts must become permanently audit-only, (5) implementation review must cover partial-wave resume and direct-recovery terminalization, or (6) the rollout's exact-head review-to-merge evidence needs auditing."
category: architecture
date: 2026-08-06
version: "1.1.0"
user-invocable: false
verification: verified-ci
history: automation-issue-waves-durable-merge-checkpoint-rollout.history
tags:
  - automation-loop
  - issue-waves
  - staged-rollout
  - durable-checkpoint
  - merge-receipt
  - git-ancestry
  - compare-and-swap
  - fail-closed
  - repository-scope
  - restart-recovery
  - audit-only
  - dry-run
---

# Automation Issue Waves: Durable Merge-Checkpoint Rollout

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-06 |
| **Objective** | Stage eligible repository issues through durable `1 -> 2 -> 4 -> 8 -> all` waves, admitting a later wave only after the previous wave's exact issues and automation-owned normal merges are verified on synchronized `main`. |
| **Outcome** | Implemented and merged in ProjectHephaestus PR #2687 / issue #2453. Implementation review caught partial-wave resume blocked by a changed `main` SHA and lease-backed direct recovery silently dropping `state:skip` / `state:plan-blocked` entries; the final patch added receipt-backed ancestry resume, fresh merge-fact checks, checkpointed terminal failures, and regression coverage. |
| **Verification** | `verified-ci` — the final reviewed head passed the repository CI and required-checks gate, then merged through the loop's exact-head conditional path. A live 1/2/4/8/all rollout was not part of this capture. |

## When to Use

- A GitHub automation loop needs a canary-style rollout across issues: one issue, then two, four,
  eight, and finally every remaining eligible issue.
- A process crash must resume the exact sealed issue identifiers rather than repeat discovery against
  a changed backlog.
- Multiple processes may attempt to seal, resume, or advance the same repository rollout.
- The next wave must depend on the automation loop's own successful conditional merges, not merely
  on closed issues, merged pull requests, labels, review prose, or CI status.
- The default branch may be rebased or rewritten, so prior base and merge commits must be checked as
  ancestors of a freshly synchronized default-branch commit.
- Operators need targeted issue/PR recovery without allowing unrelated work to bypass an active
  rollout.
- A completed rollout must remain completed and audit-only until a separately designed explicit
  reset workflow exists.
- In-memory queues and per-issue best-effort records are insufficient because admission authority
  must survive restarts and coordinate across processes.

## Verified Workflow

The checkpoint design below was implemented for issue #2453. CI validated the implementation and
the live PR audit below validated the review-to-merge ordering; a full staged rollout remains
operational follow-up.

### Quick Reference

```python
WAVE_LIMITS = (1, 2, 4, 8, None)

# None means the final all-eligible phase only after wave 8 is verified.
# It does not mean "start an ordinary checkpointed rollout" when no checkpoint exists.
```

```text
absent + omitted       -> ordinary unbounded discovery; no checkpoint
absent + 1             -> seal wave 1
active + same selector -> replay the exact sealed identifiers
complete + next limit  -> verify prior wave, then seal 2/4/8
wave 8 complete + none -> verify wave 8, then seal final all-eligible wave
final active + none    -> replay final wave; verify and mark rollout completed
completed + none       -> audit-only revalidation; no workflow mutation
completed + bounded    -> reject: rollout already completed
active + unexpected    -> reject before GitHub mutation
```

Recommended operator sequence:

```bash
<automation-loop> --repos <REPO> --issue-limit 1
<automation-loop> --repos <REPO> --issue-limit 2
<automation-loop> --repos <REPO> --issue-limit 4
<automation-loop> --repos <REPO> --issue-limit 8
<automation-loop> --repos <REPO>  # final all-eligible wave, then later audits
```

### PR #2687 / issue #2453 review-and-merge audit

The implementation review found two concrete recovery bugs and kept the PR in the no-go state:

1. After one issue in a multi-issue wave merged, `main` advanced beyond the sealed base while
   another selected issue remained unfinished. Resume must allow that expected advancement only
   when recorded merge receipts, fresh GitHub facts, and ancestry checks prove it; an unconditional
   `current_main == sealed_base` check blocks valid crash recovery.
2. Lease-backed direct recovery could drop a selected issue whose fresh classification became
   `state:skip` or `state:plan-blocked` before it reached the finished sink. Reconcile those
   overrides into checkpointed terminal failures so the later wave sees the exact failure rather
   than a misleading generic incompleteness.

The corrected head `19e513196102756eccae5a804f343855e63f2ebd` received the final head-bound
`COMMENTED` review record at `03:13:32Z`; the inline implementation replies documented both
regressions and their tests. GitHub recorded `state:implementation-go` at `03:15:56Z`, removed
`state:implementation-no-go` at `03:15:59Z`, completed `unit-tests` at `03:24:24Z` and
`required-checks-gate` at `03:25:12Z`, then merged commit
`3388466e00db9b60364bcad5119bb628bcce2640` at `03:26:07Z`. The final PR state reported
`autoMergeRequest: null`; review prose and CI remained evidence/context, while the loop-owned GO
label and exact-head conditional merge formed the authorization path.

### 1. Give one component exclusive checkpoint ownership

Create one module that owns all checkpoint types and transitions:

- repository identity and schema validation;
- phase sequencing and selector validation;
- immutable ordered selections;
- compare-and-swap sealing and advancement;
- active-wave recovery-scope binding;
- loop-owned merge receipts;
- per-item terminal outcomes;
- prior-wave verification;
- final completion and audit-only reads;
- actionable, typed diagnostics.

Do not distribute these rules across CLI parsing, source discovery, merge waiting, and terminal
cleanup. Those components should call the store; they should not reinterpret its state.

The checkpoint is an admission authority, not a serialized queue. Runtime queues can still be
reconstructed from live systems, but only identifiers admitted by the current immutable wave may
enter them.

### 2. Bind the checkpoint to one repository and one synchronized branch history

Use a stable repository-local path outside the source package, for example:

```text
<repo-root>/build/<automation-state>/issue-wave-checkpoint.json
<repo-root>/build/<automation-state>/issue-wave-checkpoint.json.lock
```

Every persisted record should include a normalized repository identity, schema version, state,
revision/generation, phase, ordered positive issue identifiers, and the synchronized default-branch
SHA used when the wave was sealed. Validate full commit SHAs and identifiers strictly.

Before every read, lock, or write:

1. Resolve and confine the state directory beneath the expected repository root.
2. Reject symlinks and non-regular checkpoint/lock files.
3. Acquire a stable sibling lock in nonblocking exclusive mode.
4. Load strictly; reject unknown fields, invalid enums, duplicate identifiers, malformed SHAs,
   repository mismatch, or impossible phase/state combinations.
5. Write atomically with mode `0600`.

Fail closed when exclusive locking is unavailable. A best-effort record is unsuitable for rollout
admission because two processes could both believe they advanced the same wave.

### 3. Use compare-and-swap for every durable transition

Separate planning from mutation:

```python
intent = store.plan_admission(
    requested_limit=requested_limit,
    current_main_sha=synchronized_main_sha,
)

# Discovery and fresh classification happen without changing the checkpoint.
selected_numbers = collect_eligible_issue_numbers(intent)

lease = store.seal_selection(
    intent=intent,
    issue_numbers=selected_numbers,
)
```

The intent carries the expected checkpoint generation/fingerprint. `seal_selection()` reopens the
file under the exclusive lock and rejects the write if state changed after planning. Never accept a
second selection for an already sealed phase, even if it happens to contain the same numbers.

An empty eligible set is still an immutable selection. Persist the empty wave so a restart sees the
same decision and the phase can be verified/advanced deterministically.

### 4. Synchronize checkout before admission and mutate labels only afterward

Admission ordering is a safety boundary:

```text
read repository -> synchronize/validate default branch -> retain exact main SHA
-> load/plan/verify/seal wave -> validate direct recovery scope if present
-> provision or mutate workflow labels -> discover/admit queue items
```

The synchronization operation must return a validated full commit SHA. Store it in generic
repository-stage state, not only in a direct-scope special case.

If checkpoint planning, prior-wave verification, or recovery binding fails, stop before label
provisioning, agent invocation, PR creation, or merge mutation. GitHub reads and local checkout
synchronization are allowed before the gate because they are needed to diagnose and verify it.

### 5. Seal fresh eligible identifiers, not classified runtime objects

Walk candidates in a deterministic order, normally oldest first. For every candidate, fetch fresh
facts and classify it immediately. Exclude anything that is now:

- closed;
- skipped, blocked, or an epic according to current policy;
- unclassifiable (`stage is None`);
- already terminal/finished.

Append only a positive issue number. Stop at the bounded limit for phases 1/2/4/8; exhaust all
pages for the final phase. Do not persist API payloads, labels, classified queue entries, or
work-item objects as the selection.

A failed read or classification must leave the checkpoint unchanged. Once sealing succeeds, a
restart replays the stored ordered identifiers and never reselects replacements for items that
later drift.

### 6. Re-read sealed issues immediately before queue admission

The immutable selection says which issues were chosen, not that stale facts remain valid. Fetch and
classify each sealed number again immediately before enqueueing.

Treat closure, skip/block/epic drift, a closed issue without a qualifying merge, or a merged PR
without this checkpoint's loop-owned receipt as a failed terminal outcome. Do not replace the issue
with another candidate and do not perform issue-label or agent mutations for the drifted item.

Attach a frozen wave lease to every admitted work item. The lease should identify the repository,
wave/phase, checkpoint generation, base-main SHA, and exact ordered selection. Every receipt and
terminal write must compare the supplied lease against the active checkpoint.

### 7. Make checkpoint-backed sources one-pass

Generic convergence logic often rediscovers work for `--loops N`. That is incompatible with an
immutable wave: after its source drains, additional discovery could silently admit work outside the
sealed set.

Mark checkpoint-backed repository, direct-issue, and direct-PR sources with the same wave lease.
When any such source activates, suppress same-process reseeding for the rest of the run.

```python
if wave_mode_active:
    logger.info("checkpointed issue wave drained; suppressing loop reseed")
    return False
```

### 8. Restrict direct recovery to active-wave membership

Explicit issue and PR selectors remain useful for repairing one failed item. During an active
rollout, bind them to the current wave after checkout synchronization and before any mutation:

1. Resolve every direct PR to its linked issue using the target repository accessor.
2. Reject a PR without a linked issue.
3. Require every requested issue to be a member of the active wave's immutable selection.
4. Return the current wave lease and attach it to each direct-source item.

Outside an active rollout, preserve the existing repository-local identifier behavior. A bounded
wave selector and explicit issue/PR scopes should be mutually exclusive at CLI parse time; recovery
uses the explicit scope on a later invocation, not both selectors together.

### 9. Record only normal loop-owned conditional merges

A merge receipt is authorization evidence, not an observation that a PR is now merged. Capture it
only from a successful conditional merge response initiated by the loop and validated at the exact
reviewed head.

```python
@dataclass(frozen=True)
class WaveMergeReceipt:
    issue_number: int
    pr_number: int
    reviewed_head_sha: str
    merge_sha: str
```

Require the response to state that the merge succeeded and to include a valid full merge commit
SHA. Then reconcile live PR state and persist the receipt before routing the item down the merged
path.

Already-merged, externally merged, ambiguous, malformed, or unsuccessful results produce no
receipt. They may retain their ordinary non-wave behavior, but they cannot authorize wave
advancement.

### 10. Persist terminal outcomes before in-memory completion

At the terminal stage:

1. Ensure an item result exists.
2. Persist the wave outcome under the item lease.
3. If persistence fails, replace the result with a checkpoint-write failure.
4. Append the final result to the in-memory ledger only after persistence.
5. Preserve the worktree on failure so recovery evidence remains available.

A failed outcome may later be replaced only when the same sealed issue completes with a valid
receipt. The store must never allow a different issue or wave lease to overwrite the record.

### 11. Verify prior waves against fresh GitHub facts and Git ancestry

Before sealing the next phase, require every selected issue to:

- have a passing terminal outcome;
- remain free of post-selection skip/block/epic overrides;
- remain associated with the same merged PR recorded by the receipt;
- have a valid loop-owned receipt for its reviewed head and merge commit.

Then submit a read-only Git-worker operation inside the existing repository Git lock. Validate that
the prior wave's base-main SHA and every merge SHA are ancestors of the newly synchronized main SHA:

```bash
git merge-base --is-ancestor <prior-base-or-merge-sha> <current-main-sha>
```

Reject malformed SHAs, unexpected repository paths, missing commits, non-ancestors, timeouts, and
Git subprocess errors. Keeping Git operations in the worker boundary prevents the coordinator from
inventing a second locking or subprocess policy.

Open, unmerged, closed-without-merge, failed, blocked, missing-receipt, mismatched-PR, or
rewritten-main states block advancement before mutation.

### 12. Make final completion permanent and audit-only

After wave 8 verifies, an omitted limit seals the final all-eligible wave. A later omitted-limit run
resumes that exact final selection. Once all its items verify, atomically mark the rollout completed
without selecting new work.

Completed behavior is intentionally asymmetric:

- omitted selector: strict audit-only reload and revalidation, then success with no label, agent,
  PR, or merge mutation;
- any bounded selector: reject with an actionable "rollout already completed" diagnostic;
- no implicit checkpoint recycling or silent restart.

Starting a new staged rollout requires a separately designed explicit reset workflow with its own
authority and rollback semantics. Do not hide reset behind checkpoint deletion.

### 13. Keep dry-run diagnostic and non-authoritative

Dry-run may load and validate the checkpoint, report the planned phase, show the ordered candidate
identifiers, explain drift, and exercise read-only ancestry diagnostics. It must not seal a
selection, advance a wave, write receipts/outcomes, complete the rollout, provision labels, invoke
agents, create PRs, or merge.

### 14. Freeze the integration with adversarial tests

Required test groups:

- strict schema, repository, SHA, identifier, path-confinement, symlink, non-regular-file, and mode
  validation;
- nonblocking lock behavior, atomic write failures, compare-and-swap conflicts, immutable and empty
  selections, and reopening through a second store instance;
- selector ordering across 1/2/4/8/all, active resume, unexpected selectors, final completion, and
  completed audit-only behavior;
- first-N fresh eligibility filtering, closed-during-selection handling, exact-ID replay, post-seal
  drift, and no replacement selection;
- real CLI-to-runtime-to-repository-stage configuration transport, including positional API
  compatibility when adding an optional field;
- mutation ordering proving admission and direct recovery binding precede label setup;
- one-pass source behavior across convergence loops;
- direct issue membership and direct PR-to-issue resolution;
- conditional merge SHA validation, receipt-before-route ordering, and rejection of external or
  ambiguous merges;
- terminal persistence before ledger append and worktree preservation on checkpoint failure;
- prior-wave fresh-fact failures, mismatched PRs, missing receipts, accepted ancestry, rewritten
  history, malformed SHAs, unexpected paths, and Git subprocess failures;
- dry-run non-mutation and completed audit-only non-mutation.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Use in-memory queues as rollout authority | Treated the current process's queue contents as the wave selection | Queues disappear on restart and can be reseeded from a changed backlog | Persist only immutable issue identities and reconstruct runtime work under a durable admission gate |
| Reuse per-issue best-effort state | Stored wave progress in records designed to tolerate lock or write failure | Cross-process admission can split-brain when durable writes are optional | Wave authority needs strict exclusive locking, atomic writes, and fail-closed compare-and-swap transitions |
| Persist classified objects | Stored API metadata, labels, `SeedEntry`, or `WorkItem` instances as the wave | Those objects become stale, are schema-heavy, and couple durability to runtime internals | Seal ordered positive identifiers only; fetch and classify fresh facts at selection and again at admission |
| Replace an ineligible sealed item | Rediscovered another candidate after a selected issue closed or became blocked | The wave ceased to be immutable and a restart could run a different set | Record drift as a failed terminal outcome; recovery must address the same selected identifier |
| Treat any merged PR as success | Advanced when GitHub showed a linked PR was merged | The merge could be external, ambiguous, or unrelated to the reviewed head | Require a receipt captured from the loop's successful exact-head conditional merge response |
| Verify only current PR state | Checked `MERGED` without confirming commit ancestry on synchronized `main` | A force-push or rewritten default branch can remove the supposedly completed work | Verify prior base and every receipt merge SHA as ancestors of current synchronized main |
| Persist completion after ledger append | Updated the in-memory result before writing the checkpoint | A crash could report/process success without durable terminal evidence | Persist the checkpoint outcome first; convert write failure to item failure and preserve the worktree |
| Let convergence reseed a wave | Allowed generic `--loops` behavior to discover more work after the sealed source drained | Unselected issues bypassed the checkpoint within the same process | Make every checkpoint-backed source one-pass and latch wave mode for the entire run |
| Permit arbitrary direct recovery | Allowed `--issues` or `--prs` to enqueue unrelated work while a wave was active | Explicit scopes became a bypass around staged admission | Resolve PRs to issues and require active-wave membership before any workflow mutation |
| Recycle completed checkpoints | Interpreted a bounded selector after completion as a new rollout | Historical authority and auditability were silently destroyed | Completed is permanent and audit-only; require a separately designed explicit reset workflow |
| Let dry-run mutate local state | Sealed a checkpoint because no GitHub mutation was planned | The preview changed what a later real run was allowed to execute | Dry-run may diagnose and display selections, but must not seal, advance, record, or complete |
| Add a config field in the middle of a dataclass | Inserted an optional rollout field before an established positional dependency | Existing positional callers silently rebound to the new field | Append optional public fields after existing positional contracts and test the legacy binding |
| Resume only when `current_main_sha == sealed_base_sha` | A two-issue wave merged its first issue, then a restart rejected the unchanged selector because `main` had advanced as expected | Resume after a partial successful wave must accept recorded receipt progress only with fresh merge facts and ancestry validation |
| Drop a lease-backed direct recovery after classification became `state:skip` or `state:plan-blocked` | The direct source discarded the selected entry before the finished sink, leaving no checkpoint terminal outcome | Reconcile selected external overrides into durable terminal failures; never silently omit a sealed identifier |

## Results & Parameters

### Verified implementation and merge parameters

```text
issue: 2453
pull_request: 2687
final_reviewed_head: 19e513196102756eccae5a804f343855e63f2ebd
implementation_go: 2026-08-07T03:15:56Z
implementation_no_go_removed: 2026-08-07T03:15:59Z
required_checks_gate: 2026-08-07T03:25:12Z
merge_commit: 3388466e00db9b60364bcad5119bb628bcce2640
merged_at: 2026-08-07T03:26:07Z
native_auto_merge: null
```

The review-to-merge contract is: final review and implementation replies bind to the current
head; the exclusive loop-owned GO label is written only after fresh live-state guards; required
checks complete as repository merge context; `merge_wait` conditionally merges that exact head;
and a rerun treats the merged PR as terminal rather than trying to infer authority from
`autoMergeRequest`.

### Fixed phase sequence

```python
WAVE_LIMITS: tuple[int | None, ...] = (1, 2, 4, 8, None)
```

Only positive bounded values are valid. If a public CLI exposes loops or repository parallelism
beside the wave limit, parse all three with the same positive-integer validator so zero and negative
values cannot create degenerate control flow.

### Checkpoint authority model

```text
selection authority = repository + checkpoint generation + phase + ordered issue IDs
merge authority     = issue + PR + reviewed head SHA + conditional-response merge SHA
history authority   = prior base SHA and all merge SHAs are ancestors of synchronized main
terminal authority  = checkpoint outcome persisted before volatile ledger/cleanup

queues              = reconstruction mechanism, never rollout authority
labels/review prose = workflow signals/audit evidence, never merge-receipt substitutes
```

### Selector matrix

| Stored state | Requested limit | Result |
|-------------|-----------------|--------|
| Absent | omitted | Ordinary unbounded discovery; no checkpoint |
| Absent | `1` | Seal the first wave |
| Active | same as stored phase | Resume exact identifiers |
| Active and complete | next of `2`, `4`, `8` | Verify prior wave, then seal next |
| Wave 8 complete | omitted | Verify and seal final all-eligible wave |
| Final active | omitted | Resume; verify; mark completed |
| Completed | omitted | Audit-only success, no workflow mutation |
| Completed | bounded | Actionable rejection |
| Active | any unexpected selector | Fail before mutation |

### Confidence gates for future rollout validation

1. Focused checkpoint, CLI, pipeline, Git-worker, merge-receipt, and terminal-ordering tests pass.
2. Lint, formatting, and static typing pass for the changed automation surface.
3. Architecture, import-boundary, ADR, and atomic-write guards pass.
4. The complete unit suite passes.
5. CI passes on the implementation PR (satisfied by PR #2687).
6. A real repository rollout completes 1/2/4/8/all and later unbounded runs remain audit-only;
   this remains pending for issue #2453.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #2453 / PR #2687 implementation review and merge | Final head `19e51319`; review corrections covered partial-wave resume and direct-recovery terminalization; CI and required checks passed before conditional merge `3388466e`. [Project-specific integration notes](./automation-issue-waves-durable-merge-checkpoint-rollout.notes.md) |
