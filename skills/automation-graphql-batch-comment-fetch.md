---
name: automation-graphql-batch-comment-fetch
license: BSD-3-Clause
description: "Use aliased GraphQL comment batches only as bounded, best-effort review context. Use when: (1) reducing N+1 comment reads where partial context is acceptable, (2) preserving a legacy review-state optimization, or (3) separating fast context caches from authoritative discovery. Never use a capped or failure-to-empty batch to prove plan absence, authorize a write, route durable state, or consume a retry budget."
category: optimization
date: 2026-08-06
version: "2.0.0"
user-invocable: false
verification: unverified
history: automation-graphql-batch-comment-fetch.history
tags:
  - graphql
  - batch-fetch
  - github-api
  - aliased-query
  - bounded-context
  - n-plus-one
  - comment-fetch
  - automation-pipeline
  - completeness-boundary
  - plan-discovery
  - fail-closed
---

# Bounded GraphQL Comment Context

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-06 |
| **Objective** | Retain the useful one-call GraphQL context optimization without allowing a capped or failed batch to become authoritative absence. |
| **Outcome** | The original batch optimization shipped and passed CI; this v2 boundary proposes moving all absence-sensitive plan discovery to complete paginated REST reads. |
| **Verification** | unverified — PR #670 verified the v1 performance optimization, but the v2 authority split and Hephaestus migration were not implemented or run in this learning session. |
| **History** | [changelog](./automation-graphql-batch-comment-fetch.history) |

Aliased GraphQL remains useful when a caller explicitly wants recent context and
can tolerate caps or missing data. It is unsafe as a source for a negative fact.
A helper that requests `comments(last: 100)` and returns empty lists after failures
cannot distinguish these states:

- the issue truly has no comments;
- the canonical comment is older than the cap;
- one alias was missing or malformed;
- GitHub rejected or rate-limited the request;
- JSON parsing failed.

Use a separate complete, strict, ownership-aware REST path whenever `ABSENT` can
cause publication, label mutation, routing, a successful worker exit, or retry
budget consumption.

## When to Use

- A review UI or prompt benefits from one bounded batch of recent issue comments.
- An N+1 optimization is needed and incomplete context only reduces quality; it
  cannot change correctness or durable state.
- A legacy `fetch_all_issue_comments_graphql()` helper must remain for review-state
  consumers while plan discovery migrates away from it.
- You are designing separate caches for fast context and authoritative decisions.
- You need to document why an empty best-effort result means "context unavailable
  or empty," not "the resource is absent."

Do not use this pattern when a negative lookup authorizes a write, suppresses work,
advances a state machine, or consumes an absence/retry budget. Use complete
paginated REST plus an explicit result contract for those paths.

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat the v2
> authority split as a hypothesis until the Hephaestus migration and CI pass.

### Quick Reference

```python
def fetch_bounded_issue_comment_context(
    issue_numbers: list[int],
) -> dict[int, list[dict[str, object]]]:
    """Return recent best-effort context, never authoritative absence.

    Empty lists may mean no comments, a capped-out older comment, or a failed
    lookup. Callers must not use this result for publication or state gates.
    """
    return fetch_all_issue_comments_graphql(issue_numbers)
```

```python
# Context-only consumer: partial data is acceptable.
review_context = fetch_bounded_issue_comment_context(issue_numbers)

# Correctness-sensitive consumer: a separate complete path is required.
plan_lookup = discover_plan_via_complete_paginated_rest(issue_number)
if plan_lookup.status is PlanDiscoveryStatus.READ_ERROR:
    return RETRY
if plan_lookup.status is PlanDiscoveryStatus.ABSENT:
    publish_candidate_or_spend_absence_budget()
```

### Detailed Steps

1. **Classify the downstream decision before optimizing.** Ask what an empty
   result causes. If it only shortens context, a bounded batch may be appropriate.
   If it changes durable state, success, publication, routing, or budget, require
   complete enumeration and explicit failure.

2. **Name the helper for its real guarantee.** Prefer names and docstrings such as
   `fetch_bounded_issue_comment_context()` over `fetch_all_*` when the query uses
   `last: 100`. If compatibility requires the historical name, document the cap
   and prohibition at the function definition.

3. **Keep GraphQL batching for context only.** Aliased fragments can still reduce
   N subprocess and network round-trips to one call. Reverse nodes if context
   consumers need chronological order. Do not pass the resulting lists to an
   authoritative plan selector.

4. **Build a separate complete REST discovery path.** Fetch every issue-comment
   page, reject non-object entries, validate every body and author login, require
   the authenticated viewer identity, derive ownership by case-insensitive login
   comparison, and return `FOUND`, `ABSENT`, or `READ_ERROR`.

5. **Do not share ambiguous caches.** A context cache may use `[]` as its
   best-effort fallback because no correctness claim is attached. An authoritative
   cache must keep successful normalized journals and per-issue read errors
   separately. A missing key triggers a real read.

6. **Remove plan-presence APIs from the context module.** Replace
   `has_existing_plan()` and callers that accept the GraphQL cache with a tri-state
   discovery method backed by the complete REST reader. Preserve review-context
   consumers only if they do not infer absence.

7. **Correct docs and tests together.** Test the GraphQL helper as bounded context:
   one aliased call, expected ordering, and documented failure-to-empty behavior.
   Separately test authoritative discovery for empty success, valid owned plan,
   foreign marker, API failure, rate limit, malformed page/body/author, and missing
   identity.

8. **Bind raw payload failure to the state-machine outcome.** Do not stop at a
   normalizer unit test. Feed a malformed REST payload through the production
   adapter and assert `RETRY`, no candidate write, no label mutation, and no
   absence-budget charge.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Treat `last: 100` as complete | A bounded query was named `fetch_all_*` and used to decide whether any plan existed. | A valid older plan could fall outside the slice. | Caps are acceptable for context, never for authoritative negative facts. |
| Return `{issue: []}` on transport failure and call `has_existing_plan()` | Operational failure was intentionally softened for the optimization. | `False` became indistinguishable from a successful empty journal. | Failure-to-empty APIs cannot feed publication, routing, success, or budget gates. |
| Return `[]` for a missing cache key | A partial alias response looked like a successfully fetched empty issue. | The caller skipped the real fallback read and invented absence. | Authoritative caches need distinct missing, empty-success, and error states. |
| Reuse one cache for review context and plan authority | DRY was applied to values with different correctness guarantees. | The weaker GraphQL guarantee contaminated the stronger plan-discovery decision. | Share parsing policy where guarantees match; keep context and authority surfaces separate. |
| Increase the cap | Raising 100 to a larger magic number appeared to reduce risk. | No finite cap proves completeness for a growing journal, and failures still collapse to empty. | Use pagination to exhaustion for completeness-sensitive reads. |
| Remove batching everywhere | The unsafe authority use made the optimization itself look invalid. | Recent review context can still benefit from one best-effort call. | Preserve the optimization inside an explicit bounded-context boundary. |

## Results & Parameters

### Decision Table

| Consumer | Bounded GraphQL allowed? | Required failure model |
|----------|--------------------------|------------------------|
| Prompt/review recent context | Yes | Empty may mean unavailable; no durable decision |
| Interactive recent-comment display | Yes | Display partial/unavailable state honestly |
| Canonical plan presence/absence | No | Complete REST -> `FOUND` / `ABSENT` / `READ_ERROR` |
| Candidate plan publication | No | `READ_ERROR` retries; only `ABSENT` authorizes initial write |
| Restart fast-forward | No second lookup | Reuse successfully reconciled journal snapshot |
| Absence/retry budget accounting | No | Charge only after confirmed `ABSENT` |

### GraphQL Context Parameters

```graphql
comments(last: 100, orderBy: {field: UPDATED_AT, direction: DESC}) {
  nodes { body updatedAt url }
}
```

- `last: 100` is a context-window choice, not a completeness guarantee.
- Aliasing N issues into one query changes round-trip count, not completeness.
- Reversing nodes restores chronological presentation for consumers that need it.
- Empty-on-failure is permitted only when callers cannot infer a negative fact.

### ProjectHephaestus Migration

```text
state/review.py
  keep fetch_all_issue_comments_graphql() as bounded legacy review context
  document that it may return empty after a failed or capped lookup

state/planner.py
  replace GraphQL plan prefetch with complete REST reads
  cache successful normalized journals separately from errors
  make a missing cache key perform a fallback read

review_journal.py
  own strict normalization and the actor-owned tri-state selector
```

### Proposed Validation

```bash
uv run pytest \
  tests/unit/automation/state/test_planner.py \
  tests/unit/automation/test_pipeline_github.py \
  tests/unit/automation/pipeline/stages/test_stage_planning.py -v

uv run ruff check \
  hephaestus/automation/state/review.py \
  hephaestus/automation/state/planner.py \
  hephaestus/automation/review_journal.py \
  tests/unit/automation
```

### Verification Promotion

Promote v2 to `verified-local` only after the complete-reader migration and
focused state/pipeline tests pass locally. Promote it to `verified-ci` after the
Hephaestus PR's required CI passes. Preserve PR #670 as evidence for the original
GraphQL round-trip optimization, not for authoritative plan absence.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | v1 aliased GraphQL optimization | PR #670 passed CI; performance pattern verified. |
| ProjectHephaestus | v2 bounded-context/authority split | Proposed only; implementation and CI pending. |

## Related Skills

- `automation-prefix-match-plan-detection` — canonical complete,
  ownership-aware `FOUND` / `ABSENT` / `READ_ERROR` plan discovery.
- `github-api-secondary-rate-limit-backoff` — rate-limit handling at GitHub API
  boundaries.
