---
name: ci-release-gate-stricter-than-branch-green-not-transferable
license: BSD-3-Clause
description: "Decide whether a green check result on one path predicts another path. Use when the default branch is green but a tag or release run failed a gate the branch never ran, or when a reusable workflow is called with an input that changes which checks execute."
category: ci-cd
date: 2026-10-19
version: "1.0.0"
user-invocable: false
tags:
  - ci-cd
  - release
  - gate-parity
  - workflow-call
  - coverage-threshold
  - required-checks
  - green-signal
---

# CI Release Gate Stricter Than the Branch: Green Does Not Transfer

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-19 |
| **Objective** | Decide whether a green result on the default branch predicts the outcome of a tag or release path, and choose the repair when it does not. |
| **Outcome** | Successful — the divergent gate was identified, the defect it exposed was repaired on the default branch, and the re-cut tag cleared every required job. |

## When to Use

- The default branch's required checks are green, but a tag-triggered run failed on a gate the branch never executed.
- A reusable workflow accepts a boolean input that selects between a stricter and a faster check, and its two callers pass different values.
- One path runs the full test suite with a per-file coverage floor while another runs a marker-filtered subset with no coverage step.
- You are about to write "main is green, so the release will pass", and the release path's job list differs from the branch path's job list.
- A tag exists, the artifact was never published, and the publish job shows **skipped** rather than failed.

**Key trigger:** the default branch is green and a tag-triggered run failed, yet the failing check is one the branch's own run never executed.

## Verified Workflow

### Quick Reference

```bash
# 1. Confirm the failing run is the tag/release path, not the branch path.
gh run view <run-id> --json name,workflowName,headBranch,headSha,conclusion
#   -> headBranch is a version tag, and workflowName is the release workflow.

# 2. Confirm the publish job was SKIPPED, not failed.
gh run view <run-id> --json jobs -q '.jobs[] | "\(.conclusion // .status)  \(.name)"'
#   -> "failure  <gate>" and "skipped  <publish job>"

# 3. Read the reusable workflow's inputs and their defaults.
grep -nA12 "workflow_call:" .github/workflows/<required>.yml
grep -nA12 "workflow_call:" .github/workflows/<release>.yml
#   -> an input whose default differs between the two callers is the divergence.

# 4. Find the condition that selects the stricter or faster step.
grep -nE "if:.*inputs|full-tests|fast" .github/workflows/<required>.yml
#   -> the branch path takes one branch of the condition, the release path the other.

# 5. Compare the ACTUAL command each path runs, not the job names.
#    Branch path: a marker-filtered subset with no coverage step.
#    Release path: the full suite plus a coverage-threshold step.
#    A branch path that never runs the threshold cannot report a threshold failure.

# 6. Reproduce the RELEASE path's invocation locally before tagging.
#    Run the stricter command exactly as the release job invokes it.
#    The branch's own green result is not a substitute.
```

### Suggested Approach

A green result is evidence about **the invocation that produced it**. It is not evidence about a
second invocation that differs in any input. When two paths call the same reusable workflow with
different inputs, the gate sets differ, and the branch's green result says nothing about the
release path's result.

The practical consequence is a defect that can sit on the default branch for an unbounded time
without any normal signal: the branch path runs a fast subset and never evaluates the threshold, so
the branch stays green while the stricter path fails on every attempt.

**Do not mirror the gate in this direction.** The neighbouring rule — that a release path must
itself run the same gate the pull-request path enforces — is directional and assumes the release
path is the weaker one. Applying it here would mean lowering the release path to the branch path's
weaker invocation, which deletes the coverage floor and silently weakens every future release.
When the release path is already the stricter one, the only correct repairs are:

1. repair the defect the stricter gate exposed, **on the default branch**, through a normal pull
   request; and
2. cut the tag on the fixed commit.

Changing the release workflow to make the two paths agree is wrong in this direction. If the
difference was accidental, fix the default branch's path to run the same stricter invocation; if it
was deliberate, leave the workflows alone and fix the code.

**The failure shape is misleading.** A failed gate causes the downstream publish job to be
**skipped**, not failed. The run then reads as an ordinary test failure while the artifact was
never published. Always read the publish job's own conclusion.

**Do not re-run the failed run to "clear" it.** A re-run executes the same invocation against the
same tagged commit and fails identically. The fix has to land in the commit the tag points at.

### Detailed Steps

1. **Establish which path the failure belongs to.** Read the run's workflow name and head branch. A
   version tag as the head branch identifies a tag-triggered run. Do not infer the path from the
   repository's green branch.

2. **Confirm the skip, not the fail.** Read each job's conclusion. A skipped publish job beside a
   failed gate is the signature of an unpublished artifact, and it tells you which gate to
   investigate.

3. **Diff the two paths' invocations, not their job names.** For each path, record the reusable
   workflow inputs, their values, and the command each step runs. Job names are often identical
   across paths even when the underlying commands differ.

4. **Locate the input that selects the divergence.** A boolean input with a default that one caller
   overrides is the usual cause. The condition it guards then splits the check set in two.

5. **Confirm the branch path cannot fail the gate.** If the branch path's command excludes the
   test tier or omits the threshold step entirely, then the branch's green status carries no
   information about that gate, and the defect has been invisible to every ordinary signal.

6. **Reproduce the stricter invocation locally.** Run the release path's command, in the same
   environment the release job uses, and read the failing check's output. This local run is the
   evidence that the defect is real and that the repair works. Expect it to be slow; budget for it.

7. **Repair the defect on a branch off the default branch.** Add the missing coverage rather than
   lowering the threshold: the uncovered code is usually correct defensive logic, and the defect is
   the missing test. Lowering a floor to make a gate pass is a validation bypass.

8. **Land the repair on the default branch first, then re-cut the tag on the fixed commit.** A tag
   placed on the still-defective commit reproduces the identical failure. Delete the old tag and
   create a new annotated signed tag on the merge commit.

9. **Verify the publish job ran rather than skipped.** Read the re-triggered run's job conclusions
   and confirm the publish job reports success. A green run whose publish job is skipped is not a
   successful release.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Cited the default branch's green required checks as release readiness | Read the branch path's green run and concluded the release path would pass | The branch path runs a marker-filtered fast tier with no coverage step, so it never evaluated the coverage floor the release path enforces | A green result transfers only between identical invocations. Compare the actual commands on both paths |
| Re-ran the failed tag-triggered run expecting a different outcome | Re-ran the failed job on the same tagged commit | The run executes the same stricter invocation against the same commit, so it fails identically | Re-running cannot clear a defect that lives in the tagged commit; land the fix, then re-cut |
| Planned to make the release path mirror the branch path's gate | Applied the neighbouring rule that a release must run the same gate the pull-request path enforces | That rule assumes the release path is the weaker one. Applying it here removes the coverage floor from every future release and weakens the guarantee | Mirror only when the release path is missing a gate the branch enforces. When the release path is stricter, repair the code |
| Read the run's top-level conclusion and stopped | Treated the run as an ordinary test failure | The failed gate skipped the publish job, so the artifact was never published while the run looked like a plain failure | Read the publish job's own conclusion; skipped means not published |
| Lowered the coverage threshold so the gate would pass | Relaxed the minimum so the release path went green | The uncovered code was correct defensive logic; the missing coverage was the defect, and a lowered floor is a validation bypass that hides the next gap | Add the missing tests. Never trade a floor for a green release |
| Waited for the branch to go red to confirm the defect | Expected the default branch to fail the gate once the code was understood | The branch path never runs that gate, so the branch stays green indefinitely and provides no signal | A gate only one path runs cannot be expected to signal on the other path |

## Results & Parameters

**The divergence to look for:**

| Question | If the answers differ, the green signal does not transfer |
| -------- | ---------------------------------------------------------- |
| Which reusable-workflow inputs does each path pass, and what are the defaults? | One path overrides an input that changes the check set |
| Which command does each path run for the shared job name? | Identical job names can hide different commands |
| Does one path omit a step the other runs? | An omitted threshold cannot fail on the path that omits it |
| Does one path filter the test set with a marker exclusion? | The excluded tier's modules are never measured on that path |

**Repair direction, chosen by which path is stricter:**

| Situation | Correct repair |
| --------- | -------------- |
| Release path is missing a gate the branch enforces | Add the gate to the release path, reusing the already-wired publish-gating job |
| Release path is stricter than the branch path | Fix the defect the stricter gate exposed on the branch; do not weaken the release path |
| The difference was accidental | Make the branch path run the same stricter invocation |
| The difference was deliberate | Leave both workflows alone; fix the code |

**Expected outcome of the repair:** the stricter invocation passes locally on the fixed commit, the
re-cut tag's run clears every required job, the publish job reports success rather than skipped,
and the artifact becomes visible in the registry.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| Multi-skill plugin release | Tag-triggered publish run against a branch whose required checks were green | The branch path ran a fast test tier with no coverage step, while the release path ran the full suite under a per-file branch-coverage floor. The release run failed the floor on one helper module, and the downstream publish job was skipped rather than failed, leaving the package unpublished while the branch stayed green. The floor was raised to the required value by adding behavior tests for uncovered defensive paths, the repair landed on the branch first, the tag was re-cut on the fixed commit, and the re-triggered run cleared every required job with the publish job running instead of skipping. **verified-local** for the repair and the re-triggered run; the environment reviewer gate was still pending at capture time. |

## References

- `ci-release-pipeline-must-mirror-required-pr-gate` — the opposite direction: the release path is missing a gate the pull-request path enforces. Read it before adding a gate to a release path; do not apply it when the release path is already stricter.
- `release-tag-drift-recut-on-fixed-commit` — the tag-scoped variant, where a version-currency guard fails only on a tag-triggered run. It covers the re-cut mechanics this skill defers to.
- `pytest-coverage-threshold-and-enforcement` — the mechanics of raising a floor with targeted branch tests rather than by relaxing the threshold.
- `ci-hygiene-and-validation-gates` — the broader convention for CI guards that pass without enforcing their intended invariant.
