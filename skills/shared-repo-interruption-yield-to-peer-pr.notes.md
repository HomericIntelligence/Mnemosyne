# Notes: Inventory and Yield Interrupted Work When Parallel Sessions Share a Repository

Supporting evidence for `shared-repo-interruption-yield-to-peer-pr.md`. Generalized from a
verified-live campaign; identifiers are intentionally omitted.

## Campaign context

- Repository: a shared Python tooling repository. Actor sessions: two interactive agent sessions
  plus two automation loops, all working concurrently on one host over several days.
- Prepared work: a feature-removal change ("removal fold") assembled in a dedicated worktree:
  ~150 file deletions, ~20 file edits, one new seam module, two authored policy documents, and a
  drafted pull-request body plus two issue comments on disk.
- Interruption: a harness server restart killed all background processes, including a delegated
  verification run and the pending commit.

## Timeline evidence

1. Restart. Background shells died; the verification subagent later reported the worktree had
   vanished mid-run (its final batches were file-disappearance artifacts, not real failures).
2. Probe results after the restart:
   - `git worktree list`: the fold worktree and its source worktree were gone; a dozen new peer
     worktrees existed.
   - Default branch had advanced three merge commits, one of which *re-added* part of the content
     the fold removed (an automation-loop merge that ran while the session was down).
   - The fold branch survived, reset forward to the new base; no fold commit existed.
   - `git ls-tree -r origin/main | grep -c <feature-marker>`: the content targeted for removal
     was still present on the default branch (148 paths).
   - `gh pr list --state open`: one open peer pull request whose head branch contained the tip
     commit that removed the same content *again* (deduced from its tree: zero marker matches in
     the peer worktree's source and test trees), including the part the loop re-added.
   - The signature seam module was found inside the peer's integration worktree by
     `grep -rl <signature-string>`, not by pull-request title — the peer pull request's title
     named a different feature entirely.
   - `git stash list`: an entry labeled as preserved work from the fold worktree, created by the
     peer session before it removed the worktree.
3. Operator-confirmed dispositions:
   - Yield the removal track to the peer pull request (no competing pull request).
   - Safe-delete the orphaned fold branch: `git branch -d` succeeded because its tip was an
     ancestor of the default branch; git prints a merge warning but deletes.
   - Remove only the dead worktree path's generated content (~0.7 MB test cache).
   - Defer five queued salvage branches: the peer pull request rewrites the code they target,
     so rebasing before its merge means rebasing twice. Re-entry trigger: peer pull request
     merges; then each salvage gets an applicability check against the new tree.
   - Keep uncovered plan parts: policy documentation (blocks the automation loop from merging
     the same removed content again) and issue bookkeeping, re-scoped as a small follow-up pull
     request after the peer lands.
   - Annotate the drafted pull-request body and one drafted comment with a top-of-file
     superseded marker so a later session cannot post them against the retired vehicle.

## Contention symptom detail

- Symptom: a required commit-gate test suite (thousands of selected tests, ~10–11 minutes wall
  time on the host) died at ~26% progress with zero FAILED lines and no summary section.
- Cause: concurrent heavyweight suites from two sessions (a separate pre-commit verification
  suite plus a peer session's hook suite) on one host.
- Recovery: retry the same commit solo; the suite passed unchanged. No test edits were needed.
- Decision rule added to the main entry: a silent mid-run kill with zero FAILED lines on a shared
  host is scheduled for a serial retry, not for debugging. Do not burn investigation time on the
  suite itself.

## Object-database recovery fallback (not needed, verified shape)

Staged-but-uncommitted content from a force-removed worktree remains in the object database
until garbage collection prunes unreachable objects (default grace ~2 weeks). Recovery shape:

```bash
git fsck --unreachable 2>/dev/null | grep blob | head -400 > /tmp/unreach.txt
# for each candidate blob: git cat-file -p <sha> | grep -l <known-marker-string>
```

In this campaign the fallback was unnecessary because a 4.2 MB source-of-truth patch existed
outside the worktree and the peer's tree already contained the recovered content. Record it as
the last-resort path only.

## Why a new entry instead of an amendment

Three existing entries cover adjacent intents (see the main entry's References). Each covers
recovering or resuming one's *own* interrupted work (single-lane loop recovery, loop relaunch
salvage, stash recovery after a concurrent reset). None contains the peer-delivery decision
branch: audit delivered work first, and yield the track when a peer's pull request covers the
intent. The trigger (interruption plus parallel sessions plus an overlapping peer delivery),
the decision branch (yield versus resume), and the disposal rules are new. The
environment-pinning entry covers host test attribution; this entry only references it.

## Campaign evidence: an assigned drive target that was already merged

Supporting evidence for the version 1.1.0 addition. Generalized from a verified-live session;
identifiers are intentionally omitted.

- Context: several parallel automation waves worked one shared repository. An interrupted
  interactive session held one local worktree with a signed commit that implemented documented
  per-model value ceilings on selected configuration paths. The commit was never pushed.
- A restart directive assigned the session to adopt and drive a named sibling pull request
  (review rounds, green checks, merge automation) that automation had opened with the same
  intent while the session was down. The directive named a fallback: report and stop if the
  pull request had closed meanwhile.
- State probe: the pull-request view showed state MERGED and a merge timestamp that fell in
  the interruption window. The linked issue view showed CLOSED with a completed reason at the
  same timestamp. Only one pull request referenced the issue, so there was no sibling to
  reconcile.
- Equivalence: a whole-tree diff of the local branch against the fetched default branch was
  unreadable, because unrelated waves had advanced the default branch across dozens of files.
  The targeted checks decided the classification:
  - `git show origin/<default>:<context-file>` and a grep at the ceiling paths confirmed that
    each pinned value matched the local variant, including the value the merge directive had
    called out as the point of conflict with an earlier merged policy.
  - `git show --stat <merge-commit>` showed a broader scope (twenty-six files, including
    adjacent contexts and golden tests) that carried the same pinned values.
  - An attempted fetch of the merged head branch returned "couldn't find remote ref": the
    source branch had been deleted after the merge, another sign that the tree equality check
    was the wrong probe.
- Disposal: the local branch tip was not an ancestor of the default branch (its values landed
  through different commits), so the safe-delete form was not applicable. The worktree was
  clean. The branch stayed as an unpushed local backup with its tip recorded, per the
  directive.
- Outcome: no competing pull request, no review rounds on a merged head, no label changes on a
  completed issue. The assigned drive collapsed into a verified-closure report.
