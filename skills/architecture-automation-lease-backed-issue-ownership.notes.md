# ProjectHephaestus Issue-Guard Design Notes

## Session Status

- Date: 2026-08-06
- Source: reviewed implementation plan supplied to `/learn`
- Verification: unverified
- No Hephaestus code, tests, live GitHub contract test, or CI run was performed in this session.

These notes preserve ProjectHephaestus-specific integration details while the main skill remains
cross-repository. Re-read the live source before implementation because line numbers and
construction sites can drift.

## Intended Authority Split

- Add `state:in-progress` to the shared label specification.
- Keep it outside `ALL_STATE_LABELS`, `ALL_IMPLEMENTATION_STATE_LABELS`, and `_LABEL_RANK`.
- Existing four plan-state labels and two implementation-review labels remain routing authority.
- `state:plan-blocked` remains operator-owned; release and recovery never remove it.
- Store ownership at `refs/heads/hephaestus/issue-guards/issue-<number>`.

## Guard Service Surface

Proposed module: `hephaestus/automation/issue_guard.py`

```python
@dataclass(frozen=True)
class GuardCredential:
    repository: str
    issue: int
    claim_id: UUID
    run_id: UUID


class IssueGuard:
    def acquire(
        self,
        repository: str,
        issue: int,
        work_stage: str,
    ) -> GuardHandle | None: ...

    def confirm(
        self,
        credential: GuardCredential,
        minimum_valid_for: timedelta,
    ) -> GuardHandle: ...

    def renew(
        self,
        handle: GuardHandle,
        minimum_valid_for: timedelta,
    ) -> GuardHandle: ...

    def release(self, handle: GuardHandle, reason: str) -> None: ...
```

Private timing constants:

```python
_BASE_LEASE = timedelta(hours=4)
_RENEW_BEFORE = timedelta(minutes=30)
_RECOVERY_GRACE = timedelta(minutes=10)
_SHUTDOWN_MARGIN = timedelta(minutes=5)
```

No queue or standalone reviewer CLI should gain timing flags.

## Source Mutation Inventory

Before implementation, refresh this inventory:

```bash
rg -n "skip_epics|ensure_blocked_audit" \
  hephaestus/automation/pipeline/coordinator_sources.py
```

The reviewed plan identified six pre-item mutation sites at then-current lines 128, 150, 165,
356, 488, and 724. Epic and blocked-audit operations need temporary source claims. Ordinary issue
and PR admission transfers the claim to the `WorkItem`. Direct PR admission resolves the linked
issue, claims it, and then re-reads the PR-to-issue association before enqueueing.

## Worker Binding Inventory

Stage-created `GitHubJob` remains an unbound specification with `issue_number`. Add worker-only
`GuardedGitHubJob`. `Coordinator._submit()` confirms the item guard and binds before
`WorkerPool.submit()`.

Refresh these four construction sites before editing:

```bash
rg -n "GitHubJob\(" \
  hephaestus/automation/pipeline/stages/implementation.py \
  hephaestus/automation/pipeline/stages/pr_review_jobs.py \
  hephaestus/automation/pipeline/stages/merge_wait.py
```

The reviewed plan identified one implementation job, two PR-review jobs, and one merge-wait job.
`ReconcilePrReviewRequest` and `RunMergeWaitCycleRequest` also need their missing `issue_number`.

## Module Integration Map

| Area | Intended change |
|------|-----------------|
| `automation/state_labels.py` | Add orthogonal constant and provisioning metadata without adding it to state tuples/rank |
| `automation/pipeline_github_mutations.py` | Provision every `STATE_LABEL_SPECS` entry instead of a second manual list |
| `github/client.py` | Thread a child-only `env` mapping through every `gh_call` retry without changing `os.environ` |
| `automation/github_api/issues.py` | Make standalone issue reads repository-explicit |
| `automation/pipeline/guarded_github.py` | Add a target-bound proxy that delegates reads and confirms before every mutator |
| `automation/pipeline/github_jobs.py` | Add issue targets and unbound-to-bound job seam |
| `automation/pipeline/jobs.py` | Restrict worker union to bound GitHub jobs |
| `automation/pipeline/worker_pool.py` | Reject unbound GitHub jobs and terminate pending/active work on ownership loss |
| `automation/pipeline_github_jobs.py` | Create a fresh raw accessor, validate canonical repository, then wrap it with the guard proxy |
| `automation/pipeline/coordinator*.py` | Own run ID, guard registry, source claims, renewals, dispatch confirmation, terminal release, and ownership-loss exit |
| `automation/plan_reviewer.py` | Pin repository, claim before agent/write, re-read after claim, confirm before every durable call, release in `finally`; dry run stays read-only/no-agent |
| `automation/recover_issue_guard.py` | Add inspect and separately credentialed operator recovery |

## Recovery CLI Contract

```text
hephaestus-recover-issue-guard --repo OWNER/REPO --issue N --inspect

hephaestus-recover-issue-guard --repo OWNER/REPO --issue N --recover \
  --expected-claim UUID --expected-oid SHA --reason TEXT
```

Mutation requirements:

- `HEPHAESTUS_GUARD_RECOVERY_TOKEN` is present.
- It differs from `GH_TOKEN` and `GITHUB_TOKEN`.
- `/user` resolves to an actor in comma-separated `HEPHAESTUS_GUARD_RECOVERY_ACTORS`.
- The lease plus ten-minute grace has expired according to server time.
- Expected claim and OID match exactly.
- `RECOVERING` installs by non-forced update.
- Only `state:in-progress` is removed; plan labels are unchanged.
- Normal automation refuses to start when the recovery secret is present.

## Test Matrix

Create focused suites for:

- Strict records, bootstrap, simultaneous CAS, acquisition/release failure windows, renewal,
  restart observations, expiry, label/ref inconsistency, and plan-label preservation.
- Recovery token isolation, actor allowlisting, claim/OID matching, grace, renewal races, malformed
  records, reasons, and `state:plan-blocked` preservation.
- Every guarded proxy mutator and adversarial target mismatch.
- Two coordinators sharing a fake ref store, source-to-item transfer, queue/timer retention,
  confirmation before dispatch, terminal/failure release, lease loss, shutdown, and all six source
  sites.
- Architecture inventory for mutation surfaces, guarded contexts, worker binding, four job
  construction sites, and package-exported agent workflows.
- Live disposable-repository GitHub behavior for refs, non-force conflicts, exact readback,
  labels, renewal-versus-recovery, and terminal records.

Suggested quality gate from the reviewed plan:

```bash
uv run pytest \
  tests/unit/automation/test_issue_guard.py \
  tests/unit/automation/test_recover_issue_guard.py \
  tests/unit/automation/pipeline/test_guarded_github.py \
  tests/unit/automation/pipeline/test_issue_guard_coordinator.py \
  tests/unit/automation/pipeline/test_issue_guard_architecture.py -q

uv run ruff check \
  hephaestus/automation hephaestus/github \
  tests/unit/automation tests/unit/github tests/integration

uv run mypy hephaestus/automation hephaestus/github
```

Live contract test, only with an explicitly supplied disposable repository:

```bash
HEPHAESTUS_GUARD_TEST_REPO=OWNER/guard-contract \
HEPHAESTUS_GUARD_TEST_ISSUE=1 \
uv run pytest tests/integration/test_issue_guard_github_contract.py \
  -m integration -q
```

## Rollout

Stop old automation versions, provision the label and required Contents/Issues permissions, deploy
the guarded version to every worker, then restart. Mixed-version execution is prohibited because
old workers do not recognize the guard.
