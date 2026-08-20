# Parallel PR Worktree Workflow Notes

Supporting evidence for
[`parallel-pr-worktree-workflow.md`](parallel-pr-worktree-workflow.md).

## Case Index

| Case | Source | Verification | Result |
| --- | --- | --- | --- |
| Bulk rebase waves | ProjectOdyssey 70 PRs; ProjectScylla 13 PRs | verified-local | Three/four batched workers with isolated state |
| Six-wave patch series | ProjectArgus PRs #463–#474 | verified-ci | First-wave bleed-over eliminated by per-agent worktrees |
| Contamination consolidation | ProjectOdyssey PR #5363 | verified-ci | Eight tangled worker PRs collapsed into one branch |
| Shared prerequisite fan-out | ProjectHephaestus output-log fixes, 2026-06-13 | verified-local | Prerequisite landed before five isolated fixes |
| Stacked auto-merge orphan | ProjectHephaestus session, 2026-06-14 | verified-local | Retarget-before-arm rule and cherry-pick recovery |
| Current-head CI rescue | example-org/inference-service PRs #149/#155/#156/#157 | verified-ci | Logs, mergeability, focused tests, current-head polling |
| Conflict-before-validate | example-org/inference-service PRs #155/#254 | verified-ci | Rebase restored merge refs and checks |
| Endpoint-only workflow drift | example-org/inference-service PR #255 | verified-ci | Full-log diagnosis, tests, current CLI commands |
| Stale branch missing trunk dependency fix | ProjectHephaestus PRs #1731/#1732; prerequisite #1730 | verified-ci | Detached rebase, exact lease, green current-head checks |

## Detailed Evidence

The ProjectArgus series delivered 17 PRs over six waves. The first shared-tree wave showed
working-tree revert bleed-over; subsequent per-agent temporary worktrees had no state interference.
Live repository settings also caught an incorrect rebase-merge assumption and selected squash.

The ProjectOdyssey rescue found eight branches whose commits were cross-contaminated through shared
Git state. Selective per-branch force repair was abandoned in favor of one clean integration branch
and ordered cherry-picks; worker PRs were closed with the consolidation link.

The endpoint-only case demonstrates log-first triage. A truncated log suggested an obsolete parser
problem, while the full traceback showed endpoint dry-runs invoking cluster autodetection on runners
without the expected mounts. Focused tests prevented autodetection, CI workflow commands were updated
to current interfaces, and all current-head checks passed.

For PRs #1731/#1732, both heads predated merged PR #1730, which installed an automation dependency
in CI. Detached temporary worktrees were rebased rather than editing branch code. Focused suites
reported 82 and 24 passing tests, signatures/trailers were checked, exact old-head leases protected
the pushes, and GitHub reported CLEAN/MERGEABLE with all checks passing.

## Provenance

- Superseded main SHA-256:
  `bb8e4a6f8e500ac3e031fcd1422a7f37e9a0e19b88602d9652661f6375af8b5d`
- Issue #3335 base: `1ae0cb498e5250c341c2a4bf585f97e2a28060af`
- Old/new version: `1.8.0` → `2.0.0`
