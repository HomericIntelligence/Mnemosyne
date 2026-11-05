---
name: hephaestus-automation-loop-branch-sync-drive-green
license: BSD-3-Clause
description: "Inspect reused issue worktrees and incomplete automation runs. Keep each worker within its PR scope, check publication and signing, and diagnose drive-green invocation failures. Recover a lane whose commit_push fails closed after a landed push or whose receipt invalidates after the pipeline's own push, arm native auto-merge when the post-GO merge stage cannot run, separate stale-payload label-gate CI noise from real failures, and classify a retry that reports an unserved-model error after the first attempt timed out as a timeout budget defect, not a dead deployment."
category: tooling
date: 2026-10-30
version: "1.7.0"
user-invocable: false
verification: verified-live
tags:
  - projecthephaestus
  - automation-loop
  - drive-green
  - git-worktree
  - branch-sync
  - codex
  - signed-commits
  - dco
  - pr-scope
  - auto-merge
  - lane-recovery
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/hephaestus-automation-loop-branch-sync-drive-green.history"
history-cleanup-date: "2026-09-20"
---

# Hephaestus Automation Loop Branch Sync and Drive-Green Scope

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-11 |
| **Objective** | Make automation-loop workers finish their owned issue/PR reliably instead of reusing stale branches, ignoring review/comment state, or letting broad drive-green phases act on unrelated PRs — and invoke a repo-wide "drive all open PRs to green" run correctly. |
| **Outcome** | Core fix landed in ProjectHephaestus PR #1646 for issue #1645 (merged 2026-06-26, verified-ci). v1.1.0 adds the `--drive-green-all` vs `--phases drive-green` invocation finding (verified-local: dry-run caught the crash; `--drive-green-all` confirmed on a live ~3-minute run driving 14 open PRs). v1.5.0 adds the post-review-round failure family on a long-lived PR lane (verified-live): landed-push commit_push fail-closes, self-inflicted receipt invalidation, post-GO merge-stage crash with direct native auto-merge arming, per-run budget refresh on relaunch, and stale-payload label-gate CI noise. v1.6.0 corrects the label-event run semantics (verified-live) and adds the skipped-job gate signature and aggregated-required-check rule. v1.7.0 adds the planner-timeout decision branch (verified-live): a first attempt that times out and then reports an unserved-model error on retry is a budget defect, not a dead deployment, so the repair is the timeout budget and never a model substitution. |
| **Verification** | verified-ci (core); verified-local (v1.1.0); verified-live (v1.5.0, v1.7.0) |
| **History** | [changelog](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/hephaestus-automation-loop-branch-sync-drive-green.history) |
| **Latest** | v1.7.0 (2026-11-04): planner-timeout-versus-served-model decision branch |

## When to Use

- A ProjectHephaestus automation loop reports progress but leaves issues, implementation PRs, or review-thread work unfinished.
- An implementation worker reuses an existing issue branch or worktree from a previous run.
- A reused worktree needs an identity, dependency, and conflict check before work resumes.
- A drive-green phase is scoped by intent to one issue/PR but logs or touches unrelated open PRs.
- A final status sweep shows green-but-unarmed, stale, or review-blocked PRs after per-worker phases finish.
- Codex is the selected agent and commits must satisfy both signed-commit and `Signed-off-by` policy checks.
- You want to drive all **existing open PRs** to green (resolve actual integration and CI blockers on existing PRs) without planning or implementing new issues from scratch.
- An attempt to run only the drive-green stage via `--phases drive-green` crashes with `KeyError: <StageName.REPO: 'repo'>` and reports the item "poisoned at repo".
- A run fails closed with `FAIL:commit_push_refresh_invalid` after a commit+push job that carried real commits, and you must decide whether the work was published.
- A run fails closed with `FAIL:source_workspace_recovery_receipt_invalid` immediately after the pipeline's own push advanced the PR branch, or the lane freezes at `source_workspace_terminal` for the same reason.
- A run dies with `FAIL:implement_exhausted` right after a landed push, and you must decide whether a relaunch is safe.
- After `state:implementation-go`, a run dies in seconds with `FAIL:auto_merge_malformed` before the merge stage can read check state, and the checks are red.
- Agent jobs ran for a long time, produced no PR or plan, and the run ends with `FAIL:plan not found; exhausted after 2 attempts`. The retry reports an unserved-model error (`No worker available`, `not in the current serving set`, or `provider.no-route: Model unavailable`), but the same model answers a direct probe. Treat this as a planner-timeout budget defect, not a dead deployment.

## v1.2.0 findings (2026-07-17)

- **Orphan PRs swept by `--drive-green-all` (fixed: PR #2254).** PR-only items (`issue=None`) were
  regressed by the implementation-go gate and terminated as "no issue number". They now skip that gate
  and proceed to REBASE_WAIT; merge containment is unchanged. Residual gap under watch: orphan PRs
  reach REBASE_WAIT with no item worktree and log `mechanical rebase requires an item worktree`.
- **`--max-merge-attempts` replaced by `--drive-green-loops N` (PR #2249).** The old default of 1 let
  one transient failure durably `state:skip` an issue (76 skip-parked in one overnight run). The old
  option is REMOVED and now fails argparse; the new default is 5.

## v1.5.0 findings (2026-10-30)

Observed on a 20-run implementation lane that drove one direct PR through 12 review rounds to
GO and merge (identifiers generalized; evidence in the notes file). These failures sit after
first publication on a long-lived lane, so they belong to the conveyor this entry covers, not
to the pre-publication recovery covered by
[hephaestus-interrupted-implementation-lane-recovery](hephaestus-interrupted-implementation-lane-recovery.md).

### Landed pushes still fail close in commit_push (`FAIL:commit_push_refresh_invalid`)

On a lane with an open PR, a commit_push job that carries real commits can fail closed
deterministically with `FAIL:commit_push_refresh_invalid` (observed on 5 of 7 real-push
attempts on one lane; 2 real pushes succeeded). **The push lands before the fail-close.** Before
any recovery action, verify `git ls-remote origin <branch>` against the lane head. A no-op
push succeeds, so the refresh binding rejects the post-push state, not the push itself.

Recovery loses no work: verify the preserved worktree has 0 unpublished commits and 0 dirty paths
(push any unpublished commits first, dry-run then fast-forward), archive — never delete — the
stale lane receipt, remove the worktree, and relaunch clean.

### A successful push can invalidate the lane's own receipt (`FAIL:source_workspace_recovery_receipt_invalid`)

The invalidation can be self-inflicted: the pipeline's own landed push advances origin past
the receipt revision, so the next adoption rejects the receipt that the previous run just
regenerated. A terminal variant freezes the lane at `source_workspace_terminal` and writes a
terminal record. Recovery is the same archive-never-delete cycle, with two records when a
terminal record exists — keep the archive append-only (one directory per run, oldest first).
A run that then dies with `FAIL:implement_exhausted` encodes a per-run budget, not a lane
defect: a clean relaunch refreshes the budgets.

### After GO the loop is terminal: arm native auto-merge directly (`FAIL:auto_merge_malformed`)

After the `state:implementation-go` label, the merge stage's GitHub mutation can crash on an
unresolvable working directory (a mount-boundary `fatal: not a git repository`) and be
misclassified as `auto_merge_malformed`. merge_wait fails before it reads check state, so every
relaunch dies in seconds at the same stage. The GO label is the whole merge contract, so the
coordinator arms GitHub native auto-merge directly:

```bash
gh pr merge <pr> --repo <org>/<repo> --auto --squash
```

The native auto-merge request survives later pushes to the lane head; GitHub merges when the
required checks pass. From then on the coordinator owns CI repair: work in a detached temporary
worktree at the lane head, push signed fast-forward commits, and confirm the auto-merge request
stays armed at each new head.

### Label-gated CI: stale-payload failures are noise

Label-gated workflows compute the gate from the event payload
(`github.event.pull_request.labels.*.name`), not from live PR state. A run whose payload
predates the GO label fails fast with a step that names the missing label, or skips at the
job-level condition. When the pull-request trigger list includes `labeled`, applying the GO
label itself starts a fresh run whose payload contains that label, so the gated checks run for
real without another push. Sequence it so: deliver the review at the exact head, then flip the
state labels; never push after the flip, because a new head invalidates the delivered review.
Read one failing job log before repairing: gate failures name the missing label within seconds
or show as skipped jobs; content failures (format, type, test-tier inventory) take minutes and
name files. A fast-failing aggregated check that reports only "require all upstream jobs to
have succeeded" has no defect of its own; read the named upstream job. A repository's
pre-commit configuration can pin an older formatter than the project-resolved one and can
reformat files a glob pass never visits, so treat `pre-commit run --all-files` as the
authoritative style gate before pushing a CI repair.

### Review convergence still terminates the conveyor

A reviewer round with zero findings and all threads resolved skips commit_push entirely, so a
lane stuck in the push fail-close cycle converges anyway. Convergence signals: finding counts
trend down, major findings stop appearing, and nitpicks dominate late rounds. When every thread
is answered and resolved, one more clean relaunch is the whole remaining cost of a review round.

## v1.7.0 findings (2026-11-04)

### A planner timeout reports on retry as an unserved model

A planning batch failed with `FAIL:plan not found; exhausted after 2 attempts plan=2` after 14
completed agent jobs. The summary named a provider error, not a timeout. Read the attempt timeline
before you act:

```text
20:36:23  seven plan AgentJobs claimed (workers 1-7)
20:56:23  all seven report "job failed: timeout"   # ~20 min = the 1200 s default
20:56:35  seven retries claimed
21:05:55  retries fail: provider.invalid-request: No worker available for model '<name>'
21:07:04  retries fail: '<name>' is not in the current serving set
21:07:08  retries fail: provider.no-route: Model unavailable: <provider>/<name>
```

Three different unserved-model texts arrived for one model in one window, and a direct
`Reply with exactly: OK` probe of that model answered OK before and after the run. The model was
served throughout. The first failure is the only real signal: the planner budget was too small for
that model. The retry then transports a timeout into the provider classifier, so the retry error
describes the transport, not the cause.

This is the inverse of the probe rule for a dead deployment. A dead deployment fails the probe. Here
the probe passes and the run still fails. When attempt 1 ends at the configured timeout and every
retry fails in seconds with an unserved-model error while the model probes live, the defect is the
budget.

Recovery:

1. Confirm the shape: the first failure is `job failed: timeout`, it lands one budget after the
   claim, and the later errors name a served model.
2. Do not substitute the model, re-probe to justify a swap, or drop the items. A different model on
   the same budget times out the same way.
3. Raise the budgets that run that model (`--planner-timeout`; prior verified evidence for a thinking
   model: 5400 s planner, 3600 s reviewer).
4. Confirm the model still probes live, then relaunch the same item list. Explicit `--issues` scope
   drains once per run and re-classifies from live labels, so a relaunch is the continuation step.

Set the budget from the largest expected plan, not from the default: a 20-minute plan and a 1200 s
default produce a silent zero-output batch on every wave.

## Verified Workflow

### Current applicability

Use [verify-pr-ready](verify-pr-ready.md) for live policy, affected validation, and evidence
reuse. A branch behind main is not itself blocked. During active work, prefer a stable
base unless a blocker or required main content makes an update useful. After completion,
prefer CI/CD or the merge queue for ordinary integration; resolve reported merge conflicts
or follow an explicit rebase request. Respect CI and revision-bound review where repository
policy requires them before merge. PR publication can precede validation if pending results
are clear.
Cleanup is separate from rebasing. Historical verification below does not verify this
policy correction or the current version of an external tool.

### Quick Reference

```bash
# 1. Before each implementation worker resumes or reuses an issue branch/worktree:
git fetch origin
git -C <issue-worktree> status --short --branch
git -C <issue-worktree> log --oneline --left-right HEAD...origin/main
git -C <issue-worktree> status --short --branch

# 2. Verify the worker owns exactly one issue/PR scope before drive-green:
gh issue view <issue> --json state,labels
gh pr list --state open --search "<issue> in:body" --json number,headRefName,state
hephaestus-automation-loop --issues <issue> --agent <agent>

# 2b. Before you swap a model because the retries named it as unserved:
#     read attempt 1. A timeout that lands one budget after the claim is the cause.
grep -nE "job failed: (timeout|agent_error)" <run>.log
#     If attempt 1 timed out, raise --planner-timeout and relaunch the same items.

# 3. Keep drive-green scoped to the owned issue/PR inside the worker:
hephaestus-merge-prs --issues <issue> --agent <agent>

# 4. After all per-worker runs, run one explicit catch-all pass:
hephaestus-merge-prs --agent <agent>

# 5. Verify commit policy before pushing or arming auto-merge:
git log origin/main..HEAD --pretty=format:'%h %G? %s'
git log origin/main..HEAD --format=%B | grep -q '^Signed-off-by: '

# 6. To drive ALL existing open PRs to green, fix CI and rebase only when the
#    task-phase rule permits it. Otherwise, use CI/CD or the merge queue. Use
#    --drive-green-all without planning or implementing new issues. It runs
#    the full loop bootstrap first so the REPO stage is seeded:
pixi run hephaestus-automation-loop \
  --repos <Repo> --drive-green-all --max-workers 4 --parallel-repos 1 --model <model>

# DO NOT use `--phases drive-green` standalone — it CRASHES because the drive-green
# stage dereferences the REPO StageQueue, which --phases drive-green never seeds:
#   KeyError: <StageName.REPO: 'repo'>   (item "poisoned at repo")
# Always --dry-run a novel flag combination first to surface this before a live run.
```

### Detailed Steps

1. **Inspect the branch before reuse.** Fetch the target and record the worktree head,
   remote PR head, ownership, and local changes. Confirm that the intended work and required
   dependencies are present. Do not rebase only because the target advanced.

2. **Preserve existing work.** Inspect `git log HEAD..origin/main`,
   `git diff --stat origin/main...HEAD`, and live PR review state. A commit subject alone
   does not prove that a fix is complete or obsolete. During active work, rebase only for a blocker
   or required main content. After task completion, rebase only for a host-reported merge conflict.
   Review changed content and run affected checks.

3. **Make worktree ownership explicit.** Each implementation worker should own one issue and the PR that closes it. If the worker discovers an existing PR, sync to that PR head and account for comments, reviews, and thread state before deciding the implementation is done.

4. **Scope drive-green inside a worker to the owned issue/PR.** A per-issue worker should not run a broad repo-wide drive-green phase that can fail because of unrelated PRs, arm unrelated PRs, or attribute unrelated CI failures back to the worker's issue. Pass the issue/PR scope through all worker-local drive-green calls.

5. **Consider a final broad pass when fleet or repository-wide delivery is requested.** A per-issue repair does not authorize arming unrelated PRs. Continue within the selected issue scope unless the existing task includes the broader sweep.

6. **Handle Codex commit policy explicitly.** When Codex is the selected agent, ensure commits satisfy the repo policy for both signed commits and `Signed-off-by` trailers. Verify the commit range before pushing or enabling auto-merge, and repair the commit history if either policy gate would fail.

7. **Use live GitHub state as the completion gate.** Before reporting the loop complete, check the issue state, PR state, required checks, review/thread state, and auto-merge state live from GitHub. Local success logs are not enough.

8. **To drive all existing open PRs to green, use `--drive-green-all` — never `--phases drive-green` standalone.** When the goal is to shepherd already-open PRs (resolve actual integration blockers and fix CI) rather than plan or implement new issues from scratch, use `--drive-green-all` with no `--phases`:

   ```bash
   pixi run hephaestus-automation-loop \
     --repos <Repo> --drive-green-all --max-workers 4 --parallel-repos 1 --model <model>
   ```

   `--drive-green-all` runs the full loop bootstrap first, which initializes the `StageName.REPO` StageQueue, and only then executes the drive-green stage. In contrast, `--phases drive-green` attempts to run ONLY the drive-green stage and skips the repo-stage bootstrap; the drive-green stage then dereferences the uninitialized REPO stage key and crashes with `KeyError: <StageName.REPO: 'repo'>`, reporting the item "poisoned at repo". The REPO stage is a **prerequisite**, not an independently runnable phase — `--phases` does not compose freely across all subsets. Prefer the purpose-built flag over hand-composing phases.

9. **Expect a correct `--drive-green-all` run to be FAST, and read a non-zero exit code carefully.** A correct run shepherds existing PRs (review + route to CI) rather than planning/implementing from scratch, so short runtime is normal (observed: ~3 minutes over 14 open PRs — 7 reviews requested, 5 already-GO'd PRs adopted → CI, 0 new GO verdicts). A short run is EXPECTED, not a sign of a no-op. An `exit_code=1` in this mode typically reflects item-level review non-GOs, not a crash — distinguish it from the `--phases drive-green` KeyError crash above.

10. **Consider a dry-run for unfamiliar flag combinations.** It can expose stage-seeding errors before an authorized live run; parser inspection and focused tests can also establish the relevant prerequisite.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Rerunning issues after stale merged-PR close detection | The loop detected that a closing PR had merged or that the issue looked stale, then reran the issue without first ensuring the branch/worktree was on current `origin/main`. | The worker could resume against stale local state and miss the actual current mainline or review/comment context. | Fetch and inspect the reused worktree against live PR state; integrate only when needed. |
| Broad drive-green over multiple PRs from inside workers | Worker-local drive-green ran over the broader repository instead of the owned issue/PR. | Unrelated PRs could be armed, fail, or affect the worker's return code, making one issue's worker responsible for repo-wide state. | Keep worker-local drive-green scoped to the issue/PR; reserve broad drive-green for a final catch-all pass. |
| Preserving stale local commits instead of rebasing | Existing local branch commits were treated as work to preserve because their subjects looked relevant. | Stale branches can be based on old main, miss required files or comments, or carry partial/revert-shaped changes. | Preserve local work, inspect its content and live PR state, and resolve actual integration needs. |
| Fake or local-only substitutes for externally required tools | Local stand-ins were used for checks that the real external workflow or policy gate would enforce. | The local result did not prove the automation path would pass required CI, signing, review, or GitHub policy gates. | Use the real tool path for required external gates, or mark the result unverified. For this workflow, rely on required CI and live PR evidence. |
| Codex commits without explicit policy verification | Codex-generated commits were allowed to proceed without checking both cryptographic signature state and `Signed-off-by` trailers. | Required policy checks can reject commits even when the code and tests are correct. | Verify `git log origin/main..HEAD --pretty=format:'%h %G? %s'` and scan commit bodies for `Signed-off-by:` before push/auto-merge. |
| Running only the drive-green stage via `--phases drive-green` | Ran `hephaestus-automation-loop --phases drive-green` to shepherd existing open PRs without planning/implementing new issues. | Crashed with `KeyError: <StageName.REPO: 'repo'>`; the item was "poisoned at repo". The drive-green stage dereferences the REPO StageQueue, which `--phases drive-green` never seeds because it skips the repo-stage bootstrap. | Use `--drive-green-all` (no `--phases`) to drive existing PRs to green; it runs the full bootstrap first so the REPO stage is seeded. Dry-run novel flag combos to surface this before a live run. |
| Assuming `--phases` composes freely across any subset | Expected any subset of phases (e.g. just `drive-green`) to run standalone. | The repo stage is a required prerequisite for later stages, not an independently runnable phase; skipping it leaves a downstream stage referencing an uninitialized key. | Some phases are prerequisites, not independently runnable. Prefer the purpose-built flag (`--drive-green-all`) over hand-composing `--phases` subsets. |
| Recovering a `commit_push_refresh_invalid` without checking origin | A fail-closed commit+push job was treated as unpublished work. | The push lands before the fail-close; origin already holds the head, so the recovery is archive-and-relaunch, not republish. | Verify `git ls-remote` against the lane head first; never delete lane records; relaunch clean after the worktree proves 0 unpublished and 0 dirty. |
| Relaunching the loop after a post-GO merge-stage crash | Relaunched so merge_wait could read red checks and drive the repair. | The merge stage crashes before it reads check state (`auto_merge_malformed` from an unresolvable `gh`-mutation working directory); each relaunch dies in seconds at the same stage. | Post-GO, arm native auto-merge directly with `gh pr merge --auto`; the coordinator owns CI repair on the lane head from a detached temporary worktree. |
| Trusting a repo-glob format check as the drive-green style gate | `ruff format --check .` passed while CI's pre-commit job kept failing. | The pre-commit configuration pins an older formatter and formats files the glob never visits (for example an extensionless script). | Use `pre-commit run --all-files` as the authoritative gate before pushing a CI repair. |
| Substitute the model after a planner timeout | The batch reported `No worker available` / `not in the current serving set` / `provider.no-route: Model unavailable` on the retries, so the next action was to re-probe the pool and re-spawn on a different model. | The retries recycled a *timeout* from attempt 1 (all seven first attempts ended together at the 1200 s default). The named model probed live both during and after the run, so substituting it changed nothing and would have burned the same budget again. | Read the first failure, not the retry error. A timeout that surfaces as an unserved-model error is a budget defect: raise `--planner-timeout` and relaunch the same items. |

## Results & Parameters

### Public Evidence

- ProjectHephaestus issue: #1645.
- ProjectHephaestus fix PR: #1646.
- Merge date: 2026-06-26.
- Required Checks run: 28256238895 succeeded.
- Test workflow run: 28256151963 succeeded.
- Squash merge commit: `2a0cd2adc2570264c1bd2c45df96c75246bac433`.

### Driving All Open PRs to Green (v1.1.0, verified-local)

Correct invocation — drives existing open PRs to green by fixing CI and, only when the
task-phase rule permits it, rebasing. Otherwise, CI/CD or the merge queue integrates the PR.
It does not plan or implement new issues:

```bash
pixi run hephaestus-automation-loop \
  --repos <Repo> --drive-green-all --max-workers 4 --parallel-repos 1 --model <model>
```

Broken invocation — crashes before doing any work:

```bash
# --phases drive-green skips the repo-stage bootstrap; the drive-green stage then
# dereferences the uninitialized REPO StageQueue:
#   KeyError: <StageName.REPO: 'repo'>   (item reported "poisoned at repo")
pixi run hephaestus-automation-loop --repos <Repo> --phases drive-green   # DO NOT USE
```

Observed behavior of a correct `--drive-green-all` run:

- FAST: a ~3-minute run over 14 open PRs.
- Of those 14: 7 reviews requested, 5 already-GO'd PRs adopted → routed to CI, 0 new GO verdicts granted.
- Short runtime is EXPECTED — drive-green shepherds existing PRs (review + route to CI) rather than planning/implementing from scratch.
- `exit_code=1` reflects item-level review non-GOs, not a crash. Distinguish it from the `--phases drive-green` KeyError crash.

Upstream improvement (low priority): `--phases drive-green` should either error
clearly ("drive-green requires the repo stage; use --drive-green-all") or
auto-include the repo bootstrap, rather than KeyError-poisoning the item. The
`--drive-green-all` workaround is reliable, so this is low priority.

### Completion Checklist

```bash
# Branch/worktree identity and dependency inspection
git fetch origin
git -C <issue-worktree> log --oneline --left-right HEAD...origin/main
git -C <issue-worktree> diff --stat origin/main...HEAD

# Live issue/PR ownership
gh issue view <issue> --json state,labels
gh pr list --state all --search "<issue> in:body" --json number,state,headRefName,mergeStateStatus

# Worker-local convergence
hephaestus-automation-loop --issues <issue> --agent <agent>
hephaestus-merge-prs --issues <issue> --agent <agent>

# Final repo-level sweep after all workers finish
hephaestus-merge-prs --agent <agent>

# Commit-policy guard for Codex or any agent path
git log origin/main..HEAD --pretty=format:'%h %G? %s'
git log origin/main..HEAD --format=%B | grep -q '^Signed-off-by: '
```

### Expected Result

- Each worker starts from the verified intended branch and required dependencies.
- Each worker implements, reviews, addresses review state, and drives only the PR it owns.
- Unrelated PR state cannot make one worker appear failed or complete.
- The final broad drive-green pass is explicit and intentionally repo-level.
- The PR can satisfy required CI plus signed and signed-off commit policy gates.
- A landed push is detected on origin before any recovery, lane records are archived and never deleted, and clean relaunches resume at the true head.
- After GO, a merge stage that cannot run yields to directly armed native auto-merge, and red checks are classified (stale-payload label-gate noise versus content failures) before any repair.
- A batch that reports an unserved-model error on retry is classified by its first failure: a timeout raises the budget and relaunches the same items instead of swapping the model.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectHephaestus | Issue #1645 / PR #1646 | verified-ci; Required Checks run 28256238895 succeeded; Test workflow run 28256151963 succeeded; merged 2026-06-26 as `2a0cd2adc2570264c1bd2c45df96c75246bac433` |
| ProjectHephaestus | `--drive-green-all` vs `--phases drive-green` (2026-07-11) | verified-local; `--dry-run` of `--phases drive-green` surfaced `KeyError: <StageName.REPO: 'repo'>` (item "poisoned at repo"); `--drive-green-all` confirmed working on a live ~3-minute run driving 14 open PRs (7 reviews requested, 5 already-GO'd PRs → CI, 0 new GO). |
| Organization repository (identifiers generalized) | Planning batch on an explicit 8-item issue selection (2026-11-04) | verified-live; seven plan jobs timed out together 1200 s after claim, seven retries failed 10-11 s later with `No worker available` / `not in the current serving set` / `provider.no-route`, 14 agent jobs and ~12,600 s of agent time produced 0 plans, and the same model probed OK before and after. See [notes](hephaestus-automation-loop-branch-sync-drive-green.notes.md#v170-evidence-planner-timeout-surfaced-as-an-unserved-model-error-2026-11-04). |
| Organization repository (identifiers generalized) | Post-review-round failure family on a 20-run implementation lane (2026-10-30) | verified-live; `commit_push_refresh_invalid` reproduced 5× on real pushes (push landed every time; 2 real pushes succeeded), receipt invalidation after the pipeline's own push (incl. the `source_workspace_terminal` freeze), per-run budget refresh on relaunch, GO label applied by the loop itself, merge stage died `auto_merge_malformed`, coordinator armed native auto-merge, coordinator CI repairs (test-tier inventory registration, format/typecheck, pinned-formatter style), and the PR merged green with post-merge main CI green. |
