---
name: stacked-pr-retarget-lint-fix-orphan
description: "When PR-B is retargeted onto PR-A's branch, only the commits present at retarget time fast-forward in. Later commits on PR-B's branch (CI/lint fixes) stay orphaned from PR-A and must be cherry-picked. Use when: (1) two open PRs are stacked via gh pr edit --base, (2) CI/lint fix lands on the dependent PR's branch after retarget, (3) the same failure later appears on the prerequisite PR."
category: ci-cd
date: 2026-05-26
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: [stacked-pr, retarget, cherry-pick, ci, lint, github]
---

# Stacked PR Retarget Lint Fix Orphan

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-26 |
| **Objective** | Recover from CI/lint failures that re-appear on a prerequisite PR after a fix was pushed only to the dependent (retargeted) PR's branch. |
| **Outcome** | Successful — cherry-pick of the orphan fix onto the prerequisite branch restores CI parity. |
| **Verification** | verified-ci (PR #1976, commit `1aa1ca86` cherry-picked from `b2a3150d`) |

## When to Use

- Two open PRs where B amends A; both initially targeted `main`.
- You retargeted B via `gh pr edit <B> --base <A-branch>` so B is now stacked on A.
- CI failed on B → you pushed a fix commit (e.g., markdownlint) to B's branch.
- Later, the identical CI/lint failure appears on A.
- `git log <A-branch>..<B-branch> --oneline` shows commits on B that A is missing — including your fix.

Related: see `[[feedback_pr_target_branches_not_main]]` (user memory) for the upstream
rule that produces this scenario — always stack PRs onto branches, never main.

Sibling skills (different scenarios):

- [[cherry-pick-fix-diverged-pr]] — same-content / different-SHA divergence from rebase
- [[diverged-branch-cherry-pick-fix]] — reset local to remote, then cherry-pick
- [[fix-rebased-ci-pr-stack]] — CI failures across a stack rebased onto main
- [[orphan-branch-recovery]] — branches with no common ancestor

## Verified Workflow

### Quick Reference

```bash
# 1. Identify the orphan commit(s) on the dependent branch that A is missing
git -C <repo> fetch origin
git -C <repo> log origin/<prereq-branch>..origin/<dependent-branch> --oneline

# 2. Worktree off the prerequisite branch (isolation — never touch shared clone HEAD)
git -C <repo> worktree add /tmp/fix-prereq origin/<prereq-branch>
cd /tmp/fix-prereq

# 3. Cherry-pick the orphan fix commit
git cherry-pick <orphan-sha>

# 4. Verify the same lint/test now passes locally
npx markdownlint-cli2 <changed-files>   # or whatever CI runs

# 5. Push the prereq branch
git push origin HEAD:<prereq-branch>

# 6. Clean up
cd - && git -C <repo> worktree remove /tmp/fix-prereq
```

### Detailed Steps

1. **Diagnose**: confirm CI failure on prerequisite PR is identical to one already
   fixed on the dependent PR. Run `git log <prereq>..<dependent> --oneline` against
   the remote refs to see exactly which commits are orphaned from the prerequisite.

2. **Pick the right SHA**: choose the smallest commit that contains the fix (not a
   squash that includes unrelated content). `git show <sha> --stat` confirms scope.

3. **Worktree isolation**: never `git checkout` the prerequisite branch in the
   shared clone — other agents (e.g., `/advise`) may be reading it. Use
   `git worktree add /tmp/<name> origin/<prereq-branch>`.

4. **Cherry-pick + verify**: apply the fix, then re-run the exact lint/test command
   CI runs. If it fails, the orphan commit may have depended on context not present
   on the prerequisite — abort and resolve manually.

5. **Push fast-forward**: pushing to the prerequisite branch is a fast-forward (you
   started from its tip). No `--force` needed.

6. **Prevention going forward**: when stacking PRs, push lint/CI fixes to the
   **prerequisite** branch first, then rebase the dependent on top. That way the
   fix flows down the stack automatically.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Trusted GitHub retarget to propagate all commits | Assumed retargeting PR-B onto PR-A's branch would auto-include later PR-B commits in PR-A | Retarget is a one-shot fast-forward at retarget time; subsequent commits on PR-B's branch don't flow back to PR-A's branch | Cherry-pick subsequent CI/lint fixes onto the prereq branch explicitly, or land lint fixes on prereq branch FIRST then rebase dependent |
| Re-ran CI on prerequisite hoping shared base would carry the fix | `gh run rerun` on PR-A after PR-B's branch had the fix | PR-A's branch SHA is unchanged — CI runs the same unfixed commit | Re-running CI never helps unless the branch tip moved; fixes must land on the prerequisite branch itself |
| Considered force-pushing dependent's history onto prerequisite | Thought rebasing dependent's history into prerequisite would migrate the fix | Would have polluted PR-A with unrelated amendment commits from PR-B and required force-push to a PR under review | Use cherry-pick of the specific fix commit, not bulk history migration |

## Results & Parameters

**Concrete recovery from this session (HomericIntelligence/ProjectMnemosyne)**:

| Field | Value |
|-------|-------|
| Prerequisite PR | #1976 (skill v1.0.0) |
| Prerequisite branch | `skill/workaround-demolition-wave-strategy` |
| Dependent PR | #1978 (v1.1.0 amendment) |
| Dependent branch | `skill/amend-demolition-partition-by-bug` |
| Orphan fix commit | `b2a3150d` (markdownlint MD031/MD040/MD032/MD022 fix) |
| Squash commit also on dependent | `b66c6c3d` (v1.1.0 content squash) |
| Recovery commit on prereq | `1aa1ca86` (cherry-pick of `b2a3150d`) |

**Diagnostic command output that confirmed the orphan**:

```bash
$ git log origin/skill/workaround-demolition-wave-strategy..origin/skill/amend-demolition-partition-by-bug --oneline
b2a3150d fix(lint): markdownlint MD031/MD040/MD032/MD022
b66c6c3d feat: amend workaround-demolition-wave-strategy skill (v1.1.0)
```

`b2a3150d` was present on the dependent branch but missing from the prerequisite —
hence the same lint failure recurred when CI ran on PR #1976.

**Prevention rule** (stack-discipline): when retargeting PR-B onto PR-A's branch via
`gh pr edit B --base A-branch`, treat A's branch as the canonical landing zone for
any CI/lint fixes that affect shared files. Push fixes to A first, then `git rebase`
B onto the new A tip.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| HomericIntelligence/ProjectMnemosyne | PR #1976 / #1978 stacked-PR markdownlint recovery, 2026-05-26 | Cherry-pick `b2a3150d` → `1aa1ca86` restored CI on prerequisite |
