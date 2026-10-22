---
name: github-issue-blockedby-bulk-linking
description: "Create native GitHub blocked-by issue dependencies in bulk with the GraphQL API instead of comments. Use when: (1) a tracking epic must be blocked by many issues, (2) comment cross-linking is unwanted, (3) the epic body checklist and the machine-readable dependency edges must stay consistent, (4) gh CLI offers no dependency subcommand."
category: ci-cd
date: 2026-10-22
version: "1.0.0"
user-invocable: false
tags: [github, graphql, issue-dependencies, blocked-by, epic, tracking-issue, bulk-operations, gh-cli]
---

# GitHub Issue Blocked-By Bulk Linking

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-22 |
| **Objective** | Link dozens of existing issues as blockers of a tracking epic without posting comment cross-references. |
| **Outcome** | Successful. 61 blocked-by edges created on an epic through the GraphQL API, two inter-blocker edges added, the epic body checklist kept consistent in the same change, and the result verified through the `blockedBy` connection count. No comments posted. |

## When to Use

- A tracking epic, milestone issue, or rollup must be marked as blocked by
  many other issues, or vice versa.
- The user or project forbids comment cross-links; linkage must be the native
  GitHub issue-dependency (blocked-by) relationship.
- An epic body carries a `- [ ] #N` checklist that must agree with the native
  dependency edges.
- One blocker must itself be blocked by another (for example, a rollout issue
  blocked by its mechanism issue).

## Verified Workflow

### Quick Reference

```bash
# 1. Resolve node IDs for the epic and all blockers in ONE aliased query:
gh api graphql -f query='query { repository(owner:"<owner>", name:"<repo>") {
  i123: issue(number: 123) { id number }
  i456: issue(number: 456) { id number }
} }'

# 2. Create each edge (reads: issueId IS BLOCKED BY blockingIssueId):
gh api graphql -f query='mutation($issue: ID!, $blocker: ID!) {
  addBlockedBy(input: {issueId: $issue, blockingIssueId: $blocker}) {
    issue { number } blockingIssue { number }
  } }' -F issue="<epic-node-id>" -F blocker="<blocker-node-id>"

# 3. Verify the edge count against the checklist:
gh api graphql -f query='query { repository(owner:"<owner>", name:"<repo>") {
  issue(number: <epic-number>) { blockedBy(first: 100) { nodes { number } } }
} }'
```

### Suggested Approach

1. Treat the epic body checklist (or another authoritative list) as the edge
   source. Extract blocker numbers from the checklist lines only; narrative
   references are not edges.
2. Batch the node-ID lookup. One repository query can carry many aliased
   `issue(number: N) { id }` fields. One query per issue is wasteful at dozens
   of issues and risks secondary rate limits.
3. Mind the direction. `addBlockedBy(input: {issueId: X, blockingIssueId: Y})`
   creates "X is blocked by Y". The API accepts the inverted direction without
   an error. Pass the epic as `issueId` and each blocker as `blockingIssueId`.
4. Create inter-blocker edges with the same mutation (rollout issue blocked by
   mechanism issue) using their node IDs directly.
5. Keep the two surfaces consistent in the same delivery: add or remove
   checklist lines through `gh issue edit --body-file` whenever edges change.
   A body link renders a reference but creates no machine-readable dependency;
   a dependency edge is invisible in the rendered checklist.
6. Verify by querying the `blockedBy` connection and comparing the node count
   with the checklist item count. A duplicate `addBlockedBy` call is not an
   idempotency signal you can rely on observing; treat the verification query
   as the record.
7. Remove an edge with `removeBlockedBy` (same input shape) when a checklist
   item leaves scope.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Body-only linking | Listed `- [ ] #N` items with full URLs in the epic body | Rendered references, but the dependency field stayed empty; blockers were not machine-readable and nothing showed the epic as "blocked by" | Body links and dependency edges are two separate surfaces. An epic that must expose dependency state needs `addBlockedBy`; keep the checklist for humans in the same edit |
| Comment cross-linking on each child issue | Considered a "tracked by epic" comment per issue | Rejected by the requirement: comment spam at dozens of issues | When comments are unwanted, the GraphQL dependency mutation is the complete substitute |
| One GraphQL query per issue for node IDs | Resolved node IDs individually | Dozens of avoidable round trips before any mutation ran | Alias many `issue(number:)` fields in a single repository query, then run one mutation per edge |

## Results & Parameters

### Configuration

```graphql
mutation LinkBlockedBy($issue: ID!, $blocker: ID!) {
  addBlockedBy(input: {issueId: $issue, blockingIssueId: $blocker}) {
    issue { number }
    blockingIssue { number }
  }
}
# verification:
# repository { issue(number: $epic) { blockedBy(first: 100) { nodes { number } } } }
```

### Expected Output

- One `addBlockedBy` success payload per edge, echoing the epic number and the
  blocker number.
- A `blockedBy` node count equal to the checklist item count after the final
  verification query.
- Each blocker displays the epic under its own "Blocking" relationship with no
  comment written.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Internal multi-model inference-serving platform | Promotion epic linked to 61 tracked issues plus 2 inter-blocker edges; zero comments | See [notes](github-issue-blockedby-bulk-linking.notes.md). |

## References

- [gh-create-pr-linked](gh-create-pr-linked.md) — PR-to-issue linking with `Closes #N`
- [planning-epic-verify-live-child-state](planning-epic-verify-live-child-state.md) — reconcile an epic checklist against live child state
- [GitHub GraphQL mutation `addBlockedBy`](https://docs.github.com/en/graphql/reference/mutations) — issue dependency mutations reference
