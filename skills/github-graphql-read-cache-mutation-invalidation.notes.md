# Notes: GitHub GraphQL Read Cache

Support for [github-graphql-read-cache-mutation-invalidation](github-graphql-read-cache-mutation-invalidation.md).
This file is not part of normal skill retrieval.

## Evidence source

- An automation loop in a private repository shared one GitHub token across
  many worker processes.
- Duplicate GraphQL reads, repeated on each poll cycle, spent the hourly
  GraphQL budget. A separate operational entry covers the budget diagnosis.
- The work moved through plan review, plan amendment, implementation, and pull
  request publication in one session.

## Verified checks in that session

- Focused unit and integration tests passed, including a single-transport
  contract test and a cross-process store test.
- Lint, format, and type checks passed on the changed paths.

Report these as local evidence. The change is not yet validated by a merge.

## Plan drift observed

The approved plan was written against an earlier source state. Three anchors
were gone at implementation time:

- merge-gate operations and a default-branch query no longer existed;
- merge-gate and check-run reads had moved to REST, outside the query entry
  point.

Result: the cache cannot reduce REST reads, and the bypass list is shorter than
the plan expected.

Check each named symbol in the plan against the current tree before you code.
Record a scope change on the issue, then continue. Do not add a cache entry for
an operation that no longer exists.

## Design notes

- Fail open at the key-building step: an unresolvable repository, or variables
  that are not scalars, skip the cache.
- Fail closed at the operation step: an operation that is not on the
  allow-list is never cached.
- The token hash is a digest prefix only. Entries from two tokens for the same
  repository never share a key, so a lower-privilege token cannot read an entry
  that a higher-privilege token wrote.
- The event counter is enough for operators. Do not invent a per-call point
  cost model. The budget cost of a GraphQL query depends on the query shape,
  and the server reports the true cost.

## Measured effect

Not measured. The first cycle fills the store, so measure over at least two
poll cycles. Compare `gh api rate_limit --jq '.resources.graphql'` before and
after a loop run with the cache enabled.