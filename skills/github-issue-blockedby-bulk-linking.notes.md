# Notes: github-issue-blockedby-bulk-linking

Supporting evidence for the main entry. Generalized; identifiers withheld per
the privacy rules.

## Session evidence (2026-10)

Context: a promotion epic needed native blocked-by relationships against 61
issues (60 pre-existing blockers plus 1 newly filed issue), plus 2
inter-blocker edges (a rollout issue blocked by its mechanism issue). The user
explicitly rejected comment cross-linking.

Execution record:

- Extracted the 61 blocker numbers from the epic body `- [ ]` checklist lines
  with a line filter plus a URL group match; narrative references inside the
  body were deliberately not made into edges.
- Resolved 62 node IDs (epic + blockers) in a single GraphQL repository query
  with one aliased `issue(number: N) { id number }` field per issue. All
  resolved; none missing.
- Ran one `addBlockedBy(input: {issueId, blockingIssueId})` mutation per edge
  with a ~0.3 s pause between calls: 61 epic-blocker edges, then 2 rollout
  edges. Every mutation returned a success payload echoing both issue numbers.
- Updated the epic body to add the two new blockers (checklist grew from 61 to
  63 items) with `gh issue edit --body-file` in the same delivery.
- Verification: a `blockedBy(first: 100) { nodes { number } }` query returned
  63 nodes, equal to the checklist item count.

## Useful details

- Direction: `addBlockedBy(issueId: X, blockingIssueId: Y)` is read
  "X is blocked by Y". The mutation reported
  `{ issue: <epic>, blockingIssue: <blocker> }` on success.
- There is no `gh issue` subcommand for dependencies; `gh api graphql` is the
  path.
- `removeBlockedBy` takes the same input shape for edge removal.
- The `blockedBy` connection is also the cheapest audit surface when the
  checklist is edited later: compare node count to checklist count before
  claiming consistency.
