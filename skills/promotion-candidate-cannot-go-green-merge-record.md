---
name: promotion-candidate-cannot-go-green-merge-record
description: "Merge a red pinned-candidate promotion pull request on the record when every failing check is attributed to a failure class that cannot pass on that branch, then rebase and merge the dependent promotion immediately. Use when: (1) a promotion pipeline pins a content-addressed candidate so a promotion branch is structurally frozen, (2) the candidate umbrella gate stays red only on classes whose root cause was cured on the source branch after the pin, (3) an operator directs a force or admin merge instead of close-as-read or supersession, (4) a dependent promotion must land on the new base tip in the same sequence, or (5) lineage claims must survive a later base rewrite."
category: ci-cd
date: 2026-10-23
version: "1.0.0"
user-invocable: false
verification: verified-ci
license: BSD-3-Clause
tags: [promotion, pinned-candidate, content-addressed, force-merge, admin-merge, explained-failure, incurable-on-branch, red-gate, rebase-dependent, first-parent-lineage, squash-merge, supersession, verified-ci]
---

# Promotion Candidate That Cannot Go Green: Merge on the Record, Then Land the Dependent

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-23 |
| **Objective** | Deliver a structurally red promotion candidate without a false green claim, and move the dependent promotion forward in the same sequence. |
| **Outcome** | Successful. A gate-observation promotion whose failures were incurable on its branch merged on a written failure-attribution record; the dependent release-pinned promotion was rebased and merged minutes later. The transient squash merge did not survive on first-parent history; the host merge record, the analysis comment, and the promoted tree did. |
| **Verification** | verified-ci: the merge sequence and the afterwards lineage checks ran against the live repository records; cited commits were checked with ancestry queries, not branch listings. |

## When to Use

- A promotion pipeline pins a content-addressed candidate: the branch name or
  trigger contract binds the candidate commit, so the promotion branch is
  structurally frozen. A rerun, retry, or edit cannot change what is tested.
- The candidate umbrella gate stays red only on failure classes whose root
  cause was cured on the source branch after the candidate was pinned. The
  candidate pins pre-cure vintage, so these checks cannot pass on this branch.
- Every failing check is attributed in writing on the pull request: a named
  failure class, the curing change, and why the class does not block
  production behavior.
- An operator directs the merge despite the red umbrella (force or admin
  merge), instead of the default close-as-read or supersession.
- A dependent promotion must land on the new base tip immediately after this
  merge.
- You must make lineage claims about any merge in the sequence after later
  base movement.

Do not use this skill when any failing check is unattributed, explained only
as "probably flaky", or a behavior regression. Do not use it without explicit
merge authority from the operator. Do not use it when the dependent candidate
pins a commit older than the cure commit: supersede it with a candidate at or
after the cure instead.

## Verified Workflow

### Quick Reference

1. Attribution completeness: the count of failing checks equals the sum of
   the checks in the attributed classes. One unexplained failure stops the
   sequence.
2. Record on the pull request, before any merge: each failing check, its
   class, the curing change on the source branch, why this branch cannot
   pass, and the merge recommendation.
3. Merge the observation candidate with the repository ceremony for a
   reviewed-but-red candidate (admin or squash merge). Do not rerun
   known-incurable shards to confirm them again.
4. Rebase the dependent promotion onto the new base tip and merge it
   immediately. A content-addressed promotion branch keeps its identity
   through the rebase: the branch binds the candidate commit, not the base.
5. Verify lineage by ancestry queries, not by branch listings. A squash- or
   force-merged observation commit can be reset away when the base moves
   again. Run `git merge-base --is-ancestor <oid> <base>` before you cite a
   merge as a lineage ancestor. Cite the host merge record and the commit
   object identity, never a moving branch tip.

### Suggested Approach

1. **Classify the third gate state.** A frozen candidate has three states,
   not two: green, red-and-fixable, and red-and-incurable-on-branch. The
   third state is the one where the root cause merged to the source branch
   after the pin. The correct actions for the third state are:
   merge-on-record, close-as-read, or supersede with a candidate at or after
   the cure commit. Driving the branch green is not an option by
   construction, so do not schedule more runs on it.

2. **Apply the class test to each failure.** A failure class is usable for
   the record only when it names the root cause, shows an error-to-pass
   reproduction on the curing change, and has a non-production boundary.
   Fixture drift, environment pins, and superseded-runner artifacts qualify.
   Behavior regressions and unattributed errors do not. For the stale-run
   variant of a red rollup, see
   [ci-required-checks-gate-superseded-run-false-failure](ci-required-checks-gate-superseded-run-false-failure.md).

3. **Keep merge authority explicit.** Tool-side authorization stays
   fail-closed: a merge helper must refuse to merge without trustworthy
   current check evidence; see
   [github-merge-current-checks-only-fail-closed](github-merge-current-checks-only-fail-closed.md).
   The operator decision is the attested override of the umbrella result, and
   the written pull-request record is the override evidence. The record must
   exist on the pull request before the merge so the host keeps it with the
   merge event.

4. **Sequence the dependent promotion in the same operation.** Rebase the
   dependent promotion branch onto the new base tip and merge it while the
   gate reading is fresh (minutes, not days). A dependent that stays open
   longer must be rebound to the current base and re-read against any new
   failure inventory. For the general dependent-branch mechanics, see
   [git-stacked-prs-rebase-merge-worktree-orchestration](git-stacked-prs-rebase-merge-worktree-orchestration.md)
   when the host permits only rebase merges.

5. **Bind lineage claims to object identity.** A squash or force merge can
   land on the base and later be replaced by the dependent-merge
   choreography: the observation merge commit is then no longer an ancestor
   of the base, although the host still shows the pull request as merged.
   `git log --first-parent` and `git branch --contains` answer the wrong
   question after such a rewrite. Use `git merge-base --is-ancestor` against
   the current base reference, and cite the pull-request number and the
   commit object identity from the host merge record.

6. **Record completion by evidence.** The sequence is complete when both
   pull requests show a merged state with their records, the promoted tree
   is present at the base tip, and the ancestry verification result is
   written down. Any step whose tool is unavailable gets a recorded gap, not
   a skipped claim.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Drive the frozen branch green with more runs | Considered rerunning the red shards on the pinned candidate; rejected before execution by the attribution record | The root cause pre-dates the pin; no run of that branch can pass those checks | For the incurable-on-branch state, reruns burn CI budget and delay the dependent promotion. Spend the same effort on the attribution record |
| Cite the observation merge from a branch listing after the dependent had landed | Read the base first-parent history to confirm the observation merge was an ancestor | The transient squash merge had been replaced by the dependent merge choreography; ancestry query answered NO for the recorded merge object | After a base rewrite, only `git merge-base --is-ancestor` against the current base and the host merge record answer lineage correctly. Branch listings and merge state disagree |

## Results & Parameters

### Configuration

```yaml
inputs:
  observation_pr: <observation-promotion-pr>
  base_branch: <deployed-base-branch>
  failing_classes: [{class: <name>, checks: <count>, cure: <change-identity>}]
  dependent_pr: <dependent-promotion-pr>
  merge_method: <admin-or-squash-per-repository-ceremony>
outputs:
  observation_merge_record: <host-record-and-commit-oid>
  dependent_merge_record: <host-record-and-commit-oid>
  lineage_verification: <ancestry-query-command-and-result>
```

### Expected Output

- One merged observation pull request that carries the failure-attribution
  record.
- One merged dependent promotion on the new base tip, minutes later.
- A recorded ancestry check for each cited merge object against the current
  base.
- No claim that a transient merge commit survives on first-parent history
  without an ancestry result.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Internal multi-model inference-serving platform | Pinned-candidate production promotion pipeline; gate-observation promotion merged on the record with one incurable failure class; dependent release-label promotion rebased and merged in the same operation; transient merge verified absent from first-parent history by ancestry query | See [notes](promotion-candidate-cannot-go-green-merge-record.notes.md). |

## References

- [github-merge-current-checks-only-fail-closed](github-merge-current-checks-only-fail-closed.md) — tool-side merge authorization stays fail-closed; the operator record is the override
- [github-auto-merge-ci-gating-merge-method](github-auto-merge-ci-gating-merge-method.md) — merge-authority layers and current-head check evidence
- [ci-required-checks-gate-superseded-run-false-failure](ci-required-checks-gate-superseded-run-false-failure.md) — distinguish real-but-incurable red from stale-run false red
- [git-stacked-prs-rebase-merge-worktree-orchestration](git-stacked-prs-rebase-merge-worktree-orchestration.md) — dependent-branch rebase mechanics for rebase-merge-only hosts
- [promotion-scope-branch-config-diff](promotion-scope-branch-config-diff.md) — promotion scope completeness from branch configuration diffs
- [live-hotfix-content-addressed-identity-rotation](live-hotfix-content-addressed-identity-rotation.md) — content-addressed identity constraints in the deployed lane
