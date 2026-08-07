---
name: automation-review-authorization-ci-boundary
description: "Keep automation-loop source-review authorization independent of CI/CD, bind it to an exact PR head, and conditionally merge only that reviewed head. Use when: (1) review authorization is mistakenly delegated to CI, (2) a review can race with a changed head or dirty checkout, (3) unresolved review threads block advancement, (4) remediation must retract out-of-scope paths before publication, (5) a label advances implementation or merge state, (6) an external actor may own auto-merge, (7) a downstream rerun sees a merged PR, (8) a completed run needs a live event-order audit, (9) a read-only reviewer checkout performs redundant pre-barrier remote synchronization or emits an expected missing-branch error, (10) a successful remediation reply has no commit and must remain reviewable, (11) an inline review leaves no GitHub review/comment object, (12) a no-commit remediation changes only PR title/body metadata, (13) review preparation force-rebases an already-current PR head and prevents convergence, or (14) an evidence-only finding needs repeated same-head review without manufacturing a source commit."
category: architecture
date: 2026-08-06
version: "3.18.0"
user-invocable: false
verification: verified-ci
history: automation-review-authorization-ci-boundary.history
tags:
  - automation-loop
  - pr-review
  - ci-independent
  - authorization-boundary
  - implementation-go
  - restart-safety
  - state-label
  - source-review
  - reviewed-head
  - review-convergence
  - noop-rebase
  - remote-head-verification
  - checkout-verification
  - auto-merge-ownership
  - fail-closed
  - review-thread-completeness
  - github-event-audit
  - scope-retraction
  - pre-publication-guard
  - no-commit-reply
  - evidence-only-remediation
  - same-head-evidence-retry
  - exact-head-receipt
  - stale-journal
  - pr-metadata
  - metadata-fingerprint
---

# Automation Review Authorization: CI Boundary

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-06 |
| **Objective** | Keep a code-automation loop's strict source-review decision inside that loop rather than delegating its authorization to CI/CD, bind the decision to the exact GitHub head SHA, and prevent the queue from mutating externally owned auto-merge. |
| **Outcome** | ProjectHephaestus PR #2345 demonstrated the active fail-closed path. PR #2506 supplied a compact happy-path audit. PR #2510 added a pre-publication scope-retraction guard. PR #2570 demonstrated how to audit several review/fix cycles without transferring authorization from an older reviewed head. PR #2592 added the evidence-only remediation rule: a successful no-commit reply is posted against the verified head and remains under reviewer-owned disposition. PR #2594 showed the same reply handoff plus a review-to-merge path where GO preceded slow required checks. PR #2595 / issue #2137 showed that repeated validation can isolate a PR-metadata-only finding: source absence is not proof that the live PR body was corrected, and the correct remediation may remain a head-bound no-commit handoff. PR #2598 showed that a scanner-backed issue remains NOGO until the current head adds remediation-specific regression coverage, then advances through exact-head review, GO-label replacement, and conditional merge. PR #2616 demonstrated a compact inline-review path: initial NOGO, final GO, NOGO removal, and merge with no GitHub review or issue-comment object. PR #2622 demonstrated a substantive remediation path: the initial exact-head review found three major host-verification gaps, the loop stayed NOGO, and a fresh review of the corrected head authorized GO before a conditional merge. PR #2635 demonstrated that an evidence-only finding may need repeated no-commit replies and reviews on one unchanged head; the loop kept NOGO until the thread was resolved, then authorized and conditionally merged that exact head. PR #2643 / issue #2366 added a direct implementation happy path: the inline review emitted no GitHub review/comment object, `state:implementation-go` was still the durable authorization, required checks completed afterward, and merge_wait merged the reviewed head with native auto-merge unset. PR #2665 / issue #2383 showed the same direct-implementation happy path with no GitHub review/comment object: the loop-owned GO label preceded the later required-check gate, and merge_wait conditionally merged the reviewed head with native auto-merge unset. PR #2689 / issue #2473 reconfirmed that path: the exact final head merged after the loop-owned GO label and later required checks, with no GitHub review/comment object and native auto-merge unset. PR #2690 / issue #2476 reconfirmed the direct implementation path for provider-session metadata hardening: no GitHub review/comment object was emitted, the exact-head GO label preceded the required-check gate, and merge_wait conditionally merged with native auto-merge unset. |
| **Verification** | verified-ci on ProjectHephaestus PRs #2345, #2506, #2510, #2570, #2592, #2594, #2595, #2598, and #2616. PR #2595's final review matched head `d68e1d43`; GO was added at `16:35:56Z`, NOGO was removed at `16:35:58Z`, the required-checks gate completed at `16:41:02Z`, and conditional merge commit `da620c2f` followed at `16:41:54Z` with `autoMergeRequest` null. PR #2616's final head was `36322151`; GO was added at `13:14:12Z`, NOGO was removed at `13:14:15Z`, the required-checks gate completed at `13:14:26Z`, and merge commit `5dbfd3e6` followed at `13:14:35Z` with `autoMergeRequest` null. PR #2622's final head was `e418b3f0`; the first review's NOGO at `14:57:29Z` was replaced by GO at `15:18:07Z`, NOGO was removed at `15:18:09Z`, the required-checks gate completed at `15:27:43Z`, and merge commit `022e2ff2` followed at `15:28:21Z` with `autoMergeRequest` null. PR #2665's final head was `f2201c97`; `state:implementation-go` was recorded at `08:27:00Z`, all required checks passed by `08:34:35Z`, and conditional merge commit `1b7bfb16` followed at `08:35:06Z` with `autoMergeRequest` null. PR #2690's final head was `6cdb34ee`; `state:implementation-go` was recorded at `23:46:40Z`, the required-checks gate completed at `23:51:51Z`, and conditional merge commit `f1e8abfd` followed at `23:52:37Z` with `autoMergeRequest` null. |
| **Issue #2618 / PR #2619** | verified-ci. Initial NOGO was recorded at `13:32:41Z`; the final review matched head `a24ccf21` at `16:04:12Z`, GO replaced NOGO at `16:04:55Z`, the required-checks gate completed at `16:14:59Z`, and conditional merge commit `4631d91c` followed at `16:15:12Z` with `autoMergeRequest` null. Local validation reported 469 focused tests, Ruff, mypy, and the full pre-push suite (7,163 passed, 11 skipped, 5 deselected; 84.76% coverage). |
| **Issue #2630 / PR #2631** | verified-ci. Review preparation preserved final head `692bc1fb` because current `origin/main` was already its ancestor, then verified the exact remote branch ref without rebasing or pushing. The matching review preceded GO replacement, the required-checks gate completed on that head, and conditional squash merge `baa59341` followed with native auto-merge null. |
| **Issue #2632 / PR #2635** | verified-ci. The initial review bound to head `0bfa3d4a` found missing host-validation receipts and applied NOGO. Two evidence-only replies and three `COMMENTED` reviews remained on that unchanged head; no synthetic source commit was created. After the thread resolved, GO replaced NOGO at `02:44:00Z` / `02:44:02Z`, and conditional squash merge `9b3450ef` followed at `02:44:12Z` with native auto-merge null. |
| **Issue #2366 / PR #2643** | verified-ci. The final implementation head was `6cc7d69079647e845d1e45ee21defb8e41544b56`; GitHub exposed no review or issue/PR comment object. The loop applied `state:implementation-go` at `22:53:34Z`, the required-checks gate completed at `23:00:42Z`, and merge_wait conditionally merged as `980c340edaaf99b650fd76e0f956d2ae2a5c197d` at `23:01:38Z` with `autoMergeRequest` null. |
| **Issue #2379 / PR #2660** | verified-ci. The first exact-head review stayed NOGO after finding that validation covered `dependencies` but omitted the producer-required top-level `fixes` list; the implementation replied on final head `1950319af73544e0a0298101f9db852cbbfd3505` with missing/non-list `fixes` regressions in human and JSON modes. The matching review was followed by GO at `06:39:06Z`, NOGO removal at `06:39:08Z`, required-checks completion at `06:48:20Z`, and conditional merge commit `911b49828c1f3b14d9573e49f4b45da06fe5b172` at `06:49:17Z`; native auto-merge was unset. |
| **Issue #2383 / PR #2665** | verified-ci. The PR body said the automation pipeline did not run tests, but live GitHub evidence showed no review/comment object, `state:implementation-go` at `08:27:00Z`, required-check completion at `08:34:35Z`, and merge commit `1b7bfb16e2177f8988baecca65dd25fc5878bc9a` at `08:35:06Z`; native auto-merge was null. |
| **Issue #2473 / PR #2689** | verified-ci. The direct implementation review targeted final head `289e14c0a5955812650c9d876d48ba696102c604` and emitted no GitHub review or issue/PR comment object. The loop recorded `state:implementation-go` at `23:17:26Z`; `pr-policy`, unit, integration, and the required-checks gate passed later, with the gate completing at `23:42:45Z`; and merge_wait conditionally merged as `70f5a8fe03c2cd6ad17c7a4e58803bbec69fa502` at `23:43:11Z` with `autoMergeRequest` null. The PR body's `Testing: Not run by the automation pipeline` note was informational, not review or CI evidence. |
| **Issue #2476 / PR #2690** | verified-ci. The direct implementation review targeted final head `6cdb34ee951ab295fc22cfad23dd26dd7a540111` and emitted no GitHub review or issue/PR comment object. The loop recorded `state:implementation-go` at `23:46:40Z`; the required-checks gate completed at `23:51:51Z` after the required checks passed; and merge_wait conditionally merged as `f1e8abfd9f094671a5e31192f69ae3954d4f3b41` at `23:52:37Z` with `autoMergeRequest` null. |

## When to Use

- A strict source review has been added as a required CI check even though the automation loop, not CI, is expected to decide whether implementation may advance.
- The loop is blocked by a workflow artifact, status, lease, or trigger that it cannot start, observe reliably, or repair.
- A restart path needs to determine whether a PR may proceed without reconstructing a CI-run proof artifact.
- You need to retire an external review-proof system while preserving historical ADRs and making the active contract unambiguous.
- A direct `--prs` discovery route can create an issue-less work item that reaches merge-wait with a stale or externally applied GO label.
- You are about to launch a direct `--prs` review run and need to know whether a selected reviewer model will actually be invoked, rather than merely selected by CLI configuration.
- A process-local strict-review mutex is released at a stage handoff even though the successor has not yet confirmed the live reviewed head and safe continuation.
- Review-local head, verdict, or evidence data remains in a work item after the label has been applied, where a later stage could accidentally turn it into a second authorization requirement.
- A downstream rerun evaluates a PR after merge and must short-circuit on PR state instead of expecting `autoMergeRequest` to still be present; GitHub clears `autoMergeRequest` on merged PRs.
- A PR body/diff is fetched while a push may occur, or the reviewer can inspect a dirty/stale checkout rather than the GitHub head it is supposed to approve.
- Review preparation rewrites and lease-pushes an already-current PR branch before every review pass, invalidating head-bound receipts and preventing convergence.
- A label write would advance the pipeline without fresh proof that the PR is `OPEN` and explicitly unarmed, or an approving/GO label would advance without also proving the reviewed head still matches.
- The queue sees `autoMergeRequest` populated and is tempted to defer, disable, adopt, or replace it. GitHub does not expose a conditional disable operation that can prove ownership of that request.
- Repeated review runs encounter unresolved automation-created threads and must distinguish a safe stand-down from authorization to advance.
- A review finding says to drop, remove, or split unrelated/out-of-scope files, and the address agent must not publish a partial or malformed retraction.
- A scanner-backed review validates only fields consumed by the filter and may miss required fields in the producer's complete result contract.
- You need to audit a completed automation-loop run from durable GitHub facts without treating review prose or CI results as authorization.
- A loop review is inline/local and GitHub exposes no review or issue-comment object; audit the exact head, state labels, required-check timing, and merge event without fabricating a review record.
- A no-commit remediation changes only PR title/body metadata, so validation must not reuse the pre-correction PR snapshot.
- A scanner-backed issue has a superficially related test or documentation change, but the current head must prove that the reported scanner input is addressed.
- Review authorization appears before slow required checks finish, and `merge_wait` must preserve the exact-head decision while waiting for repository merge requirements.
- A successful remediation reply produced no commit and must still be reviewed as evidence rather than rejected as a failed implementation.
- A reply journal may have been created for an older PR head and must not be replayed after the head changes.
- An evidence-only finding requires another review pass on the same head, and the loop must preserve NOGO until the reviewer accepts and resolves the thread rather than manufacturing a commit to force progress.

## Verified Workflow

### Quick Reference

```text
automation loop owns source-review authorization
  1. snapshot GitHub PR metadata and its head; reject it if the head moves
  2. if the writer already contains the current base, verify local HEAD and the exact remote branch ref, then return the unchanged head without rebasing or pushing
  3. verify a clean checkout at that exact head in a dedicated Git job, then derive its diff locally from the verified base/head pair
  4. run the strict PR review in the loop (CI-free) against that metadata and derived diff
  5. stand down while any relevant review thread remains unresolved; rerun only after thread state or head changes
  6. for successful no-commit remediation, re-read current PR title/body and head immediately before validation; require the metadata head to equal the verified current head, nonce-fence the fields, post `[auto-msg] reply has no corresponding commit, review thoroughly`, return an exact `{pushed:false, head_sha:<sha>}` receipt, and leave reviewer disposition open
  7. if evidence remains under review, preserve the unchanged head and NOGO across further reply/review passes; do not manufacture a source commit merely to advance the queue
  8. ignore reply journals whose recorded head differs from the verified current head
  9. for a scope retraction, require a complete safe path manifest and compare every path to the reviewed base before push
  10. before every state-changing label, re-read OPEN + explicit autoMergeRequest:null
  11. require the exact reviewed head only for an approving/GO label; drift revokes proof and re-reviews
  12. merge_wait revalidates the proof and conditionally squash-merges only that exact head; it never mutates native auto-merge

merge-wait is also the authorization boundary of last resort
  1. reject an item without required issue/requirements context before consuming a label
  2. route missing or drifted reviewed-head proof back to PR review
  3. stand down without mutation when external auto-merge is present or state is partial
  4. after repository merge requirements pass, use a SHA-conditional normal squash merge
  5. retain the strict-review guard until the terminal or reviewed-head-safe continuation

CI/CD is outside this decision:
  - do not query checks, workflow runs, artifacts, or deployments
  - do not create review-proof workflows or triggers on review/implementation-go
  - do not make an external CI result a prerequisite for loop progress
```

### Completed-run event audit

```bash
REPO=HomericIntelligence/Hephaestus
PR=2506

# Confirm the review's commit binding and informational record.
gh api "repos/$REPO/pulls/$PR/reviews" \
  --jq '.[] | {submitted_at, commit_id, state, body}'

# Confirm the durable authorization and terminal transition order.
gh api "repos/$REPO/issues/$PR/events" --paginate \
  --jq '.[] | select(.event == "labeled" or .event == "merged")
    | {created_at, event, label: (.label.name // null), commit_id}'

gh pr view "$PR" --repo "$REPO" \
  --json state,mergedAt,mergeCommit,commits \
  --jq '{state, mergedAt, mergeCommit: .mergeCommit.oid,
         head: .commits[-1].oid}'
```

Read the result as three distinct facts: the review record identifies what head was inspected,
the `state:implementation-go` event is the loop's durable authorization, and the merge event is
the terminal mutation. Check runs may be inspected separately as repository-health context, but
their completion time does not replace any of those facts.

Some inline review paths intentionally publish no GitHub review or issue-comment object. When
both surfaces are empty, record that observability fact rather than treating it as a missing
authorization or inventing a review record; use the exact-head and exclusive label/merge events
as the durable audit, with CI still treated as merge-contract context only.

When a PR has several review/fix cycles, compare every review's `commit_id` with the final PR
head. Older reviews remain useful audit history but cannot authorize the newer revision. A
`COMMENTED` review with an empty body can still prove commit binding; its prose and review state
do not grant GO. Confirm that the matching final-head review precedes the exclusive GO/NOGO
label transition, required checks finish before merge, and the merge event is last.

### Direct-PR admission preflight

```bash
PR=2357
REPO=HomericIntelligence/Hephaestus

# `--prs` selects a target; it does not override the requirements-context invariant.
gh pr view "$PR" --repo "$REPO" --json number,body,closingIssuesReferences \
  --jq '{number, closingIssuesReferences, body}'

# Require exactly one standalone closing line before spending a reviewer-model job.
test "$(gh pr view "$PR" --repo "$REPO" --json body --jq .body \
  | rg -x 'Closes #[0-9]+' | wc -l | tr -d ' ')" = 1
```

If this preflight has no exact closing line or no usable linked requirement, stop and repair the
PR metadata first. Do not retry with a different reviewer model or reasoning effort: model
selection is downstream of deterministic admission, so it cannot turn an orphaned PR into a
reviewable one.

### Detailed Steps

1. Establish a single decision owner. Source-review authorization belongs to the automation loop when that loop is responsible for planning, implementation, review, and advancement. CI/CD may validate a repository independently, but it is not evidence the loop can depend on for this decision.

2. Capture stable GitHub metadata before dispatching the reviewer. Read the body, base branch, and head SHA, then read the head again. If the two heads differ, discard the context rather than reviewing a moving target. Run a dedicated Git job that proves the worktree was clean, synchronized to that exact head, has `HEAD` equal to it, and remained clean after synchronization. After that proof, fetch the named base branch and derive the diff locally from the verified base/head pair. Do not use a remotely fetched mutable diff as review evidence: an ABA head change can otherwise pair an intermediate diff with a restored head. An expected SHA embedded only in an agent prompt is not checkout evidence.

   Prepare the writer branch without manufacturing head drift. After fetching the base, use
   `git merge-base --is-ancestor <remote>/<base> HEAD`. When it succeeds, read local `HEAD`,
   require it to equal the expected remote head, and query exactly `refs/heads/<branch>` with
   `git ls-remote --refs` without updating local refs. Return `{rebased:false, published:false,
   head_sha:<sha>}` only when the remote still matches. Perform no rebase or push on this no-op
   path. A missing, malformed, or moved remote ref fails closed; a genuinely behind branch keeps
   the signed policy-rebase and conditional lease-publish path.

   For a disposable read-only reviewer worktree, separate local scratch creation from that authoritative proof. Create it detached at the parent checkout's `HEAD`; do not attempt to add the remote/fork PR branch and do not synchronize it to the remote. Then capture the live review context and let the single checkout barrier fetch, bind, clean-check, and compare `HEAD` with the captured PR SHA. Only that barrier may give the worktree to the reviewer. A pre-barrier sync is a second mutable fetch with no authorization value; a pre-barrier remote-branch checkout can log an expected missing-ref error and fall back to trunk before the very same barrier replaces it. Both obscure the audit while adding no safety.

   Run strict PR review as an in-loop, CI-free operation against that metadata and checkout-derived diff. Require an explicit GO result before transition; a missing, ambiguous, or NO-GO result must not apply the approval label.

   For direct `--prs` operation, first verify the requirements context deterministically. `--prs`
   identifies the PR but does not waive the exact standalone `Closes #N` contract or synthesize
   acceptance criteria from prose such as `Addresses #N`. When the preflight fails, the correct
   result is a fail-closed terminal record with zero reviewer jobs; changing `--reviewer-model` or
   its reasoning effort must not bypass that result. This is admission control, not a duplicate
   LLM policy check and not a CI dependency.

3. Report review evidence precisely. A reviewer may issue GO from sufficient source and local evidence even when its sandbox cannot independently rerun every claimed test, but it must name the gap, avoid claiming those tests passed, and grade the evidence accordingly. For scanner-backed issues, a docstring-only or expectation-only change is not remediation evidence; require a current-head change that addresses the scanner input and a regression that would fail if it returns. Do not turn that disclosure into a CI dependency for the loop decision.

4. Require complete review-thread state before approval. If automation-created threads remain unresolved and the loop cannot prove that replying or resolving them preserves human activity, retain NOGO and stand down without arming merge. Repeated runs against the same unresolved state are not progress. Resume with a fresh review only after the threads have concrete dispositions and resolutions or the head changes.

   A successful remediation reply is still review input when it produces no commit. Post it only
   against the verified current head, include the literal `[auto-msg] reply has no corresponding
   commit, review thoroughly` warning, and leave acceptance, rejection, and resolution to the
   reviewer. A clean pinned commit job must return the exact current `head_sha` receipt instead of
   bare `False`, and a reply journal is replayable only when its recorded head matches that verified
   head; stale journals are ignored.
   More than one reply/review pass may be legitimate when the finding asks only for host evidence.
   Keep every pass bound to the unchanged head and retain NOGO until the reviewer resolves the
   thread. Do not create an empty or unrelated source commit to make the retry look like progress.
   If the remediation changes only PR title/body, re-read those fields immediately before validation and capture the live head in the same response. Reject the context if that head differs from the verified review head; include the title/body only as nonce-fenced untrusted data. This lets validation recognize a metadata-only correction without treating stale pre-remediation text as evidence, while the no-commit warning and reviewer-owned disposition remain unchanged.

   Treat an explicit request to drop, remove, or split unrelated/out-of-scope paths as a
   publication-safety boundary, not advisory prose. Host-normalize it to blocking severity
   before filtering, require one complete non-empty manifest of safe repository-relative paths,
   and require the finding's own path to be present in that manifest. Give an adopted-PR address
   session the linked issue context and the verified current diff, with the manifest in a
   nonce-fenced data block. Immediately before commit/push, compare every declared path at the
   post-address `HEAD` with the immutable base captured by the review checkout barrier, using
   literal Git pathspecs. Missing/malformed metadata, unsafe paths, unavailable base proof, or
   any remaining diff must stop publication and remain local-only.

5. Record the completed loop decision with one loop-owned state marker such as `state:implementation-go`, but only after a fresh authorization read proves all three conditions: PR state is `OPEN`, the response explicitly includes `autoMergeRequest` with value `null`, and the live head equals the reviewed head. A missing auto-merge field is partial data, not proof that the request is absent. Verify the exclusive label state by a post-write readback.

   Apply the fresh `OPEN`/explicitly-unarmed guard to every state-changing label path, including exhaustion and skip paths, but do **not** require an old reviewed head to write a no-go/recovery result. A head drift revokes approval and routes to review precisely so the system may record that safe negative outcome.

   `merge_wait` may consume the label only with an in-memory reviewed-head proof. On restart, refresh, checkout mismatch, or head drift, clear the proof and route back to PR review. After repository merge requirements pass, conditionally squash-merge only if the live head still equals that proof. It must not require a workflow artifact, lease, status context, or external proof document for review authorization, and it must never arm native auto-merge.

6. Keep the reviewed head proof only in active-run memory and clear it on refresh, restart, failure, checkout mismatch, or head drift. Discard other review-local state after the label's post-write current-head confirmation and before transition to `merge_wait`. Use a fixed allowlist of ordinary issue/implementation context, the cleanup worktree path, and the process-local handoff mutex. A denylist cannot anticipate aliases; a dynamic ingress list can preserve a forged or stale proof after a retry.

7. Enforce the requirements-context invariant at `merge_wait.on_enter`, not only at strict review. An unlinked direct PR may have an externally retained GO label, and a stage-routing regression can otherwise bypass the strict-stage orphan check. Before recovery or label consumption, return a terminal blocked result for the orphaned item. Do not defer, disable, adopt, create, or poll auto-merge as cleanup.

8. Treat the strict-review guard as a handoff mutex, not merely a strict-stage mutex. Keep it held after strict review advances to merge-wait. Preserve ownership through fail-back/retry to strict review; release idempotently on terminal finish, shutdown parking, or exception handling. The continuation is a SHA-conditional normal squash merge of the reviewed head, never a native auto-merge arm.

9. Keep the boundary mechanically enforceable. Delete CI workflows and automatic tasks that trigger from review or implementation-go solely to produce authorization proof. Remove their references from active documentation, agent directions, prompt contracts, and tests.

10. Cover direct PR discovery as well as issue-driven discovery. First distinguish a PR with a valid closing requirement from an orphan: only the former may reach strict review. For that valid PR, if the strict stage needs issue/comment context, pass the PR number as its work-item context rather than `None`. Passing `None` converts a valid PR into a terminal strict-review failure. If direct PRs deliberately remain issue-less, they must stop at admission/merge-wait under step 7; never treat a label alone, the `--prs` selector, or reviewer-model configuration as enough to compensate for missing requirements context.

11. Preserve ADR history. Do not rewrite accepted historical decisions just to erase obsolete policy. Add a new superseding ADR and update the ADR index so active readers find the current contract while audits retain the original record.

12. Validate the source-only behavior locally: resolve the PR identity and exact head, inspect the source diff and active contracts, run targeted stage/documentation tests, and run `git diff --check`. Tests must cover (a) a moving head revokes review context, (b) a dirty or mismatched checkout never dispatches review, (c) every advancing label path blocks a populated or partial auto-merge state, (d) absent or drifted reviewed-head proof routes to review, and (e) no queue stage calls an auto-merge mutator. State clearly that this is not CI evidence.

13. Short-circuit downstream reruns on terminal PR state. If a later workflow or review pass reruns after the PR has merged, fetch PR `state` first and exit 0 when it is not `OPEN`. GitHub clears `autoMergeRequest` on merged PRs, so a null arm is expected and not a blocker.

14. Audit a completed run from live GitHub events rather than from summary prose alone. Match the
    authorizing review's `commit_id` to the final PR head, especially when earlier reviews target
    superseded revisions. Confirm the loop-owned GO label was applied after that matching review,
    the incompatible NOGO label was removed, required checks completed before merge, and the merge
    event followed. Treat review state, an empty review body, a grade, or `LGTM` as informational;
    only the label records the loop decision, and only the merge event proves terminal completion.
    A GO label may legitimately precede slow required checks: that timing demonstrates CI is not
    review authorization, while `merge_wait` still waits for the repository's merge requirements.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Put strict-review proof in CI/CD | A required workflow generated proof artifacts and gated progress. | The automation loop did not control the CI loop, so it could neither make progress nor make a trustworthy decision from that external state. | The component that owns the review decision must execute and persist it; make strict source review an in-loop CI-free operation. |
| Restart from external proof data | `merge_wait` depended on workflow artifacts, leases, and status records. | Those records were external coupling, could be absent or stale after restart. A label alone also cannot prove which SHA was reviewed. | Restart from loop-owned label and live PR state, but route to PR review when the active-run reviewed-head proof is absent. |
| Preserve strict-review ingress fields dynamically | A review pass snapshotted its ingress payload keys and kept those keys after GO. | An unknown alias or forged snapshot entry could preserve review evidence; after a NOGO retry, the stale snapshot could drop fresh implementation context. | At the GO boundary, retain a small fixed set of non-authorizing context keys instead of trying to classify or remember review fields. |
| Treat a repository-wide PR as an issue-less strict review | Direct PR discovery constructed a work item with `issue=None`. | The strict stage requires issue/comment context and rejected the work item as terminal. | For direct PR review, use the PR number as the work-item context unless the design supplies an equivalent explicit context. |
| Retry an orphaned direct PR with a different reviewer setting | Launched `hephaestus-automation-loop --prs 2357 --reviewer-model sol --reviewer-reasoning-effort medium` without first proving an exact closing requirement. | The admission gate found no standalone `Closes #N` line, completed with `agent jobs: 0`, and no reviewer model was invoked; `Addresses #2138 and #2223` was not usable requirements context. | Preflight direct PR metadata before dispatch. `--prs` and model flags select work only after the deterministic requirements-context invariant passes. |
| Trust strict review as the only orphan check | An unlinked direct PR with a stale `state:implementation-go` label was routed around strict review and into merge-wait. | The strict-stage check never ran on that path, so merge-wait could otherwise consume an authorization without requirements context. | Repeat the invariant at the irreversible state boundary: terminally block before merge-wait consumes labels; do not perform auto-merge cleanup. |
| Release strict guard at the stage transition | The guard was released as soon as strict review routed to merge-wait. | A competing strict reviewer could enter while the first item was between review approval and final exact-head verification. | Retain ownership through the reviewed-head-safe continuation; all finish/park/exception paths remain idempotent releases. |
| Treat `autoMergeRequest` as a post-merge signal | A rerun checked `autoMergeRequest` after the PR had already merged. | GitHub clears `autoMergeRequest` on merged PRs, so the rerun misread a terminal PR as still pending. | Post-merge consumers must check `state` and short-circuit on non-`OPEN` instead of treating `autoMergeRequest` as durable. |
| Review a PR without binding its head | The reviewer saw a remotely fetched diff while a push could occur, and the later label write reused the result. | Approval of one revision was treated as approval of a different revision; even a head-before/head-after check permits an ABA change that restores the original head while retaining an intermediate diff. | Snapshot metadata and head, verify a clean checkout at that SHA in a Git job, derive the diff locally from the verified base/head pair, and clear the proof on every drift or refresh. |
| Synchronize the disposable review checkout before the checkout barrier | Creation synced the worktree to the PR branch, then the exact-head barrier synchronized it again. | The first fetch happened before the immutable expected-head proof existed; the second was still required, so the successful run did redundant network work and ambiguous log lines. | Bootstrap only from local `HEAD`; capture the GitHub context and perform exactly one fetch-and-bind in the exact-head checkout barrier. |
| Force-rebase an already-current writer before review | Review preparation ran `git rebase --force-rebase` and a lease push even when the current base was already an ancestor of `HEAD`. | Every pass changed commit SHAs, invalidated head-bound receipts, reran pre-push work, and prevented convergence. | Preserve the head on the no-op path, verify the exact live remote ref, and reserve signed rebase plus conditional publication for genuinely behind branches. |
| Add the review worktree directly at a remote or fork branch | The branch was not guaranteed to exist locally when the detached worktree was created. | Git logged a caught exit-128 missing-ref error and fell back to an auto-detected base branch, even though the later barrier fetched the real PR head. | Use local `HEAD` solely as scratch state. Do not resolve a PR branch until the one barrier that fetches and proves the captured head. |
| Treat a missing `autoMergeRequest` field as null | A partial PR response defaulted absent data to unarmed. | A failed or narrowed fetch became false safety evidence for a label mutation. | Require the field to be present with value `null`; otherwise fail closed. |
| Try to disable a request that looked queue-owned | The design compared a later request's visible fields to an earlier queue arm before disabling it. | GitHub has no conditional disable mutation or persisted client nonce; another actor can replace an indistinguishable request between reads. | Never enable, defer, disable, adopt, create, or poll auto-merge from a shared queue; stand down on every populated request. |
| Reject a successful no-commit remediation reply | The implementation path treated the absence of a commit as proof that the remediation failed. | Evidence-only replies never reached the reviewer, so the reviewer could not evaluate the response or leave an evidence-specific thread disposition. | Publish a verified-head-bound reply with the explicit no-commit warning and keep reviewer-owned disposition intact. |
| Manufacture a commit for an evidence-only retry | A missing host-validation receipt was treated as though review could advance only after the PR head changed. | The requested correction was evidence in a review reply, so an artificial source change would invalidate existing head-bound receipts without addressing the finding. | Keep NOGO, post the evidence against the verified unchanged head, and permit another exact-head review; advance only after the thread resolves. |
| Validate a metadata-only remediation with the original PR snapshot | PR #2619 changed only PR title/body after the first review, but reply validation lacked the corrected live metadata. | The live correction could not be observed, so the loop could repeat NOGO even though the PR metadata was fixed. | Re-read title/body immediately before validation, bind that snapshot to the verified head, fence it, and retain no-commit replies as reviewable evidence. |
| Use tracked-source absence as proof of a PR-body correction | PR #2595 replies established that the unsupported pytest count was absent from checked-in source, but reviewer validation still found no evidence that the PR-level numeric assertion had been removed. | A source checkout cannot prove the live GitHub title/body metadata was corrected; the handoff remained unresolved despite requiring no source edit. | Re-read live PR title/body immediately before validation, bind the metadata snapshot to the verified head, and treat the correction as exact-head no-commit evidence. |
| Replay a reply journal after the PR head changed | A prior head's handoff journal was treated as current because its text still looked complete. | The reply could describe a superseded revision and bypass the current-head review boundary. | Bind journals to `head_sha` and ignore any journal that does not match the verified current head. |
| Treat a docstring-only change as scanner remediation | PR #2598's first implementation head changed the topology-test docstring but did not address the retired scanner inputs or add a regression for them. | The review correctly returned NOGO: the issue's scanner findings would remain unchanged and the pre-existing assertions could still pass. | For scanner-backed issues, require a current-head change that addresses the reported input plus a regression that fails if the input returns before applying GO. |
| Validate only consumer-traversed scanner fields | PR #2660's first review validated `dependencies` but not the producer-required top-level `fixes` list, so missing or non-list `fixes` could still reach a clean verdict. | Consumer-shaped validation accepted incomplete scanner evidence even though the producer contract required another top-level collection. | Validate the complete producer result shape, including fields not traversed by classification, and cover missing/non-list cases in every output mode before GO. |
| Rewrite accepted ADRs to remove obsolete instructions | Historical ADR text was modified in place. | It obscured the decision record and broke the repository's ADR immutability convention. | Preserve accepted ADRs verbatim; add a superseding ADR and make the index point to the active policy. |
| Re-run review against unchanged unresolved threads | PR #2345 repeatedly re-entered review while seven automation-created threads remained unresolved. | The loop could not prove that automated reply/resolution would preserve human activity, so each run correctly stood down with NOGO and could not advance. | Treat unchanged unresolved-thread state as a fail-closed wait condition; obtain concrete dispositions and resolutions, then run a fresh exact-head review. |
| Treat an automated review comment as authorization | A completed run's `A`, `LGTM`, or decision-shaped review prose was used as the apparent GO signal. | Review prose is audit evidence and can exist without the fresh live-state guards required for a label transition. | Audit the exact-head review, GO-label event, and merge event separately; the comment never substitutes for the loop-owned label. |
| Treat GitHub review/comment presence as the review audit | PR #2616's inline loop review left `reviews=[]` and no issue comments even though the state-label path completed successfully. | GitHub's review/comment APIs are not the durable authorization surface for every loop mode; requiring an object that the mode does not publish creates a false failure. | Record the empty review/comment surface and audit the exact head, exclusive GO/NOGO label transition, required-check timing, and merge event instead. |
| Let an immutable receipt run only a synthesized test file | PR #2622 initially proved the generated pytest specs but not the emitted conftest-directory command; its claimed `607 passed` reproduction was therefore unproved. | A passing helper/spec test does not establish that the host verifier executed the exact directory target at the reviewed head. | Add a regression that executes the emitted directory target through the real worker path and asserts the exact-head immutable receipt before GO. |
| Let an address agent interpret “drop unrelated files” without a host-enforced manifest | Scope-control prose was passed to remediation like an ordinary finding. | The agent could omit a path, retain an out-of-scope change, or publish from stale task context while still self-reporting success. | Normalize scope retractions to blocking, carry a complete validated path manifest plus linked issue/current diff, and compare every path to the reviewed base before push. |

## Results & Parameters

| Item | Result |
|------|--------|
| Decision marker | `state:implementation-go` is the loop-owned authorization only after a review of the exact GitHub head and a fresh mutation guard. |
| Prohibited dependencies | CI checks, workflow runs, artifacts, deployments, external status contexts, and review-proof leases. |
| Review-state handoff | Keep `reviewed_head_sha` only for the active run; clear it on refresh, restart, mismatch, or drift. After label readback, retain only fixed non-authorizing context, cleanup, and the ephemeral handoff mutex. |
| Direct-PR correction | Use the PR number as strict-review work-item context rather than `None`. |
| Direct-PR admission | Before launching reviewer work, require one exact standalone `Closes #N` line and a usable linked requirement. `Addresses #N` is not a substitute; failed admission means zero agent jobs by design. |
| Label mutation guard | Every mutation needs fresh `OPEN` plus explicitly present `autoMergeRequest: null`; an approving/GO label additionally needs live head equal to `reviewed_head_sha`. A post-write label read verifies exclusivity. |
| Thread-completeness gate | PR #2345 retained NOGO while review threads were unresolved. After all 12 threads were resolved, a fresh review of head `c6c59048` returned GO; `state:implementation-go` was added, `state:implementation-no-go` was removed, and the PR merged 12 seconds later. |
| External auto-merge | A populated request is unprovably externally owned. Queue stages stand down and never enable, defer, disable, adopt, create, or poll auto-merge. |
| Defense in depth | `merge_wait.on_enter` rejects `issue=None` before consuming labels and routes absent/drifted head proof back to PR review. |
| Guard lifetime | Strict-review ownership covers the strict-to-merge-wait handoff through a terminal or SHA-conditional normal squash merge; no native auto-merge arm continuation exists. |
| Merge mutation | Revalidate the process-local reviewed-head proof and conditionally squash-merge that exact SHA. Head drift routes back to review; it never inherits authorization from a prior GO label. |
| Post-merge terminality | PR #2306 / issue #2177 merged at `2026-07-21T01:53:35Z` with `state=MERGED`; `autoMergeRequest` is `null` and `mergeStateStatus` was `UNKNOWN` after merge. Downstream reruns must key off PR state and treat terminal PRs as complete. |
| Review evidence boundary | PR #2347's reviewer passed `diff --check`, Ruff, formatting, mypy, and direct probes but could not rerun pytest or artifact builds in its sandbox. It reported a B/GO without overclaiming those tests; source review authorized the label, while the independent required-checks gate completed before merge. |
| PR #2643 / issue #2366 audit | The PR body said the automation pipeline did not run tests, but that statement was separate from the loop's review authorization and GitHub's required-check merge contract. The final head was `6cc7d690`; no GitHub review/comment object existed, `state:implementation-go` was recorded at `22:53:34Z`, all required checks including the gate completed by `23:00:42Z`, and conditional merge `980c340e` followed at `23:01:38Z` with native auto-merge null. |
| Read-only reviewer checkout | Create a detached scratch checkout from local `HEAD`; it has no remote branch binding and performs no remote sync. |
| Checkout barrier | After capturing GitHub PR context, perform the sole remote fetch, bind to the expected head, prove clean `HEAD == expected`, and derive the local base/head diff before reviewer dispatch. |
| No-op writer preparation | If `<remote>/<base>` is already an ancestor of `HEAD`, require local `HEAD == expected_remote_sha` and `git ls-remote --refs <remote> refs/heads/<branch>` to return that same SHA. Return an unchanged-head receipt and perform no rebase or push; remote drift fails closed. |
| Scope-retraction publication gate | Explicit remove/drop/split plus unrelated/out-of-scope wording requires a complete safe path manifest. The host normalizes the finding to blocking, fences the manifest as data, and refuses commit/push unless every declared path matches the reviewed base. |
| Complete producer-shape validation | For scanner-backed remediation, validate the full producer result contract—not only fields the consumer currently traverses. Missing or non-list required fields must fail closed in both human and JSON modes. |
| Local validation example | `uv run pytest` over pipeline stage/coordinator and active-documentation/ADR tests: 85 passed; `git diff --check` passed. |
| Historical-policy migration | Preserve accepted ADRs; record the new label-only rule in a superseding ADR and its index entry. |
| Completed-run audit | PR #2506 review targeted head `92f790df` at `17:49:49Z`; `state:implementation-go` was added at `17:49:54Z`; merge commit `784fc58b` followed at `17:50:06Z`. The required-checks gate had already succeeded at `17:45:01Z`, independently of review authorization. |
| Multi-cycle completed-run audit | PR #2570 had reviews on superseded heads `93706c99` and `8465ee72`. The final review targeted the live head `219ec8ce` at `15:56:12Z`; GO was added at `15:56:44Z`, NOGO removed at `15:56:46Z`, the required-checks gate succeeded at `15:56:56Z`, and merge followed at `15:57:07Z`. |
| Evidence-only remediation | Successful no-commit replies carry `[auto-msg] reply has no corresponding commit, review thoroughly`, are posted against the verified current head, and remain open for reviewer-owned accept/reject/resolve disposition. |
| Fresh metadata for no-commit replies | Re-read live PR title/body against the current head immediately before validation; reject head drift, nonce-fence all GitHub text, and keep the no-commit warning plus reviewer-owned disposition. |
| PR #2595 / issue #2137 audit | Initial source findings were corrected, then validation isolated an unsupported numeric pytest claim in PR metadata. Repeated no-commit replies remained bound to the final head `d68e1d438f51ff0f903b1ea77576d603d28ec682`; GO was added at `16:35:56Z`, NOGO was removed at `16:35:58Z`, the required-checks gate completed at `16:41:02Z`, and `merge_wait` conditionally merged `da620c2f5d8b3b02857b13c549aca31307d333bd` at `16:41:54Z` with `autoMergeRequest` null. |
| PR #2635 / issue #2632 audit | The migration-only head `0bfa3d4a8b313215cf04a69ecb49ae7a69da4b92` stayed unchanged through two no-commit evidence replies and three head-bound `COMMENTED` reviews. Required checks completed at `02:41:00Z`; the final review followed at `02:42:46Z`; GO replaced NOGO at `02:44:00Z` / `02:44:02Z`; and `merge_wait` conditionally merged `9b3450effd6ae1ef276180c754c3fc135bd93b73` at `02:44:12Z` with `autoMergeRequest` null. |
| Exact no-push receipt | Clean pinned commit jobs release unused reservations, read verified `HEAD`, and return `{"pushed": false, "head_sha": <sha>}`; bare `False` is insufficient for current-head binding. |
| Reply journal freshness | Replay only when the journal's `head_sha` equals the verified current PR head; ignore stale-head journals. |
| PR #2592 / issue #2591 audit | Final review record targeted `051be9de` at `00:39:57Z`; GO replaced NOGO at `00:40:47Z`; required checks completed before merge; merge commit `04f268dd` landed at `00:50:56Z`. Earlier review records on superseded heads were historical only. |
| PR #2594 / issue #2149 audit | Evidence-only handoffs were accepted only on their bound heads (`e3251313` then `ccd15161`); the final review matched `ccd15161` at `01:19:29Z`, GO replaced NOGO at `01:23:40Z`, slow unit and required-check gates finished at `01:29:29Z` and `01:29:40Z`, and merge commit `3fd39fc3` landed at `01:30:39Z`. CI completed the merge contract but did not authorize review. |
| PR #2598 / issue #2255 audit | The first review flagged the docstring-only head and applied `state:implementation-no-go` at `01:55:37Z`. The follow-up head `c565b6f7` added `RETIRED_PLUGIN_SCANNER_INPUTS` regression coverage; the matching review at `02:08:24Z` was followed by `state:implementation-go` at `02:09:43Z`, NOGO removal two seconds later, and merge commit `d065fff2` at `02:21:10Z`. Required checks passed independently; `autoMergeRequest` remained null. |
| PR #2616 / issue #2615 audit | The inline review path had no GitHub review or issue-comment object. GitHub recorded NOGO at `13:05:12Z`, GO at `13:14:12Z`, NOGO removal at `13:14:15Z`, required-checks completion at `13:14:26Z`, and merge commit `5dbfd3e6` at `13:14:35Z` for final head `36322151`; `autoMergeRequest` was null. |
| PR #2622 / issue #2621 audit | The first review on superseded head `f69726b0` found nested-directory duplication, lost nonhermetic exclusions, and an unproved immutable directory receipt; the loop recorded NOGO at `14:57:29Z`. Replies were tied to the remediation commits, the final review matched `e418b3f0`, GO replaced NOGO, required checks completed at `15:27:43Z`, and `merge_wait` conditionally merged `022e2ff2` at `15:28:21Z`; `autoMergeRequest` was null. Final validation reported 7,165 passed, 11 skipped, 5 deselected, 84.74% coverage, and a 607-passed exact immutable directory receipt. |
| PR #2665 / issue #2383 audit | The direct implementation review emitted no GitHub review or issue-comment object. Treat the generated `Testing: Not run by the automation pipeline` note as informational; audit the loop-owned `state:implementation-go` marker, the exact final head `f2201c972eef9c1e9c4e61d5637d51d635a02b52`, live required-check completion, and the `merge_wait` conditional merge `1b7bfb16e2177f8988baecca65dd25fc5878bc9a`. The label authorizes review progression; required checks complete the repository merge contract. |
| PR #2689 / issue #2473 audit | The direct implementation review emitted no GitHub review or issue/comment object. Audit the exact final head `289e14c0a5955812650c9d876d48ba696102c604`, the loop-owned `state:implementation-go` event at `23:17:26Z`, later `pr-policy`/unit/integration/required-check success, and `merge_wait`'s conditional merge `70f5a8fe03c2cd6ad17c7a4e58803bbec69fa502` at `23:43:11Z`; native auto-merge remained unset. |
| PR #2690 / issue #2476 audit | The direct implementation review emitted no GitHub review or issue/comment object. Audit the exact final head `6cdb34ee951ab295fc22cfad23dd26dd7a540111`, the loop-owned `state:implementation-go` event at `23:46:40Z`, the required-checks gate success at `23:51:51Z`, and `merge_wait`'s conditional merge `f1e8abfd9f094671a5e31192f69ae3954d4f3b41` at `23:52:37Z`; native auto-merge remained unset. |

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #2423 reviewed-head interlock | Local design evidence established the exact-head review proof and that auto-merge disable has no conditional ownership token. PR #2345 subsequently verified the production continuation: a conditional normal squash merge of the reviewed head. |
| ProjectHephaestus | PR #2280 / issues #2053 and #2276 | CI-free source review and loop-owned `state:implementation-go` authorization. The direct repository-wide PR route now supplies PR context to strict review. Local swarm review then found that dynamic review-payload preservation could retain an aliased proof or survive a NOGO retry; a fixed allowlist removes those fields only after the label's current-head readback. Local verification only; no CI/CD state was queried. |
| ProjectHephaestus | PR #2306 / issue #2177 | Docs PR that reached merged state through the normal review-to-merge path: review GO, loop-owned `state:implementation-go`, and merge_wait. Post-merge `gh pr view` showed `state=MERGED` with `autoMergeRequest=null`, confirming reruns must short-circuit on terminal PR state. |
| ProjectHephaestus | PR #2347 / issue #2283 | The review posted B/GO at `ecba01d9`, explicitly recorded that its sandbox could not rerun pytest or artifact builds, and applied `state:implementation-go` at `2026-07-21T04:35:08Z`. `merge_wait` completed the merge at `2026-07-21T04:44:01Z` as `fde855ad`, after the independent required-checks gate succeeded. |
| ProjectHephaestus | PR #2357 | A scoped direct-PR run selected Sol at medium reasoning effort, but the deterministic admission gate found no exact `Closes #N` link and completed with `agent jobs: 0`. The independent strict review could still inspect the source, but the in-loop reviewer was correctly not invoked. Verified locally; no CI conclusion follows from this admission result. |
| ProjectHephaestus | PR #2345 / issue #2233 | Verified-ci thread-completeness and merge path. The loop repeatedly stood down with NOGO while automation-created review threads were unresolved. After the implementation preserved accepted ADR-0005, added superseding ADR-0017, and resolved all 12 threads, the final review bound to head `c6c59048` returned A/GO. GitHub recorded GO-label addition at `16:58:06Z`, NOGO-label removal at `16:58:08Z`, and merge as `7b8dc730` at `16:58:20Z`; all required checks passed and `autoMergeRequest` remained null. |
| ProjectHephaestus | PR #2506 / issue #2505 | Verified-ci compact happy path. The informational A/LGTM review was bound to head `92f790df`; the loop added `state:implementation-go` five seconds later and merged as `784fc58b` after another 12 seconds. Required checks were independently green before review. |
| ProjectHephaestus | PR #2510 / issue #2509 | Verified-ci scope-retraction path. Adopted-PR address sessions now receive linked issue context and the verified current diff; explicit scope-control findings require a host-validated complete path manifest and a pre-push comparison to the reviewed base. The informational B review targeted `cacab13e`; GO was labeled at `21:00:10Z`, and `d5cad541` merged that head 12 seconds later with required checks green. |
| ProjectHephaestus | PR #2570 / issue #2385 | Verified-ci multi-cycle review and merge path. Reviews on `93706c99` and `8465ee72` remained historical only. The final review matched live head `219ec8ce`; GO replaced NOGO, the required-checks gate then succeeded, and the PR merged 55 seconds after the final review. |
| ProjectHephaestus | PR #2570 completed-run audit and read-only checkout correction | The completed log showed a caught missing-branch probe plus two review-worktree synchronizations per review round. The proposed corrective implementation creates a detached `HEAD` scratch checkout and defers the sole remote fetch-and-bind to the exact-head barrier. Three focused regressions, 300 relevant tests, the full 6,690-test unit suite (84.60% coverage), mypy, Ruff, and pre-commit passed locally. |
| ProjectHephaestus | PR #2592 / issue #2591 | Verified-ci convergence path. Review records on superseded heads were not reused; the final review matched `051be9de`, GO replaced NOGO only after the current-head checks, required checks completed, and merge commit `04f268dd` followed. The issue's live validation also showed a no-commit remediation reply reaching review with the warning intact and the thread left open for evidence feedback. |
| ProjectHephaestus | PR #2594 / issue #2149 | Verified-ci evidence-only review and merge path. The no-commit handoff on `e3251313` was not treated as implementation failure; a later handoff and final review bound to `ccd15161`. GO replaced NOGO before the slow unit/required-check gates finished, then `merge_wait` waited and conditionally merged the reviewed head as `3fd39fc3`; `autoMergeRequest` was null. |
| ProjectHephaestus | PR #2598 / issue #2255 | Verified-ci scanner-remediation review path. The first head correctly remained NOGO because it changed only a docstring. A new head added a regression that rejects retired plugin-scanner inputs; exact-head review then authorized GO, the loop replaced NOGO, and `merge_wait` conditionally merged `d065fff2` after required checks. |
| ProjectHephaestus | PR #2616 / issue #2615 | Verified-ci inline-review path. No GitHub review/comment object was emitted; the durable audit was the exact final head, NOGO→GO label replacement, required-check completion, and merge event. The GO label preceded the final required-check gate, so CI remained merge-contract context rather than review authorization. |
| ProjectHephaestus | PR #2622 / issue #2621 | Verified-ci remediation path. The initial exact-head review remained NOGO until the implementation corrected conftest-directory target selection, shallowest-directory deduplication, nonhermetic exclusions, and the immutable WorkerPool receipt regression. The final head `e418b3f0` then passed the label and required-check gates before conditional merge commit `022e2ff2`. |
| ProjectHephaestus | PR #2619 / issue #2618 | Verified-ci metadata-only remediation path. The final review matched `a24ccf2193f560b407f13049f306acfe1947af64`; GO replaced NOGO, required checks completed independently, and `merge_wait` conditionally merged `4631d91cc0a4f981f050f47bb1af1f20f4a4e1ab` with `autoMergeRequest` null. |
| ProjectHephaestus | PR #2631 / issue #2630 | Verified-ci review-convergence path. The already-current writer preserved head `692bc1fb6e4a762ffaf672c12c5de1c4b0292a5c` without rebase or push and checked the exact remote ref for concurrent movement. The final review matched that head at `00:05:51Z`; GO replaced NOGO at `00:07:23Z` / `00:07:25Z`; the required-checks gate completed on the same head at `00:15:52Z`; and conditional squash merge `baa59341ae2d6ad0bbfc0e919fcd47cc1d57a33b` followed at `00:16:31Z` with native auto-merge null. |
| ProjectHephaestus | PR #2635 / issue #2632 | Verified-ci evidence-only retry path. The review thread requested host receipts rather than source changes, so the loop kept the PR at head `0bfa3d4a8b313215cf04a69ecb49ae7a69da4b92` through two no-commit replies and three reviews. After the thread resolved, exclusive GO replacement and conditional squash merge completed on that exact head; native auto-merge remained null. |
| ProjectHephaestus | PR #2643 / issue #2366 | Verified-ci direct implementation happy path. The inline review left GitHub's review/comment APIs empty, so the audit used the exact head `6cc7d690`, the loop-owned GO label, the later required-checks gate, and the conditional merge commit `980c340e`; native auto-merge was null. |
| ProjectHephaestus | PR #2665 / issue #2383 | Verified-ci direct implementation and merge audit. GitHub exposed no review/comment object; the loop recorded `state:implementation-go` at `08:27:00Z`, required checks completed at `08:34:35Z`, and `merge_wait` conditionally merged final head `f2201c97` as `1b7bfb16` at `08:35:06Z` with native auto-merge unset. The PR body's testing note was not used as CI evidence. |
| ProjectHephaestus | PR #2660 / issue #2379 | Verified-ci scanner-evidence review path. The initial exact-head review applied NOGO for incomplete top-level validation; the implementation replied on final head `1950319a` with `fixes` shape regressions in human and JSON modes. The final review matched that head, GO replaced NOGO, required checks completed afterward, and merge_wait conditionally merged `911b4982` with native auto-merge unset. |
| ProjectHephaestus | PR #2689 / issue #2473 | Verified-ci direct implementation review and merge audit. No GitHub review/comment object was emitted; the loop-owned GO label preceded the later required-check gate, and merge_wait conditionally merged exact head `289e14c0` as `70f5a8fe` with native auto-merge unset. The PR body's testing note was not used as review or CI evidence. |
| ProjectHephaestus | PR #2690 / issue #2476 | Verified-ci direct implementation review and merge audit. No GitHub review/comment object was emitted; the loop-owned GO label preceded the required-check gate, and merge_wait conditionally merged exact head `6cdb34ee` as `f1e8abfd` with native auto-merge unset. |
