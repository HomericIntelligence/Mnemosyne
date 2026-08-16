---
name: rebase-stale-automation-pr-onto-refactored-main
license: BSD-3-Clause
description: "Semantic conflict-resolution and clean-history rebuild patterns for stale automation-authored PRs after a large refactor. Use when: (1) a queued/DIRTY PR was branched many commits behind and now conflicts after a big landed refactor, (2) a PR routes to a pipeline stage/symbol the refactor deleted, (3) a merge queue crawls because stale-base PRs fail a newly landed gate, (4) an automation update created a DCO-less merge commit, (5) a stale PR adds a workflow job that misses current security hardening, (6) two PRs claim the same ADR number, (7) an AST-guard registry conflicts with renamed call sites, (8) deciding whether a PR is genuinely superseded, (9) a PR history contains an unrelated duplicated commit and must be rebuilt from current main, (10) a rewritten PR needs an exact-head strict-review gate and rollback lease."
category: ci-cd
date: 2026-07-20
version: "1.1.0"
user-invocable: false
verification: unverified
history: rebase-stale-automation-pr-onto-refactored-main.history
tags:
  - rebase
  - merge-conflict
  - stale-base
  - refactor-collision
  - merge-queue-drain
  - zizmor
  - artipacked
  - persist-credentials
  - deleted-stage-routing
  - adr-collision
  - ast-guard-registry
  - dco-merge-commit
  - superseded-pr
  - pixi-boilerplate
  - contaminated-history
  - rebuild-branch
  - diff-allowlist
  - explicit-force-lease
  - exact-head-review
  - homericintelligence
  - hephaestus
---

# Rebasing a Stale Automation PR onto a Heavily-Refactored Main

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-20 |
| **Objective** | Preserve valid PR intent across a refactored `main`, including the case where the stale branch history is contaminated by an unrelated duplicated commit and must be rebuilt rather than replayed. |
| **Outcome** | The original semantic-rebase workflow is verified in CI. The new contaminated-history rebuild, explicit path-scope proof, rollback lease, and exact-head review gate are proposed from a reviewed implementation plan but have not been executed end-to-end. |
| **Verification** | unverified for the v1.1.0 rebuild extension; the inherited v1.0.0 semantic conflict catalog remains verified-ci. See the [changelog](./rebase-stale-automation-pr-onto-refactored-main.history). |

## When to Use

Reach for this when a **single** stale PR must be replayed onto a `main` that a
large refactor restructured — a different problem from a multi-repo backlog
sweep (see `automation-multi-repo-pr-sweep-rebase-resolve` for that). The value
here is the **catalog of semantic conflict classes** the refactor creates and
how to resolve each faithfully.

Also use the rebuild variant when the PR's desired file changes are valid but
its commit graph contains scope bleed from another issue. In that case, a
rebase or multi-commit cherry-pick preserves the contamination; rebuild from
current `main`, port only the intended hunks, and prove the complete diff scope.

## Proposed Workflow

> **Warning:** The contaminated-history rebuild extension has not been validated
> end-to-end. Treat it as a hypothesis until CI and a strict exact-head review
> confirm it. The semantic conflict classes inherited from v1.0.0 are verified-ci.

Core insight: **the conflict text is a distraction; resolve against the CURRENT
code/enum on `main`, never against what the stale branch assumed.** An
automation branch encodes the world as it was N commits ago. After a big
refactor, "take theirs" or "take ours" are both usually wrong — you must map the
branch's *intent* onto `main`'s *new structure*.

### Contaminated history: rebuild, do not replay

When an unrelated commit appears in a PR's range, treat the old branch as a
read-only evidence source. Do not rebase or cherry-pick its multi-commit range.

1. Fetch the live base and PR branch. Record the exact remote PR-head SHA, and
   create a local backup ref at that SHA. Never push the backup ref.
2. Create a fresh branch from the fetched base. Port only the intended hunks,
   resolving their semantics against current symbols and behavior.
3. Add or update regression tests first and confirm the clean base fails the new
   expectation. Apply the smallest source/doc change that makes them pass.
4. Prove scope in two dimensions: a positive path allowlist rejects every
   unexpected changed path, while a negative denylist asserts that the known
   contamination surface has no diff. Review the full three-dot diff too; an
   allowlist alone cannot detect an unrelated hunk hidden inside an allowed file.
5. Run focused tests, repository validation, lint, and `git diff --check`. Commit
   with the repository's signature and DCO policy, then verify that the rewritten
   range contains only the intended commit(s).
6. Replace the remote branch with an explicit force-with-lease bound to the SHA
   captured in step 1. A bare tracking-ref lease is weaker when another process
   may fetch or mutate the remote-tracking ref during the rebuild.
7. Run the strict reviewer only after the rewritten head is pushed. Accept only
   an unqualified GO tied to that exact head with zero unresolved blocking
   threads. Any later commit invalidates the verdict and restarts verification.
8. If validation or review fails irrecoverably, restore the local backup ref with
   a second explicit lease bound to the rejected rebuilt SHA. Never rewrite the
   base branch.

### The merge-queue-crawl diagnosis (do this first)

A GitHub merge queue that barely advances is usually NOT runner starvation and
NOT queue config. Check, in order:

1. `gh run list --workflow=<required>.yml` — are `merge_group` runs stuck
   `queued` (runner starvation) or **completing `failure`**? A failing entry is
   far worse than a slow one.
2. If failing: `gh run view <id> --json jobs --jq '.jobs[]|select(.conclusion=="failure").name'`.
   A recurring `lint` + `security/workflow-scan` failure across MANY entries
   means a **gate that landed on `main` now scans files the stale PRs still
   carry in an old form**.
3. Confirm the stale base: `behind=$(git rev-list --count $(git merge-base origin/main origin/<branch>)..origin/main)`.
   A PR ~6+ behind, whose `_required.yml`/`contract.yml` differs from `main`, will
   FAIL the new gate in its `merge_group` — then GitHub ejects it after a full
   ~20-min matrix and **re-validates every entry behind it**. That cascade, not
   runners, is the crawl. **Fix = rebase the stale PRs onto current `main`** (which
   pulls in the hardened workflow files). Re-enqueuing without rebasing just
   re-poisons the queue.

### The conflict classes (resolve each this way)

- **DCO-less merge commit** — an automation "update main into branch" created a
  `Merge remote-tracking branch ...` commit with no `Signed-off-by` trailer;
  `pr-policy` rejects it. **Rebase onto `origin/main`** — this DROPS the merge
  commit entirely, replaying only the real (already-signed+DCO) work commit. Do
  not try to amend a merge commit. (Commit-signing remediation proper lives in
  `pr-compliance-dco-and-rebase-fix`.)

- **zizmor `artipacked` on a NEW job** — the landed security PR added
  `persist-credentials: false` to every *pre-existing* checkout, but the stale
  PR *introduces a new job* whose checkout git-auto-merged in WITHOUT that line.
  Finding points at `release.yml:<new-job-checkout>`. Fix: add
  `persist-credentials: false` to the new job's `actions/checkout`. Verify
  locally: `uv run zizmor --no-online-audits --min-severity medium <file>` →
  "No findings".

- **Routing to a DELETED stage/symbol** — the stale PR routes to
  `StageName.CI` (or any symbol) that the refactor removed. **Verify against the
  enum on `main`, not the branch**: read `routing.py`'s `StageName` members. If
  the target is gone, map the branch's intent to a surviving member (e.g. a
  legacy issue-level label → `PR_REVIEW`, not the deleted `CI`). Routing to a
  nonexistent member reintroduces the exact `KeyError` a prior fix closed.

- **ADR-number collision** — both the stale PR and a landed PR claimed
  `0012`. Renumber the incoming one: edit the README index row, `git mv` the
  file to the next free number, fix the ADR's own `# ADR-NNNN` header, and update
  EVERY reference (runbook links AND prose "per ADR-NNNN" mentions AND any
  guard-test assertion that hardcodes the number). Grep the whole tree for the
  old number to be sure.

- **AST-guard registry realignment** — a test that AST-scans call sites (e.g.
  `dontAsk` permission scopes, `allowed_tools`) conflicts because the refactor
  renamed the function the scope attaches to. Resolve by matching the registry
  to the ACTUAL post-rebase code: for each entry, `grep` the real symbol name
  and its literal scope in the source, then write exactly that. The guard test
  itself re-validates your resolution — run it.

- **Superseded vs. pixi-boilerplate** — a PR whose *substance* is done by a
  landed PR (same issue, same file, older base whose diff would REVERT newer
  work) is genuinely superseded → close it, resolve its issue. But a PR that
  merely mentions `pixi run` in its stale testing-boilerplate section is NOT
  pixi-specific — check `git diff --name-only` for actual `pixi*` file touches;
  if none, its substance is real → rebase it, don't close it.

### Quick Reference

```bash
# 1. Diagnose a crawling merge queue: are merge_group runs FAILING (not just slow)?
gh run list --workflow=_required.yml --limit 20 \
  --json event,conclusion,headBranch \
  --jq '.[]|select(.event=="merge_group" and .conclusion=="failure")|.headBranch'
gh run view <id> --json jobs \
  --jq '.jobs[]|select(.conclusion=="failure").name'   # -> lint, security/workflow-scan

# 2. Confirm stale base carries an old workflow file the new gate rejects
BR=<branch>; BASE=$(git merge-base origin/main origin/$BR)
git rev-list --count "$BASE"..origin/main                       # how far behind
diff <(git show origin/main:.github/workflows/_required.yml) \
     <(git show origin/$BR:.github/workflows/_required.yml) >/dev/null \
     && echo "fresh" || echo "STALE workflow -> will fail zizmor in merge_group"

# 3. Rebase in an ISOLATED worktree; a DCO-less merge commit is dropped automatically
git worktree add /tmp/rb-$BR "$BR"
cd /tmp/rb-$BR && git fetch origin main "$BR" && git rebase origin/main
# ...resolve each conflict class per the sections above...
git log origin/main..HEAD                    # expect ONLY real work commits, no merge commit

# 4. Before routing decisions, read the ACTUAL enum on main (never the branch)
git show origin/main:hephaestus/automation/pipeline/routing.py | grep -A12 'class StageName'

# 5. Verify with the repo's OWN guards on the resolved tree, then push signed
uv run pytest <affected pipeline/AST-guard/doc-guard suites> --override-ini="addopts=" -q
uv run zizmor --no-online-audits --min-severity medium .github/workflows/<changed>.yml
git push --force-with-lease origin "$BR"     # PR ejected from queue first if it was queued
gh pr merge <n> --auto                        # queue owns merge method; do NOT pass --squash

# 6. For contaminated history, rebuild from current main and pin both rewrite leases
OLD_SHA=$(git ls-remote --heads origin "refs/heads/$BR" | awk '{print $1}')
git branch "backup/<pr>-pre-isolation" "$OLD_SHA"     # local only; do not push
git switch -c "$BR-rebuild" origin/main
# Port only intended hunks and tests; do not cherry-pick the contaminated range.

# ALLOWED_PATHS is a sorted file containing the exact intended PR path set.
comm -23 \
  <(git diff --name-only origin/main...HEAD | sort) \
  "$ALLOWED_PATHS" \
  | (! read -r unexpected)
git diff --exit-code origin/main...HEAD -- <known-contamination-paths...>
git diff --check origin/main...HEAD

git push --force-with-lease="refs/heads/$BR:$OLD_SHA" origin \
  "HEAD:refs/heads/$BR"
PUSHED_SHA=$(git rev-parse HEAD)
# Run the repository's strict reviewer now; require unqualified GO for PUSHED_SHA.

# Roll back only if required; lease against the rejected rebuilt head.
git push --force-with-lease="refs/heads/$BR:$PUSHED_SHA" origin \
  "backup/<pr>-pre-isolation:refs/heads/$BR"
```

## Verified Workflow

The semantic conflict catalog, merge-queue diagnosis, and current-symbol
resolution rule inherited from v1.0.0 remain `verified-ci`; their exact verified
snapshot is preserved in the history file. The contaminated-history rebuild,
scope-proof combination, and exact-head review/rollback steps in the Proposed
Workflow above are explicitly excluded from this verification claim.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | Diagnosed the slow queue as runner starvation and waited | Runners were fine; the real cause was stale-base PRs FAILING the new zizmor gate in `merge_group`, ejecting after a 20-min matrix and re-validating the whole tail | Check `merge_group` run *conclusion*, not just runner counts. A failing entry poisons everything behind it. |
| 2 | On the release-workflow rebase, took the incoming branch's `StageName.CI` route | The refactor had DELETED the CI stage from the enum; the resolution would have crashed (the `KeyError` a prior fix closed) | Resolve routing against the CURRENT enum on `main`, not the branch's assumption. Read `routing.py`. |
| 3 | Took the branch's side wholesale on an AST-guard `dontAsk`/`allowed_tools` registry | The branch predated a scope change AND renamed the call-site symbol; blind "take theirs" would desync the registry from the real code | Match the registry to the actual post-rebase symbols+scopes (`grep` them); let the guard test re-validate. |
| 4 | Left a docstring note "the FOLLOWUP_WAIT state was retired" after removing the state | A retirement guard test did a plain substring `"FOLLOWUP_WAIT" not in source` and failed on the note | When a guard is a substring check, even a historical mention trips it — reword to avoid the literal token. |
| 5 | Passed `gh pr merge <n> --auto --squash` to re-enqueue | "The merge strategy for main is set by the merge queue" — rejected | On merge-queue repos, arm with `--auto` and NO strategy flag; the queue supplies SQUASH. |
| 6 | Considered closing PRs that mention `pixi run` as pixi-specific | The `pixi run` was only stale testing boilerplate; the PRs' substance (SLOs, NATS DLQ, docs) touched no pixi files and was still valid | Judge by `git diff --name-only` (does it touch `pixi*`?), not by a boilerplate string. |
| 7 | Rebased or replayed the complete commit range of a PR that contained a duplicated sibling-issue commit | Git faithfully preserved the unrelated commit, so the rewritten PR still had scope bleed even when its desired hunks were correct | Rebuild from current `main`; use the old head only as evidence and manually port the intended hunks. |
| 8 | Checked only a positive changed-path allowlist | The allowlist catches unexpected files but cannot catch unrelated edits inside an allowed file | Combine the allowlist with a known-contamination denylist and a human review of the complete three-dot diff. |
| 9 | Relied on CI or a review verdict produced before the branch rewrite | That evidence was tied to an obsolete commit graph and did not establish approval for the pushed replacement head | Re-run strict review after push and bind acceptance to the exact SHA; any later commit invalidates it. |
| 10 | Used an implicit `--force-with-lease` after background fetches | The remote-tracking ref used as the implicit expectation can change during a long rebuild, weakening the intended compare-and-swap boundary | Capture the live remote SHA before rebuilding and pass `--force-with-lease=refs/heads/<branch>:<sha>` explicitly. |

## Results & Parameters

- **Scale:** one session cleared all DIRTY PRs after a large refactor landed; each reached MERGEABLE + armed or was closed as genuinely superseded (with its issue resolved).
- **Verification signal:** the repo's OWN guard tests are the oracle — an AST-scanning `dontAsk` registry test and a doc/ADR retirement test each *pass only if* the resolution matches the real code. Run them on the resolved tree before pushing.
- **Queue mechanics:** `maximumEntriesToMerge` is not the throughput limit when entries FAIL; a failing entry ejects after a full matrix and re-stacks the tail. Throughput recovers only after the stale bases are rebased away.
- **Merge-method:** merge-queue repos reject `gh pr merge --squash`; arm with bare `--auto`.
- **Signatures:** rebasing re-signs replayed commits automatically when the GPG key is configured; verify `git log --show-signature` shows Good + `Signed-off-by` before pushing. Sign with `4211002+mvillmow@users.noreply.github.com`.
- **Rebuild inputs:** exact base ref, live remote PR-head SHA, local-only backup ref,
  sorted positive path allowlist, explicit contamination denylist, and focused test
  commands. If any input is unknown, stop before rewriting the remote branch.
- **Handoff proof:** pushed SHA, clean allowlist/denylist checks, focused tests,
  signed+DCO commit verification, and a fresh unqualified strict-review GO for
  that same SHA with zero unresolved blocking threads.

### Related skills (cross-links)

- `pr-compliance-dco-and-rebase-fix` — the commit-signing/DCO/pr-policy remediation proper (whole-range rewrite); this entry's DCO-less-merge-commit case is the "drop it via rebase" sibling.
- `automation-multi-repo-pr-sweep-rebase-resolve` — the multi-repo backlog-sweep orchestration this single-PR conflict catalog complements.
- `hephaestus-automation-loop-branch-sync-drive-green` — driving open PRs to green via the loop, and the `--drive-green-all` vs `--phases drive-green` KeyError.
- `planning-pr-open-file-scope-via-git-diff` — deriving an open PR's changed-path set; pair its positive scope with a known-contamination denylist here.
- `pr-review-two-dot-vs-three-dot-diff` — selecting the three-dot PR delta used by the complete scope proof.
- `prompt-loader-rebuild-race` — the `__file__`-loader fix that was one of the landed PRs in this wave.
- `adr-authoring-indexing-and-maintenance` — ADR index/landing mechanics (this entry adds the collision-renumber-on-rebase case).

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | PR #2206 / issue #2140 contaminated-history isolation plan | [Session notes](./rebase-stale-automation-pr-onto-refactored-main.notes.md); proposed only, strict exact-head review and CI execution pending. |
