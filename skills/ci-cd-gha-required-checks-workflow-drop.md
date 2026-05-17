---
name: ci-cd-gha-required-checks-workflow-drop
description: "GitHub Actions Required Checks downstream gate workflows stuck pending forever after a push. Use when: (1) gh pr checks shows the real test workflows (Test, CodeQL, Security, Pre-commit) running and passing but downstream gates (pr-policy, shellcheck, markdownlint, justfile-check, symlink-check, pixi-check, integration-tests) sit at pending:0 and never start; (2) PR cannot auto-merge because branch protection requires those gates green; (3) waiting / gh run rerun / close+reopen did not help. Fix: push one empty signed commit to re-trigger workflow scheduling."
category: ci-cd
date: 2026-05-17
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - github-actions
  - required-checks
  - workflow_run
  - workflow-drop
  - branch-protection
  - empty-commit
  - re-trigger
  - auto-merge
---

# GitHub Actions Required Checks Workflow-Drop

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-05-17 |
| **Objective** | Recover a PR whose downstream Required Checks gate workflows were never scheduled by GitHub Actions after a push, so auto-merge stays blocked indefinitely |
| **Outcome** | A single empty signed commit (`git commit --allow-empty -S -m "chore: re-trigger CI"` followed by `git push`) forces GitHub to re-evaluate workflow triggers, the previously-dropped gate workflows get scheduled, and the PR proceeds to auto-merge |
| **Verification** | verified-local — observed twice in HomericIntelligence/ProjectHephaestus PRs #420 and #421; the empty-commit fix worked both times. Not a CI test of itself. |

## Symptom

After pushing a commit to a PR branch:

- `gh pr checks <num>` shows the **upstream / real** workflows (Test, CodeQL, Security, Pre-commit) running and then passing.
- The **downstream Required Checks gate** workflows (`pr-policy`, `shellcheck`, `markdownlint`, `justfile-check`, `symlink-check`, `pixi-check`, `integration-tests`) sit at `pending:0` forever — never scheduled, never start, no run created.
- Branch protection requires those gate jobs to be green, so auto-merge never fires.
- The pending state is **durable**, not transient — waiting does not help.

## Root Cause Hypothesis

GitHub Actions occasionally drops workflow scheduling for compound `workflow_run`-style downstream gates when:

- The upstream workflow is still in flight at the moment the push event is processed, **or**
- Multiple pushes arrive in rapid succession, **or**
- A race occurs between the upstream workflow's completion event and the downstream gate's trigger evaluation.

The dependent gate workflow never receives its trigger event, so no run is ever created. Because no run exists, there is nothing for `gh run rerun` to act on, and the `pending` status comes from branch-protection's required-context check (which expects a run that will never appear).

## When to Use

1. PR checks show **passing** real-test workflows BUT **pending** downstream gate workflows for 10+ minutes.
2. The pending workflows are downstream gates (`pr-policy`, status-reporting, lint-aggregators) that depend on upstream workflow completion via `workflow_run` or similar fan-in.
3. The branch has **not** been force-pushed in a way that would naturally re-trigger.
4. `gh run list --branch <branch>` shows runs for the upstream workflows but **no run at all** for the stuck gate workflow.

If the upstream workflow itself hasn't run, this is a different problem — see `ci-github-actions-pull-request-trigger`.

## Verified Workflow

> **Verification level:** verified-local — observed twice in real PRs (#420 empty commit `619a45e`, #421 empty commit `3bbbbb6`) in HomericIntelligence/ProjectHephaestus on 2026-05-17. Fix worked both times.

### Quick Reference

```bash
# 1. Detect: real tests green, downstream gates pending
gh pr checks <PR> --repo <org>/<repo>

# 2. Confirm: no run was ever created for the stuck gate workflow
gh run list --branch <branch> --workflow <gate-workflow.yml> --repo <org>/<repo>

# 3. Fix: empty signed commit forces GitHub to re-evaluate triggers
git commit --allow-empty -S -m "chore: re-trigger CI"
git push

# 4. Verify: gate workflows now have runs and progress to success
gh pr checks <PR> --repo <org>/<repo> --watch
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | Waiting 30+ minutes | Workflows were never scheduled — pending state is durable, not transient | GitHub will not self-heal a dropped workflow trigger |
| 2 | `gh run rerun` on the upstream workflow | Re-runs the upstream run but does not re-fire the downstream gate's trigger event | `gh run rerun` only affects the specific run you target; it cannot create a run that never existed |
| 3 | Closing + reopening the PR | Has side effects on auto-merge state, review approvals, and required-check evaluation; gate workflows still did not get scheduled in some retries | Too disruptive vs. an empty commit, and not deterministic |

## Results & Parameters

- **Sign the empty commit** if branch protection requires signed commits (`-S`). An unsigned empty commit will be blocked by the same `pr-policy` gate this is trying to unblock.
- Use a **conventional-commit `chore:` prefix** so the empty commit is excluded from release notes generated by `gh release create --generate-notes`.
- **One empty commit is sufficient.** Do not chain multiple — that creates noisy history and can re-trigger the same race.
- The fix is **not preventive**, only **reactive**. There is no known way to force GitHub to never drop a workflow trigger; this skill is purely for recovery after the drop has happened.

## Detection Heuristic

If `gh pr checks` shows:

- A mix of `pass` (upstream) and `pending:0` (downstream) for more than 10 minutes, and
- `gh run list --workflow <stuck-gate>.yml --branch <branch>` returns zero rows,

then the trigger was dropped. Apply the fix.

## Related Skills

- `ci-github-actions-pull-request-trigger` — different symptom (the `on: pull_request` event itself does not fire; empty-commit trick **did not** work there, force-push was required). This skill handles the inverse where the `pull_request` event fired correctly but a downstream `workflow_run` gate was dropped.
- `ci-cd-reusable-workflow-required-checks-aggregator` — structural fix to consolidate the gate jobs; reduces but does not eliminate the workflow-drop race.
- `github-actions-required-fanin-conflict-resolution` — rebase-conflict handling for the same `_required.yml` fan-in surface.
