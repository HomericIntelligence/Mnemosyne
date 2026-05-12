---
name: pr-preexisting-failure-triage
description: 'Distinguish PR-introduced CI failures from pre-existing main-branch rot using the GitHub check-runs API per individual check name (NOT workflow name), then resolve confirmed pre-existing failures via the quick-fix / admin-merge / tracking-issue ladder. Use when: (1) a PR is BLOCKED by failing required status checks, (2) a reviewer has labeled failures as PREEXISTING_CI_NOISE (re-verify — they are wrong ~2/3 of the time), (3) you must decide between fixing in-scope, admin-merging, or filing a follow-up issue.'
category: ci-cd
date: 2026-05-11
version: 1.1.0
user-invocable: false
verification: verified-ci
history: pr-preexisting-failure-triage.history
tags:
  - ci-failure
  - pr-blocked
  - preexisting
  - check-runs-api
  - admin-merge
  - tracking-issue
  - required-status-check
---
## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-05-11 |
| **Goal** | Determine whether each failing required check on a BLOCKED PR is PR-introduced (must fix) or pre-existing on main (use admin-merge + tracking-issue ladder), without trusting reviewer pre-classifications |
| **Input** | PR number, repo slug (`org/repo`) |
| **Output** | Per-check classification (PR-INTRODUCED / PRE-EXISTING / NEW-CHECK) plus a resolution action for each |
| **Outcome** | 3-of-3 BLOCKED PRs in the 2026-05-11 sweep correctly triaged: 2 reviewer mis-classifications caught and fixed (Agamemnon #368 markdownlint+depscan, Hermes #614 urllib3 CVE), 1 truly pre-existing admin-merged with tracking issue (Keystone #552 + #553) |
| **Verification** | verified-ci |
| **History** | [changelog](./pr-preexisting-failure-triage.history) |

## When to Use

- A PR shows status `BLOCKED` because one or more required checks are failing
- A reviewer has tagged failures as `PREEXISTING_CI_NOISE`, `pre-existing`, or "not caused by this PR" — ALWAYS re-verify; reviewers were wrong on 2 of 3 such labels in the 2026-05-11 sweep
- A `.claude-review-fix-*.md` plan states "no fixes required" but CI shows FAILURE
- Before enabling `gh pr merge --auto` on a PR with red checks
- Before deciding to expand a PR's scope to fix a failing check (you may not need to — admin-merge may be valid)
- After a tooling/dependency bump where a reviewer claims unrelated failures are noise

## Verified Workflow

### Quick Reference

```bash
# 0. Always unset shadowing tokens first
unset GITHUB_TOKEN GH_TOKEN

ORG=HomericIntelligence
REPO=ProjectAgamemnon
PR_NUM=368

# 1. List failing checks on the PR by EXACT name
gh pr view "$PR_NUM" --repo "$ORG/$REPO" --json statusCheckRollup \
  --jq '.statusCheckRollup[] | select(.conclusion == "FAILURE") | .name'

# 2. Get main HEAD SHA
MAIN_SHA=$(gh api "repos/$ORG/$REPO/branches/main" --jq '.commit.sha')

# 3. Per failing check name, query main HEAD's check-runs (authoritative)
for chk in "markdownlint" "depscan / trivy"; do
  status=$(gh api "repos/$ORG/$REPO/commits/$MAIN_SHA/check-runs" \
    --jq ".check_runs[] | select(.name == \"$chk\") | .conclusion" | head -1)
  printf "%-30s main=%s\n" "$chk" "${status:-not-run}"
done
# success  -> PR-INTRODUCED  (fix in this PR)
# failure  -> PRE-EXISTING   (use ladder below; do NOT fix in this PR)
# not-run  -> NEW-CHECK      (added by PR's branch; investigate)

# 4a. Resolution: confirmed PRE-EXISTING -> admin-merge + tracking issue
gh pr merge "$PR_NUM" --repo "$ORG/$REPO" --squash --admin
gh issue create --repo "$ORG/$REPO" \
  --title "ci: <check-name> failing on main since YYYY-MM-DD" \
  --body "Diagnostic context, log excerpt, action checklist"
```

### Detailed Steps

#### Step 1: Identify failing required checks (by exact name)

```bash
gh pr view "$PR_NUM" --repo "$ORG/$REPO" --json state,statusCheckRollup
```

If `state` is `BLOCKED`, list every entry with `conclusion == "FAILURE"`. Use the EXACT
`name` field — this is the required-status-check context that branch protection enforces.

CRITICAL: do NOT use the workflow name from the Actions UI. A workflow can show FAILURE
while one of its sub-jobs (the actual required-check context) was PASS. The required check
is identified by the exact `name` from `statusCheckRollup`.

#### Step 2: Resolve main HEAD SHA

```bash
MAIN_SHA=$(gh api "repos/$ORG/$REPO/branches/main" --jq '.commit.sha')
```

This is the authoritative reference state. We test whether each failing check passes here.

#### Step 3: Query check-runs API per check name on main

```bash
for chk in "<failing-check-1>" "<failing-check-2>"; do
  status=$(gh api "repos/$ORG/$REPO/commits/$MAIN_SHA/check-runs" \
    --jq ".check_runs[] | select(.name == \"$chk\") | .conclusion" | head -1)
  printf "%-30s main=%s\n" "$chk" "${status:-not-run}"
done
```

Three possible outcomes per check:

| Outcome on main | Classification | Action |
| --------------- | -------------- | ------ |
| `success` | PR-INTRODUCED | Fix in this PR — your responsibility |
| `failure` | PRE-EXISTING | Use resolution ladder (Step 4) — do NOT expand scope |
| `not-run` | NEW-CHECK | Check was added by the PR's branch — investigate why it doesn't exist on main |

#### Step 4: Resolution ladder for PRE-EXISTING failures

Try in order:

```text
Option A: Quick fix (<=10 min budget)
   ONLY if root cause is a config error or test flake easily fixed without scope creep.
   Push fix in this PR; otherwise proceed to B.

Option B: Admin-merge
   gh pr merge "$PR_NUM" --repo "$ORG/$REPO" --squash --admin
   Bypasses the failing required check via admin override.
   Requires the keyring token to have admin scope; if it lacks scope,
   auto-merge stays armed and a human admin must merge.

Option C: File tracking issue (ALWAYS, even alongside A or B)
   gh issue create --repo "$ORG/$REPO" \
     --title "ci: <check-name> failing on main since YYYY-MM-DD" \
     --body "<check name>, link to failing run, log excerpt, suspected root cause, action checklist"
```

#### Step 5: Re-verify reviewer classifications

If a reviewer/agent already classified failures as `PREEXISTING_CI_NOISE`, run Steps 1-3
anyway. Empirically, 2 of 3 such classifications in the 2026-05-11 sweep were wrong.
The ~5-second `check-runs` query produces authoritative truth that overrides any prior label.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Trusting reviewer's PREEXISTING_CI_NOISE label | Took the reviewer's classification at face value on Agamemnon #368 and Hermes #614 | `check-runs` API showed those checks PASSED on main HEAD — failures were PR-introduced (markdownlint MD031 blank-line, urllib3 CVE upgrade) | ALWAYS re-verify with `check-runs` API before trusting any prior classification; ~5 sec to verify, ~10 min wasted per false trust |
| Comparing workflow run conclusion | Looked at the workflow's overall `conclusion` field instead of the individual check name | A workflow can show FAILURE while one of its sub-jobs (the actual required-check context) was PASS — workflow conclusion != required-check conclusion | Use `check-runs` API keyed by the EXACT `name` from `statusCheckRollup`, not workflow names |
| File-overlap heuristic alone | Assumed a failing test group with zero file overlap to PR diff means pre-existing | A check can fail because of an env/config drift unrelated to file paths (e.g., trivy DB lookup, transient dep install) — file overlap is necessary but not sufficient | File-overlap is a hint; the `check-runs` API on main HEAD is the only authoritative test |
| Assuming `gh pr merge --admin` always works | Ran admin-merge with the default keyring token | Not all bot/PAT setups have admin scope on every repo; some failed silently | Test admin-merge on one PR first; on failure, auto-merge stays armed and a human admin must merge |
| Expanding PR scope to fix unrelated rot | Started fixing pre-existing failures inside the surface PR | Scope creep, slower review, harder revert if the rot fix regresses something else | Use admin-merge + tracking issue (Option B + C) for confirmed pre-existing failures; never expand scope |
| Committing review plan file | Treated `.claude-review-fix-*.md` as an implementation artifact to commit | File is a working artifact for the agent, not a deliverable | Only commit actual code/config changes, never the review plan file |
| Retrying tests locally | Attempted to rerun failing CI groups locally to confirm pre-existing status | Unnecessary — `check-runs` API on main HEAD is faster and authoritative | Use `gh api .../check-runs` to classify failures without running tests |

## Results & Parameters

### Empirical re-classification rate (2026-05-11 sweep)

3 of 3 lingering BLOCKED PRs in the post-fix-wave state needed this triage. 2 of 3
reviewer classifications were wrong. **Diagnose every time** before either fixing or
admin-merging.

| PR | Reviewer label | Actual (check-runs API) | Resolution |
| -- | -------------- | ----------------------- | ---------- |
| ProjectAgamemnon #368 | PREEXISTING_CI_NOISE | PR-INTRODUCED (markdownlint MD031 + transient trivy install) | Fix in PR |
| ProjectHermes #614 | PREEXISTING_CI_NOISE | PR-INTRODUCED (urllib3 CVE 2026-44431/44432) | Fix in PR (upgrade urllib3) |
| ProjectKeystone #552 | (none) | PRE-EXISTING (`AgentCoreTest.BackpressureConcurrentTrigger` aborting on main HEAD) | Admin-merge + tracking issue #553 |

### Full diagnostic script

```bash
#!/usr/bin/env bash
set -euo pipefail
unset GITHUB_TOKEN GH_TOKEN

ORG="${1:?org}"
REPO="${2:?repo}"
PR_NUM="${3:?pr-number}"

mapfile -t FAILING < <(
  gh pr view "$PR_NUM" --repo "$ORG/$REPO" --json statusCheckRollup \
    --jq '.statusCheckRollup[] | select(.conclusion == "FAILURE") | .name'
)

if [ "${#FAILING[@]}" -eq 0 ]; then
  echo "No failing required checks on PR #$PR_NUM."
  exit 0
fi

MAIN_SHA=$(gh api "repos/$ORG/$REPO/branches/main" --jq '.commit.sha')
echo "Main HEAD SHA: $MAIN_SHA"
echo

for chk in "${FAILING[@]}"; do
  status=$(gh api "repos/$ORG/$REPO/commits/$MAIN_SHA/check-runs" \
    --jq ".check_runs[] | select(.name == \"$chk\") | .conclusion" | head -1)
  case "${status:-not-run}" in
    success) verdict="PR-INTRODUCED  (fix in this PR)" ;;
    failure) verdict="PRE-EXISTING   (use admin-merge + tracking issue ladder)" ;;
    *)       verdict="NEW-CHECK      (added by PR branch; investigate)" ;;
  esac
  printf "%-40s main=%-10s -> %s\n" "$chk" "${status:-not-run}" "$verdict"
done
```

### Resolution decision tree

```text
Is the failure pre-existing on main? (per check-runs API)
- NO  -> fix in this PR (PR-introduced is your responsibility)
- YES -> Three-option ladder (try in order):
    - Option A: Quick fix (<=10 min budget) — only if root cause is a config
                error or test flake easily fixed without scope creep
    - Option B: Admin-merge — gh pr merge <PR> --repo <org/repo> --squash --admin
                Bypasses the failing required check via admin override
    - Option C: File tracking issue (ALWAYS, even alongside A or B)
                gh issue create --repo <org/repo> \
                  --title "ci: <check-name> failing on main since YYYY-MM-DD"
```

### Tracking issue body template

```markdown
## Failing check
`<exact check name from statusCheckRollup>`

## Status on main
- Main HEAD SHA: <sha>
- Conclusion: failure
- First observed failing on main: <best-known date or run URL>

## Log excerpt
<paste the failing log lines that show root cause>

## Suspected root cause
<one paragraph hypothesis>

## Action checklist
- [ ] Reproduce locally on `main`
- [ ] Identify regressing commit (`git bisect` or run history)
- [ ] Open fix PR
- [ ] Close this issue when main is green again
```

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| ProjectAgamemnon | PR #368 (markdownlint MD031 + depscan trivy) — reviewer mis-classified as PREEXISTING_CI_NOISE; check-runs API showed PR-introduced | 2026-05-11 ecosystem sweep, fix-up cycle |
| ProjectHermes | PR #614 (urllib3 CVE 2026-44431/44432) — reviewer mis-classified as PREEXISTING_CI_NOISE; check-runs API showed PR-introduced | 2026-05-11 ecosystem sweep, fix-up cycle |
| ProjectKeystone | PR #552 (`coverage` failing) — confirmed truly pre-existing (`AgentCoreTest.BackpressureConcurrentTrigger` aborts on main HEAD); resolved via `gh pr merge --admin --squash` + tracking issue #553 | 2026-05-11 ecosystem sweep, fix-up cycle |
