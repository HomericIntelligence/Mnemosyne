---
name: pr-rebase-conflict-resolution-patterns
description: "Use when a pull request reports DIRTY or CONFLICTING, an active task needs a main artifact to continue, a permitted stacked or same-file rebase needs serialization, conflict status is ambiguous (AA/UU/modify-delete), or a textually clean rebase may hide semantic, test, lint, policy, or inventory drift, or the resolution keeps both sides' guards for one failure mode, or a delete-side commit conflicts with trunk entries added inside the deleted block, or the conflict carries test-pinned values derived from source content that neither side can supply correctly, or the target pull request merged, closed, or lost its source ref between resolution work and the delivery mutation, or two lanes independently created the same file for one issue and the second to merge sees it as `AA` while either copy may be the narrower one, or every conflict resolves to the current target side because a sibling pull request already delivered the same intent and the reviewed head carries a delivered approval state, or an already-armed auto-merge on the same pull request can fire on the new head as soon as your rebase push turns its checks green, or a scripted resolution keeps only part of one conflict side and silently drops adjacent numbered steps, or a conflict was resolved by copying one side's whole file and the replayed commit's planned hunks are missing while its message still claims them, or a conflicted merge or rebase on a shared or slow filesystem produced a result that misses plain upstream files because the checkout had not finished when the paths were staged."
category: ci-cd
date: 2026-07-12
version: "2.9.0"
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
- The pull request already has an armed auto-merge request, so the delivery push
  can merge it at the new head without a fresh re-review.
- A script or a side-selection rule resolves conflicts in a document with ordered
  structure: headings, numbered steps, or table rows. A resolver that keeps only
  part of one side can drop adjacent entries while the file stays valid.
- A conflict was resolved by copying one side's whole file. The copy can silently
  drop the replayed commit's planned hunks while its commit message and PR body
  still claim them.
- A conflicted merge or rebase ran on a shared or slow filesystem, and the result
  is about to be staged or pushed. Upstream-added files can be absent from the
  working tree while the merge reports success, and a broad stage records them
  as deletions.

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

Two lanes that implement one issue in parallel can each create the same new file,
and the second to merge then conflicts as `AA`. A smaller file on either side is not
evidence that it is the narrower one. Prove the relation before you resolve:

```bash
git diff origin/<trunk> origin/<replayed> -- <path>   # trunk has, replayed lacks
git diff origin/<replayed> origin/<trunk> -- <path>   # replayed has, trunk lacks
```

When one direction shows only additions and the other only removals, the copy with
the additions is the superset and it keeps the capabilities the issue names. Take
that copy. Do not rebase a subset onto a superset: it reproduces the superset's
code or regresses it. When the replayed copy is the superset but the trunk copy is
the reviewed model, re-land the replayed copy as one commit on the trunk's model
instead of replaying each original commit through its own conflicts.

A replayed commit that deletes a block can conflict with a trunk edit inside that
same block. Read the deleted block and the trunk delta. Take the deletion when the
commit removes the whole artifact, for example because the value now comes from a
server response. Take the trunk delta when the commit only restructures the block
and the trunk additions must survive. After the rebase, search the tree for the
deleted name. A reference to it that no other commit explains is an incomplete
deletion.

Resolve according to intent:

| Conflict | Default disposition | Required check |
| --- | --- | --- |
| Generated lockfile | Remove and regenerate with the owning tool | Tool reports lock current |
| Generated marketplace/index | Keep current trunk, regenerate or reapply the unique delta | Schema/count/inventory check |
| Full rewrite vs small edit | Keep coherent rewrite, port the small edit | Whole-file semantic review |
| Same import line | Union symbols into one formatter-ordered import | Lint plus runtime import |
| Import symbol used by a later replayed commit (lint `F821` after the rebase) | Restore the symbol in the replayed commit that uses it | Lint passes on the final tree |
| Replayed commit removed the last use of an import (`F401` after the rebase) | Delete the import in that same commit | Lint passes on the final tree |
| Parallel source extraction | Prefer current trunk structure; add only unique behavior | Source diff and focused tests |
| Two competing guards or states for one failure mode | Keep the trunk design; delete the replayed branch's duplicate guard, helper, state, and tests | Trunk file diff is empty for that artifact, and the surviving guard's own tests pass |
| Parallel test addition | Union materially distinct tests | Test collection and run |
| Test-pinned content-derived values (digests, computed IDs) | Resolve the source content first; then recompute the pins from the merged content through the repository's own derivation; never copy either side's value | The focused consumer test passes on the recomputed values |
| Additive build/config blocks | Keep both valid blocks | Parser/configure step |
| Table, map, or block deleted by the replayed commit, with trunk entries added inside it | Take the deletion when the commit retires the whole artifact; take the trunk delta when the commit keeps the artifact | Grep the final tree for the deleted name; any surviving reference is a resolution defect |
| Policy prose | Pick the chronologically current contract, then update every restatement | Whole-file search and backing test |
| Every hunk resolves to the target side | Stop before you resolve or push. Prove the sibling delivery and the empty residual, then close the pull request | Sibling merge commit reachable from the target, plus an empty residual diff against the target |
| `AA` on a file that two lanes created independently for the same issue, where the target copy is smaller than the replayed copy | Do not take the target side on size alone. Diff the two copies in both directions and prove which is the superset. Take the superset; if the replayed copy is the superset, re-land it as one commit on the target model | One direction of the diff shows only target additions, the other shows only replayed-only removals, and the surviving copy keeps every capability the issue names |
| Already-upstream commit | Skip only after proving no unique delta remains | Empty/trivial trunk diff |

A wholesale side copy — `git show <side>:<path> > <path>` or
`git checkout --ours/--theirs <path>` — resolves the conflict and looks correct,
because the file is exactly one valid side. When trunk moved under a reviewed
commit, the copy takes trunk's whole file and silently drops the replayed
commit's planned hunks in that file. The commit message, PR body, and plan
still claim them, and no check that does not pin those hunks can fail. A real
delivery lost the scheduled-trigger and wrapper changes for a CI workflow this
way; a read-only simplify review found the gap against the plan.

Verify each replayed commit by hunk identity, not by file validity:

```bash
git diff "$trunk"...<original-head> -- <path>   # every planned hunk
git diff "$trunk"...HEAD            -- <path>   # replayed result
```

Every planned hunk must still appear in the replayed diff. A missing hunk needs
a new explicit resolution that restores it on top of the moved trunk content;
re-apply planned edits to the taken side instead of trusting the copy. Record
the hunk comparison in the resolution evidence.

Stage paths explicitly. Do not use `git add .` or `git add -A` in a conflict loop.
If a safety policy blocks checkout/restore shortcuts, reconstruct from read-only
objects and apply the desired content through an approved editor; do not bypass
the policy or use destructive reset commands.

A conflicted merge or rebase on a shared or slow filesystem can report success
while the working tree is still incomplete. Upstream-added files then have no
checkout, and a broad stage records them as deletions; the index looks staged
and the commit can succeed. After every conflicted merge or rebase, prove the
result against the trunk before the commit and the push. Before the commit, the
index holds the merge result, so compare the index; after the commit, compare
`HEAD`:

```bash
git diff --cached --stat "$trunk"                    # before the commit: only the PR's intended paths
git diff --name-status --cached "$trunk" | grep '^D' # before the commit: unexpected upstream "deletions"
git diff --stat HEAD "$trunk"                        # after the commit: the same check
```

A plain upstream file that the PR never touched must not appear. When it does,
abort (`git merge --abort`, `git rebase --abort`) and redo the merge. Confirm
the checkout completed — `git status --short` shows only the resolved conflict
paths — then stage explicit paths and re-verify. Do not repair the gap with
`git checkout "$trunk" -- <path>` inside the same merge: the missing tree
proves the checkout is incomplete, and a second operation can lose the same
objects again.

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

Always pass the editor override. A plain `git rebase --continue` opens the
commit-message editor, and a non-interactive harness blocks until the command
times out. If that happens, do not blind-retry: a killed process can leave
`.git/worktrees/<name>/index.lock` or a partial `rebase-merge` directory. Confirm
the lock is gone and the todo still lists your commit, then continue with both
overrides set:

```bash
ls "$(git rev-parse --git-dir)"/index.lock 2>/dev/null || echo "no lock"
ls "$(git rev-parse --git-dir)"/rebase-merge/git-rebase-todo
GIT_EDITOR=true GIT_SEQUENCE_EDITOR=true git -c commit.gpgsign=false rebase --continue
```

Then check signatures before the push. A replay creates new commit objects, and
the new objects can carry `%G?` = `N` even when the original head was signed. A
provenance gate rejects that new head:

```bash
git log --format='%h %G? %s' "$trunk"..HEAD   # expect G, never N
```

Re-sign before the push when any replayed commit shows `N`:

```bash
git log -1 --format='%B' > /tmp/msg.txt
git commit -S -s --amend -F /tmp/msg.txt
```

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
- the edited document's own structure: compare the heading list, numbered-step
  sequence, and table-row count in the result with each conflict stage. A
  scripted resolver that indexes only the first line of a multi-line side drops
  the remaining adjacent steps, and the result can still parse, lint, and pass
  every test that does not pin the inventory.
- generated lockfiles and manifests after dependency/config changes;
- test pins and adjacent assertions derived from source content that either side
  changed, recomputed from the merged content and never guessed.

Run the structural comparison before each push in a stack, not only at the end.
Each merged stack entry writes its result to the trunk, so a later branch that
restores dropped content does not undo the earlier regression.

```bash
# Compare the ordered structure of both stages with the resolved file.
git show :2:<path> | grep -nE '^(#{1,6} |[0-9]+[a-z]?\. )' > /tmp/ours.txt
git show :3:<path> | grep -nE '^(#{1,6} |[0-9]+[a-z]?\. )' > /tmp/theirs.txt
grep -nE '^(#{1,6} |[0-9]+[a-z]?\. )' <path> > /tmp/result.txt
diff /tmp/ours.txt /tmp/result.txt; diff /tmp/theirs.txt /tmp/result.txt
```

Every element in a stage and absent from the result needs an intentional
deletion reason. A count that drops without one is the defect, not a clean
resolution.

Regenerate stale mocks from the current implementation. Do not change production
code merely to satisfy expectations written for an abandoned branch design.

Label each lint or type failure by the commit that causes it. Place the repair in
that commit, not in `HEAD`. A repair amended onto `HEAD` attaches to an unrelated
commit and leaves the intermediate commit broken. Use an interactive rebase:

```bash
git rebase -i "$trunk"          # mark the offending commit with `edit`
<repair the import set>
git add <path> && git commit --amend --no-edit -S -s
git rebase --continue
```

Find the causing commit by searching history, not by the first commit that shows
the error:

```bash
git log --format='%h %s' "$trunk"..HEAD -- <path>
git show <commit>:<path> | grep -n '<symbol>'
```

Measure local test failures against a bounded baseline worktree at `"$trunk"`
with the same test command. Record both failure sets. The branch is acceptable
when its failures are a subset of the baseline failures. A new failure that is
absent from the baseline is a rebase defect; the environment cause is not.

Compare failing node identities, not totals. Equal failure counts can hold
different nodes, and a shared total then hides a branch-only defect. Refresh the
baseline to the same `"$trunk"` revision before you compare, so a stale baseline
tree does not produce either false result.

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

An inherited armed request is the opposite case, and it needs a check before the
push. Read the arm state now, not after the delivery:

```bash
gh pr view <N> --json autoMergeRequest,mergeStateStatus,labels \
  --jq '{armed: .autoMergeRequest, state: .mergeStateStatus, labels: [.labels[].name]}'
```

An armed request is not head-pinned. It merges the first head that satisfies the
branch protection, so your delivery push is a trigger: the new head turns its
checks green, and the forge merges it with no further action. A force-push may
clear the request on some hosts, but do not rely on that. When the request is
already armed, these hold:

- You did not arm it. It is a prior operator decision, and it can land the
  change before a re-review runs at the new head.
- Publish the consequence before the push: which head the approval label
  covers, and that the new head is not covered by that approval.
- Do not disarm or arm it on your own authority. Surface the state and continue
  the authorized delivery.
- After the merge lands, confirm the landed tree matches your prepared head
  (`git diff <prepared-head> <merge-commit>` prints nothing for the changed
  paths). Report the merge as the result, not as a failure.

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

### Clean merge that keeps both competing implementations

Tools that hold the replayed commit on top of current trunk can resolve a
conflicting hunk as the union of both sides. A union that compiles is still a
wrong resolution when the two sides implement opposite designs for one failure
mode. The classic shape is a branch that adds a fail-closed guard and a trunk
commit that makes the same path fail open. The result carries both guards, both
states, and both test suites, so the stricter guard silently wins.

Detect it before you trust the result. Read the resolved function as a whole, not
only the conflicted hunk, then list the end state of every state enum, guard
helper, and early return that either side touched. The decisive check is a diff
against trunk for each artifact: when trunk already implements the requested
design, the correct residual diff for that file is empty. A nonempty diff in an
artifact that trunk has fully superseded, with no review request that names the
change, is the union signature.

Resolve it by keeping the trunk design and deleting the replayed side's copy:
the duplicate guard, the helper that only that guard called, the extra state
member, the parser for the same error class, and every test that duplicates the
trunk tests. Then confirm the kept guard's own tests pass on the new head.
Do not add the replayed side's behavior to make the union consistent. Report the
deleted duplicate as part of the resolution, because the branch's earlier
commits and review records still describe it.

A pull request can also merge its own change mid-task. When an armed auto-merge
fires on your delivery head while you still hold the old head, the new trunk
commit **is** your change, squashed. Detect it before you classify it as
unrelated main movement:

```bash
git log --oneline -3 "$trunk"
gh pr view <N> --json state,mergeCommit,mergedAt   # state: MERGED
git diff --stat <prepared-head> <merge-commit> -- <changed paths>   # empty
```

Read the branch name in the trunk commit subject: a trailing `(#<N>)` naming
your own pull request proves the self-merge. Do this check before you decide
that trunk moved and a second rebase is required. A self-merge is not new trunk
movement. No rebase is needed, and a replay push would resurrect a ref for
content that already landed. Close out instead: confirm the content equivalence,
remove your own worktree, and post the one delivery comment. Do not push. Do not
rebase again.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Blanket side selection | Used `--ours` or `--theirs` for every conflict | Drops one branch's intent; rebase side names are counterintuitive | Read both stages and resolve per artifact |
| Lockfile hand merge | Manually combined generated lock state | Hashes and solver state are not safely mergeable | Regenerate with the owning tool |
| Marker-only review | Trusted no markers or a clean rebase | Semantic conflicts are outside Git's model | Run tests, lint, policy, inventory, and runtime checks |
| Union of two competing guards | Accepted the clean merge of a fail-closed guard onto a trunk that made the same path fail open | Both guards and both states survived, and the stricter one silently won | Diff each artifact against trunk; an empty diff is correct when trunk fully superseded it |
| Deleted block with trunk entries | Kept trunk's new entries because the hunk conflicted, so half the retired table survived with no other reference | The branch intent to drop the artifact is lost, and the leftover block can drift without a reader | When the replayed commit retires an artifact, take the deletion and grep the tree for every reference |
| Equal failure counts | Reported "also fails on trunk" from matching totals | The branch-only node and the trunk node were different tests | Compare node identities, not counts |
| Parallel hot-file rebases | Rebased the same-file cluster concurrently | Each merge re-conflicts the remaining branches | Use a smallest-diff-first serial train |
| Self-report acceptance | Trusted a rebase success report | Stale refs or a later push can preserve old ancestry | Compare merge base and inherited trunk behavior |
| Empty workflow retrigger | Pushed an empty commit for stale workflow policy | Reruns the same rejected workflow | An active task can rebase only when corrected workflow files are required; otherwise let CI/CD integrate |
| Scoped hook evidence | Ran hooks only on conflict-touched files | Misses whole-tree complexity and inventory checks | Run the full hook suite and tests |
| Unqualified force-push | Rewrote the remote without an explicit lease | Can overwrite new remote work | Pin the lease to the observed old SHA |
| Pushing on stale authorization | Replayed a completed repair after the target merged upstream during the work | Recreates a deleted source branch and duplicates integrated content | Refresh and re-read artifact state immediately before the mutation; a merged or ref-deleted target is a stop pending content-equivalence proof |
| Resolving an all-target-side conflict to keep the PR alive | Rebased a branch whose every conflicting hunk showed the same correction already on the target side, resolved both sides to the target text, and force-pushed | The result had an empty residual, so the new head carried no product value, invalidated the check record for the old head, and started a second review of nothing | When a rebase would resolve every hunk to the target side, stop before the write; prove the sibling delivery, then close the PR |
| Closing from the conflict markers alone | Read the three conflicted files, saw the same wording on both sides, and closed the PR | The decision was correct, but the evidence named no sibling merge commit and no acceptance check, so a reader could not audit it | Add the sibling merge commit reachability, the issue closing reference, and the acceptance-term search to the close evidence |
| Treating a delivered approval label as current authority | Read the delivered approval state at the reviewed head as a reason to keep driving the PR to merge | The label attests one reviewed head, not that the change is still absent from the target branch | Re-check the residual against the target branch first; the label cannot make an empty change useful |
| Plain `rebase --continue` in a non-interactive harness | Ran `git rebase --continue` after resolving the conflict | The commit-message editor opened and the command blocked until the timeout killed it | Always set `GIT_EDITOR=true GIT_SEQUENCE_EDITOR=true`; on a timeout, confirm no `index.lock` or partial `rebase-merge` remains before the retry |
| Pushing the rebase head without reading the arm state | Pushed a rebase of a conflicted PR that already carried an armed auto-merge request from an earlier operator action | The push turned the new head's checks green and the forge merged it before a re-review ran at that head | Read `autoMergeRequest` before the push; an armed request is not head-pinned, so the delivery push is a merge trigger |
| Reading the self-merge as trunk movement | Saw a new trunk commit and prepared a second rebase against it | The commit subject named the same pull request, so trunk already held the exact prepared content | Read the `(#<N>)` suffix before a second rebase; a self-merge needs the close-out, not a replay |
| Programmatic side selection kept one line of a multi-line conflict side | Wrote a resolver that read only the first element of each side and joined the chosen lines | Adjacent numbered steps inside the same conflict block disappeared; the file parsed, linted, and passed every test because no test pinned the step inventory | Preserve each whole side or a verified union, then diff the heading and step inventory against both stages before every push in a stack |
| Wholesale side copy dropped the replayed commit's planned hunks | Resolved a workflow-file conflict by taking the trunk side's whole file, then re-applying planned edits from memory | Two planned hunks were silently lost; the commit message and PR body still claimed them, and a review found the gap against the plan | After each replayed commit, diff each resolved path against the original head (`git diff "$trunk"...<original-head> -- <path>` versus `HEAD`); every planned hunk must still appear |
| Broad stage after a conflicted merge on shared storage | Merged the trunk into a PR branch in a worktree, resolved conflicts, and staged everything with `git add -A` | The conflicted merge's working-tree checkout was still incomplete, so upstream-added files (a vendored patch stack and CI workflows) had no checkout; the stage recorded them as deletions and the result looked clean | Before the commit, compare the index against the trunk (`git diff --cached --stat "$trunk"` shows only the PR's paths) after every conflicted merge or rebase; on a mismatch, abort and redo the merge instead of repairing individual paths |

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
already landed upstream. The push requires a signed replayed head and a recorded
read of the auto-merge arm state.

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
