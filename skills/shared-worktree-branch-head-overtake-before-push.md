---
name: shared-worktree-branch-head-overtake-before-push
license: BSD-3-Clause
description: "Rebind to the live head before you push a fix that you made in a shared review worktree, and re-publish a verdict that named a head which a peer publisher has advanced past. Use when an unpredictable reset discards your uncommitted edits, when another writer's in-flight change appears in your staging, or when the branch head moves after you post a head-bound verdict."
category: tooling
date: 2026-11-07
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - git
  - shared-worktree
  - multi-agent
  - branch-head-overtake
  - git-add-all
  - peer-publisher
  - verdict-supersession
  - head-bound-verdict
  - push-lease
  - rebind-before-push
  - concurrent-writer
  - review-delivery
---

# Shared Worktree: Rebind to the Branch Head Before Push

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-07 |
| **Objective** | Publish a fix and a head-bound verdict from a shared review worktree without racing another publisher, and keep the published record correct when the branch head moves after publication. |
| **Outcome** | Successful. The rebind rule and the verdict re-publication rule were applied in the captured session, verified-local. |

## When to Use

- Another publisher, not a version-control operation that you ran, advances a branch head that your worktree tracks. The worktree then replaces your uncommitted edits with the new head. This can occur more than once in one session.
- A reset repeats after a second attempt to leave the same uncommitted edits. Each attempt to hold uncommitted work loses the same work.
- You ran one stage command that matched every dirty path, and a diff or a commit summary contains files that you did not edit.
- Your review contract binds the verdict and the merge label to one exact head. Another writer advances the head after you publish.

## Verified Workflow

### Quick Reference

```bash
# Rebind to the live head before you edit, after an unexpected reset.
git rev-parse HEAD
git ls-remote origin refs/heads/<branch>      # remote head, not only the local ref
git status --short

# Publish atomically: apply edits, commit, and push in one command chain.
git add <your files> && git commit -S -s -F <message-file> \
  && git push origin HEAD:refs/heads/<branch>

# Confirm what other writers added on top of your commit.
git log --oneline -4

# When the head moves after your verdict, post one short addendum that names the new head.
```

### Suggested Approach

1. Treat the branch head as a value that another writer can change at any moment. Read `git rev-parse HEAD` before you edit, before you stage, and immediately before you push. Read the remote head with `git ls-remote`, because a local ref can lag.
2. Confirm that your edit is still on disk. Use `git rev-parse HEAD` to compare with the head that you read before the edit. If the head changed, re-apply the edit on the new head.
3. Do not retry a lost edit by holding it uncommitted for longer. Re-apply and publish in one command chain. A separate edit turn that compiles, lints, and runs tests is a window in which the reset can occur again.
4. Stage explicit paths for your own edits. Do not use one command that matches every dirty path. When a stage command already included a foreign change, inspect the extra files before you decide what to do:
   - Read the extra diff. If it is a coherent inactive change for the same intent, and the test evidence covers the combination, keep it and state that in the record.
   - If it disagrees with your fix, or has no evidence, remove it from your commit and tell the owner. Do not push work that you cannot justify.
5. Use a fast-forward push with no force. If the push is rejected because the remote moved, fetch, re-integrate your change on the new head, and push again. Do not rewrite the shared history.
6. After a version-control command that matched too many paths, verify the scope with `git show --stat <commit>`. Compare every path with your edit list.
7. When the head moves after you publish a verdict that names the head, post one brief addendum. Name the new head. State which of your records still apply: test evidence that no code change affects, and label conditions that the new head changes. Do not restate the full verdict.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | --------------- |
| Keep the fix uncommitted across a lint and test run | Edited the target files, then ran lint and a long test batch with the changes still only in the working tree | The worktree was reset to a new head that the branch received from another publisher during the run. Both the edits and the run became invalid. The reset occurred twice. | Rebind to the live head before the edit, then apply, commit, and push in one chain. Commit the large verified portion before you start more work. |
| One stage command for every dirty path | Ran a command that matched every path in the working tree, then committed and pushed | A peer's in-flight change for the same finding was in the tree. The commit then contained files that this review did not write. The pushed head failed lint because the foreign change was not complete. | Stage the exact paths of your own edits. After a broad stage, read `git show --stat <commit>` and reconcile each extra path before the record claims the commit. |
| Report the verdict, then rely on the head identifier | Posted a verdict that named one head, then continued to read the branch | The branch received a new commit after the post. The published head no longer matched the branch. | Keep the verdict as issued. Post one addendum that names the new head and the records that continue to apply. |

## Results & Parameters

### Configuration

- `git rev-parse HEAD` and `git ls-remote origin refs/heads/<branch>`: read both before each write decision.
- No force push. A rejected push means the remote advanced. Integrate on the new head and push again.
- Stage explicit paths. Never use a command that matches every dirty path in a shared worktree.

### Expected Output

- The published commit contains only the paths that you can justify, and the branch head matches the published identifier.
- The verdict record names a head and has one addendum when the branch moves.
- Each reset is noticed before you write again. You lose no work that was not already pushed.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Comet | Pull-request review in a shared review checkout | The worktree was reset twice to a peer head, which discarded uncommitted fixes. A broad stage included a peer's partial fix in the pushed commit. The head then advanced after the verdict was posted. The rebind rule and the addendum rule were applied. verified-local. |

## References

- [Stage only your own files in a shared worktree](tooling-stage-only-your-own-files-in-shared-worktree.md)
- [Preserve foreign uncommitted changes in a shared checkout](shared-checkout-foreign-working-tree-changes.md)
- [Shared checkout: unstable ref reads](shared-checkout-unstable-ref-reads.md)
- [PR review head-bound check evidence](github-pr-review-head-bound-check-evidence.md)