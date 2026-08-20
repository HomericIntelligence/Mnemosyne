---
name: parallel-pr-worktree-workflow
description: "Use when executing or rescuing multiple independent PRs concurrently: each writer needs an isolated worktree, dependency-aware batching, current-head CI triage, explicit merge-method/base handling, exact-lease rebases, contamination rescue, and bounded cleanup."
category: ci-cd
date: 2026-07-01
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-ci
history: parallel-pr-worktree-workflow.history
tags: [parallel-prs, git-worktree, agent-isolation, dependency-waves, current-head-ci,
  mergeability, stacked-pr, auto-merge, contamination-rescue, force-with-lease]
---

# Parallel PR Worktree Workflow

## Overview

Parallelize independent PR work across isolated worktrees while preserving one writer per branch,
explicit dependency order, and current-head evidence. Worktrees isolate `HEAD` and index state;
waves isolate dependencies. Live PR metadata decides whether to rebase, fix CI, retarget, merge, or
stop.

Detailed examples are indexed in
[`parallel-pr-worktree-workflow.notes.md`](parallel-pr-worktree-workflow.notes.md). The complete
superseded source is in
[`parallel-pr-worktree-workflow.history`](parallel-pr-worktree-workflow.history).

## When to Use

- Two or more agents will commit or push in the same repository.
- Five or more independent fixes/PRs can be batched for throughput.
- Many stale PRs need rebase, conflict resolution, checks, and conditional merge.
- A shared prerequisite must land before a fan-out wave.
- Branch/file contamination has already occurred and individual cleanup is becoming quadratic.
- A stacked PR must be retargeted before auto-merge, or an earlier stacked merge was orphaned.
- Checks are stale/missing, mergeability is DIRTY/CONFLICTING, or a branch predates a trunk CI fix.

## Verified Workflow

### 1. Inventory live state before editing

For every PR, record number, head branch/OID, base, draft/state, mergeability, merge-state status,
and check rollup. Query required checks and allowed merge methods once for the repository.

```bash
gh pr view <pr> --json number,state,isDraft,headRefName,headRefOid,baseRefName,\
mergeable,mergeStateStatus,statusCheckRollup,url
gh pr checks <pr>
gh repo view --json squashMergeAllowed,rebaseMergeAllowed,mergeCommitAllowed
```

Do not rely on `gh pr checks` alone: it may display earlier-head results. Missing required checks can
mean GitHub cannot synthesize a merge ref because the PR conflicts. Read the full failed job log
before changing code.

### 2. Build dependency waves and ownership maps

Partition work into:

- independent PRs that can start from the same trunk SHA;
- prerequisite PRs that must land first;
- dependents that branch from the prerequisite and target it temporarily; and
- shared hot files that must be serialized.

Use roughly three to four PRs per worker for repetitive rebase work, but one worktree and one writer
per writable branch. Give every worker exact PRs, branch/base, worktree path, owned files, validation,
push lease, and merge policy. Never use the primary checkout when another session may move it.

### 3. Create explicit worktrees

```bash
git fetch origin
git worktree add -b <branch> <absolute-path> origin/main
git -C <absolute-path> status --short --branch
```

For an existing remote PR branch, create a unique detached or local-branch worktree without
switching a possibly dirty local checkout:

```bash
git worktree add --detach <absolute-path> origin/<pr-branch>
```

Use the worktree path for all edits and commands. Verify branch and changed paths before commit.
Unique paths are permanent isolation boundaries for the run; do not recycle a path across agents.

### 4. Triage current-head CI and mergeability

Connect failures to `headRefOid`. If a check is red, inspect the actual job log. If a required check
is absent and `mergeable=CONFLICTING`/`mergeStateStatus=DIRTY`, rebase first—waiting cannot create a
merge ref. After a push, `mergeable=UNKNOWN` usually means recomputation; poll rather than inventing
a new defect.

When stale branches fail on dependencies or workflows, inspect trunk history before editing branch
code. If the fix is already on trunk, rebase the PR; do not duplicate it.

```bash
git fetch origin main <pr-branch>
git rebase origin/main
<focused-tests-and-lints>
git push --force-with-lease=refs/heads/<pr-branch>:<observed-old-head> \
  origin HEAD:refs/heads/<pr-branch>
```

Run focused tests for the edited surface and the repository's complete required validation. After
each push, query checks again because one gate can mask the next. Distinguish unrelated local host
failures from the repository's current-head CI evidence, but report both honestly.

### 5. Handle shared prerequisites and stacked PRs

Land a common blocker as its own PR. Branch dependents from that prerequisite and target the
prerequisite branch only while it is genuinely expected to merge. Before arming auto-merge on a
dependent, confirm the prerequisite content is on trunk, retarget the dependent to trunk, and rebase
to remove redundant commits:

```bash
gh pr edit <dependent-pr> --base main
git rebase origin/main
git push --force-with-lease=refs/heads/<branch>:<old-head> origin HEAD:<branch>
```

Only then enable the repository-supported merge method. A dependent left based on a branch that is
closed unmerged can merge into that dead branch and become orphaned. If already orphaned, cherry-pick
the intended squash/commit onto a fresh trunk branch, validate, and open a new PR to trunk.

### 6. Commit and publish each isolated unit

For each worktree:

1. Make only the assigned change.
2. Run pre-commit on all PR-diff files and relevant/full tests.
3. Inspect staged paths and commit under repository signing/DCO policy.
4. Push the exact branch, create/update its PR, and verify the live head.
5. Enable auto-merge only if authorized, the base is final, and the method is allowed.

Do not assume `--rebase`; detect repository settings and use the accepted method, commonly squash.
Do not publish generic PR bodies: summarize the actual delta, dependency, and runnable evidence.

### 7. Rescue cross-contaminated branches

If concurrent workers used a shared checkout and commits are tangled, stop publishing individual
branches. Export staged/unstaged safety patches, identify every intended commit, and create one fresh
integration worktree from trunk. Cherry-pick the worker commits in dependency order, resolve once,
run combined validation, and open one consolidation PR referencing every issue. Close superseded
worker PRs with a link.

This rescue is preferable when per-branch disentangling is O(N²). For a single hijacked branch,
stash/export the local delta and apply it in a fresh owned worktree; never continue after another
session moves `HEAD`.

### 8. Merge in waves and preserve cleanup state

Wait for current-head required checks and mergeability. Merge or arm only authorized PRs. After all
PRs in a wave land, fetch the new trunk and create the next wave from that head. Never branch a
dependent wave from stale local main.

Cleanup happens per PR only after merge/closure and work preservation are proven:

```bash
git worktree remove <absolute-path>
git worktree prune
```

Dirty, locked, submodule-containing, or otherwise force-required worktrees need the repository's
guarded cleanup policy; do not improvise destructive commands.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Concurrent work in primary checkout | Concurrent work in primary checkout | Shared HEAD/index contaminates branches | One explicit worktree per writer |
| Branch all dependents from trunk | Branch all dependents from trunk | Shared prerequisite blocks every PR | Land prerequisite, then fan out |
| Arm auto-merge while still stacked | Arm auto-merge while still stacked | May merge into a dead intermediate base | Retarget/rebase to trunk first |
| Trust stale check table | Trust stale check table | Results may belong to an old head | Bind checks to `headRefOid` |
| Wait for missing validate on conflict | Wait for missing validate on conflict | No merge ref exists | Rebase when mergeability is conflicting |
| Fix branch code before checking trunk | Fix branch code before checking trunk | Duplicates already-landed CI/dependency fixes | Inspect logs and trunk history first |
| Bare force-with-lease | Bare force-with-lease | Does not pin the observed PR head explicitly | Lease exact branch and old OID |
| Repair many contaminated PRs separately | Repair many contaminated PRs separately | Tangled commits create quadratic cleanup | Consolidate by cherry-pick in one fresh branch |
| Reuse worktree paths | Reuse worktree paths | Risks stale state and ownership ambiguity | Unique path per writer/run |

## Results & Parameters

Worker brief:

```text
PR and issue: <identifiers>
worktree: <absolute path>
head branch/OID: <branch>/<oid>
base branch/OID: <branch>/<oid>
owned and forbidden paths: <lists>
dependency wave: <number and prerequisites>
focused/full validation: <commands>
push: exact force-with-lease if rewritten
merge: off | authorized method after final-base confirmation
```

Orchestrator acceptance requires one writer per branch, no unowned files, current-head green required
checks, correct final base, supported merge method, and a recorded final head/merge OID.

## Verified On

- Verified-ci parallel PR, current-head triage, conflict rebase, endpoint/workflow drift, and stale
  automation branch rescues through 2026-07-01.
- Compacted for issue #3335 without changing the evidence classification.
