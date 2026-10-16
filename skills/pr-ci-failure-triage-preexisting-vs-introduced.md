---
name: pr-ci-failure-triage-preexisting-vs-introduced
description: "Classify red PR checks as introduced, pre-existing, flaky, environmental, stale-commit, or status-rollup artifacts before fixing or rerunning. Use after rebases/force-pushes, unrelated failures, merge-preview coverage changes, or hosted-only process-launch errors. Also use when the required check is a fan-in gate reported by a ruleset, when the failing symbol on the base was deliberately removed, when a base update turns a green branch red without a textual conflict, when grouped or sharded logs hide individual failed node identities, when failures reproduce only on the local host, or when a path-filtered check fails on stale in-repo plan inputs that main already repaired."
category: ci-cd
date: 2026-07-31
version: "2.4.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-ci
tags:
  - ci-failure
  - triage
  - check-runs
  - preexisting
  - concurrency
  - flaky
  - stale-commit
  - merge-preview
  - ruleset
  - fan-in-gate
  - undefined-symbol
  - e2big
  - post-merge-hybrid
  - file-provenance
  - host-window
  - shard-logs
  - paths-filter
  - stale-plan-inputs
  - evidence-artifact
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/pr-ci-failure-triage-preexisting-vs-introduced.history"
history-cleanup-date: "2026-09-20"
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
[pr-ci-failure-triage-preexisting-vs-introduced.history](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/pr-ci-failure-triage-preexisting-vs-introduced.history).

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
- Checks go red only after a base update merged current main into the branch, while main's own CI is green.
- Shard or grouped step output fails without listing the individual `FAILED` node identities.
- Tests fail on the local host but pass on the hosted runners.
- The failing workflow is path-filtered (`on.pull_request.paths`), so it is absent from
  main's run history and from PRs whose diffs stay outside the filter — and a check with
  pinned in-repo plan inputs (a fixed selector or case list) dies before any test count
  with a usage-style error.

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
| Fails; sibling PRs on the same base show no run | No main run; workflow is path-filtered and the diff touches the filter | Trigger-scoped failure; classify from the check's inputs, not from run history |
| Intermittent signature | Main/PR history mixed | Flake/infrastructure candidate |

“Unrelated diff” is supporting context, not classification evidence. A path filter can
empty the comparison set entirely: when the workflow only runs for diffs that touch its
`paths:` list, neither main nor unaffected PRs carry any run for these inputs, so the
absence of a main failure is expected and says nothing about ownership.

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
- Path-filtered check whose plan inputs are pinned in-repo (a fixed selector, node list, or
  case file): a rename or removal on main makes those inputs stale, and every base that
  predates the input repair fails with an exit before any test count. Diff the pinned input
  against the current tree — `git log -S <missing-selector> -- <input-file>` names the
  change that renamed it, and `git log -1 --format=%H origin/main -- <input-file>` shows
  whether current main already carries a corrected input. When the failure log collapses to
  one usage-style line, download the job's uploaded evidence artifacts; the harness's
  selection or execution record usually names the collected-vs-selected mismatch directly:

  ```bash
  gh run download <failed-run-id> -n <evidence-artifact-name>
  ```

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

### 6. Attribute post-base-update failures by file provenance

A base update that merges current main into the branch can turn a green branch red without a
textual conflict. Before you change code, establish which parent owns each side of the failing
content:

```bash
OLD_BASE=<recorded-previous-base>
PRE_UPDATE=<branch-head-before-the-update>
git diff "$OLD_BASE"..HEAD -- <failing-test-file>
git diff "$OLD_BASE"..HEAD -- <subject-source-files>
git diff "$OLD_BASE".."$PRE_UPDATE" -- <subject-source-files>
```

| Evidence | Class | Action |
| --- | --- | --- |
| Test file carries branch-only deltas, subject source is identical to trunk, and the branch never carried companion source | Stale branch assertion against current trunk semantics | Port the test's intent onto trunk's semantics; retire it when trunk supersedes the coverage |
| The update took one half of a lockstep pair, such as a workflow and the script that consumes its output, from different eras | Half-moved pair | Move the pair atomically to all-old or all-new, then rerun the pair's own checks |
| Subject source carries branch deltas and reverting them removes the failure | Genuine PR regression | Fix minimally in scope |
| The same nodes fail set-identically on a pristine trunk worktree on this host, and trunk CI is green | Host/environment window | Report FYI with the reproduction evidence; do not patch the PR for it |

Keep one pristine worktree at the recorded base with a synced environment as the attribution
oracle. A failure that reproduces there is not introduced by the branch. When the failure involves
filesystem ownership, modes, or ACL semantics, prefer the hosted-runner result: a local mount can
force modes, mask ACL behavior, or change user identity, so chmod-based assumptions can fail in
either direction.

Diagnose from the failing node identity, not from a shard or step summary. Grouped step output can
withhold individual `FAILED` lines until the job ends, and sharding splits the parametrized cases
of one test across jobs, so any single job under-reports the failing set. Wait for the job to end,
then extract node identities:

```bash
gh run view --job <JOB_ID> --log-failed
```

An exit before any test count, for example a pytest usage exit with zero reported tests, names a
plan-stage failure: missing planner input, collection error, or workflow rejection. Read its first
error line directly instead of guessing from the shard list.

### 7. Inspect branch content for stale duplicate commits

```bash
git log --oneline --decorate origin/main..HEAD
git diff --stat origin/main...HEAD
git cherry -v origin/main HEAD
```

If a stale commit duplicates a fix already on main, rebuild the branch from current main with only
the real payload. Do not amend an arbitrary tip when the unwanted commit is lower in history.

### 8. Resolve according to evidence

- PR-introduced: fix within scope and add regression coverage.
- Merge interaction: rebase/update, reproduce merge preview, and fix the interaction.
- Confirmed flake: rerun only failed jobs after recording the signature.
- Pre-existing required failure: fix main separately when practical; otherwise use only an
  explicitly authorized governance path and file a linked tracking issue.
- Trigger-scoped stale-plan-input failure already repaired on current main: take a base
  update under the repository's task-base policy (record the reason plus old and new base
  and head commits, then rebind verification to the new head). Do not patch the PR's own
  files to mask a check that main already fixed.
- Rollup artifact: no code change; wait for/read the current-head run.
- New-check failure: fix the check or product contract; do not compare it to a nonexistent main run.

After any fix/rebase, repeat SHA and check-run binding. Surface classification and evidence in the
PR, not only stderr or a private note.

### Guidance retained from an absorbed history

Distinguish a workflow setup failure from a product failure before replacing a
CI action. Inspect the selected action or hook revision and reproduce its actual
invocation. An old failure at one version does not establish a permanent ban on
that action or on commit-based pins. Preserve required-check coverage when changing
the tool invocation.

History cleanup: 2026-09-20. The [prior source](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/ci-cd-pipeline-maintenance-patterns.history)
retains its original evidence limits. This migration does not establish new
operational verification.

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
| 9 | Satisfied a stale branch assertion by changing source after a base update | The update had taken trunk's source while the branch's test asserted semantics trunk had deliberately retired | Diff test and subject source against the old base; port the test's intent onto trunk semantics |
| 10 | Diagnosed the failing set from shard and step summaries | Grouped logs and parametrized splits withheld node identities; the visible rows were not the complete set | Wait for job end; extract `FAILED` nodes with `gh run view --job <job> --log-failed` |
| 11 | Took trunk's half of a lockstep workflow/validator pair during conflict resolution | The surviving branch half rejected every trunk-shaped evidence on prefix checks | Move producer/consumer halves atomically; rerun the pair's own checks |
| 12 | Treated a local-only failure as a PR defect | The same nodes failed set-identically on a pristine trunk worktree; hosted CI was green | Bind local failures to the pristine-base oracle before attribution |
| 13 | Classified a path-filtered check from main's history alone | The workflow runs only for diffs that touch its `paths:` list, so main carried no failure and same-base unaffected PRs carried no run at all — the comparison set was empty while a stale pinned selector made every filtered base fail | Check the workflow's trigger filter first; for in-repo plan inputs, diff the pinned selector against the tree and read the job's uploaded evidence artifacts, then remediate a main-repaired input by a base update |

## Results & Parameters

- Authoritative identity: exact PR head and current main head SHAs.
- Primary status source: check-runs API per commit; workflow history supplies recurrence evidence.
- Rerun policy: failed jobs only, and only after a flake classification is recorded.
- Generated harness transport: stdin for large scripts; avoid platform-dependent argv budgets.
- Final gate: current-head required checks, not cancelled or stale runs.
- Resolution record: check name, PR/main result, log signature, classification, action, and linked
  issue/repair when outside scope.
- Post-update provenance diffs: old base to head for the failing test and its subject source, plus
  old base to the pre-update branch head to detect companion source the update dropped.
- Attribution oracle: one pristine worktree at the recorded base with a synced environment.
- Node identity: `gh run view --job <JOB_ID> --log-failed` after the job ends; shard and step
  summaries are not exhaustive. An exit before any test count is a plan-stage signature, not a
  test verdict.
- Trigger audit for a red check with no main history: read the workflow's `on:` block for a
  `paths:` filter before comparing runs; classify from the check's pinned inputs and its
  uploaded evidence artifacts (`gh run download <run-id> -n <evidence-name>`), not from an
  empty run comparison.
- Main-repaired stale input: `git log -1 origin/main -- <input-file>` differing from the
  base copy means current main may already carry the repair; remediate by a recorded base
  update, not by PR-side workarounds.

## Evidence Boundary

The decision method is CI-verified across the indexed GitHub cases. Exact administrative options,
required-check policy, runner limits, and merge-preview behavior are repository-specific; inspect
live rules and current runs before acting.
