---
name: peer-rewrote-pr-head-orphaned-push
description: "Recover when concurrent agents share one pull-request branch and a peer force-pushes over or merges from an older commit than your reviewed head. Use when your pushed fix is missing from the remote branch, the remote head is not a descendant of your commit, a PR label changed to a blocking state after your review, or another agent claimed the same PR before your push. Also use before a coordinator assigns a second background agent to a branch that a first agent may still write."
category: tooling
date: 2026-11-10
version: "1.1.0"
user-invocable: false
tags: [single-writer, task-stop, coordinator, parallel-agents, shared-branch, force-push, head-orphaned, push-rejected, stale-lease, merge-from-older-head, claimed-pr, pr-stack, follow-up-pr]
---

# Peer Rewrote the PR Head: Keep the Work, Do Not Reprint the Push

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-02 |
| **Objective** | Keep a reviewed fix that a concurrent agent removed from a shared pull-request branch, without a push race, a duplicate review, or lost work. |
| **Outcome** | Operational. Three such rewrites were observed in one session. Two ended as a recovered follow-up pull request. One ended as a review comment on the peer's head, because that peer had claimed the pull request. |
| **Verification** | verified-local (two follow-up pull requests opened and one comment posted this session) |

## When to Use

- Several agents push to one pull-request branch, and your reviewed commit is not an ancestor of the remote head.
- A leased push fails with `stale info` or a "cannot fast-forward" hint after you fetched only minutes before.
- A merge landed from an older head of your own branch, so the merged tree lacks a fix that your local work contains.
- Another agent posted a claim on the pull request or set a blocking state label after your review, before your push.
- You are a coordinator and will hand the same branch or pull request to a second background agent, or you told an agent by message to stop pushing.
- You must decide between a force push to restore your commit, a rebase, or a separate pull request.

## Verified Workflow

### Quick Reference

```bash
# 1. Read the remote before any write. A branch can be deleted or rewritten.
git fetch origin <branch>; git log --oneline -5 origin/<branch>
git merge-base --is-ancestor <your-commit> origin/<branch> && echo "mine is in" || echo "mine is orphaned"

# 2. Read the pull request and the claim record. Do not write to a claimed branch.
gh pr view <PR> --json state,headRefOid,labels,mergedAt,mergeCommit

# 3. Compare your commit to the merged head by content, not by identity.
git diff --stat <your-commit> <merged-head>

# 4. Recover on the current default head when the pull request is merged.
git branch <rescue> <your-commit>
git rebase --onto origin/main <old-base> <rescue>

# 5. Push only with a lease bound to the head you read.
git push --force-with-lease=<branch>:<expected-head> origin HEAD:<branch>
```

Rule: **a missing commit is evidence, not a failure to retry.** If the remote head is not a descendant of your commit, your push did not apply. Find out who moved the head before you push again.

Rule: **a claim or a blocking label ends your write authority on that branch.** Publish the remaining delta where the owner can read it: a review comment with a patch, or a follow-up pull request against the default branch.

### Prevent It: One Writer per Branch

A message does not cancel a command that is already running. A first agent told to stop can still land a queued push, which overwrites the second agent's head. Two heads then exist and one agent's work is lost. Before you assign a second writer:

1. Stop the first agent process itself with the task-stop control. Do not rely on a stop message.
2. Confirm its worktree has no running git process (check the process table for that worktree path).
3. Re-read the remote head and confirm it did not change after the stop.
4. Record that head object ID. The second agent starts from it.
5. Give the second agent a pinned push: `git push --force-with-lease=<ref>:<expected-oid>`.

Allow one writer per branch at a time. All other agents on that branch are read-only. Read-only reviewers can run in parallel with the writer.

### Suggested Approach

1. **Check ancestry, not just the branch name.** A push that reports success once does not stay published. Re-read the remote before every later write, including a push to the same branch that you pushed one commit earlier. `git merge-base --is-ancestor <your-commit> origin/<branch>` is the authority.

2. **Read the merge path, not only the head.** When a pull request into a feature branch is merged, the merge commit names the head that landed. That head can be older than the reviewed head. Compare your commit to the merged commit: an empty `git diff --stat` means the content landed and only the identity moved. A non-empty diff means a fix is lost and needs a route of its own.

3. **Confirm the owner of the branch before you force it.** Read the pull-request labels, the latest comments, and the timeline. A peer comment that claims the fix, or a state label that blocks implementation, is a handover. Do not force-push a peer's history to restore your commit. When the requirement is still open, send the delta as a comment with the exact patch and the test that proves it. When the pull request has merged, open a follow-up.

4. **Rebase the orphaned commit onto the current default head.** Replay with `--onto` so only your commit moves. Resolve conflicts by keeping the merged form of a hunk that an equivalent peer fix already made; do not re-apply a change that the default branch contains in another shape. Re-run the affected tests and the linter on the rebuilt branch before you publish.

5. **Re-sign after a rewrite.** A cherry-pick or a rebase preserves the message but can drop the signature. Confirm `git log --show-signature -1` shows a good signature before the push.

6. **Use the lease as a compare-and-swap.** `--force-with-lease=<branch>:<sha>` fails when the remote moved, and that failure is correct: another agent wrote during your work. Fetch and re-read instead of pushing unguarded.

7. **Report the split, not a single "done".** State which requirement reached the default branch, which reached the feature branch behind it, and which is still open. The next agent needs the open requirement more than the closed one.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Tell the first agent by message to stop, then start a second writer | Delegated fixes for one pull request to a second background agent while the first might still run | The message did not cancel a running command; the first agent's queued push landed and overwrote the second agent's head | Stop the process, verify no git process and an unchanged remote head, then pin the second writer's lease |
| Push the reviewed commit to the branch that received it before | Re-ran the same branch push after more review fixes | The peer had rewritten the branch, and the remote reported the branch as deleted or advanced | A prior successful push to a branch does not grant later write access; re-read the remote first |
| Merge from the newest head of your own branch | Merged a feature-branch pull request and expected the merge to carry the newest commits | The merge used an older head, so the reviewed fix was absent from the merged tree | The merge picks a head; verify the merged commit contains your commit before you clean up |
| Force-push to restore the orphaned commit | Rebased locally and pushed with a lease | The lease was stale, and the peer had claimed the same branch with a review round | A stale lease after a claim is a stop signal, not a retry signal |
| Deduplicate a log that re-checked a record | Added a `note=False` flag to suppress a duplicate event | A direct caller that skips the loader depended on the event, and its test failed | Fix a duplicate only when every caller path keeps the behavior; otherwise record why the duplicate stays |

## Results & Parameters

### Configuration

```yaml
head_verification:
  before: [push, force-push, branch-delete, worktree-remove]
  probe: git merge-base --is-ancestor <your-commit> origin/<branch>
merged_head_audit:
  compare: git diff --stat <your-commit> <merged-commit>
  empty: content landed; identity moved
  non-empty: recover the delta
single_writer:
  before_second_writer: [task-stop-first-agent, no-git-process-in-its-worktree, remote-head-unchanged, record-head-oid]
  second_writer_push: --force-with-lease=<ref>:<expected-oid>
  parallel_ok: read-only-reviewers
write_authority:
  cleared_by: [peer-claim-comment, blocking-state-label, branch-deleted]
  then: review-comment-with-patch, or follow-up-pr-against-default
force_push:
  form: --force-with-lease=<branch>:<expected-head>
  on_failure: fetch, re-read the owner, do not retry blind
```

### Expected Output

- The orphaned commit is rebased onto the current default head, signed, and green on the affected tests.
- A follow-up issue and pull request carry the lost fix when the original pull request has merged.
- A review comment with an exact patch and a test replaces a force push when a peer owns the branch.
- The report names each requirement the default branch has and has not received.

## Verified On

| Project | Context | Details |
| --------- | --------- | ------- |
| Comet (LLM360) | Three concurrent-agent rewrites of two pull-request branches in one session | Merge and recovery detail in [peer-rewrote-pr-head-orphaned-push.notes.md](peer-rewrote-pr-head-orphaned-push.notes.md) |

## References

- [mid-drive-peer-completion-audit.md](mid-drive-peer-completion-audit.md) — the sibling for a peer that completes or advances an artifact while you drive; this skill covers a peer that removes your commit from an open branch.
- [shared-token-agent-identity-claim-coordination.md](shared-token-agent-identity-claim-coordination.md) — claim, attribution, and stand-down rules for a shared forge credential.
- [automation-review-loop-unpushed-fix-oscillates.md](automation-review-loop-unpushed-fix-oscillates.md) — the inverse persistence case: your fix was never pushed; here it was pushed and then rewritten.
- [git-stacked-prs-rebase-merge-worktree-orchestration.md](git-stacked-prs-rebase-merge-worktree-orchestration.md) — stacked-pull-request rebases when a base commit and a branch are rewritten.