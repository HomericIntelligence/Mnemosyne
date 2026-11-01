---
name: pr-rebase-conflict-resolution-patterns
description: "Use when a pull request reports DIRTY or CONFLICTING, an active task needs a main artifact to continue, a permitted stacked or same-file rebase needs serialization, conflict status is ambiguous (AA/UU/modify-delete), or a textually clean rebase may hide semantic, test, lint, policy, or inventory drift, or the conflict carries test-pinned values derived from source content that neither side can supply correctly, or the target pull request merged, closed, or lost its source ref between resolution work and the delivery mutation, or every conflict resolves to the current target side because a sibling pull request already delivered the same intent and the reviewed head carries a delivered approval state."
category: ci-cd
date: 2026-07-12
version: "2.4.0"
license: BSD-3-Clause
user-invocable: false
tags: [git, rebase, merge-conflict, pull-request, worktree, force-with-lease, semantic-conflict, stacked-pr, ci]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/pr-rebase-conflict-resolution-patterns.history"
history-cleanup-date: "2026-09-20"
---

# PR Rebase and Conflict Resolution Patterns

## Overview

Use this playbook only for a permitted rebase: a host-reported merge conflict, or
an active task that cannot continue without a main artifact. After task start,
keep the selected main base stable. Do not rebase because main advanced, review
started, or a branch is old. After task completion, rebase only to resolve a
reported merge conflict; repository CI/CD owns other integration with main.
Git's conflict markers cover only textual overlap; preserve each side's intent,
runtime behavior, tests, policy prose, generated state, and inventories.

- Verification: `verified-ci` overall. Individual cases retain their original
  status in [the case notes](./pr-rebase-conflict-resolution-patterns.notes.md).
- Full prior versions: [history](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/pr-rebase-conflict-resolution-patterns.history).

## When to Use

- GitHub reports `mergeStateStatus=DIRTY` or `mergeable=CONFLICTING`, even when
  every check is green.
- An active task must use a layout, API, workflow, or other artifact that a
  prerequisite or sibling refactor changed on main.
- Several PRs edit the same hot files, or two PRs independently added the same
  source/test module.
- Rebase reports `AA`, `UU`, or modify/delete; an `AA` file may contain no markers.
- A clean rebase fails tests, type checks, complexity limits, policy checks, or
  inventory consistency.
- A branch is mergeable but a required job is `SKIPPED` because an upstream job
  uses stale workflow configuration.
- A rebase is reported complete but its merge base or inherited trunk behavior is
  uncertain.
- The pull request merged upstream, was closed, or lost its source ref while
  conflict-resolution work was underway.
- Every conflict resolves to the current target side because a sibling pull
  request already delivered the same intent to the target branch.

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

If unrelated PRs fail the same check, investigate whether the failure comes from trunk.
Prefer one shared repair when the cause is confirmed and the task authorizes it. Continue
independent work; a red trunk alone is not a reason to stop the whole queue or rebase every PR.

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
| Test-pinned content-derived values (digests, computed IDs) | Resolve the source content first; then recompute the pins from the merged content through the repository's own derivation; never copy either side's value | The focused consumer test passes on the recomputed values |
| Additive build/config blocks | Keep both valid blocks | Parser/configure step |
| Policy prose | Pick the chronologically current contract, then update every restatement | Whole-file search and backing test |
| Every hunk resolves to the target side | Stop before you resolve or push. Prove the sibling delivery and the empty residual, then close the pull request | Sibling merge commit reachable from the target, plus an empty residual diff against the target |
| Already-upstream commit | Skip only after proving no unique delta remains | Empty/trivial trunk diff |

Stage paths explicitly. Do not use `git add .` or `git add -A` in a conflict loop.
If a safety policy blocks checkout/restore shortcuts, reconstruct from read-only
objects and apply the desired content through an approved editor; do not bypass
the policy or use destructive reset commands.

Some conflicts carry test-pinned values that are pure functions of source
content, such as a digest map over configuration files or a computed context
identifier. Neither side's pinned value is correct after a content union.
Resolve the semantic source content first. Then recompute each pin with the
same derivation the consuming test uses: run the repository's derivation code
against the merged content, or run the focused test and harvest the computed
values from its assertion diffs. Mirror adjacent semantic assertions to the
computed merged truth; do not infer invariants by symmetry. Treat mechanical
pins as safe to harvest verbatim, but require semantic assertions to come from
the merged content's own rules: an assertion that looks symmetric can encode
an invariant the implementation does not have.

### 3. Handle queue topology deliberately

For same-file sibling PRs, rank the remaining branches by smallest meaningful
diff and land them serially. After PR `k-1` merges, rebase PR `k` only if it
reports a merge conflict or its active task needs main content. Otherwise keep
its task base stable and let CI/CD integrate it. Union reusable helpers, leave
duplicated consumers as thin delegates, merge imports, and let lint remove
now-unused symbols.

For stacked PRs, verify the new base contains the prerequisite. Retargeting does
not automatically copy later fix commits. Cherry-pick orphaned CI/lint fixes only
after proving they are absent from the new history.

If the substantive change already landed through a sibling, compare both files
and the final branch diff. Close a fully superseded PR; do not manufacture an
empty residual.

Do not close from a conflict marker alone. A conflict that shows the same
correction on both sides is not proof of delivered work. Prove these three
items:

1. The sibling PR is `MERGED`, and its merge commit is reachable from the
   target branch.
2. The linked issue names that sibling PR as a closing reference and is
   `CLOSED`.
3. The target branch content satisfies each acceptance criterion, and a search
   for the stale term returns only the unrelated matches.

Before you close, read the complete current head, the sibling merge commit, and
the full branch diff. Some residual can stay: a wording variant, a missed third
file, or a `gitignore`-based revert backdrop. Close only when a rebase would
resolve every hunk to the target side.

Then post a close comment and close the PR. Do not force-push, do not rebase, and
do not request a new review. All these actions only replace the head, and the
same content cannot add value. If the branch conflicts, the PR cannot merge.

A delivered approval label at the reviewed head is a record for that head only.
Do not remove it. Do not treat it as a reason to drive the PR to merge.

Keep the close comment short and make it sufficient. It needs the rebase
conflict list, the sibling merge commit and merge time, the issue closing
reference, the acceptance check, and one sentence that the delta is empty. When
the same intent can still need a change, ask for a new issue against the current
target text. Do not reopen the superseded branch.

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
- generated lockfiles and manifests after dependency/config changes;
- test pins and adjacent assertions derived from source content that either side
  changed, recomputed from the merged content and never guessed.

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
commit reruns the same broken workflow. An active task can rebase to use trunk's
corrected YAML because that artifact is required to continue. For a completed PR
without a reported conflict, let CI/CD perform ordinary integration.

### Same failure across unrelated rebased PRs

Prove the failure on trunk. Two independently green PRs can semantically collide
(for example a return-tuple expansion plus a stale mock) without a text conflict.
Fix trunk once rather than patching every trailing branch.

### Clean merge, new semantic failure

Start with the affected behavior and expand checks when the integration risk warrants it.
Common causes are stale mocks, a byte-identical test
whose shared contract changed elsewhere, two clean edits combining past a
complexity limit, or deleted files left in an inventory table.

### Target merged during resolution work

Treat the §1 immutable facts as time-boxed. Immediately before the delivery
mutation, refresh the trunk and re-read the artifact state, even when the push
is explicitly authorized:

```bash
git fetch origin
gh pr view <N> --json state,headRefOid,mergeCommit
git log --oneline -3 "$trunk"
```

If the target pull request merged upstream or its source ref was deleted while
resolution work ran, do not push. A replay push now resurrects a deleted branch
with duplicated content and can confuse automation or review state bound to the
original ref. Prove equivalence at content level, not by commit subject, before
standing down: compare the upstream merge commit's copy of each conflicted file
with the prepared resolution (`git show <merge>:<path> | sha256sum`, or the
repository's own derived pins) and compare the final residual diff.
Byte-identical content closes the task as integrated by the upstream merge;
keep the worktree pending cleanup authority, and do not reopen, comment, or
recreate the ref unless asked. Any real content delta is new evidence: report
it against the landed merge commit and take direction before writing.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Blanket side selection | Used `--ours` or `--theirs` for every conflict | Drops one branch's intent; rebase side names are counterintuitive | Read both stages and resolve per artifact |
| Lockfile hand merge | Manually combined generated lock state | Hashes and solver state are not safely mergeable | Regenerate with the owning tool |
| Marker-only review | Trusted no markers or a clean rebase | Semantic conflicts are outside Git's model | Run tests, lint, policy, inventory, and runtime checks |
| Parallel hot-file rebases | Rebased the same-file cluster concurrently | Each merge re-conflicts the remaining branches | Use a smallest-diff-first serial train |
| Self-report acceptance | Trusted a rebase success report | Stale refs or a later push can preserve old ancestry | Compare merge base and inherited trunk behavior |
| Empty workflow retrigger | Pushed an empty commit for stale workflow policy | Reruns the same rejected workflow | An active task can rebase only when corrected workflow files are required; otherwise let CI/CD integrate |
| Scoped hook evidence | Ran hooks only on conflict-touched files | Misses whole-tree complexity and inventory checks | Run the full hook suite and tests |
| Unqualified force-push | Rewrote the remote without an explicit lease | Can overwrite new remote work | Pin the lease to the observed old SHA |
| Pushing on stale authorization | Replayed a completed repair after the target merged upstream during the work | Recreates a deleted source branch and duplicates integrated content | Refresh and re-read artifact state immediately before the mutation; a merged or ref-deleted target is a stop pending content-equivalence proof |
| Resolving an all-target-side conflict to keep the PR alive | Rebased a branch whose every conflicting hunk showed the same correction already on the target side, resolved both sides to the target text, and force-pushed | The result had an empty residual, so the new head carried no product value, invalidated the check record for the old head, and started a second review of nothing | When a rebase would resolve every hunk to the target side, stop before the write; prove the sibling delivery, then close the PR |
| Closing from the conflict markers alone | Read the three conflicted files, saw the same wording on both sides, and closed the PR | The decision was correct, but the evidence named no sibling merge commit and no acceptance check, so a reader could not audit it | Add the sibling merge commit reachability, the issue closing reference, and the acceptance-term search to the close evidence |
| Treating a delivered approval label as current authority | Read the delivered approval state at the reviewed head as a reason to keep driving the PR to merge | The label attests one reviewed head, not that the change is still absent from the target branch | Re-check the residual against the target branch first; the label cannot make an empty change useful |

## Results & Parameters

- `<trunk>`: current `origin/main` or the repository's documented default branch.
- `<original-head>`: remote PR SHA captured immediately before the operation.
- `<known-trunk-evidence>`: a recently merged symbol, file, or test absent at the
  old merge base.
- `<repository checks>`: exact commands required by repository policy; do not
  weaken, skip, or silently substitute them.

Completion requires current parentage, a reviewed nonempty residual (or an
explicit superseded disposition), zero unresolved conflicts, passing required
local checks, preserved verification boundaries, and either a lease-safe push
with CI on the new head or a content-verified stand-down when the target
already landed upstream.

### Superseded-disposition check

Use this check when a rebase conflicts and a sibling may have delivered the
same intent. Run it before you resolve a hunk or push:

```bash
git fetch origin
trunk=origin/main
git merge-base "$trunk" <superseded-head>
git rev-list --count "$trunk"..<superseded-head>
git log --oneline -5 "$trunk" -- <each conflicted path>
git grep -n '<stale term>' "$trunk" -- <the changed paths>
gh pr view <sibling-pr> --json state,mergedAt,mergeCommit
gh issue view <issue> --json state,closedByPullRequestsReferences
```

Close the pull request when all these results are true:

| Check | Required result |
| --- | --- |
| Sibling state | `MERGED`, and its merge commit is reachable from the trunk |
| Issue state | `CLOSED`, and the sibling is in the closing references |
| Stale-term search | No match in the changed files, or only unrelated matches |
| Rebase residual | Every conflicted hunk resolves to the trunk side |
| Branch diff against trunk | Empty or reverses later trunk work |

Do not use the resolved pull-request head as evidence of the trunk content. The
reviewed head can stay older than the trunk. Read the trunk content directly.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| Anonymized multi-repository delivery fleet, 2026-10 | Documentation-only PR: all three conflicts resolved to the target side after a sibling delivered the same correction; the PR was closed with the sibling merge commit and the acceptance check as evidence | See [notes](./pr-rebase-conflict-resolution-patterns.notes.md) |

## References

- [Detailed case index and evidence](./pr-rebase-conflict-resolution-patterns.notes.md)
- [Version history and full superseded content](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/pr-rebase-conflict-resolution-patterns.history)
