# Notes: Refactor Program Milestone Capacity Allocation

## Source

- One planning session on a private Python service repository, 2026-11-17.
- The session read an existing release board, measured the module graph, and created a backlog of child issues.
- No code was executed. No implementation merged.

## Evidence

- The board exposed themes, due dates, and open-issue counts. The counts varied by an order of magnitude across six milestones.
- The source tree had a flat root package with most of the source and an import cycle that spanned many modules. Exact values are withheld.
- The plan assigned the boundary gate to the CI-hygiene milestone, low-risk merges to the lowest-load milestone, domain merges to the matching performance and access milestones, the cycle break to the design-decision milestone, and release consolidation plus two supervisor slices to the pre-GA milestone.
- Eight deep splits were assigned to release-candidate or GA milestones.

## Verification boundary

- Planning only. The allocation has not been validated by merged pull requests.
- The issues and milestone assignments were created successfully. No execution data exists.
- The cycle counts and module sizes in the source repository are not copied here.

## Related decisions

- The audit epic entry covers wave sequencing for audit findings.
- The release-board realignment entry covers a board change after a schedule change.
- This entry covers a new refactor program that must fit an existing release train.
- The god-package and module-decomposition entries cover the content of each slice.