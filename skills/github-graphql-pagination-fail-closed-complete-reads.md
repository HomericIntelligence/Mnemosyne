---
name: github-graphql-pagination-fail-closed-complete-reads
description: "Design complete, fail-closed GitHub GraphQL connection reads with centralized cursor traversal, nested-connection ceilings, duplicate detection, and caller-specific failure policy. Use when: (1) a GitHub GraphQL consumer reads reviewThreads or another cursor connection, (2) later pages must not be silently omitted, (3) malformed pageInfo, cursor cycles, duplicate IDs, or oversized nested histories must not expose partial facts, (4) read-only dedupe helpers may fail open but authorization or reconciliation reads must fail closed."
category: architecture
date: 2026-08-06
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - github
  - graphql
  - pagination
  - cursor-connection
  - review-threads
  - fail-closed
  - complete-read
  - fixed-point
  - duplicate-detection
  - safety-ceiling
---

# GitHub GraphQL Pagination: Fail-Closed Complete Reads

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-06 |
| **Objective** | Design standalone GitHub PR review reads that traverse every outer review-thread page, fetch every required nested comment page within an explicit ceiling, and never expose partial facts after malformed, cyclic, duplicate, or oversized input. |
| **Outcome** | Proposed architecture and regression matrix. The central rule is to finish and validate the transport-level connection before normalizing or returning domain facts. No implementation or test run was performed in the source session. |
| **Verification** | `unverified` — planning artifact only; implementation, local tests, and CI validation are pending. |

The reusable distinction is between **mechanism** and **policy**:

- One private paginator owns cursor forwarding, page-shape checks, cycle detection,
  optional node ceilings, and all-or-error completion.
- Domain readers own response-path validation, identity consistency, duplicate-ID
  semantics, fixed-point rereads, and the choice to fail open or fail closed.
- Consumers receive nodes only after the whole connection succeeds. A later-page
  error must not leak an earlier-page subset as if it were complete.

## When to Use

- A GitHub GraphQL query selects a connection such as
  `reviewThreads(first:100, after:$after)` or
  `comments(first:100, after:$after)`.
- Correctness depends on seeing items beyond the first page, especially unresolved
  review threads, ownership receipts, markers, or authorship history.
- A connection is security- or authorization-relevant and absence must mean
  "confirmed absent," not "not found in the first page."
- Nested histories are potentially unbounded and need a documented ingest ceiling,
  while the outer identity set must remain uncapped for completeness.
- Multiple callers have different failure contracts: reconciliation must stop on an
  incomplete read, while a best-effort dedupe lookup can log once and behave as if it
  found nothing.
- Concurrent mutations can change the connection during traversal, requiring two
  equal complete reads before deriving a mutation or remediation snapshot.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a
> hypothesis until implementation tests and CI confirm it.
>
> **Repository compatibility:** Mnemosyne's current validator requires the literal
> `## Verified Workflow` heading. The executable proposal is therefore retained
> under that compatibility heading below, but it remains unverified.

## Verified Workflow

> **Warning:** This is the proposed workflow from an unexecuted design. No source
> changes or tests were run in the originating session.

### Quick Reference

```python
"""Shared GraphQL connection pagination for automation GitHub reads."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

MAX_PR_REVIEW_THREAD_COMMENTS = 2_000

GraphQLPageFetcher = Callable[[str | None], dict[str, Any]]


def collect_graphql_connection_nodes(
    fetch_page: GraphQLPageFetcher,
    *,
    connection_name: str,
    max_nodes: int | None = None,
) -> list[dict[str, Any]]:
    """Collect a complete cursor connection or raise without returning partial data."""
    nodes: list[dict[str, Any]] = []
    seen_cursors: set[str] = set()
    after: str | None = None

    while True:
        connection = fetch_page(after)
        page_nodes = connection.get("nodes")
        page_info = connection.get("pageInfo")
        if not isinstance(page_nodes, list) or not all(
            isinstance(node, dict) for node in page_nodes
        ):
            raise RuntimeError(f"malformed {connection_name} nodes")
        if not isinstance(page_info, dict):
            raise RuntimeError(f"malformed {connection_name} pageInfo")
        if max_nodes is not None and len(nodes) + len(page_nodes) > max_nodes:
            raise RuntimeError(
                f"{connection_name} exceeds the {max_nodes}-node safety ceiling"
            )
        nodes.extend(page_nodes)

        has_next_page = page_info.get("hasNextPage")
        if not isinstance(has_next_page, bool):
            raise RuntimeError(f"malformed {connection_name} hasNextPage")
        if not has_next_page:
            return nodes

        end_cursor = page_info.get("endCursor")
        if (
            not isinstance(end_cursor, str)
            or not end_cursor
            or end_cursor in seen_cursors
        ):
            raise RuntimeError(f"invalid or repeated {connection_name} cursor")
        seen_cursors.add(end_cursor)
        after = end_cursor
```

### Detailed Steps

1. **Centralize only connection traversal.** Give the helper a callback accepting the
   previous page's cursor and returning one already-located connection object. Keep
   repository/PR path extraction and GraphQL error checks in the callback because
   those are query-specific.

2. **Validate each page before accumulating it.** Require `nodes` to be a list of
   mappings, `pageInfo` to be a mapping, and `hasNextPage` to be a real boolean.
   When another page is required, require a non-empty, previously unseen string
   `endCursor`. A terminal page does not need a usable cursor.

3. **Keep partial state private.** The accumulator lives inside the paginator, and the
   callback performs no consumer-visible mutation. If page 2 fails after page 1
   succeeded, the helper raises; no caller can receive page 1 as a complete result.
   Normalize, filter, deduplicate, or publish domain facts only after the helper
   returns.

4. **Do not cap the outer identity connection.** Traverse all PR review threads with
   `max_nodes=None`. Completeness of the unresolved-thread set and review ownership
   lookup requires following every `hasNextPage` cursor, even after 100 threads.
   Cursor-cycle rejection still bounds a malformed traversal.

5. **Bound full nested histories explicitly.** Fetch review-thread comments in pages
   (for example, `first:100`) and pass
   `max_nodes=MAX_PR_REVIEW_THREAD_COMMENTS`. A proposed ceiling of `2_000` comments
   protects memory and runtime without silently truncating a conversation: node
   2,001 raises before any thread fact is returned.

6. **Select only contract-required nested fields.** Inline dedupe and review ownership
   consume the thread's root comment, so their outer thread query can use
   `comments(first:1)` and select the root ID/body/editability/review ID. Authorship,
   marker reconciliation, or complete prompt construction must use the separate full
   comment-history traversal.

7. **Validate identities after complete pagination.** For strict reconciliation,
   reject duplicate thread IDs and duplicate comment IDs, PR/thread identity drift,
   or changing thread fields. For best-effort shared thread selection, preserve first
   appearance of an identical duplicate but treat a repeated ID with a conflicting
   payload as a failed read. Never let last-write-wins hide contradictory facts.

8. **Preserve fixed-point rereads.** Read the complete outer unresolved-thread set
   twice and require equality before hydrating it. When a thread conversation spans
   multiple pages, read that complete comment connection twice and require equal
   snapshots. If either complete read fails or differs, do not derive a remediation
   or mutation snapshot.

9. **Apply failure policy at the caller boundary.** Let the shared paginator raise on
   transport, JSON, GraphQL, response-shape, cursor, duplicate, or ceiling errors.
   Strict unresolved-thread reconciliation propagates or converts these to
   `RuntimeError`. Best-effort inline dedupe and review-receipt lookup catch the whole
   read once, log one warning, and return an empty result so posting can continue
   without trusting partial evidence.

10. **Reuse the centralized outer fetch.** Review ownership lookup should filter the
    same paginated thread nodes used by inline dedupe instead of maintaining a second
    cursor loop. Ordered dictionaries or an insertion-ordered mapping give stable,
    once-only thread IDs after validation.

11. **Drive the design with later-page failures.** Unit tests must assert exact
    callback cursors (`None`, then each `endCursor`), zero extra calls after
    `hasNextPage: false`, stable aggregation order, rejection of malformed
    `pageInfo`, missing/repeated cursors, and rejection above the optional ceiling.
    At the domain layer, include 101+ threads, 21+ comments, a 2,001-comment thread,
    identical and conflicting duplicates, and a GraphQL error on a later page.

12. **Document the completeness contract beside the consumer.** State that outer
    review threads are uncapped, full comment histories have the explicit 2,000-node
    ceiling, and any malformed/cyclic/oversized read fails without exposing partial
    facts. Explain why root-only queries intentionally use `comments(first:1)`.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| First-page-only outer query | Read `reviewThreads(first:100)` without `pageInfo` or `after`. | A matching unresolved thread or review receipt after the first 100 was treated as absent. | Any correctness-relevant connection needs full cursor traversal, not a large-looking page size. |
| Fixed nested comment slice | Read `comments(first:20)` and treated it as the conversation. | Later authors, replies, or markers disappeared, producing a partial review fact. | Fetch complete histories when the contract consumes history; use `first:1` only for an explicitly root-only contract. |
| Duplicate cursor loops per caller | Inline dedupe and review ownership each implemented pagination separately. | Shape validation, cursor-cycle handling, fields, and exception coverage drifted between callers. | Centralize traversal and share the fully paginated node fetch; keep caller policy outside it. |
| Return accumulated nodes after a later-page error | Kept page 1 when page 2 had JSON, GraphQL, shape, or cursor failure. | An incomplete prefix was indistinguishable from a complete read and could authorize incorrect review behavior. | A complete-read primitive has only two outcomes: all nodes or an exception. |
| Cap the outer thread set | Applied a safety ceiling to `reviewThreads`. | A valid large PR could never establish the complete unresolved-thread set. | Leave the outer identity traversal uncapped; cap only the expensive nested history with an explicit failure. |
| Accept repeated IDs or cursors | Allowed last-write-wins dedupe or reused the current cursor. | Conflicting payloads hid inconsistent facts, while cursor cycles could loop forever. | Reject cycles and strict-reader duplicates; only coalesce equivalent duplicates where the caller contract permits it. |
| Catch only subprocess and JSON errors | Best-effort helper ignored GraphQL error payloads and malformed connection shapes. | Later-page semantic failures could bypass the fallback and leak inconsistent behavior. | Wrap the whole centralized read at the caller boundary and log exactly once before returning the caller's safe empty value. |

## Results & Parameters

This design was not executed. The following are proposed contract parameters and test
expectations, not observed production results.

| Parameter | Proposed value | Reason |
|-----------|----------------|--------|
| Outer review-thread page size | `100` | GitHub GraphQL page size while still following every cursor. |
| Outer review-thread ceiling | None | Every thread must be traversed; a size cap would turn a valid large PR into an incomplete fact set. |
| Full comment-history page size | `100` | Reduces round trips while retaining explicit cursor traversal. |
| Full comment-history ceiling | `2_000` nodes per thread | Bounded-ingest safety limit; exceeding it raises instead of truncating. |
| Root-only nested selection | `comments(first:1)` | Dedupe and ownership contracts consume only the root comment. |
| Cursor state | `set[str]` of prior `endCursor` values | Detects non-adjacent cycles as well as an immediately repeated cursor. |
| Strict-reader failure | `RuntimeError` | Reconciliation cannot safely continue without complete facts. |
| Best-effort helper failure | One warning plus `[]` | Dedupe/receipt lookup may decline to optimize, but must not trust a partial prefix. |

**Minimum paginator regression matrix:**

```text
one terminal page                 -> nodes returned; callback receives [None]
three valid pages                 -> stable concatenation; after=[None, c1, c2]
terminal page with endCursor null -> accepted; no extra call
nodes not list[dict]              -> RuntimeError; no result returned
pageInfo missing/not dict         -> RuntimeError; no result returned
hasNextPage missing/not bool      -> RuntimeError; no result returned
next page cursor empty/not string -> RuntimeError; no result returned
cursor c1 -> c2 -> c1             -> RuntimeError; no infinite loop
exactly max_nodes                 -> accepted
max_nodes + 1 on later page       -> RuntimeError; earlier nodes not returned
```

**Minimum PR review regression matrix:**

```text
matching thread at index 101        -> found after outer pagination
thread with more than 20 comments   -> all required comments present
thread with 2,001 comments          -> strict read raises; helper returns []
identical repeated thread payload   -> emitted once in stable order where permitted
same thread ID, conflicting payload -> failed read; no partial facts
GraphQL error on page 2             -> page 1 never escapes
hasNextPage false on page 1         -> no second API request
fixed-point traversal differs       -> reconciliation raises
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Standalone PR review pagination design | Proposed refactor of automation-layer GitHub API thread and review readers; not implemented or verified in the source session. |
