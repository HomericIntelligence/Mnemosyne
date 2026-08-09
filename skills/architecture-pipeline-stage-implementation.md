---
name: architecture-pipeline-stage-implementation
description: "Implement queue-based pipeline stages and worker-result boundaries against the landed state-machine contract. Use when: (1) returning Continue, JobRequest, or StageOutcome; (2) handling on_job_done without mutating coordinator-owned state; (3) distinguishing RETRY timer-parks from job submission; (4) ordering durable writes before queue advancement; (5) translating a helper's expected negative sentinel into JobResult; (6) a failed JobResult has error=None and downstream warnings render None; (7) checking whether a proposed stage still exists in the active routing table."
category: architecture
date: 2026-07-20
version: "2.0.0"
user-invocable: false
verification: verified-local
history: architecture-pipeline-stage-implementation.history
tags:
  - pipeline
  - stage
  - state-machine
  - coordinator
  - worker-pool
  - job-result
  - error-contract
  - failure-observability
  - sentinel-translation
  - durable-mutations
  - timer-park
  - rebase-conflicts
---

# Queue Pipeline Stages and Worker Result Contracts

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-20 |
| **Objective** | Implement stages against the landed queue-pipeline API and make worker failures observable by translating expected negative helper returns into complete `JobResult` values. |
| **Outcome** | The canonical stage skill now matches the current API and adds the invariant that every non-interrupted failure has an actionable `error`. The ProjectHephaestus mechanical-rebase mapping was exercised locally for clean and conflict returns. |
| **Verification** | **verified-local** — both parameterized worker-pool cases passed with `--no-cov`; Ruff passed for the implementation and test files. CI validation is pending. |
| **History** | [changelog](./architecture-pipeline-stage-implementation.history) |

## When to Use

- Implementing or reviewing a queue stage with `on_enter`, `step`, and `on_job_done`.
- Choosing among `Continue`, `JobRequest`, and `StageOutcome`.
- Adding a worker operation whose helper can return an expected negative sentinel such as `False`, an empty optional, or a domain status instead of raising.
- Debugging logs such as `operation failed: None` when the result has `ok=False`.
- Deciding whether failure text belongs in a stage, a coordinator, or the worker boundary.
- Adding regression coverage for both success and expected-negative result metadata.
- Planning work against an architecture diagram that may mention a removed stage. Read `StageName` and the routing table first; do not create tests for a stage that no longer exists.

## Verified Workflow

### Quick Reference

```bash
# Confirm the landed pipeline vocabulary and active stages.
rg -n "class StageName|class Continue|class JobRequest|class JobResult" \
  hephaestus/automation/pipeline

# Audit incomplete non-interrupted failure results.
rg -n "JobResult\(.*ok=False|JobResult\(" \
  hephaestus/automation/pipeline/worker_pool.py

# Focused verification without triggering repository-wide coverage fail-under.
uv run pytest --no-cov \
  tests/unit/automation/pipeline/test_worker_pool.py::TestGitOps::test_rebase_dispatch_propagates_result -v

uv run ruff check \
  hephaestus/automation/pipeline/worker_pool.py \
  tests/unit/automation/pipeline/test_worker_pool.py
```

### Detailed Steps

#### 1. Read the landed contract before designing the stage

The current ProjectHephaestus pipeline has these active stages:

```text
repo → planning → plan_review → implementation → pr_review → merge_wait → finished
```

CI/CD intentionally has no independent pipeline stage. Normal review may collect CI/CD
evidence, but CI/CD does not authorize approval and the loop does not change it. Treat
issue bodies, plans, and old architecture examples as hypotheses until `StageName`,
`ROUTES`, and the stage base types confirm them.

The landed result vocabulary is:

```python
@dataclass(frozen=True)
class Continue:
    next_state: str

@dataclass(frozen=True)
class JobRequest:
    job: AgentJob | BuildTestJob | GitJob
    on_done_state: str

@dataclass(frozen=True)
class JobResult:
    ok: bool
    value: Any = None
    error: str | None = None
    interrupted: bool = False

@dataclass(frozen=True)
class StageOutcome:
    disposition: Disposition
    note: str = ""
```

Use the actual fields: `next_state`, `on_done_state`, `ok`, and `note`.
`Disposition.FINISH_PASS` is the successful terminal disposition. Names such as
`next_stage`, `job_result.success`, `reason`, and `FINISH_OK` are stale.

#### 2. Keep state ownership in the coordinator

A stage returns a transition; it does not write `item.state` directly:

```python
def step(self, item: WorkItem, ctx: StageContext) -> StepResult:
    if item.state == "READY":
        return Continue("SUBMIT")

    if item.state == "SUBMIT":
        return JobRequest(
            job=BuildTestJob(
                repo=item.repo,
                cwd=ctx.paths.worktree(item),
                argv=("uv", "run", "pytest", "--no-cov", "tests/unit"),
                timeout_s=600,
            ),
            on_done_state="EVALUATE",
        )

    if item.state == "EVALUATE":
        if item.payload["build_ok"]:
            return StageOutcome(Disposition.FINISH_PASS, note="build passed")
        return StageOutcome(Disposition.RETRY, note="build failed")

    return StageOutcome(Disposition.FINISH_FAIL, note=f"unknown state {item.state}")
```

`on_job_done` receives the result while the item remains at the submitting wait state.
It stores facts in `item.payload` and returns `None`; the coordinator then advances to
`on_done_state`.

```python
def on_job_done(
    self,
    item: WorkItem,
    result: JobResult,
    ctx: StageContext,
) -> None:
    item.payload["build_ok"] = result.ok
    item.payload["build_error"] = result.error
```

#### 3. Enforce the worker-result failure invariant

For any completed, non-interrupted job:

```text
result.ok is False  ⇒  result.error is a non-empty actionable string
```

`value`, `stdout_tail`, and `stderr_tail` remain useful structured evidence, but
none substitutes for the short summary downstream warnings interpolate. Interrupted
results are a separate resumability channel and may be excluded from ordinary failure
routing.

Audit the invariant where each worker operation constructs `JobResult`. The worker
boundary knows which helper return means what; translating later in every stage duplicates
domain knowledge and still leaves other consumers exposed to `None`.

#### 4. Separate expected-negative sentinels from raised failures

First read the helper contract.

- If the helper raises on timeout, fetch failure, or non-zero subprocess exit, preserve the
  worker's existing exception translation and output tails.
- If the helper returns a sentinel for an expected branch, translate that sentinel at the
  operation dispatch boundary.

Mechanical rebase is the concrete pattern:

```python
# BEFORE: False becomes a failed result with no explanation.
result = git_utils.rebase_worktree_onto(**job.kwargs, timeout=job.timeout_s)
return JobResult(ok=result, value=result)

# AFTER: only the expected conflict sentinel gets the deterministic summary.
result = git_utils.rebase_worktree_onto(**job.kwargs, timeout=job.timeout_s)
error = None if result else "mechanical rebase hit conflicts; aborted"
return JobResult(ok=result, value=result, error=error)
```

This is intentionally narrow. `rebase_worktree_onto()` documents `False` as “conflicts
encountered and rebase aborted.” Fetch and other subprocess failures raise, so their
existing timeout, return-code, stdout-tail, and stderr-tail handling remains unchanged.

#### 5. Test the result contract at the dispatch boundary

Extend the existing operation-dispatch test. Cover success and the expected-negative
branch in one parameterized contract:

```python
@pytest.mark.parametrize(
    ("rebase_clean", "expected_error"),
    [
        (True, None),
        (False, "mechanical rebase hit conflicts; aborted"),
    ],
)
def test_rebase_dispatch_propagates_result(
    self,
    pool: WorkerPool,
    completion_q: CompletionQueue,
    rebase_clean: bool,
    expected_error: str | None,
) -> None:
    job = GitJob(
        repo="test/repo",
        op="rebase",
        timeout_s=60,
        kwargs={"cwd": Path("/tmp/wt"), "base_branch": "main"},
    )
    with patch(
        "hephaestus.automation.git_utils.rebase_worktree_onto",
        return_value=rebase_clean,
    ) as mock_rebase:
        pool.submit(job, StageName.MERGE_WAIT)
        _, result = completion_q.get(timeout=10)

    mock_rebase.assert_called_once_with(
        cwd=Path("/tmp/wt"),
        base_branch="main",
        timeout=60,
    )
    assert result.ok is rebase_clean
    assert result.value is rebase_clean
    assert result.error == expected_error
```

A stage-specific test is the wrong seam for this defect. The incomplete result originates
in the generic worker operation and can affect every consumer.

#### 6. Preserve timer and durability semantics

- Return `StageOutcome(Disposition.RETRY, note=...)` to timer-park the item. If a delay
  is needed, write `item.payload["retry_delay_s"]` before returning; stages never sleep.
- Return `JobRequest` only with a real immutable job object. Never use
  `JobRequest(None, ...)`.
- Perform durable GitHub mutations immediately before the transition that queues or
  advances the item. If a durable write fails, return a failure outcome; do not swallow
  the exception and advance.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Propagate only the helper boolean | `JobResult(ok=result, value=result)` | The conflict sentinel produced `ok=False` with `error=None`; downstream warnings rendered `mechanical rebase failed (non-fatal): None`. | A negative sentinel needs domain translation at the worker boundary. |
| Rely on exception handlers for every rebase failure | Kept only timeout and `CalledProcessError` translation | Mechanical conflicts are intentionally caught, aborted, and returned as `False`; no exception reaches those handlers. | Read the helper's return and raise contract before choosing the translation path. |
| Add a test to a CI pipeline stage | Targeted a stage mentioned in old design material | The current routing table intentionally has no CI/CD stage. | Confirm `StageName` and `ROUTES`; test the surviving generic worker boundary. |
| Run one focused node with repository coverage enabled | Used the ordinary pytest command unchanged | Both cases passed, but pytest exited nonzero because one node reported 7.33% repository coverage below the 83% global gate. | Use `--no-cov` for the focused contract, then rely on the full suite or CI for the repository-wide gate. |
| Translate the same failure in each stage | Each consumer invented its own fallback text | Duplicates worker-operation knowledge and leaves logs from other consumers incomplete. | Construct a complete `JobResult` once, where the helper is dispatched. |
| Use stale API examples | Used `job_result.success`, `Continue(next_stage=...)`, `StageOutcome(reason=...)`, and `FINISH_OK`. | These names do not match the landed dataclasses and enum. | Re-read the base types and routing enum before copying an old architecture example. |
| Mutate `item.state` in a stage | Assigned the next state directly | The coordinator is the sole state writer and can clobber stage-owned assignments. | Return transitions and store completed-job facts in `item.payload`. |
| Use `JobRequest(None)` as a timer | Submitted a null job to request a callback | The coordinator expects a real job object and will fail when handling the request. | Use `RETRY` for timer-parking and `JobRequest` only for actual work. |

## Results & Parameters

The verified mechanical-rebase result matrix is:

| Helper outcome | `JobResult.ok` | `JobResult.value` | `JobResult.error` |
|---------------|----------------|-------------------|-------------------|
| Clean rebase (`True`) | `True` | `True` | `None` |
| Conflict aborted (`False`) | `False` | `False` | `mechanical rebase hit conflicts; aborted` |
| Timeout or subprocess failure | `False` | Existing behavior | Existing `timeout` / `rc=N` translation plus output tails |

Local verification on 2026-07-20:

```text
uv run pytest --no-cov ...::test_rebase_dispatch_propagates_result -v
2 passed in 0.16s

uv run ruff check hephaestus/automation/pipeline/worker_pool.py \
  tests/unit/automation/pipeline/test_worker_pool.py
All checks passed!
```

The same focused pytest command without `--no-cov` executed both assertions successfully
but exited nonzero on the repository's global 83% coverage threshold. Full-suite and CI
validation of the proposed Hephaestus change remain pending.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Mechanical rebase conflict result contract | Source contract inspected; temporary implementation and parameterized regression test executed locally, then the Hephaestus checkout was restored clean. |
| ProjectHephaestus | Original queue-pipeline stage implementation | Prior v1.0.0 recorded 479 passing pipeline unit tests; see history for the archived version and its historical CI claim. |
