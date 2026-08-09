# ProjectHephaestus PR #2206 / Issue #2140 Session Notes

## Status

These notes capture a reviewed implementation plan. The rebuild was not executed
in this session, so every command and expected result below remains **unverified**.

## Objective

Rebuild PR #2206 from current `main` so its diff contains only issue #2140's
legacy-pipeline compatibility retirement and containment changes. Exclude the
duplicated issue #2196 Terra model-selection commit, preserve valid current
pipeline semantics, and require a fresh strict-review GO for the rewritten head.

## Scope Proof

The positive allowlist contains exactly these ten paths:

```text
docs/architecture.md
hephaestus/automation/pipeline/seeding.py
hephaestus/automation/pipeline/stages/merge_wait.py
hephaestus/automation/pipeline/stages/pr_review.py
tests/unit/automation/pipeline/test_coordinator_shutdown.py
tests/unit/automation/pipeline/test_seeding.py
tests/unit/automation/pipeline/stages/test_stage_finish_state_names.py
tests/unit/automation/pipeline/stages/test_stage_pr_review.py
tests/unit/automation/pipeline/stages/test_stage_repo.py
tests/unit/docs/test_pipeline_compatibility_retirement.py
```

The negative denylist names issue #2196's Terra/model-selection surface:

```text
hephaestus/agents/runtime.py
hephaestus/automation/loop_runner.py
tests/unit/agents/test_runtime.py
tests/unit/automation/test_automation_parsers.py
```

Run both checks. The allowlist rejects unexpected files; the denylist makes the
known contamination surface explicit.

```bash
comm -23 \
  <(git diff --name-only origin/main...HEAD | sort) \
  <(printf '%s\n' \
    docs/architecture.md \
    hephaestus/automation/pipeline/seeding.py \
    hephaestus/automation/pipeline/stages/merge_wait.py \
    hephaestus/automation/pipeline/stages/pr_review.py \
    tests/unit/automation/pipeline/test_coordinator_shutdown.py \
    tests/unit/automation/pipeline/test_seeding.py \
    tests/unit/automation/pipeline/stages/test_stage_finish_state_names.py \
    tests/unit/automation/pipeline/stages/test_stage_pr_review.py \
    tests/unit/automation/pipeline/stages/test_stage_repo.py \
    tests/unit/docs/test_pipeline_compatibility_retirement.py | sort) \
  | (! read -r unexpected)

git diff --exit-code origin/main...HEAD -- \
  hephaestus/agents/runtime.py \
  hephaestus/automation/loop_runner.py \
  tests/unit/agents/test_runtime.py \
  tests/unit/automation/test_automation_parsers.py
```

## Semantic Invariants

- A legacy issue-level `state:implementation-go` on an open PR emits the named
  `legacy_issue_impl_go_fallback` warning and routes to current `PR_REVIEW`.
- A PR-level implementation-GO remains authoritative and routes to `MERGE_WAIT`.
- An implementation-NOGO never emits the legacy fallback warning.
- Deleted `CI`, follow-up, or finish mini-states do not return.
- `already_implementation_go_pr` and `not_implementation_go` remain contained
  until observable removal gates are satisfied; they are not deleted early.
- Restart reconstruction and normal seeding choose the same stage.

## Verification Commands

```bash
uv run pytest \
  tests/unit/automation/pipeline \
  tests/unit/docs/test_pipeline_compatibility_retirement.py \
  -q

uv run ruff check \
  hephaestus/automation/pipeline \
  tests/unit/automation/pipeline \
  tests/unit/docs/test_pipeline_compatibility_retirement.py

git diff --check origin/main...HEAD
```

After the isolated head is pushed, run the repository's strict reviewer. Accept
only a verbatim, unqualified GO for that exact SHA with zero unresolved blocking
threads. CI alone is not approval, and any later commit invalidates the review.

## Rewrite and Rollback Boundary

Before rebuilding, record the live remote PR-head SHA and create a local-only
backup ref. Rewrite the remote branch only with an explicit expected-SHA lease.
If rollback is required, lease the restore against the rejected rebuilt SHA.

```bash
OLD_SHA=$(git ls-remote --heads origin refs/heads/2140-auto-impl | awk '{print $1}')
git branch backup/2206-pre-isolation "$OLD_SHA"

git push --force-with-lease="refs/heads/2140-auto-impl:$OLD_SHA" origin \
  HEAD:refs/heads/2140-auto-impl

REBUILT_SHA=$(git rev-parse HEAD)
git push --force-with-lease="refs/heads/2140-auto-impl:$REBUILT_SHA" origin \
  backup/2206-pre-isolation:refs/heads/2140-auto-impl
```

The backup ref stays local. Never rewrite `main`.
