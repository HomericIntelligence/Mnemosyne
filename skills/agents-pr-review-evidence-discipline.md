---
name: agents-pr-review-evidence-discipline
license: BSD-3-Clause
description: "Use PR-head evidence for rename reviews, classify the evidence face when a node fails locally but is green in CI, and avoid unnecessary follow-up commits."
category: tooling
date: 2026-07-11
version: "1.2.0"
user-invocable: false
verification: verified-local
tags: [pr-review, evidence-tagging, branch-vs-tip, dry-thrash, auto-merge, code-review, adr-014, verified-local, verified-ci, chore-rename]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/agents-pr-review-evidence-discipline.history"
history-cleanup-date: "2026-09-20"
---

# PR Review Evidence Discipline

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-11 |
| **Objective** | Codify the four rules learned during the HomericIntelligence rename-sweep (ADR-015 + ADR-016) review cycle, so future agents don't repeat the same overclaim / false-positive patterns. |
| **Outcome** | Four rules published, plus a fifth rule for the local-red / CI-green evidence face. Apply on every chore/rename PR review. |
| **Verification** | verified-local (file-only; no CI observation on the rules themselves) |
| **History** | [changelog](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/agents-pr-review-evidence-discipline.history) |

## When to Use

- Reviewing a `chore/rename-*` PR or any cross-package rename PR.
- Posting a `CLEAN` / `DIRTY` / `NO-GO` verdict comment on a PR.
- Deciding whether to push a follow-up commit on a chore branch.
- Deciding whether to enable `--auto --rebase` on a sub-repo PR.
- Catching a teammate's overclaim that "CI is green" without `gh pr checks` evidence.
- A test passes in CI but fails in your checkout, and you are about to report it as
  a defect.

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

1. **Branch-vs-Tip Discipline.** Default-branch tip (`main`) shows the post-merge state, NOT the in-progress PR state. Inspect the actual PR head before claiming a residual; fetch it if the required revision is not available locally. A "NO-GO" verdict based on `origin/main` is a false positive when the PR's chore branch is clean.

**Concrete example from this session:** Agamemnon#444 was initially flagged NO-GO because `target_include_directories(ProjectAgamemnon_core ...)` appeared at `CMakeLists.txt:105` on the default-branch tip. Re-verifying the actual chore branch (`chore/rename-drop-project-prefix-r2`, HEAD `3de2053`) showed zero matches. The literal was on `main`, not the PR. Lesson: never trust the default-branch tip for in-progress PR review.

2. **Evidence Tagging.** Distinguish `verified-local` (file-only grep / diff evidence) from `verified-ci` (CI gate observed green via `gh pr checks`). Never claim `verified-ci` without observation. If the CI status has not been observed, the verdict is `verified-local` regardless of how clean the diff looks.

**Concrete example from this session:** 11 PR verdicts were issued during the rename-sweep cycle; 3 of those were subsequently corrected (Agamemnon NO-GO retraction, Hermes CI-drag qualifier, Nestor default-branch-tip qualifier). All 11 were tagged `verified-local` (file-only) rather than `verified-ci` because no `gh pr checks` observation was performed in the agent session.

```bash
# How to upgrade verified-local to verified-ci:
gh pr checks <PR> --repo <org>/<repo> --jq '.[] | select(.conclusion=="FAILURE") | .name'
```

3. **DRY-Thrash Avoidance.** On cosmetic PRs, avoid follow-up commits when the review finds no defect. Correct substantiated defects when that work is authorized. Pushing noise commits risks merge conflict with the operator's working copy and creates PR pileup.

**Concrete example from this session:** Telemachy#300, Mnemosyne#3050, Odyssey#5584, and Keystone#603 had zero residuals on their chore branches. The 4 cosmetic PRs (plus 4 others) received clean verdict comments rather than follow-up commits, avoiding merge conflicts with the operators' in-progress work. Rule: if `grep -rnE "project<Name>" --exclude-dir=.git .` returns 0, post a clean verdict, do not commit.

4. **Auto-Merge Isolation.** `--auto --rebase` is per-PR; one PR's gate state does not transfer. Each PR must be evaluated independently against its own `gh pr checks` output.

5. **Separate an environment face from a code defect before you report.** A test that
   passes in CI and fails in your checkout is an environment claim until you hold
   evidence of a defect. Find the ambient value the gate reads, set it to a neutral
   value, and run the same node again in the same command block:

   ```bash
   # Read the ambient value, then change only it and re-run the same node.
   umask   # 0002 creates group-writable files; a 0o022 mode gate refuses them
   ( umask 022; <runner> <same node> )   # passes -> environment face, not a defect
   ```

   Test one variable at a time. When a neutral value flips the result, report the
   ambient variable and its value as the cause. Do not report the node as red on the
   default branch. Do not weaken the gate: a refusal that is correct under a hostile
   umask, a permissive parent directory, or a foreign owner is by design. Fix the
   environment or the fixture, not the check. When CI is green at the same commit and
   your checkout is red, treat CI as the higher evidence face and explain the gap.

**Concrete example from this session:** Eleven sub-repo PRs were reviewed independently. One PR's gate state (e.g. Agamemnon#444 green) does NOT transfer to another (e.g. Charybdis#274 may be red). Each PR's `--auto --rebase` arming is per-PR:

```bash
gh pr merge 275 --auto --rebase --repo HomericIntelligence/Charybdis
gh pr merge 444 --auto --rebase --repo HomericIntelligence/Agamemnon
# These operate on independent gate state; arming one does not affect the other.
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | NO-GO on Agamemnon#444 based on `origin/main` HEAD showing `ProjectAgamemnon_core` literal | The chore branch (HEAD `3de2053`) was clean; the literal was on main, not on the PR | Always verify on the PR's head branch, not default-branch tip |
| 2 | "CI is green" claim without `gh pr checks` | Speculative; risked approving a PR with a red gate | Tag evidence level: only `verified-ci` after observation |
| 3 | Pushed follow-up cosmetic commits to a clean chore branch | Triggered merge conflict with operator's working copy | If the PR is clean, report the verdict without a noise commit; continue remaining requested work |
| 4 | Reported a node as red on the default branch because it failed in a local checkout | CI was green at the same commit. The host umask was `0002`, so the fixture file was group-writable (`0o664`) and a correct `0o022` identity gate refused it. The closure note attributed the failure to the temporary-directory path, but the node also failed under a root-owned sticky directory | Test one ambient variable at a time. Run the same node under a neutral value. When that flips the result, the check is right and the environment is the cause |

## Results & Parameters

### Apply pattern

| PR type | Action | Verdict tag |
|---------|--------|-------------|
| `chore/rename-*` with verified local residuals | Push follow-up commit on `<pr-number>-<slug>` branch, open new PR targeting chore | `verified-local` (cite file:line) |
| `chore/rename-*` with verified CI green | Post clean verdict, do not push follow-up | `verified-ci` (cite `gh pr checks` output) |
| `chore/rename-*` with CI status unobserved | Post clean verdict with evidence tag | `verified-local` (do not overclaim `verified-ci`) |
| Strictly cosmetic `chore/*` PR | Post clean verdict, no follow-up commit | `verified-local` |
| Node red locally, green at the same commit in CI | Report the ambient variable and value; re-run under a neutral value | `verified-local` (state that CI is green) |

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
