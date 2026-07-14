---
name: agents-pr-review-evidence-discipline
description: "Four codified rules for reviewing AI-agent authored PRs that drop a project prefix or rename a package. Use when reviewing chore/rename-* PRs, when claiming a PR is CLEAN/DIRTY, or when posting a verdict comment. Prevents false-positive NO-GO verdicts caused by inspecting the wrong branch."
category: tooling
date: 2026-07-11
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [pr-review, evidence, ci, branch-discipline, dry-thrash, auto-merge]
---

# PR Review Evidence Discipline

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-11 |
| **Objective** | Codify the four rules learned during the HomericIntelligence rename-sweep (ADR-015 + ADR-016) review cycle, so future agents don't repeat the same overclaim / false-positive patterns. |
| **Outcome** | Four rules published. Apply on every chore/rename PR review. |
| **Verification** | verified-local (file-only; no CI observation on the rules themselves) |
| **History** | [changelog](./agents-pr-review-evidence-discipline.history) |

## When to Use

- Reviewing a `chore/rename-*` PR or any cross-package rename PR.
- Posting a `CLEAN` / `DIRTY` / `NO-GO` verdict comment on a PR.
- Deciding whether to push a follow-up commit on a chore branch.
- Deciding whether to enable `--auto --rebase` on a sub-repo PR.
- Catching a teammate's overclaim that "CI is green" without `gh pr checks` evidence.

## Verified Workflow

### Quick Reference

```bash
# 1. Always verify on the PR's actual branch
git fetch origin refs/heads/<chore-branch>:refs/remotes/origin/<chore-branch>
git checkout <chore-branch>
# Inspect: NOT origin/main HEAD

# 2. Tag your evidence level
echo "verified-local"  # file-only grep/diff
echo "verified-ci"     # only after `gh pr checks` shows green

# 3. Don't push cosmetic follow-ups
# If the PR is already CLEAN on the chore branch, post the verdict, don't commit.

# 4. Auto-merge is per-PR
gh pr merge <PR> --auto --rebase   # gates independently per PR
```

### Detailed Steps

1. **Branch-vs-Tip Discipline.** Default-branch tip (`main`) shows the post-merge state, NOT the in-progress PR state. Always fetch the PR's actual head branch with `git fetch origin refs/heads/<branch>` and `git checkout <branch>` before claiming a residual. A "NO-GO" verdict based on `origin/main` is a false positive when the PR's chore branch is clean.

2. **Evidence Tagging.** Distinguish `verified-local` (file-only grep / diff evidence) from `verified-ci` (CI gate observed green via `gh pr checks`). Never claim `verified-ci` without observation. If the CI status has not been observed, the verdict is `verified-local` regardless of how clean the diff looks.

3. **DRY-Thrash Avoidance.** On strictly cosmetic PRs (e.g. chore-only renames, doc-only changes), post a clean verdict rather than push follow-up commits. Pushing noise commits risks merge conflict with the operator's working copy and creates PR pileup.

4. **Auto-Merge Isolation.** `--auto --rebase` is per-PR; one PR's gate state does not transfer. Each PR must be evaluated independently against its own `gh pr checks` output.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | NO-GO on Agamemnon#444 based on `origin/main` HEAD showing `ProjectAgamemnon_core` literal | The chore branch (HEAD `3de2053`) was clean; the literal was on main, not on the PR | Always verify on the PR's head branch, not default-branch tip |
| 2 | "CI is green" claim without `gh pr checks` | Speculative; risked approving a PR with a red gate | Tag evidence level: only `verified-ci` after observation |
| 3 | Pushed follow-up cosmetic commits to a clean chore branch | Triggered merge conflict with operator's working copy | DRY-thrash: if the PR is clean, post the verdict and stop |

## Results & Parameters

### Apply pattern

| PR type | Action | Verdict tag |
|---------|--------|-------------|
| `chore/rename-*` with verified local residuals | Push follow-up commit on `<pr-number>-<slug>` branch, open new PR targeting chore | `verified-local` (cite file:line) |
| `chore/rename-*` with verified CI green | Post clean verdict, do not push follow-up | `verified-ci` (cite `gh pr checks` output) |
| `chore/rename-*` with CI status unobserved | Post clean verdict with evidence tag | `verified-local` (do not overclaim `verified-ci`) |
| Strictly cosmetic `chore/*` PR | Post clean verdict, no follow-up commit | `verified-local` |

### Naming

- Branch: `<pr-number>-<slug>` (e.g. `274-residual-include-path`).
- Commit prefix: `fix(scope):` for build/code, `chore:` for cosmetic.
- PR body: `Refs: #<original-pr>` to link follow-up to chore branch.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| HomericIntelligence/Charybdis | PR #274 follow-up at CMakeLists.txt:27 | Residual `projectcharybdis` literal post-rename |
| HomericIntelligence/Agamemnon | PR #444 retraction | Prior NO-GO was based on default-branch tip, not chore branch |
| HomericIntelligence/* | 12-PR rename sweep | Cross-repo evidence tagging audit |
