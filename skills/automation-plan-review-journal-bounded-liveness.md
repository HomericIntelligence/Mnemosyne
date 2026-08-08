---
name: automation-plan-review-journal-bounded-liveness
description: "Keep issue-based plan/review loops compact and live. Use when: (1) an issue has canonical plan and review comments, (2) review amendments risk growing the timeline, (3) repeated plans must stop without oscillation, or (4) migration must remove old actor-owned raw reviews and diffs safely."
category: architecture
date: 2026-07-21
version: "2.0.0"
user-invocable: false
verification: verified
tags:
  - automation-loop
  - plan-review
  - canonical-comments
  - bounded-context
  - no-progress
  - liveness
  - state-machine
  - prompt-budget
---

# Automation Plan-Review Journal: Canonical Comments and Liveness

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-08 |
| **Objective** | Keep the linked issue limited to the latest plan and latest plan review while preserving restart safety and terminating repeated no-progress amendments. |
| **Outcome** | ProjectHephaestus replaced append-only public history with two actor-owned canonical comments, bounded hidden plan fingerprints, patch rejection, PR-scoped reply recovery, and a dry-run-first migration for legacy comments. |
| **Verification** | Verified by the ProjectHephaestus #2719 implementation: 7,017 unit tests passed, the focused journal/prompt/migration suites passed, and a live dry-run against issue #2363 identified the expected canonical update and three obsolete actor-owned comments with zero failures. |

## When to Use

- A workflow writes plans and reviews to a GitHub issue.
- Repeated review rounds are making the issue or prompt context grow.
- Only the current plan and current critique are actionable.
- An amendment can repeat the immediately prior plan or oscillate back to an older one.
- Legacy issues contain archived full plans, raw plan diffs, old reviews, skip-reason comments, or reply-recovery records.

## Verified Workflow

### Quick Reference

```text
Linked GitHub issue:
  original issue body and human comments
  latest actor-owned canonical plan
  latest actor-owned canonical plan review

On amendment:
  normalize candidate content
  reject raw patches before publication
  compare against current + bounded prior fingerprints
  if unchanged or repeated: transition to the durable blocked path
  otherwise: replace the two canonical comments in place

Detailed implementation evidence:
  commits and PR-native review threads

Legacy cleanup:
  dry-run all open and closed issues
  mutate only comments GitHub proves belong to the authenticated actor
  fail one malformed issue without deleting its content
```

### Detailed Steps

1. Treat the issue body as the immutable task and mutually exclusive labels as the durable state authority. Comments are current audit/context pointers, not authorization.

2. Keep exactly two automation-owned comments on the linked issue: the latest complete implementation plan and the latest complete plan review. Update those comments in place on every review cycle. Do not append superseded raw plans or reviews.

3. Put a concise cumulative `Changes from Review` section in the current plan. Preserve useful prior bullets and fold new findings into high-level themes. Do not quote raw reviewer output, enumerate line-by-line findings, or include code patches.

4. Reject unified patches before publication. Detect fenced `diff` blocks, `diff --git` headers, and unified hunk headers. A plan describes intended behavior and verification; Git commits remain the source of patch history.

5. Preserve liveness with bounded fingerprints rather than full historical bodies. Normalize away generated markers and revision metadata, hash the plan, keep a fixed number of prior hashes in hidden canonical metadata, and block an identical or previously seen candidate before another revision/job is created.

6. Keep auxiliary artifacts off the linked issue. Log skip reasons while the `state:skip` label remains authoritative. Store transient implementation-reply recovery on the PR and leave human-facing replies attached to native review threads.

7. Migrate old timelines with a dry-run-first, ownership-checked command. Scan open and closed issues but exclude PRs; preserve the issue body and every human/foreign comment; upsert canonical bodies; delete only strictly recognized actor-owned legacy artifacts; re-read after apply and require convergence. A malformed marker or conflicting legacy identity fails only that issue before deletion.

8. Test observable behavior: canonical comment count remains two across amendments, raw patches never publish, repeated plans block, foreign marker comments remain inert, dry-run performs no writes, apply is idempotent, and restart repairs a stale canonical review without appending history.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Retain every plan/review/diff on the GitHub issue | Appended complete old plans, unified diffs, reviews, skip explanations, and recovery records as new comments. | Issue timelines and API/model context grew without bound; stale critique competed with the current decision and source patches duplicated Git history. | Keep only the latest canonical plan and review. Put detailed evidence in commits and PR-native review threads. |
| Bound prompts but preserve complete public history | Excluded older comments from agent prompts while leaving them on the issue. | This reduced prompt projection but did not solve noisy, oversized GitHub issues or costly comment ingestion. | Compact the durable public surface itself; bounded prompt projection alone is insufficient. |
| Delete every marker-bearing comment | Considered marker prefixes sufficient proof of automation ownership. | A human or another actor can quote the same marker, making prefix-only deletion destructive. | Require GitHub-authenticated ownership plus an exact recognized format before mutation. |
| Treat only reviewer-emitted `BLOCKED` as no progress | NOGO amendments continued until the fixed iteration budget even when the planner returned the same plan. | The loop re-reviewed identical work and could oscillate between old plans. | Compare normalized current and bounded prior fingerprints before publication and enter the durable blocked path immediately. |
| Compare raw stored comment bodies | Compared generated comment text directly. | Revision markers and wrappers made equivalent plans look different. | Normalize to plan payload before hashing or equality checks. |

## Results & Parameters

| Item | Required contract |
|------|-------------------|
| Linked issue automation comments | At most one actor-owned canonical plan and one actor-owned canonical plan review. |
| Review-cycle summary | Cumulative high-level bullets in the latest plan only. |
| Patch content | Reject fenced diffs, `diff --git`, and unified hunk headers before publication. |
| Historical liveness state | Fixed-size prior normalized-plan fingerprints, not full bodies. |
| No-progress result | Durable blocked state; no new revision and no further planner/reviewer job. |
| Skip explanations | Structured run log; `state:skip` remains durable authority. |
| Implementation discussion | Commits and PR-native review threads. |
| Migration default | Dry-run, open + closed issues, PRs excluded. |
| Mutation authority | Exact recognized format plus authenticated actor ownership. |
| Apply verification | Re-read every changed issue and require idempotent two-comment convergence. |

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #2719 implementation | Canonical replacement, bounded fingerprints, patch guard, PR-scoped handoff journal, strict migration planner/CLI, docs/ADR, and full unit suite (7,017 passed). |
| ProjectHephaestus | Live dry-run on issue #2363 | Proposed one canonical metadata update and deletion of three obsolete actor-owned artifacts; zero failures and no writes. |
