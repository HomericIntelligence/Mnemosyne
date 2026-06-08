---
name: git-branch-state-triage-and-recovery
description: "Diagnose and recover branches that have entered an invalid or obsolete state. Use when: (1) a branch is many commits behind main and its remote tracking ref is gone — determine whether any net-new contribution remains before creating a PR, (2) a branch has no common ancestor with main ('fatal: refusing to merge unrelated histories') and needs content extraction and recreation, (3) a stacked PR was retargeted and lint/CI fix commits made after retarget are orphaned from the prerequisite PR and must be cherry-picked, (4) fix commits exist locally but cannot fast-forward push to a remote PR branch because histories diverged after a rebase — cherry-pick onto the remote tip instead"
category: tooling
date: 2026-06-07
version: "1.0.0"
user-invocable: false
history: git-branch-state-triage-and-recovery.history
tags: [git, branch, triage, recovery, stale, superseded, orphan, diverged, merge-base, cherry-pick, fork-point, diff-filter, unrelated-histories, non-fast-forward]
---

# Git Branch State Triage and Recovery

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-07 |
| **Objective** | Diagnose what state a branch is in (stale/superseded, orphaned/unrelated history, or diverged from remote) and recover it cleanly |
| **Outcome** | Success — unified triage tree: confirm-and-discard superseded branches, extract+recreate orphan branches, reset+cherry-pick diverged branches |
| **Verification** | verified-ci |

## When to Use

Use this skill whenever a branch is in an unexpected or unmergeable state. The root question
is always: **what state is this branch in, and how do I recover it?** Three distinct states:

**State A — Stale / superseded by main:**
- A branch is many commits behind main **and** its remote tracking ref is gone (`[gone]` in `git branch -vv`)
- The task is "get all open PRs merged" — check `gh pr list --state open` first; if zero open PRs the premise has changed
- A `git diff origin/main...HEAD` shows a large file count difference but you suspect most of it is merge noise
- Staged files with AD status in `git status --short` (added in index, deleted from working dir)

**State B — Orphan / unrelated history:**
- `git merge-base` returns nothing between branch and main
- Error: "fatal: refusing to merge unrelated histories"
- Branch appears to have a completely different commit history (suspect: pushed from wrong repo)
- PR shows massive unexpected file changes

**State C — Diverged from remote:**
- `git push` fails with "non-fast-forward" on a feature branch
- `git status` shows "Your branch and 'origin/<branch>' have diverged"
- A fix commit exists locally but the remote has accumulated additional commits (e.g. after a rebase or stacked-PR retarget)
- A fix plan assumed the remote was behind, but it actually has more commits than local

## Verified Workflow

### Quick Reference

```bash
# === Triage: which state am I in? ===
git branch -vv | grep "$(git rev-parse --abbrev-ref HEAD)"   # [gone] = remote ref deleted
git merge-base HEAD origin/main || echo "ORPHAN: no common ancestor"  # empty = State B
git status                                                    # "diverged" = State C

# === State A: stale / superseded by main ===
gh pr list --state open                          # check premise FIRST
FORK=$(git merge-base HEAD origin/main)           # fork point
git ls-tree --name-only -r HEAD skills/ | sort > /tmp/head.txt
git ls-tree --name-only -r origin/main skills/ | sort > /tmp/main.txt
comm -23 /tmp/head.txt /tmp/main.txt              # HEAD-only files (maybe new, maybe old)
git log --diff-filter=D --oneline origin/main -- <path> | head -1  # how main disposed of it
# staged-index no-op check:
git ls-files --stage | awk '{print $1, $4}' | sort > /tmp/staged.txt
git ls-tree -r origin/main | awk '{print $3, $4}' | sort > /tmp/mainh.txt
comm -23 /tmp/staged.txt /tmp/mainh.txt           # staged files NOT on main = true new work

# === State B: orphan / unrelated history ===
git fetch origin <branch>
git merge-base origin/main origin/<branch>        # empty = orphan
git log --oneline origin/<branch> | tail -10      # oldest commits reveal origin repo
git ls-tree --name-only origin/<branch> | head    # unexpected files = wrong repo
git show origin/<branch>:<path> > /tmp/extracted   # extract before deleting
git log --oneline origin/main -- <path>           # CHECK: already merged on main?
git push origin --delete <branch>                 # delete broken branch

# === State C: diverged from remote ===
git log --oneline origin/<branch>..HEAD           # local-only commits
git log --oneline HEAD..origin/<branch>           # remote-only commits (often forgotten!)
git merge-base HEAD origin/<branch>               # common ancestor
git reset --hard origin/<branch>                  # absorb remote, AFTER confirming fix applies
git cherry-pick <fix-sha>                         # apply only the targeted fix
```

### Detailed Steps

#### State A — Stale-branch-superseded-by-main diagnosis

1. **Check the premise**: run `gh pr list --state open` before any branch archaeology. If
   there are zero open PRs, the task "get all PRs merged" is already done — report and stop.
2. **Find the fork point**: `git merge-base HEAD origin/main` gives the SHA where the branch
   diverged. All analysis is relative to this point.
3. **Three-way file inventory**: compare `git ls-tree` outputs for HEAD and origin/main on
   the relevant directories, piped through `sort` then `comm` → three sets: HEAD-only,
   main-only, both.
4. **For each HEAD-only file**: run `git log --diff-filter=D --oneline origin/main -- <path>`.
   A commit message containing "consolidate", "merge", or "absorb" means main intentionally
   deleted it via a consolidation PR. An empty result means the file genuinely never reached
   main (rare for an old branch).
5. **For each file in both**: compare `version:` frontmatter. If main's version number is
   strictly greater, main has the newer copy and the branch's change is stale.
6. **Staged index check**: if `git status --short` shows many AD-status files (added in index,
   deleted in working tree), hash-compare `git ls-files --stage` against `git ls-tree
   origin/main`. If every staged hash matches a main hash, the staged index is a no-op.
7. **Apply the three-condition test** — a branch is fully superseded when **all three** hold:
   - Its deletions are already absent from main, AND
   - Its modified files have lower version numbers than main's, AND
   - Its "new" files are already present on main.

   When all three hold the branch has zero net contribution and can be discarded.

#### State B — Orphan-branch recovery (no common ancestor)

1. **Diagnose**: `git fetch origin <branch>` then `git merge-base origin/main
   origin/<branch>`. No output (exit 1) = no common ancestor.
2. **Understand the divergence**: `git log --oneline origin/main..origin/<branch>` (commits
   on branch not in main) and the reverse. Then `git log --oneline origin/<branch> | tail -10`
   — unfamiliar "Initial commit" lines reveal the branch was created from a different repo.
3. **Inspect contents**: `git ls-tree --name-only origin/<branch> | head` — unexpected files
   (e.g. `.mojo-version` in a Python project) confirm a wrong-repo push.
4. **Extract valuable content** before any deletion:
   ```bash
   git show origin/<branch>:plugins/cat/name/SKILL.md > /tmp/SKILL.md
   ```
5. **Check if already merged**: `git log --oneline origin/main -- <path>`. Often the real
   content already landed via a correct PR and the orphan is just a stale duplicate — then no
   recreation is needed, just delete.
6. **Delete and (if needed) recreate**:
   ```bash
   git push origin --delete <branch>
   git checkout main && git pull origin main
   git checkout -b <branch>
   cp /tmp/extracted <path>/ && git add . && git commit -m "feat: recreated from broken branch"
   git push -u origin <branch>
   ```

   **Root cause / prevention**: orphan branches typically come from running `/learn` (or any
   commit-and-push flow) from one project's working directory while pushing to another's
   remote. Always verify `git remote -v` matches the expected repository before pushing.

#### State C — Diverged-branch cherry-pick fix

1. **Diagnose the divergence**: `git status` shows "diverged, N and M different commits". Run
   both `git log --oneline origin/<branch>..HEAD` (local-only) AND `git log --oneline
   HEAD..origin/<branch>` (remote-only). The remote-only side is the one usually forgotten —
   a fix plan may claim "just push" while the remote has accumulated commits since.
2. **Understand each side**: `git show origin/<branch>:path/to/file` to see the remote's
   current version; `git show <fix-sha> --stat` to see exactly what the local fix touches.
   Confirm the fix applies cleanly on top of the remote tip.
3. **Reset local to remote tip** (only after confirming the fix applies):
   `git reset --hard origin/<branch>`.
4. **Cherry-pick the minimal fix**: `git cherry-pick <fix-sha>`. Resolve any conflicts, then
   `git cherry-pick --continue`. Cherry-pick the targeted fix only — never the full local
   commit stack, which may duplicate an equivalent commit already on the remote.
5. **Verify**: `git status` should show "ahead by 1 commit"; `git show HEAD --stat` confirms
   the fix is present. Then push (fast-forward now succeeds).

   This same pattern recovers stacked-PR fix commits: when a stacked PR is retargeted and
   lint/CI fix commits made after the retarget become orphaned from the prerequisite, reset to
   the correct remote tip and cherry-pick the orphaned fix commits onto it.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Treating HEAD-only files as unmerged value | Assumed "file present in HEAD but not in main" = "work not yet on main" | Most HEAD-only files were OLD files that main subsequently deleted or consolidated through later PRs after the branch diverged | Always check HOW a file left main (`--diff-filter=D`) before assuming it was never there |
| Using plain `git log` to find deletions | `git log --oneline origin/main -- <path>` showed nothing | Plain log only shows commits that touched the file; it does not surface the deletion commit reliably | `--diff-filter=D` is required to find the commit that removed a file |
| Treating AD status as uncommitted work | `git status --short` showed hundreds of AD lines and looked like staged changes needing attention | AD status is normal for branches created in worktrees not fully restored to disk — files exist in the index but not on disk | AD means "added in index, deleted from working dir"; verify hashes match main before treating as new work |
| Direct push after local commits (diverged) | Assumed local was ahead of remote and pushed | Branches had diverged; remote had 13 additional commits not present locally | Always check `HEAD..origin/<branch>` not just `origin/<branch>..HEAD` before pushing |
| Treating a fix plan at face value | Plan said "2 commits ahead, just push" | Plan was written before the remote accumulated additional commits | Re-diagnose actual remote state with `git log --oneline HEAD..origin/<branch>` before acting |
| Keeping local commits and merging (diverged) | Would merge the local cleanup commit with the remote's equivalent | Remote already had an equivalent cleanup commit; merge would create a duplicate | Cherry-pick the minimal fix only, not the full local commit stack |
| Deleting an orphan branch before extraction | Tempted to just `git push --delete` the broken branch | Risked losing valid skill content that lived only on the branch tip | Extract content (and check whether it is already on main) before deleting |

## Results & Parameters

### State A — Superseded decision matrix

| Condition | Check Command | "Stale" Verdict |
| --------- | ------------- | --------------- |
| Deletions already absent from main | `comm -23 head.txt main.txt` → each: `git log --diff-filter=D origin/main -- <path>` | consolidation commit found for all |
| Modified files have lower version | `grep "^version:" skills/<f>.md` vs `git show origin/main:skills/<f>.md \| grep "^version:"` | branch version < main version |
| "New" files already on main | `comm -23 staged_hashes.txt main_hashes.txt \| wc -l` | result = 0 |

Expected output for a fully superseded branch:

```text
# gh pr list --state open
No pull requests match your search
# comm -23 /tmp/head.txt /tmp/main.txt | wc -l
1193    ← looks alarming, but all are old deletions
# git log --diff-filter=D --oneline origin/main -- skills/old-skill.md | head -1
a3f2b1c feat(skill-merge): consolidate 12 skills into automation-bundle (C086)
# comm -23 staged_hashes.txt main_hashes.txt | wc -l
0       ← zero true new files; staged index is a no-op
```

### State B — Orphan signs and recovery checklist

Signs of a wrong-repo push: unfamiliar "Initial commit" at `git log <branch> | tail`;
unexpected files at `git ls-tree --name-only <branch>`; massive ahead/behind counts; commit
messages referencing a different project.

- [ ] Verify branch has no merge-base with main
- [ ] Identify valuable content on branch tip
- [ ] Check whether content is already on main (`git log origin/main -- <path>`)
- [ ] Extract files before deletion
- [ ] Delete remote branch
- [ ] Recreate from main only if content not already merged

### State C — Reset + cherry-pick recipe

```bash
git log --oneline origin/<branch>..HEAD       # local-only commits
git log --oneline HEAD..origin/<branch>       # remote-only commits
git merge-base HEAD origin/<branch>           # common ancestor SHA
git reset --hard origin/<branch>              # absorb all remote commits
git cherry-pick <fix-sha>                     # apply only the targeted fix
git log --oneline -3                          # fix should be single HEAD commit
git status                                    # "ahead by 1 commit"
```

Cherry-picks of small, focused single-file fixes rarely conflict, even on heavily diverged
branches, because they touch a narrow region the remote version differs in only slightly.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectMnemosyne | Branch `feature/myrmidon-merge-triage` (32 ahead, 525 behind, remote gone) — confirmed fully superseded; no PRs opened | State A |
| ProjectMnemosyne | Branch `skill/debugging/fixme-todo-cleanup-v2` pushed from ProjectOdyssey's history — no merge-base; content already on main; deleted | State B |
| ProjectOdyssey | PR #3197, issue #3088 — BF16 test skip; reset to remote (13 remote-only commits) + cherry-pick fix | State C |

## References

- [git-branch-state-triage-and-recovery.history](git-branch-state-triage-and-recovery.history) — superseded source skills (verbatim)
