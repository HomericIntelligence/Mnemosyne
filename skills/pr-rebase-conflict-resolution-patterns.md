---
name: pr-rebase-conflict-resolution-patterns
description: "Use when a pull request is DIRTY or CONFLICTING after its base advances, a stacked or same-file PR queue needs serialized rebasing, conflict status is ambiguous (AA/UU/modify-delete), or a textually clean rebase may hide semantic, test, lint, policy, or inventory drift."
category: ci-cd
date: 2026-07-12
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
history: pr-rebase-conflict-resolution-patterns.history
tags: [git, rebase, merge-conflict, pull-request, worktree, force-with-lease, semantic-conflict, stacked-pr, ci]
---

# PR Rebase and Conflict Resolution Patterns

## Overview

Use this playbook to re-parent a pull-request branch onto current trunk without
dropping either side's intent. Git's conflict markers cover only textual overlap;
the required result is a current-base branch whose unique delta, runtime behavior,
tests, policy prose, generated state, and repository inventories remain coherent.

- Verification: `verified-ci` overall. Individual cases retain their original
  status in [the case notes](./pr-rebase-conflict-resolution-patterns.notes.md).
- Full prior versions: [history](./pr-rebase-conflict-resolution-patterns.history).

## When to Use

- GitHub reports `mergeStateStatus=DIRTY` or `mergeable=CONFLICTING`, even when
  every check is green.
- A prerequisite or sibling refactor merged and the feature must be ported to a
  new layout or API.
- Several PRs edit the same hot files, or two PRs independently added the same
  source/test module.
- Rebase reports `AA`, `UU`, or modify/delete; an `AA` file may contain no markers.
- A clean rebase fails tests, type checks, complexity limits, policy checks, or
  inventory consistency.
- A branch is mergeable but a required job is `SKIPPED` because an upstream job
  uses stale workflow configuration.
- A rebase is reported complete but its merge base or inherited trunk behavior is
  uncertain.

## Verified Workflow

### 1. Establish immutable facts

```bash
git fetch origin
trunk=origin/main                    # use origin/master where the repo does
git rev-parse "$trunk"
git rev-parse origin/<pr-branch>
git merge-base "$trunk" origin/<pr-branch>
gh pr view <N> --json headRefName,baseRefName,mergeStateStatus,mergeable,statusCheckRollup
gh run list --branch main --limit 10
```

Do not rebase a queue onto a red trunk. If unrelated PRs all fail the same test,
run that test on an isolated checkout of bare trunk. A failure there is a broken-
trunk problem: fix trunk once, then restart the queue.

Record the original remote head. Create a fresh isolated worktree from that exact
head; preserve dirty local work before touching a reused checkout.

```bash
git worktree add --detach /tmp/rebase-<N> origin/<pr-branch>
git -C /tmp/rebase-<N> switch -c rebase-<N>
git -C /tmp/rebase-<N> log --oneline "$trunk"..HEAD
git -C /tmp/rebase-<N> diff --stat "$trunk"...HEAD
```

### 2. Rebase and classify every conflict

```bash
git rebase "$trunk"
git status --short
git ls-files --unmerged
```

During a rebase, `ours` is the rebased-onto trunk state and `theirs` is the commit
being replayed—the opposite of the intuition many people carry from merge. Read
both stages before resolving:

```bash
git show :2:<path>                   # ours / trunk-side stage
git show :3:<path>                   # theirs / replayed-commit stage
git show HEAD:<path>
git show REBASE_HEAD:<path>
```

`AA` means both sides added a file and may show no `<<<<<<<` markers. `UU` means
both modified it. For modify/delete, inspect trunk's file and confirm it is still
the stale artifact the commit intends to delete before running `git rm <path>`.

Resolve according to intent:

| Conflict | Default disposition | Required check |
| --- | --- | --- |
| Generated lockfile | Remove and regenerate with the owning tool | Tool reports lock current |
| Generated marketplace/index | Keep current trunk, regenerate or reapply the unique delta | Schema/count/inventory check |
| Full rewrite vs small edit | Keep coherent rewrite, port the small edit | Whole-file semantic review |
| Same import line | Union symbols into one formatter-ordered import | Lint plus runtime import |
| Parallel source extraction | Prefer current trunk structure; add only unique behavior | Source diff and focused tests |
| Parallel test addition | Union materially distinct tests | Test collection and run |
| Additive build/config blocks | Keep both valid blocks | Parser/configure step |
| Policy prose | Pick the chronologically current contract, then update every restatement | Whole-file search and backing test |
| Already-upstream commit | Skip only after proving no unique delta remains | Empty/trivial trunk diff |

Stage paths explicitly. Do not use `git add .` or `git add -A` in a conflict loop.
If a safety policy blocks checkout/restore shortcuts, reconstruct from read-only
objects and apply the desired content through an approved editor; do not bypass
the policy or use destructive reset commands.

### 3. Handle queue topology deliberately

For same-file sibling PRs, rank the remaining branches by smallest meaningful
diff and land them serially. Rebase PR `k` only after PR `k-1` has merged and
trunk has been fetched. Union reusable helpers, leave duplicated consumers as
thin delegates, merge imports, and let lint remove now-unused symbols.

For stacked PRs, verify the new base contains the prerequisite. Retargeting does
not automatically copy later fix commits. Cherry-pick orphaned CI/lint fixes only
after proving they are absent from the new history.

If the substantive change already landed through a sibling, compare both files
and the final branch diff. Close a fully superseded PR; do not manufacture an
empty residual.

### 4. Continue, verify parentage, and inspect the residual

```bash
git diff --check
git status --short
GIT_EDITOR=true git rebase --continue

test "$(git merge-base "$trunk" HEAD)" = "$(git rev-parse "$trunk")"
git diff --stat "$trunk"...HEAD
git log --oneline "$trunk"..HEAD
```

Repeat until complete. If `--continue` reports no changes, prove the replayed
commit is already represented and use `git rebase --skip`; otherwise recover its
unique delta. After completion, also check for a known trunk-only symbol or
behavior. This catches a stale ref or later force-push that silently restored the
old ancestry.

### 5. Audit beyond conflict markers

A zero-marker scan is necessary but not sufficient:

```bash
git grep -nE '^(<<<<<<<|=======|>>>>>>>)' -- . ':!*.lock'
git diff --check
pre-commit run --all-files
<repository test command>
<repository type-check/build command>
```

Audit every decision-changing layer touched by either side:

- constants, environment readers, option defaults, helper returns, and callers;
- actual function signatures versus mocks and fixtures;
- imports at runtime, not only lexically;
- block-scoped names after branch union (rename shadowed locals that create TDZ or
  type-checker failures);
- numerical API changes at every call site, with derived equivalence checks rather
  than compile-only evidence or relaxed tolerances;
- language source and build files with their own tools (never run a source
  formatter over CMake or another build DSL);
- complexity after two individually valid changes combine;
- all repetitions of changed policy values, not only conflicted hunks;
- inventory/index rows after file deletion;
- generated lockfiles and manifests after dependency/config changes.

Regenerate stale mocks from the current implementation. Do not change production
code merely to satisfy expectations written for an abandoned branch design.

### 6. Preserve signatures, push safely, and re-arm automation

Repositories that require signed, DCO-attested commits need replayed commits
re-signed because rebase changes their object IDs:

```bash
git rebase --exec 'git commit --amend --no-edit -s -S' "$trunk"
old=<recorded-remote-head>
git push --force-with-lease=refs/heads/<pr-branch>:"$old" origin HEAD:<pr-branch>
```

Re-fetch and verify the pushed remote merge base. Use the hosting API to verify
commit signatures when local keyrings cannot validate collaborators' keys.
Force-pushes commonly clear auto-merge; arm it only after the push and required
checks are running against the new head.

## Special Diagnoses

### Green checks but DIRTY

Green historical checks do not make a conflicting head mergeable. The conflict is
the blocker; rebase instead of hunting for a nonexistent failing job.

### Required check is SKIPPED

Inspect required contexts and check runs. If a required job has `needs:` on a lint
job rejected for stale workflow policy (for example an unpinned action), an empty
commit reruns the same broken workflow. Rebase to inherit trunk's corrected YAML,
then push and re-arm.

### Same failure across unrelated rebased PRs

Prove the failure on trunk. Two independently green PRs can semantically collide
(for example a return-tuple expansion plus a stale mock) without a text conflict.
Fix trunk once rather than patching every trailing branch.

### Clean merge, new semantic failure

Run whole-tree lint and tests. Common causes are stale mocks, a byte-identical test
whose shared contract changed elsewhere, two clean edits combining past a
complexity limit, or deleted files left in an inventory table.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Blanket side selection | Used `--ours` or `--theirs` for every conflict | Drops one branch's intent; rebase side names are counterintuitive | Read both stages and resolve per artifact |
| Lockfile hand merge | Manually combined generated lock state | Hashes and solver state are not safely mergeable | Regenerate with the owning tool |
| Marker-only review | Trusted no markers or a clean rebase | Semantic conflicts are outside Git's model | Run tests, lint, policy, inventory, and runtime checks |
| Parallel hot-file rebases | Rebased the same-file cluster concurrently | Each merge re-conflicts the remaining branches | Use a smallest-diff-first serial train |
| Self-report acceptance | Trusted a rebase success report | Stale refs or a later push can preserve old ancestry | Compare merge base and inherited trunk behavior |
| Empty workflow retrigger | Pushed an empty commit for stale workflow policy | Reruns the same rejected workflow | Rebase to inherit corrected workflow files |
| Scoped hook evidence | Ran hooks only on conflict-touched files | Misses whole-tree complexity and inventory checks | Run the full hook suite and tests |
| Unqualified force-push | Rewrote the remote without an explicit lease | Can overwrite new remote work | Pin the lease to the observed old SHA |

## Results & Parameters

- `<trunk>`: current `origin/main` or the repository's documented default branch.
- `<original-head>`: remote PR SHA captured immediately before the operation.
- `<known-trunk-evidence>`: a recently merged symbol, file, or test absent at the
  old merge base.
- `<repository checks>`: exact commands required by repository policy; do not
  weaken, skip, or silently substitute them.

Completion requires current parentage, a reviewed nonempty residual (or an
explicit superseded disposition), zero unresolved conflicts, passing required
local checks, preserved verification boundaries, a lease-safe push, and CI on the
new head.

## References

- [Detailed case index and evidence](./pr-rebase-conflict-resolution-patterns.notes.md)
- [Version history and full superseded content](./pr-rebase-conflict-resolution-patterns.history)
