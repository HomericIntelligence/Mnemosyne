# Freeze Partial-Migration Import Debt - Notes

Supporting evidence for `architecture-migration-freeze-import-debt-baseline.md`.
These notes are not retrieved as guidance.

## Provenance

| Item | Value |
| ---- | ----- |
| Initial capture | 2026-07-20, planning and review session for a provider-runtime migration; no implementation, tests, or CI observed. |
| Amendment | 2026-11-01, review of a structural-debt change in an isolated checkout. |

## Amendment example: retract an upward edge

Context:

- A lower (service/runtime) module imported an upper (command-layer) module at
  function scope to run a group of job-submission actions.
- A layer-policy file listed the permitted upward import edges.
- A boundary test compared the observed edges with that list by exact
  equality, and counted package `__init__` re-exports as edges.

Change shape:

1. A new lower module took ownership of the job-submission action group.
2. The upper module kept its own handlers and called the new lower module.
3. The policy file lost the upward edge in the same commit.
4. The old upper module did not re-export the moved actions. Tests that
   patched the old import site now patch the new module.

Why the re-export variant is weaker:

- A forwarding import in the old module is a new edge. The guard accepts it
  only when it is recorded, and it delays the retirement of each consumer.
- If the export is added to a package `__init__` that the guard counts as a
  module, the guard reports a new edge and fails the policy check.

## Discovery limits of this amendment

- The advise helper was not installed in the session environment. Duplicate
  discovery used a direct regular-file listing of the resolved knowledge
  checkout, `skills/*.md`, with notes and history companions excluded.
- Open pull requests were checked with a read-only forge query against the
  resolved delivery revision. No open pull request changed the selected
  canonical entry.
- CI for the reviewed source change was not observed. The retirement rules are
  generalized from the reviewed diff, not from a green pipeline.
