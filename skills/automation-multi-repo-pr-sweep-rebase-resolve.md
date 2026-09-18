---
name: automation-multi-repo-pr-sweep-rebase-resolve
license: BSD-3-Clause
description: "Inspect an authorized PR backlog across repositories when review alone leaves checks, conflicts, or review threads unresolved. Select repairs from live policy and actual blockers."
history: automation-multi-repo-pr-sweep-rebase-resolve.history
category: tooling
date: 2026-06-28
version: "1.1.0"
user-invocable: false
verification: verified-ci
tags:
  - multi-repo
  - pr-sweep
  - rebase-resolve
  - hephaestus-review-prs
  - merge-train-cascade
  - ci-throughput
  - red-main-first
  - auto-merge
  - github
  - homericintelligence
  - worktree-per-pr
  - resolveReviewThread
---

# Multi-Repo PR Sweep: Rebase + Resolve to Drive a Backlog Green and Merged

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-28 |
| **Objective** | Drive a large backlog of author-scoped (mvillmow) PRs to green + merged across many HomericIntelligence repos in one session, when `hephaestus-review-prs` alone leaves them unmerged. |
| **Outcome** | Successful. One session resolved ~97/108 mvillmow PRs across 13 repos; 89 merged. Remaining were regressive PRs left for manual re-authoring or CI-throughput-throttled (merged as runners freed). |
| **Verification** | verified-ci (PRs went green in CI and squash-merged on `main`; commit signatures verified `verified==true`). |

## When to Use

- `hephaestus-review-prs` (the automation loop) ran but PRs are still open / `BLOCKED` with all checks green.
- You have a big backlog of PRs **authored by one account** spread across many repos and want them merged, not just reviewed.
- You need to decide whether a documented task-phase exception permits a rebase or CI/CD should integrate the branch.
- An armed `--auto --squash` PR sits `BLOCKED` and you must tell apart: unresolved review threads vs. CI runner backlog vs. a red `main` blocking every PR.
- A **merge train** of PRs touching shared files (CHANGELOG, pixi.lock, `_required.yml`, coverage.xml) keeps re-conflicting as siblings merge.
- After rebasing a PR branch onto a moved `main`, a plain `git push` is rejected non-fast-forward.

## Verified Workflow

### Current applicability

Use [verify-pr-ready](verify-pr-ready.md) for live policy, affected validation, and evidence
reuse. A branch behind main is not itself blocked. During active work, rebase only for a blocker
or required main content. After task completion, rebase only for a host-reported merge conflict;
otherwise CI/CD or the merge queue integrates main. Keep required CI and exact-head review before
merge. PR publication can precede validation if pending results are clear.
Cleanup is separate from rebasing. Historical verification below does not verify this
policy correction or the current version of an external tool.

The historical sweep exposed these tool limits. Check the installed version before
assuming that a limit still applies:

1. It did not perform needed integration in the captured cases. Main moving alone does not invalidate required checks.
2. It pushes fix **commits** but does **not resolve the GitHub review-THREAD objects** -> with `required_review_thread_resolution=true` (the `homeric-main-baseline` ruleset) PRs stay `BLOCKED` with everything green.
3. It does a plain `git push` after a history-rewriting rebase -> non-fast-forward rejection, **and** its worktrees auto-clean on exit, so the rebase fix is **lost**.
4. It has **no `--repo` flag** — it operates on the CWD repo, so it must be invoked from inside each submodule/clone (not the Odysseus meta-repo root).

The working pattern is the **rebase + resolve sweep**: dispatch **one sub-agent per repo** into a **fresh `/tmp/sweep-<repo>` clone** (never the shared submodule, whose branch state and worktrees are shared). Per PR the sub-agent:

1. `git fetch origin`
2. Inspect conflicts and dependencies. Rebase only when applicable, preserving signatures, authorship, and one matching final DCO trailer.
3. Resolve conflicts **semantically** (understand both sides; do not blindly take theirs/ours).
4. Fix any residual CI failures the rebase surfaces.
5. Use a normal push for a fast-forward update. Use `git push --force-with-lease` only for an authorized history rewrite after checking the remote head.
6. Resolve only threads that the review workflow authorizes after the exact-head response and review. A pushed fix alone is not authority to close a thread.
7. Verify the tip commit is signed: `gh api repos/<o>/<r>/commits/<sha> --jq .commit.verification.verified` returns `true`.

The orchestrator then **strict-verifies** each PR and arms auto-merge:

- Verify live repository policy, required checks, required approvals, exact-head review,
  signatures, and applicable thread-resolution requirements. Do not require `CLEAN` merely
  as a substitute for those gates, or assume that a named check is optional.
- Use the repository-supported merge method or queue after all required gates pass.
  An auto-merge command can merge immediately; confirm authority and the exact head first.

**Shared CI failure:** A failure on main can affect multiple PRs. Confirm that it applies
to each candidate before choosing a shared fix. Use a separate authorized PR where needed;
do not change unrelated dependencies merely because main is red.

**Overlapping PRs:** Inspect actual conflicts as siblings merge. Integrate only where
needed. Do not rebase and push solely to test whether a PR is redundant. Compare its full
intended change with the target and preserve ambiguous work.

**CI-THROUGHPUT CEILING:** force-pushing ~80 PRs saturates GitHub's runner pool — armed PRs sit `BLOCKED` with all checks **QUEUED** (not stuck, just waiting); auto-merge fires as runners free up. This is the real rate limit once structural blockers are gone.

### Quick Reference

```bash
# --- Per-repo sweep (one sub-agent per repo, fresh clone) ---
REPO=ProjectHermes; ORG=HomericIntelligence
git clone "https://github.com/$ORG/$REPO" "/tmp/sweep-$REPO"
cd "/tmp/sweep-$REPO"
# hephaestus-review-prs has NO --repo flag — must run from inside the clone (CWD):
hephaestus-review-prs   # optional first pass; then fix its 3 gaps manually below

# --- Only after an active-task blocker or required main content, or a reported completed-PR conflict ---
git fetch origin
git checkout <pr-branch>
git -c commit.gpgsign=true rebase origin/main
# ...resolve conflicts semantically, fix residual CI...
git push --force-with-lease

# --- Inspect threads; resolve only with authority from the exact-head review workflow ---
gh api graphql -f query='
  query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){
    pullRequest(number:$n){reviewThreads(first:50){nodes{id isResolved}}}}}' \
  -f o="$ORG" -f r="$REPO" -F n=<pr>
gh api graphql -f query='
  mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' \
  -f id=<threadId>

# --- Verify the tip commit signature is valid ---
gh api repos/$ORG/$REPO/commits/<sha> --jq .commit.verification.verified   # -> true

# --- After live policy gates and exact-head review pass, use the permitted merge method ---
gh pr view <pr> --repo $ORG/$REPO \
  --json mergeStateStatus,headRefOid,statusCheckRollup
gh pr merge <pr> --auto --squash --repo $ORG/$REPO   # only if live policy permits squash
```

### Detailed Steps

1. **Discover** the author-scoped PR backlog per repo: `gh pr list --repo <o>/<r> --author <user> --json number,mergeStateStatus`.
2. Inspect required-check failures and determine whether a shared cause affects the candidates.
3. **Fan out** one sub-agent per repo into `/tmp/sweep-<repo>` (fresh clone — never the shared submodule).
4. Per PR: bind the head, inspect actual blockers, rebase only for a documented active-task exception or reported completed-PR conflict, publish the fix, and obtain exact-head review. Retain required CI and signing gates.
5. Verify all live repository gates, then use the authorized merge method or queue. Target movement alone does not require another rebase.
6. Leave **regressive** PRs untouched for manual re-authoring; let CI-throughput-throttled armed PRs merge as runners free.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | Ran `hephaestus-review-prs` alone and expected it to merge the backlog | 15/30 PRs "failed" — plain `git push` after rebase was rejected non-fast-forward, and the review THREADs were never resolved so PRs stayed BLOCKED-all-green; the loop's auto-cleaned worktrees LOST the fix | Preserve the worktree. Use a lease only for an authorized history rewrite, and resolve threads only under the exact-head review workflow. |
| 2 | Ran the loop from the wrong CWD (the Odysseus meta-repo root) | `hephaestus-review-prs` has NO `--repo` flag — it targeted the wrong repo's issues/PRs | Always invoke it from inside each individual repo clone (CWD = that repo). |
| 3 | Armed `--auto --squash` on all overlapping PRs simultaneously | Maximal merge-train cascade: every merge advanced `main`, re-conflicting siblings that touched shared files (CHANGELOG, pixi.lock, `_required.yml`, coverage.xml) | Serialize the arm, or expect and budget for multiple re-rebase passes; the cascade converges as the queue shrinks. |
| 4 | Treated `BLOCKED`-all-green PRs as broken/stuck | They were not broken — either unresolved review threads (review-gate) OR a CI runner backlog with all checks QUEUED | Inspect unresolved threads and queued checks. Confirm that a shared failure affects each candidate before selecting a shared fix. |

## Results & Parameters

- **Scale:** ~97/108 mvillmow PRs resolved across 13 HomericIntelligence repos in one session; **89 merged**.
- **Repos where `main` was red on a required check (fixed first):** Hermes, Agamemnon, Proteus, Odysseus (`security`/`dependency-scan` via `pip-audit`).
- **Required checks:** read live policy; historical check names do not establish current requirements.
- **Merge method:** the captured repositories used squash. Check current repository settings and queue requirements.
- **Ruleset:** the captured cases required thread resolution. Apply current policy and review authority before resolving a thread.
- **Signature email:** sign with the noreply email `4211002+mvillmow@users.noreply.github.com` so rewritten/re-signed commits stay `verified==true` and survive the GH007 email-privacy push block (see cross-link below).
- **Throughput ceiling:** force-pushing ~80 PRs saturates the runner pool; armed PRs sit BLOCKED/QUEUED and auto-merge as runners free — this is the rate limit, not a failure.

### Related skills (cross-links)

- `automation-reuse-repo-clone-with-worktree-per-pr` — the clone/worktree-per-PR reuse mechanics this sweep builds on.
- `github-auto-merge-ci-gating-merge-method` — auto-merge CI gating and the squash merge-method requirement.
- `automation-review-loop-unpushed-fix-oscillates` — narrower review-loop failure mode (unpushed fix oscillation).
- `dependabot-lockfile-rebase-regenerate-resign` — regenerating + re-signing lockfiles when rebasing dependency PRs (the pixl.lock / CHANGELOG re-conflict case).
- `multi-repo-pr-automation-loop-orchestration` — the driver-side honest-reporting / report-vs-live-state failures of the loop itself.
- `reference_signed_commits_email_privacy` (Odysseus memory) — the noreply email `4211002+mvillmow@users.noreply.github.com` that keeps signatures valid past GH007.
