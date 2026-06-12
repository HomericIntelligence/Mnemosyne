---
name: ci-cd-non-required-precommit-strict-false-breaks-main
description: "Non-required pre-commit workflow plus strict:false branch protection silently breaks main's required checks while PRs keep auto-merging. Use when: (1) main's Required Checks are red for hours but PRs still merge, (2) a GO'd PR fails CI on lint/pre-commit only (not tests), (3) auditing branch-protection required-status-check configuration."
category: ci-cd
date: 2026-06-12
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: []
---

# Non-Required Pre-commit + strict:false Silently Breaks Main

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-12 |
| **Objective** | Explain why main's Required Checks went red across every SHA for hours while PRs kept auto-merging, and how to fix the underlying branch-protection gap |
| **Outcome** | Fixed in PR #1174 (merged green); main Required Checks = success |
| **Verification** | verified-ci |

## When to Use

- main's `Required Checks` is RED across multiple/every recent SHA for hours, yet PRs are still auto-merging (and it's NOT an admin/force push).
- A GO'd PR fails CI on lint/pre-commit ONLY (tests are green) — suspect main-debt contamination, not the PR.
- Auditing a repo's branch-protection required-status-check list and `strict` setting.

## Verified Workflow

Two interacting root causes let main go red while PRs kept merging:

### Root cause 1 — non-required (advisory) pre-commit check

main's required status checks were ONLY:

- `test (ubuntu-latest, 3.12, integration)`
- `test (ubuntu-latest, 3.12, unit)`

The `Pre-commit` workflow ran on every PR but was **ADVISORY** (not in the required-check list). Because nothing gated on it, PR #959 merged an unformatted file — its tests were green, so it satisfied every required check. Pre-commit then failed on main and on every later PR: this is repo-wide all-files pre-commit contamination — one stray malformed file fails the all-files markdownlint/pre-commit gate on every PR, but since the gate is advisory it never blocks the merge.

### Root cause 2 — strict:false

With `strict: false` on main, PRs are NOT re-checked against current main — they merge on their **base SHA's** green checks. So PR #1035 (which added a parametrized "version flag" test AND missed wiring 3 console scripts) merged with the integration test red on main, because its branch predated the failure surfacing. strict:false means a stale-but-green base SHA is enough to merge even while main is broken.

### The fix (PR #1174)

1. `ruff format` the one offending file.
2. Fix the 3 missed console scripts.
3. **FOLD** the standalone `pre-commit.yml` INTO the **REQUIRED** `lint` job in `_required.yml` so `lint` runs `pre-commit run --all-files` as its single step. This requires running `pixi install --environment default` then `pixi run dev-install` FIRST so the `hephaestus-*` local hooks resolve. The whole hook suite then becomes required AND de-duplicated (ruff/mypy/yamllint no longer run twice — once in lint, once in pre-commit). Delete `pre-commit.yml`.

### Quick Reference

When a GO'd PR fails CI on lint/pre-commit only (not tests), check main FIRST:

```bash
gh run list --branch main --workflow "Required Checks" --limit 10
```

If main is red on lint/pre-commit, it's main-debt contamination — fix main, not the PR.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Delete pre-commit.yml outright | Considered just removing the standalone pre-commit workflow | Would have LOST ~25 hooks — the required `lint` job only ran ruff/yamllint/mypy, so dropping pre-commit.yml silently drops the rest of the hook suite | FOLD the hooks into the required job (run `pre-commit run --all-files`) instead of deleting; preserve full coverage |
| Blame the failing PR | Treated the GO'd PR that failed lint/pre-commit as the culprit | The PR was clean; main itself was already red (contaminated) so every PR inherited the failure | When a PR fails lint/pre-commit only, check `gh run list --branch main` before touching the PR |

## Results & Parameters

- **Open follow-up:** `strict: false` is still unfixed. Enabling `strict: true` forces every open PR to rebase onto current main before merging (mergeability churn), which is why it was deferred. Tracked under issue #1173.
- **Required contexts at breakage time:** `test (ubuntu-latest, 3.12, integration)` and `test (ubuntu-latest, 3.12, unit)`; `Pre-commit` was advisory.
