---
name: architecture-automation-lease-backed-issue-ownership
description: "Design lease-backed, target-bound issue ownership for concurrent GitHub automation. Use when: (1) multiple automation runs can select the same issue, (2) visible labels must not become workflow authority, (3) stale ownership needs explicit operator-only recovery, (4) coordinator and worker mutation paths must carry the same claim."
category: architecture
date: 2026-08-06
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - github
  - automation
  - concurrency
  - issue-ownership
  - lease
  - git-ref
  - compare-and-swap
  - target-binding
  - stale-recovery
  - worker-authorization
---

# Architecture: Lease-Backed Issue Ownership for Concurrent Automation

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-06 |
| **Objective** | Prevent concurrent automation runs from dispatching agents or mutating issue, branch, journal, or PR state for the same issue while preserving the existing workflow-state authority. |
| **Outcome** | A reviewed design was produced: use a per-issue Git ref as lock authority, an orthogonal label as a visible contention signal, target-bound credentials throughout coordinator and worker paths, owner-only release, and separately authorized stale recovery. No implementation or end-to-end test was executed in this session. |
| **Verification** | `unverified` — design and test matrix only; implementation, local tests, live GitHub contract tests, and CI are pending. |

## When to Use

- Two schedulers, queue coordinators, or standalone automation commands can discover the same GitHub issue concurrently.
- Issue or PR work begins before a durable item exists, so pre-admission mutation sites also need ownership.
- Existing `state:*` labels authorize workflow routing and a new ownership signal must not accidentally become another routing verdict.
- A coordinator dispatches work to workers and the worker must receive constructible, target-specific proof of ownership rather than relying on ambient process state.
- Long-running jobs need renewable leases, ownership-loss shutdown, and restart-safe observations.
- Stale locks must be recoverable without allowing ordinary automation to steal an expired or malformed claim.
- Pull-request mutations must remain bound to the issue currently linked to the PR.

## Verified Workflow

> **Warning:** This is a proposed workflow. It has not been validated end-to-end. Treat it as a hypothesis until implementation tests, a disposable-repository GitHub contract test, and CI all pass.

### Quick Reference

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Literal
from uuid import UUID


class GuardPhase(StrEnum):
    ACQUIRING = "acquiring"
    ACTIVE = "active"
    RELEASING = "releasing"
    RELEASED = "released"
    RECOVERING = "recovering"
    RECOVERED = "recovered"


@dataclass(frozen=True)
class GuardRecord:
    version: Literal[1]
    repository: str
    issue: int
    claim_id: UUID
    run_id: UUID
    actor: str
    phase: GuardPhase
    work_stage: str
    lease_expires_at: datetime
    predecessor_oid: str | None
    reason: str


@dataclass(frozen=True)
class GuardCredential:
    repository: str
    issue: int
    claim_id: UUID
    run_id: UUID


BASE_LEASE = timedelta(hours=4)
RENEW_BEFORE = timedelta(minutes=30)
RECOVERY_GRACE = timedelta(minutes=10)
SHUTDOWN_MARGIN = timedelta(minutes=5)
```

```text
acquire:
  read labels + ref -> install ACQUIRING child with non-forced CAS
  -> confirm exact OID/record -> add guard label -> confirm label
  -> install ACTIVE child -> confirm record + target + lease + label

release:
  confirm owner-held ACTIVE/ACQUIRING + label + unexpired lease
  -> install RELEASING child -> confirm -> remove only guard label
  -> confirm label absent and workflow labels unchanged
  -> install RELEASED child -> confirm

recover:
  separate credential + authenticated actor allowlist
  + expired lease/grace + expected claim + expected OID
  -> install RECOVERING child with non-forced CAS
  -> remove only guard label -> preserve workflow labels
  -> install RECOVERED child -> confirm
```

### 1. Separate ownership from workflow authority

Keep the visible ownership label out of every exclusive routing tuple, transition rank, and
workflow-state reducer. The label answers only, "does some run visibly claim this issue?"
The Git ref record answers, "which run owns it?" Existing plan and review labels continue to
authorize stages.

```python
STATE_IN_PROGRESS = "state:in-progress"

# Provision it from the shared label specification, but never add it here:
assert STATE_IN_PROGRESS not in ALL_STATE_LABELS
assert STATE_IN_PROGRESS not in ALL_IMPLEMENTATION_STATE_LABELS
assert STATE_IN_PROGRESS not in LABEL_RANK
```

Do not let guard release or recovery remove, replace, or infer any workflow-state label. An
operator-owned blocked label is especially important: ownership cleanup must not silently unblock
work.

### 2. Use a per-issue Git ref as the durable CAS object

Allocate one ref per issue, for example:

```text
refs/heads/<automation>/issue-guards/issue-<number>
```

Each transition creates a no-op child commit with the predecessor's unchanged tree. Put a strict,
canonical, versioned JSON record in the commit message. Install the child with a non-forced ref
update. Two contenders may create children of the same predecessor, but only one child can
fast-forward the ref first; the loser must defer.

Bootstrap a missing ref from a validated default-branch commit and its unchanged tree. Fail closed
before any durable mutation when the repository is empty, default-branch metadata is invalid,
record JSON is malformed or non-canonical, the response lacks server time, or required Contents
or Issues permissions are unavailable.

Use GitHub's response `Date` header for lease calculations so clients with skewed clocks do not
disagree about expiry. Parse timestamps as timezone-aware UTC and reject ambiguous or unexpected
fields rather than ignoring them.

### 3. Acquire with compare, install, and exact readback

An acquisition should use this order:

1. Read live issue labels. If the visible guard label is present, defer without mutation.
2. Read and strictly validate the guard ref. Defer for operator recovery on malformed,
   nonterminal, expired, or label/ref-inconsistent state. Ordinary automation never steals it.
3. Create a new claim/run identity and an `ACQUIRING` child whose lease uses server time.
4. Install the child with create-ref or a non-forced update, then re-read and confirm its exact OID
   and record.
5. Add only the visible guard label, then re-read labels.
6. Install an `ACTIVE` child with a non-forced update.
7. Re-read and confirm OID, repository, issue, claim ID, run ID, phase, lease, and label before
   returning a handle.

Every failure window matters. If the ref advances but label application fails, or the label applies
but `ACTIVE` installation fails, do not pretend the issue is free. Attempt only owner-held rollback;
otherwise leave auditable state for recovery.

### 4. Claim before every pre-item mutation and transfer ownership

Search for mutation chokepoints before an ordinary queue item exists. This includes epic skipping,
blocked-audit writes, direct-issue seeding, and direct-PR admission. Wrap each site in a temporary
source claim:

```python
with claim_source_issue(repository, issue, "source-admission") as claim:
    if claim is None:
        return DEFERRED

    github = claim.github
    # Any read-dependent mutation uses this target-bound accessor.
    entry = seed_or_classify(issue, github)
    item = admit(entry)
    claim.transfer_to(item)
```

The temporary claim releases in `finally` on exclusion, overlap deferral, classification failure,
or failed queue insertion. On successful admission, the exact handle transfers to the item. Retain
it through queues, timer parking, stage handoffs, in-flight jobs, and the terminal sink.

Acquire source claims only while the existing global work window has capacity. Count temporary
and admitted claims together:

```python
active_item_guards + temporary_source_guards <= max(
    1,
    parallel_repositories * max_workers,
)
```

For direct PR admission, resolve the linked issue, acquire that issue, then re-read the PR-to-issue
association through the guarded accessor before enqueueing.

### 5. Bind all mutation authority to the exact target

A credential is valid only for one normalized `OWNER/REPO`, one issue, one claim, and one run.
Reject repository, issue, claim, run, phase, label, or lease mismatch before mutation.

Wrap every issue-bearing stage accessor in a target-bound proxy. Delegate reads, but before each
mutator:

1. Reconfirm the credential against the ref and lease.
2. Verify the method target equals the credential issue.
3. Reject attempts to add, edit, or remove the guard label; only the guard service owns it.
4. Reject repository-wide methods such as label provisioning on issue-bound accessors.
5. Require batched methods to contain exactly the credential's single issue.
6. Before a PR mutation, freshly resolve the PR's linked issue and require equality.
7. For PR creation, confirm the issue before creation and confirm the returned PR links back to
   that issue before returning.

Keep repository-wide provisioning available only through a repository-stage raw accessor.

### 6. Make the coordinator-to-worker binding seam explicit

Stage code should construct an unbound GitHub job specification with an explicit issue target.
The coordinator confirms the item's guard immediately before dispatch and binds the credential.
Workers accept only the bound envelope.

```python
@dataclass(frozen=True)
class GitHubJob:
    repository_name: str
    issue_number: int
    request: GitHubRequest

    def __post_init__(self) -> None:
        if request_issue(self.request) != self.issue_number:
            raise ValueError("request target differs from job issue")


@dataclass(frozen=True)
class GuardedGitHubJob:
    operation: GitHubJob
    guard: GuardCredential

    @classmethod
    def bind(cls, operation: GitHubJob, guard: GuardCredential, org: str):
        if guard.repository != f"{org}/{operation.repository_name}":
            raise ValueError("guard repository differs from job repository")
        if guard.issue != operation.issue_number:
            raise ValueError("guard issue differs from job issue")
        return cls(operation=operation, guard=guard)
```

The worker creates a fresh raw repository accessor, validates the canonical repository, wraps it
with the target-bound proxy, and confirms again before each GitHub mutation. Reconfirm item
ownership before dispatching agent, Git, build/test, and GitHub jobs, not only GitHub jobs: all can
produce issue-scoped side effects or consume exclusive work.

### 7. Renew for the full dispatch horizon and fail closed on lease loss

Use a private timing policy unless operators have a demonstrated need to tune it. Before dispatch,
renew sufficiently to cover the larger of the base lease and the job's timeout plus recovery and
shutdown margins:

```python
minimum_valid_for = max(
    BASE_LEASE,
    job.timeout + RECOVERY_GRACE + SHUTDOWN_MARGIN,
)
```

Perform renewal checks in the coordinator's existing event loop. If confirm or renewal loses the
claim, mark the run failed and stop new dispatch. Shut down the worker pool and use the process
registry to terminate active subprocesses before considering any guard release. Release only
handles whose work termination was acknowledged; otherwise leave evidence for recovery.

At terminal completion, release the guard before returning the global work permit. On graceful
shutdown or handled failure, stop workers first, then release only owner-held live claims.

### 8. Release only an owner-held, unexpired claim

Release is a state transition, not label cleanup:

1. Confirm the current `ACTIVE` record, or an owner-held `ACQUIRING` rollback case, plus repository,
   issue, claim, run, unexpired lease, and expected label state.
2. Snapshot the workflow-state labels.
3. Install and confirm a `RELEASING` child by non-forced update.
4. Remove only the visible ownership label.
5. Confirm the guard label is absent and the workflow-state snapshot is unchanged.
6. Install and confirm `RELEASED`.

A conflict, expired lease, or failed readback stops release. Never clear a label merely because a
local `finally` block ran: the local process may no longer own the ref.

### 9. Isolate stale recovery from normal automation

Provide inspect and recover modes. Inspection is read-only. Recovery requires all of:

- A dedicated recovery token passed only to child GitHub calls, never by mutating global process
  environment.
- Rejection when the recovery token equals the normal automation token.
- An authenticated `/user` identity present in an explicit operator allowlist.
- A nonempty audit reason.
- Current server time after `lease_expires_at + recovery_grace`.
- Exact expected claim ID and ref OID captured during inspection.
- A non-forced `RECOVERING` transition, so a concurrent owner renewal changes the OID and wins.

Normal automation should refuse to start when the recovery secret is present. This enforces a
separate operator execution environment instead of treating recovery as a hidden automation mode.
After winning the CAS, remove only the guard label, prove workflow labels are unchanged, and
install `RECOVERED`.

### 10. Roll out only during quiescence

Mixed-version execution is unsafe because old workers do not recognize the guard. Stop old
automation, provision the ownership label and Contents/Issues permissions, deploy the guarded
version everywhere, and only then restart. Record this as an operational requirement, not a soft
recommendation.

### 11. Freeze the architecture with adversarial tests

Required test groups:

- Strict canonical record validation, default-branch bootstrap, create/update conflicts, exact
  readbacks, and all acquisition/release failure windows.
- Simultaneous contenders against one fake ref store, proving a single winner.
- Pre-item mutation inventory, source-claim transfer, timer/queue retention, dispatch confirmation,
  terminal/failure release ordering, lease loss, and shutdown.
- Every proxy mutator plus adversarial repository, issue, credential, guard-label, batch-target,
  and PR-link mismatches.
- Unbound-to-bound job construction and worker rejection of unbound GitHub work.
- Standalone agent entry points: live-guard deferral, fresh post-claim reads, no-agent dry run,
  reconfirmation before writes, and release in `finally`.
- Separate recovery credential, actor allowlist, expiry/grace, expected claim/OID, renewal race,
  malformed records, audit reason, and blocked-label preservation.
- A disposable-repository integration test for GitHub create-ref, non-force contention, response
  time, label application/removal, renewal-versus-recovery CAS, and terminal records.

Prefer AST or source-inventory tests for architecture surfaces, but pair them with behavioral
tests. A static inventory proves coverage of known call sites; it does not prove the proxy actually
reconfirms ownership.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Treat the visible label as the lock | Used `state:in-progress` presence as ownership authority | Label updates do not identify an owner, encode a lease, or provide a strong compare-and-swap transition; routing code may also accidentally treat it as a verdict | Keep the label orthogonal and visible, with a Git ref record as the ownership authority |
| Guard only admitted work items | Acquired after queue admission while pre-item skip, audit, or classification paths could already mutate GitHub state | Concurrent runs could race before a durable item or handle existed | Inventory and guard every pre-item mutation, then transfer the temporary claim to the admitted item |
| Make worker credentials implicit | Added a guard requirement to the worker union without a constructible envelope or coordinator binding point | Stage-created jobs had no credential yet, while workers required one; the type contract could not be satisfied | Keep stage jobs unbound, bind immediately before submit, and let workers accept only the explicit bound envelope |
| Confirm only claim identity | Checked claim/run but not canonical repository, issue, request target, or fresh PR linkage | A valid claim could authorize mutation of the wrong repository, issue, batch, or newly relinked PR | Bind authority to exact targets and re-resolve PR-to-issue association immediately before mutation |
| Add public lease timing flags | Exposed base lease, renewal, grace, and shutdown timing on every CLI | This enlarged the public configuration surface before operators had a real tuning requirement | Start with fixed private policy and add flags only after evidence demonstrates a need |
| Let ordinary automation recover expired claims | Automatically stole a malformed or expired record during acquisition | Clock skew, partial release, delayed work, or a concurrent renewal could make the steal unsafe and unauditable | Defer to an explicit operator-only recovery path with grace, exact claim/OID CAS, allowlisting, and a separate token |
| Remove labels in a generic `finally` | Cleared the visible label whenever local work ended | The lease may have expired or the ref may have advanced, so the local process might no longer be the owner | Release only after exact owner/lease/ref confirmation; otherwise preserve evidence for recovery |
| Confirm only at coordinator dispatch | Trusted the coordinator's pre-submit check for all subsequent worker mutations | A lease can expire or be replaced while work is queued or running | Confirm at dispatch and again inside a fresh target-bound worker proxy before each durable mutation |
| Recover by force-updating the ref | Used a forced update to clear stale state | A live owner can renew concurrently and be overwritten | Recovery must use expected OID plus non-forced CAS; a renewal changes the OID and defeats recovery |
| Deploy incrementally | Ran guarded and unguarded automation versions together | Old workers can ignore the new label/ref contract and mutate an issue owned by a guarded run | Require rollout quiescence and deploy the guard to every worker before restart |

## Results & Parameters

### Fixed timing policy

| Parameter | Proposed value | Purpose |
|-----------|----------------|---------|
| Base lease | 4 hours | Covers ordinary planning, implementation, and review work without frequent churn |
| Renew-before window | 30 minutes | Gives the coordinator time to renew before expiry |
| Recovery grace | 10 minutes | Prevents immediate recovery at the lease boundary |
| Shutdown margin | 5 minutes | Reserves time to stop workers and descendants before release |

These values are design inputs, not measured results. Keep them private until production evidence
supports a public tuning surface.

### Core invariants

```text
ownership_authority = exact Git ref OID + strict GuardRecord
visibility_signal    = orthogonal issue label
routing_authority    = existing workflow-state labels only

credential.repository == canonical job repository
credential.issue      == item issue == job issue == request issue == mutator issue

active_item_guards + temporary_source_guards
    <= max(1, parallel_repositories * max_workers)

release_order = stop/acknowledge work -> owner confirmation -> guard release -> permit release
```

### Recovery interface shape

```text
<tool> --repo OWNER/REPO --issue N --inspect

<tool> --repo OWNER/REPO --issue N --recover \
  --expected-claim UUID \
  --expected-oid SHA \
  --reason TEXT
```

Recommended environment separation:

```text
AUTOMATION_TOKEN=<normal token>
GUARD_RECOVERY_TOKEN=<distinct operator token>
GUARD_RECOVERY_ACTORS=alice,bob
```

The recovery process passes a child-only environment to GitHub calls and must ensure secrets are
absent from logs and exception text.

### Confidence gates before upgrading verification

1. Focused unit and architecture suites pass locally.
2. Lint and static typing pass for guard, coordinator, worker, proxy, and recovery modules.
3. A disposable-repository integration test observes GitHub's create-ref and non-force conflict
   behavior, response `Date` header, label transitions, and recovery-versus-renewal race.
4. Full CI passes.
5. A quiescent rollout proves live-guard deferral and owner-only cleanup in an automation run.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Reviewed issue-guard implementation plan; no code executed | [Project-specific integration notes](./architecture-automation-lease-backed-issue-ownership.notes.md) |
