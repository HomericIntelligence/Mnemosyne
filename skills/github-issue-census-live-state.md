---
name: github-issue-census-live-state
description: "Take GitHub issue census membership and state from live paginated reads, not from the search index. Use when an audit, backlog count, or reconciliation claims all open or all closed issues, when a search total is larger than the tracker suggests, or when a search row disagrees with recent activity."
category: tooling
date: 2026-11-17
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [github, issues, census, search-index, stale-state, graphql, pagination, pull-requests, audit]
---

# GitHub Issue Census: Use Live State

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-17 |
| **Objective** | Make an issue census correct by separating text discovery from authoritative membership and state. |
| **Outcome** | Operational. In the source audit, a search-based count was more than twice the live issue count, and one residual owner read closed in search while it was open. |
| **Verification** | `verified-local` — the search read and the live read were compared in one session. No automated test runs this cross-check. |

The GitHub issue search endpoint is a text index. It is not a complete issue list. It also returns
pull requests, and its open or closed state can lag the live record. A census that uses it as the
membership source reports the wrong set and the wrong state.

## When to Use

- A census, audit, backlog count, or residual-owner list claims "all open issues" or "all issues
  closed since a date".
- The count comes from `search/issues`, `gh search issues`, or a similar search endpoint.
- The search total is larger than the issue tracker suggests, or the extra rows look like pull
  requests.
- A search row says an issue is closed, but recent activity or a linked owner list disagrees.
- The owner list will be published, and every owner state must be current at publication.

## Verified Workflow

### Quick Reference

```bash
# Authoritative read: paginate issue nodes, then filter on the live timestamps.
gh api graphql -f query='
query($end: String) {
  repository(owner: "<owner>", name: "<repo>") {
    issues(first: 100, after: $end, orderBy: {field: CREATED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes { number state createdAt closedAt title }
    }
  }
}'

# Text discovery only. is:issue excludes pull requests.
gh search issues --repo <owner>/<repo> 'is:issue <term>' --limit 100
```

### Suggested Approach

1. Separate discovery from authority. Use the search endpoint for keywords and body text. Use
   paginated issue nodes for membership, open or closed state, and timestamps.
2. Exclude pull requests. The issue search endpoint returns both object types. Add `is:issue`, or
   drop each row that carries a `pull_request` field.
3. Re-filter the boundary on the live record. Filter `createdAt` and `closedAt` from the
   authoritative nodes. Do not take the count or the state from search.
4. Reconcile the difference. When the search count exceeds the live count, name the exclusion that
   explains the extra rows before you publish the census.
5. Re-read each owner at publication. An issue can close or reopen during the audit. Read the
   current state immediately before you publish the owner list.
6. Record the query and the boundary. Put the exact query, the boundary timestamp, and the source
   revision in the audit record. A later delta can repeat them.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | ---------------- | --------------- | --------------- |
| Used the issue search endpoint as the census | Counted every row that the search returned for the date range | The endpoint includes pull requests, and its state can lag the live record | Use search for text only. Take membership and state from live paginated reads. |
| Trusted a search row for a residual owner | Removed the owner because search said it was closed | The issue was open, so the published list was wrong | Re-read each owner state at publication. |

## Results & Parameters

### Configuration

```yaml
issue_census:
  membership: paginated_issue_nodes
  state: live_nodes
  boundary: local_created_at_closed_at
  search: text_discovery_only
  search_type_filter: "is:issue"
  owner_reread_before_publication: true
```

### Expected Output

- The census count equals the number of live issue nodes in the range.
- Pull request numbers are absent from the issue count.
- Each residual owner state is read at publication.
- The record names the query, the boundary timestamp, and the source revision.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| A multi-service deployment repository | Delta audit of a previously closed audit issue, 2026-11-17 | The live read gave fewer than half the search count, and one owner issue read closed in search while it was open. |

## References

- [PR enumeration and idempotency](pr-enumeration-discovery-idempotency.md)
- [GraphQL fail-closed complete reads](github-graphql-pagination-fail-closed-complete-reads.md)
- [Negative-scan coverage attestation](negative-scan-coverage-attestation.md)