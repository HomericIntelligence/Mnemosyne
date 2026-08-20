---
name: github-ruleset-review-count-governance
description: "Use when setting or auditing required approving-review counts, diagnosing whether a PR is blocked by review or CI, reconciling committed ruleset JSON with live GitHub state, preventing automation self-approval deadlock, or writing a per-scope validation guard. Select the repository's human-review or automation-author regime first, inspect both classic protection and rulesets, and preserve all unrelated policy fields."
category: ci-cd
date: 2026-07-13
version: "2.0.0"
verification: verified-ci
license: BSD-3-Clause
user-invocable: false
history: github-ruleset-review-count-governance.history
tags:
  - github
  - branch-protection
  - ruleset
  - governance
  - review-count
  - auto-merge
  - required-checks
  - drift
---

# GitHub Ruleset Review-Count Governance

## Overview

Required approvals have two legitimate regimes. Human-reviewed repositories need a nonzero review
gate. Repositories where one automation/operator account authors every PR cannot satisfy a nonzero
self-review gate and may intentionally use zero approvals with required CI/CD checks as the merge
contract. Diagnose and change live policy, not assumptions from committed JSON.

Verification remains `verified-ci`. Applied cases and repository-specific values are in the
[notes](./github-ruleset-review-count-governance.notes.md); the byte-preserved source and prior
changelog are in [history](./github-ruleset-review-count-governance.history).

## When to Use

- Canonical ruleset JSON contains `required_approving_review_count: 0` and governance expects human
  review.
- Green auto-merge PRs cannot merge because the automation author is also the only potential
  approver.
- A PR is described as “waiting for review” based only on committed configuration.
- Classic branch protection and a repository ruleset may encode different review requirements.
- Base and `-active` ruleset variants drift or an apply script selects a file the issue omitted.
- A schema guard assumes every scope must use `>=1`, but repository and organization policy differ.
- Committed required-check contexts do not match the live enforcing ruleset.
- Documentation still calls human approval a merge gate in an intentional zero-review,
  single-maintainer repository.

## Regime Decision

| Regime | Preconditions | Approval count | Merge contract |
| --- | --- | --- | --- |
| A: human-reviewed | A distinct eligible reviewer exists and policy requires review | At least 1, or the exact policy value | Required review plus required checks |
| B: automation authors as operator | Same account authors and would approve; no eligible second reviewer | 0 | Required checks and thread-resolution policy |

The regimes are mutually exclusive for a branch. A workflow label such as `state:implementation-go`
is not a GitHub approving review. Existing bypass actors may affect feasibility, but do not infer
their semantics without live evidence.

## Decision Rules

1. **Read live policy first.** Enumerate rulesets, source type, enforcement, pull-request parameters,
   and required checks. Committed JSON is desired-state evidence, not reliable runtime diagnosis.
2. **Inspect both enforcement layers.** Classic protection and repository rulesets are independent.
   A 404 for classic protection means no classic gate, not that ruleset inspection can stop.
3. **Choose the regime from actor topology.** A nonzero count is unsatisfiable when every PR is
   authored by the sole operator and GitHub forbids self-approval.
4. **Preserve unrelated fields.** Read the current full object, change only the approved field, and
   retain thread resolution, stale-review, code-owner, bypass, enforcement, and required-check data.
5. **Scope all canonical variants.** Search base/active and org/repo files and read the deployment
   script. Fixing only issue-named files can leave deployed policy unchanged.
6. **Do not conflate `BLOCKED` with review.** `MERGEABLE` plus required checks queued/in progress can
   be a runner backlog. Inspect required contexts and live review parameters.
7. **Guard exact policy per scope.** A map such as org=1/repo=0 catches drift in both directions;
   blanket `>=1` cannot express a legitimate zero-review repository.
8. **Keep rollout separate.** Do not alter `enforcement` while changing a review count unless the
   task explicitly includes activation.
9. **Make surgical config diffs.** Do not rewrite full JSON formatting to change one field.
10. **Align documentation.** In Regime B, human confirmations for tagging, force updates, or swarm
    deployment remain agent-safety controls, not GitHub review gates.

## Verified Workflow

### 1. Read live state and diagnose the actual blocker

```bash
gh api repos/OWNER/REPO/rulesets \
  --jq '.[] | {id,name,source_type,enforcement}'

gh api repos/OWNER/REPO/rulesets/<id> \
  --jq '.rules[] | select(.type=="pull_request") | .parameters
        | {required_approving_review_count,required_review_thread_resolution}'

gh api repos/OWNER/REPO/rulesets/<id> \
  --jq '[.rules[] | select(.type=="required_status_checks")
         .parameters.required_status_checks[].context]'

gh pr view <pr> --repo OWNER/REPO \
  --json mergeable,mergeStateStatus,reviewDecision,autoMergeRequest
gh pr checks <pr> --repo OWNER/REPO
```

Identify which returned ruleset applies to `main` and whether its `source_type` is repository or
organization. Compare only required contexts when diagnosing a queue; optional matrix jobs do not
explain a required gate.

Read classic protection independently:

```bash
gh api repos/OWNER/REPO/branches/main/protection/required_pull_request_reviews \
  --jq '{count:.required_approving_review_count,
         dismiss:.dismiss_stale_reviews,
         codeowners:.require_code_owner_reviews}'
```

### 2. Inventory desired-state files and deployment consumers

```bash
rg -n 'required_approving_review_count' configs .github scripts tools
rg -n 'active|--active|enforcement|ruleset' scripts tools .github
for file in configs/github/*ruleset*.json; do jq empty "$file"; done
```

List every base/active and org/repo variant, the apply path that selects them, current count,
enforcement, bypass actors, thread resolution, and required checks. Record live-vs-file differences
before editing.

### 3. Apply Regime A — require human review

Change every deployed canonical variant to the exact policy value (commonly 1). Leave enforcement
and unrelated pull-request flags unchanged. Inspect existing bypass actors before proposing new
ones. Use `first(...)` when reading the pull-request rule so the shell receives one scalar:

```bash
count=$(jq 'first(.rules[] | select(.type=="pull_request")
  | .parameters.required_approving_review_count)' "$file")
test "$count" -ge 1
```

If policy says exactly one, validate equality rather than `>=1`; the guard must encode the actual
consumer contract.

### 4. Apply Regime B — remove the unsatisfiable self-review gate

First prove the same account authors the PR and would be the only approver. A self-approval failure
is confirming evidence, not the only input.

For classic protection, preserve current flags in the PATCH. For a repository ruleset, fetch the
complete object, modify only the count, and PUT the full accepted payload required by the current API:

```bash
repo=OWNER/REPO
ruleset_id=<id>

# Values come from the preceding GET; do not replace them with assumed defaults.
gh api -X PATCH \
  "repos/$repo/branches/main/protection/required_pull_request_reviews" \
  -F required_approving_review_count=0 \
  -F dismiss_stale_reviews=<preserved-boolean> \
  -F require_code_owner_reviews=<preserved-boolean>

gh api "repos/$repo/rulesets/$ruleset_id" > /tmp/ruleset.json
jq '(.rules[] | select(.type=="pull_request")
  .parameters.required_approving_review_count) = 0' \
  /tmp/ruleset.json > /tmp/ruleset.patched.json
diff -u /tmp/ruleset.json /tmp/ruleset.patched.json
gh api -X PUT "repos/$repo/rulesets/$ruleset_id" --input /tmp/ruleset.patched.json
```

Mutating live protection is an external policy change: perform it only when the task authorizes the
repository and regime. Re-read both layers and verify required checks and thread resolution remain.

### 5. Reconcile committed configuration and guards

Treat live state as runtime evidence and repository policy as desired-state authority. If they
conflict, resolve which should change; do not silently overwrite either direction.

Use an exact per-file map:

```bash
declare -A expected_reviews=(
  [configs/github/org-ruleset.json]=1
  [configs/github/org-ruleset-active.json]=1
  [configs/github/repo-ruleset.json]=0
  [configs/github/repo-ruleset-active.json]=0
)

for file in "${!expected_reviews[@]}"; do
  count=$(jq 'first(.rules[] | select(.type=="pull_request")
    | .parameters.required_approving_review_count)' "$file")
  want=${expected_reviews[$file]}
  test "$count" = "$want" || {
    echo "ERROR: $file count=$count expected=$want" >&2
    exit 1
  }
done
```

Also compare live and committed required-check sets. Keep JSON formatting stable with a targeted
edit and review the field-level diff.

### 6. Verify end to end

```bash
for file in configs/github/*ruleset*.json; do
  jq empty "$file"
  jq 'first(.rules[] | select(.type=="pull_request")
      | .parameters.required_approving_review_count)' "$file"
done

git diff --check
<repository-schema-and-policy-tests>
gh api repos/OWNER/REPO/rulesets/<id> --jq \
  '.rules[] | select(.type=="pull_request" or .type=="required_status_checks")'
```

For Regime B, verify a green PR becomes eligible through required checks without claiming that an
automation label is an approval. For Regime A, verify an eligible distinct reviewer can satisfy the
gate. Record live IDs and timestamps as volatile evidence, not portable constants.

## Examples

### False approval diagnosis

A committed file said one approval and eight checks, while the live enforcing ruleset said zero
approvals and eleven checks. Two PRs merged without review; the delay was queued required jobs. The
fix reconciled desired state and changed the schema guard to org=1/repo=0.

### Human-review gap across variants

An issue named two JSON files, but the deployment script selected `-active` variants carrying the
same zero count. Searching all consumers identified four files; the review field changed in each
while enforcement and bypass actors remained untouched.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Failure 1 | Edit only issue-named files | Active/deployed variants retain drift | Search every variant and consumer |
| Failure 2 | Use bare multi-result `jq select` | Shell comparison can receive several lines | Wrap with `first()` or validate cardinality |
| Failure 3 | Change enforcement with the count | Mixes policy content and rollout | Keep activation separate |
| Failure 4 | Add bypass actors reflexively | Existing actors may already cover policy | Inspect and verify before adding |
| Failure 5 | Self-approve an automation-authored PR | GitHub forbids approving one’s own PR | Choose Regime B or add a distinct reviewer |
| Failure 6 | Change only classic protection | Repository ruleset may keep the gate | Inspect and update both authorized layers |
| Failure 7 | Treat a workflow label as approval | Labels are not review objects | Diagnose actual GitHub review state |
| Failure 8 | Trust committed JSON for live diagnosis | Files drift from enforcement | Query the live ruleset first |
| Failure 9 | Treat `BLOCKED` as review-required | Pending required checks produce the same state | Inspect required contexts and live parameters |
| Failure 10 | Hardcode `>=1` for every scope | Rejects legitimate automation-author repos | Encode exact per-scope expectations |
| Failure 11 | Reformat the full JSON object | Hides the policy change in churn | Make a surgical field edit |
| Failure 12 | Rewrite docs as “human review required” in Regime B | Contradicts the actual merge contract | Separate CI gates from agent-safety confirmations |
## Results & Parameters

| Parameter | Contract |
| --- | --- |
| Regime A | Distinct eligible reviewer; exact nonzero policy value |
| Regime B | Sole automation/operator author; approval count zero |
| Enforcement layers | Classic protection and applicable rulesets inspected independently |
| Runtime authority | Live API state for diagnosis; committed files for reviewed desired state |
| Guard | Exact expected count per file/scope, plus required-check set comparison |
| Mutation scope | Review count only unless rollout or other fields are explicitly authorized |

## Output Contract

Report the selected regime and actor proof, live classic/ruleset state, enforcing ruleset source,
required review and check values, committed-file inventory, exact authorized mutation, preserved
fields, guard/tests, and final PR eligibility evidence. Mark numeric IDs and live values with their
observation time; never diagnose review blockage from committed JSON alone.

## Companions

- [Case notes](./github-ruleset-review-count-governance.notes.md)
- [Version history and superseded snapshot](./github-ruleset-review-count-governance.history)
