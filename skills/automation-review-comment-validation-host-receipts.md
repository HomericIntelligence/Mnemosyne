---
name: automation-review-comment-validation-host-receipts
description: "Use when: (1) an automation loop validates implementation replies on existing PR threads, (2) validation needs host-bound pytest evidence, (3) a comment-only review must avoid starting a second broad audit before merge authorization, (4) a reply claims test/coverage results for a SHA without a concrete command/output or artifact receipt, or (5) docs-only path checks or tag-dependent guards can be bypassed by early-return or tagless logic."
category: ci-cd
date: 2026-08-07
version: "1.2.0"
user-invocable: false
verification: verified-ci
history: automation-review-comment-validation-host-receipts.history
tags:
  - automation-loop
  - pr-review
  - comment-validation
  - host-verification
  - pytest-receipts
  - exact-head
  - validation-only
  - merge-wait
  - receipt-completeness
  - claimed-test-results
  - path-triggered-verification
  - tag-integrity
---

# Automation Review Comment Validation with Host Receipts

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-07 |
| **Objective** | Preserve host-bound test evidence when an automation loop validates implementation replies on existing review threads. |
| **Outcome** | Validation-only review received fresh immutable host-verification receipts without dispatching a second broad review, then advanced through the normal exact-head merge path. PR #2611 also showed that prose-only test totals are not receipts: validation kept the thread unresolved until a current-head review could authorize the merge path. PR #2699 added the path-triggered docs-only guard and fail-closed tagless version check, then completed the same exact-head GO, required-check, and conditional-merge path. |
| **Verification** | verified-ci |
| **History** | [changelog](./automation-review-comment-validation-host-receipts.history) |

## When to Use

- A PR re-enters review with implementation replies on existing threads.
- The reviewer needs pytest or other host-run evidence tied to the fresh reviewed head.
- Comment-only validation currently skips host checks or receives an empty receipt list.
- A remediation reply claims tests or coverage for a SHA but supplies no exact command/output or linked artifact.
- The last review thread may resolve while host checks are running, but the loop must not start a new broad audit.
- A docs-only diff has a release or documentation contract that must trigger host verification before language-specific early returns.
- A tag-dependent guard has no reachable canonical tag; treat that as failed evidence, not a skipped success.

## Verified Workflow

### Quick Reference

```text
comment_validation_only = true
review_checkout_wait:
  verify the detached checkout is clean and bound to the live PR head
  run applicable immutable host checks from the reviewed diff
  persist normalized receipts with head_sha, argv, outcome, and output tails
validate_wait:
  pass host_verification_receipts as host_verifications_json to the validator
  if the last thread resolved during host checks, remain validation-only
  do not submit a second broad review
review -> state:implementation-go -> merge_wait:
  retain the reviewed-head proof
  wait for repository merge requirements
  conditionally squash-merge only the same live head
```

### Detailed Steps

1. Keep the comment-validation route selected when the PR has replied threads; it is a
   validation-only review, not a new broad audit.
2. At the fresh exact-head checkout barrier, derive applicable immutable host verification
   from both language/configuration rules and the changed-path manifest before any early return
   that says no Python validation is needed. A docs-only change can still alter a release or
   documentation contract. Store every result as a normalized receipt, including the reviewed
   `head_sha`, exact command arguments, `immutable_source`, `ok: true`, and bounded output tails.
   A tag-dependent guard with no reachable canonical tag fails closed; it never records a skipped
   success.
3. Pass the receipts into the validation agent prompt. An empty receipt list or a prose-only
   claim such as “SHA verified; N tests passed” is not an acceptable substitute for a receipt
   containing the exact command/output or a linked immutable artifact for the current head.
   Leave the thread unresolved and revalidate; do not convert the claim into GO evidence.
4. If the final thread resolves while host checks are in flight, route to validation with
   the receipts already collected. Do not fall through to the broad-review submission path.
5. After validation earns the loop-owned GO decision, apply `state:implementation-go` only
   with the fresh exact-head and explicitly-unarmed checks. `merge_wait` then waits for the
   repository's required checks and conditionally merges that same head; it does not arm
   native auto-merge.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Early return for comment-only validation | Skipped the immutable host-verification plan whenever the comment-validation flag was set. | The validator received no host receipts, so evidence-only findings requiring a host-bound pytest receipt could not be resolved and returned to implementation. | Validation-only means no second broad audit; it does not mean no host verification. |
| Broad-review fallback after thread resolution | Submitted a new broad review when no live threads remained after host checks. | A reply could resolve the last thread during verification, causing the already-selected validation-only route to dispatch redundant broad review work. | Preserve the route selected at entry and continue to `VALIDATE_WAIT` when comment validation owns the pass. |
| Prose-only test receipt | Replied with a reviewed SHA and test/coverage totals but no exact pytest command/output or linked artifact. | The validator could not prove that the claimed run executed on that head, so it kept the evidence thread unresolved and did not treat the reply as GO evidence. | A SHA plus numeric totals is a claim, not a host-bound receipt; persist and pass concrete receipt fields. |
| Language-only host-check selection | Returned before scheduling a path-specific verifier because the diff changed documentation but no Python files. | The intended release/documentation guard never ran, so the review could advance without evidence for the changed contract. | Select path-triggered checks before language/configuration early returns; docs-only diffs still require exact-head receipts. |
| Skip a tag-dependent guard when tags are unavailable | Treated a tagless checkout as an environmental skip. | A skipped comparison cannot prove that the release declaration matches the canonical version source. | Fail closed when the required tag source is unavailable; missing evidence is not success. |

## Results & Parameters

### PR Evidence

- ProjectHephaestus issue `#2624`, PR `#2625`.
- Reviewed implementation head: `6bf5d8feda1518b65b8c9ef9384f1c45fd5c2109`.
- Focused stage tests: 218 passed; full locked suite: 7,186 passed, 11 skipped, 5 deselected; coverage: 84.81%.
- Live state sequence: `state:implementation-no-go` → `state:implementation-go` at 17:56:28Z → NOGO removal at 17:56:30Z → merge at 18:05:38Z.
- Merge commit: `982316b4f0527b43cc898c866d574381b034a82d`.
- ProjectHephaestus issue `#2362`, PR `#2611`: validation rejected prose-only pytest claims across superseded heads; the final review matched head `588a9d8bde5d9ee40e7c620c0e6bcd8e67b8b831`, `state:implementation-go` was added at 18:30:07Z, NOGO was removed at 18:30:09Z, and conditional merge commit `d65d5e495c34d4b5fa2527a05f40aaa68043bf18` landed at 18:30:20Z. Required checks passed and `autoMergeRequest` was null.
- ProjectHephaestus issue `#2696`, PR `#2699`: the docs-only path triggered an exact-head host check whose receipt required the command, immutable source, and `ok: true`; tagless version validation failed closed. The final head `1e0dbf5c` received GO at 18:15:14Z, the required-checks gate completed at 18:28:01Z, and conditional merge `867eecbf` followed at 18:28:39Z with no GitHub review/comment object or native auto-merge request.

### Path-triggered receipt contract

```yaml
changed_path: <path from the verified diff>
head_sha: <exact reviewed head>
argv: [<host command arguments>]
immutable_source: true
ok: true
```

Do not let a language-specific early return suppress a selected path check. If the command needs a
canonical release tag and no tag is reachable, return a blocking validation result instead of a
skipped receipt.

### Regression Contract

```python
assert item.payload["host_verification_receipts"]
assert json.loads(validation.job.prompt_kwargs["host_verifications_json"]) == receipts
assert no_broad_review_was_submitted
```

Expected behavior is a validation `AgentJob` carrying receipts from the exact reviewed
head, followed by the normal loop-owned GO-label and conditional merge path.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #2624 / PR #2625 | Comment-only validation carried fresh host receipts, avoided a second broad review, and merged after exact-head authorization and required checks. |
| ProjectHephaestus | Issue #2362 / PR #2611 | Prose-only test/coverage claims without concrete host receipts remained review findings across changed heads; the final exact-head GO-label transition was followed by NOGO removal and conditional merge with required checks green. |
