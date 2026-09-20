---
name: planning-pr-open-load-bearing-assumption-hygiene
license: BSD-3-Clause
description: "Check PR delivery assumptions when merge settings, compatibility wrappers, or referenced documentation may differ from the plan."
category: architecture
date: 2026-07-02
version: "1.2.0"
user-invocable: false
verification: unverified
tags:
  - planning
  - pr-open
  - load-bearing-assumption
  - auto-merge
  - autoMergeAllowed
  - compat-wrapper
  - glibc
  - precommit
  - probe-before-plan
  - documented-fallback
  - task-mandated-merge-method
  - no-silent-fallback
  - block-on-method-mismatch
---

# Planning: Load-Bearing Assumption Hygiene in PR-Open Plans

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-02 |
| **Objective** | Prevent PR-open plans from silently depending on unverified external assumptions (repo auto-merge settings; the presence/behavior of a compat wrapper script; the current state of a referenced doc) by requiring either (a) a probe at plan time or (b) an explicit hedge with a documented fallback. |
| **Outcome** | PLAN ONLY — captured during ProjectOdyssey #5527 planning where the plan (i) invoked `gh pr merge --auto --rebase` without probing `autoMergeAllowed` or `rebaseMergeAllowed`, and (ii) asserted `just precommit` would pass without `SKIP=mojo-format` based on a claim about `scripts/mojo-format-compat.sh` and `docs/dev/mojo-glibc-compatibility.md` — neither of which was read. |
| **Verification** | unverified |

## When to Use

- A PR delivery plan depends on auto-merge or a particular merge method.
- A compatibility wrapper or document is used to predict a tool's behavior.
- A repository setting or unavailable tool may affect delivery but not implementation.

## Verified Workflow

This guidance remains unverified. Check assumptions that change the action, and keep uncertainty
local to the affected step. A missing optional delivery capability need not stop useful work.

### Quick Reference

```bash
gh repo view <owner>/<repo> --json autoMergeAllowed,rebaseMergeAllowed,squashMergeAllowed,mergeCommitAllowed
```

### Detailed Steps

1. Inspect relevant repository settings before relying on a merge mechanism. Use an allowed method
   consistent with the user's request and current repository policy.
2. If auto-merge is unavailable, finish the authorized PR work, leave the PR open, and report the
   remaining delivery step. Do not enable repository settings without authorization.
3. Read a compatibility wrapper when its behavior determines the next action. If it is unavailable,
   record the uncertainty and use a supported environment or an already-authorized alternative.
4. Prefer current source and observed behavior over document age as evidence. Read referenced
   documentation when it supplies a decision-changing contract; avoid automatic freshness rituals.
5. If an explicit user requirement conflicts with repository merge settings, defer that merge and
   ask for the unresolved choice. Continue implementation, review, and other independent work.
6. Treat an issue-body example or a regex match as context, not proof of a user mandate. Resolve
   conflicts using the actual request and applicable repository contract.

### Necessary decision boundary

A different merge method can change the requested history. When the user explicitly requires a
method that the repository forbids, user input is needed for that merge decision. This boundary
protects the user's requirement; it does not block unrelated progress or imply permission to change
repository settings. Reuse existing authorization instead of requesting it again.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | ProjectOdyssey #5527 planning session: assert `just precommit` will pass without `SKIP=mojo-format` on a WSL host with GLIBC < 2.32, based on the claim that `scripts/mojo-format-compat.sh` exits 0 in that scenario and `docs/dev/mojo-glibc-compatibility.md` documents this. Neither the wrapper nor the docs file was read. | Two silent load-bearing assumptions: (a) the wrapper's GLIBC-detection logic may not cover the executor's specific host, (b) the docs file may be stale. If either fails, `just precommit` fails at execute time and the plan offers no fallback. | Read the wrapper. Read the doc. Or hedge explicitly: "if precommit fails on `mojo-format`, use `SKIP=mojo-format git commit -m '…'` and reference `docs/dev/mojo-glibc-compatibility.md` in the commit body." |
| Attempt 2 | ProjectOdyssey #5527 planning session: invoke `gh pr merge --auto --rebase` without probing `gh repo view --json autoMergeAllowed,rebaseMergeAllowed`. | On some repos `autoMergeAllowed=false` (auto-merge is not enabled at the repo level); on others `rebaseMergeAllowed=false` (only squash/merge is permitted). Either causes `--auto --rebase` to fail with a non-obvious error. The plan does not hedge, so a failure aborts the PR-open task even though the PR itself is fine. | Probe repo settings before writing the plan step, OR soft-fail the `--auto` step (record the failure, continue) so the PR stays open and manual merge remains available. |
| Attempt 3 (v1.1.0) | Prior /learn session on Mnemosyne: probed `rebaseMergeAllowed=false` at plan time, then silently substituted `gh pr merge --auto --squash` because Mnemosyne permits squash. The originating ProjectOdyssey task's issue body mandated `--rebase`. | Silent substitution: (a) reinterprets a task-text mandate without disclosure, (b) ships a PR merged with the wrong method for the originating task's requirements, (c) the reviewer of the originating task cannot tell from the merged PR that the method was substituted. Silent fallback moves a decision from human to agent without a paper trail. | If an explicitly requested merge method is unavailable, explain that action-specific conflict and seek the necessary choice. Continue independent work; existing task authorization does not imply authority to change repository settings. |

## Results & Parameters

- Record decision-changing assumptions, available evidence, and practical alternatives.
- Distinguish completed implementation from pending checks or publication.
- Report a specific unavailable action rather than labeling the whole task blocked.
- Keep binding validation controls enabled; a historical example of skipping a hook is not
  authorization to bypass current policy.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectOdyssey | Issue #5527 planning session (2026-07-02) — captured two anti-patterns: (a) unhedged `gh pr merge --auto --rebase`, (b) unread `scripts/mojo-format-compat.sh` justifying "no SKIP= needed". Corrective pattern PLAN ONLY, not executed. | See ProjectOdyssey issue #5527 comments. |
| Mnemosyne | v1.1.0 amendment (2026-07-02) — prior /learn session on Mnemosyne silently substituted `--squash` for a `--rebase`-mandated task because Mnemosyne disallows rebase. This amendment closes the gap: on task-mandated method + repo disallow, plan verdict is BLOCKED, no silent fallback. Rule captured, not exercised. | Cross-repo: originating task in ProjectOdyssey #5527, silent-fallback observation in a Mnemosyne /learn PR. |

## References

- [github-auto-merge-ci-gating-merge-method](github-auto-merge-ci-gating-merge-method.md) — sibling skill; deep dive on why `gh pr merge --auto` fails and how to diagnose. This skill covers the PLANNING-time probe; that skill covers RUN-time diagnosis.
- [planning-pr-body-extract-sibling-artifact-at-runtime](planning-pr-body-extract-sibling-artifact-at-runtime.md) — companion skill for sibling-task artifacts.
- [planning-pr-body-numeric-claims-source-derived](planning-pr-body-numeric-claims-source-derived.md) — companion skill for numeric claims.
- [planning-pr-open-file-scope-via-git-diff](planning-pr-open-file-scope-via-git-diff.md) — companion skill for file-path claims.
- [planning-self-identified-defects-must-be-fixed-not-noted](planning-self-identified-defects-must-be-fixed-not-noted.md) — related guidance for resolving defects discovered during planning.
