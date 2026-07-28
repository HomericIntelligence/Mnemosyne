---
name: automation-review-authorization-ci-boundary
description: "Keep automation-loop source-review authorization independent of CI/CD, bind it to an exact PR head, and conditionally merge only that reviewed head. Use when: (1) review authorization is mistakenly delegated to CI, (2) a review can race with a changed head or dirty checkout, (3) unresolved review threads block advancement, (4) remediation must retract out-of-scope paths before publication, (5) a label advances implementation or merge state, (6) an external actor may own auto-merge, (7) a downstream rerun sees a merged PR, or (8) a completed run needs a live event-order audit."
category: architecture
date: 2026-07-28
version: "3.2.0"
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
  - checkout-verification
  - auto-merge-ownership
  - fail-closed
  - review-thread-completeness
  - github-event-audit
  - scope-retraction
  - pre-publication-guard
---

# Automation Review Authorization: CI Boundary

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-28 |
| **Objective** | Keep a code-automation loop's strict source-review decision inside that loop rather than delegating its authorization to CI/CD, bind the decision to the exact GitHub head SHA, and prevent the queue from mutating externally owned auto-merge. |
| **Outcome** | ProjectHephaestus PR #2345 demonstrated the active fail-closed path. PR #2506 supplied a compact happy-path audit. PR #2510 added a pre-publication scope-retraction guard so remediation cannot push declared out-of-scope paths before the exact-head GO/merge continuation. |
| **Verification** | verified-ci on ProjectHephaestus PRs #2345, #2506, and #2510. For #2510, the review targeted head `cacab13e`, `state:implementation-go` followed six seconds later, and merge commit `d5cad541` landed 12 seconds after the label with required checks green. |

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
- A label write would advance the pipeline without fresh proof that the PR is `OPEN` and explicitly unarmed, or an approving/GO label would advance without also proving the reviewed head still matches.
- The queue sees `autoMergeRequest` populated and is tempted to defer, disable, adopt, or replace it. GitHub does not expose a conditional disable operation that can prove ownership of that request.
- Repeated review runs encounter unresolved automation-created threads and must distinguish a safe stand-down from authorization to advance.
- A review finding says to drop, remove, or split unrelated/out-of-scope files, and the address agent must not publish a partial or malformed retraction.
- You need to audit a completed automation-loop run from durable GitHub facts without treating review prose or CI results as authorization.

## Verified Workflow

### Quick Reference

```text
automation loop owns source-review authorization
  1. snapshot GitHub PR metadata and its head; reject it if the head moves
  2. verify a clean checkout at that exact head in a dedicated Git job, then derive its diff locally from the verified base/head pair
  3. run the strict PR review in the loop (CI-free) against that metadata and derived diff
  4. stand down while any relevant review thread remains unresolved; rerun only after thread state or head changes
  5. for a scope retraction, require a complete safe path manifest and compare every path to the reviewed base before push
  6. before every state-changing label, re-read OPEN + explicit autoMergeRequest:null
  7. require the exact reviewed head only for an approving/GO label; drift revokes proof and re-reviews
  8. merge_wait revalidates the proof and conditionally squash-merges only that exact head; it never mutates native auto-merge

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

   Run strict PR review as an in-loop, CI-free operation against that metadata and checkout-derived diff. Require an explicit GO result before transition; a missing, ambiguous, or NO-GO result must not apply the approval label.

   For direct `--prs` operation, first verify the requirements context deterministically. `--prs`
   identifies the PR but does not waive the exact standalone `Closes #N` contract or synthesize
   acceptance criteria from prose such as `Addresses #N`. When the preflight fails, the correct
   result is a fail-closed terminal record with zero reviewer jobs; changing `--reviewer-model` or
   its reasoning effort must not bypass that result. This is admission control, not a duplicate
   LLM policy check and not a CI dependency.

3. Report review evidence precisely. A reviewer may issue GO from sufficient source and local evidence even when its sandbox cannot independently rerun every claimed test, but it must name the gap, avoid claiming those tests passed, and grade the evidence accordingly. Do not turn that disclosure into a CI dependency for the loop decision.

4. Require complete review-thread state before approval. If automation-created threads remain unresolved and the loop cannot prove that replying or resolving them preserves human activity, retain NOGO and stand down without arming merge. Repeated runs against the same unresolved state are not progress. Resume with a fresh review only after the threads have concrete dispositions and resolutions or the head changes.

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

14. Audit a completed run from live GitHub events rather than from summary prose alone. Confirm
    that the review record is bound to the expected head, the loop-owned GO label was applied
    after that review, and the merge event followed the label. Treat a review grade or `LGTM`
    comment as informational even when it immediately precedes the label; only the label records
    the loop decision, and only the merge event proves terminal completion.

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
| Treat a missing `autoMergeRequest` field as null | A partial PR response defaulted absent data to unarmed. | A failed or narrowed fetch became false safety evidence for a label mutation. | Require the field to be present with value `null`; otherwise fail closed. |
| Try to disable a request that looked queue-owned | The design compared a later request's visible fields to an earlier queue arm before disabling it. | GitHub has no conditional disable mutation or persisted client nonce; another actor can replace an indistinguishable request between reads. | Never enable, defer, disable, adopt, create, or poll auto-merge from a shared queue; stand down on every populated request. |
| Rewrite accepted ADRs to remove obsolete instructions | Historical ADR text was modified in place. | It obscured the decision record and broke the repository's ADR immutability convention. | Preserve accepted ADRs verbatim; add a superseding ADR and make the index point to the active policy. |
| Re-run review against unchanged unresolved threads | PR #2345 repeatedly re-entered review while seven automation-created threads remained unresolved. | The loop could not prove that automated reply/resolution would preserve human activity, so each run correctly stood down with NOGO and could not advance. | Treat unchanged unresolved-thread state as a fail-closed wait condition; obtain concrete dispositions and resolutions, then run a fresh exact-head review. |
| Treat an automated review comment as authorization | A completed run's `A`, `LGTM`, or decision-shaped review prose was used as the apparent GO signal. | Review prose is audit evidence and can exist without the fresh live-state guards required for a label transition. | Audit the exact-head review, GO-label event, and merge event separately; the comment never substitutes for the loop-owned label. |
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
| Scope-retraction publication gate | Explicit remove/drop/split plus unrelated/out-of-scope wording requires a complete safe path manifest. The host normalizes the finding to blocking, fences the manifest as data, and refuses commit/push unless every declared path matches the reviewed base. |
| Local validation example | `uv run pytest` over pipeline stage/coordinator and active-documentation/ADR tests: 85 passed; `git diff --check` passed. |
| Historical-policy migration | Preserve accepted ADRs; record the new label-only rule in a superseding ADR and its index entry. |
| Completed-run audit | PR #2506 review targeted head `92f790df` at `17:49:49Z`; `state:implementation-go` was added at `17:49:54Z`; merge commit `784fc58b` followed at `17:50:06Z`. The required-checks gate had already succeeded at `17:45:01Z`, independently of review authorization. |

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
