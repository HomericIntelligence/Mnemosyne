---
name: github-ruleset-required-status-checks-management
description: "Safely add, rename, or tune required GitHub ruleset checks without deadlocking pull requests. Use when a check must be required, all-green PRs remain blocked, emitted and required names may differ, strict up-to-date mode causes rebase churn, or a multi-repo emit-before-require rollout needs structural verification and explicit authorization."
category: ci-cd
date: 2026-07-11
version: "2.0.0"
license: BSD-3-Clause
history: github-ruleset-required-status-checks-management.history
user-invocable: false
verification: verified-ci
tags: [github, rulesets, branch-protection, required-status-checks, emit-before-require]
---

# GitHub Ruleset Required Status Checks Management

## Overview

A required context that never reports blocks every PR. GitHub ruleset updates replace whole rule
objects, so safe changes follow read–modify–write, preserve every existing check and rule, and require
proof that the exact context emits on both default-branch and pull-request heads before it becomes
required.

Detailed rollout cases are indexed in
[`github-ruleset-required-status-checks-management.notes.md`](github-ruleset-required-status-checks-management.notes.md).
The complete prior source is in
[`github-ruleset-required-status-checks-management.history`](github-ruleset-required-status-checks-management.history).

## When to Use

- Adding a workflow context to a branch ruleset.
- A required context is absent while all visible checks are green.
- The workflow job exists but its emitted check-run name may not match policy.
- Fast-moving main causes continual up-to-date/rebase churn.
- Canonical CI names have rolled out across multiple repositories.
- An issue says a prerequisite PR already added the check and that premise needs verification.

## Verified Workflow

### 1. Read live policy and emitted names

Find the applying ruleset and record its full payload before mutation:

```bash
gh api repos/<owner>/<repo>/rulesets
gh api repos/<owner>/<repo>/rulesets/<ruleset-id>
MAIN_SHA=$(gh api repos/<owner>/<repo>/commits/main --jq .sha)
gh api repos/<owner>/<repo>/commits/$MAIN_SHA/check-runs \
  --jq '[.check_runs[].name] | unique'
```

Diff `required_status_checks[].context` against emitted check-run names. Exact names matter: a job
can exist and pass under a different display name while the required name never posts. Copy
`integration_id` from an existing GitHub Actions check in the same live ruleset; do not guess it.

Verify claimed prerequisite PRs live:

```bash
gh pr view <pr> --repo <owner>/<repo> --json state,mergedAt,headRefOid
```

An open prerequisite is not default-branch capability.

### 2. Emit before require

Land the workflow/name rollout first. Confirm the exact context on main and on a merged PR’s head:

```bash
gh api repos/<owner>/<repo>/commits/<merged-pr-head>/check-runs \
  --jq '[.check_runs[].name] | unique'
```

A main-push-only job must not be required for PRs. If required and emitted names differ, merge a
keystone rename PR whose own branch emits the canonical names, then let main emit them before any
policy update.

For a batch rollout compute:

```text
add = canonical_names ∩ emitted_on_main ∩ emitted_on_pr - already_required
```

Add only proven names and remove nothing. Retaining an old granular check beside a new aggregate is
the safest superset unless a separately approved migration removes it.

### 3. Obtain explicit mutation authority

Rulesets and branch protection are shared repository state. Reconfirm the exact target repositories,
rulesets, intended checks, and authorization immediately before writes. A broad “finish it,” timed-out
question, or earlier instruction to defer policy changes is not consent to mutate shared protection.

### 4. Read–modify–write the full rule

Extract the live ruleset, append only missing `{context, integration_id}` entries, and PUT the full
replacement body. Preserve enforcement, target, conditions, bypass actors, every rule type, strictness,
and the complete required-check array. Never hand-reconstruct the array from memory.

Use a temporary payload file and validate it before PUT:

```bash
jq '<preserving transformation>' ruleset-before.json > ruleset-after.json
jq empty ruleset-after.json
gh api --method PUT repos/<owner>/<repo>/rulesets/<id> --input ruleset-after.json
```

Keep a digest or immutable capture of the before payload for rollback and audit.

### 5. Verify structural integrity after PUT

Re-read the ruleset and require:

- `enforcement` remains `active`;
- the branch condition still includes `refs/heads/main`;
- all prior rule types remain, including deletion, non-fast-forward, pull request, linear history,
  signatures, and required status checks where applicable;
- every old required check plus the intended additions survives with its integration ID;
- strictness retains the intended value.

Then inspect an open PR and confirm the required names actually report. A 2xx response is not enough;
replacement APIs can accept a structurally incomplete policy.

### 6. Change strict mode on both policy layers

“Require branch up to date” can be enforced independently by classic branch protection and the
ruleset’s `strict_required_status_checks_policy`. Read both:

```bash
gh api repos/<owner>/<repo>/branches/main/protection/required_status_checks --jq .strict
gh api repos/<owner>/<repo>/rules/branches/main
```

On a continuously advancing base, `strict: false` still requires checks but avoids mandatory rebase
churn. If the approved change disables strict mode, patch classic protection and the ruleset layer,
preserving contexts in both. Re-read both values and the check arrays. Flipping only one layer leaves
PRs behind-blocked.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Require first | Added a context before it emitted | Every PR waited forever | Emit on main and PR heads first |
| Near-name match | Required job ID rather than check-run name | Green job posted a different context | Diff exact required/emitted names |
| Hand-built PUT | Reconstructed one rule/check array | Replacement silently dropped gates | Transform the complete live payload |
| Main-only proof | Checked only a push-to-main run | Context never appeared on PR heads | Verify a merged PR head too |
| Destructive canonicalization | Removed old checks during rollout | Reduced protection without separate proof | Add safest superset; remove nothing |
| One-layer strict change | Patched classic protection only | Ruleset strictness still blocked PRs | Read and patch both layers |
| Assumed prerequisite | Trusted issue text saying PR landed | Prerequisite was still open | Query live PR state |
| Implicit authority | Treated broad completion as policy consent | Cross-repo protection exceeded scope | Reconfirm explicit mutation authority |

## Results & Parameters

```text
repository, target branch, ruleset id/name
before-payload digest and enforcement/conditions/rule types
required contexts with integration IDs
default-branch and PR-head emitted context sets
computed additions and explicit no-removal disposition
classic strict value and ruleset strict value before/after
authorization record, PUT response, post-PUT structural diff
representative open-PR required-check result
```

## Verified On

- Emit-before-require and structural verification across 13 repositories.
- Dual-layer strictness correction and blocked-all-green diagnosis verified in CI.
- Verification remains `verified-ci`; proposed/admin-only mutations in historical cases remain
  separately identified in notes/history.
