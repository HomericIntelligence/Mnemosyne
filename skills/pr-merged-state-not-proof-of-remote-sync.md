---
name: pr-merged-state-not-proof-of-remote-sync
description: "GitHub API state, your local `origin/<branch>` ref, and your working tree are three independent surfaces that diverge until `git fetch` runs — in BOTH the read direction (`gh pr view` says MERGED but refs are stale) and the write direction (a local branch and `origin/<same-name>` point at different commits because a parallel process pushed). A matching branch NAME does not imply matching CONTENT. Use when: (1) about to report `PR is merged` based on `gh pr view`, (2) auditing whether a file is present/absent in main after a deletion or rename PR, (3) spawning sub-agents that grep or scan the working tree expecting it matches main, (4) running deletion-validation or migration-completeness workflows, (5) reasoning about whether `origin/main` reflects the latest merges, (6) a sub-agent reports `feature X didn't execute / files missing / wave didn't run` immediately after PRs were marked merged, (7) about to push a local `<issue>-impl` / feature branch to update a PR when a parallel automation process may have pushed to the same branch name, (8) merging main into a local branch and pushing it to a PR branch you did not author end-to-end."
category: ci-cd
date: 2026-05-29
version: "1.1.0"
user-invocable: false
verification: verified-local
history: pr-merged-state-not-proof-of-remote-sync.history
tags:
  - gh-cli
  - git-fetch
  - audit
  - sub-agents
  - merge-verification
  - working-tree
  - branch-divergence
  - parallel-automation
  - fast-forward-gate
  - rev-parse
---

# `gh pr view` MERGED Is Not Proof Of Local/Remote Sync

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-29 (v1.1.0) |
| **Objective** | Stop trusting a local ref as the source of truth for a remote PR — in BOTH directions: (READ) reporting "PRs merged / files deleted from main" based on `gh pr view --json state` alone, and (WRITE) pushing a local branch to update a PR when a parallel process may have pushed a different commit to the same branch name. Require remote-ref verification before any claim or push, and pin audit sub-agents to a specific git ref |
| **Outcome** | Successful — established that GitHub API state, local `origin/<branch>` refs (refresh only on `git fetch`), and the working tree (whatever branch is checked out) are three independent surfaces. v1.1.0 adds the write direction: a local `<issue>-impl` branch and `origin/<issue>-impl` can point at entirely different implementations when a parallel automation process pushes to the same name; gate pushes on a `merge-base --is-ancestor` fast-forward check |
| **Verification** | verified-local — v1.0.0 (read direction) grounded in ProjectOdyssey PRs #5458/#5459/#5460 audit-swarm false positives; v1.1.0 (write direction) grounded in ProjectKeystone PR #571 / branch `512-impl`, where a parallel `.issue_implementer` automation pushed a different implementation to `origin/512-impl` than the local background-agent commit, caught before a clobbering push |
| **History** | [changelog](./pr-merged-state-not-proof-of-remote-sync.history) |

## When to Use

- About to report **"PR is merged"** to the user based on `gh pr view --json state` or `mergedAt`
- About to claim **"file X is gone from main"** or **"directory Y was deleted"** after a deletion PR
- Spawning **audit sub-agents** that will grep, find, or scan the working tree expecting it reflects `main`
- Running **deletion-validation**, **migration-completeness**, or **wave-execution-audit** workflows
- Reasoning about whether `origin/main` reflects the latest merges (it doesn't, until you fetch)
- A sub-agent reports "feature X didn't execute / files missing / wave didn't run" immediately after PRs were marked merged — likely a stale-ref or wrong-branch hallucination
- Coordinating multiple stacked PRs and you need to confirm earlier ones landed in main before basing later work on that assumption
- **(WRITE direction)** About to push a local `<issue>-impl` / feature branch to update an open PR, when a **parallel automation process** (e.g. `.issue_implementer`, an issue-backlog runner, or another agent) may have pushed to the **same branch name**
- The local branch and `origin/<same-name>` were produced by **different processes** for the **same issue** — branch names collide but contents may differ
- Merging `main` into a local branch and pushing it to a PR branch you **did not author end-to-end** — verify you are fast-forwarding the real PR head, not overwriting it

## The Core Insight

Three independent state surfaces diverge, and `git fetch` is the only thing that reconciles the local view:

1. **GitHub API state** — what `gh pr view --json state,mergedAt,mergeCommit,headRefOid` returns. Authoritative for "did GitHub accept the merge" / "what commit backs the PR right now", lags ≤ seconds behind reality.
2. **Local remote-tracking ref** — `origin/main`, `origin/<branch>`. Only updates when you run `git fetch origin`. Can be hours/days stale.
3. **Working tree / local branch** — whatever branch is currently checked out, and whatever commit your **local** `<branch>` ref points at. Reflects that local commit's files, not the remote PR head's. Sub-agents that grep the working tree are auditing the checked-out branch, not main.

**Read direction:** `gh pr view` returning MERGED only proves (1). Reporting "merged to main" or auditing "what's in main" requires verifying (2) and choosing the right ref for (3).

**Write direction (the symmetric trap):** A local branch named `512-impl` proves nothing about what backs PR #571. If a parallel process pushed a different implementation to `origin/512-impl`, then your local `512-impl` (carrying your own agent's commit) is **stale relative to the real PR head**. A matching branch **NAME** does not imply matching **CONTENT**. Merging `main` into the local branch and pushing it would fast-forward-clobber the wrong implementation onto the PR. Before pushing to any PR branch you did not author end-to-end, re-derive your work from `origin/<pr-branch>` and gate the push on a `merge-base --is-ancestor` fast-forward check.

## Verified Workflow

### Quick Reference

```bash
# Before reporting "PR is merged" or auditing main:
git fetch origin --quiet
git log origin/main --oneline -10                       # confirm merge commits present

# For deletion audits (file should be GONE from main):
git show origin/main:path/to/file 2>/dev/null && echo "STILL PRESENT" || echo "DELETED"

# For presence audits (file should EXIST in main):
git show origin/main:path/to/file >/dev/null 2>&1 && echo "PRESENT" || echo "MISSING"

# For broad audits — use a fresh clone, never the working tree of a feature branch:
REPO_URL=$(git remote get-url origin)
REPO_NAME=$(basename "$REPO_URL" .git)
rm -rf "/tmp/${REPO_NAME}-audit"
git clone --depth 5 --branch main "$REPO_URL" "/tmp/${REPO_NAME}-audit"
# Run audits inside /tmp/${REPO_NAME}-audit, not the working tree

# For sub-agents — pin them to a specific ref in the prompt:
# "Audit the state of origin/main (NOT the current working tree). Use
#  `git show origin/main:<path>` or run inside /tmp/<repo>-audit. The working
#  tree is on branch <X> which is NOT main."

# === WRITE direction: before pushing a local branch to update a PR ===
git fetch origin --quiet

# 1. Divergence check — does your local branch match the remote PR head?
git rev-parse HEAD                      # your local commit
git rev-parse origin/<pr-branch>        # the commit backing the open PR
# If these DIFFER, your local branch is NOT the PR head. STOP and investigate.

# 2. Confirm by comparing commit subjects (different implementations look different)
git log --oneline -3 HEAD
git log --oneline -3 origin/<pr-branch>
# e.g. "...automatic off-host forwarding" (yours) vs
#      "...automatic off-host NATS promotion" (the parallel automation's) = DIVERGED

# 3. Re-derive your work from the REAL remote PR head, not the local ref:
git worktree add /tmp/sync-<branch> --detach origin/<pr-branch>   # --detach pins remote head
cd /tmp/sync-<branch>
git switch -c sync-<branch>
git merge origin/main                   # do your update on top of the real PR head

# 4. Fast-forward GATE — must be an ancestor or you'd overwrite someone else's PR:
git merge-base --is-ancestor origin/<pr-branch> HEAD && echo "FF-safe" || \
  { echo "NOT a fast-forward of the PR head — STOP, do not push"; exit 1; }

# 5. Only now push (updates the PR by fast-forward, never clobbers):
unset GH_TOKEN GITHUB_TOKEN; git push origin HEAD:<pr-branch>
```

### Detailed Steps

1. **Fetch before trusting any local ref.** `git fetch origin --quiet` is cheap. Run it before any claim that touches "main".

2. **Verify merge commits in `origin/main`'s log, not in `gh pr view` output.**

   ```bash
   gh pr view 5460 --json state,mergeCommit --jq '.mergeCommit.oid'   # e.g., abc123def
   git log origin/main --oneline | grep abc123de                       # must return a line
   ```

   If the commit is not in `origin/main`'s log after a fetch, the merge has not propagated to the branch ref yet (rare, but possible during high-throughput auto-merge cascades) — wait and re-fetch.

3. **For deletion audits, use `git show origin/main:<path>`.** Non-zero exit means the file is absent in main. Do NOT `ls`/`find` the working tree — that's the checked-out branch, not main.

4. **For broad multi-file or directory audits, clone fresh.** A shallow clone to `/tmp/<repo>-audit --branch main` guarantees the audit surface is main and only main. Auditors cannot accidentally scan a feature branch.

5. **Pin every audit sub-agent to a specific git ref.** In the sub-agent's prompt, explicitly state:
   - Which branch/ref it must audit (e.g., `origin/main`)
   - How to query that ref (`git show origin/main:<path>` or the fresh clone path)
   - That the working tree is NOT main, with the actual branch name

6. **For stacked PRs, verify the parent landed in `origin/main` before reporting the child is "ready to merge to main"** — auto-merge on a child whose parent has only the API-state of MERGED can race in obvious and non-obvious ways.

### Pushing to a PR branch you do not own end-to-end (WRITE direction)

When a **parallel automation process** (an issue-backlog runner like `.issue_implementer`,
or another agent) targets the **same `<issue>-impl` branch names** as your own background
agents, the local branch and the remote PR head can be **completely different
implementations of the same feature**. The trap: your worktree's `512-impl` points at your
background agent's commit (files in `core/`), while the OPEN PR #571 is backed by the
automation's commit on `origin/512-impl` (files in `transport/`). The branch names match;
the contents diverged.

7. **Divergence check before any push to a PR branch.** Fetch, then compare:

   ```bash
   git fetch origin --quiet
   git rev-parse HEAD                 # local commit
   git rev-parse origin/512-impl      # commit backing PR #571
   ```

   If they differ, your local branch is **not** the PR head. Confirm with subjects —
   different implementations have different commit messages:

   ```bash
   git log --oneline -3 HEAD              # "...automatic off-host forwarding"
   git log --oneline -3 origin/512-impl   # "...automatic off-host NATS promotion"
   ```

   Different subject + different files = a parallel process owns the PR head. STOP.

8. **Re-derive your work from the remote PR head, not the local ref.** A plain
   `git worktree add <dir> <branch>` checks out the **local** branch ref (which has
   diverged). Pin to the remote head explicitly with `--detach origin/<branch>`:

   ```bash
   git worktree add /tmp/sync-512-impl --detach origin/512-impl
   cd /tmp/sync-512-impl
   git switch -c sync-512-impl
   git merge origin/main            # do the update on top of the REAL PR head
   ```

9. **Gate the push on a fast-forward check.** The remote PR head MUST be an ancestor of
   what you are about to push, or you would rewrite/overwrite someone else's PR:

   ```bash
   git merge-base --is-ancestor origin/512-impl HEAD \
     && echo "FF-safe — origin/512-impl is an ancestor of HEAD" \
     || { echo "NOT a fast-forward — STOP, you'd clobber the PR"; exit 1; }
   unset GH_TOKEN GITHUB_TOKEN; git push origin HEAD:512-impl
   ```

   If `--is-ancestor` returns non-zero, do not push. Investigate who owns the PR head and
   reconcile, or open your own separate PR.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Trusted `gh pr view <N> --json state` returning MERGED as proof commits were in main | After arming auto-merge on PRs #5458/#5459/#5460, `gh pr view` returned MERGED within ~30s for all three. Reported "all merged" to the user without running `git fetch`. Subsequent audit sub-agents scanned the stale feature-branch working tree and reported "files not deleted" | API state and remote-ref state diverge: `gh pr view` queries GitHub directly; local refs (`origin/main`) only refresh on `git fetch`. Working-tree scans on feature branches show that branch's files, not main's | Always `git fetch origin && git log origin/main --oneline -10` before claiming a merge propagated. For deletion audits, use `git show origin/main:<path>` or a fresh shallow clone — never the working tree |
| Spawned 4 audit sub-agents against the working tree without specifying which branch they should audit | 3 of 4 sub-agents reported "Wave 2 didn't execute" with 10+ false positives each. Working tree was checked out on branch `5452-autograd-phase2-substrate`, not main. Sub-agents trusted the working tree as ground truth for "what's in main" | Sub-agents default to scanning whatever the working tree shows. If the prompt doesn't pin them to a ref, they silently audit the wrong branch and produce confident, wrong answers | Pin every audit sub-agent to a specific git ref in the prompt: either `cd /tmp/<repo>-audit` (fresh clone of main), or instruct them to use `git show origin/main:<path>`. Tell them the actual current branch and that it is NOT main |
| Trusted the local branch named `512-impl` as the PR's content and merged main into it | A parallel `.issue_implementer` automation and my own background agents both produced `512-impl` branches. My worktree's `512-impl` pointed at my agent's commit (files in `core/`); the OPEN PR #571 was backed by the automation's commit on `origin/512-impl` (files in `transport/`). I was about to `git merge origin/main` into the local branch and push to update the PR | It was a stale local commit, not the PR head. Pushing would have fast-forward-clobbered PR #571 with the wrong implementation. A matching branch **NAME** does not mean matching **CONTENT** when an external process pushes to the same name | Before pushing to a PR branch, `git fetch` then compare `git rev-parse HEAD` vs `git rev-parse origin/<branch>` and the `git log --oneline` subjects. If they differ, your local branch is not the PR head — re-derive from `origin/<branch>` |
| Assumed `git worktree add <dir> <branch>` checks out the remote PR head | Ran `git worktree add /tmp/wt 512-impl` expecting it to give me the commit backing PR #571 | `git worktree add <dir> <branch>` checks out the **local** branch ref, which had diverged from `origin/512-impl`. I'd have continued working on the wrong (local) implementation | Use `git worktree add <dir> --detach origin/<branch>` to pin to the remote head explicitly, then `git switch -c sync-<branch>`. Gate the eventual push on `git merge-base --is-ancestor origin/<branch> HEAD` |

## Results & Parameters

**Verification one-liner** (before claiming "PR N merged to main"):

```bash
git fetch origin --quiet && \
  COMMIT=$(gh pr view "$N" --json mergeCommit --jq '.mergeCommit.oid') && \
  git log origin/main --oneline | grep -q "${COMMIT:0:8}" && \
  echo "VERIFIED: $COMMIT is in origin/main" || \
  echo "NOT YET IN origin/main — wait and re-fetch"
```

**Push-safety one-liner** (before pushing a local branch to update a PR you didn't author end-to-end):

```bash
# B = the PR branch name (e.g. 512-impl)
git fetch origin --quiet && \
  if [ "$(git rev-parse HEAD)" = "$(git rev-parse origin/$B)" ]; then
    echo "IN SYNC: local HEAD == origin/$B"
  elif git merge-base --is-ancestor "origin/$B" HEAD; then
    echo "FF-safe: origin/$B is an ancestor of HEAD — push is a fast-forward"
  else
    echo "DIVERGED: origin/$B is NOT an ancestor of HEAD — pushing would clobber the PR. STOP."
  fi
```

**Re-derive-from-remote-head pattern** (when the divergence check says DIVERGED):

```bash
B=512-impl
git fetch origin --quiet
git worktree add "/tmp/sync-$B" --detach "origin/$B"   # --detach pins the REMOTE head
( cd "/tmp/sync-$B" && git switch -c "sync-$B" && git merge origin/main )
# then re-run the push-safety one-liner inside /tmp/sync-$B before pushing
```

**Fresh-clone audit pattern**:

```bash
audit_main_fresh() {
  local repo_url="$1"            # e.g., https://github.com/HomericIntelligence/ProjectOdyssey
  local repo_name
  repo_name=$(basename "$repo_url" .git)
  local audit_dir="/tmp/${repo_name}-audit"
  rm -rf "$audit_dir"
  git clone --depth 5 --branch main "$repo_url" "$audit_dir" --quiet
  echo "$audit_dir"             # caller cd's into it
}
```

**Sub-agent prompt template** (paste into any audit sub-agent task):

```text
AUDIT SCOPE: You are auditing the state of `origin/main` in <REPO>.
The current working tree is on branch `<BRANCH_NAME>`, which is NOT main.
Do NOT trust `ls`, `find`, or `grep` against the working tree as evidence
about main.

To inspect a single file in main:        git show origin/main:<path>
To inspect a directory listing in main:  git ls-tree -r origin/main <path>
To run broad audits against main only:   cd /tmp/<repo>-audit  (fresh shallow clone)

Before starting, run: git fetch origin --quiet
```

**Real session evidence**: PRs #5458, #5459, #5460 on HomericIntelligence/ProjectOdyssey reported MERGED by `gh pr view` within ~30 seconds of `gh pr merge --auto` arming. A 4-agent audit swarm immediately afterward scanned the working tree (which was on branch `5452-autograd-phase2-substrate`) and 3 of 4 agents produced 10+ false positives each claiming "Wave 2 didn't execute" — they were grepping a feature branch's files, not main's, while local `origin/main` was also stale because no `git fetch` had run between the merges and the audit.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| HomericIntelligence/ProjectOdyssey | JIT demolition Wave 1.5 — PRs #5458/#5459/#5460 reported MERGED by `gh pr view`; audit swarm on stale feature-branch working tree hallucinated "Wave 2 didn't execute" with 10+ false positives per agent (2026-05-26 session) | Working tree branch: `5452-autograd-phase2-substrate`; local `origin/main` was stale because no `git fetch` ran between merge and audit |
| ProjectKeystone | WRITE direction (2026-05-29) — parallel `.issue_implementer` automation + own background agents both produced `<issue>-impl` branches. Local `512-impl` pointed at the background agent's commit (files in `core/`); OPEN PR #571 was backed by the automation's commit on `origin/512-impl` (files in `transport/`). About to merge main + push, which would have clobbered #571 | Caught via `git rev-parse HEAD` ≠ `git rev-parse origin/512-impl` and divergent commit subjects ("off-host forwarding" vs "off-host NATS promotion"). Re-derived from `origin/512-impl` via `--detach`, merged main, confirmed `merge-base --is-ancestor` fast-forward, pushed safely |
