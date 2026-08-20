# PR Review Loop Orchestration Notes

Supporting evidence for
[`pr-review-loop-orchestration-agent-patterns.md`](pr-review-loop-orchestration-agent-patterns.md).

## Case Index

| Case | Source | Verification | Result |
| --- | --- | --- | --- |
| Commit-gated progress and GO convergence | ProjectHephaestus PR #1084, issue #1083 | verified-ci | Reviewer-side resolution and bounded state vocabulary |
| Inline diff-hunk validation | ProjectHephaestus PR #1043, issue #1039 | verified-ci | Old/new line parser and HTTP 422 regression tests |
| One no-commit retry | ProjectHephaestus PR #847 | verified-ci | Verbatim thread injection and forensic marker |
| GraphQL mutation correction | ProjectHephaestus PRs #906/#1006, issues #905/#999 | verified-ci | Live-schema-compatible selections and inputs |
| GO-only existing-PR shortcut | ProjectHephaestus PR #1104 | verified-ci | NO-GO PRs re-enter loop |
| Live head-branch resolution | ProjectHephaestus PR #1106 | verified-ci | `headRefName` replaces issue-derived branch |
| Zero-thread non-GO iteration | ProjectHephaestus PR #1114, issue #725 | verified-ci | Re-review until GO or true exhaustion |
| CI gate owns policy | ProjectHephaestus PR #1112 | verified-ci | Removed false LLM policy enforcement |
| Out-of-scope thread disposition | ProjectHephaestus PR #1245, issue #1216 | verified-local | No edit/commit; empty addressed set |
| Complete review pagination | ProjectHephaestus issue #2390, PR #2671 | verified-ci | Thread and nested-comment pages collected |
| Branch-point and post-review rebase | ProjectHephaestus issue #2711, PR #2712 | verified-ci | Reviewed-head re-entry, conflict budget, merge proof |
| Head-bound normal merges | Issues #2338/#2617/#2371; PRs #2610/#2620/#2652 | verified-ci | Required checks and final reviewed heads bound to merge |

## Detailed Evidence

PR #847 added a single force-engagement retry after a no-commit fixer turn. The retry prompt included
unresolved thread bodies and failing required checks, while a persistent marker recorded the
attempt. It did not allow self-report to resolve threads.

PR #1114 fixed convergence that stopped on a zero-thread non-GO. It reran review through
`MAX_REVIEW_ITERATIONS`, converged immediately only on GO, and assigned `state:skip` only after true
exhaustion. Eighty-one implementer-suite tests passed alongside clean Ruff and mypy evidence.

PR #1245 is intentionally only verified-local. Its sole thread was explicitly pre-existing and out
of scope under a count guard; the coordinator launched no fixer, changed no code, committed nothing,
and returned an empty addressed set. This preserves the distinction between disposition and edit.

PR #2712 preserved the original branch-point snapshot, resolved four findings on the final head,
used a restored-writer re-entry path and independent conflict budget, and required new review after
remote drift. Required checks passed before a normal merge; duplicate plan publication was treated
as benign ownership loss.

## Provenance

- Superseded main SHA-256:
  `8887769a6ef537562282b8f9d6f06ab8392d64ae4c8262e01c78af4816125494`
- Issue #3335 base: `1ae0cb498e5250c341c2a4bf585f97e2a28060af`
- Old/new version: `1.11.0` → `2.0.0`
