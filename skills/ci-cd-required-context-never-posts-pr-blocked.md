---
name: ci-cd-required-context-never-posts-pr-blocked
description: "Diagnose a PR with mergeStateStatus BLOCKED but zero failing checks — required status-check contexts are missing entirely (not-run), distinct from FAILURE. Two mechanisms: (1) workflow `paths:` filter excludes the PR's file changes so the workflow never triggers; (2) job-level `if: github.event_name != 'pull_request'` whole-skips the job on PR events (a whole-job skip does NOT satisfy a required context). Use when: (1) gh pr view shows BLOCKED with 0 FAILUREs, (2) gh pr checks shows green or skipped only, (3) branch protection requires a context that the PR's statusCheckRollup never contains. Companion of ci-cd-summary-aggregator-job-skip-required-context."
category: ci-cd
date: 2026-05-15
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - github
  - branch-protection
  - required-status-checks
  - not-run
  - blocked
  - merge-state-status
  - paths-filter
  - workflow-trigger
  - job-skip
  - github-actions
---

# Required Status-Check Context Never Posts: PR Permanently BLOCKED

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-15 |
| **Objective** | Diagnose and fix PRs that are `mergeStateStatus: BLOCKED` even though `gh pr view --json statusCheckRollup` shows zero FAILUREs — the blocker is a *required* status-check context that never posts at all (not-run), not a failing one. |
| **Outcome** | Two-prong diagnosis (paths-filter vs whole-job skip) using a required-vs-present diff; both mechanisms are systemic misconfigurations that must be fixed in the workflow YAML, not bypassed via admin merge. |
| **Verification** | verified-ci — diagnosis applied on ProjectOdyssey PR #5382; fixes landed in PR #5406 (paths broaden) and PR #5407 (aggregator gate). |

## When to Use

- `gh pr view <pr> --json mergeStateStatus` returns `BLOCKED` and `--json statusCheckRollup` shows **no** entries with `conclusion == "FAILURE"`
- `gh pr checks <pr>` is all green/pending/skipped — nothing red
- Branch protection requires a context whose name does NOT appear in the PR's `statusCheckRollup`
- You are tempted to admin-merge but suspect the misconfig will re-block the next PR

Do **NOT** use this skill if any required context shows `FAILURE` — use `pr-preexisting-failure-triage` instead. That skill assumes a check *ran and failed on main*; it cannot diagnose contexts that never produced any check-run at all (`status=null` on both PR and main).

## Verified Workflow

### Quick Reference

```bash
unset GITHUB_TOKEN GH_TOKEN
ORG=HomericIntelligence; REPO=ProjectOdyssey; PR=5382

# 1. Confirm BLOCKED with zero failures
gh pr view "$PR" --repo "$ORG/$REPO" --json mergeStateStatus,statusCheckRollup --jq '{
  mergeStateStatus,
  by_conclusion: (.statusCheckRollup | group_by(.conclusion // .status) | map({k: (.[0].conclusion // .[0].status // "?"), n: length}))
}'
# Signal: mergeStateStatus=BLOCKED AND no FAILURE bucket.

# 2. List branch-protection required contexts
gh api "repos/$ORG/$REPO/branches/main/protection/required_status_checks" --jq '.contexts'

# 3. Diff required-vs-present — the "missing" set is the cause
gh pr view "$PR" --repo "$ORG/$REPO" --json statusCheckRollup \
  --jq '[.statusCheckRollup[].name] | unique' > /tmp/present.json
gh api "repos/$ORG/$REPO/branches/main/protection/required_status_checks" \
  --jq '.contexts' > /tmp/required.json
jq -r '.[]' /tmp/required.json | sort > /tmp/required.txt
jq -r '.[]' /tmp/present.json  | sort > /tmp/present.txt
echo "Required contexts NOT present on PR (the blockers):"
comm -23 /tmp/required.txt /tmp/present.txt
```

### Detailed Steps

1. **Confirm the failure mode.** Run step (1) above. If you see a FAILURE bucket, stop and use `pr-preexisting-failure-triage`. If not, proceed.
2. **Build the missing-context list.** Step (3) above yields the exact set of required context names that the PR never produced.
3. **For each missing context, find its workflow & job.** The context name is usually `<workflow-name> / <job-name>` or just `<job-name>`. Locate it:

   ```bash
   grep -rE "^\s+<JOB_NAME>:|name:\s*['\"]?<JOB_NAME>" .github/workflows/
   ```

4. **Classify the cause** using the decision table in *Results & Parameters* below.
5. **Fix the workflow.** Either broaden the `paths:` filter (mechanism 1) or restructure to an aggregator/summary job that always runs (mechanism 2 — see companion skill `ci-cd-summary-aggregator-job-skip-required-context`).
6. **Do NOT admin-merge as the resolution.** Admin-merge unblocks one PR; the misconfig re-blocks the next PR that touches the same files / has the same event shape. Fix the workflow in a separate PR; once merged to main, branch protection now sees the fixed context appear on subsequent PRs.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Trusted check-rollup conclusion count | Saw `0 FAILURE` on `gh pr view --json statusCheckRollup` and assumed PR was ready | The rollup shows what *posted*. Missing contexts don't appear at all. `mergeStateStatus: BLOCKED` with 0 failures is the signal. | Always cross-check required-contexts vs present-contexts via the `comm -23` diff above |
| Applied `pr-preexisting-failure-triage` workflow | Tried per-check-name `check-runs` API query against main HEAD | That skill assumes the failing check *ran on main*; for `not-run` contexts the API returns empty (`status=null`) on both PR and main. The check-runs API can't distinguish "missing because never required" from "missing because workflow didn't fire" | Use the protection-API-vs-rollup diff first; `pr-preexisting-failure-triage` is for FAILURE classification, not for `not-run` |
| Assumed `gh pr merge --admin` would resolve it | Recommended admin-merge from the resolution ladder | Skipping a required check via admin merges this PR but leaves *every future Dockerfile-touching PR* permanently BLOCKED. The misconfig is systemic. | For `not-run` blockers caused by misconfig, fix the misconfig in a separate PR — admin-merge is for one-off pre-existing rot, not systemic gaps |
| Tried to add `paths: Dockerfile*` only | Hypothesised that broadening the filter would unblock the PR | Even after the workflow triggers, `test-images` and `security-scan` jobs are whole-job-skipped on PR events. Filter fix alone leaves PR BLOCKED with the same checks now showing SKIPPED instead of missing. | Filter fix and aggregator fix are *both* needed when the misconfig has both flavours |

## Results & Parameters

### Decision table — two mechanisms

For each missing context, find the workflow that *should* emit it, then classify:

| Cause | Tell-tale | Fix |
|-------|-----------|-----|
| Workflow `paths:` filter excludes PR | `gh run list --branch <branch> --workflow=<file> --limit 3` shows no runs for the PR's HEAD SHA | Broaden `paths:` (see skill `ci-cd-throttle-container-publish-nightly-paths-filter` Quick Reference — use `Dockerfile*` glob, not literal filenames) |
| Whole-job skip on event type | The workflow runs; the job's row in `gh run view <run-id> --json jobs` shows `"conclusion": "skipped"`, and the job has `if: github.event_name != 'pull_request'` (or similar) at job level | Aggregator gate: see companion skill `ci-cd-summary-aggregator-job-skip-required-context` |

Key invariant — branch protection sees a whole-job `if:` skip as **missing**, not as success. (A *step*-level skip inside a running job is different: the job still posts a `success` conclusion and satisfies the context.)

### Diagnosis script (paste-ready)

```bash
PR=$1
ORG=$(gh repo view --json owner --jq .owner.login)
REPO=$(gh repo view --json name --jq .name)
BRANCH=$(gh pr view "$PR" --json headRefName --jq .headRefName)
SHA=$(gh pr view "$PR" --json headRefOid --jq .headRefOid)

gh api "repos/$ORG/$REPO/branches/main/protection/required_status_checks" \
  --jq '.contexts[]' | sort > /tmp/required.txt
gh pr view "$PR" --json statusCheckRollup \
  --jq '.statusCheckRollup[].name' | sort -u > /tmp/present.txt

echo "=== Missing required contexts ==="
comm -23 /tmp/required.txt /tmp/present.txt

echo "=== Workflow runs for this SHA ==="
gh run list --commit "$SHA" --json name,conclusion,event \
  --jq '.[] | "\(.name): \(.conclusion // "in-progress") (\(.event))"'
```

If a required context's owning workflow file is absent from the run list → mechanism (1). If present but the named job shows `conclusion=skipped` → mechanism (2).

## Verified On

| Repository | PR / Commit | Date | Notes |
|------------|-------------|------|-------|
| HomericIntelligence/ProjectOdyssey | PR #5382 (diagnosed) → PR #5406 (paths fix) / PR #5407 (aggregator gate) | 2026-05-15 | Ecosystem session. PR #5382 edited `Dockerfile` only; `container-publish.yml` `paths:` filter watched literal `Dockerfile.ci` so workflow never triggered → 6 required contexts missing → BLOCKED with 70 SUCCESS + 0 FAILURE. Branch protection also required `test-images` and `security-scan`, both gated `if: github.event_name != 'pull_request'` at job level → would have stayed skipped even after filter fix. Both mechanisms needed correction. |
