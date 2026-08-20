# Git Branch State Triage and Recovery Notes

Supporting cases for
[`git-branch-state-triage-and-recovery.md`](git-branch-state-triage-and-recovery.md).

## Case Index

| State/case | Source | Verification | Result |
| --- | --- | --- | --- |
| Corpus branch superseded after consolidation | Mnemosyne `feature/myrmidon-merge-triage` | verified-local | Three-way counts and content proved old originals were absorbed |
| Unrelated-history branch | Mnemosyne `skill/debugging/fixme-todo-cleanup-v2` | verified-local | Content already on main; classified orphan/superseded |
| Diverged BF16 fix | ProjectOdyssey issue #3088, PR #3197 | verified-local | Reset to remote tip and cherry-picked intended fix |
| Squash-merge false positives | ProjectHephaestus issues #1041/#1282/#1335 | verified-local | Message/content search proved all branches subsumed |
| Selective replay after premature merge | LLM360/Inference360 PRs #460/#462 | verified-ci | Missing commits replayed; artifact rebuilt and exact-head review passed |
| Uncommitted follow-up on merged branch | example-org/metrics-service issue #907, PR #908 | verified-local; CI pending at capture | Stash moved to fresh branch and signed commit |
| Closed PR replacement | Existing source case around closed unmerged recovery | verified-local | Recovered head published as replacement when reopen refused |
| Contaminated stacked child | example-org/inference-service PRs #399/#400 | verified-ci | Parent rebased; child rebuilt with exact leases |

## Detailed Verification

The large Mnemosyne consolidation case compared skill counts at merge-base, branch, and main. The
branch grew while main intentionally shrank through consolidation; branch-only files were old
originals, not unreleased features. The destructive reset followed a preservation stash and direct
content review. The reusable rule is the three-way classification, not the repository-specific
counts.

For the Inference360 replay, the old PR merged while final remediation was active. The follow-up
started at current trunk and replayed only two missing commits, retaining concurrent trunk semantics.
The source-addressed Warden artifact was rebuilt, its digest checked, local validation reported
1,189 tests with 9 skips and 85.10% coverage, and nine exact-head checks plus an independent GO
review covered the final head before merge.

The stacked-child recovery preserved dated backup refs, rebased the parent first, rebuilt the child
on that new parent, and used explicit force-with-lease publication. Local suites and GitHub
CI/CodeQL passed. This is why the main workflow distinguishes parent-relative child verification
from trunk-relative PR verification.

## Provenance

- Superseded main SHA-256:
  `6d115b78ee3f13728871ea289351e746c7933f10e2269e32cddeed02e0330b08`
- Issue #3335 base: `1ae0cb498e5250c341c2a4bf585f97e2a28060af`
- Old/new version: `1.8.0` → `2.0.0`
