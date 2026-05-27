---
name: pr-merged-state-not-proof-of-remote-sync
description: "`gh pr view --json state` returning MERGED does NOT prove the merge commit is in your local main, your origin/main ref, or even in any local checkout. The GitHub API and local git refs diverge until `git fetch` runs. Use when: (1) about to report `PR is merged` to the user based on `gh pr view`, (2) auditing whether a file is still present/absent in main after a deletion or rename PR, (3) spawning sub-agents that will grep or scan the working tree expecting it matches main, (4) running deletion-validation or migration-completeness workflows, (5) reasoning about whether `origin/main` reflects the latest merges, (6) a sub-agent reports `feature X didn't execute / files missing / wave didn't run` immediately after PRs were marked merged."
category: ci-cd
date: 2026-05-26
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - gh-cli
  - git-fetch
  - audit
  - sub-agents
  - merge-verification
  - working-tree
---

# `gh pr view` MERGED Is Not Proof Of Local/Remote Sync

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-26 |
| **Objective** | Stop reporting "PRs merged" or "files deleted from main" based on `gh pr view --json state` alone; require remote-ref verification before any claim and pin audit sub-agents to a specific git ref |
| **Outcome** | Successful — established that `gh pr view` queries GitHub directly while local refs (including `origin/main`) only refresh on `git fetch`, and that sub-agents auditing the working tree silently scan whatever branch is checked out (not main) |
| **Verification** | verified-ci — protocol grounded in real session events where PRs #5458/#5459/#5460 on HomericIntelligence/ProjectOdyssey reported MERGED within ~30s of auto-merge arming, yet a subsequent audit swarm scanning the working tree on branch `5452-autograd-phase2-substrate` hallucinated "Wave 2 didn't execute" with 10+ false positives per agent because local refs were stale and the working tree wasn't main |
| **History** | n/a (initial version) |

## When to Use

- About to report **"PR is merged"** to the user based on `gh pr view --json state` or `mergedAt`
- About to claim **"file X is gone from main"** or **"directory Y was deleted"** after a deletion PR
- Spawning **audit sub-agents** that will grep, find, or scan the working tree expecting it reflects `main`
- Running **deletion-validation**, **migration-completeness**, or **wave-execution-audit** workflows
- Reasoning about whether `origin/main` reflects the latest merges (it doesn't, until you fetch)
- A sub-agent reports "feature X didn't execute / files missing / wave didn't run" immediately after PRs were marked merged — likely a stale-ref or wrong-branch hallucination
- Coordinating multiple stacked PRs and you need to confirm earlier ones landed in main before basing later work on that assumption

## The Core Insight

Three independent state surfaces diverge:

1. **GitHub API state** — what `gh pr view --json state,mergedAt,mergeCommit` returns. Authoritative for "did GitHub accept the merge", lags ≤ seconds behind reality.
2. **Local remote-tracking ref** — `origin/main`. Only updates when you run `git fetch origin`. Can be hours/days stale.
3. **Working tree** — whatever branch is currently checked out. Reflects that branch's files, not main's. Sub-agents that grep the working tree are auditing the checked-out branch, not main.

`gh pr view` returning MERGED only proves (1). Reporting "merged to main" or auditing "what's in main" requires verifying (2) and choosing the right ref for (3).

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

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Trusted `gh pr view <N> --json state` returning MERGED as proof commits were in main | After arming auto-merge on PRs #5458/#5459/#5460, `gh pr view` returned MERGED within ~30s for all three. Reported "all merged" to the user without running `git fetch`. Subsequent audit sub-agents scanned the stale feature-branch working tree and reported "files not deleted" | API state and remote-ref state diverge: `gh pr view` queries GitHub directly; local refs (`origin/main`) only refresh on `git fetch`. Working-tree scans on feature branches show that branch's files, not main's | Always `git fetch origin && git log origin/main --oneline -10` before claiming a merge propagated. For deletion audits, use `git show origin/main:<path>` or a fresh shallow clone — never the working tree |
| Spawned 4 audit sub-agents against the working tree without specifying which branch they should audit | 3 of 4 sub-agents reported "Wave 2 didn't execute" with 10+ false positives each. Working tree was checked out on branch `5452-autograd-phase2-substrate`, not main. Sub-agents trusted the working tree as ground truth for "what's in main" | Sub-agents default to scanning whatever the working tree shows. If the prompt doesn't pin them to a ref, they silently audit the wrong branch and produce confident, wrong answers | Pin every audit sub-agent to a specific git ref in the prompt: either `cd /tmp/<repo>-audit` (fresh clone of main), or instruct them to use `git show origin/main:<path>`. Tell them the actual current branch and that it is NOT main |

## Results & Parameters

**Verification one-liner** (before claiming "PR N merged to main"):

```bash
git fetch origin --quiet && \
  COMMIT=$(gh pr view "$N" --json mergeCommit --jq '.mergeCommit.oid') && \
  git log origin/main --oneline | grep -q "${COMMIT:0:8}" && \
  echo "VERIFIED: $COMMIT is in origin/main" || \
  echo "NOT YET IN origin/main — wait and re-fetch"
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
