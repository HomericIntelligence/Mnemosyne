---
name: git-workflow-rebase-worktree-signing
description: "Operate rebases, isolated worktrees, signed commits/tags, submodules, branch recovery, cherry-picks, stashes, and preservation-biased cleanup. Use for conflict resolution, stale bases, rejected signatures, parallel sibling branches, or uncertain branch/worktree state."
category: tooling
date: 2026-08-05
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
history: git-workflow-rebase-worktree-signing.history
tags:
  - git
  - rebase
  - worktree
  - signing
  - submodule
  - recovery
  - cherry-pick
  - stash
---

# Git Workflow: Rebase, Worktree, and Signing

## Overview

Preserve work first, isolate each branch, rebase from a verified upstream, resolve conflicts by
intent, and publish only signed commits with lease-protected updates. Treat cleanup as an audited
separate phase. A valid local signature is only one part of hosted verification: key, commit/tag
identity, account registration, and verified email must align.

Detailed case provenance is in
[git-workflow-rebase-worktree-signing.notes.md](git-workflow-rebase-worktree-signing.notes.md).
The complete superseded guide is in
[git-workflow-rebase-worktree-signing.history](git-workflow-rebase-worktree-signing.history).

## When to Use

- Rebasing a feature branch with non-trivial conflicts.
- Creating, syncing, or auditing one worktree per branch.
- Batch-rebasing disjoint sibling branches.
- A signed commit or annotated tag is rejected or shown as unverified.
- A registered public key still does not verify on the hosting service.
- Reconciling submodule commits and worktrees across branches.
- Recovering detached state, commits made on local main, or stale dirty worktrees.
- Salvaging portable changes from a rejected PR by cherry-pick.
- Resolving stash-pop conflicts without discarding either side.
- An implementation plan cites files or jobs missing from the branch.
- Auditing stale branches, worktrees, and stashes with a preservation bias.

## Verified Workflow

### 1. Audit state before mutation

```bash
git status --short --branch
git worktree list --porcelain
git branch -vv
git stash list
git remote -v
git fetch origin --prune
```

Record the current HEAD, upstream, dirty/staged files, worktree ownership, and remote default branch.
Do not discard, force-remove, or overwrite uncertain state. If local changes exist, inspect them and
either commit them on a preservation branch or stash them with an explicit message.

### 2. Detect a stale base before editing

When a reviewed plan cites a file, line range, or job absent from the branch, compare with current
upstream before declaring the plan wrong:

```bash
git rev-parse HEAD
git rev-parse origin/main
git log --oneline --left-right --cherry-pick HEAD...origin/main
git show origin/main:path/to/cited-file
```

If upstream contains the cited artifact, rebase first, then rediscover anchors. Never create a
parallel substitute for code that simply has not reached the stale branch.

### 3. Rebase one branch in its own worktree

```bash
git worktree add ../worktree-feature feature-branch
git -C ../worktree-feature rebase origin/main
```

On conflict:

1. read the commit being replayed with `git show REBASE_HEAD`;
2. read both sides in context;
3. preserve the feature's intent using current APIs and policy;
4. search for unresolved markers;
5. stage only resolved files and continue;
6. run the branch's required checks.

```bash
git diff --name-only --diff-filter=U
rg -n '^(<<<<<<<|=======|>>>>>>>)' .
git add path/to/resolved-file
git rebase --continue
```

Do not use a blanket “ours” or “theirs” rule. Those names also change meaning across rebase and
merge contexts. Resolve semantically.

Publish rewritten history only after checks pass:

```bash
git push --force-with-lease origin feature-branch
```

Never replace lease protection with an unconditional force push.

### 4. Parallelize only isolated branches

Create one worktree per sibling branch and assign non-overlapping ownership. Fetch once before
dispatch, but revalidate `origin/main` and branch heads before publishing. Do not let multiple
workers share an index, worktree, or branch.

Resolve a common conflict root on main first when repository policy allows; then rebase siblings.
Repeatedly hand-resolving the same generated or hook defect across branches creates divergence.

### 5. Diagnose hook failures after rebase

Distinguish a feature regression from a repository-wide hook that scans sibling worktrees or stale
paths. Reproduce the exact hook, inspect its discovery scope, and fix the authoritative guard on
main if the root cause is shared. Do not bypass required hooks or commit generated noise.

### 6. Align commit/tag signing identities

Hosted verification requires all four:

1. the object has a cryptographically valid signature;
2. the signing public key registered with the hosting account matches the full fingerprint;
3. the commit author/committer or tagger email matches a UID on that key;
4. that email is verified on the account owning the registered key.

```bash
git log -1 --show-signature --format=fuller
git tag -v vX.Y.Z
gpg --list-keys --with-colons
git config --get user.signingkey
git config --get user.email
```

Use the full fingerprint, not a short key ID. Export/register only the matching public key, then
read back the hosted key identity and email verification state. Re-sign the commit or recreate the
annotated tag only when the object identity is wrong; re-registering the same key cannot fix an
unverified email.

### 7. Recover common branch states

#### Commits accidentally made on local main

Create a feature branch at the current commit before changing main:

```bash
git switch -c recovery-feature
git status --short --branch
```

Publish and review that branch. Restore local main only after the work is preserved and with the
appropriate repository workflow; do not reset destructively.

#### Detached HEAD with useful commits

Create a named branch at the current commit, then inspect its divergence and open a normal review
path. Reflog is evidence for locating commits, not permission to discard other state.

#### Dirty worktree after rebase

Inspect staged and unstaged diffs independently:

```bash
git diff --cached
git diff
git show --stat --oneline HEAD
```

A staged revert of the branch's own feature may be leftover partial work, while an unstaged lint
fix may be useful. Preserve uncertain material on a separate branch or stash and commit only the
intended improvement. Never commit a partial revert merely because it is already staged.

#### Open PR with no or failed CI

Verify the PR head SHA, workflow triggers, and current check runs. A stale or closed run does not
prove the new head was tested. Re-run only after confirming the workflow applies to the head.

### 8. Handle cherry-picks by semantic portability

Before resolving a rejected-PR commit:

```bash
git show --stat --oneline COMMIT
git show COMMIT
git cherry-pick --no-commit COMMIT
```

Classify each addition: feature-specific lines tied to a dropped design are removed; general
mechanisms applied to surviving behavior may stay. If the destination already contains the net
change, an empty cherry-pick is evidence of a no-op—do not fabricate a replacement commit.

### 9. Resolve stash conflicts without dropping evidence

`Updated upstream` is current branch state; `Stashed changes` is saved work. Read every conflict in
context, choose or combine intentionally, remove all markers, test, then stage the result. Keep the
stash until the resolution commit is verified; dropping it is a separate destructive decision.

### 10. Coordinate submodules and permission retries

The superproject records a submodule commit, not a branch. Verify both repositories:

```bash
git submodule status --recursive
git -C path/to/submodule status --short --branch
git -C path/to/submodule rev-parse HEAD
git diff --submodule=log
```

Create feature worktrees inside the submodule's own Git repository, then update the superproject
pointer deliberately. For transient worktree metadata permission failures, use a small bounded
retry with diagnostics; do not redirect to another checkout or silently continue.

### 11. Audit cleanup separately

For each worktree/branch/stash, prove whether its commits are reachable, merged, superseded by a
squash, or still unique. A squash merge requires patch/file comparison because commit ancestry may
not show containment. Report safe cleanup candidates, but preserve anything ambiguous. Forced
worktree removal, branch deletion, and stash drop require explicit authority.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | Rebase several branches in one checkout | Index and branch state collide | Use one isolated worktree per branch |
| 2 | Resolve every conflict with ours/theirs | Replay context makes the labels misleading | Resolve from commit intent and current APIs |
| 3 | Push rewritten history with `--force` | Can overwrite concurrent remote work | Use `--force-with-lease` after head recheck |
| 4 | Bypass a failing hook | Publishes unverified state and hides shared defect | Reproduce and fix the enforcement boundary |
| 5 | Register a valid key and expect verified tags | UID email/account verification may still disagree | Align all four signing identities |
| 6 | Edit around files missing on a stale branch | Duplicates code already on current main | Compare and rebase before implementation |
| 7 | Commit all dirty worktree changes together | Leftover revert can undo the feature | Inspect staged and unstaged intent separately |
| 8 | Delete squash-merged branches by ancestry alone | Squash commit has different identity | Compare patch/file content and preserve ambiguity |
| 9 | Drop stash immediately after conflicted pop | Removes recovery evidence before verification | Keep stash until resolved commit is proven |
| 10 | Treat submodule branch as superproject state | Superproject pins only a commit | Verify child HEAD and parent pointer separately |

## Results & Parameters

- Worktree ownership: one branch and one worker per worktree.
- Publication after rebase: `git push --force-with-lease`, never unconditional force.
- Conflict gate: zero unmerged paths and zero conflict markers before continue.
- Signature gate: good local signature plus full-fingerprint, UID email, and verified-account match.
- Permission/transient retry: small finite attempt count with visible final failure.
- Cleanup: independent audited phase; preserve uncertain branches, worktrees, and stashes.
- Verification: focused conflict/import tests, repository required checks, signature status, and PR
  head/check readback.

## Evidence Boundary

The consolidated workflow is `verified-local` across the indexed repositories. Individual cases
have different scopes; the public hosted-tag case proves identity alignment, not every hosting
provider's signing behavior. Consult the notes index before claiming case-specific verification.
