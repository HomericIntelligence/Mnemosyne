---
name: pr-ci-failure-triage-preexisting-vs-introduced
description: "Classify red PR checks as introduced, pre-existing, flaky, environmental, stale-commit, or status-rollup artifacts before fixing or rerunning. Use after rebases/force-pushes, unrelated failures, merge-preview coverage changes, or hosted-only process-launch errors."
category: ci-cd
date: 2026-07-31
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-ci
history: pr-ci-failure-triage-preexisting-vs-introduced.history
tags:
  - ci-failure
  - triage
  - check-runs
  - preexisting
  - concurrency
  - flaky
  - stale-commit
  - merge-preview
  - e2big
---

# PR CI Failure Triage: Pre-Existing vs Introduced

## Overview

Classify each failing check against the PR's current head and current main before changing code.
A PR rollup can show cancelled runs from an old SHA; an unrelated-looking failure can still be
introduced; and main can be genuinely broken. Evidence determines whether to fix in scope, rerun a
known flake, repair main separately, or create an explicit follow-up.

This workflow is verified in CI across the indexed cases. Detailed run links and edge cases are in
[pr-ci-failure-triage-preexisting-vs-introduced.notes.md](pr-ci-failure-triage-preexisting-vs-introduced.notes.md),
and the complete prior version is in
[pr-ci-failure-triage-preexisting-vs-introduced.history](pr-ci-failure-triage-preexisting-vs-introduced.history).

## When to Use

- Required checks are red and scope ownership is unclear.
- A force-push or rerun left cancelled/superseded runs in the PR rollup.
- The failing job appears unrelated to the diff.
- A crash signature looks flaky or infrastructure-specific.
- Coverage measures a synthetic merge tree rather than the feature branch alone.
- A stacked/rebased PR needs fresh checks without a code change.
- Several sanitizers fail identically after a rebase.
- CodeQL and validation fail for different reasons.
- Tests depend on host filesystem auto-detection.
- Hosted Linux raises `E2BIG` before a generated `node -e` harness starts.

## Verified Workflow

### 1. Bind every observation to a SHA

```bash
PR_JSON=$(gh pr view "$PR" --repo "$REPO" --json headRefOid,baseRefOid,url)
PR_HEAD=$(printf '%s' "$PR_JSON" | jq -r .headRefOid)
MAIN_HEAD=$(gh api "repos/$REPO/commits/main" --jq .sha)
printf 'pr=%s main=%s\n' "$PR_HEAD" "$MAIN_HEAD"
```

Do not rely on a cached browser rollup or run from a rebased-out commit. Re-read after any push.
Avoid environment tokens that shadow the authenticated GitHub CLI identity.

### 2. Inspect check runs for exact commits

```bash
gh api "repos/$REPO/commits/$PR_HEAD/check-runs" \
  --jq '.check_runs[] | [.name,.status,.conclusion,.details_url] | @tsv'
gh api "repos/$REPO/commits/$MAIN_HEAD/check-runs" \
  --jq '.check_runs[] | [.name,.status,.conclusion,.details_url] | @tsv'
```

Classify per check name and workflow:

| PR head | Main head | Initial class |
| --- | --- | --- |
| Fails | Passes | PR-introduced or merge interaction |
| Fails identically | Fails | Pre-existing/systemic candidate |
| Cancelled/superseded | Current head has newer run | Rollup artifact |
| New check only on PR | No main run | New-check; inspect policy and merge preview |
| Intermittent signature | Main/PR history mixed | Flake/infrastructure candidate |

“Unrelated diff” is supporting context, not classification evidence.

### 3. Filter cancelled and stale runs

List workflow runs with `head_sha`, event, attempt, status, and conclusion. A concurrency group can
cancel an in-flight rerun when a newer run starts. Only the newest applicable run for the current
head should influence resolution.

Use the check-runs API for authoritative status. `gh pr checks --json` supports a narrow field set;
do not assume it exposes arbitrary run metadata.

### 4. Compare workflow history on main

Inspect several recent main runs for the same workflow. One failed main run can be transient; a
repeated identical failure establishes systemic rot more strongly. Compare logs, runner image,
dependency versions, and failing test IDs.

If the required job evaluates a merge-preview commit, reproduce that tree or use GitHub's merge
commit SHA. A coverage drop can arise from interaction with main even when the branch-alone suite
passes.

### 5. Classify known failure signatures before rerunning

- Compiler/JIT crash or SIGABRT with identical historical flakes: infrastructure candidate; capture
  signature and recurrence first.
- All sanitizer jobs fail on the same unexpected feature: inspect branch history for a stale
  duplicate commit already represented on main.
- CI-only path discovery: replace ambient filesystem probing with explicit deterministic inputs.
- `E2BIG` before Node logs appear: `execve` rejected argument/environment size; Node code never ran.

For generated harnesses, stream code over stdin instead of `node -e <large-script>`:

```python
subprocess.run(
    ["node"],
    input=generated_javascript,
    text=True,
    capture_output=True,
    check=False,
)
```

Test with realistic large payloads on hosted Linux; local `ARG_MAX` and environment size differ.

### 6. Inspect branch content for stale duplicate commits

```bash
git log --oneline --decorate origin/main..HEAD
git diff --stat origin/main...HEAD
git cherry -v origin/main HEAD
```

If a stale commit duplicates a fix already on main, rebuild the branch from current main with only
the real payload. Do not amend an arbitrary tip when the unwanted commit is lower in history.

### 7. Resolve according to evidence

- PR-introduced: fix within scope and add regression coverage.
- Merge interaction: rebase/update, reproduce merge preview, and fix the interaction.
- Confirmed flake: rerun only failed jobs after recording the signature.
- Pre-existing required failure: fix main separately when practical; otherwise use only an
  explicitly authorized governance path and file a linked tracking issue.
- Rollup artifact: no code change; wait for/read the current-head run.
- New-check failure: fix the check or product contract; do not compare it to a nonexistent main run.

After any fix/rebase, repeat SHA and check-run binding. Surface classification and evidence in the
PR, not only stderr or a private note.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | Trust `PREEXISTING_CI_NOISE` label | Prior sweeps found many labels wrong | Query exact PR/main check runs |
| 2 | Treat unrelated diff as proof | Dependency, merge, and policy interactions cross file scope | Use SHA-bound execution evidence |
| 3 | Count cancelled old-SHA runs as failures | Force-push/concurrency superseded them | Filter by current head and newest applicable run |
| 4 | Rerun before classifying | New run can hide signature or cancel another run | Capture logs/history first |
| 5 | Assume one failed main run proves rot | It may be a transient flake | Inspect repeated main history |
| 6 | Amend tip to remove stale lower commit | Wrong commit remains in branch | Rebuild/cherry-pick real payload onto current main |
| 7 | Debug generated Node program after `E2BIG` | Kernel rejected argv before Node started | Send harness through stdin |
| 8 | Test CI path auto-detection only locally | Host layout differs | Inject explicit paths and test missing/ambiguous cases |

## Results & Parameters

- Authoritative identity: exact PR head and current main head SHAs.
- Primary status source: check-runs API per commit; workflow history supplies recurrence evidence.
- Rerun policy: failed jobs only, and only after a flake classification is recorded.
- Generated harness transport: stdin for large scripts; avoid platform-dependent argv budgets.
- Final gate: current-head required checks, not cancelled or stale runs.
- Resolution record: check name, PR/main result, log signature, classification, action, and linked
  issue/repair when outside scope.

## Evidence Boundary

The decision method is CI-verified across the indexed GitHub cases. Exact administrative options,
required-check policy, runner limits, and merge-preview behavior are repository-specific; inspect
live rules and current runs before acting.
