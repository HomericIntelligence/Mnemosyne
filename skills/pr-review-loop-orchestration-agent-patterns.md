---
name: pr-review-loop-orchestration-agent-patterns
description: "Use when implementing or debugging an agent-driven PR review/fix loop: progress must be commit-gated, GO convergence bounded, inline comments diff-valid, review evidence fully paginated, branch/head identity live-bound, non-blocking threads correctly dispositioned, and merge conditional on the reviewed head."
category: ci-cd
date: 2026-08-08
version: "2.0.0"
license: BSD-3-Clause
verification: verified-ci
user-invocable: false
history: pr-review-loop-orchestration-agent-patterns.history
tags: [implement-review-loop, review-thread-resolution, commit-gated-progress,
  verdict-go-convergence, inline-comment-diff-hunk, "422", no-commit-retry,
  graphql-review-threads, go-only-short-circuit, headrefname, ci-gate-owns-policy,
  state-skip-on-exhaustion, out-of-scope-thread-disposition, head-bound-review,
  connection-pagination, reviewed-head-rebind, rebase-conflict-budget,
  duplicate-plan-ownership, homericintelligence]
---

# PR Review Loop Orchestration and Agent Patterns

## Overview

A review loop advances only on externally observable evidence: a real commit, a complete thread
snapshot, an explicit verdict, and a head-bound merge check. Model self-report, zero comments, or a
branch-name convention are not evidence. Keep reviewer, fixer, CI-policy gate, and merge owner
responsibilities distinct.

Case-level evidence is indexed in
[`pr-review-loop-orchestration-agent-patterns.notes.md`](pr-review-loop-orchestration-agent-patterns.notes.md).
The full superseded source is in
[`pr-review-loop-orchestration-agent-patterns.history`](pr-review-loop-orchestration-agent-patterns.history).

## When to Use

- Threads are resolved even though the fixer produced no commit.
- The loop exits on AMBIGUOUS/NO-GO, zero threads, or one unchanged iteration.
- GitHub rejects generated inline comments with HTTP 422.
- A no-commit CI-fix needs one bounded retry with unresolved evidence.
- A reviewer/fixer lacks shell or GitHub capabilities, or GraphQL fields fail at runtime.
- Existing PR discovery assumes an issue-derived branch rather than `headRefName`.
- Review duplicates a policy already enforced by a required CI gate.
- Non-blocking/out-of-scope comments are incorrectly edited or marked addressed.
- Review evidence can span multiple pages or nested comment connections.
- The reviewed head changes, becomes behind/conflicting, or is merged from a queue.

## Verified Workflow

### 1. Bind the loop to the live PR and head

Resolve the PR first, then use its real `headRefName`, `headRefOid`, and base. Never infer the head
from an issue number. Persist the reviewed head and branch-point snapshot as part of the review
record.

```bash
gh pr view <pr> --json \
  number,state,headRefName,headRefOid,baseRefName,mergeable,mergeStateStatus,statusCheckRollup,url
```

If the current branch already belongs to a MERGED PR, it is a spent identity. Follow-up work uses a
fresh branch and PR. Duplicate plan publishers should lose an ownership/admission race as a benign
terminal outcome, not poison an already completed run.

### 2. Assign capabilities and ownership explicitly

The reviewer needs repository/diff inspection and review-posting capability. The fixer needs shell,
editing, tests, commit, and push. A constrained code-reviewer agent that cannot run commands or post
reviews is not a fixer or GitHub review publisher. The coordinator owns iteration limits, head
binding, state transitions, and merge admission.

Required CI gates own deterministic policy such as issue linkage and signed commits. Do not ask an
LLM reviewer to rediscover those facts, especially when a policy fetch can fail open into a false
violation. Keep advisory gates advisory and read the live required-check configuration.

### 3. Collect complete review evidence

Before concluding that no blocking evidence exists, paginate every review-thread connection and
every nested comment connection. Preserve stable thread/comment IDs, author, body, path, line/side,
resolution state, and timestamps. A first page or top-level review summary is insufficient.

Take the branch-point snapshot before any post-review rebase. Review the proposed patch relative to
that original base; rebasing first can erase the context that the reviewer was supposed to inspect.

### 4. Validate inline comment locations

GitHub accepts an inline review comment only on a line represented by the PR diff. Parse hunk headers
of the form `@@ -oldStart[,oldLen] +newStart[,newLen] @@`; omitted lengths mean one line. Track old
and new coordinates through context, deletion, and addition lines. RIGHT-side comments target new
file `+`/context lines; LEFT-side comments target old file `-`/context lines.

Before posting, verify path, side, and line against the parsed changed-line set. If no legal inline
anchor exists, post a non-inline review body or omit the comment according to policy; do not retry
the same invalid payload.

### 5. Run a commit-gated review/fix cycle

For each bounded iteration:

1. Snapshot the current head and unresolved blocking threads.
2. Run the reviewer and parse an explicit GO, NO-GO, or AMBIGUOUS verdict.
3. If GO, ensure required checks and head-binding conditions are satisfied.
4. If non-GO with blocking threads, dispatch the fixer with their verbatim bodies and IDs.
5. Compare the repository head before and after the fixer.
6. Resolve only threads whose disposition is supported by the resulting commit or an accepted
   no-edit disposition.
7. Re-review the new head; never treat the fixer's self-report as convergence.

Thread resolution belongs to the reviewer/coordinator, not the fixer. A claimed change without a
new commit is no progress. Run pre-commit against the full PR diff from the merge base, not merely
the files the last agent remembers editing.

Existing PR idempotency short-circuits only on a valid GO for the current head. `has_go or has_no_go`
is wrong: it permanently skips PRs that need another iteration. Zero threads is not equivalent to
GO; AMBIGUOUS/NO-GO continues until explicit GO or the configured maximum is truly exhausted.

### 6. Handle no-commit outcomes and bounded retry

When a CI/review fixer produces no commit while blocking threads remain, perform exactly one forced
engagement retry. Inject unresolved thread text verbatim, state that a real commit is required for
progress, and provide the current failure/check evidence. Persist a forensic marker containing PR,
head, attempt, unresolved IDs, and outcome.

If the retry also produces no commit, leave threads unresolved and classify the terminal state
honestly. Do not resolve based on prose. For stale PRs, a deterministic zero-thread NO-GO can be an
intentional no-progress escalation to `state:skip`; inspect the anomaly comment before diagnosing a
reviewer defect. A freshly implemented PR entering the same state warrants investigation.

### 7. Disposition non-blocking and out-of-scope threads

A reviewer may explicitly classify a comment as non-blocking, pre-existing, follow-up-worthy, or
outside the approved plan. Give it a recorded disposition without changing code and keep it out of
the `addressed` set when the contract defines addressed as in-scope remediation. Resolving a comment
means deciding what happens; it does not always mean editing.

If a requested edit violates an approved guard—such as a required count not increasing—preserve the
guard and create/link a follow-up instead. An empty addressed set is a valid no-op when all comments
were correctly deferred.

### 8. Validate GraphQL against the live schema

Do not guess mutation fields. Introspect the live schema or use documented leaf selections before
shipping. Distinguish:

- `Field 'X' doesn't exist on type 'Y'`: wrong selected output field.
- `InputObject '<Input>' doesn't accept argument '<arg>'` plus unused variable: wrong mutation
  input/name.

For replies, use the schema-supported review-thread reply mutation and select a valid leaf (for
example the returned comment ID). Resolution uses the separate resolve-thread mutation. Keep query
pagination and mutation behavior covered by focused tests.

### 9. Rebind before merge

A GO applies to one exact reviewed head. Immediately before a normal conditional or queue merge,
re-read the PR head and required checks. If the head changed, discard the stale GO and re-review.
If it is behind/conflicting after review, use the host-owned bounded rebase path, restore the writer
checkout, re-run validations, and re-enter review. Enforce a conflict/retry budget; remote-head drift
must not become an unbounded force-push loop.

Merge evidence includes the reviewed head, final head, required check conclusions, merge commit or
squash OID, and complete thread disposition snapshot.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Resolve on model self-report | Resolve on model self-report | No repository evidence changed | Gate progress on actual commit/head |
| Exit on zero comments | Exit on zero comments | Verdict may still be NO-GO/AMBIGUOUS | Require explicit GO or true exhaustion |
| Skip existing PR on NO-GO | Skip existing PR on NO-GO | Prevents remediation forever | GO-only idempotency shortcut |
| Retry invalid inline payload | Retry invalid inline payload | Line is not on a diff hunk | Parse old/new hunk coordinates first |
| Infer branch from issue number | Infer branch from issue number | Fetches the wrong/nonexistent head | Read live `headRefName` |
| Reviewer rechecks CI-owned policy | Reviewer rechecks CI-owned policy | Fetch errors create false violations | Let deterministic required gates own policy |
| First-page thread audit | First-page thread audit | Misses blocking nested/page-two evidence | Paginate both connection levels |
| Resolve every comment by editing | Resolve every comment by editing | Violates scope and follow-up semantics | Record explicit no-edit dispositions |
| Merge after head drift | Merge after head drift | GO no longer covers the code | Rebind and re-review exact head |

## Results & Parameters

Loop state contract:

```text
MAX_REVIEW_ITERATIONS = <bounded positive integer>
reviewed_head = <oid>
branch_point = <oid>
verdict = GO | NO-GO | AMBIGUOUS
unresolved_blocking_thread_ids = [...]
head_before_fixer = <oid>
head_after_fixer = <oid>
forced_no_commit_retry_used = true | false
addressed_thread_ids = [...]
deferred_thread_dispositions = [{id, reason, follow_up}]
required_checks = [{name, conclusion, head_oid}]
merge_proof = {final_head, merge_oid}
```

Review/fixer prompts should include PR URL, exact head/base, owned files, forbidden scope, unresolved
thread bodies, expected commands/tests, commit requirements, and the iteration budget.

## Verified On

- Verified-ci orchestration, thread, GraphQL, branch-point, and head-rebind behavior through
  2026-08-08.
- Compacted for issue #3335 without promoting any evidence classification.
