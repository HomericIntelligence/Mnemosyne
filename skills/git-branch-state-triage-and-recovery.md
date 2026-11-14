---
name: git-branch-state-triage-and-recovery
description: >-
  Diagnose and recover stale, orphaned, diverged, prematurely merged, closed-PR, rewritten-SHA,
  or contaminated stacked branches, and retire classified work safely. Use before rebasing,
  discarding, replaying, opening a PR, or deleting stale branches when branch identity, ancestry,
  PR ownership, the unique patch, or the remote retirement state is uncertain. Also use for a
  bulk local-branch inventory cleanup.
category: tooling
date: 2026-10-13
version: "2.8.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
tags: [git, branch, triage, recovery, stale, superseded, orphan, diverged, merge-base,
  cherry-pick, unrelated-histories, consolidation, squash-merge, stash, auto-merge,
  follow-up-branch, force-with-lease, closed-pr, replacement-pr, stacked-pr, backup-ref,
  exact-head, concurrent-trunk, artifact-provenance, decommission, remote-only-commits,
  retirement, rebase-conflict, intent-unit, refspec-fetch, tip-claim, fork-deletion]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/git-branch-state-triage-and-recovery.history"
history-cleanup-date: "2026-09-20"
---

# Git Branch State Triage and Recovery

## Overview

Recover the intended patch, not the historical branch shape. First bind the local branch to its
live PR and exact remote head, then distinguish content already on trunk from work that is truly
unique. Squash and rebase merges rewrite commit identity, so ancestry and `git cherry` are evidence,
not final authority.

Case evidence is indexed in
[`git-branch-state-triage-and-recovery.notes.md`](git-branch-state-triage-and-recovery.notes.md).
The complete superseded source is archived in
[`git-branch-state-triage-and-recovery.history`](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/git-branch-state-triage-and-recovery.history).

## When to Use

- The remote tracking ref disappeared or the branch is far behind trunk.
- A rebase, repair, or recovery task addresses a PR that is already merged or closed before local
  work starts.
- `merge-base` is absent, a branch contains many HEAD-only files, or consolidation changed paths.
- A PR merged while review/fixes were in progress, or a merged branch has new uncommitted work.
- A closed PR cannot be reopened, but its head can be recovered into a replacement PR.
- PRs whose head lived on a fork turned CLOSED and the fork repository is gone; re-creating a
  same-named fork does not revive them.
- A merged PR's branch looks unique because commit SHAs were rewritten.
- A stacked child includes unrelated commits and must be rebuilt from its current parent.
- An approved cleanup retires several stale branches, worktrees, or stashes and the local clone
  can lag the remote.
- A branch was deleted locally while its remote name can still hold commits that no local ref
  fetched.
- A rebase conflict places side-by-side rewrites of the same lines for the same upstream change,
  or per-hunk resolution that always takes the trunk side trends toward an empty final diff.
- An instruction asks to rebase an open PR, or to keep it open, while a replacement PR may already
  have landed the same patch, so the rebase could leave nothing to push.
- A published tip claim, a rebase base, or a mergeability or dependency check must name the
  current remote branch state, and the last fetch used a refspec without a destination mapping
  (for example `git fetch origin <branch>`).

## Verified Workflow

### 1. Capture live ownership and immutable recovery points

Do not mutate first. Fetch, record the local/remote tips, query the PR by the actual head branch,
and create a backup ref when a rewrite may follow.

```bash
git fetch origin
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
git merge-base HEAD origin/main || true
git branch backup/<branch>-<timestamp> HEAD
gh pr list --head <branch> --state all \
  --json number,state,headRefName,headRefOid,baseRefName,url
```

Use `headRefName` from GitHub; never derive a PR branch from an issue number. Re-read `headRefOid`
before pushing rewritten history.

Bind every published branch-tip claim to fresh state, not to a fetch that already ran. A refspec
fetch without a destination mapping (`git fetch origin <branch>`) updates `FETCH_HEAD` only;
`refs/remotes/origin/<branch>` keeps its old value, so a later `git rev-parse origin/<branch>`
reads a stale tip. Refresh the ref immediately before the claim, or read the forge directly for
a published record:

```bash
git fetch origin              # configured refspec updates the tracking refs
git fetch origin <branch>:refs/remotes/origin/<branch>   # explicit destination mapping
gh api repos/<user>/<repo>/branches/<branch> --jq .commit.sha   # forge truth
```

This rule covers each read that later carries a decision: a tip in a coordination record, the
start point of a rebase, and any "the branch has not moved" dependency check.

Read `state` with the merge state. `mergeStateStatus` is a mergeability value, not a lifecycle
value. A task that gates on it stops only on `CLEAN`, and that gate does not catch a closed or
merged PR. Compare `state` with the intended action before you start a rebase:

```bash
gh pr view <N> --json state,mergeStateStatus,headRefName,headRefOid,mergeCommit
```

A rebase task on a `MERGED` PR stops at classification. Do not fetch the head branch, rebase, or
push. `mergeStateStatus=UNKNOWN` on a `MERGED` or `CLOSED` PR is not a conflict report. The remote
head branch usually no longer exists; confirm with `git ls-remote --heads origin <headRefName>`
before you rely on a push target.

For a retirement scope, also enumerate the live remote names. A local clone does not prove the
remote state: a remote head can hold commits that no local ref ever fetched.

```bash
git ls-remote --heads origin '<retirement-pattern>'
git fetch origin <branch>:refs/remotes/origin/<branch>
mb=$(git merge-base origin/main refs/remotes/origin/<branch>)
git log --oneline "$mb"..refs/remotes/origin/<branch>
```

### 2. Classify the state

| State | Evidence | Recovery direction |
| --- | --- | --- |
| Superseded | PR merged or patch/content already on trunk | Stop; do not rebase or duplicate |
| Superseded at task start | The task asks for a rebase, but the PR is already merged before any local work | Stop before the rebase; the merged-PR case in this entry applies, not the rebase playbook |
| Open PR superseded by a different merged PR | A replacement PR landed the same patch; the old PR is still open, often with a stale label or armed auto-merge | Rebase locally only to prove equivalence. If the rebased tree equals trunk, do not push: the forge closes a PR whose head has an empty diff. Report the per-file evidence and let the owner decide |
| Partially superseded | Trunk absorbed the delta in a parallel rewrite; the per-intent-unit proof finds surviving units | Re-propose only the surviving units as minimized commits on current trunk |
| Orphan | No common ancestor | Export the intended patch, recreate from trunk |
| Diverged | Common base exists; local/remote tips differ | Reset/rebuild from the chosen tip, cherry-pick intended commits |
| Prematurely merged | Old PR is merged; later commits are missing | Fresh trunk branch; replay only missing commits |
| Merged branch with uncommitted follow-up | PR identity is spent; working tree has a new delta | Stash, fresh trunk branch, pop and verify |
| Closed unmerged | Head is recoverable from a surviving clone or ref but reopen is refused — permanently so when the head fork was deleted | Rebase/rebuild and open a replacement PR |
| Contaminated stacked child | Child diff contains parent-unrelated commits | Rebuild child from rebased parent |

Use both two-dot and triple-dot views deliberately:

```bash
git log --oneline origin/main..HEAD
git diff --stat origin/main..HEAD
git diff --stat origin/main...HEAD
git cherry origin/main HEAD
```

Two-dot answers what tree delta would be applied now. Triple-dot describes change since the merge
base and becomes noisy when merge strategy rewrites history. For squash-merged work, search trunk
by PR number/subject and verify the resulting tree or markers. A merged PR plus equivalent content
is stronger evidence than ahead count or `cherry=+`.

### 3. Prove whether apparent work is unique

For modified working-tree files, compare bytes or content against trunk; zero unique lines across
all files means the delta may already have shipped. For many branch-only paths after consolidation,
compare counts at the fork point, branch head, and trunk, then inspect whether trunk replaced or
absorbed the old files.

```bash
git diff --name-status origin/main...HEAD
git log --diff-filter=D --oneline origin/main -- <old-path>
git cat-file -e origin/main:<path>
git grep -n '<stable-marker>' origin/main
```

Prove uniqueness per intent unit when both sides rewrite the same lines in response to the same
upstream change. Content comparison then reports zero unique lines, but a parallel rewrite can
land a different subset of one intent: trunk can replace a check with a differently shaped check
and drop a behavior that the branch still carries. Split each side into intent units — one
assertion, one trigger, one failure mode, one mechanical follow-up per unit — and give each unit
a landed or not-landed verdict on current trunk. For a not-landed candidate, prove its value
against trunk itself: grep the trunk tree for the same assertion targets, then transplant the
unit onto the current trunk tree and make it pass there (for a test, copy it next to trunk's
replacement and run it). A clean pass proves that the unit is expressible and that trunk lacks
it. An empty `git diff <trunk>` after take-trunk-side resolutions is not proof of obsolescence;
it only proves that no hunk survived mechanically. Do not classify superseded, force-push, or
close until each unit has a recorded verdict, and deliver surviving units as their own minimized
change on current trunk — conflict resolution cannot re-add a unit that lives inside a
differently shaped hunk.

Do not discard based on counts alone. Preserve with a stash or backup ref before any authorized
destructive operation.

### 4. Recover by state

#### Merged or superseded before any local work

Prove content equivalence against the merge commit, not the commit subject, before you stand down.
A squash or rebase merge rewrites identity, so the PR head is not an ancestor of trunk and a bare
`git merge-base --is-ancestor` check can look negative even when all content landed.

```bash
git fetch origin <trunk>
gh pr view <N> --json state,mergeCommit --jq '.state, .mergeCommit.oid'
git rev-parse <trunk>
git diff --quiet <merge-commit> <pr-head> -- <paths the PR touched> \
  && echo "IDENTICAL content" || echo "DIFFERS - inspect"
git diff --stat <pr-head> <trunk>
```

An empty diff over the PR's own paths, for any merge strategy, is the equivalence proof. A non-empty
total diff must contain only later unrelated commits. Do not attribute that later work to the PR or
treat it as lost PR content. If the paths differ, this is a premature merge; use that state instead.
Report the task as superseded by the merge and push nothing. State the reasons separately:
`state=MERGED`, the merge commit identity, and content compared equal.

#### Orphan or diverged branch

List and inspect candidate commits, recreate from current trunk in an isolated worktree, then
cherry-pick only the intended commits in dependency order. If commit history is unusable, produce a
reviewable patch and apply it to the new branch. Resolve conflicts according to current trunk
semantics, not by restoring the old whole tree.

```bash
git switch -c <fresh-branch> origin/main
git cherry-pick <sha1> <sha2>
```

#### Old PR merged during review

The old branch is no longer a PR update target even if a push succeeds. Create a fresh branch at
current trunk and replay only commits absent from trunk. Inspect the two-dot patch for inversions of
concurrent changes. If an artifact embeds a source SHA, rebuild it from the replayed source and
verify both embedded revision and digest.

#### Merged current branch with uncommitted follow-up

```bash
git stash push -u -m 'follow-up from merged <branch>'
git switch -c <fresh-follow-up> origin/main
git stash pop
git status --short
```

Run affected checks and any repository-required validation, make a signed/DCO commit if
required, and open a linked new PR when publication is authorized. Never append a new change to a branch whose PR is already merged.

#### Closed PR cannot reopen

Confirm the PR is CLOSED rather than MERGED, preserve the exact old head, rebase or rebuild against
current trunk, and push with an explicit lease:

```bash
git push --force-with-lease=refs/heads/<branch>:<old-head> origin HEAD:<branch>
```

If GitHub still refuses reopen, create a replacement PR from that recovered branch and link the old
PR. Do not create a duplicate if the two-dot delta is empty or already on trunk.

Fork deletion is a distinct cause and its refusal is permanent. Deleting the head fork closes its
open PRs and destroys each PR's head-repository binding. Re-creating a fork under the same name
makes a new repository with a new identity, so the old binding dangles and `gh pr reopen` fails —
for example with `GraphQL: Could not open the pull request (reopenPullRequest)` — no matter how
often it is retried. Do not retry reopen; recover each head from a surviving clone or ref, verify
the recovered tip equals the PR's recorded `headRefOid`, push it to the new fork, and open a
replacement PR per affected PR, linking the closed one as superseded. Before deleting a fork with
open PRs, mirror its branches: if the fork is the only copy of the head commits, the deletion
destroys them with the PRs.

#### Contaminated stacked child

Record the parent and child heads, preserve a backup ref, rebase the parent first, create a clean
child at the rebased parent, and cherry-pick only child-owned commits. Verify the final child range
against the parent, not against trunk, until the dependency is removed.

#### Retirement of classified-superseded work

Retirement is a destructive operation with its own proof. The approved disposition list is a
point-in-time snapshot of both local and remote state, so bind execution to a fresh enumeration:
destroy only items on the approved list, and treat objects that appear mid-operation from parallel
streams as foreign. Report them; never include them only because they match the cleanup pattern.

For each approved branch, archive every commit that no preserved ref contains, then delete the
name in both namespaces:

```bash
git format-patch -o <archive-dir> "$mb"..refs/remotes/origin/<branch>
git branch -D <branch>
git push origin --delete <branch>
git update-ref -d refs/remotes/origin/<branch>
```

Retirement is complete only when re-enumeration returns zero refs in both the local branches and
the remote heads for every retired pattern.

#### Retirement of local-only branches

A local inventory cleanup has no approved disposition list and no remote ref. The classification is
the proof, so derive it from live PR state rather than an ahead count. Sort each branch into one
class and retire only the first three:

| Class | Evidence | Action |
| --- | --- | --- |
| Merged into trunk | `git merge-base --is-ancestor <branch> origin/main` is true | `git branch -d`; the command itself proves redundancy |
| PR merged, branch not an ancestor | PR state is `MERGED` but ahead count is positive | Preserve a backup ref, then `git branch -D` |
| PR closed, never landed | PR state is `CLOSED` and no open replacement exists | Preserve a backup ref, then `git branch -D` |
| No PR ever opened | No pull request for any state names the head | Keep; it may hold the only copy of the work |
| Open PR | PR state is `OPEN` | Keep |

Squash and rebase merges leave the head ahead of trunk, so an ahead count never separates "already
shipped" from "never shipped". Only PR state does. Use `git branch -d` where ancestry already holds,
because its refusal catches a mistake that `-D` would hide. For the other classes, create a backup
ref before deletion; a backup ref is the local-only equivalent of a format-patch archive:

```bash
git update-ref refs/backup/<branch> refs/heads/<branch>
git branch -D <branch>
```

Restore a retired branch with `git branch <branch> refs/backup/<branch>`. Enumerate backups with
`git for-each-ref refs/backup`.

A branch that a worktree holds cannot be deleted at all; the command reports the holding worktree
path. Do not detach or delete that worktree to free the branch inside a branch-only cleanup. Remove
the worktree in its own operation, then re-enumerate, because other agents can create branches and
stashes while the cleanup runs.

### 5. Verify and publish

Before push, inspect `git diff <intended-base>..HEAD`, changed paths, commit signatures/trailers,
and focused/full tests. Re-read the remote head and use an exact force-with-lease if rewriting.
After push, ensure the PR head, base, and current-head checks match the recovered commit.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Rebase before classification | Rebase before classification | Can resurrect superseded work or erase recovery context | Capture refs and classify first |
| Trust `git cherry`/ahead count | Trust `git cherry`/ahead count | Squash/rebase merges rewrite SHAs | Pair live PR state with content evidence |
| Use only triple-dot diff | Use only triple-dot diff | Rewritten ancestry produces a noisy false delta | Inspect two-dot application delta too |
| Push follow-up work to a merged PR branch | Push follow-up work to a merged PR branch | The branch identity is spent | Fresh branch from current trunk |
| Replay the whole old tree | Replay the whole old tree | Reverts concurrent trunk changes | Replay only missing commits semantically |
| Assume branch name from issue | Assume branch name from issue | Existing PR may use another head | Read `headRefName` from GitHub |
| Bare `--force-with-lease` | Bare `--force-with-lease` | May not protect the observed head | Pin the branch and old OID explicitly |
| Resolve each rebase conflict by taking the newer side | Treat per-hunk take-trunk-side resolution as the uniqueness classification | The resolutions converge to an empty final diff and discard behavioral units that trunk never landed | Split the delta into intent units; prove each unit landed or not-landed on current trunk; reshape or close from the recorded verdicts |
| Retire local branches by ahead count | Delete every branch whose ahead count looked redundant | A squash merge leaves the head ahead of trunk, so the count cannot separate shipped from unshipped work, and a branch with no PR ever was deleted with its only copy | Classify by live PR state; use `-d` where ancestry holds and a backup ref before `-D` |
| Rebuild child from trunk | Rebuild child from trunk | Loses intended stack dependency | Rebuild from the rebased parent |
| Trust a point-in-time inventory | Retire branches from the initial local-only inventory | A remote head held commits that no local ref fetched; a parallel stream also created new matching objects mid-operation | Re-enumerate remote and local state at execution; archive remote-unique commits before `push origin --delete`; destroy only enumerated approved items |
| Start a rebase from a merge-state gate only | Gated a rebase task on `mergeStateStatus` and stopped only on `CLEAN` | A merged PR reports `UNKNOWN`, not `CLEAN`, so the gate passed and the rebase was attempted against a deleted branch | Read `state` with the merge state; a `MERGED` or `CLOSED` PR stops at classification |
| Trust the tracking ref after a refspec-only fetch | Read `git rev-parse origin/main` right after `git fetch origin refs/heads/main` to decide whether the trunk had moved | The refspec fetch updated `FETCH_HEAD` only; the tracking ref still held a tip dozens of merges behind, and the trunk dependencies had in fact already merged | Refresh with an unqualified fetch or an explicit destination mapping before any tip claim, rebase base, or dependency check; for a published record, bind the tip to the forge branch API |
| Re-create the fork and retry reopen | Re-created a same-named fork and retried `gh pr reopen` | The PR's head binding points at the deleted repository's identity, which the same-named new repository does not satisfy; the refusal never clears | Fork-deleted PRs can never be reopened; push verified heads to the new fork and open linked replacements immediately |

## Results & Parameters

Triage report contract:

```text
local head: <oid>
remote head: <oid>
trunk head: <oid>
merge base: <oid or none>
PR: <number/state/base/head>
two-dot delta: <summary>
triple-dot delta: <summary>
classification: <state>
preservation ref: <ref>
recovery action: <bounded action>
verification: <commands/results>
remote refs for retired names: <before enumeration → after enumeration (zero)>
```

Never call a branch superseded solely because it is old, or unique solely because it is ahead.
The decision requires both repository history and content-level proof; for parallel rewrites of
the same lines, content-level proof means one landed verdict per intent unit.

## Verified On

- Verified-local branch recovery cases through 2026-07-13.
- A merged-PR-at-task-start case on 2026-10-31 proved path-scoped content equivalence against the
  merge commit and the `UNKNOWN` merge state of a merged PR.
- A refspec-only fetch plus a tracking-ref read on 2026-11-02 reported a trunk tip dozens of
  merges behind the forge during a coordinated multi-lane delivery drive; the corrected binding
  used an unqualified fetch and the forge branch API.
- Compacted for issue #3335; evidence status was preserved without promotion.
