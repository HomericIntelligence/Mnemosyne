---
name: pr-review-two-dot-vs-three-dot-diff
description: "When reviewing OPEN auto-impl / long-lived feature PRs for MERGE-READINESS, diff with two-dot (git diff origin/main..branch) NOT three-dot (origin/main...branch). Use when: (1) reviewing a stale *-auto-impl or long-lived feature branch that is N commits behind origin/main, (2) a three-dot diff shows a scary regression (e.g. a timeout 7200s->300s) that turns out to already be on main via a sibling PR, (3) deciding whether re-merging a stale branch is safe or would REVERT sibling work already landed on trunk, (4) you suspect a PR is a zombie whose feature already merged, (5) verifying a PR's true revert footprint before issuing a GO/NO-GO verdict."
category: tooling
date: 2026-06-27
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [pr-review, git-diff, two-dot, three-dot, merge-base, stale-branch, merge-readiness, zombie-pr, auto-impl, revert-footprint]
---

# PR Review: Two-Dot vs Three-Dot Diff for Merge-Readiness

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-27 |
| **Objective** | Review OPEN auto-impl / long-lived feature PRs for merge-readiness without being fooled by phantom changes that already landed on main |
| **Outcome** | Verified: two-dot diff reveals the true effect of re-merging a stale branch; three-dot produces false verdicts |
| **Verification** | verified-local |

## When to Use

- Reviewing a stale `*-auto-impl` or long-lived feature branch that is N commits behind `origin/main`.
- A three-dot diff (`origin/main...branch`) shows a scary regression (e.g. a timeout `7200s -> 300s`) that turns out to already be on main via a sibling PR.
- Deciding whether re-merging a stale branch is safe or would REVERT sibling work already landed on trunk.
- You suspect a PR is a zombie whose feature already merged.
- Verifying a PR's true revert footprint before issuing a GO/NO-GO verdict.

## Verified Workflow

When reviewing an OPEN auto-impl / long-lived feature PR for MERGE-READINESS, diff with
**two-dot** (`git diff origin/main..branch`) NOT **three-dot** (`origin/main...branch`).

**Why:** The loop's `*-auto-impl` branches in ProjectHephaestus are frequently STALE
(4–27 commits behind `origin/main`) because sibling refactor PRs keep landing on trunk.
The three-dot diff (`A...B`) shows everything changed on the branch SINCE THE MERGE-BASE —
including code that has SINCE been merged to main by OTHER PRs. A reviewer reading the
three-dot diff sees "phantom" additions/changes that are already on main, producing FALSE
verdicts. The two-dot diff (`A..B`) shows the literal current delta between the two refs:
files it reports as DELETED are sibling work on main that the stale branch would REVERT.

> **Note:** GitHub's own squash-merge rebases the stale PR onto current main at merge time,
> so it does NOT blindly apply the two-dot diff. The danger is a MANUAL hand-merge of the
> stale diff, which WOULD revert trunk. Let the loop's `tidy`/rebase step or GitHub's
> squash-rebase handle stale branches; a manual merge-readiness pass must replicate that
> (rebase onto current main, re-run CI) before any verdict is actionable.

### Quick Reference

```bash
# 1. ALWAYS check staleness FIRST — how far behind main is the branch?
git rev-list --count origin/<branch>..origin/main   # commits behind; if >0, branch needs rebase before its diff is meaningful for merge

# 2. For "what does re-merging ACTUALLY do to main", use TWO-DOT:
git diff origin/main..origin/<branch>               # files shown as DELETED = sibling work on main this stale branch would REVERT
git diff origin/main..origin/<branch> --diff-filter=D --name-only   # explicit revert footprint

# 3. Check whether the PR's feature is ALREADY MERGED (zombie PR):
git log origin/main --oneline | grep -iE "<pr-number>|<pr-title-keywords>"
git diff origin/main origin/<branch> -- <key-file>  # empty = already on main, close the PR

# 4. Three-dot (...) is fine for "what did the AUTHOR change on the branch", but NOT for merge-readiness on a stale branch.
```

### Detailed Steps

1. **Check staleness before reading any diff.** Run
   `git rev-list --count origin/<branch>..origin/main`. If the count is `> 0`, the branch
   is behind main and its three-dot diff is contaminated by sibling work already on trunk.
2. **Read the two-dot diff for merge-readiness.** `git diff origin/main..origin/<branch>`
   shows the literal current difference. Files reported as DELETED are sibling work the
   stale branch would REVERT if hand-merged.
3. **Enumerate the revert footprint explicitly.**
   `git diff origin/main..origin/<branch> --diff-filter=D --name-only` lists every file a
   manual merge of the stale branch would delete from trunk.
4. **Confirm the change is real, not a stale-merge-base artifact.** When a value looks like
   a regression, check what main actually has:
   `git show origin/main:<path>`. If main already has the "new" value, the three-dot diff
   was lying.
5. **Detect zombie PRs.** `git log origin/main --oneline | grep -iE "<pr-keywords>"` plus
   `git diff origin/main origin/<branch> -- <key-file>` (empty output means the feature is
   already on main — close the PR rather than merging).
6. **Do not hand-apply a stale diff.** Defer to the loop's `tidy`/rebase step or GitHub's
   squash-rebase, which rebase onto current main before merging.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | Reviewed the three-dot diff (`origin/main...branch`) for merge-readiness | Branch was 4 commits behind main; three-dot showed timeout values relative to the stale merge-base, making an already-on-main 300s value look like a 7200->300 regression introduced by the PR | Use two-dot for merge-readiness; check commits-behind first |
| 2 | Assumed GitHub `mergeable=MERGEABLE` meant safe to hand-merge | GitHub squash-merge actually rebases the stale PR onto current main at merge time, so it does NOT blindly apply the two-dot diff — but a MANUAL merge of the stale diff would revert trunk | Let the loop's tidy/rebase step or GitHub's own squash-rebase handle stale branches; don't hand-apply a stale diff |

## Results & Parameters

**Concrete evidence (verified 2026-06-27, ProjectHephaestus):**

- **PR #1642** ("centralize agent timeout constants"): the three-dot diff made it look like
  the PR changed the planner agent timeout `7200s -> 300s` (a scary 24x reduction, flagged
  NO-GO). But `git show origin/main:hephaestus/automation/claude_timeouts.py` showed main
  ALREADY had 300s (via `AGENT_PLAN_TIMEOUT`, landed by a sibling PR). The "regression" was
  a stale-merge-base artifact, not a real change. The real two-dot diff showed the PR would
  actually REVERT files already on main.
- **PR #1640**: 27 commits behind main; its two-dot diff would DELETE 61 files already on main.
- **PR #1603**: feature already MERGED (commit on main); re-merging the stale branch would
  REVERT `cli.utils.__all__` + COMPATIBILITY rows and break the `api_table_docs` validator.
- All 6 "ready" PRs reviewed were 4–27 commits behind main.

**Key parameters / takeaways:**

- The loop's own `tidy`/rebase step normally rebases these branches before merge; a manual
  merge-readiness pass MUST replicate that (rebase onto current main, re-run CI) before any
  verdict is actionable.
- Several "open" auto-impl PRs are zombies whose work already landed on main — detect them
  with `git diff origin/main origin/<branch> -- <key-file>` returning empty.
- Two-dot (`A..B`) = current delta between refs (merge-readiness / revert footprint).
  Three-dot (`A...B`) = changes since merge-base (author intent only; contaminated by
  sibling merges on a stale branch).
