---
name: mid-drive-peer-completion-audit
description: "Reconcile live forge state against a stale snapshot while driving an issue-to-merge queue that parallel lanes also work. Use when: (1) your queue map or status snapshot is minutes-to-hours old and the repository moves under you, (2) a peer lane can complete a review round or merge on your PR while you wait, (3) you must decide between redoing and auditing-plus-finishing leftover bookkeeping, (4) more than one review process can race on one PR, (5) a plan decision table can make a merged PR partial so the issue must stay open, (6) a single-PR directive carries a mergeability premise captured at issuance (conflicting state, red checks) and a peer may have delivered the whole task before you start."
category: tooling
date: 2026-10-31
version: "1.2.0"
license: BSD-3-Clause
user-invocable: false
tags: [parallel-lanes, stale-snapshot, peer-completion, adopt-pr, refs-vs-closes, partial-scope, label-hygiene, review-race, immutable-artifact, lane-record, rebase-audit, force-push-timeline, zero-delta]
---

# Mid-Drive Peer-Completion Audit

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-25 |
| **Objective** | Drive an issue-to-merge queue to completion in a repository that parallel lanes share, without redoing delivered work, losing leftover bookkeeping, or forcing wrong closure state. |
| **Outcome** | Operational. A three-issue queue completed with every PR merged. Peers completed exchange rounds or merges on all three PRs mid-drive. Each takeover was audited against the live forge instead of redone; the one bookkeeping step peers skipped (the issue-label swap, on two of three issues) was finished after the audit; one issue was correctly kept open as partial scope per its plan decision table. A later single-PR pickup verified a peer's complete delivery of its directive (zero-delta takeover) and stopped without a second mutation. |

## When to Use

- You drive a serial or small-concurrency issue queue and other lanes work the same queue or adjacent queues in the same repository.
- Your orders or status snapshot came from a coordinator minutes to hours ago; treat it as stale the moment you receive it.
- A directive for one PR (a rebase, a check repair, or a report task) carries a forge-state premise captured at issuance, such as "conflicting against the default branch" or "checks are red".
- You hold a durable approval label delivered at an older head, and the head may have moved after delivery.
- Review exchanges on your PRs run as background processes that peers or earlier sessions can also start.
- An approved plan contains a decision table that can make a merged PR partial (the issue must not auto-close).
- You must label, merge, clean up, or report against artifacts whose state you did not verify in the last few minutes.

## Verified Workflow

### Quick Reference

```bash
# Fresh read before EVERY mutation. A coordinator snapshot decays within hours.
gh pr view <PR> --json state,mergedAt,mergeCommit,headRefOid,labels,reviews
gh issue view <N> --json state,labels

# Peer completed your exchange? Compare heads before you conclude:
gh api repos/<owner>/<repo>/compare/<your-head>...<merge-commit> \
  --jq '{ahead: .ahead_by, behind: .behind_by, files: [.files[].filename]}'

# Find every PR that references the issue, all states, not only open:
gh pr list --state all --search "<issue-number> in:body,title" \
  --json number,state,mergedAt,mergeCommit,headRefName

# Directive premise says a PR needs a rebase? Test the premise at the live head first:
git fetch origin main <pr-branch>
[ "$(git merge-base origin/main <pr-branch>)" = "$(git rev-parse origin/main)" ] \
  && echo "branch is already based on the current default head"

# Did a peer force-push the head after the approval label?
gh api graphql -f query='{ repository(owner:"<owner>", name:"<repo>") { pullRequest(number: <N>) {
  timelineItems(itemTypes:[HEAD_REF_FORCE_PUSHED_EVENT, LABELED_EVENT], first: 50) {
    nodes { __typename
            ... on HeadRefForcePushedEvent { createdAt }
            ... on LabeledEvent { createdAt label { name } } } } } } }'
```

Rule: **redo never; audit, then finish the leftovers.** When a peer delivered or advanced the artifact, your remaining work is the delta between the delivered state and your contract — usually a few bookkeeping steps, not the implementation. When the delta is empty, the audit ends in a takeover report and a stop, not in a repeat mutation.

### Suggested Approach

1. **Re-read before every mutation.** Before a label swap, a merge, a review round, or a cleanup delete, take a fresh read of the PR and the issue. In one measured drive, a snapshot one hour old was wrong on all three queue items: one PR had advanced by a repair commit, one PR was already merged, one PR existed from a prior session the directive did not know about.
2. **Audit a peer completion instead of redoing it.** When a peer completes your review round or merge: bind the merged head and your head; compare content (`git compare` or file lists at both trees); verify forge coherence (merge commit reachable from the default branch, review carrier bound to the exact head, milestone, labels). Then enumerate the exchange's post-GO steps and check each one. In the measured drive, the issue-label swap was the step peers skipped on two of three issues — cheap to finish, invisible if you do not look. When one actor produced review and merge in the same round, record the reviewer-independence gap in the report; do not rerun the exchange to manufacture independence after merge. When you regenerate published diff or digest evidence, first match the publisher's documented command flags: a mismatch under different flags is a flags mismatch, not a content mismatch, and must not be reported as tamper evidence.
3. **Leave duplicate reviewers to the publication guard.** More than one review process can target one PR: yours, a prior session's, a peer lane's. Do not kill processes you cannot attribute — a killed foreign reviewer can still be mid-delivery. Delivery-on-exact-head guards withhold publication once the artifact is immutable (merged), and reviewers read from their own snapshots, so branch and worktree cleanup is safe while they run. Checking that a running reviewer reads from its own snapshot directory, not your worktree, is the precondition for cleanup.
4. **Keep a partial-scope issue open on purpose.** When the plan's decision table makes the merged PR partial, the PR body references the issue (`Refs`), and closure is wrong even though a review GO exists. Retain the plan-state label (the remaining scope is the same approved plan), post a lane-record comment naming the decision-table row that landed, what shipped, and what remains, and escalate the disposition (continue the same plan versus re-plan) to the coordinator. Do not switch the body to `Closes` to make a board row look finished — the forced close loses approved remaining scope and misreports the release.
5. **Clean up only with bound evidence.** After a squash merge, the lane branch's commits are not ancestors of the default branch; branch deletion is justified by merge evidence (merge commit, PR state), and worktree removal is justified by rule 3's snapshot check — never by branch name or a zero-ahead count.
6. **Test a task premise, then stop on a zero-delta takeover.** A single-task directive can arrive after a peer lane delivered it without a claim post. Verify the premise at the live forge before the first mutation: a rebase task is already done when `git merge-base <default> <head>` equals the default-branch head, and the PR timeline shows the peer's force-pushes after the approval-label timestamp. The forge mergeability field and a directive premise can each be stale; merge-base equality is the authority for "already based on the current default head". A rebased PR has no merge commit, so merge-base equality — not a compare against a merge commit — is the content-binding probe. Then audit the peer's handover comment (old head, new head, conflict resolutions, check claims) against the live forge: checks at the new head, the label retained, mergeable state, auto-merge state. If every contract step is delivered, including the report, the delta is empty: do not re-run the mutation to produce deliverables. A second rebase changes the head again, invalidates the peer's green checks, and duplicates the report. Report the takeover evidence (old head, new head, checks, label coverage) to your coordinator and stop. State in the record that an approval label delivered at the old head does not cover the new head, even while the label stays on the PR.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Act on a received status snapshot | Proceeded to author-response steps from a directive's state summary | The PR had already advanced one head and changed review state during the gap between snapshot and action | Fresh-read the forge immediately before each mutation; the snapshot is a hint, never state |
| Trust the merge to complete the exchange contract | Assumed a merged PR implies all post-GO steps ran | The issue-label swap had never executed on two of three merged items | On any takeover or adoption, enumerate the pipeline's post-GO steps and verify each one — merges complete code, not bookkeeping |
| Rely on the dispatch-time keyword rule alone | The partial-fix keyword rule (`Refs`, not `Closes`) was applied in the PR body, with no follow-up bookkeeping | The issue kept its full-scope plan state with no record of what remained; a later lane could not tell deliberate openness from abandonment | The keyword is half the rule; the issue-side record (lane-record comment, retained plan label, escalated disposition) is the other half |
| Act on a directive's mergeability premise | Accepted "this PR is conflicting and cannot merge" as current state and prepared the assigned rebase | The premise was minutes stale: a peer worker had already rebased onto the then-current default head, force-pushed twice, repaired the branch-caused check failures, and posted the required handover report; a redo would have changed the head again and duplicated the report | A directive premise is a claim, not state: prove it with merge-base equality plus the force-push timeline; when the audit delta is empty, verify the handover, report, and stop |

## Results & Parameters

### Configuration

```yaml
fresh_read_before: [label-swap, merge, review-round, cleanup-delete]
takeover_audit:
  - head-content-comparison          # your head vs the peer's merged head
  - forge-coherence                  # merge on default, exact-head carrier, labels
  - post-go-step-checklist           # label swap, auto-merge arm, closure keyword
  - independence-gap-record          # one-actor review+merge rounds go in the report
  - evidence-flag-reproduction       # match the publisher's documented flags before calling a digest mismatch
duplicate_reviewers: leave-to-publication-guard   # never kill unattributed processes
partial_closure:
  pr_body: "Refs #N (per the plan decision table)"
  issue: stays open; plan-state label retained; lane-record comment required
  disposition: escalate to the queue coordinator
cleanup_preconditions:
  branch_delete: merge commit bound and PR state MERGED
  worktree_remove: no live review process reads the worktree (check snapshot dirs)
directive_premise_check:          # at pickup, before the first mutation
  - merge-base-equality           # branch base == current default head proves "already rebased"
  - force-push-timeline           # head force-pushes vs the approval-label timestamp
  - handover-verification         # peer report claims vs live checks, labels, mergeable state
zero_delta_takeover: no second mutation; report old head, new head, checks, label coverage; stop
approval_label_coverage: binds to the exact delivery head; a rebase voids coverage while the label remains
```

### Expected Output

- Zero re-implemented work and zero competing PRs for an intent a peer delivered.
- Every merged item's post-GO checklist verified or finished, with readbacks.
- A directive with a false premise ends as a verified zero-delta takeover report, not as a second mutation.
- Reviewer-independence gaps recorded where a peer round collapsed review and merge into one actor.
- Partial-scope issues stay open with a lane-record comment and an escalated disposition.
- Lane branches and worktrees removed only against merge and snapshot evidence.

## Verified On

List the projects in which you tested this skill:

| Project | Context | Details |
| --------- | --------- | --------- |
| Large shared monorepo under a many-lane release wave | Serial drive of a three-issue queue, 2026-10-25; peers completed rounds or merges on all three items | Measured pass detail in [mid-drive-peer-completion-audit.notes.md](mid-drive-peer-completion-audit.notes.md) |
| Large shared monorepo under many-lane operation | Single-PR rebase-directive pickup, 2026-10-31; a peer had delivered the full contract about 30 minutes earlier | Zero-delta takeover detail in [mid-drive-peer-completion-audit.notes.md](mid-drive-peer-completion-audit.notes.md) |

## References

- [ambient-partial-clone-lazy-fetch-read-hazard.md](ambient-partial-clone-lazy-fetch-read-hazard.md) — ambient read pricing while you audit: a partial checkout turns read-heavy commands into silent network I/O; keep bulk reads on an explicitly acquired immutable source.
- [shared-repo-interruption-yield-to-peer-pr.md](shared-repo-interruption-yield-to-peer-pr.md) — the resume-after-interruption sibling: inventory peer deliveries before redoing prepared work. This skill covers the active-drive case: the peer advances your artifact while you work.
- [stale-plan-already-resolved.md](stale-plan-already-resolved.md) — the premise-still-reproduces sibling for defect and plan artifacts; this skill adds the peer-completion branch of the same stale-premise family.
- [hephaestus-interrupted-implementation-lane-recovery.md](hephaestus-interrupted-implementation-lane-recovery.md) — salvage when a lane stopped before first publication.
- [parallel-agent-swarm-dispatch-patterns.md](parallel-agent-swarm-dispatch-patterns.md) — dispatch-time keyword rule (`Refs` for partial fixes); this skill adds the issue-side bookkeeping that must follow the merge.
- [github-pr-review-record-void-repair.md](github-pr-review-record-void-repair.md) — repair of an already-published review carrier; the publication guard that withholds post-merge delivery is the safe side of the same boundary.
