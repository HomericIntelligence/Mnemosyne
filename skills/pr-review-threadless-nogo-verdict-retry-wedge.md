---
name: pr-review-threadless-nogo-verdict-retry-wedge
description: "Prevent threadless PR-review retry wedges by distinguishing missing remediation artifacts from actionable host-verification diagnostics. Use when: (1) a NOGO has no durable review threads, (2) a formatter, test, or validation command failed on an exact PR head, (3) implementation must receive bounded command/output context without fabricating thread replies, (4) real review threads must retain exhaustive reply, journal, and handoff semantics, or (5) a repaired head must pass fresh verification, required CI, review, and exact-head merge gates."
category: ci-cd
date: 2026-08-06
version: "1.1.0"
user-invocable: false
verification: unverified
history: pr-review-threadless-nogo-verdict-retry-wedge.history
tags:
  - pr-review
  - nogo-verdict
  - threadless-nogo
  - durable-finding
  - retry-wedge
  - deterministic-retry
  - artifact-failure-cap
  - fail-back-budget
  - review-loop
  - pipeline
  - queue-based-automation
  - poisoned-item-isolation
  - terminal-stop
  - audit-finding-issues
  - escalate-not-retry
  - synthetic-finding
  - host-verification
  - verification-only-remediation
  - bounded-diagnostic
  - exact-head-merge
  - required-checks
  - reply-lifecycle
  - root-cause-clustering
  - homericintelligence
---

# PR Review Threadless NOGO Verdict Retry Wedge

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-06 |
| **Objective** | Prevent deterministic threadless-review wedges while allowing an actionable host-verification failure to return to implementation without weakening the strict reply lifecycle for real review threads. |
| **Outcome** | The original wedge diagnosis remains verified in CI. A distinct verification-only remediation contract is now documented as a proposed extension: carry a bounded exact-head diagnostic, bypass thread reply state, validate push receipts, then re-enter fresh verification, required CI, review, and exact-head merge admission. |
| **Verification** | unverified for the new host-verification workflow; the original zero-artifact wedge diagnosis remains verified-ci via ProjectHephaestus bug #2079 and PR #2105. |
| **History** | [changelog](./pr-review-threadless-nogo-verdict-retry-wedge.history) |

## When to Use

- A queue-based pipeline `pr_review` stage returns a NOGO verdict but the findings-parser extracts NO durable line-level findings — no review threads, no `file:line` comments — so the implementer has nothing concrete to address.
- The fail-back path re-runs the review deterministically (2 retries + final = 3 attempts), producing the SAME threadless NOGO each time and tripping the artifact-failure cap, failing the item back to implementation.
- Implementation's own fail-back budget (2/2) then also exhausts re-adopting the same PR, and the item reaches a TERMINAL "manual look needed" stop.
- A cluster of terminal stops over a long single-repo loop run all trace to the SAME root cause and correlate with ONE issue class (here, AUDIT-FINDING issues) rather than a global reviewer breakdown.
- You are tempted to (a) react to each recurrence as a fresh bug, (b) kill the loop on the first wedge, or (c) "just let it retry" — when the input is deterministic and cannot change between attempts.
- A host-side formatter, test, or validation command fails on the reviewed head, but no GitHub review thread exists because the failure came from the pipeline rather than a reviewer comment.
- You need to keep real-thread remediation strict while giving threadless verification remediation a raw-prose agent result and no reply journal, snapshot, or handoff lifecycle.
- A repaired head must not merge merely because source review is GO: required checks still have to report success before a conditional exact-head merge.

## Verified Workflow

### Quick Reference

```text
# The wedge condition (distinct case that MUST NOT silently retry):
verdict == NOGO  AND  durable_findings(review_output) == []   # no threads, no file:line

# WRONG: default fail-back retries the identical input
for attempt in (1, 2, final):        # 2 retries + final = 3 attempts
    verdict, findings = run_pr_review(pr)   # deterministic -> same threadless NOGO
    # nothing to address -> artifact-failure cap trips -> fail back to implementation
    # implementation fail-back (2/2) re-adopts same PR -> exhausts -> TERMINAL stop

# RIGHT (verified for the zero-artifact case): treat it as a DISTINCT case
if verdict == NOGO and not durable_findings:
    # (a) surface the raw verdict body as a SYNTHETIC finding, OR
    # (b) classify as a review-ARTIFACT error and ESCALATE to a human
    # Do NOT loop the deterministic fail-back.
```

```text
# Wedge vs normal stop:
normal poisoned-item stop  -> isolated, correct, may spend < full budget
threadless-NOGO wedge      -> DETERMINISTIC: same input -> same NOGO -> ALWAYS burns full budget
```

### Detailed Steps

**1. Recognize the wedge by its determinism, not its symptom.** The terminal "manual look needed" stop looks like any other poisoned-item stop. What makes THIS one a wedge is that the retry is deterministic: same input -> same threadless NOGO -> same exhaustion. Nothing changes between attempts, so the retry budget is spent achieving nothing. A normal poisoned-item stop is isolated and correct (an item that genuinely can't proceed); the wedge is a specific input class that ALWAYS burns the full budget.

**2. Trace to the single root cause before filing.** In a queue-based pipeline, the `pr_review` stage can return a NOGO whose findings-parser yields no durable line-level findings (`_nogo_without_durable_artifact` at `pr_review.py:805`). The implementer then has nothing concrete to address, so the fail-back path re-runs the review deterministically (2 retries + final = 3 attempts). Each attempt produces the same threadless NOGO, tripping the artifact-failure cap and failing the item back to implementation. If implementation's own fail-back budget (2/2) also exhausts re-adopting the same PR, the item reaches the TERMINAL stop.

**3. Cluster recurrences by root cause; count at run_end, don't file per-occurrence.** Over the observed run, 7 issues / 10 terminal stops all traced to `pr_review.py:805`. File ONE bug (#2079) with the aggregate occurrence data, not one per stop. Note the final count at run_end.

**4. Confirm the blast radius is CLASS-scoped, not a global reviewer breakdown.** The wedge correlated specifically with AUDIT-FINDING issues; other issue classes passed review cleanly. ~15-21% of pr_review'd issues hit it (7 issues / 10 terminal stops over a 4.3h single-repo run). This is a targeted input-class failure, not the reviewer being broken everywhere.

**5. Let the loop finish; the wedge is survivable.** Poisoned-item isolation bounded each wedge — the loop always continued to the next issue and stayed net-productive (29 PRs created). The stuck PRs' underlying implementation work was INTACT: each PR's own CI judged it independently, so only the review infra failed and no work was lost. Do NOT abort the loop on the first wedge — that would abandon good, independently-CI-judged work.

**6. Fix the root cause: treat "NOGO + zero durable findings" as a DISTINCT case.** Either (a) surface the raw verdict body as a synthetic finding so the implementer has something concrete to act on, or (b) classify it as a review-artifact error and escalate to a human — rather than looping the deterministic fail-back. The load-bearing principle: **do NOT silently retry an input that cannot change.** Merged via PR #2105.

## Proposed Workflow

> **Warning:** The verification-only extension has not been validated end-to-end. Treat it as a hypothesis until focused tests and CI confirm the complete repair-to-merge path.

### Quick Reference

```text
artifact classification
├─ nonempty remediation_threads
│  └─ strict thread mode: parsed exhaustive replies + snapshots + journal + handoff
├─ empty/missing remediation_threads + valid host_verification_failure
│  └─ verification-only mode: parse=None + raw prose + no reply lifecycle
└─ malformed/ambiguous inputs
   └─ fail closed while retaining remediation context

valid host_verification_failure:
  argv         = nonempty list of nonempty strings
  head_sha     = full commit SHA matching the failed head
  failure_kind = test | validation
  path/error/stdout_tail/stderr_tail = strings bounded by the producer limit
  error        = nonblank

valid commit/push receipt:
  pushed  = boolean
  head_sha = full commit SHA
```

### Detailed Steps

1. **Classify at the implementation-stage boundary.** A nonempty thread list is real-thread remediation. A missing or empty list is verification-only only when paired with a valid host diagnostic. Reject explicit `None`, malformed containers, invalid or oversized diagnostics, and ambiguous empty-thread input.
2. **Validate before prompting.** Reuse the producer's diagnostic-size constant rather than duplicating it. Copy only known fields into the prompt payload, require a full exact head SHA, and accept only the bounded command and output fields needed to reproduce the failure.
3. **Make the prompt and parser contracts mode-specific.** Verification-only mode sends `threads_json="[]"`, fences the host diagnostic, forbids fabricated thread IDs/replies/GitHub actions, uses `parse=None`, and treats successful raw prose as implementation evidence. Real-thread mode retains the structured parser and exhaustive reply validation.
4. **Keep durable thread state out of threadless remediation.** Do not create or consume reply snapshots, journals, reply mappings, or handoffs. Fail closed if nonempty stale thread state is already present; silently deleting it could lose durable review work.
5. **Retain context through failures.** Agent, test, commit, push, malformed receipt, or failed receipt errors must use bounded retry paths without clearing the host diagnostic. Validate `pushed` as a Boolean and `head_sha` as a full SHA before mutating remediation state.
6. **Re-enter the pipeline after a valid receipt.** Clear verification-only state only after a valid receipt. If `pushed=true`, submit the new PR head to fresh review. If `pushed=false`, clear any issue-level no-commit shortcut and run fresh host verification on the unchanged head; do not apply a skip label merely because no thread existed.
7. **Preserve exact-head gates.** A repaired head must pass fresh host verification and source review. A GO readback is not sufficient to merge while a required check is pending: merge readiness must remain blocked, and conditional merge must receive exactly the reviewed repaired SHA only after required checks succeed.
8. **Prove both branches.** Keep existing thread reply/journal tests as the strict-thread oracle. Add a deterministic cross-stage regression covering failed head A, repair head B, pending required check with no merge attempt, required-check success, conditional merge of exactly B, and terminal pass.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Let the loop retry | Default fail-back re-ran the same review 3x (2 retries + final) | Deterministic input -> identical threadless NOGO each attempt -> artifact-failure cap trips -> budget exhausted for nothing | A retry only helps if SOMETHING can change between attempts; a threadless NOGO is invariant. Do not silently retry an input that cannot change. |
| Treat every terminal stop as a new bug | Reacted to each #2079 recurrence as a fresh signal | They were all the SAME root cause (`pr_review.py:805`, `_nogo_without_durable_artifact`) | Cluster by root cause before filing; note the final count at run_end, don't file per-occurrence. |
| Kill the loop on first wedge | Considered aborting the whole run when the wedge first appeared | Would abandon 8 PRs of good, independently-CI-judged work whose implementation was intact | Poisoned-item isolation means a bounded wedge is survivable; let the loop finish and fix the root cause separately. |
| Require a review thread for a host-command failure | Reused the thread-remediation gate for a formatter/test/validation failure produced by the host | The failure has actionable command/output evidence but no legitimate thread ID, so the item fails or wedges before implementation can repair it | Classify by durable artifact, not merely by thread count; host diagnostics need a separate bounded contract. |
| Reuse the thread reply parser with `threads_json=[]` | Asked a threadless implementer for structured reply JSON | An empty thread set has no valid exhaustive mapping, encouraging fabricated IDs or parser failure | Use `parse=None` and raw prose for verification-only work; reserve structured reply parsing for nonempty real threads. |
| Clear all reply state when entering threadless mode | Discarded stale snapshots or handoffs as irrelevant | Nonempty durable thread state may represent real reviewer work and cannot be safely erased | Reject conflicting thread state fail-closed instead of silently discarding it. |
| Advance or merge immediately after a repair | Treated an implementation completion or GO label as enough evidence | The repaired head may not have passed fresh host verification or required CI, and an older review may authorize a different SHA | Re-run verification and review, then wait for required checks before conditionally merging the exact reviewed head. |

## Results & Parameters

### The wedge condition and the two correct dispositions

```text
Condition:  verdict == NOGO  AND  durable_findings == []   (no threads, no file:line comments)
Root cause: hephaestus/automation/pipeline/pr_review.py:805  (_nogo_without_durable_artifact)

WRONG (default): loop the deterministic fail-back
  pr_review fail-back: 2 retries + final = 3 attempts  -> same threadless NOGO each time
  -> trips artifact-failure cap -> fails back to implementation
  implementation fail-back: 2/2 -> re-adopts same PR -> exhausts -> TERMINAL "manual look needed"

RIGHT (fix, PR #2105): treat as a DISTINCT case
  (a) surface raw verdict body as a SYNTHETIC finding (implementer gets something concrete), OR
  (b) classify as a review-ARTIFACT error and ESCALATE to a human
  NEVER silently retry an input that cannot change.
```

### Verification-only state and gate invariants (proposed)

| Boundary | Required invariant |
|----------|--------------------|
| Producer -> implementation | Bounded known diagnostic fields; full exact failed-head SHA; no fabricated thread state |
| Agent job | Empty thread array, verification-only prompt, raw prose result, no structured reply parser |
| Durable reply lifecycle | Used only for nonempty real threads; stale nonempty state is rejected |
| Commit/push | Receipt contains Boolean `pushed` and full `head_sha`; malformed receipts retain remediation context |
| No-commit result | Returns to fresh host verification without issue-level skip disposition |
| Pushed repair | New head receives fresh host verification and source review |
| Merge readiness | Required checks must succeed; pending checks produce retry and no merge attempt |
| Conditional merge | Merges exactly the reviewed repaired head, never an older or newer SHA |

### Deterministic cross-stage acceptance sequence (proposed)

```text
head A formatter failure
  -> bounded host_verification_failure, no review threads
  -> raw implementation-agent completion
  -> configured build/test succeeds
  -> valid pushed receipt for head B
  -> fresh host verification of B succeeds
  -> fresh review authorizes B and GO label is read back
  -> required lint pending: merge readiness BLOCKED, RETRY, zero merge attempts
  -> lint SUCCESS: merge readiness CLEAN
  -> conditional merge(pr, reviewed_sha=B)
  -> FINISH_PASS("merged")
```

### Blast-radius data (4.3h single-repo loop run)

| Metric | Value | Notes |
|--------|-------|-------|
| Terminal stops hitting the wedge | 7 issues / 10 terminal stops | All same root cause (`pr_review.py:805`) |
| Fraction of pr_review'd issues affected | ~15-21% | Class-scoped, NOT a global reviewer breakdown |
| Correlated issue class | AUDIT-FINDING issues | Other issue classes passed review cleanly |
| Net productivity | POSITIVE — 29 PRs created | Poisoned-item isolation bounded each wedge; loop always continued |
| Stuck PRs' underlying work | INTACT | Each PR's own CI judged it independently; only the review infra failed, no work lost |

### Retry budgets involved

| Budget | Value | Behavior on the wedge |
|--------|-------|-----------------------|
| pr_review fail-back | 2 retries + final = 3 attempts | Each attempt deterministically reproduces the threadless NOGO; trips the artifact-failure cap |
| implementation fail-back | 2 / 2 | Re-adopts the same PR; exhausts; reaches TERMINAL "manual look needed" stop |

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Queue-based automation pipeline `pr_review` stage; 4.3h single-repo loop run surfaced 7 issues / 10 terminal stops all tracing to `pr_review.py:805` (`_nogo_without_durable_artifact`), correlated with AUDIT-FINDING issues; loop stayed net-productive (29 PRs) via poisoned-item isolation | Bug #2079 (full occurrence data); root-cause fix merged via PR #2105 |
| ProjectHephaestus | Proposed threadless host-verification remediation design: bounded diagnostic handoff, raw agent result, receipt validation, strict real-thread preservation, and A-to-B required-check/exact-head regression | Unverified design supplied 2026-08-06; implementation and CI validation pending |
